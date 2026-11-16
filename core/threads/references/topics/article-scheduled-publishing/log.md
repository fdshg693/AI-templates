---
type: Thread Log
---

# 記事の予約公開 - 経緯（サンプル）

> [00-thread.md](00-thread.md) の経緯を示すサンプル。実装対象ではありません。古い順に追記し、過去のエントリは書き換えない。1つのプランの中で閉じる詳細は各プランの本文と progress にあり、ここにはプラン横断の事実と判断だけを書く。

## 2026-10-01 [計画] スレッドを作成し2プランに分ける

公開状態の導入（DB・編集画面）と、予約時刻に公開するジョブは触る層が違うため、2つのプランに分ける。状態の導入を先に行う。
反映先: [00-thread.md](00-thread.md)

## 2026-10-02 [計画] article-publish-state を作成

反映先: [article-publish-state](../../planning/article-publish-state/00-overview.md)

## 2026-10-09 [発見] RSS フィードとサイトマップが作成日時で記事を選んでいる

予約中の記事が公開前にフィードへ出る。article-publish-state の Step 2 に「公開済みだけを出す」絞り込みを足し、公開ジョブ側でもキャッシュの破棄が要るので scheduled-publish-job の役割に追記した。
反映先: [article-publish-state Step 2](../../planning/article-publish-state/02-editor-and-feeds.md) / [00-thread.md](00-thread.md)

## 2026-10-20 [仕様変更] 予約日時を投稿者のタイムゾーンで入力・表示する

海外在住の投稿者が増えたため、依頼者から追加の要求があった。`目的・スコープ` を更新した。
反映先: [00-thread.md](00-thread.md)

## 2026-10-20 [手戻り] 予約日時をサーバーのローカル時刻で保存していた

完了済みの article-publish-state は `PublishAt` をサーバーのローカル時刻（JST）で保存しており、投稿者のタイムゾーンへ変換できない。元のプランの `status` は戻さず、UTC で保存し直す publish-at-utc を追加した。
反映先: [article-publish-state](../../planning/article-publish-state/00-overview.md)（原因） / [publish-at-utc](../../planning/publish-at-utc.md)

## 2026-10-21 [順序変更] scheduled-publish-job を publish-at-utc の後へ

公開ジョブは UTC の `PublishAt` と現在時刻を比べるため、publish-at-utc の完了を着手条件にする。scheduled-publish-job を作るときに `depends_on` で publish-at-utc を指す。
反映先: [00-thread.md](00-thread.md)
