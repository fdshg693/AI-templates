---
type: Plan Step
status: implementing-done
---

# Step 1: Junction の挙動調査と取り込み方式の確定

> [00-overview.md](00-overview.md) の続き。このステップではテンプレートのファイルは作らない。結論は後続ステップ（02〜05）の本文と overview の決定事項へ直接反映する。

## やること

`core/threads/{plans フォルダ名}` → `core/plans` の Junction が、(1) git への記録、(2) 他 OS・別パスでの clone、(3) 導入先へのコピー、(4) 同梱スクリプトの走査で期待どおり振る舞うかを確かめ、overview の方式 A/B/C から1つを選ぶ。

## 調査観点・キーワード

- **git への記録形式**: Git for Windows が Junction（`IO_REPARSE_TAG_MOUNT_POINT`）を `git add` したとき、ディレクトリとして中身を追跡するか、シンボリックリンク（mode 120000）として絶対パスを記録するか。`core.symlinks` の設定値で変わるか。キーワード: `git for windows junction mount point symlink`, `mingw_lstat reparse point`
- **clone 後の状態**: 別パス・Linux/macOS に clone したとき、記録された内容がリンク切れ・テキストファイル化しないか
- **導入先へのコピー**: エクスプローラーのコピー、`cp -r`（Git Bash）、`robocopy`（`/XJ` 有無）、`Copy-Item -Recurse` で Junction の中身が実体としてコピーされるか、Junction のまま（元を指したまま）コピーされるか
- **同梱スクリプトの走査**: `Path.rglob` / `iterdir` が Junction をたどるか（Python のバージョン差、`Path.is_junction()` は 3.12+）。対象: `.claude/skills/template-review/scripts/inspect_template.py`（`rglob`）、`starter/check_starters.py`（`rglob`）、`core/plans/lint_plans.py`（`iterdir`）
- **方式 C の既存パターン**: `starter/check_starters.py` の `--sync` と一致検査を threads 用に流用できるか（コピー対象・除外の指定方法）

## 調査方法

- Web 調査は `web-lookup` スキルで行う（ユーザーのグローバル指示）。
- 実挙動はスクラッチパッドに使い捨ての git リポジトリを作って試す（`cmd //c mklink /J` で Junction を作り、`git add` → `git ls-files -s` で mode を確認、コピー各種を実行）。テンプレート集のリポジトリ内では試さない（誤ってコミットしないため）。

## 調査結果

詳細・実験コマンド・参照 URL は [progress/01-junction-research.md](progress/01-junction-research.md)。

- **git**: Git for Windows 2.47 は `core.symlinks` が true でも false でも Junction を普通のディレクトリとして扱い、中身を `core/plans` と二重にコミットする。clone 先では独立した実体2つになる → 方式 A は二重管理になる。`.gitignore` に `core/threads/planning/` を書けば追跡されない。
- **コピー**: `cp -r`・`Copy-Item -Recurse`・`robocopy /E` はどれも中身を実体としてコピーする（導入先は Junction ではなく普通のフォルダになる）。`robocopy /XJ` だけは Junction を飛ばす。
- **走査**: Python 3.11〜3.13 の `rglob` / `os.walk` は Junction をたどる（`is_symlink()` が False のため）。`inspect_template.py` の `rglob` は plans を二重に拾い、重複として報告する。`lint_plans.py` は `iterdir` で1階層だけ見るので影響なし。ripgrep は Junction の下を列挙しない。
- **削除**: `rm -rf`・`Remove-Item -Recurse`・`shutil.rmtree` で Junction を含むフォルダを消しても、リンク先の `core/plans` は残る。

## 判定基準（調査結果から方式を選ぶ）

| 結果 | 方式 |
| ---- | ---- |
| git がディレクトリの中身として追跡し、clone・コピーでも実体になる | A（Junction をコミット）。ただし core/plans と threads 側で同じファイルが二重にコミットされないか確認する |
| git がリンクとして記録する／clone で壊れるが、ローカルでの参照は便利 | B（作成スクリプト＋`.gitignore`）。README に「clone 後に作成スクリプトを1回実行」を書く |
| コピーで Junction のまま残る、またはスクリプトの走査が二重計上・無限ループする | C（実体コピー＋同期検査）。ユーザーに Junction を諦める理由を示して合意を取る |

## 結論: 方式 B（2026-11-13 ユーザー合意）

- A は二重コミットになるため不採用。走査の二重計上は `inspect_template.py` 1か所だけで、Junction を飛ばせば済むので C までは要らない。
- Junction はテンプレート集の中でだけ使う、編集用の窓口と位置づける。導入先へのコピーは実体になるので、導入先は Junction を持たない。
- 後続ステップへの反映: 作成スクリプト・`.gitignore`・`inspect_template.py` の修正は [03](03-scaffold-and-guides.md)、lint の走査は [04](04-references-and-lint.md)、登録と検証は [05](05-verify-and-register.md)、コピー手順は [02](02-design-thread-format.md) と overview の決定事項に書いた。

## 進め方

- **実行主体**: メインエージェントが実験し、判定する。Web 調査だけはサブエージェントに委任してよい（要約と URL だけ受け取る）。方式の採否はユーザーに結論と理由を示して確認する（ユーザーの第一希望が Junction のため、B・C を選ぶ場合は特に）。
- **TODO化**: (1) Web 調査、(2) スクラッチパッドでの実験、(3) 方式の確定と後続ステップへの反映、の3項目。
