from __future__ import annotations

import json
import os
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
from .paths import ROOT, ensure_orchestrator_layout

DEFAULT_WORKER_IDLE_SECONDS = 15
DEFAULT_WORKER_LEASE_SECONDS = 45 * 60
DEFAULT_TASK_TIMEOUT_SECONDS = 45 * 60
DEFAULT_SUPERVISOR_INTERVAL_SECONDS = 20

DEFAULT_WORKER_PENDING_CAP = 80
DEFAULT_COMPLETION_GATE_TIMEOUT_SECONDS = 180

CONTENT_DOC_PREFIX = "knowledge/cs/contents/"
RAG_CODE_PREFIX = "scripts/learning/rag/"
CS_RAG_TEST_PREFIX = "tests/unit/test_cs_rag_"
CS_RAG_FIXTURE = "tests/fixtures/cs_rag_golden_queries.json"

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

WORKER_FLEET = QUALITY_REPAIR_FLEET

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


def _profile_for_worker(worker: str, lane: str) -> dict[str, Any]:
    for profile in [*WORKER_FLEET, *WORKER_PROFILES]:
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

    python = _project_python()
    commands: list[list[str]] = []
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


def _fleet_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for spec in WORKER_FLEET:
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


def _fleet_can_enqueue() -> bool:
    return any(spec.get("can_enqueue", True) for spec in WORKER_FLEET)


def _lane_prompt(lane: str) -> str:
    return LANE_SCOPE.get(lane, "knowledge/cs/**")


def _worker_prompt(worker: str, lane: str, item: dict[str, Any]) -> str:
    profile = _profile_for_worker(worker, lane)
    scope = _lane_prompt(lane)
    target_paths = _profile_list(profile, "target_paths") or [scope]
    write_scopes = _profile_list(profile, "write_scopes")
    claim_tags = _profile_list(profile, "claim_tags")
    quality_gates = _profile_list(profile, "quality_gates")
    mode = str(profile.get("mode", "write"))
    role = str(profile.get("role", "ad-hoc"))
    tags = ", ".join(item.get("tags", []))
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
- Prefer repairing existing docs and tests over adding new content when this is a QA/RAG/Ops profile.
- Strengthen related-doc links and retrieval-anchor-keywords when directly relevant.
- Do not revert edits made by others.
- Keep changes scoped; do not drift into unrelated categories.
- If this is a QA lane, make the smallest high-value fixes that reduce the named quality debt.
- Platform completion gates run after your JSON response. Touched content docs under `knowledge/cs/contents/**` must pass `scripts/lint_cs_authoring.py`, and touched CS RAG code/tests/fixtures must pass the narrow related pytest target. Gate failures requeue this item.
- Report every modified path in `changed_files`; missing paths can hide a failing gate and will be treated as worker-quality debt.
{mode_rules}
{beginner_rules}- Final response must be JSON only with:
- Summary should mention the beginner-facing quality improvement when this is a QA lane.
{qa_beginner_rules}- Final response must be JSON only with:
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
    timeout_seconds: int,
) -> dict[str, Any]:
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = _worker_prompt_path(worker)
    output_path = _worker_output_path(worker)
    schema_path = _ensure_worker_schema()
    prompt = _worker_prompt(worker, lane, item)
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
            _write_json(
                _fleet_status_path(),
                {"updated_at": _isoformat(_utc_now()), "workers": _fleet_summary()},
            )
        finally:
            unlock(handle)


def run_worker_loop(
    *,
    worker: str,
    lane: str,
    model: str,
    idle_seconds: int = DEFAULT_WORKER_IDLE_SECONDS,
    lease_seconds: int = DEFAULT_WORKER_LEASE_SECONDS,
    timeout_seconds: int = DEFAULT_TASK_TIMEOUT_SECONDS,
) -> int:
    orchestrator = Orchestrator()
    profile = _profile_for_worker(worker, lane)
    write_scopes = _profile_list(profile, "write_scopes")
    claim_tags = _profile_list(profile, "claim_tags")
    refresh_backlog = bool(profile.get("can_enqueue", True))
    pending_cap = int(profile.get("pending_cap", DEFAULT_WORKER_PENDING_CAP))
    worker_dir = _worker_dir(worker)
    worker_dir.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    _worker_pid_path(worker).write_text(str(pid), encoding="utf-8")
    orchestrator.release_worker_leases(worker, "worker_loop_restart", refresh_backlog=refresh_backlog)
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
            task = _run_codex_task(worker, lane, item, model=model, timeout_seconds=timeout_seconds)
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
                if profile.get("can_enqueue", True) and isinstance(next_candidates, list) and next_candidates:
                    orchestrator.enqueue_candidates(
                        lane,
                        [candidate for candidate in next_candidates if isinstance(candidate, dict)],
                        source=f"worker-suggestion:{worker}",
                        pending_cap=pending_cap,
                    )
                status["last_success_at"] = _isoformat(_utc_now())
                status["last_summary"] = summary
                status["last_changed_files"] = validation.get("changed_files", task.get("changed_files", []))
                status["last_next_candidates"] = next_candidates
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


def _start_worker_process(cli_script: Path, worker: str, lane: str, model: str) -> int:
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
    interval_seconds: int = DEFAULT_SUPERVISOR_INTERVAL_SECONDS,
) -> int:
    orchestrator = Orchestrator()
    supervisor_pid = os.getpid()
    _supervisor_pid_path().write_text(str(supervisor_pid), encoding="utf-8")
    if _fleet_can_enqueue():
        orchestrator.start_background(cli_script=cli_script)
    else:
        # Quality-repair fleets consume existing QA/RAG/Ops debt only. Starting the
        # backlog refresher here would keep generating expansion waves.
        orchestrator.clear_stop_request()
        orchestrator.run_once(low_water_mark=0, wave_size=0, refresh_backlog=False)
    try:
        while True:
            if orchestrator.stop_path.exists():
                break
            for spec in WORKER_FLEET:
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
                    _start_worker_process(cli_script, worker, lane, model)
            _update_fleet_status()
            time.sleep(interval_seconds)
    finally:
        if _supervisor_pid_path().exists():
            _supervisor_pid_path().unlink()
        _update_fleet_status()
    return 0


def start_fleet_background(*, cli_script: Path, model: str) -> dict[str, Any]:
    orchestrator = Orchestrator()
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    if supervisor_pid and _pid_alive(supervisor_pid):
        return {"already_running": True, "supervisor_pid": supervisor_pid, "workers": _fleet_summary()}
    ensure_orchestrator_layout()
    with (ensure_orchestrator_layout() / "fleet-supervisor.log").open("a", encoding="utf-8") as handle:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(cli_script),
                "orchestrator",
                "supervisor-loop",
                "--model",
                model,
            ],
            cwd=str(ROOT),
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _supervisor_pid_path().write_text(str(proc.pid), encoding="utf-8")
    return {"already_running": False, "supervisor_pid": proc.pid, "workers": _fleet_summary()}


def fleet_status() -> dict[str, Any]:
    supervisor_pid = None
    if _supervisor_pid_path().exists():
        try:
            supervisor_pid = int(_supervisor_pid_path().read_text(encoding="utf-8").strip())
        except ValueError:
            supervisor_pid = None
    return {
        "supervisor": {"pid": supervisor_pid, "alive": bool(supervisor_pid and _pid_alive(supervisor_pid))},
        "workers": _fleet_summary(),
    }


def stop_fleet(*, force: bool = False) -> dict[str, Any]:
    orchestrator = Orchestrator()
    orchestrator.request_stop(force=force)
    for spec in WORKER_FLEET:
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
    return fleet_status()
