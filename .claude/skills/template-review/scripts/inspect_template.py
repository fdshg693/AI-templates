#!/usr/bin/env python3
"""Collect mechanical facts about a template folder for template-review.

Usage:
    uv run .claude/skills/template-review/scripts/inspect_template.py core/plans
    uv run .claude/skills/template-review/scripts/inspect_template.py core/*  [--json]

Reports (per template folder):
    - entry points: README.md / AGENTS.md / CLAUDE.md presence, CLAUDE.md alias form
    - always-loaded cost: lines of AGENTS.md + CLAUDE.md (+ @imports)
    - broken relative links, links escaping the template folder
    - reachability: hop count from AGENTS.md / README.md, unreachable .md files
    - reference stats: size, near-duplicate reference files (line-set Jaccard)
    - duplicated long lines across files (single-source-of-truth candidates)
    - bundled scripts: docstring/usage, stdlib-only, where documented
    - placeholders ({name}, <name>) and TODO/FIXME markers

This script only gathers facts; judging them is the reviewer's job.
Only the standard library is used.
"""

import argparse
import ast
import json
import os
import re
import stat
import sys
from collections import defaultdict, deque
from itertools import combinations
from pathlib import Path

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMPORT_RE = re.compile(r"^@(\S+)", re.MULTILINE)
CODE_FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z_][\w-]*\}|<[a-z][\w-]*>")
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX)\b")
REFERENCE_DIRS = {"reference", "references", "examples", "example", "samples"}
SCRIPT_SUFFIXES = {".py", ".sh", ".ps1", ".js", ".ts", ".mjs"}
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "snapshot"}
ALWAYS_LOADED_WARN = 150
DUP_MIN_LEN = 40
SIMILAR_THRESHOLD = 0.6


IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003


def is_link_dir(p: Path) -> bool:
    """True for a directory symlink or a Windows junction (Python 3.11+).

    rglob / os.walk follow junctions (is_symlink() is False for them), so a
    template that links another template in (core/threads/planning ->
    core/plans) would otherwise be scanned twice.
    """
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return (
        stat.S_ISLNK(st.st_mode) or getattr(st, "st_reparse_tag", 0) == IO_REPARSE_TAG_MOUNT_POINT
    )


def iter_files(root: Path):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not is_link_dir(base / d)]
        found.extend(base / f for f in filenames)
    yield from sorted(p for p in found if p.is_file())


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="replace")


def rel(p: Path, root: Path) -> str:
    return p.relative_to(root).as_posix()


def strip_code(text: str) -> str:
    return CODE_FENCE_RE.sub("", text)


def md_links(md: Path):
    """Yield (line_no, target) for relative links in a markdown file."""
    text = read(md)
    for m in LINK_RE.finditer(text):
        target = m.group(1)
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
            continue
        yield text.count("\n", 0, m.start()) + 1, target.split("#", 1)[0]
    if md.name == "CLAUDE.md":
        for m in IMPORT_RE.finditer(text):
            yield text.count("\n", 0, m.start()) + 1, m.group(1)


def resolve(md: Path, target: str) -> Path:
    return (md.parent / target).resolve()


def dir_entry(d: Path):
    """Markdown files a directory link leads to."""
    readme = d / "README.md"
    if readme.exists():
        return [readme]
    return sorted(d.glob("*.md"))


def inspect(root: Path) -> dict:
    root = root.resolve()
    files = list(iter_files(root))
    mds = [p for p in files if p.suffix == ".md"]
    result: dict = {"template": root.name, "path": str(root)}

    # --- entry points ---------------------------------------------------
    entry = {}
    for name in ("README.md", "AGENTS.md", "CLAUDE.md"):
        p = root / name
        entry[name] = {
            "exists": p.exists(),
            "lines": len(read(p).splitlines()) if p.exists() else 0,
        }
    claude = root / "CLAUDE.md"
    if claude.exists():
        body = [
            line
            for line in read(claude).splitlines()
            if line.strip() and not line.strip().startswith("<!--")
        ]
        entry["CLAUDE.md"]["imports"] = IMPORT_RE.findall(read(claude))
        entry["CLAUDE.md"]["alias_only"] = all(line.startswith("@") for line in body)
    result["entry_points"] = entry

    # --- always loaded cost ----------------------------------------------
    loaded, seen, queue = (
        0,
        set(),
        deque(p for p in (root / "AGENTS.md", root / "CLAUDE.md") if p.exists()),
    )
    while queue:
        p = queue.popleft().resolve()
        if p in seen or not p.exists():
            continue
        seen.add(p)
        text = read(p)
        loaded += len(text.splitlines())
        queue.extend(resolve(p, t) for t in IMPORT_RE.findall(text))
    result["always_loaded"] = {
        "lines": loaded,
        "files": sorted(rel(p, root) for p in seen if p.is_relative_to(root)),
        "warn": loaded > ALWAYS_LOADED_WARN,
    }

    # --- links ----------------------------------------------------------
    graph: dict[Path, set[Path]] = defaultdict(set)
    broken, escaping = [], []
    for md in mds:
        for line, target in md_links(md):
            if not target:
                continue
            dest = resolve(md, target)
            loc = f"{rel(md, root)}:{line}"
            if not dest.is_relative_to(root):
                escaping.append({"at": loc, "target": target, "exists": dest.exists()})
                continue
            if not dest.exists():
                broken.append({"at": loc, "target": target})
                continue
            if dest.is_dir():
                graph[md.resolve()].update(p.resolve() for p in dir_entry(dest))
            elif dest.suffix == ".md":
                graph[md.resolve()].add(dest)
    result["broken_links"] = broken
    result["escaping_links"] = escaping

    # --- reachability ---------------------------------------------------
    def hops_from(start: Path) -> dict[Path, int]:
        if not start.exists():
            return {}
        dist = {start.resolve(): 0}
        q = deque([start.resolve()])
        while q:
            cur = q.popleft()
            for nxt in graph.get(cur, ()):
                if nxt not in dist:
                    dist[nxt] = dist[cur] + 1
                    q.append(nxt)
        return dist

    from_agents = (
        hops_from(root / "AGENTS.md") if (root / "AGENTS.md").exists() else hops_from(claude)
    )
    from_readme = hops_from(root / "README.md")
    reach = {}
    entry_names = {"README.md", "AGENTS.md", "CLAUDE.md"}
    for md in mds:
        if md.parent.resolve() == root and md.name in entry_names:
            continue
        r = md.resolve()
        reach[rel(md, root)] = {"agents": from_agents.get(r), "readme": from_readme.get(r)}
    result["reachability"] = {
        "unreachable_from_any": sorted(
            k for k, v in reach.items() if v["agents"] is None and v["readme"] is None
        ),
        "unreachable_from_agents": sorted(k for k, v in reach.items() if v["agents"] is None),
        "max_hops_from_agents": max(
            (v["agents"] for v in reach.values() if v["agents"] is not None), default=None
        ),
        "hops": reach,
    }

    # --- reference stats ------------------------------------------------
    ref_files = [p for p in mds if REFERENCE_DIRS & set(p.relative_to(root).parts[:-1])]
    total_lines = sum(len(read(p).splitlines()) for p in mds)
    ref_lines = sum(len(read(p).splitlines()) for p in ref_files)

    def line_set(p: Path) -> set[str]:
        return {
            s for s in (line.strip() for line in strip_code(read(p)).splitlines()) if len(s) > 15
        }

    sets = {p: line_set(p) for p in ref_files}
    similar = []
    for a, b in combinations(ref_files, 2):
        sa, sb = sets[a], sets[b]
        if sa and sb:
            j = len(sa & sb) / len(sa | sb)
            if j >= SIMILAR_THRESHOLD:
                similar.append({"a": rel(a, root), "b": rel(b, root), "jaccard": round(j, 2)})
    result["references"] = {
        "files": len(ref_files),
        "lines": ref_lines,
        "share_of_md_lines": round(ref_lines / total_lines, 2) if total_lines else 0,
        "largest": sorted(
            ({"file": rel(p, root), "lines": len(read(p).splitlines())} for p in ref_files),
            key=lambda x: -x["lines"],
        )[:5],
        "near_duplicates": sorted(similar, key=lambda x: -x["jaccard"]),
    }

    # --- duplicated lines across files ----------------------------------
    occurrences: dict[str, set[str]] = defaultdict(set)
    for md in mds:
        for line in strip_code(read(md)).splitlines():
            s = line.strip()
            if len(s) >= DUP_MIN_LEN and not set(s) <= set("|-: "):
                occurrences[s].add(rel(md, root))
    dups = [{"text": t[:120], "files": sorted(fs)} for t, fs in occurrences.items() if len(fs) >= 2]
    result["duplicated_lines"] = {
        "count": len(dups),
        "samples": sorted(dups, key=lambda d: -len(d["files"]))[:15],
    }

    # --- scripts --------------------------------------------------------
    stdlib = getattr(sys, "stdlib_module_names", set())
    md_texts = {rel(md, root): read(md) for md in mds}
    scripts = []
    for p in files:
        if p.suffix not in SCRIPT_SUFFIXES:
            continue
        text = read(p)
        info = {
            "file": rel(p, root),
            "lines": len(text.splitlines()),
            "documented_in": sorted(k for k, v in md_texts.items() if p.name in v),
        }
        if p.suffix == ".py":
            try:
                tree = ast.parse(text)
                info["docstring"] = bool(ast.get_docstring(tree))
                mods = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        mods |= {a.name.split(".")[0] for a in node.names}
                    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                        mods.add(node.module.split(".")[0])
                info["third_party_imports"] = sorted(m for m in mods if stdlib and m not in stdlib)
                info["argparse"] = "argparse" in mods
                info["pep723"] = "# /// script" in text
            except SyntaxError as e:
                info["syntax_error"] = str(e)
        scripts.append(info)
    result["scripts"] = scripts

    # --- placeholders / todo --------------------------------------------
    ph: dict[str, set[str]] = defaultdict(set)
    todos = []
    for md in mds:
        text = strip_code(read(md))
        for m in PLACEHOLDER_RE.finditer(text):
            ph[m.group(0)].add(rel(md, root))
        for i, line in enumerate(read(md).splitlines(), 1):
            if TODO_RE.search(line):
                todos.append(f"{rel(md, root)}:{i}")
    result["placeholders"] = {
        k: sorted(v) for k, v in sorted(ph.items(), key=lambda kv: -len(kv[1]))
    }
    result["todos"] = todos

    result["tree"] = [{"file": rel(p, root), "lines": len(read(p).splitlines())} for p in files]
    return result


def to_markdown(r: dict) -> str:
    out = [f"# inspect: {r['template']}", ""]
    ep = r["entry_points"]
    out.append("## Entry points")
    for name, v in ep.items():
        extra = ""
        if name == "CLAUDE.md" and v["exists"]:
            extra = f" imports={v.get('imports')} alias_only={v.get('alias_only')}"
        out.append(f"- {name}: {'yes' if v['exists'] else 'MISSING'} ({v['lines']} lines){extra}")
    al = r["always_loaded"]
    out.append(
        f"- always loaded: {al['lines']} lines {al['files']}" + ("  ⚠ large" if al["warn"] else "")
    )

    out += ["", f"## Links (broken {len(r['broken_links'])}, escaping {len(r['escaping_links'])})"]
    out += [f"- BROKEN {b['at']} -> {b['target']}" for b in r["broken_links"]]
    out += [
        f"- ESCAPES {e['at']} -> {e['target']} (exists={e['exists']})" for e in r["escaping_links"]
    ]

    rc = r["reachability"]
    out += ["", "## Reachability", f"- max hops from AGENTS.md: {rc['max_hops_from_agents']}"]
    out.append(f"- unreachable from any entry: {rc['unreachable_from_any'] or 'none'}")
    out.append(f"- unreachable from AGENTS.md: {len(rc['unreachable_from_agents'])} files")
    out += [f"  - {f}" for f in rc["unreachable_from_agents"][:20]]

    ref = r["references"]
    out += [
        "",
        "## References",
        f"- {ref['files']} files / {ref['lines']} lines ({int(ref['share_of_md_lines'] * 100)}% of all md lines)",
    ]
    out += [f"- largest: {x['file']} ({x['lines']})" for x in ref["largest"]]
    out += [
        f"- NEAR-DUP {x['a']} ~ {x['b']} (jaccard {x['jaccard']})" for x in ref["near_duplicates"]
    ]

    d = r["duplicated_lines"]
    out += ["", f"## Duplicated lines across files ({d['count']})"]
    out += [f"- {', '.join(s['files'])}: {s['text']}" for s in d["samples"]]

    out += ["", f"## Scripts ({len(r['scripts'])})"]
    for s in r["scripts"]:
        flags = {
            k: s[k]
            for k in ("docstring", "argparse", "pep723", "third_party_imports", "syntax_error")
            if k in s
        }
        out.append(
            f"- {s['file']} ({s['lines']} lines) documented_in={s['documented_in'] or 'NOWHERE'} {flags}"
        )

    out += ["", "## Placeholders"]
    out += [f"- {k}: {len(v)} files" for k, v in list(r["placeholders"].items())[:15]] or ["- none"]
    out += ["", f"## TODO markers ({len(r['todos'])})"] + [f"- {t}" for t in r["todos"][:20]]

    out += ["", "## Tree"] + [f"- {t['file']} ({t['lines']})" for t in r["tree"]]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("targets", nargs="+", type=Path, help="template folder(s)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    results = []
    for t in args.targets:
        if not t.is_dir():
            print(f"skip (not a directory): {t}", file=sys.stderr)
            continue
        results.append(inspect(t))
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("\n".join(to_markdown(r) for r in results))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
