#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from markdown_link_scanner import (
    iter_markdown_files,
    iter_markdown_targets,
    iter_prose_lines,
    normalize_target,
)

DEFAULT_SCAN_PATHS = ("knowledge/cs/contents",)
REPO_ROOT = Path.cwd().resolve()
CONTENTS_ROOT = (REPO_ROOT / "knowledge/cs/contents").resolve(strict=False)
HEADING_RE = re.compile(r"^(#{1,6})\s+(?P<title>.+?)\s*$")
BEGINNER_MARKERS = (
    "난이도: 🟢 beginner",
    "beginner primer",
    "beginner bridge",
    "beginner companion",
    "beginner troubleshooting",
    "beginner follow-up",
    "beginner-safe",
)
ENTRYPOINT_STEM_CUES = ("primer", "bridge", "guide", "shortcut")
BROWSER_SESSION_BRIDGE_MARKERS = (
    "browser / session",
    "browser session",
    "login loop",
    "savedrequest",
    "jsessionid",
    "cookie-header gate",
    "browser 401",
    "login redirect",
)
FOLLOW_UP_HEADING_CUES = (
    "다음 읽기",
    "다음에 이어서 읽기",
    "다음에 이어서 보면 좋은 문서",
    "다음으로 어디를 읽을까",
    "이 다음에 어디로 이어 읽으면 좋은가",
    "여기까지 이해했으면 다음 deep dive",
    "다음 문서 라우팅",
    "이 문서 다음에 보면 좋은 문서",
    "질문별 다음 문서",
    "다음 단계와 복귀 경로",
    "다음 한 걸음과 복귀 경로",
    "beginner용 사다리",
    "안전한 handoff",
    "safe next doc",
    "detour에서 복귀하는",
)
IGNORED_PREFIXES = ("http://", "https://", "mailto:")


@dataclass(frozen=True)
class LinkEvidence:
    line_number: int
    raw_target: str


@dataclass(frozen=True)
class Finding:
    path: Path
    missing_return_path: bool
    missing_follow_up: bool
    return_path: LinkEvidence | None
    follow_up: LinkEvidence | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Warn when a beginner browser/session primer or bridge doc lacks both parts "
            "of the link contract: a same-category README anchor return-path and an "
            "obvious next safe follow-up."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="Markdown files or directories to scan. Defaults to knowledge/cs/contents.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_beginner_entrypoint_doc(path: Path) -> bool:
    if path.suffix != ".md" or path.name == "README.md":
        return False

    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(CONTENTS_ROOT)
    except ValueError:
        return False

    stem = path.stem.lower()
    matched_cues = [cue for cue in ENTRYPOINT_STEM_CUES if cue in stem]
    if not matched_cues:
        return False

    text = path.read_text(encoding="utf-8")
    preview = "\n".join(text.splitlines()[:80]).lower()
    if not any(marker in preview for marker in BEGINNER_MARKERS):
        return False

    if "primer" in matched_cues:
        return True

    return any(marker in preview for marker in BROWSER_SESSION_BRIDGE_MARKERS)


def resolve_target_path(target: str, source_path: Path) -> tuple[Path, str | None] | None:
    lowered = target.lower()
    if not target or lowered.startswith(IGNORED_PREFIXES) or target.startswith("#"):
        return None

    if "#" in target:
        raw_path, anchor = target.split("#", 1)
    else:
        raw_path, anchor = target, None

    if raw_path.startswith("/"):
        resolved_path = (REPO_ROOT / raw_path.lstrip("/")).resolve(strict=False)
    else:
        resolved_path = (source_path.parent / raw_path).resolve(strict=False)

    return resolved_path, anchor


def normalize_heading_cue(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"^\d+\.\s*", "", lowered)
    lowered = lowered.replace("`", "")
    lowered = lowered.replace("?", " ")
    lowered = re.sub(r"\([^)]*\)", " ", lowered)
    lowered = re.sub(r"[-_/]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def has_follow_up_cue(current_heading: str) -> bool:
    normalized_heading = normalize_heading_cue(current_heading)
    return any(cue in normalized_heading for cue in FOLLOW_UP_HEADING_CUES)


def scan_file(path: Path) -> Finding | None:
    if not is_beginner_entrypoint_doc(path):
        return None

    same_category_readme = (path.parent / "README.md").resolve(strict=False)
    current_heading = ""
    return_path: LinkEvidence | None = None
    follow_up: LinkEvidence | None = None

    for markdown_line in iter_prose_lines(path):
        heading_match = HEADING_RE.match(markdown_line.text)
        if heading_match is not None:
            current_heading = heading_match.group("title").strip()

        for target_match in iter_markdown_targets(markdown_line.text, include_images=False):
            target = normalize_target(target_match.raw_target)
            resolved = resolve_target_path(target, path)
            if resolved is None:
                continue

            target_path, anchor = resolved
            if target_path == same_category_readme and anchor:
                return_path = return_path or LinkEvidence(
                    line_number=markdown_line.line_number,
                    raw_target=target,
                )
                continue

            normalized_target = target_path.as_posix().lower()
            if not normalized_target.endswith(".md"):
                continue
            if target_path == path.resolve(strict=False):
                continue
            if target_path == same_category_readme:
                continue
            if follow_up is None and has_follow_up_cue(current_heading):
                follow_up = LinkEvidence(
                    line_number=markdown_line.line_number,
                    raw_target=target,
                )

    missing_return_path = return_path is None
    missing_follow_up = follow_up is None

    if not missing_return_path and not missing_follow_up:
        return None

    return Finding(
        path=path,
        missing_return_path=missing_return_path,
        missing_follow_up=missing_follow_up,
        return_path=return_path,
        follow_up=follow_up,
    )


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []

    for path in iter_markdown_files(args.paths):
        finding = scan_file(path)
        if finding is not None:
            findings.append(finding)

    if findings:
        print(
            "Beginner browser/session entrypoint warnings: add an obvious README anchor "
            "return-path and/or a next safe follow-up link.",
            file=sys.stderr,
        )
        for finding in findings:
            print(display_path(finding.path), file=sys.stderr)
            if finding.missing_return_path:
                print(
                    "  warning: missing same-category README anchor return-path "
                    "such as `./README.md#...`.",
                    file=sys.stderr,
                )
            if finding.missing_follow_up:
                print(
                    "  warning: missing obvious next safe follow-up link under a "
                    "`다음 읽기` / `다음 문서 라우팅` / `safe next doc` / "
                    "`안전한 handoff` style section.",
                    file=sys.stderr,
                )
            if finding.return_path is not None:
                print(
                    f"  found return-path at line {finding.return_path.line_number}: "
                    f"{finding.return_path.raw_target}",
                    file=sys.stderr,
                )
            if finding.follow_up is not None:
                print(
                    f"  found follow-up at line {finding.follow_up.line_number}: "
                    f"{finding.follow_up.raw_target}",
                    file=sys.stderr,
                )
        return 1

    print(
        "Primer link contract lint passed "
        "(beginner browser/session primers and bridge docs keep both a README anchor "
        "return-path and a safe follow-up)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
