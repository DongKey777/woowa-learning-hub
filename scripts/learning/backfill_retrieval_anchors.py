"""One-shot backfill: add ``retrieval-anchor-keywords`` blockquote meta to
CS docs that are missing any anchor metadata.

Why this exists
---------------
``corpus_loader._extract_retrieval_anchors`` recognizes three styles:

1. ``### Retrieval Anchors`` H3 section
2. ``retrieval-anchor-keywords: phrase1, phrase2, ...`` inline line
3. ``> retrieval-anchor-keywords:`` blockquote followed by ``> - phrase`` list

Most spring/database/software-engineering docs already carry one of these,
but a small tail (21 files as of 2026-04) has no anchor metadata at all —
which forces retrieval to rely on raw FTS token collisions. This script
backfills style 3 (blockquote + bulleted list) for only those tail files,
using a hand-picked anchor list per document.

The script is idempotent — if a target file already has any anchor meta,
it is skipped with a note. Run from repo root:

    python3 scripts/learning/backfill_retrieval_anchors.py            # apply
    python3 scripts/learning/backfill_retrieval_anchors.py --dry-run  # preview

Non-goals: this script is **not** a general-purpose anchor generator. The
original plan imagined a heuristic that would process hundreds of docs;
the actual coverage gap turned out to be ~21 docs, so the hand-picked
mapping below is more precise than a heuristic and is reviewable in diff.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# rel_path → ordered anchor phrases (Korean + English pairs where relevant)
ANCHORS: dict[str, list[str]] = {
    "knowledge/cs/contents/spring/spring-bean-lifecycle-scope-traps.md": [
        "Spring bean lifecycle",
        "bean scope traps",
        "singleton scope",
        "prototype scope",
        "request scope",
        "session scope",
        "scoped proxy",
        "@PostConstruct",
        "@PreDestroy",
        "bean 생명주기",
        "스코프 함정",
    ],
    "knowledge/cs/contents/spring/spring-eventlistener-transaction-phase-outbox.md": [
        "Spring EventListener",
        "TransactionalEventListener",
        "transaction phase",
        "AFTER_COMMIT",
        "BEFORE_COMMIT",
        "outbox pattern",
        "domain event dispatch",
        "event listener transaction boundary",
        "이벤트 트랜잭션 경계",
    ],
    "knowledge/cs/contents/spring/spring-observability-micrometer-tracing.md": [
        "Spring observability",
        "Micrometer",
        "Micrometer Tracing",
        "distributed tracing",
        "metrics",
        "traces",
        "logs correlation",
        "OpenTelemetry",
        "trace context propagation",
        "관측성",
    ],
    "knowledge/cs/contents/database/index-condition-pushdown-filesort-temporary-table.md": [
        "index condition pushdown",
        "ICP",
        "filesort",
        "temporary table",
        "using temporary",
        "using filesort",
        "covering index",
        "optimizer trace",
        "EXPLAIN extra",
    ],
    "knowledge/cs/contents/database/jdbc-code-patterns.md": [
        "JDBC",
        "PreparedStatement",
        "ResultSet",
        "try-with-resources",
        "connection pool",
        "transaction pattern",
        "batch insert",
        "SQLException handling",
        "JDBC 코드 패턴",
    ],
    "knowledge/cs/contents/database/jdbc-jpa-mybatis.md": [
        "JDBC",
        "JPA",
        "Hibernate",
        "MyBatis",
        "persistence framework comparison",
        "ORM vs SQL mapper",
        "first level cache",
        "SQLite vs H2 vs MySQL",
    ],
    "knowledge/cs/contents/database/mvcc-replication-sharding.md": [
        "MVCC",
        "multi-version concurrency control",
        "replication",
        "read replica",
        "replication lag",
        "sharding",
        "shard key",
        "horizontal partitioning",
    ],
    "knowledge/cs/contents/database/mysql-optimizer-hints-index-merge.md": [
        "MySQL optimizer hints",
        "USE INDEX",
        "FORCE INDEX",
        "IGNORE INDEX",
        "index merge",
        "index_merge_intersect",
        "index_merge_union",
        "optimizer switch",
    ],
    "knowledge/cs/contents/database/pagination-offset-vs-seek.md": [
        "pagination",
        "offset pagination",
        "seek pagination",
        "keyset pagination",
        "cursor pagination",
        "LIMIT OFFSET",
        "deep pagination",
        "스크롤 페이지네이션",
    ],
    "knowledge/cs/contents/database/partition-pruning-hot-cold-data.md": [
        "partition pruning",
        "range partitioning",
        "hot cold data",
        "cold archive",
        "partition elimination",
        "time-series partition",
        "핫콜드 데이터",
    ],
    "knowledge/cs/contents/database/sql-joins-and-query-order.md": [
        "SQL join",
        "INNER JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "query execution order",
        "logical query processing",
        "GROUP BY HAVING",
        "subquery vs join",
        "조인 실행 순서",
    ],
    "knowledge/cs/contents/software-engineering/api-contract-testing-consumer-driven.md": [
        "API contract testing",
        "consumer-driven contracts",
        "CDC test",
        "Pact",
        "Spring Cloud Contract",
        "provider verification",
        "consumer expectations",
        "contract broker",
        "컨슈머 주도 계약",
    ],
    "knowledge/cs/contents/software-engineering/api-design-error-handling.md": [
        "API design",
        "API error handling",
        "error response envelope",
        "problem details",
        "RFC 7807",
        "HTTP status code semantics",
        "error code taxonomy",
        "exception to API translation",
        "예외 처리 설계",
    ],
    "knowledge/cs/contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md": [
        "API versioning",
        "URI versioning",
        "media type versioning",
        "backward compatibility",
        "contract testing",
        "anti-corruption layer",
        "ACL",
        "monolith to microservice",
        "버전 관리",
    ],
    "knowledge/cs/contents/software-engineering/cache-message-observability.md": [
        "cache observability",
        "messaging observability",
        "cache hit ratio",
        "cache miss",
        "consumer lag",
        "Kafka lag",
        "dead letter queue",
        "Prometheus alert",
        "캐시 메트릭",
        "관측성",
    ],
    "knowledge/cs/contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md": [
        "deployment rollout",
        "rollback",
        "canary deployment",
        "blue-green deployment",
        "rolling deployment",
        "release vs deploy",
        "progressive delivery",
        "배포 전략",
    ],
    "knowledge/cs/contents/software-engineering/feature-flag-cleanup-expiration.md": [
        "feature flag cleanup",
        "feature flag expiration",
        "flag debt",
        "flag sunset",
        "stale toggle",
        "flag lifecycle",
        "토글 정리",
    ],
    "knowledge/cs/contents/software-engineering/feature-flags-rollout-dependency-management.md": [
        "feature flags",
        "rollout strategy",
        "gradual rollout",
        "percentage rollout",
        "flag dependency",
        "dependent flag graph",
        "kill switch",
        "롤아웃 전략",
    ],
    "knowledge/cs/contents/software-engineering/outbox-inbox-domain-events.md": [
        "domain event",
        "integration event",
        "outbox pattern",
        "inbox pattern",
        "idempotent consumer",
        "eventual consistency",
        "event dispatch",
        "consistency boundary",
    ],
    "knowledge/cs/contents/software-engineering/solid-failure-patterns.md": [
        "SOLID",
        "single responsibility violation",
        "open-closed violation",
        "liskov violation",
        "interface segregation",
        "dependency inversion",
        "SOLID 위반 패턴",
        "responsibility leak",
    ],
    "knowledge/cs/contents/software-engineering/technical-debt-refactoring-timing.md": [
        "technical debt",
        "refactoring timing",
        "refactor window",
        "architectural debt",
        "boy scout rule",
        "debt interest",
        "리팩터링 타이밍",
        "기술 부채",
    ],
}


ANCHOR_SENTINELS = (
    "retrieval-anchor-keywords",
    "Retrieval Anchors",
    "Retrieval anchors",
)


def _already_has_anchors(text: str) -> bool:
    return any(sentinel in text for sentinel in ANCHOR_SENTINELS)


def _render_block(phrases: list[str]) -> str:
    lines = ["> retrieval-anchor-keywords:"]
    for phrase in phrases:
        lines.append(f"> - {phrase}")
    return "\n".join(lines) + "\n"


def _insert_block(text: str, block: str) -> str:
    """Insert ``block`` immediately before the first ``## `` heading,
    preserving a blank line above and below.
    """
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("## "):
            # ensure exactly one blank line before the inserted block
            head = "".join(lines[:i])
            tail = "".join(lines[i:])
            if not head.endswith("\n\n"):
                head = head.rstrip("\n") + "\n\n"
            return f"{head}{block}\n{tail}"
    # no H2 in document — append at end
    suffix = text if text.endswith("\n") else text + "\n"
    return suffix + "\n" + block


def backfill(dry_run: bool = False) -> int:
    missing: list[str] = []
    skipped: list[str] = []
    updated: list[str] = []

    for rel_path, phrases in ANCHORS.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            missing.append(rel_path)
            continue
        text = path.read_text(encoding="utf-8")
        if _already_has_anchors(text):
            skipped.append(rel_path)
            continue
        block = _render_block(phrases)
        new_text = _insert_block(text, block)
        if dry_run:
            print(f"[dry-run] would update {rel_path}")
            print(f"--- {len(phrases)} anchors ---")
            print(block)
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"updated {rel_path} (+{len(phrases)} anchors)")
        updated.append(rel_path)

    print()
    print(f"summary: updated={len(updated)} skipped={len(skipped)} missing={len(missing)}")
    if skipped:
        print("skipped (already had anchors):")
        for p in skipped:
            print(f"  - {p}")
    if missing:
        print("missing (not found on disk):")
        for p in missing:
            print(f"  - {p}")
    return 0 if not missing else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return backfill(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
