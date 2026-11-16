# 学習レポジトリ・テンプレート

「学習方法をリポジトリ構造とAI向け指示ファイルで強制する」やり方を、特定の題材から切り離して
誰でも使える形にしたテンプレートです。

対象読者は「新しい学習リポジトリ（任意の技術領域）をこれから作りたい人」です。
このテンプレート自体には特定ドメインの学習内容は含みません。
ChatGPT などとの練習セッションのログをレビューし続ける運用は、別テンプレート `practice-review` で扱います。

## 構成

- [`guides/`](./guides) — 考え方の説明（なぜこう分けるか）。最初に読む。
  - [01-philosophy.md](./guides/01-philosophy.md) — 核となる4つの原則
  - [02-layout.md](./guides/02-layout.md) — トップフォルダの分け方と使い分け
  - [03-agent-instructions.md](./guides/03-agent-instructions.md) — AI向け指示ファイル（AGENTS.md）の書き方
  - [04-adapting.md](./guides/04-adapting.md) — 自分のリポジトリに移植する手順とチェックリスト
- [`references/`](./references) — 実際に配置するファイルの参考パターン。コピー先のリポジトリと同じ構造で並べてあり、
  プレースホルダ（`{topic}` 等）と最小限のダミー内容のみで構成されている。
- [`lint_learning_repo.py`](./lint_learning_repo.py) — 移植後のリポジトリに残ったプレースホルダ・リンク切れ・
  `CLAUDE.md` の形式・階層ごとの必須ファイルを検査するスクリプト（Python 標準ライブラリのみ）。

## 使い方

1. `guides/01-philosophy.md` と `guides/02-layout.md` を読み、自分の学習目的にどのトップフォルダ構成が
   合うか決める（全部揃える必要はない）。
2. [guides/04-adapting.md](./guides/04-adapting.md) の手順に従ってコピー・置き換え・検査を行う。
