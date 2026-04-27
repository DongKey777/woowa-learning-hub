#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

LANE_ROOT = Path(__file__).resolve().parent
BEGINNER_RE = re.compile(r"난이도:\s*🟢\s*Beginner", re.IGNORECASE)
TITLE_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$")
PRIMER_HINT_RE = re.compile(r"(기초|입문|primer|basics|entrypoint)", re.IGNORECASE)
IGNORE_PRIMER_HINT_RE = re.compile(r"template", re.IGNORECASE)

ANCHOR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("quick check", re.compile(r"quick[\s-]?check|빠른 진입", re.IGNORECASE)),
    ("10초", re.compile(r"10초")),
    ("30초 비교표", re.compile(r"30초\s*비교표")),
    ("1분 예시", re.compile(r"1분\s*예시")),
)


@dataclass(frozen=True)
class Finding:
    path: Path
    missing_anchors: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint beginner design-pattern primers for a minimum retrieval anchor set: "
            "quick check, 10초, 30초 비교표, 1분 예시."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=[str(LANE_ROOT)],
        help=(
            "Markdown files or directories to scan. Defaults to the design-pattern lane."
        ),
    )
    parser.add_argument(
        "--all-beginner",
        action="store_true",
        help=(
            "Scan every beginner markdown doc. By default only primer-like beginner docs "
            "(기초 / 입문 / primer / basics / entrypoint) are checked."
        ),
    )
    return parser.parse_args()


def iter_markdown_files(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for raw_path in raw_paths:
        path = Path(raw_path)
        candidates: list[Path]
        if path.is_dir():
            candidates = sorted(item for item in path.rglob("*.md") if item.is_file())
        elif path.is_file() and path.suffix == ".md":
            candidates = [path]
        else:
            continue

        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(candidate)

    return files


def read_visible_lines(path: Path) -> list[str]:
    visible_lines: list[str] = []
    in_code_block = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if "retrieval-anchor-keywords:" in raw_line:
            continue
        visible_lines.append(raw_line)

    return visible_lines


def is_beginner_doc(lines: list[str]) -> bool:
    return any(BEGINNER_RE.search(line) for line in lines)


def extract_title(lines: list[str]) -> str:
    for line in lines:
        match = TITLE_RE.match(line.strip())
        if match is not None:
            return match.group("title")
    return ""


def is_primer_like(path: Path, title: str) -> bool:
    if IGNORE_PRIMER_HINT_RE.search(path.name):
        return False

    haystacks = (path.stem, title)
    return any(PRIMER_HINT_RE.search(text) for text in haystacks if text)


def collect_missing_anchors(lines: list[str]) -> tuple[str, ...]:
    joined = "\n".join(lines)
    missing = [
        anchor_name
        for anchor_name, pattern in ANCHOR_PATTERNS
        if pattern.search(joined) is None
    ]
    return tuple(missing)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    markdown_files = iter_markdown_files(args.paths)

    scoped_files: list[tuple[Path, list[str]]] = []
    for path in markdown_files:
        if path.name == "README.md":
            continue

        lines = read_visible_lines(path)
        if not is_beginner_doc(lines):
            continue

        title = extract_title(lines)
        if not args.all_beginner and not is_primer_like(path, title):
            continue

        scoped_files.append((path, lines))

    findings: list[Finding] = []
    for path, lines in scoped_files:
        missing_anchors = collect_missing_anchors(lines)
        if missing_anchors:
            findings.append(Finding(path=path, missing_anchors=missing_anchors))

    scope_label = "all beginner docs" if args.all_beginner else "primer-like beginner docs"
    if findings:
        print(
            f"Missing beginner primer anchors in {len(findings)} / {len(scoped_files)} "
            f"{scope_label}.",
            file=sys.stderr,
        )
        for finding in findings:
            missing = ", ".join(finding.missing_anchors)
            print(f"- {display_path(finding.path)}: {missing}", file=sys.stderr)
        print(
            "Add the missing anchor sections or rerun with a narrower scope if the file is "
            "not intended to be a primer.",
            file=sys.stderr,
        )
        return 1

    print(
        f"All {len(scoped_files)} {scope_label} include quick check / 10초 / "
        "30초 비교표 / 1분 예시 anchors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
