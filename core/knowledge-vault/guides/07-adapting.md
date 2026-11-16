# 自分のリポジトリに導入する手順

導入手順の正本はこのファイル。

## 手順

1. [01-philosophy.md](01-philosophy.md) と [02-layout.md](02-layout.md) を読み、何を「エンティティ」にし、何で「scope」を切るかを決める（下の「決めること」）。
2. `references/` の**中身**を新しいリポジトリのルートにコピーする。`references/` はコピー先と同じ構造なので、パスはそのまま対応する。
3. `tools/vault/schema.py` の「# --- 導入先で書き換える ---」の印がある定義を、自分の題材に合わせて書き換える。
   - `SCOPES`: scope 名と説明
   - `ENTITY_STATUS`: ステータスの値・ラベル・分類・並び順・除外範囲
   - `EVENT_KINDS`・`EVIDENCE_LEVELS`
   - `RECENT_DAYS`（ダッシュボードの「最近の出来事」の日数）・`EVENT_DIGEST_DAYS`（イベントログを `digests` に畳むまでの日数）
   - `DASHBOARD_COLUMNS`（進行中の一覧に足す列）・`DASHBOARD_GROUP_BY`（一覧を小見出しで分ける enum のキー）
   - `_ENTITY` の `fields`: 題材固有の構造化値（サンプルの `cost_min` / `cost_max` / `cost_note` など）
4. `vault/scopes/` のフォルダ名を `SCOPES` に合わせ、サンプルのエンティティ・イベント・コンタクト・トリアージ・台帳を削除する（書き方の参考に1件残して、最初の実データを書いたら消してもよい）。`dashboard.md` はマーカーだけ残す。
5. `vault/_templates/` と `vault/AGENTS.md` の本文セクション・用語を題材に合わせる。ルート `README.md`・`AGENTS.md` の `（…）` を埋める。
6. 使わない仕組みを削除する（下の「削ってよいもの」）。
7. 生成物と一覧を作り直し、検証を通す。

   ```sh
   uv run tools/vault/gen_schema_doc.py
   uv run tools/vault/build_dashboard.py --all
   uv run tools/vault/validate.py --summary --strict
   ```

8. commit フックに検証を登録する（[03-schema.md](03-schema.md) の例）。
9. 実際に1件目の対象を、`check_entity.py` → `_templates/entity.md` からの作成 → 検証 → ダッシュボード更新、の流れで記録してみる。運用しづらければ、その場で `vault/AGENTS.md` と `schema.py` を直す（ルールが実態と合わなくなるのが一番よくない）。

前提: Python 3.11 以上と [uv](https://docs.astral.sh/uv/)。各スクリプトは PEP 723 のインラインメタデータで依存（PyYAML）を宣言しているので、`uv run tools/vault/<script>.py` で仮想環境の準備なしに動く。uv を使わないなら `pip install pyyaml` して `python tools/vault/<script>.py` でよい。

## 決めること

| 決めること | 問い | サンプルでは |
| --- | --- | --- |
| エンティティ | 「1件1フォルダ」で追いかけ、状態が変わっていく単位は何か | 導入を検討するツール・サービス |
| scope | 条件の前提が丸ごと変わる軸はあるか（無ければ `main` 1つ） | 業務用 / 個人用（費用の負担者） |
| ステータス | どんな段階を経て、どう終わるか。誰が決めて終わったかを分けるか | 調査中 → 比較検討中 → 試用中 → 採用 / 見送り / 不可 / 除外 |
| イベント | 1回ごとに一次情報を残したい出来事は何か | 調査メモ・打ち合わせ・試用・レビュー・振り返り |
| 構造化値 | 一覧で絞り込み・並べ替えしたい値は何か。単位は | 費用（円/月）、適合度（0〜100 の幅） |
| コンタクト | 情報をくれる人・経路を評価する必要があるか | 営業担当（紹介された対象の一覧） |
| 圧縮の期間 | 終了から何日で台帳に畳むか。続いている対象のイベントログを何日で要約に畳むか | 14 日（`compact.py` の `DEFAULT_OLDER_THAN_DAYS`）・90 日（`EVENT_DIGEST_DAYS`） |
| 一覧の見せ方 | 「最近」は何日か。進行中の一覧に何の列を出し、何で分けるか | 30 日・適合度と費用・分けない |

## 削ってよいもの

| 仕組み | 削るときに消すもの |
| --- | --- |
| contacts | `vault/contacts/`、`_templates/contact.md`、`schema.py` の `_CONTACT` と `_ENTITY` の `contact`、`vaultlib.py` の contact の関係検査、`compact.py` の `contact` |
| triage | `scopes/*/triage/`、`schema.py` の `_TRIAGE`、`check_entity.py` と `compact.py` の triage 処理 |
| 派生文書 | `profile/en/`、`_NOTE` の `source_file` / `source_updated_at` と `vaultlib.py` の同期検査 |
| 外部スナップショット | `data/{source}/`、`build_index.py` の `SNAPSHOT_GLOB` |
| scope の分割 | `SCOPES` を1つにする（フォルダ構成はそのまま） |

削ったら `validate.py` と各 CLI が動くことを確かめる。

## スクリプトで確認できないチェックリスト

- [ ] 各 scope の `README.md` に、どちらの scope に入れるかの判定基準が書いてある
- [ ] `vault/AGENTS.md` の本文セクション名と `_templates/` の見出しが一致している
- [ ] `internal` にすべきファイル（本音・足切り条件）に `visibility: "internal"` が付いている
- [ ] `data/vault_index.sqlite` が `.gitignore` に入っている
- [ ] ルートの `AGENTS.md` から `vault/AGENTS.md` を読むよう指示している
- [ ] リポジトリを公開するなら、`vault/`・`data/` が同期対象から外れている（[05-derived.md](05-derived.md)）
