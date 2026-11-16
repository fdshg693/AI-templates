# repo-plans

新しいリポジトリを立ち上げるとき、AIコーディングエージェントと一緒に「仕様・技術選定 → 最小実装 → 土台整備」の3フェーズで計画を書き、進めるための運用テンプレート。既存コードベースへの機能追加は対象外（別テンプレート `plans` で扱う）。

- **対象**: AGENTS.md / CLAUDE.md を読むコーディングエージェントと、新規リポジトリを作る人。言語・フレームワーク・パッケージマネージャ・CI は問わない。
- **ねらい**: 新規作成では、実装対象・ドキュメントの置き場・エージェントへの指示・検証方法が同時に未確定になりやすい。実装を急ぐ前にそれらを小さく決め、実際の作業で得た知見だけをルールとスキルへ戻す。

## 導入手順

1. 次を新規リポジトリの `repo-plans/` にコピーする。この README はコピーしない。

   | コピーするもの                               | 内容                                                         |
   | -------------------------------------------- | ------------------------------------------------------------ |
   | [AGENTS.md](AGENTS.md)                       | エージェント向けの作業規約（入口）                           |
   | [CLAUDE.md](CLAUDE.md)                       | `@./AGENTS.md` を読み込むだけ（Claude Code 用）              |
   | [asis.md](asis.md)                           | 現在地と次の作業（運用中に書き換える）                       |
   | [phase-status.md](phase-status.md)           | 3フェーズの状態一覧（運用中に書き換える）                    |
   | [lint_repo_plans.py](lint_repo_plans.py)     | frontmatter・必須の節・フェーズ順・完了ゲート・リンクの検査 |
   | [guides/](guides)                            | フェーズ別の手順と計画の書式。書き換えない                   |
   | [references/](references)                    | 3フェーズを通した記入例。書き換えない                        |

2. ルートの指示ファイルから `repo-plans/AGENTS.md` を参照する。サブフォルダの AGENTS.md は、ルートで作業するエージェントに自動では読まれないため。
   ルートの `AGENTS.md` に1行足す例:

   ```markdown
   新規立ち上げ中（repo-plans のフェーズ3完了まで）は repo-plans/AGENTS.md に従う。
   ```

   Claude Code でルートの `CLAUDE.md` を使う場合は `@repo-plans/AGENTS.md` の1行でもよい。

   この1行はフェーズ3の完了時に外す（[フェーズ完了ゲート](guides/phase-gate.md)の項目に含まれる）。
3. リポジトリのルートで検査を実行し、エラーが出ないことを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

   ```bash
   uv run repo-plans/lint_repo_plans.py repo-plans
   ```

4. エージェントに作業を依頼する。エージェントは `asis.md` から始め、フェーズ1のフォルダに最初の計画を作る。

## フェーズ

次の3フェーズを順番に進める。A/B/Cの選択肢ではなく、すべて必要な工程である。作業フォルダはこのテンプレートには含まれず、コピー先で `repo-plans/` 直下にそのフェーズを始めるときに作る。

| 順序 | 作業フォルダ                       | 確定すること                                             | ガイド                                                                   |
| ---- | ---------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------ |
| 1    | `01-specification-and-technology/` | 目的、対象外、成功条件、技術選定の根拠、最初の縦切り     | [フェーズ1](guides/01-specification-and-technology.md)        |
| 2    | `02-minimal-delivery/`             | 最小実装、最初の利用・検証手順、初回のルール・スキル利用 | [フェーズ2](guides/02-minimal-delivery.md)                    |
| 3    | `03-foundation/`                   | ドキュメント地図、ルールとスキルの配置、継続的な改善方法 | [フェーズ3](guides/03-foundation.md)                          |

各フェーズで、計画の提示 → ユーザーの回答・レビュー → 反映 を少なくとも一度行う（[対話ループ](guides/interaction-loop.md)）。計画ファイルの書式は [plan-format.md](guides/plan-format.md)、架空リポジトリ `worklog` を3フェーズ通して進めた記入例は [references/](references/README.md) にある。

## テンプレートを編集するとき

記入例を変更したら、テンプレート置き場のルートで次を実行する。

```bash
uv run core/repo-plans/lint_repo_plans.py --examples core/repo-plans/references
uv run core/repo-plans/lint_repo_plans.py core/repo-plans
```
