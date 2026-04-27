#!/usr/bin/env python3
"""Static guardrail for beginner starter document quality.

Checks the curated beginner starter subset in this lane and fails when a
document is missing one of these beginner-facing anchors or link contracts:
- beginner-facing sections (mental model / comparison / common confusion)
- related-doc links resolve to existing files and anchors
- README has a matching anchor entry for every starter doc in the manifest
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
README_PATH = BASE_DIR / "README.md"
MANIFEST_START = "<!-- beginner-starter-manifest:start -->"
MANIFEST_END = "<!-- beginner-starter-manifest:end -->"

SECTION_PATTERNS = {
    "mental_model": re.compile(r"^#{2,6}\s+.*멘탈\s*모델", re.MULTILINE),
    "before_after": re.compile(
        r"^#{2,6}\s+.*("
        r"before\s*/\s*after"
        r"|before/after"
        r"|한\s*장\s*비교표"
        r"|한눈\s*비교"
        r"|10초\s*비교표"
        r"|30초\s*비교표"
        r"|비교표"
        r"|번역표"
        r"|대조표"
        r")",
        re.MULTILINE | re.IGNORECASE,
    ),
    "common_confusion": re.compile(
        r"^#{2,6}\s+.*("
        r"흔한\s*오해(?:와\s*함정)?"
        r"|자주\s*하는\s*오해"
        r"|자주\s*생기는\s*오해"
        r"|흔한\s*오해와\s*빠른\s*교정"
        r"|자주\s*하는\s*혼동"
        r"|오해\s*교정"
        r"|오해\s*faq"
        r"|혼동\s*faq"
        r"|헷갈리(?:는|기\s*쉬운)\s*(?:지점|포인트|부분)"
        r")",
        re.MULTILINE | re.IGNORECASE,
    ),
}

SECTION_LABELS = {
    "mental_model": "멘탈 모델 섹션",
    "before_after": "비교 섹션",
    "common_confusion": "오해/혼동 정리 섹션",
}

STARTER_DOC_PATTERN = re.compile(r"- \[([^\]]+)\]\(\./([^)]+\.md)\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
INTERNAL_README_LINK_PATTERN = re.compile(r"\]\(#([^)]+)\)")
RELATED_DOC_HEADER_PATTERN = re.compile(r"^>?\s*관련 문서:\s*$")
RELATED_DOC_ITEM_PATTERN = re.compile(r"^>?\s*-\s+\[([^\]]+)\]\(([^)]+)\)")


def slugify_heading(text: str) -> str:
    normalized = re.sub(r"`", "", text.strip().lower())
    normalized = re.sub(r"[^\w\s\-가-힣]", "", normalized, flags=re.UNICODE)
    normalized = re.sub(r"[\s\-]+", "-", normalized)
    return normalized.strip("-")


def load_starter_docs() -> list[tuple[str, str]]:
    if not README_PATH.exists():
        raise FileNotFoundError(f"README not found: {README_PATH}")

    readme_text = README_PATH.read_text(encoding="utf-8")
    try:
        manifest = readme_text.split(MANIFEST_START, 1)[1].split(MANIFEST_END, 1)[0]
    except IndexError as exc:
        raise ValueError("README beginner starter manifest block is missing.") from exc

    starter_docs: list[tuple[str, str]] = []
    for raw_line in manifest.splitlines():
        match = STARTER_DOC_PATTERN.search(raw_line.strip())
        if match:
            starter_docs.append((match.group(1), match.group(2)))

    if not starter_docs:
        raise ValueError("README starter manifest did not yield any markdown targets.")

    return starter_docs


def extract_heading_slugs(text: str) -> set[str]:
    return {slugify_heading(match.group(2)) for match in HEADING_PATTERN.finditer(text)}


def extract_related_doc_targets(text: str) -> list[str]:
    targets: list[str] = []
    in_related_docs = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not in_related_docs:
            if RELATED_DOC_HEADER_PATTERN.match(line):
                in_related_docs = True
            continue

        match = RELATED_DOC_ITEM_PATTERN.match(line)
        if match:
            targets.append(match.group(2))
            continue

        if line.strip() == "":
            if targets:
                break
            continue

        if targets:
            break

    return targets


def validate_link(source_path: Path, target: str) -> str | None:
    if target.startswith(("http://", "https://")):
        return None

    relative_target, _, anchor = target.partition("#")
    resolved_path = (
        (source_path.parent / relative_target).resolve()
        if relative_target
        else source_path.resolve()
    )

    if not resolved_path.exists():
        return f"관련 문서 링크 대상 파일이 없음: {target}"

    if anchor:
        heading_slugs = extract_heading_slugs(resolved_path.read_text(encoding="utf-8"))
        if anchor not in heading_slugs:
            return f"관련 문서 링크 앵커가 없음: {target}"

    return None


def validate_readme_anchor(readme_text: str, title: str) -> list[str]:
    failures: list[str] = []
    title_slug = slugify_heading(title)
    readme_headings = extract_heading_slugs(readme_text)
    readme_links = set(INTERNAL_README_LINK_PATTERN.findall(readme_text))

    if title_slug not in readme_headings:
        failures.append(f"README 섹션 헤딩이 없음: {title}")

    if title_slug not in readme_links:
        failures.append(f"README 앵커 링크가 없음: #{title_slug}")

    return failures


def main() -> int:
    try:
        starter_docs = load_starter_docs()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Beginner starter section check failed: {exc}")
        return 1

    readme_text = README_PATH.read_text(encoding="utf-8")
    failures: list[tuple[str, list[str]]] = []

    for title, relative_path in starter_docs:
        path = BASE_DIR / relative_path
        if not path.exists():
            failures.append((relative_path, ["문서 파일이 없음"]))
            continue

        text = path.read_text(encoding="utf-8")
        doc_failures = [
            SECTION_LABELS[key]
            for key, pattern in SECTION_PATTERNS.items()
            if not pattern.search(text)
        ]

        related_doc_targets = extract_related_doc_targets(text)
        if len(related_doc_targets) < 3:
            doc_failures.append("관련 문서 링크 3개 미만")
        else:
            for target in related_doc_targets:
                link_failure = validate_link(path, target)
                if link_failure:
                    doc_failures.append(link_failure)

        doc_failures.extend(validate_readme_anchor(readme_text, title))

        if doc_failures:
            failures.append((relative_path, doc_failures))

    if failures:
        print("Beginner starter quality check failed.")
        for relative_path, issues in failures:
            print(f"- {relative_path}: {'; '.join(issues)}")
        return 1

    print(
        "Beginner starter quality check passed "
        f"({len(starter_docs)} docs from README starter list: "
        "mental model / comparison / common confusion / related-doc links / README anchors)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
