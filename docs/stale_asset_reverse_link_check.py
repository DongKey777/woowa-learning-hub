#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCAN_PATHS = ("knowledge/cs", "docs")
REPO_ROOT = Path.cwd().resolve()
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
    in_fence = False

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        masked_line = mask_inline_code(line)
        raw_targets: list[tuple[str, str]] = []
        raw_targets.extend(iter_inline_targets(masked_line))

        reference_match = REFERENCE_LINK_RE.match(masked_line)
        if reference_match:
            raw_targets.append(("reference-link", reference_match.group(1)))

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
                    line_number=line_number,
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
