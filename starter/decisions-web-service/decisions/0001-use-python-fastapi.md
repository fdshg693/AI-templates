---
type: Decision
status: accepted
date: 2026-03-02
supersedes: []
superseded_by: []
---

# 0001 バックエンドは Python と FastAPI で書く

## 背景

チームのタスクボード Web サービス「tsumiki」の API サーバーを新規に作る。開発者は3人で、全員が Python の業務経験を持ち、うち2人は TypeScript も書ける。最初のリリースは6週間後で、画面はフロントエンド担当が別リポジトリで作る。API 仕様は OpenAPI でフロントエンドと共有したい。

## 決定

API サーバーは Python 3.12 と FastAPI で書き、OpenAPI 仕様は FastAPI の自動生成を正とする。

## 検討した選択肢

### Python + FastAPI

- 利点: 3人全員が書ける。型ヒントから OpenAPI 仕様を自動生成でき、フロントエンドとの仕様共有の手作業が要らない
- 欠点: CPU を使う処理が多くなると、同じ台数あたりの処理量が Node.js / Go より落ちる

### TypeScript + NestJS

- 利点: フロントエンドと型定義を共有できる
- 欠点: 書けるのが2人で、6週間の期限に対してレビューが1人に集中する

### Go + 標準ライブラリ

- 利点: 処理性能が高く、単一バイナリで配布できる
- 欠点: 経験者がいない。OpenAPI 仕様を別途書いて同期する必要がある

## 結果

- 3人で並行して API を実装できる
- OpenAPI 仕様は `/openapi.json` から取得し、手で書かない
- API の p95 応答時間が 300ms を超え、原因が CPU 処理にあると分かったら、該当部分の別言語化を別の判断として検討する
