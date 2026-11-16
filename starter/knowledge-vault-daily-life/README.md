# life-log

架空の人物「三上 葵」の日常生活（仕事・趣味・健康・食・人づきあいなど）を、AI エージェントとの会話を通して記録するリポジトリ。AI が本人の近況・好み・やめたことの理由を把握し、相談に答えたり予定を提案したりできるようにする。

## 構成

| フォルダ                                     | 中身                                                                               |
| -------------------------------------------- | ---------------------------------------------------------------------------------- |
| [vault/](vault/README.md)                    | 情報の正本（frontmatter 付き Markdown）。地図は [vault/README.md](vault/README.md) |
| [data/](data/README.md)                      | 外部から取得したスナップショット（キャッシュ）と派生索引                           |
| [docs/vault-schema.md](docs/vault-schema.md) | frontmatter のスキーマ一覧（生成物）                                               |
| `tools/vault/`                               | スキーマ（`schema.py`）と CLI                                                      |

## よく使うコマンド

```sh
uv run tools/vault/validate.py --summary                    # 検証
uv run tools/vault/build_dashboard.py --all                 # ダッシュボードの一覧を作り直す
uv run tools/vault/build_index.py -q "キーワード" -s         # 横断検索
uv run tools/vault/build_index.py --where area=hobby -s     # 趣味だけ（新しい順）
uv run tools/vault/build_index.py --kind event --since 2026-10-01 --tag 友人 -s   # 最近の、友人がらみの出来事
uv run tools/vault/check_entity.py --scope life -s "名称"   # 重複・除外チェック
uv run tools/vault/compact.py list --summary                # 台帳への圧縮候補
uv run tools/vault/compact.py list --events --summary       # 要約に畳む古いイベントログ
```

AI エージェント向けのルールは [AGENTS.md](AGENTS.md) と [vault/AGENTS.md](vault/AGENTS.md)。
