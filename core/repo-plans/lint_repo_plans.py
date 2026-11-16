#!/usr/bin/env python3
"""Lint a repo-plans folder: frontmatter values, phase order, completion gate, links.

Usage:
    uv run repo-plans/lint_repo_plans.py repo-plans
    python repo-plans/lint_repo_plans.py repo-plans [--strict]
    uv run repo-plans/lint_repo_plans.py --examples repo-plans/references

Checks (the definitions live in guides/plan-format.md and guides/plan-skeleton.md):
    - phase plans (`01-specification-and-technology/*.md`, `02-minimal-delivery/*.md`,
      `03-foundation/*.md`): frontmatter exists, `type` is Repository Phase Plan,
      `status` is drafting / revising / complete, file name is `{MM}-{slice}.md`
    - phase plans have the skeleton headings (PLAN_SECTIONS)
    - `complete` plans have a `## フェーズ完了ゲート` section and no `- [ ]`
    - a later phase has plans only when every earlier phase is complete
    - rough/*.md: `type` is Repository Rough Plan, `status` is drafting / promoted / dropped,
      the headings in ROUGH_SECTIONS exist, and a `promoted` one links from 詳細計画への移行先
    - asis.md has the headings in ASIS_SECTIONS
    - phase-status.md: the 状態 of each phase agrees with its plan files
    - relative links in every .md file resolve (code blocks are skipped)

Problems are printed as `path:line: message`.
Exit code 1 if any error. `--strict` also fails on warnings.

`--examples` lints the template samples: the phase folders sit under snapshot
folders (`drafting/`, `revising/`, `complete/`) that hold the same plan at several
moments. Each plan's `status` must match its snapshot folder, a phase counts as
complete when it has a `complete` plan, and asis.md / phase-status.md are not
required. All other checks are the same as for a real repo-plans folder.

Only the standard library is used.
"""

import argparse
import re
import sys
from pathlib import Path

PHASES = ["01-specification-and-technology", "02-minimal-delivery", "03-foundation"]
SNAPSHOTS = ["drafting", "revising", "complete"]
# Headings required by guides/plan-skeleton.md. A heading matches when its text starts
# with the name, so `### 質問（回答まで…）` matches `### 質問`. Keep in sync with the skeleton.
PLAN_SECTIONS = [
    "## 目的と対象外",
    "## 前提",
    "## 計画",
    "## 完了条件と検証方法",
    "## ユーザーとの対話",
    "### 質問",
    "### レビュー項目",
    "### 回答と反映",
    "## 未決事項と引継ぎ",
]
# Headings required by guides/plan-format.md (ラフ案の status).
ROUGH_SECTIONS = [
    "## 依頼の原文",
    "## 何をしたいか",
    "## まだ決めていないこと",
    "## 次にすること",
    "## 詳細計画への移行先",
]
ROUGH_TARGET = "## 詳細計画への移行先"
# Headings of the shipped asis.md that the workflow relies on.
ASIS_SECTIONS = ["## 現在地", "## 次に行うこと", "## ブロッカーと確認待ち"]
PLAN_TYPE = "Repository Phase Plan"
PLAN_STATUSES = {"drafting", "revising", "complete"}
ROUGH_TYPE = "Repository Rough Plan"
ROUGH_STATUSES = {"drafting", "promoted", "dropped"}
PHASE_STATES = {"未開始", "進行中", "確認待ち", "完了", "中断"}
GATE_HEADING = re.compile(r"^##\s+フェーズ完了ゲート\s*$")
UNCHECKED = re.compile(r"^\s*- \[ \]")
PLAN_NAME = re.compile(r"^\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
LINK = re.compile(r"\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STATUS_ROW = re.compile(r"^\|\s*([123])\.[^|]*\|\s*([^|]+?)\s*\|")
SKIP_FILES = {"readme.md", "agents.md", "claude.md"}


def headings(lines):
    """Return [("## text", line_no, last_line_no_of_section)] outside code blocks."""
    found = []
    in_fence = False
    for i, line in enumerate(lines, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        match = None if in_fence else HEADING.match(line)
        if match:
            found.append((f"{match.group(1)} {match.group(2)}", i))
    ends = [line - 1 for _, line in found[1:]] + [len(lines)]
    return [(text, line, end) for (text, line), end in zip(found, ends)]


def find_heading(found, name):
    """Return (line_no, last_line_no) of the first heading matching `name`, or None."""
    level, _, title = name.partition(" ")
    for text, line, end in found:
        text_level, _, text_title = text.partition(" ")
        if text_level == level and text_title.startswith(title):
            return line, end
    return None


def parse_frontmatter(lines):
    """Return {key: (value, line_no)} for `key: value` lines, or None if absent."""
    if not lines or lines[0].strip() != "---":
        return None
    result = {}
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return result
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*(?:#.*)?$", line)
        if match:
            result[match.group(1)] = (match.group(2), i)
    return None


class Linter:
    def __init__(self, root, examples=False):
        self.root = root
        self.examples = examples
        self.errors = []
        self.warnings = []
        self.checked = 0

    def _format(self, path, line, msg):
        rel = path.relative_to(self.root.parent) if path.is_relative_to(self.root.parent) else path
        return f"{rel}:{line}: {msg}"

    def error(self, path, msg, line=1):
        self.errors.append(self._format(path, line, msg))

    def warn(self, path, msg, line=1):
        self.warnings.append(self._format(path, line, msg))

    @staticmethod
    def read_lines(path):
        return path.read_text(encoding="utf-8").splitlines()

    def check_sections(self, path, lines, required):
        found = headings(lines)
        for name in required:
            if find_heading(found, name) is None:
                self.error(path, f"'{name}' 節がない")
        return found

    def check_frontmatter(self, path, lines, expected_type, statuses):
        fm = parse_frontmatter(lines)
        if fm is None:
            self.error(path, "frontmatter（--- で囲んだ type / status）がない")
            return None
        type_value, type_line = fm.get("type", (None, 1))
        if type_value != expected_type:
            self.error(
                path, f"type は '{expected_type}' であるべき（実際: {type_value!r}）", type_line
            )
        status, status_line = fm.get("status", (None, 1))
        if status not in statuses:
            allowed = " / ".join(sorted(statuses))
            self.error(path, f"status は {allowed} のいずれか（実際: {status!r}）", status_line)
            return None
        return status

    def lint_phase_plan(self, path, snapshot=None):
        self.checked += 1
        lines = self.read_lines(path)
        if not PLAN_NAME.match(path.name):
            self.warn(path, "ファイル名は {MM}-{slice}.md（例: 01-first-slice.md）にする")
        status = self.check_frontmatter(path, lines, PLAN_TYPE, PLAN_STATUSES)
        if snapshot and status and status != snapshot:
            self.error(
                path,
                f"記入例の status は時点フォルダ名 '{snapshot}' と同じにする（実際: {status!r}）",
            )
        self.check_sections(path, lines, PLAN_SECTIONS)
        if status != "complete":
            return status
        if not any(GATE_HEADING.match(line) for line in lines):
            self.error(path, "complete の計画に '## フェーズ完了ゲート' 節がない")
        in_fence = False
        for i, line in enumerate(lines, start=1):
            if FENCE.match(line):
                in_fence = not in_fence
            elif not in_fence and UNCHECKED.match(line):
                self.error(path, "complete の計画に未チェックの項目 '- [ ]' が残っている", i)
        return status

    def lint_rough(self, path):
        self.checked += 1
        lines = self.read_lines(path)
        status = self.check_frontmatter(path, lines, ROUGH_TYPE, ROUGH_STATUSES)
        target = find_heading(self.check_sections(path, lines, ROUGH_SECTIONS), ROUGH_TARGET)
        if status == "promoted" and target:
            start, end = target
            if not any(LINK.search(line) for line in lines[start:end]):
                self.error(
                    path, f"promoted のラフ案は '{ROUGH_TARGET}' に計画へのリンクを書く", start
                )

    def lint_asis(self):
        path = self.root / "asis.md"
        if not path.is_file():
            self.error(path, "asis.md がない")
            return
        self.check_sections(path, self.read_lines(path), ASIS_SECTIONS)

    def plan_files(self, folder):
        if not folder.is_dir():
            return []
        return sorted(p for p in folder.glob("*.md") if p.name.lower() not in SKIP_FILES)

    def phase_folders(self, phase):
        """Return [(folder, snapshot)] that hold the plans of one phase."""
        if self.examples:
            return [(self.root / snapshot / phase, snapshot) for snapshot in SNAPSHOTS]
        return [(self.root / phase, None)]

    def lint_phases(self):
        """Return {phase: [statuses]} after checking each plan and the phase order."""
        statuses = {}
        for index, phase in enumerate(PHASES):
            files, statuses[phase] = [], []
            for folder, snapshot in self.phase_folders(phase):
                for p in self.plan_files(folder):
                    files.append(p)
                    statuses[phase].append(self.lint_phase_plan(p, snapshot))
            if not files or index == 0:
                continue
            for earlier in PHASES[:index]:
                if not self.phase_complete(statuses[earlier]):
                    self.error(files[0], f"前のフェーズ {earlier}/ が完了していないのに計画がある")
                    break
        return statuses

    def phase_complete(self, statuses):
        if not statuses:
            return False
        if self.examples:
            return "complete" in statuses
        return all(s == "complete" for s in statuses)

    def lint_phase_status(self, statuses):
        path = self.root / "phase-status.md"
        if not path.is_file():
            if not self.examples:
                self.error(path, "phase-status.md がない")
            return
        seen = set()
        for i, line in enumerate(self.read_lines(path), start=1):
            match = STATUS_ROW.match(line)
            if not match:
                continue
            phase = PHASES[int(match.group(1)) - 1]
            state = match.group(2).strip("` ")
            seen.add(phase)
            plans = statuses.get(phase, [])
            if state not in PHASE_STATES:
                self.error(
                    path,
                    f"状態は {' / '.join(sorted(PHASE_STATES))} のいずれか（実際: {state!r}）",
                    i,
                )
            elif state == "未開始" and plans:
                self.error(path, f"{phase}/ に計画があるのに '未開始'", i)
            elif state == "完了" and not self.phase_complete(plans):
                self.error(path, f"{phase}/ の計画がすべて complete ではないのに '完了'", i)
            elif state in {"進行中", "確認待ち"} and not plans:
                self.error(path, f"{phase}/ に計画が無いのに '{state}'", i)
            elif state != "完了" and plans and self.phase_complete(plans):
                self.warn(path, f"{phase}/ の計画はすべて complete。状態を '完了' にする", i)
        for phase in PHASES:
            if phase not in seen:
                self.warn(path, f"フェーズ一覧の表に {phase} の行が見つからない")

    def lint_links(self):
        for path in sorted(self.root.rglob("*.md")):
            in_fence = False
            for i, line in enumerate(self.read_lines(path), start=1):
                if FENCE.match(line):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                for target in LINK.findall(re.sub(r"`[^`]*`", "", line)):
                    if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                        continue
                    file_part = target.split("#", 1)[0]
                    if not (path.parent / file_part).exists():
                        self.error(path, f"リンク切れ: {target}", i)

    def run(self):
        statuses = self.lint_phases()
        for path in self.plan_files(self.root / "rough"):
            self.lint_rough(path)
        if not self.examples:
            self.lint_asis()
        self.lint_phase_status(statuses)
        self.lint_links()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "plans_dir", type=Path, help="repo-plans フォルダ（--examples では記入例のフォルダ）"
    )
    parser.add_argument("--strict", action="store_true", help="警告でも非0で終了する")
    parser.add_argument(
        "--examples", action="store_true", help="テンプレートの記入例として検査する"
    )
    args = parser.parse_args()
    if not args.plans_dir.is_dir():
        print(f"error: not a directory: {args.plans_dir}", file=sys.stderr)
        return 1
    linter = Linter(args.plans_dir.resolve(), examples=args.examples)
    linter.run()
    for line in linter.warnings:
        print(f"warn : {line}")
    for line in linter.errors:
        print(f"error: {line}")
    print(
        f"checked {linter.checked} plan(s): {len(linter.errors)} error(s), {len(linter.warnings)} warning(s)"
    )
    return 1 if linter.errors or (args.strict and linter.warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
