# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""scope のダッシュボード（vault/scopes/{scope}/dashboard.md）の一覧を自動生成する.

エンティティの frontmatter とイベントログから「要対応 / 予定 / 待ち」・最近の出来事（直近 RECENT_DAYS 日）・
進行中一覧を組み立て、マーカー（<!-- dashboard:begin --> 〜 <!-- dashboard:end -->）の間だけを書き換える。
マーカー外の手書き部分は変えない。題材固有の列と小見出しの分け方は schema.py の DASHBOARD_COLUMNS / DASHBOARD_GROUP_BY。
stdout には更新した dashboard.md のパスだけを出す。

    uv run tools/vault/build_dashboard.py --scope work [--summary]
    uv run tools/vault/build_dashboard.py --all [--today YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

from schema import DASHBOARD_COLUMNS, DASHBOARD_GROUP_BY, ENTITY_STATUS, EVENT_KINDS, KINDS, RECENT_DAYS, SCOPES, StatusCategory
from vaultlib import ROOT, Doc, Vault, configure_stdio, emit_paths, load_vault, log

BEGIN, END = "<!-- dashboard:begin -->", "<!-- dashboard:end -->"
ACTION_SECTIONS = (("action_required", "🔴 要対応"), ("scheduled", "📅 確定済みの予定"), ("waiting", "⏳ 返信・結果待ち"))


def _cell(value: object, max_len: int = 40) -> str:
    text = "" if value is None else str(value).replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _link(doc: Doc) -> str:
    return f"[{_cell(doc.get('title'))}](entities/{doc.folder_key}/index.md)"


def _recent(vault: Vault, scope: str, entities: list[Doc], today: dt.date) -> list[str]:
    since = today - dt.timedelta(days=RECENT_DAYS)
    by_key = {d.folder_key: d for d in entities}
    events = sorted(
        (e for e in vault.of("event", scope) if e.ok and e.folder_key in by_key and since <= e.get("date") <= today),
        key=lambda e: (e.get("date"), e.rel),
        reverse=True,
    )
    lines = [f"### 🕘 最近の出来事（直近 {RECENT_DAYS} 日）", ""]
    if not events:
        return [*lines, "（なし）", ""]
    lines += ["| 日付 | 対象 | 記録 |", "| --- | --- | --- |"]
    for e in events:
        label = _cell(e.get("title") or EVENT_KINDS.get(e.get("kind"), e.get("kind")))
        lines.append(f"| {e.get('date')} | {_link(by_key[e.folder_key])} | [{label}](entities/{e.folder_key}/{e.path.name}) |")
    return [*lines, ""]


def _active_table(rows: list[Doc]) -> list[str]:
    extra = [label for label, _ in DASHBOARD_COLUMNS]
    lines = [
        "| " + " | ".join(["対象", "状態", *extra, "状態の補足", "更新日"]) + " |",
        "| " + " | ".join(["---"] * (len(extra) + 4)) + " |",
    ]
    for d in rows:
        cells = [
            _link(d),
            ENTITY_STATUS[d.get("status")].label,
            *(_cell(fn(d.data)) for _, fn in DASHBOARD_COLUMNS),
            _cell(d.get("status_note")),
            str(d.get("updated_at")),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _groups(rows: list[Doc]) -> list[tuple[str, list[Doc]]]:
    """DASHBOARD_GROUP_BY の enum の定義順に分ける（分けないなら1グループ）."""
    if DASHBOARD_GROUP_BY is None:
        return [("", rows)]
    choices = next(f.choices for f in KINDS["entity"].fields if f.name == DASHBOARD_GROUP_BY) or {}
    return [(label, [d for d in rows if d.get(DASHBOARD_GROUP_BY) == value]) for value, label in choices.items()]


def render_block(vault: Vault, scope: str, today: dt.date) -> str:
    entities = [d for d in vault.of("entity", scope) if d.ok]
    active = sorted(
        (d for d in entities if ENTITY_STATUS[d.get("status")].category == StatusCategory.ACTIVE),
        key=lambda d: (ENTITY_STATUS[d.get("status")].order, str(d.get("next_due") or "9999"), d.folder_key),
    )
    lines = [BEGIN, "", "<!-- 自動生成: tools/vault/build_dashboard.py。この区間は手で編集しない -->", ""]
    for action, title in ACTION_SECTIONS:
        rows = sorted((d for d in active if d.get("action_type") == action), key=lambda d: str(d.get("next_due") or "9999"))
        lines += [f"### {title}", ""]
        if not rows:
            lines += ["（なし）", ""]
            continue
        lines += ["| 期限 | 対象 | 内容 |", "| --- | --- | --- |"]
        lines += [f"| {_cell(d.get('next_due'))} | {_link(d)} | {_cell(d.get('next_action'), 60)} |" for d in rows]
        lines.append("")

    lines += _recent(vault, scope, entities, today)

    lines += ["### 進行中の一覧", ""]
    if not active:
        lines += ["（なし）", ""]
    for label, rows in _groups(active):
        if not rows:
            continue
        if label:
            lines += [f"#### {label}", ""]
        lines += [*_active_table(rows), ""]
    counts = Counter(ENTITY_STATUS[d.get("status")].label for d in entities if d not in active)
    archived = sum(1 for _ in vault.archived_entries(scope))
    closed = " / ".join(f"{k} {v}" for k, v in counts.items()) or "なし"
    lines += [f"進行中 {len(active)} 件。終了・除外: {closed}。見送り台帳: {archived} 件。", "", END]
    return "\n".join(lines)


def replace_block(text: str, block: str) -> str:
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"マーカー（{BEGIN} 〜 {END}）が無い")
    return pattern.sub(lambda _: block, text, count=1)


def build(vault: Vault, scope: str, today: dt.date) -> Path | None:
    path = vault.root / "vault" / "scopes" / scope / "dashboard.md"
    if not path.exists():
        log(f"[skip] {path} が無い")
        return None
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    block = render_block(vault, scope, today).replace("\n", newline)
    new = replace_block(raw, block)
    if new != raw:
        path.write_bytes(new.encode("utf-8"))
        log(f"[更新] {path.name}（{scope}）")
    return path


def main() -> int:
    configure_stdio()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--scope", choices=list(SCOPES))
    g.add_argument("--all", action="store_true", help="全 scope を更新する")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today(), help="「最近の出来事」の基準日")
    p.add_argument("-s", "--summary", action="store_true", help="生成した一覧を stderr に出す")
    args = p.parse_args()

    vault = load_vault(args.root)
    if vault.errors:
        log(f"[warn] 検証エラーが {len(vault.errors)} 件ある（エラーのあるファイルは一覧に出ない）。validate.py で確認する")
    paths = []
    for scope in SCOPES if args.all else [args.scope]:
        path = build(vault, scope, args.today)
        if path:
            paths.append(path)
            if args.summary:
                log(render_block(vault, scope, args.today))
    emit_paths(paths, vault.root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
