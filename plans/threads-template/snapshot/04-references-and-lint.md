---
type: Plan Step
status: planning-breakdown
---

# Step 4: 記入例（references）と `lint_threads.py`

> [00-overview.md](00-overview.md) の続き。template-create 手順4・5 に相当する。Step 3 の完了が前提。

## やること

コピー先と同じ構造で、スレッド1件とその所属プラン（複数）の記入例を `core/threads/references/` に置き、スレッドとプランの関連付けの整合を検査する `lint_threads.py` を書く。

## 読むべきファイル

- 記入例の粒度（優先）
  - `core/plans/references/postal-code-autofill/00-overview.md` — `order` / `depends_on` / `blocks` を持つ overview
  - `core/plans/references/tag-popularity-sort.md` — 単一ファイル完結プラン
- lint の雛形と前例
  - `.claude/skills/template-create/assets/lint_skeleton.py`
  - `core/plans/lint_plans.py` — `parse_frontmatter`、依存の対応・循環検査（`lint_dependencies`）、`--examples`
  - `core/decisions/lint_decisions.py` — 置き換え関係の双方向検査

## 触るファイル

- 新規: `core/threads/references/{スレッド置き場}/{thread-name}...` — 記入例のスレッド1件
- 新規: `core/threads/references/{plans フォルダ名}/...` — スレッドに所属するプランの記入例（`thread` キー付き）
- 変更: `core/threads/lint_threads.py` — 雛形の `FILE_RULES` / `REQUIRED_FILES` を合わせ、固有検査を足す

## 決定事項・注意点／落とし穴

- **記入例の題材**: 1つのスレッドで「プラン分割 → 実装中の発見 → 仕様変更でプラン追加・順序変更 → 完了済みプランへの手戻り」が一通り読める架空の題材にする。書き方の判断が違うものだけを置く（スレッド1件、フォルダ方式プラン1つ、単一ファイル完結プラン1つ程度）。題材違いを増やさない（評価基準1）。積み重なった状態の例が欲しければ references ではなく starter で作る（本プランの範囲外）。
- **所属プランの記入例の置き場**: `core/plans/references/` には `thread` キー付きの例を足さない（plans 単体の利用者に関係ないため）。threads の references 側に置く。取り込んだ plans フォルダ（Junction 等）の中には置かない — 方式 A/B では `core/plans` に書き込むことになるため。
- **lint の検査項目（候補）**: スレッドの `type` / `status` / 必須見出し／`plans` ⇔ プランの `thread` の対応（片側だけ・リンク切れ・別スレッドへの二重所属）／スレッドのプラン一覧の並び順と `depends_on` の矛盾／経緯エントリの日付書式と時系列順（追記のみの不変条件の機械的な近似）／`closed` のスレッドに未完了プランが残っていない。
- **lint_plans との分担**: プラン自体の検査は `lint_plans.py` に任せる。`lint_threads.py` から `lint_plans.py` を呼んで1コマンドで両方を検査するかは実装時に決める（呼ぶ場合も plans 側のコードは変更しない）。`--examples` では、references の所属プランに対して `lint_plans.py --examples` も通ることを確認する。
- **frontmatter パーサ**: `lint_plans.py` と同じ最小パーサ（標準ライブラリのみ）にする。コピー先で plans が無い構成は想定しない。

## ルール更新ポイント

- `core/threads/AGENTS.md`「サンプル」節（このステップ）: 成果物 → 記入例の表
- ガイドの必須見出し・状態値の表と `lint_threads.py` の定数に「このガイドと同期」のコメント

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: (1) 記入例、(2) lint、(3) 動作確認（references で通る／スクラッチパッドにコピーして `thread` を片側だけ消す・`status` を崩すと失敗する）、の3項目。
