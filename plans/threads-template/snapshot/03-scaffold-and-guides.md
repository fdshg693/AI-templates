---
type: Plan Step
status: planning-breakdown
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
- 取り込み方式 C を選んだ場合
  - `starter/check_starters.py` — コピー一致検査と `--sync`

## 触るファイル

- 新規: `core/threads/`（`uv run .claude/skills/template-create/scripts/scaffold_template.py core/threads --guides <Step 2 で決めた場面>` で生成）
- 新規: `core/threads/{plans フォルダ名}/` — 方式 A: Junction / B: 作成スクリプト（例 `core/threads/link_plans.py`）＋ `.gitignore` / C: 実体コピー＋同期検査スクリプト
- 新規: `core/threads/guides/*.md` — 場面ごと（スレッド作成／実行中の追記／クローズ）。状態値・経緯の種別・必須見出しの表は1つのガイドにだけ置く
- 新規: `core/threads/AGENTS.md` / `CLAUDE.md` / `README.md`

## 決定事項・注意点／落とし穴

- **plans の AGENTS.md との関係**: 取り込んだ plans には自前の `AGENTS.md` があり、そのコマンドは `plans/lint_plans.py plans` のように `plans/` 前提で書かれている。フォルダ名を変えると導入先でパスが合わない。threads の AGENTS.md に「plans の guides 内の `plans/` は `threads/{plans フォルダ名}/` と読み替える」と明記し、lint コマンドは threads の AGENTS.md に正しいパスで載せる。plans 側の文面は変えない。
- **場面表の分担**: プランの作成・実行の場面は plans の AGENTS.md へリンクするだけにし、threads のガイドに plans のルールを再掲しない（正本の一意性、評価基準5）。
- **plans 規約の上書き**: Step 2 で決めた「スレッド所属プランの後片付け」は、threads のガイドで「plans の『完了後の後片付け』に対する追加ルール」として書き、どちらが優先かを明記する。
- **AGENTS.md の行数**: 常時ロードは150行以内。plans の AGENTS.md も同じフォルダ階層で読まれるため、合計の読み込み量も意識し、threads の AGENTS.md には plans の内容を要約しない。
- **Junction と inspect_template.py**: Step 1 の結果、`rglob` が Junction をたどる場合は plans のファイルが threads の検査対象に混ざる。到達性・行数の判定がぶれるなら、Step 5 での確認方法（除外して読む等）を本文に追記する。

## ルール更新ポイント

- `core/threads/AGENTS.md`「このテンプレートを編集するとき」（このステップ）: 取り込んだ plans は `core/plans` を直す／ガイドの表 ⇔ `lint_threads.py` の定数を同時に更新する

## 進め方

- **実行主体**: メインエージェント。guides の文面はユーザーの合意内容（Step 2）から逸脱しない。
- **TODO化**: (1) 雛形生成と plans の取り込み、(2) guides、(3) AGENTS.md / CLAUDE.md / README.md、の3項目（各1コミット単位）。
