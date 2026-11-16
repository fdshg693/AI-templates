#!/usr/bin/env python3
"""Link core/threads/planning to core/plans (template collection only).

Usage (from the template collection root):
    uv run core/threads/link_plans.py           # create or repair the link
    uv run core/threads/link_plans.py --check   # report only; exit 1 if missing or broken

threads bundles the plans template as `planning/`. Inside the template
collection, `planning/` is not committed: it is a link to the single source
`core/plans` (Windows: directory junction via `mklink /J`, POSIX: relative
symlink `../plans`) and is listed in the root .gitignore. Run this once after
cloning, and again if the link breaks (e.g. the repository was moved and the
junction's absolute path no longer resolves).

- Correct link already present -> does nothing.
- Broken link or link to somewhere else -> removes the link (never the target
  contents) and creates it again.
- A real directory or file at `planning/` -> stops with an error and deletes
  nothing. In a repository where threads was copied in, `planning/` is a real
  directory and this script is not needed.

Only the standard library is used.
"""

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINK = HERE / "planning"
SOURCE = HERE.parent / "plans"
POSIX_TARGET = "../plans"
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003


def is_link(p: Path) -> bool:
    """True for a symlink or a Windows junction (works on Python 3.11+)."""
    try:
        st = os.lstat(p)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    return getattr(st, "st_reparse_tag", 0) == IO_REPARSE_TAG_MOUNT_POINT


def points_to_source(p: Path) -> bool:
    try:
        return os.path.samefile(p, SOURCE)
    except OSError:
        return False


def remove_link(p: Path) -> None:
    # os.rmdir removes a junction (or a directory symlink on Windows) without
    # touching what it points to; os.unlink removes a POSIX symlink.
    if os.name == "nt":
        os.rmdir(p)
    else:
        os.unlink(p)


def create_link(p: Path) -> None:
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(p), str(SOURCE)], check=True, capture_output=True
        )
    else:
        os.symlink(POSIX_TARGET, p, target_is_directory=True)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="作成・修復せず状態だけ表示する（無い・壊れていれば終了コード1）",
    )
    args = ap.parse_args()

    if not SOURCE.is_dir():
        print(f"error: {SOURCE} が無い。テンプレート集の中でだけ使うスクリプト", file=sys.stderr)
        return 1

    if is_link(LINK):
        if points_to_source(LINK):
            print(f"ok: {LINK} -> {SOURCE}")
            return 0
        if args.check:
            print(f"broken: {LINK} がリンク切れ、または別の場所を指している", file=sys.stderr)
            return 1
        remove_link(LINK)
        print(f"removed broken link: {LINK}")
    elif LINK.exists():
        print(
            f"error: {LINK} はリンクではない実体。消さずに中止する（中身を確認して手で移動・削除すること）",
            file=sys.stderr,
        )
        return 1
    elif args.check:
        print(
            f"missing: {LINK} が無い。`uv run core/threads/link_plans.py` を実行する",
            file=sys.stderr,
        )
        return 1

    create_link(LINK)
    if not points_to_source(LINK):
        print(f"error: {LINK} を作ったが {SOURCE} を指していない", file=sys.stderr)
        return 1
    print(f"linked: {LINK} -> {SOURCE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
