## リポジトリ全体のルール

このリポジトリは、本人の日常生活（仕事・趣味・健康・食・人づきあいなど）を AI エージェントとの会話を通して記録し、近況と好みを把握するためのもの。本人が「今日〜した」「〜をやめた」と話したら、[vault/AGENTS.md](vault/AGENTS.md) に従って記録する。情報の正本は `vault/`、道具は `tools/`、外部から取ってきたスナップショットは `data/` に置く。

| フォルダ | 中身 | 書き換えてよいか |
| --- | --- | --- |
| `vault/` | 正本（frontmatter 付き Markdown） | 運用ルール [vault/AGENTS.md](vault/AGENTS.md) に従って書く |
| `data/{source}/` | 外部から取得したスナップショット | 取得スクリプトだけが書く。判断・経緯は書かない |
| `data/vault_index.sqlite` | 検索用の派生索引 | 直接書かない。`build_index.py` が作り直す |
| `docs/vault-schema.md` | スキーマ一覧（生成物） | 直接書かない。`gen_schema_doc.py` が作る |
| `tools/vault/` | スキーマ（`schema.py`）と CLI | スキーマを変えるときは下の手順に従う |

### `vault/` を読み書きするとき

- 必ず [vault/AGENTS.md](vault/AGENTS.md) を読む（`vault/` 配下のファイルを開いたときに自動で読まれないツールもあるため）。
- 横断的に探すときは、ファイルを片端から開かずに索引を引く。ヒットした正本のパスが返るので、それを開く。

  ```sh
  uv run tools/vault/build_index.py -q "キーワード" [--kind entity] [--scope {scope}] [-s]
  uv run tools/vault/build_index.py --kind event --since YYYY-MM-DD [--tag タグ] [--where KEY=VALUE] -s   # 絞り込みだけ（新しい順）
  ```

  イベントログは親エンティティのタグ・値でも一致する。`digests` の要約や台帳の `reason` も全文検索に入っている。

### `tools/` の CLI 規約

- stdout には作成・更新・該当したファイルのパスだけを1行1件（リポジトリルート相対）で出す。人間向けの一覧は `--summary`、ログ・警告・エラーは stderr。
- 正常終了は 0、検証エラーなどは 1。
- vault を読むコードは `tools/vault/vaultlib.py` の `load_vault()` を使い、frontmatter を独自にパースしない。ステータスのラベル・並び順・分類は `schema.py` から引き、値のリストを書き写さない。
- 判断を伴うこと（台帳の `reason` を書く、足切りするか決める）は CLI にさせない。CLI は候補の列挙・下書き・機械的な変更だけを担い、判断は AI が材料を読んで行い本人が確認する。

### スキーマを変えるとき

同じ変更の中で次を全部行う。

1. `tools/vault/schema.py` を直す（キー・型・許容値・ステータスの意味はここにだけ書く）。
2. 既存の vault ファイルを新しいスキーマに移行する。
3. `uv run tools/vault/gen_schema_doc.py` で `docs/vault-schema.md` を作り直す。
4. 読む側（`build_dashboard.py`・`build_index.py`・`check_entity.py`・`compact.py`）が新しいキーに対応しているか確かめる。索引のテーブルを変えたら `build_index.py` の `SCHEMA_VERSION` を上げる。
5. `uv run tools/vault/validate.py` がエラー 0 で終わることを確かめる。
