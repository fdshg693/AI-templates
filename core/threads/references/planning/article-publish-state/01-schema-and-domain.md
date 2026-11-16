---
type: Plan Step
status: implementing-done
---

# Step 1: 公開状態と予約日時のカラム・ドメインルール（サンプル）

> [00-overview.md](00-overview.md) の続き。実装対象ではありません。スレッドに所属するプランでも、ステップファイルには `thread:` を書かない。

## やること

`Article` に公開状態 `PublishState` と予約日時 `PublishAt` を追加し、「`Scheduled` のときだけ `PublishAt` を持つ」ルールをドメイン側で守る。

## 読むべきファイル・実行推奨Grep

**既存のドメインルールの置き場を確認するため（優先度: 高）**

- 読む: `ArticleShare/Models/Article.cs` — 既存の論理削除フラグの持ち方
- Grep: `IsDeleted` — 一覧系クエリの絞り込み箇所（Step 2 で公開状態の絞り込みを足す場所の洗い出し）

## 触るファイル

- 新規: `ArticleShare/Migrations/AddPublishState.cs` — 既存記事は `Published` で埋める
- 変更: `ArticleShare/Models/Article.cs` — `PublishState`・`PublishAt`・状態遷移のメソッド

## 決定事項

| 決定 | 理由 |
| ---- | ---- |
| `PublishAt` は `DateTime` でサーバーのローカル時刻のまま保存する | 投稿者は全員国内で、表示もサーバー時刻でよい（後の仕様変更で手戻りになった） |

## ルール更新ポイント

- `article-domain.md`（既存ファイルへの追記）: 公開状態の3値と、`PublishAt` を持つのは `Scheduled` だけであること

## 進め方

- **実行主体**: メインエージェント単独。
- **TODO化**: カラム追加とドメインルールの2項目。
