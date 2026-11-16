# ファイルの書式

このフォルダのファイルを作る・直すとき、または lint のエラーの意味を確かめるときに読む。ここにある表が書式の正本で、`lint_practice_review.py` の定数（`SESSION_STATUSES` / `OUTPUT_KINDS` / `PROFILE_SECTIONS` / `MIN_SUGGESTIONS` / `MAX_SESSIONS_PER_FEEDBACK` / `DIGEST_AFTER` / `FILL_MARK`）と同期している。

## フォルダ構成

```text
practice-review/
├── AGENTS.md / CLAUDE.md
├── index.md          # ダッシュボード。practice.py refresh が生成する（手で編集しない）
├── profile.md        # 学習者プロフィール。レビューのたびに更新する
├── inbox/            # 練習相手からエクスポートしたファイルを、そのまま置く場所
├── sessions/YYYY/    # 取り込んだセッション（Session）
├── feedback/         # セッションごとの指摘（Feedback）
├── digests/          # 複数の Feedback のまとめ（Digest）
└── suggestions/      # 次の練習の題材（Suggestions）
```

ファイル名は、`index.md`・`profile.md` 以外はすべて `YYYY-MM-DD-{slug}.md` にする。日付は、セッションなら練習した日、出力なら作った日（`generated_at`）。`{slug}` は英小文字・数字・ハイフン（`practice.py` が付ける）。ファイル名だけで、いつのものかが分かるようにするため。

## セッション（`sessions/YYYY/`）

`practice.py ingest` が作る。エクスポートした本文は frontmatter の下にそのまま置き、取り込んだ後は本文を編集しない（指摘の出典として、後から同じ文面を確かめられるようにするため）。

| キー | 値 |
| ---- | -- |
| `type` | `Session` 固定 |
| `status` | 下の表の値 |
| `date` | 練習した日 `YYYY-MM-DD`。ファイル名の日付・フォルダの年と同じ |
| `title` | エクスポートの最初の `#` 見出し（無ければ元のファイル名） |
| `source` | 練習相手・ツール（例: `chatgpt`） |
| `reviewed_in` | レビューした Feedback のファイル名（拡張子なし）。未レビューなら空 |

| `status` | 意味 |
| -------- | ---- |
| `unreviewed` | まだ Feedback に反映していない。次のレビューの対象 |
| `reviewed` | `reviewed_in` の Feedback で扱った。以後は読まない |

## 出力（`feedback/` `digests/` `suggestions/`）

`practice.py new` が雛形を作る。`（記入）` をすべて埋めたら完成。

| キー | 値 |
| ---- | -- |
| `type` | `Feedback` / `Digest` / `Suggestions`（フォルダで決まる） |
| `status` | `current`（最新）/ `superseded`（古い）。`practice.py refresh` が下の条件で書き換える |
| `generated_at` | 作った日 `YYYY-MM-DD` |
| `covers_through` | どの日のセッションまで反映したか。`generated_at` 以前の日付 |
| `sessions` | Feedback だけ。対象セッションのファイル名のリスト `[a, b]`。1ファイル5件まで |
| `superseded_by` | 置き換えた出力のファイル名。`current` なら空 |

### 古くなる条件

| 種類 | `superseded` になる条件 | `superseded_by` |
| ---- | ----------------------- | --------------- |
| Digest | 後から別の Digest が作られた | 次に作られた Digest |
| Suggestions | 後から別の Suggestions が作られた | 次に作られた Suggestions |
| Feedback | 同じ日以降に作られ、`covers_through` が同じかそれより後の Digest がある（指摘がまとめに吸収された） | その条件を満たす最初の Digest |

`superseded_by` を「次の版」にするのは、一度古くなったファイルを後から書き換えずに済ませるため。最新版は `index.md` で分かる。

### 状態バナー

frontmatter の直後の最初の行に、状態を1行で書く（実物は [references の Feedback](../references/feedback/2026-10-06-ordering-coffee.md)）。`practice.py refresh` が書くので、手で書かない。ファイルを開いた人が本文を読む前に、読む必要があるかを判断できるようにするため。

- 最新: `> 状態: 最新 ／ 生成 2026-10-13 ／ 2026-10-12 までのセッションを反映`
- 古い: `> 状態: 古い ／ 生成 2026-10-06 ／ （次の版へのリンク） に置き換え済み。読み返さなくてよい（最新は （index.md へのリンク））`

### 本文の節

`#` 見出しは雛形のまま（「フィードバック 2026-10-13」など）。次の `##` 見出しをこの順に置く。

| 種類 | `##` 見出し | 書くこと |
| ---- | ----------- | -------- |
| Feedback | `要点` | 次の練習で真っ先に気をつけること。3項目まで |
| | `直すところ` | 表「言ったこと ｜ 直し ｜ ポイント ｜ 出典」。学習者の発言の誤り・不自然な言い方だけ。8行まで、`profile.md` の「繰り返している誤り」にあるものを優先する。出典はセッションへのリンク（2行目以降の同じ出典は「同上」でよい） |
| | `取り入れたい表現` | 表「表現 ｜ 意味・使う場面 ｜ 例文」。練習相手が使った表現、または学習者が言いたかったことの自然な言い方。5行まで |
| Digest | `要点` | 対象期間を通して気をつけること。3項目まで |
| | `繰り返している誤り` | 表「パターン ｜ 回数 ｜ 例 → 直し」。個々の誤りではなく、型でまとめる |
| | `定着させたい表現` | 表「表現 ｜ 例文」 |
| Suggestions | `提案` | 題材ごとに `###` 見出し。2つ以上。各題材に「ねらい」「使ってみる表現」「練習相手への最初のメッセージ」（コードブロック）を書く |

Feedback では、`sessions` に挙げたセッションすべてに本文からリンクする（指摘の根拠を辿れるようにするため）。

## 学習者プロフィール（`profile.md`）

全セッションを読み返さずに、学習者の状態を把握するための要約。エージェントは、レビュー・まとめ・提案の前に必ずこれを読む。

| キー | 値 |
| ---- | -- |
| `type` | `Profile` 固定 |
| `updated_at` | 最後に更新した日 |
| `covers_through` | どの日のセッションまで反映したか。レビュー済みの最新のセッションの日付以上（未レビューしかなければ空） |

| `##` 見出し | 書くこと |
| ----------- | -------- |
| `練習の設定` | 練習するもの（言語・場面）、練習相手、フィードバックに使う言語、学習者の母語。導入時に書く |
| `目標とレベル` | 期限付きの目標と、現在のレベル（いつ時点かを書く） |
| `繰り返している誤り` | 表「パターン ｜ 回数 ｜ 最後に出た ｜ 例 → 直し」 |
| `定着した表現` | 「取り入れたい表現」に挙げたもののうち、後のセッションで学習者が正しく使えたもの |

## ダッシュボード（`index.md`）

`practice.py refresh` が生成する（`ingest` と `new` の後にも自動で走る）。`current` の出力、未レビューのセッション、古い出力の件数を載せる。学習者が最初に開くファイル。手で書き換えると lint がエラーにする。

## しきい値

| 定数 | 値 | 意味 |
| ---- | -- | ---- |
| `MAX_SESSIONS_PER_FEEDBACK` | 5 | 1つの Feedback で扱うセッションの上限 |
| `DIGEST_AFTER` | 3 | `current` の Feedback がこの件数以上になったら Digest を作る（lint が警告する） |
| `MIN_SUGGESTIONS` | 2 | Suggestions の題材の最小数 |
| `FILL_MARK` | `（記入）` | 雛形の記入欄。残っていると lint がエラーにする |
