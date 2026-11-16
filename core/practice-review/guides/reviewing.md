# セッションをレビューする

未レビューのセッションがあるとき（`index.md` の「未レビューのセッション」、または取り込みの直後）、または学習者にフィードバックを頼まれたときに読む。

## 作るもの

- `feedback/YYYY-MM-DD-{slug}.md`（Feedback）。書式は [formats.md「出力」](formats.md#出力feedback-digests-suggestions)
- 対象セッションの frontmatter（`status: reviewed`、`reviewed_in`。`practice.py new` が書き換える）
- `profile.md` の更新

## 守ること

- 読むのは `profile.md` と、未レビューのセッションだけ。レビュー済みのセッション・古い出力は読まない。セッションは増え続けるので、過去の内容は `profile.md` で把握する。学習者が特定の過去のセッションを指定したときだけ、そのファイルを読む。
- 指摘するのは学習者の発言だけ。練習相手（ChatGPT など）の発言は、「取り入れたい表現」の材料にだけ使う。
- セッションの本文は編集しない。出典として、後から同じ文面を確かめられるようにするため。

## 手順

1. `profile.md` を読み、「練習の設定」（フィードバックの言語など）と「繰り返している誤り」を把握する。
2. 未レビューのセッションを古い順に一覧する。

   ```bash
   uv run practice-review/practice.py pending practice-review
   ```

3. 古い順に、最大5件を1つの Feedback の対象に決めて読む。6件以上あれば、この手順3〜6を5件ずつ繰り返す。
4. 雛形を作る。`--sessions` を省くと、古い順に最大5件が対象になる。指定したセッションは `reviewed` になる。

   ```bash
   uv run practice-review/practice.py new feedback practice-review --slug {slug} [--sessions {a},{b}]
   ```

   途中でやめる場合は、作った Feedback を削除し、対象セッションの `status` を `unreviewed`、`reviewed_in` を空に戻して `practice.py refresh` を実行する。

5. `（記入）` を埋める。各節の書き方と行数の上限は [formats.md「本文の節」](formats.md#本文の節)。
6. `profile.md` を更新する。
   - 「繰り返している誤り」: 今回出たパターンの回数と「最後に出た」を更新する。新しいパターンは行を足す。
   - 「定着した表現」: 以前の「取り入れたい表現」を、今回のセッションで学習者が正しく使っていれば移す。
   - 「目標とレベル」: 変化があれば日付付きで書き換える。
   - frontmatter の `updated_at` を今日に、`covers_through` を今回の対象セッションの最新の日付にする。
7. lint を実行する。`current な feedback が N 件ある` の警告が出たら [digesting.md](digesting.md) に進む。
8. 学習者に、Feedback の「要点」を伝える。次の題材を頼まれていれば [suggesting.md](suggesting.md) に進む。

## 完了条件

- [ ] `practice.py pending` の対象にしたセッションが `reviewed` になり、`reviewed_in` が今回の Feedback を指している
- [ ] Feedback に `（記入）` が残っていない
- [ ] `profile.md` の `covers_through` がレビュー済みの最新のセッションの日付以上
- [ ] lint がエラー0で終わる
