#!/usr/bin/env python3
"""Smoke-test the beginner ladder links across root README, roadmap, and primer."""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CS_ROOT = BASE_DIR.parent

ROOT_README = CS_ROOT / "README.md"
ROADMAP = CS_ROOT / "JUNIOR-BACKEND-ROADMAP.md"
PRIMER = (
    CS_ROOT
    / "contents"
    / "software-engineering"
    / "woowacourse-backend-mission-prerequisite-primer.md"
)

TARGET_DOCS = {
    ROOT_README: [
        "./JUNIOR-BACKEND-ROADMAP.md#우테코-백엔드-안전-사다리-동기화",
        "./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md",
        "./contents/language/java/java-language-basics.md",
        "./contents/language/java/java-types-class-object-oop-basics.md",
        "./contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md",
        "./contents/network/http-methods-rest-idempotency-basics.md",
        "./contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
        "./contents/spring/spring-mvc-controller-basics.md",
        "./contents/database/jdbc-jpa-mybatis-basics.md",
        "./contents/database/transaction-isolation-basics.md",
        "./contents/spring/spring-ioc-di-basics.md",
        "./contents/spring/spring-aop-basics.md",
        "./contents/spring/spring-transactional-basics.md",
        "./contents/system-design/stateless-backend-cache-database-queue-starter-pack.md",
        "./contents/system-design/system-design-foundations.md",
    ],
    ROADMAP: [
        "./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md",
        "./contents/language/java/java-language-basics.md",
        "./contents/language/java/java-types-class-object-oop-basics.md",
        "./contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md",
        "./contents/network/http-methods-rest-idempotency-basics.md",
        "./contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
        "./contents/spring/spring-mvc-controller-basics.md",
        "./contents/database/jdbc-jpa-mybatis-basics.md",
        "./contents/database/transaction-isolation-basics.md",
        "./contents/spring/spring-ioc-di-basics.md",
        "./contents/spring/spring-aop-basics.md",
        "./contents/spring/spring-transactional-basics.md",
        "./contents/system-design/stateless-backend-cache-database-queue-starter-pack.md",
        "./contents/system-design/system-design-foundations.md",
    ],
    PRIMER: [
        "../../README.md#woowacourse-backend-beginner-ladder",
        "../../JUNIOR-BACKEND-ROADMAP.md#우테코-백엔드-안전-사다리-동기화",
        "../language/java/java-language-basics.md",
        "../language/java/java-types-class-object-oop-basics.md",
        "../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md",
        "../network/http-methods-rest-idempotency-basics.md",
        "../spring/spring-request-pipeline-bean-container-foundations-primer.md",
        "../spring/spring-mvc-controller-basics.md",
        "../database/jdbc-jpa-mybatis-basics.md",
        "../database/transaction-isolation-basics.md",
        "../spring/spring-ioc-di-basics.md",
        "../spring/spring-aop-basics.md",
        "../spring/spring-transactional-basics.md",
        "../system-design/stateless-backend-cache-database-queue-starter-pack.md",
        "../system-design/system-design-foundations.md",
    ],
}

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def slugify(heading: str) -> str:
    normalized = unicodedata.normalize("NFC", heading).strip().lower()
    normalized = re.sub(r"[^\w\s\-가-힣]", "", normalized)
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized.strip("-")


def collect_headings(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {slugify(match.group(2)) for match in HEADING_PATTERN.finditer(text)}


def main() -> int:
    failures: list[str] = []
    heading_cache: dict[Path, set[str]] = {}

    for source_path, expected_links in TARGET_DOCS.items():
        text = source_path.read_text(encoding="utf-8")
        actual_links = set(LINK_PATTERN.findall(text))

        for link in expected_links:
            if link not in actual_links:
                failures.append(f"{source_path.relative_to(CS_ROOT)} missing link: {link}")
                continue

            if "://" in link or link.startswith("mailto:"):
                continue

            target, _, anchor = link.partition("#")
            target_path = (source_path.parent / target).resolve()
            if not target_path.exists():
                failures.append(
                    f"{source_path.relative_to(CS_ROOT)} -> {link}: target file missing"
                )
                continue

            if anchor:
                headings = heading_cache.setdefault(
                    target_path, collect_headings(target_path)
                )
                if anchor not in headings:
                    failures.append(
                        f"{source_path.relative_to(CS_ROOT)} -> {link}: anchor missing"
                    )

    if failures:
        print("Beginner ladder link smoke test failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "Beginner ladder link smoke test passed "
        "(root README / roadmap / primer safe-next-step links are aligned)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
