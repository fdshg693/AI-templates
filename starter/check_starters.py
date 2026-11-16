#!/usr/bin/env python3
"""Check that each starter stays in sync with its core template and passes the template's lint.

Usage:
    uv run starter/check_starters.py                      # check every starter/*/STARTER.md
    uv run starter/check_starters.py starter/decisions-web-service
    uv run starter/check_starters.py --sync               # copy changed core files into starters, then check

Each starter declares in the frontmatter of its STARTER.md (rules: starter/README.md):
    template: decisions                                   # folder name under core/
    source: references                                    # optional: copy core/<template>/<source>/ instead of the whole template
    installed_at: decisions                               # where the template is copied inside the starter
    extended: [AGENTS.md]                                 # files the starter may only append to
    adapted: [tools/vault/schema.py]                      # optional: files the template's install steps tell you to rewrite
    samples: [vault/scopes/*]                             # optional: sample files replaced by the starter's own (not checked)
    lint: decisions/lint_decisions.py decisions           # script and args, run from the starter root
                                                          # (or [cmd, cmd]; a command starting with `uv` runs as is)

`adapted` and `samples` are fnmatch patterns relative to the copy (`*` also matches `/`).

Checks:
    - every file of core/<template>/[<source>/] except the template's README.md is copied to <starter>/<installed_at>/
    - copied files are identical; files in `extended` must contain every core line, in order;
      files in `adapted` must exist; files in `samples` are not checked
    - the template's lint passes when run from the starter root

`--sync` overwrites copied files (not `extended` / `adapted` / `samples`) with the core version before checking.
Problems are printed as `path:line: message`. Exit code 1 if any problem.

Only the standard library is used.
"""

import argparse
import fnmatch
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CORE = REPO / "core"
# core から導入先へコピーしないもの（README は人間向けでテンプレート置き場にだけ置く）。
NOT_COPIED = {"README.md"}
IGNORED_PARTS = {"__pycache__", ".git", "node_modules"}
REQUIRED_KEYS = ["template", "installed_at", "extended", "lint"]


def parse_manifest(path):
    """Return {key: value} from the frontmatter of STARTER.md, or None if absent."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    result = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if match:
            result[match.group(1)] = match.group(2)
    return None


def parse_list(value):
    match = re.match(r"^\[(.*)\]$", value)
    return [s.strip() for s in match.group(1).split(",") if s.strip()] if match else None


def matches(name, patterns):
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def lint_commands(value):
    """Return the lint commands as argv lists. Plain script commands run with this Python."""
    commands = parse_list(value) or [value]
    return [
        cmd.split() if cmd.split()[0] == "uv" else [sys.executable, *cmd.split()]
        for cmd in commands
    ]


def first_missing_line(core_lines, starter_lines):
    """Return the index of the first core line not found in order in starter_lines, or None."""
    pos = 0
    for i, line in enumerate(core_lines):
        while pos < len(starter_lines) and starter_lines[pos] != line:
            pos += 1
        if pos == len(starter_lines):
            return i
        pos += 1
    return None


def rel(path):
    return path.relative_to(REPO).as_posix()


def check_starter(starter, sync):
    problems = []
    manifest_path = starter / "STARTER.md"
    manifest = parse_manifest(manifest_path)
    if manifest is None:
        return [f"{rel(manifest_path)}:1: frontmatter（先頭の --- ブロック）がない"]
    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    if missing:
        return [f"{rel(manifest_path)}:1: frontmatter に {', '.join(missing)} がない"]
    template = CORE / manifest["template"]
    if not template.is_dir():
        return [f"{rel(manifest_path)}:1: core/{manifest['template']} が存在しない"]
    lists = {}
    for key in ("extended", "adapted", "samples"):
        lists[key] = parse_list(manifest.get(key, "[]"))
        if lists[key] is None:
            return [f"{rel(manifest_path)}:1: {key} は [a, b] 形式のリストにする"]
    extended, adapted, samples = lists["extended"], lists["adapted"], lists["samples"]
    source = template / manifest.get("source", "")
    if not source.is_dir():
        return [f"{rel(manifest_path)}:1: {rel(source)} が存在しない"]
    installed = starter / manifest["installed_at"]

    for src in sorted(source.rglob("*")):
        relative = src.relative_to(source)
        if (
            src.is_dir()
            or src.relative_to(template).as_posix() in NOT_COPIED
            or IGNORED_PARTS & set(relative.parts)
        ):
            continue
        dest = installed / relative
        name = relative.as_posix()
        if matches(name, samples):
            continue
        if sync and name not in extended and not matches(name, adapted):
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dest)
                print(f"synced: {rel(dest)}")
        core_name = src.relative_to(CORE).as_posix()
        if not dest.exists():
            problems.append(f"{rel(dest)}:1: core/{core_name} のコピーがない")
            continue
        if matches(name, adapted):
            continue
        if name in extended:
            core_lines = src.read_text(encoding="utf-8").splitlines()
            index = first_missing_line(core_lines, dest.read_text(encoding="utf-8").splitlines())
            if index is not None:
                problems.append(
                    f"{rel(dest)}:1: extended のファイルは core の内容に追記だけできる。core の {index + 1} 行目が無いか順序が違う"
                )
        elif dest.read_bytes() != src.read_bytes():
            problems.append(
                f"{rel(dest)}:1: core/{core_name} と内容が違う（core を直して --sync する）"
            )

    for command in lint_commands(manifest["lint"]):
        result = subprocess.run(
            command, cwd=starter, capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            problems.append(
                f"{rel(manifest_path)}:1: lint が失敗した（{' '.join(command[1:] if command[0] == sys.executable else command)}）\n{output}"
            )
    return problems


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "starters",
        nargs="*",
        type=Path,
        help="検査するスターター（省略時は starter/ 直下のすべて）",
    )
    parser.add_argument(
        "--sync", action="store_true", help="core の変更をスターターのコピーへ反映してから検査する"
    )
    args = parser.parse_args()
    starters = [p.resolve() for p in args.starters] or sorted(
        p.parent for p in HERE.glob("*/STARTER.md")
    )
    problems = []
    for starter in starters:
        if not (starter / "STARTER.md").is_file():
            problems.append(f"{starter}: STARTER.md が無い")
            continue
        problems.extend(check_starter(starter, args.sync))
    for msg in problems:
        print(f"error: {msg}")
    print(f"{len(starters)} starters checked, {len(problems)} errors")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
