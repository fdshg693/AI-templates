## `practice-review` の作業規約

外部の練習相手（ChatGPT など）と行った練習セッションのエクスポートを取り込み、未レビューの分だけを読んでフィードバック・まとめ・次の題材を作る場所。主な用途は外国語の会話練習。学習教材そのものや、練習以外の調査記録はここに置かない。

学習者が最初に開くのは `index.md`（`practice.py refresh` の生成物）。エージェントは作業を始める前に、場面に対応するガイドを読む。

| 場面                                                       | 読む場所                                                                                       |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `inbox/` にファイルが置かれた・「ログを置いた」と言われた  | [guides/ingesting.md](guides/ingesting.md) → 続けて [guides/reviewing.md](guides/reviewing.md) |
| 未レビューのセッションがある・フィードバックを頼まれた     | [guides/reviewing.md](guides/reviewing.md)                                                     |
| lint が `current な feedback` を警告した・まとめを頼まれた | [guides/digesting.md](guides/digesting.md)                                                     |
| 次に何を練習するか聞かれた                                 | [guides/suggesting.md](guides/suggesting.md)                                                   |
| ファイルの書式・状態値・lint エラーの意味を確かめる        | [guides/formats.md](guides/formats.md)                                                         |

## 不変条件

- 読むのは `profile.md`・未レビューのセッション・`current` の出力だけ。レビュー済みのセッションと `superseded` の出力は、学習者が指定したときだけ読む。理由: セッションは増え続け、過去の内容は profile と最新の出力に要約されている → [reviewing.md「守ること」](guides/reviewing.md#守ること)
- 取り込んだセッションの本文は編集しない。理由: 指摘の出典として同じ文面を確かめられるようにする → [formats.md「セッション」](guides/formats.md#セッションsessionsyyyy)
- `status`・`superseded_by`・状態バナー・`index.md` は手で書かず、`practice.py refresh` に書かせる。理由: 古さの判定を1か所（スクリプト）に集め、学習者がバナーだけで読む必要を判断できるようにする → [formats.md「古くなる条件」](guides/formats.md#古くなる条件)
- 1スレッド＝1セッション。同じスレッドの再エクスポートは、重なりを除いてから取り込む → [ingesting.md「同じスレッドの再エクスポート」](guides/ingesting.md#同じスレッドの再エクスポート)
- レビューしたら、同じ作業の中で `profile.md` の `covers_through` を更新する。理由: 次のレビュー・提案は profile だけで過去を把握する → [reviewing.md「手順」](guides/reviewing.md#手順)
- ファイルを作成・更新したら、リポジトリのルートで lint がエラー0で終わることを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

  ```bash
  uv run practice-review/lint_practice_review.py practice-review
  ```

## 同梱スクリプト

リポジトリのルートで実行する。`ingest` と `new` の後は `refresh` が自動で走る。

```bash
uv run practice-review/practice.py ingest  practice-review [--date YYYY-MM-DD]   # inbox → sessions
uv run practice-review/practice.py pending practice-review                       # 未レビューの一覧
uv run practice-review/practice.py new feedback|digest|suggestions practice-review --slug {slug}
uv run practice-review/practice.py refresh practice-review                       # status・バナー・index.md
```

## サンプル

書こうとしているファイルに対応するサンプルだけを読み、書式と粒度をそろえる。`references/` は導入先の `practice-review/` と同じ構造で、2026-10-20 に3件目のセッションを取り込み、まだレビューしていない状態。

| 書くもの                                         | サンプル                                                                                                                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Feedback（`current`）                            | [references/feedback/2026-10-13-job-interview.md](references/feedback/2026-10-13-job-interview.md)                                                                 |
| Feedback（Digest に置き換えられた `superseded`） | [references/feedback/2026-10-06-ordering-coffee.md](references/feedback/2026-10-06-ordering-coffee.md)（本文は作ったときのまま。frontmatter とバナーだけが変わる） |
| Digest                                           | [references/digests/2026-10-10-first-week.md](references/digests/2026-10-10-first-week.md)                                                                         |
| Suggestions                                      | [references/suggestions/2026-10-13-next-topics.md](references/suggestions/2026-10-13-next-topics.md)                                                               |
| profile.md                                       | [references/profile.md](references/profile.md)                                                                                                                     |
| 取り込んだセッション（`unreviewed`）             | [references/sessions/2026/2026-10-20-weekend-plans.md](references/sessions/2026/2026-10-20-weekend-plans.md)（エクスポートの書式の例を兼ねる）                     |
| index.md（生成物）                               | [references/index.md](references/index.md)                                                                                                                         |

## このテンプレートを編集するとき

テンプレート置き場（`core/practice-review/`）で作業するときだけ従う。

- ルールの正本は `guides/`、書式の正本は [guides/formats.md](guides/formats.md)。本ファイルと `references/` にはルールを重複して書かず、リンクにする。
- プレースホルダは `{name}` のように `{}` で書く。
- 状態値・必須の節・しきい値を変えるときは、[guides/formats.md](guides/formats.md) の表と `lint_practice_review.py` の定数（ファイル冒頭の「guides/formats.md の表と同期する」の範囲）を同時に更新する。バナーと index.md の書式は `lint_practice_review.py` の `banner` / `render_index` が正本で、`practice.py` はそれを使う。
- `references/` の出力・セッションは `practice.py` で作ってから本文を埋める（frontmatter とバナーを手で合わせない）。日付を固定するときは `--today` を使う。
- `guides/` / `references/` / スクリプトを変更したら、テンプレート置き場のルートで次を実行し、エラー0・`refresh` の出力なしを確かめる。

  ```bash
  uv run core/practice-review/practice.py refresh core/practice-review/references
  uv run core/practice-review/lint_practice_review.py --examples core/practice-review/references
  ```

## 導入先固有の運用

練習する言語・場面・練習相手は `profile.md` の「練習の設定」に書く。それ以外の導入先固有の運用（エクスポートの方法など）はこの節に書き足す。
