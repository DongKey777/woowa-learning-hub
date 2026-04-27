#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from markdown_link_scanner import (
    iter_markdown_files,
    iter_markdown_targets,
    iter_local_asset_html_targets,
    iter_prose_lines,
    mask_inline_code,
    normalize_target,
)

DEFAULT_SCAN_PATHS = ("knowledge/cs", "docs")
REPO_ROOT = Path.cwd().resolve()
LOCAL_DOC_SUFFIX = ".md"
IGNORED_PREFIXES = ("http://", "https://", "mailto:", "data:")


@dataclass(frozen=True)
class InboundReference:
    path: Path
    line_number: int
    kind: str
    target: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Group inbound Markdown/HTML references that still point at missing "
            "local assets after a rename or delete."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="Markdown files or directories to scan. Defaults to knowledge/cs and docs.",
    )
    return parser.parse_args()


def iter_html_targets(line: str) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for target in iter_local_asset_html_targets(line):
        kind = "html-srcset" if target.attr == "srcset" else "html-asset"
        targets.append((kind, target.raw_target))
    return targets


def is_local_asset_target(target: str) -> bool:
    if not target or target.startswith("#"):
        return False

    lowered = target.lower()
    if lowered.startswith(IGNORED_PREFIXES):
        return False

    candidate = target.split("#", 1)[0]
    if not candidate or candidate.endswith("/"):
        return False

    return not candidate.lower().endswith(LOCAL_DOC_SUFFIX)


def resolve_target(target: str, source_path: Path) -> Path:
    candidate = target.split("#", 1)[0]
    if candidate.startswith("/"):
        return (REPO_ROOT / candidate.lstrip("/")).resolve(strict=False)
    return (source_path.parent / candidate).resolve(strict=False)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def collect_file_references(path: Path) -> dict[str, list[InboundReference]]:
    findings: dict[str, list[InboundReference]] = defaultdict(list)
    for markdown_line in iter_prose_lines(path):
        masked_line = mask_inline_code(markdown_line.text)
        raw_targets = [
            (target.kind, target.raw_target)
            for target in iter_markdown_targets(markdown_line.text)
        ]
        raw_targets.extend(iter_html_targets(masked_line))

        for kind, raw_target in raw_targets:
            target = normalize_target(raw_target)
            if not is_local_asset_target(target):
                continue

            resolved = resolve_target(target, path)
            if resolved.exists():
                continue

            findings[display_path(resolved)].append(
                InboundReference(
                    path=path,
                    line_number=markdown_line.line_number,
                    kind=kind,
                    target=target,
                )
            )

    return findings


def main() -> int:
    args = parse_args()
    markdown_files = iter_markdown_files(args.paths)
    findings: dict[str, list[InboundReference]] = defaultdict(list)

    for markdown_file in markdown_files:
        for missing_target, references in collect_file_references(markdown_file).items():
            findings[missing_target].extend(references)

    if findings:
        print(
            "Missing local asset targets still have inbound Markdown/HTML references.",
            file=sys.stderr,
        )
        for missing_target in sorted(findings):
            references = sorted(
                findings[missing_target],
                key=lambda ref: (display_path(ref.path.resolve()), ref.line_number, ref.kind),
            )
            print(
                f"{missing_target} -> {len(references)} inbound reference(s)",
                file=sys.stderr,
            )
            for reference in references:
                print(
                    f"  {display_path(reference.path)}:{reference.line_number}: "
                    f"{reference.kind} -> {reference.target}",
                    file=sys.stderr,
                )
        print(
            "Rename or restore the asset, update every inbound reference, then rerun "
            "this sweep.",
            file=sys.stderr,
        )
        return 1

    print(f"No stale inbound local asset links found in {len(markdown_files)} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
