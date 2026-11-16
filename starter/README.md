# スターター置き場

`core/` のテンプレートを架空のリポジトリに導入し、**しばらく運用した状態**を再現した一式を置く。core の `references/` が「書式が一意に分かる最小の記入例」なのに対し、スターターは成果物が積み重なったときに出てくる状況（状態の遷移途中、成果物どうしの参照、導入先固有の運用の書き足し）を見せる。

- そのままテンプレート集の外へコピーし、エージェントにテンプレートの運用を試させる起点にする。
- 1つのテンプレートに複数のスターターがあってよい（題材ごとに作る）。

## 一覧

| スターター | 元のテンプレート | 題材 |
| ---------- | ---------------- | ---- |
| [decisions-web-service](decisions-web-service/STARTER.md) | [core/decisions](../core/decisions) | タスクボード Web サービスの API で、設計判断8件（置き換え・不採用・提案中を含む） |
| [knowledge-vault-daily-life](knowledge-vault-daily-life/STARTER.md) | [core/knowledge-vault](../core/knowledge-vault) | 架空の人物の日常生活の記録を約1年分（近況・古い記録の要約・やめたことの台帳・area での絞り込み） |

## 構成

```text
starter/<template>-<題材>/      # 例: decisions-web-service
├── STARTER.md                  # スターターの説明。frontmatter に検査用の宣言（下記）
├── README.md / AGENTS.md / CLAUDE.md   # 架空リポジトリのルート。テンプレートへの1行の導線を含む
└── <installed_at>/             # core/<template>/ を README.md 以外コピーし、成果物を足したもの
```

テンプレートが「`references/` の中身をリポジトリのルートにコピーし、決まった箇所を書き換える」形（knowledge-vault など）なら、`source: references`・`installed_at: .` にし、書き換えるファイルを `adapted`、置き換えるサンプルデータを `samples` に挙げる。

`STARTER.md` の frontmatter:

```yaml
---
template: decisions                       # core/ 直下のフォルダ名
installed_at: decisions                   # スターター内のコピー先
extended: [AGENTS.md]                     # 追記だけを許すコピー（「導入先固有の運用」節など）
lint: decisions/lint_decisions.py decisions   # スターターのルートから実行する lint と引数
---
```

| キー | 必須 | 意味 |
| --- | --- | --- |
| `template` | ✓ | `core/` 直下のフォルダ名 |
| `source` | | コピー元を `core/<template>/<source>/` に絞る（省略時はテンプレート全体） |
| `installed_at` | ✓ | スターター内のコピー先（ルートなら `.`） |
| `extended` | ✓ | 追記だけを許すコピー（無ければ `[]`） |
| `adapted` | | テンプレートの導入手順が書き換えを求めるファイル（存在だけ検査） |
| `samples` | | テンプレートのサンプルデータで、スターターの成果物に置き換えるもの（検査しない。`*` は `/` をまたぐ） |
| `lint` | ✓ | スターターのルートから実行する検査。`[a, b]` で複数。`uv` で始まるものはそのまま実行し、それ以外は Python スクリプトとして実行する |

## スターターを作る・直すときのルール

- テンプレートのファイル（ガイド・記入例・lint）はスターター側で編集しない。理由: core と食い違うと、どちらが正しいか分からなくなる。直すときは core を直し、`--sync` で反映する。
- `extended` に挙げたファイルは、core の内容を消さずに追記だけする（導入先固有の運用を書き足す想定）。
- `adapted` に挙げてよいのは、テンプレートの導入手順（`guides/` の導入ガイド）が書き換え箇所として挙げているファイルだけ。それ以外の道具（CLI など）を変えたくなったら、core を汎用的に直す。
- スターターに新しいルールを書かない。必要なルールが見つかったら core のガイドに足す。スターターには成果物と、導入先として自然な書き足しだけを置く。
- `STARTER.md` には「references より複雑な点」（どの状況をどのファイルが示すか）と、試せる作業の例を書く。題材が違うだけで示す状況が同じスターターは作らない。
- 成果物は架空の題材で、テンプレートの lint をエラー0で通す状態にする。
- 新しいスターターを足したら、上の一覧とリポジトリルートの `CLAUDE.md` に1行足し、元テンプレートの README からも名前で触れる。

## 検査

テンプレート集のルートで実行する。core のテンプレートを変更したときも、対応するスターターについて実行する。

```bash
uv run starter/check_starters.py           # 全スターター: core との一致、extended の追記のみ、lint
uv run starter/check_starters.py --sync    # core の変更をコピーへ反映してから検査
```
