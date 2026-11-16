# フォルダ構成とドキュメント種別

[01-philosophy.md](01-philosophy.md) の原則を、具体的な配置に落とす。`references/` はコピー先のリポジトリと同じ構造なので、ここに出てくるパスはそのままコピー先のパスになる。

## 全体

```
（リポジトリルート）
├── AGENTS.md / CLAUDE.md / README.md
├── vault/                          # 正本
│   ├── AGENTS.md / CLAUDE.md       # vault の運用ルール
│   ├── README.md                   # データの地図
│   ├── profile/                    # scope 共通の情報（判断軸・本音メモ・派生翻訳）
│   ├── scopes/{scope}/             # 区分ごとに同じ構造
│   │   ├── README.md / criteria.md / dashboard.md / archive.md
│   │   ├── entities/{key}/         # index.md ＋ {YYYY-MM-DD}_{kind}.md
│   │   └── triage/                 # {YYYY-MM-DD}_{topic}.md
│   ├── contacts/{key}/             # scope 横断（人・情報源）
│   └── _templates/                 # 新規ファイルの雛形（検証対象外）
├── data/{source}/                  # 外部スナップショット
├── data/vault_index.sqlite         # 派生索引（git 管理外）
├── docs/vault-schema.md            # スキーマ一覧（生成物）
└── tools/vault/                    # schema.py ＋ CLI
```

## ドキュメント種別

種別と配置パス（glob）の対応の正本は `schema.py` の `KINDS`。下表はその要約。

| 種別      | 配置                                                                             | 役割                                                      | サンプル                                                                                       |
| --------- | -------------------------------------------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| entity    | `scopes/{scope}/entities/{key}/index.md`                                         | 1対象の最新の要約・調査・結論                             | [acme-notes/index.md](../references/vault/scopes/work/entities/acme-notes/index.md)            |
| event     | `entities/{key}/{YYYY-MM-DD}_{kind}.md`、`contacts/{key}/{YYYY-MM-DD}_{kind}.md` | 1回の出来事の一次情報                                     | [2026-10-05_trial.md](../references/vault/scopes/work/entities/acme-notes/2026-10-05_trial.md) |
| contact   | `contacts/{key}/index.md`                                                        | 情報をくれる人・経路の評価と、紹介された対象の一覧        | [vendor_sato-hanako](../references/vault/contacts/vendor_sato-hanako/index.md)                 |
| triage    | `scopes/{scope}/triage/{YYYY-MM-DD}_{topic}.md`                                  | 一次スクリーニングで打ち切った対象をバッチ単位で1ファイル | [2026-09-20_note-apps.md](../references/vault/scopes/work/triage/2026-09-20_note-apps.md)      |
| archive   | `scopes/{scope}/archive.md`                                                      | 終了した対象の台帳（1件数行）                             | [archive.md](../references/vault/scopes/work/archive.md)                                       |
| dashboard | `scopes/{scope}/dashboard.md`                                                    | 一覧（自動生成）＋手書きのフェーズ・メモ                  | [dashboard.md](../references/vault/scopes/work/dashboard.md)                                   |
| note      | `profile/**`、`scopes/*/README.md`、`scopes/*/criteria.md`                       | 判断軸・条件など。`visibility` 必須                       | [preferences.md](../references/vault/profile/preferences.md)                                   |

## 三層構造（一覧 → 要約 → 一次情報）

| 層       | ファイル                  | 粒度                                        | 誰が更新するか                                           |
| -------- | ------------------------- | ------------------------------------------- | -------------------------------------------------------- |
| 一覧     | `dashboard.md`            | 全対象を1行ずつ。要対応・予定・待ちを先頭に | 生成区間は CLI、外は手書き                               |
| 要約     | `entities/{key}/index.md` | 1対象の最新状態と結論                       | AI（frontmatter と結論は常に最新に書き換え、経緯は追記） |
| 一次情報 | `{YYYY-MM-DD}_{kind}.md`  | 1回の出来事の生メモ                         | AI（その回だけ。後から書き換えない）                     |

上の層ほど短く、常に最新。下の層ほど詳しく、書いた時点のまま。何かを知りたいときは上から順に降りていけば、必要以上のファイルを開かずに済む。

一次情報は無限には残さない。続いている対象の古いイベントログは要約の層（`index.md` の `digests`）に畳み、終わった対象はフォルダごと台帳に畳む（[04-lifecycle.md](04-lifecycle.md)）。

## 打ち切りの粒度を分ける（triage と entity）

公開情報だけで足切り条件に当たったものまで1件1フォルダにすると、フォルダが増えすぎる。そこで「深く調べる前に打ち切ったもの」は triage にバッチ単位でまとめる。`entries` に名称と理由を列挙しておけば、重複チェックはフォルダと同じように照合できる。

## scope（区分）

- scope は「雇用・契約・費用負担の主体」のように、**条件の前提が変わる軸**で切る。題材の分類（カテゴリ）で切らない（それはタグでよい）。
- scope の一覧と説明の正本は `schema.py` の `SCOPES`。フォルダ名と一致させる。
- scope 固有のファイル（`criteria.md`・`archive.md`）は必要になった時点で作る。サンプルの `personal` には無い。
- 1つしか scope が要らないなら `main` 1つでよい。後から増やしても構造は変わらない。

## profile（scope 共通）と scope 固有の振り分け

| 情報                                 | 置き場所                                                           |
| ------------------------------------ | ------------------------------------------------------------------ |
| scope に依存しない判断軸・好み       | `profile/preferences.md`                                           |
| scope 固有の必須条件・予算・NG       | `scopes/{scope}/criteria.md`                                       |
| 判断の背景にある本音（外に出さない） | `profile/internal/`                                                |
| 派生（翻訳・要約）版                 | `profile/en/` など。`source_file` / `source_updated_at` を持たせる |

迷う記述は scope 側に置く。共通部に誤って入れると、別 scope の判断をその条件で縛ってしまう。

## contacts（scope 横断のエンティティ）

対象そのものとは別に、「誰（どの経路）からどんな情報・紹介が来たか」を評価したいときに使う。同じ人が複数の scope に関わるので scope の外に置き、`scopes` で関わる範囲を示す。紹介を受けたら、エンティティの `contact` とコンタクトの `introduced` の両方にキーを書く（どちらからでも辿れるように）。不要なら丸ごと削除してよい。

## 公開範囲（visibility）

`note` 種別は `visibility`（`public` / `internal`）が必須。`internal` は判断にだけ使い、外部に出す文章の生成時に引用しない。閲覧画面を作るなら表示しない。リポジトリ自体を公開する場合は、`vault/`・`data/` を同期対象から外し、`references/` のような空の雛形だけを公開する（[05-derived.md](05-derived.md)）。
