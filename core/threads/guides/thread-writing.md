# スレッド作成時

複数のプランにまたがる作業を始めるとき、プランへ分割する**前**に読む。スレッドの書式（フォルダ構成・frontmatter・必須見出し・経緯エントリ）の正本はこのファイル。

## スレッドを立てる基準

次のいずれかに当てはまったらスレッドを立てる。1プランで閉じる作業は `planning/` のプランだけで扱い、スレッドは作らない（記録が二重になるだけのため）。

- 作業が2つ以上のプランに分かれる（分かれる見込みがある）。
- `implementing-done` のプランに手戻りが発生した（完了済みプランの `status` は戻さず、新しいプランを起こすため2プラン以上になる）。
- スレッドに所属していない既存のプラン2つ以上に、同じ事実の発覚・仕様変更が影響する。

設計判断そのものの記録・新規リポジトリの立ち上げはこのテンプレートの対象外。別の仕組みがあれば、スレッドからはリンクするだけにする。

## 作るもの

1スレッド＝1フォルダ。導入先の `threads/` の下は次の構成になる。

```text
threads/
├── planning/                     # plans テンプレート（プランの置き場。書き方は planning/AGENTS.md）
│   ├── {plan-a}/00-overview.md   # 所属プラン（フォルダ方式）。frontmatter に thread:
│   └── {plan-b}.md               # 所属プラン（単一ファイル完結）。frontmatter に thread:
└── topics/
    └── {thread-name}/            # ケバブケース。1スレッド＝1フォルダ
        ├── 00-thread.md          # 目的・所属プラン一覧・未解決事項（読み返す部分。書き換えてよい）
        └── log.md                # 経緯（増え続ける部分。追記のみ）
```

### `00-thread.md`

```yaml
---
type: Thread
status: open
plans:
  - ../../planning/{plan-a}/00-overview.md # 役割を1行で
  - ../../planning/{plan-b}.md # 役割を1行で
---
```

- `plans:` は所属プランの overview（単一ファイル完結ならそのファイル）への、`00-thread.md` からの相対パスの列。**並び順が予定順**。各項目のコメントに役割を書く。所属プランが無いときは `plans: []`。
- 並び順は着手条件の正本ではない（正本はプランの `depends_on`）。ただし、同じスレッド内でプラン A が B に `depends_on` するなら、`plans:` では B を A より前に置く。

`status` は次の4値だけを使う（`lint_threads.py` の `THREAD_STATUSES` と同期）。

| 値 | 意味 | `plans:` |
| -- | ---- | -------- |
| `open` | プランへの分割・実行を進めている | 所属プランを列挙 |
| `paused` | 中断している。再開条件を `未解決事項` に書く | 所属プランを列挙（削除しない） |
| `closed` | 全プランが完了し、後片付けまで終えた（[thread-closing.md](thread-closing.md)） | 空 |
| `abandoned` | 途中で中止し、後片付けまで終えた（[thread-closing.md](thread-closing.md)） | 空 |

本文の必須の `##` 見出しは次の3つ（この順。前方一致で照合。`lint_threads.py` の `THREAD_SECTIONS` と同期）。

| 見出し | 書くこと |
| ------ | -------- |
| `目的・スコープ` | 何を達成するか、どこまでを含めないか（2〜5行）。関係する過去のスレッドや判断記録へのリンク |
| `プラン一覧` | `plans:` と同じリンクを同じ順で、番号付きリストで並べ、各1行の役割を添える。まだ作っていないプランはリンクなしで `（未作成）` と書く |
| `未解決事項` | プランをまたいで決まっていないこと・`paused` の再開条件。無ければ「なし」。解決したら消してよい（経緯は `log.md` に残る） |

`プラン一覧` の書き方:

```markdown
1. [{plan-a}](../../planning/{plan-a}/00-overview.md) — 役割
2. [{plan-b}](../../planning/{plan-b}.md) — 役割
3. （未作成）{plan-c} — 役割
```

### `log.md`

```yaml
---
type: Thread Log
---
```

`status` は持たない。本文は経緯エントリを古い順に並べる。エントリは次の形で、本文は1〜3行と反映先プランへのリンクだけにする（詳細はプランの progress に置く）。

```markdown
## 2026-11-13 [発見] 見出し

何が分かったか・何を決めたかを1〜3行。
反映先: [{plan-b}](../../planning/{plan-b}.md)
```

- 見出しは `## YYYY-MM-DD [種別] 見出し`。日付は昇順（同じ日付の連続は可）。
- **追記のみ**。過去のエントリを書き換え・削除しない。理由: 手戻りの原因を後から辿れなくなる。誤りは新しいエントリで訂正する。

種別は次の6値だけを使う（`lint_threads.py` の `LOG_KINDS` と同期）。

| 種別 | 書くとき |
| ---- | -------- |
| `計画` | スレッドの作成、プランへの分割、プランの追加 |
| `発見` | 実行中に分かった事実が、実行中のプラン以外にも影響する |
| `仕様変更` | 依頼者の要求・スコープが変わった |
| `手戻り` | `implementing-done` のプランをやり直す必要が出た |
| `順序変更` | `plans:` の並び・プラン間の `depends_on` を変えた |
| `完了` | クローズ時の各プランの完了要約と、スレッド全体の結果（[thread-closing.md](thread-closing.md)） |

### 所属プラン側

所属プランの overview（単一ファイル完結ならそのファイル）の frontmatter に、`00-thread.md` への相対パスを `thread:` で書く。`Plan Step`・`rough/`・`progress/` には書かない。

```yaml
thread: ../../topics/{thread-name}/00-thread.md # フォルダ方式の 00-overview.md から
thread: ../topics/{thread-name}/00-thread.md    # 単一ファイル完結の {plan-name}.md から
```

1つのプランは1つのスレッドにだけ所属する。スレッドの `plans:` とプランの `thread:` は必ず対で更新する（片側だけだと lint がエラーにする）。

## 手順

1. `topics/` に、同じ目的の `open` / `paused` のスレッドが無いか確かめる。あればそのスレッドにプランを足す（[thread-updating.md](thread-updating.md)）。
2. `topics/{thread-name}/00-thread.md` を `status: open`・`plans: []` で作り、`目的・スコープ` と `未解決事項` を書く。`プラン一覧` には、予定するプランを予定順に `（未作成）` で並べる。
3. `log.md` を作り、最初のエントリを `[計画]` で書く（なぜスレッドにしたか、どう分割するか）。
4. プランを1つずつ書く。書き方は plans のガイド（`planning/AGENTS.md` の場面表）に従う。プランを1つ作るたびに、次を同時に行う。
   - プランの overview に `thread:` を足す。
   - `00-thread.md` の `plans:` に足し、`プラン一覧` の `（未作成）` 行をリンクに置き換える。
   - プラン間の着手条件は plans の `order` / `depends_on` / `blocks` で書き、`plans:` の並びと矛盾させない。
   - 既存のプラン（スレッド未所属）を束ねるときは、書く代わりに同じ3か所を更新する。きっかけの事実・仕様変更は、プラン本文へ反映してから `log.md` に `[発見]` / `[仕様変更]` で追記する（[thread-updating.md](thread-updating.md)）。
5. スレッドに実装手順を書かない。理由: 実装の正本はプランで、両方に書くと食い違う。手順・触るファイルはプランに書く。

## 完了条件

- [ ] `00-thread.md` と `log.md` があり、`log.md` に `[計画]` エントリが1つ以上ある
- [ ] 作成済みの全プランが `plans:` と `プラン一覧` に同じ順で載り、各プランの overview に `thread:` がある
- [ ] リポジトリのルートで次がエラー0で終わる

  ```bash
  uv run threads/lint_threads.py threads
  uv run threads/planning/lint_plans.py threads/planning
  ```
