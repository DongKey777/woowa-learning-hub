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


# ---------------------------------------------------------------------------
# Phase 8 — migration_v3_60: high-throughput fleet for ChatGPT Pro quota
# ---------------------------------------------------------------------------
#
# The 30-worker MIGRATION_V3_FLEET above was designed for ChatGPT Plus,
# where rate limit bound the wallclock and adding more workers would
# only burn the 5-hour window faster. ChatGPT Pro has higher quota, so
# this fleet doubles in-flight parallelism to ~60 and rebalances the
# topology toward the cohorts that scored weakest in the
# post-9.3 cohort_eval (2026-05-05):
#
#   mission_bridge   83.3% — 5/30 fail; 2 are corpus gaps (sentinel)
#   confusable_pairs 90.0% — 4/40 fail; chooser docs disambiguate
#   symptom_to_cause 93.3% — 2/30 fail; symptom_router routes
#
# So this fleet has *more* Wave C (new doc) writers than v3_30, sized
# proportional to each cohort's weakness:
#
#   5 mission_bridge writers (one per Woowa mission)
#   3 chooser writers (Spring / Database / Design Pattern)
#   3 symptom_router writers (Database / Spring / Network)
#
# Plus 11 frontmatter (Wave A) and 11 prefix (Wave B) writers — one
# per category — and a richer QA / RAG / ops layer that validates
# v3-specific invariants (concept_id uniqueness, aliases ⊥
# expected_queries, role-conditional fields, citation trace).

MIGRATION_V3_60_WORKER_PENDING_CAP = 28  # match expansion60 / Pro quota
MIGRATION_V3_60_FLEET_SIZE = 60

MIGRATION_V3_60_WAVE_C_MISSIONS: tuple[str, ...] = (
    "roomescape", "baseball", "lotto", "shopping-cart", "blackjack",
)

MIGRATION_V3_60_WAVE_C_CHOOSER_CATEGORIES: tuple[str, ...] = (
    "spring", "database", "design-pattern",
)

MIGRATION_V3_60_WAVE_C_SYMPTOM_CATEGORIES: tuple[str, ...] = (
    "database", "spring", "network",
)


def _migration_v3_60_profile(
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
    """60-fleet profile factory.

    Mirrors ``_migration_v3_profile`` shape. The pending_cap doubles
    (12 → 28) so the supervisor can keep up with parallel Pro-tier
    codex calls. ``fleet_size`` carries 60 so topology tests can pin
    the contract without grepping the list.
    """
    default_scope = f"migration_v3_60:{role}:{name.removeprefix('migration-v3-60-')}"
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
        "pending_cap": MIGRATION_V3_60_WORKER_PENDING_CAP,
        "fleet_size": MIGRATION_V3_60_FLEET_SIZE,
        "batch_size": batch_size,
    }


def _migration_v3_60_wave_a_workers() -> list[dict[str, Any]]:
    """11 frontmatter authoring workers — one per category."""
    workers: list[dict[str, Any]] = []
    for category in MIGRATION_V3_CATEGORIES:
        target = (
            "knowledge/cs/contents/language/java/**"
            if category == "language-java"
            else f"knowledge/cs/contents/{category}/**"
        )
        workers.append(_migration_v3_60_profile(
            f"migration-v3-60-frontmatter-{category}",
            f"migration-content-{category}",
            "migration",
            "migrate_v0_to_v3",
            [category, "frontmatter", "v3", "wave-a"],
            [target],
            write_scopes=[f"migration_v3_60:{category}:frontmatter"],
            batch_size=MIGRATION_V3_DEFAULT_BATCH_SIZE,
        ))
    return workers


def _migration_v3_60_wave_b_workers() -> list[dict[str, Any]]:
    """11 prefix authoring workers — one per category."""
    workers: list[dict[str, Any]] = []
    for category in MIGRATION_V3_CATEGORIES:
        target = (
            "knowledge/cs/contents/language/java/**"
            if category == "language-java"
            else f"knowledge/cs/contents/{category}/**"
        )
        workers.append(_migration_v3_60_profile(
            f"migration-v3-60-prefix-{category}",
            f"migration-content-{category}",
            "migration",
            "migrate_prefix",
            [category, "prefix", "wave-b", "context"],
            [target],
            write_scopes=[f"migration_v3_60:{category}:prefix"],
            batch_size=MIGRATION_V3_PREFIX_BATCH_SIZE,
        ))
    return workers


def _migration_v3_60_wave_d_workers() -> list[dict[str, Any]]:
    """1 quality revisit worker — the "always-on" loop closer.

    When all underweight cells are filled and Wave A/B/C have nothing
    productive to do, the revisit worker picks an existing v3 doc with
    weak aliases / linked_paths / forbidden_neighbors / undersized
    contextual_chunk_prefix and deepens it. This keeps the fleet from
    spinning on an empty queue and from creating speculative low-value
    new docs (the failure mode the user explicitly flagged: bias
    accumulation when the fleet is left running indefinitely).
    """
    return [_migration_v3_60_profile(
        "migration-v3-60-revisit-quality-deepen",
        "migration-content-revisit",
        "migration",
        "migrate_revisit",
        ["revisit", "wave-d", "quality", "alias-thin",
         "linked-paths-empty", "prefix-out-of-band"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:wave-d:revisit"],
        batch_size=1,
    )]


def _migration_v3_60_wave_c_workers() -> list[dict[str, Any]]:
    """11 new-doc authoring workers (5 mission_bridge + 3 chooser +
    3 symptom_router) — direct-attack the cohort_eval weak spots."""
    workers: list[dict[str, Any]] = []

    for mission in MIGRATION_V3_60_WAVE_C_MISSIONS:
        workers.append(_migration_v3_60_profile(
            f"migration-v3-60-new-mission-bridge-{mission}",
            "migration-content-mission-bridge",
            "migration",
            "migrate_new_doc",
            [mission, "mission-bridge", "new-doc", "wave-c"],
            [
                "knowledge/cs/contents/spring/**",
                "knowledge/cs/contents/software-engineering/**",
                "knowledge/cs/contents/database/**",
                "knowledge/cs/contents/design-pattern/**",
            ],
            write_scopes=[f"migration_v3_60:wave-c:mission-bridge:{mission}"],
            batch_size=1,  # one new doc per claim — content density
        ))

    for category in MIGRATION_V3_60_WAVE_C_CHOOSER_CATEGORIES:
        workers.append(_migration_v3_60_profile(
            f"migration-v3-60-new-chooser-{category}",
            "migration-content-chooser",
            "migration",
            "migrate_new_doc",
            [category, "chooser", "new-doc", "wave-c", "confusable"],
            [f"knowledge/cs/contents/{category}/**"],
            write_scopes=[f"migration_v3_60:wave-c:chooser:{category}"],
            batch_size=1,
        ))

    for category in MIGRATION_V3_60_WAVE_C_SYMPTOM_CATEGORIES:
        workers.append(_migration_v3_60_profile(
            f"migration-v3-60-new-symptom-router-{category}",
            "migration-content-symptom-router",
            "migration",
            "migrate_new_doc",
            [category, "symptom-router", "new-doc", "wave-c"],
            [f"knowledge/cs/contents/{category}/**"],
            write_scopes=[f"migration_v3_60:wave-c:symptom-router:{category}"],
            batch_size=1,
        ))

    return workers


MIGRATION_V3_60_FLEET: list[dict[str, Any]] = [
    # ── 2 curriculum
    _migration_v3_60_profile(
        "migration-v3-60-curriculum-pilot-lock",
        "migration-curriculum",
        "curriculum",
        "report",
        ["pilot", "lock", "v3", "baseline", "guard"],
        [
            "docs/worklogs/rag-r3-pilot-50-docs-selection.md",
            "config/migration_v3/locked_pilot_paths.json",
        ],
        write_scopes=["migration_v3_60:curriculum:pilot-lock"],
        quality_gates=["pilot_50_untouched"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-curriculum-batch-planner",
        "migration-curriculum",
        "curriculum",
        "report",
        ["batch", "wave", "category", "manifest", "queue"],
        [
            "state/orchestrator/migration_v3/**",
            "knowledge/cs/contents/**/*.md",
        ],
        write_scopes=["migration_v3_60:curriculum:batch-planner"],
        can_enqueue=True,
        quality_gates=["pilot_50_untouched"],
    ),

    # ── 11 Wave A (frontmatter author)
    *_migration_v3_60_wave_a_workers(),

    # ── 11 Wave B (prefix author)
    *_migration_v3_60_wave_b_workers(),

    # ── 11 Wave C (new doc — 5 mission_bridge + 3 chooser + 3 symptom_router)
    *_migration_v3_60_wave_c_workers(),

    # ── 1 Wave D (revisit existing v3 doc to deepen quality)
    *_migration_v3_60_wave_d_workers(),

    # ── 14 QA (v3-specific invariants)
    _migration_v3_60_profile(
        "migration-v3-60-qa-frontmatter-lint",
        "migration-qa",
        "qa", "fix",
        ["lint", "v3", "schema", "frontmatter"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:frontmatter-lint"],
        quality_gates=["v3_frontmatter_complete", "no_alias_query_overlap"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-pilot-lock-guard",
        "migration-qa",
        "qa", "fix",
        ["pilot", "guard", "lock", "diff"],
        [
            "config/migration_v3/locked_pilot_paths.json",
            "knowledge/cs/contents/**/*.md",
        ],
        write_scopes=["migration_v3_60:qa:pilot-guard"],
        quality_gates=["pilot_50_untouched"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-concept-id-uniqueness",
        "migration-qa",
        "qa", "fix",
        ["concept-id", "uniqueness", "canonical"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:concept-id"],
        quality_gates=["concept_id_unique"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-prefix-format",
        "migration-qa",
        "qa", "fix",
        ["prefix", "format", "token-range", "korean"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:prefix-format"],
        quality_gates=["contextual_prefix_format"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-aliases-eq-disjoint",
        "migration-qa",
        "qa", "fix",
        ["aliases", "expected-queries", "disjoint", "circular-leak"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:alias-eq-disjoint"],
        quality_gates=["no_alias_query_overlap"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-linked-paths-integrity",
        "migration-qa",
        "qa", "fix",
        ["linked-paths", "next-docs", "prerequisites", "integrity"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:linked-paths"],
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-forbidden-bidirectional",
        "migration-qa",
        "qa", "fix",
        ["forbidden-neighbors", "bidirectional", "confusable"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:forbidden-bidir"],
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-doc-role-coverage",
        "migration-qa",
        "qa", "fix",
        ["doc-role", "coverage", "primer", "chooser", "playbook"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:doc-role"],
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-symptom-completeness",
        "migration-qa",
        "qa", "fix",
        ["symptoms", "symptom-router", "playbook", "completeness"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:symptom-completeness"],
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-mission-id-coverage",
        "migration-qa",
        "qa", "fix",
        ["mission-id", "mission-bridge", "coverage"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:mission-id"],
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-confusable-pair-symmetry",
        "migration-qa",
        "qa", "fix",
        ["confusable-with", "symmetry", "chooser", "ranking"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:confusable-symmetry"],
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-qa-next-doc-graph",
        "migration-qa",
        "qa", "fix",
        ["next-docs", "graph", "ladder", "learning-path"],
        ["knowledge/cs/contents/**/*.md"],
        write_scopes=["migration_v3_60:qa:next-doc-graph"],
        quality_gates=["v3_frontmatter_complete"],
    ),

    # ── 8 RAG (eval gates + recalibration)
    _migration_v3_60_profile(
        "migration-v3-60-rag-cohort-eval-gate",
        "migration-rag",
        "rag", "script",
        ["cohort", "eval", "regression", "baseline", "94.0"],
        [
            "state/cs_rag/**",
            "tests/fixtures/r3_qrels_real_v1.json",
            "scripts/learning/rag/r3/eval/**",
            "reports/rag_eval/**",
        ],
        write_scopes=["migration_v3_60:rag:cohort-eval"],
        quality_gates=["v3_frontmatter_complete"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-rag-golden-mutator",
        "migration-rag",
        "rag", "fix",
        ["golden", "fixture", "v3", "regression"],
        [
            "tests/fixtures/cs_rag_golden_queries.json",
            "tests/fixtures/r3_qrels_real_v1.json",
        ],
        write_scopes=["migration_v3_60:rag:golden"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-rag-signal-rules-mutator",
        "migration-rag",
        "rag", "fix",
        ["signal", "boost", "suppress", "v3"],
        [
            "scripts/learning/rag/signal_rules.py",
            "tests/unit/test_cs_rag_signal_rules.py",
        ],
        write_scopes=["migration_v3_60:rag:signal-rules"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-rag-refusal-threshold-recalibrate",
        "migration-rag",
        "rag", "script",
        ["refusal", "threshold", "calibration", "9.3"],
        [
            "scripts/learning/rag/r3/eval/calibrate_refusal_threshold.py",
            "reports/rag_eval/refusal_threshold_calibration.json",
            "bin/_rag_env.sh",
        ],
        write_scopes=["migration_v3_60:rag:refusal-threshold"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-rag-citation-trace-validate",
        "migration-rag",
        "rag", "script",
        ["citation", "9.4", "trace", "response-hints"],
        [
            "scripts/learning/integration.py",
            "tests/unit/test_citation_contract.py",
        ],
        write_scopes=["migration_v3_60:rag:citation-trace"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-rag-index-smoke",
        "migration-rag",
        "rag", "script",
        ["index", "stale", "cs-index-build", "readiness"],
        [
            "state/cs_rag/**",
            "scripts/learning/rag/**",
        ],
        write_scopes=["migration_v3_60:rag:index-smoke"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-rag-paraphrase-robustness",
        "migration-rag",
        "rag", "script",
        ["paraphrase", "robustness", "cohort", "100%"],
        [
            "tests/fixtures/r3_qrels_real_v1.json",
            "reports/rag_eval/**",
        ],
        write_scopes=["migration_v3_60:rag:paraphrase"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-rag-balance-monitor",
        "migration-rag",
        "rag", "script",
        ["balance", "monitor", "drift", "saturation", "alarm"],
        [
            "state/orchestrator/migration_v3/**",
            "reports/rag_eval/**",
            "knowledge/cs/contents/**/*.md",
        ],
        write_scopes=["migration_v3_60:rag:balance-monitor"],
        quality_gates=["v3_frontmatter_complete"],
    ),

    # ── 4 ops
    _migration_v3_60_profile(
        "migration-v3-60-ops-batch-release",
        "migration-ops",
        "ops", "ops",
        ["release", "batch-merge", "cherry-pick"],
        [
            "state/orchestrator/migration_v3/**",
            "knowledge/cs/contents/**",
        ],
        write_scopes=["migration_v3_60:ops:batch-release"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-ops-index-rebuild-trigger",
        "migration-ops",
        "ops", "ops",
        ["index", "rebuild", "runpod", "release-tag"],
        [
            "state/cs_rag/**",
            "config/rag_models.json",
        ],
        write_scopes=["migration_v3_60:ops:index-rebuild"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-ops-queue-governor",
        "migration-ops",
        "ops", "queue",
        ["queue", "pending", "candidate", "governor"],
        ["state/orchestrator/**"],
        write_scopes=["migration_v3_60:ops:queue-governor"],
    ),
    _migration_v3_60_profile(
        "migration-v3-60-ops-rollback-handler",
        "migration-ops",
        "ops", "ops",
        ["rollback", "revert", "cohort-eval-fail"],
        [
            "state/orchestrator/migration_v3/**",
            "knowledge/cs/contents/**",
        ],
        write_scopes=["migration_v3_60:ops:rollback"],
    ),
]


# Compile-time invariant — fails the import if topology drifts.
assert len(MIGRATION_V3_60_FLEET) == MIGRATION_V3_60_FLEET_SIZE, (
    f"MIGRATION_V3_60_FLEET has {len(MIGRATION_V3_60_FLEET)} workers, "
    f"expected {MIGRATION_V3_60_FLEET_SIZE}"
)
