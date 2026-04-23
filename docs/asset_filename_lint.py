#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from markdown_link_scanner import (
    iter_markdown_files,
    iter_markdown_targets,
    iter_prose_lines,
    mask_inline_code,
    normalize_target,
)

DEFAULT_SCAN_PATHS = ("knowledge/cs", "docs")
HTML_SIMPLE_ATTR_RE = re.compile(
    r"""<(?:img|a|source)\b[^>]*\b(?:src|href)=["']([^"']+)["']""",
    re.IGNORECASE,
)
HTML_SRCSET_RE = re.compile(
    r"""<(?:img|source)\b[^>]*\bsrcset=["']([^"']+)["']""",
    re.IGNORECASE,
)
ALLOWED_SEGMENT_RE = re.compile(r"^[가-힣A-Za-z0-9_-]+$")
ALLOWED_STEM_RE = re.compile(r"^[가-힣A-Za-z0-9_-]+$")
ALLOWED_EXTENSION_RE = re.compile(r"^[a-z0-9]+$")
LOCAL_DOC_SUFFIX = ".md"
IGNORED_PREFIXES = ("http://", "https://", "mailto:", "data:")


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    kind: str
    target: str
    issues: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flag punctuation-heavy local asset filenames referenced from Markdown "
            "or inline HTML before review."
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
    seen: set[tuple[str, str]] = set()

    for raw_target in HTML_SIMPLE_ATTR_RE.findall(line):
        pair = ("html-asset", raw_target)
        if pair in seen:
            continue
        seen.add(pair)
        targets.append(pair)

    for raw_srcset in HTML_SRCSET_RE.findall(line):
        for candidate in raw_srcset.split(","):
            entry = candidate.strip()
            if not entry:
                continue
            target = entry.split(None, 1)[0]
            pair = ("html-srcset", target)
            if pair in seen:
                continue
            seen.add(pair)
            targets.append(pair)

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


def iter_segments(target: str) -> list[str]:
    pure = PurePosixPath(target.split("#", 1)[0])
    return [segment for segment in pure.parts if segment not in ("/", ".", "..")]


def format_chars(chars: set[str]) -> str:
    rendered = []
    for char in sorted(chars):
        if char == " ":
            rendered.append("space")
        else:
            rendered.append(char)
    return ", ".join(rendered)


def collect_bad_chars(segment: str, allowed: re.Pattern[str]) -> set[str]:
    return {char for char in segment if not allowed.fullmatch(char)}


def collect_issues(target: str) -> tuple[str, ...]:
    segments = iter_segments(target)
    if not segments:
        return ()

    issues: list[str] = []
    directories = segments[:-1]
    filename = segments[-1]

    for directory in directories:
        bad_chars = collect_bad_chars(directory, ALLOWED_SEGMENT_RE)
        if bad_chars:
            issues.append(
                f"dir segment `{directory}` has scanner-hostile chars: {format_chars(bad_chars)}"
            )

    if "." in filename:
        stem, extension = filename.rsplit(".", 1)
    else:
        stem, extension = filename, ""

    if "." in stem:
        issues.append(f"filename stem `{stem}` uses extra `.`")

    bad_stem_chars = collect_bad_chars(stem.replace(".", ""), ALLOWED_STEM_RE)
    if bad_stem_chars:
        issues.append(
            f"filename stem `{stem}` has scanner-hostile chars: {format_chars(bad_stem_chars)}"
        )

    if extension:
        if extension != extension.lower():
            issues.append(f"extension `{extension}` should be lowercase")
        elif not ALLOWED_EXTENSION_RE.fullmatch(extension):
            issues.append(
                f"extension `{extension}` should use only lowercase letters and digits"
            )

    return tuple(issues)


def build_finding(
    path: Path,
    line_number: int,
    kind: str,
    raw_target: str,
) -> Finding | None:
    target = normalize_target(raw_target)
    if not is_local_asset_target(target):
        return None

    issues = collect_issues(target)
    if not issues:
        return None

    return Finding(
        path=path,
        line_number=line_number,
        kind=kind,
        target=target,
        issues=issues,
    )


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for markdown_line in iter_prose_lines(path):
        for target in iter_markdown_targets(markdown_line.text):
            finding = build_finding(
                path,
                markdown_line.line_number,
                target.kind,
                target.raw_target,
            )
            if finding is not None:
                findings.append(finding)

        for kind, raw_target in iter_html_targets(mask_inline_code(markdown_line.text)):
            finding = build_finding(path, markdown_line.line_number, kind, raw_target)
            if finding is not None:
                findings.append(finding)

    return findings


def main() -> int:
    args = parse_args()
    markdown_files = iter_markdown_files(args.paths)

    findings: list[Finding] = []
    for markdown_file in markdown_files:
        findings.extend(scan_file(markdown_file))

    if findings:
        print(
            "Markdown/HTML references contain local asset filenames with "
            "punctuation-heavy or scanner-hostile segments.",
            file=sys.stderr,
        )
        for finding in findings:
            print(
                f"{finding.path}:{finding.line_number}: {finding.kind} -> "
                f"{finding.target} [{'; '.join(finding.issues)}]",
                file=sys.stderr,
            )
        print(
            "Rename the asset to a scanner-safe path "
            "(`[가-힣A-Za-z0-9_-]+` stem, lowercase extension) and update the "
            "markdown reference in the same turn.",
            file=sys.stderr,
        )
        print(
            "If the problem is a missing target rather than filename hygiene, run "
            "`python docs/local_asset_existence_lint.py` as the companion check.",
            file=sys.stderr,
        )
        return 1

    print(
        f"No punctuation-heavy local asset filename references found in "
        f"{len(markdown_files)} markdown files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
