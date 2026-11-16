# Step 1 調査ログ: Junction の挙動

環境: Windows 11 Pro 10.0.26200 / Git for Windows 2.47.1 / Python 3.11.14・3.12.12・3.13.9（uv）。実験はスクラッチパッドの使い捨てリポジトリ `jx/repo` で行い、`core/plans`（README.md・guides/a.md）と、`core/threads/planning` → `core/plans` の Junction（`cmd //c "mklink /J core\threads\planning core\plans"`）を作った。

## 1. git への記録

```text
$ git config --show-origin --get-all core.symlinks
file:C:/Program Files/Git/etc/gitconfig  false
file:.git/config                         false

$ git add -A && git ls-files -s
100644 ab0867... 0  core/plans/README.md
100644 01058d... 0  core/plans/guides/a.md
100644 ab0867... 0  core/threads/planning/README.md     ← 同じ blob を別パスで追跡
100644 01058d... 0  core/threads/planning/guides/a.md

$ git rm -r --cached core/threads && git -c core.symlinks=true add -A && git ls-files -s
（上と同じ。mode 120000 にはならない）
```

- Git for Windows 2.47 は、`core.symlinks` の値に関係なく Junction を普通のディレクトリとして扱い、中身をファイルとして二重に追跡する。
- clone すると `core/threads/planning/` は Junction ではなく独立した実体になる。片方だけ編集されると食い違う（二重管理）。
- Git Bash の `ls -la` は Junction をシンボリックリンク（`lrwxrwxrwx ... -> /tmp/.../core/plans/`、絶対パス）として表示するが、git の index はそう記録しない。
- `.gitignore` に `core/threads/planning` または `core/threads/planning/` を書くと、Junction の下のファイルは追跡されない（`git check-ignore -v` で確認）。

## 2. 導入先へのコピー

| 方法 | 結果 |
| ---- | ---- |
| `cp -r`（Git Bash） | 実体のディレクトリになる（ファイル2件） |
| `Copy-Item -Recurse` | 実体（`LinkType` 空、ファイル2件） |
| `robocopy /E` | 実体 |
| `robocopy /E /SL` | 実体（/SL はシンボリックリンク用で、Junction には効かない） |
| `robocopy /E /XJ` | `planning/` 自体がコピーされない |

エクスプローラーのコピーはこの環境では試していない（GUI 操作のため）。

## 3. スクリプトの走査

```text
3.11 / 3.12 / 3.13 共通:
is_symlink False   is_junction True（3.12+、3.11 は属性なし）   is_dir True
rglob('*.md'): plans/README.md, plans/guides/a.md, threads/planning/README.md, threads/planning/guides/a.md
os.walk のファイル数: 4（実体は2）
```

- `Path.rglob` は `**` でシンボリックリンクをたどらないが、Junction は `is_symlink()` が False なのでたどってしまう。Python のどのバージョンでも二重に数える。循環はない（Junction は兄弟を指していて、祖先ではない）。
- リポジトリ内の該当箇所:
  - `.claude/skills/template-review/scripts/inspect_template.py:45` `iter_files` が `root.rglob("*")` を使う。`core/threads` を inspect すると plans のファイルを全部二重に拾い、重複検出（`DUP_MIN_LEN`）・類似度チェックが plans 全体と threads 側の写しを重複として報告する。
  - `starter/check_starters.py:119` `source.rglob("*")`。threads のスターターを作る場合は Junction の下も実体としてコピー・比較される（結果としては実体コピーになり、害はない）。
  - `core/plans/lint_plans.py:317` は `root.iterdir()` で1階層だけ見る。`lint_plans.py core/threads/planning` は問題なく動く。
- ripgrep（`rg --files`、`-L` 付きでも）は Junction の下を列挙しなかった。Claude Code の Grep/Glob で二重ヒットは起きない。

## 4. 削除の安全性

`d/threads/planning` → `d/plans` の Junction を作って `d/threads` を削除し、`d/plans/f.md` が残るかを見た。

| 方法 | `plans/f.md` |
| ---- | ---- |
| `rm -rf`（Git Bash） | 残る |
| `Remove-Item -Recurse -Force` | 残る |
| `shutil.rmtree`（3.13） | 残る |

## 参照

- Git for Windows「Symbolic Links」: https://gitforwindows.org/symbolic-links.html — 既定では symlink を無効化し、`core.symlinks=true` で有効化する。Junction については記載なし（Junction は実験で確認）。
- Python pathlib: https://docs.python.org/3/library/pathlib.html — `**` は既定でシンボリックリンクをたどらない（`recurse_symlinks`, 3.13）。`Path.is_junction()` は 3.12 で追加。
