# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""スキーマ文書 docs/vault-schema.md を schema.py から生成する.

--check を付けると書き込まずに差分の有無だけを判定し、差分があれば終了コード1（pre-commit 用）。

    uv run tools/vault/gen_schema_doc.py [--check]
"""

from __future__ import annotations

import argparse
import sys

from schema import ENTITY_STATUS, KINDS, F
from vaultlib import ROOT, configure_stdio, emit_paths, log

DOC_PATH = ROOT / "docs" / "vault-schema.md"

HEADER = """<!-- 自動生成ファイル: tools/vault/gen_schema_doc.py が tools/vault/schema.py から生成する。手で編集しない -->

# vault フロントマタースキーマ

正（SSOT）は [`tools/vault/schema.py`](../tools/vault/schema.py)。スキーマを変えたら
`uv run tools/vault/gen_schema_doc.py` でこの文書を再生成する。

- 未知のキーはエラー。空文字は未記入と同じ扱い。日付は `YYYY-MM-DD`。
- 「必須」でないキーは省略してよい。
"""


def _type(f: F) -> str:
    if f.type == "enum":
        return "enum: " + " / ".join(f"`{k}`" for k in f.choices or {})
    extra = []
    if f.pattern:
        extra.append(f"`{f.pattern}`")
    if f.min is not None or f.max is not None:
        lo = "" if f.min is None else f"{f.min:g}"
        hi = "" if f.max is None else f"{f.max:g}"
        extra.append(f"{lo}〜{hi}")
    if f.max_len:
        extra.append(f"{f.max_len} 文字以内")
    return f.type + (f"（{', '.join(extra)}）" if extra else "")


def _table(fields: tuple[F, ...]) -> list[str]:
    lines = ["| キー | 型 | 必須 | 説明 |", "| --- | --- | --- | --- |"]
    for f in fields:
        typ = _type(f).replace("|", "\\|")
        lines.append(f"| `{f.name}` | {typ} | {'✓' if f.required else ''} | {f.desc} |")
    return lines


def render() -> str:
    out = [HEADER]
    for kind in KINDS.values():
        out += [f"## {kind.name}: {kind.label}", ""]
        out += [f"- 配置: {', '.join(f'`{g}`' for g in kind.globs)}"]
        if kind.key_field:
            out.append(f"- `{kind.key_field}` は配置フォルダ名と一致させる")
        if kind.scope_field:
            out.append(f"- `{kind.scope_field}` は配置先 scope と一致させる")
        if kind.event_name:
            out.append("- ファイル名は `{YYYY-MM-DD}_{kind}.md`。`date` / `kind` と一致させる")
        out += [f"- {n}" for n in kind.notes]
        out += ["", *_table(kind.fields), ""]
        for f in kind.fields:
            if f.item:
                out += [f"`{f.name}` の要素:", "", *_table(f.item), ""]
    out += [
        "## entity の status",
        "",
        "| 値 | ラベル | 分類 | 並び順 | 除外範囲 | 意味 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for key, m in ENTITY_STATUS.items():
        out.append(
            f"| `{key}` | {m.label} | {m.category} | {m.order} | {m.exclusion} | {m.description} |"
        )
    return "\n".join(out) + "\n"


def main() -> int:
    configure_stdio()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="差分があれば終了コード1（書き込まない）")
    args = p.parse_args()
    text = render()
    current = DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
    if args.check:
        if current != text:
            log(f"{DOC_PATH.name} がスキーマと一致しない。gen_schema_doc.py で再生成する")
            emit_paths([DOC_PATH])
            return 1
        return 0
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(text, encoding="utf-8", newline="\n")
    emit_paths([DOC_PATH])
    return 0


if __name__ == "__main__":
    sys.exit(main())
