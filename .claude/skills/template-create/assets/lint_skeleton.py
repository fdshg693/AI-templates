#!/usr/bin/env python3
"""Lint a __NAME__ folder: frontmatter values, required headings, links, placeholders.

Usage:
    uv run __NAME__/__LINT__ __NAME__
    python __NAME__/__LINT__ __NAME__ [--strict]
    uv run __NAME__/__LINT__ --examples __NAME__/references

Checks (the definitions live in guides/; keep FILE_RULES in sync with them):
    - files matching FILE_RULES: frontmatter exists, `type` and `status` are allowed values,
      required headings exist
    - REQUIRED_FILES exist (skipped with --examples)
    - relative links in every .md file resolve and stay inside the folder (code blocks skipped)
    - leftover `{placeholder}` in checked files is a warning (skipped with --examples)

Problems are printed as `path:line: message`.
Exit code 1 if any error. `--strict` also fails on warnings.

`--examples` lints the template samples in references/ with the same FILE_RULES.

Only the standard library is used.
"""

import argparse
import re
import sys
from pathlib import Path

# TODO: 成果物の種類ごとに1エントリ。glob は検査対象フォルダからの相対パス。
# 値の正本は guides/ の表。変えるときは両方を同時に更新する。
FILE_RULES = [
    {
        "glob": "*.md",
        "type": "TODO Type",
        "statuses": {"draft", "done"},
        "sections": ["## TODO 見出し"],
    },
]
# TODO: 導入先で必ず存在するファイル（検査対象フォルダからの相対パス）。
REQUIRED_FILES = ["AGENTS.md", "CLAUDE.md"]
# FILE_RULES の対象外。ガイド・記入例・凍結コピーは成果物ではない。
SKIP_DIRS = {"guides", "references", "snapshot", ".git", "node_modules"}
SKIP_FILES = {"readme.md", "agents.md", "claude.md"}

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


class Linter:
    def __init__(self, root, examples=False):
        self.root = root
        self.examples = examples
        self.errors = []
        self.warnings = []
        self.checked = 0

    def _format(self, path, line, msg):
        base = self.root.parent
        rel = path.relative_to(base) if path.is_relative_to(base) else path
        return f"{rel.as_posix()}:{line}: {msg}"

    def error(self, path, msg, line=1):
        self.errors.append(self._format(path, line, msg))

    def warn(self, path, msg, line=1):
        self.warnings.append(self._format(path, line, msg))

    def is_artifact(self, path):
        parts = path.relative_to(self.root).parts
        skip = SKIP_DIRS - {"references"} if self.examples else SKIP_DIRS
        return not any(p in skip for p in parts[:-1]) and path.name.lower() not in SKIP_FILES

    def check_rule(self, path, lines, rule):
        self.checked += 1
        fm = parse_frontmatter(lines)
        if fm is None:
            self.error(path, "frontmatter（先頭の --- ブロック）がない")
        else:
            value, line = fm.get("type", (None, 1))
            if value != rule["type"]:
                self.error(path, f"type は '{rule['type']}' にする（現在: {value!r}）", line)
            value, line = fm.get("status", (None, 1))
            if value not in rule["statuses"]:
                allowed = " / ".join(sorted(rule["statuses"]))
                self.error(path, f"status は {allowed} のいずれか（現在: {value!r}）", line)
        found = []
        for _, line in body_lines(lines):
            match = HEADING.match(line)
            if match:
                found.append((match.group(1), match.group(2)))
        for name in rule["sections"]:
            level, _, title = name.partition(" ")
            if not any(lv == level and text.startswith(title) for lv, text in found):
                self.error(path, f"'{name}' 節がない")
        if not self.examples:
            for i, line in body_lines(lines):
                for ph in PLACEHOLDER.findall(INLINE_CODE.sub("", line)):
                    self.warn(path, f"プレースホルダ {ph} が残っている", i)

    def check_links(self, path, lines):
        for i, line in body_lines(lines):
            for target in LINK.findall(INLINE_CODE.sub("", line)):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                dest = (path.parent / target.split("#", 1)[0]).resolve()
                if not dest.is_relative_to(self.root.resolve()):
                    self.error(path, f"フォルダ外へのリンク: {target}", i)
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
            lines = path.read_text(encoding="utf-8").splitlines()
            self.check_links(path, lines)
            if not self.is_artifact(path):
                continue
            for rule in FILE_RULES:
                if path.relative_to(self.root).match(rule["glob"]):
                    self.check_rule(path, lines, rule)
                    break


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "root",
        type=Path,
        help="検査するフォルダ（導入先の __NAME__/、または --examples で references/）",
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
