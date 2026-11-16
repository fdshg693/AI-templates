# テンプレート集

AIコーディングエージェント（AGENTS.md / CLAUDE.md）と一緒に作業するときに使い回せる、リポジトリ運用のテンプレートを集めたリポジトリです。特定の言語・フレームワーク・ツールには依存せず、必要なものを自分のリポジトリにコピーして使います。

## 構成

| フォルダ | 内容 |
| -------- | ---- |
| [core/](core) | テンプレート本体 |
| [starter/](starter) | テンプレートを導入して運用した状態の架空リポジトリ（より複雑な適用例）。運用ルールは [starter/README.md](starter/README.md) |

各テンプレートの中は、`guides/`（ルールの正本・手順）、`references/`（コピー先と同じ構造の例）、`lint_<template>.py`（成果物が規約に沿っているかの検査）で揃える。

### core の中身

- [learning-template/](core/learning-template) — 学習用リポジトリのテンプレート。学習方法をリポジトリ構造とAI向け指示ファイルで強制する。考え方（`guides/`）、コピー先と同じ構造の参考パターン（`references/`）、移植後の検査スクリプト（`lint_learning_repo.py`）で構成。
- [plans/](core/plans) — 既存コードベースに機能を追加する際のプラン運用。書式・`status`・依存関係・スナップショット、整合性チェック用スクリプト（`lint_plans.py` / `snapshot_plan.py`）を含む。
- [knowledge-vault/](core/knowledge-vault) — 調べて・比べて・判断していく活動の記録を、長期間・大量になっても AI と人間が使える状態に保つ情報集約テンプレート。frontmatter 付き Markdown を正本にし、スキーマ（`schema.py`）・検証・自動生成のダッシュボード・SQLite 全文検索索引・重複チェック・見送り台帳への圧縮を組み合わせる。考え方（`guides/`）と、コピー先と同じ構造の実例一式（`references/`、検証は `references/tools/vault/validate.py`）で構成。
- [decisions/](core/decisions) — 設計判断を1判断＝1ファイルで残す最小テンプレート（ADR）。`status`（proposed / accepted / rejected / superseded）と置き換え関係の整合を `lint_decisions.py` で検査する。
- [repo-plans/](core/repo-plans) — 新規リポジトリを立ち上げるための計画運用。仕様・技術選定 → 最小実装 → 土台整備の3フェーズで進める。計画の書式（`guides/plan-format.md`）と整合性チェック用スクリプト（`lint_repo_plans.py`）を含む。
- [practice-review/](core/practice-review) — 外部の練習相手（ChatGPT など）との練習セッションのエクスポートを取り込み、未レビュー分だけをレビューしてフィードバック・まとめ・次の題材を出す運用（主な用途は外国語会話の練習）。セッションの `unreviewed` / `reviewed`、出力の `current` / `superseded` と状態バナー・自動生成のダッシュボード、検査・運用スクリプト（`lint_practice_review.py` / `practice.py`）を含む。
- [threads/](core/threads) — 複数プランにまたがる大規模な変更を「スレッド」単位で束ねるテンプレート。所属プラン・予定順・実行中に判明した事実・仕様変更・手戻りの経緯を記録し、プラン ⇔ スレッドの双方向の関連付けを `lint_threads.py` で検査する。plans は `core/threads/planning` への Junction（POSIX ではシンボリックリンク、コミットしない）で取り込んでおり正本は `core/plans`。clone 後に `uv run core/threads/link_plans.py` を1回実行する。

### starter の中身

- [decisions-web-service/](starter/decisions-web-service) — `core/decisions` を Web サービスの API リポジトリに導入した例。置き換えの連鎖・複数判断の一括置き換え・不採用・提案中を含む。core との同期と lint は `starter/check_starters.py` で検査。
- [knowledge-vault-daily-life/](starter/knowledge-vault-daily-life) — `core/knowledge-vault` を架空の人物の日常生活の記録に導入した例。最近の出来事・古いイベントログの要約（digests）・やめたことの台帳・profile への昇格・area での絞り込みを含む。

## 使い方

1. `core` から使いたいテンプレートを選び、各フォルダの `README.md` を読む。
2. 対象リポジトリのルートにフォルダごとコピーする。
3. プレースホルダやドメイン固有の記述を自分向けに書き換える。

運用した状態を見たい・試したいときは、対応する `starter/` のスターターをフォルダごとテンプレート集の外へコピーして使う。
