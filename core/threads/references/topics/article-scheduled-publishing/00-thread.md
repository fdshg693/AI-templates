---
type: Thread
status: open
plans:
  - ../../planning/article-publish-state/00-overview.md # 公開状態と予約日時の導入（完了済み。スレッドが open の間は削除しない）
  - ../../planning/publish-at-utc.md # 手戻り: 予約日時を UTC で保存し直す
---

# 記事の予約公開（サンプル）

> 架空の機能を題材に、`open` のスレッドの `00-thread.md` を示すサンプル。実装対象ではありません。1つ目のプランは完了済みだがスレッドが `open` なので残している。2つ目は完了済みプランへの手戻りで追加したプラン、3つ目はまだ作っていないプラン。経緯は [log.md](log.md)。

## 目的・スコープ

投稿者が記事の公開日時を予約でき、その時刻に自動で公開されるようにする。予約日時は投稿者のタイムゾーンで入力・表示する（2026-10-20 の仕様変更で追加）。

含めないもの: 公開時の購読者への通知（既存の通知設定の範囲。必要になったら別のスレッドにする）、予約の一括編集。

## プラン一覧

1. [article-publish-state](../../planning/article-publish-state/00-overview.md) — 記事に公開状態（下書き・予約・公開）と予約日時を導入する（完了）
2. [publish-at-utc](../../planning/publish-at-utc.md) — 手戻り: 予約日時を UTC で保存し、表示時に投稿者のタイムゾーンへ変換する
3. （未作成）scheduled-publish-job — 予約日時を過ぎた記事を公開するバックグラウンドジョブ。公開時に RSS フィードとサイトマップのキャッシュを破棄する（2026-10-09 の発見）。publish-at-utc の完了が着手条件

## 未解決事項

- 公開ジョブの実行間隔（1分か5分か）。scheduled-publish-job を作るときに決める。
