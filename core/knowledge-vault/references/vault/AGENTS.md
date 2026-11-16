## vault 運用ルール

`vault/` は情報の正本。地図は [README.md](README.md)、キー・型・許容値は [docs/vault-schema.md](../docs/vault-schema.md)（正は `tools/vault/schema.py`）。ここには運用の決まりだけを書く。

### 相談を受けたら最初に

関係する scope の `dashboard.md`（直近アクション・最近の出来事・進行中の一覧）と `profile/` を読んでから答える。個別の経緯が要るときは `index.md`（古い経緯は frontmatter の `digests`）→ イベントログの順に降りる。

### 新しい対象を扱う前に（必須）

1. どの scope に入るかを各 scope の `README.md` の判定基準で決める。決められなければ本人に確認する。
2. 調査に着手する前に重複・除外チェックを流す。

   ```sh
   uv run tools/vault/check_entity.py --scope {scope} -s "{名称}"
   ```

   | 判定 | すること |
   | --- | --- |
   | `[EXCLUDED]` | 過去の理由（台帳なら再検討の条件も）を示し、本人が再検討を指示しない限り調べ直さない |
   | `[OTHER SCOPE]` | 別 scope の記録を参考として示し、この scope の条件で改めて判断する |
   | `[EXISTING]` | 新しいフォルダは作らず、既存 `index.md` に `### 追記: YYYY-MM-DD` で足す |
   | `[NOT FOUND]` | `_templates/entity.md` から `scopes/{scope}/entities/{key}/index.md` を作る |

3. 公開情報だけで足切り条件（`criteria.md`）に当たったものはフォルダを作らず、`triage/{YYYY-MM-DD}_{topic}.md` にバッチ単位でまとめる。`entries` に名称を漏れなく書く（重複チェックが照合する）。

### 書くときの決まり

- **ステータスは frontmatter の `status` だけで表す**。状態が変わってもフォルダを移動しない。`status` を変えたら `status_note`・`updated_at`（終了なら `close_reason`）も同時に更新する。
- **1件1フォルダ・1回1ファイル**。`index.md` は最新の要約、打ち合わせ・試用などの一次情報は同じフォルダの `{YYYY-MM-DD}_{kind}.md` に書き、`index.md` の「5. 経過サマリ」に要点とリンクを足す。
- **追記で育てる**。過去の記述は消さず、日付付きの見出しで足す。古くなった要約（`index.md` の結論・frontmatter）は最新に書き換える。
- **何をどこまで確かめたかを書く**。`evidence_level`・`verified_items`・`unverified_items` を埋め、事実と推測を分ける。調査を途中で打ち切ったら「〜を理由に詳細調査はスキップ」と根拠を残す。
- **評価は幅で書く**。`score_min` / `score_max` は一次情報で確かめるまで同じ値にしない。幅の理由は `score_summary`。本人の気持ち（`interest`）は本人に聞いて書き、推測で埋めない。
- **絞り込みに使う値は構造化する**。数値は単位を揃えた整数（費用は円/月）、分類は enum、補足は `*_note` に書く。enum の欄に自由文を書かない。
- **直近の動き**は `action_type`（`action_required` / `scheduled` / `waiting` / `none`）・`next_action`・`next_due` に書く。終わったら更新する（期限切れは validate が警告する）。
- **参照はキーで書く**。frontmatter にはパスを書かず `contact` などのキーを書く。本文のリンクは相対パス。紹介を受けたら、エンティティの `contact` とコンタクトの `introduced` の両方を書く。
- **判断軸を能動的に更新する**。記録をきっかけに本人へ質問し、新しく分かった好み・条件は scope 共通なら `profile/`、scope 固有なら `scopes/{scope}/criteria.md` に書く。迷ったら scope 側に置く。
- **派生文書**（`profile/en/` など）は正本を先に直し、派生側を同期して `source_updated_at` を正本の `updated_at` に合わせる。
- `visibility: "internal"` のファイル（`criteria.md`・`profile/internal/`）は判断にだけ使い、外部に出す文章（問い合わせ・社外向け資料など）に引用しない。

### 書いた後に（必須）

```sh
uv run tools/vault/validate.py --summary                  # エラー 0 にする
uv run tools/vault/build_dashboard.py --scope {scope}     # dashboard.md の一覧を作り直す
```

`dashboard.md` のマーカー（`<!-- dashboard:begin -->` 〜 `<!-- dashboard:end -->`）の間は手で編集しない。マーカーの外（フェーズ・メモ）は手で書く。

### 終わったものの圧縮（見送り台帳）

`dropped` / `blocked` / `blacklisted` になって 14 日以上経ったフォルダと、14 日以上前のトリアージログは `archive.md` に 1 件数行で畳み、元のファイルは消す（詳細は git の履歴に残る）。定期実行はしない。相談や整理のついでに候補を出し、どれを畳むかは本人が決める。

```sh
uv run tools/vault/compact.py list --summary
uv run tools/vault/compact.py draft --scope {scope} --key {key}     # 材料（index.md・イベントログ）のパスと下書き
uv run tools/vault/compact.py apply --scope {scope} --key {key} --reason "..." --reconsider-if "..."
uv run tools/vault/compact.py apply --triage vault/scopes/{scope}/triage/{file}.md
```

- `reason` は「何が合わなかったか」を**条件の言葉で** 1〜2 文（例: 「SSO が無い」）。経緯や対象の説明は書かない。`reconsider_if` は「何が変われば再検討してよいか」。どちらもイベントログまで読んで AI が下書きし、本人の確認を取ってから `apply` する。
- `apply` は未コミットの変更があるフォルダを拒否するので、先にコミットする。
- 圧縮のたびに「この見送りで初めて分かった条件」が無いか確かめ、あれば台帳ではなく `profile/` や `criteria.md` への追記を提案する。一般化できる学びを台帳に閉じ込めない。
- 再検討することになったら、台帳のエントリを消してから新しいフォルダを作り、`index.md` の「1. 依頼・きっかけ」に台帳の要約を引き写す（台帳と生きたフォルダに同じキーがあると検証エラー）。

### 続いている対象の古いイベントログの要約（digests）

終わっていない対象のイベントログのうち、`schema.py` の `EVENT_DIGEST_DAYS` 日より前のものは、`index.md` の frontmatter `digests` に期間ごと 1 エントリで畳み、元のファイルは消す。台帳と同じく定期実行はせず、相談や整理のついでに候補を出し、本人の確認を取ってから `apply` する。

```sh
uv run tools/vault/compact.py list --events --summary
uv run tools/vault/compact.py draft --events --scope {scope} --key {key}     # 材料（index.md・畳むイベントログ）のパスと下書き
uv run tools/vault/compact.py apply --events --scope {scope} --key {key} --digest "..."
```

- `--digest` は件数や日付の羅列ではなく、その期間で「何が分かったか・どう変わったか」を 2〜3 文で書く。
- `apply` の後、`index.md` の本文（「5. 経過サマリ」など）から、消したイベントログへのリンクを外す（残っていると validate が警告する）。
- 畳むたびに、期間をまたいで繰り返し出てきた好み・条件が無いか確かめ、あれば `profile/` や `criteria.md` への追記を提案する。
