#!/usr/bin/env python3
"""Check a learning repository built from learning-template.

Usage:
    uv run lint_learning_repo.py path/to/new-repo
    uv run lint_learning_repo.py --allow-placeholders references   # template self-check
    uv run lint_learning_repo.py --study practice path/to/new-repo  # renamed top folder

Checks:
    - placeholders in PLACEHOLDER left in file/folder names or Markdown text
      (with --allow-placeholders: only placeholders not in PLACEHOLDER are errors)
    - required / forbidden files per folder level (LAYOUT; source of truth is the
      「必須ファイル」table in guides/02-layout.md). Top folders not present are skipped.
    - relative Markdown links point to an existing file/folder inside the checked root
    - every CLAUDE.md is exactly `@./AGENTS.md` and has a sibling AGENTS.md
    - AGENTS.md does not use `@` imports (Claude Code only; other tools read it as text)

Fenced code blocks are skipped. Errors are printed as `path:line: message`.
Exit code 1 if any error. Only the standard library is used.
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

PLACEHOLDER = {"domain", "topic", "project", "tool", "concept", "question"}
PLACEHOLDER_RE = re.compile(r"(?<![$\w])\{([A-Za-z][\w-]*)\}")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}
CLAUDE_BODY = "@./AGENTS.md"

# Keep in sync with the 「必須ファイル」 table in guides/02-layout.md.
ROOT_REQUIRED = ("README.md", "AGENTS.md", "CLAUDE.md")
TOP = (("AGENTS.md", "CLAUDE.md"), ())  # (required, forbidden)
TOPIC = (("AGENTS.md", "CLAUDE.md"), ())
PROJECT = (("README.md", "KNOWLEDGE.md"), ("AGENTS.md", "CLAUDE.md"))
# pattern -> rules for [top folder, depth 1, depth 2, ...]
LAYOUT = {
    "study": [TOP, TOPIC, PROJECT],
    "reading": [TOP, (("overview/README.md",), ())],
    "sandbox": [TOP, TOPIC, PROJECT],
    "build": [TOP, (("README.md",), ())],
    "cheatsheet": [TOP],
}


def iter_paths(root):
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def text_lines(path):
    """Yield (line number, line) outside fenced code blocks."""
    in_fence = False
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield no, line


def bad_placeholders(text, allow):
    names = dict.fromkeys(PLACEHOLDER_RE.findall(text))
    return [n for n in names if not (allow and n in PLACEHOLDER)]


def subdirs(folder):
    return [
        p
        for p in sorted(folder.iterdir())
        if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith(".")
    ]


def check_layout(root, folder_names, err):
    for name in ROOT_REQUIRED:
        if not (root / name).exists():
            err(root, 0, f"必須ファイル {name} が無い")

    def walk(folder, rules):
        required, forbidden = rules[0]
        for name in required:
            if not (folder / name).exists():
                err(folder, 0, f"必須ファイル {name} が無い")
        for name in forbidden:
            if (folder / name).exists():
                err(
                    folder / name,
                    0,
                    "この階層には置かない（ルールはルート・トップ・トピック階層に集約する）",
                )
        if len(rules) > 1:
            for child in subdirs(folder):
                walk(child, rules[1:])

    for pattern, rules in LAYOUT.items():
        top = root / folder_names[pattern]
        if top.is_dir():
            walk(top, rules)


def check(root, allow_placeholders, folder_names):
    errors = []

    def err(path, line, msg):
        rel = path.relative_to(root).as_posix() if path != root else "."
        errors.append(f"{rel}:{line}: {msg}" if line else f"{rel}: {msg}")

    check_layout(root, folder_names, err)

    for path in iter_paths(root):
        for name in bad_placeholders(path.name, allow_placeholders):
            err(path, 0, f"名前にプレースホルダ {{{name}}} が残っている")

        if path.is_dir() or path.suffix.lower() != ".md":
            continue

        if path.name == "CLAUDE.md":
            body = path.read_text(encoding="utf-8").strip()
            if body != CLAUDE_BODY:
                err(path, 1, f"CLAUDE.md の中身は `{CLAUDE_BODY}` の1行だけにする")
            if not (path.parent / "AGENTS.md").exists():
                err(path, 1, "同じフォルダに AGENTS.md が無い")
            continue

        for no, line in text_lines(path):
            for name in bad_placeholders(line, allow_placeholders):
                err(path, no, f"プレースホルダ {{{name}}} が残っている")

            if path.name == "AGENTS.md" and line.startswith("@"):
                err(path, no, "AGENTS.md で `@` import を使っている（通常のリンクにする）")

            for target in LINK_RE.findall(INLINE_CODE_RE.sub("", line)):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                target_path = unquote(target.split("#", 1)[0])
                resolved = (path.parent / target_path).resolve()
                if not resolved.is_relative_to(root):
                    err(path, no, f"チェック対象の外を指すリンク: {target}")
                elif not resolved.exists():
                    err(path, no, f"リンク切れ: {target}")

    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", type=Path, help="検査するリポジトリ（またはフォルダ）")
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="PLACEHOLDER のプレースホルダを許容する（テンプレート自体の検査用）",
    )
    for pattern in LAYOUT:
        parser.add_argument(
            f"--{pattern}",
            default=pattern,
            metavar="NAME",
            help=f"`{pattern}/` パターンの実際のフォルダ名（名前を変えた場合）",
        )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: {args.root} はフォルダではない")
        return 1

    folder_names = {p: getattr(args, p) for p in LAYOUT}
    errors = check(root, args.allow_placeholders, folder_names)
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
