from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import fcntl
import re
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .paths import ROOT, ensure_global_layout, ensure_orchestrator_layout

DEFAULT_LOOP_INTERVAL_SECONDS = 45
DEFAULT_LEASE_SECONDS = 30 * 60
DEFAULT_LOW_WATER_MARK = 2
DEFAULT_WAVE_SIZE = 6
RECENT_COMPLETION_WINDOW = 8
QUEUE_PENDING = "pending"
QUEUE_LEASED = "leased"
QUEUE_COMPLETED = "completed"
QUEUE_BLOCKED = "blocked"
KNOWLEDGE_CONTENTS_DIR = ROOT / "knowledge" / "cs" / "contents"

BEGINNER_SIGNAL_TAGS = {
    "beginner",
    "junior",
    "primer",
    "basics",
    "fundamentals",
    "overview",
    "intro",
}
BEGINNER_SIGNAL_TERMS = (
    "beginner",
    "junior",
    "primer",
    "basics",
    "fundamentals",
    "foundation",
    "foundations",
    "overview",
    "intro",
    "entry-level",
    "입문",
    "기초",
    "기본",
    "처음 배우",
    "큰 그림",
)
BEGINNER_FOUNDATION_TERMS = (
    "basics",
    "fundamentals",
    "foundation",
    "foundations",
    "primer",
    "overview",
    "입문",
    "기초",
    "기본",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+cycle\s+\d+$", "", title).strip().lower()


def _relative_to_contents(path: Path) -> str:
    try:
        return str(path.relative_to(KNOWLEDGE_CONTENTS_DIR))
    except ValueError:
        return str(path.relative_to(ROOT))


def _extract_markdown_links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def _text_has_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def _is_beginner_focused(title: str, goal: str, tags: list[str]) -> bool:
    normalized_tags = {tag.strip().lower() for tag in tags if tag}
    if normalized_tags & BEGINNER_SIGNAL_TAGS:
        return True
    return _text_has_any(title, BEGINNER_SIGNAL_TERMS) or _text_has_any(goal, BEGINNER_SIGNAL_TERMS)


def _is_foundation_focused(title: str, goal: str, tags: list[str]) -> bool:
    normalized_tags = {tag.strip().lower() for tag in tags if tag}
    if normalized_tags & BEGINNER_SIGNAL_TAGS and (
        "beginner" in normalized_tags
        or "primer" in normalized_tags
        or "basics" in normalized_tags
        or "fundamentals" in normalized_tags
        or "overview" in normalized_tags
    ):
        return True
    return _text_has_any(title, BEGINNER_FOUNDATION_TERMS) or _text_has_any(goal, BEGINNER_FOUNDATION_TERMS)


def _normalize_candidate_tags(title: str, goal: str, tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = tag.strip().lower()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    if _is_beginner_focused(title, goal, normalized):
        for tag in ("beginner", "primer"):
            if tag not in seen:
                normalized.append(tag)
                seen.add(tag)
    return normalized


def _matches_claim_tags(item: dict[str, Any], claim_tags: list[str] | None) -> bool:
    if not claim_tags:
        return True
    haystack = " ".join(
        [
            str(item.get("title", "")),
            str(item.get("goal", "")),
            " ".join(str(tag) for tag in item.get("tags", [])),
            str(item.get("base_title", "")),
            str(item.get("lane", "")),
        ]
    ).lower()
    return any(str(tag).strip().lower() in haystack for tag in claim_tags if str(tag).strip())


def _lease_write_scopes(item: dict[str, Any]) -> set[str]:
    raw_scopes = item.get("lease_write_scopes") or item.get("write_scopes") or []
    return {str(scope).strip() for scope in raw_scopes if str(scope).strip()}


def _priority_with_beginner_bias(base_priority: int, title: str, goal: str, tags: list[str], *, source: str) -> int:
    priority = int(base_priority)
    if _is_beginner_focused(title, goal, tags):
        priority += 2
    if _is_foundation_focused(title, goal, tags):
        priority += 1
    if source.startswith("worker-suggestion") and _is_beginner_focused(title, goal, tags):
        priority += 1
    return priority


def _is_beginner_quality_task(lane: str, title: str, goal: str, tags: list[str]) -> bool:
    if not lane.startswith("qa-"):
        return False
    if _is_beginner_focused(title, goal, tags):
        return True
    return _text_has_any(
        f"{title} {goal}",
        (
            "learning path",
            "next-step",
            "next step",
            "entrypoint",
            "entry point",
            "primer",
            "survey",
            "deep dive",
            "first-hit",
            "first hit",
            "junior",
            "beginner",
            "입문",
            "기초",
            "큰 그림",
        ),
    )


def _qa_content_prefixes_for_lane(lane: str) -> tuple[str, ...] | None:
    if lane == "qa-content":
        return None
    config = QA_CONTENT_CATEGORY_LANES.get(lane)
    if config is None:
        return None
    return tuple(config["prefixes"])


def _live_lane_items(items: list[dict[str, Any]], lane: str) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if item["lane"] == lane and item["status"] in {QUEUE_PENDING, QUEUE_LEASED}
    ]


def _has_live_beginner_item(items: list[dict[str, Any]], lane: str) -> bool:
    return any(
        _is_beginner_focused(
            item.get("base_title") or item["title"],
            item["goal"],
            list(item.get("tags", [])),
        )
        for item in _live_lane_items(items, lane)
    )


def _lane_has_beginner_template(lane: str) -> bool:
    return any(
        _is_beginner_focused(
            template["title"],
            template["goal"],
            list(template.get("tags", [])),
        )
        for template in LANE_CATALOG[lane]["templates"]
    )


LANE_CATALOG: dict[str, dict[str, Any]] = {
    "database": {
        "kind": "content",
        "priority": 95,
        "templates": [
            {
                "title": "Transaction basics and ACID foundations",
                "goal": "Strengthen beginner-facing explanations of transactions, ACID, isolation levels, dirty/non-repeatable/phantom reads, and when locking is needed.",
                "tags": ["transaction", "acid", "isolation", "locking", "beginner"],
            },
            {
                "title": "Index and execution-plan basics",
                "goal": "Expand entry-level material for B-Tree indexes, clustered vs secondary indexes, covering indexes, EXPLAIN reading, and common query-plan mistakes.",
                "tags": ["index", "explain", "btree", "query-plan", "beginner"],
            },
            {
                "title": "Schema design basics and key choices",
                "goal": "Fill gaps around primary keys, foreign keys, normalization vs denormalization, unique constraints, pagination fundamentals, and modeling trade-offs for juniors.",
                "tags": ["schema-design", "primary-key", "foreign-key", "normalization", "beginner"],
            },
            {
                "title": "Replication, MVCC, and stale-read intuition",
                "goal": "Explain MVCC, replica lag, read-after-write, and sharding/partitioning at a foundation level before the deeper operational docs.",
                "tags": ["mvcc", "replication", "stale-read", "sharding", "beginner"],
            },
            {
                "title": "SQL and join fundamentals",
                "goal": "Improve beginner explanations for joins, grouping, filtering order, and practical SQL reading before advanced engine-specific tuning topics.",
                "tags": ["sql", "join", "group-by", "query-order", "beginner"],
            },
        ],
    },
    "security": {
        "kind": "content",
        "priority": 94,
        "templates": [
            {
                "title": "Authentication vs authorization foundations",
                "goal": "Strengthen beginner-friendly explanations of authentication, authorization, principal, session, and permission modeling.",
                "tags": ["authentication", "authorization", "session", "permission", "beginner"],
            },
            {
                "title": "JWT, cookie, session, and BFF basics",
                "goal": "Build clearer entry-level guidance for JWT vs cookie vs server session vs BFF boundaries, including storage and logout intuition.",
                "tags": ["jwt", "cookie", "session", "bff", "beginner"],
            },
            {
                "title": "Web security essentials",
                "goal": "Expand the basic layer for HTTPS, CSRF, XSS, CORS, password hashing, API key signing, and secret management fundamentals.",
                "tags": ["https", "csrf", "xss", "cors", "password", "beginner"],
            },
            {
                "title": "Identity lifecycle and provisioning basics",
                "goal": "Make SCIM, account disable, role mapping drift, session revocation, and operator tooling easier for juniors to connect end-to-end.",
                "tags": ["identity-lifecycle", "scim", "revocation", "roles", "beginner"],
            },
        ],
    },
    "network": {
        "kind": "content",
        "priority": 93,
        "templates": [
            {
                "title": "HTTP request-response basics",
                "goal": "Strengthen beginner docs for URL -> DNS -> TCP/TLS -> HTTP request/response flow, status codes, keep-alive, and browser-server basics.",
                "tags": ["http", "dns", "tcp", "tls", "status-code", "beginner"],
            },
            {
                "title": "Timeout, retry, and idempotency basics",
                "goal": "Make timeout types, retry safety, backoff, circuit breaker, and idempotency easier to learn from first principles.",
                "tags": ["timeout", "retry", "backoff", "idempotency", "beginner"],
            },
            {
                "title": "Protocol comparison foundations",
                "goal": "Expand beginner comparisons for REST, WebSocket, SSE, gRPC, HTTP/2, and HTTP/3 so transport choices are easier to explain.",
                "tags": ["rest", "websocket", "sse", "grpc", "http2", "http3", "beginner"],
            },
            {
                "title": "Caching, CDN, and load balancer basics",
                "goal": "Clarify cache headers, CDN behavior, proxy/load-balancer roles, and common stale-data or timeout symptoms for juniors.",
                "tags": ["cache", "cdn", "load-balancer", "proxy", "beginner"],
            },
        ],
    },
    "system-design": {
        "kind": "content",
        "priority": 92,
        "templates": [
            {
                "title": "System design foundations",
                "goal": "Build stronger beginner docs for scale basics: load balancer, cache, database, queue, stateless app, and horizontal scaling intuition.",
                "tags": ["load-balancer", "cache", "queue", "database", "scaling", "beginner"],
            },
            {
                "title": "Consistency and messaging basics",
                "goal": "Improve foundation docs for sync vs async, idempotency, eventual consistency, outbox, and retry-safe message handling.",
                "tags": ["consistency", "messaging", "outbox", "idempotency", "beginner"],
            },
            {
                "title": "Availability and failover intuition",
                "goal": "Make failover, redundancy, health check, quorum, and blast-radius basics easier to understand before advanced control-plane docs.",
                "tags": ["availability", "failover", "health-check", "quorum", "beginner"],
            },
            {
                "title": "Data pipeline and analytics foundations",
                "goal": "Clarify basic event pipeline, replay, late data, and dashboard consistency concepts before advanced reconciliation UX topics.",
                "tags": ["pipeline", "analytics", "late-data", "replay", "beginner"],
            },
        ],
    },
    "operating-system": {
        "kind": "content",
        "priority": 91,
        "templates": [
            {
                "title": "Process, thread, and memory basics",
                "goal": "Strengthen foundation docs for process vs thread, virtual memory, stack vs heap, context switch, and scheduler basics.",
                "tags": ["process", "thread", "memory", "context-switch", "scheduler", "beginner"],
            },
            {
                "title": "I/O model and event loop basics",
                "goal": "Improve beginner-facing explanations of blocking/non-blocking, sync/async, event loop, epoll, and backpressure.",
                "tags": ["io-model", "event-loop", "epoll", "backpressure", "beginner"],
            },
            {
                "title": "File system and persistence basics",
                "goal": "Clarify page cache, fsync, mmap, rename, crash consistency, and file descriptor basics before advanced writeback topics.",
                "tags": ["filesystem", "page-cache", "fsync", "mmap", "fd", "beginner"],
            },
            {
                "title": "Network and kernel path basics",
                "goal": "Strengthen intuition for socket, syscall, accept queue, interrupt, softirq, and kernel-user boundary concepts.",
                "tags": ["socket", "syscall", "accept-queue", "interrupt", "kernel", "beginner"],
            },
        ],
    },
    "spring": {
        "kind": "content",
        "priority": 90,
        "templates": [
            {
                "title": "Spring bean and DI basics",
                "goal": "Strengthen beginner docs for bean lifecycle, DI, component scan, configuration, and proxy intuition.",
                "tags": ["spring", "bean", "di", "configuration", "beginner"],
            },
            {
                "title": "Spring MVC request lifecycle basics",
                "goal": "Improve entry-level explanations of DispatcherServlet, filter/interceptor/controller flow, binding, and exception handling.",
                "tags": ["spring-mvc", "dispatcher-servlet", "filter", "controller", "beginner"],
            },
            {
                "title": "Spring transaction and persistence basics",
                "goal": "Make @Transactional, transaction propagation, JPA persistence context, flush/clear, and repository basics easier for juniors.",
                "tags": ["transactional", "jpa", "persistence-context", "repository", "beginner"],
            },
            {
                "title": "Spring security and web basics",
                "goal": "Expand basic understanding of security filter chain, session policy, request cache, login/logout, and API vs browser differences.",
                "tags": ["spring-security", "filter-chain", "session", "login", "beginner"],
            },
        ],
    },
    "design-pattern": {
        "kind": "content",
        "priority": 89,
        "templates": [
            {
                "title": "Object-oriented design pattern basics",
                "goal": "Strengthen beginner-facing docs for strategy, template method, factory, builder, observer, and when to use each.",
                "tags": ["strategy", "template-method", "factory", "builder", "observer", "beginner"],
            },
            {
                "title": "Layering and boundary basics",
                "goal": "Clarify repository vs DAO, service vs domain model, command vs query separation, and layering fundamentals for juniors.",
                "tags": ["repository", "dao", "service", "command-query", "boundary", "beginner"],
            },
            {
                "title": "Event, queue, and workflow pattern basics",
                "goal": "Build a simpler bridge into event-driven patterns, outbox, saga/process manager, and read-model basics before advanced cutover docs.",
                "tags": ["event", "outbox", "saga", "workflow", "read-model", "beginner"],
            },
            {
                "title": "Testing and refactoring pattern basics",
                "goal": "Expand pattern-level guidance for seams, dependency inversion, null object, specification, and refactoring-friendly design.",
                "tags": ["testing", "refactoring", "dependency-inversion", "specification", "beginner"],
            },
        ],
    },
    "software-engineering": {
        "kind": "content",
        "priority": 88,
        "templates": [
            {
                "title": "Architecture and layering fundamentals",
                "goal": "Strengthen beginner docs for clean architecture, layered architecture, modular monolith, DDD boundaries, and repository/entity separation.",
                "tags": ["architecture", "layering", "modular-monolith", "ddd", "beginner"],
            },
            {
                "title": "Testing strategy fundamentals",
                "goal": "Expand the basic layer for unit/integration/e2e tests, test doubles, test slice choices, and feedback loops for juniors.",
                "tags": ["testing", "unit-test", "integration-test", "e2e", "beginner"],
            },
            {
                "title": "Deployment and rollout basics",
                "goal": "Clarify blue-green, canary, rollback, feature flags, and release safety at an introductory level before governance-heavy docs.",
                "tags": ["deployment", "rollback", "canary", "feature-flag", "beginner"],
            },
            {
                "title": "Observability and incident basics",
                "goal": "Make logs, metrics, tracing, SLI/SLO, error budget, and incident review basics easier to learn before advanced governance topics.",
                "tags": ["observability", "logging", "metrics", "sli", "incident", "beginner"],
            },
        ],
    },
    "language-java": {
        "kind": "content",
        "priority": 87,
        "templates": [
            {
                "title": "Java language and OOP fundamentals",
                "goal": "Strengthen beginner material for Java syntax, primitive/reference types, classes, objects, interfaces, abstract classes, and core OOP principles.",
                "tags": ["java-basics", "oop", "class", "interface", "beginner"],
            },
            {
                "title": "Collections and equality fundamentals",
                "goal": "Clarify Collection hierarchy, HashMap/List/Set basics, equals/hashCode/Comparable, and common beginner pitfalls.",
                "tags": ["collections", "hashmap", "list", "set", "equals-hashcode", "beginner"],
            },
            {
                "title": "Exception, I/O, and serialization basics",
                "goal": "Expand checked vs unchecked exceptions, stream I/O, serialization, and common API pitfalls from a junior perspective.",
                "tags": ["exception", "io", "serialization", "beginner"],
            },
            {
                "title": "Java concurrency foundations",
                "goal": "Improve foundation docs for threads, synchronized, volatile, executor basics, CompletableFuture basics, and memory model intuition.",
                "tags": ["thread", "synchronized", "volatile", "executor", "memory-model", "beginner"],
            },
        ],
    },
    "data-structure": {
        "kind": "content",
        "priority": 86,
        "templates": [
            {
                "title": "Core data-structure basics",
                "goal": "Strengthen beginner docs for array, linked list, stack, queue, hash table, heap, tree, graph, and union-find basics.",
                "tags": ["array", "linked-list", "stack", "queue", "heap", "tree", "graph", "beginner"],
            },
            {
                "title": "Algorithm pattern foundations",
                "goal": "Use the data-structure lane to also strengthen core algorithm primers: sorting, binary search, BFS/DFS, greedy, DP, shortest path basics.",
                "tags": ["algorithm", "sorting", "binary-search", "bfs", "dfs", "greedy", "dp", "beginner"],
            },
            {
                "title": "Practical structure choice basics",
                "goal": "Clarify when to choose map vs set vs queue vs priority queue vs trie vs bitmap from a junior engineer's point of view.",
                "tags": ["selection", "map", "set", "priority-queue", "trie", "bitmap", "beginner"],
            },
        ],
    },
    "qa-bridge": {
        "kind": "quality",
        "priority": 84,
        "templates": [
            {
                "title": "Beginner bridge debt",
                "goal": "Scan and reduce missing beginner bridges between primer docs, follow-up docs, and deeper docs so juniors can climb from basics to advanced material without jumping straight into advanced incident or operator-only material.",
                "tags": ["qa", "bridge", "beginner", "learning-path", "next-step", "entrypoint"],
            }
        ],
    },
    "qa-anchor": {
        "kind": "quality",
        "priority": 83,
        "templates": [
            {
                "title": "Primer anchor coverage",
                "goal": "Find beginner and primer docs with weak anchors, add beginner-phrased retrieval-anchor-keywords, and make first-question concept queries land on primers instead of deep dives.",
                "tags": ["qa", "anchor", "primer", "beginner", "retrieval", "first-hit"],
            }
        ],
    },
    "qa-link": {
        "kind": "quality",
        "priority": 82,
        "templates": [
            {
                "title": "Primer reverse-link hygiene",
                "goal": "Keep broken links at zero and strengthen reverse links from primers and READMEs into the right next-step docs, while also preserving a safe return path back to the category navigator for junior readers.",
                "tags": ["qa", "link", "primer", "reverse-link", "readme", "next-step"],
            }
        ],
    },
    "qa-taxonomy": {
        "kind": "quality",
        "priority": 81,
        "templates": [
            {
                "title": "Beginner taxonomy clarity",
                "goal": "Reduce primer/survey/deep-dive/playbook mixing in README and navigator docs so junior readers can see the intended learning path clearly and do not mistake advanced incident docs for entrypoints.",
                "tags": ["qa", "taxonomy", "beginner", "readme", "navigation", "labels"],
            }
        ],
    },
    "qa-retrieval": {
        "kind": "quality",
        "priority": 80,
        "templates": [
            {
                "title": "Beginner query retrieval stabilization",
                "goal": "Stabilize beginner/basic concept queries so primer docs win over deep dives when the question is introductory, and lock the behavior with golden fixtures or signal/search regressions.",
                "tags": ["qa", "retrieval", "beginner", "golden", "signal-rules", "first-hit"],
            }
        ],
    },
    "qa-content": {
        "kind": "quality",
        "priority": 79,
        "templates": [
            {
                "title": "Beginner content clarity pass",
                "goal": "Audit beginner or primer docs for missing mental model, weak examples, dense terminology, and unclear next-step links so entry docs read like teaching guides instead of glossaries.",
                "tags": ["qa", "content", "beginner", "clarity", "rubric"],
            },
            {
                "title": "Common confusion and example pass",
                "goal": "Strengthen beginner docs that explain terms but still need one concrete example, one compact comparison table, or one common-confusion section.",
                "tags": ["qa", "content", "beginner", "examples", "confusion"],
            },
            {
                "title": "Beginner scope creep cleanup",
                "goal": "Trim advanced operator or incident-heavy digressions from docs marked Beginner and push those branches behind related-doc links or deeper follow-up docs.",
                "tags": ["qa", "content", "beginner", "scope", "next-step"],
            },
        ],
    },
}

QA_CONTENT_CATEGORY_LANES: dict[str, dict[str, Any]] = {
    "qa-content-database": {
        "label": "database",
        "prefixes": ("database/",),
        "scope_hint": "database primers, transaction/JDBC/JPA entrypoints, and README routing",
    },
    "qa-content-security": {
        "label": "security",
        "prefixes": ("security/",),
        "scope_hint": "security primers, auth/session/cookie/JWT/web-security entrypoints, and README routing",
    },
    "qa-content-network": {
        "label": "network",
        "prefixes": ("network/",),
        "scope_hint": "network primers, HTTP/browser/request lifecycle/caching entrypoints, and README routing",
    },
    "qa-content-system-design": {
        "label": "system-design",
        "prefixes": ("system-design/",),
        "scope_hint": "system design foundations, consistency/cache/queue starter docs, and README routing",
    },
    "qa-content-operating-system": {
        "label": "operating-system",
        "prefixes": ("operating-system/",),
        "scope_hint": "OS primers for backend runtime/process/thread/I-O basics and README routing",
    },
    "qa-content-spring": {
        "label": "spring",
        "prefixes": ("spring/",),
        "scope_hint": "Spring beginner docs for MVC/DI/transaction/request pipeline and README routing",
    },
    "qa-content-design-pattern": {
        "label": "design-pattern",
        "prefixes": ("design-pattern/",),
        "scope_hint": "design-pattern beginner docs for naming, strategy/factory/registry boundaries, and README routing",
    },
    "qa-content-software-engineering": {
        "label": "software-engineering",
        "prefixes": ("software-engineering/",),
        "scope_hint": "software-engineering primers for layering/testing/readability and README routing",
    },
    "qa-content-language-java": {
        "label": "language-java",
        "prefixes": ("language/java/",),
        "scope_hint": "Java beginner docs for execution/object model/collections/equality and language README routing",
    },
    "qa-content-data-structure": {
        "label": "data-structure",
        "prefixes": ("data-structure/", "algorithm/"),
        "scope_hint": "data-structure and algorithm entrypoint primers used by backend juniors, plus README routing",
    },
}

for lane, config in QA_CONTENT_CATEGORY_LANES.items():
    label = config["label"]
    scope_hint = config["scope_hint"]
    LANE_CATALOG[lane] = {
        "kind": "quality",
        "priority": 79,
        "templates": [
            {
                "title": f"{label} beginner content clarity pass",
                "goal": f"Audit {scope_hint} for missing mental model, weak examples, dense terminology, and unclear next-step links so entry docs read like teaching guides instead of glossaries.",
                "tags": ["qa", "content", "beginner", "clarity", label],
            },
            {
                "title": f"{label} common confusion and example pass",
                "goal": f"Strengthen {scope_hint} where beginner docs still need one concrete example, one compact comparison table, or one common-confusion section.",
                "tags": ["qa", "content", "beginner", "examples", "confusion", label],
            },
            {
                "title": f"{label} beginner scope creep cleanup",
                "goal": f"Trim advanced operator or incident-heavy digressions from {scope_hint} and push those branches behind related-doc links or deeper follow-up docs.",
                "tags": ["qa", "content", "beginner", "scope", "next-step", label],
            },
        ],
    }

WOOWA_BACKEND_CURRICULUM_BACKLOG: dict[str, list[dict[str, Any]]] = {
    "language-java": [
        {
            "title": "Java execution model and object mental model",
            "goal": "Build a beginner-first entrypoint for source -> bytecode -> JVM execution, class vs object vs instance, static vs instance, and stack/heap intuition for Woowacourse backend learners.",
            "tags": ["java", "jvm", "object-model", "beginner", "primer", "woowacourse-backend"],
        },
        {
            "title": "Collections, equality, and mutable-state foundations",
            "goal": "Strengthen the first-read layer for List/Set/Map choice, equals/hashCode/Comparable, mutable key pitfalls, and collection iteration/update trade-offs in Java mission code.",
            "tags": ["java", "collections", "equals-hashcode", "mutable-state", "beginner", "woowacourse-backend"],
        },
    ],
    "data-structure": [
        {
            "title": "Backend data-structure starter pack",
            "goal": "Clarify the practical choice among array/list/map/set/queue/priority queue/trie from backend scenarios such as lookup, dedupe, ordering, FIFO handoff, and top-k selection.",
            "tags": ["data-structure", "selection", "map", "queue", "priority-queue", "beginner", "woowacourse-backend"],
        },
        {
            "title": "Complexity and algorithm pattern foundations for backend juniors",
            "goal": "Tighten the beginner layer for Big-O, sorting, binary search, BFS/DFS, and the small set of algorithm patterns that repeatedly appear in Woowacourse mission problem solving.",
            "tags": ["algorithm", "complexity", "sorting", "binary-search", "bfs", "dfs", "beginner", "woowacourse-backend"],
        },
    ],
    "network": [
        {
            "title": "Browser to server request lifecycle foundations",
            "goal": "Strengthen the beginner explanation of URL -> DNS -> TCP/TLS -> HTTP request/response, cookies, sessions, status codes, and proxies so backend learners can read web traffic before building Spring apps.",
            "tags": ["network", "http", "dns", "tcp", "tls", "cookie", "session", "beginner", "woowacourse-backend"],
        },
        {
            "title": "HTTP semantics and caching first principles",
            "goal": "Clarify HTTP methods, safety/idempotency, cache-control, conditional requests, CDN/reverse-proxy roles, and the basic difference between browser cache and server-side caching.",
            "tags": ["network", "http", "cache", "idempotency", "cdn", "beginner", "woowacourse-backend"],
        },
    ],
    "operating-system": [
        {
            "title": "Process, thread, memory, and file descriptor foundations",
            "goal": "Build a beginner-first mental model for process vs thread, stack vs heap, file descriptor, socket, and why backend servers care about these boundaries.",
            "tags": ["os", "process", "thread", "memory", "file-descriptor", "socket", "beginner", "woowacourse-backend"],
        },
        {
            "title": "Blocking I/O, thread pool, and backpressure foundations",
            "goal": "Explain blocking vs non-blocking I/O, request-per-thread intuition, thread pool role, queue saturation, and backpressure at the level needed for java-http and server-side troubleshooting.",
            "tags": ["os", "io-model", "thread-pool", "backpressure", "beginner", "woowacourse-backend"],
        },
    ],
    "database": [
        {
            "title": "SQL reading and relational modeling foundations",
            "goal": "Strengthen the beginner layer for SELECT/JOIN/GROUP BY reading, primary/foreign key modeling, cardinality, and normalization trade-offs that appear in early backend missions.",
            "tags": ["database", "sql", "join", "modeling", "primary-key", "foreign-key", "beginner", "woowacourse-backend"],
        },
        {
            "title": "Transactions, locks, and connection pool foundations",
            "goal": "Build a first-read explanation for transaction boundaries, isolation, locking vs uniqueness, deadlock intuition, and why a connection pool exists before deeper JDBC and JPA material.",
            "tags": ["database", "transaction", "locking", "connection-pool", "isolation", "beginner", "woowacourse-backend"],
        },
    ],
    "spring": [
        {
            "title": "Spring request pipeline and bean container foundations",
            "goal": "Create or strengthen beginner entrypoints for DispatcherServlet, controller/service/repository roles, bean registration, DI, component scan, and configuration reading in Spring missions.",
            "tags": ["spring", "dispatcher-servlet", "bean", "di", "component-scan", "beginner", "woowacourse-backend"],
        },
        {
            "title": "Spring persistence and transaction mental model",
            "goal": "Clarify @Transactional, persistence context, flush, lazy loading, and transaction boundaries across web/service/repository layers for backend juniors.",
            "tags": ["spring", "transactional", "jpa", "persistence-context", "beginner", "woowacourse-backend"],
        },
    ],
    "security": [
        {
            "title": "Authentication, authorization, and session foundations",
            "goal": "Strengthen the basic layer for authentication vs authorization, session/cookie/JWT/BFF boundaries, login/logout, and permission checks in browser and API flows.",
            "tags": ["security", "authentication", "authorization", "session", "jwt", "bff", "beginner", "woowacourse-backend"],
        },
        {
            "title": "Web security starter pack for backend juniors",
            "goal": "Improve beginner entry docs for HTTPS, password hashing, CSRF, XSS, CORS, and secret/config handling so web-security basics are in place before Spring Security deep dives.",
            "tags": ["security", "https", "csrf", "xss", "cors", "password", "beginner", "woowacourse-backend"],
        },
    ],
    "software-engineering": [
        {
            "title": "Readable code, layering, and test feedback loop",
            "goal": "Strengthen beginner material for readable code, separation of concerns, unit vs integration testing, and the refactor-with-tests loop that underpins Woowacourse code review culture.",
            "tags": ["software-engineering", "readable-code", "layering", "testing", "refactoring", "beginner", "woowacourse-backend"],
        },
        {
            "title": "Backend delivery and observability foundations",
            "goal": "Clarify logs, metrics, feature flags, rollout/rollback, and simple incident-response intuition so project-stage backend work has a practical foundation.",
            "tags": ["software-engineering", "observability", "deployment", "rollback", "feature-flag", "beginner", "woowacourse-backend"],
        },
    ],
    "system-design": [
        {
            "title": "Stateless backend, cache, database, and queue starter pack",
            "goal": "Build a beginner-first system view of how stateless apps, database, cache, and queue fit together before learners dive into deeper project architecture.",
            "tags": ["system-design", "stateless", "cache", "database", "queue", "beginner", "woowacourse-backend"],
        },
        {
            "title": "Consistency, idempotency, and async workflow foundations",
            "goal": "Strengthen the first-read layer for sync vs async, eventual consistency, outbox, retry, idempotency, and duplicate handling in backend workflows.",
            "tags": ["system-design", "consistency", "idempotency", "outbox", "async", "beginner", "woowacourse-backend"],
        },
    ],
    "qa-bridge": [
        {
            "title": "Woowacourse backend learning ladder sync",
            "goal": "Tighten README and related-doc ladders so learners can climb from Java basics -> HTTP/web basics -> MVC -> JDBC/transactions -> DI/AOP -> system design without unsafe jumps.",
            "tags": ["qa", "bridge", "beginner", "learning-path", "woowacourse-backend"],
        }
    ],
    "qa-link": [
        {
            "title": "Woowacourse backend primer return-path hygiene",
            "goal": "Make foundational backend primers link back to the right README entrypoints and forward to the next safe follow-up doc, especially across Java, Spring, network, and database lanes.",
            "tags": ["qa", "link", "primer", "readme", "beginner", "woowacourse-backend"],
        }
    ],
    "qa-retrieval": [
        {
            "title": "Woowacourse backend beginner query lock-in",
            "goal": "Lock first-hit retrieval for core learner prompts such as DispatcherServlet, keep-alive, connection pool, @Transactional, DI vs IoC, and session vs JWT so primers consistently win over deep dives.",
            "tags": ["qa", "retrieval", "beginner", "golden", "woowacourse-backend"],
        }
    ],
    "qa-content": [
        {
            "title": "Mission-prerequisite primer rubric pass",
            "goal": "Audit the most important prerequisite primers for Woowacourse backend missions and add missing mental models, examples, common-confusion notes, and safe next-step links.",
            "tags": ["qa", "content", "beginner", "clarity", "woowacourse-backend"],
        }
    ],
}


class Orchestrator:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or ensure_orchestrator_layout()
        self.queue_path = self.base_dir / "queue.json"
        self.status_path = self.base_dir / "status.json"
        self.planner_path = self.base_dir / "planner.json"
        self.wave_path = self.base_dir / "current-wave.json"
        self.history_path = self.base_dir / "history.jsonl"
        self.pid_path = self.base_dir / "runner.pid"
        self.log_path = self.base_dir / "runner.log"
        self.stop_path = self.base_dir / "stop.request"
        self.lock_path = self.base_dir / ".lock"
        self._lock_handle = None
        self._lock_depth = 0
        self.ensure_layout()

    def ensure_layout(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        if not self.queue_path.exists():
            _write_json(self.queue_path, {"items": []})
        if not self.planner_path.exists():
            _write_json(
                self.planner_path,
                {
                    "lane_cursors": {lane: 0 for lane in LANE_CATALOG},
                    "created_at": _isoformat(_utc_now()),
                    "updated_at": _isoformat(_utc_now()),
                },
            )
        if not self.status_path.exists():
            _write_json(self.status_path, self._default_status())

    def _default_status(self) -> dict[str, Any]:
        now = _isoformat(_utc_now())
        return {
            "status": "idle",
            "pid": None,
            "started_at": None,
            "heartbeat_at": now,
            "last_refresh_at": None,
            "last_wave_at": None,
            "current_wave_id": None,
            "stop_requested": False,
            "queue_summary": {"pending": 0, "leased": 0, "completed": 0, "blocked": 0, "total": 0},
            "lane_summary": {},
            "log_path": str(self.log_path),
        }

    @contextmanager
    def _locked(self):
        if self._lock_depth == 0:
            self._lock_handle = self.lock_path.open("a+", encoding="utf-8")
            fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_EX)
        self._lock_depth += 1
        try:
            yield
        finally:
            self._lock_depth -= 1
            if self._lock_depth == 0 and self._lock_handle is not None:
                fcntl.flock(self._lock_handle.fileno(), fcntl.LOCK_UN)
                self._lock_handle.close()
                self._lock_handle = None

    def load_queue(self) -> list[dict[str, Any]]:
        return list(_read_json(self.queue_path, {"items": []}).get("items", []))

    def save_queue(self, items: list[dict[str, Any]]) -> None:
        _write_json(self.queue_path, {"items": items})

    def load_planner(self) -> dict[str, Any]:
        planner = _read_json(self.planner_path, None)
        if planner is None:
            planner = {
                "lane_cursors": {lane: 0 for lane in LANE_CATALOG},
                "created_at": _isoformat(_utc_now()),
                "updated_at": _isoformat(_utc_now()),
            }
        planner.setdefault("lane_cursors", {})
        for lane in LANE_CATALOG:
            planner["lane_cursors"].setdefault(lane, 0)
        return planner

    def save_planner(self, planner: dict[str, Any]) -> None:
        planner["updated_at"] = _isoformat(_utc_now())
        _write_json(self.planner_path, planner)

    def load_status(self) -> dict[str, Any]:
        return _read_json(self.status_path, self._default_status())

    def save_status(self, status: dict[str, Any]) -> None:
        _write_json(self.status_path, status)

    def _append_history(self, event_type: str, payload: dict[str, Any], *, now: datetime | None = None) -> None:
        _append_jsonl(
            self.history_path,
            {
                "type": event_type,
                "at": _isoformat(now or _utc_now()),
                **payload,
            },
        )

    def _queue_summary(self, items: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
        summary = {"pending": 0, "leased": 0, "completed": 0, "blocked": 0, "total": len(items)}
        lane_summary: dict[str, dict[str, int]] = {}
        for item in items:
            status = item.get("status", QUEUE_PENDING)
            summary[status] = summary.get(status, 0) + 1
            lane = item["lane"]
            lane_entry = lane_summary.setdefault(
                lane,
                {"pending": 0, "leased": 0, "completed": 0, "blocked": 0, "total": 0},
            )
            lane_entry["total"] += 1
            lane_entry[status] = lane_entry.get(status, 0) + 1
        return summary, lane_summary

    def _new_item(self, lane: str, planner: dict[str, Any], now: datetime) -> dict[str, Any]:
        cursor = int(planner["lane_cursors"].get(lane, 0))
        lane_config = LANE_CATALOG[lane]
        template = lane_config["templates"][cursor % len(lane_config["templates"])]
        cycle = cursor // len(lane_config["templates"]) + 1
        suffix = f" cycle {cycle}" if cycle > 1 else ""
        item_id = f"{lane}-{cursor + 1:05d}"
        planner["lane_cursors"][lane] = cursor + 1
        return {
            "item_id": item_id,
            "lane": lane,
            "kind": lane_config["kind"],
            "title": template["title"] + suffix,
            "base_title": template["title"],
            "goal": template["goal"],
            "priority": lane_config["priority"],
            "tags": list(template.get("tags", [])),
            "status": QUEUE_PENDING,
            "attempts": 0,
            "wave_count": 0,
            "created_at": _isoformat(now),
            "updated_at": _isoformat(now),
            "lease_owner": None,
            "lease_expires_at": None,
            "completed_at": None,
            "completion_summary": None,
            "source": "template",
        }

    def _choose_template(
        self,
        lane: str,
        items: list[dict[str, Any]],
        *,
        require_beginner: bool = False,
    ) -> dict[str, Any]:
        lane_config = LANE_CATALOG[lane]
        templates = lane_config["templates"]
        live_titles = {
            _normalize_title(item.get("base_title") or item["title"])
            for item in items
            if item["lane"] == lane and item["status"] in {QUEUE_PENDING, QUEUE_LEASED}
        }
        completed_titles: list[str] = [
            _normalize_title(item.get("base_title") or item["title"])
            for item in items
            if item["lane"] == lane and item["status"] == QUEUE_COMPLETED
        ]
        recent = completed_titles[-RECENT_COMPLETION_WINDOW:]
        best_template = templates[0]
        best_score = None
        for idx, template in enumerate(templates):
            base_title = _normalize_title(template["title"])
            is_beginner = _is_beginner_focused(
                template["title"],
                template["goal"],
                list(template.get("tags", [])),
            )
            score = (
                1 if require_beginner and not is_beginner else 0,
                100 if base_title in live_titles else 0,
                recent.count(base_title),
                0 if is_beginner else 1,
                idx,
            )
            if best_score is None or score < best_score:
                best_score = score
                best_template = template
        return best_template

    def _make_template_item(self, lane: str, template: dict[str, Any], planner: dict[str, Any], now: datetime) -> dict[str, Any]:
        cursor = int(planner["lane_cursors"].get(lane, 0))
        cycle = cursor // len(LANE_CATALOG[lane]["templates"]) + 1
        suffix = f" cycle {cycle}" if cycle > 1 else ""
        item_id = f"{lane}-{cursor + 1:05d}"
        planner["lane_cursors"][lane] = cursor + 1
        tags = _normalize_candidate_tags(template["title"], template["goal"], list(template.get("tags", [])))
        return {
            "item_id": item_id,
            "lane": lane,
            "kind": LANE_CATALOG[lane]["kind"],
            "title": template["title"] + suffix,
            "base_title": template["title"],
            "goal": template["goal"],
            "priority": _priority_with_beginner_bias(
                int(LANE_CATALOG[lane]["priority"]),
                template["title"],
                template["goal"],
                tags,
                source="template",
            ),
            "tags": tags,
            "status": QUEUE_PENDING,
            "attempts": 0,
            "wave_count": 0,
            "created_at": _isoformat(now),
            "updated_at": _isoformat(now),
            "lease_owner": None,
            "lease_expires_at": None,
            "completed_at": None,
            "completion_summary": None,
            "source": "template",
        }

    def _make_adaptive_item(
        self,
        lane: str,
        title: str,
        goal: str,
        tags: list[str],
        planner: dict[str, Any],
        now: datetime,
        *,
        source: str,
        priority_boost: int = 3,
    ) -> dict[str, Any]:
        cursor = int(planner["lane_cursors"].get(lane, 0))
        item_id = f"{lane}-{cursor + 1:05d}"
        planner["lane_cursors"][lane] = cursor + 1
        normalized_tags = _normalize_candidate_tags(title, goal, tags)
        return {
            "item_id": item_id,
            "lane": lane,
            "kind": LANE_CATALOG[lane]["kind"],
            "title": title,
            "base_title": title,
            "goal": goal,
            "priority": _priority_with_beginner_bias(
                int(LANE_CATALOG[lane]["priority"]) + priority_boost,
                title,
                goal,
                normalized_tags,
                source=source,
            ),
            "tags": normalized_tags,
            "status": QUEUE_PENDING,
            "attempts": 0,
            "wave_count": 0,
            "created_at": _isoformat(now),
            "updated_at": _isoformat(now),
            "lease_owner": None,
            "lease_expires_at": None,
            "completed_at": None,
            "completion_summary": None,
            "source": source,
        }

    def _candidate_exists(self, items: list[dict[str, Any]], lane: str, title: str) -> bool:
        target = _normalize_title(title)
        return any(
            item["lane"] == lane and _normalize_title(item.get("base_title") or item["title"]) == target
            for item in items
            if item["status"] in {QUEUE_PENDING, QUEUE_LEASED, QUEUE_COMPLETED}
        )

    def _scan_anchorless_docs(self, limit: int = 4) -> list[str]:
        candidates: list[str] = []
        for path in sorted(KNOWLEDGE_CONTENTS_DIR.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            if "retrieval-anchor-keywords:" in lowered or "### retrieval anchors" in lowered or "retrieval anchors:" in lowered:
                continue
            relative = _relative_to_contents(path)
            if relative.endswith("README.md"):
                continue
            candidates.append(relative)
            if len(candidates) >= limit:
                break
        return candidates

    def _scan_readme_taxonomy_gaps(self, limit: int = 4) -> list[str]:
        gaps: list[str] = []
        for path in sorted(KNOWLEDGE_CONTENTS_DIR.rglob("README.md")):
            text = path.read_text(encoding="utf-8")
            if "빠른 탐색" in text or "Quick Routes" in text:
                continue
            gaps.append(_relative_to_contents(path))
            if len(gaps) >= limit:
                break
        root_readme = ROOT / "knowledge" / "cs" / "README.md"
        if len(gaps) < limit and root_readme.exists():
            root_text = root_readme.read_text(encoding="utf-8")
            if "Quick Routes" not in root_text and "빠른 탐색" not in root_text:
                gaps.append("README.md")
        return gaps[:limit]

    def _scan_broken_links(self, limit: int = 4) -> list[str]:
        broken: list[str] = []
        for path in sorted((ROOT / "knowledge" / "cs").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for target in _extract_markdown_links(text):
                target = target.strip()
                if not target or target.startswith("#") or "://" in target or target.startswith("mailto:"):
                    continue
                file_target = target.split("#", 1)[0]
                if not file_target:
                    continue
                resolved = (path.parent / file_target).resolve()
                if not resolved.exists():
                    broken.append(f"{_relative_to_contents(path)} -> {target}")
                    if len(broken) >= limit:
                        return broken
        return broken

    def _scan_beginner_content_gaps(self, limit: int = 4, prefixes: tuple[str, ...] | None = None) -> list[str]:
        scored: list[tuple[int, str]] = []
        for path in sorted(KNOWLEDGE_CONTENTS_DIR.rglob("*.md")):
            if path.name == "README.md":
                continue
            relative = _relative_to_contents(path)
            if prefixes and not any(relative.startswith(prefix) for prefix in prefixes):
                continue
            text = path.read_text(encoding="utf-8")
            if "**난이도: 🟢 Beginner**" not in text:
                continue
            score = 0
            lowered = text.lower()
            if "한 줄 요약" not in text:
                score += 2
            if "관련 문서:" not in text:
                score += 1
            if not any(
                marker in lowered
                for marker in (
                    "헷갈",
                    "오해",
                    "자주 묻",
                    "common confusion",
                    "빠른 비교표",
                    "먼저 10초 판별표",
                    "먼저 자를 질문",
                    "한눈에 보기",
                )
            ):
                score += 1
            if "다음 단계" not in text and "다음에 읽" not in text:
                score += 1
            if score <= 0:
                continue
            scored.append((score, relative))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [path for _, path in scored[:limit]]

    def _adaptive_probe(self, lane: str, items: list[dict[str, Any]], planner: dict[str, Any], now: datetime) -> dict[str, Any] | None:
        if lane == "qa-anchor":
            docs = self._scan_anchorless_docs()
            if docs:
                title = f"Anchorless high-value docs: {docs[0].split('/')[0]}"
                if not self._candidate_exists(items, lane, title):
                    goal = "Add retrieval-anchor-keywords to these docs and tighten nearby related-doc navigation: " + ", ".join(docs)
                    return self._make_adaptive_item(lane, title, goal, ["qa", "anchor", "metadata", "retrieval"], planner, now, source="adaptive-probe")
        if lane == "qa-taxonomy":
            gaps = self._scan_readme_taxonomy_gaps()
            if gaps:
                title = f"README taxonomy gaps: {gaps[0].split('/')[0]}"
                if not self._candidate_exists(items, lane, title):
                    goal = "Clarify survey/deep-dive/primer/catalog routing in these README or navigator files: " + ", ".join(gaps)
                    return self._make_adaptive_item(lane, title, goal, ["qa", "taxonomy", "readme", "navigation"], planner, now, source="adaptive-probe")
        if lane == "qa-link":
            broken = self._scan_broken_links()
            if broken:
                title = "Broken links and reverse-link cleanup"
                if not self._candidate_exists(items, lane, title):
                    goal = "Fix broken markdown links and strengthen reverse links. Current examples: " + "; ".join(broken)
                    return self._make_adaptive_item(lane, title, goal, ["qa", "link", "broken-links", "reverse-link"], planner, now, source="adaptive-probe")
        if lane == "qa-content" or lane in QA_CONTENT_CATEGORY_LANES:
            prefixes = _qa_content_prefixes_for_lane(lane)
            docs = self._scan_beginner_content_gaps(prefixes=prefixes)
            if docs:
                title_prefix = lane.removeprefix("qa-content-") if lane in QA_CONTENT_CATEGORY_LANES else docs[0].split('/')[0]
                title = f"Beginner content rubric gaps: {title_prefix}"
                if not self._candidate_exists(items, lane, title):
                    goal = "Tighten beginner content quality (mental model, examples, common confusion, next-step routing) in: " + ", ".join(docs)
                    return self._make_adaptive_item(
                        lane,
                        title,
                        goal,
                        ["qa", "content", "beginner", "clarity", "adaptive"],
                        planner,
                        now,
                        source="adaptive-probe",
                    )
        return None

    def seed_woowa_backend_curriculum_backlog(self, *, now: datetime | None = None) -> dict[str, list[str]]:
        with self._locked():
            current = now or _utc_now()
            items = self.load_queue()
            planner = self.load_planner()
            created: dict[str, list[str]] = {}
            for lane, candidates in WOOWA_BACKEND_CURRICULUM_BACKLOG.items():
                for candidate in candidates:
                    title = str(candidate["title"]).strip()
                    goal = str(candidate["goal"]).strip()
                    tags = [str(tag).strip() for tag in candidate.get("tags", []) if str(tag).strip()]
                    if not title or not goal or self._candidate_exists(items, lane, title):
                        continue
                    priority_boost = 18 if LANE_CATALOG[lane]["kind"] == "content" else 15
                    item = self._make_adaptive_item(
                        lane,
                        title,
                        goal,
                        tags + ["curriculum-foundation"],
                        planner,
                        current,
                        source="curriculum-foundation",
                        priority_boost=priority_boost,
                    )
                    items.append(item)
                    created.setdefault(lane, []).append(item["item_id"])
                    self._append_history(
                        "queue.seed",
                        {"item_id": item["item_id"], "lane": lane, "title": item["title"], "source": "curriculum-foundation"},
                        now=current,
                    )
            if created:
                items.sort(key=lambda entry: (entry["lane"], entry["item_id"]))
                self.save_queue(items)
                self.save_planner(planner)
                self.run_once(now=current)
            return created

    def enqueue_candidates(
        self,
        lane: str,
        candidates: list[dict[str, Any]],
        *,
        source: str,
        pending_cap: int | None = None,
        now: datetime | None = None,
    ) -> list[str]:
        with self._locked():
            current = now or _utc_now()
            items = self.load_queue()
            planner = self.load_planner()
            created: list[str] = []
            for candidate in candidates:
                title = str(candidate.get("title", "")).strip()
                goal = str(candidate.get("goal", "")).strip()
                tags = [str(tag).strip() for tag in candidate.get("tags", []) if str(tag).strip()]
                if not title or not goal:
                    continue
                if self._candidate_exists(items, lane, title):
                    continue
                if pending_cap is not None and len(_live_lane_items(items, lane)) >= pending_cap:
                    self._append_history(
                        "queue.enqueue_skipped",
                        {"lane": lane, "title": title, "source": source, "reason": "pending_cap", "pending_cap": pending_cap},
                        now=current,
                    )
                    break
                item = self._make_adaptive_item(lane, title, goal, tags, planner, current, source=source)
                items.append(item)
                created.append(item["item_id"])
                self._append_history(
                    "queue.seed",
                    {"item_id": item["item_id"], "lane": lane, "title": item["title"], "source": source},
                    now=current,
                )
            if created:
                items.sort(key=lambda entry: (entry["lane"], entry["item_id"]))
                self.save_queue(items)
                self.save_planner(planner)
                self.run_once(now=current)
            return created

    def _refresh_backlog(
        self,
        items: list[dict[str, Any]],
        planner: dict[str, Any],
        *,
        low_water_mark: int,
        now: datetime,
    ) -> list[dict[str, Any]]:
        for lane in LANE_CATALOG:
            lane_config = LANE_CATALOG[lane]
            live_count = len(_live_lane_items(items, lane))
            while live_count < low_water_mark:
                item = self._adaptive_probe(lane, items, planner, now)
                if item is None:
                    require_beginner = (
                        lane_config["kind"] == "content"
                        and _lane_has_beginner_template(lane)
                        and not _has_live_beginner_item(items, lane)
                    )
                    template = self._choose_template(lane, items, require_beginner=require_beginner)
                    item = self._make_template_item(lane, template, planner, now)
                items.append(item)
                self._append_history("queue.seed", {"item_id": item["item_id"], "lane": lane, "title": item["title"]}, now=now)
                live_count += 1
            if (
                lane_config["kind"] == "content"
                and _lane_has_beginner_template(lane)
                and not _has_live_beginner_item(items, lane)
            ):
                template = self._choose_template(lane, items, require_beginner=True)
                item = self._make_template_item(lane, template, planner, now)
                items.append(item)
                self._append_history(
                    "queue.seed",
                    {"item_id": item["item_id"], "lane": lane, "title": item["title"], "source": "beginner-guard"},
                    now=now,
                )
            adaptive_live = [
                item
                for item in items
                if item["lane"] == lane
                and item["status"] in {QUEUE_PENDING, QUEUE_LEASED}
                and str(item.get("source", "")).startswith("adaptive")
            ]
            if not adaptive_live:
                adaptive_item = self._adaptive_probe(lane, items, planner, now)
                if adaptive_item is not None:
                    items.append(adaptive_item)
                    self._append_history(
                        "queue.seed",
                        {"item_id": adaptive_item["item_id"], "lane": lane, "title": adaptive_item["title"], "source": adaptive_item["source"]},
                        now=now,
                    )
        return items

    def _release_expired_leases(self, items: list[dict[str, Any]], *, now: datetime) -> list[dict[str, Any]]:
        changed = False
        for item in items:
            if item.get("status") != QUEUE_LEASED:
                continue
            lease_expires_at = _parse_dt(item.get("lease_expires_at"))
            if lease_expires_at and lease_expires_at <= now:
                previous_owner = item.get("lease_owner")
                item["status"] = QUEUE_PENDING
                item["lease_owner"] = None
                item["lease_expires_at"] = None
                item["lease_write_scopes"] = []
                item["updated_at"] = _isoformat(now)
                changed = True
                self._append_history(
                    "queue.lease_expired",
                    {"item_id": item["item_id"], "lane": item["lane"], "lease_owner": previous_owner},
                    now=now,
                )
        if changed:
            items.sort(key=lambda entry: (entry["lane"], entry["item_id"]))
        return items

    def _build_wave(self, items: list[dict[str, Any]], *, wave_size: int, now: datetime) -> dict[str, Any]:
        pending = [item for item in items if item.get("status") == QUEUE_PENDING]
        pending.sort(key=lambda entry: (-int(entry["priority"]), entry["created_at"], entry["item_id"]))
        selected: list[dict[str, Any]] = []
        if wave_size <= 0:
            wave = {
                "wave_id": f"wave-{now.strftime('%Y%m%d%H%M%S')}",
                "created_at": _isoformat(now),
                "items": selected,
            }
            _write_json(self.wave_path, wave)
            return wave
        seen_lanes: set[str] = set()
        for item in pending:
            if item["lane"] in seen_lanes:
                continue
            selected.append(self._wave_view(item))
            seen_lanes.add(item["lane"])
            if len(selected) >= wave_size:
                break
        if len(selected) < wave_size:
            selected_ids = {entry["item_id"] for entry in selected}
            for item in pending:
                if item["item_id"] in selected_ids:
                    continue
                selected.append(self._wave_view(item))
                if len(selected) >= wave_size:
                    break
        wave = {
            "wave_id": f"wave-{now.strftime('%Y%m%d%H%M%S')}",
            "created_at": _isoformat(now),
            "items": selected,
        }
        _write_json(self.wave_path, wave)
        return wave

    def _wave_view(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "item_id": item["item_id"],
            "lane": item["lane"],
            "kind": item["kind"],
            "title": item["title"],
            "goal": item["goal"],
            "priority": item["priority"],
            "tags": item.get("tags", []),
            "worker_prompt": self.build_worker_prompt(item),
        }

    def build_worker_prompt(self, item: dict[str, Any]) -> str:
        tags = ", ".join(item.get("tags", []))
        beginner_suffix = ""
        if _is_beginner_focused(item["title"], item["goal"], list(item.get("tags", []))):
            beginner_suffix = (
                " Keep the output beginner-first: start from a plain-language mental model, "
                "separate core definitions from edge cases, prefer one entrypoint primer plus "
                "README routing over jumping straight into advanced failure modes, and include "
                "common confusions or decision tables when they help a junior reader."
            )
        qa_suffix = ""
        if _is_beginner_quality_task(item["lane"], item["title"], item["goal"], list(item.get("tags", []))):
            qa_suffix = (
                " QA success means more than fixing metadata: verify a junior reader can enter through a primer, "
                "see the next safe step, and avoid mistaking deep dives or playbooks for entrypoints. Prefer fixes "
                "that improve first-hit routing, beginner wording, and explicit primer -> follow-up -> deep-dive ladders."
            )
        content_qa_suffix = ""
        if item["lane"] == "qa-content" or item["lane"].startswith("qa-content-"):
            content_qa_suffix = (
                " For this lane, inspect the body itself: favor plain-language mental models, one concrete example or small comparison table, an explicit common-confusion section, and clear next-step links. If a doc is marked Beginner, advanced incident or operator detail should not dominate the main narrative."
            )
        return (
            f"[{item['lane']}] {item['title']}\n"
            f"Goal: {item['goal']}\n"
            f"Tags: {tags}\n"
            "Do one coherent wave: add or deepen docs, strengthen related-doc links, add retrieval-anchor-keywords where missing, and update the relevant README index."
            f"{beginner_suffix}{qa_suffix}{content_qa_suffix}"
        )

    def run_once(
        self,
        *,
        low_water_mark: int = DEFAULT_LOW_WATER_MARK,
        wave_size: int = DEFAULT_WAVE_SIZE,
        refresh_backlog: bool = True,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        with self._locked():
            current = now or _utc_now()
            items = self._release_expired_leases(self.load_queue(), now=current)
            planner = self.load_planner()
            if refresh_backlog:
                items = self._refresh_backlog(items, planner, low_water_mark=low_water_mark, now=current)
            items.sort(key=lambda entry: (entry["lane"], entry["item_id"]))
            self.save_queue(items)
            if refresh_backlog:
                self.save_planner(planner)
            wave = self._build_wave(items, wave_size=wave_size, now=current)
            summary, lane_summary = self._queue_summary(items)
            status = self.load_status()
            status.update(
                {
                    "heartbeat_at": _isoformat(current),
                    "last_refresh_at": _isoformat(current),
                    "last_wave_at": wave["created_at"],
                    "current_wave_id": wave["wave_id"],
                    "queue_summary": summary,
                    "lane_summary": lane_summary,
                    "stop_requested": self.stop_path.exists(),
                }
            )
            if status.get("status") not in {"running", "stopping"}:
                status["status"] = "idle"
            self.save_status(status)
            self._append_history(
                "orchestrator.wave",
                {"wave_id": wave["wave_id"], "size": len(wave["items"]), "queue_summary": summary},
                now=current,
            )
            return {"status": status, "current_wave": wave}

    def claim(
        self,
        worker: str,
        *,
        limit: int = 1,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        lanes: list[str] | None = None,
        write_scopes: list[str] | None = None,
        claim_tags: list[str] | None = None,
        refresh_backlog: bool = True,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        with self._locked():
            current = now or _utc_now()
            self.run_once(
                now=current,
                refresh_backlog=refresh_backlog,
                wave_size=DEFAULT_WAVE_SIZE if refresh_backlog else 0,
            )
            items = self.load_queue()
            normalized_write_scopes = [scope for scope in (write_scopes or []) if str(scope).strip()]
            if self._write_scope_has_foreign_lease(normalized_write_scopes, worker, items=items):
                return {"worker": worker, "claimed": []}
            lane_filter = set(lanes or [])
            suggested_ids = {
                item["item_id"]
                for item in _read_json(self.wave_path, {"items": []}).get("items", [])
            }
            candidates = [
                item
                for item in items
                if item.get("status") == QUEUE_PENDING and (not lane_filter or item["lane"] in lane_filter)
                and _matches_claim_tags(item, claim_tags)
            ]
            candidates.sort(
                key=lambda entry: (
                    0 if entry["item_id"] in suggested_ids else 1,
                    -int(entry["priority"]),
                    entry["created_at"],
                    entry["item_id"],
                )
            )
            claimed: list[dict[str, Any]] = []
            for item in candidates[:limit]:
                item["status"] = QUEUE_LEASED
                item["lease_owner"] = worker
                item["lease_expires_at"] = _isoformat(current + timedelta(seconds=lease_seconds))
                item["lease_write_scopes"] = normalized_write_scopes
                item["updated_at"] = _isoformat(current)
                item["attempts"] = int(item.get("attempts", 0)) + 1
                item["wave_count"] = int(item.get("wave_count", 0)) + 1
                claimed.append(self._wave_view(item))
                self._append_history(
                    "queue.claim",
                    {
                        "item_id": item["item_id"],
                        "lane": item["lane"],
                        "worker": worker,
                        "write_scopes": normalized_write_scopes,
                    },
                    now=current,
                )
            self.save_queue(items)
            self.run_once(
                now=current,
                refresh_backlog=refresh_backlog,
                wave_size=DEFAULT_WAVE_SIZE if refresh_backlog else 0,
            )
            return {"worker": worker, "claimed": claimed}

    def complete(
        self,
        item_id: str,
        worker: str,
        summary: str,
        *,
        refresh_backlog: bool = True,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        with self._locked():
            current = now or _utc_now()
            items = self.load_queue()
            target = next((item for item in items if item["item_id"] == item_id), None)
            if target is None:
                raise ValueError(f"unknown item_id: {item_id}")
            if target.get("status") != QUEUE_LEASED:
                raise ValueError(f"item is not leased: {item_id}")
            if target.get("lease_owner") != worker:
                raise ValueError(f"item {item_id} is leased by {target.get('lease_owner')}, not {worker}")
            target["status"] = QUEUE_COMPLETED
            target["lease_owner"] = None
            target["lease_expires_at"] = None
            target["lease_write_scopes"] = []
            target["completion_summary"] = summary
            target["completed_at"] = _isoformat(current)
            target["updated_at"] = _isoformat(current)
            self.save_queue(items)
            self._append_history(
                "queue.complete",
                {"item_id": item_id, "lane": target["lane"], "worker": worker, "summary": summary},
                now=current,
            )
            self.run_once(
                now=current,
                refresh_backlog=refresh_backlog,
                wave_size=DEFAULT_WAVE_SIZE if refresh_backlog else 0,
            )
            return {"item_id": item_id, "worker": worker, "status": "completed"}

    def requeue(
        self,
        item_id: str,
        worker: str,
        reason: str,
        *,
        refresh_backlog: bool = True,
        now: datetime | None = None,
        blocked: bool = False,
    ) -> dict[str, Any]:
        with self._locked():
            current = now or _utc_now()
            items = self.load_queue()
            target = next((item for item in items if item["item_id"] == item_id), None)
            if target is None:
                raise ValueError(f"unknown item_id: {item_id}")
            if target.get("status") != QUEUE_LEASED:
                raise ValueError(f"item is not leased: {item_id}")
            if target.get("lease_owner") != worker:
                raise ValueError(f"item {item_id} is leased by {target.get('lease_owner')}, not {worker}")
            target["status"] = QUEUE_BLOCKED if blocked else QUEUE_PENDING
            target["lease_owner"] = None
            target["lease_expires_at"] = None
            target["lease_write_scopes"] = []
            target["updated_at"] = _isoformat(current)
            target["completion_summary"] = reason
            self.save_queue(items)
            self._append_history(
                "queue.blocked" if blocked else "queue.requeued",
                {"item_id": item_id, "lane": target["lane"], "worker": worker, "summary": reason},
                now=current,
            )
            self.run_once(
                now=current,
                refresh_backlog=refresh_backlog,
                wave_size=DEFAULT_WAVE_SIZE if refresh_backlog else 0,
            )
            return {"item_id": item_id, "worker": worker, "status": target["status"]}

    def worker_leased_item(self, worker: str) -> dict[str, Any] | None:
        return next(
            (item for item in self.load_queue() if item.get("status") == QUEUE_LEASED and item.get("lease_owner") == worker),
            None,
        )

    def lane_has_foreign_lease(self, lane: str, worker: str) -> bool:
        return any(
            item.get("status") == QUEUE_LEASED and item["lane"] == lane and item.get("lease_owner") != worker
            for item in self.load_queue()
        )

    def _write_scope_has_foreign_lease(
        self,
        write_scopes: list[str],
        worker: str,
        *,
        items: list[dict[str, Any]],
    ) -> bool:
        requested = {str(scope).strip() for scope in write_scopes if str(scope).strip()}
        if not requested:
            return False
        return any(
            item.get("status") == QUEUE_LEASED
            and item.get("lease_owner") != worker
            and bool(requested & _lease_write_scopes(item))
            for item in items
        )

    def write_scope_has_foreign_lease(self, write_scopes: list[str], worker: str) -> bool:
        return self._write_scope_has_foreign_lease(write_scopes, worker, items=self.load_queue())

    def release_worker_leases(
        self,
        worker: str,
        reason: str,
        *,
        refresh_backlog: bool = True,
        now: datetime | None = None,
    ) -> list[str]:
        with self._locked():
            current = now or _utc_now()
            items = self.load_queue()
            released: list[str] = []
            for item in items:
                if item.get("status") == QUEUE_LEASED and item.get("lease_owner") == worker:
                    item["status"] = QUEUE_PENDING
                    item["lease_owner"] = None
                    item["lease_expires_at"] = None
                    item["lease_write_scopes"] = []
                    item["updated_at"] = _isoformat(current)
                    item["completion_summary"] = reason
                    released.append(item["item_id"])
                    self._append_history(
                        "queue.requeued",
                        {"item_id": item["item_id"], "lane": item["lane"], "worker": worker, "summary": reason},
                        now=current,
                    )
            if released:
                self.save_queue(items)
                self.run_once(
                    now=current,
                    refresh_backlog=refresh_backlog,
                    wave_size=DEFAULT_WAVE_SIZE if refresh_backlog else 0,
                )
            return released

    def list_queue(self, *, status_filter: str | None = None, lane: str | None = None, limit: int | None = None) -> dict[str, Any]:
        items = self.load_queue()
        if status_filter:
            items = [item for item in items if item.get("status") == status_filter]
        if lane:
            items = [item for item in items if item["lane"] == lane]
        items.sort(key=lambda entry: (-int(entry["priority"]), entry["lane"], entry["item_id"]))
        if limit is not None:
            items = items[:limit]
        return {"items": items}

    def status(self) -> dict[str, Any]:
        status = self.load_status()
        pid = status.get("pid")
        if pid and not _pid_alive(int(pid)):
            status["status"] = "stopped"
            status["pid"] = None
            self.save_status(status)
        return {
            "status": status,
            "current_wave": _read_json(self.wave_path, {"wave_id": None, "items": []}),
            "queue": self.list_queue(limit=20),
        }

    def request_stop(self, *, force: bool = False, now: datetime | None = None) -> dict[str, Any]:
        current = now or _utc_now()
        self.stop_path.write_text(_isoformat(current) + "\n", encoding="utf-8")
        status = self.load_status()
        status["stop_requested"] = True
        status["status"] = "stopping" if status.get("pid") else "stopped"
        self.save_status(status)
        self._append_history("orchestrator.stop_requested", {"force": force}, now=current)
        pid = status.get("pid")
        if force and pid and _pid_alive(int(pid)):
            os.kill(int(pid), signal.SIGTERM)
        return {"status": status}

    def clear_stop_request(self) -> None:
        if self.stop_path.exists():
            self.stop_path.unlink()

    def start_background(
        self,
        *,
        cli_script: Path,
        interval_seconds: int = DEFAULT_LOOP_INTERVAL_SECONDS,
        low_water_mark: int = DEFAULT_LOW_WATER_MARK,
        wave_size: int = DEFAULT_WAVE_SIZE,
    ) -> dict[str, Any]:
        status = self.load_status()
        pid = status.get("pid")
        if pid and _pid_alive(int(pid)):
            return {"status": status, "already_running": True}
        ensure_global_layout()
        self.clear_stop_request()
        with self.log_path.open("a", encoding="utf-8") as handle:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(cli_script),
                    "orchestrator",
                    "run-loop",
                    "--interval-seconds",
                    str(interval_seconds),
                    "--low-water-mark",
                    str(low_water_mark),
                    "--wave-size",
                    str(wave_size),
                ],
                cwd=str(ROOT),
                stdout=handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        now = _utc_now()
        status.update(
            {
                "status": "running",
                "pid": proc.pid,
                "started_at": _isoformat(now),
                "heartbeat_at": _isoformat(now),
                "stop_requested": False,
                "log_path": str(self.log_path),
            }
        )
        self.save_status(status)
        self.pid_path.write_text(str(proc.pid), encoding="utf-8")
        self._append_history("orchestrator.start", {"pid": proc.pid}, now=now)
        return {"status": status, "already_running": False}

    def run_loop(
        self,
        *,
        interval_seconds: int = DEFAULT_LOOP_INTERVAL_SECONDS,
        low_water_mark: int = DEFAULT_LOW_WATER_MARK,
        wave_size: int = DEFAULT_WAVE_SIZE,
    ) -> int:
        now = _utc_now()
        pid = os.getpid()
        current_status = self.load_status()
        existing_pid = current_status.get("pid")
        if existing_pid and existing_pid != pid and _pid_alive(int(existing_pid)):
            raise RuntimeError(f"orchestrator already running with pid {existing_pid}")
        self.clear_stop_request()
        self.pid_path.write_text(str(pid), encoding="utf-8")
        current_status.update(
            {
                "status": "running",
                "pid": pid,
                "started_at": current_status.get("started_at") or _isoformat(now),
                "heartbeat_at": _isoformat(now),
                "stop_requested": False,
                "log_path": str(self.log_path),
            }
        )
        self.save_status(current_status)
        self._append_history("orchestrator.loop_started", {"pid": pid}, now=now)
        try:
            while True:
                cycle_now = _utc_now()
                self.run_once(low_water_mark=low_water_mark, wave_size=wave_size, now=cycle_now)
                status = self.load_status()
                status["status"] = "running"
                status["pid"] = pid
                status["heartbeat_at"] = _isoformat(_utc_now())
                status["stop_requested"] = self.stop_path.exists()
                self.save_status(status)
                if self.stop_path.exists():
                    break
                time.sleep(interval_seconds)
        finally:
            end_now = _utc_now()
            status = self.load_status()
            status["status"] = "stopped"
            status["pid"] = None
            status["heartbeat_at"] = _isoformat(end_now)
            status["stop_requested"] = self.stop_path.exists()
            self.save_status(status)
            if self.pid_path.exists():
                self.pid_path.unlink()
            self._append_history("orchestrator.loop_stopped", {"pid": pid}, now=end_now)
        return 0


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True
