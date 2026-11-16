#!/usr/bin/env python3
"""Lint a practice-review folder: sessions, outputs, supersede states, banners, index.md.

Usage:
    uv run practice-review/lint_practice_review.py practice-review
    python practice-review/lint_practice_review.py practice-review [--strict]
    uv run practice-review/lint_practice_review.py --examples practice-review/references

Checks (the definitions live in guides/formats.md; keep the constants below in sync):
    - sessions/YYYY/YYYY-MM-DD-slug.md: type Session, status unreviewed / reviewed,
      date matches the file name and folder, reviewed <=> reviewed_in names a feedback
      that lists this session
    - feedback/ digests/ suggestions/: file name date == generated_at, status current / superseded,
      covers_through <= generated_at, required `##` headings, no leftover FILL_MARK,
      status / superseded_by / banner line equal what `practice.py refresh` would write
    - feedback: sessions exist and are linked in the body, at most MAX_SESSIONS_PER_FEEDBACK
    - suggestions: at least MIN_SUGGESTIONS `###` under `## 提案`
    - profile.md: required headings, covers_through >= the newest reviewed session
    - index.md equals the output of `practice.py refresh`
    - REQUIRED_FILES exist (AGENTS.md / CLAUDE.md skipped with --examples)
    - relative links resolve and stay inside the folder (sessions/ is skipped: raw exports)
    - warnings: files left in inbox/, too many current feedback files (make a digest),
      leftover `{placeholder}` (skipped with --examples)

Problems are printed as `path:line: message`.
Exit code 1 if any error. `--strict` also fails on warnings.

practice.py imports this module (load_vault / expected_states / banner / render_index),
so the rules that the lint checks and the files that refresh writes cannot drift apart.

Only the standard library is used.
"""

import argparse
import os
import re
import sys
from pathlib import Path

# --- guides/formats.md の表と同期する -------------------------------------------------
SESSION_TYPE = "Session"
SESSION_STATUSES = {"unreviewed", "reviewed"}
OUTPUT_STATUSES = {"current", "superseded"}
# フォルダ: (type, index.md での表示名, 必須の ## 見出し)。index.md の「いま読むもの」はこの順に並ぶ
OUTPUT_KINDS = {
    "digests": ("Digest", "まとめ", ["要点", "繰り返している誤り", "定着させたい表現"]),
    "feedback": ("Feedback", "フィードバック", ["要点", "直すところ", "取り入れたい表現"]),
    "suggestions": ("Suggestions", "題材提案", ["提案"]),
}
PROFILE_TYPE = "Profile"
PROFILE_SECTIONS = ["練習の設定", "目標とレベル", "繰り返している誤り", "定着した表現"]
MIN_SUGGESTIONS = 2
MAX_SESSIONS_PER_FEEDBACK = 5
DIGEST_AFTER = 3  # current な feedback がこの件数以上になったらまとめを作る
FILL_MARK = "（記入）"
# ---------------------------------------------------------------------------------------

# 導入先で必ず存在するファイル（検査対象フォルダからの相対パス）。
REQUIRED_FILES = ["AGENTS.md", "CLAUDE.md", "profile.md", "index.md"]
EXAMPLES_SKIP_REQUIRED = {"AGENTS.md", "CLAUDE.md"}
# リンク検査の対象外。guides/references はテンプレート置き場だけにあり、sessions/ は生ログ。
SKIP_LINK_DIRS = {"guides", "references", "sessions", "inbox", ".git", "node_modules"}
INDEX_LIMIT = 20  # index.md に並べる未レビューのセッションの最大件数

DATED_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-[\w-]+\.md$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIST_VALUE = re.compile(r"^\[(.*)\]$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PLACEHOLDER = re.compile(r"\{[a-zA-Z_][\w-]*\}")
INLINE_CODE = re.compile(r"`[^`]*`")
FM_LINE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*?)(?:\s+#.*)?\s*$")


def body_lines(lines):
    """Yield (line_no, line) outside fenced code blocks."""
    in_fence = False
    for i, line in enumerate(lines, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield i, line


def frontmatter_end(lines):
    """Index of the closing `---`, or None if there is no frontmatter."""
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return i
    return None


def parse_frontmatter(lines):
    """Return {key: (value, line_no)} for `key: value` lines, or None if absent."""
    end = frontmatter_end(lines)
    if end is None:
        return None
    result = {}
    for i in range(1, end):
        match = FM_LINE.match(lines[i])
        if match:
            value = match.group(2)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            result[match.group(1)] = (value, i + 1)
    return result


def parse_list(value):
    """`[a, b]` -> ['a', 'b']; None if not a list."""
    match = LIST_VALUE.match(value or "")
    if not match:
        return None
    return [s.strip() for s in match.group(1).split(",") if s.strip()]


def set_frontmatter(lines, key, value):
    """Replace `key: ...` in the frontmatter, or insert it before the closing `---`."""
    end = frontmatter_end(lines)
    for i in range(1, end):
        match = FM_LINE.match(lines[i])
        if match and match.group(1) == key:
            lines[i] = f"{key}: {value}".rstrip()
            return
    lines.insert(end, f"{key}: {value}".rstrip())


def banner_index(lines):
    """Index of the first non-empty line after the frontmatter (where the banner lives)."""
    end = frontmatter_end(lines)
    for i in range(end + 1, len(lines)):
        if lines[i].strip():
            return i
    return None


def rel_link(src_dir, dest):
    return Path(os.path.relpath(dest, src_dir)).as_posix()


class Doc:
    def __init__(self, path, folder):
        self.path = path
        self.folder = folder
        self.stem = path.stem
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.fm = parse_frontmatter(self.lines)

    def get(self, key):
        return (self.fm or {}).get(key, ("", 1))[0]

    def line(self, key):
        return (self.fm or {}).get(key, ("", 1))[1]


class Vault:
    """All files of a practice-review folder, loaded without validation."""

    def __init__(self, root):
        self.root = root
        self.sessions = [Doc(p, "sessions") for p in sorted((root / "sessions").rglob("*.md"))]
        self.outputs = {
            folder: [Doc(p, folder) for p in sorted((root / folder).glob("*.md"))] for folder in OUTPUT_KINDS
        }
        profile = root / "profile.md"
        self.profile = Doc(profile, "") if profile.exists() else None
        inbox = root / "inbox"
        self.inbox = sorted(p for p in inbox.iterdir() if p.is_file() and not p.name.startswith(".")) if inbox.is_dir() else []

    def session_map(self):
        return {d.stem: d for d in self.sessions}

    def unreviewed(self):
        return sorted((d for d in self.sessions if d.get("status") != "reviewed"), key=lambda d: (d.get("date"), d.stem))

    def latest_reviewed_date(self):
        return max((d.get("date") for d in self.sessions if d.get("status") == "reviewed"), default="")


def load_vault(root):
    return Vault(root)


def by_generated(docs):
    return sorted(docs, key=lambda d: (d.get("generated_at"), d.stem))


def expected_states(vault):
    """{path: (status, successor Doc or None)} — the rules of guides/formats.md「古くなる条件」."""
    result = {}
    for folder in ("digests", "suggestions"):
        docs = by_generated(vault.outputs[folder])
        for i, doc in enumerate(docs):
            result[doc.path] = ("current", None) if i == len(docs) - 1 else ("superseded", docs[i + 1])
    digests = by_generated(vault.outputs["digests"])
    for doc in vault.outputs["feedback"]:
        succ = next(
            (g for g in digests
             if g.get("covers_through") >= doc.get("covers_through") and g.get("generated_at") >= doc.get("generated_at")),
            None,
        )
        result[doc.path] = ("current", None) if succ is None else ("superseded", succ)
    return result


def banner(vault, doc, status, succ):
    """The status line written right after the frontmatter of every output file."""
    generated = doc.get("generated_at")
    if status == "current":
        return f"> 状態: 最新 ／ 生成 {generated} ／ {doc.get('covers_through')} までのセッションを反映"
    link = rel_link(doc.path.parent, succ.path)
    index = rel_link(doc.path.parent, vault.root / "index.md")
    return f"> 状態: 古い ／ 生成 {generated} ／ [{succ.stem}]({link}) に置き換え済み。読み返さなくてよい（最新は [index.md]({index})）"


def render_index(vault):
    """Content of index.md (generated by `practice.py refresh`)."""
    states = expected_states(vault)
    root = vault.root
    unreviewed = vault.unreviewed()
    latest = max((d.get("date") for d in vault.sessions), default="なし")
    out = [
        "# 練習ダッシュボード",
        "",
        "<!-- practice.py refresh が生成する。手で編集しない -->",
        "",
        f"最新のセッション: {latest} ／ セッション {len(vault.sessions)} 件（未レビュー {len(unreviewed)} 件）",
        "",
        "## いま読むもの",
        "",
    ]
    rows = []
    for folder, (_, label, _) in OUTPUT_KINDS.items():
        for doc in reversed(by_generated(vault.outputs[folder])):
            if states[doc.path][0] == "current":
                link = rel_link(root, doc.path)
                rows.append(f"| {label} | [{doc.stem}]({link}) | {doc.get('generated_at')} | {doc.get('covers_through')} |")
    if rows:
        out += ["| 種類 | ファイル | 生成 | 反映済みのセッション |", "| --- | --- | --- | --- |", *rows]
    else:
        out.append("まだ無い。")
    if unreviewed:
        out += ["", f"> 未レビューのセッションが {len(unreviewed)} 件ある。上の出力には反映されていない。"]
    out += ["", "## 未レビューのセッション", ""]
    if unreviewed:
        out += ["| 日付 | ファイル | タイトル |", "| --- | --- | --- |"]
        for doc in unreviewed[:INDEX_LIMIT]:
            out.append(f"| {doc.get('date')} | [{doc.stem}]({rel_link(root, doc.path)}) | {doc.get('title')} |")
        if len(unreviewed) > INDEX_LIMIT:
            out += ["", f"ほか {len(unreviewed) - INDEX_LIMIT} 件（`practice.py pending` で一覧できる）。"]
    else:
        out.append("なし。")
    counts = [
        f"{folder} {sum(1 for d in vault.outputs[folder] if states[d.path][0] == 'superseded')}"
        for folder in OUTPUT_KINDS
    ]
    out += ["", "## 古い出力", "", f"置き換え済み: {' ／ '.join(counts)}。読み返さなくてよい。", ""]
    return "\n".join(out)


class Linter:
    def __init__(self, root, examples=False):
        self.root = root
        self.examples = examples
        self.errors = []
        self.warnings = []
        self.vault = load_vault(root)

    def _format(self, path, line, msg):
        base = self.root.parent
        rel = path.relative_to(base) if path.is_relative_to(base) else path
        return f"{rel.as_posix()}:{line}: {msg}"

    def error(self, path, msg, line=1):
        self.errors.append(self._format(path, line, msg))

    def warn(self, path, msg, line=1):
        self.warnings.append(self._format(path, line, msg))

    def check_date(self, doc, key):
        value = doc.get(key)
        if not DATE.match(value):
            self.error(doc.path, f"{key} は YYYY-MM-DD にする（現在: {value!r}）", doc.line(key))
            return False
        return True

    def headings(self, doc):
        """[(level, title, line)] outside code blocks."""
        found = []
        for i, line in body_lines(doc.lines):
            match = HEADING.match(line)
            if match:
                found.append((len(match.group(1)), match.group(2), i))
        return found

    def check_sections(self, doc, sections):
        titles = [t for level, t, _ in self.headings(doc) if level == 2]
        for name in sections:
            if name not in titles:
                self.error(doc.path, f"'## {name}' 節がない")
        present = [t for t in titles if t in sections]
        if present != [s for s in sections if s in present]:
            self.error(doc.path, "節の順序は " + " → ".join(sections) + " にする")

    def check_fill_marks(self, doc):
        for i, line in body_lines(doc.lines):
            if FILL_MARK in line:
                self.error(doc.path, f"{FILL_MARK} が残っている。書き終えてから完了にする", i)
            if not self.examples:
                for ph in PLACEHOLDER.findall(INLINE_CODE.sub("", line)):
                    self.warn(doc.path, f"プレースホルダ {ph} が残っている", i)

    def check_sessions(self):
        seen = {}
        feedback = {d.stem: d for d in self.vault.outputs["feedback"]}
        for doc in self.vault.sessions:
            if doc.fm is None:
                self.error(doc.path, "frontmatter がない。inbox/ に置いて practice.py ingest で取り込む")
                continue
            if doc.stem in seen:
                self.error(doc.path, f"ファイル名が {seen[doc.stem].path.as_posix()} と重複している")
            seen[doc.stem] = doc
            match = DATED_NAME.match(doc.path.name)
            if not match:
                self.error(doc.path, "ファイル名は YYYY-MM-DD-slug.md にする")
            if doc.get("type") != SESSION_TYPE:
                self.error(doc.path, f"type は {SESSION_TYPE} にする（現在: {doc.get('type')!r}）", doc.line("type"))
            status = doc.get("status")
            if status not in SESSION_STATUSES:
                self.error(doc.path, f"status は {' / '.join(sorted(SESSION_STATUSES))} のいずれか（現在: {status!r}）", doc.line("status"))
            if self.check_date(doc, "date"):
                date = doc.get("date")
                if match and match.group(1) != date:
                    self.error(doc.path, f"ファイル名の日付と date（{date}）が違う", doc.line("date"))
                if doc.path.parent.name != date[:4] or doc.path.parent.parent != self.root / "sessions":
                    self.error(doc.path, f"sessions/{date[:4]}/ に置く")
            if not doc.get("title"):
                self.error(doc.path, "title がない", doc.line("title"))
            reviewed_in = doc.get("reviewed_in")
            if status == "reviewed":
                fb = feedback.get(reviewed_in)
                if fb is None:
                    self.error(doc.path, f"reviewed なら reviewed_in に feedback/ のファイル名（拡張子なし）を書く（現在: {reviewed_in!r}）", doc.line("reviewed_in"))
                elif doc.stem not in (parse_list(fb.get("sessions")) or []):
                    self.error(doc.path, f"reviewed_in の {reviewed_in} の sessions にこのセッションが無い", doc.line("reviewed_in"))
            elif status == "unreviewed" and reviewed_in:
                self.error(doc.path, "unreviewed なら reviewed_in は空にする", doc.line("reviewed_in"))

    def check_outputs(self):
        states = expected_states(self.vault)
        sessions = self.vault.session_map()
        for folder, (type_, _, sections) in OUTPUT_KINDS.items():
            for doc in self.vault.outputs[folder]:
                if doc.fm is None:
                    self.error(doc.path, "frontmatter がない")
                    continue
                match = DATED_NAME.match(doc.path.name)
                if not match:
                    self.error(doc.path, "ファイル名は YYYY-MM-DD-slug.md（日付は generated_at）にする")
                if doc.get("type") != type_:
                    self.error(doc.path, f"type は {type_} にする（現在: {doc.get('type')!r}）", doc.line("type"))
                ok = self.check_date(doc, "generated_at") & self.check_date(doc, "covers_through")
                if ok and doc.get("covers_through") > doc.get("generated_at"):
                    self.error(doc.path, "covers_through が generated_at より後になっている", doc.line("covers_through"))
                if ok and match and match.group(1) != doc.get("generated_at"):
                    self.error(doc.path, "ファイル名の日付と generated_at が違う", doc.line("generated_at"))
                self.check_state(doc, *states[doc.path])
                self.check_sections(doc, sections)
                self.check_fill_marks(doc)
                if folder == "feedback":
                    self.check_feedback(doc, sessions)
                if folder == "suggestions":
                    self.check_suggestions(doc)
        current = [d for d in self.vault.outputs["feedback"] if states[d.path][0] == "current"]
        if len(current) >= DIGEST_AFTER:
            self.warn(self.root / "feedback", f"current な feedback が {len(current)} 件ある。guides/digesting.md に従ってまとめを作る")

    def check_state(self, doc, status, succ):
        refresh = "practice.py refresh を実行する"
        if doc.get("status") not in OUTPUT_STATUSES:
            self.error(doc.path, f"status は {' / '.join(sorted(OUTPUT_STATUSES))} のいずれか（現在: {doc.get('status')!r}）", doc.line("status"))
        elif doc.get("status") != status:
            self.error(doc.path, f"status は {status} になるはず。{refresh}", doc.line("status"))
        want = succ.stem if succ else ""
        if doc.get("superseded_by") != want:
            self.error(doc.path, f"superseded_by は {want!r} になるはず。{refresh}", doc.line("superseded_by"))
        i = banner_index(doc.lines)
        if i is None or doc.lines[i] != banner(self.vault, doc, status, succ):
            self.error(doc.path, f"frontmatter 直後の状態バナーが古い・無い。{refresh}", (i or 0) + 1)

    def check_feedback(self, doc, sessions):
        names = parse_list(doc.get("sessions"))
        if not names:
            self.error(doc.path, "sessions に対象セッションのファイル名を [a, b] 形式で書く", doc.line("sessions"))
            return
        if len(names) > MAX_SESSIONS_PER_FEEDBACK:
            self.error(doc.path, f"1ファイルで扱うセッションは {MAX_SESSIONS_PER_FEEDBACK} 件まで（現在: {len(names)}）", doc.line("sessions"))
        text = "\n".join(doc.lines)
        dates = []
        for name in names:
            session = sessions.get(name)
            if session is None:
                self.error(doc.path, f"sessions の {name} が sessions/ に無い", doc.line("sessions"))
                continue
            dates.append(session.get("date"))
            if session.get("status") != "reviewed" or session.get("reviewed_in") != doc.stem:
                self.error(session.path, f"{doc.stem} がこのセッションを扱っている。status: reviewed、reviewed_in: {doc.stem} にする", session.line("status"))
            if f"{name}.md)" not in text:
                self.error(doc.path, f"本文から {name} へのリンクが無い（指摘の根拠を示す）")
        if dates and doc.get("covers_through") != max(dates):
            self.error(doc.path, f"covers_through は対象セッションの最新の日付 {max(dates)} にする", doc.line("covers_through"))

    def check_suggestions(self, doc):
        count, inside = 0, False
        for level, title, _ in self.headings(doc):
            if level == 2:
                inside = title == "提案"
            elif level == 3 and inside:
                count += 1
        if count < MIN_SUGGESTIONS:
            self.error(doc.path, f"'## 提案' に ### の題材を {MIN_SUGGESTIONS} つ以上書く（現在: {count}）")

    def check_profile(self):
        doc = self.vault.profile
        if doc is None:
            return
        if doc.fm is None:
            self.error(doc.path, "frontmatter がない")
            return
        if doc.get("type") != PROFILE_TYPE:
            self.error(doc.path, f"type は {PROFILE_TYPE} にする（現在: {doc.get('type')!r}）", doc.line("type"))
        self.check_date(doc, "updated_at")
        if doc.get("covers_through") and not DATE.match(doc.get("covers_through")):
            self.error(doc.path, "covers_through は YYYY-MM-DD にする（未レビューなら空）", doc.line("covers_through"))
        latest = self.vault.latest_reviewed_date()
        if latest and doc.get("covers_through") < latest:
            self.error(doc.path, f"{latest} のセッションまでレビュー済みなのに covers_through が古い。guides/reviewing.md の手順で更新する", doc.line("covers_through"))
        self.check_sections(doc, PROFILE_SECTIONS)
        self.check_fill_marks(doc)

    def check_index(self):
        path = self.root / "index.md"
        if path.exists() and path.read_text(encoding="utf-8") != render_index(self.vault):
            self.error(path, "index.md が最新でない。practice.py refresh を実行する")

    def check_links(self):
        for path in sorted(self.root.rglob("*.md")):
            if any(p in SKIP_LINK_DIRS for p in path.relative_to(self.root).parts[:-1]):
                continue
            for i, line in body_lines(path.read_text(encoding="utf-8").splitlines()):
                for target in LINK.findall(INLINE_CODE.sub("", line)):
                    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                        continue
                    dest = (path.parent / target.split("#", 1)[0]).resolve()
                    if self.examples and not dest.is_relative_to(self.root.resolve()):
                        self.error(path, f"フォルダ外へのリンク（記入例はコピー先に無いものを指せない）: {target}", i)
                    elif not dest.exists():
                        self.error(path, f"リンク切れ: {target}", i)

    def run(self):
        for name in REQUIRED_FILES:
            if self.examples and name in EXAMPLES_SKIP_REQUIRED:
                continue
            if not (self.root / name).exists():
                self.error(self.root / name, "必須ファイルがない")
        for path in self.vault.inbox:
            self.warn(path, "inbox/ に取り込み前のファイルがある。guides/ingesting.md に従って取り込む")
        self.check_sessions()
        self.check_outputs()
        self.check_profile()
        self.check_index()
        self.check_links()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path, help="検査するフォルダ（導入先の practice-review/、または --examples で references/）")
    parser.add_argument("--examples", action="store_true", help="テンプレートの記入例を検査する")
    parser.add_argument("--strict", action="store_true", help="警告もエラー扱いにする")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"{args.root}: フォルダが見つからない", file=sys.stderr)
        return 2
    linter = Linter(args.root, examples=args.examples)
    linter.run()
    for msg in linter.errors:
        print(f"error: {msg}")
    for msg in linter.warnings:
        print(f"warning: {msg}")
    files = len(linter.vault.sessions) + sum(len(v) for v in linter.vault.outputs.values())
    print(f"{files} files checked, {len(linter.errors)} errors, {len(linter.warnings)} warnings")
    failed = linter.errors or (args.strict and linter.warnings)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
