# vault/ — データの地図

情報の正本（SSOT）はすべてここに置く。ルート直下の `tools/`・`docs/` は「道具」、`vault/` は「データ」、`data/` は外部から取ってきた「スナップショット（キャッシュ）」。

## 構成

```
vault/
├── profile/                    # scope 共通の情報（自分の判断軸など）
│   ├── preferences.md          # 判断軸
│   ├── en/                     # 派生（翻訳）版。source_file / source_updated_at で同期を管理
│   └── internal/notes.md       # 本音メモ（非公開）
├── scopes/{scope}/             # 区分ごとに同じ構造を並べる
│   ├── README.md               # この scope の対象・判定基準・期間
│   ├── criteria.md             # 足切り条件（非公開）
│   ├── dashboard.md            # 一覧（マーカー間は自動生成）＋手書きのフェーズ・メモ
│   ├── archive.md              # 見送り台帳（終了したものを 1 件数行に圧縮）
│   ├── entities/{key}/         # 1件1フォルダ: index.md ＋ {YYYY-MM-DD}_{kind}.md
│   └── triage/                 # 一次スクリーニングで打ち切った分をバッチ単位で1ファイル
├── contacts/{key}/             # 情報をくれる人・経路（scope 横断）: index.md ＋ イベントログ
└── _templates/                 # 新しいファイルの雛形（検証対象外）
```

## 入口

| 知りたいこと | 見る場所 |
| --- | --- |
| 何を基準に選ぶか | [profile/preferences.md](profile/preferences.md) ＋ 各 scope の `criteria.md` |
| 今どうなっているか | [scopes/work/dashboard.md](scopes/work/dashboard.md) / [scopes/personal/dashboard.md](scopes/personal/dashboard.md) |
| ある対象の調査・経緯 | `scopes/{scope}/entities/{key}/index.md` |
| 過去に見送った理由 | `scopes/{scope}/archive.md`（または `uv run tools/vault/check_entity.py`） |
| 横断検索したい | `uv run tools/vault/build_index.py -q <キーワード>`（ヒットした正本のパスを返す） |
| フロントマターに何を書けるか | [docs/vault-schema.md](../docs/vault-schema.md)（正は `tools/vault/schema.py`） |

運用ルールは [AGENTS.md](AGENTS.md)。
