# tsumiki-api

チーム向けタスクボード「tsumiki」の API サーバー。概要と開発手順は [README.md](README.md)。

## 作業のルール

- 設計判断を書く・変えるとき、判断に関わるコード（データベース、ID、エラー応答、通知、使用言語・フレームワーク）を変えるときは [decisions/AGENTS.md](decisions/AGENTS.md) に従う。
- 現在有効な設計判断は `decisions/` の `status: accepted` のファイル。判断に反する実装を頼まれたら、実装する前に依頼者へ伝える。
