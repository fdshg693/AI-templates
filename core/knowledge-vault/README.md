# knowledge-vault

調べて・比べて・判断していく活動の記録を、**長期間・大量**になっても AI エージェントと人間の両方が使える状態に保つためのテンプレート。frontmatter 付き Markdown を正本にし、スキーマ・検証・自動生成の一覧・検索索引・終わったものの圧縮を組み合わせる。題材は問わない（ツール選定、物件探し、論文調査、取引先管理、収集趣味など）。

- **対象**: AGENTS.md / CLAUDE.md を読むコーディングエージェントと一緒に、情報を継続的に集めて判断したい人。
- **含まれるもの**: 考え方（`guides/`）、コピー先と同じ構造の実例一式（`references/`。ツール・サービスの導入検討を題材にしたサンプルの vault と、スキーマ・CLI）。

## 仕組みの概要

| 仕組み                                                                              | 何を防ぐか                                                     | 詳細                                                               |
| ----------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------ |
| 正本・道具・キャッシュの分離                                                        | どれが正しいか分からなくなる                                   | [01](guides/01-philosophy.md)                                      |
| 1件1フォルダ・1回1ファイル・状態は frontmatter                                      | 移動でリンクが切れる、要約と生メモが混ざる                     | [02](guides/02-layout.md)                                          |
| スキーマをコード1か所に、検証を commit 前に強制                                     | 書式が少しずつ崩れて集計できなくなる                           | [03](guides/03-schema.md)                                          |
| 確かさの記録（evidence・幅のあるスコア）                                            | 推測が事実として読まれる                                       | [01](guides/01-philosophy.md)・[06](guides/06-ai-collaboration.md) |
| 重複・除外チェック                                                                  | 見送ったものをまた調べる                                       | [04](guides/04-lifecycle.md)                                       |
| 見送り台帳への圧縮                                                                  | 終わった案件で検索結果と文脈が埋まる                           | [04](guides/04-lifecycle.md)                                       |
| 古いイベントログの要約（digests）                                                   | 続いている対象のログが増え続け、直近の動きが埋もれる           | [04](guides/04-lifecycle.md)                                       |
| 自動生成のダッシュボード（最近の出来事を含む）・SQLite 索引（タグ・値での絞り込み） | 手で保守する一覧が古くなる、近況が分からない、全文を舐めて遅い | [05](guides/05-derived.md)                                         |
| stdout はパスだけ・機械と判断の分離                                                 | AI のトークン浪費、一律処理による質の低下                      | [06](guides/06-ai-collaboration.md)                                |

## 構成

- [`guides/`](guides) — 考え方と手順。最初に読む。
  - [01-philosophy.md](guides/01-philosophy.md) — 核となる原則
  - [02-layout.md](guides/02-layout.md) — フォルダ構成・ドキュメント種別・三層構造・scope
  - [03-schema.md](guides/03-schema.md) — スキーマと検証
  - [04-lifecycle.md](guides/04-lifecycle.md) — ステータス設計・追記・直近アクション・重複チェック・圧縮
  - [05-derived.md](guides/05-derived.md) — ダッシュボード・検索索引・閲覧画面・派生文書・公開リポジトリとの分離
  - [06-ai-collaboration.md](guides/06-ai-collaboration.md) — AI エージェントとの協働の決まり
  - [07-adapting.md](guides/07-adapting.md) — 導入手順と書き換える箇所
- [`references/`](references) — コピー先のリポジトリと同じ構造の実例一式。
  - [`vault/`](references/vault/README.md) — サンプルの正本（scope 2つ、エンティティ・イベント・コンタクト・トリアージ・台帳・ダッシュボード）
  - [`tools/vault/`](references/tools/vault) — スキーマ（`schema.py`）と CLI

    | スクリプト           | 役割                                                                                                   |
    | -------------------- | ------------------------------------------------------------------------------------------------------ |
    | `validate.py`        | スキーマ・配置・関係の検証（エラー / 警告）                                                            |
    | `gen_schema_doc.py`  | `docs/vault-schema.md` の生成（`--check` で差分検査）                                                  |
    | `build_dashboard.py` | ダッシュボードのマーカー区間の生成                                                                     |
    | `build_index.py`     | SQLite 索引（FTS5 trigram）の作成・検索                                                                |
    | `check_entity.py`    | 名称・別名の正規化照合による重複・除外チェック                                                         |
    | `compact.py`         | 終了したものの台帳への圧縮、続いているものの古いイベントログの要約（list / draft / apply、`--events`） |

## 使い方

1. [guides/01-philosophy.md](guides/01-philosophy.md) と [guides/02-layout.md](guides/02-layout.md) を読む。
2. サンプルで動きを見る（`references/` で実行）。

   ```sh
   cd references
   uv run tools/vault/validate.py --summary
   uv run tools/vault/build_index.py -q 権限 -s
   uv run tools/vault/check_entity.py --scope work -s "Delta Pages"
   uv run tools/vault/compact.py list --summary
   ```

3. [guides/07-adapting.md](guides/07-adapting.md) に従ってコピー・書き換え・検証する。この README と `guides/` はコピーしない。

別の題材に導入して運用した状態の例（日常生活の記録）は、テンプレート集の `starter/knowledge-vault-daily-life/` にある（スターターの位置づけはテンプレート集ルートの `starter/README.md`）。
