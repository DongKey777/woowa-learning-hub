#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FENCE_RE = re.compile(r"^\s*```(?P<lang>[A-Za-z0-9_-]*)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]\n]+\]:\s*(.+?)\s*$")
SIMPLE_QUOTED_TITLE_RE = re.compile(
    r"""^(?P<target>\S+)(?:\s+(?:"[^"]*"|'[^']*'))\s*$"""
)


@dataclass(frozen=True)
class MarkdownLine:
    line_number: int
    text: str
    fence_lang: str = ""


@dataclass(frozen=True)
class MarkdownTarget:
    kind: str
    raw_target: str


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


def iter_prose_lines(path: Path) -> list[MarkdownLine]:
    lines: list[MarkdownLine] = []
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
            lines.append(MarkdownLine(line_number=line_number, text=line))

    return lines


def iter_fence_lines(path: Path) -> list[MarkdownLine]:
    lines: list[MarkdownLine] = []
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

        if in_fence:
            lines.append(MarkdownLine(line_number=line_number, text=line, fence_lang=fence_lang))

    return lines


def mask_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub(lambda match: " " * len(match.group(0)), line)


def iter_inline_targets(line: str) -> list[MarkdownTarget]:
    targets: list[MarkdownTarget] = []
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
                        targets.append(
                            MarkdownTarget(
                                kind=kind,
                                raw_target=line[close_bracket + 2 : cursor].strip(),
                            )
                        )
                        index = cursor + 1
                        break
            cursor += 1
        else:
            break

    return targets


def iter_reference_targets(line: str) -> list[MarkdownTarget]:
    reference_match = REFERENCE_LINK_RE.match(line)
    if reference_match is None:
        return []

    return [MarkdownTarget(kind="reference-link", raw_target=reference_match.group(1))]


def iter_markdown_targets(
    line: str,
    *,
    include_images: bool = True,
    include_references: bool = True,
    mask_code_spans: bool = True,
) -> list[MarkdownTarget]:
    scan_line = mask_inline_code(line) if mask_code_spans else line
    targets = [
        target
        for target in iter_inline_targets(scan_line)
        if include_images or target.kind != "inline-image"
    ]
    if include_references:
        targets.extend(iter_reference_targets(scan_line))
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
