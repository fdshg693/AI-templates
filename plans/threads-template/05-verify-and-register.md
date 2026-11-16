---
type: Plan Step
status: implementing-done
---

# Step 5: 検証・レビュー・リポジトリへの登録

> [00-overview.md](00-overview.md) の続き。template-create 手順7・8 に相当する。

## やること

template-create 手順7の検証を通し、典型タスクで入口から辿れることを確かめたうえで、ルート `CLAUDE.md` と `core/plans/README.md` に登録する。

## 読むべきファイル

- `.claude/skills/template-create/SKILL.md` — 手順7・8
- `.claude/skills/template-review/SKILL.md` — 手順3（典型タスクを想定して辿る）と評価基準
- `CLAUDE.md`（ルート）— 「core の中身」の書き方

## 触るファイル

- 変更: `CLAUDE.md`（ルート）— 「core の中身」に threads を1行
- 変更: `core/plans/README.md` — 「複数プランにまたがる作業・手戻りの経緯は `threads` で扱う」の1行

## 決定事項・注意点／落とし穴

- 検証コマンド（リポジトリルート）:
  - `uv run core/threads/lint_threads.py --examples core/threads/references`
  - `uv run core/plans/lint_plans.py --examples core/threads/references/planning`
  - `uv run .claude/skills/template-review/scripts/inspect_template.py core/threads`（Junction を張った状態で実行し、plans のファイルが混ざらないことを見る）
  - `git status --short` に `core/threads/planning/` が出ないこと
  - 導入手順の確認: スクラッチパッドへ README の手順どおりにコピーし、`threads/planning/` が実体であること・導入先のパスで lint が通ることを見る
- 典型タスクは「既存の2プランにまたがる仕様変更が実装途中で発生した」を想定し、threads の AGENTS.md → ガイド → plans の該当ガイドの順に辿って着手できるかを見る。
- **plans 側の lint**: `core/plans/README.md` を変更したら `uv run core/plans/lint_plans.py --examples core/plans/references` も通す。plans に対応するスターターは無いが、`uv run starter/check_starters.py` も念のため通す。
- **ルートの `plans/`**: 本プランを置いているリポジトリルートの `plans/` は `core/plans` のコピー（コミット `2f54664` で追跡済み。Step 1 で確認）。threads 作成とは無関係なので触らない。本プランの完了後の扱い（削除・コミット）はユーザーに確認する。

## ルール更新ポイント

- `CLAUDE.md`（ルート）: 「core の中身」に1行。「plans は Junction で取り込んでおり正本は core/plans、clone 後に `uv run core/threads/link_plans.py` を1回実行する」も添える
- `core/plans/README.md`: threads との境界の1行

## 実行中に判明した変更

- 2026-11-13（Step 1 完了時）: plans の取り込み方式が B（Junction＋`.gitignore`）に確定。`.gitignore` を Step 3 へ移し、検証コマンドに Junction・導入手順の確認を追加。ルートの `plans/` は追跡済みだったので記述を修正。
- 2026-11-13（Step 2 完了時）: 検証コマンドのフォルダ名を `planning` に確定。
- 2026-11-13（Step 3 完了時）: inspect の結果で想定どおり残る指摘: `AGENTS.md` → `planning/AGENTS.md` は Junction の先を指すので「フォルダ外リンク」、`README.md` → `../plans` は他テンプレートへの依存を明記したもの、`guides/thread-writing.md` のコードブロック内の例のリンク（inspect はコードブロックを除外しない）。この3種は許容して、それ以外を0にする。
- 2026-11-13（Step 4 完了時）: `uv run core/threads/lint_threads.py core/threads`（`--examples` なし）は `README.md` → `../plans` の2件をフォルダ外リンクのエラーにする。README は導入先にコピーしないので想定どおりで、テンプレート置き場では `--examples` の2コマンドだけを検証に使う。導入手順の確認（スクラッチパッドでのコピーと lint）は Step 4 で一度通している（[progress/04-references-lint-notes.md](progress/04-references-lint-notes.md)）。
- 2026-11-13（Step 5 完了時）: 典型タスクを確認したところ、どのスレッドにも所属していない既存プランを束ねる手順がなかったので、`thread-writing.md` の基準と手順4に追記した。検証・完了記録は [progress/05-verify-register-notes.md](progress/05-verify-register-notes.md)。

## 進め方

- **実行主体**: 検証はメインエージェント。template-review 相当の評価はサブエージェントに1回依頼してよい（指摘のみ受け取り、修正判断はメイン）。
- **TODO化**: (1) 検証コマンド、(2) 典型タスクでの確認と修正、(3) 登録、の3項目。最後に template-create の「報告」形式でユーザーへ報告する。
