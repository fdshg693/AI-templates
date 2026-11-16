# threads

複数のプランにまたがる大規模な変更を「スレッド」単位で束ねる運用テンプレート。スレッドはトピックごとに、所属プランとその予定順、実装中に判明した事実・仕様変更・手戻りの経緯を時系列で残す。プランそのものは [plans](../plans) テンプレートを `threads/planning/` として内包して使う。

- **対象**: AGENTS.md / CLAUDE.md を読むコーディングエージェントと、複数プランに分かれる作業をするリポジトリ。言語・フレームワークは問わない。
- **含まれるもの**: スレッドの書式（`00-thread.md` と追記のみの `log.md`、`status` 4値、経緯の種別6値）、プランとの双方向の関連付け（`plans:` ⇔ `thread:`）、実行中の追記とクローズ時の後片付けのルール、整合性チェックのスクリプト。
- **境界**: 1プランで閉じる作業は plans だけで扱う。新規リポジトリの立ち上げは `repo-plans`、設計判断そのものの記録は `decisions` の範囲で、スレッドからはリンクするだけにする。

## 導入手順

1. 導入先リポジトリに `threads/` を作り、次をコピーする。

   | コピーするもの | コピー先 | 内容 |
   | -------------- | -------- | ---- |
   | [AGENTS.md](AGENTS.md) | `threads/` | エージェント向けの運用ルール（入口） |
   | [CLAUDE.md](CLAUDE.md) | `threads/` | `@./AGENTS.md` を読み込むだけ（Claude Code 用） |
   | [guides/](guides) | `threads/` | 場面別ガイド（ルールの正本） |
   | [references/](references) | `threads/` | 記入例（導入先の `threads/` と同じ構造） |
   | [lint_threads.py](lint_threads.py) | `threads/` | スレッドとプランの関連付けの検査 |
   | plans の導入手順の表にあるもの一式 | `threads/planning/` | プランの書式・ガイド・スクリプト（[plans の README](../plans/README.md#導入手順)） |

   この README と `link_plans.py`（テンプレート集の中でだけ使う）はコピーしない。テンプレート集のルートからなら次のとおり。

   ```bash
   mkdir -p {dest}/threads/planning
   cp -r core/threads/AGENTS.md core/threads/CLAUDE.md core/threads/guides core/threads/references core/threads/lint_threads.py {dest}/threads/
   cp -r core/plans/AGENTS.md core/plans/CLAUDE.md core/plans/guides core/plans/references core/plans/lint_plans.py core/plans/snapshot_plan.py {dest}/threads/planning/
   ```

   テンプレート集の `core/threads/planning/` は `core/plans` への Junction（コミットされていない）。`core/threads` をフォルダごとコピーした場合も、2回目のコピーで `threads/planning/` が実体の plans で埋まるので結果は同じになる（その場合は `README.md`・`link_plans.py` を消す）。
2. （任意）plans の README の手順2に従い、Claude Code 用の進め方を `threads/planning/AGENTS.md` の「導入先固有の運用」節へ書き写す。
3. ルートの `AGENTS.md`（または `CLAUDE.md`）に「プランの作成・実行と、複数プランにまたがる作業は `threads/AGENTS.md` に従う」と1行足す（Claude Code ならルート `CLAUDE.md` に `@threads/AGENTS.md` でもよい）。サブフォルダの AGENTS.md は、ルートで作業するエージェントに自動では読まれないため。
4. リポジトリのルートで検査を実行し、エラーが出ないことを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

   ```bash
   uv run threads/lint_threads.py threads
   uv run threads/planning/lint_plans.py threads/planning
   ```

### plans を単独で導入済みのリポジトリへ追加する

既存の `plans/` を `threads/planning/` へ移し、上の手順のうち threads 側のファイルだけをコピーする。

```bash
mkdir -p {dest}/threads
git -C {dest} mv plans threads/planning
cp -r core/threads/AGENTS.md core/threads/CLAUDE.md core/threads/guides core/threads/references core/threads/lint_threads.py {dest}/threads/
```

ルートの指示ファイルにある `plans/AGENTS.md` の1行を、手順3の `threads/AGENTS.md` の1行に差し替える。既存のプランは `thread:` を持たないまま使える（スレッドに所属させるときに足す）。

`{dest}` は導入先リポジトリのパス。他に置き換えるプレースホルダは無い。

## 同梱スクリプト

導入先のリポジトリのルートで実行する。

```bash
uv run threads/lint_threads.py threads                         # スレッドの検査（エラーは path:line: 形式、非0終了）
uv run threads/planning/lint_plans.py threads/planning         # プランの検査（plans の同梱スクリプト）
uv run threads/lint_threads.py --examples threads/references   # テンプレート編集時: 記入例自体を検査
```

テンプレート集の中でだけ使うもの（テンプレート集のルートで実行）:

```bash
uv run core/threads/link_plans.py           # core/threads/planning -> core/plans の Junction を作る・直す（clone 後に1回）
uv run core/threads/link_plans.py --check   # 状態だけ確認
```
