# まとめを作る

lint が「current な feedback が N 件ある」と警告したとき（`current` の Feedback が3件以上）、または学習者にまとめを頼まれたときに読む。

## 作るもの

`digests/YYYY-MM-DD-{slug}.md`（Digest）。書式は [formats.md「出力」](formats.md#出力feedback-digests-suggestions)。作ると、反映した Feedback と前の Digest が `superseded` になる（条件は [formats.md「古くなる条件」](formats.md#古くなる条件)）。学習者は、古い Feedback を読み返さずにこの1ファイルだけを読めばよくなる。

## 守ること

- 読むのは `profile.md`、`current` の Digest（あれば）、`current` の Feedback だけ。セッションと `superseded` の出力は読まない（それらの内容はすでに Feedback・Digest・profile に反映されているため）。
- 前の Digest の内容のうち、まだ定着していないものは引き継ぐ。新しい Digest が前の Digest を置き換えるので、引き継がないと学習者の目から消えるため。

## 手順

1. `index.md` の「いま読むもの」から、`current` の Digest と Feedback を確かめて読む。
2. 雛形を作る。`covers_through` は、`current` の Feedback の最新の `covers_through` になる。

   ```bash
   uv run practice-review/practice.py new digest practice-review --slug {slug}
   ```

3. `（記入）` を埋める。
   - 「繰り返している誤り」: `profile.md` の同名の表と Feedback の「直すところ」から、パターン単位でまとめる。回数の多い順に並べる。
   - 「定着させたい表現」: Feedback の「取り入れたい表現」と前の Digest から、`profile.md` の「定着した表現」にまだ無いものを選ぶ。
4. lint を実行し、エラー0にする。`index.md` の「いま読むもの」で、Feedback が新しい Digest に置き換わっていることを確かめる。

## 完了条件

- [ ] 新しい Digest に `（記入）` が残っていない
- [ ] 反映した Feedback と前の Digest が `superseded` で、状態バナーが「古い」になっている
- [ ] lint がエラー0で終わる（`current な feedback` の警告が消えている）
