# tsumiki-api

チーム向けタスクボード「tsumiki」の API サーバー（Python 3.12 / FastAPI / PostgreSQL）。

> スターター用の架空リポジトリのため、アプリケーションのコードは含まない。説明は [STARTER.md](STARTER.md)。

## 設計判断

なぜこの構成なのかは [decisions/](decisions) に1判断＝1ファイルで残している。主なもの:

- [0001](decisions/0001-use-python-fastapi.md) Python と FastAPI で書く
- [0005](decisions/0005-error-responses-problem-details.md) エラー応答は RFC 9457 Problem Details
- [0006](decisions/0006-move-to-postgresql-with-uuid.md) PostgreSQL と UUID v7

判断を足すときの手順は [decisions/AGENTS.md](decisions/AGENTS.md)。
