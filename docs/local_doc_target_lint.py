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
    iter_html_targets,
    iter_markdown_files,
    iter_markdown_targets,
    iter_prose_lines,
    mask_inline_code,
    normalize_target,
)

DEFAULT_SCAN_PATHS = ("knowledge/cs", "docs")
REPO_ROOT = Path.cwd().resolve()
LOCAL_DOC_SUFFIX = ".md"
IGNORED_PREFIXES = ("http://", "https://", "mailto:", "data:")


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    kind: str
    target: str
    issue: str
    anchor: str | None = None
    suggestion: MarkdownAnchor | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fail repo-local markdown links when the `.md` target is missing or the "
            "`#anchor` slug no longer exists."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="Markdown files or directories to scan. Defaults to knowledge/cs and docs.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def iter_html_doc_targets(line: str) -> list[tuple[str, str]]:
    return [
        ("html-doc-link", target.raw_target)
        for target in iter_html_targets(line, attrs=("href",), tags=("a",))
    ]


def is_local_doc_target(target: str) -> bool:
    if not target:
        return False
    if target.startswith("#"):
        return True

    lowered = target.lower()
    if lowered.startswith(IGNORED_PREFIXES):
        return False

    candidate = target.split("#", 1)[0]
    if not candidate or candidate.endswith("/"):
        return False

    return candidate.lower().endswith(LOCAL_DOC_SUFFIX)


def resolve_target(target: str, source_path: Path) -> tuple[Path, str | None]:
    if target.startswith("#"):
        return source_path.resolve(strict=False), target[1:] or None

    if "#" in target:
        raw_path, anchor = target.split("#", 1)
    else:
        raw_path, anchor = target, None

    if raw_path.startswith("/"):
        resolved = (REPO_ROOT / raw_path.lstrip("/")).resolve(strict=False)
    else:
        resolved = (source_path.parent / raw_path).resolve(strict=False)

    return resolved, anchor or None


def suggest_anchor(anchor: str, anchors: dict[str, MarkdownAnchor]) -> MarkdownAnchor | None:
    match = difflib.get_close_matches(anchor, list(anchors), n=1, cutoff=0.55)
    if not match:
        return None
    return anchors[match[0]]


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    anchor_cache: dict[Path, dict[str, MarkdownAnchor]] = {}

    for markdown_line in iter_prose_lines(path):
        masked_line = mask_inline_code(markdown_line.text)
        raw_targets = [
            (target.kind, target.raw_target)
            for target in iter_markdown_targets(markdown_line.text, include_images=False)
        ]
        raw_targets.extend(iter_html_doc_targets(masked_line))

        for kind, raw_target in raw_targets:
            target = normalize_target(raw_target)
            if not is_local_doc_target(target):
                continue

            resolved_path, anchor = resolve_target(target, path)
            if not resolved_path.exists():
                findings.append(
                    Finding(
                        path=path,
                        line_number=markdown_line.line_number,
                        kind=kind,
                        target=target,
                        issue="missing-doc",
                    )
                )
                continue

            if anchor is None:
                continue

            anchors = anchor_cache.setdefault(
                resolved_path, collect_markdown_anchors(resolved_path)
            )
            if anchor in anchors:
                continue

            findings.append(
                Finding(
                    path=path,
                    line_number=markdown_line.line_number,
                    kind=kind,
                    target=target,
                    issue="stale-anchor",
                    anchor=anchor,
                    suggestion=suggest_anchor(anchor, anchors),
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
            "Markdown/HTML local doc links point at missing `.md` targets or stale `#anchor` slugs.",
            file=sys.stderr,
        )
        for finding in findings:
            message = (
                f"{display_path(finding.path)}:{finding.line_number}: "
                f"{finding.kind} -> {finding.target} [{finding.issue}]"
            )
            if finding.issue == "stale-anchor" and finding.suggestion is not None:
                message += (
                    f" suggestion=#{finding.suggestion.anchor} "
                    f"({finding.suggestion.label}, line {finding.suggestion.line_number})"
                )
            print(message, file=sys.stderr)
        print(
            "Update the local markdown path or refresh the anchor slug in the same turn, "
            "then rerun this lint.",
            file=sys.stderr,
        )
        return 1

    print(f"No missing local markdown targets or stale anchor refs found in {len(markdown_files)} markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
