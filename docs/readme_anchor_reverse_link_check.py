#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import dataclass
from pathlib import Path

from markdown_link_scanner import (
    MarkdownAnchor,
    collect_markdown_anchors,
    iter_markdown_files,
    iter_markdown_targets,
    iter_prose_lines,
    normalize_target,
)

DEFAULT_SCAN_PATHS = ("knowledge/cs/contents",)
REPO_ROOT = Path.cwd().resolve()
CONTENTS_ROOT = (REPO_ROOT / "knowledge/cs/contents").resolve(strict=False)
IGNORED_PREFIXES = ("http://", "https://", "mailto:")


@dataclass(frozen=True)
class StaleReverseLink:
    line_number: int
    raw_target: str
    anchor: str
    suggestion: MarkdownAnchor | None


@dataclass(frozen=True)
class Finding:
    path: Path
    readme_path: Path
    missing: bool
    stale_links: tuple[StaleReverseLink, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flag category markdown docs whose same-category README anchor reverse-link "
            "is missing or still points at a stale heading slug."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help=(
            "Markdown files or directories to scan. Defaults to knowledge/cs/contents."
        ),
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_category_doc(path: Path) -> bool:
    if path.name == "README.md":
        return False

    resolved = path.resolve(strict=False)
    try:
        relative = resolved.relative_to(CONTENTS_ROOT)
    except ValueError:
        return False

    return len(relative.parts) >= 2 and (resolved.parent / "README.md").is_file()


def resolve_target_path(target: str, source_path: Path) -> tuple[Path, str | None] | None:
    lowered = target.lower()
    if not target or lowered.startswith(IGNORED_PREFIXES) or target.startswith("#"):
        return None

    if "#" not in target:
        return None

    raw_path, anchor = target.split("#", 1)
    if not anchor:
        return None

    if raw_path.startswith("/"):
        resolved_path = (REPO_ROOT / raw_path.lstrip("/")).resolve(strict=False)
    else:
        resolved_path = (source_path.parent / raw_path).resolve(strict=False)

    return resolved_path, anchor


def suggest_anchor(anchor: str, anchors: dict[str, MarkdownAnchor]) -> MarkdownAnchor | None:
    match = difflib.get_close_matches(anchor, list(anchors), n=1, cutoff=0.55)
    if not match:
        return None
    return anchors[match[0]]


def scan_file(path: Path) -> Finding | None:
    if not is_category_doc(path):
        return None

    readme_path = path.parent / "README.md"

    readme_resolved = readme_path.resolve(strict=False)
    anchor_defs = collect_markdown_anchors(readme_path)
    stale_links: list[StaleReverseLink] = []
    found_same_readme_anchor = False
    for markdown_line in iter_prose_lines(path):
        for target_match in iter_markdown_targets(markdown_line.text, include_images=False):
            target = normalize_target(target_match.raw_target)
            resolved_target = resolve_target_path(target, path)
            if resolved_target is None:
                continue

            target_path, anchor = resolved_target
            if target_path != readme_resolved:
                continue

            found_same_readme_anchor = True
            if anchor in anchor_defs:
                continue

            stale_links.append(
                StaleReverseLink(
                    line_number=markdown_line.line_number,
                    raw_target=target,
                    anchor=anchor,
                    suggestion=suggest_anchor(anchor, anchor_defs),
                )
            )

    if not found_same_readme_anchor:
        return Finding(
            path=path,
            readme_path=readme_path,
            missing=True,
            stale_links=(),
        )

    if stale_links:
        return Finding(
            path=path,
            readme_path=readme_path,
            missing=False,
            stale_links=tuple(stale_links),
        )

    return None


def main() -> int:
    args = parse_args()
    markdown_files = iter_markdown_files(args.paths)
    category_docs = [path for path in markdown_files if is_category_doc(path)]

    if not category_docs:
        print("No category docs found beneath the supplied paths.")
        return 0

    findings: list[Finding] = []
    for markdown_file in category_docs:
        finding = scan_file(markdown_file)
        if finding is not None:
            findings.append(finding)

    if findings:
        missing_count = sum(1 for finding in findings if finding.missing)
        stale_count = len(findings) - missing_count

        print(
            "Category docs are missing a same-category README anchor reverse-link or "
            "still point at stale README anchors.",
            file=sys.stderr,
        )
        print(
            f"Scanned {len(category_docs)} markdown docs: "
            f"{missing_count} missing, {stale_count} stale.",
            file=sys.stderr,
        )

        for finding in sorted(findings, key=lambda item: display_path(item.path.resolve())):
            readme_display = display_path(finding.readme_path.resolve())
            print(
                f"{display_path(finding.path)} -> {readme_display}",
                file=sys.stderr,
            )

            if finding.missing:
                print(
                    "  missing: add a same-category README anchor reverse-link such as "
                    "`./README.md#...`.",
                    file=sys.stderr,
                )
                continue

            print("  stale same-category README anchor reverse-link(s):", file=sys.stderr)
            for stale_link in finding.stale_links:
                print(
                    f"    line {stale_link.line_number}: {stale_link.raw_target}",
                    file=sys.stderr,
                )
                if stale_link.suggestion is None:
                    continue
                print(
                    "      suggestion: "
                    f"./README.md#{stale_link.suggestion.anchor} "
                    f"({stale_link.suggestion.label}, line {stale_link.suggestion.line_number})",
                    file=sys.stderr,
                )

        print(
            "Prefer running this check on the category or docs touched in the current "
            "wave, then add or refresh the README anchor reverse-link and rerun.",
            file=sys.stderr,
        )
        return 1

    print(
        f"All {len(category_docs)} scanned category docs have valid same-category README "
        "anchor reverse-links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
