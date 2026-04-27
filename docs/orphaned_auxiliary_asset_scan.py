#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from markdown_link_scanner import iter_local_asset_html_targets

DEFAULT_SCAN_PATHS = ("knowledge/cs/contents",)
REPO_ROOT = Path.cwd().resolve()
ASSET_DIR_NAMES = {"img", "code"}
FENCE_RE = re.compile(r"^\s*```")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]\n]+\]:\s*(.+?)\s*$")
SIMPLE_QUOTED_TITLE_RE = re.compile(
    r"""^(?P<target>\S+)(?:\s+(?:"[^"]*"|'[^']*'))\s*$"""
)
LOCAL_DOC_SUFFIX = ".md"
IGNORED_PREFIXES = ("http://", "https://", "mailto:", "data:")
ALLOWED_SEGMENT_RE = re.compile(r"^[가-힣A-Za-z0-9_-]+$")
ALLOWED_STEM_RE = re.compile(r"^[가-힣A-Za-z0-9_-]+$")
ALLOWED_EXTENSION_RE = re.compile(r"^[a-z0-9]+$")


@dataclass(frozen=True)
class OrphanedAsset:
    path: Path
    group: str
    issues: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find img/code asset files under knowledge/cs/contents that no longer "
            "have inbound Markdown or inline HTML references from contents docs."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help=(
            "Markdown files or directories to scan. Directory inputs scan markdown "
            "and img/code assets beneath that directory; markdown files scan that "
            "file and sibling assets beneath its parent directory."
        ),
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


def iter_asset_files(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_dir():
            candidates = sorted(item for item in path.rglob("*") if item.is_file())
        elif path.is_file() and path.suffix == ".md":
            parent = path.parent
            candidates = sorted(item for item in parent.rglob("*") if item.is_file())
        else:
            continue

        for candidate in candidates:
            if not is_auxiliary_asset(candidate):
                continue
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
    for target in iter_local_asset_html_targets(line):
        kind = "html-srcset" if target.attr == "srcset" else "html-asset"
        targets.append((kind, target.raw_target))
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


def is_auxiliary_asset(path: Path) -> bool:
    if not path.is_file():
        return False
    return any(part in ASSET_DIR_NAMES for part in path.parts)


def iter_segments(path: Path) -> list[str]:
    pure = PurePosixPath(display_path(path))
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


def collect_issues(path: Path) -> tuple[str, ...]:
    segments = iter_segments(path)
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


def group_for(path: Path) -> str:
    parts = iter_segments(path)
    if len(parts) >= 5 and parts[:3] == ["knowledge", "cs", "contents"]:
        return f"{parts[3]}/{parts[4]}"
    return display_path(path.parent)


def collect_referenced_assets(markdown_files: list[Path]) -> set[Path]:
    referenced_assets: set[Path] = set()

    for path in markdown_files:
        in_fence = False

        for line in path.read_text(encoding="utf-8").splitlines():
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

            for _, raw_target in raw_targets:
                target = normalize_target(raw_target)
                if not is_local_asset_target(target):
                    continue

                resolved = resolve_target(target, path)
                if not resolved.exists() or not resolved.is_file():
                    continue

                if not is_auxiliary_asset(resolved):
                    continue

                referenced_assets.add(resolved)

    return referenced_assets


def build_orphaned_assets(asset_files: list[Path], referenced_assets: set[Path]) -> list[OrphanedAsset]:
    findings: list[OrphanedAsset] = []

    for asset_file in asset_files:
        resolved = asset_file.resolve()
        if resolved in referenced_assets:
            continue

        findings.append(
            OrphanedAsset(
                path=resolved,
                group=group_for(resolved),
                issues=collect_issues(resolved),
            )
        )

    return findings


def main() -> int:
    args = parse_args()
    markdown_files = iter_markdown_files(args.paths)
    asset_files = iter_asset_files(args.paths)
    referenced_assets = collect_referenced_assets(markdown_files)
    findings = build_orphaned_assets(asset_files, referenced_assets)

    if findings:
        grouped: dict[str, list[OrphanedAsset]] = defaultdict(list)
        for finding in findings:
            grouped[finding.group].append(finding)

        print(
            "Unreferenced img/code asset files were found under the scanned contents scope.",
            file=sys.stderr,
        )
        print(
            f"Scanned {len(markdown_files)} markdown files and {len(asset_files)} asset files; "
            f"found {len(findings)} orphaned asset(s).",
            file=sys.stderr,
        )
        for group in sorted(grouped):
            print(
                f"{group} -> {len(grouped[group])} orphaned asset(s)",
                file=sys.stderr,
            )
            for finding in sorted(grouped[group], key=lambda item: display_path(item.path)):
                issues = f" [{'; '.join(finding.issues)}]" if finding.issues else ""
                print(f"  {display_path(finding.path)}{issues}", file=sys.stderr)
        print(
            "Either add a contents-doc link, move the asset out of the retrieval path, "
            "or rename it before relinking, then rerun this scan.",
            file=sys.stderr,
        )
        return 1

    print(
        f"No unreferenced img/code asset files found across {len(markdown_files)} markdown "
        f"files and {len(asset_files)} asset files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
