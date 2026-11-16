# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""vault のフロントマターをスキーマ（schema.py）と配置ルールで検証する.

- エラー（型・許容値・必須キー・フォルダ名/ファイル名との不一致・台帳との二重登録）があれば終了コード1。
- 警告（幅の無い score、期限切れの next_due、参照先キーが無い、派生文書の同期漏れ等）は --strict のときだけ失敗。
- stdout には問題のあったファイルのパスだけを出す。内容は stderr、一覧は --summary。

    uv run tools/vault/validate.py [--summary] [--strict] [--today YYYY-MM-DD] [--root DIR]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from vaultlib import ROOT, configure_stdio, emit_paths, load_vault, log


def main() -> int:
    configure_stdio()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="vault/ を含むディレクトリ（既定: リポジトリルート）",
    )
    p.add_argument("--strict", action="store_true", help="警告も失敗扱いにする")
    p.add_argument(
        "--today", type=dt.date.fromisoformat, default=dt.date.today(), help="期限切れ判定の基準日"
    )
    p.add_argument("-s", "--summary", action="store_true", help="人間向けの一覧を stderr に出す")
    args = p.parse_args()

    vault = load_vault(args.root, today=args.today)
    errors, warnings = vault.errors, vault.warnings
    for i in errors:
        log(f"[error] {i}")
    for i in warnings:
        log(f"[warn]  {i}")
    if args.summary:
        log(
            f"\n{len(vault.docs)} ファイルを検証: エラー {len(errors)} 件 / 警告 {len(warnings)} 件"
        )
    emit_paths([i.path for i in vault.issues])
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
