## `threads` の作業規約

複数のプランにまたがる変更を「スレッド」単位で束ね、所属プラン・予定順・実行中に判明した事実・仕様変更・手戻りの経緯を残す場所。プランそのもの（実装手順）は `planning/`（plans テンプレート）に書き、スレッドには書かない。

作業を始める前に、場面に対応するファイルを読む。

| 場面 | 読む場所 |
| ---- | -------- |
| 複数プランにまたがる作業を始める・スレッドを立てるか決める | [guides/thread-writing.md](guides/thread-writing.md)（書式の正本） |
| 所属プランの実行中に、事実の発覚・仕様変更・手戻り・プランの追加・順序変更が起きた | [guides/thread-updating.md](guides/thread-updating.md) |
| 所属プランがすべて完了した・作業をやめる（`closed` / `abandoned`） | [guides/thread-closing.md](guides/thread-closing.md) |
| プランを書く・実行する（スレッドに所属するかどうかによらない） | [planning/AGENTS.md](planning/AGENTS.md) の場面表 |

`planning/` は plans テンプレートをそのまま置いたもの。plans のガイドとコマンドに出てくる `plans/` は `threads/planning/` と読み替える（例: `uv run threads/planning/snapshot_plan.py threads/planning/{plan-name}`）。

## 不変条件

- スレッドの `plans:` とプランの `thread:` は対で更新する。理由: 片側だけだと所属が辿れない → [thread-writing.md「所属プラン側」](guides/thread-writing.md#所属プラン側)
- スレッドの `status` は `open` / `paused` / `closed` / `abandoned` だけを使う → [thread-writing.md「00-thread.md」](guides/thread-writing.md#00-threadmd)
- `log.md` は追記のみ。過去のエントリを書き換えない。理由: 手戻りの原因を後から辿れなくなる → [thread-writing.md「log.md」](guides/thread-writing.md#logmd)
- 予定外の事実は、`log.md` に書く前に影響する所属プランの本文へ直接反映する（plans の不変条件を維持） → [thread-updating.md](guides/thread-updating.md#何をどこに書くか)
- スレッドに実装手順を書かない。理由: 実装の正本はプラン → [thread-writing.md「手順」](guides/thread-writing.md#手順)
- スレッドが `open` / `paused` の間は、所属プランが完了しても削除しない（plans の「完了後の後片付け」より優先） → [thread-updating.md](guides/thread-updating.md#スレッドが-open--paused-の間の追加ルール)
- スレッド・所属プランを作成・更新したら、リポジトリのルートで次がエラー0で終わることを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

  ```bash
  uv run threads/lint_threads.py threads
  uv run threads/planning/lint_plans.py threads/planning
  ```

## サンプル

書こうとしているファイルに対応するサンプルだけを読み、書式と粒度をそろえる。`references/` は導入先の `threads/` と同じ構造。

| 書くもの | サンプル |
| -------- | -------- |
| `00-thread.md`（`plans:`・`プラン一覧`・`（未作成）` 行） | [references/topics/article-scheduled-publishing/00-thread.md](references/topics/article-scheduled-publishing/00-thread.md) |
| `log.md` のエントリ（計画・発見・仕様変更・手戻り・順序変更） | [references/topics/article-scheduled-publishing/log.md](references/topics/article-scheduled-publishing/log.md) |
| 所属プラン（フォルダ方式。完了済みだが `open` の間は残す） | [references/planning/article-publish-state/00-overview.md](references/planning/article-publish-state/00-overview.md) |
| 手戻りで追加した所属プラン（単一ファイル完結） | [references/planning/publish-at-utc.md](references/planning/publish-at-utc.md) |

記入例はすべて `open` の状態。`closed` / `abandoned` の書き方（`[完了]` エントリ、`plans: []`）は [thread-closing.md](guides/thread-closing.md) の手順どおりに読み替える。

## このテンプレートを編集するとき

テンプレート置き場（`core/threads/`）で作業するときだけ従う。

- ルールの正本は `guides/`。本ファイルと `references/` にはルールを重複して書かず、リンクにする。プランのルールは plans の guides が正本で、threads のガイドに再掲しない。
- `core/threads/planning/` は `core/plans` への Junction（POSIX ではシンボリックリンク）で、`.gitignore` で追跡から外している。正本は `core/plans`。Junction 経由で編集しても `core/plans` のファイルが変わるので、threads の作業中は `planning/` の中を編集しない。無い・壊れているときはテンプレート置き場のルートで `uv run core/threads/link_plans.py` を実行する。
- 所属プランの記入例は `references/planning/`（実体のフォルダ）に置く。`core/plans/references/` には `thread:` 付きの例を足さない。
- プレースホルダは `{name}` のように `{}` で書く。
- 次の組は同時に更新する: [thread-writing.md](guides/thread-writing.md) の `status` の表 ⇔ `lint_threads.py` の `THREAD_STATUSES`、必須見出しの表 ⇔ `THREAD_SECTIONS`、種別の表 ⇔ `LOG_KINDS`。
- `guides/` / `references/` / `lint_threads.py` を変更したら、テンプレート置き場のルートで次を実行する。

  ```bash
  uv run core/threads/lint_threads.py --examples core/threads/references
  uv run core/plans/lint_plans.py --examples core/threads/references/planning
  ```

## 導入先固有の運用

スレッドを立てる人・クローズを判断する人など、導入先固有の運用はこの節に書き足す。プランに関する導入先固有の運用は `planning/AGENTS.md` の同名の節に書く。
