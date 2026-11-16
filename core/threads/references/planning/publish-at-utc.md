---
type: Plan
status: implementing-in-progress
thread: ../topics/article-scheduled-publishing/00-thread.md
---

## 実装ステータス

- [ ] 予約日時の UTC 保存と、投稿者のタイムゾーンでの入力・表示

# 予約日時の UTC 保存 実装プラン（サンプル・単一ファイル完結・手戻り）

> 完了済みプランへの手戻りを、新しい単一ファイル完結プランとして起こしたサンプル。実装対象ではありません。元のプラン [article-publish-state](article-publish-state/00-overview.md) の `status` は戻さず、本文も書き換えない。手戻りの原因はスレッドの log.md の `[手戻り]` エントリにある。

## やること

`Article.PublishAt` をサーバーのローカル時刻（JST）から UTC に変え、既存の予約データを変換する。編集画面では投稿者のタイムゾーンで入力・表示し、保存時に UTC へ変換する。

## 読むべきファイル・実行推奨Grep

**ローカル時刻を前提にしている箇所を洗い出すため（優先度: 高）**

- Grep: `PublishAt` — 読み書きしている全箇所
- 読む: `ArticleShare/Models/User.cs` — 投稿者のタイムゾーン設定（`TimeZoneId`）の有無

## 触るファイル

- 新規: `ArticleShare/Migrations/ConvertPublishAtToUtc.cs` — 既存の `PublishAt` を JST から UTC へ変換
- 変更: `ArticleShare/Models/Article.cs` — `PublishAt` を `DateTimeOffset` にする
- 変更: `ArticleShare/Views/Articles/Edit.cshtml` — 投稿者のタイムゾーンで入力・表示

## 決定事項

| 決定                                                                   | 理由                                                                                   |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `PublishAt` は `DateTimeOffset`（UTC）で保存し、変換は表示層だけで行う | 公開ジョブ（スレッドの次のプラン）が現在時刻と比べるとき、タイムゾーンを意識せずに済む |

## 注意点・落とし穴

- 変換マイグレーションの実行中に予約時刻を迎える記事がないよう、公開ジョブを作る前（このプランの間）に済ませる。

## ルール更新ポイント

- `article-domain.md`（既存ファイルへの追記）: 日時は UTC で保存し、表示層でだけ変換すること

## 進め方

- **実行主体**: メインエージェント単独。
- **TODO化**: マイグレーション、モデル、編集画面の3項目。
