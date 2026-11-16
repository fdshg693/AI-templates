---
type: Plan Step
status: implementing-done
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

- 新規: `core/threads/references/topics/{thread-name}/00-thread.md`・`log.md` — 記入例のスレッド1件（`open` の状態で、所属プランが残っている）
- 新規: `core/threads/references/planning/...` — スレッドに所属するプランの記入例（`thread:` キー付き）
- 変更: `core/threads/lint_threads.py` — 雛形の `FILE_RULES` / `REQUIRED_FILES` を合わせ、固有検査を足す

## 決定事項・注意点／落とし穴

- **記入例の題材**: 1つのスレッドで「プラン分割 → 実装中の発見 → 仕様変更でプラン追加・順序変更 → 完了済みプランへの手戻り」が一通り読める架空の題材にする。書き方の判断が違うものだけを置く（スレッド1件、フォルダ方式プラン1つ、単一ファイル完結プラン1つ程度）。題材違いを増やさない（評価基準1）。積み重なった状態の例が欲しければ references ではなく starter で作る（本プランの範囲外）。
- **所属プランの記入例の置き場**: `core/plans/references/` には `thread` キー付きの例を足さない（plans 単体の利用者に関係ないため）。threads の references 側に置く。取り込んだ plans フォルダ（Junction）の中には置かない — `core/plans` に書き込むことになるため。references 側の plans フォルダは実体（Junction ではない）。
- **lint の走査**（Step 1）: `lint_threads.py` は `topics/` と、スレッドの `plans:` が指すファイルだけを読む。`planning/` を `rglob` / `os.walk` で再帰しない（テンプレート集の中では Junction をたどって `core/plans/references` まで拾うため）。プランの列挙が要るなら `lint_plans.py` と同じく1階層の `iterdir` にする。
- **lint の検査項目**（Step 2 で確定した書式に対して）: 各 `topics/{thread-name}/` に `00-thread.md` と `log.md` がある／`type`（`Thread` / `Thread Log`）・`status`（`open` / `paused` / `closed` / `abandoned`）・必須見出し（`目的・スコープ` / `プラン一覧` / `未解決事項`）／`plans:` ⇔ プランの `thread:` の対応（片側だけ・リンク切れ・別スレッドへの二重所属）／`plans:` と `プラン一覧` 節のリンクの集合と順序の一致（リンクなしの「（未作成）」行は除く）／同じスレッド内で A が B に `depends_on` するなら `plans:` で B が A より前／`log.md` のエントリ見出し `## YYYY-MM-DD [種別] 見出し` の書式・種別6値・日付の昇順（追記のみの機械的な近似）／`closed` / `abandoned` のスレッドは `plans:` が空で、`log.md` の最後のエントリが `[完了]`。
- **lint_plans との分担**: プラン自体の検査は `lint_plans.py` に任せる。`lint_threads.py` から `lint_plans.py` を呼んで1コマンドで両方を検査するかは実装時に決める（呼ぶ場合も plans 側のコードは変更しない）。`--examples` では、references の所属プランに対して `lint_plans.py --examples` も通ることを確認する。
- **frontmatter パーサ**: `lint_plans.py` と同じ最小パーサ（標準ライブラリのみ）にする。コピー先で plans が無い構成は想定しない。

## ルール更新ポイント

- `core/threads/AGENTS.md`「サンプル」節（このステップ）: 成果物 → 記入例の表
- ガイドの必須見出し・状態値の表と `lint_threads.py` の定数に「このガイドと同期」のコメント

## 実行中に判明した変更

- 2026-11-13（Step 1 完了時）: plans の取り込み方式が B（Junction＋`.gitignore`）に確定。注意点に「`lint_threads.py` は plans フォルダを再帰で走査しない」を追加。
- 2026-11-13（Step 2 完了時）: references のパス（`topics/` / `planning/`）と lint の検査項目を確定した書式に合わせた。
- 2026-11-13（Step 3 完了時）: ガイドに合わせて lint の定数名（`THREAD_STATUSES` / `THREAD_SECTIONS` / `LOG_KINDS`）と次の検査を確定: `THREAD_SECTIONS` は見出しの順序も前方一致で見る／`closed` / `abandoned` のスレッドの `log.md` はリンク切れを検査しない（クローズ時にプランを削除するため）／`closed` の最後の `[完了]` の前に所属プランごとの `[完了]` がある（数は検査しない）。雛形の `references/example.md` を削除し、AGENTS.md「サンプル」表の TODO 行を記入例で置き換える。
- 2026-11-13（Step 4 完了時）: 題材は「記事の予約公開」（`open`、完了済みプラン1・手戻りの単一ファイルプラン1・`（未作成）` 1）。`lint_threads.py` から `lint_plans.py` は呼ばず、2コマンドのままにした。追加で決めた検査: `log.md` の最初のエントリは `[計画]`、`log.md` に `status` を書かない、Plan Step に `thread:` を書かない、どのスレッドにも載らない `thread:` もエラー。リンクの解決は Junction をたどらない `os.path.normpath` で行う。詳細 → [progress/04-references-lint-notes.md](progress/04-references-lint-notes.md)

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: (1) 記入例、(2) lint、(3) 動作確認（references で通る／スクラッチパッドにコピーして `thread` を片側だけ消す・`status` を崩すと失敗する）、の3項目。
