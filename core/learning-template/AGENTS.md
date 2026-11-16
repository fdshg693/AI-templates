## `learning-template` の作業規約

学習リポジトリを作るためのテンプレート。考え方を説明する `guides/` と、コピーして使う参考ファイル一式の `references/`（コピー先と同じ構造）、移植後の検査スクリプト `lint_learning_repo.py` に分かれる。人間向けの概要と導入手順は [README.md](README.md) にある。

**`references/` 配下の `AGENTS.md` / `CLAUDE.md` は、コピー先の学習リポジトリで使う成果物（サンプル）であり、このフォルダで作業するときのルールではない。** このフォルダでの作業ルールは本ファイルだけに書く。

### 場面別の参照先

| 場面                                              | 読む場所                                                                                   |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 原則（なぜこう分けるか）を確認・変更する          | [guides/01-philosophy.md](guides/01-philosophy.md)                                         |
| トップフォルダのパターンを追加・変更する          | [guides/02-layout.md](guides/02-layout.md) の表と、そこからリンクされた `references/` 配下 |
| AI向け指示ファイル（AGENTS.md）の書き方を変更する | [guides/03-agent-instructions.md](guides/03-agent-instructions.md)                         |
| 移植手順・プレースホルダ一覧を変更する            | [guides/04-adapting.md](guides/04-adapting.md)                                             |
| 新しい学習リポジトリへの導入を手伝う              | [guides/04-adapting.md](guides/04-adapting.md)                                             |

### 編集時のルール

- `guides/` と `references/` を対で更新する。guides で説明しているパターン・ルールを変えたら、対応する `references/` のファイルも同じ変更に合わせる（逆も同様）。パターンと `references/` 内フォルダの対応は [guides/02-layout.md](guides/02-layout.md) の表が正本。
- `references/` には特定ドメインの学習内容を書かない。置換必須の固有名は [guides/04-adapting.md](guides/04-adapting.md) の一覧にあるもの（`{domain}` `{topic}` など）だけを使い、本文の記入欄は `（…）` で書く。置換必須のプレースホルダを増やす場合は [guides/04-adapting.md](guides/04-adapting.md) の一覧と `lint_learning_repo.py` の `PLACEHOLDER` を同時に更新する。
- `references/` はコピー先のリポジトリと同じ構造に保つ（`references/` 内のパス＝コピー先のパス）。フォルダを追加・移動したら [guides/04-adapting.md](guides/04-adapting.md) の対応表と [guides/02-layout.md](guides/02-layout.md) の表を合わせる。必須ファイルを変えたら、[guides/02-layout.md](guides/02-layout.md) の「必須ファイル」表と `lint_learning_repo.py` の `LAYOUT` を同時に更新する。
- `references/` 内の各階層でも、`AGENTS.md` を正本、`CLAUDE.md` を `@./AGENTS.md` の1行のエイリアスにする関係を崩さない。`AGENTS.md` には `@` import を書かず、他ファイルは通常のリンクで参照する。
- `references/` 内のリンクは `references/` の外（`guides/` 等）を指さない（コピー先には存在しない）。
- `guides/` / `references/` を編集したら、次のコマンドがエラー0で終わることを確認する。

  ```sh
  uv run lint_learning_repo.py --allow-placeholders references
  uv run lint_learning_repo.py --allow-placeholders .
  ```

- このフォルダでテンプレートを使った実作業（実際の学習リポジトリ作り）はしない。試すときは別の場所にコピーする。
