"""vault の共通ローダー・検証・フロントマター読み書き.

- vault を読むコードはすべて ``load_vault()`` を使い、独自にフロントマターをパースしない。
- 1ファイルの記入ミスで全体を止めないよう、検証の問題は例外にせず ``Vault.issues`` に集める。
  問題のあるファイルも、読めた範囲の ``data`` と ``body`` は返す（``ok`` が False になる）。
- 他ファイルや今日の日付に依存する検査（キー参照の存在、台帳と生きたフォルダの二重登録、
  期限切れの next_due、要約に畳んだイベントログの残り・リンク切れ、派生文書の同期漏れ）もここで行う。
- 索引（SQLite）には依存しない。CLI は常に正本の Markdown を直接読む。
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml

from schema import ENTITY_STATUS, KINDS, LINTS, SCOPES, F, Kind, StatusCategory

ROOT = Path(__file__).resolve().parents[2]  # tools/vault/ の2階層上 = リポジトリルート
_FM = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_EVENT_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)$")
_EVENT_LINK = re.compile(
    r"\]\((\d{4}-\d{2}-\d{2}_[^)/\s]+\.md)\)"
)  # index.md 本文から同じフォルダのイベントログへのリンク


# ---------------------------------------------------------------------------
# フロントマター
# ---------------------------------------------------------------------------


@dataclass
class Markdown:
    data: dict[str, Any]
    body: str
    newline: str
    has_frontmatter: bool


def split(text: str) -> Markdown:
    newline = "\r\n" if text.split("\n", 1)[0].endswith("\r") else "\n"
    m = _FM.match(text)
    if not m:
        return Markdown({}, text, newline, False)
    data = yaml.safe_load(m.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError("フロントマターが YAML の mapping ではない")
    return Markdown(data, text[m.end() :], newline, True)


def read(path: Path) -> Markdown:
    return split(path.read_bytes().decode("utf-8"))


class _Quoted(str):
    """ダブルクォートで書き出す文字列値（キーは素のまま）."""


class _Dumper(yaml.SafeDumper):
    """リストをキーより1段下げ、文字列値はダブルクォートで書き、アンカー（&id001）を使わない."""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:  # noqa: ARG002
        super().increase_indent(flow, False)

    def ignore_aliases(self, data: Any) -> bool:  # noqa: ARG002
        return True


_Dumper.add_representer(
    _Quoted, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", v, style='"')
)


def _clean(value: Any) -> Any:
    """書き出し用に整える: None・空文字・空リストのキーを落とし、文字列値をクォート付きにする."""
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if v not in (None, "", [])}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, str):
        return _Quoted(value)
    return value


def render(data: dict[str, Any], body: str, newline: str = "\n") -> str:
    """フロントマター（キー順は data のまま）と本文を組み立てる. 本文は1文字も変えない."""
    fm = yaml.dump(
        _clean(data), Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=10**9
    ).rstrip("\n")
    if newline != "\n":
        fm = fm.replace("\n", newline)
    return f"---{newline}{fm}{newline}---{newline}{body}"


def write(path: Path, data: dict[str, Any], doc: Markdown) -> None:
    path.write_bytes(render(data, doc.body, doc.newline).encode("utf-8"))


# ---------------------------------------------------------------------------
# 値の検証
# ---------------------------------------------------------------------------


def _check(f: F, value: Any, loc: str) -> list[str]:
    if value is None:
        return [f"{loc}: 必須"] if f.required else []
    t = f.type
    if t == "str":
        if not isinstance(value, str):
            return [f"{loc}: 文字列にする"]
        out = []
        if f.pattern and not re.match(f.pattern, value):
            out.append(f"{loc}: 形式が違う（{f.pattern}）")
        if f.max_len and len(value) > f.max_len:
            out.append(f"{loc}: {f.max_len} 文字以内にする（{len(value)} 文字）")
        return out
    if t in ("int", "float"):
        ok = isinstance(value, int) if t == "int" else isinstance(value, (int, float))
        if not ok or isinstance(value, bool):
            return [f"{loc}: 数値（{t}）にする"]
        if f.min is not None and value < f.min:
            return [f"{loc}: {f.min} 以上にする"]
        if f.max is not None and value > f.max:
            return [f"{loc}: {f.max} 以下にする"]
        return []
    if t == "bool":
        return [] if isinstance(value, bool) else [f"{loc}: true / false にする"]
    if t == "date":
        return (
            []
            if isinstance(value, dt.date) and not isinstance(value, dt.datetime)
            else [f"{loc}: YYYY-MM-DD にする"]
        )
    if t == "due":
        if isinstance(value, dt.date):
            return []
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", value):
            return []
        return [f"{loc}: YYYY-MM-DD または YYYY-MM-DD HH:MM にする"]
    if t == "enum":
        return (
            []
            if value in (f.choices or {})
            else [f"{loc}: {value!r} は許容値 {list(f.choices or {})} に無い"]
        )
    if t == "list[str]":
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            return [f"{loc}: 文字列のリストにする"]
        return []
    if t == "list[object]":
        if not isinstance(value, list):
            return [f"{loc}: リストにする"]
        out = []
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                out.append(f"{loc}[{i}]: mapping にする")
                continue
            out += check_mapping(f.item, item, f"{loc}[{i}]")
        return out
    raise ValueError(f"未知の型 {t}")


def check_mapping(fields: tuple[F, ...], data: dict[str, Any], prefix: str = "") -> list[str]:
    known = {f.name for f in fields}
    out = [f"{prefix + '.' if prefix else ''}{k}: 未知のキー" for k in data if k not in known]
    for f in fields:
        value = data.get(f.name)
        if isinstance(value, str) and not value.strip():
            value = None  # 空文字は未記入扱い
        out += _check(f, value, f"{prefix + '.' if prefix else ''}{f.name}")
    return out


# ---------------------------------------------------------------------------
# ロード
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Issue:
    level: str  # "error" | "warning"
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass
class Doc:
    kind: str
    path: Path
    rel: str
    data: dict[str, Any]
    body: str
    ok: bool
    scope: str | None  # 配置パスから決まる scope
    folder_key: str | None  # 配置パスから決まるキー（エンティティ・コンタクトのフォルダ名）

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


@dataclass
class Vault:
    root: Path
    docs: list[Doc] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    def of(self, kind: str, scope: str | None = None) -> list[Doc]:
        return [d for d in self.docs if d.kind == kind and (scope is None or d.scope == scope)]

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "warning"]

    def entity(self, key: str, scope: str | None = None) -> Doc | None:
        return next((d for d in self.of("entity", scope) if d.folder_key == key), None)

    def events_of(self, entity: Doc) -> list[Doc]:
        return [
            d
            for d in self.of("event", entity.scope)
            if d.folder_key == entity.folder_key and d.rel.split("/")[1] == "scopes"
        ]

    def archived_entries(self, scope: str | None = None) -> Iterator[tuple[Doc, dict[str, Any]]]:
        for doc in self.of("archive", scope):
            if doc.ok:
                for entry in doc.get("entries") or []:
                    yield doc, entry


def _location(rel: str) -> tuple[str | None, str | None]:
    parts = rel.split("/")
    if parts[1] == "scopes":
        scope = parts[2]
        key = parts[4] if len(parts) > 5 and parts[3] == "entities" else None
        return scope, key
    if parts[1] == "contacts" and len(parts) > 3:
        return None, parts[2]
    return None, None


def load_doc(kind: Kind, path: Path, root: Path) -> tuple[Doc, list[Issue]]:
    rel = path.relative_to(root).as_posix()
    scope, folder_key = _location(rel)
    issues: list[Issue] = []
    try:
        md = read(path)
    except (yaml.YAMLError, ValueError, UnicodeDecodeError, OSError) as e:
        return Doc(kind.name, path, rel, {}, "", False, scope, folder_key), [
            Issue("error", rel, f"読み込めない: {e}")
        ]
    doc = Doc(kind.name, path, rel, md.data, md.body, True, scope, folder_key)
    if not md.has_frontmatter:
        doc.ok = False
        return doc, [Issue("error", rel, "フロントマターが無い")]

    errors = check_mapping(kind.fields, md.data)
    lint = LINTS.get(kind.name)
    warnings: list[str] = []
    if lint and not errors:
        e2, warnings = lint(md.data)
        errors += e2
    errors += _check_location(kind, doc)
    doc.ok = not errors
    issues += [Issue("error", rel, m) for m in errors]
    issues += [Issue("warning", rel, m) for m in warnings]
    return doc, issues


def _check_location(kind: Kind, doc: Doc) -> list[str]:
    out = []
    d = doc.data
    if kind.key_field and doc.folder_key and d.get(kind.key_field) != doc.folder_key:
        out.append(
            f"{kind.key_field}={d.get(kind.key_field)} がフォルダ名 {doc.folder_key} と一致しない"
        )
    if kind.scope_field and doc.scope and d.get(kind.scope_field) != doc.scope:
        out.append(
            f"{kind.scope_field}={d.get(kind.scope_field)} が配置先 scope {doc.scope} と一致しない"
        )
    if kind.event_name:
        m = _EVENT_NAME.match(doc.path.stem)
        if not m:
            out.append("ファイル名を {YYYY-MM-DD}_{kind}.md にする")
        else:
            if str(d.get("date")) != m.group(1):
                out.append(f"date={d.get('date')} がファイル名の日付 {m.group(1)} と一致しない")
            if d.get("kind") != m.group(2):
                out.append(f"kind={d.get('kind')} がファイル名の {m.group(2)} と一致しない")
    if doc.scope is not None and doc.scope not in SCOPES:
        out.append(f"scope フォルダ {doc.scope} が schema.SCOPES に無い")
    return out


def _due_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _check_relations(vault: Vault, today: dt.date | None) -> list[Issue]:
    """ファイル間の関係（キー参照）・二重登録・期限切れ・派生文書の同期漏れ."""
    issues: list[Issue] = []
    contacts = {d.folder_key for d in vault.of("contact")}
    entity_keys = {d.folder_key for d in vault.of("entity")}
    archived_keys = {e.get("key") for _, e in vault.archived_entries() if e.get("key")}

    for doc in vault.of("entity"):
        if not doc.ok:
            continue
        if doc.get("contact") and doc.get("contact") not in contacts:
            issues.append(
                Issue(
                    "warning",
                    doc.rel,
                    f"contact={doc.get('contact')} のコンタクト（vault/contacts/{doc.get('contact')}/）が無い",
                )
            )
        due = _due_date(doc.get("next_due"))
        if (
            today
            and due
            and due < today
            and doc.get("action_type") in ("action_required", "scheduled")
            and ENTITY_STATUS[doc.get("status")].category == StatusCategory.ACTIVE
        ):
            issues.append(
                Issue(
                    "warning",
                    doc.rel,
                    f"next_due={due} を過ぎている。next_action / next_due を更新する",
                )
            )
        for name in _EVENT_LINK.findall(doc.body):
            if not (doc.path.parent / name).is_file():
                issues.append(
                    Issue(
                        "warning",
                        doc.rel,
                        f"本文のリンク先 {name} が無い。digests に畳んだなら本文からリンクを外す",
                    )
                )
        digests = doc.get("digests") or []
        for event in vault.events_of(doc):
            hit = next(
                (g for g in digests if event.ok and g["from"] <= event.get("date") <= g["to"]), None
            )
            if hit:
                issues.append(
                    Issue(
                        "warning",
                        event.rel,
                        f"digests（{hit['from']}〜{hit['to']}）に畳んだ期間のイベントログが残っている",
                    )
                )

    for doc in vault.of("contact"):
        for item in (doc.get("introduced") or []) if doc.ok else []:
            key = item.get("key")
            if key and key not in entity_keys | archived_keys:
                issues.append(
                    Issue(
                        "warning",
                        doc.rel,
                        f"introduced の key={key} のエンティティ・台帳エントリが無い",
                    )
                )

    live = {(d.scope, d.folder_key) for d in vault.of("entity")}
    for doc, entry in vault.archived_entries():
        if entry.get("key") and (doc.scope, entry["key"]) in live:
            issues.append(
                Issue(
                    "error",
                    doc.rel,
                    f"key={entry['key']} が台帳と entities/{entry['key']}/ の両方にある。再検討するなら台帳エントリを消す",
                )
            )

    for doc in vault.of("event"):
        if doc.scope is not None and doc.folder_key not in entity_keys:
            issues.append(
                Issue("warning", doc.rel, f"同じフォルダに index.md が無い（{doc.folder_key}）")
            )

    for doc in vault.of("note"):
        src = doc.get("source_file")
        if not (doc.ok and src):
            continue
        src_path = vault.root / src
        if not src_path.is_file():
            issues.append(Issue("warning", doc.rel, f"source_file={src} が無い"))
            continue
        try:
            src_updated = read(src_path).data.get("updated_at")
        except (yaml.YAMLError, ValueError, OSError):
            continue
        synced = doc.get("source_updated_at")
        if isinstance(src_updated, dt.date) and (
            not isinstance(synced, dt.date) or synced < src_updated
        ):
            issues.append(
                Issue(
                    "warning",
                    doc.rel,
                    f"派生元 {src}（updated_at={src_updated}）より古い。同期して source_updated_at を更新する",
                )
            )
    return issues


def load_vault(root: Path | None = None, *, today: dt.date | None = None) -> Vault:
    """vault 全体を読み込む. root は vault/ を含むディレクトリ（既定: リポジトリルート）."""
    root = (root or ROOT).resolve()
    vault = Vault(root)
    seen: set[Path] = set()
    for kind in KINDS.values():
        paths = sorted({p for g in kind.globs for p in root.glob(g) if p.is_file()} - seen)
        for path in paths:
            seen.add(path)
            doc, issues = load_doc(kind, path, root)
            vault.docs.append(doc)
            vault.issues += issues
    vault.issues += _check_relations(vault, today)
    return vault


# ---------------------------------------------------------------------------
# CLI 出力規約: stdout はファイルパスだけ（1行1パス、ルート相対）。人間向けの表示は --summary、ログは stderr
# ---------------------------------------------------------------------------


def rel(path: Path, root: Path | None = None) -> str:
    root = root or ROOT
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def emit_paths(paths: list[Path] | list[str], root: Path | None = None) -> None:
    for p in dict.fromkeys(paths):
        print(p if isinstance(p, str) else rel(p, root))


def log(message: str) -> None:
    print(message, file=sys.stderr)


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
