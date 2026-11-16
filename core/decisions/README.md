# decisions

設計判断を「何を決め、なぜそうしたか」とともに1判断＝1ファイルで残す、最小構成のテンプレート（いわゆる ADR: Architecture Decision Record）。実装の手順は別テンプレート `plans`、長期にわたる調査・比較の記録は別テンプレート `knowledge-vault` で扱い、ここには採否の結論と理由だけを置く。

- **対象**: AGENTS.md / CLAUDE.md を読むエージェントと作業するリポジトリ。言語・フレームワークは問わない。
- **含まれるもの**: 判断ファイルの書式（番号付きファイル名・frontmatter の `status`・4つの必須節）、置き換え（supersede）の手順、番号・節・置き換え関係を検査するスクリプト。

もっと多くの判断が積み重なった状態の例は、テンプレート集の `starter/decisions-web-service/` にある（スターターの位置づけはテンプレート集ルートの `starter/README.md`）。

## 導入手順

1. 次を導入先リポジトリの `decisions/` にコピーする。この README はコピーしない。

   | コピーするもの | 内容 |
   | -------------- | ---- |
   | [AGENTS.md](AGENTS.md) | エージェント向けの運用ルール（入口） |
   | [CLAUDE.md](CLAUDE.md) | `@./AGENTS.md` を読み込むだけ（Claude Code 用） |
   | [guides/](guides) | 場面別ガイド（ルールの正本） |
   | [references/](references) | 記入例（導入先の `decisions/` と同じ構造） |
   | [lint_decisions.py](lint_decisions.py) | 判断ファイルの検査・次の番号の表示 |

   置き換えが必要なプレースホルダは無い。判断の持ち主が決まっていれば、`decisions/AGENTS.md` の「導入先固有の運用」節に書く。
2. ルートの `AGENTS.md`（または `CLAUDE.md`）に「設計判断を書く・変えるとき、判断に関わるコードを変えるときは `decisions/AGENTS.md` に従う」と1行足す（Claude Code ならルート `CLAUDE.md` に `@decisions/AGENTS.md` でもよい）。サブフォルダの AGENTS.md は、ルートで作業するエージェントに自動では読まれないため。
3. リポジトリのルートで検査を実行し、エラーが出ないことを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

   ```bash
   uv run decisions/lint_decisions.py decisions
   ```

4. 最初の判断として、すでに決まっている大きな選択（使っている言語・データベースなど）を1件書くと、書式の確認を兼ねられる。

## 同梱スクリプト

リポジトリのルートで実行する。

```bash
uv run decisions/lint_decisions.py decisions                         # 検査（エラーは path:line: 形式、非0終了）
uv run decisions/lint_decisions.py decisions --next                  # 次に使う番号を表示
uv run decisions/lint_decisions.py --examples decisions/references   # テンプレート編集時: 記入例自体を検査
```
