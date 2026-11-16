# （リポジトリ名）

（何の情報を、何のために集めるリポジトリか）

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
uv run tools/vault/check_entity.py --scope work -s "名称"   # 重複・除外チェック
uv run tools/vault/compact.py list --summary                # 台帳への圧縮候補
uv run tools/vault/compact.py list --events --summary       # 要約に畳む古いイベントログ
```

AI エージェント向けのルールは [AGENTS.md](AGENTS.md) と [vault/AGENTS.md](vault/AGENTS.md)。
