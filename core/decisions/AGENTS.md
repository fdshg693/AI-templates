## `decisions` の作業規約

設計判断を「何を決め、なぜそうしたか」とともに1判断＝1ファイル（`NNNN-{slug}.md`）で残す場所。実装の手順・作業分割はここに書かない。

作業を始める前に、場面に対応するファイルを読む。

| 場面                                                         | 読む場所                                                                     |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| 判断を書く・提案する（`proposed` → `accepted` / `rejected`） | [guides/decision-writing.md](guides/decision-writing.md)                     |
| 既存の `accepted` の判断を覆す・変える                       | [guides/superseding.md](guides/superseding.md)（書式は decision-writing.md） |
| コードを変える前に、関係する判断を確かめる                   | このフォルダの `status: accepted` のファイルの `## 決定` だけを読む          |

## 不変条件

- 番号は既存の最大番号＋1。欠番を詰めない。理由: 他の場所から番号で参照される → [decision-writing.md「ファイル名」](guides/decision-writing.md#ファイル名)
- `status` は `proposed` / `accepted` / `rejected` / `superseded` だけを使う → [decision-writing.md「frontmatter」](guides/decision-writing.md#frontmatter)
- `accepted` の判断の本文は書き換えず、新しい判断で置き換える。理由: 当時の理由が失われる → [superseding.md「守ること」](guides/superseding.md#守ること)
- `supersedes` と `superseded_by` は対で更新する → [superseding.md「手順」](guides/superseding.md#手順)
- `accepted` の判断に反するコードを書く必要が出たら、コードを書く前に置き換えの判断を `proposed` で作り、依頼者に確認する。理由: 判断とコードが食い違うと、どちらが正しいか後で分からなくなる
- 判断ファイルを作成・更新したら、リポジトリのルートで次がエラー0で終わることを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

  ```bash
  uv run decisions/lint_decisions.py decisions          # 検査
  uv run decisions/lint_decisions.py decisions --next   # 次の番号を表示
  ```

## サンプル

書こうとしているファイルに対応するサンプルだけを読み、書式と粒度をそろえる。`references/` は導入先の `decisions/` と同じ構造。

| 書くもの                           | サンプル                                                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 新しい判断（`accepted`）           | [references/0002-move-settings-to-toml.md](references/0002-move-settings-to-toml.md)（既存の判断を置き換える例を兼ねる）             |
| 置き換えられた判断（`superseded`） | [references/0001-store-settings-in-ini.md](references/0001-store-settings-in-ini.md)（frontmatter だけが変わり、本文は採用時のまま） |

新しい判断を書き始めるときは `status: proposed`、`supersedes: []`、`superseded_by: []` にする。

## このテンプレートを編集するとき

テンプレート置き場（`core/decisions/`）で作業するときだけ従う。

- ルールの正本は `guides/`。本ファイルと `references/` にはルールを重複して書かず、リンクにする。
- プレースホルダは `{name}` のように `{}` で書く。
- 状態値と必須の節を変えるときは、[decision-writing.md](guides/decision-writing.md) の表と `lint_decisions.py` の `STATUSES` / `SECTIONS` を同時に更新する。
- `guides/` / `references/` を変更したら、テンプレート置き場のルートで次を実行する。対応するスターター（`starter/decisions-*`）がある場合は `uv run starter/check_starters.py` も実行する。

  ```bash
  uv run core/decisions/lint_decisions.py --examples core/decisions/references
  ```

## 導入先固有の運用

判断の持ち主（`accepted` / `rejected` を決める人）など、導入先固有の運用はこの節に書き足す。
