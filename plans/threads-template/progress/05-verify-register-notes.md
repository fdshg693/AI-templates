# Step 5 検証・登録メモ

## 検証

```text
link_plans.py --check                                              -> ok
lint_threads.py --examples core/threads/references                 -> 2 files checked, 0 errors
lint_plans.py --examples core/threads/references/planning          -> checked 2 plan(s): 0 error(s)
lint_plans.py --examples core/plans/references                     -> 0 error(s), 2 warning(s)（依存先が references に無いという既存の warning。変更前も同じ）
starter/check_starters.py                                          -> 2 starters checked, 0 errors
inspect core/threads -> 常時ロード 65 行 / 到達不能 0 / リンク切れ 0 / TODO 0、フォルダ外リンクは既知の6件のみ
git status --short   -> core/threads/planning は出ない

# README の手順どおりスクラッチパッドへ導入
threads/planning は実体のフォルダ
lint_threads.py threads / lint_plans.py threads/planning / lint_threads.py --examples threads/references -> すべて 0 errors
```

## 典型タスクでの確認

「既存の2プランにまたがる仕様変更が実装途中で発生した」を想定し、AGENTS.md → thread-updating.md（表の「要求・スコープの変更」行）→ plans の plan-execution.md 手順4・5 と辿った。2プランがすでに同じスレッドに所属していれば、この順で着手できた。

足りなかった点: 2プランがどのスレッドにも所属していない場合。thread-writing.md の「スレッドを立てる基準」にも手順4（新しくプランを書く場合だけ）にも、既存プランを束ねる場合の記述がなかった。直したこと:

- 「スレッドを立てる基準」に「スレッドに所属していない既存のプラン2つ以上に、同じ事実の発覚・仕様変更が影響する」を追加
- 手順4に「既存のプランを束ねるときは、書く代わりに同じ3か所を更新し、きっかけはプラン本文へ反映してから `[発見]` / `[仕様変更]` で追記する」を追加

## 登録

- ルート `CLAUDE.md`「core の中身」に threads の1行（Junction で取り込んでいることと、clone 後の `link_plans.py`）
- `core/plans/README.md` の冒頭の箇条書きに「**境界**」の1行

template-review 相当のサブエージェントによる評価は実施していない（任意の項目のため）。

## 完了記録

- **完了範囲**: Step 5 の (1) 検証コマンド、(2) 典型タスクでの確認と修正、(3) 登録。これで全ステップが完了。
- **検証結果**: 上記のとおり、すべてエラー0。
- **計画との差分**: thread-writing.md に、既存プランを束ねる場合の記述2点を追加。template-review のサブエージェント評価は省略。
