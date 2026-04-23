#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from stale_asset_reverse_link_check import (
    DEFAULT_SCAN_PATHS,
    InboundReference,
    collect_file_references,
    display_path,
    iter_markdown_files,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fail unresolved repo-local asset targets referenced from Markdown or "
            "inline HTML."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="Markdown files or directories to scan. Defaults to knowledge/cs and docs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown_files = iter_markdown_files(args.paths)
    findings: dict[str, list[InboundReference]] = defaultdict(list)

    for markdown_file in markdown_files:
        for missing_target, references in collect_file_references(markdown_file).items():
            findings[missing_target].extend(references)

    if findings:
        print(
            "Markdown/HTML references still point at unresolved repo-local asset targets.",
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
            "Restore the asset or update every inbound reference, then rerun this lint.",
            file=sys.stderr,
        )
        return 1

    print(f"No unresolved repo-local asset targets found in {len(markdown_files)} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
