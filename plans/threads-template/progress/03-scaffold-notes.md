# Step 3 実装メモ: 雛形・plans の取り込み・guides・入口ファイル

## 作成・変更したファイル

- 新規: `core/threads/`（scaffold で生成）— `AGENTS.md` / `CLAUDE.md` / `README.md` / `guides/thread-writing.md`・`thread-updating.md`・`thread-closing.md` / `link_plans.py`。`lint_threads.py` と `references/example.md` は雛形のまま（Step 4）
- 変更: `.gitignore` — `core/threads/planning/`
- 変更: `.claude/skills/template-review/scripts/inspect_template.py` — `iter_files` を `os.walk` にし、Junction・シンボリックリンクのディレクトリを間引く

## その場で決めた細かい判断

- Junction の判定は `Path.is_junction()`（3.12+）ではなく `os.lstat().st_reparse_tag == IO_REPARSE_TAG_MOUNT_POINT` にした。uv が 3.11 を選ぶ環境でも動かすため。
- `link_plans.py` に `--check` を足した（作らずに状態だけ見る。無い・壊れていれば終了コード1）。
- `log.md` は追記のみなので、クローズ時にプランを削除すると過去エントリのプランへのリンクが切れる。書き換えずに残し、lint 側で `closed` / `abandoned` の `log.md` のリンク切れを検査しない方針にした（thread-closing.md「守ること」、実装は Step 4）。
- クローズの `[完了]` エントリは「所属プランごとに1つ＋最後にスレッド全体の1つ」にした（lint の「最後のエントリが `[完了]`」と両立する）。
- プランの完了時には `log.md` に書かず、クローズ時にまとめて書く（Step 2 の合意どおり）。`open` ⇔ `paused` の切り替えも種別6値に無いので `log.md` には書かず、`未解決事項` に再開条件を書く。
- `closed` / `abandoned` のスレッドは `open` に戻さず、関連作業は新しいスレッドを立てる（クローズ時にプランを削除済みのため）。
- AGENTS.md の場面表から `planning/AGENTS.md` へリンクした。テンプレート集では Junction の先（`core/plans`）を指すため inspect では「フォルダ外リンク」になるが、導入先では実体なので許容する。

## 検証

```text
# inspect の出力が既存テンプレートで変わらないこと（HEAD 版と比較）
core/plans / core/knowledge-vault / core/decisions: diff なし

# Junction
link_plans.py --check（作成前）  -> missing, exit=1
link_plans.py                    -> linked
link_plans.py（2回目）           -> ok
git status --short               -> core/threads/planning は出ない（.gitignore:24 で無視）
inspect core/threads の "planning" を含む行: 旧版 123 -> 新版 0

# スクラッチパッドで修復・停止
フォルダごと移動して Junction の絶対パスをずらす -> --check: broken exit=1 -> 実行で張り直し、中身が読める
planning を実体のフォルダにする                 -> error で停止 exit=1、core/plans は残る

# inspect core/threads（Step 3 終了時）
常時ロード 60 行 / 到達不能 0 / リンク切れ 0
フォルダ外リンク: AGENTS.md -> planning/AGENTS.md（Junction）、README.md -> ../plans（依存の明記）、thread-writing.md のコードブロック内の例
TODO: AGENTS.md「サンプル」表 1 か所と references/example.md（Step 4）
```
