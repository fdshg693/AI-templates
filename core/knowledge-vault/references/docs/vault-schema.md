<!-- 自動生成ファイル: tools/vault/gen_schema_doc.py が tools/vault/schema.py から生成する。手で編集しない -->

# vault フロントマタースキーマ

正（SSOT）は [`tools/vault/schema.py`](../tools/vault/schema.py)。スキーマを変えたら
`uv run tools/vault/gen_schema_doc.py` でこの文書を再生成する。

- 未知のキーはエラー。空文字は未記入と同じ扱い。日付は `YYYY-MM-DD`。
- 「必須」でないキーは省略してよい。

## entity: エンティティ（1件1フォルダの index.md）

- 配置: `vault/scopes/*/entities/*/index.md`
- `key` は配置フォルダ名と一致させる
- `scope` は配置先 scope と一致させる

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `title` | str | ✓ | 正式名称 |
| `key` | str（`^[a-z0-9]+(?:-[a-z0-9]+)*$`） | ✓ | kebab-case のキー。フォルダ名と一致させる |
| `aliases` | list[str] |  | 別名・略称・表記ゆれ（重複チェックの照合に使う） |
| `scope` | enum: `work` / `personal` | ✓ | 区分 |
| `status` | enum: `trialing` / `evaluating` / `researching` / `on_hold` / `adopted` / `dropped` / `blocked` / `blacklisted` | ✓ | 現在の状態 |
| `status_note` | str |  | 状態の補足（今どこで止まっているか） |
| `close_reason` | str |  | 終了・除外した理由（closed / excluded のとき必須） |
| `date` | date | ✓ | 初回記録日 |
| `updated_at` | date | ✓ | 最終更新日 |
| `tags` | list[str] |  | 検索用タグ |
| `url` | str |  | 主となる参照先 URL |
| `sources` | list[str] |  | 参照した情報源 |
| `evidence_level` | enum: `listing` / `reviews` / `web` / `firsthand` |  | どこまで確かめたか |
| `verified_items` | list[str] |  | 確認できた事項 |
| `unverified_items` | list[str] |  | 未検証・今後確かめる事項 |
| `score_min` | int（0〜100） |  | 適合度の下限（0〜100） |
| `score_max` | int（0〜100） |  | 適合度の上限（0〜100） |
| `score_summary` | str |  | 適合度の要約と、幅の理由 |
| `interest` | int（1〜5） |  | 本人の関心度（1〜5）。AI が推測で埋めない |
| `cost_min` | int（0〜） |  | 月額費用の下限（円） |
| `cost_max` | int（0〜） |  | 月額費用の上限（円）。上限なしは未記入 |
| `cost_note` | str |  | 費用の補足（年払い割引・席数課金 等） |
| `contact` | str（`^[a-z0-9]+(?:-[a-z0-9]+)*(?:_[a-z0-9]+(?:-[a-z0-9]+)*)+$`） |  | 紹介元の contact-key（パスは書かない） |
| `action_type` | enum: `none` / `action_required` / `scheduled` / `waiting` |  | 直近アクションの種類 |
| `next_action` | str |  | 直近アクションの内容 |
| `next_due` | due |  | 期限・予定日時（YYYY-MM-DD / YYYY-MM-DD HH:MM） |
| `digests` | list[object] |  | 要約に畳んだ古いイベントログ（compact.py --events が追記する） |

`digests` の要素:

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `from` | date | ✓ | 畳んだ期間の最初のイベントの日付 |
| `to` | date | ✓ | 畳んだ期間の最後のイベントの日付 |
| `count` | int（1〜） | ✓ | 畳んだイベントログの件数 |
| `summary` | str（200 文字以内） | ✓ | その期間の傾向（2〜3 文） |

## event: イベントログ（1回1ファイル）

- 配置: `vault/scopes/*/entities/*/????-??-??_*.md`, `vault/contacts/*/????-??-??_*.md`
- ファイル名は `{YYYY-MM-DD}_{kind}.md`。`date` / `kind` と一致させる

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `date` | date | ✓ | 実施日。ファイル名の日付と一致させる |
| `kind` | enum: `note` / `meeting` / `trial` / `review` / `retro` | ✓ | 種類。ファイル名の後半と一致させる |
| `title` | str |  | 表示名（標準ラベルから変えたいときだけ） |
| `result` | enum: `pending` / `positive` / `negative` / `not_applicable` |  | その回の結果 |
| `participants` | list[str] |  | 参加者・相手 |
| `updated_at` | date | ✓ | 最終更新日 |
| `tags` | list[str] |  | 検索用タグ |

## contact: コンタクト（情報をくれる人・経路。scope 横断）

- 配置: `vault/contacts/*/index.md`
- `contact_key` は配置フォルダ名と一致させる

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `name` | str | ✓ | 氏名・表示名 |
| `contact_key` | str（`^[a-z0-9]+(?:-[a-z0-9]+)*(?:_[a-z0-9]+(?:-[a-z0-9]+)*)+$`） | ✓ | {org}_{name} 形式。フォルダ名と一致させる |
| `org` | str |  | 所属 |
| `scopes` | list[str] |  | 関わる scope |
| `status` | enum: `active` / `trusted` / `declined` / `blacklisted` | ✓ | 関係の状態 |
| `rating` | enum: `S` / `A` / `B` / `C` / `D` |  | 情報源としての評価 |
| `introduced` | list[object] |  | 紹介されたエンティティ |
| `first_contact` | date | ✓ | 初回接触日 |
| `updated_at` | date | ✓ | 最終更新日 |
| `tags` | list[str] |  | 検索用タグ |

`introduced` の要素:

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `name` | str | ✓ | 名称 |
| `key` | str（`^[a-z0-9]+(?:-[a-z0-9]+)*$`） |  | エンティティのキー（ログがあれば） |
| `date` | date |  | 紹介日 |
| `note` | str |  | ログを作らなかった紹介の所感 |

## triage: トリアージ集約ログ（早期打ち切りをバッチ単位で1ファイル）

- 配置: `vault/scopes/*/triage/*.md`
- `scope` は配置先 scope と一致させる

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `date` | date | ✓ | 実施日 |
| `scope` | enum: `work` / `personal` | ✓ | 区分 |
| `topic` | str | ✓ | このバッチで何を見たか |
| `entries` | list[object] | ✓ | 打ち切った対象（check_entity が照合する） |
| `updated_at` | date | ✓ | 最終更新日 |
| `tags` | list[str] |  | 検索用タグ |

`entries` の要素:

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `name` | str | ✓ | 名称 |
| `aliases` | list[str] |  | 別名 |
| `reason` | str | ✓ | 打ち切った理由（条件の言葉で） |

## archive: 見送り台帳（終了したエンティティを 1 件数行に圧縮）

- 配置: `vault/scopes/*/archive.md`
- `scope` は配置先 scope と一致させる

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `scope` | enum: `work` / `personal` | ✓ | 区分 |
| `entries` | list[object] |  | 圧縮したエンティティ |
| `updated_at` | date | ✓ | 最終更新日 |
| `tags` | list[str] |  | 検索用タグ |

`entries` の要素:

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `name` | str | ✓ | 名称 |
| `key` | str（`^[a-z0-9]+(?:-[a-z0-9]+)*$`） |  | 元のキー（トリアージ由来なら無し） |
| `aliases` | list[str] |  | 別名 |
| `status` | enum: `dropped` / `blocked` / `blacklisted` / `discarded` | ✓ | 元の status |
| `closed_at` | date | ✓ | 終了日 |
| `reason` | str（120 文字以内） | ✓ | 何が合わなかったか（条件の言葉で 1〜2 文） |
| `reconsider_if` | str |  | 何が変われば再検討してよいか |
| `contact` | str（`^[a-z0-9]+(?:-[a-z0-9]+)*(?:_[a-z0-9]+(?:-[a-z0-9]+)*)+$`） |  | 紹介元の contact-key |

## dashboard: ダッシュボード（一覧はマーカー間を自動生成）

- 配置: `vault/scopes/*/dashboard.md`
- `scope` は配置先 scope と一致させる

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `scope` | enum: `work` / `personal` | ✓ | 区分 |
| `updated_at` | date | ✓ | 最終更新日 |
| `tags` | list[str] |  | 検索用タグ |

## note: ノート（判断軸・条件など、上記以外の frontmatter 付き文書）

- 配置: `vault/profile/**/*.md`, `vault/scopes/*/README.md`, `vault/scopes/*/criteria.md`
- source_file を書いた文書は、派生元の updated_at が source_updated_at より新しいと警告になる（同期漏れ）。

| キー | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `title` | str | ✓ | 表題 |
| `visibility` | enum: `public` / `internal` | ✓ | 公開範囲 |
| `updated_at` | date | ✓ | 最終更新日 |
| `tags` | list[str] |  | 検索用タグ |
| `source_file` | str |  | 派生（翻訳・要約）元のファイル。リポジトリルート相対 |
| `source_updated_at` | date |  | 派生元の updated_at（同期した時点の値） |

## entity の status

| 値 | ラベル | 分類 | 並び順 | 除外範囲 | 意味 |
| --- | --- | --- | --- | --- | --- |
| `trialing` | 試用中 | active | 0 | none | 実際に使って確かめている |
| `evaluating` | 比較検討中 | active | 1 | none | 調査済みで、試すか検討中 |
| `researching` | 調査中 | active | 2 | none | 調査に着手したばかり・未検証 |
| `on_hold` | 保留 | active | 3 | none | 時期待ち等で一時停止 |
| `adopted` | 採用 | closed | 10 | none | 採用した（検討終了） |
| `dropped` | 見送り | closed | 11 | same_scope | 自分の判断で見送った |
| `blocked` | 不可 | closed | 12 | same_scope | 外部要因で使えなかった |
| `blacklisted` | 除外 | excluded | 20 | all_scopes | 二度と検討しない |
