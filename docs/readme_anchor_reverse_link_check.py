#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import html
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCAN_PATHS = ("knowledge/cs/contents",)
REPO_ROOT = Path.cwd().resolve()
CONTENTS_ROOT = (REPO_ROOT / "knowledge/cs/contents").resolve(strict=False)
FENCE_RE = re.compile(r"^\s*```")
HEADING_RE = re.compile(r"^(#{1,6})\s+(?P<title>.+?)\s*$")
EXPLICIT_ANCHOR_RE = re.compile(r"""<a\s+id=["']([^"']+)["']\s*>\s*</a>""", re.IGNORECASE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
SIMPLE_QUOTED_TITLE_RE = re.compile(
    r"""^(?P<target>\S+)(?:\s+(?:"[^"]*"|'[^']*'))\s*$"""
)
IGNORED_PREFIXES = ("http://", "https://", "mailto:")


@dataclass(frozen=True)
class AnchorDef:
    anchor: str
    label: str
    line_number: int


@dataclass(frozen=True)
class StaleReverseLink:
    line_number: int
    raw_target: str
    anchor: str
    suggestion: AnchorDef | None


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


def mask_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub(lambda match: " " * len(match.group(0)), line)


def iter_inline_targets(line: str) -> list[str]:
    targets: list[str] = []
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
                        if open_bracket == 0 or line[open_bracket - 1] != "!":
                            targets.append(line[close_bracket + 2 : cursor].strip())
                        index = cursor + 1
                        break
            cursor += 1
        else:
            break

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


def normalize_heading_title(title: str) -> str:
    text = html.unescape(title)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*_~]", "", text)
    return text.strip()


def slugify_heading(title: str) -> str:
    slug_chars: list[str] = []

    for char in normalize_heading_title(title).lower():
        if char.isspace():
            slug_chars.append("-")
            continue

        category = unicodedata.category(char)
        if category[0] in {"L", "N"} or char in {"-", "_"}:
            slug_chars.append(char)

    return "".join(slug_chars).strip("-")


def collect_readme_anchors(path: Path) -> dict[str, AnchorDef]:
    anchors: dict[str, AnchorDef] = {}
    slug_counts: dict[str, int] = {}
    in_fence = False

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        for explicit_anchor in EXPLICIT_ANCHOR_RE.findall(line):
            anchors.setdefault(
                explicit_anchor,
                AnchorDef(
                    anchor=explicit_anchor,
                    label=f"explicit anchor `{explicit_anchor}`",
                    line_number=line_number,
                ),
            )

        heading_match = HEADING_RE.match(line)
        if heading_match is None:
            continue

        title = normalize_heading_title(heading_match.group("title"))
        base_slug = slugify_heading(title)
        if not base_slug:
            continue

        suffix = slug_counts.get(base_slug, 0)
        anchor = base_slug if suffix == 0 else f"{base_slug}-{suffix}"
        slug_counts[base_slug] = suffix + 1
        anchors.setdefault(anchor, AnchorDef(anchor=anchor, label=title, line_number=line_number))

    return anchors


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


def suggest_anchor(anchor: str, anchors: dict[str, AnchorDef]) -> AnchorDef | None:
    match = difflib.get_close_matches(anchor, list(anchors), n=1, cutoff=0.55)
    if not match:
        return None
    return anchors[match[0]]


def scan_file(path: Path) -> Finding | None:
    if not is_category_doc(path):
        return None

    readme_path = path.parent / "README.md"

    readme_resolved = readme_path.resolve(strict=False)
    anchor_defs = collect_readme_anchors(readme_path)
    stale_links: list[StaleReverseLink] = []
    found_same_readme_anchor = False
    in_fence = False

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        for raw_target in iter_inline_targets(mask_inline_code(line)):
            target = normalize_target(raw_target)
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
                    line_number=line_number,
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
