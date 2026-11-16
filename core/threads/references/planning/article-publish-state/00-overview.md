---
type: Plan
status: implementing-done
thread: ../../topics/article-scheduled-publishing/00-thread.md
---

## 実装ステータス

- [x] [01-schema-and-domain.md](01-schema-and-domain.md) — 公開状態と予約日時のカラム・ドメインルール
- [x] [02-editor-and-feeds.md](02-editor-and-feeds.md) — 編集画面の公開設定と、一覧・フィードの絞り込み

# 記事の公開状態と予約日時の導入 実装プラン - 概要（サンプル）

> スレッドに所属するフォルダ方式のプランのサンプル。実装対象ではありません。プランの書き方は plans のガイドのとおりで、違いは frontmatter の `thread:` だけ。完了済みだが、所属スレッドが `open` なので削除せずに残している。`PublishAt` をローカル時刻で保存した点は完了後に手戻りになった（経緯はスレッドの log.md、やり直しは [publish-at-utc](../publish-at-utc.md)）。完了済みプランの本文は手戻りがあっても書き換えない。

## 要件

- 記事に公開状態（下書き・予約・公開）と予約日時を持たせ、編集画面で設定できるようにする。
- 公開済みでない記事は、一覧・RSS フィード・サイトマップに出さない。

## 実装ステップ

1. [01-schema-and-domain.md](01-schema-and-domain.md) — カラム追加とドメインルール
2. [02-editor-and-feeds.md](02-editor-and-feeds.md) — 編集画面と一覧・フィードの絞り込み → 完了記録: [progress/99-completion.md](progress/99-completion.md)

## 主要な決定事項

| 決定                                                             | 理由                                                                       |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 公開状態は `Draft` / `Scheduled` / `Published` の enum 1列にする | 真偽値を複数持つと「予約かつ公開」のような矛盾した組み合わせが作れてしまう |
| 予約時刻での公開処理はこのプランに含めない                       | 触る層（バックグラウンドジョブ）が違う。スレッドの別プランで扱う           |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `ArticleShare/Migrations/AddPublishState.cs`

### 変更

- `ArticleShare/Models/Article.cs`
- `ArticleShare/Views/Articles/Edit.cshtml`
- `ArticleShare/Repositories/ArticleRepository.cs`
- `ArticleShare/Controllers/FeedController.cs`

## ルール更新ポイント

- `article-domain.md`（Step 1, 既存ファイルへの追記）: 公開状態の3値と、一覧に出すのは `Published` だけであること

## 進め方

- **TODO化**: ステップ一覧の各項目をそのまま1つのTODOにする。
