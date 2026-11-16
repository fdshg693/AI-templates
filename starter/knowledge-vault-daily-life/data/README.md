# data/ — 外部から取得したスナップショット

外部サイト・API・手作業のコピーで取ってきた「その時点の内容」を `data/{source}/` に置く。正本ではないキャッシュで、判断や経緯は書かない（それは `vault/` に書く）。

- 1件1ファイルの frontmatter 付き Markdown にし、少なくとも `id`・`source`・`title`・`url`・`fetched_at` を持たせる。
- 同じ対象を取り直したら上書きしてよい（履歴が必要なら git に任せる）。
- `build_index.py` が `data/*/**/*.md` を `snapshot` 種別として索引に入れるので、vault と一緒に検索できる。
- `vault_index.sqlite` は派生索引。消してもよい（次の検索で作り直される）。
