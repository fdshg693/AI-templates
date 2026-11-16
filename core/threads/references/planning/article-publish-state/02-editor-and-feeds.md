---
type: Plan Step
status: implementing-done
---

# Step 2: 編集画面の公開設定と、一覧・フィードの絞り込み（サンプル）

> [01-schema-and-domain.md](01-schema-and-domain.md) の続き。実装対象ではありません。実行中に分かった事実（フィードの絞り込み漏れ）をプラン本文へ直接反映した例。スレッドの log.md にはプラン横断の影響だけを1エントリで書いている。

## やること

編集画面で公開状態と予約日時を設定できるようにし、記事一覧・RSS フィード・サイトマップには `Published` の記事だけを出す。

## 読むべきファイル・実行推奨Grep

**絞り込みの漏れを防ぐため（優先度: 高）**

- Grep: `Articles.Where` — 記事を列挙している全クエリ
- 読む: `ArticleShare/Controllers/FeedController.cs` — RSS フィードとサイトマップの記事の選び方

## 触るファイル

- 変更: `ArticleShare/Views/Articles/Edit.cshtml` — 公開状態の選択と予約日時の入力欄
- 変更: `ArticleShare/Repositories/ArticleRepository.cs` — 一覧クエリに `PublishState == Published` を追加
- 変更: `ArticleShare/Controllers/FeedController.cs` — フィードとサイトマップも同じ絞り込みにする

## 決定事項

| 決定                                                              | 理由                                                                   |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 絞り込みは Repository の共通メソッド `PublishedOnly()` にまとめる | フィードのように Repository を通らない箇所で漏れたため（実行中に判明） |

## ルール更新ポイント

- なし（Step 1 で追記した `article-domain.md` の範囲に収まる）

## 進め方

- **実行主体**: メインエージェント単独。
- **TODO化**: 編集画面、一覧の絞り込み、フィードとサイトマップの絞り込みの3項目。

## 実行中に判明した変更

- 2026-10-09: `FeedController` が作成日時で記事を選んでおり、予約中の記事がフィードに出ることが分かった。「触るファイル」に `FeedController.cs` を、決定事項に `PublishedOnly()` を追加した。
