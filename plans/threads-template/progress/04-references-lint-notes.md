# Step 4 実装メモ: 記入例と `lint_threads.py`

## 作成・変更したファイル

- 新規: `core/threads/references/topics/article-scheduled-publishing/00-thread.md`・`log.md`
- 新規: `core/threads/references/planning/article-publish-state/`（`00-overview.md`・`01-schema-and-domain.md`・`02-editor-and-feeds.md`・`progress/99-completion.md`）
- 新規: `core/threads/references/planning/publish-at-utc.md`
- 削除: `core/threads/references/example.md`（雛形）
- 変更: `core/threads/lint_threads.py`（雛形を置き換え）、`core/threads/AGENTS.md`「サンプル」表

## その場で決めた細かい判断

- 題材「記事の予約公開」で、`log.md` に 計画 → 発見 → 仕様変更 → 手戻り → 順序変更 を一通り入れた。`[完了]` は `open` の例では出ないので、AGENTS.md のサンプル節に「closed / abandoned は thread-closing.md の手順で読み替える」と書いた（plans の「サンプルは完了状態」と同じ扱い）。
- 所属プランはフォルダ方式（完了済み・残している）と単一ファイル完結（手戻りで追加・実行中）の2つ。3つ目は `（未作成）` 行で、`plans:` に載らないリンクなし行の書き方を示す。
- 記入例の `depends_on` は使っていない（完了済みプランへの依存は意味が無いため）。`plans:` の並びの検査はスクラッチパッドで確認した。
- references から guides へのリンクは張らない（コピー先で references の外になる。lint の `--examples` でもフォルダ外リンクになる）。ガイド名は本文で触れるだけ。
- `lint_threads.py` は `lint_plans.py` を呼ばない。理由: 2コマンドは既に AGENTS.md・README・ガイドに書いてあり、呼ぶと plans 側の出力形式・終了コードに依存する。
- 追加した検査: `log.md` の最初のエントリは `[計画]`（thread-writing.md 手順3）／`log.md` に `status` を書かない／Plan Step に `thread:` を書かない／どのスレッドの `plans:` にも載らない `thread:`／`topics/` 直下のファイルとケバブケースでないフォルダ名。
- リンク・パスの解決は `Path.resolve()` ではなく `os.path.normpath(os.path.abspath())`。テンプレート集で `planning/AGENTS.md` が Junction の先（`core/plans`）に解決されてフォルダ外扱いになるのを避けるため。
- `planning/` はプラン列挙のための1階層 `iterdir`（＋各フォルダの `[0-9][0-9]-*.md`）だけで、再帰しない。
- `--examples` なしのときは `AGENTS.md`・`CLAUDE.md` の存在と、ルート直下と `guides/` の `.md` のリンクも見る。`references/` は `--examples` なしでは検査しない（記入例は `--examples` で検査する）。

## 検証

```text
# 記入例
lint_threads.py --examples core/threads/references          -> 2 files checked, 0 errors
lint_plans.py --examples core/threads/references/planning   -> checked 2 plan(s): 0 error(s)

# スクラッチパッドで崩す（すべて exit=1、期待どおりのメッセージ）
プランの thread: を削除                -> plans: の ... に thread: が無い（片側だけ）
status: active                         -> status は ... のいずれか
## 未解決事項 を改名                   -> '## 未解決事項' 節がない
status: closed（後片付けなし）          -> plans: は空に / 最後は [完了] / 所属プランごとの [完了]
プラン一覧の2行を入れ替え              -> プランへのリンクが plans: と同じ順で一致しない
log の最後を 2026-10-05 [メモ] に       -> 種別不正 / 日付が昇順でない
同じ plans: のスレッドをもう1つ         -> 片側だけ（x2）/ 複数のスレッドの plans: に載っている（x2）
1つ目が2つ目に depends_on              -> 後ろに置く
Plan Step に thread:                   -> overview にだけ書く
log.md を削除                          -> 必須ファイルがない（00-thread.md の log.md リンク切れも）

# 正常系の closed（プラン削除・plans: []・[完了] x2・log.md に削除済みプランへのリンクが残る） -> 0 errors

# README の手順どおりスクラッチパッドへ導入
導入直後: lint_threads.py threads / lint_plans.py threads/planning -> ともに 0 errors
記入例を topics/・planning/ に置く -> lint_threads 0 errors、lint_plans は snapshot/ 無しの1件だけ（記入例に snapshot を置かない plans の仕様どおり）

# テンプレート集（Junction あり）
link_plans.py --check -> ok
lint_threads.py core/threads -> README.md の ../plans へのリンク2件のみ（README はコピーしないので想定どおり）
inspect core/threads -> 常時ロード 65 行 / 到達不能 0 / リンク切れ 0 / TODO 0、フォルダ外リンクは Step 3 と同じ既知の6件
```

## 完了記録

- **完了範囲**: 記入例（スレッド1件・所属プラン2つ）、`lint_threads.py`、AGENTS.md「サンプル」表。
- **検証結果**: 上記のとおり。記入例は両 lint でエラー0、崩した10パターンはすべて失敗、導入手順のシミュレーションも通った。
- **計画との差分**: 検査項目を5つ追加（上記）。`lint_plans.py` は呼ばない方に決めた。
