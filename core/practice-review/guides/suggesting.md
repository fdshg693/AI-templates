# 次の題材を提案する

学習者に「次は何を練習すればいい？」と聞かれたとき、またはレビューの後に `current` の Suggestions の `covers_through` がレビュー済みの最新のセッションより古いとき（`index.md` で比べられる）に読む。

## 作るもの

`suggestions/YYYY-MM-DD-{slug}.md`（Suggestions）。書式は [formats.md「出力」](formats.md#出力feedback-digests-suggestions)。作ると、前の Suggestions は `superseded` になる。

## 守ること

- 未レビューのセッションがあれば、先に [reviewing.md](reviewing.md) を済ませる。反映していない練習を前提に提案すると、同じ題材を重ねたり、直った誤りを狙ったりするため。
- 読むのは `profile.md`、`current` の Digest と Feedback だけ。これまでの題材は、`sessions/` のファイル名（日付と slug）で確かめ、本文は開かない。

## 手順

1. `profile.md` の「目標とレベル」「繰り返している誤り」と、`current` の Digest・Feedback を読む。
2. `sessions/` のファイル名を一覧し、最近練習した題材を確かめる。
3. 雛形を作る。

   ```bash
   uv run practice-review/practice.py new suggestions practice-review --slug {slug}
   ```

4. 題材を2つ以上書く。各題材に次を書く。
   - ねらい: `profile.md` の「繰り返している誤り」または「目標」のどれに効くか
   - 使ってみる表現: 「取り入れたい表現」「定着させたい表現」から選ぶ
   - 練習相手への最初のメッセージ: 学習者がそのまま貼り付けられる文。練習する言語で書き、コードブロックに入れる
5. 直近3セッションと同じ題材は、ねらいが違う場合だけ選ぶ。
6. lint を実行し、エラー0にする。学習者には題材の見出しと、ファイルへのリンクを伝える。

## 完了条件

- [ ] `## 提案` に `###` の題材が2つ以上あり、各題材に3項目がそろっている
- [ ] 前の Suggestions が `superseded` になっている
- [ ] lint がエラー0で終わる
