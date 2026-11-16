---
type: Plan Step
status: implementing-done
---

# Step 2: 要件の合意とスレッド書式の確定

> [00-overview.md](00-overview.md) の続き。template-create 手順1（要件を固める）に相当する。決めた内容は Step 3・4 の本文へ反映し、ガイドの正本は Step 3 で書く。

## やること

template-create 手順1の5点（目的と対象外／コピー先／場面一覧／成果物一覧／不変条件）をユーザーと合意し、スレッドの書式・状態値・プランとの連携ルールを確定する。

### 確定内容（2026-11-13 ユーザー合意）

- **目的と対象外**: 複数プランにまたがる変更・手戻り・仕様変更の経緯を束ねる。スレッドを立てる基準は「プランが2つ以上」または「完了済みプランへの手戻りが発生した」。1プランで閉じる作業は plans だけで扱う。設計判断そのものの記録は `core/decisions`、新規リポジトリ立ち上げは `core/repo-plans` の範囲で、スレッドからはリンクするだけにする。
- **フォルダ名**: 取り込む plans は `planning/`、スレッド置き場は `topics/`。テンプレート集では `core/threads/planning` → `core/plans` の Junction、導入先では `threads/planning/`（実体）と `threads/topics/`。
- **コピー先**: 導入先の `threads/`。手順は「`core/threads` を `threads/` にコピーし、`core/plans` を `threads/planning/` としてコピー」。plans を単独で導入済みのリポジトリ向けに、既存の `plans/` を `threads/planning/` へ移す手順（`git mv` とルート指示ファイルの1行の差し替え）を README に書く。
- **場面**: スレッド作成（プラン分割前） / 実行中の追記（事実の発覚・仕様変更・手戻り・プランの追加・順序変更） / スレッドのクローズ（`closed` と `abandoned`）。プランの作成・実行は plans の guides をそのまま使う。
- **成果物（1スレッド＝1フォルダ `topics/{thread-name}/`）**:
  - `00-thread.md`（`type: Thread`）— frontmatter に `status` と `plans:`。必須の `##` 見出しは `目的・スコープ` / `プラン一覧` / `未解決事項`。
  - `log.md`（`type: Thread Log`、`status` なし）— 経緯。エントリは `## YYYY-MM-DD [種別] 見出し` ＋ 1〜3行 ＋ 反映先プランへのリンク。追記のみ。
  - 種別は固定の6値: `計画` / `発見` / `仕様変更` / `手戻り` / `順序変更` / `完了`。
  - スレッド `status` は4値: `open` / `paused` / `closed` / `abandoned`。
  - `plans:` は所属プランの overview（単一ファイル完結ならそのファイル）への相対パスの列で、並び順が予定順。各項目にコメントで役割を書く。プラン側は overview に `thread:`（`00-thread.md` への相対パス）を書く。
  - `プラン一覧` 節は `plans:` と同じリンクを同じ順で並べ、各1行の役割を添える。まだ作っていないプランはリンクなしで「（未作成）」と書いてよい（スレッドに先にプランを書いてから分割する運用のため）。
- **不変条件**: (1) スレッドの `plans:` とプランの `thread:` は対で更新する。(2) `log.md` は追記のみで過去エントリを書き換えない（手戻りの原因を後から追えるようにする）。(3) 発覚した事実は `log.md` に書いたうえで影響プラン本文へも反映する（plans の不変条件を維持）。(4) スレッドに実装手順を書かない（実装はプランの役割）。(5) スレッドが `open` / `paused` の間は所属プランを削除しない。

## 読むべきファイル

- 境界と既存の書式を確認するため（優先）
  - `core/plans/guides/plan-writing.md` — frontmatter、`order` / `depends_on` / `blocks`、snapshot
  - `core/plans/guides/plan-execution.md` — 「実行中に必ず行うこと」「完了後の後片付け」（完了プラン削除との衝突）
  - `core/plans/guides/progress.md` — progress との棲み分け
- 他テンプレートの状態値・追記型記録の前例を見るため
  - `core/decisions/guides/superseding.md` — 本文を書き換えず、新しい記録を足して置き換える考え方
  - `core/knowledge-vault/guides/04-lifecycle.md` — 長期間・大量になった記録の圧縮（digests）

## 触るファイル

- なし（決定内容は Step 3・4 の本文と overview の決定事項・未決事項へ反映した）

## 決定事項・注意点／落とし穴

- **完了プランの削除（合意: 保留→クローズ時に一括削除）**: スレッドが `open` / `paused` の間は、所属プランが `implementing-done` でも削除しない（plans の「依存プラン群が残る場合は削除を保留」と同じ考え方で、作業中は全プランへリンクで辿れる）。クローズ時に、各プランの完了要約を `log.md` に `[完了]` エントリで追記し、`plans:` を空にし、各プランの `thread:` を外してからプランを一括削除する。スレッドのフォルダは記録として残す。plans のガイドは変更せず、threads 側のガイドで「plans の『完了後の後片付け』に対する追加ルール（threads 側が優先）」として書く。
- **`abandoned` のときの未完了プラン**: プランごとに「削除」か「`thread:` を外して単独プランとして続ける」を選び、`log.md` の `[完了]` エントリに書く。どちらでも `plans:` は空にする。
- **順序の正本**: plans では `order` は正本ではなく、着手条件の正本は `depends_on`。`plans:` の並び順は「予定順の表示」とし、lint で「同じスレッド内で A が B に `depends_on` するなら、`plans:` で B が A より前」を検査する。
- **`plans:` と `プラン一覧` 節の二重記載**: plans の overview の `status` ⇔ チェックボックスと同じく、lint で一致（集合と順序）を検査して二重管理の食い違いを防ぐ。
- **snapshot との関係**: 着手済みプランの仕様変更は plans の規約どおりプラン本文を書き換える（snapshot は触らない）。完了済みプランへの手戻りは、スレッドが `open` ならそのプランがまだ残っているので、新しいプランを起こしてスレッドに追加する（完了済みプランの status は戻さない）。
- **`log.md` の肥大化**: エントリは1〜3行とリンクに限り、詳細は影響プランの progress へ置く。knowledge-vault の digests のような圧縮はこの段階では入れない（必要になったら追加する）。
- **方式 B の制約（Step 1）**: `planning` は `.gitignore` に書く固定名。導入先の lint は `uv run threads/planning/lint_plans.py threads/planning`。

## ルール更新ポイント

- なし（このステップでは確定のみ。ルールの正本は Step 3 の guides）

## 実行中に判明した変更

- 2026-11-13（Step 1 完了時）: plans の取り込み方式が B（Junction＋`.gitignore`）に確定。「コピー先」にコピー手順を、注意点に方式 B によるフォルダ名の制約を反映。
- 2026-11-13（Step 2 完了時）: 素案を「確定内容」に置き換えた。素案から変えたのは、1スレッド＝1フォルダ（`00-thread.md` ＋ `log.md`）にした点と、完了プランを「open 中は保留→クローズ時に一括削除」に決めた点。素案は [snapshot/02-design-thread-format.md](snapshot/02-design-thread-format.md) に残っている。

## 進め方

- **実行主体**: メインエージェントが素案を詰め、AskUserQuestion などでユーザーと合意する（未決事項3点を含む）。
- **TODO化**: (1) 既存ガイドの確認、(2) 5点とフォルダ名・削除ルールの合意、(3) Step 3・4 の本文更新、の3項目。
