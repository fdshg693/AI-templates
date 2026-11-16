#!/usr/bin/env python3
"""Create the skeleton of a new template folder for template-create.

Usage:
    uv run .claude/skills/template-create/scripts/scaffold_template.py core/<name>
    uv run .claude/skills/template-create/scripts/scaffold_template.py core/<name> --guides rough-plan,plan-writing
    uv run .claude/skills/template-create/scripts/scaffold_template.py core/<name> --lint-name lint_x.py --dry-run

Creates:
    AGENTS.md, CLAUDE.md, README.md, guides/<scene>.md (one per --guides entry),
    references/example.md, lint_<snake>.py (from assets/lint_skeleton.py)

Every spot to fill in is marked `TODO:`; inspect_template.py lists them.
Refuses to run if the target folder already exists.
Only the standard library is used.
"""

import argparse
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def agents_md(name, lint, guides):
    scene_rows = "\n".join(
        f"| TODO: 場面（{g}） | [guides/{g}.md](guides/{g}.md) |" for g in guides
    )
    return f"""## `{name}` の作業規約

TODO: このテンプレートで行う作業と対象外を1〜2文で書く。（README.md は導入先にコピーしないので、ここからリンクしない）

作業を始める前に、場面に対応するファイルを読む。

| 場面 | 読む場所 |
| ---- | -------- |
{scene_rows}

## 不変条件

- TODO: 確認できる行動で1行。理由を添える → [guides/{guides[0]}.md](guides/{guides[0]}.md)
- 成果物を作成・更新したら、リポジトリのルートで次がエラー0で終わることを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

  ```bash
  uv run {name}/{lint} {name}
  ```

## サンプル

書こうとしているファイルに対応するサンプルだけを読み、書式と粒度をそろえる。`references/` は導入先の `{name}/` と同じ構造。

| 書くもの | サンプル |
| -------- | -------- |
| TODO: 成果物 | [references/example.md](references/example.md) |

## このテンプレートを編集するとき

テンプレート置き場（`core/{name}/`）で作業するときだけ従う。

- ルールの正本は `guides/`。本ファイルと `references/` にはルールを重複して書かず、リンクにする。
- プレースホルダは `{{name}}` のように `{{}}` で書く。
- TODO: 同時に更新すべき組を書く（例: ガイドの状態値の表と `{lint}` の `FILE_RULES`）。
- `guides/` / `references/` を変更したら、テンプレート置き場のルートで次を実行する。

  ```bash
  uv run core/{name}/{lint} --examples core/{name}/references
  ```
"""


def claude_md():
    return """@./AGENTS.md

<!-- 役割分担: AGENTS.md = エージェント向けの運用ルール（本ファイルはそれを読み込むだけ）。README.md = 人間向けの概要と導入手順（導入先にはコピーしない）。ルールの正本は guides/。記入例は references/（導入先と同じ構造）。 -->
"""


def readme_md(name, lint):
    return f"""# {name}

TODO: 何のためのテンプレートかを1〜2文で書く。既存テンプレートとの境界（〜は別テンプレート `xxx` で扱う）も書く。

- **対象**: TODO: 誰が・どんなリポジトリで使うか。言語・フレームワークは問わない。
- **含まれるもの**: TODO: 書式・手順・検査スクリプトの要約。

## 導入手順

1. 次を導入先リポジトリの `{name}/` にコピーする。この README はコピーしない。

   | コピーするもの | 内容 |
   | -------------- | ---- |
   | [AGENTS.md](AGENTS.md) | エージェント向けの運用ルール（入口） |
   | [CLAUDE.md](CLAUDE.md) | `@./AGENTS.md` を読み込むだけ（Claude Code 用） |
   | [guides/](guides) | 場面別ガイド（ルールの正本） |
   | [references/](references) | 記入例（導入先の `{name}/` と同じ構造） |
   | [{lint}]({lint}) | 成果物の検査 |

2. TODO: 置き換えるプレースホルダ（`{{x}}`）があれば一覧にする。無ければこの手順を消す。
3. ルートの `AGENTS.md`（または `CLAUDE.md`）に「TODO: 〜のときは `{name}/AGENTS.md` に従う」と1行足す（Claude Code ならルート `CLAUDE.md` に `@{name}/AGENTS.md` でもよい）。サブフォルダの AGENTS.md は、ルートで作業するエージェントに自動では読まれないため。
4. リポジトリのルートで検査を実行し、エラーが出ないことを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

   ```bash
   uv run {name}/{lint} {name}
   ```

## 同梱スクリプト

```bash
uv run {name}/{lint} {name}                         # 成果物の検査（エラーは path:line: 形式、非0終了）
uv run {name}/{lint} --examples {name}/references   # テンプレート編集時: 記入例自体を検査
```
"""


def guide_md(scene):
    return f"""# TODO: {scene} のガイド

TODO: どの場面で読むかを1文で書く。

## 作るもの

TODO: 作成・更新するファイルと書式。状態値や必須見出しの一覧はここに表で書き、lint の定数と同期する。

## 手順

1. TODO: 確認できる行動で書く。

## 完了条件

- [ ] TODO: 成果物で確認できる条件
- [ ] lint がエラー0で終わる
"""


def example_md():
    return """---
type: TODO Type
status: done
---

## TODO 見出し

TODO: 架空の題材で、そのまま読める完成状態の記入例を書く。ルール本文は書かず、ガイドへのリンクにとどめる。
"""


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target", type=Path, help="作成するフォルダ（例: core/my-template）")
    parser.add_argument(
        "--guides", default="format", help="作るガイドのファイル名（拡張子なし、カンマ区切り）"
    )
    parser.add_argument("--lint-name", help="lint スクリプト名（既定: lint_<snake>.py）")
    parser.add_argument("--dry-run", action="store_true", help="作成するファイルを表示するだけ")
    args = parser.parse_args()

    name = args.target.name
    if not NAME_RE.match(name):
        print(f"{args.target}: フォルダ名はケバブケース（例: repo-plans）にする", file=sys.stderr)
        return 2
    if args.target.exists():
        print(f"{args.target}: 既に存在する。上書きしない", file=sys.stderr)
        return 1
    guides = [g.strip() for g in args.guides.split(",") if g.strip()]
    if not guides or not all(NAME_RE.match(g) for g in guides):
        print("--guides はケバブケースの名前をカンマ区切りで指定する", file=sys.stderr)
        return 2
    lint = args.lint_name or f"lint_{name.replace('-', '_')}.py"
    lint_src = (ASSETS / "lint_skeleton.py").read_text(encoding="utf-8")

    files = {
        "AGENTS.md": agents_md(name, lint, guides),
        "CLAUDE.md": claude_md(),
        "README.md": readme_md(name, lint),
        "references/example.md": example_md(),
        lint: lint_src.replace("__NAME__", name).replace("__LINT__", lint),
    }
    for g in guides:
        files[f"guides/{g}.md"] = guide_md(g)

    for rel_path, content in files.items():
        path = args.target / rel_path
        print(f"{'would create' if args.dry_run else 'create'}: {path.as_posix()}")
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
