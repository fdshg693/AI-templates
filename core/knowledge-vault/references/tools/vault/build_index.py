# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""vault と data/ のスナップショットから SQLite の派生索引（data/vault_index.sqlite）を作る・検索する.

- 正本は Markdown。索引はいつ消しても作り直せる派生キャッシュで、直接書き込まない。
- 差分更新はせず毎回全件作り直す。一時ファイルに書いてから os.replace で差し替えるので、読み手が途中の DB を読むことは無い。
- 全文検索は FTS5 の trigram（日本語も分かち書き不要）。3文字未満の語を含む検索は LIKE にフォールバックする。
- 全文検索の対象は本文と frontmatter の文字列値（digests の要約・台帳の理由も引っかかる）。
- 絞り込み（--kind / --scope / --tag / --where / --since）だけでも引ける。イベントログは親エンティティの
  タグ・値でも一致する（例: --where area=hobby --kind event で、hobby のエンティティのイベントログ）。
- ensure_index() は正本ファイルの件数・最終更新時刻が索引作成時と変わったときだけ作り直す（読む側はこれを呼ぶ）。
- stdout には DB のパス（検索・絞り込み時はヒットした正本ファイルのパス）だけを出す。

    uv run tools/vault/build_index.py                 # 作り直す
    uv run tools/vault/build_index.py -q キーワード    # 検索（必要なら自動で作り直す）
    uv run tools/vault/build_index.py -q 共有 --kind entity --scope work -s
    uv run tools/vault/build_index.py --kind event --since 2026-10-01 --tag SSO -s   # 新しい順に一覧
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

from schema import ENTITY_STATUS, KINDS
from vaultlib import ROOT, Vault, configure_stdio, emit_paths, load_vault, log, read

SCHEMA_VERSION = 2  # テーブル構成を変えたら上げる（古い索引は作り直される）
SNAPSHOT_GLOB = "data/*/**/*.md"  # 外部から取得したスナップショット（正本ではないが検索対象）
TRIGRAM_MIN = 3

DDL = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE issues (level TEXT, path TEXT, message TEXT);
CREATE TABLE docs (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,        -- schema.KINDS の name、または snapshot
    scope TEXT,
    key TEXT,                  -- エンティティ・コンタクトのフォルダ名
    title TEXT,
    status TEXT,
    status_category TEXT,
    status_order INTEGER,
    updated_at TEXT,
    path TEXT NOT NULL UNIQUE, -- リポジトリルート相対
    ok INTEGER NOT NULL,       -- スキーマ検証に通ったか
    data TEXT NOT NULL         -- フロントマター全体（JSON）。列に無い値は json_extract で引く
);
CREATE INDEX docs_kind ON docs (kind, scope);
CREATE TABLE doc_tags (doc_id INTEGER NOT NULL REFERENCES docs (id), tag TEXT NOT NULL);
CREATE INDEX doc_tags_tag ON doc_tags (tag);
CREATE TABLE names (doc_id INTEGER REFERENCES docs (id), normalized TEXT NOT NULL, raw TEXT NOT NULL);
CREATE INDEX names_normalized ON names (normalized);
CREATE VIRTUAL TABLE search_fts USING fts5 (title, body, doc_id UNINDEXED, tokenize = 'trigram');
"""


def normalize(text: str) -> str:
    """表記ゆれ吸収用の正規化（NFKC・小文字化・空白と記号の除去）."""
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def source_files(root: Path) -> list[Path]:
    files = {p for k in KINDS.values() for g in k.globs for p in root.glob(g)}
    files |= set(root.glob(SNAPSHOT_GLOB))
    return sorted(p for p in files if p.is_file())


def fingerprint(root: Path) -> str:
    files = source_files(root)
    latest = max((p.stat().st_mtime_ns for p in files), default=0)
    return f"v{SCHEMA_VERSION}:{len(files)}:{latest}"


def default_db(root: Path) -> Path:
    return root / "data" / "vault_index.sqlite"


def _json_default(value: object) -> str:
    return str(value)


def _strings(value: object) -> list[str]:
    """frontmatter の文字列値を平らに集める（全文検索用）."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def _insert(conn: sqlite3.Connection, *, kind: str, rel: str, data: dict, body: str, ok: bool,
            scope: str | None = None, key: str | None = None) -> None:
    status = data.get("status") if kind == "entity" else None
    meta = ENTITY_STATUS.get(status) if isinstance(status, str) else None
    title = data.get("title") or data.get("name") or data.get("topic") or Path(rel).stem
    cur = conn.execute(
        "INSERT INTO docs (kind, scope, key, title, status, status_category, status_order, updated_at, path, ok, data)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (kind, scope, key, str(title), status, meta and str(meta.category), meta and meta.order,
         str(data.get("updated_at") or data.get("fetched_at") or ""), rel, int(ok),
         json.dumps(data, ensure_ascii=False, default=_json_default)),
    )
    doc_id = cur.lastrowid
    tags = data.get("tags") if isinstance(data.get("tags"), list) else []
    conn.executemany("INSERT INTO doc_tags VALUES (?, ?)", [(doc_id, str(t)) for t in tags])
    names = [title, key, *(data.get("aliases") or [])] if kind in ("entity", "contact") else []
    conn.executemany("INSERT INTO names VALUES (?, ?, ?)", [(doc_id, normalize(str(n)), str(n)) for n in names if n])
    text = "\n".join([body, *_strings(data)])
    conn.execute("INSERT INTO search_fts (title, body, doc_id) VALUES (?, ?, ?)", (str(title), text, doc_id))


def build_index(root: Path | None = None, db_path: Path | None = None, *, vault: Vault | None = None) -> Path:
    root = (root or ROOT).resolve()
    db_path = db_path or default_db(root)
    vault = vault or load_vault(root)
    fp = fingerprint(root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    conn = sqlite3.connect(tmp)
    try:
        conn.executescript(DDL)
        for d in vault.docs:
            _insert(conn, kind=d.kind, rel=d.rel, data=d.data, body=d.body, ok=d.ok, scope=d.scope, key=d.folder_key)
        for path in root.glob(SNAPSHOT_GLOB):
            if path.is_file() and path.resolve() != db_path.resolve():
                try:
                    md = read(path)
                except Exception as e:  # noqa: BLE001  スナップショットの破損で索引作成を止めない
                    log(f"[skip] {path}: {e}")
                    continue
                _insert(conn, kind="snapshot", rel=path.relative_to(root).as_posix(), data=md.data, body=md.body, ok=True,
                        scope=path.relative_to(root).parts[1])
        conn.executemany("INSERT INTO issues VALUES (?, ?, ?)", [(i.level, i.path, i.message) for i in vault.issues])
        conn.executemany("INSERT INTO meta VALUES (?, ?)", [("fingerprint", fp), ("built_at", time.strftime("%Y-%m-%dT%H:%M:%S"))])
        conn.commit()
    finally:
        conn.close()
    for attempt in range(5):  # Windows では読み手が開いていると置き換えに失敗することがある
        try:
            os.replace(tmp, db_path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.2)
    return db_path


def is_stale(root: Path, db_path: Path) -> bool:
    if not db_path.exists():
        return True
    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = 'fingerprint'").fetchone()
    except sqlite3.DatabaseError:
        return True
    return row is None or row[0] != fingerprint(root)


def ensure_index(root: Path | None = None, db_path: Path | None = None) -> Path:
    """正本が変わっていれば作り直し、索引のパスを返す（読む側は毎回これを呼ぶ）."""
    root = (root or ROOT).resolve()
    db_path = db_path or default_db(root)
    if is_stale(root, db_path):
        build_index(root, db_path)
    return db_path


# 自分自身、またはイベントログなら親エンティティ（同じ scope・フォルダの index.md）
_SELF_OR_PARENT = "(x.id = d.id OR (d.kind = 'event' AND x.kind = 'entity' AND x.scope IS d.scope AND x.key = d.key))"
_DATE = "COALESCE(json_extract(d.data, '$.date'), d.updated_at)"


def search(conn: sqlite3.Connection, query: str = "", *, kinds: list[str] | None = None, scope: str | None = None,
           tags: list[str] | None = None, where_eq: list[tuple[str, str]] | None = None, since: str | None = None,
           limit: int = 50) -> list[sqlite3.Row]:
    """全文検索と絞り込み. query が空なら絞り込みだけで、日付（date か updated_at）の新しい順に返す."""
    terms = [t for t in unicodedata.normalize("NFKC", query).split() if t]
    where, params = [], []
    if not terms:
        base = "SELECT d.* FROM docs d WHERE 1 = 1"
        order = f" ORDER BY {_DATE} DESC, d.path"
    elif all(len(t) >= TRIGRAM_MIN for t in terms):
        base = "SELECT d.* FROM search_fts f JOIN docs d ON d.id = f.doc_id WHERE search_fts MATCH ?"
        params.append(" ".join('"' + t.replace('"', '""') + '"' for t in terms))
        order = " ORDER BY rank"
    else:
        base = "SELECT d.* FROM search_fts f JOIN docs d ON d.id = f.doc_id WHERE 1 = 1"
        for t in terms:
            pattern = "%" + t.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            where.append("(f.title LIKE ? ESCAPE '\\' OR f.body LIKE ? ESCAPE '\\')")
            params += [pattern, pattern]
        order = " ORDER BY d.updated_at DESC"
    if kinds:
        where.append(f"d.kind IN ({', '.join('?' for _ in kinds)})")
        params += kinds
    if scope:
        where.append("d.scope = ?")
        params.append(scope)
    for tag in tags or []:
        where.append(f"EXISTS (SELECT 1 FROM docs x JOIN doc_tags t ON t.doc_id = x.id WHERE {_SELF_OR_PARENT} AND t.tag = ?)")
        params.append(tag)
    for key, value in where_eq or []:
        where.append(f"EXISTS (SELECT 1 FROM docs x WHERE {_SELF_OR_PARENT} AND CAST(json_extract(x.data, ?) AS TEXT) = ?)")
        params += [f'$."{key}"', value]
    if since:
        where.append(f"{_DATE} >= ?")
        params.append(since)
    sql = base + "".join(f" AND {w}" for w in where) + order + " LIMIT ?"
    params.append(limit)
    conn.row_factory = sqlite3.Row
    return conn.execute(sql, params).fetchall()


def main() -> int:
    configure_stdio()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("-q", "--query", help="全文検索するキーワード（空白区切りで AND）")
    p.add_argument("--kind", action="append", help="種別で絞る（entity / event / contact / ... / snapshot）")
    p.add_argument("--scope", help="scope で絞る")
    p.add_argument("--tag", action="append", help="タグで絞る（複数指定で AND）。イベントログは親エンティティのタグでも一致")
    p.add_argument("--where", action="append", metavar="KEY=VALUE",
                   help="frontmatter の値で絞る（例: status=adopted）。イベントログは親エンティティの値でも一致")
    p.add_argument("--since", type=lambda v: str(date.fromisoformat(v)), metavar="YYYY-MM-DD",
                   help="date（無ければ updated_at）がこの日以降")
    p.add_argument("-n", "--limit", type=int, default=50)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("-s", "--summary", action="store_true", help="ヒット一覧を stderr に出す")
    args = p.parse_args()
    root = args.root.resolve()

    where_eq = []
    for item in args.where or []:
        key, sep, value = item.partition("=")
        if not sep:
            p.error(f"--where は KEY=VALUE で指定する: {item}")
        where_eq.append((key, value))
    filtered = bool(args.kind or args.scope or args.tag or where_eq or args.since)
    if not args.query and not filtered:
        db = build_index(root)
        log(f"[作成] {db}")
        emit_paths([db], root)
        return 0
    db = ensure_index(root)
    conn = sqlite3.connect(db)
    try:
        hits = search(conn, args.query or "", kinds=args.kind, scope=args.scope, tags=args.tag, where_eq=where_eq,
                      since=args.since, limit=args.limit)
    finally:
        conn.close()
    if args.summary:
        for h in hits:
            day = json.loads(h["data"]).get("date") or h["updated_at"]
            log(f"{day:<10} {h['kind']:<9} {h['scope'] or '-':<9} {h['status'] or '-':<12} {h['title']}  ({h['path']})")
        log(f"{len(hits)} 件")
    emit_paths([h["path"] for h in hits])
    return 0


if __name__ == "__main__":
    sys.exit(main())
