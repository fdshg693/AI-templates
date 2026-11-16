---
type: Plan
status: planning-research
---

## 実装ステータス

- [ ] [01-research-junction.md](01-research-junction.md) — Junction の git・コピー・スクリプト上の挙動を調査し、取り込み方式を確定
- [ ] [02-design-thread-format.md](02-design-thread-format.md) — 要件の合意とスレッドの書式・状態値・プラン連携ルールの確定
- [ ] [03-scaffold-and-guides.md](03-scaffold-and-guides.md) — 雛形生成・plans の取り込み・guides と入口ファイル（AGENTS/CLAUDE/README）
- [ ] [04-references-and-lint.md](04-references-and-lint.md) — 記入例（スレッド＋所属プラン）と `lint_threads.py`
- [ ] [05-verify-and-register.md](05-verify-and-register.md) — 検証・レビュー・リポジトリへの登録

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
| plans の取り込み方式は Step 1 の調査で A/B/C から選ぶ（下記「未決事項」） | Junction が git・他 OS・コピーで期待どおり振る舞うか未確認のため |

## 未決事項（確定するステップ）

- **plans の取り込み方式**（Step 1）: A = Junction をそのままコミット / B = Junction はコミットせず、作成スクリプト（`mklink /J` 相当、POSIX ではシンボリックリンク）で張り `.gitignore` する / C = Junction を使わず実体コピー＋同期検査（`starter/check_starters.py --sync` と同じ方式）。ユーザーの第一希望は Junction。
- **フォルダ名**（Step 2）: 取り込んだ plans のフォルダ名（`plans` 以外。候補: `planning/`、`plan-sets/`）とスレッド置き場の名前（候補: `topics/`、`threads/`）。`core/threads/threads/` のような重複は避ける。
- **完了プランの削除とスレッドのリンク**（Step 2）: plans は完了したプランを削除する運用（[plan-execution.md「完了後の後片付け」](../guides/plan-execution.md#完了後の後片付け)）。スレッドの frontmatter から削除済みプランを指すとリンク切れになる。

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `core/threads/AGENTS.md` / `CLAUDE.md` / `README.md`
- `core/threads/guides/`（スレッド作成・実行中の追記・クローズの場面別ガイド。ファイル名は Step 2 で確定）
- `core/threads/references/`（スレッド1件＋所属プランの記入例。コピー先と同じ構造）
- `core/threads/lint_threads.py`
- `core/threads/{plans フォルダ名}/`（Junction、または方式 B の作成スクリプト／方式 C の実体コピー）

### 変更

- `CLAUDE.md`（リポジトリルート。「core の中身」に1行）
- `core/plans/README.md`（「複数プランにまたがる作業は `threads` で扱う」の1行）
- `.gitignore`（方式 B のときだけ）

## ルール更新ポイント

- `CLAUDE.md`（ルート, Step 5）: 「core の中身」に threads を追記。方式 A/B なら「Junction で plans を取り込んでいる」ことも1行添える（編集時に core/plans を直接直すべきことが分かるように）
- `core/plans/README.md`（Step 5）: threads との境界の1行
- `core/threads/AGENTS.md`「このテンプレートを編集するとき」（Step 3）: 取り込んだ plans は `core/plans` が正本で、threads 側からは編集しないこと

## 進め方

- **TODO化**: ステップ一覧の各項目をそのまま1つのTODOにする。各ステップの実行主体・TODO粒度は各ステップファイルの「進め方」節に書く。
- 作成手順そのものは [template-create スキル](../../.claude/skills/template-create/SKILL.md) に従い、本プランは threads 固有の判断と順序だけを持つ。
