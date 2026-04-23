#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from markdown_link_scanner import (
    iter_fence_lines,
    iter_markdown_files,
    iter_markdown_targets,
    normalize_target,
)

DEFAULT_SCAN_PATHS = ("knowledge/cs", "docs")
LINKISH_SUFFIXES = (
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".gif",
    ".webp",
    ".json",
    ".yml",
    ".yaml",
    ".txt",
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    kind: str
    fence_lang: str
    line: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flag markdown link-like patterns inside fenced code blocks before "
            "broken-link reporting runs."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="Markdown files or directories to scan. Defaults to knowledge/cs and docs.",
    )
    return parser.parse_args()


def target_looks_linkish(target: str) -> bool:
    return (
        target.startswith(("./", "../", "/", "#"))
        or "://" in target
        or target.startswith("mailto:")
        or target.endswith(LINKISH_SUFFIXES)
        or any(suffix in target for suffix in (".md#", ".png#", ".jpg#", ".svg#"))
    )


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for markdown_line in iter_fence_lines(path):
        for target in iter_markdown_targets(markdown_line.text):
            if not target_looks_linkish(normalize_target(target.raw_target)):
                continue
            findings.append(
                Finding(
                    path=path,
                    line_number=markdown_line.line_number,
                    kind=target.kind,
                    fence_lang=markdown_line.fence_lang,
                    line=markdown_line.text.strip(),
                )
            )
            break

    return findings


def main() -> int:
    args = parse_args()
    markdown_files = iter_markdown_files(args.paths)

    findings: list[Finding] = []
    for markdown_file in markdown_files:
        findings.extend(scan_file(markdown_file))

    if findings:
        print(
            "Fenced code contains markdown link-like patterns that can become "
            "broken-link false positives.",
            file=sys.stderr,
        )
        for finding in findings:
            print(
                f"{finding.path}:{finding.line_number}: {finding.kind} "
                f"in fence({finding.fence_lang}) -> {finding.line}",
                file=sys.stderr,
            )
        print(
            "Fix with `] (` / `] :` spacing guards for literal markdown, or "
            "move path-only snippets to `text`/`yaml` fences.",
            file=sys.stderr,
        )
        return 1

    print(f"No fenced false-link candidates found in {len(markdown_files)} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
