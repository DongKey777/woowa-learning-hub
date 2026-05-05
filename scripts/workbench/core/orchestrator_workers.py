from __future__ import annotations

import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .file_lock import lock_exclusive, unlock
from .orchestrator import Orchestrator, _isoformat, _pid_alive, _utc_now
from .orchestrator_migration_workers import (
    MIGRATION_V3_60_FLEET,
    MIGRATION_V3_60_FLEET_SIZE,
    MIGRATION_V3_60_WORKER_PENDING_CAP,
    MIGRATION_V3_FLEET,
    MIGRATION_V3_FLEET_SIZE,
    MIGRATION_V3_WORKER_PENDING_CAP,
)
from .paths import ROOT, ensure_orchestrator_layout

DEFAULT_WORKER_IDLE_SECONDS = 15
DEFAULT_WORKER_LEASE_SECONDS = 45 * 60
DEFAULT_TASK_TIMEOUT_SECONDS = 45 * 60
DEFAULT_SUPERVISOR_INTERVAL_SECONDS = 20

DEFAULT_WORKER_PENDING_CAP = 80
EXPANSION_WORKER_PENDING_CAP = 35
EXPANSION60_WORKER_PENDING_CAP = 28
DEFAULT_COMPLETION_GATE_TIMEOUT_SECONDS = 180
DEFAULT_FLEET_PROFILE = "quality"

CONTENT_DOC_PREFIX = "knowledge/cs/contents/"
RAG_CODE_PREFIX = "scripts/learning/rag/"
CS_RAG_TEST_PREFIX = "tests/unit/test_cs_rag_"
CS_RAG_FIXTURE = "tests/fixtures/cs_rag_golden_queries.json"
DIFFICULTY_RE = re.compile(r"\*\*난이도:\s*([^*]+)\*\*")

DIFFICULTY_BALANCE_TARGETS = {
    "Beginner": (0.35, 0.45),
    "Intermediate": (0.15, 0.25),
}
CATEGORY_BEGINNER_FLOOR = 0.35
CATEGORY_BEGINNER_CEILING = 0.50
CATEGORY_INTERMEDIATE_FLOOR = 0.10
ANTI_DRIFT_NEXT_CANDIDATE_TAGS = {
    "accuracy",
    "advanced",
    "balance-gap",
    "bridge",
    "cross-category",
    "deep-dive",
    "intermediate",
    "misconception",
    "practice",
    "qa",
    "recovery",
    "retrieval",
    # Phase 8 long-running balance guard — at least one of these
    # tags must appear on every migration_v3 next_candidate so the
    # platform anti-drift filter accepts it.
    "v3-frontmatter",
    "v3-prefix",
    "v3-new-doc",
    "v3-revisit",
    "cohort-weak",
    "mission-bridge",
    "chooser",
    "symptom-router",
}
GENERIC_DRIFT_TAGS = {
    "beginner",
    "basics",
    "foundation",
    "foundations",
    "junior",
    "primer",
    "woowacourse-backend",
}

WORKER_PROFILES: list[dict[str, Any]] = [
    {
        "name": "runtime-curriculum-map",
        "lane": "qa-taxonomy",
        "role": "curriculum",
        "mode": "report",
        "claim_tags": ["woowacourse", "curriculum", "level", "mission", "foundation"],
        "write_scopes": [],
        "target_paths": ["knowledge/cs/**", "state/orchestrator/reports/**"],
        "quality_gates": ["mission_coverage", "no_content_edits"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-mission-prerequisite",
        "lane": "qa-content",
        "role": "curriculum",
        "mode": "report",
        "claim_tags": ["woowacourse", "mission", "prerequisite", "curriculum", "foundation"],
        "write_scopes": [],
        "target_paths": ["knowledge/cs/**", "state/orchestrator/reports/**"],
        "quality_gates": ["mission_prerequisite_matrix", "no_content_edits"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-backlog-governor",
        "lane": "qa-taxonomy",
        "role": "curriculum",
        "mode": "queue",
        "claim_tags": ["queue", "pending", "candidate", "governor", "duplicate"],
        "write_scopes": ["queue:governor"],
        "target_paths": ["state/orchestrator/**"],
        "quality_gates": ["pending_cap", "duplicate_candidate_control"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-java-basics",
        "lane": "language-java",
        "role": "content",
        "mode": "write",
        "claim_tags": ["java", "jvm", "syntax", "basics", "execution", "object-model"],
        "write_scopes": ["content:language-java:basics"],
        "target_paths": ["knowledge/cs/contents/language/java/**"],
        "quality_gates": ["beginner_first", "example_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-java-oop",
        "lane": "language-java",
        "role": "content",
        "mode": "write",
        "claim_tags": ["oop", "equality", "equals", "hashcode", "value", "object"],
        "write_scopes": ["content:language-java:oop"],
        "target_paths": ["knowledge/cs/contents/language/java/**"],
        "quality_gates": ["beginner_first", "example_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-java-collections",
        "lane": "language-java",
        "role": "content",
        "mode": "write",
        "claim_tags": ["collections", "generics", "bigdecimal", "comparable", "comparator", "map", "set", "list"],
        "write_scopes": ["content:language-java:collections"],
        "target_paths": ["knowledge/cs/contents/language/java/**"],
        "quality_gates": ["beginner_first", "example_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-testing-refactoring",
        "lane": "software-engineering",
        "role": "content",
        "mode": "write",
        "claim_tags": ["testing", "test", "tdd", "refactoring", "readable-code"],
        "write_scopes": ["content:software-engineering:testing"],
        "target_paths": ["knowledge/cs/contents/software-engineering/**"],
        "quality_gates": ["beginner_first", "practice_loop"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-data-structure-foundations",
        "lane": "data-structure",
        "role": "content",
        "mode": "write",
        "claim_tags": ["data-structure", "list", "map", "set", "queue", "heap", "priority-queue"],
        "write_scopes": ["content:data-structure:foundations"],
        "target_paths": ["knowledge/cs/contents/data-structure/**"],
        "quality_gates": ["beginner_first", "selection_table"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-algorithm-foundations",
        "lane": "data-structure",
        "role": "content",
        "mode": "write",
        "claim_tags": ["algorithm", "complexity", "bfs", "dfs", "binary-search", "sorting"],
        "write_scopes": ["content:algorithm:foundations"],
        "target_paths": ["knowledge/cs/contents/algorithm/**"],
        "quality_gates": ["beginner_first", "pattern_router"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-network-http",
        "lane": "network",
        "role": "content",
        "mode": "write",
        "claim_tags": ["network", "http", "dns", "tcp", "tls", "browser", "cookie"],
        "write_scopes": ["content:network:http"],
        "target_paths": ["knowledge/cs/contents/network/**"],
        "quality_gates": ["beginner_first", "protocol_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-os-runtime",
        "lane": "operating-system",
        "role": "content",
        "mode": "write",
        "claim_tags": ["os", "process", "thread", "memory", "file-descriptor", "io", "backpressure"],
        "write_scopes": ["content:operating-system:runtime"],
        "target_paths": ["knowledge/cs/contents/operating-system/**"],
        "quality_gates": ["beginner_first", "runtime_model"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-db-sql-modeling",
        "lane": "database",
        "role": "content",
        "mode": "write",
        "claim_tags": ["sql", "join", "modeling", "index", "primary-key", "foreign-key"],
        "write_scopes": ["content:database:sql-modeling"],
        "target_paths": ["knowledge/cs/contents/database/**"],
        "quality_gates": ["beginner_first", "example_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-db-transaction",
        "lane": "database",
        "role": "content",
        "mode": "write",
        "claim_tags": ["transaction", "locking", "deadlock", "isolation", "retry", "concurrency"],
        "write_scopes": ["content:database:transaction"],
        "target_paths": ["knowledge/cs/contents/database/**"],
        "quality_gates": ["beginner_first", "concurrency_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-spring-core-mvc",
        "lane": "spring",
        "role": "content",
        "mode": "write",
        "claim_tags": ["spring", "bean", "di", "mvc", "dispatcher", "component-scan"],
        "write_scopes": ["content:spring:core-mvc"],
        "target_paths": ["knowledge/cs/contents/spring/**"],
        "quality_gates": ["beginner_first", "spring_contract_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-spring-jpa-transaction",
        "lane": "spring",
        "role": "content",
        "mode": "write",
        "claim_tags": ["jpa", "transactional", "persistence-context", "flush", "lazy"],
        "write_scopes": ["content:spring:jpa-transaction"],
        "target_paths": ["knowledge/cs/contents/spring/**", "knowledge/cs/contents/database/**"],
        "quality_gates": ["beginner_first", "transaction_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-security-auth",
        "lane": "security",
        "role": "content",
        "mode": "write",
        "claim_tags": ["security", "authentication", "authorization", "session", "jwt", "cors", "csrf", "xss"],
        "write_scopes": ["content:security:auth"],
        "target_paths": ["knowledge/cs/contents/security/**"],
        "quality_gates": ["beginner_first", "security_accuracy"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-architecture-ops",
        "lane": "system-design",
        "role": "content",
        "mode": "write",
        "claim_tags": ["architecture", "system-design", "cache", "queue", "observability", "deployment", "rollback", "feature-flag"],
        "write_scopes": ["content:system-design:architecture-ops"],
        "target_paths": ["knowledge/cs/contents/system-design/**", "knowledge/cs/contents/software-engineering/**"],
        "quality_gates": ["beginner_first", "ops_practicality"],
        "can_enqueue": True,
    },
    {
        "name": "runtime-qa-technical-accuracy",
        "lane": "qa-content",
        "role": "qa",
        "mode": "fix",
        "claim_tags": ["accuracy", "example", "confusion", "beginner", "qa"],
        "write_scopes": ["qa:technical-accuracy"],
        "target_paths": ["knowledge/cs/**"],
        "quality_gates": ["example_accuracy", "no_large_rewrite"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-qa-beginner-pedagogy",
        "lane": "qa-content",
        "role": "qa",
        "mode": "fix",
        "claim_tags": ["beginner", "primer", "mental", "clarity", "entrypoint"],
        "write_scopes": ["qa:beginner-pedagogy"],
        "target_paths": ["knowledge/cs/**"],
        "quality_gates": ["beginner_first", "no_large_rewrite"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-qa-link-anchor",
        "lane": "qa-link",
        "role": "qa",
        "mode": "script",
        "claim_tags": ["link", "anchor", "reverse-link", "broken"],
        "write_scopes": ["qa:link-anchor"],
        "target_paths": ["knowledge/cs/**", "docs/**"],
        "quality_gates": ["link_integrity"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-qa-retrieval-precision",
        "lane": "qa-retrieval",
        "role": "qa",
        "mode": "fix",
        "claim_tags": ["retrieval", "golden", "first-hit", "precision", "anchor"],
        "write_scopes": ["qa:retrieval-precision"],
        "target_paths": ["knowledge/cs/**", "tests/fixtures/**", "scripts/learning/rag/**"],
        "quality_gates": ["retrieval_safety"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-qa-dup-taxonomy",
        "lane": "qa-taxonomy",
        "role": "qa",
        "mode": "fix",
        "claim_tags": ["taxonomy", "duplicate", "overlap", "navigation", "readme"],
        "write_scopes": ["qa:taxonomy"],
        "target_paths": ["knowledge/cs/**"],
        "quality_gates": ["taxonomy_consistency", "no_large_rewrite"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-qa-example-lint",
        "lane": "qa-content",
        "role": "qa",
        "mode": "script",
        "claim_tags": ["code", "example", "lint", "java", "spring", "sql"],
        "write_scopes": ["qa:example-lint"],
        "target_paths": ["knowledge/cs/**", "scripts/lint_cs_authoring.py"],
        "quality_gates": ["authoring_lint", "example_accuracy"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-rag-golden",
        "lane": "qa-retrieval",
        "role": "rag",
        "mode": "write",
        "claim_tags": ["golden", "query", "fixture", "regression"],
        "write_scopes": ["rag:golden"],
        "target_paths": ["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_*.py"],
        "quality_gates": ["golden_regression"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-rag-signal-rules",
        "lane": "qa-retrieval",
        "role": "rag",
        "mode": "write",
        "claim_tags": ["signal", "rule", "boost", "suppress", "rerank"],
        "write_scopes": ["rag:signal_rules"],
        "target_paths": ["scripts/learning/rag/signal_rules.py", "tests/unit/test_cs_rag_signal_rules.py"],
        "quality_gates": ["retrieval_safety", "unit_regression"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-rag-relevance-report",
        "lane": "qa-retrieval",
        "role": "rag",
        "mode": "report",
        "claim_tags": ["relevance", "top-k", "evaluation", "search"],
        "write_scopes": [],
        "target_paths": ["state/orchestrator/reports/**"],
        "quality_gates": ["top_k_relevance"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-rag-index-health",
        "lane": "qa-retrieval",
        "role": "rag",
        "mode": "script",
        "claim_tags": ["index", "cs-index-build", "health", "stats"],
        "write_scopes": ["rag:index"],
        "target_paths": ["state/cs_rag/**", "knowledge/cs/**"],
        "quality_gates": ["index_health"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-mission-coverage-score",
        "lane": "qa-taxonomy",
        "role": "rag",
        "mode": "report",
        "claim_tags": ["coverage", "mission", "level", "woowacourse", "prerequisite"],
        "write_scopes": [],
        "target_paths": ["state/orchestrator/reports/**"],
        "quality_gates": ["mission_coverage"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-queue-governor",
        "lane": "qa-taxonomy",
        "role": "ops",
        "mode": "ops",
        "claim_tags": ["queue", "pending", "candidate", "governor", "duplicate"],
        "write_scopes": ["ops:queue-governor"],
        "target_paths": ["state/orchestrator/**"],
        "quality_gates": ["pending_cap", "duplicate_candidate_control"],
        "can_enqueue": False,
    },
    {
        "name": "runtime-release-gate",
        "lane": "qa-link",
        "role": "ops",
        "mode": "ops",
        "claim_tags": ["release", "gate", "commit", "lint", "index", "test"],
        "write_scopes": ["ops:release-gate"],
        "target_paths": ["knowledge/cs/**", "tests/**", "state/cs_rag/**"],
        "quality_gates": ["link_integrity", "golden_regression", "index_health"],
        "can_enqueue": False,
    },
]

def _quality_profile(
    name: str,
    lane: str,
    *,
    role: str,
    mode: str,
    write_scope: str,
    target_paths: list[str],
    quality_gates: list[str],
    claim_tags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "lane": lane,
        "role": role,
        "mode": mode,
        "claim_tags": claim_tags or [],
        "write_scopes": [write_scope],
        "target_paths": target_paths,
        "quality_gates": quality_gates,
        "can_enqueue": False,
    }


QUALITY_REPAIR_FLEET: list[dict[str, Any]] = [
    _quality_profile(
        "runtime-qa-content-database",
        "qa-content-database",
        role="qa",
        mode="fix",
        write_scope="qa:content:database",
        target_paths=["knowledge/cs/contents/database/**", "knowledge/cs/contents/database/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-security",
        "qa-content-security",
        role="qa",
        mode="fix",
        write_scope="qa:content:security",
        target_paths=["knowledge/cs/contents/security/**", "knowledge/cs/contents/security/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-network",
        "qa-content-network",
        role="qa",
        mode="fix",
        write_scope="qa:content:network",
        target_paths=["knowledge/cs/contents/network/**", "knowledge/cs/contents/network/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-system-design",
        "qa-content-system-design",
        role="qa",
        mode="fix",
        write_scope="qa:content:system-design",
        target_paths=["knowledge/cs/contents/system-design/**", "knowledge/cs/contents/system-design/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-operating-system",
        "qa-content-operating-system",
        role="qa",
        mode="fix",
        write_scope="qa:content:operating-system",
        target_paths=["knowledge/cs/contents/operating-system/**", "knowledge/cs/contents/operating-system/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-spring",
        "qa-content-spring",
        role="qa",
        mode="fix",
        write_scope="qa:content:spring",
        target_paths=["knowledge/cs/contents/spring/**", "knowledge/cs/contents/spring/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-design-pattern",
        "qa-content-design-pattern",
        role="qa",
        mode="fix",
        write_scope="qa:content:design-pattern",
        target_paths=["knowledge/cs/contents/design-pattern/**", "knowledge/cs/contents/design-pattern/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-software-engineering",
        "qa-content-software-engineering",
        role="qa",
        mode="fix",
        write_scope="qa:content:software-engineering",
        target_paths=["knowledge/cs/contents/software-engineering/**", "knowledge/cs/contents/software-engineering/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-language-java",
        "qa-content-language-java",
        role="qa",
        mode="fix",
        write_scope="qa:content:language-java",
        target_paths=["knowledge/cs/contents/language/java/**", "knowledge/cs/contents/language/README.md"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-content-data-structure",
        "qa-content-data-structure",
        role="qa",
        mode="fix",
        write_scope="qa:content:data-structure",
        target_paths=["knowledge/cs/contents/data-structure/**", "knowledge/cs/contents/algorithm/**"],
        quality_gates=["authoring_lint", "related_docs", "retrieval_anchor_limit", "beginner_first"],
    ),
    _quality_profile(
        "runtime-qa-primer-contract-database",
        "qa-content-database",
        role="qa",
        mode="fix",
        write_scope="qa:content:database",
        target_paths=["knowledge/cs/contents/database/**"],
        quality_gates=["primer_contract", "h2_size_limit", "final_summary", "related_docs"],
        claim_tags=["primer", "lint", "related", "anchor", "beginner"],
    ),
    _quality_profile(
        "runtime-qa-primer-contract-spring",
        "qa-content-spring",
        role="qa",
        mode="fix",
        write_scope="qa:content:spring",
        target_paths=["knowledge/cs/contents/spring/**"],
        quality_gates=["primer_contract", "h2_size_limit", "final_summary", "related_docs"],
        claim_tags=["primer", "lint", "related", "anchor", "beginner"],
    ),
    _quality_profile(
        "runtime-qa-primer-contract-language-java",
        "qa-content-language-java",
        role="qa",
        mode="fix",
        write_scope="qa:content:language-java",
        target_paths=["knowledge/cs/contents/language/java/**"],
        quality_gates=["primer_contract", "h2_size_limit", "final_summary", "related_docs"],
        claim_tags=["primer", "lint", "related", "anchor", "beginner"],
    ),
    _quality_profile(
        "runtime-qa-primer-contract-system-design",
        "qa-content-system-design",
        role="qa",
        mode="fix",
        write_scope="qa:content:system-design",
        target_paths=["knowledge/cs/contents/system-design/**"],
        quality_gates=["primer_contract", "h2_size_limit", "final_summary", "related_docs"],
        claim_tags=["primer", "lint", "related", "anchor", "beginner"],
    ),
    _quality_profile(
        "runtime-qa-anchor-database-security",
        "qa-anchor",
        role="qa",
        mode="script",
        write_scope="qa:anchor:database-security",
        target_paths=["knowledge/cs/contents/database/**", "knowledge/cs/contents/security/**", "knowledge/cs/rag/retrieval-anchor-keywords.md"],
        quality_gates=["anchor_8_to_15", "lowercase_anchor", "symptom_phrase_anchors"],
    ),
    _quality_profile(
        "runtime-qa-anchor-java-spring",
        "qa-anchor",
        role="qa",
        mode="script",
        write_scope="qa:anchor:java-spring",
        target_paths=["knowledge/cs/contents/language/java/**", "knowledge/cs/contents/spring/**", "knowledge/cs/rag/retrieval-anchor-keywords.md"],
        quality_gates=["anchor_8_to_15", "lowercase_anchor", "symptom_phrase_anchors"],
    ),
    _quality_profile(
        "runtime-qa-anchor-network-os",
        "qa-anchor",
        role="qa",
        mode="script",
        write_scope="qa:anchor:network-os",
        target_paths=["knowledge/cs/contents/network/**", "knowledge/cs/contents/operating-system/**", "knowledge/cs/rag/retrieval-anchor-keywords.md"],
        quality_gates=["anchor_8_to_15", "lowercase_anchor", "symptom_phrase_anchors"],
    ),
    _quality_profile(
        "runtime-qa-anchor-system-design",
        "qa-anchor",
        role="qa",
        mode="script",
        write_scope="qa:anchor:system-design",
        target_paths=["knowledge/cs/contents/system-design/**", "knowledge/cs/contents/software-engineering/**", "knowledge/cs/rag/retrieval-anchor-keywords.md"],
        quality_gates=["anchor_8_to_15", "lowercase_anchor", "symptom_phrase_anchors"],
    ),
    _quality_profile(
        "runtime-qa-link-return-paths",
        "qa-link",
        role="qa",
        mode="script",
        write_scope="qa:link:return-paths",
        target_paths=["knowledge/cs/contents/**/README.md", "knowledge/cs/contents/**/*.md"],
        quality_gates=["readme_return_path", "link_integrity"],
    ),
    _quality_profile(
        "runtime-qa-link-follow-up-ladders",
        "qa-link",
        role="qa",
        mode="script",
        write_scope="qa:link:follow-up-ladders",
        target_paths=["knowledge/cs/contents/**/*.md"],
        quality_gates=["safe_next_step", "primer_to_deep_dive_ladder"],
    ),
    _quality_profile(
        "runtime-qa-link-cross-category",
        "qa-link",
        role="qa",
        mode="script",
        write_scope="qa:link:cross-category",
        target_paths=["knowledge/cs/contents/**/*.md", "knowledge/cs/README.md"],
        quality_gates=["cross_category_bridge", "no_broken_links"],
    ),
    _quality_profile(
        "runtime-qa-link-release-sweep",
        "qa-link",
        role="ops",
        mode="ops",
        write_scope="qa:link:release-sweep",
        target_paths=["knowledge/cs/**", "docs/**"],
        quality_gates=["primer_link_contract", "beginner_ladder_smoke"],
    ),
    _quality_profile(
        "runtime-rag-ranking-projection",
        "qa-retrieval",
        role="rag",
        mode="fix",
        write_scope="rag:ranking:projection",
        target_paths=["scripts/learning/rag/signal_rules.py", "tests/unit/test_cs_rag_search.py", "tests/unit/test_cs_rag_signal_rules.py", "tests/fixtures/cs_rag_golden_queries.json"],
        quality_gates=["projection_freshness_topk", "no_database_noise", "unit_regression"],
        claim_tags=["projection", "freshness", "read model", "cutover", "stale"],
    ),
    _quality_profile(
        "runtime-rag-ranking-jwt",
        "qa-retrieval",
        role="rag",
        mode="fix",
        write_scope="rag:ranking:jwt",
        target_paths=["scripts/learning/rag/signal_rules.py", "tests/unit/test_cs_rag_search.py", "tests/unit/test_cs_rag_signal_rules.py", "knowledge/cs/contents/security/**"],
        quality_gates=["jwt_primer_top1", "auth_session_balance", "unit_regression"],
        claim_tags=["jwt", "authentication", "session", "authorization"],
    ),
    _quality_profile(
        "runtime-rag-ranking-transaction",
        "qa-retrieval",
        role="rag",
        mode="fix",
        write_scope="rag:ranking:transaction",
        target_paths=["scripts/learning/rag/signal_rules.py", "tests/unit/test_cs_rag_search.py", "tests/unit/test_cs_rag_signal_rules.py", "knowledge/cs/contents/database/**"],
        quality_gates=["transaction_isolation_signal", "rollback_not_projection", "unit_regression"],
        claim_tags=["transaction", "rollback", "isolation", "dirty", "phantom"],
    ),
    _quality_profile(
        "runtime-rag-signal-rules",
        "qa-retrieval",
        role="rag",
        mode="fix",
        write_scope="rag:signal_rules",
        target_paths=["scripts/learning/rag/signal_rules.py", "tests/unit/test_cs_rag_signal_rules.py"],
        quality_gates=["signal_rule_regression", "top_signal_tag"],
        claim_tags=["signal", "rule", "boost", "suppress", "rerank"],
    ),
    _quality_profile(
        "runtime-rag-golden-fixtures",
        "qa-retrieval",
        role="rag",
        mode="fix",
        write_scope="rag:golden",
        target_paths=["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_golden.py"],
        quality_gates=["golden_fixture_contract", "no_masked_regression"],
        claim_tags=["golden", "fixture", "query", "regression"],
    ),
    _quality_profile(
        "runtime-rag-index-readiness",
        "qa-retrieval",
        role="rag",
        mode="script",
        write_scope="rag:index",
        target_paths=["state/cs_rag/**", "scripts/learning/rag/**"],
        quality_gates=["index_readiness", "stale_index_detection"],
        claim_tags=["index", "stale", "cs-index-build", "readiness"],
    ),
    _quality_profile(
        "runtime-queue-governor",
        "qa-taxonomy",
        role="ops",
        mode="queue",
        write_scope="ops:queue-governor",
        target_paths=["state/orchestrator/**"],
        quality_gates=["pending_cap", "duplicate_candidate_control", "qa_first"],
        claim_tags=["queue", "pending", "candidate", "governor", "duplicate"],
    ),
    _quality_profile(
        "runtime-release-gate",
        "qa-link",
        role="ops",
        mode="ops",
        write_scope="ops:release-gate",
        target_paths=["knowledge/cs/**", "tests/**", "state/cs_rag/**"],
        quality_gates=["authoring_lint", "rag_regression", "index_health", "release_readiness"],
        claim_tags=["release", "gate", "commit", "lint", "index", "test"],
    ),
]

def _default_expansion_gates(role: str) -> list[str]:
    if role == "content":
        return [
            "authoring_lint",
            "difficulty_balance",
            "category_balance",
            "misconception_guard",
            "context_qualified_claims",
            "readme_registration",
            "duplicate_topic_check",
            "targeted_rag_query",
        ]
    if role == "qa":
        return ["difficulty_balance", "misconception_guard", "beginner_first", "symptom_phrase_anchors", "cross_category_bridge"]
    if role == "rag":
        return ["beginner_query_precision", "golden_fixture_contract", "unit_regression"]
    if role == "ops":
        return ["pending_cap", "index_health", "release_readiness"]
    return ["learner_profile_gap_map", "balanced_backlog", "level2_roomescape_alignment", "no_content_edits"]


def _expansion_profile(
    name: str,
    lane: str,
    role: str,
    mode: str,
    claim_tags: list[str],
    target_paths: list[str],
    *,
    write_scopes: list[str] | None = None,
    can_enqueue: bool = False,
    quality_gates: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "lane": lane,
        "role": role,
        "mode": mode,
        "claim_tags": claim_tags,
        "write_scopes": write_scopes or [f"expansion:{role}:{name.removeprefix('expansion-')}"],
        "target_paths": target_paths,
        "quality_gates": quality_gates or _default_expansion_gates(role),
        "can_enqueue": can_enqueue,
        "pending_cap": EXPANSION_WORKER_PENDING_CAP,
    }


def _expansion60_profile(
    name: str,
    lane: str,
    role: str,
    mode: str,
    claim_tags: list[str],
    target_paths: list[str],
    *,
    write_scopes: list[str] | None = None,
    can_enqueue: bool = False,
    quality_gates: list[str] | None = None,
) -> dict[str, Any]:
    profile = _expansion_profile(
        name,
        lane,
        role,
        mode,
        claim_tags,
        target_paths,
        write_scopes=write_scopes,
        can_enqueue=can_enqueue,
        quality_gates=quality_gates,
    )
    profile["pending_cap"] = EXPANSION60_WORKER_PENDING_CAP
    profile["fleet_size"] = 60
    return profile


EXPANSION_FLEET: list[dict[str, Any]] = [
    _expansion_profile("expansion-curriculum-learner-map", "qa-taxonomy", "curriculum", "report", ["woowacourse", "level2", "roomescape", "spring", "foundation"], ["knowledge/cs/JUNIOR-BACKEND-ROADMAP.md", "state/learner/**", "state/orchestrator/reports/**"]),
    _expansion_profile("expansion-spring-core-di", "spring", "content", "expand", ["spring", "bean", "di", "ioc", "component-scan", "beginner"], ["knowledge/cs/contents/spring/**", "knowledge/cs/contents/spring/README.md"], write_scopes=["expansion:content:spring"], can_enqueue=True),
    _expansion_profile("expansion-spring-mvc-roomescape", "spring", "content", "expand", ["spring-mvc", "controller", "restcontroller", "dispatcher", "roomescape", "admin"], ["knowledge/cs/contents/spring/**", "knowledge/cs/contents/network/**", "knowledge/cs/contents/spring/README.md"], write_scopes=["expansion:content:spring", "expansion:content:network"], can_enqueue=True),
    _expansion_profile("expansion-roomescape-admin-web", "software-engineering", "content", "expand", ["roomescape", "admin", "dto", "validation", "exception", "layering"], ["knowledge/cs/contents/software-engineering/**", "knowledge/cs/contents/spring/**", "knowledge/cs/contents/network/**"], write_scopes=["expansion:content:software-engineering", "expansion:content:spring", "expansion:content:network"], can_enqueue=True),
    _expansion_profile("expansion-roomescape-admin-persistence", "database", "content", "expand", ["jdbc", "jpa", "repository", "transaction", "roomescape"], ["knowledge/cs/contents/database/**", "knowledge/cs/contents/spring/**", "knowledge/cs/contents/database/README.md"], write_scopes=["expansion:content:database", "expansion:content:spring"], can_enqueue=True),
    _expansion_profile("expansion-java-oop-collections", "language-java", "content", "expand", ["java", "oop", "collections", "equals", "hashcode", "enum", "optional"], ["knowledge/cs/contents/language/java/**", "knowledge/cs/contents/language/README.md"], write_scopes=["expansion:content:language-java"], can_enqueue=True),
    _expansion_profile("expansion-http-web-foundations", "network", "content", "expand", ["http", "rest", "status-code", "cookie", "session", "web"], ["knowledge/cs/contents/network/**", "knowledge/cs/contents/network/README.md"], write_scopes=["expansion:content:network"], can_enqueue=True),
    _expansion_profile("expansion-testing-layering", "software-engineering", "content", "expand", ["testing", "layering", "readable-code", "refactoring", "tdd"], ["knowledge/cs/contents/software-engineering/**", "knowledge/cs/contents/software-engineering/README.md"], write_scopes=["expansion:content:software-engineering"], can_enqueue=True),
    _expansion_profile("expansion-algorithm-data-structure-practice", "data-structure", "content", "expand", ["algorithm", "data-structure", "bfs", "dfs", "queue", "map", "set"], ["knowledge/cs/contents/data-structure/**", "knowledge/cs/contents/algorithm/**"], write_scopes=["expansion:content:data-structure", "expansion:content:algorithm"], can_enqueue=True),
    _expansion_profile("expansion-qa-spring-entrypoints", "qa-content-spring", "qa", "fix", ["spring", "beginner", "component-scan", "di", "bean"], ["knowledge/cs/contents/spring/**", "knowledge/cs/contents/spring/README.md"], write_scopes=["expansion:content:spring"]),
    _expansion_profile("expansion-qa-roomescape-bridges", "qa-bridge", "qa", "fix", ["roomescape", "spring", "database", "testing", "bridge"], ["knowledge/cs/contents/spring/**", "knowledge/cs/contents/database/**", "knowledge/cs/contents/software-engineering/**"], write_scopes=["expansion:content:spring", "expansion:content:database", "expansion:content:software-engineering"]),
    _expansion_profile("expansion-qa-database-persistence", "qa-content-database", "qa", "fix", ["jdbc", "jpa", "transaction", "sql", "repository"], ["knowledge/cs/contents/database/**", "knowledge/cs/contents/database/README.md"], write_scopes=["expansion:content:database"]),
    _expansion_profile("expansion-qa-java-primer-contract", "qa-content-language-java", "qa", "fix", ["java", "oop", "collections", "primer"], ["knowledge/cs/contents/language/java/**", "knowledge/cs/contents/language/README.md"], write_scopes=["expansion:content:language-java"]),
    _expansion_profile("expansion-qa-http-web", "qa-content-network", "qa", "fix", ["http", "rest", "cookie", "session", "status-code"], ["knowledge/cs/contents/network/**", "knowledge/cs/contents/network/README.md"], write_scopes=["expansion:content:network"]),
    _expansion_profile("expansion-qa-testing-layering", "qa-content-software-engineering", "qa", "fix", ["testing", "layering", "refactoring", "readable-code"], ["knowledge/cs/contents/software-engineering/**", "knowledge/cs/contents/software-engineering/README.md"], write_scopes=["expansion:content:software-engineering"]),
    _expansion_profile("expansion-qa-anchor-symptoms", "qa-anchor", "qa", "script", ["anchor", "symptom", "beginner", "뭐예요", "왜", "헷갈"], ["knowledge/cs/contents/**/*.md", "knowledge/cs/rag/retrieval-anchor-keywords.md"], write_scopes=["expansion:content:spring", "expansion:content:database", "expansion:content:software-engineering", "expansion:content:language-java", "expansion:content:network", "expansion:content:data-structure", "expansion:content:algorithm"]),
    _expansion_profile("expansion-qa-cross-category", "qa-link", "qa", "script", ["bridge", "cross-category", "readme", "next-step"], ["knowledge/cs/contents/**/*.md", "knowledge/cs/contents/**/README.md"], write_scopes=["expansion:content:spring", "expansion:content:database", "expansion:content:software-engineering", "expansion:content:language-java", "expansion:content:network", "expansion:content:data-structure", "expansion:content:algorithm"]),
    _expansion_profile("expansion-qa-duplicate-taxonomy", "qa-taxonomy", "qa", "fix", ["duplicate", "taxonomy", "overlap", "navigation"], ["knowledge/cs/**"], write_scopes=["expansion:content:spring", "expansion:content:database", "expansion:content:software-engineering", "expansion:content:language-java", "expansion:content:network", "expansion:content:data-structure", "expansion:content:algorithm"]),
    _expansion_profile("expansion-qa-code-density", "qa-content", "qa", "fix", ["code", "example", "beginner", "clarity"], ["knowledge/cs/contents/**"], write_scopes=["expansion:content:spring", "expansion:content:database", "expansion:content:software-engineering", "expansion:content:language-java", "expansion:content:network", "expansion:content:data-structure", "expansion:content:algorithm"]),
    _expansion_profile("expansion-qa-readme-registration", "qa-link", "qa", "script", ["readme", "registration", "navigator", "return-path"], ["knowledge/cs/contents/**/README.md", "knowledge/cs/contents/**/*.md"], write_scopes=["expansion:content:spring", "expansion:content:database", "expansion:content:software-engineering", "expansion:content:language-java", "expansion:content:network", "expansion:content:data-structure", "expansion:content:algorithm"]),
    _expansion_profile("expansion-qa-algorithm-data-structure", "qa-content-data-structure", "qa", "fix", ["algorithm", "data-structure", "bfs", "dfs", "queue", "map"], ["knowledge/cs/contents/data-structure/**", "knowledge/cs/contents/algorithm/**"], write_scopes=["expansion:content:data-structure", "expansion:content:algorithm"]),
    _expansion_profile("expansion-rag-spring-di", "qa-retrieval", "rag", "fix", ["spring", "di", "bean", "component-scan", "golden"], ["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_*.py", "scripts/learning/rag/**"], write_scopes=["expansion:rag:golden", "expansion:rag:signal-rules"]),
    _expansion_profile("expansion-rag-roomescape-admin", "qa-retrieval", "rag", "fix", ["roomescape", "admin", "controller", "validation", "exception"], ["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_*.py", "scripts/learning/rag/**"], write_scopes=["expansion:rag:golden", "expansion:rag:signal-rules"]),
    _expansion_profile("expansion-rag-persistence", "qa-retrieval", "rag", "fix", ["jdbc", "jpa", "transaction", "repository"], ["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_*.py", "scripts/learning/rag/**"], write_scopes=["expansion:rag:golden", "expansion:rag:signal-rules"]),
    _expansion_profile("expansion-rag-http-testing", "qa-retrieval", "rag", "fix", ["http", "rest", "testing", "layering"], ["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_*.py", "scripts/learning/rag/**"], write_scopes=["expansion:rag:golden", "expansion:rag:signal-rules"]),
    _expansion_profile("expansion-rag-signal-rules", "qa-retrieval", "rag", "fix", ["signal", "boost", "suppress", "beginner"], ["scripts/learning/rag/signal_rules.py", "tests/unit/test_cs_rag_signal_rules.py"], write_scopes=["expansion:rag:signal-rules"]),
    _expansion_profile("expansion-rag-golden-curation", "qa-retrieval", "rag", "fix", ["golden", "fixture", "query", "regression"], ["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_golden.py"], write_scopes=["expansion:rag:golden"]),
    _expansion_profile("expansion-ops-queue-governor", "qa-taxonomy", "ops", "queue", ["queue", "pending", "candidate", "governor"], ["state/orchestrator/**"]),
    _expansion_profile("expansion-ops-index-readiness", "qa-retrieval", "ops", "ops", ["index", "cs-index-build", "readiness", "post-wave"], ["state/cs_rag/**", "knowledge/cs/**", "scripts/learning/rag/**"]),
    _expansion_profile("expansion-ops-release-gate", "qa-link", "ops", "ops", ["release", "gate", "commit", "lint", "index", "test"], ["knowledge/cs/**", "tests/**", "state/cs_rag/**"]),
]

EXPANSION60_FLEET: list[dict[str, Any]] = [
    _expansion60_profile("expansion60-curriculum-level2-map", "qa-taxonomy", "curriculum", "report", ["woowacourse", "level2", "roomescape", "spring", "foundation"], ["knowledge/cs/JUNIOR-BACKEND-ROADMAP.md", "state/learner/**", "state/orchestrator/reports/**"]),
    _expansion60_profile("expansion60-curriculum-gap-prioritizer", "qa-taxonomy", "curriculum", "report", ["gap", "priority", "learner", "module", "roadmap"], ["knowledge/cs/JUNIOR-BACKEND-ROADMAP.md", "knowledge/cs/contents/**/README.md", "state/orchestrator/reports/**"]),
    _expansion60_profile("expansion60-spring-di-bean", "spring", "content", "expand", ["spring", "di", "bean", "ioc", "component-scan"], ["knowledge/cs/contents/spring/**"], write_scopes=["expansion60:content:spring:di-bean"], can_enqueue=True),
    _expansion60_profile("expansion60-spring-mvc-binding", "spring", "content", "expand", ["spring-mvc", "controller", "binding", "requestbody", "modelattribute"], ["knowledge/cs/contents/spring/**"], write_scopes=["expansion60:content:spring:mvc-binding"], can_enqueue=True),
    _expansion60_profile("expansion60-spring-validation-error", "spring", "content", "expand", ["validation", "bindingresult", "exception", "problemdetail", "400"], ["knowledge/cs/contents/spring/**"], write_scopes=["expansion60:content:spring:validation-error"], can_enqueue=True),
    _expansion60_profile("expansion60-security-session-auth", "security", "content", "expand", ["security", "authentication", "authorization", "session", "jwt", "csrf"], ["knowledge/cs/contents/security/**"], write_scopes=["expansion60:content:security:session-auth"], can_enqueue=True),
    _expansion60_profile("expansion60-spring-transaction-aop", "spring", "content", "expand", ["transaction", "transactional", "aop", "proxy", "self-invocation"], ["knowledge/cs/contents/spring/**"], write_scopes=["expansion60:content:spring:transaction-aop"], can_enqueue=True),
    _expansion60_profile("expansion60-spring-test-slice", "spring", "content", "expand", ["spring-test", "slice", "mockmvc", "test", "profile"], ["knowledge/cs/contents/spring/**"], write_scopes=["expansion60:content:spring:test-slice"], can_enqueue=True),
    _expansion60_profile("expansion60-system-design-backend-foundations", "system-design", "content", "expand", ["system-design", "cache", "queue", "consistency", "idempotency", "availability"], ["knowledge/cs/contents/system-design/**"], write_scopes=["expansion60:content:system-design:backend-foundations"], can_enqueue=True),
    _expansion60_profile("expansion60-network-http-status", "network", "content", "expand", ["http", "status-code", "redirect", "prg", "401", "403"], ["knowledge/cs/contents/network/**"], write_scopes=["expansion60:content:network:http-status"], can_enqueue=True),
    _expansion60_profile("expansion60-network-browser-devtools", "network", "content", "expand", ["browser", "devtools", "waterfall", "cache", "application"], ["knowledge/cs/contents/network/**"], write_scopes=["expansion60:content:network:browser-devtools"], can_enqueue=True),
    _expansion60_profile("expansion60-operating-system-runtime-io", "operating-system", "content", "expand", ["operating-system", "process", "thread", "memory", "io", "backpressure"], ["knowledge/cs/contents/operating-system/**"], write_scopes=["expansion60:content:operating-system:runtime-io"], can_enqueue=True),
    _expansion60_profile("expansion60-network-api-browser-boundary", "network", "content", "expand", ["api", "browser", "json", "html", "redirect"], ["knowledge/cs/contents/network/**"], write_scopes=["expansion60:content:network:api-browser-boundary"], can_enqueue=True),
    _expansion60_profile("expansion60-database-jdbc", "database", "content", "expand", ["jdbc", "sql", "datasource", "connection"], ["knowledge/cs/contents/database/**"], write_scopes=["expansion60:content:database:jdbc"], can_enqueue=True),
    _expansion60_profile("expansion60-database-jpa-repository", "database", "content", "expand", ["jpa", "repository", "entity", "dao", "mapper"], ["knowledge/cs/contents/database/**"], write_scopes=["expansion60:content:database:jpa-repository"], can_enqueue=True),
    _expansion60_profile("expansion60-database-transaction-lock", "database", "content", "expand", ["transaction", "isolation", "lock", "deadlock", "retry"], ["knowledge/cs/contents/database/**"], write_scopes=["expansion60:content:database:transaction-lock"], can_enqueue=True),
    _expansion60_profile("expansion60-database-index-explain", "database", "content", "expand", ["index", "explain", "query", "mysql", "postgresql"], ["knowledge/cs/contents/database/**"], write_scopes=["expansion60:content:database:index-explain"], can_enqueue=True),
    _expansion60_profile("expansion60-java-object-model", "language-java", "content", "expand", ["java", "object", "reference", "memory", "class"], ["knowledge/cs/contents/language/java/**"], write_scopes=["expansion60:content:language-java:object-model"], can_enqueue=True),
    _expansion60_profile("expansion60-java-equality-hashcode", "language-java", "content", "expand", ["equals", "hashcode", "identity", "value", "set"], ["knowledge/cs/contents/language/java/**"], write_scopes=["expansion60:content:language-java:equality-hashcode"], can_enqueue=True),
    _expansion60_profile("expansion60-java-collections-map-set", "language-java", "content", "expand", ["collections", "map", "set", "list", "queue"], ["knowledge/cs/contents/language/java/**"], write_scopes=["expansion60:content:language-java:collections-map-set"], can_enqueue=True),
    _expansion60_profile("expansion60-design-pattern-boundary-patterns", "design-pattern", "content", "expand", ["design-pattern", "strategy", "factory", "repository", "command-query", "event"], ["knowledge/cs/contents/design-pattern/**"], write_scopes=["expansion60:content:design-pattern:boundary-patterns"], can_enqueue=True),
    _expansion60_profile("expansion60-algo-bfs-dfs-graph", "data-structure", "content", "expand", ["algorithm", "bfs", "dfs", "graph", "visited"], ["knowledge/cs/contents/algorithm/**"], write_scopes=["expansion60:content:algorithm:bfs-dfs-graph"], can_enqueue=True),
    _expansion60_profile("expansion60-ds-queue-deque-map", "data-structure", "content", "expand", ["queue", "deque", "map", "set", "treemap"], ["knowledge/cs/contents/data-structure/**"], write_scopes=["expansion60:content:data-structure:queue-deque-map"], can_enqueue=True),
    _expansion60_profile("expansion60-ds-tree-heap-unionfind", "data-structure", "content", "expand", ["tree", "heap", "union-find", "priority-queue"], ["knowledge/cs/contents/data-structure/**"], write_scopes=["expansion60:content:data-structure:tree-heap-unionfind"], can_enqueue=True),
    _expansion60_profile("expansion60-se-layering-dto-contract", "software-engineering", "content", "expand", ["layering", "dto", "contract", "service", "repository"], ["knowledge/cs/contents/software-engineering/**"], write_scopes=["expansion60:content:software-engineering:layering-dto-contract"], can_enqueue=True),
    _expansion60_profile("expansion60-se-testing-refactoring", "software-engineering", "content", "expand", ["testing", "refactoring", "readable-code", "tdd"], ["knowledge/cs/contents/software-engineering/**"], write_scopes=["expansion60:content:software-engineering:testing-refactoring"], can_enqueue=True),
    _expansion60_profile("expansion60-qa-spring-di-bean", "qa-content-spring", "qa", "fix", ["spring", "di", "bean", "ioc"], ["knowledge/cs/contents/spring/**"], write_scopes=["expansion60:content:spring:di-bean"]),
    _expansion60_profile("expansion60-qa-system-design-backend-foundations", "qa-content-system-design", "qa", "fix", ["system-design", "cache", "queue", "consistency"], ["knowledge/cs/contents/system-design/**"], write_scopes=["expansion60:content:system-design:backend-foundations"]),
    _expansion60_profile("expansion60-qa-security-session-auth", "qa-content-security", "qa", "fix", ["security", "authentication", "authorization", "session"], ["knowledge/cs/contents/security/**"], write_scopes=["expansion60:content:security:session-auth"]),
    _expansion60_profile("expansion60-qa-spring-transaction-test", "qa-content-spring", "qa", "fix", ["transaction", "aop", "test", "slice"], ["knowledge/cs/contents/spring/**"], write_scopes=["expansion60:content:spring:transaction-aop", "expansion60:content:spring:test-slice"]),
    _expansion60_profile("expansion60-qa-network-status-redirect", "qa-content-network", "qa", "fix", ["http", "status", "redirect", "prg"], ["knowledge/cs/contents/network/**"], write_scopes=["expansion60:content:network:http-status"]),
    _expansion60_profile("expansion60-qa-operating-system-runtime-io", "qa-content-operating-system", "qa", "fix", ["operating-system", "process", "thread", "io"], ["knowledge/cs/contents/operating-system/**"], write_scopes=["expansion60:content:operating-system:runtime-io"]),
    _expansion60_profile("expansion60-qa-database-jdbc-jpa", "qa-content-database", "qa", "fix", ["jdbc", "jpa", "repository", "entity"], ["knowledge/cs/contents/database/**"], write_scopes=["expansion60:content:database:jdbc", "expansion60:content:database:jpa-repository"]),
    _expansion60_profile("expansion60-qa-database-transaction-index", "qa-content-database", "qa", "fix", ["transaction", "lock", "index", "explain"], ["knowledge/cs/contents/database/**"], write_scopes=["expansion60:content:database:transaction-lock", "expansion60:content:database:index-explain"]),
    _expansion60_profile("expansion60-qa-java-object-equality", "qa-content-language-java", "qa", "fix", ["java", "object", "equals", "hashcode"], ["knowledge/cs/contents/language/java/**"], write_scopes=["expansion60:content:language-java:object-model", "expansion60:content:language-java:equality-hashcode"]),
    _expansion60_profile("expansion60-qa-design-pattern-boundary-patterns", "qa-content-design-pattern", "qa", "fix", ["design-pattern", "strategy", "factory", "repository"], ["knowledge/cs/contents/design-pattern/**"], write_scopes=["expansion60:content:design-pattern:boundary-patterns"]),
    _expansion60_profile("expansion60-qa-algorithm-graph", "qa-content-data-structure", "qa", "fix", ["algorithm", "bfs", "dfs", "graph"], ["knowledge/cs/contents/algorithm/**"], write_scopes=["expansion60:content:algorithm:bfs-dfs-graph"]),
    _expansion60_profile("expansion60-qa-ds-map-tree", "qa-content-data-structure", "qa", "fix", ["queue", "map", "treemap", "heap", "union-find"], ["knowledge/cs/contents/data-structure/**"], write_scopes=["expansion60:content:data-structure:queue-deque-map", "expansion60:content:data-structure:tree-heap-unionfind"]),
    _expansion60_profile("expansion60-qa-se-layering-testing", "qa-content-software-engineering", "qa", "fix", ["layering", "dto", "testing", "refactoring"], ["knowledge/cs/contents/software-engineering/**"], write_scopes=["expansion60:content:software-engineering:layering-dto-contract", "expansion60:content:software-engineering:testing-refactoring"]),
    _expansion60_profile("expansion60-qa-readme-web-runtime", "qa-link", "qa", "script", ["readme", "registration", "spring", "network", "security", "operating-system"], ["knowledge/cs/contents/spring/README.md", "knowledge/cs/contents/network/README.md", "knowledge/cs/contents/security/README.md", "knowledge/cs/contents/operating-system/README.md"], write_scopes=["expansion60:readme:spring", "expansion60:readme:network", "expansion60:readme:security", "expansion60:readme:operating-system"]),
    _expansion60_profile("expansion60-qa-readme-data-java", "qa-link", "qa", "script", ["readme", "registration", "database", "java"], ["knowledge/cs/contents/database/README.md", "knowledge/cs/contents/language/README.md"], write_scopes=["expansion60:readme:database", "expansion60:readme:language-java"]),
    _expansion60_profile("expansion60-qa-readme-architecture-practice", "qa-link", "qa", "script", ["readme", "registration", "algorithm", "data-structure", "software-engineering", "system-design", "design-pattern"], ["knowledge/cs/contents/algorithm/README.md", "knowledge/cs/contents/data-structure/README.md", "knowledge/cs/contents/software-engineering/README.md", "knowledge/cs/contents/system-design/README.md", "knowledge/cs/contents/design-pattern/README.md"], write_scopes=["expansion60:readme:algorithm", "expansion60:readme:data-structure", "expansion60:readme:software-engineering", "expansion60:readme:system-design", "expansion60:readme:design-pattern"]),
    _expansion60_profile("expansion60-qa-anchor-symptoms-a", "qa-anchor", "qa", "script", ["anchor", "symptom", "beginner", "뭐예요", "헷갈"], ["knowledge/cs/contents/{spring,network,database,security,operating-system}/**"], write_scopes=["expansion60:qa:anchor:a"]),
    _expansion60_profile("expansion60-qa-anchor-symptoms-b", "qa-anchor", "qa", "script", ["anchor", "symptom", "beginner", "처음", "왜"], ["knowledge/cs/contents/{language,data-structure,algorithm,software-engineering,system-design,design-pattern}/**"], write_scopes=["expansion60:qa:anchor:b"]),
    _expansion60_profile("expansion60-qa-cross-category-a", "qa-bridge", "qa", "script", ["bridge", "cross-category", "spring", "database", "network", "security"], ["knowledge/cs/contents/{spring,database,network,security,operating-system}/**"], write_scopes=["expansion60:qa:bridge:a"]),
    _expansion60_profile("expansion60-qa-cross-category-b", "qa-bridge", "qa", "script", ["bridge", "cross-category", "java", "algorithm", "software-engineering", "system-design"], ["knowledge/cs/contents/{language,data-structure,algorithm,software-engineering,system-design,design-pattern}/**"], write_scopes=["expansion60:qa:bridge:b"]),
    _expansion60_profile("expansion60-qa-duplicate-taxonomy", "qa-taxonomy", "qa", "fix", ["duplicate", "taxonomy", "overlap", "navigation"], ["knowledge/cs/**"], write_scopes=["expansion60:qa:taxonomy"]),
    _expansion60_profile("expansion60-qa-code-density", "qa-content", "qa", "fix", ["code", "example", "beginner", "clarity"], ["knowledge/cs/contents/**"], write_scopes=["expansion60:qa:code-density"]),
    _expansion60_profile("expansion60-rag-spring-query-eval", "qa-retrieval", "rag", "fix", ["spring", "di", "mvc", "transaction", "query"], ["tests/unit/test_cs_rag_search.py", "tests/unit/test_cs_rag_signal_rules.py"], write_scopes=["expansion60:rag:eval:spring"]),
    _expansion60_profile("expansion60-rag-roomescape-admin-eval", "qa-retrieval", "rag", "fix", ["roomescape", "admin", "security", "validation"], ["tests/unit/test_cs_rag_search.py", "tests/unit/test_cs_rag_signal_rules.py"], write_scopes=["expansion60:rag:eval:roomescape-admin"]),
    _expansion60_profile("expansion60-rag-persistence-eval", "qa-retrieval", "rag", "fix", ["jdbc", "jpa", "transaction", "database"], ["tests/unit/test_cs_rag_search.py", "tests/unit/test_cs_rag_signal_rules.py"], write_scopes=["expansion60:rag:eval:persistence"]),
    _expansion60_profile("expansion60-rag-http-java-eval", "qa-retrieval", "rag", "fix", ["http", "java", "collections", "browser"], ["tests/unit/test_cs_rag_search.py", "tests/unit/test_cs_rag_signal_rules.py"], write_scopes=["expansion60:rag:eval:http-java"]),
    _expansion60_profile("expansion60-rag-signal-rules-mutator", "qa-retrieval", "rag", "fix", ["signal", "boost", "suppress", "beginner"], ["scripts/learning/rag/signal_rules.py", "tests/unit/test_cs_rag_signal_rules.py"], write_scopes=["expansion60:rag:signal-rules"]),
    _expansion60_profile("expansion60-rag-golden-mutator", "qa-retrieval", "rag", "fix", ["golden", "fixture", "query", "regression"], ["tests/fixtures/cs_rag_golden_queries.json", "tests/unit/test_cs_rag_golden.py"], write_scopes=["expansion60:rag:golden"]),
    _expansion60_profile("expansion60-rag-router-runtime", "qa-retrieval", "rag", "fix", ["rag-ask", "router", "tier", "interactive"], ["scripts/workbench/core/interactive_rag_router.py", "tests/unit/test_interactive_rag_router.py"], write_scopes=["expansion60:rag:router"]),
    _expansion60_profile("expansion60-rag-index-smoke", "qa-retrieval", "rag", "script", ["index", "stale", "cs-index-build", "readiness"], ["state/cs_rag/**", "scripts/learning/rag/**"], write_scopes=["expansion60:rag:index-smoke"]),
    _expansion60_profile("expansion60-ops-queue-governor", "qa-taxonomy", "ops", "queue", ["queue", "pending", "candidate", "governor"], ["state/orchestrator/**"], write_scopes=["expansion60:ops:queue-governor"]),
    _expansion60_profile("expansion60-ops-write-scope-governor", "qa-taxonomy", "ops", "ops", ["write-scope", "lease", "waiting", "throughput"], ["state/orchestrator/**", "docs/orchestrator-30-worker-fleet.md"], write_scopes=["expansion60:ops:write-scope-governor"]),
    _expansion60_profile("expansion60-ops-index-readiness", "qa-retrieval", "ops", "ops", ["index", "cs-index-build", "readiness", "post-wave"], ["state/cs_rag/**", "knowledge/cs/**", "scripts/learning/rag/**"], write_scopes=["expansion60:ops:index-readiness"]),
    _expansion60_profile("expansion60-ops-release-gate", "qa-link", "ops", "ops", ["release", "gate", "commit", "lint", "test"], ["knowledge/cs/**", "tests/**", "state/cs_rag/**"], write_scopes=["expansion60:ops:release-gate"]),
]

FLEET_PROFILES: dict[str, list[dict[str, Any]]] = {
    "quality": QUALITY_REPAIR_FLEET,
    "expansion": EXPANSION_FLEET,
    "expansion60": EXPANSION60_FLEET,
    # migration_v3: 30-worker fleet that transforms 2,200+ legacy docs
    # into the R3 v3 frontmatter contract. Created but intentionally
    # unstarted — see docs/master-plan-progress.md Phase 8.
    "migration_v3": MIGRATION_V3_FLEET,
    # migration_v3_60: 60-worker high-throughput variant for ChatGPT
    # Pro quota. Wave C topology direct-attacks the cohort_eval weak
    # spots (mission_bridge 83.3%, confusable_pairs 90%,
    # symptom_to_cause 93.3%) with 5 mission_bridge + 3 chooser + 3
    # symptom_router new-doc writers. See docs/migration-v3-runbook.md.
    "migration_v3_60": MIGRATION_V3_60_FLEET,
}

WORKER_FLEET = QUALITY_REPAIR_FLEET


def _normalize_fleet_profile(profile: str | None) -> str:
    normalized = (profile or DEFAULT_FLEET_PROFILE).strip().lower()
    if normalized not in FLEET_PROFILES:
        allowed = ", ".join(sorted(FLEET_PROFILES))
        raise ValueError(f"unknown fleet profile: {profile!r}; expected one of: {allowed}")
    return normalized


def _fleet_for_profile(profile: str | None = None) -> list[dict[str, Any]]:
    return FLEET_PROFILES[_normalize_fleet_profile(profile)]

LANE_SCOPE: dict[str, str] = {
    "qa-content-database": "knowledge/cs/contents/database/** and knowledge/cs/contents/database/README.md",
    "qa-content-security": "knowledge/cs/contents/security/** and knowledge/cs/contents/security/README.md",
    "qa-content-network": "knowledge/cs/contents/network/** and knowledge/cs/contents/network/README.md",
    "qa-content-system-design": "knowledge/cs/contents/system-design/** and knowledge/cs/contents/system-design/README.md",
    "qa-content-operating-system": "knowledge/cs/contents/operating-system/** and knowledge/cs/contents/operating-system/README.md",
    "qa-content-spring": "knowledge/cs/contents/spring/** and knowledge/cs/contents/spring/README.md",
    "qa-content-design-pattern": "knowledge/cs/contents/design-pattern/** and knowledge/cs/contents/design-pattern/README.md",
    "qa-content-software-engineering": "knowledge/cs/contents/software-engineering/** and knowledge/cs/contents/software-engineering/README.md",
    "qa-content-language-java": "knowledge/cs/contents/language/java/** and knowledge/cs/contents/language/README.md",
    "qa-content-data-structure": "knowledge/cs/contents/data-structure/**, knowledge/cs/contents/algorithm/**, and their README files",
    "qa-bridge": "knowledge/cs/**, especially cross-category README and related-doc bridges",
    "qa-anchor": "knowledge/cs/** where retrieval-anchor-keywords are missing or weak",
    "qa-link": "knowledge/cs/** and docs/** for link/reverse-link hygiene",
    "qa-taxonomy": "knowledge/cs/** README/navigator/taxonomy files",
    "qa-retrieval": "tests/fixtures/**, tests/unit/test_cs_rag_*.py, scripts/learning/rag/signal_rules.py",
    "qa-content": "knowledge/cs/**, especially beginner or primer docs that need clearer explanations, examples, common-confusion notes, and safer next-step routing",
}


def _profile_for_worker(worker: str, lane: str, fleet_profile: str | None = None) -> dict[str, Any]:
    selected_profile = _normalize_fleet_profile(fleet_profile)
    fallback_profiles: list[dict[str, Any]] = []
    for profile_name, profiles in FLEET_PROFILES.items():
        if profile_name != selected_profile:
            fallback_profiles.extend(profiles)
    for profile in [*_fleet_for_profile(selected_profile), *fallback_profiles, *WORKER_PROFILES]:
        if profile["name"] == worker:
            return profile
    return {
        "name": worker,
        "lane": lane,
        "role": "ad-hoc",
        "mode": "write",
        "claim_tags": [],
        "write_scopes": [f"lane:{lane}"],
        "target_paths": [_lane_prompt(lane)],
        "quality_gates": [],
        "can_enqueue": True,
    }


def _profile_list(profile: dict[str, Any], key: str) -> list[str]:
    value = profile.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _candidate_tags(candidate: dict[str, Any]) -> set[str]:
    return {str(tag).strip().lower() for tag in candidate.get("tags", []) if str(tag).strip()}


def _non_generic_tags(tags: set[str]) -> set[str]:
    return {tag for tag in tags if tag not in GENERIC_DRIFT_TAGS}


_MIGRATION_V3_DRIFT_MODES = {
    "migrate_v0_to_v3",
    "migrate_prefix",
    "migrate_new_doc",
    "migrate_revisit",
}


def _anti_drift_next_candidates(
    item: dict[str, Any],
    candidates: list[dict[str, Any]],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Reject next_candidates that re-walk the angle just completed.

    Two profile gates open this filter:

      * legacy expansion fleet — ``role=content`` AND ``mode=expand``
      * Phase 8 migration fleet — any of the four migrate_* modes
        (regardless of role) so a Wave A worker proposing the same
        (category, doc_role) combo gets rejected before the planner
        re-enqueues it.

    A candidate must (a) carry at least one tag from
    ``ANTI_DRIFT_NEXT_CANDIDATE_TAGS`` (proves the worker thought
    about balance / cohort weakness) and (b) introduce a non-generic
    angle the current item didn't already have.
    """
    role = profile.get("role")
    mode = profile.get("mode")

    is_legacy_expansion = role == "content" and mode == "expand"
    is_migration_v3 = mode in _MIGRATION_V3_DRIFT_MODES

    if not (is_legacy_expansion or is_migration_v3):
        return candidates

    current_tags = _non_generic_tags({str(tag).strip().lower() for tag in item.get("tags", []) if str(tag).strip()})
    filtered: list[dict[str, Any]] = []
    for candidate in candidates:
        tags = _candidate_tags(candidate)
        non_generic = _non_generic_tags(tags)
        has_balance_signal = bool(tags & ANTI_DRIFT_NEXT_CANDIDATE_TAGS)
        has_new_angle = bool(non_generic - current_tags)
        if has_balance_signal and has_new_angle:
            filtered.append(candidate)
    return filtered


def _normalize_difficulty_label(raw_label: str) -> str:
    if "Beginner" in raw_label or "🟢" in raw_label:
        return "Beginner"
    if "Intermediate" in raw_label or "🟡" in raw_label:
        return "Intermediate"
    if "Advanced" in raw_label or "🔴" in raw_label:
        return "Advanced"
    if "Expert" in raw_label or "⚫" in raw_label or "🟣" in raw_label:
        return "Expert"
    return raw_label.strip() or "Unspecified"


def _doc_category(path: Path, contents_root: Path) -> str:
    relpath = path.relative_to(contents_root)
    return relpath.parts[0] if relpath.parts else "unknown"


def _corpus_balance_snapshot() -> str:
    contents_root = ROOT / CONTENT_DOC_PREFIX
    if not contents_root.exists():
        return "Corpus balance snapshot: unavailable (knowledge/cs/contents missing)."

    difficulty_counts: dict[str, int] = {}
    category_counts: dict[str, dict[str, int]] = {}
    total_docs = 0
    for path in contents_root.rglob("*.md"):
        if path.name == "README.md":
            continue
        total_docs += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = DIFFICULTY_RE.search(text)
        difficulty = _normalize_difficulty_label(match.group(1)) if match else "Unspecified"
        category = _doc_category(path, contents_root)
        difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        category_bucket = category_counts.setdefault(category, {})
        category_bucket[difficulty] = category_bucket.get(difficulty, 0) + 1

    if total_docs == 0:
        return "Corpus balance snapshot: no CS content docs found."

    def ratio(count: int, denominator: int) -> float:
        return count / denominator if denominator else 0.0

    beginner_count = difficulty_counts.get("Beginner", 0)
    intermediate_count = difficulty_counts.get("Intermediate", 0)
    advanced_count = difficulty_counts.get("Advanced", 0) + difficulty_counts.get("Expert", 0)
    beginner_target = DIFFICULTY_BALANCE_TARGETS["Beginner"]
    intermediate_target = DIFFICULTY_BALANCE_TARGETS["Intermediate"]
    category_rows: list[tuple[str, int, float, float]] = []
    for category, counts in category_counts.items():
        category_total = sum(counts.values())
        category_rows.append(
            (
                category,
                category_total,
                ratio(counts.get("Beginner", 0), category_total),
                ratio(counts.get("Intermediate", 0), category_total),
            )
        )
    beginner_gaps = sorted(
        (row for row in category_rows if row[2] < CATEGORY_BEGINNER_FLOOR),
        key=lambda row: row[2],
    )[:5]
    beginner_saturated = sorted(
        (row for row in category_rows if row[2] > CATEGORY_BEGINNER_CEILING),
        key=lambda row: row[2],
        reverse=True,
    )[:5]
    intermediate_gaps = sorted(
        (row for row in category_rows if row[3] < CATEGORY_INTERMEDIATE_FLOOR),
        key=lambda row: row[3],
    )[:5]

    def category_summary(rows: list[tuple[str, int, float, float]]) -> str:
        if not rows:
            return "none"
        return ", ".join(f"{name} B{beginner:.0%}/I{intermediate:.0%}" for name, _, beginner, intermediate in rows)

    return "\n".join(
        [
            "Corpus balance snapshot:",
            f"- Total docs: {total_docs}",
            (
                "- Difficulty mix: "
                f"Beginner {beginner_count} ({ratio(beginner_count, total_docs):.0%}), "
                f"Intermediate {intermediate_count} ({ratio(intermediate_count, total_docs):.0%}), "
                f"Advanced/Expert {advanced_count} ({ratio(advanced_count, total_docs):.0%})"
            ),
            (
                "- Target mix for new work: "
                f"Beginner {beginner_target[0]:.0%}-{beginner_target[1]:.0%}, "
                f"Intermediate {intermediate_target[0]:.0%}-{intermediate_target[1]:.0%}, "
                "Advanced/Expert as curated deep dives."
            ),
            f"- Beginner gap categories: {category_summary(beginner_gaps)}",
            f"- Beginner-saturated categories: {category_summary(beginner_saturated)}",
            f"- Intermediate gap categories: {category_summary(intermediate_gaps)}",
        ]
    )


def _worker_root() -> Path:
    return ensure_orchestrator_layout() / "workers"


def _worker_dir(worker: str) -> Path:
    return _worker_root() / worker


def _worker_status_path(worker: str) -> Path:
    return _worker_dir(worker) / "status.json"


def _worker_log_path(worker: str) -> Path:
    return _worker_dir(worker) / "worker.log"


def _worker_output_path(worker: str) -> Path:
    return _worker_dir(worker) / "last-output.json"


def _worker_prompt_path(worker: str) -> Path:
    return _worker_dir(worker) / "last-prompt.txt"


def _worker_pid_path(worker: str) -> Path:
    return _worker_dir(worker) / "worker.pid"


def _worker_schema_path() -> Path:
    return ensure_orchestrator_layout() / "worker-output.schema.json"


def _fleet_status_path() -> Path:
    return ensure_orchestrator_layout() / "fleet-status.json"


def _supervisor_pid_path() -> Path:
    return ensure_orchestrator_layout() / "fleet-supervisor.pid"


def _fleet_profile_path() -> Path:
    return ensure_orchestrator_layout() / "fleet-profile.json"


def _write_active_fleet_profile(profile: str, *, supervisor_pid: int | None = None) -> None:
    _write_json(
        _fleet_profile_path(),
        {
            "profile": _normalize_fleet_profile(profile),
            "supervisor_pid": supervisor_pid,
            "updated_at": _isoformat(_utc_now()),
        },
    )


def _active_fleet_profile(default: str = DEFAULT_FLEET_PROFILE) -> str:
    payload = _load_json(_fleet_profile_path(), {})
    try:
        return _normalize_fleet_profile(str(payload.get("profile") or default))
    except ValueError:
        return _normalize_fleet_profile(default)


def _worker_codex_home(worker: str) -> Path:
    return ensure_orchestrator_layout() / "codex-home" / worker


def _prepare_worker_codex_home(worker: str) -> Path:
    codex_home = _worker_codex_home(worker)
    codex_home.mkdir(parents=True, exist_ok=True)
    (codex_home / "sessions").mkdir(parents=True, exist_ok=True)
    source_home = Path.home() / ".codex"
    for name in ("auth.json", "config.toml", "version.json"):
        source = source_home / name
        target = codex_home / name
        if source.exists() and not target.exists():
            shutil.copy2(source, target)
    return codex_home


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _append_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def _ensure_worker_schema() -> Path:
    path = _worker_schema_path()
    payload = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "changed_files": {"type": "array", "items": {"type": "string"}},
            "next_candidates": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "goal": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "goal", "tags"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary", "changed_files", "next_candidates"],
        "additionalProperties": False,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _project_python() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _normalize_changed_files(raw_files: Any) -> tuple[list[str], list[str]]:
    if raw_files in (None, ""):
        return [], []
    if not isinstance(raw_files, list):
        return [], ["changed_files must be an array"]
    normalized: list[str] = []
    errors: list[str] = []
    seen: set[str] = set()
    for raw in raw_files:
        value = str(raw).strip()
        if not value:
            continue
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"invalid changed file path: {value}")
            continue
        relpath = path.as_posix()
        if relpath not in seen:
            normalized.append(relpath)
            seen.add(relpath)
    return normalized, errors


def _authoring_lint_targets(changed_files: list[str]) -> list[str]:
    targets: list[str] = []
    for relpath in changed_files:
        path = Path(relpath)
        if (
            relpath.startswith(CONTENT_DOC_PREFIX)
            and path.suffix == ".md"
            and path.name != "README.md"
        ):
            targets.append(relpath)
    return targets


# ---------------------------------------------------------------------------
# Migration v3 gate helpers (Phase 8)
# ---------------------------------------------------------------------------

PILOT_LOCK_PATH_REL = "config/migration_v3/locked_pilot_paths.json"


def _is_migration_v3_worker(worker: str) -> bool:
    return worker.startswith("migration-v3-")


def _load_pilot_lock_paths() -> set[str]:
    path = ROOT / PILOT_LOCK_PATH_REL
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    paths = payload.get("locked_paths", [])
    if not isinstance(paths, list):
        return set()
    return {str(p) for p in paths}


def _pilot_lock_violations(changed_files: list[str]) -> list[str]:
    """Return changed files that intersect the Pilot v3 lock list.

    Pilot 50 + Phase 4 wave docs (69 total as of 2026-05-05) hold the
    OVERALL 95.5% baseline. Migration workers writing to these paths
    would corrupt the eval contract, so the gate fails fast before
    spawning any subprocess.
    """
    locked = _load_pilot_lock_paths()
    if not locked:
        return []
    return sorted(p for p in changed_files if p in locked)


def _migration_v3_lint_targets(changed_files: list[str]) -> list[str]:
    """Content docs touched by a migration_v3 worker.

    Returned solely to gate-or-skip the v3 corpus_lint pass; the
    actual ``corpus_lint`` invocation scans the whole corpus root, so
    individual paths are not passed through.
    """
    return [
        relpath for relpath in changed_files
        if relpath.startswith(CONTENT_DOC_PREFIX)
        and Path(relpath).suffix == ".md"
        and Path(relpath).name != "README.md"
    ]


def _rag_pytest_args(worker: str, lane: str, changed_files: list[str]) -> list[list[str]]:
    tests: list[list[str]] = []
    changed = set(changed_files)

    if "tests/unit/test_cs_rag_signal_rules.py" in changed or "scripts/learning/rag/signal_rules.py" in changed:
        tests.append(["tests/unit/test_cs_rag_signal_rules.py"])

    search_sensitive = {
        "scripts/learning/rag/searcher.py",
        "scripts/learning/rag/corpus_loader.py",
        "scripts/learning/rag/indexer.py",
        "scripts/learning/rag/reranker.py",
        "tests/unit/test_cs_rag_search.py",
    }
    if changed & search_sensitive:
        tests.append(["tests/unit/test_cs_rag_search.py"])

    if CS_RAG_FIXTURE in changed or "tests/unit/test_cs_rag_golden.py" in changed:
        tests.append(["tests/unit/test_cs_rag_golden.py::CsRagGoldenFixtureContract"])

    if "tests/unit/test_cs_readiness.py" in changed or any(path.startswith("state/cs_rag/") for path in changed):
        tests.append(["tests/unit/test_cs_readiness.py"])

    if lane == "qa-retrieval" and not tests:
        if "projection" in worker:
            tests.append(["tests/unit/test_cs_rag_search.py", "-k", "projection"])
        elif "transaction" in worker:
            tests.append(["tests/unit/test_cs_rag_search.py", "-k", "transaction or rollback or isolation"])
            tests.append(["tests/unit/test_cs_rag_signal_rules.py", "-k", "transaction or rollback or isolation"])
        elif "jwt" in worker:
            tests.append(["tests/unit/test_cs_rag_search.py", "-k", "jwt or auth or session"])
            tests.append(["tests/unit/test_cs_rag_signal_rules.py", "-k", "jwt or auth or session"])
        elif "golden" in worker:
            tests.append(["tests/unit/test_cs_rag_golden.py::CsRagGoldenFixtureContract"])
        elif "index" in worker:
            tests.append(["tests/unit/test_cs_readiness.py"])
        else:
            tests.append(["tests/unit/test_cs_rag_signal_rules.py"])

    deduped: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for args in tests:
        key = tuple(args)
        if key not in seen:
            deduped.append(args)
            seen.add(key)
    return deduped


def _run_completion_gate_command(command: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    output = "\n".join(part for part in (result.stdout[-1200:], result.stderr[-1200:]) if part)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "ok": result.returncode == 0,
        "output": output[-2000:],
    }


def _run_completion_gates(
    worker: str,
    lane: str,
    task: dict[str, Any],
    *,
    timeout_seconds: int = DEFAULT_COMPLETION_GATE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    changed_files, path_errors = _normalize_changed_files(task.get("changed_files", []))
    if path_errors:
        return {
            "ok": False,
            "summary": "; ".join(path_errors),
            "changed_files": changed_files,
            "commands": [],
        }

    # Migration v3 pre-flight: Pilot lock guard. Fails fast (no
    # subprocess) if the worker tried to write to a Pilot v3 doc, which
    # would invalidate the OVERALL 95.5% baseline.
    if _is_migration_v3_worker(worker):
        violations = _pilot_lock_violations(changed_files)
        if violations:
            return {
                "ok": False,
                "summary": (
                    f"pilot lock violation: {len(violations)} file(s) — "
                    f"first: {violations[0]}"
                ),
                "changed_files": changed_files,
                "commands": [],
            }

    python = _project_python()
    commands: list[list[str]] = []
    if _is_migration_v3_worker(worker):
        # v3 contract uses corpus_lint, not lint_cs_authoring (legacy).
        if _migration_v3_lint_targets(changed_files):
            commands.append([
                python, "-m", "scripts.learning.rag.corpus_lint",
                "--strict", "--strict-v3",
                "--corpus", "knowledge/cs/contents",
            ])
    else:
        lint_targets = _authoring_lint_targets(changed_files)
        if lint_targets:
            commands.append([python, "scripts/lint_cs_authoring.py", "--strict", "--quiet", *lint_targets])
    for pytest_args in _rag_pytest_args(worker, lane, changed_files):
        commands.append([python, "-m", "pytest", *pytest_args, "-q"])

    results: list[dict[str, Any]] = []
    for command in commands:
        try:
            result = _run_completion_gate_command(command, timeout_seconds=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            result = {
                "command": " ".join(command),
                "returncode": None,
                "ok": False,
                "output": f"completion gate timed out after {exc.timeout}s",
            }
        results.append(result)
        if not result["ok"]:
            return {
                "ok": False,
                "summary": f"completion gate failed: {result['command']}",
                "changed_files": changed_files,
                "commands": results,
            }

    return {
        "ok": True,
        "summary": "completion gates passed" if commands else "no completion gates required",
        "changed_files": changed_files,
        "commands": results,
    }


def _fleet_summary(fleet_profile: str | None = None) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for spec in _fleet_for_profile(fleet_profile):
        worker = spec["name"]
        status = _load_json(_worker_status_path(worker), {})
        pid_path = _worker_pid_path(worker)
        pid = None
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text(encoding="utf-8").strip())
            except ValueError:
                pid = None
        summary[worker] = {
            "lane": spec["lane"],
            "role": spec.get("role"),
            "mode": spec.get("mode"),
            "pid": pid,
            "alive": bool(pid and _pid_alive(pid)),
            "status": status.get("status"),
            "current_item_id": status.get("current_item_id"),
            "last_heartbeat_at": status.get("last_heartbeat_at"),
            "last_success_at": status.get("last_success_at"),
            "last_error": status.get("last_error"),
        }
    return summary


def _fleet_can_enqueue(fleet_profile: str | None = None) -> bool:
    return any(spec.get("can_enqueue", True) for spec in _fleet_for_profile(fleet_profile))


def _lane_prompt(lane: str) -> str:
    return LANE_SCOPE.get(lane, "knowledge/cs/**")


# ---------------------------------------------------------------------------
# Phase 8 — long-running balance + cohort feedback + saturation
# ---------------------------------------------------------------------------
#
# When the migration_v3_60 fleet is left running indefinitely the
# corpus can drift toward whatever cell the workers most easily fill
# — typically `primer` in the densest category. These helpers feed
# *live* corpus state and the latest cohort_eval result into every
# migration worker prompt so each codex call sees the gap it should
# close *next*, not just the gap that was named when the queue item
# was enqueued days ago.
#
# Coupled with the `_anti_drift_next_candidates` filter, this gives us
# three layers of bias defense:
#   1. snapshot — workers are told the live distribution
#   2. saturation ceiling — categories at cap are explicitly marked
#   3. cohort feedback — the prompt cites the cohort_eval cells where
#      pass_rate is below the 94.0% baseline so workers prioritize
#      doc_roles that move those cells

import time as _time

# Saturation ceilings — hard caps per (category, doc_role) cell. These
# are NOT thresholds for refusing work; they are signals that get
# surfaced in the prompt so the worker shifts to a different cell.
# Wave 8.5 review can tune these once the first migration cycle
# finishes.
V3_SATURATION_CAPS: dict[str, int] = {
    "primer": 30,         # one canonical primer per concept; 30 covers most categories
    "deep_dive": 20,
    "playbook": 15,
    "chooser": 10,
    "bridge": 25,
    "drill": 10,
    "symptom_router": 8,
    "mission_bridge": 8,
}
V3_DOC_ROLE_SHARE_CEILING = 0.60  # one doc_role can't hold > 60% of a category

# Live snapshot cache — the corpus walk is ~50ms but each fleet cycle
# can hit it 60× / second when 60 workers all spawn. 30s TTL keeps
# the prompt freshness inside a single user-attention window.
_V3_SNAPSHOT_CACHE: dict[str, tuple[float, str]] = {}
_V3_SNAPSHOT_TTL_SECONDS = 30.0


def _v3_balance_snapshot() -> str:
    """Live category × doc_role × frontmatter-coverage snapshot.

    Returns a short text block injected into the migration worker
    prompt. The snapshot is recomputed on a 30-second TTL so 60
    parallel workers don't each scan 2,286 markdown files.
    """
    cache = _V3_SNAPSHOT_CACHE.get("v3")
    if cache and cache[0] + _V3_SNAPSHOT_TTL_SECONDS > _time.monotonic():
        return cache[1]

    contents_root = ROOT / CONTENT_DOC_PREFIX
    if not contents_root.exists():
        block = "v3 balance snapshot: unavailable (knowledge/cs/contents missing)."
        _V3_SNAPSHOT_CACHE["v3"] = (_time.monotonic(), block)
        return block

    schema_v3_re = re.compile(r"^schema_version:\s*3\b", re.MULTILINE)
    prefix_re = re.compile(r"^contextual_chunk_prefix:", re.MULTILINE)
    doc_role_re = re.compile(r"^doc_role:\s*([a-z_]+)", re.MULTILINE)
    level_re = re.compile(r"^level:\s*([a-z]+)", re.MULTILINE)

    total = 0
    v3_count = 0
    prefix_count = 0
    by_category: dict[str, dict[str, int]] = {}
    by_category_total: dict[str, int] = {}
    by_doc_role: dict[str, int] = {}
    by_level: dict[str, int] = {}
    no_frontmatter = 0

    for path in contents_root.rglob("*.md"):
        if path.name == "README.md":
            continue
        total += 1
        category = _doc_category(path, contents_root)
        by_category_total[category] = by_category_total.get(category, 0) + 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if schema_v3_re.search(text):
            v3_count += 1
            if prefix_re.search(text):
                prefix_count += 1
            role_match = doc_role_re.search(text)
            if role_match:
                role = role_match.group(1)
                by_doc_role[role] = by_doc_role.get(role, 0) + 1
                bucket = by_category.setdefault(category, {})
                bucket[role] = bucket.get(role, 0) + 1
            level_match = level_re.search(text)
            if level_match:
                lvl = level_match.group(1)
                by_level[lvl] = by_level.get(lvl, 0) + 1
        elif text.lstrip().startswith("---"):
            pass  # legacy v2 / partial frontmatter
        else:
            no_frontmatter += 1

    v3_pct = v3_count / total if total else 0.0
    prefix_pct = prefix_count / v3_count if v3_count else 0.0

    # Find the 5 most underweight (category, doc_role) cells — these
    # are the next-action candidates for content workers.
    underweight: list[tuple[str, str, int]] = []
    for category in sorted(by_category_total):
        cat_total = by_category_total[category]
        cells = by_category.get(category, {})
        for role in sorted(V3_SATURATION_CAPS):
            count = cells.get(role, 0)
            cap = V3_SATURATION_CAPS[role]
            if count < cap:
                underweight.append((category, role, count))
    underweight.sort(key=lambda t: t[2])
    underweight_lines = [
        f"  {cat}/{role} = {count}" for cat, role, count in underweight[:6]
    ]

    # Saturated cells — workers should NOT add more here.
    saturated: list[tuple[str, str, int, int]] = []
    for category, cells in by_category.items():
        cat_total = by_category_total.get(category, 1)
        for role, count in cells.items():
            cap = V3_SATURATION_CAPS.get(role)
            if cap and count >= cap:
                saturated.append((category, role, count, cap))
            elif count / cat_total > V3_DOC_ROLE_SHARE_CEILING:
                saturated.append((category, role, count, int(cat_total * V3_DOC_ROLE_SHARE_CEILING)))
    saturated.sort(key=lambda t: -(t[2] / t[3] if t[3] else 0))
    saturated_lines = [
        f"  {cat}/{role} = {count} (cap {cap})"
        for cat, role, count, cap in saturated[:5]
    ] or ["  none"]

    # doc_role share — top 3 most-represented roles in v3 docs
    role_share_lines = []
    for role, n in sorted(by_doc_role.items(), key=lambda kv: -kv[1])[:5]:
        role_share_lines.append(f"  {role}: {n} ({n / v3_count:.0%})" if v3_count else f"  {role}: {n}")

    block = "\n".join([
        "v3 balance snapshot (live, 30s TTL):",
        f"- corpus total: {total} docs",
        f"- v3 frontmatter coverage: {v3_count}/{total} ({v3_pct:.1%})",
        f"- contextual_chunk_prefix coverage: {prefix_count}/{v3_count if v3_count else 1} ({prefix_pct:.1%})",
        f"- no frontmatter (v0): {no_frontmatter}",
        "- v3 doc_role share:",
        *role_share_lines,
        "- underweight cells (prefer these):",
        *underweight_lines,
        "- saturated cells (avoid; pivot to chooser / symptom_router / bridge):",
        *saturated_lines,
    ])
    _V3_SNAPSHOT_CACHE["v3"] = (_time.monotonic(), block)
    return block


def _recent_cohort_eval_feedback() -> str:
    """Pull the most recent cohort_eval JSON and surface fail patterns.

    Looks first for ``reports/rag_eval/post_phase_9_3_active.json``
    (the honest baseline written by the activation cycle), then falls
    back to any newer cohort_eval result. The block is short — only
    the cells that are below 100% and the failure_class breakdown for
    those — so the prompt stays under the codex context budget.
    """
    candidates = [
        ROOT / "reports" / "rag_eval" / "post_phase_9_3_active.json",
        ROOT / "reports" / "rag_eval" / "phase9_done.json",
    ]
    eval_path = next((p for p in candidates if p.exists()), None)
    if eval_path is None:
        return "Recent cohort_eval feedback: no recent JSON found — run cohort_eval to refresh."

    try:
        data = json.loads(eval_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return f"Recent cohort_eval feedback: unable to parse {eval_path.name}."

    overall = data.get("overall_pass_rate")
    per_cohort = data.get("per_cohort") or {}
    weak_cohorts: list[tuple[str, float, dict]] = []
    for tag, metrics in per_cohort.items():
        rate = metrics.get("pass_rate")
        if rate is None or rate >= 1.0:
            continue
        weak_cohorts.append((tag, rate, metrics))
    weak_cohorts.sort(key=lambda t: t[1])

    fail_outcomes: dict[str, dict[str, int]] = {}
    for q in data.get("per_query") or []:
        if q.get("pass_status"):
            continue
        tag = q.get("cohort_tag") or "unknown"
        outcome = q.get("actual_outcome") or "unknown"
        fail_outcomes.setdefault(tag, {})[outcome] = (
            fail_outcomes.setdefault(tag, {}).get(outcome, 0) + 1
        )

    lines = [
        f"Recent cohort_eval feedback (source: {eval_path.name}):",
        f"- OVERALL: {overall:.1%}" if isinstance(overall, (int, float)) else "- OVERALL: n/a",
        "- Weak cohorts (pass < 100%, weakest first):",
    ]
    for tag, rate, metrics in weak_cohorts[:6]:
        outcomes = fail_outcomes.get(tag, {})
        outcome_str = ", ".join(f"{k}:{v}" for k, v in sorted(outcomes.items())) or "n/a"
        lines.append(f"  {tag}: {rate:.1%} (fails → {outcome_str})")
    if not weak_cohorts:
        lines.append("  none — all cohorts at 100% (recompute with newer index)")
    return "\n".join(lines)


def _v3_saturation_ceilings_block() -> str:
    """Static text describing the per-doc_role caps.

    The ``_v3_balance_snapshot`` already lists *which* cells are
    saturated. This block tells the worker the *rules* by which
    saturation is decided, so the codex prompt is self-contained
    even when the snapshot is unavailable.
    """
    cap_lines = [
        f"  {role}: ≤ {cap} per category"
        for role, cap in sorted(V3_SATURATION_CAPS.items(),
                                key=lambda kv: -kv[1])
    ]
    return "\n".join([
        "Saturation ceiling rules:",
        *cap_lines,
        f"- Plus: any doc_role > {V3_DOC_ROLE_SHARE_CEILING:.0%} of a category total is saturated",
        "  → pivot to underweight doc_role even if the cap isn't reached",
    ])


# ---------------------------------------------------------------------------
# Phase 8 — migration_v3 / migration_v3_60 prompt builder
# ---------------------------------------------------------------------------

_MIGRATION_V3_HEADER = """\
You are {worker}, the persistent migration worker for {lane}.

Worker profile:
- Role: {role}
- Mode: {mode}
- Target paths: {target_paths}
- Write scopes: {write_scopes}
- Claim tags: {claim_tags}
- Quality gates: {quality_gates}

Task:
- Item ID: {item_id}
- Title: {title}
- Goal: {goal}
- Tags: {tags}

PHASE 8 V3 MIGRATION CONTRACT (DO NOT mix with the legacy expansion contract)
=============================================================================
This work transforms existing docs to the v3 frontmatter contract defined
in `docs/worklogs/rag-r3-corpus-v3-contract.md` (18 fields) plus the
`contextual_chunk_prefix` per-doc Korean string. **You are NOT writing
the legacy retrieval-anchor-keywords / 7-element Beginner-primer
contract** — that contract is being phased out for the docs you touch.

Hard rules (gate failure = automatic backlog return):
1. Pilot lock — read `config/migration_v3/locked_pilot_paths.json`
   before editing. If any path you would change is in `locked_paths`,
   STOP and return changed_files=[] with a summary explaining the
   conflict. The Pilot 50 + Phase 4 wave 69 docs hold the OVERALL
   95.5%/94.0% baseline — touching them invalidates the eval contract.
2. Body bytes — preserve the markdown body byte-for-byte unless your
   mode is `migrate_new_doc`. `migrate_v0_to_v3` and `migrate_prefix`
   modes ONLY edit the YAML frontmatter block (between the leading and
   trailing `---` lines).
3. v3 contract lint — `python -m scripts.learning.rag.corpus_lint
   --strict --strict-v3 --corpus knowledge/cs/contents` must pass for
   every doc you touch. Missing role-conditional fields are warnings,
   not errors, in Wave A.
4. Aliases ⊥ expected_queries — no phrase may appear in both lists
   (case-folded, whitespace-normalized).
5. Korean prose — Korean fields (`symptoms`, `contextual_chunk_prefix`)
   must be Korean; English technical terms (lock, primary, MVCC) are
   acceptable inside Korean sentences.
6. Output schema — final response is JSON only, with `summary`,
   `changed_files`, `next_candidates`. Every modified file MUST appear
   in `changed_files`; missing entries hide gate failures.

V3 frontmatter field map (canonical order from `migrate_frontmatter_v3.V3_FIELD_ORDER`):
   schema_version (always 3) ; title ; concept_id (`category/slug`,
   kebab-case lowercase) ; canonical (true for the canonical primer per
   concept_id) ; category ; difficulty ; doc_role (one of: primer /
   chooser / bridge / deep_dive / playbook / drill / symptom_router /
   mission_bridge) ; level (beginner / intermediate / advanced) ;
   language (ko / mixed / en) ; source_priority (0..100, primer 90 /
   chooser 88 / bridge 85 / deep_dive 80 / playbook 78 / drill 75 /
   symptom_router 80 / mission_bridge 78) ; mission_ids ;
   review_feedback_tags ; aliases ; symptoms ; intents ;
   prerequisites ; next_docs ; linked_paths ; confusable_with ;
   forbidden_neighbors ; expected_queries ; contextual_chunk_prefix.
"""


def _build_migration_v3_prompt(
    *,
    worker: str,
    lane: str,
    item: dict[str, Any],
    profile: dict[str, Any],
    target_paths: list[str],
    write_scopes: list[str],
    claim_tags: list[str],
    quality_gates: list[str],
    mode: str,
    role: str,
    tags: str,
) -> str:
    """Compose the v3-migration-aware codex prompt.

    Three prompt modes share a common header (Pilot lock, v3 lint,
    output contract) and diverge in the per-mode authoring guide:

      * ``migrate_v0_to_v3`` — Wave A: the deterministic baseline
        from ``create_v3_frontmatter.py`` is already on disk; this
        worker fills the LLM-required authorial fields (mission_ids,
        symptoms, intents, prerequisites, next_docs, linked_paths,
        confusable_with, forbidden_neighbors, expected_queries).
      * ``migrate_prefix`` — Wave B: author the
        ``contextual_chunk_prefix`` block (50-100 token Korean prose)
        for v3 docs that have all other fields filled but an empty
        prefix. Uses ``synthesize_chunk_prefix.build_authoring_prompt``
        as the single-doc seed.
      * ``migrate_new_doc`` — Wave C: write a brand new doc of one of
        three high-impact roles (chooser / symptom_router /
        mission_bridge) — the cohorts that scored weakest in
        post-9.3 cohort_eval (mission_bridge 83.3%, confusable_pairs
        90%, symptom_to_cause 93.3%).
    """
    header = _MIGRATION_V3_HEADER.format(
        worker=worker, lane=lane, role=role, mode=mode,
        target_paths=", ".join(target_paths),
        write_scopes=", ".join(write_scopes) if write_scopes else "report-only",
        claim_tags=", ".join(claim_tags) if claim_tags else "none",
        quality_gates=", ".join(quality_gates) if quality_gates else "none",
        item_id=item.get("item_id", ""),
        title=item.get("title", ""),
        goal=item.get("goal", ""),
        tags=tags or "none",
    )

    if mode == "migrate_v0_to_v3":
        body = _MIGRATION_V0_TO_V3_BODY
    elif mode == "migrate_prefix":
        body = _MIGRATION_PREFIX_BODY
    elif mode == "migrate_new_doc":
        body = _MIGRATION_NEW_DOC_BODY
    elif mode == "migrate_revisit":
        body = _MIGRATION_REVISIT_BODY
    else:
        # Defensive — _worker_prompt only routes the four known modes
        # here, but a future enum addition without a body should fail
        # closed.
        body = (
            f"Unknown migration mode {mode!r}. Return changed_files=[] "
            "and summary explaining the misconfiguration."
        )

    # Long-running balance defenses: every migration prompt carries
    # the live balance snapshot, recent cohort_eval weak-cohort
    # feedback, and the saturation ceiling rules. The worker reads
    # these BEFORE deciding which doc to author / which authorial
    # field to fill / which new doc role to write.
    balance_block = _v3_balance_snapshot()
    cohort_block = _recent_cohort_eval_feedback()
    saturation_block = _v3_saturation_ceilings_block()

    long_running_guard = f"""
==== LONG-RUNNING BALANCE GUARD (read before choosing what to write) ====

{balance_block}

{cohort_block}

{saturation_block}

How to use these:
- Prefer underweight cells. If your queue item targets a cell that
  is already saturated, summarize the conflict and propose a
  next_candidate in an underweight cell instead.
- If a weak cohort points at a cell you can move (e.g.
  mission_bridge 83.3% + mission_ids:roomescape underweight), bias
  toward that cell.
- next_candidates MUST add a different angle from the current item.
  Repeating the same (category, doc_role) pair within 5 turns is
  enqueue-rejected by the platform anti-drift filter.
- If every queue option you can take is saturated AND no weak
  cohort improves with more docs, return changed_files=[] and a
  next_candidate of `migrate_revisit` (existing-doc quality boost
  on the doc with the weakest aliases / linked_paths / forbidden_neighbors).
"""

    return header + long_running_guard + "\n" + body


_MIGRATION_V0_TO_V3_BODY = """\
WAVE A — v0 → v3 frontmatter authoring
=======================================
This worker runs after `create_v3_frontmatter.py --apply` has
deposited a deterministic baseline on the target docs. The baseline
fills the fields that need NO LLM judgment: schema_version=3, title,
concept_id, canonical (heuristic primer=true), category, difficulty,
doc_role (filename-suffix heuristic), level, language, source_priority,
aliases (lifted from legacy `retrieval-anchor-keywords` if present),
intents (default-by-role), and the empty containers for the fields
below.

Your job: fill the authorial fields the baseline left empty.

Authorial fields to write (preserve everything else exactly):

  mission_ids — list[string] of `missions/<slug>` IDs the doc connects
    to. Empty list when not mission-relevant. Examples:
    `missions/roomescape`, `missions/baseball`, `missions/lotto`,
    `missions/shopping-cart`. ONLY use mission slugs that actually
    exist in this repo's mission registry.
  review_feedback_tags — list[string] short tags from common reviewer
    comment patterns. Examples: `DI-vs-locator`, `repository-boundary`,
    `transactional-self-invocation`, `controller-binding-direction`.
    Empty when no specific reviewer pattern applies.
  symptoms — list[string] short Korean phrases of how a confused
    learner would describe the problem. Examples: `구현체를 어떻게
    골라?`, `같은 트랜잭션인데 왜 격리가 안 돼?`, `403이 떴는데
    원인을 모르겠어`. doc_role=symptom_router needs ≥3, playbook ≥1.
  prerequisites — list[string] concept_id of docs that should be
    learned before this one. Stay within the same corpus
    (`spring/bean`, `database/transaction-basics`, etc.).
  next_docs — list[string] concept_id of docs the learner should read
    next after mastering this. Same constraint as prerequisites.
  linked_paths — list[string] repo-relative .md paths that are
    related but not in the prerequisites/next_docs graph (siblings,
    cross-category bridges). Must be real files in the repo.
  confusable_with — list[string] concept_id of docs that confused
    learners often substitute for this one. doc_role=chooser needs ≥2.
  forbidden_neighbors — list[string] repo-relative .md paths that
    must NEVER be top-1 retrieval for this doc's concept. The
    `r3.search` post-rerank forbidden_filter consumes this. Be
    conservative — only list docs that would actively mislead the
    learner if surfaced for this concept's queries.
  expected_queries — list[string] of 5-10 raw Korean/English learner
    query strings. THESE ARE QREL SEEDS FOR EVAL ONLY — do NOT
    duplicate alias terms here (the v3 contract enforces aliases ⊥
    expected_queries). Use phrasing the learner would actually type:
    `Spring DI가 뭐야?`, `처음 배우는 트랜잭션 정리`,
    `MVCC와 락 비교 좀`, etc. Frame the query so this doc would be
    the TOP-1 expected hit.

Role-conditional minimums (Wave 2 lint warnings):
  - doc_role=symptom_router → symptoms ≥ 3
  - doc_role=playbook       → symptoms ≥ 1
  - doc_role=mission_bridge → mission_ids ≥ 1
  - doc_role=chooser        → confusable_with ≥ 2

What NOT to do:
  - DO NOT modify the markdown body. Tests assert byte-level
    preservation outside the frontmatter block.
  - DO NOT add the legacy `retrieval-anchor-keywords:` body line. It
    is being phased out; the baseline already lifted any present
    anchors into the `aliases` frontmatter field.
  - DO NOT regenerate the deterministic fields the baseline produced
    (schema_version, concept_id, category, language, aliases, etc.) —
    re-running the script is the safe way to refresh those.
  - DO NOT touch `contextual_chunk_prefix` — that is Wave B.

Output:
  - summary: "{N} docs migrated v0→v3, mission_ids/symptoms/intents/...
    filled per role contract. Pilot lock checked."
  - changed_files: every doc you edited, repo-relative.
  - next_candidates: 1-3 concrete follow-up gaps in the same lane,
    e.g. "Wave B prefix authoring for the same {category} batch"
    or "QA pass for confusable_with bidirectional consistency".
"""


_MIGRATION_PREFIX_BODY = """\
WAVE B — contextual_chunk_prefix authoring
==========================================
The v3 frontmatter is fully populated for the target docs. Your job is
to author the doc-level `contextual_chunk_prefix` block — the 50-100
token Korean prose string that the indexer prepends to every chunk's
embedding text. This is the SINGLE biggest dense-retrieval lever per
the Phase 4 closing report (+35.5pp OVERALL on Pilot, from 41
prefix-authored docs).

Format:
   contextual_chunk_prefix: |
     이 문서는 [doc_role 톤에 맞춰 누구에게/무엇을/왜] [doc의 의도]
     [tone-specific verb]. [paraphrase 표현 4-6개], [more] 같은
     자연어 paraphrase가 본 문서의 [핵심 개념]에 매핑된다.

doc_role tone guide:
   primer       → "처음 잡는다" / "기초를 잡는다"
   deep_dive    → "깊이 잡는다" / "내부 메커니즘을 본다"
   playbook     → "전략으로 막는다" / "결정 가이드를 따른다"
   chooser      → "결정한다" / "A vs B를 골라준다"
   bridge       → "연결한다" / "두 개념을 잇는다"
   drill        → "확인 질문으로 굳힌다"
   symptom_router → "증상 → 원인으로 이어진다"
   mission_bridge → "Woowa 미션 ↔ CS concept를 잇는다"

Reference samples (from existing Pilot v3 docs — match this density
and style, NOT longer):

   contents/database/lock-basics.md:
     이 문서는 데이터베이스 학습자가 여러 사용자가 같은 데이터를
     동시에 바꾸려 할 때 충돌을 어떻게 막는지, 동시성 제어 메커니즘
     으로서 lock이 무엇이고 왜 필요한지 처음 잡는 primer다. 동시
     변경 충돌 방지, 동시성 충돌, 같은 데이터 동시에 수정, 락이
     뭐야, optimistic vs pessimistic, shared vs exclusive lock 같은
     자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.

   contents/database/replica-lag-read-after-write-strategies.md:
     이 문서는 학습자가 DB를 여러 대로 복사해서 읽기 부담을 나누면
     일관성이 어떻게 깨지는지, replica lag로 인한 read-after-write
     불일치를 어떤 설계로 막는지 깊이 잡는 deep_dive다. DB 여러 대
     복사, 읽기 부담 나누기, 복제 지연으로 인한 일관성 깨짐, write
     직후 read stale, primary fallback 같은 자연어 paraphrase가 본
     문서의 전략에 매핑된다.

Critical rules:
  - 50-100 token (한국어 약 30-60글자 × 2~3문장). Hard cap 400 chars.
  - paraphrase 표현은 alias와 표면형이 다른 것 — alias는 별도 indexed
    채널, prefix는 dense semantic anchor. 만약 alias에 "락"이 있으면
    prefix paraphrase에는 "락이 뭐야", "잠금 메커니즘", "동시 변경
    방지" 같이 다른 표면형으로.
  - 본문에 없는 사실 추가 금지. 추측 금지. 본문 H2 제목과 한 줄
    요약을 근거로 작성.
  - 영어는 corpus의 기술 용어일 때만 (lock, primary, MVCC, etc.) —
    의역으로 풀면 paraphrase 매핑이 약해진다.
  - 따옴표 / 마크다운 / 코드 펜스 / 헤더 ❌. YAML 멀티라인 (`|`)
    안의 plain Korean prose만.

Tooling: `synthesize_chunk_prefix.build_authoring_prompt(file_path)`
returns a per-doc seeding prompt with H2 headings + body excerpt
extracted; use it as the input frame when stuck.

What NOT to do:
  - DO NOT modify any other frontmatter field.
  - DO NOT modify the markdown body.
  - DO NOT generate per-chunk prefixes (the v3 contract is doc-level
    only — `corpus_loader.py:110,482` consumes one prefix per doc).
  - DO NOT skip docs that already have a non-empty
    `contextual_chunk_prefix` (those are Pilot — Pilot lock will
    catch this anyway).

Output:
  - summary: "{N} docs prefix-authored. Token range A-B avg C.
    doc_role distribution: ..."
  - changed_files: every doc you edited.
  - next_candidates: 1-3 concrete next batches in the same category.
"""


_MIGRATION_REVISIT_BODY = """\
WAVE D — existing-doc quality revisit
======================================
The fleet has been running long enough that all underweight cells
are filled or saturated. Your job in this mode is to *deepen* an
existing v3 doc's quality so the cohort_eval has more high-quality
hits per query, without authoring a new doc.

Pick ONE existing v3 doc that scores low on these checks:

  - aliases length < 5 → learner paraphrase coverage thin
  - expected_queries length < 4 → qrel seed thin (cohort_eval can't
    measure improvement on this doc)
  - linked_paths == [] AND next_docs == [] → doc is graph-isolated
  - confusable_with == [] for chooser/bridge → ranking drift risk
  - forbidden_neighbors == [] for primer with confusable_with set
    → forbidden_filter has no work to do
  - contextual_chunk_prefix < 30 chars or > 400 chars → prefix is
    out of the 50-100 token target band

Allowed authorial actions on the chosen doc:

  - Add 2-4 alias terms that are paraphrase-distinct from existing
    aliases (different surface form, same concept).
  - Add 2-3 expected_queries that are realistic learner phrasings
    NOT covered by current entries (different intent: definition vs
    comparison vs symptom).
  - Add 1-3 linked_paths to genuinely related docs (cross-category
    bridge preferred when it widens the learning path).
  - Add 1-3 next_docs that the learner should read next.
  - Add 1-2 confusable_with for chooser/bridge if the doc is
    silent on alternatives.
  - Add 1-2 forbidden_neighbors when a confusable doc's primer
    would actively mislead a learner of THIS concept.
  - Rewrite contextual_chunk_prefix only if it is out of the token
    target band (50-100 token, ~30-60 글자 × 2-3 문장).

What NOT to do:
  - DO NOT modify the markdown body bytes.
  - DO NOT touch the deterministic baseline fields (schema_version,
    concept_id, category, language, level, source_priority).
  - DO NOT add fields just to add them. Each addition must improve
    one of the cohort_eval failure_class buckets
    (`candidate_absent`, `qrel_incomplete`).
  - DO NOT revisit a doc that was modified in the last 24 hours
    (check `git log --since='24 hours ago' -- <path>`).

Output:
  - summary: "Revisit: {doc_path}. Aliases +{n}, expected_queries
    +{m}, linked_paths +{p}. Targeted gap: {failure_class}."
  - changed_files: [the one revisited doc]
  - next_candidates: 1-3 — other revisit candidates with the same
    weak field, prefer different categories.
"""


_MIGRATION_NEW_DOC_BODY = """\
WAVE C — new doc authoring (chooser / symptom_router / mission_bridge)
======================================================================
The post-9.3 cohort_eval ranked these doc_roles' cohorts as the three
weakest spots in the corpus:

   mission_bridge cohort  83.3% (5/30 fail) — corpus has no docs for
     baseball / lotto / shopping-cart / blackjack mission ↔ CS bridges
     in 2 of 5 fail cases (sentinel emit). 3 of 5 are qrel
     definition issues that will resolve when bridge docs become
     canonical.
   confusable_pairs       90.0% — 4 fails are paired-doc ranking
     drift; chooser docs disambiguate explicitly.
   symptom_to_cause       93.3% — 2 fails route incorrectly when no
     symptom_router doc exists for that symptom.

Your job: write a NEW doc of the role specified in the task tags.

doc_role-specific structure:

CHOOSER ("X vs Y vs Z 결정")
   Title: `{Topic} 결정 가이드`
   Body:
     ## 한 줄 요약 (블록쿼트, 1줄)
     ## 결정 매트릭스 (표 — 4-6 행 max, 결정 축 ≤ 3)
     ## 흔한 오선택 (각 옵션이 잘못 선택되는 패턴 + 학습자 표현)
     ## 다음 학습 (next_docs 후보)
   Frontmatter must set:
     doc_role: chooser
     confusable_with: ≥ 2 concept_id of the alternatives
     symptoms: ≥ 1 (학습자의 결정 실패 표현)

SYMPTOM_ROUTER ("증상 → 원인")
   Title: `{Symptom} 원인 라우터` (symptom 명사형)
   Body:
     ## 한 줄 요약 (증상 한 줄)
     ## 가능한 원인 (3-6 항목, 각 1-2문장 + 다음 doc 링크)
     ## 빠른 자기 진단 (3-5 step, 각 step → 다음 항목으로 가지치기)
     ## 다음 학습
   Frontmatter:
     doc_role: symptom_router
     symptoms: ≥ 3 (학습자가 칠 가능한 증상 phrasing)
     next_docs: ≥ 3 (cause-side concept_id)

MISSION_BRIDGE (Woowa 미션 ↔ CS concept)
   Title: `{Mission} {기능} ↔ {CS concept} 브릿지`
   Body:
     ## 한 줄 요약
     ## 미션 시나리오 (학습자가 미션에서 마주치는 구체 상황)
     ## CS concept 매핑 (이 미션의 X가 일반 CS의 Y와 어떻게 닿는지)
     ## 미션 PR 코멘트 패턴 (자주 받는 리뷰 — 짧게)
     ## 다음 학습
   Frontmatter:
     doc_role: mission_bridge
     mission_ids: ≥ 1 (해당 미션 slug — `missions/roomescape` 등)
     review_feedback_tags: ≥ 1 (PR 코멘트 패턴 tag)

Hard rules (all roles):
  - Body Korean prose, 한 단락 ≤ 7줄.
  - 코드 dump 금지. SQL/Java 한두 줄 + 그 줄의 의미만.
  - 다른 doc 본문 베끼기 금지 — 새 각도 (정의 / 결정 / 증상 / 미션
    매핑) 로 다뤄야 가치 있음.
  - frontmatter 18 fields 모두 채워라 (Wave A 가이드 참조). Wave 2
    role-conditional 최소치 충족.
  - `contextual_chunk_prefix`는 빈 문자열로 두지 말고 같이 작성하라
    — 새 doc은 Wave A+B를 한 번에 끝낸다.
  - corpus_lint --strict --strict-v3가 에러 0으로 통과해야 한다.
  - concept_id 충돌 검증: 같은 concept_id를 가진 doc이 이미 있으면
    `canonical: false`로 설정.

What NOT to do:
  - DO NOT touch any other doc unless adding it to a `linked_paths`
    list. Cross-doc references stay one-way (link out from this new
    doc).
  - DO NOT add the doc to a category README — that is QA worker
    territory.

Output:
  - summary: "New {role} doc {filename}. concept_id={cid}, links: ..."
  - changed_files: ["knowledge/cs/contents/{category}/{slug}.md"]
  - next_candidates: 1-3 — the next sibling in the same gap (other
    missions / other confusable sets / other symptoms).
"""


def _worker_prompt(worker: str, lane: str, item: dict[str, Any], fleet_profile: str | None = None) -> str:
    profile = _profile_for_worker(worker, lane, fleet_profile)
    scope = _lane_prompt(lane)
    target_paths = _profile_list(profile, "target_paths") or [scope]
    write_scopes = _profile_list(profile, "write_scopes")
    claim_tags = _profile_list(profile, "claim_tags")
    quality_gates = _profile_list(profile, "quality_gates")
    mode = str(profile.get("mode", "write"))
    role = str(profile.get("role", "ad-hoc"))
    tags = ", ".join(item.get("tags", []))

    # Phase 8 migration profiles use a completely different prompt body
    # — the legacy expansion prompt pushes the *retrieval-anchor-keywords
    # + 7-element* legacy authoring contract, which directly contradicts
    # the v3 frontmatter (18 fields, contextual_chunk_prefix, no body
    # anchors) the migration is supposed to introduce.
    if mode in (
        "migrate_v0_to_v3",
        "migrate_prefix",
        "migrate_new_doc",
        "migrate_revisit",
    ):
        return _build_migration_v3_prompt(
            worker=worker, lane=lane, item=item, profile=profile,
            target_paths=target_paths, write_scopes=write_scopes,
            claim_tags=claim_tags, quality_gates=quality_gates,
            mode=mode, role=role, tags=tags,
        )
    balance_snapshot = _corpus_balance_snapshot()
    lowered_text = f"{item['title']} {item['goal']} {' '.join(item.get('tags', []))}".lower()
    beginner_rules = ""
    if any(
        term in lowered_text
        for term in ("beginner", "primer", "basics", "fundamentals", "overview", "입문", "기초", "기본")
    ):
        beginner_rules = """- This item targets beginner/junior readers.
- Prefer one entrypoint primer or bridge over a scattered advanced sweep.
- Start with a simple mental model before terminology.
- Use short comparison tables, concrete examples, and common-confusion bullets when useful.
- Keep advanced failure modes or operator edge cases as links, not as the center of the new doc.
"""
    qa_beginner_rules = ""
    if lane == "qa-bridge":
        qa_beginner_rules = """- Judge bridge quality through a beginner-first lens.
- Verify primers lead to one safe next-step doc before any deep-dive or incident doc.
- Prefer explicit primer -> follow-up -> deep-dive ladders over generic related-doc sprawl.
"""
    elif lane == "qa-anchor":
        qa_beginner_rules = """- Judge anchor quality through a beginner-first lens.
- Add beginner phrasing such as \"처음 배우는데\", \"큰 그림\", \"기초\", \"언제 쓰는지\" when it improves first-hit retrieval.
- Prefer anchors that make primer docs win on introductory prompts before deep dives.
"""
    elif lane == "qa-link":
        qa_beginner_rules = """- Judge link quality through a beginner-first lens.
- Verify each primer has a clear next-step link and an obvious return path to the category README.
- Prefer fixing misleading jumps into advanced docs over broad link cleanup.
"""
    elif lane == "qa-taxonomy":
        qa_beginner_rules = """- Judge taxonomy quality through a beginner-first lens.
- Make `primer`, `survey`, `deep dive`, `playbook`, and `recovery` roles explicit where they could be confused.
- Prefer label clarity and entrypoint safety over catalog completeness.
"""
    elif lane == "qa-retrieval":
        qa_beginner_rules = """- Judge retrieval quality through a beginner-first lens.
- Prefer primer docs over deep dives for introductory prompts.
- When possible, lock the behavior with golden fixtures, signal-rule assertions, or search regressions.
"""
    elif lane == "qa-content" or lane.startswith("qa-content-"):
        qa_beginner_rules = """- Judge the body itself through a beginner-first lens.
- Prefer plain-language mental models before jargon.
- Add one concrete example or a small comparison table when it clarifies the first read.
- Add or tighten common-confusion guidance when the doc still reads like a glossary.
- If the doc is marked Beginner, push advanced operator or incident-heavy detail behind related-doc links instead of centering it.
"""
    corpus_quality_rules = """Corpus quality contract:
- Treat the CS corpus as a sequenced learning system, not a collection of isolated articles.
- Every touched Beginner/Junior doc should answer a real learner question, give a compact mental model, show one concrete example or decision table, name common confusions, and point to one safe next step.
- Before adding a new doc, check for an existing near-duplicate in the target category. Strengthen the existing doc instead when that gives the learner a clearer path.
- Do not invent links or categories. Related-doc links must point to real files and should include at least one cross-category bridge when it helps the learning path.
- Retrieval anchors must include canonical terms and learner symptom phrases such as "처음", "헷갈", "왜", "언제", "뭐예요", "basics", or "what is" when relevant.
- Keep advanced incident, operations, and edge-case material behind follow-up links unless the task is explicitly advanced.
- If a doc is meant to win a RAG query, state the target query shape in the summary and make the title/anchors/body align with that query.
- Prevent misconceptions: qualify claims that depend on product/version/protocol/vendor behavior, separate "usually" from "guaranteed", and name the caveat or link to a deeper doc instead of making absolute statements.
- Use analogies only as entry ramps. State where the analogy stops being true before the learner could overgeneralize it.
"""
    corpus_balance_rules = """Corpus balance contract:
- Do not keep expanding Beginner docs blindly. Use the snapshot below to decide whether this item should create a Beginner entrypoint, an Intermediate application bridge, an Advanced deep dive, or a QA strengthening patch.
- If the target category is below the Beginner floor, prefer a clear entrypoint primer or symptom-to-concept bridge.
- If the target category is already Beginner-saturated, prefer Intermediate bridges, exercises, comparison cards, or strengthening existing docs unless the item explicitly requires a missing Beginner entrypoint.
- If the topic already has a Beginner primer but lacks a next step, create or improve an Intermediate bridge rather than another primer.
- Every new content item should declare its role in the summary: entrypoint primer, bridge, practice drill, deep dive, playbook, or recovery note.
- next_candidates should prioritize underrepresented category/difficulty pairs and include tags such as `balance-gap`, `intermediate`, `bridge`, or `advanced` when appropriate.
- Anti-drift rule: next_candidates from content workers must add a genuinely different angle from the current item and include at least one balance/quality tag such as `balance-gap`, `intermediate`, `bridge`, `practice`, `accuracy`, `misconception`, `cross-category`, or `retrieval`; otherwise the platform will not enqueue them.
"""
    if mode == "report":
        mode_rules = """- Report-only mode: do not edit knowledge content files.
- You may return changed_files as [] unless you intentionally write a small report under state/orchestrator/reports/.
- Focus on gaps, risks, coverage, and concrete next_candidates.
"""
    elif mode == "fix":
        mode_rules = """- Fix mode: repair existing quality debt; do not create new docs unless the item explicitly requires one.
- Prefer making a failing doc pass its authoring/retrieval contract over broad content expansion.
- For Beginner primer docs, prioritize: H1, `> 한 줄 요약`, exact difficulty, `관련 문서:` with >=3 bullets, 8..15 lowercase `retrieval-anchor-keywords`, <=1600 chars per H2, and final `## 한 줄 정리`.
- If you touch RAG ranking, run or update the narrow regression that proves the target query now behaves correctly.
"""
    elif mode == "script":
        mode_rules = """- Script-assisted mode: prefer deterministic checks or narrow mechanical fixes.
- Keep human-authored content edits minimal and directly tied to the detected issue.
"""
    elif mode == "ops":
        mode_rules = """- Ops mode: focus on queue health, release readiness, validation, and safe batching.
- Do not expand learner-facing content unless the task explicitly requires a release-blocking fix.
"""
    elif mode == "queue":
        mode_rules = """- Queue-governor mode: reduce duplicate or runaway candidates before adding more work.
- Prefer pruning, bucketing, or reporting over creating new documentation.
"""
    elif mode == "expand":
        mode_rules = """- Expansion mode: create or extend Beginner/Junior docs only when the claimed item calls for content growth.
- Treat learner-profile signals, Woowacourse Level 2/RoomEscape prerequisites, and RAG retrieval gaps as the source of truth for topic choice.
- New docs must follow `docs/cs-authoring-guide.md`, include symptom-style anchors, and be registered in the relevant category README when discoverability would otherwise be weak.
- If a category README is not listed in Target paths, do not edit it; report the needed registration in the summary or as a follow-up candidate for README QA.
- Avoid duplicating an existing primer; if a near-duplicate exists, strengthen that doc instead and explain the choice in the summary.
- Prefer 1 focused entrypoint doc plus precise bridge links over broad encyclopedia-style coverage.
"""
    else:
        mode_rules = """- Write mode: edit only the target paths listed in this profile.
- Do not edit README/index/taxonomy files unless the task specifically requires it and your write scopes cover it.
"""
    profile_block = "\n".join(
        [
            f"Worker profile:",
            f"- Role: {role}",
            f"- Mode: {mode}",
            f"- Target paths: {', '.join(target_paths)}",
            f"- Write scopes: {', '.join(write_scopes) if write_scopes else 'report-only/no direct write lock'}",
            f"- Claim tags: {', '.join(claim_tags) if claim_tags else 'none'}",
            f"- Quality gates: {', '.join(quality_gates) if quality_gates else 'none'}",
        ]
    )
    return f"""You are {worker}, the persistent lane worker for {lane}.

{profile_block}

Work only inside:
- {scope}

Task:
- Item ID: {item['item_id']}
- Title: {item['title']}
- Goal: {item['goal']}
- Tags: {tags}

Execution rules:
- Complete exactly one coherent wave for this item.
- Prefer repairing existing docs and tests over adding new content when this is a QA/RAG/Ops profile; content expansion profiles may create new docs when the claimed item requires it.
- Strengthen related-doc links and retrieval-anchor-keywords when directly relevant.
- Do not revert edits made by others.
- Keep changes scoped; do not drift into unrelated categories.
- If this is a QA lane, make the smallest high-value fixes that reduce the named quality debt.
- Platform completion gates run after your JSON response. Touched content docs under `knowledge/cs/contents/**` must pass `scripts/lint_cs_authoring.py`, and touched CS RAG code/tests/fixtures must pass the narrow related pytest target. Gate failures requeue this item.
- Report every modified path in `changed_files`; missing paths can hide a failing gate and will be treated as worker-quality debt.
{corpus_quality_rules}
{balance_snapshot}
{corpus_balance_rules}
{mode_rules}
{beginner_rules}{qa_beginner_rules}Output contract:
- Final response must be JSON only.
- Summary should mention the learner-facing quality improvement, especially for QA/RAG lanes.
- summary: short worker-completion summary
- changed_files: array of relative file paths you changed
- next_candidates: array with 1 to 3 concise follow-up gaps worth queueing next for the same lane
Always include next_candidates. Prefer concrete next gaps that avoid repeating the exact same work you just finished.
"""


def _run_codex_task(
    worker: str,
    lane: str,
    item: dict[str, Any],
    *,
    model: str,
    fleet_profile: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = _worker_prompt_path(worker)
    output_path = _worker_output_path(worker)
    schema_path = _ensure_worker_schema()
    prompt = _worker_prompt(worker, lane, item, fleet_profile)
    prompt_path.write_text(prompt, encoding="utf-8")
    if output_path.exists():
        output_path.unlink()
    started_at = _utc_now()
    env = os.environ.copy()
    env["CODEX_HOME"] = str(_prepare_worker_codex_home(worker))
    result = subprocess.run(
        [
            "codex",
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            "danger-full-access",
            "--dangerously-bypass-approvals-and-sandbox",
            "--model",
            model,
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            prompt,
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    log_text = (
        f"\n=== {item['item_id']} @ {_isoformat(started_at)} ===\n"
        f"PROMPT:\n{prompt}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n"
    )
    _append_log(_worker_log_path(worker), log_text)
    if result.returncode != 0:
        return {
            "ok": False,
            "summary": f"backend_failed: returncode={result.returncode}",
            "stderr": result.stderr[-1200:],
        }
    if not output_path.exists():
        return {"ok": False, "summary": "backend_failed: missing output schema file", "stderr": result.stderr[-1200:]}
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    return {"ok": True, **payload}


def _worker_status(worker: str) -> dict[str, Any]:
    return _load_json(_worker_status_path(worker), {"worker": worker})


def _write_worker_status(worker: str, payload: dict[str, Any]) -> None:
    _write_json(_worker_status_path(worker), payload)


def _update_fleet_status() -> None:
    lock_path = ensure_orchestrator_layout() / ".fleet-status.lock"
    lock_path.touch(exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        lock_exclusive(handle)
        try:
            fleet_profile = _active_fleet_profile()
            _write_json(
                _fleet_status_path(),
                {
                    "updated_at": _isoformat(_utc_now()),
                    "profile": fleet_profile,
                    "workers": _fleet_summary(fleet_profile),
                },
            )
        finally:
            unlock(handle)


def run_worker_loop(
    *,
    worker: str,
    lane: str,
    model: str,
    fleet_profile: str = DEFAULT_FLEET_PROFILE,
    idle_seconds: int = DEFAULT_WORKER_IDLE_SECONDS,
    lease_seconds: int = DEFAULT_WORKER_LEASE_SECONDS,
    timeout_seconds: int = DEFAULT_TASK_TIMEOUT_SECONDS,
) -> int:
    orchestrator = Orchestrator()
    fleet_profile = _normalize_fleet_profile(fleet_profile)
    _write_active_fleet_profile(fleet_profile)
    profile = _profile_for_worker(worker, lane, fleet_profile)
    write_scopes = _profile_list(profile, "write_scopes")
    claim_tags = _profile_list(profile, "claim_tags")
    refresh_backlog = bool(profile.get("can_enqueue", True))
    pending_cap = int(profile.get("pending_cap", DEFAULT_WORKER_PENDING_CAP))
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    _worker_pid_path(worker).write_text(str(pid), encoding="utf-8")
    orchestrator.release_worker_leases(
        worker,
        "worker_loop_restart",
        refresh_backlog=refresh_backlog,
        fleet_profile=fleet_profile,
    )
    status = _worker_status(worker)
    status.update(
        {
            "worker": worker,
            "lane": lane,
            "pid": pid,
            "status": "running",
            "started_at": status.get("started_at") or _isoformat(_utc_now()),
            "last_heartbeat_at": _isoformat(_utc_now()),
            "current_item_id": None,
            "last_error": None,
            "role": profile.get("role"),
            "mode": profile.get("mode"),
            "fleet_profile": fleet_profile,
            "write_scopes": write_scopes,
            "claim_tags": claim_tags,
        }
    )
    _write_worker_status(worker, status)
    _update_fleet_status()
    try:
        while True:
            now = _utc_now()
            status["last_heartbeat_at"] = _isoformat(now)
            if orchestrator.stop_path.exists():
                status["status"] = "stopping"
                _write_worker_status(worker, status)
                break
            if orchestrator.write_scope_has_foreign_lease(write_scopes, worker):
                status["status"] = "waiting_write_scope"
                _write_worker_status(worker, status)
                _update_fleet_status()
                time.sleep(idle_seconds)
                continue
            claimed = orchestrator.claim(
                worker=worker,
                lanes=[lane],
                limit=1,
                lease_seconds=lease_seconds,
                write_scopes=write_scopes,
                claim_tags=claim_tags,
                refresh_backlog=refresh_backlog,
                fleet_profile=fleet_profile,
            )
            if not claimed["claimed"]:
                status["status"] = "idle"
                status["current_item_id"] = None
                _write_worker_status(worker, status)
                _update_fleet_status()
                time.sleep(idle_seconds)
                continue
            item = claimed["claimed"][0]
            status["status"] = "working"
            status["current_item_id"] = item["item_id"]
            status["current_title"] = item["title"]
            _write_worker_status(worker, status)
            _update_fleet_status()
            task = _run_codex_task(
                worker,
                lane,
                item,
                model=model,
                fleet_profile=fleet_profile,
                timeout_seconds=timeout_seconds,
            )
            if task["ok"]:
                validation = _run_completion_gates(worker, lane, task)
                status["last_validation"] = validation
                if not validation["ok"]:
                    error_summary = validation.get("summary") or "completion gate failed"
                    orchestrator.requeue(item["item_id"], worker, error_summary, refresh_backlog=refresh_backlog)
                    status["last_error"] = error_summary
                    status["last_error_detail"] = validation
                    status["last_changed_files"] = validation.get("changed_files", [])
                    status["current_item_id"] = None
                    status["status"] = "running"
                    _write_worker_status(worker, status)
                    _update_fleet_status()
                    time.sleep(1)
                    continue
                summary = task.get("summary") or f"completed {item['item_id']}"
                orchestrator.complete(item["item_id"], worker, summary, refresh_backlog=refresh_backlog)
                next_candidates = task.get("next_candidates") or []
                valid_next_candidates: list[dict[str, Any]] = []
                if profile.get("can_enqueue", True) and isinstance(next_candidates, list) and next_candidates:
                    valid_next_candidates = _anti_drift_next_candidates(
                        item,
                        [candidate for candidate in next_candidates if isinstance(candidate, dict)],
                        profile,
                    )
                    orchestrator.enqueue_candidates(
                        lane,
                        valid_next_candidates,
                        source=f"worker-suggestion:{worker}",
                        fleet_profile=fleet_profile,
                        pending_cap=pending_cap,
                    )
                status["last_success_at"] = _isoformat(_utc_now())
                status["last_summary"] = summary
                status["last_changed_files"] = validation.get("changed_files", task.get("changed_files", []))
                status["last_next_candidates"] = next_candidates
                status["last_enqueued_next_candidates"] = valid_next_candidates if isinstance(next_candidates, list) else []
                status["last_error"] = None
            else:
                error_summary = task.get("summary") or "worker backend failed"
                orchestrator.requeue(item["item_id"], worker, error_summary, refresh_backlog=refresh_backlog)
                status["last_error"] = error_summary
                status["last_error_detail"] = task.get("stderr")
            status["current_item_id"] = None
            status["status"] = "running"
            _write_worker_status(worker, status)
            _update_fleet_status()
            time.sleep(1)
    finally:
        final_status = _worker_status(worker)
        final_status["status"] = "stopped"
        final_status["current_item_id"] = None
        final_status["last_heartbeat_at"] = _isoformat(_utc_now())
        _write_worker_status(worker, final_status)
        if _worker_pid_path(worker).exists():
            _worker_pid_path(worker).unlink()
        _update_fleet_status()
    return 0


def _start_worker_process(cli_script: Path, worker: str, lane: str, model: str, fleet_profile: str) -> int:
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    with _worker_log_path(worker).open("a", encoding="utf-8") as handle:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(cli_script),
                "orchestrator",
                "worker-loop",
                "--worker",
                worker,
                "--lane",
                lane,
                "--model",
                model,
                "--profile",
                fleet_profile,
            ],
            cwd=str(ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _worker_pid_path(worker).write_text(str(proc.pid), encoding="utf-8")
    status = _worker_status(worker)
    status.update(
        {
            "worker": worker,
            "lane": lane,
            "pid": proc.pid,
            "fleet_profile": fleet_profile,
            "status": "starting",
            "last_heartbeat_at": _isoformat(_utc_now()),
            "current_item_id": None,
        }
    )
    _write_worker_status(worker, status)
    return proc.pid


def run_supervisor_loop(
    *,
    cli_script: Path,
    model: str,
    fleet_profile: str = DEFAULT_FLEET_PROFILE,
    interval_seconds: int = DEFAULT_SUPERVISOR_INTERVAL_SECONDS,
) -> int:
    orchestrator = Orchestrator()
    fleet_profile = _normalize_fleet_profile(fleet_profile)
    supervisor_pid = os.getpid()
    _supervisor_pid_path().write_text(str(supervisor_pid), encoding="utf-8")
    _write_active_fleet_profile(fleet_profile, supervisor_pid=supervisor_pid)
    if _fleet_can_enqueue(fleet_profile):
        orchestrator.start_background(cli_script=cli_script, fleet_profile=fleet_profile)
    else:
        # Quality-repair fleets consume existing QA/RAG/Ops debt only. Starting the
        # backlog refresher here would keep generating expansion waves.
        orchestrator.clear_stop_request()
        orchestrator.run_once(low_water_mark=0, wave_size=0, refresh_backlog=False)
    try:
        while True:
            if orchestrator.stop_path.exists():
                break
            for spec in _fleet_for_profile(fleet_profile):
                worker = spec["name"]
                lane = spec["lane"]
                pid_path = _worker_pid_path(worker)
                pid = None
                if pid_path.exists():
                    try:
                        pid = int(pid_path.read_text(encoding="utf-8").strip())
                    except ValueError:
                        pid = None
                if not pid or not _pid_alive(pid):
                    _start_worker_process(cli_script, worker, lane, model, fleet_profile)
            _update_fleet_status()
            time.sleep(interval_seconds)
    finally:
        if _supervisor_pid_path().exists():
            _supervisor_pid_path().unlink()
        _update_fleet_status()
    return 0


def start_fleet_background(*, cli_script: Path, model: str, fleet_profile: str = DEFAULT_FLEET_PROFILE) -> dict[str, Any]:
    orchestrator = Orchestrator()
    fleet_profile = _normalize_fleet_profile(fleet_profile)
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    if supervisor_pid and _pid_alive(supervisor_pid):
        active_profile = _active_fleet_profile(fleet_profile)
        return {
            "already_running": True,
            "profile": active_profile,
            "requested_profile": fleet_profile,
            "supervisor_pid": supervisor_pid,
            "workers": _fleet_summary(active_profile),
        }
    ensure_orchestrator_layout()
    _write_active_fleet_profile(fleet_profile)
    with (ensure_orchestrator_layout() / "fleet-supervisor.log").open("a", encoding="utf-8") as handle:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(cli_script),
                "orchestrator",
                "supervisor-loop",
                "--model",
                model,
                "--profile",
                fleet_profile,
            ],
            cwd=str(ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _supervisor_pid_path().write_text(str(proc.pid), encoding="utf-8")
    _write_active_fleet_profile(fleet_profile, supervisor_pid=proc.pid)
    return {
        "already_running": False,
        "profile": fleet_profile,
        "supervisor_pid": proc.pid,
        "workers": _fleet_summary(fleet_profile),
    }


def fleet_status(fleet_profile: str | None = None) -> dict[str, Any]:
    active_profile = _active_fleet_profile()
    selected_profile = _normalize_fleet_profile(fleet_profile or active_profile)
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    return {
        "profile": selected_profile,
        "active_profile": active_profile,
        "supervisor": {"pid": supervisor_pid, "alive": bool(supervisor_pid and _pid_alive(supervisor_pid))},
        "workers": _fleet_summary(selected_profile),
    }


def stop_fleet(*, force: bool = False, fleet_profile: str | None = None) -> dict[str, Any]:
    orchestrator = Orchestrator()
    selected_profile = _normalize_fleet_profile(fleet_profile or _active_fleet_profile())
    orchestrator.request_stop(force=force)
    for spec in _fleet_for_profile(selected_profile):
        pid_path = _worker_pid_path(spec["name"])
        if not pid_path.exists():
            continue
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
        except ValueError:
            continue
        if _pid_alive(pid):
            os.kill(pid, signal.SIGTERM if force else signal.SIGTERM)
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    if supervisor_pid and _pid_alive(supervisor_pid):
        os.kill(supervisor_pid, signal.SIGTERM if force else signal.SIGTERM)
    return fleet_status(selected_profile)
