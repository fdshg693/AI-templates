#!/usr/bin/env python3
"""Lint a decisions folder: file names, frontmatter, sections, supersede links, markdown links.

Usage:
    uv run decisions/lint_decisions.py decisions
    python decisions/lint_decisions.py decisions [--strict]
    uv run decisions/lint_decisions.py decisions --next
    uv run decisions/lint_decisions.py --examples decisions/references

Checks (the definitions live in guides/decision-writing.md; keep STATUSES / SECTIONS in sync):
    - every decision file is named NNNN-slug.md and numbers are unique
    - frontmatter: type, status, date (YYYY-MM-DD), supersedes / superseded_by lists
    - required `##` sections exist in order, the first `#` heading starts with the number,
      and `## 検討した選択肢` has at least two `###` options
    - supersede links are paired (guides/superseding.md):
        status superseded  <=> superseded_by is not empty
        superseded_by X    =>  X exists, is accepted, and lists this number in supersedes
        accepted D supersedes S  =>  S lists D in superseded_by
    - relative links in every .md file resolve (with --examples they must also stay inside the folder)
    - leftover `{placeholder}` in decision files is a warning (skipped with --examples)

Problems are printed as `path:line: message`.
Exit code 1 if any error. `--strict` also fails on warnings.
`--next` prints the next free number and exits.

Only the standard library is used.
"""

import argparse
import re
import sys
from pathlib import Path

# guides/decision-writing.md の状態表・節の表と同期する。
TYPE = "Decision"
STATUSES = {"proposed", "accepted", "rejected", "superseded"}
SECTIONS = ["背景", "決定", "検討した選択肢", "結果"]
OPTIONS_SECTION = "検討した選択肢"
MIN_OPTIONS = 2
# 導入先で必ず存在するファイル（検査対象フォルダからの相対パス）。
REQUIRED_FILES = ["AGENTS.md", "CLAUDE.md"]
# 判断ファイルはフォルダ直下だけを探す（guides/ と references/ は成果物ではない）。これらは判断ファイルではない。
SKIP_FILES = {"readme.md", "agents.md", "claude.md"}

DECISION_NAME = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
NUMBER = re.compile(r"\d{4}")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIST_VALUE = re.compile(r"^\[(.*)\]$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PLACEHOLDER = re.compile(r"\{[a-zA-Z_][\w-]*\}")
INLINE_CODE = re.compile(r"`[^`]*`")


def body_lines(lines):
    """Yield (line_no, line) outside fenced code blocks."""
    in_fence = False
    for i, line in enumerate(lines, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield i, line


def parse_frontmatter(lines):
    """Return {key: (value, line_no)} for `key: value` lines, or None if absent."""
    if not lines or lines[0].strip() != "---":
        return None
    result = {}
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return result
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*(?:#.*)?$", line)
        if match:
            result[match.group(1)] = (match.group(2), i)
    return None


class Decision:
    def __init__(self, path, number, fm):
        self.path = path
        self.number = number
        self.fm = fm
        self.status = fm.get("status", (None, 1))[0]
        self.supersedes = []
        self.superseded_by = []

    def line(self, key):
        return self.fm.get(key, (None, 1))[1]


class Linter:
    def __init__(self, root, examples=False):
        self.root = root
        self.examples = examples
        self.errors = []
        self.warnings = []
        self.decisions = {}

    def _format(self, path, line, msg):
        base = self.root.parent
        rel = path.relative_to(base) if path.is_relative_to(base) else path
        return f"{rel.as_posix()}:{line}: {msg}"

    def error(self, path, msg, line=1):
        self.errors.append(self._format(path, line, msg))

    def warn(self, path, msg, line=1):
        self.warnings.append(self._format(path, line, msg))

    def decision_files(self):
        """Markdown files directly under root (decisions are flat) that are not README/AGENTS/CLAUDE."""
        return sorted(p for p in self.root.glob("*.md") if p.name.lower() not in SKIP_FILES)

    def parse_list(self, decision, key):
        value, line = decision.fm.get(key, (None, 1))
        if value is None:
            self.error(decision.path, f"frontmatter に {key} がない（無ければ [] と書く）", line)
            return []
        match = LIST_VALUE.match(value)
        if not match:
            self.error(
                decision.path, f"{key} は [0001, 0002] 形式のリストにする（現在: {value!r}）", line
            )
            return []
        items = [s.strip() for s in match.group(1).split(",") if s.strip()]
        for item in items:
            if not NUMBER.fullmatch(item):
                self.error(decision.path, f"{key} の要素は4桁の番号にする（現在: {item!r}）", line)
        return [s for s in items if NUMBER.fullmatch(s)]

    def check_file(self, path, lines):
        match = DECISION_NAME.match(path.name)
        if not match:
            self.error(path, "ファイル名は NNNN-slug.md（4桁番号＋英小文字・数字・ハイフン）にする")
            return
        number = match.group(1)
        fm = parse_frontmatter(lines)
        if fm is None:
            self.error(path, "frontmatter（先頭の --- ブロック）がない")
            return
        decision = Decision(path, number, fm)
        if number in self.decisions:
            self.error(path, f"番号 {number} が {self.decisions[number].path.name} と重複している")
        else:
            self.decisions[number] = decision

        value, line = fm.get("type", (None, 1))
        if value != TYPE:
            self.error(path, f"type は '{TYPE}' にする（現在: {value!r}）", line)
        if decision.status not in STATUSES:
            allowed = " / ".join(sorted(STATUSES))
            self.error(
                path,
                f"status は {allowed} のいずれか（現在: {decision.status!r}）",
                decision.line("status"),
            )
        value, line = fm.get("date", (None, 1))
        if value is None or not DATE.match(value):
            self.error(path, f"date は YYYY-MM-DD にする（現在: {value!r}）", line)
        decision.supersedes = self.parse_list(decision, "supersedes")
        decision.superseded_by = self.parse_list(decision, "superseded_by")
        self.check_sections(path, lines, number)
        if not self.examples:
            for i, line in body_lines(lines):
                for ph in PLACEHOLDER.findall(INLINE_CODE.sub("", line)):
                    self.warn(path, f"プレースホルダ {ph} が残っている", i)

    def check_sections(self, path, lines, number):
        h1 = None
        found = []  # (title, line)
        options = 0
        current = None
        for i, line in body_lines(lines):
            match = HEADING.match(line)
            if not match:
                continue
            level, title = len(match.group(1)), match.group(2)
            if level == 1 and h1 is None:
                h1 = (title, i)
            elif level == 2:
                found.append((title, i))
                current = title
            elif level == 3 and current == OPTIONS_SECTION:
                options += 1
        if h1 is None:
            self.error(path, f"'# {number} …' の見出しがない")
        elif not h1[0].startswith(number):
            self.error(path, f"最初の # 見出しは番号 {number} で始める", h1[1])
        titles = [t for t, _ in found]
        for name in SECTIONS:
            if name not in titles:
                self.error(path, f"'## {name}' 節がない")
        present = [t for t in titles if t in SECTIONS]
        expected = [s for s in SECTIONS if s in present]
        if present != expected:
            line = next(i for t, i in found if t in SECTIONS)
            self.error(path, "節の順序は " + " → ".join(SECTIONS) + " にする", line)
        if OPTIONS_SECTION in titles and options < MIN_OPTIONS:
            line = next(i for t, i in found if t == OPTIONS_SECTION)
            self.error(
                path,
                f"'## {OPTIONS_SECTION}' に ### の選択肢を{MIN_OPTIONS}つ以上書く（現在: {options}）",
                line,
            )

    def check_supersede(self):
        for d in self.decisions.values():
            if d.number in d.supersedes or d.number in d.superseded_by:
                self.error(
                    d.path,
                    "自分自身を supersedes / superseded_by に書いている",
                    d.line("supersedes"),
                )
            if d.status == "superseded" and not d.superseded_by:
                self.error(
                    d.path,
                    "status: superseded なら superseded_by に後継の番号を書く",
                    d.line("superseded_by"),
                )
            if d.superseded_by and d.status != "superseded":
                self.error(
                    d.path,
                    f"superseded_by があるなら status は superseded にする（現在: {d.status!r}）",
                    d.line("status"),
                )
            for num in d.supersedes:
                old = self.decisions.get(num)
                if old is None:
                    self.error(d.path, f"supersedes の {num} が存在しない", d.line("supersedes"))
                elif d.status == "accepted" and d.number not in old.superseded_by:
                    self.error(
                        old.path,
                        f"{d.number} が accepted でこれを置き換えている。superseded_by に {d.number} を足し、status を superseded にする",
                        old.line("superseded_by"),
                    )
            for num in d.superseded_by:
                new = self.decisions.get(num)
                if new is None:
                    self.error(
                        d.path, f"superseded_by の {num} が存在しない", d.line("superseded_by")
                    )
                    continue
                if d.number not in new.supersedes:
                    self.error(
                        new.path,
                        f"{d.number} の superseded_by がこれを指している。supersedes に {d.number} を足す",
                        new.line("supersedes"),
                    )
                if new.status != "accepted":
                    self.error(
                        d.path,
                        f"後継 {num} が accepted ではない（現在: {new.status!r}）。後継が採用されるまで置き換えない",
                        d.line("superseded_by"),
                    )

    def check_links(self, path, lines):
        for i, line in body_lines(lines):
            for target in LINK.findall(INLINE_CODE.sub("", line)):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                dest = (path.parent / target.split("#", 1)[0]).resolve()
                if self.examples and not dest.is_relative_to(self.root.resolve()):
                    self.error(
                        path,
                        f"フォルダ外へのリンク（記入例はコピー先に無いものを指せない）: {target}",
                        i,
                    )
                elif not dest.exists():
                    self.error(path, f"リンク切れ: {target}", i)

    def run(self):
        if not self.examples:
            for name in REQUIRED_FILES:
                if not (self.root / name).exists():
                    self.error(self.root / name, "必須ファイルがない")
        for path in sorted(self.root.rglob("*.md")):
            if any(p in {".git", "node_modules"} for p in path.relative_to(self.root).parts):
                continue
            self.check_links(path, path.read_text(encoding="utf-8").splitlines())
        for path in self.decision_files():
            self.check_file(path, path.read_text(encoding="utf-8").splitlines())
        self.check_supersede()

    def next_number(self):
        numbers = [
            int(m.group(1)) for p in self.decision_files() if (m := DECISION_NAME.match(p.name))
        ]
        return f"{max(numbers, default=0) + 1:04d}"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "root",
        type=Path,
        help="検査するフォルダ（導入先の decisions/、または --examples で references/）",
    )
    parser.add_argument("--examples", action="store_true", help="テンプレートの記入例を検査する")
    parser.add_argument("--strict", action="store_true", help="警告もエラー扱いにする")
    parser.add_argument("--next", action="store_true", help="次に使う番号を表示して終了する")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"{args.root}: フォルダが見つからない", file=sys.stderr)
        return 2
    linter = Linter(args.root, examples=args.examples)
    if args.next:
        print(linter.next_number())
        return 0
    linter.run()
    for msg in linter.errors:
        print(f"error: {msg}")
    for msg in linter.warnings:
        print(f"warning: {msg}")
    print(
        f"{len(linter.decisions)} decisions checked, {len(linter.errors)} errors, {len(linter.warnings)} warnings"
    )
    failed = linter.errors or (args.strict and linter.warnings)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
