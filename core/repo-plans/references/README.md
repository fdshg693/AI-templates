# サンプルプラン: 架空リポジトリ `worklog` の3フェーズ通し

> 架空の新規リポジトリ `worklog` を、ラフ案から最初の縦切り、基盤の定着まで実行したと仮定した**記入済みのサンプルプラン**である。実装対象ではない。各ファイルは作業時点のスナップショットなので、完了済みの計画を新規リポジトリへそのままコピーしない。

書式の正本は [plan-format.md](../guides/plan-format.md)、節の骨格は [plan-skeleton.md](../guides/plan-skeleton.md) にある。ここでは、実際の作業で起こりうる具体的な出来事を一つの架空事例で示す。型の説明を繰り返す場所ではない。

**ファイル構成の読み方**: 実際の運用では1計画 = 1ファイル（例: `01-specification-and-technology/01-worklog-first-slice.md`）を更新し続け、状態は `status` で表す。ここでは流れを追えるよう、同じ計画の3時点を時点名のフォルダに分けて保存している。時点フォルダの中は、コピー先の `repo-plans/` と同じパス・ファイル名である。時点フォルダ自体はコピー先に作らない。

```text
references/
  rough/01-worklog-idea.md                        # コピー先と同じ
  drafting/{NN}-{phase}/{MM}-{slice}.md            # 初期案を提示した時点
  revising/{NN}-{phase}/{MM}-{slice}.md            # 回答・レビューを反映した時点
  complete/{NN}-{phase}/{MM}-{slice}.md            # 完了ゲートを満たした時点
  progress/                                       # コピー先と同じ
  next-slice-boundary.md                          # 3フェーズ完了後の振り分けの例
```

## 架空の設定

`worklog` は、ローカルの作業メモを追記し、日付順に一覧する小さなコマンドラインツールである。

- 依頼者: 5人の開発チームのリーダー。Windows 3人、macOS 2人。各自 Python を入れているが、版は 3.11〜3.13 とばらつく。
- 依頼の動機: 日報を書くとき、その日何をしたか思い出せない。
- 事例の途中で実際に起きること: ユーザーが対象外の検索を頼む、Windows で文字化けする、利用者が保存ファイルを手で直して一覧が壊れる、テストが実際のホームディレクトリを汚す、エージェントがスキル化を提案して見送る。

## 読む順序

| フェーズ | drafting | revising | complete |
| -------- | -------- | -------- | -------- |
| ラフ案 | [rough/01-worklog-idea.md](rough/01-worklog-idea.md)（`promoted`） | | |
| 1. 仕様・技術確定 | [初期案と送る質問](drafting/01-specification-and-technology/01-worklog-first-slice.md) | [回答と、混ざった対象外の要望の扱い](revising/01-specification-and-technology/01-worklog-first-slice.md) | [フェーズ2への引継ぎ](complete/01-specification-and-technology/01-worklog-first-slice.md) |
| 2. 最小実装 | [最小実装の提示](drafting/02-minimal-delivery/01-add-and-list.md) | [デモで見つかった問題と改訂](revising/02-minimal-delivery/01-add-and-list.md) | [フェーズ3への引継ぎ](complete/02-minimal-delivery/01-add-and-list.md) |
| 3. 基盤の定着 | [正本の置き場の案](drafting/03-foundation/01-readme-and-rules.md) | [文書と規約のレビュー反映](revising/03-foundation/01-readme-and-rules.md) | [次の縦切りへ渡せる完了状態](complete/03-foundation/01-readme-and-rules.md) |

行ごとに左から右へ読むと、1つの計画ファイルがどう更新されていくかが分かる。最後に [next-slice-boundary.md](next-slice-boundary.md)（完了後に来た二つの要望の振り分け）を読む。

## 詳細記録

[progress/](progress/README.md) には、各フェーズで実行して初めて分かった比較、実装メモ、検証結果を置く。後続作業の正本は各フェーズの計画本文であり、progress は経緯を確認したいときだけ読む。

## `plans/references/` との対応

| 既存コードベース向けの参照例                 | この実行例で対応する場所                                                                                                                                       | 違い                                                                         |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `postal-code-autofill/00-overview.md`        | この `README.md`                                                                                                                                               | repo-plans では機能の概要ではなく、3フェーズ全体の入口を示す。               |
| `postal-code-autofill/rough/01-initial-idea.md` | [rough/01-worklog-idea.md](rough/01-worklog-idea.md)                                                                                                        | 詳細計画前の仮説を残す役割は同じ。                                           |
| `postal-code-autofill/01-research-*.md`      | [フェーズ1](drafting/01-specification-and-technology/01-worklog-first-slice.md) と [progress/01-technology-research.md](progress/01-technology-research.md) | 調査は技術選定と不可分なので、仕様・技術確定フェーズで完了する。             |
| `postal-code-autofill/02-*.md`               | [フェーズ2](drafting/02-minimal-delivery/01-add-and-list.md) と [progress/02-minimal-delivery.md](progress/02-minimal-delivery.md)                           | 最小の縦切りを実装し、利用者へのデモまでを一つのフェーズとして扱う。         |
| `tag-popularity-sort.md`                     | [next-slice-boundary.md](next-slice-boundary.md)                                                                                                               | 新規リポジトリ作成後の小さな機能追加は repo-plans ではなく `plans/` で扱う。 |
| `postal-code-autofill/progress/`             | [progress/README.md](progress/README.md)                                                                                                                       | 詳細記録と計画本文を分ける原則は同じ。                                       |

## 最終状態

- フェーズ1で、用途、対象外、保存形式、実行環境、最初の縦切りをユーザーと合意した。
- フェーズ2で、メモの追加と一覧、空データ時の表示、作成時刻を実装・検証し、デモで見つかった手編集行の問題と日付見出しを反映した。
- フェーズ3で、利用・検証の入口を README に、保存形式変更時の不変条件をエージェント規約に定着した。
- 次に追加する日付絞り込みは `plans/` から、チーム共有の要望は repo-plans のフェーズ1から、それぞれ新しい計画として始める。
