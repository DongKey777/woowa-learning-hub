#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

FENCE_RE = re.compile(r"^\s*```(?P<lang>[A-Za-z0-9_-]*)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]\n]+\]:\s*(.+?)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(?P<title>.+?)\s*$")
EXPLICIT_ANCHOR_RE = re.compile(r"""<a\s+id=["']([^"']+)["']\s*>\s*</a>""", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"""<(?P<tag>[A-Za-z0-9:-]+)\b(?P<attrs>[^>]*)>""")
HTML_ATTR_RE = re.compile(
    r"""\b(?P<attr>[A-Za-z_:][-A-Za-z0-9_:.]*)=["'](?P<value>[^"']*)["']""",
    re.IGNORECASE,
)
SIMPLE_QUOTED_TITLE_RE = re.compile(
    r"""^(?P<target>\S+)(?:\s+(?:"[^"]*"|'[^']*'))\s*$"""
)
LOCAL_ASSET_HTML_ATTRS = ("href", "poster", "src", "srcset")
LOCAL_ASSET_HTML_TAGS = ("a", "audio", "img", "source", "track", "video")


@dataclass(frozen=True)
class MarkdownLine:
    line_number: int
    text: str
    fence_lang: str = ""


@dataclass(frozen=True)
class MarkdownTarget:
    kind: str
    raw_target: str


@dataclass(frozen=True)
class MarkdownAnchor:
    anchor: str
    label: str
    line_number: int


@dataclass(frozen=True)
class HtmlTarget:
    tag: str
    attr: str
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


def iter_html_targets(
    line: str,
    *,
    attrs: tuple[str, ...] = LOCAL_ASSET_HTML_ATTRS,
    tags: tuple[str, ...] | None = None,
) -> list[HtmlTarget]:
    allowed_attrs = {attr.lower() for attr in attrs}
    allowed_tags = None if tags is None else {tag.lower() for tag in tags}
    targets: list[HtmlTarget] = []
    seen: set[tuple[str, str, str]] = set()

    for tag_match in HTML_TAG_RE.finditer(line):
        tag = tag_match.group("tag").lower()
        if allowed_tags is not None and tag not in allowed_tags:
            continue

        for attr_match in HTML_ATTR_RE.finditer(tag_match.group("attrs")):
            attr = attr_match.group("attr").lower()
            if attr not in allowed_attrs:
                continue

            raw_value = attr_match.group("value")
            raw_targets = (
                [
                    candidate.strip().split(None, 1)[0]
                    for candidate in raw_value.split(",")
                    if candidate.strip()
                ]
                if attr == "srcset"
                else [raw_value]
            )

            for raw_target in raw_targets:
                key = (tag, attr, raw_target)
                if key in seen:
                    continue
                seen.add(key)
                targets.append(HtmlTarget(tag=tag, attr=attr, raw_target=raw_target))

    return targets


def iter_local_asset_html_targets(line: str) -> list[HtmlTarget]:
    return iter_html_targets(line, attrs=LOCAL_ASSET_HTML_ATTRS, tags=LOCAL_ASSET_HTML_TAGS)


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


def collect_markdown_anchors(path: Path) -> dict[str, MarkdownAnchor]:
    anchors: dict[str, MarkdownAnchor] = {}
    slug_counts: dict[str, int] = {}

    for markdown_line in iter_prose_lines(path):
        line_number = markdown_line.line_number
        line = markdown_line.text

        for explicit_anchor in EXPLICIT_ANCHOR_RE.findall(line):
            anchors.setdefault(
                explicit_anchor,
                MarkdownAnchor(
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
        anchors.setdefault(
            anchor,
            MarkdownAnchor(anchor=anchor, label=title, line_number=line_number),
        )

    return anchors
