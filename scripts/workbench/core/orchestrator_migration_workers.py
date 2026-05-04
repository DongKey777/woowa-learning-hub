"""Phase 8 v3 migration worker fleet.

Defines a 30-worker fleet that *transforms* the existing 2,200+ legacy
docs into v3 frontmatter contract instead of *growing* the corpus
(which is what the existing ``EXPANSION60_FLEET`` does). The two are
complementary — expansion fleets add Beginner/Intermediate primers in
the legacy authoring contract; this fleet rewrites those docs into the
R3 v3 contract that the Pilot 50 baseline depends on.

Companion artifacts:
  * ``config/migration_v3/locked_pilot_paths.json`` —
    Pilot 50 + Phase 4 wave docs that must NOT be touched (they hold
    the OVERALL 95.5% baseline).
  * ``state/orchestrator/migration_v3/batches/<category>/batch-NNN.json``
    — per-batch manifest written by the curriculum batch planner.
  * ``scripts/learning/rag/r3/create_v3_frontmatter.py`` — builds the
    deterministic baseline frontmatter (no LLM) for v0 → v3.
  * ``scripts/learning/rag/r3/synthesize_chunk_prefix.py`` — builds
    the codex-exec authoring prompt for ``contextual_chunk_prefix``.

This fleet is **created but not started**. Phase 8 execution is gated
on the user freeing token budget — see
``docs/master-plan-progress.md`` Phase 8.

Topology (30 workers):

    2  curriculum  : pilot lock guard + batch planner
    22 migration   : 11 categories x (frontmatter, prefix)
    3  qa          : v3 lint, pilot guard, cross-doc consistency
    2  rag         : cohort_eval gate (95.5%), golden mutator
    1  ops         : batch release / index rebuild / rollback

Worker mode taxonomy (new for migration_v3, on top of existing
expand/write/fix/report/script/queue/ops):
  * ``migrate_v0_to_v3`` — synthesize a v3 frontmatter for a doc that
    has none (calls ``create_v3_frontmatter`` for the deterministic
    baseline, then a codex-exec pass for authorial fields).
  * ``migrate_prefix`` — author the doc-level
    ``contextual_chunk_prefix`` for a v3 doc that has the rest of
    the frontmatter but an empty prefix.

Both modes are write-once-per-doc-per-stage and idempotent — re-running
on an already-migrated doc is a no-op.

The fleet is registered in ``orchestrator_workers.FLEET_PROFILES``
under the ``"migration_v3"`` key. Start with::

    bin/orchestrator fleet-start --profile migration_v3

(The user has explicitly deferred starting this fleet until token
budget allows. The code path is wired but should not be invoked yet.)
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIGRATION_V3_WORKER_PENDING_CAP = 12  # tighter than expansion60 (28)
MIGRATION_V3_FLEET_SIZE = 30
MIGRATION_V3_DEFAULT_BATCH_SIZE = 3   # docs per claim
MIGRATION_V3_PREFIX_BATCH_SIZE = 5    # prefix authoring is lighter

# 11 corpus categories (verified against
# ``find knowledge/cs/contents -mindepth 1 -maxdepth 1 -type d``).
MIGRATION_V3_CATEGORIES: tuple[str, ...] = (
    "algorithm",
    "data-structure",
    "database",
    "design-pattern",
    "language-java",       # nested under language/
    "network",
    "operating-system",
    "security",
    "software-engineering",
    "spring",
    "system-design",
)

# Migration-specific quality gates beyond the expansion gates.
MIGRATION_V3_GATES: tuple[str, ...] = (
    "v3_frontmatter_complete",     # 18 fields all present
    "pilot_50_untouched",          # Pilot lock guard
    "no_alias_query_overlap",      # aliases ⊥ expected_queries
    "contextual_prefix_format",    # 50-100 token, no markdown fences
    "concept_id_unique",           # cross-doc concept_id uniqueness
)


# ---------------------------------------------------------------------------
# Worker profile factory
# ---------------------------------------------------------------------------

def _migration_v3_profile(
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
    batch_size: int = 1,
) -> dict[str, Any]:
    """Build a migration_v3 worker profile.

    Mirrors ``_expansion60_profile`` shape so the orchestrator
    supervisor can claim/lease/run these workers without case-splits.
    Differences:
      * ``pending_cap`` = MIGRATION_V3_WORKER_PENDING_CAP (12, not 28)
      * ``fleet_size`` = MIGRATION_V3_FLEET_SIZE (30, not 60)
      * ``batch_size`` field added (orchestrator claim layer reads it
        to lease ``batch_size`` items at once)
      * default ``write_scopes`` namespaced under ``migration_v3:*``
      * ``quality_gates`` defaults include MIGRATION_V3_GATES
    """
    default_scope = f"migration_v3:{role}:{name.removeprefix('migration-v3-')}"
    return {
        "name": name,
        "lane": lane,
        "role": role,
        "mode": mode,
        "claim_tags": claim_tags,
        "write_scopes": write_scopes or [default_scope],
        "target_paths": target_paths,
        "quality_gates": list(quality_gates or MIGRATION_V3_GATES),
        "can_enqueue": can_enqueue,
        "pending_cap": MIGRATION_V3_WORKER_PENDING_CAP,
        "fleet_size": MIGRATION_V3_FLEET_SIZE,
        "batch_size": batch_size,
    }


# ---------------------------------------------------------------------------
# Per-category content workers (22)
# ---------------------------------------------------------------------------

def _category_content_workers() -> list[dict[str, Any]]:
    workers: list[dict[str, Any]] = []
    for category in MIGRATION_V3_CATEGORIES:
        # Path glob: language-java is nested as language/java/
        if category == "language-java":
            target = "knowledge/cs/contents/language/java/**"
        else:
            target = f"knowledge/cs/contents/{category}/**"

        workers.append(_migration_v3_profile(
            f"migration-v3-{category}-frontmatter",
            f"migration-content-{category}",
            "migration",
            "migrate_v0_to_v3",
            [category, "frontmatter", "v3", "schema"],
            [target],
            write_scopes=[f"migration_v3:{category}:frontmatter"],
            can_enqueue=False,  # batch planner owns enqueuing
            batch_size=MIGRATION_V3_DEFAULT_BATCH_SIZE,
        ))
        workers.append(_migration_v3_profile(
            f"migration-v3-{category}-prefix",
            f"migration-content-{category}",
            "migration",
            "migrate_prefix",
            [category, "prefix", "context", "embed"],
            [target],
            write_scopes=[f"migration_v3:{category}:prefix"],
            can_enqueue=False,
            batch_size=MIGRATION_V3_PREFIX_BATCH_SIZE,
        ))
    return workers


# ---------------------------------------------------------------------------
# Fleet definition
# ---------------------------------------------------------------------------

MIGRATION_V3_FLEET: list[dict[str, Any]] = [
    # ── 2 curriculum
    _migration_v3_profile(
        "migration-v3-curriculum-pilot-lock",
        "migration-curriculum",
        "curriculum",
        "report",
        ["pilot", "lock", "v3", "baseline"],
        [
            "docs/worklogs/rag-r3-pilot-50-docs-selection.md",
            "config/migration_v3/locked_pilot_paths.json",
        ],
        write_scopes=["migration_v3:curriculum:pilot-lock"],
        quality_gates=["pilot_50_untouched"],
    ),
    _migration_v3_profile(
        "migration-v3-curriculum-batch-planner",
        "migration-curriculum",
        "curriculum",
        "report",
        ["batch", "wave", "category", "manifest"],
        [
            "state/orchestrator/migration_v3/**",
            "knowledge/cs/contents/**/*.md",
        ],
        write_scopes=["migration_v3:curriculum:batch-planner"],
        can_enqueue=True,
        quality_gates=["pilot_50_untouched"],
    ),

    # ── 22 content (11 categories x {frontmatter, prefix})
    *_category_content_workers(),

    # ── 3 QA
    _migration_v3_profile(
        "migration-v3-qa-lint",
        "migration-qa",
        "qa",
        "fix",
        ["lint", "v3", "schema", "frontmatter"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3:qa:lint"],
        quality_gates=[
            "v3_frontmatter_complete",
            "no_alias_query_overlap",
            "contextual_prefix_format",
        ],
    ),
    _migration_v3_profile(
        "migration-v3-qa-pilot-guard",
        "migration-qa",
        "qa",
        "fix",
        ["pilot", "guard", "diff", "lock"],
        [
            "config/migration_v3/locked_pilot_paths.json",
            "knowledge/cs/contents/**/*.md",
        ],
        write_scopes=["migration_v3:qa:pilot-guard"],
        quality_gates=["pilot_50_untouched"],
    ),
    _migration_v3_profile(
        "migration-v3-qa-cross-doc-consistency",
        "migration-qa",
        "qa",
        "fix",
        ["concept-id", "linked-paths", "forbidden-neighbors", "consistency"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3:qa:consistency"],
        quality_gates=[
            "concept_id_unique",
            "v3_frontmatter_complete",
        ],
    ),

    # ── 2 RAG
    _migration_v3_profile(
        "migration-v3-rag-cohort-eval-gate",
        "migration-rag",
        "rag",
        "script",
        ["cohort", "eval", "regression", "baseline"],
        [
            "state/cs_rag/**",
            "tests/fixtures/r3_qrels_real_v1.json",
            "scripts/learning/rag/r3/eval/**",
        ],
        write_scopes=["migration_v3:rag:cohort-eval"],  # singleton
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_profile(
        "migration-v3-rag-golden-mutator",
        "migration-rag",
        "rag",
        "fix",
        ["golden", "fixture", "v3", "regression"],
        [
            "tests/fixtures/cs_rag_golden_queries.json",
            "tests/fixtures/r3_qrels_real_v1.json",
        ],
        write_scopes=["migration_v3:rag:golden"],  # singleton
    ),

    # ── 1 ops
    _migration_v3_profile(
        "migration-v3-ops-batch-release",
        "migration-ops",
        "ops",
        "ops",
        ["release", "index-build", "batch-merge", "rollback"],
        [
            "state/cs_rag/**",
            "config/rag_models.json",
            "state/orchestrator/migration_v3/**",
        ],
        write_scopes=["migration_v3:ops:release"],
    ),
]


# Compile-time invariant: count must equal MIGRATION_V3_FLEET_SIZE.
# Surfaced as a regression test in
# tests/unit/test_migration_v3_workers_topology.py.
assert len(MIGRATION_V3_FLEET) == MIGRATION_V3_FLEET_SIZE, (
    f"MIGRATION_V3_FLEET has {len(MIGRATION_V3_FLEET)} workers, "
    f"expected {MIGRATION_V3_FLEET_SIZE}"
)
