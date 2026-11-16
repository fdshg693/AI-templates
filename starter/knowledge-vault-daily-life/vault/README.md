# vault/ — データの地図

日常生活の記録の正本（SSOT）はすべてここに置く。ルート直下の `tools/`・`docs/` は「道具」、`vault/` は「データ」、`data/` は外部から取ってきた「スナップショット（キャッシュ）」。

## 構成

```
vault/
├── profile/                    # 本人について変わりにくいこと（半固定）
│   ├── about.md                # 基本情報（仕事・住まい・家族構成）
│   ├── preferences.md          # 好み・傾向（記録の圧縮から昇格させたもの）
│   ├── routine.md              # 生活リズム
│   └── internal/notes.md       # 本音メモ（非公開）
├── scopes/life/                # scope は1つ。仕事・趣味などの分類は frontmatter の area
│   ├── README.md               # 何を記録するか・area の付け方
│   ├── criteria.md             # 新しく始めることの足切り条件（非公開）
│   ├── dashboard.md            # 直近の予定・最近の出来事・続けていること（マーカー間は自動生成）
│   ├── archive.md              # やめた・合わなかったものの台帳（1 件数行）
│   ├── entities/{key}/         # 1件1フォルダ: index.md ＋ {YYYY-MM-DD}_{kind}.md
│   └── triage/                 # 調べただけで候補から外したものをバッチ単位で1ファイル
├── contacts/{key}/             # おすすめをくれる人（本・お店などの紹介元）
└── _templates/                 # 新しいファイルの雛形（検証対象外）
```

## 入口

| 知りたいこと                               | 見る場所                                                                                                   |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| 最近何をしているか・次の予定               | [scopes/life/dashboard.md](scopes/life/dashboard.md)                                                       |
| どんな人か・何が好きか（変わりにくいこと） | [profile/](profile/about.md)（[preferences.md](profile/preferences.md)・[routine.md](profile/routine.md)） |
| ある活動の経緯                             | `scopes/life/entities/{key}/index.md`（古い経緯は frontmatter の `digests`）                               |
| やめた・合わなかった理由                   | [scopes/life/archive.md](scopes/life/archive.md)（または `uv run tools/vault/check_entity.py`）            |
| 仕事だけ・趣味だけ見たい                   | `uv run tools/vault/build_index.py --where area=hobby -s`                                                  |
| 横断検索したい                             | `uv run tools/vault/build_index.py -q <キーワード>`（ヒットした正本のパスを返す）                          |
| フロントマターに何を書けるか               | [docs/vault-schema.md](../docs/vault-schema.md)（正は `tools/vault/schema.py`）                            |

運用ルールは [AGENTS.md](AGENTS.md)。
