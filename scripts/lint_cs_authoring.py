"""Lint Beginner CS notes against docs/cs-authoring-guide.md.

Usage::

    python3 scripts/lint_cs_authoring.py path/to/file.md [path2.md ...]

Exits 0 when every file passes, 1 otherwise. Designed to be cheap (stdlib only)
so workers can run it in their own commit loop.

Checks for Beginner/Intermediate notes (all enforced by the contract in
docs/cs-authoring-guide.md):

1. H1 on the first non-empty line
2. ``> 한 줄 요약: ...`` blockquote in the first 10 lines
3. ``**난이도: 🟢 Beginner**`` (or 🟡 Intermediate / 🔴 Advanced / 🔴 Expert) — exact form
4. ``관련 문서:`` section with >= 3 bullets
5. ``retrieval-anchor-keywords:`` line with 8..15 lowercase entries
6. >= 5 H2 sections; each H2 body <= 1600 characters
7. final H2 must be ``## 한 줄 정리``

Only Beginner/Intermediate files are required to pass strict mode.
Advanced/Expert files are skipped to avoid retrofitting legacy deep-dive docs
into the beginner authoring template.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

H1_RE = re.compile(r"^#\s+\S")
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
SUMMARY_RE = re.compile(r"^>\s*한\s*줄\s*요약\s*:\s*\S")
DIFFICULTY_RE = re.compile(r"^\*\*난이도:\s*[🟢🟡🔴]\s*(Beginner|Intermediate|Advanced|Expert)\*\*\s*$")
RELATED_HEADER_RE = re.compile(r"^관련\s*문서\s*:\s*$")
ANCHOR_LINE_RE = re.compile(r"^retrieval-anchor-keywords\s*:\s*(.+)$", re.IGNORECASE)
BULLET_RE = re.compile(r"^\s*[-*]\s+\S")
CROSS_LINK_RE = re.compile(r"\(\.\.\/")
SYMPTOM_RE = re.compile(
    r"(뭐예요|왜\s|처음|헷갈|언제|어떻게|모르겠|기초|입문"
    r"|beginner|intro|basics|what is|why|how to)",
)
FINAL_SUMMARY_HEADING = "한 줄 정리"

MAX_H2_BODY_CHARS = 1600
MIN_ANCHORS = 8
MAX_ANCHORS = 15
MIN_RELATED = 3
MIN_H2_SECTIONS = 5
MIN_SYMPTOM_ANCHORS = 2
MAX_CODE_RATIO_IN_OVERVIEW = 0.6


class LintError(Exception):
    pass


def _find_h1(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        if line.strip() == "":
            continue
        if H1_RE.match(line):
            return i
        raise LintError("first non-empty line must be an H1 (`# ...`)")
    raise LintError("file is empty")


def _check_summary(lines: list[str], h1_idx: int) -> None:
    window = lines[h1_idx + 1 : h1_idx + 12]
    for line in window:
        if SUMMARY_RE.match(line):
            return
    raise LintError("missing `> 한 줄 요약: ...` blockquote within 10 lines of the H1")


def _check_difficulty(lines: list[str]) -> str:
    for line in lines:
        m = DIFFICULTY_RE.match(line.rstrip())
        if m:
            return m.group(1).lower()
    raise LintError(
        "missing exact difficulty label "
        "`**난이도: 🟢 Beginner**` (or 🟡 Intermediate / 🔴 Advanced / 🔴 Expert)"
    )


def _check_related_docs(lines: list[str]) -> None:
    for i, line in enumerate(lines):
        if RELATED_HEADER_RE.match(line.rstrip()):
            bullets = 0
            for follow in lines[i + 1 :]:
                if follow.strip() == "":
                    if bullets > 0:
                        break
                    continue
                if BULLET_RE.match(follow):
                    bullets += 1
                    continue
                # any non-bullet, non-empty line ends the section
                break
            if bullets < MIN_RELATED:
                raise LintError(
                    f"`관련 문서:` section has {bullets} bullets, need >= {MIN_RELATED}"
                )
            return
    raise LintError("missing `관련 문서:` section header")


def _check_anchors(lines: list[str]) -> None:
    for line in lines:
        m = ANCHOR_LINE_RE.match(line.strip())
        if not m:
            continue
        raw = m.group(1).strip()
        items = [piece.strip() for piece in raw.split(",") if piece.strip()]
        if not (MIN_ANCHORS <= len(items) <= MAX_ANCHORS):
            raise LintError(
                f"retrieval-anchor-keywords has {len(items)} entries, "
                f"need {MIN_ANCHORS}..{MAX_ANCHORS}"
            )
        for item in items:
            if item != item.lower():
                raise LintError(
                    f"retrieval-anchor entry must be lowercase: {item!r}"
                )
        return
    raise LintError("missing `retrieval-anchor-keywords:` line")


def _check_h2_sections(text: str) -> None:
    matches = list(H2_RE.finditer(text))
    if len(matches) < MIN_H2_SECTIONS:
        raise LintError(
            f"only {len(matches)} H2 sections, need >= {MIN_H2_SECTIONS}"
        )
    last_heading = matches[-1].group(1).strip()
    if FINAL_SUMMARY_HEADING not in last_heading:
        raise LintError(
            f"final H2 must contain `{FINAL_SUMMARY_HEADING}`, got `{last_heading}`"
        )
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if len(body) > MAX_H2_BODY_CHARS:
            raise LintError(
                f"H2 `{heading}` body is {len(body)} chars, exceeds {MAX_H2_BODY_CHARS} "
                f"(would trigger RAG hard-split)"
            )


class LintWarning(Exception):
    pass


def _warn_cross_category_bridge(lines: list[str]) -> None:
    in_related = False
    for line in lines:
        if RELATED_HEADER_RE.match(line.rstrip()):
            in_related = True
            continue
        if in_related:
            if line.strip() == "":
                continue
            if not BULLET_RE.match(line):
                break
            if CROSS_LINK_RE.search(line):
                return
    raise LintWarning(
        "no cross-category bridge link (../) in `관련 문서:` — "
        "add ≥1 link outside this category"
    )


def _warn_symptom_anchors(lines: list[str]) -> None:
    for line in lines:
        m = ANCHOR_LINE_RE.match(line.strip())
        if not m:
            continue
        raw = m.group(1).strip()
        items = [piece.strip() for piece in raw.split(",") if piece.strip()]
        symptom_count = sum(1 for item in items if SYMPTOM_RE.search(item))
        if symptom_count < MIN_SYMPTOM_ANCHORS:
            raise LintWarning(
                f"only {symptom_count} symptom-phrase anchors (need ≥{MIN_SYMPTOM_ANCHORS}) "
                f"— add learner phrases like '처음 배우는데', 'basics', '뭐예요'"
            )
        return


def _warn_overview_code_density(text: str) -> None:
    matches = list(H2_RE.finditer(text))
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        if "한눈에 보기" not in heading:
            continue
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body_lines = text[body_start:body_end].strip().splitlines()
        if not body_lines:
            return
        in_fence = False
        code_lines = 0
        for bl in body_lines:
            stripped = bl.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                code_lines += 1
        ratio = code_lines / len(body_lines) if body_lines else 0
        if ratio > MAX_CODE_RATIO_IN_OVERVIEW:
            raise LintWarning(
                f"`## 한눈에 보기` has {code_lines}/{len(body_lines)} code lines "
                f"({ratio:.0%}) — move code to `## 실무에서 쓰는 모습`"
            )
        return


def lint_file(path: Path) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)``."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        h1_idx = _find_h1(lines)
    except LintError as exc:
        return [str(exc)], []

    try:
        difficulty = _check_difficulty(lines)
    except LintError as exc:
        return [str(exc)], []
    if difficulty in {"advanced", "expert"}:
        return [], []

    for check in (
        lambda: _check_summary(lines, h1_idx),
        lambda: _check_related_docs(lines),
        lambda: _check_anchors(lines),
        lambda: _check_h2_sections(text),
    ):
        try:
            check()
        except LintError as exc:
            errors.append(str(exc))

    for warn_check in (
        lambda: _warn_cross_category_bridge(lines),
        lambda: _warn_symptom_anchors(lines),
        lambda: _warn_overview_code_density(text),
    ):
        try:
            warn_check()
        except LintWarning as exc:
            warnings.append(str(exc))

    return errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress per-file PASS lines; only print failures/warnings",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as failures (exit 1 on any WARN)",
    )
    args = parser.parse_args(argv)

    failed = 0
    warned = 0
    for path in args.paths:
        if not path.exists():
            print(f"[MISS] {path}: file not found", file=sys.stderr)
            failed += 1
            continue
        errors, warnings = lint_file(path)
        if errors:
            failed += 1
            print(f"[FAIL] {path}")
            for err in errors:
                print(f"  - {err}")
        if warnings:
            warned += 1
            if args.strict:
                failed += 1
            print(f"[WARN] {path}")
            for w in warnings:
                print(f"  - {w}")
        if not errors and not warnings and not args.quiet:
            print(f"[PASS] {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
