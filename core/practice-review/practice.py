#!/usr/bin/env python3
"""Routine operations for a practice-review folder: ingest exports, list pending, scaffold outputs, refresh.

Usage:
    uv run practice-review/practice.py ingest practice-review [--date 2026-10-20] [--source chatgpt] [--force]
    uv run practice-review/practice.py pending practice-review [--limit 5]
    uv run practice-review/practice.py new feedback practice-review --slug cafe-and-interview [--sessions a,b]
    uv run practice-review/practice.py new digest practice-review --slug october-first-half
    uv run practice-review/practice.py new suggestions practice-review --slug next-topics
    uv run practice-review/practice.py refresh practice-review

Commands:
    ingest   move inbox/*.md to sessions/YYYY/YYYY-MM-DD-slug.md with a Session frontmatter
             (status: unreviewed). The exported text is kept as is below the frontmatter.
             The date is --date, or the file's modified date. An export identical to an existing
             session is skipped; an export that continues an existing session (same text + more)
             is refused unless --force (guides/ingesting.md「同じスレッドの再エクスポート」).
    pending  list unreviewed sessions, oldest first, with their line counts.
    new      create an output file with frontmatter, banner and headings filled with （記入）.
             feedback: --sessions defaults to the oldest unreviewed sessions (at most 5), and
             those sessions are marked status: reviewed / reviewed_in: <the new file>.
    refresh  rewrite status / superseded_by / the banner line of every output and regenerate
             index.md. ingest and new run it automatically.

--today YYYY-MM-DD fixes "today" (default: the system date).
The rules come from lint_practice_review.py (same folder), so lint and refresh always agree.

Only the standard library is used.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_practice_review as lint  # noqa: E402

KIND_FOLDERS = {"feedback": "feedback", "digest": "digests", "suggestions": "suggestions"}
TITLES = {"feedback": "フィードバック", "digests": "まとめ", "suggestions": "題材提案"}


def write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def slugify(text):
    slug = re.sub(r"[^\w]+", "-", text.lower()).strip("-_")[:40].strip("-_")
    return slug or "session"


def unique_path(folder, date, slug):
    path = folder / f"{date}-{slug}.md"
    n = 2
    while path.exists():
        path = folder / f"{date}-{slug}-{n}.md"
        n += 1
    return path


def session_body(doc):
    end = lint.frontmatter_end(doc.lines)
    return "\n".join(doc.lines[end + 1:]).strip()


def cmd_ingest(root, args):
    vault = lint.load_vault(root)
    if not vault.inbox:
        print("inbox/ に取り込むファイルが無い")
        return 0
    bodies = {doc.stem: session_body(doc) for doc in vault.sessions if doc.fm is not None}
    status = 0
    for src in vault.inbox:
        if src.suffix.lower() != ".md":
            print(f"skip: {src.name}（.md 以外は取り込まない）")
            continue
        text = src.read_text(encoding="utf-8-sig").strip()
        same = next((s for s, b in bodies.items() if b == text), None)
        if same:
            print(f"skip: {src.name} は {same} と同じ内容。inbox/ から消してよい")
            continue
        cont = next((s for s, b in bodies.items() if b and text.startswith(b)), None)
        if cont and not args.force:
            print(f"refuse: {src.name} は {cont} の続き（再エクスポート）に見える。guides/ingesting.md を読む。取り込むなら --force")
            status = 1
            continue
        heading = next((m.group(1) for line in text.splitlines() if (m := re.match(r"^#\s+(.+?)\s*$", line))), None)
        title = (heading or src.stem).replace('"', "'")
        date = args.date or datetime.date.fromtimestamp(src.stat().st_mtime).isoformat()
        dest = unique_path(root / "sessions" / date[:4], date, slugify(title))
        front = ["---", f"type: {lint.SESSION_TYPE}", "status: unreviewed", f"date: {date}",
                 f'title: "{title}"', f"source: {args.source}", "reviewed_in:", "---", ""]
        write(dest, front + text.splitlines())
        bodies[dest.stem] = text
        src.unlink()
        print(f"ingest: {src.name} -> {dest.relative_to(root).as_posix()}")
    refresh(root)
    return status


def cmd_pending(root, args):
    vault = lint.load_vault(root)
    pending = vault.unreviewed()
    for doc in pending[: args.limit or None]:
        print(f"{doc.path.relative_to(root).as_posix()}\t{len(doc.lines)} lines\t{doc.get('title')}")
    print(f"{len(pending)} unreviewed")
    return 0


def output_lines(vault, folder, path, today, covers, sessions):
    front = ["---", f"type: {lint.OUTPUT_KINDS[folder][0]}", "status: current", f"generated_at: {today}",
             f"covers_through: {covers}"]
    if folder == "feedback":
        front.append(f"sessions: [{', '.join(d.stem for d in sessions)}]")
    front += ["superseded_by:", "---", "", "> 状態:", "", f"# {TITLES[folder]} {today}", ""]
    body = []
    if sessions:
        links = ", ".join(f"[{d.stem}]({lint.rel_link(path.parent, d.path)})" for d in sessions)
        body += [f"対象: {links}", ""]
    for name in lint.OUTPUT_KINDS[folder][2]:
        body += [f"## {name}", ""]
        if folder == "suggestions":
            body += [f"### {lint.FILL_MARK}", "", lint.FILL_MARK, "", f"### {lint.FILL_MARK}", "", lint.FILL_MARK, ""]
        else:
            body += [lint.FILL_MARK, ""]
    return front + body


def cmd_new(root, args):
    folder = KIND_FOLDERS[args.kind]
    vault = lint.load_vault(root)
    today = args.today
    states = lint.expected_states(vault)
    sessions = []
    if folder == "feedback":
        smap = vault.session_map()
        if args.sessions:
            names = [s.strip() for s in args.sessions.split(",") if s.strip()]
            missing = [n for n in names if n not in smap]
            if missing:
                print(f"error: sessions/ に無い: {', '.join(missing)}", file=sys.stderr)
                return 1
            sessions = [smap[n] for n in names]
        else:
            sessions = vault.unreviewed()[: lint.MAX_SESSIONS_PER_FEEDBACK]
        if not sessions:
            print("error: 未レビューのセッションが無い", file=sys.stderr)
            return 1
        if len(sessions) > lint.MAX_SESSIONS_PER_FEEDBACK:
            print(f"error: 1ファイルで扱うセッションは {lint.MAX_SESSIONS_PER_FEEDBACK} 件まで", file=sys.stderr)
            return 1
        done = [d.stem for d in sessions if d.get("status") == "reviewed"]
        if done:
            print(f"error: レビュー済み: {', '.join(done)}", file=sys.stderr)
            return 1
        covers = max(d.get("date") for d in sessions)
    elif folder == "digests":
        current = [d.get("covers_through") for d in vault.outputs["feedback"] if states[d.path][0] == "current"]
        covers = max(current, default=vault.latest_reviewed_date() or today)
    else:
        covers = vault.latest_reviewed_date() or today
    path = unique_path(root / folder, today, slugify(args.slug))
    write(path, output_lines(vault, folder, path, today, covers, sessions))
    for doc in sessions:
        lint.set_frontmatter(doc.lines, "status", "reviewed")
        lint.set_frontmatter(doc.lines, "reviewed_in", path.stem)
        write(doc.path, doc.lines)
    print(f"new: {path.relative_to(root).as_posix()}（{lint.FILL_MARK} を埋める）")
    refresh(root)
    return 0


def refresh(root):
    vault = lint.load_vault(root)
    states = lint.expected_states(vault)
    for docs in vault.outputs.values():
        for doc in docs:
            if doc.fm is None:
                continue
            status, succ = states[doc.path]
            lines = list(doc.lines)
            lint.set_frontmatter(lines, "status", status)
            lint.set_frontmatter(lines, "superseded_by", succ.stem if succ else "")
            line = lint.banner(vault, doc, status, succ)
            i = lint.banner_index(lines)
            if i is not None and lines[i].startswith("> 状態:"):
                lines[i] = line
            else:
                end = lint.frontmatter_end(lines)
                lines[end + 1:end + 1] = ["", line]
            if lines != doc.lines:
                write(doc.path, lines)
                print(f"refresh: {doc.path.relative_to(root).as_posix()}（{status}）")
    index = root / "index.md"
    text = lint.render_index(lint.load_vault(root))
    if not index.exists() or index.read_text(encoding="utf-8") != text:
        index.write_text(text, encoding="utf-8", newline="\n")
        print("refresh: index.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ingest", help="inbox/ のエクスポートを sessions/ に取り込む")
    p.add_argument("root", type=Path)
    p.add_argument("--date", help="セッションの日付 YYYY-MM-DD（既定: ファイルの更新日）")
    p.add_argument("--source", default="chatgpt", help="練習相手・ツール名（既定: chatgpt）")
    p.add_argument("--force", action="store_true", help="既存セッションの続きに見えても取り込む")
    p = sub.add_parser("pending", help="未レビューのセッションを古い順に表示する")
    p.add_argument("root", type=Path)
    p.add_argument("--limit", type=int, default=0)
    p = sub.add_parser("new", help="出力ファイルの雛形を作る")
    p.add_argument("kind", choices=sorted(KIND_FOLDERS))
    p.add_argument("root", type=Path)
    p.add_argument("--slug", required=True, help="ファイル名の後半（内容を表す短い語）")
    p.add_argument("--sessions", help="feedback の対象（セッションのファイル名、拡張子なし、カンマ区切り）")
    p = sub.add_parser("refresh", help="status・バナー・index.md を更新する")
    p.add_argument("root", type=Path)
    for p in sub.choices.values():
        p.add_argument("--today", default=datetime.date.today().isoformat(), help="今日の日付 YYYY-MM-DD")
    args = parser.parse_args()
    if not args.root.is_dir():
        print(f"{args.root}: フォルダが見つからない", file=sys.stderr)
        return 2
    if getattr(args, "date", None) and not lint.DATE.match(args.date):
        print("--date は YYYY-MM-DD", file=sys.stderr)
        return 2
    if args.command == "ingest":
        return cmd_ingest(args.root, args)
    if args.command == "pending":
        return cmd_pending(args.root, args)
    if args.command == "new":
        return cmd_new(args.root, args)
    refresh(args.root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
