---
template: knowledge-vault
source: references
installed_at: .
extended: []
adapted: [README.md, AGENTS.md, docs/vault-schema.md, tools/vault/schema.py, vault/README.md, vault/AGENTS.md, vault/_templates/entity.md, vault/_templates/event.md]
samples: [vault/scopes/*, vault/profile/*, vault/contacts/*, data/catalog/*]
lint: [uv run tools/vault/validate.py --strict --today 2026-10-20, uv run tools/vault/gen_schema_doc.py --check]
---

# スターター: knowledge-vault-daily-life

[core/knowledge-vault](../../core/knowledge-vault) を、架空の人物「三上 葵」の日常生活の記録に導入し、約 1 年運用した状態（2026-10-20 時点）。本人が AI エージェントに話したことを記録していき、AI が近況・好み・やめたことの理由を把握できるようにする。このファイルはスターターの説明で、架空リポジトリの一部ではない（コピーして使うときは削除してよい）。

## 導入時に決めたこと

[07-adapting.md](../../core/knowledge-vault/guides/07-adapting.md) の「決めること」への答え。書き換えたのは `adapted` に挙げたファイルだけで、CLI（`tools/vault/` の `schema.py` 以外）は core と同一。

| 決めること | このスターターでは |
| --- | --- |
| エンティティ | 続いている関心ごと・活動（ランニング、パン作り、行きつけの店、仕事のプロジェクトなど） |
| scope | `life` の1つ。仕事・趣味などは必須の enum `area` で分け、自由な分類は `tags` |
| ステータス | 続けている / 試し中 / これから / 休止中 → 終えた / やめた / 続けられなくなった / 合わない |
| イベント | 実施記録・訪問・購入・相談・振り返り |
| 構造化値 | `area`・`frequency`・`interest`・`cost_monthly`（ダッシュボードの列は頻度・関心・月額、小見出しは area） |
| コンタクト | おすすめをくれる友人（本・ゲームの紹介元） |
| 圧縮の期間 | 最近の出来事は 14 日、イベントログの要約は 30 日、台帳は終了から 14 日 |

## references より複雑な点

| 状況 | ファイル |
| ---- | -------- |
| 直近 14 日の出来事が、対象をまたいで新しい順に並ぶ | [dashboard.md](vault/scopes/life/dashboard.md) の「最近の出来事」 |
| 古いイベントログを要約に畳んだ後、直近のログだけが残っている | [running](vault/scopes/life/entities/running/index.md)（`digests` 2件 ＋ 直近3件） |
| 30 日を過ぎて要約に畳める状態のログ（まだ畳んでいない） | [sourdough](vault/scopes/life/entities/sourdough/index.md) の 3 件、[boardgame-meetup](vault/scopes/life/entities/boardgame-meetup/index.md) の 1 件 |
| 区切りがついた対象が、台帳ではなく要約だけ持って残る | [lp-renewal-kitano](vault/scopes/life/entities/lp-renewal-kitano/index.md)（`finished`、イベントログなし） |
| 休止中で、再開を決める期限だけがある | [english-podcast](vault/scopes/life/entities/english-podcast/index.md) |
| やめて 14 日以上経ち、台帳に畳める | [balcony-garden](vault/scopes/life/entities/balcony-garden/index.md) |
| やめた理由の台帳が、新しい候補の足切りに効く | [archive.md](vault/scopes/life/archive.md) の「ホットヨガ」→ [triage](vault/scopes/life/triage/2026-10-16_gyms.md) |
| 圧縮のたびに、繰り返し出た傾向を半固定の profile に昇格させた | [preferences.md](vault/profile/preferences.md) の更新履歴（digests・台帳・振り返りが根拠） |
| 1 回だけの発言は profile に上げず、エンティティに留めている | [galaxy-route-series](vault/scopes/life/entities/galaxy-route-series/index.md)・[boardgame-meetup の 10/18](vault/scopes/life/entities/boardgame-meetup/2026-10-18_visit.md) |
| 予定どうしの衝突を記録して調整した | [running](vault/scopes/life/entities/running/index.md) の大会と [boardgame-meetup](vault/scopes/life/entities/boardgame-meetup/index.md) の 11 月の会 |
| 外に出さない背景（評価面談・睡眠） | [profile/internal/notes.md](vault/profile/internal/notes.md) |

## 使い方

1. このフォルダをテンプレート集の外へコピーし、`git init` して最初のコミットをする（圧縮は `git rm` を使う）。
2. コピー先のルートで検査を実行し、エラー 0 を確かめる。サンプルの日付は 2026-10-20 時点なので `--today` を付ける。

   ```bash
   uv run tools/vault/validate.py --summary --strict --today 2026-10-20
   uv run tools/vault/build_dashboard.py --all --today 2026-10-20
   ```

3. 次のような話をエージェントにして、テンプレートの運用どおりに進むかを試す。
   - 「最近どう過ごしてた？」→ ダッシュボードの「最近の出来事」と profile を読んで答える（イベントログを片端から開かない）
   - 「今日 5 km 走った。ふくらはぎの張りはもう無い」→ `running` にイベントログを足し、`unverified_items` の張りの件を解消する
   - 「趣味のことだけ振り返りたい」→ `build_index.py --where area=hobby` で引く
   - 「ちょっと整理しよう」→ `compact.py list` と `list --events` で候補を出し、`sourdough` の古いログを `digests` に、`balcony-garden` を台帳に畳む（本人確認の後）。畳んだ後に profile へ上げる傾向が無いか確かめる
   - 「ホットヨガ、また行ってみようかな」→ `check_entity.py` が `[EXCLUDED]` を返し、台帳の理由を示す
   - 「料理教室に行きたい」→ 台帳の再検討の条件（単発・振替自由）を示し、その条件に合う候補かを確かめる
