## vault 運用ルール

`vault/` は日常生活の記録の正本。地図は [README.md](README.md)、キー・型・許容値は [docs/vault-schema.md](../docs/vault-schema.md)（正は `tools/vault/schema.py`）。ここには運用の決まりだけを書く。

### 相談を受けたら最初に

[scopes/life/dashboard.md](scopes/life/dashboard.md)（直近の予定・最近の出来事・続けていること）と `profile/` を読んでから答える。個別の経緯が要るときは `index.md`（古い経緯は frontmatter の `digests`）→ イベントログの順に降りる。

### 新しい対象を扱う前に（必須）

1. scope は `life` だけ。`area`（仕事・趣味・健康…）を [scopes/life/README.md](scopes/life/README.md) の基準で決める。決められなければ本人に確認する。
2. フォルダを作る前に重複・除外チェックを流す。

   ```sh
   uv run tools/vault/check_entity.py --scope life -s "{名称}"
   ```

   | 判定          | すること                                                                                                 |
   | ------------- | -------------------------------------------------------------------------------------------------------- |
   | `[EXCLUDED]`  | 前にやめた・合わなかった理由（台帳なら再開の条件も）を示し、本人が「それでもやる」と言わない限り勧めない |
   | `[EXISTING]`  | 新しいフォルダは作らず、既存の対象にイベントログを足すか、`index.md` に `### 追記: YYYY-MM-DD` で足す    |
   | `[NOT FOUND]` | `_templates/entity.md` から `scopes/life/entities/{key}/index.md` を作る                                 |

3. 調べただけで足切り条件（`criteria.md`）に当たった候補（お店・ジム・教室など）はフォルダを作らず、`triage/{YYYY-MM-DD}_{topic}.md` にバッチ単位でまとめる。`entries` に名称を漏れなく書く（重複チェックが照合する）。

### 書くときの決まり

- **ステータスは frontmatter の `status` だけで表す**。状態が変わってもフォルダを移動しない。`status` を変えたら `status_note`・`updated_at`（終わったなら `close_reason`）も同時に更新する。
- **1件1フォルダ・1回1ファイル**。`index.md` はその対象の最新の要約、1回ごとの出来事（走った・焼いた・行った・相談した）は同じフォルダの `{YYYY-MM-DD}_{kind}.md` に書き、`index.md` の「5. 経過サマリ」に要点とリンクを足す。1回の会話で複数の対象の話が出たら、対象ごとにイベントログを分ける。
- **追記で育てる**。過去の記述は消さず、日付付きの見出しで足す。古くなった要約（`index.md` の「4. 今の状態・所見」・frontmatter）は最新に書き換える。
- **本人が言ったことと推測を分ける**。`verified_items` には本人が言った・繰り返し記録された好みや条件だけを書き、1回だけの印象や AI の推測は `unverified_items`（次に聞くこと）に置く。`evidence_level` はどこまで経験したか。
- **気持ちは本人に聞く**。`interest` は本人に聞いて書き、推測で埋めない。
- **絞り込みに使う値は構造化する**。生活の領域は `area`（enum）、自由な分類は `tags`、頻度は `frequency`、費用は `cost_monthly`（円/月）。enum の欄に自由文を書かない。
- **直近の予定**は `action_type`（`action_required` / `scheduled` / `waiting` / `none`）・`next_action`・`next_due` に書く。終わったら更新する（期限切れは validate が警告する）。
- **参照はキーで書く**。frontmatter にはパスを書かず `contact` などのキーを書く。本文のリンクは相対パス。人から勧められたら、エンティティの `contact` とコンタクトの `introduced` の両方を書く。
- **判断軸を能動的に更新する**。記録をきっかけに本人へ質問し、新しく分かった好み・条件は `profile/`（変わりにくいこと）か `scopes/life/criteria.md`（新しく始めるときの足切り）に書く。
- `visibility: "internal"` のファイル（`criteria.md`・`profile/internal/`）は判断にだけ使い、外に出す文章（人へのメッセージ・予約フォームの備考など）に引用しない。

### 書いた後に（必須）

```sh
uv run tools/vault/validate.py --summary                  # エラー 0 にする
uv run tools/vault/build_dashboard.py --scope life        # dashboard.md の一覧を作り直す
```

`dashboard.md` のマーカー（`<!-- dashboard:begin -->` 〜 `<!-- dashboard:end -->`）の間は手で編集しない。マーカーの外（今のフェーズ・メモ）は手で書く。

### やめたものの圧縮（台帳）

`quit` / `unavailable` / `disliked` になって 14 日以上経ったフォルダと、14 日以上前のトリアージログは `archive.md` に 1 件数行で畳み、元のファイルは消す（詳細は git の履歴に残る）。定期実行はしない。相談や整理のついでに候補を出し、どれを畳むかは本人が決める。

```sh
uv run tools/vault/compact.py list --summary
uv run tools/vault/compact.py draft --scope life --key {key}     # 材料（index.md・イベントログ）のパスと下書き
uv run tools/vault/compact.py apply --scope life --key {key} --reason "..." --reconsider-if "..."
uv run tools/vault/compact.py apply --triage vault/scopes/life/triage/{file}.md
```

- `reason` は「何が合わなかったか」を**条件の言葉で** 1〜2 文（例: 「決まった曜日に縛られる」）。経緯や対象の説明は書かない。`reconsider_if` は「何が変われば再開してよいか」。どちらもイベントログまで読んで AI が下書きし、本人の確認を取ってから `apply` する。
- `apply` は未コミットの変更があるフォルダを拒否するので、先にコミットする。
- 圧縮のたびに「このことで初めて分かった好み・条件」が無いか確かめ、あれば台帳ではなく `profile/` や `criteria.md` への追記を提案する。一般化できる学びを台帳に閉じ込めない。
- 再開することになったら、台帳のエントリを消してから新しいフォルダを作り、`index.md` の「1. きっかけ」に台帳の要約を引き写す（台帳と生きたフォルダに同じキーがあると検証エラー）。

### 続いている対象の古いイベントログの要約（digests）

終わっていない対象（続けている・休止中・終えた）のイベントログのうち、`schema.py` の `EVENT_DIGEST_DAYS` 日より前のものは、`index.md` の frontmatter `digests` に期間ごと 1 エントリで畳み、元のファイルは消す。台帳と同じく定期実行はせず、相談や整理のついでに候補を出し、本人の確認を取ってから `apply` する。

```sh
uv run tools/vault/compact.py list --events --summary
uv run tools/vault/compact.py draft --events --scope life --key {key}     # 材料（index.md・畳むイベントログ）のパスと下書き
uv run tools/vault/compact.py apply --events --scope life --key {key} --digest "..."
```

- `--digest` は件数や日付の羅列ではなく、その期間で「何が分かったか・どう変わったか」を 2〜3 文で書く。
- `apply` の後、`index.md` の本文（「5. 経過サマリ」など）から、消したイベントログへのリンクを外す（残っていると validate が警告する）。
- 畳むたびに、期間をまたいで繰り返し出てきた好み・条件が無いか確かめ、あれば `profile/` や `criteria.md` への追記を提案する。
