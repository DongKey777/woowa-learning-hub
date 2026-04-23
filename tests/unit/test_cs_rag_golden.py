"""Golden query → expected-path regression for the real CS RAG index.

Each entry in ``tests/fixtures/cs_rag_golden_queries.json`` asserts that
the expected path shows up in the top-K results for a handcrafted
prompt + learning_points pair. High-value entries may also declare a
``max_rank`` budget so we catch ranking drift, not just total misses.
Close sibling docs may also declare ``acceptable_paths`` so the fixture
locks in a retrieval family instead of overfitting to a single file when
the corpus grows, but high-frequency sibling intents should still get
their own dedicated prompts so swaps stay visible. The fixture is the
source of truth for retrieval quality baselines — adding a new curated
query here is how we lock in a tuning win or catch a regression.

This test requires the full index (FTS + dense + reranker) and the
ML deps (numpy, sentence-transformers). When the index is genuinely
missing — which is the default on fresh clones and CI without model
cache — the live suite skips cleanly so First-Run Protocol environments
are not blocked. A stale or corrupt index does *not* get the same pass:
those states fail the readiness contract so corpus churn during a
session cannot hide full-mode golden regressions behind a skip.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.learning.rag import indexer

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "cs_rag_golden_queries.json"


def _load_fixture_payload() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_readiness_contract() -> dict[str, str]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("live_readiness_contract", {})


def _full_mode_index_ready() -> bool:
    try:
        return indexer.is_ready(indexer.DEFAULT_INDEX_ROOT).state == "ready"
    except Exception:
        return False


def _describe_hash(value: str | None) -> str:
    return value or "missing"


def _require_live_full_mode_readiness(
    report: indexer.ReadinessReport | None = None,
) -> indexer.ReadinessReport:
    contract = _load_readiness_contract()
    if report is None:
        try:
            report = indexer.is_ready(indexer.DEFAULT_INDEX_ROOT)
        except Exception as exc:
            raise AssertionError(
                "CS RAG readiness probe failed before golden verification; "
                "do not treat readiness errors as skippable."
            ) from exc

    if report.state == "ready":
        return report

    next_command = report.next_command or "bin/cs-index-build"
    if contract.get(report.state, "fail") == "skip":
        raise unittest.SkipTest(f"CS RAG index not built — run {next_command}")

    rationale = contract.get(
        "rationale",
        "Stale or corrupt indexes can hide full-mode golden regressions.",
    )
    detail = ""
    if report.state == "stale":
        detail = (
            " Corpus/index hash mismatch: "
            f"corpus-hash={_describe_hash(report.corpus_hash)}, "
            f"manifest-hash={_describe_hash(report.index_manifest_hash)}."
        )
    raise AssertionError(
        f"CS RAG index is not fresh enough for golden verification "
        f"(state={report.state}, reason={report.reason}).{detail} {rationale} "
        f"Next step: {next_command}"
    )


class CsRagGoldenFixtureContract(unittest.TestCase):
    def test_readiness_contract_marks_stale_as_a_failure_not_a_skip(self) -> None:
        contract = _load_readiness_contract()

        self.assertEqual(contract.get("missing"), "skip")
        self.assertEqual(contract.get("stale"), "fail")
        self.assertEqual(contract.get("corrupt"), "fail")
        self.assertIn("golden regressions", contract.get("rationale", ""))

    def test_payment_ledger_idempotency_prompt_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("idempotency", queries_by_id)
        self.assertIn("payment_ledger_idempotency", queries_by_id)

        ledger_query = queries_by_id["payment_ledger_idempotency"]
        self.assertIn("payment ledger", ledger_query["prompt"])
        self.assertIn("reconciliation", ledger_query["prompt"])
        self.assertEqual(
            ledger_query["expected_path"],
            "contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md",
        )
        self.assertEqual(
            ledger_query.get("acceptable_paths"),
            ["contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md"],
        )
        self.assertEqual(ledger_query.get("max_rank"), 1)

    def test_key_store_replay_safe_retry_prompt_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("idempotency_key_store_replay_safe_retry", queries_by_id)

        key_store_query = queries_by_id["idempotency_key_store_replay_safe_retry"]
        self.assertIn("dedup-window", key_store_query["prompt"])
        self.assertIn("replay-safe-retry", key_store_query["prompt"])
        self.assertEqual(
            key_store_query["expected_path"],
            "contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md",
        )
        self.assertEqual(key_store_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", key_store_query)

    def test_key_store_dedup_window_lease_prompt_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("idempotency_key_store_dedup_window_lease", queries_by_id)

        key_store_query = queries_by_id["idempotency_key_store_dedup_window_lease"]
        self.assertIn("dedup-window", key_store_query["prompt"])
        self.assertIn("processing lease", key_store_query["prompt"])
        self.assertEqual(
            key_store_query["expected_path"],
            "contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md",
        )
        self.assertEqual(key_store_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", key_store_query)

    def test_key_store_request_log_retention_ttl_prompt_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("idempotency_key_store_request_log_retention_ttl", queries_by_id)

        key_store_query = queries_by_id["idempotency_key_store_request_log_retention_ttl"]
        self.assertIn("request-log retention", key_store_query["prompt"])
        self.assertIn("key TTL", key_store_query["prompt"])
        self.assertEqual(
            key_store_query["expected_path"],
            "contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md",
        )
        self.assertEqual(key_store_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", key_store_query)

    def test_cdc_schema_evolution_prompt_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("cdc_schema_evolution_expand_contract", queries_by_id)

        cdc_query = queries_by_id["cdc_schema_evolution_expand_contract"]
        self.assertIn("CDC schema evolution", cdc_query["prompt"])
        self.assertIn("expand-contract migration", cdc_query["prompt"])
        self.assertIn("forward compatible consumer", cdc_query["prompt"])
        self.assertEqual(
            cdc_query["expected_path"],
            "contents/database/cdc-schema-evolution-compatibility-playbook.md",
        )
        self.assertEqual(cdc_query.get("max_rank"), 3)
        self.assertNotIn("acceptable_paths", cdc_query)

    def test_column_retirement_cleanup_prompts_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("contract_remove_phase_destructive_cleanup", queries_by_id)
        cleanup_query = queries_by_id["contract_remove_phase_destructive_cleanup"]
        self.assertIn("contract/remove phase", cleanup_query["prompt"])
        self.assertIn("destructive schema cleanup", cleanup_query["prompt"])
        self.assertIn("retention/replay window", cleanup_query["prompt"])
        self.assertEqual(
            cleanup_query["expected_path"],
            "contents/database/destructive-schema-cleanup-column-retirement.md",
        )
        self.assertEqual(
            cleanup_query.get("acceptable_paths"),
            ["contents/database/cdc-schema-evolution-compatibility-playbook.md"],
        )
        self.assertEqual(cleanup_query.get("max_rank"), 3)

        self.assertIn("column_retirement_read_off_write_off_drop", queries_by_id)
        retirement_query = queries_by_id["column_retirement_read_off_write_off_drop"]
        self.assertIn("column retirement", retirement_query["prompt"])
        self.assertIn("read-off", retirement_query["prompt"])
        self.assertIn("field removal runbook", retirement_query["prompt"])
        self.assertEqual(
            retirement_query["expected_path"],
            "contents/database/destructive-schema-cleanup-column-retirement.md",
        )
        self.assertEqual(retirement_query.get("max_rank"), 3)
        self.assertNotIn("acceptable_paths", retirement_query)

    def test_lock_wait_timeout_prompt_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("innodb_lock_wait_timeout", queries_by_id)

        lock_wait_query = queries_by_id["innodb_lock_wait_timeout"]
        self.assertIn("lock wait timeout", lock_wait_query["prompt"])
        self.assertIn("next-key lock", lock_wait_query["prompt"])
        self.assertEqual(
            lock_wait_query["expected_path"],
            "contents/database/gap-lock-next-key-lock.md",
        )
        self.assertEqual(
            lock_wait_query.get("acceptable_paths"),
            ["contents/database/deadlock-case-study.md"],
        )
        self.assertNotIn(
            "contents/network/timeout-retry-backoff-practical.md",
            lock_wait_query.get("acceptable_paths", []),
        )
        self.assertEqual(lock_wait_query.get("max_rank"), 3)

    def test_introductory_primer_queries_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("java_runtime_intro_before_deep_dive", queries_by_id)
        java_runtime_query = queries_by_id["java_runtime_intro_before_deep_dive"]
        self.assertIn("처음 배우는데", java_runtime_query["prompt"])
        self.assertIn("classloader", java_runtime_query["prompt"])
        self.assertIn("큰 그림", java_runtime_query["prompt"])
        self.assertEqual(
            java_runtime_query["expected_path"],
            "contents/language/java/jvm-gc-jmm-overview.md",
        )
        self.assertEqual(java_runtime_query.get("max_rank"), 1)

        self.assertIn("java_concurrency_intro_before_executor_tuning", queries_by_id)
        java_concurrency_query = queries_by_id["java_concurrency_intro_before_executor_tuning"]
        self.assertIn("처음 배우는데", java_concurrency_query["prompt"])
        self.assertIn("queue rejection policy", java_concurrency_query["prompt"])
        self.assertIn("CountDownLatch", java_concurrency_query["prompt"])
        self.assertEqual(
            java_concurrency_query["expected_path"],
            "contents/language/java/java-concurrency-utilities.md",
        )
        self.assertEqual(java_concurrency_query.get("max_rank"), 1)

        self.assertIn("java_future_completablefuture_intro_overview", queries_by_id)
        java_future_query = queries_by_id["java_future_completablefuture_intro_overview"]
        self.assertIn("처음 배우는데", java_future_query["prompt"])
        self.assertIn("ExecutorService", java_future_query["prompt"])
        self.assertIn("Callable", java_future_query["prompt"])
        self.assertIn("CountDownLatch", java_future_query["prompt"])
        self.assertEqual(
            java_future_query["expected_path"],
            "contents/language/java/java-concurrency-utilities.md",
        )
        self.assertEqual(java_future_query.get("max_rank"), 1)

        self.assertIn("jwt_intro_validation_basics", queries_by_id)
        jwt_query = queries_by_id["jwt_intro_validation_basics"]
        self.assertIn("처음 배우는데", jwt_query["prompt"])
        self.assertIn("입문자", jwt_query["prompt"])
        self.assertEqual(
            jwt_query["expected_path"],
            "contents/security/jwt-deep-dive.md",
        )
        self.assertEqual(jwt_query.get("max_rank"), 1)

        self.assertIn("io_uring_intro_before_sq_cq", queries_by_id)
        io_uring_query = queries_by_id["io_uring_intro_before_sq_cq"]
        self.assertIn("처음 배우는데", io_uring_query["prompt"])
        self.assertIn("SQ CQ 보다", io_uring_query["prompt"])
        self.assertEqual(
            io_uring_query["expected_path"],
            "contents/operating-system/epoll-kqueue-io-uring.md",
        )
        self.assertEqual(io_uring_query.get("max_rank"), 1)

        self.assertIn("tx_intro_isolation_locking_primer", queries_by_id)
        tx_query = queries_by_id["tx_intro_isolation_locking_primer"]
        self.assertIn("처음 배우는데", tx_query["prompt"])
        self.assertIn("optimistic/pessimistic lock 전에", tx_query["prompt"])
        self.assertIn("read committed", tx_query["prompt"])
        self.assertEqual(
            tx_query["expected_path"],
            "contents/database/read-committed-vs-repeatable-read-anomalies.md",
        )
        self.assertEqual(tx_query.get("max_rank"), 1)

        self.assertIn("tx_lock_intro_optimistic_pessimistic_primer", queries_by_id)
        tx_lock_query = queries_by_id["tx_lock_intro_optimistic_pessimistic_primer"]
        self.assertIn("optimistic/pessimistic lock", tx_lock_query["prompt"])
        self.assertIn("처음 배우는데", tx_lock_query["prompt"])
        self.assertIn("큰 그림부터", tx_lock_query["prompt"])
        self.assertEqual(
            tx_lock_query["expected_path"],
            "contents/database/transaction-isolation-locking.md",
        )
        self.assertEqual(
            tx_lock_query.get("acceptable_paths"),
            ["contents/database/compare-and-swap-vs-pessimistic-locks.md"],
        )
        self.assertEqual(tx_lock_query.get("max_rank"), 3)

        self.assertIn("mvcc_intro_before_read_view_deep_dive", queries_by_id)
        mvcc_query = queries_by_id["mvcc_intro_before_read_view_deep_dive"]
        self.assertIn("처음 배우는데", mvcc_query["prompt"])
        self.assertIn("read view", mvcc_query["prompt"])
        self.assertIn("undo chain", mvcc_query["prompt"])
        self.assertEqual(
            mvcc_query["expected_path"],
            "contents/database/transaction-isolation-locking.md",
        )
        self.assertEqual(
            mvcc_query.get("acceptable_paths"),
            [
                "contents/database/read-committed-vs-repeatable-read-anomalies.md",
                "contents/database/mvcc-read-view-consistent-read-internals.md",
            ],
        )
        self.assertEqual(mvcc_query.get("max_rank"), 3)

        self.assertIn("projection_freshness_intro_before_cutover_playbooks", queries_by_id)
        projection_query = queries_by_id["projection_freshness_intro_before_cutover_playbooks"]
        self.assertIn("처음 배우는데", projection_query["prompt"])
        self.assertIn("read model cutover guardrails", projection_query["prompt"])
        self.assertIn("projection rebuild backfill cutover playbook", projection_query["prompt"])
        self.assertIn("stale read", projection_query["prompt"])
        self.assertEqual(
            projection_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(projection_query.get("max_rank"), 1)

    def test_java_direct_sibling_queries_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        explicit_paths = payload.get("_meta", {}).get("explicit_sibling_paths", [])

        self.assertIn(
            "contents/language/java/classloader-memory-leak-playbook.md",
            explicit_paths,
        )
        self.assertIn(
            "contents/language/java/jit-warmup-deoptimization.md",
            explicit_paths,
        )
        self.assertIn(
            "contents/language/java/executor-sizing-queue-rejection-policy.md",
            explicit_paths,
        )

        runtime_overview_query = queries_by_id["java_runtime_overview"]
        self.assertEqual(
            runtime_overview_query.get("acceptable_paths"),
            [
                "contents/language/java/classloader-memory-leak-playbook.md",
                "contents/language/java/jit-warmup-deoptimization.md",
            ],
        )

        self.assertIn("java_classloader_metaspace_leak_playbook", queries_by_id)
        classloader_query = queries_by_id["java_classloader_metaspace_leak_playbook"]
        self.assertIn("metaspace leak", classloader_query["prompt"])
        self.assertIn("thread context class loader", classloader_query["prompt"])
        self.assertIn("hot redeploy leak triage", classloader_query["prompt"])
        self.assertEqual(
            classloader_query["expected_path"],
            "contents/language/java/classloader-memory-leak-playbook.md",
        )
        self.assertEqual(classloader_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", classloader_query)

        self.assertIn("java_jit_warmup_deoptimization", queries_by_id)
        jit_query = queries_by_id["java_jit_warmup_deoptimization"]
        self.assertIn("tiered compilation", jit_query["prompt"])
        self.assertIn("profile pollution", jit_query["prompt"])
        self.assertIn("JIT warmup", jit_query["prompt"])
        self.assertEqual(
            jit_query["expected_path"],
            "contents/language/java/jit-warmup-deoptimization.md",
        )
        self.assertEqual(jit_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", jit_query)

        concurrency_overview_query = queries_by_id["java_concurrency_overview"]
        self.assertEqual(
            concurrency_overview_query.get("acceptable_paths"),
            ["contents/language/java/executor-sizing-queue-rejection-policy.md"],
        )

        self.assertIn("java_executor_sizing_queue_rejection", queries_by_id)
        executor_query = queries_by_id["java_executor_sizing_queue_rejection"]
        self.assertIn("executor sizing", executor_query["prompt"])
        self.assertIn("queue capacity", executor_query["prompt"])
        self.assertIn("worker saturation", executor_query["prompt"])
        self.assertEqual(
            executor_query["expected_path"],
            "contents/language/java/executor-sizing-queue-rejection-policy.md",
        )
        self.assertEqual(executor_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", executor_query)

        self.assertIn("java_completablefuture_common_pool_pitfalls", queries_by_id)
        common_pool_query = queries_by_id["java_completablefuture_common_pool_pitfalls"]
        self.assertIn("common pool", common_pool_query["prompt"])
        self.assertIn("default executor", common_pool_query["prompt"])
        self.assertIn("thread hopping", common_pool_query["prompt"])
        self.assertEqual(
            common_pool_query["expected_path"],
            "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
        )
        self.assertEqual(common_pool_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", common_pool_query)

    def test_java_virtual_thread_family_queries_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("java_virtual_threads_project_loom_intro", queries_by_id)
        intro_query = queries_by_id["java_virtual_threads_project_loom_intro"]
        self.assertIn("Project Loom", intro_query["prompt"])
        self.assertIn("virtual threads", intro_query["prompt"])
        self.assertIn("carrier thread", intro_query["prompt"])
        self.assertEqual(
            intro_query["expected_path"],
            "contents/language/java/virtual-threads-project-loom.md",
        )
        self.assertEqual(intro_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", intro_query)

        self.assertIn("java_virtual_thread_migration_boundaries", queries_by_id)
        migration_query = queries_by_id["java_virtual_thread_migration_boundaries"]
        self.assertIn("ThreadLocal", migration_query["prompt"])
        self.assertIn("pool boundary", migration_query["prompt"])
        self.assertEqual(
            migration_query["expected_path"],
            "contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md",
        )
        self.assertEqual(migration_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", migration_query)

        self.assertIn("java_connection_budget_alignment_after_loom", queries_by_id)
        budget_query = queries_by_id["java_connection_budget_alignment_after_loom"]
        self.assertIn("datasource pool sizing", budget_query["prompt"])
        self.assertIn("DB safe concurrency", budget_query["prompt"])
        self.assertIn("outbound HTTP bulkhead", budget_query["prompt"])
        self.assertEqual(
            budget_query["expected_path"],
            "contents/language/java/connection-budget-alignment-after-loom.md",
        )
        self.assertEqual(budget_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", budget_query)

        self.assertIn("java_jfr_loom_incident_signal_map", queries_by_id)
        incident_query = queries_by_id["java_jfr_loom_incident_signal_map"]
        self.assertIn("ThreadPark", incident_query["prompt"])
        self.assertIn("VirtualThreadPinned", incident_query["prompt"])
        self.assertIn("JavaMonitorEnter", incident_query["prompt"])
        self.assertEqual(
            incident_query["expected_path"],
            "contents/language/java/jfr-loom-incident-signal-map.md",
        )
        self.assertEqual(incident_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", incident_query)

    def test_deadlock_vs_gap_lock_boundary_prompts_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("mysql_deadlock_lock_ordering", queries_by_id)
        deadlock_query = queries_by_id["mysql_deadlock_lock_ordering"]
        self.assertIn("MySQL deadlock log", deadlock_query["prompt"])
        self.assertIn("lock ordering", deadlock_query["prompt"])
        self.assertEqual(
            deadlock_query["expected_path"],
            "contents/database/deadlock-case-study.md",
        )
        self.assertEqual(deadlock_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", deadlock_query)

        self.assertIn("innodb_lock_wait_timeout_range_locking", queries_by_id)
        gap_lock_query = queries_by_id["innodb_lock_wait_timeout_range_locking"]
        self.assertIn("lock wait timeout", gap_lock_query["prompt"])
        self.assertIn("range locking", gap_lock_query["prompt"])
        self.assertEqual(
            gap_lock_query["expected_path"],
            "contents/database/gap-lock-next-key-lock.md",
        )
        self.assertEqual(gap_lock_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", gap_lock_query)

    def test_overlap_engine_fallback_prompt_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("engine_fallback_overlap_enforcement", queries_by_id)
        overlap_query = queries_by_id["engine_fallback_overlap_enforcement"]
        self.assertIn("engine fallback overlap enforcement", overlap_query["prompt"])
        self.assertIn("예약 겹침 검사", overlap_query["prompt"])
        self.assertEqual(
            overlap_query["expected_path"],
            "contents/database/engine-fallbacks-overlap-enforcement.md",
        )
        self.assertEqual(
            overlap_query.get("acceptable_paths"),
            ["contents/database/gap-lock-next-key-lock.md"],
        )

    def test_upcaster_sibling_guardrail_prompts_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("event_upcaster_legacy_fixture_replay", queries_by_id)
        fixture_replay_query = queries_by_id["event_upcaster_legacy_fixture_replay"]
        self.assertIn("legacy fixture replay", fixture_replay_query["prompt"])
        self.assertIn("semantic versioned event", fixture_replay_query["prompt"])
        self.assertIn("upcast chain", fixture_replay_query["prompt"])
        self.assertEqual(
            fixture_replay_query["expected_path"],
            "contents/design-pattern/event-upcaster-compatibility-patterns.md",
        )
        self.assertEqual(fixture_replay_query.get("max_rank"), 1)

        self.assertIn("event_upcaster_snapshot_mixed_replay", queries_by_id)
        snapshot_query = queries_by_id["event_upcaster_snapshot_mixed_replay"]
        self.assertIn("snapshot", snapshot_query["prompt"])
        self.assertIn("혼합 replay", snapshot_query["prompt"])
        self.assertIn("event upcaster compatibility policy", snapshot_query["prompt"])
        self.assertEqual(
            snapshot_query["expected_path"],
            "contents/design-pattern/event-upcaster-compatibility-patterns.md",
        )
        self.assertEqual(snapshot_query.get("max_rank"), 1)

    def test_generic_schema_evolution_guardrail_prompts_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("api_schema_evolution_compatibility_layer", queries_by_id)
        api_query = queries_by_id["api_schema_evolution_compatibility_layer"]
        self.assertIn("REST API versioning", api_query["prompt"])
        self.assertIn("schema evolution", api_query["prompt"])
        self.assertIn("compatibility layer", api_query["prompt"])
        self.assertEqual(
            api_query["expected_path"],
            "contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md",
        )
        self.assertIn(
            "contents/software-engineering/schema-contract-evolution-cross-service.md",
            api_query.get("acceptable_paths", []),
        )
        self.assertEqual(api_query.get("max_rank"), 3)

        self.assertIn("schema_contract_evolution_cross_service", queries_by_id)
        schema_query = queries_by_id["schema_contract_evolution_cross_service"]
        self.assertIn("cross-service schema evolution", schema_query["prompt"])
        self.assertIn("backward compatible payload", schema_query["prompt"])
        self.assertIn("consumer tolerance", schema_query["prompt"])
        self.assertEqual(
            schema_query["expected_path"],
            "contents/software-engineering/schema-contract-evolution-cross-service.md",
        )
        self.assertIn(
            "contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md",
            schema_query.get("acceptable_paths", []),
        )
        self.assertEqual(schema_query.get("max_rank"), 3)

    def test_curated_high_frequency_sibling_paths_are_explicitly_tracked(self) -> None:
        payload = _load_fixture_payload()
        required_paths = payload.get("_meta", {}).get("explicit_sibling_paths", [])
        expected_paths = {query["expected_path"] for query in payload["queries"]}
        acceptable_paths = {
            path
            for query in payload["queries"]
            for path in (query.get("acceptable_paths") or [])
        }

        self.assertTrue(required_paths, "fixture must declare explicit_sibling_paths")

        failures: list[str] = []
        for path in required_paths:
            if path not in acceptable_paths:
                failures.append(f"{path}: missing from acceptable_paths coverage")
            if path not in expected_paths:
                failures.append(f"{path}: covered only by acceptable_paths; add explicit query")

        if failures:
            self.fail("\n".join(failures))


class CsRagGoldenReadinessGuardContract(unittest.TestCase):
    def test_missing_index_remains_skippable(self) -> None:
        report = indexer.ReadinessReport(
            state="missing",
            reason="first_run",
            corpus_hash=None,
            index_manifest_hash=None,
            next_command="bin/cs-index-build",
        )

        with self.assertRaises(unittest.SkipTest):
            _require_live_full_mode_readiness(report)

    def test_stale_index_fails_fast_instead_of_skipping(self) -> None:
        report = indexer.ReadinessReport(
            state="stale",
            reason="corpus_changed",
            corpus_hash="current",
            index_manifest_hash="old",
            next_command="bin/cs-index-build",
        )

        with self.assertRaisesRegex(AssertionError, "golden regressions") as exc_info:
            _require_live_full_mode_readiness(report)
        message = str(exc_info.exception)
        self.assertIn("corpus-hash=current", message)
        self.assertIn("manifest-hash=old", message)

    def test_corrupt_index_fails_fast_instead_of_skipping(self) -> None:
        report = indexer.ReadinessReport(
            state="corrupt",
            reason="index_corrupt",
            corpus_hash=None,
            index_manifest_hash=None,
            next_command="bin/cs-index-build",
        )

        with self.assertRaisesRegex(AssertionError, "state=corrupt"):
            _require_live_full_mode_readiness(report)

    def test_ready_index_allows_full_mode_verification(self) -> None:
        report = indexer.ReadinessReport(
            state="ready",
            reason="ready",
            corpus_hash="current",
            index_manifest_hash="current",
            next_command=None,
        )

        self.assertIs(_require_live_full_mode_readiness(report), report)


class CsRagGoldenLiveIndexContract(unittest.TestCase):
    def test_live_index_is_fresh_or_explicitly_missing(self) -> None:
        _require_live_full_mode_readiness()


@unittest.skipUnless(
    _full_mode_index_ready(),
    "CS RAG index not ready for full-mode golden checks — run bin/cs-index-build",
)
class CsRagGoldenQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import numpy  # noqa: F401
            import sentence_transformers  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(f"ML deps missing: {exc}")
        from scripts.learning.rag import searcher
        cls.searcher = searcher
        payload = _load_fixture_payload()
        cls.top_k = int(payload.get("_meta", {}).get("top_k", 5))
        cls.queries = payload["queries"]

    def test_every_query_keeps_expected_path_within_rank_budget(self) -> None:
        failures: list[str] = []
        for q in self.queries:
            hits = self.searcher.search(
                q["prompt"],
                learning_points=q.get("learning_points") or None,
                top_k=self.top_k,
                experience_level=q.get("experience_level"),
            )
            paths = [h["path"] for h in hits]
            accepted_paths = [q["expected_path"], *(q.get("acceptable_paths") or [])]
            ranked_matches = [
                (path, paths.index(path) + 1) for path in accepted_paths if path in paths
            ]
            if not ranked_matches:
                failures.append(
                    f"{q['id']}: expected one of {accepted_paths} "
                    f"not in top-{self.top_k} {paths}"
                )
                continue

            matched_path, rank = min(ranked_matches, key=lambda item: item[1])
            max_rank = int(q.get("max_rank", self.top_k))
            if rank > max_rank:
                failures.append(
                    f"{q['id']}: expected one of {accepted_paths} within top-{max_rank} "
                    f"(best match {matched_path}) "
                    f"but ranked #{rank} in {paths}"
                )
        if failures:
            self.fail("\n".join(failures))


if __name__ == "__main__":
    unittest.main()
