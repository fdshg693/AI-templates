---
template: decisions
installed_at: decisions
extended: [AGENTS.md]
lint: decisions/lint_decisions.py decisions
---

# スターター: decisions-web-service

[core/decisions](../../core/decisions) を、チーム向けタスクボード Web サービス「tsumiki」の API リポジトリに導入し、半年ほど運用した状態。このファイルはスターターの説明で、架空リポジトリの一部ではない（コピーして使うときは削除してよい）。

## references より複雑な点

core の `references/` は「判断1件」と「それを置き換えた判断1件」だけを示す。このスターターは、判断が積み重なったときに出てくる次の状況を含む。

| 状況                                                             | ファイル                                                                                                                                        |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 見直し条件を満たして置き換えられた判断                           | [0002](decisions/0002-store-data-in-sqlite.md) → [0006](decisions/0006-move-to-postgresql-with-uuid.md)                                         |
| 1つの判断で複数の判断をまとめて置き換える                        | [0006](decisions/0006-move-to-postgresql-with-uuid.md)（`supersedes: [0002, 0004]`）                                                            |
| 置き換えを提案したが不採用になり、元の判断がそのまま残る         | [0007](decisions/0007-rewrite-api-in-typescript.md)（`rejected`、`supersedes: [0001]`）と [0001](decisions/0001-use-python-fastapi.md)          |
| 置き換えを提案中で、元の判断はまだ `accepted`                    | [0008](decisions/0008-job-queue-on-postgresql.md)（`proposed`、`supersedes: [0003]`）と [0003](decisions/0003-send-notifications-in-process.md) |
| 置き換えと無関係に有効なままの判断                               | [0005](decisions/0005-error-responses-problem-details.md)                                                                                       |
| 導入先固有の運用（判断の持ち主・レビュー依頼先）を書き足した入口 | [decisions/AGENTS.md](decisions/AGENTS.md) の「導入先固有の運用」節                                                                             |
| ルートの指示ファイルから decisions への1行の導線                 | [AGENTS.md](AGENTS.md)                                                                                                                          |

現在有効な判断は `accepted` の 0001・0003・0005・0006。

## 使い方

1. このフォルダをテンプレート集の外へコピーする（テンプレート集の中では成果物を作らない）。
2. コピー先のルートで検査を実行し、エラー0を確かめる。

   ```bash
   uv run decisions/lint_decisions.py decisions
   ```

3. 次のような作業をエージェントに頼み、テンプレートの運用どおりに進むかを試す。
   - 「0008 を承認したので反映して」→ 0008 を `accepted`、0003 を `superseded` にする（[superseding.md](decisions/guides/superseding.md) の手順4）
   - 「0008 は見送りになった」→ 0008 だけを `rejected` にし、0003 は変更しない
   - 「エラー応答に `trace_id` を足したい」→ 0005 を書き換えず、置き換えの判断を `proposed` で作る
   - 「フロントエンドから TypeScript 化の提案がまた来た」→ 0007 を読み、新しい事実がなければ同じ結論になることを示す
