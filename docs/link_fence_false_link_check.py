#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCAN_PATHS = ("knowledge/cs", "docs")
FENCE_RE = re.compile(r"^\s*```(?P<lang>[A-Za-z0-9_-]*)")
INLINE_LINK_RE = re.compile(r"(!?\[[^\]\n]+\])\(([^)\s]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]\n]+\]:\s*(\S+)")
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


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    in_fence = False
    fence_lang = ""

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            if not in_fence:
                in_fence = True
                fence_lang = fence_match.group("lang") or "plain"
            else:
                in_fence = False
                fence_lang = ""
            continue

        if not in_fence:
            continue

        inline_match = INLINE_LINK_RE.search(line)
        if inline_match and target_looks_linkish(inline_match.group(2)):
            findings.append(
                Finding(
                    path=path,
                    line_number=line_number,
                    kind="inline-link",
                    fence_lang=fence_lang,
                    line=line.strip(),
                )
            )
            continue

        reference_match = REFERENCE_LINK_RE.search(line)
        if reference_match and target_looks_linkish(reference_match.group(1)):
            findings.append(
                Finding(
                    path=path,
                    line_number=line_number,
                    kind="reference-link",
                    fence_lang=fence_lang,
                    line=line.strip(),
                )
            )

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
