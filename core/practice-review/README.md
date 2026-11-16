# practice-review

外部の練習相手（ChatGPT など）と行った練習セッションの記録を、エージェントにレビューさせ続けるためのテンプレート。主な用途は、ChatGPT と外国語で会話して練習し、スレッドを Markdown でエクスポートして置いていく使い方。面接練習・ロールプレイなど、「対話のログを置き、直すところと次の練習を出してもらう」練習なら同じ仕組みで使える。

学習リポジトリ全体の構造は別テンプレート `learning-template`、調査・比較・判断の長期記録は別テンプレート `knowledge-vault` で扱う。

- **対象**: AGENTS.md / CLAUDE.md を読むエージェントと作業する、個人の学習用リポジトリ。言語・ツールは問わない（同梱スクリプトは Python 標準ライブラリのみ）。
- **含まれるもの**: エクスポートの取り込み、未レビュー分だけを対象にするステータス管理、フィードバック・まとめ・題材提案の書式、古くなった出力の自動判定（状態バナー・ダッシュボード）、検査スクリプト。

## 仕組み

- **差分だけを読む**: 取り込んだセッションは `unreviewed` → `reviewed` と状態を持つ。エージェントは未レビューの分と `profile.md`（学習者の苦手パターンなどの要約）だけを読むので、セッションが何百件になっても読む量は増えない。
- **古い出力を読み返さずに済む**: 出力（フィードバック・まとめ・題材提案）には、生成日と「どの日のセッションまで反映したか」が付く。新しいまとめ・提案ができると、古いものは自動で `superseded` になり、ファイルの先頭行が「古い → 新しい版へのリンク」に書き換わる。学習者は `index.md` を開けば、いま読むべきファイルだけが分かる。

```text
inbox/ ──ingest──▶ sessions/ (unreviewed) ──review──▶ feedback/ ──まとめ──▶ digests/
                                                 │                    （feedback は superseded に）
                                                 └──▶ profile.md 更新 ──▶ suggestions/
```

## 導入手順

1. 次を導入先リポジトリの `practice-review/` にコピーする。この README はコピーしない。

   | コピーするもの                                                                  | 内容                                                                                                                 |
   | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
   | [AGENTS.md](AGENTS.md)                                                          | エージェント向けの運用ルール（入口）                                                                                 |
   | [CLAUDE.md](CLAUDE.md)                                                          | `@./AGENTS.md` を読み込むだけ（Claude Code 用）                                                                      |
   | [guides/](guides)                                                               | 場面別ガイド（ルールの正本）                                                                                         |
   | [references/](references)                                                       | 記入例（導入先の `practice-review/` と同じ構造）。`references/` のままコピーし、AGENTS.md の「サンプル」から参照する |
   | [lint_practice_review.py](lint_practice_review.py) / [practice.py](practice.py) | 検査 / 取り込み・雛形作成・状態更新                                                                                  |

2. 作業用のファイルを作る: `references/profile.md` を `practice-review/profile.md` にコピーし、空の `practice-review/inbox/.gitkeep` を作る。`sessions/`・`feedback/`・`digests/`・`suggestions/` はスクリプトが必要になったときに作る。
3. `practice-review/profile.md` を書き換える。「練習の設定」（練習するもの・練習相手・フィードバックの言語・母語）と「目標とレベル」を書き、「繰り返している誤り」の表の行と「定着した表現」の本文を消す。frontmatter の `updated_at` を今日に、`covers_through` を空にする。置き換えが必要な `{name}` 形式のプレースホルダは無い。
4. ルートの `AGENTS.md`（または `CLAUDE.md`）に「練習のログ・フィードバック・題材提案を扱うときは `practice-review/AGENTS.md` に従う」と1行足す（Claude Code ならルート `CLAUDE.md` に `@practice-review/AGENTS.md` でもよい）。サブフォルダの AGENTS.md は、ルートで作業するエージェントに自動では読まれないため。
5. リポジトリのルートで、`index.md` を作り直してから検査する。

   ```bash
   uv run practice-review/practice.py refresh practice-review
   uv run practice-review/lint_practice_review.py practice-review
   ```

6. 最初の練習のエクスポートを `practice-review/inbox/` に置き、エージェントに「ログを置いたので見て」と頼む。

外国語会話以外に使う場合は、手順3の「練習の設定」に練習するものを書けばよい。節の名前（「直すところ」「取り入れたい表現」）は外国語に限らない言い方にしてある。ChatGPT 以外の練習相手なら、取り込みのときに `--source` で名前を付ける。

## 同梱スクリプト

リポジトリのルートで実行する。

```bash
uv run practice-review/practice.py ingest practice-review [--date YYYY-MM-DD]   # inbox/ を sessions/ に取り込む
uv run practice-review/practice.py pending practice-review                      # 未レビューのセッション一覧
uv run practice-review/practice.py new feedback practice-review --slug cafe     # 出力の雛形（feedback / digest / suggestions）
uv run practice-review/practice.py refresh practice-review                      # status・状態バナー・index.md を更新
uv run practice-review/lint_practice_review.py practice-review                   # 検査（エラーは path:line: 形式、非0終了）
uv run practice-review/lint_practice_review.py --examples practice-review/references   # テンプレート編集時: 記入例自体を検査
```
