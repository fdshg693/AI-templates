## `knowledge-vault` の作業規約

情報集約・長期管理のためのテンプレート。考え方を説明する `guides/` と、コピー先と同じ構造の実例一式 `references/` に分かれる。人間向けの概要は [README.md](README.md)。

**`references/` 配下の `AGENTS.md` / `CLAUDE.md` は、コピー先で使う成果物（サンプル）であり、このフォルダで作業するときのルールではない。** このフォルダでの作業ルールは本ファイルだけに書く。

### 場面別の参照先

| 場面 | 読む場所 |
| --- | --- |
| 原則を確認・変更する | [guides/01-philosophy.md](guides/01-philosophy.md) |
| フォルダ構成・ドキュメント種別を変える | [guides/02-layout.md](guides/02-layout.md) と `references/tools/vault/schema.py` の `KINDS` |
| スキーマ・検証の仕組みを変える | [guides/03-schema.md](guides/03-schema.md) と `references/tools/vault/` |
| ステータス・圧縮・重複チェックの流れを変える | [guides/04-lifecycle.md](guides/04-lifecycle.md) と `references/vault/AGENTS.md` |
| ダッシュボード・索引・派生文書を変える | [guides/05-derived.md](guides/05-derived.md) |
| AI 向けの決まり・CLI 規約を変える | [guides/06-ai-collaboration.md](guides/06-ai-collaboration.md) と `references/AGENTS.md` |
| 導入手順・書き換え箇所を変える | [guides/07-adapting.md](guides/07-adapting.md) |

### 編集時のルール

- `guides/` と `references/` を対で更新する。guides で説明している仕組みを変えたら、対応する `references/` のファイル（スキーマ・CLI・サンプル・`references/vault/AGENTS.md`）も同じ変更に合わせる（逆も同様）。
- `references/` には特定の題材に依存しない書き方をする。サンプルの題材（ツール・サービスの導入検討）は、導入先で置き換える前提の例として扱い、`schema.py` の「# --- 導入先で書き換える ---」の印の範囲に閉じ込める。印の範囲を変えたら [guides/07-adapting.md](guides/07-adapting.md) の手順3を合わせる。
- `references/` はコピー先と同じ構造に保つ（`references/` 内のパス＝コピー先のパス）。`references/` 内のリンクは `references/` の外（`guides/` 等）を指さない。
- `references/` 内の各階層で、`AGENTS.md` を正本、`CLAUDE.md` を `@./AGENTS.md` の1行にする関係を崩さない。
- ルール文書（`references/AGENTS.md`・`references/vault/AGENTS.md`・guides）にスキーマのフィールド表を書き写さない。正は `schema.py`、一覧は生成物 `references/docs/vault-schema.md`。
- `guides/` / `references/` を編集したら、`references/` で次を実行し、エラー 0・差分なしで終わることを確認する。生成物（`docs/vault-schema.md`・`dashboard.md` のマーカー区間）に差分が出たらその結果をコミットする。

  ```sh
  cd references
  uv run tools/vault/validate.py --summary --strict --today 2026-10-20
  uv run tools/vault/gen_schema_doc.py --check
  uv run tools/vault/build_dashboard.py --all --today 2026-10-20
  ```

  終わったら `references/data/vault_index.sqlite` と `__pycache__/` を消す（コピー先に持ち込まない）。
- サンプルの日付は 2026-10-20 時点の状態として書いてある（期限切れ・圧縮候補の判定がこの日付を前提にしている）。日付を変えるなら `--today` も合わせる。
- このフォルダでテンプレートを使った実作業はしない。試すときは別の場所にコピーする。
- `references/` を変えたら、テンプレート集ルートで `uv run starter/check_starters.py --sync` を実行し、このテンプレートを使うスターター（`starter/knowledge-vault-*`）にも反映する。
