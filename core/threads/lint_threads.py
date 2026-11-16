#!/usr/bin/env python3
"""Lint a threads folder: thread frontmatter, plan membership, log entries, links.

Usage:
    uv run threads/lint_threads.py threads
    python threads/lint_threads.py threads [--strict]
    uv run threads/lint_threads.py --examples threads/references

Checks (the definitions live in guides/thread-writing.md; keep the constants in sync):
    - every `topics/{thread-name}/` (kebab-case) has 00-thread.md and log.md
    - 00-thread.md: type Thread, status in THREAD_STATUSES, `##` THREAD_SECTIONS in order
    - `plans:` items point to `planning/{plan}/00-overview.md` or `planning/{plan}.md`,
      exist, are not duplicated, and the plan's `thread:` points back (both directions;
      a plan listed by two threads is an error)
    - plans with `thread:` that no thread lists are errors; Plan Step files have no `thread:`
    - the plan links in `## プラン一覧` equal `plans:` in the same order (unlinked
      `（未作成）` rows are ignored)
    - within a thread, if plan A depends_on plan B, B comes before A in `plans:`
    - closed / abandoned threads have `plans: []`
    - log.md: type Thread Log, no status; entries `## YYYY-MM-DD [kind] title` with kind in
      LOG_KINDS and dates in ascending order; the first entry is [計画]; for closed /
      abandoned the last entry is [完了], and closed has a [完了] entry before it
    - relative links in AGENTS.md, guides/ and topics/ resolve and stay inside the folder
      (log.md of closed / abandoned threads is skipped: deleted plans stay linked there)
    - REQUIRED_FILES exist and leftover `{placeholder}` in topics/ is a warning
      (both skipped with --examples)

Plan files themselves are checked by planning/lint_plans.py, not here. planning/ is never
walked recursively (in the template collection it is a junction to core/plans).

Problems are printed as `path:line: message`.
Exit code 1 if any error. `--strict` also fails on warnings.

Only the standard library is used.
"""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

# guides/thread-writing.md の表と同期する（status の表 / 必須見出しの表 / 種別の表）。
THREAD_STATUSES = {"open", "paused", "closed", "abandoned"}
CLOSED_STATUSES = {"closed", "abandoned"}
THREAD_SECTIONS = ["目的・スコープ", "プラン一覧", "未解決事項"]
PLAN_LIST_SECTION = "プラン一覧"
LOG_KINDS = {"計画", "発見", "仕様変更", "手戻り", "順序変更", "完了"}
FIRST_KIND = "計画"
DONE_KIND = "完了"
THREAD_FILE = "00-thread.md"
LOG_FILE = "log.md"
TOPICS = "topics"
PLANNING = "planning"
# 導入先で必ず存在するファイル（検査対象フォルダからの相対パス）。
REQUIRED_FILES = ["AGENTS.md", "CLAUDE.md"]
# planning/ 直下でプランとして扱わないもの（lint_plans.py と同じ）。
PLAN_SKIP_DIRS = {"guides", "references", "snapshot", "progress", "rough"}
PLAN_SKIP_FILES = {"readme.md", "agents.md", "claude.md"}

THREAD_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOG_ENTRY = re.compile(r"^(\d{4})-(\d{2})-(\d{2}) \[([^\]]+)\] \S")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^##\s+(.+?)\s*$")
PLACEHOLDER = re.compile(r"\{[a-zA-Z_][\w-]*\}")
INLINE_CODE = re.compile(r"`[^`]*`")


def norm(path):
    """Absolute, normalized path WITHOUT following junctions / symlinks."""
    return Path(os.path.normpath(os.path.abspath(path)))


def body_lines(lines):
    """Yield (line_no, line) outside fenced code blocks."""
    in_fence = False
    for i, line in enumerate(lines, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield i, line


class Frontmatter(dict):
    """Frontmatter values plus the file line number of each key / list item."""

    def __init__(self):
        super().__init__()
        self.lines = {}

    def line(self, key):
        return self.lines.get(key, 1)


def parse_frontmatter(text):
    """Minimal parser (same as lint_plans.py): scalars and `key:` + `- item` lists."""
    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match:
        return None
    fm, current = Frontmatter(), None
    for lineno, raw in enumerate(match.group(1).splitlines(), start=2):
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s+(.+)$", line)
        if item and current is not None:
            if not isinstance(fm.get(current), list):
                fm[current] = []
            fm.lines[f"{current}[{len(fm[current])}]"] = lineno
            fm[current].append(item.group(1).strip())
            continue
        kv = re.match(r"^([\w-]+):\s*(.*)$", line)
        if kv:
            current = kv.group(1)
            value = kv.group(2).strip()
            fm[current] = [] if value in ("", "[]") else value
            fm.lines[current] = lineno
    return fm


def as_list(value):
    if isinstance(value, list):
        return value
    return [value] if value else []


class Linter:
    def __init__(self, root, examples=False):
        self.root = norm(root)
        self.examples = examples
        self.errors = []
        self.warnings = []
        self.checked = 0

    def _format(self, path, line, msg):
        base = self.root.parent
        path = norm(path)
        rel = path.relative_to(base) if path.is_relative_to(base) else path
        return f"{rel.as_posix()}:{line}: {msg}"

    def error(self, path, msg, line=1):
        self.errors.append(self._format(path, line, msg))

    def warn(self, path, msg, line=1):
        self.warnings.append(self._format(path, line, msg))

    @staticmethod
    def read(path):
        return path.read_text(encoding="utf-8")

    # ---- generic checks -------------------------------------------------

    def check_links(self, path, lines):
        for i, line in body_lines(lines):
            for target in LINK.findall(INLINE_CODE.sub("", line)):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                dest = norm(path.parent / target.split("#", 1)[0])
                if not dest.is_relative_to(self.root):
                    self.error(path, f"フォルダ外へのリンク: {target}", i)
                elif not dest.exists():
                    self.error(path, f"リンク切れ: {target}", i)

    def check_placeholders(self, path, lines):
        if self.examples:
            return
        for i, line in body_lines(lines):
            for ph in PLACEHOLDER.findall(INLINE_CODE.sub("", line)):
                self.warn(path, f"プレースホルダ {ph} が残っている", i)

    @staticmethod
    def headings(lines):
        return [(i, m.group(1)) for i, line in body_lines(lines) if (m := HEADING.match(line))]

    # ---- plans ----------------------------------------------------------

    def plan_files(self):
        """Plan files in planning/ (one level, like lint_plans.py): {norm path: frontmatter}."""
        planning = self.root / PLANNING
        plans = {}
        if not planning.is_dir():
            return plans
        for entry in sorted(planning.iterdir()):
            if entry.is_dir():
                overview = entry / "00-overview.md"
                if entry.name in PLAN_SKIP_DIRS or not overview.is_file():
                    continue
                for step in sorted(entry.glob("[0-9][0-9]-*.md")):
                    if step.name.startswith("00-"):
                        continue
                    step_fm = parse_frontmatter(self.read(step))
                    if step_fm and "thread" in step_fm:
                        self.error(
                            step,
                            "thread: は overview にだけ書く（Plan Step には書かない）",
                            step_fm.line("thread"),
                        )
                target = overview
            elif entry.suffix == ".md" and entry.name.lower() not in PLAN_SKIP_FILES:
                target = entry
            else:
                continue
            fm = parse_frontmatter(self.read(target))
            if fm is not None:
                plans[norm(target)] = fm
        return plans

    def is_plan_path(self, path):
        """planning/{plan}/00-overview.md or planning/{plan}.md"""
        if not path.is_relative_to(self.root / PLANNING):
            return False
        parts = path.relative_to(self.root / PLANNING).parts
        return (len(parts) == 2 and parts[1] == "00-overview.md") or (
            len(parts) == 1 and parts[0].endswith(".md")
        )

    # ---- threads --------------------------------------------------------

    def check_thread(self, thread_path, plans, members):
        """Check 00-thread.md. Returns its status (or None)."""
        self.checked += 1
        lines = self.read(thread_path).splitlines()
        fm = parse_frontmatter("\n".join(lines))
        if fm is None:
            self.error(thread_path, "frontmatter（先頭の --- ブロック）がない")
            return None
        if fm.get("type") != "Thread":
            self.error(
                thread_path, f"type は 'Thread' にする（現在: {fm.get('type')!r}）", fm.line("type")
            )
        status = fm.get("status")
        if status not in THREAD_STATUSES:
            allowed = " / ".join(sorted(THREAD_STATUSES))
            self.error(
                thread_path,
                f"status は {allowed} のいずれか（現在: {status!r}）",
                fm.line("status"),
            )

        # required sections, in order (prefix match)
        heads = self.headings(lines)
        pos = 0
        for name in THREAD_SECTIONS:
            idx = next((k for k in range(pos, len(heads)) if heads[k][1].startswith(name)), None)
            if idx is None:
                where = (
                    "がない" if not any(t.startswith(name) for _, t in heads) else "の順序が違う"
                )
                self.error(
                    thread_path, f"'## {name}' 節{where}（{' → '.join(THREAD_SECTIONS)} の順）"
                )
            else:
                pos = idx + 1

        # plans:
        if "plans" not in fm:
            self.error(thread_path, "plans: がない（所属プランが無ければ plans: []）")
        raw_plans = fm.get("plans", [])
        if not isinstance(raw_plans, list):
            self.error(thread_path, "plans: は相対パスのリストにする", fm.line("plans"))
            raw_plans = []
        listed, lines_of = [], {}
        for k, item in enumerate(raw_plans):
            line = fm.line(f"plans[{k}]")
            dest = norm(thread_path.parent / item)
            if not self.is_plan_path(dest):
                self.error(
                    thread_path,
                    f"plans: は planning/{{plan}}/00-overview.md か planning/{{plan}}.md を指す: {item}",
                    line,
                )
                continue
            if dest in listed:
                self.error(thread_path, f"plans: に重複: {item}", line)
                continue
            listed.append(dest)
            lines_of[dest] = line
            members.setdefault(dest, []).append(thread_path)
            plan_fm = plans.get(dest)
            if plan_fm is None:
                self.error(thread_path, f"plans: の参照先が見つからない: {item}", line)
                continue
            back = plan_fm.get("thread")
            if not back or isinstance(back, list) or norm(dest.parent / back) != thread_path:
                self.error(
                    thread_path,
                    f"plans: の {item} に、このスレッドを指す thread: が無い（片側だけ）",
                    line,
                )
        if status in CLOSED_STATUSES and listed:
            self.error(
                thread_path,
                f"status が {status} なら plans: は空にする（thread-closing.md）",
                fm.line("plans"),
            )

        # depends_on order within the thread
        index = {p: k for k, p in enumerate(listed)}
        for plan in listed:
            plan_fm = plans.get(plan, {})
            for dep in as_list(plan_fm.get("depends_on")):
                dep_path = norm(plan.parent / dep)
                if dep_path in index and index[dep_path] > index[plan]:
                    self.error(
                        thread_path,
                        f"plans: の並び: {self.rel_plan(plan)} は {self.rel_plan(dep_path)} に depends_on するので後ろに置く",
                        lines_of[plan],
                    )

        # プラン一覧 links == plans:
        section_links, in_section, section_line = [], False, 1
        for i, line in body_lines(lines):
            head = HEADING.match(line)
            if head:
                in_section = head.group(1).startswith(PLAN_LIST_SECTION)
                section_line = i if in_section else section_line
                continue
            if in_section:
                for target in LINK.findall(INLINE_CODE.sub("", line)):
                    dest = norm(thread_path.parent / target.split("#", 1)[0])
                    if dest.is_relative_to(self.root / PLANNING):
                        section_links.append(dest)
        if section_links != listed:
            self.error(
                thread_path,
                f"'## {PLAN_LIST_SECTION}' のプランへのリンク（{len(section_links)}件）が plans:（{len(listed)}件）と同じ順で一致しない",
                section_line,
            )

        self.check_links(thread_path, lines)
        self.check_placeholders(thread_path, lines)
        return status

    def rel_plan(self, path):
        return path.relative_to(self.root / PLANNING).as_posix()

    def check_log(self, log_path, status):
        self.checked += 1
        lines = self.read(log_path).splitlines()
        fm = parse_frontmatter("\n".join(lines))
        if fm is None:
            self.error(log_path, "frontmatter（先頭の --- ブロック）がない")
        else:
            if fm.get("type") != "Thread Log":
                self.error(
                    log_path,
                    f"type は 'Thread Log' にする（現在: {fm.get('type')!r}）",
                    fm.line("type"),
                )
            if "status" in fm:
                self.error(
                    log_path,
                    "log.md に status は書かない（スレッドの status は 00-thread.md）",
                    fm.line("status"),
                )
        entries, prev = [], None
        for i, title in self.headings(lines):
            match = LOG_ENTRY.match(title)
            if not match:
                self.error(
                    log_path, f"エントリ見出しは '## YYYY-MM-DD [種別] 見出し' にする: {title}", i
                )
                continue
            y, m, d, kind = match.groups()
            try:
                day = date(int(y), int(m), int(d))
            except ValueError:
                self.error(log_path, f"日付が不正: {y}-{m}-{d}", i)
                continue
            if kind not in LOG_KINDS:
                self.error(
                    log_path,
                    f"種別は {' / '.join(sorted(LOG_KINDS))} のいずれか（現在: [{kind}]）",
                    i,
                )
            if prev and day < prev:
                self.error(
                    log_path, f"日付が昇順でない（{prev} の後に {day}）。追記のみで、末尾に足す", i
                )
            prev = day
            entries.append((i, kind))
        if not entries:
            self.error(log_path, f"エントリが無い（最初のエントリは [{FIRST_KIND}]）")
        else:
            if entries[0][1] != FIRST_KIND:
                self.error(log_path, f"最初のエントリは [{FIRST_KIND}] にする", entries[0][0])
            if status in CLOSED_STATUSES and entries[-1][1] != DONE_KIND:
                self.error(
                    log_path,
                    f"status が {status} なら最後のエントリは [{DONE_KIND}] にする",
                    entries[-1][0],
                )
            if status == "closed" and not any(kind == DONE_KIND for _, kind in entries[:-1]):
                self.error(
                    log_path,
                    f"closed なら最後の [{DONE_KIND}] の前に所属プランごとの [{DONE_KIND}] エントリを書く",
                    entries[-1][0],
                )
        if status not in CLOSED_STATUSES:
            self.check_links(log_path, lines)
        self.check_placeholders(log_path, lines)

    def run(self):
        if not self.examples:
            for name in REQUIRED_FILES:
                if not (self.root / name).exists():
                    self.error(self.root / name, "必須ファイルがない")
            # links in the entry files and guides (not planning/: lint_plans.py's job)
            for path in [
                *sorted(self.root.glob("*.md")),
                *sorted((self.root / "guides").glob("*.md")),
            ]:
                self.check_links(path, self.read(path).splitlines())

        plans = self.plan_files()
        members = {}
        topics = self.root / TOPICS
        if topics.is_dir():
            for entry in sorted(topics.iterdir()):
                if not entry.is_dir():
                    self.error(entry, f"{TOPICS}/ 直下にはスレッドのフォルダだけを置く")
                    continue
                if not THREAD_NAME.match(entry.name):
                    self.error(entry, f"スレッドのフォルダ名はケバブケースにする: {entry.name}")
                thread_path, log_path = norm(entry / THREAD_FILE), norm(entry / LOG_FILE)
                status = None
                if thread_path.is_file():
                    status = self.check_thread(thread_path, plans, members)
                else:
                    self.error(thread_path, "必須ファイルがない")
                if log_path.is_file():
                    self.check_log(log_path, status)
                else:
                    self.error(log_path, "必須ファイルがない")

        # plan side: thread: must be listed by exactly that thread
        for plan, fm in plans.items():
            listed_by = members.get(plan, [])
            if len(listed_by) > 1:
                names = ", ".join(p.parent.name for p in listed_by)
                self.error(
                    plan, f"複数のスレッドの plans: に載っている（1プラン1スレッド）: {names}"
                )
            if "thread" not in fm:
                continue
            back = fm.get("thread")
            line = fm.line("thread")
            if not back or isinstance(back, list):
                self.error(plan, "thread: は 00-thread.md への相対パスを1つ書く", line)
                continue
            dest = norm(plan.parent / back)
            if dest.name != THREAD_FILE or dest.parent.parent != norm(topics):
                self.error(
                    plan, f"thread: は topics/{{thread-name}}/{THREAD_FILE} を指す: {back}", line
                )
            elif not dest.is_file():
                self.error(plan, f"thread: の参照先が見つからない: {back}", line)
            elif dest not in listed_by:
                self.error(
                    plan,
                    f"thread: のスレッドの plans: にこのプランが無い（片側だけ）: {back}",
                    line,
                )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "root",
        type=Path,
        help="検査するフォルダ（導入先の threads/、または --examples で references/）",
    )
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
    print(
        f"{linter.checked} files checked, {len(linter.errors)} errors, {len(linter.warnings)} warnings"
    )
    failed = linter.errors or (args.strict and linter.warnings)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
