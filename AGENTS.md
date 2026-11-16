@./README.md

## このフォルダだけを開いたとき

アンブレラ（fdshg693/AI）の `templates/` として clone されている前提。共通の手順（Junction・フックの作り方、`_umbrella/` の扱い、2 段階コミット）は [repo-layout](../maintenance/docs/repo-layout.md#サブモジュールを単体で開く)。

- `plans/` はアンブレラの `plans/` への Junction。作成・変更したプランはアンブレラに属する。テンプレートとしての plans の正本は `core/plans/`。
- `core/threads/planning` は `core/plans` への Junction で、アンブレラのルートで `just links-sync` を実行すると作られる。単体で clone した場合は `uv run core/threads/link_plans.py` を 1 回実行する。
