---
type: Plan Step
status: implementing-done
---

# Step 3: 雛形生成・plans の取り込み・guides と入口ファイル

> [00-overview.md](00-overview.md) の続き。template-create 手順2・3・6 に相当する。Step 1・2 の完了が前提。

## やること

`core/threads/` の雛形を生成し、Step 1 で決めた方式で plans を取り込み、Step 2 で合意した書式を guides（正本）に書き、AGENTS.md / CLAUDE.md / README.md を仕上げる。

## 読むべきファイル

- 作成手順と完成基準（必読）
  - `.claude/skills/template-create/SKILL.md` — 手順2・3・6
  - `.claude/skills/template-review/SKILL.md` — 評価基準 1〜10
- 入口ファイルの書き方の前例
  - `core/plans/AGENTS.md` / `README.md` — 場面表・不変条件・導入手順の粒度
  - `core/decisions/AGENTS.md` — 小さめのテンプレートの AGENTS.md
- 方式 B の根拠と走査の問題箇所
  - [progress/01-junction-research.md](progress/01-junction-research.md) — 実験コマンドと結果
  - `.claude/skills/template-review/scripts/inspect_template.py` — `iter_files`（`rglob`）

## 触るファイル

- 新規: `core/threads/`（`uv run .claude/skills/template-create/scripts/scaffold_template.py core/threads --guides thread-writing,thread-updating,thread-closing` で生成）
- 新規: `core/threads/link_plans.py` — `core/threads/planning` → `core/plans` を張る。標準ライブラリのみ。Windows は `cmd /c mklink /J`、POSIX は相対パスの `os.symlink`。既にあれば何もしない、リンク切れ（リポジトリを移動して絶対パスがずれた Junction など）なら張り直す。実体のフォルダがあるときは消さずにエラーで止める
- 変更: `.gitignore`（ルート）— `core/threads/planning/` を追加（Junction の下が二重にコミットされるのを防ぐ）
- 変更: `.claude/skills/template-review/scripts/inspect_template.py` — `iter_files` が Junction（`Path.is_junction()`、3.12+）とシンボリックリンクのディレクトリの下を飛ばす。`rglob` は Junction をたどるため、`os.walk` で `dirnames` を間引く形にする
- Junction を張ったら `git status` に `core/threads/planning/` が出ないことを確認する
- 新規: `core/threads/guides/thread-writing.md` — スレッド作成（プラン分割前）。フォルダ構成・frontmatter（`status` 4値・`plans:` / プラン側 `thread:`）・必須見出し・経緯エントリの書式と種別6値の表の正本（`lint_threads.py` の定数と同期）
- 新規: `core/threads/guides/thread-updating.md` — 実行中の追記（発見・仕様変更・手戻り・プランの追加・順序変更）。`log.md` とプラン本文のどちらに何を書くか、`plans:` ⇔ `thread:` の対の更新
- 新規: `core/threads/guides/thread-closing.md` — `closed` / `abandoned` へのクローズと所属プランの一括削除（plans の「完了後の後片付け」への追加ルール）
- 新規: `core/threads/AGENTS.md` / `CLAUDE.md` / `README.md`

## 決定事項・注意点／落とし穴

- **plans の AGENTS.md との関係**: 取り込んだ plans には自前の `AGENTS.md` があり、そのコマンドは `plans/lint_plans.py plans` のように `plans/` 前提で書かれている。フォルダ名を変えると導入先でパスが合わない。threads の AGENTS.md に「plans の guides 内の `plans/` は `threads/planning/` と読み替える」と明記し、lint コマンドは threads の AGENTS.md に正しいパスで載せる。plans 側の文面は変えない。
- **場面表の分担**: プランの作成・実行の場面は plans の AGENTS.md へリンクするだけにし、threads のガイドに plans のルールを再掲しない（正本の一意性、評価基準5）。
- **plans 規約の上書き**: Step 2 で決めた「スレッド所属プランの後片付け」（`open` / `paused` の間は削除しない。クローズ時に完了要約を `log.md` に追記し、`plans:` と `thread:` を外して一括削除。`abandoned` では未完了プランごとに削除か単独プラン化を選ぶ）は、threads のガイドで「plans の『完了後の後片付け』に対する追加ルール」として書き、threads 側が優先することを明記する。
- **AGENTS.md の行数**: 常時ロードは150行以内。plans の AGENTS.md も同じフォルダ階層で読まれるため、合計の読み込み量も意識し、threads の AGENTS.md には plans の内容を要約しない。
- **Junction と inspect_template.py**（Step 1 で確認済み）: Python 3.11〜3.13 の `rglob` は Junction をたどり、plans のファイルを全部二重に拾って重複として報告する。上記の修正で飛ばす。修正後に `inspect_template.py core/plans` の出力が変わらないことも確かめる。
- **導入手順**: README は「`core/threads` を `threads/` にコピーし、`core/plans` を `threads/planning/` としてコピー」と書く（overview の決定事項）。plans を単独で導入済みのリポジトリ向けに、既存の `plans/` を `threads/planning/` へ `git mv` し、ルートの指示ファイルの1行を差し替える移行手順も書く。`robocopy /XJ` は Junction を飛ばすので、使う場合も2回目のコピーで補われる。

## ルール更新ポイント

- `core/threads/AGENTS.md`「このテンプレートを編集するとき」（このステップ）: `planning/` は `core/plans` への Junction で正本は `core/plans`（Junction 経由の編集も同じファイルを変える）／無ければ `link_plans.py` を実行する／ガイドの表 ⇔ `lint_threads.py` の定数を同時に更新する

## 実行中に判明した変更

- 2026-11-13（Step 1 完了時）: plans の取り込み方式が B（Junction＋`.gitignore`）に確定。「触るファイル」に `link_plans.py`・`.gitignore`・`inspect_template.py` の修正を、注意点に走査と導入手順を反映。
- 2026-11-13（Step 2 完了時）: フォルダ名とガイド3本のファイル名・役割、後片付けの上書きルール、移行手順を反映。
- 2026-11-13（Step 3 完了時）: 計画どおり作成。`link_plans.py` に `--check`（状態の確認のみ）を追加し、Python 3.11 でも動くよう Junction は `st_reparse_tag` で判定した（`inspect_template.py` も同じ）。lint の定数名を `THREAD_STATUSES` / `THREAD_SECTIONS` / `LOG_KINDS` に決めてガイドと AGENTS.md に書いた。クローズ時にプランを削除すると `log.md` の過去エントリのリンクが切れるため、「`closed` / `abandoned` の `log.md` はリンク切れを検査しない」と thread-closing.md に書いた（実装は Step 4）。AGENTS.md の「サンプル」表と `references/example.md`・`lint_threads.py` は雛形のまま Step 4 へ残した。検証結果は [progress/03-scaffold-notes.md](progress/03-scaffold-notes.md)。

## 進め方

- **実行主体**: メインエージェント。guides の文面はユーザーの合意内容（Step 2）から逸脱しない。
- **TODO化**: (1) 雛形生成と plans の取り込み（`link_plans.py`・`.gitignore`・`inspect_template.py`）、(2) guides、(3) AGENTS.md / CLAUDE.md / README.md、の3項目（各1コミット単位）。
