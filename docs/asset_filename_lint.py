#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

DEFAULT_SCAN_PATHS = ("knowledge/cs", "docs")
FENCE_RE = re.compile(r"^\s*```")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
HTML_SIMPLE_ATTR_RE = re.compile(
    r"""<(?:img|a|source)\b[^>]*\b(?:src|href)=["']([^"']+)["']""",
    re.IGNORECASE,
)
HTML_SRCSET_RE = re.compile(
    r"""<(?:img|source)\b[^>]*\bsrcset=["']([^"']+)["']""",
    re.IGNORECASE,
)
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]\n]+\]:\s*(.+?)\s*$")
SIMPLE_QUOTED_TITLE_RE = re.compile(
    r"""^(?P<target>\S+)(?:\s+(?:"[^"]*"|'[^']*'))\s*$"""
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


def iter_inline_targets(line: str) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    index = 0

    while index < len(line):
        open_bracket = line.find("[", index)
        if open_bracket == -1:
            break

        close_bracket = line.find("]", open_bracket + 1)
        if close_bracket == -1:
            break

        if close_bracket + 1 >= len(line) or line[close_bracket + 1] != "(":
            index = close_bracket + 1
            continue

        cursor = close_bracket + 2
        depth = 1
        in_angle = False

        while cursor < len(line):
            char = line[cursor]
            if char == "<":
                in_angle = True
            elif char == ">" and in_angle:
                in_angle = False
            elif not in_angle:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        kind = (
                            "inline-image"
                            if open_bracket > 0 and line[open_bracket - 1] == "!"
                            else "inline-link"
                        )
                        targets.append((kind, line[close_bracket + 2 : cursor].strip()))
                        index = cursor + 1
                        break
            cursor += 1
        else:
            break

    return targets


def mask_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub(lambda match: " " * len(match.group(0)), line)


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


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<"):
        closing = target.find(">")
        if closing != -1:
            return target[1:closing].strip()

    title_match = SIMPLE_QUOTED_TITLE_RE.match(target)
    if title_match:
        return title_match.group("target")

    return target


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
    in_fence = False

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        masked_line = mask_inline_code(line)

        for kind, raw_target in iter_inline_targets(masked_line):
            finding = build_finding(path, line_number, kind, raw_target)
            if finding is not None:
                findings.append(finding)

        reference_match = REFERENCE_LINK_RE.match(masked_line)
        if reference_match:
            finding = build_finding(path, line_number, "reference-link", reference_match.group(1))
            if finding is not None:
                findings.append(finding)

        for kind, raw_target in iter_html_targets(masked_line):
            finding = build_finding(path, line_number, kind, raw_target)
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
        return 1

    print(
        f"No punctuation-heavy local asset filename references found in "
        f"{len(markdown_files)} markdown files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
