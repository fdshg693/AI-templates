---
type: Plan
status: implementing-done
---

## 実装ステータス

- [x] [01-research-junction.md](01-research-junction.md) — Junction の git・コピー・スクリプト上の挙動を調査し、取り込み方式を確定
- [x] [02-design-thread-format.md](02-design-thread-format.md) — 要件の合意とスレッドの書式・状態値・プラン連携ルールの確定
- [x] [03-scaffold-and-guides.md](03-scaffold-and-guides.md) — 雛形生成・plans の取り込み・guides と入口ファイル（AGENTS/CLAUDE/README）
- [x] [04-references-and-lint.md](04-references-and-lint.md) — 記入例（スレッド＋所属プラン）と `lint_threads.py`
- [x] [05-verify-and-register.md](05-verify-and-register.md) — 検証・レビュー・リポジトリへの登録

# スレッドテンプレート（`core/threads`）作成プラン - 概要

> 元アイデア: [rough/01-initial-idea.md](rough/01-initial-idea.md)

## 要件

- `core/plans` を二重管理せずに内包し、複数プランにまたがる大規模な変更を「スレッド」単位で束ねるテンプレート `core/threads/` を作る。
- スレッドはトピックごとに、所属プラン・プランの順序関係・実装中に判明した事実・手戻り・仕様変更を時系列に記録する。複数プランにまたがる作業は、まずスレッドに書いてからプランへ分割する。
- プラン ⇔ スレッドを frontmatter で双方向に関連付け、同一スレッド内のプラン同士の関係も辿れるようにする。整合は lint で検査する。
- `core/plans` 単体の使い方（スレッドを使わない導入先）は壊さない。

## 実装ステップ

1. [01-research-junction.md](01-research-junction.md) — Junction の挙動調査（git への記録形式、他 OS での clone、導入先へのコピー、同梱スクリプトの走査）。結果で取り込み方式を A/B/C から確定する
2. [02-design-thread-format.md](02-design-thread-format.md) — template-create 手順1の5点をユーザーと合意し、スレッドの書式を確定する
3. [03-scaffold-and-guides.md](03-scaffold-and-guides.md) — 雛形生成、plans の取り込み、guides、AGENTS.md / CLAUDE.md / README.md
4. [04-references-and-lint.md](04-references-and-lint.md) — 記入例と lint
5. [05-verify-and-register.md](05-verify-and-register.md) — inspect・lint・template-review 相当の確認、ルート CLAUDE.md と `core/plans/README.md` への登録

Step 1 と Step 2 は独立して進められるが、Step 2 の「フォルダ名・コピー手順」は Step 1 の結論に依存する。Step 3 以降は 1・2 の完了が前提。

## 主要な決定事項

| 決定 | 理由 |
| ---- | ---- |
| テンプレート名は `core/threads/`（ケバブケース単語、lint は `lint_threads.py`） | template-create の命名規則に合わせる |
| `core/plans` のルール本文は変更しない（変更は README の境界の1行だけ） | plans は単体で使われる。スレッド固有のキー（`thread`）は threads 側のガイドで定義し、`lint_plans.py` が未知キーを無視することを利用する（`parse_frontmatter` は任意キーを受け付け、検査しない） |
| スレッドの順序表・時系列記録は「プラン横断の事実と判断」、plans の progress は「プラン内の詳細根拠」と棲み分ける | 両方に同じ事実を書くと二重管理になる。plans の不変条件「予定外の事実は影響プラン本文へ直接反映」はそのまま守り、スレッドには横断の経緯だけを残す |
| 同一スレッド内のプラン同士の関係は新キーを作らず、共通の `thread` キー＋既存の `order` / `depends_on` / `blocks` で表す | 兄弟プラン一覧を各プランに持たせると、プランの追加・削除のたびに全プランを書き換える二重管理になる。兄弟はスレッド側の一覧から辿れる |
| plans は方式 B で取り込む: `core/threads/planning` → `core/plans` の Junction（POSIX ではシンボリックリンク）を作成スクリプトで張り、ルートの `.gitignore` で追跡から外す（Step 1 で確定） | Git for Windows は Junction を普通のフォルダとして扱い、中身を二重にコミットする（A は不可）。`.gitignore` すれば追跡されず、`cp -r` などで導入先へコピーすると中身は実体になる。詳細は [01](01-research-junction.md#結論-方式-b2026-11-13-ユーザー合意) |
| 導入手順は「`core/threads` をコピーし、`core/plans` を `threads/planning/` としてコピーする」と書き、Junction の有無に頼らない | clone 直後でスクリプトを実行していないと Junction が無い。2回目のコピーは同じ内容の上書きになるだけなので、どちらの状態でも同じ結果になる |
| フォルダ名は取り込む plans を `planning/`、スレッド置き場を `topics/` とする（Step 2 で確定） | `threads/threads/` の重複を避け、導入先の lint コマンド `uv run threads/planning/lint_plans.py threads/planning` が自然に読める |
| 1スレッド＝1フォルダ `topics/{thread-name}/`。`00-thread.md`（`type: Thread`、`status`: `open` / `paused` / `closed` / `abandoned`、`plans:`）と `log.md`（`type: Thread Log`、経緯を追記のみ。種別は 計画・発見・仕様変更・手戻り・順序変更・完了）の2ファイル（Step 2 で確定） | 目的・プラン一覧（読み返す部分）と経緯（増え続ける部分）を分ける。書式の詳細は [02](02-design-thread-format.md#確定内容2026-11-13-ユーザー合意) |
| スレッドが `open` / `paused` の間は所属プランを削除しない。クローズ時に各プランの完了要約を `log.md` へ追記し、`plans:` と各プランの `thread:` を外してから一括削除する（Step 2 で確定） | `plans:` のリンク切れを防ぎ、作業中は全プランへ辿れるようにする。plans の「依存プラン群が残る場合は削除を保留」と同じ考え方で、plans のガイドは変更しない |
| 同梱スクリプトは `planning/` の下を再帰で走査しない。`inspect_template.py` は Junction（`Path.is_junction()`）とシンボリックリンクのディレクトリを飛ばす | Python 3.11〜3.13 の `rglob` / `os.walk` は Junction をたどり、plans のファイルを二重に数える |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `core/threads/AGENTS.md` / `CLAUDE.md` / `README.md`
- `core/threads/guides/`（スレッド作成・実行中の追記・クローズの場面別ガイド: `thread-writing.md` / `thread-updating.md` / `thread-closing.md`）
- `core/threads/references/`（`topics/` にスレッド1件、`planning/` に所属プランの記入例。コピー先と同じ構造）
- `core/threads/lint_threads.py`
- `core/threads/link_plans.py`（`core/threads/planning` → `core/plans` の Junction／シンボリックリンクを張る作成スクリプト。Junction 自体はコミットしない）

### 変更

- `CLAUDE.md`（リポジトリルート。「core の中身」に1行）
- `core/plans/README.md`（「複数プランにまたがる作業は `threads` で扱う」の1行）
- `.gitignore`（`core/threads/planning/` を追加）
- `.claude/skills/template-review/scripts/inspect_template.py`（`iter_files` で Junction・シンボリックリンクのディレクトリを飛ばす）

## ルール更新ポイント

- `CLAUDE.md`（ルート, Step 5）: 「core の中身」に threads を追記。「plans は Junction で取り込んでおり正本は core/plans、clone 後に `link_plans.py` を1回実行する」ことも1行添える
- `core/plans/README.md`（Step 5）: threads との境界の1行
- `core/threads/AGENTS.md`「このテンプレートを編集するとき」（Step 3）: 取り込んだ plans は `core/plans` が正本で、threads 側からは編集しないこと

## 実行中に判明した変更

- 2026-11-13（Step 1 完了時）: plans の取り込み方式が B（Junction＋`.gitignore`）に確定。決定事項に方式 B・導入手順・走査の3行を追加し、未決事項から取り込み方式を削除。変更ファイルに `link_plans.py`・`.gitignore`・`inspect_template.py` を反映。
- 2026-11-13（Step 2 完了時）: フォルダ名（`planning/` / `topics/`）・スレッドの書式（1スレッド＝1フォルダ）・完了プランの削除ルールが確定。決定事項に3行を追加し、未決事項の節を削除。新規ファイル一覧のガイド名・references の構成・`.gitignore` のパスを確定値にした。
- 2026-11-13（Step 3 完了時）: 計画どおり `core/threads/` の雛形・guides・入口ファイル・`link_plans.py` を作成。クローズ時のプラン削除で `log.md` の過去エントリのリンクが切れるため、「`closed` / `abandoned` の `log.md` はリンク切れを検査しない」を Step 4 の lint の検査項目に追加した。
- 2026-11-13（Step 4 完了時）: 計画どおり記入例と `lint_threads.py` を作成。`lint_threads.py` は `lint_plans.py` を呼ばず、検査は2コマンドのままにした（AGENTS.md・README・ガイドの記述と一致）。Step 5 に「テンプレート置き場の `core/threads` を `--examples` なしで lint すると README のフォルダ外リンクが出る（想定どおり）」を追記した。
- 2026-11-13（Step 5 完了時）: 検証はすべて通過し、ルート `CLAUDE.md` と `core/plans/README.md` に登録した。典型タスクの確認で、既存プランを束ねる場合の記述を `thread-writing.md` に追加した。完了記録は [progress/05-verify-register-notes.md](progress/05-verify-register-notes.md)。

## 進め方

- **TODO化**: ステップ一覧の各項目をそのまま1つのTODOにする。各ステップの実行主体・TODO粒度は各ステップファイルの「進め方」節に書く。
- 作成手順そのものは [template-create スキル](../../.claude/skills/template-create/SKILL.md) に従い、本プランは threads 固有の判断と順序だけを持つ。
