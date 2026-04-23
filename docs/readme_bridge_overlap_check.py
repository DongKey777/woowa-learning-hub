#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCAN_PATHS = ("knowledge/cs",)
HEADING_RE = re.compile(r"^(#{2,6})\s+(?P<title>.+?)\s*$")
INLINE_LINK_RE = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)")
QUICK_SECTION_TITLES = {
    "빠른 시작",
    "빠른 탐색",
    "quick routes",
    "quick start",
    "quick-start",
}
BRIDGE_SECTION_MARKERS = ("연결해서 보면 좋은 문서", "cross-category bridge")


@dataclass(frozen=True)
class Section:
    title: str
    level: int
    start_line: int
    end_line: int


@dataclass(frozen=True)
class LinkOccurrence:
    display_target: str
    line_number: int


@dataclass(frozen=True)
class Overlap:
    canonical_target: str
    quick_occurrence: LinkOccurrence
    bridge_occurrence: LinkOccurrence


@dataclass(frozen=True)
class Finding:
    path: Path
    quick_section: Section
    bridge_section: Section
    overlaps: tuple[Overlap, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flag README quick-start sections that repeat multiple local markdown "
            "links already owned by a later grouped bridge section."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="README files or directories to scan. Defaults to knowledge/cs.",
    )
    parser.add_argument(
        "--min-overlap",
        type=int,
        default=2,
        help="Minimum number of repeated markdown links required to fail. Default: 2.",
    )
    return parser.parse_args()


def normalize_title(title: str) -> str:
    collapsed = re.sub(r"\s+", " ", title.replace("`", "")).strip().lower()
    return collapsed


def iter_readme_files(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for raw_path in raw_paths:
        path = Path(raw_path)
        candidates: list[Path]
        if path.is_dir():
            candidates = sorted(item for item in path.rglob("README.md") if item.is_file())
        elif path.is_file() and path.name == "README.md":
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


def collect_sections(path: Path) -> list[Section]:
    lines = path.read_text(encoding="utf-8").splitlines()
    headings: list[tuple[int, int, str]] = []

    for line_number, line in enumerate(lines, 1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        headings.append((line_number, len(match.group(1)), match.group("title").strip()))

    sections: list[Section] = []
    for index, (start_line, level, title) in enumerate(headings):
        end_line = len(lines)
        for next_line, next_level, _ in headings[index + 1 :]:
            if next_level <= level:
                end_line = next_line - 1
                break
        sections.append(
            Section(title=title, level=level, start_line=start_line, end_line=end_line)
        )

    return sections


def select_quick_and_bridge_sections(sections: list[Section]) -> tuple[Section, Section] | None:
    quick_section: Section | None = None

    for section in sections:
        if normalize_title(section.title) in QUICK_SECTION_TITLES:
            quick_section = section
            break

    if quick_section is None:
        return None

    for section in sections:
        if section.start_line <= quick_section.start_line:
            continue
        normalized = normalize_title(section.title)
        if any(marker in normalized for marker in BRIDGE_SECTION_MARKERS):
            return quick_section, section

    return None


def canonicalize_target(raw_target: str, base_dir: Path) -> str | None:
    if raw_target.startswith("#") or "://" in raw_target or raw_target.startswith("mailto:"):
        return None

    target = raw_target.strip("<>")
    target = target.split("#", 1)[0]
    if not target.endswith(".md"):
        return None

    if target.startswith("/"):
        return Path(target).as_posix()

    return (base_dir / target).resolve(strict=False).as_posix()


def collect_link_occurrences(path: Path, section: Section) -> dict[str, LinkOccurrence]:
    lines = path.read_text(encoding="utf-8").splitlines()
    occurrences: dict[str, LinkOccurrence] = {}

    for line_number in range(section.start_line, section.end_line + 1):
        for raw_target in INLINE_LINK_RE.findall(lines[line_number - 1]):
            canonical_target = canonicalize_target(raw_target, path.parent)
            if canonical_target is None or canonical_target in occurrences:
                continue
            occurrences[canonical_target] = LinkOccurrence(
                display_target=raw_target,
                line_number=line_number,
            )

    return occurrences


def scan_file(path: Path, min_overlap: int) -> Finding | None:
    sections = collect_sections(path)
    section_pair = select_quick_and_bridge_sections(sections)
    if section_pair is None:
        return None

    quick_section, bridge_section = section_pair
    quick_links = collect_link_occurrences(path, quick_section)
    bridge_links = collect_link_occurrences(path, bridge_section)

    overlapping_targets = sorted(set(quick_links) & set(bridge_links))
    if len(overlapping_targets) < min_overlap:
        return None

    overlaps = tuple(
        Overlap(
            canonical_target=target,
            quick_occurrence=quick_links[target],
            bridge_occurrence=bridge_links[target],
        )
        for target in overlapping_targets
    )
    return Finding(
        path=path,
        quick_section=quick_section,
        bridge_section=bridge_section,
        overlaps=overlaps,
    )


def main() -> int:
    args = parse_args()
    readme_files = iter_readme_files(args.paths)

    findings: list[Finding] = []
    for readme_file in readme_files:
        finding = scan_file(readme_file, args.min_overlap)
        if finding is not None:
            findings.append(finding)

    if findings:
        print(
            "README quick-start sections repeat multiple local markdown links "
            "already listed in a later grouped bridge section.",
            file=sys.stderr,
        )
        for finding in findings:
            print(
                f"{finding.path}: quick '{finding.quick_section.title}' "
                f"(line {finding.quick_section.start_line}) vs bridge "
                f"'{finding.bridge_section.title}' "
                f"(line {finding.bridge_section.start_line}) -> "
                f"{len(finding.overlaps)} overlap(s)",
                file=sys.stderr,
            )
            for overlap in finding.overlaps:
                print(
                    f"  quick line {overlap.quick_occurrence.line_number} / "
                    f"bridge line {overlap.bridge_occurrence.line_number}: "
                    f"{overlap.quick_occurrence.display_target}",
                    file=sys.stderr,
                )
        print(
            "Keep quick-start bullets as entrypoint anchors or route labels, and "
            "leave the detailed bridge bundle in the later grouped bridge section.",
            file=sys.stderr,
        )
        return 1

    print(f"No quick-start bridge overlap candidates found in {len(readme_files)} README files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
