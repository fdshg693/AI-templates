# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""新しい対象を扱う前の重複・除外チェック.

名称（と別名）を正規化して、エンティティ（生きたフォルダ）・トリアージ集約ログ・見送り台帳と照合し、
判定を stderr に出す。stdout には照合に使った既存ファイルのパスだけを出す。

    [EXCLUDED]    同じ scope で見送り・不可・打ち切り済み、または全 scope で除外 → 過去の理由を示して再調査しない
    [OTHER SCOPE] 別の scope で履歴がある → 参考として示し、この scope の条件で改めて判断する
    [EXISTING]    進行中・採用済みのエンティティがある → 新しいフォルダは作らず既存 index.md に追記する
    [NOT FOUND]   未登録 → 新規に作る

    uv run tools/vault/check_entity.py --scope work -s "Acme Notes"
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from schema import ENTITY_STATUS, SCOPES, TRIAGE_STATUS, ExclusionScope, exclusion_of
from vaultlib import ROOT, configure_stdio, emit_paths, load_vault, log


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(ch for ch in text if ch.isalnum())


@dataclass
class Match:
    name: str
    scope: str
    status: str
    path: str
    reason: str | None
    reconsider_if: str | None = None
    exact: bool = True

    def verdict(self, scope: str) -> str:
        excl = exclusion_of(self.status)
        if excl == ExclusionScope.ALL_SCOPES or (excl == ExclusionScope.SAME_SCOPE and self.scope == scope):
            return "EXCLUDED"
        if self.scope != scope:
            return "OTHER SCOPE"
        return "EXISTING"


def find(query: str, scope: str, root: Path) -> list[Match]:
    q = normalize(query)
    vault = load_vault(root)
    matches: list[Match] = []

    def consider(names: list[str], **kw) -> None:
        normed = [normalize(n) for n in names if n]
        if q in normed:
            matches.append(Match(exact=True, **kw))
        elif len(q) >= 3 and any(q in n or (len(n) >= 3 and n in q) for n in normed):
            matches.append(Match(exact=False, **kw))

    for d in vault.of("entity"):
        consider([d.get("title", ""), d.folder_key or "", *(d.get("aliases") or [])], name=d.get("title", d.folder_key),
                 scope=d.scope, status=d.get("status", "researching"), path=d.rel, reason=d.get("close_reason"))
    for d in vault.of("triage"):
        for e in d.get("entries") or []:
            consider([e.get("name", ""), *(e.get("aliases") or [])], name=e.get("name"), scope=d.scope,
                     status=TRIAGE_STATUS, path=d.rel, reason=e.get("reason"))
    for d, e in vault.archived_entries():
        consider([e.get("name", ""), e.get("key") or "", *(e.get("aliases") or [])], name=e.get("name"), scope=d.scope,
                 status=e.get("status"), path=d.rel, reason=e.get("reason"), reconsider_if=e.get("reconsider_if"))
    return [m for m in matches if m.status in ENTITY_STATUS or m.status == TRIAGE_STATUS]


def main() -> int:
    configure_stdio()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("-s", "--search", required=True, help="名称（別名・略称でもよい）")
    p.add_argument("--scope", required=True, choices=list(SCOPES))
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args()

    matches = find(args.search, args.scope, args.root.resolve())
    exact = [m for m in matches if m.exact]
    if not exact:
        log(f"[NOT FOUND] {args.search}")
        for m in matches:
            log(f"  似た名前: {m.name}（{m.scope} / {m.status}）{m.path}")
        emit_paths([m.path for m in matches])
        return 0
    priority = {"EXCLUDED": 0, "EXISTING": 1, "OTHER SCOPE": 2}
    for m in sorted(exact, key=lambda m: priority[m.verdict(args.scope)]):
        log(f"[{m.verdict(args.scope)}] {m.name}（{m.scope} / {m.status}）{m.path}")
        if m.reason:
            log(f"  理由: {m.reason}")
        if m.reconsider_if:
            log(f"  再検討の条件: {m.reconsider_if}")
    emit_paths([m.path for m in exact])
    return 0


if __name__ == "__main__":
    sys.exit(main())
