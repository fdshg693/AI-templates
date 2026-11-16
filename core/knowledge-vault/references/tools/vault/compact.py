# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""終わったもの・古くなったものを圧縮する.

- 既定: 終了したエンティティ・古いトリアージログを見送り台帳（vault/scopes/{scope}/archive.md）に畳む。
- --events: 続いているエンティティの古いイベントログ（EVENT_DIGEST_DAYS 日より前）を、
  その index.md の frontmatter `digests` に要約 1 件として畳む。

圧縮の「本質」（台帳の reason / reconsider_if、digests の summary）は AI が材料を読んで書き、
ユーザーが確認する。この CLI は機械的な部分（候補の列挙・下書き・追記・git rm）だけを担う。
消したファイルの詳細は git の履歴に残る。

    uv run tools/vault/compact.py list [--scope work] [--older-than-days 14] [-s]
    uv run tools/vault/compact.py draft --scope work --key beta-board            # 材料のパスと下書き
    uv run tools/vault/compact.py apply --scope work --key beta-board --reason "..." [--reconsider-if "..."]
    uv run tools/vault/compact.py apply --triage vault/scopes/work/triage/2026-09-20_note-apps.md

    uv run tools/vault/compact.py list --events [--scope work] [-s]
    uv run tools/vault/compact.py draft --events --scope work --key acme-notes
    uv run tools/vault/compact.py apply --events --scope work --key acme-notes --digest "..."

stdout: list は候補のパス、draft は材料のパス、apply は書き換えた台帳・index.md のパス。
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from schema import ARCHIVABLE_STATUS, EVENT_DIGEST_DAYS, KINDS, SCOPES, TRIAGE_STATUS
from vaultlib import (
    ROOT,
    Doc,
    Markdown,
    Vault,
    check_mapping,
    configure_stdio,
    emit_paths,
    load_vault,
    log,
    read,
    write,
)

DEFAULT_OLDER_THAN_DAYS = 14
ENTRY_FIELDS = next(f for f in KINDS["archive"].fields if f.name == "entries").item
DIGEST_FIELDS = next(f for f in KINDS["entity"].fields if f.name == "digests").item


def _days_old(value: Any, today: dt.date) -> int:
    return (today - value).days if isinstance(value, dt.date) else 0


def candidates(vault: Vault, scope: str | None, days: int, today: dt.date) -> list[Doc]:
    out = [
        d
        for d in vault.of("entity", scope)
        if d.ok
        and d.get("status") in ARCHIVABLE_STATUS
        and _days_old(d.get("updated_at"), today) >= days
    ]
    out += [
        d for d in vault.of("triage", scope) if d.ok and _days_old(d.get("date"), today) >= days
    ]
    return out


def old_events(vault: Vault, entity: Doc, days: int, today: dt.date) -> list[Doc]:
    """台帳に畳む対象ではないエンティティの、days 日以上前のイベントログ（日付順）."""
    if entity.get("status") in ARCHIVABLE_STATUS:
        return []
    events = [
        e for e in vault.events_of(entity) if e.ok and _days_old(e.get("date"), today) >= days
    ]
    return sorted(events, key=lambda e: (e.get("date"), e.rel))


def draft_entry(doc: Doc) -> dict[str, Any]:
    return {
        "name": doc.get("title"),
        "key": doc.folder_key,
        "aliases": doc.get("aliases") or [],
        "status": doc.get("status"),
        "closed_at": doc.get("updated_at"),
        "reason": doc.get("close_reason") or "",
        "reconsider_if": "",
        "contact": doc.get("contact"),
    }


def draft_digest(events: list[Doc], summary: str = "") -> dict[str, Any]:
    return {
        "from": events[0].get("date"),
        "to": events[-1].get("date"),
        "count": len(events),
        "summary": summary,
    }


def _git(*args: str, root: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def _require_clean(paths: list[Path], root: Path) -> None:
    for path in paths:
        if _git("status", "--porcelain", "--", str(path), root=root).strip():
            raise SystemExit(f"{path} に未コミットの変更がある。先にコミットしてから圧縮する")


def _validate(fields: tuple, items: list[dict[str, Any]], what: str) -> None:
    for i, e in enumerate(items):
        problems = check_mapping(
            fields, {k: v for k, v in e.items() if v not in (None, "", [])}, f"{what}[{i}]"
        )
        if problems:
            raise SystemExit(f"{what} が不正: " + "; ".join(problems))


def _append(vault: Vault, scope: str, entries: list[dict[str, Any]], today: dt.date) -> Path:
    _validate(ENTRY_FIELDS, entries, "entries")
    path = vault.root / "vault" / "scopes" / scope / "archive.md"
    if path.exists():
        md = read(path)
    else:
        md = Markdown(
            {"scope": scope, "entries": [], "updated_at": today}, "\n# 見送り台帳\n", "\n", True
        )
    data = dict(md.data)
    data["entries"] = [*(data.get("entries") or []), *entries]
    data["updated_at"] = today
    write(path, data, md)
    return path


def _entity(vault: Vault, args: argparse.Namespace) -> Doc:
    if not (args.scope and args.key):
        raise SystemExit(f"{args.command} には --scope と --key が必要")
    doc = vault.entity(args.key, args.scope)
    if doc is None or not doc.ok:
        raise SystemExit(f"{args.scope}/{args.key} は検証済みのエンティティではない")
    return doc


def cmd_list(args: argparse.Namespace, vault: Vault, today: dt.date) -> int:
    if args.events:
        days = args.older_than_days or EVENT_DIGEST_DAYS
        paths = []
        for entity in vault.of("entity", args.scope):
            events = old_events(vault, entity, days, today)
            if events:
                paths += [e.path for e in events]
                if args.summary:
                    log(
                        f"{entity.scope:<9} {entity.folder_key:<24} {len(events)} 件（{events[0].get('date')}〜{events[-1].get('date')}）"
                    )
        if args.summary:
            log(f"イベントログ {len(paths)} 件（{days} 日以上前）")
        emit_paths(paths, vault.root)
        return 0
    days = args.older_than_days or DEFAULT_OLDER_THAN_DAYS
    docs = candidates(vault, args.scope, days, today)
    if args.summary:
        for d in docs:
            what = d.get("status") if d.kind == "entity" else TRIAGE_STATUS
            log(f"{d.scope:<9} {what:<12} {d.rel}")
        log(f"{len(docs)} 件（{days} 日以上前に終了）")
    emit_paths([d.path.parent if d.kind == "entity" else d.path for d in docs], vault.root)
    return 0


def cmd_draft(args: argparse.Namespace, vault: Vault, today: dt.date) -> int:
    doc = _entity(vault, args)
    if args.events:
        events = old_events(vault, doc, args.older_than_days or EVENT_DIGEST_DAYS, today)
        if not events:
            raise SystemExit(f"{args.scope}/{args.key} に畳めるイベントログが無い")
        log("# digests の下書き（summary はイベントログを読んで、その期間の傾向を 2〜3 文で書く）")
        log(yaml.safe_dump(draft_digest(events), allow_unicode=True, sort_keys=False))
        emit_paths([doc.path, *(e.path for e in events)], vault.root)
        return 0
    log("# 台帳エントリの下書き（reason はイベントログも読んで条件の言葉で書き直す）")
    log(yaml.safe_dump(draft_entry(doc), allow_unicode=True, sort_keys=False))
    emit_paths([doc.path, *(e.path for e in vault.events_of(doc))], vault.root)
    return 0


def _apply_events(args: argparse.Namespace, vault: Vault, today: dt.date) -> Path:
    doc = _entity(vault, args)
    if not args.digest:
        raise SystemExit("apply --events には --digest が必要")
    events = old_events(vault, doc, args.older_than_days or EVENT_DIGEST_DAYS, today)
    if not events:
        raise SystemExit(f"{args.scope}/{args.key} に畳めるイベントログが無い")
    _require_clean([doc.path, *(e.path for e in events)], vault.root)
    digest = draft_digest(events, args.digest)
    _validate(DIGEST_FIELDS, [digest], "digests")
    md = read(doc.path)
    data = dict(md.data)
    data["digests"] = sorted([*(data.get("digests") or []), digest], key=lambda g: g["from"])
    data["updated_at"] = today
    write(doc.path, data, md)
    for e in events:
        _git("rm", "-q", str(e.path), root=vault.root)
    log(
        "[完了] index.md の本文から消したイベントログへのリンクを外し、validate.py と build_dashboard.py を実行してコミットする"
    )
    return doc.path


def cmd_apply(args: argparse.Namespace, vault: Vault, today: dt.date) -> int:
    root = vault.root
    if args.events:
        emit_paths([_apply_events(args, vault, today)], root)
        return 0
    if args.triage:
        path = (root / args.triage).resolve()
        doc = next((d for d in vault.of("triage") if d.path.resolve() == path), None)
        if doc is None or not doc.ok:
            raise SystemExit(f"{args.triage} は検証済みのトリアージログではない")
        _require_clean([path], root)
        entries = [
            {
                "name": e["name"],
                "aliases": e.get("aliases") or [],
                "status": TRIAGE_STATUS,
                "closed_at": doc.get("date"),
                "reason": e["reason"],
            }
            for e in doc.get("entries")
        ]
        archive = _append(vault, doc.scope, entries, today)
        _git("rm", "-q", str(path), root=root)
    else:
        if not args.reason:
            raise SystemExit(
                "apply には --scope --key --reason（または --triage / --events）が必要"
            )
        doc = _entity(vault, args)
        if doc.get("status") not in ARCHIVABLE_STATUS:
            raise SystemExit(
                f"status={doc.get('status')} は台帳に畳めない（{', '.join(ARCHIVABLE_STATUS)} のみ）"
            )
        _require_clean([doc.path.parent], root)
        entry = draft_entry(doc) | {
            "reason": args.reason,
            "reconsider_if": args.reconsider_if or "",
        }
        archive = _append(vault, args.scope, [entry], today)
        _git("rm", "-r", "-q", str(doc.path.parent), root=root)
    log("[完了] validate.py と build_dashboard.py を実行し、台帳の変更をコミットする")
    emit_paths([archive], root)
    return 0


def main() -> int:
    configure_stdio()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("command", choices=["list", "draft", "apply"])
    p.add_argument(
        "--events",
        action="store_true",
        help="台帳ではなく、続いているエンティティの古いイベントログを digests に畳む",
    )
    p.add_argument("--scope", choices=list(SCOPES))
    p.add_argument("--key")
    p.add_argument("--reason", help="何が合わなかったか（条件の言葉で 1〜2 文）")
    p.add_argument("--reconsider-if", help="何が変われば再検討してよいか")
    p.add_argument("--triage", help="畳み込むトリアージログ（ルート相対パス）")
    p.add_argument("--digest", help="--events: 畳む期間の傾向（2〜3 文）")
    p.add_argument(
        "--older-than-days",
        type=int,
        help=f"既定: 台帳は {DEFAULT_OLDER_THAN_DAYS} 日、--events は {EVENT_DIGEST_DAYS} 日（schema.EVENT_DIGEST_DAYS）",
    )
    p.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("-s", "--summary", action="store_true")
    args = p.parse_args()

    vault = load_vault(args.root)
    if args.command == "list":
        return cmd_list(args, vault, args.today)
    if args.command == "draft":
        return cmd_draft(args, vault, args.today)
    return cmd_apply(args, vault, args.today)


if __name__ == "__main__":
    sys.exit(main())
