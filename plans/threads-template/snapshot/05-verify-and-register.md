---
type: Plan Step
status: planning-breakdown
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
- 変更: `.gitignore` — 方式 B のときだけ

## 決定事項・注意点／落とし穴

- 検証コマンド（リポジトリルート）:
  - `uv run core/threads/lint_threads.py --examples core/threads/references`
  - `uv run core/plans/lint_plans.py --examples core/threads/references/{plans フォルダ名}`
  - `uv run .claude/skills/template-review/scripts/inspect_template.py core/threads`
- 典型タスクは「既存の2プランにまたがる仕様変更が実装途中で発生した」を想定し、threads の AGENTS.md → ガイド → plans の該当ガイドの順に辿って着手できるかを見る。
- **plans 側の lint**: `core/plans/README.md` を変更したら `uv run core/plans/lint_plans.py --examples core/plans/references` も通す。plans に対応するスターターは無いが、`uv run starter/check_starters.py` も念のため通す。
- **ルートの未追跡 `plans/`**: 本プランを置いているリポジトリルートの `plans/` は `core/plans` のコピー（未追跡）。threads 作成とは無関係なので触らない。本プランの完了後の扱い（削除・コミット）はユーザーに確認する。

## ルール更新ポイント

- `CLAUDE.md`（ルート）: 「core の中身」に1行。方式 A/B なら「plans は Junction で取り込んでおり、正本は core/plans」も添える
- `core/plans/README.md`: threads との境界の1行

## 進め方

- **実行主体**: 検証はメインエージェント。template-review 相当の評価はサブエージェントに1回依頼してよい（指摘のみ受け取り、修正判断はメイン）。
- **TODO化**: (1) 検証コマンド、(2) 典型タスクでの確認と修正、(3) 登録、の3項目。最後に template-create の「報告」形式でユーザーへ報告する。
