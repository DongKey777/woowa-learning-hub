"""Golden query → expected-path regression for the real CS RAG index.

Each entry in ``tests/fixtures/cs_rag_golden_queries.json`` asserts that
the expected path shows up in the top-K results for a handcrafted
prompt + learning_points pair. High-value entries may also declare a
``max_rank`` budget so we catch ranking drift, not just total misses.
Close sibling docs may also declare ``acceptable_paths`` so the fixture
locks in a retrieval family instead of overfitting to a single file when
the corpus grows. Broad discovery intents should prefer family/meta
contracts over exact companion paths; exact ``companion_paths`` are for
contrast prompts where the neighboring concept is part of the user intent.
The fixture is the source of truth for retrieval quality baselines — adding
a new curated query here is how we lock in a tuning win or catch a regression.

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

from scripts.learning.rag import corpus_loader, indexer, signal_rules

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "cs_rag_golden_queries.json"
_PROJECTION_BEGINNER_CONTRAST_QUERY_IDS = (
    "projection_freshness_intro_primer_vs_guardrail_compare",
    "projection_freshness_intro_primer_vs_rebuild_playbook_compare",
    "projection_freshness_intro_primer_vs_guardrail_and_rebuild_triad",
    "projection_freshness_intro_korean_only_primer_vs_guardrail_compare",
    "projection_freshness_intro_korean_only_primer_vs_rebuild_backfill_compare",
    "projection_freshness_intro_fully_korean_primer_vs_guardrail_compare",
    "projection_freshness_intro_fully_korean_primer_vs_rebuild_backfill_compare",
    "projection_freshness_intro_korean_phrase_only_primer_vs_guardrail_compare",
    "projection_freshness_intro_primer_vs_slo_lag_budget_compare",
    "projection_freshness_intro_korean_only_primer_vs_slo_lag_budget_compare",
    "projection_freshness_intro_fully_korean_primer_vs_slo_lag_budget_compare",
    "projection_freshness_intro_rollback_window_vs_transaction_rollback",
    "projection_freshness_intro_rollback_window_vs_korean_transaction_rollback",
    "projection_freshness_intro_korean_rollback_window_vs_korean_transaction_rollback",
    "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_compare",
    "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_distinguish",
    "projection_freshness_intro_full_korean_old_value_visible_rollback_compare",
    "projection_freshness_intro_full_korean_saved_not_visible_rollback_compare",
    "projection_freshness_intro_full_korean_cutover_safety_failover_rollback_compare",
    "projection_freshness_intro_full_korean_cutover_safety_key_rotation_rollback_compare",
    "projection_freshness_intro_cutover_safety_vs_failover_visibility_different",
    "projection_freshness_intro_mixed_cutover_safety_vs_failover_visibility_compare",
    "projection_freshness_intro_full_korean_cutover_safety_vs_failover_visibility_compare",
    "projection_freshness_intro_cutover_safety_vs_failover_rollback_compare",
    "projection_freshness_intro_vs_failover_compare",
    "projection_freshness_intro_vs_failover_visibility_compare",
    "projection_freshness_intro_vs_failover_visibility_alias_compare",
    "projection_freshness_intro_full_korean_projection_vs_visibility_window_compare",
    "projection_freshness_intro_vs_stateful_failover_placement_compare",
    "projection_freshness_intro_vs_failover_verification_compare",
    "projection_freshness_intro_failover_visibility_vs_write_loss_verification_compare",
    "projection_freshness_intro_cutover_safety_vs_key_rotation_rollback_compare",
)
_FAILOVER_DIVERGENCE_BEGINNER_ALIAS_QUERY_IDS = (
    "failover_stale_primary_beginner_alias",
    "failover_old_primary_read_beginner_alias",
    "failover_promotion_read_divergence_beginner_alias",
)
_SPRING_FOUNDATION_ROLE_BEGINNER_QUERY_IDS = (
    "beginner_applicationcontext_role_shortform_lockin",
    "beginner_spring_bean_role_shortform_lockin",
    "beginner_applicationcontext_english_role_shortform_lockin",
    "beginner_spring_bean_english_role_shortform_lockin",
    "beginner_beanfactory_english_role_shortform_lockin",
)
_BEGINNER_INFRA_PRIMER_QUERY_IDS = (
    "beginner_keepalive_shortform_lockin",
    "beginner_keepalive_colloquial_shortform_lockin",
    "beginner_keepalive_english_meaning_lockin",
    "beginner_keep_alive_spacing_shortform_lockin",
    "beginner_connection_pool_shortform_lockin",
    "beginner_connection_pool_colloquial_shortform_lockin",
    "beginner_connection_pooling_shortform_lockin",
    "beginner_connection_pooling_english_meaning_lockin",
    "beginner_hikaricp_shortform_lockin",
    "beginner_hikaricp_english_meaning_lockin",
    "beginner_hikaricp_korean_why_use_lockin",
)
_BEGINNER_QUERY_MODEL_BROAD_QUERY_IDS = (
    "beginner_query_model_shortform_lockin",
    "beginner_query_service_english_shortform_lockin",
    "beginner_query_service_korean_why_use_lockin",
)


def _load_fixture_payload() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_readiness_contract() -> dict[str, str]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("live_readiness_contract", {})


def _load_beginner_prompt_language_contracts() -> dict[str, dict[str, object]]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("beginner_prompt_language_contracts", {})


def _load_generic_crud_negative_projection_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("generic_crud_negative_projection_contracts", {})


def _load_stable_full_mode_fixture_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("stable_full_mode_fixture_queries", {})


def _load_projection_symptom_only_primer_family_batch_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("projection_symptom_only_primer_family_batch", {})


def _load_projection_symptom_only_search_regression_sweep_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("projection_symptom_only_search_regression_sweep", {})


def _generic_companion_family_contract_query_ids() -> set[str]:
    contract = _load_projection_symptom_only_primer_family_batch_contract()
    family_query_ids: set[str] = set(_BEGINNER_INFRA_PRIMER_QUERY_IDS)
    family_query_ids.update(_BEGINNER_QUERY_MODEL_BROAD_QUERY_IDS)
    if contract.get("generic_companion_policy") == "family_contract":
        family_query_ids.update(contract.get("query_ids") or [])
    return family_query_ids


def _load_projection_korean_failover_visibility_contrast_sweep_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("projection_korean_failover_visibility_contrast_sweep", {})


def _load_stateful_failover_beginner_contrast_sweep_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("stateful_failover_beginner_contrast_sweep", {})


def _load_live_readiness_diagnostics_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("live_readiness_diagnostics", {})


def _full_mode_index_ready() -> bool:
    try:
        return indexer.is_ready(indexer.DEFAULT_INDEX_ROOT).state == "ready"
    except Exception:
        return False


def _describe_hash(value: str | None) -> str:
    return value or "missing"


def _non_indexed_markdown_paths(
    corpus_root: Path | str = corpus_loader.DEFAULT_CORPUS_ROOT,
) -> list[str]:
    root = Path(corpus_root)
    indexed_paths = {chunk.path for chunk in corpus_loader.iter_corpus(root)}
    extra_paths: list[str] = []
    for md_path in sorted(root.rglob("*.md")):
        relpath = md_path.relative_to(root).as_posix()
        if relpath not in indexed_paths:
            extra_paths.append(relpath)
    return extra_paths


def _live_readiness_stale_diagnostic() -> str:
    contract = _load_live_readiness_diagnostics_contract()
    extra_paths = _non_indexed_markdown_paths()
    if not extra_paths:
        return ""
    sample = ", ".join(extra_paths[:3])
    scope_summary = contract.get(
        "scope_summary",
        "knowledge/cs 해시 범위와 실제 인덱싱 범위가 다릅니다.",
    )
    rebuild_note = contract.get(
        "rebuild_note",
        "Rebuild alone will not clear a stale report while those out-of-index markdown files keep changing.",
    )
    return (
        f" {scope_summary} Non-indexed markdown files still counted by the live hash: "
        f"{len(extra_paths)} total ({sample}). {rebuild_note}"
    )


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
        detail += _live_readiness_stale_diagnostic()
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

    def test_live_readiness_diagnostics_explain_hash_scope_drift(self) -> None:
        contract = _load_live_readiness_diagnostics_contract()
        extra_paths = _non_indexed_markdown_paths()

        self.assertIn("knowledge/cs/contents", contract.get("scope_summary", ""))
        rebuild_note = contract.get("rebuild_note", "")
        self.assertIn("Rebuild alone", rebuild_note)
        self.assertIn("flip back to stale immediately", rebuild_note)
        self.assertTrue(extra_paths)
        self.assertTrue(
            any(not path.startswith("contents/") for path in extra_paths),
            "live readiness diagnostics should keep at least one out-of-index culprit visible",
        )
        self.assertIn("Non-indexed markdown files", _live_readiness_stale_diagnostic())

    def test_stable_full_mode_fixture_queries_track_beginner_primer_paths(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        contract = _load_stable_full_mode_fixture_contract()

        self.assertIn("concurrent corpus churn", contract.get("description", ""))
        query_contracts = contract.get("queries", {})
        self.assertTrue(query_contracts)

        for query_id, query_contract in query_contracts.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("max_rank"), 1)
                self.assertTrue(
                    query.get("experience_level") == "beginner"
                    or "처음 배우는데" in query["prompt"]
                    or "입문자" in query["prompt"]
                )
                companion_paths = query_contract.get("companion_paths", [])
                self.assertTrue(companion_paths)
                self.assertNotIn(query["expected_path"], companion_paths)
                self.assertGreaterEqual(query_contract.get("companion_max_rank", 0), 2)

    def test_spring_foundation_role_shortform_queries_stay_on_beginner_primer_contract(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        for query_id in _SPRING_FOUNDATION_ROLE_BEGINNER_QUERY_IDS:
            with self.subTest(query_id=query_id):
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(
                    query.get("expected_path"),
                    "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
                )
                self.assertEqual(query.get("max_rank"), 1)
                self.assertTrue(
                    "뭐 하는 거야" in query["prompt"] or "What does" in query["prompt"]
                )
                self.assertIn(
                    "contents/spring/spring-bean-definition-overriding-semantics.md",
                    query.get("companion_paths", []),
                )

        english_role_expanded = signal_rules.expand_query(
            queries_by_id["beginner_applicationcontext_english_role_shortform_lockin"]["prompt"]
        )
        self.assertIn("applicationcontext role basics", english_role_expanded)
        self.assertIn("applicationcontext what it does", english_role_expanded)
        self.assertNotIn("refreshbeanfactory", english_role_expanded)

        bean_role_expanded = signal_rules.expand_query(
            queries_by_id["beginner_spring_bean_english_role_shortform_lockin"]["prompt"]
        )
        self.assertIn("spring bean role basics", bean_role_expanded)
        self.assertIn("spring bean what it does", bean_role_expanded)
        self.assertNotIn("beanfactorypostprocessor", bean_role_expanded)

    def test_beginner_infra_meaning_queries_stay_on_primer_contract(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})

        expected = {
            "beginner_keepalive_shortform_lockin": (
                "HTTP keep-alive 뭐야?",
                "contents/network/keepalive-connection-reuse-basics.md",
                "contents/network/http2-http3-connection-reuse-coalescing.md",
            ),
            "beginner_keepalive_colloquial_shortform_lockin": (
                "HTTP keep-alive 뭔데?",
                "contents/network/keepalive-connection-reuse-basics.md",
                "contents/network/http2-http3-connection-reuse-coalescing.md",
            ),
            "beginner_keepalive_english_meaning_lockin": (
                "What is HTTP keep-alive?",
                "contents/network/keepalive-connection-reuse-basics.md",
                "contents/network/http2-http3-connection-reuse-coalescing.md",
            ),
            "beginner_keep_alive_spacing_shortform_lockin": (
                "HTTP keep alive 뭐야?",
                "contents/network/keepalive-connection-reuse-basics.md",
                "contents/network/http2-http3-connection-reuse-coalescing.md",
            ),
            "beginner_connection_pool_shortform_lockin": (
                "connection pool 이 뭐야?",
                "contents/database/connection-pool-basics.md",
                "contents/database/transaction-locking-connection-pool-primer.md",
            ),
            "beginner_connection_pool_colloquial_shortform_lockin": (
                "connection pool 뭔데?",
                "contents/database/connection-pool-basics.md",
                "contents/database/transaction-locking-connection-pool-primer.md",
            ),
            "beginner_connection_pooling_shortform_lockin": (
                "connection pooling 이 뭐야?",
                "contents/database/connection-pool-basics.md",
                "contents/database/transaction-locking-connection-pool-primer.md",
            ),
            "beginner_connection_pooling_english_meaning_lockin": (
                "What is connection pooling?",
                "contents/database/connection-pool-basics.md",
                "contents/database/transaction-locking-connection-pool-primer.md",
            ),
            "beginner_hikaricp_shortform_lockin": (
                "HikariCP가 뭐야?",
                "contents/database/connection-pool-basics.md",
                "contents/database/transaction-locking-connection-pool-primer.md",
            ),
            "beginner_hikaricp_english_meaning_lockin": (
                "What is HikariCP?",
                "contents/database/connection-pool-basics.md",
                "contents/database/transaction-locking-connection-pool-primer.md",
            ),
            "beginner_hikaricp_korean_why_use_lockin": (
                "HikariCP 왜 써?",
                "contents/database/connection-pool-basics.md",
                "contents/database/transaction-locking-connection-pool-primer.md",
            ),
        }

        for query_id in _BEGINNER_INFRA_PRIMER_QUERY_IDS:
            with self.subTest(query_id=query_id):
                query = queries_by_id[query_id]
                prompt, expected_path, companion_path = expected[query_id]
                self.assertIn(query_id, stable_contract)
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(query.get("prompt"), prompt)
                self.assertEqual(query.get("expected_path"), expected_path)
                self.assertEqual(query.get("max_rank"), 1)
                self.assertIn(companion_path, query.get("companion_paths", []))
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    [companion_path],
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

    def test_projection_freshness_beginner_contrast_queries_keep_beginner_rank_one_contract(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        for query_id in _PROJECTION_BEGINNER_CONTRAST_QUERY_IDS:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                self.assertEqual(
                    queries_by_id[query_id].get("experience_level"),
                    "beginner",
                )
                self.assertEqual(queries_by_id[query_id].get("max_rank"), 1)

    def test_projection_freshness_beginner_navigator_bridge_query_keeps_neighbor_contract(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn(
            "projection_freshness_beginner_navigator_bridge_overview_neighbors",
            queries_by_id,
        )
        query = queries_by_id["projection_freshness_beginner_navigator_bridge_overview_neighbors"]
        self.assertEqual(query.get("experience_level"), "beginner")
        self.assertEqual(
            query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            query.get("companion_paths"),
            [
                "contents/design-pattern/read-model-cutover-guardrails.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(query.get("require_all_companion_paths"))
        self.assertEqual(query.get("companion_max_rank"), 3)
        self.assertEqual(query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_beginner_staleness_overview_neighbors",
            queries_by_id,
        )
        staleness_overview_query = queries_by_id[
            "projection_freshness_beginner_staleness_overview_neighbors"
        ]
        self.assertEqual(staleness_overview_query.get("experience_level"), "beginner")
        self.assertIn("staleness overview doc", staleness_overview_query["prompt"])
        self.assertIn("nearby docs", staleness_overview_query["prompt"])
        self.assertIn("CQRS 전체 overview 말고", staleness_overview_query["prompt"])
        self.assertEqual(
            staleness_overview_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )

        self.assertIn(
            "projection_freshness_beginner_overview_docs_sibling_docs_route_rejection",
            queries_by_id,
        )
        overview_docs_query = queries_by_id[
            "projection_freshness_beginner_overview_docs_sibling_docs_route_rejection"
        ]
        self.assertEqual(overview_docs_query.get("experience_level"), "beginner")
        self.assertIn("overview docs", overview_docs_query["prompt"])
        self.assertIn("nearby sibling docs", overview_docs_query["prompt"])
        self.assertIn("broad CQRS survey routes 말고", overview_docs_query["prompt"])
        self.assertEqual(
            overview_docs_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            overview_docs_query.get("companion_paths"),
            [
                "contents/design-pattern/read-model-cutover-guardrails.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(overview_docs_query.get("require_all_companion_paths"))
        self.assertEqual(overview_docs_query.get("companion_max_rank"), 3)
        self.assertEqual(overview_docs_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_beginner_entrypoint_bridge_siblings",
            queries_by_id,
        )
        entrypoint_bridge_query = queries_by_id[
            "projection_freshness_beginner_entrypoint_bridge_siblings"
        ]
        self.assertEqual(entrypoint_bridge_query.get("experience_level"), "beginner")
        self.assertIn("entrypoint primer", entrypoint_bridge_query["prompt"])
        self.assertIn("bridge docs", entrypoint_bridge_query["prompt"])
        self.assertIn("linked sibling docs", entrypoint_bridge_query["prompt"])
        self.assertIn("broad CQRS survey routes 말고", entrypoint_bridge_query["prompt"])
        self.assertEqual(
            entrypoint_bridge_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            entrypoint_bridge_query.get("companion_paths"),
            [
                "contents/design-pattern/read-model-cutover-guardrails.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(entrypoint_bridge_query.get("require_all_companion_paths"))
        self.assertEqual(entrypoint_bridge_query.get("companion_max_rank"), 3)
        self.assertEqual(entrypoint_bridge_query.get("max_rank"), 1)
        self.assertEqual(
            staleness_overview_query.get("companion_paths"),
            [
                "contents/design-pattern/read-model-cutover-guardrails.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(staleness_overview_query.get("require_all_companion_paths"))
        self.assertEqual(staleness_overview_query.get("companion_max_rank"), 3)
        self.assertEqual(staleness_overview_query.get("max_rank"), 1)

    def test_failover_divergence_beginner_alias_queries_keep_sibling_playbook_visible(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        for query_id in _FAILOVER_DIVERGENCE_BEGINNER_ALIAS_QUERY_IDS:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(
                    query["expected_path"],
                    "contents/database/failover-promotion-read-divergence.md",
                )

    def test_beginner_transactional_shortform_queries_keep_basics_primer_ahead_of_companion(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        expected_companion_paths = [
            "contents/spring/spring-transaction-propagation-deep-dive.md",
            "contents/spring/spring-transactional-self-invocation-test-bridge-primer.md",
        ]

        for query_id, prompt_cue in (
            ("beginner_transactional_shortform_lockin", "@Transactional 이 뭐야"),
            ("beginner_transactional_colloquial_shortform_lockin", "@Transactional 뭔데"),
            ("beginner_transactional_korean_meaning_lockin", "@Transactional 무슨 뜻이야"),
            ("beginner_transactional_english_shortform_lockin", "What is @Transactional"),
            ("beginner_transactional_english_plain_alias_lockin", "What is transactional in Spring"),
            (
                "beginner_transactional_english_meaning_alias_lockin",
                "What does transactional mean in Spring",
            ),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/spring/spring-transactional-basics.md",
                )
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(query.get("companion_paths"), expected_companion_paths)
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    expected_companion_paths,
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

    def test_beginner_spring_bean_container_shortform_queries_keep_foundation_primer_ahead(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        expected_companion_paths = [
            "contents/spring/spring-bean-definition-overriding-semantics.md",
        ]

        for query_id, prompt_cue in (
            ("beginner_spring_bean_shortform_lockin", "Spring bean 이 뭐야"),
            ("beginner_spring_bean_english_shortform_lockin", "What is a Spring bean"),
            (
                "beginner_spring_bean_english_meaning_shortform_lockin",
                "What does a Spring bean mean",
            ),
            (
                "beginner_spring_bean_english_role_shortform_lockin",
                "What does a Spring bean do",
            ),
            ("beginner_spring_bean_korean_definition_shortform_lockin", "Spring bean이란"),
            ("beginner_bean_korean_shortform_lockin", "빈이 뭐야"),
            ("beginner_applicationcontext_shortform_lockin", "ApplicationContext 가 뭐야"),
            (
                "beginner_applicationcontext_english_shortform_lockin",
                "What is ApplicationContext in Spring",
            ),
            (
                "beginner_applicationcontext_english_meaning_shortform_lockin",
                "What does ApplicationContext mean in Spring",
            ),
            (
                "beginner_applicationcontext_english_role_shortform_lockin",
                "What does ApplicationContext do in Spring",
            ),
            (
                "beginner_application_context_spacing_english_shortform_lockin",
                "What is Application Context in Spring",
            ),
            (
                "beginner_applicationcontext_korean_definition_shortform_lockin",
                "ApplicationContext란",
            ),
            ("beginner_beanfactory_shortform_lockin", "BeanFactory가 뭐야"),
            (
                "beginner_beanfactory_english_meaning_shortform_lockin",
                "What does BeanFactory mean in Spring",
            ),
            (
                "beginner_beanfactory_english_role_shortform_lockin",
                "What does BeanFactory do in Spring",
            ),
            (
                "beginner_bean_factory_spacing_english_shortform_lockin",
                "What is Bean Factory in Spring",
            ),
            (
                "beginner_beanfactory_vs_applicationcontext_shortform_lockin",
                "BeanFactory vs ApplicationContext 차이가 뭐야",
            ),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
                )
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(query.get("companion_paths"), expected_companion_paths)
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    expected_companion_paths,
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        expanded = signal_rules.expand_query(
            queries_by_id["beginner_applicationcontext_english_shortform_lockin"]["prompt"]
        )
        self.assertIn("applicationcontext beginner mental model", expanded)
        self.assertIn("spring request pipeline bean container foundations primer", expanded)
        self.assertIn("bean 컨테이너 큰 그림", expanded)
        self.assertNotIn("refreshbeanfactory", expanded)

    def test_beginner_component_scan_shortform_queries_keep_intro_primer_ahead(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        expected_companion_paths = [
            "contents/spring/spring-component-scan-failure-patterns.md",
        ]

        for query_id, prompt_cue in (
            ("beginner_component_scan_shortform_lockin", "component scan 이 뭐야"),
            (
                "beginner_component_scan_english_meaning_shortform_lockin",
                "What does component scan mean in Spring",
            ),
            (
                "beginner_component_scanning_english_shortform_lockin",
                "What is component scanning in Spring",
            ),
            (
                "beginner_component_scan_annotation_definition_shortform_lockin",
                "@ComponentScan이란",
            ),
            (
                "beginner_component_scan_vs_bean_registration_shortform_lockin",
                "@Bean이랑 component scan 차이가 뭐야",
            ),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/spring/spring-bean-di-basics.md",
                )
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(query.get("companion_paths"), expected_companion_paths)
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    expected_companion_paths,
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        expanded = signal_rules.expand_query(
            queries_by_id["beginner_component_scan_english_meaning_shortform_lockin"]["prompt"]
        )
        self.assertIn("spring bean di basics", expanded)
        self.assertIn("bean registration vs component scan", expanded)

    def test_beginner_dispatcherservlet_and_mvc_shortform_queries_keep_foundation_primer_ahead(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        expected_companion_paths = [
            "contents/spring/spring-mvc-request-lifecycle-basics.md",
            "contents/spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md",
        ]

        for query_id, prompt_cue in (
            ("beginner_dispatcherservlet_shortform_lockin", "DispatcherServlet 이 뭐야"),
            ("beginner_dispatcher_servlet_spacing_shortform_lockin", "Dispatcher Servlet 이 뭐야"),
            ("beginner_dispatcher_servlet_lowercase_shortform_lockin", "dispatcher servlet 이 뭐야"),
            ("beginner_dispatcherservlet_colloquial_shortform_lockin", "DispatcherServlet 뭔데"),
            (
                "beginner_dispatcherservlet_english_shortform_lockin",
                "What is DispatcherServlet in Spring",
            ),
            ("spring_mvc_shortform_beginner_primer", "Spring MVC 뭐야"),
            ("spring_mvc_english_shortform_beginner_primer", "What is Spring MVC"),
            ("spring_mvc_shortform_spacing_beginner_primer", "Spring M V C 뭐야"),
            ("spring_mvc_shortform_korean_spacing_beginner_primer", "스프링 M V C 뭐야"),
            ("spring_mvc_shortform_korean_alias_beginner_primer", "스프링 MVC 뭐야"),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
                )
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(query.get("companion_paths"), expected_companion_paths)
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    expected_companion_paths,
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        dispatcher_expanded = signal_rules.expand_query(
            queries_by_id["beginner_dispatcherservlet_english_shortform_lockin"]["prompt"]
        )
        self.assertIn("spring request pipeline bean container foundations primer", dispatcher_expanded)
        self.assertIn("dispatcher servlet bean container big picture", dispatcher_expanded)
        self.assertIn("요청 처리 흐름", dispatcher_expanded)
        self.assertIn("객체 준비 흐름", dispatcher_expanded)

        mvc_expanded = signal_rules.expand_query(
            queries_by_id["spring_mvc_english_shortform_beginner_primer"]["prompt"]
        )
        self.assertIn("spring mvc beginner mental model", mvc_expanded)
        self.assertIn("bean 컨테이너 큰 그림", mvc_expanded)

    def test_beginner_transaction_isolation_and_mvcc_shortforms_keep_basics_primer_ahead(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})

        expected_cases = {
            "beginner_transaction_isolation_shortform_basics": {
                "prompt_cue": "트랜잭션 격리 수준이 뭐예요",
                "companion_paths": [
                    "contents/database/transaction-isolation-locking.md",
                    "contents/database/read-committed-vs-repeatable-read-anomalies.md",
                ],
            },
            "beginner_mvcc_meaning_shortform_basics": {
                "prompt_cue": "MVCC가 뭐야",
                "companion_paths": [
                    "contents/database/transaction-isolation-locking.md",
                    "contents/database/mvcc-read-view-consistent-read-internals.md",
                ],
            },
        }

        for query_id, case in expected_cases.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(case["prompt_cue"], query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/database/transaction-isolation-basics.md",
                )
                self.assertEqual(query.get("companion_paths"), case["companion_paths"])
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    case["companion_paths"],
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        isolation_expanded = signal_rules.expand_query(
            queries_by_id["beginner_transaction_isolation_shortform_basics"]["prompt"]
        )
        self.assertIn("transaction isolation level basics", isolation_expanded)
        self.assertIn("read committed beginner", isolation_expanded)
        self.assertNotIn("optimistic lock", isolation_expanded)
        self.assertNotIn("pessimistic lock", isolation_expanded)

        mvcc_expanded = signal_rules.expand_query(
            queries_by_id["beginner_mvcc_meaning_shortform_basics"]["prompt"]
        )
        self.assertIn("mvcc 개념 설명", mvcc_expanded)
        self.assertIn("mvcc beginner", mvcc_expanded)
        self.assertNotIn("locking strategy", mvcc_expanded)
        self.assertNotIn("rollback", mvcc_expanded)

    def test_beginner_db_normalization_queries_keep_basics_primer_ahead_of_tradeoff_doc(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        expected_companion_paths = [
            "contents/database/normalization-denormalization-tradeoffs.md",
        ]

        for query_id, prompt_cue in (
            ("beginner_db_normalization_intro", "정규화가 뭐예요"),
            ("beginner_db_normalization_english_shortform_lockin", "What is database normalization"),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/database/normalization-basics.md",
                )
                self.assertEqual(query.get("companion_paths"), expected_companion_paths)
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    expected_companion_paths,
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        normalization_expanded = signal_rules.expand_query(
            queries_by_id["beginner_db_normalization_english_shortform_lockin"]["prompt"]
        )
        self.assertIn("database normalization basics", normalization_expanded)
        self.assertIn("normal form basics", normalization_expanded)
        self.assertNotIn("canonicalization", normalization_expanded)
        self.assertNotIn("scale normalization", normalization_expanded)

        normalization_hits = signal_rules.detect_signals(
            queries_by_id["beginner_db_normalization_english_shortform_lockin"]["prompt"]
        )
        self.assertEqual([hit["tag"] for hit in normalization_hits], ["db_modeling"])

    def test_beginner_ioc_and_dependency_injection_shortforms_keep_spring_basics_ahead(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        expected_companion_paths = [
            "contents/spring/ioc-di-container.md",
            "contents/software-engineering/dependency-injection-basics.md",
        ]

        for query_id, prompt_cue in (
            ("beginner_ioc_english_shortform_lockin", "What is IoC in Spring?"),
            (
                "beginner_inversion_of_control_english_shortform_lockin",
                "What is inversion of control in Spring?",
            ),
            (
                "beginner_inversion_of_control_korean_shortform_lockin",
                "제어 역전이 뭐야?",
            ),
            (
                "beginner_dependency_injection_korean_shortform_lockin",
                "의존성 주입이 뭐야?",
            ),
            (
                "beginner_dependency_injection_english_shortform_lockin",
                "What is dependency injection in Spring?",
            ),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/spring/spring-ioc-di-basics.md",
                )
                self.assertEqual(query.get("companion_paths"), expected_companion_paths)
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    expected_companion_paths,
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        ioc_expanded = signal_rules.expand_query(
            queries_by_id["beginner_ioc_english_shortform_lockin"]["prompt"]
        )
        self.assertIn("spring ioc di beginner primer", ioc_expanded)
        self.assertIn("ioc 제어 역전 입문", ioc_expanded)
        self.assertIn("spring 객체 조립 컨테이너", ioc_expanded)

        english_inversion_of_control_expanded = signal_rules.expand_query(
            queries_by_id["beginner_inversion_of_control_english_shortform_lockin"]["prompt"]
        )
        self.assertIn("spring ioc di beginner primer", english_inversion_of_control_expanded)
        self.assertIn("ioc 제어 역전 입문", english_inversion_of_control_expanded)
        self.assertIn("inversion of control", english_inversion_of_control_expanded)

        inversion_of_control_expanded = signal_rules.expand_query(
            queries_by_id["beginner_inversion_of_control_korean_shortform_lockin"]["prompt"]
        )
        self.assertIn("spring ioc di beginner primer", inversion_of_control_expanded)
        self.assertIn("ioc 제어 역전 입문", inversion_of_control_expanded)
        self.assertIn("inversion of control", inversion_of_control_expanded)

        dependency_injection_expanded = signal_rules.expand_query(
            queries_by_id["beginner_dependency_injection_english_shortform_lockin"]["prompt"]
        )
        self.assertIn("dependency injection 입문", dependency_injection_expanded)
        self.assertIn("의존성 주입이 뭐예요", dependency_injection_expanded)
        self.assertIn("테스트하기 좋은 코드 di", dependency_injection_expanded)
        self.assertNotIn("beanfactorypostprocessor", dependency_injection_expanded)

        korean_dependency_injection_expanded = signal_rules.expand_query(
            queries_by_id["beginner_dependency_injection_korean_shortform_lockin"]["prompt"]
        )
        self.assertIn("spring ioc di beginner primer", korean_dependency_injection_expanded)
        self.assertIn("dependency injection 입문", korean_dependency_injection_expanded)
        self.assertIn("의존성 주입이 뭐예요", korean_dependency_injection_expanded)
        self.assertNotIn("beanfactorypostprocessor", korean_dependency_injection_expanded)

    def test_beginner_spring_aop_shortform_query_keeps_aop_primer_ahead_of_proxy_deep_dive(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        for query_id, prompt_cue in (
            ("beginner_spring_aop_shortform_lockin", "Spring AOP가 뭐야"),
            ("beginner_spring_aop_english_why_use_lockin", "Why use Spring AOP?"),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/spring/spring-aop-basics.md",
                )
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(
                    query.get("companion_paths"),
                    ["contents/spring/aop-proxy-mechanism.md"],
                )
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    ["contents/spring/aop-proxy-mechanism.md"],
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        expanded = signal_rules.expand_query(
            queries_by_id["beginner_spring_aop_english_why_use_lockin"]["prompt"]
        )
        self.assertIn("why use spring aop", expanded)
        self.assertIn("spring aop beginner overview", expanded)
        self.assertIn("aspect oriented programming basics", expanded)
        self.assertNotIn("advisor pointcut advice", expanded)

    def test_beginner_hikaricp_korean_why_use_shortform_stays_on_connection_pool_primer(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})

        query_id = "beginner_hikaricp_korean_why_use_lockin"
        self.assertIn(query_id, queries_by_id)
        self.assertIn(query_id, stable_contract)

        query = queries_by_id[query_id]
        self.assertEqual(query.get("prompt"), "HikariCP 왜 써?")
        self.assertEqual(query.get("experience_level"), "beginner")
        self.assertEqual(query.get("expected_path"), "contents/database/connection-pool-basics.md")
        self.assertEqual(
            query.get("companion_paths"),
            ["contents/database/transaction-locking-connection-pool-primer.md"],
        )
        self.assertEqual(query.get("companion_max_rank"), 4)
        self.assertEqual(query.get("max_rank"), 1)
        self.assertEqual(
            stable_contract[query_id].get("companion_paths"),
            ["contents/database/transaction-locking-connection-pool-primer.md"],
        )
        self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

        expanded = signal_rules.expand_query(query["prompt"])
        self.assertIn("db connection pool beginner", expanded)
        self.assertIn("hikari cp beginner", expanded)
        self.assertIn("hikaricp basics", expanded)
        self.assertNotIn("resource lifecycle", expanded)

    def test_beginner_session_and_jwt_shortform_queries_keep_cookie_jwt_primer_ahead_of_foundations(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        stable_contract = _load_stable_full_mode_fixture_contract().get("queries", {})
        expected_companion_paths = [
            "contents/security/authentication-authorization-session-foundations.md",
        ]

        for query_id, prompt_cue in (
            ("beginner_session_vs_jwt_shortform_lockin", "세션이랑 JWT 차이가 뭐야"),
            ("beginner_session_shortform_lockin", "세션이 뭐야"),
            ("beginner_session_korean_meaning_lockin", "세션 무슨 뜻이야"),
            ("beginner_session_english_shortform_lockin", "What is session?"),
            ("beginner_session_vs_jwt_colloquial_shortform_lockin", "세션이랑 JWT 차이가 뭔데"),
            ("beginner_session_login_persistence_shortform_lockin", "세션이 왜 유지돼"),
            ("beginner_session_vs_jwt_english_shortform_lockin", "session vs JWT what is the difference"),
            ("beginner_jwt_meaning_english_shortform_lockin", "What does JWT mean?"),
        ):
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, stable_contract)
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertIn(prompt_cue, query["prompt"])
                self.assertEqual(
                    query["expected_path"],
                    "contents/security/session-cookie-jwt-basics.md",
                )
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(query.get("companion_paths"), expected_companion_paths)
                self.assertEqual(query.get("companion_max_rank"), 4)
                self.assertEqual(
                    stable_contract[query_id].get("companion_paths"),
                    expected_companion_paths,
                )
                self.assertEqual(stable_contract[query_id].get("companion_max_rank"), 4)

    def test_projection_symptom_only_primer_family_batch_contract_tracks_beginner_queries(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        contract = _load_projection_symptom_only_primer_family_batch_contract()

        description = contract.get("description", "")
        self.assertIn("Symptom-only projection prompts", description)
        self.assertIn("expansion-friendly", description)
        self.assertIn("top", description)
        query_ids = contract.get("query_ids", [])
        canonical_query_ids = contract.get("canonical_query_ids", [])
        family_paths = contract.get("family_paths", [])
        canonical_primer_path = contract.get("canonical_primer_path")

        self.assertGreaterEqual(len(query_ids), 3)
        self.assertTrue(set(canonical_query_ids).issubset(set(query_ids)))
        self.assertEqual(
            canonical_primer_path,
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertIn(canonical_primer_path, family_paths)
        self.assertGreaterEqual(contract.get("family_top_k", 0), 3)
        self.assertGreaterEqual(contract.get("min_family_hits", 0), 1)
        self.assertGreaterEqual(contract.get("canonical_max_rank", 0), 3)

        for query_id in query_ids:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(query["expected_path"], canonical_primer_path)
                self.assertTrue(query_id.startswith("projection_freshness_symptom_only_"))

    def test_projection_symptom_only_search_regression_sweep_tracks_small_beginner_batch(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        contract = _load_projection_symptom_only_search_regression_sweep_contract()

        self.assertIn("small beginner-safe projection sweep", contract.get("description", ""))
        query_ids = contract.get("query_ids", [])
        family_paths = contract.get("family_paths", [])
        primer_path = contract.get("primer_path")

        self.assertGreaterEqual(len(query_ids), 4)
        self.assertEqual(
            primer_path,
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertIn(primer_path, family_paths)
        self.assertEqual(contract.get("family_top_k"), 3)
        self.assertEqual(contract.get("primer_max_rank"), 3)

        for query_id in query_ids:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(query["expected_path"], primer_path)
                self.assertTrue(query_id.startswith("projection_freshness_symptom_only_"))

    def test_projection_korean_failover_visibility_contrast_sweep_tracks_non_english_beginner_query(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        contract = _load_projection_korean_failover_visibility_contrast_sweep_contract()

        self.assertIn("Korean-only beginner contrast prompts", contract.get("description", ""))
        query_ids = contract.get("query_ids", [])
        primer_path = contract.get("primer_path")
        companion_path = contract.get("companion_path")

        self.assertEqual(
            primer_path,
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            companion_path,
            "contents/database/failover-visibility-window-topology-cache-playbook.md",
        )
        self.assertEqual(contract.get("primer_max_rank"), 1)
        self.assertEqual(contract.get("companion_max_rank"), 3)
        self.assertTrue(query_ids)

        for query_id in query_ids:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(query["expected_path"], primer_path)
                self.assertEqual(query.get("companion_paths"), [companion_path])
                self.assertEqual(query.get("companion_max_rank"), 3)

    def test_stateful_failover_beginner_contrast_sweep_tracks_specific_sibling_order(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        contract = _load_stateful_failover_beginner_contrast_sweep_contract()

        self.assertIn("stateful failover placement doc ahead", contract.get("description", ""))
        query_ids = contract.get("query_ids", [])
        primary_path = contract.get("primary_path")
        companion_path = contract.get("companion_path")

        self.assertEqual(
            primary_path,
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md",
        )
        self.assertEqual(
            companion_path,
            "contents/system-design/global-traffic-failover-control-plane-design.md",
        )
        self.assertEqual(contract.get("primary_max_rank"), 1)
        self.assertEqual(contract.get("companion_max_rank"), 3)
        self.assertTrue(query_ids)

        for query_id in query_ids:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(query["expected_path"], primary_path)
                self.assertEqual(query.get("companion_paths"), [companion_path])
                self.assertEqual(query.get("max_rank"), 1)
                self.assertEqual(query.get("companion_max_rank"), 3)

    def test_korean_only_beginner_projection_primer_prompts_avoid_english_primer_vocab(
        self,
    ) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        contracts = _load_beginner_prompt_language_contracts()

        self.assertIn("korean_only_projection_freshness_primer_prompts", contracts)
        contract = contracts["korean_only_projection_freshness_primer_prompts"]
        query_ids = contract.get("query_ids", [])
        forbidden_terms = contract.get("forbidden_terms", [])

        self.assertTrue(query_ids)
        self.assertEqual(
            forbidden_terms,
            ["primer", "guardrail", "read model freshness", "read-your-writes"],
        )

        for query_id in query_ids:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                for term in forbidden_terms:
                    self.assertNotIn(term, query["prompt"])

        self.assertIn("korean_only_failover_visibility_contrast_primer_prompts", contracts)
        failover_contract = contracts["korean_only_failover_visibility_contrast_primer_prompts"]
        failover_query_ids = failover_contract.get("query_ids", [])
        failover_forbidden_terms = failover_contract.get("forbidden_terms", [])

        self.assertEqual(
            failover_forbidden_terms,
            ["projection freshness", "failover", "visibility", "window", "read-your-writes"],
        )

        for query_id in failover_query_ids:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                for term in failover_forbidden_terms:
                    self.assertNotIn(term, query["prompt"])

    def test_generic_korean_crud_prompts_are_locked_away_from_projection_primer(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}
        contract = _load_generic_crud_negative_projection_contract()

        self.assertIn("Generic Korean CRUD prompts", contract.get("description", ""))
        forbidden_path = contract.get("forbidden_path")
        query_ids = contract.get("query_ids", [])

        self.assertEqual(
            forbidden_path,
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertTrue(query_ids)

        for query_id in query_ids:
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertNotEqual(query["expected_path"], forbidden_path)
                self.assertLessEqual(query.get("max_rank", 99), 3)
                self.assertFalse(
                    any(
                        term in query["prompt"]
                        for term in ("읽기 모델", "예전 값", "옛값", "반영", "새로고침")
                    )
                )

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
        self.assertIn("Java 동시성을 처음 배우는데", java_future_query["prompt"])
        self.assertIn("관계", java_future_query["prompt"])
        self.assertIn("처음 배우는데", java_future_query["prompt"])
        self.assertIn("ExecutorService", java_future_query["prompt"])
        self.assertIn("Callable", java_future_query["prompt"])
        self.assertIn("CountDownLatch", java_future_query["prompt"])
        self.assertEqual(
            java_future_query["expected_path"],
            "contents/language/java/java-concurrency-utilities.md",
        )
        self.assertEqual(java_future_query.get("max_rank"), 1)
        self.assertEqual(
            java_future_query.get("companion_paths"),
            [
                "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
                "contents/language/java/executor-sizing-queue-rejection-policy.md",
            ],
        )
        self.assertEqual(java_future_query.get("companion_max_rank"), 4)

        self.assertIn("java_future_vs_completablefuture_beginner_shortform", queries_by_id)
        java_future_short_query = queries_by_id["java_future_vs_completablefuture_beginner_shortform"]
        self.assertIn("Future vs CompletableFuture", java_future_short_query["prompt"])
        self.assertIn("입문자용", java_future_short_query["prompt"])
        self.assertIn("common pool", java_future_short_query["prompt"])
        self.assertIn("overview", java_future_short_query["prompt"])
        self.assertEqual(
            java_future_short_query["expected_path"],
            "contents/language/java/java-concurrency-utilities.md",
        )
        self.assertEqual(java_future_short_query.get("experience_level"), "beginner")
        self.assertEqual(
            java_future_short_query.get("companion_paths"),
            [
                "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
            ],
        )
        self.assertEqual(java_future_short_query.get("companion_max_rank"), 4)
        self.assertEqual(java_future_short_query.get("max_rank"), 1)

        self.assertIn("jwt_basics", queries_by_id)
        jwt_basics_query = queries_by_id["jwt_basics"]
        self.assertIn("세션 쿠키", jwt_basics_query["prompt"])
        self.assertIn("로그인 상태", jwt_basics_query["prompt"])
        self.assertEqual(
            jwt_basics_query["expected_path"],
            "contents/security/session-cookie-jwt-basics.md",
        )
        self.assertEqual(
            jwt_basics_query.get("acceptable_paths"),
            [
                "contents/security/authentication-authorization-session-foundations.md",
                "contents/network/cookie-session-jwt-browser-flow-primer.md",
            ],
        )
        self.assertEqual(jwt_basics_query.get("max_rank"), 3)

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

        self.assertIn("mvcc_beginner_shortform_before_internals", queries_by_id)
        mvcc_short_query = queries_by_id["mvcc_beginner_shortform_before_internals"]
        self.assertEqual(mvcc_short_query.get("experience_level"), "beginner")
        self.assertIn("MVCC가 뭐야?", mvcc_short_query["prompt"])
        self.assertIn("read view", mvcc_short_query["prompt"])
        self.assertIn("큰 그림부터", mvcc_short_query["prompt"])
        self.assertEqual(
            mvcc_short_query["expected_path"],
            "contents/database/transaction-isolation-locking.md",
        )
        self.assertEqual(
            mvcc_short_query.get("companion_paths"),
            [
                "contents/database/read-committed-vs-repeatable-read-anomalies.md",
                "contents/database/mvcc-read-view-consistent-read-internals.md",
            ],
        )
        self.assertTrue(mvcc_short_query.get("require_all_companion_paths"))
        self.assertEqual(mvcc_short_query.get("companion_max_rank"), 4)
        self.assertEqual(mvcc_short_query.get("max_rank"), 1)

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

        self.assertIn("projection_freshness_intro_primer_vs_guardrail_compare", queries_by_id)
        primer_vs_guardrail_query = queries_by_id[
            "projection_freshness_intro_primer_vs_guardrail_compare"
        ]
        self.assertIn("stale read", primer_vs_guardrail_query["prompt"])
        self.assertIn("read-your-writes primer", primer_vs_guardrail_query["prompt"])
        self.assertIn("read model cutover guardrails", primer_vs_guardrail_query["prompt"])
        self.assertEqual(
            primer_vs_guardrail_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(primer_vs_guardrail_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_primer_vs_rebuild_playbook_compare",
            queries_by_id,
        )
        primer_vs_rebuild_query = queries_by_id[
            "projection_freshness_intro_primer_vs_rebuild_playbook_compare"
        ]
        self.assertIn("stale read", primer_vs_rebuild_query["prompt"])
        self.assertIn("read-your-writes primer", primer_vs_rebuild_query["prompt"])
        self.assertIn(
            "projection rebuild backfill cutover playbook",
            primer_vs_rebuild_query["prompt"],
        )
        self.assertEqual(
            primer_vs_rebuild_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(primer_vs_rebuild_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_primer_vs_guardrail_and_rebuild_triad",
            queries_by_id,
        )
        triad_query = queries_by_id[
            "projection_freshness_intro_primer_vs_guardrail_and_rebuild_triad"
        ]
        self.assertIn("stale read", triad_query["prompt"])
        self.assertIn("read-your-writes primer", triad_query["prompt"])
        self.assertIn("read model cutover guardrails", triad_query["prompt"])
        self.assertIn("projection rebuild backfill cutover playbook", triad_query["prompt"])
        self.assertEqual(
            triad_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(triad_query.get("experience_level"), "beginner")
        self.assertEqual(triad_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_korean_only_primer_vs_guardrail_compare",
            queries_by_id,
        )
        korean_primer_vs_guardrail_query = queries_by_id[
            "projection_freshness_intro_korean_only_primer_vs_guardrail_compare"
        ]
        self.assertIn("읽기 모델을 처음 배우는데", korean_primer_vs_guardrail_query["prompt"])
        self.assertIn("예전 값이 보여", korean_primer_vs_guardrail_query["prompt"])
        self.assertIn("쓴 직후 읽기", korean_primer_vs_guardrail_query["prompt"])
        self.assertIn("전환 안전 구간", korean_primer_vs_guardrail_query["prompt"])
        self.assertIn("운영 안전 규칙", korean_primer_vs_guardrail_query["prompt"])
        self.assertIn("비교", korean_primer_vs_guardrail_query["prompt"])
        self.assertNotIn("primer", korean_primer_vs_guardrail_query["prompt"])
        self.assertNotIn("stale read", korean_primer_vs_guardrail_query["prompt"])
        self.assertNotIn("read-your-writes", korean_primer_vs_guardrail_query["prompt"])
        self.assertNotIn("read model freshness", korean_primer_vs_guardrail_query["prompt"])
        self.assertNotIn("guardrail", korean_primer_vs_guardrail_query["prompt"])
        self.assertEqual(
            korean_primer_vs_guardrail_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_primer_vs_guardrail_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_korean_only_primer_vs_rebuild_backfill_compare",
            queries_by_id,
        )
        korean_primer_vs_rebuild_query = queries_by_id[
            "projection_freshness_intro_korean_only_primer_vs_rebuild_backfill_compare"
        ]
        self.assertIn("저장했는데도 예전 값이 보여서", korean_primer_vs_rebuild_query["prompt"])
        self.assertIn("쓴 직후 읽기 보장", korean_primer_vs_rebuild_query["prompt"])
        self.assertIn(
            "프로젝션 재빌드 백필 컷오버 안내",
            korean_primer_vs_rebuild_query["prompt"],
        )
        self.assertEqual(
            korean_primer_vs_rebuild_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_primer_vs_rebuild_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_fully_korean_primer_vs_guardrail_compare",
            queries_by_id,
        )
        fully_korean_guardrail_query = queries_by_id[
            "projection_freshness_intro_fully_korean_primer_vs_guardrail_compare"
        ]
        self.assertIn("읽기 모델 최신성을 처음 배우는데", fully_korean_guardrail_query["prompt"])
        self.assertIn("예전 값이 보여서", fully_korean_guardrail_query["prompt"])
        self.assertIn("방금 쓴 값 읽기 보장 설명", fully_korean_guardrail_query["prompt"])
        self.assertIn("전환 안전 구간 안내", fully_korean_guardrail_query["prompt"])
        self.assertIn("운영 안전 규칙", fully_korean_guardrail_query["prompt"])
        self.assertIn("비교", fully_korean_guardrail_query["prompt"])
        self.assertNotRegex(fully_korean_guardrail_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            fully_korean_guardrail_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(fully_korean_guardrail_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_fully_korean_primer_vs_rebuild_backfill_compare",
            queries_by_id,
        )
        fully_korean_rebuild_query = queries_by_id[
            "projection_freshness_intro_fully_korean_primer_vs_rebuild_backfill_compare"
        ]
        self.assertIn("읽기 모델 최신성을 처음 배우는데", fully_korean_rebuild_query["prompt"])
        self.assertIn("저장했는데도 예전 값이 보여서", fully_korean_rebuild_query["prompt"])
        self.assertIn("방금 쓴 값 읽기 보장 설명", fully_korean_rebuild_query["prompt"])
        self.assertIn("프로젝션 재빌드 백필 컷오버 안내", fully_korean_rebuild_query["prompt"])
        self.assertIn("운영 복구 문서", fully_korean_rebuild_query["prompt"])
        self.assertIn("비교", fully_korean_rebuild_query["prompt"])
        self.assertNotRegex(fully_korean_rebuild_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            fully_korean_rebuild_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(fully_korean_rebuild_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_korean_phrase_only_primer_vs_guardrail_compare",
            queries_by_id,
        )
        korean_phrase_only_query = queries_by_id[
            "projection_freshness_intro_korean_phrase_only_primer_vs_guardrail_compare"
        ]
        self.assertIn("읽기 모델을 처음 배우는데", korean_phrase_only_query["prompt"])
        self.assertIn("방금 저장했는데도 예전 값이 보여", korean_phrase_only_query["prompt"])
        self.assertIn("쓴 직후 읽기 보장 설명", korean_phrase_only_query["prompt"])
        self.assertIn("전환 안전 구간 안내", korean_phrase_only_query["prompt"])
        self.assertIn("기초 설명", korean_phrase_only_query["prompt"])
        self.assertIn("비교", korean_phrase_only_query["prompt"])
        self.assertNotIn("primer", korean_phrase_only_query["prompt"])
        self.assertNotIn("stale read", korean_phrase_only_query["prompt"])
        self.assertNotIn("read-your-writes", korean_phrase_only_query["prompt"])
        self.assertNotIn("read model freshness", korean_phrase_only_query["prompt"])
        self.assertNotIn("guardrail", korean_phrase_only_query["prompt"])
        self.assertEqual(
            korean_phrase_only_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_phrase_only_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_list_refresh_lag_primer",
            queries_by_id,
        )
        symptom_only_query = queries_by_id[
            "projection_freshness_symptom_only_list_refresh_lag_primer"
        ]
        self.assertIn("목록 새로고침이 느리고", symptom_only_query["prompt"])
        self.assertIn("이전 화면 상태", symptom_only_query["prompt"])
        self.assertNotIn("read-your-writes", symptom_only_query["prompt"])
        self.assertNotIn("CQRS", symptom_only_query["prompt"])
        self.assertEqual(
            symptom_only_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            symptom_only_query.get("companion_paths"),
            ["contents/design-pattern/projection-lag-budgeting-pattern.md"],
        )
        self.assertEqual(symptom_only_query.get("companion_max_rank"), 3)
        self.assertEqual(symptom_only_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_old_screen_state_primer",
            queries_by_id,
        )
        mixed_symptom_query = queries_by_id[
            "projection_freshness_symptom_only_old_screen_state_primer"
        ]
        self.assertIn("list refresh lag", mixed_symptom_query["prompt"])
        self.assertIn("old screen state", mixed_symptom_query["prompt"])
        self.assertIn("read model cutover guardrails", mixed_symptom_query["prompt"])
        self.assertNotIn("read-your-writes", mixed_symptom_query["prompt"])
        self.assertNotIn("stale read", mixed_symptom_query["prompt"])
        self.assertEqual(
            mixed_symptom_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(mixed_symptom_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_saved_not_visible_old_screen_state_korean",
            queries_by_id,
        )
        saved_not_visible_old_screen_state_query = queries_by_id[
            "projection_freshness_symptom_only_saved_not_visible_old_screen_state_korean"
        ]
        self.assertIn("저장했는데 안 보이고", saved_not_visible_old_screen_state_query["prompt"])
        self.assertIn("이전 화면 상태", saved_not_visible_old_screen_state_query["prompt"])
        self.assertNotRegex(saved_not_visible_old_screen_state_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            saved_not_visible_old_screen_state_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(saved_not_visible_old_screen_state_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_beginner_navigator_bridge_overview_neighbors",
            queries_by_id,
        )
        navigator_bridge_query = queries_by_id[
            "projection_freshness_beginner_navigator_bridge_overview_neighbors"
        ]
        self.assertIn("읽기 모델 projection", navigator_bridge_query["prompt"])
        self.assertIn("예전 값이 왜 보이는지", navigator_bridge_query["prompt"])
        self.assertIn("개요 문서", navigator_bridge_query["prompt"])
        self.assertIn("주변 형제 문서", navigator_bridge_query["prompt"])
        self.assertIn("CQRS 전체 survey 말고", navigator_bridge_query["prompt"])
        self.assertEqual(
            navigator_bridge_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            navigator_bridge_query.get("companion_paths"),
            [
                "contents/design-pattern/read-model-cutover-guardrails.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(navigator_bridge_query.get("require_all_companion_paths"))
        self.assertEqual(navigator_bridge_query.get("companion_max_rank"), 3)
        self.assertEqual(navigator_bridge_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_beginner_navigator_bridge_overview_neighbors_cqrs_overview_rejection",
            queries_by_id,
        )
        navigator_bridge_overview_rejection_query = queries_by_id[
            "projection_freshness_beginner_navigator_bridge_overview_neighbors_cqrs_overview_rejection"
        ]
        self.assertIn("옆 형제 문서", navigator_bridge_overview_rejection_query["prompt"])
        self.assertIn("CQRS 전체 개요 말고", navigator_bridge_overview_rejection_query["prompt"])
        self.assertEqual(
            navigator_bridge_overview_rejection_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            navigator_bridge_overview_rejection_query.get("companion_paths"),
            [
                "contents/design-pattern/read-model-cutover-guardrails.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(
            navigator_bridge_overview_rejection_query.get("require_all_companion_paths")
        )
        self.assertEqual(
            navigator_bridge_overview_rejection_query.get("companion_max_rank"), 3
        )
        self.assertEqual(navigator_bridge_overview_rejection_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_detail_updated_list_card_stale",
            queries_by_id,
        )
        detail_list_split_query = queries_by_id[
            "projection_freshness_symptom_only_detail_updated_list_card_stale"
        ]
        self.assertIn("상세는 바뀌었는데", detail_list_split_query["prompt"])
        self.assertIn("목록 카드만 예전 값", detail_list_split_query["prompt"])
        self.assertNotRegex(detail_list_split_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            detail_list_split_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(detail_list_split_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_detail_screen_updated_list_card_old_value",
            queries_by_id,
        )
        detail_screen_split_query = queries_by_id[
            "projection_freshness_symptom_only_detail_screen_updated_list_card_old_value"
        ]
        self.assertIn("상세 화면은 바뀌었는데", detail_screen_split_query["prompt"])
        self.assertIn("리스트 카드만 이전 값", detail_screen_split_query["prompt"])
        self.assertIn("저장 직후", detail_screen_split_query["prompt"])
        self.assertNotRegex(detail_screen_split_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            detail_screen_split_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(detail_screen_split_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_detail_updated_list_old_value",
            queries_by_id,
        )
        detail_list_old_value_query = queries_by_id[
            "projection_freshness_symptom_only_detail_updated_list_old_value"
        ]
        self.assertIn("상세는 바뀌었는데", detail_list_old_value_query["prompt"])
        self.assertIn("목록은 예전 값", detail_list_old_value_query["prompt"])
        self.assertNotIn("카드", detail_list_old_value_query["prompt"])
        self.assertNotRegex(detail_list_old_value_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            detail_list_old_value_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(detail_list_old_value_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_delete_still_visible_in_list",
            queries_by_id,
        )
        delete_list_query = queries_by_id[
            "projection_freshness_symptom_only_delete_still_visible_in_list"
        ]
        self.assertIn("삭제는 성공했는데", delete_list_query["prompt"])
        self.assertIn("목록에 계속 남아", delete_list_query["prompt"])
        self.assertIn("처음 배우는 사람 기준", delete_list_query["prompt"])
        self.assertEqual(
            delete_list_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(delete_list_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_symptom_only_delete_still_visible_in_search",
            queries_by_id,
        )
        delete_search_query = queries_by_id[
            "projection_freshness_symptom_only_delete_still_visible_in_search"
        ]
        self.assertIn("삭제했는데 검색 결과", delete_search_query["prompt"])
        self.assertIn("검색 결과나 목록", delete_search_query["prompt"])
        self.assertIn("입문자 기준", delete_search_query["prompt"])
        self.assertEqual(
            delete_search_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(delete_search_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_primer_vs_slo_lag_budget_compare",
            queries_by_id,
        )
        primer_vs_slo_budget_query = queries_by_id[
            "projection_freshness_intro_primer_vs_slo_lag_budget_compare"
        ]
        self.assertIn("stale read", primer_vs_slo_budget_query["prompt"])
        self.assertIn("read-your-writes primer", primer_vs_slo_budget_query["prompt"])
        self.assertIn("projection freshness SLO", primer_vs_slo_budget_query["prompt"])
        self.assertIn("projection lag budget", primer_vs_slo_budget_query["prompt"])
        self.assertEqual(
            primer_vs_slo_budget_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            primer_vs_slo_budget_query.get("companion_paths"),
            [
                "contents/design-pattern/projection-freshness-slo-pattern.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(primer_vs_slo_budget_query.get("require_all_companion_paths"))
        self.assertEqual(primer_vs_slo_budget_query.get("companion_max_rank"), 3)
        self.assertEqual(primer_vs_slo_budget_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_fully_korean_primer_vs_slo_lag_budget_compare",
            queries_by_id,
        )
        fully_korean_slo_budget_query = queries_by_id[
            "projection_freshness_intro_fully_korean_primer_vs_slo_lag_budget_compare"
        ]
        self.assertIn("읽기 모델을 처음 배우는데", fully_korean_slo_budget_query["prompt"])
        self.assertIn("저장했는데 예전 값이 보여", fully_korean_slo_budget_query["prompt"])
        self.assertIn("읽기 모델 최신성", fully_korean_slo_budget_query["prompt"])
        self.assertIn("서비스 수준 목표", fully_korean_slo_budget_query["prompt"])
        self.assertIn("반영 지연 예산", fully_korean_slo_budget_query["prompt"])
        self.assertIn("비교", fully_korean_slo_budget_query["prompt"])
        self.assertNotRegex(fully_korean_slo_budget_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            fully_korean_slo_budget_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            fully_korean_slo_budget_query.get("companion_paths"),
            [
                "contents/design-pattern/projection-freshness-slo-pattern.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(fully_korean_slo_budget_query.get("require_all_companion_paths"))
        self.assertEqual(fully_korean_slo_budget_query.get("companion_max_rank"), 3)
        self.assertEqual(fully_korean_slo_budget_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_korean_only_primer_vs_slo_lag_budget_compare",
            queries_by_id,
        )
        korean_only_slo_budget_query = queries_by_id[
            "projection_freshness_intro_korean_only_primer_vs_slo_lag_budget_compare"
        ]
        self.assertIn("읽기 모델을 처음 배우는데", korean_only_slo_budget_query["prompt"])
        self.assertIn("최신성 SLO", korean_only_slo_budget_query["prompt"])
        self.assertIn("지연 예산", korean_only_slo_budget_query["prompt"])
        self.assertEqual(
            korean_only_slo_budget_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(
            korean_only_slo_budget_query.get("companion_paths"),
            [
                "contents/design-pattern/projection-freshness-slo-pattern.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            ],
        )
        self.assertTrue(korean_only_slo_budget_query.get("require_all_companion_paths"))
        self.assertEqual(korean_only_slo_budget_query.get("companion_max_rank"), 3)
        self.assertEqual(korean_only_slo_budget_query.get("max_rank"), 1)

        for query_id in (
            "projection_freshness_intro_primer_vs_slo_lag_budget_compare",
            "projection_freshness_intro_korean_only_primer_vs_slo_lag_budget_compare",
            "projection_freshness_intro_fully_korean_primer_vs_slo_lag_budget_compare",
        ):
            expanded = signal_rules.expand_query(queries_by_id[query_id]["prompt"])
            self.assertIn("projection freshness slo pattern", expanded)
            self.assertIn("projection lag budgeting pattern", expanded)
            self.assertNotIn("replica lag", expanded)
            self.assertNotIn("read replica delay", expanded)
            self.assertNotIn("primary fallback", expanded)

        self.assertIn(
            "projection_freshness_advanced_slo_tuning_without_beginner_cues",
            queries_by_id,
        )
        advanced_slo_query = queries_by_id[
            "projection_freshness_advanced_slo_tuning_without_beginner_cues"
        ]
        self.assertIn("projection freshness SLO tuning", advanced_slo_query["prompt"])
        self.assertIn("consumer backlog budget", advanced_slo_query["prompt"])
        self.assertIn("projection watermark gap", advanced_slo_query["prompt"])
        self.assertIn("read-your-writes exception budget", advanced_slo_query["prompt"])
        self.assertEqual(
            advanced_slo_query["expected_path"],
            "contents/design-pattern/projection-freshness-slo-pattern.md",
        )
        self.assertEqual(
            advanced_slo_query.get("acceptable_paths"),
            ["contents/design-pattern/projection-lag-budgeting-pattern.md"],
        )
        self.assertEqual(advanced_slo_query.get("max_rank"), 1)

        self.assertIn("projection_freshness_intro_rollback_window_noise_guard", queries_by_id)
        rollback_query = queries_by_id["projection_freshness_intro_rollback_window_noise_guard"]
        self.assertIn("rollback window", rollback_query["prompt"])
        self.assertIn("stale read", rollback_query["prompt"])
        self.assertIn("read-your-writes", rollback_query["prompt"])
        self.assertEqual(
            rollback_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(rollback_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_rollback_window_vs_transaction_rollback",
            queries_by_id,
        )
        contrast_query = queries_by_id[
            "projection_freshness_intro_rollback_window_vs_transaction_rollback"
        ]
        self.assertIn("rollback window", contrast_query["prompt"])
        self.assertIn("transaction rollback", contrast_query["prompt"])
        self.assertIn("차이", contrast_query["prompt"])
        self.assertEqual(
            contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(contrast_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_rollback_window_vs_korean_transaction_rollback",
            queries_by_id,
        )
        korean_contrast_query = queries_by_id[
            "projection_freshness_intro_rollback_window_vs_korean_transaction_rollback"
        ]
        self.assertIn("rollback window", korean_contrast_query["prompt"])
        self.assertIn("트랜잭션 롤백", korean_contrast_query["prompt"])
        self.assertIn("차이", korean_contrast_query["prompt"])
        self.assertEqual(
            korean_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_contrast_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_korean_rollback_window_vs_korean_transaction_rollback",
            queries_by_id,
        )
        full_korean_contrast_query = queries_by_id[
            "projection_freshness_intro_korean_rollback_window_vs_korean_transaction_rollback"
        ]
        self.assertIn("롤백 윈도우", full_korean_contrast_query["prompt"])
        self.assertIn("트랜잭션 롤백", full_korean_contrast_query["prompt"])
        self.assertNotIn("rollback window", full_korean_contrast_query["prompt"])
        self.assertNotIn("transaction rollback", full_korean_contrast_query["prompt"])
        self.assertIn("차이", full_korean_contrast_query["prompt"])
        self.assertEqual(
            full_korean_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(full_korean_contrast_query.get("max_rank"), 1)

        synonym_cases = {
            "projection_freshness_intro_rollback_window_transaction_rollback_distinguish": "구분",
            "projection_freshness_intro_rollback_window_transaction_rollback_confusion": "헷갈림",
            "projection_freshness_intro_rollback_window_transaction_rollback_vs": "vs",
        }
        for query_id, cue in synonym_cases.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                synonym_query = queries_by_id[query_id]
                self.assertIn("rollback window", synonym_query["prompt"])
                self.assertIn("transaction rollback", synonym_query["prompt"])
                self.assertIn(cue, synonym_query["prompt"])
                self.assertIn("stale read", synonym_query["prompt"])
                self.assertIn("read-your-writes", synonym_query["prompt"])
                self.assertEqual(
                    synonym_query["expected_path"],
                    "contents/design-pattern/read-model-staleness-read-your-writes.md",
                )
                self.assertEqual(synonym_query.get("max_rank"), 1)

        self.assertIn(
            "transaction_rollback_window_korean_contrast_without_primer_cue",
            queries_by_id,
        )
        db_contrast_query = queries_by_id[
            "transaction_rollback_window_korean_contrast_without_primer_cue"
        ]
        self.assertIn("rollback window", db_contrast_query["prompt"])
        self.assertIn("트랜잭션 롤백", db_contrast_query["prompt"])
        self.assertNotIn("experience_level", db_contrast_query)
        self.assertEqual(
            db_contrast_query["expected_path"],
            "contents/database/transaction-isolation-locking.md",
        )
        self.assertEqual(
            db_contrast_query.get("acceptable_paths"),
            ["contents/database/transaction-boundary-isolation-locking-decision-framework.md"],
        )
        self.assertEqual(db_contrast_query.get("max_rank"), 2)

        self.assertIn(
            "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_compare",
            queries_by_id,
        )
        full_korean_beginner_query = queries_by_id[
            "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_compare"
        ]
        self.assertIn("읽기 모델 최신성", full_korean_beginner_query["prompt"])
        self.assertIn("롤백 윈도우", full_korean_beginner_query["prompt"])
        self.assertIn("트랜잭션 롤백", full_korean_beginner_query["prompt"])
        self.assertIn("예전 값이 보이고", full_korean_beginner_query["prompt"])
        self.assertIn("방금 쓴 값 읽기", full_korean_beginner_query["prompt"])
        self.assertEqual(
            full_korean_beginner_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(full_korean_beginner_query.get("experience_level"), "beginner")
        self.assertEqual(full_korean_beginner_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_distinguish",
            queries_by_id,
        )
        full_korean_distinguish_query = queries_by_id[
            "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_distinguish"
        ]
        self.assertIn("읽기 모델 최신성", full_korean_distinguish_query["prompt"])
        self.assertIn("롤백 윈도우", full_korean_distinguish_query["prompt"])
        self.assertIn("트랜잭션 롤백", full_korean_distinguish_query["prompt"])
        self.assertIn("어떻게 구분해야 해?", full_korean_distinguish_query["prompt"])
        self.assertIn("방금 쓴 값 읽기 보장", full_korean_distinguish_query["prompt"])
        self.assertNotRegex(full_korean_distinguish_query["prompt"], r"[A-Za-z]")
        self.assertEqual(
            full_korean_distinguish_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(full_korean_distinguish_query.get("experience_level"), "beginner")
        self.assertEqual(full_korean_distinguish_query.get("max_rank"), 1)

        full_korean_operational_contrast_cases = {
            "projection_freshness_intro_full_korean_cutover_safety_failover_rollback_compare": (
                "장애 전환 되돌리기"
            ),
            "projection_freshness_intro_full_korean_cutover_safety_key_rotation_rollback_compare": (
                "키 교체 되돌리기"
            ),
        }
        for query_id, contrast_phrase in full_korean_operational_contrast_cases.items():
            with self.subTest(query_id=query_id):
                operational_contrast_query = queries_by_id[query_id]
                self.assertIn("읽기 모델 최신성", operational_contrast_query["prompt"])
                self.assertIn("전환 안전 구간", operational_contrast_query["prompt"])
                self.assertIn(contrast_phrase, operational_contrast_query["prompt"])
                self.assertIn("예전 값이 보이고", operational_contrast_query["prompt"])
                self.assertIn("방금 쓴 값 읽기 보장", operational_contrast_query["prompt"])
                self.assertNotRegex(operational_contrast_query["prompt"], r"[A-Za-z]")
                self.assertEqual(
                    operational_contrast_query["expected_path"],
                    "contents/design-pattern/read-model-staleness-read-your-writes.md",
                )
                self.assertEqual(
                    operational_contrast_query.get("experience_level"), "beginner"
                )
                self.assertEqual(operational_contrast_query.get("max_rank"), 1)

        korean_synonym_cases = {
            "projection_freshness_intro_korean_rollback_window_transaction_rollback_compare": (
                "비교"
            ),
            "projection_freshness_intro_korean_rollback_window_transaction_rollback_distinguish": (
                "구분"
            ),
            "projection_freshness_intro_korean_rollback_window_transaction_rollback_confusion": (
                "헷갈림"
            ),
        }
        for query_id, cue in korean_synonym_cases.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                synonym_query = queries_by_id[query_id]
                self.assertIn("롤백 윈도우", synonym_query["prompt"])
                self.assertIn("트랜잭션 롤백", synonym_query["prompt"])
                self.assertNotIn("rollback window", synonym_query["prompt"])
                self.assertNotIn("transaction rollback", synonym_query["prompt"])
                self.assertIn(cue, synonym_query["prompt"])
                self.assertIn("stale read", synonym_query["prompt"])
                self.assertIn("read-your-writes", synonym_query["prompt"])
                self.assertEqual(
                    synonym_query["expected_path"],
                    "contents/design-pattern/read-model-staleness-read-your-writes.md",
                )
                self.assertEqual(synonym_query.get("max_rank"), 1)

        self.assertIn("projection_freshness_intro_korean_synonyms", queries_by_id)
        korean_query = queries_by_id["projection_freshness_intro_korean_synonyms"]
        self.assertIn("롤백 윈도우", korean_query["prompt"])
        self.assertIn("예전 값이 보임", korean_query["prompt"])
        self.assertIn("쓴 직후 읽기", korean_query["prompt"])
        self.assertEqual(
            korean_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_query.get("max_rank"), 1)

        self.assertIn("projection_freshness_intro_korean_saved_not_visible", queries_by_id)
        saved_not_visible_query = queries_by_id[
            "projection_freshness_intro_korean_saved_not_visible"
        ]
        self.assertIn("방금 저장했는데 안 보여", saved_not_visible_query["prompt"])
        self.assertIn("옛값이 보여", saved_not_visible_query["prompt"])
        self.assertEqual(
            saved_not_visible_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(saved_not_visible_query.get("max_rank"), 1)

        compact_beginner_cases = {
            "projection_freshness_intro_korean_old_value_only_visible": "옛값만 보여",
            "projection_freshness_intro_korean_list_not_changing_compact": "목록이 안 바뀜",
            "projection_freshness_intro_korean_recent_write_not_visible_compact": "방금 쓴 값이 안 보임",
        }
        for query_id, prompt in compact_beginner_cases.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                symptom_query = queries_by_id[query_id]
                self.assertEqual(symptom_query["prompt"], prompt)
                self.assertEqual(
                    symptom_query["expected_path"],
                    "contents/design-pattern/read-model-staleness-read-your-writes.md",
                )
                self.assertEqual(symptom_query.get("experience_level"), "beginner")
                self.assertEqual(symptom_query.get("max_rank"), 1)

        self.assertIn("projection_freshness_intro_korean_cache_confusion", queries_by_id)
        cache_confusion_query = queries_by_id["projection_freshness_intro_korean_cache_confusion"]
        self.assertIn("방금 저장했는데도 예전 값이 보여", cache_confusion_query["prompt"])
        self.assertIn("캐시 때문인가요", cache_confusion_query["prompt"])
        self.assertEqual(
            cache_confusion_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(cache_confusion_query.get("max_rank"), 1)

        self.assertIn("projection_freshness_intro_korean_write_read_mismatch", queries_by_id)
        write_read_mismatch_query = queries_by_id[
            "projection_freshness_intro_korean_write_read_mismatch"
        ]
        self.assertIn("저장은 됐는데 조회가 달라", write_read_mismatch_query["prompt"])
        self.assertEqual(
            write_read_mismatch_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(write_read_mismatch_query.get("max_rank"), 1)

        self.assertIn("projection_freshness_intro_korean_stale_list_after_update", queries_by_id)
        stale_list_query = queries_by_id[
            "projection_freshness_intro_korean_stale_list_after_update"
        ]
        self.assertIn("수정했는데 목록은 그대로야", stale_list_query["prompt"])
        self.assertEqual(
            stale_list_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(stale_list_query.get("max_rank"), 1)

        no_jargon_symptom_cases = {
            "projection_freshness_symptom_only_no_jargon_list_stuck": [
                "목록이 바로 안 바뀌고",
                "예전 화면이 잠깐 보여",
                "큰 그림부터",
            ],
            "projection_freshness_symptom_only_no_jargon_delayed_screen": [
                "새로고침 전까지 이전 상태가 보이고",
                "화면 반영이 한참 늦어",
                "입문자 기준",
            ],
        }
        jargon_tokens = ("read model", "read-your-writes", "projection", "읽기 모델")
        for query_id, cues in no_jargon_symptom_cases.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                symptom_query = queries_by_id[query_id]
                for cue in cues:
                    self.assertIn(cue, symptom_query["prompt"])
                for jargon in jargon_tokens:
                    self.assertNotIn(jargon, symptom_query["prompt"])
                self.assertEqual(
                    symptom_query["expected_path"],
                    "contents/design-pattern/read-model-staleness-read-your-writes.md",
                )
                self.assertEqual(symptom_query.get("experience_level"), "beginner")
                self.assertEqual(symptom_query.get("max_rank"), 1)

        fixture_anchor_cases = {
            "projection_freshness_intro_korean_query_old_data": "저장 직후 조회하면 예전 데이터가 보임",
            "projection_freshness_intro_korean_list_not_refreshing": "저장 직후 목록 최신화가 안 됨",
            "projection_freshness_intro_korean_list_still_same": "저장했는데 목록이 그대로",
            "projection_freshness_intro_korean_old_list_on_screen": "수정했는데 화면엔 예전 목록이 보여",
            "projection_freshness_intro_korean_screen_update_late": "저장한 뒤 화면 반영이 늦음",
        }
        for query_id, cue in fixture_anchor_cases.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                symptom_query = queries_by_id[query_id]
                self.assertIn(cue, symptom_query["prompt"])
                self.assertEqual(
                    symptom_query["expected_path"],
                    "contents/design-pattern/read-model-staleness-read-your-writes.md",
                )
                self.assertEqual(symptom_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_cutover_safety_failover_rollback_noise_guard",
            queries_by_id,
        )
        failover_noise_query = queries_by_id[
            "projection_freshness_intro_cutover_safety_failover_rollback_noise_guard"
        ]
        self.assertIn("cutover safety window", failover_noise_query["prompt"])
        self.assertIn("failover rollback", failover_noise_query["prompt"])
        self.assertIn("큰 그림부터", failover_noise_query["prompt"])
        self.assertEqual(
            failover_noise_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(failover_noise_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", failover_noise_query)

        self.assertIn(
            "projection_freshness_intro_cutover_safety_vs_failover_visibility_different",
            queries_by_id,
        )
        failover_contrast_query = queries_by_id[
            "projection_freshness_intro_cutover_safety_vs_failover_visibility_different"
        ]
        self.assertIn("cutover safety window", failover_contrast_query["prompt"])
        self.assertIn("failover visibility window", failover_contrast_query["prompt"])
        self.assertIn("다른지", failover_contrast_query["prompt"])
        self.assertEqual(
            failover_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(failover_contrast_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", failover_contrast_query)

        self.assertIn(
            "projection_freshness_intro_cutover_safety_vs_failover_rollback_compare",
            queries_by_id,
        )
        failover_rollback_contrast_query = queries_by_id[
            "projection_freshness_intro_cutover_safety_vs_failover_rollback_compare"
        ]
        self.assertIn("cutover safety window", failover_rollback_contrast_query["prompt"])
        self.assertIn("failover rollback", failover_rollback_contrast_query["prompt"])
        self.assertIn("비교", failover_rollback_contrast_query["prompt"])
        self.assertEqual(
            failover_rollback_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(failover_rollback_contrast_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", failover_rollback_contrast_query)

        self.assertIn(
            "projection_freshness_intro_korean_cutover_safety_window_key_rotation_noise_guard",
            queries_by_id,
        )
        korean_key_rotation_noise_query = queries_by_id[
            "projection_freshness_intro_korean_cutover_safety_window_key_rotation_noise_guard"
        ]
        self.assertIn("읽기 모델을 처음 배우는데", korean_key_rotation_noise_query["prompt"])
        self.assertIn("전환 안전 윈도우", korean_key_rotation_noise_query["prompt"])
        self.assertIn("예전 값이 보이고", korean_key_rotation_noise_query["prompt"])
        self.assertIn("쓴 직후 읽기 보장", korean_key_rotation_noise_query["prompt"])
        self.assertIn("key rotation rollback", korean_key_rotation_noise_query["prompt"])
        self.assertIn("큰 그림부터", korean_key_rotation_noise_query["prompt"])
        self.assertEqual(
            korean_key_rotation_noise_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_key_rotation_noise_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", korean_key_rotation_noise_query)

        self.assertIn(
            "projection_freshness_intro_full_korean_cutover_safety_window_korean_key_rotation_noise_guard",
            queries_by_id,
        )
        full_korean_key_rotation_noise_query = queries_by_id[
            "projection_freshness_intro_full_korean_cutover_safety_window_korean_key_rotation_noise_guard"
        ]
        self.assertIn("읽기 모델 최신성을 처음 배우는데", full_korean_key_rotation_noise_query["prompt"])
        self.assertIn("전환 안전 윈도우", full_korean_key_rotation_noise_query["prompt"])
        self.assertIn("예전 값이 보이고", full_korean_key_rotation_noise_query["prompt"])
        self.assertIn("방금 쓴 값 읽기 보장", full_korean_key_rotation_noise_query["prompt"])
        self.assertIn("키 교체 되돌리기", full_korean_key_rotation_noise_query["prompt"])
        self.assertIn("큰 그림부터", full_korean_key_rotation_noise_query["prompt"])
        self.assertEqual(
            full_korean_key_rotation_noise_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(full_korean_key_rotation_noise_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", full_korean_key_rotation_noise_query)

        self.assertIn("projection_freshness_intro_vs_failover_compare", queries_by_id)
        generic_failover_contrast_query = queries_by_id[
            "projection_freshness_intro_vs_failover_compare"
        ]
        self.assertIn("projection freshness", generic_failover_contrast_query["prompt"])
        self.assertIn("failover", generic_failover_contrast_query["prompt"])
        self.assertIn("비교", generic_failover_contrast_query["prompt"])
        self.assertEqual(
            generic_failover_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(generic_failover_contrast_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", generic_failover_contrast_query)

        self.assertIn("projection_freshness_intro_vs_failover_visibility_compare", queries_by_id)
        visibility_contrast_query = queries_by_id[
            "projection_freshness_intro_vs_failover_visibility_compare"
        ]
        self.assertIn("projection freshness", visibility_contrast_query["prompt"])
        self.assertIn("failover visibility window", visibility_contrast_query["prompt"])
        self.assertIn("차이", visibility_contrast_query["prompt"])
        self.assertEqual(
            visibility_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(visibility_contrast_query.get("max_rank"), 1)
        self.assertEqual(
            visibility_contrast_query.get("companion_paths"),
            ["contents/database/failover-visibility-window-topology-cache-playbook.md"],
        )
        self.assertEqual(visibility_contrast_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", visibility_contrast_query)

        self.assertIn(
            "projection_freshness_intro_vs_failover_visibility_alias_compare",
            queries_by_id,
        )
        visibility_alias_query = queries_by_id[
            "projection_freshness_intro_vs_failover_visibility_alias_compare"
        ]
        self.assertIn("읽기 모델을 처음 배우는데", visibility_alias_query["prompt"])
        self.assertIn("projection freshness", visibility_alias_query["prompt"])
        self.assertIn("failover visibility", visibility_alias_query["prompt"])
        self.assertNotIn("failover visibility window", visibility_alias_query["prompt"])
        self.assertEqual(
            visibility_alias_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(visibility_alias_query.get("max_rank"), 1)
        self.assertEqual(
            visibility_alias_query.get("companion_paths"),
            ["contents/database/failover-visibility-window-topology-cache-playbook.md"],
        )
        self.assertEqual(visibility_alias_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", visibility_alias_query)

        self.assertIn(
            "projection_freshness_intro_full_korean_projection_vs_visibility_window_compare",
            queries_by_id,
        )
        korean_visibility_alias_query = queries_by_id[
            "projection_freshness_intro_full_korean_projection_vs_visibility_window_compare"
        ]
        self.assertIn("읽기 모델 최신성을 처음 배우는데", korean_visibility_alias_query["prompt"])
        self.assertIn("투영 최신성", korean_visibility_alias_query["prompt"])
        self.assertIn("장애 전환 뒤 읽기 보임 구간", korean_visibility_alias_query["prompt"])
        self.assertIn("저장 직후엔 예전 값", korean_visibility_alias_query["prompt"])
        self.assertIn("옛 주 서버", korean_visibility_alias_query["prompt"])
        self.assertNotIn("failover", korean_visibility_alias_query["prompt"])
        self.assertNotIn("visibility", korean_visibility_alias_query["prompt"])
        self.assertNotIn("window", korean_visibility_alias_query["prompt"])
        self.assertEqual(
            korean_visibility_alias_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_visibility_alias_query.get("max_rank"), 1)
        self.assertEqual(
            korean_visibility_alias_query.get("companion_paths"),
            ["contents/database/failover-visibility-window-topology-cache-playbook.md"],
        )
        self.assertEqual(korean_visibility_alias_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", korean_visibility_alias_query)

        self.assertIn(
            "projection_freshness_intro_full_korean_cutover_safety_vs_failover_visibility_compare",
            queries_by_id,
        )
        korean_visibility_contrast_query = queries_by_id[
            "projection_freshness_intro_full_korean_cutover_safety_vs_failover_visibility_compare"
        ]
        self.assertIn("읽기 모델 최신성", korean_visibility_contrast_query["prompt"])
        self.assertIn("전환 안전 윈도우", korean_visibility_contrast_query["prompt"])
        self.assertIn("failover visibility window", korean_visibility_contrast_query["prompt"])
        self.assertIn("차이", korean_visibility_contrast_query["prompt"])
        self.assertIn("예전 값이 보이고", korean_visibility_contrast_query["prompt"])
        self.assertIn("방금 쓴 값 읽기 보장", korean_visibility_contrast_query["prompt"])
        self.assertEqual(
            korean_visibility_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_visibility_contrast_query.get("max_rank"), 1)
        self.assertEqual(
            korean_visibility_contrast_query.get("companion_paths"),
            ["contents/database/failover-visibility-window-topology-cache-playbook.md"],
        )
        self.assertEqual(korean_visibility_contrast_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", korean_visibility_contrast_query)

        self.assertIn(
            "projection_freshness_intro_vs_stateful_failover_placement_compare",
            queries_by_id,
        )
        stateful_contrast_query = queries_by_id[
            "projection_freshness_intro_vs_stateful_failover_placement_compare"
        ]
        self.assertIn("projection freshness", stateful_contrast_query["prompt"])
        self.assertIn("stateful failover placement", stateful_contrast_query["prompt"])
        self.assertIn("차이", stateful_contrast_query["prompt"])
        self.assertEqual(
            stateful_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(stateful_contrast_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", stateful_contrast_query)

        self.assertIn(
            "stateful_failover_beginner_compare_vs_global_failover_control_plane",
            queries_by_id,
        )
        stateful_vs_global_query = queries_by_id[
            "stateful_failover_beginner_compare_vs_global_failover_control_plane"
        ]
        self.assertIn("global traffic failover", stateful_vs_global_query["prompt"])
        self.assertIn(
            "stateful workload placement failover control plane",
            stateful_vs_global_query["prompt"],
        )
        self.assertIn("leader placement", stateful_vs_global_query["prompt"])
        self.assertIn("placement budget", stateful_vs_global_query["prompt"])
        self.assertEqual(stateful_vs_global_query.get("experience_level"), "beginner")
        self.assertEqual(
            stateful_vs_global_query["expected_path"],
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md",
        )
        self.assertEqual(stateful_vs_global_query.get("max_rank"), 1)
        self.assertEqual(
            stateful_vs_global_query.get("companion_paths"),
            ["contents/system-design/global-traffic-failover-control-plane-design.md"],
        )
        self.assertEqual(stateful_vs_global_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", stateful_vs_global_query)

        self.assertIn(
            "stateful_failover_beginner_korean_compare_vs_global_failover",
            queries_by_id,
        )
        korean_stateful_vs_global_query = queries_by_id[
            "stateful_failover_beginner_korean_compare_vs_global_failover"
        ]
        self.assertIn("전역 트래픽 우회", korean_stateful_vs_global_query["prompt"])
        self.assertIn("상태 있는 워크로드 배치", korean_stateful_vs_global_query["prompt"])
        self.assertIn("regional evacuation", korean_stateful_vs_global_query["prompt"])
        self.assertIn("shard owner", korean_stateful_vs_global_query["prompt"])
        self.assertIn("leader placement", korean_stateful_vs_global_query["prompt"])
        self.assertIn("placement budget", korean_stateful_vs_global_query["prompt"])
        self.assertEqual(korean_stateful_vs_global_query.get("experience_level"), "beginner")
        self.assertEqual(
            korean_stateful_vs_global_query["expected_path"],
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md",
        )
        self.assertEqual(korean_stateful_vs_global_query.get("max_rank"), 1)
        self.assertEqual(
            korean_stateful_vs_global_query.get("companion_paths"),
            ["contents/system-design/global-traffic-failover-control-plane-design.md"],
        )
        self.assertEqual(korean_stateful_vs_global_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", korean_stateful_vs_global_query)

        self.assertIn(
            "stateful_failover_beginner_alias_compare_vs_global_failover",
            queries_by_id,
        )
        alias_stateful_vs_global_query = queries_by_id[
            "stateful_failover_beginner_alias_compare_vs_global_failover"
        ]
        self.assertIn("global failover", alias_stateful_vs_global_query["prompt"])
        self.assertIn("stateful failover placement", alias_stateful_vs_global_query["prompt"])
        self.assertIn("regional evacuation", alias_stateful_vs_global_query["prompt"])
        self.assertIn("leader placement", alias_stateful_vs_global_query["prompt"])
        self.assertIn("placement budget", alias_stateful_vs_global_query["prompt"])
        self.assertEqual(alias_stateful_vs_global_query.get("experience_level"), "beginner")
        self.assertEqual(
            alias_stateful_vs_global_query["expected_path"],
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md",
        )
        self.assertEqual(alias_stateful_vs_global_query.get("max_rank"), 1)
        self.assertEqual(
            alias_stateful_vs_global_query.get("companion_paths"),
            ["contents/system-design/global-traffic-failover-control-plane-design.md"],
        )
        self.assertEqual(alias_stateful_vs_global_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", alias_stateful_vs_global_query)

        self.assertIn(
            "stateful_failover_beginner_korean_alias_compare_vs_global_failover",
            queries_by_id,
        )
        korean_alias_stateful_vs_global_query = queries_by_id[
            "stateful_failover_beginner_korean_alias_compare_vs_global_failover"
        ]
        self.assertIn("글로벌 장애 전환", korean_alias_stateful_vs_global_query["prompt"])
        self.assertIn("상태 있는 장애 전환 배치", korean_alias_stateful_vs_global_query["prompt"])
        self.assertIn("regional evacuation", korean_alias_stateful_vs_global_query["prompt"])
        self.assertIn("leader placement", korean_alias_stateful_vs_global_query["prompt"])
        self.assertIn("shard owner", korean_alias_stateful_vs_global_query["prompt"])
        self.assertIn("placement budget", korean_alias_stateful_vs_global_query["prompt"])
        self.assertEqual(
            korean_alias_stateful_vs_global_query.get("experience_level"), "beginner"
        )
        self.assertEqual(
            korean_alias_stateful_vs_global_query["expected_path"],
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md",
        )
        self.assertEqual(korean_alias_stateful_vs_global_query.get("max_rank"), 1)
        self.assertEqual(
            korean_alias_stateful_vs_global_query.get("companion_paths"),
            ["contents/system-design/global-traffic-failover-control-plane-design.md"],
        )
        self.assertEqual(korean_alias_stateful_vs_global_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", korean_alias_stateful_vs_global_query)

        self.assertIn("failover_visibility_alias", queries_by_id)
        visibility_alias_doc_query = queries_by_id["failover_visibility_alias"]
        self.assertIn("failover visibility", visibility_alias_doc_query["prompt"])
        self.assertNotIn("visibility window", visibility_alias_doc_query["prompt"])
        self.assertIn("topology cache divergence", visibility_alias_doc_query["prompt"])
        self.assertEqual(
            visibility_alias_doc_query["expected_path"],
            "contents/database/failover-visibility-window-topology-cache-playbook.md",
        )
        self.assertEqual(visibility_alias_doc_query.get("max_rank"), 3)
        self.assertNotIn("acceptable_paths", visibility_alias_doc_query)

        self.assertIn(
            "projection_freshness_intro_vs_failover_verification_compare",
            queries_by_id,
        )
        verification_contrast_query = queries_by_id[
            "projection_freshness_intro_vs_failover_verification_compare"
        ]
        self.assertIn("projection freshness", verification_contrast_query["prompt"])
        self.assertIn("failover verification", verification_contrast_query["prompt"])
        self.assertIn("차이", verification_contrast_query["prompt"])
        self.assertEqual(
            verification_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(verification_contrast_query.get("max_rank"), 1)
        self.assertEqual(
            verification_contrast_query.get("companion_paths"),
            ["contents/database/commit-horizon-after-failover-verification.md"],
        )
        self.assertEqual(verification_contrast_query.get("companion_max_rank"), 3)
        self.assertNotIn("acceptable_paths", verification_contrast_query)

        self.assertIn(
            "projection_freshness_intro_failover_visibility_vs_write_loss_verification_compare",
            queries_by_id,
        )
        mixed_failover_contrast_query = queries_by_id[
            "projection_freshness_intro_failover_visibility_vs_write_loss_verification_compare"
        ]
        self.assertIn("failover visibility window", mixed_failover_contrast_query["prompt"])
        self.assertIn("stale read", mixed_failover_contrast_query["prompt"])
        self.assertIn("write loss audit", mixed_failover_contrast_query["prompt"])
        self.assertIn("verify", mixed_failover_contrast_query["prompt"])
        self.assertEqual(
            mixed_failover_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(mixed_failover_contrast_query.get("max_rank"), 1)
        self.assertEqual(
            mixed_failover_contrast_query.get("companion_paths"),
            [
                "contents/database/failover-visibility-window-topology-cache-playbook.md",
                "contents/database/commit-horizon-after-failover-verification.md",
            ],
        )
        self.assertEqual(mixed_failover_contrast_query.get("companion_max_rank"), 4)
        self.assertNotIn("acceptable_paths", mixed_failover_contrast_query)

        self.assertIn(
            "projection_freshness_intro_cutover_safety_key_rotation_noise_guard",
            queries_by_id,
        )
        key_rotation_noise_query = queries_by_id[
            "projection_freshness_intro_cutover_safety_key_rotation_noise_guard"
        ]
        self.assertIn("cutover safety window", key_rotation_noise_query["prompt"])
        self.assertIn("key rotation rollback", key_rotation_noise_query["prompt"])
        self.assertIn("stale read", key_rotation_noise_query["prompt"])
        self.assertEqual(
            key_rotation_noise_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(key_rotation_noise_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_cutover_safety_vs_key_rotation_rollback_compare",
            queries_by_id,
        )
        key_rotation_contrast_query = queries_by_id[
            "projection_freshness_intro_cutover_safety_vs_key_rotation_rollback_compare"
        ]
        self.assertIn("cutover safety window", key_rotation_contrast_query["prompt"])
        self.assertIn("key rotation rollback", key_rotation_contrast_query["prompt"])
        self.assertIn("비교", key_rotation_contrast_query["prompt"])
        self.assertEqual(
            key_rotation_contrast_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(key_rotation_contrast_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", key_rotation_contrast_query)

        self.assertIn(
            "projection_freshness_intro_mixed_cutover_safety_failover_key_rotation_noise_guard",
            queries_by_id,
        )
        mixed_operational_noise_query = queries_by_id[
            "projection_freshness_intro_mixed_cutover_safety_failover_key_rotation_noise_guard"
        ]
        self.assertIn("읽기 모델을 처음 배우는데", mixed_operational_noise_query["prompt"])
        self.assertIn("cutover safety window", mixed_operational_noise_query["prompt"])
        self.assertIn("stale reads", mixed_operational_noise_query["prompt"])
        self.assertIn("쓴 직후 읽기 보장", mixed_operational_noise_query["prompt"])
        self.assertIn("failover rollback", mixed_operational_noise_query["prompt"])
        self.assertIn("key rotation rollback", mixed_operational_noise_query["prompt"])
        self.assertIn("운영 키워드", mixed_operational_noise_query["prompt"])
        self.assertIn("큰 그림부터", mixed_operational_noise_query["prompt"])
        self.assertEqual(
            mixed_operational_noise_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(mixed_operational_noise_query.get("max_rank"), 1)
        self.assertEqual(mixed_operational_noise_query.get("top3_category"), "design-pattern")
        self.assertNotIn("acceptable_paths", mixed_operational_noise_query)

        self.assertIn(
            "projection_freshness_intro_korean_cutover_safety_failover_noise_guard",
            queries_by_id,
        )
        korean_cutover_noise_query = queries_by_id[
            "projection_freshness_intro_korean_cutover_safety_failover_noise_guard"
        ]
        self.assertIn("전환 안전 구간", korean_cutover_noise_query["prompt"])
        self.assertIn("예전 값이 보이고", korean_cutover_noise_query["prompt"])
        self.assertIn("failover rollback", korean_cutover_noise_query["prompt"])
        self.assertEqual(
            korean_cutover_noise_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(korean_cutover_noise_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_transliterated_cutover_safety_zone_failover_noise_guard",
            queries_by_id,
        )
        transliterated_cutover_noise_query = queries_by_id[
            "projection_freshness_intro_transliterated_cutover_safety_zone_failover_noise_guard"
        ]
        self.assertIn("컷오버 안전 구간", transliterated_cutover_noise_query["prompt"])
        self.assertIn("예전 값이 보이고", transliterated_cutover_noise_query["prompt"])
        self.assertIn("failover rollback", transliterated_cutover_noise_query["prompt"])
        self.assertEqual(
            transliterated_cutover_noise_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(transliterated_cutover_noise_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_mixed_korean_english_cutover_safety_stale_reads",
            queries_by_id,
        )
        mixed_cutover_stale_reads_query = queries_by_id[
            "projection_freshness_intro_mixed_korean_english_cutover_safety_stale_reads"
        ]
        self.assertIn("cutover safety window", mixed_cutover_stale_reads_query["prompt"])
        self.assertIn("stale reads", mixed_cutover_stale_reads_query["prompt"])
        self.assertIn("쓴 직후 읽기 보장", mixed_cutover_stale_reads_query["prompt"])
        self.assertEqual(
            mixed_cutover_stale_reads_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(mixed_cutover_stale_reads_query.get("max_rank"), 1)

        self.assertIn(
            "projection_freshness_intro_spaced_transliterated_cutover_safety_window_key_rotation_noise_guard",
            queries_by_id,
        )
        spaced_transliterated_cutover_query = queries_by_id[
            "projection_freshness_intro_spaced_transliterated_cutover_safety_window_key_rotation_noise_guard"
        ]
        self.assertIn("컷 오버 안전 윈도우", spaced_transliterated_cutover_query["prompt"])
        self.assertIn("예전 값이 보이고", spaced_transliterated_cutover_query["prompt"])
        self.assertIn("key rotation rollback", spaced_transliterated_cutover_query["prompt"])
        self.assertEqual(
            spaced_transliterated_cutover_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(spaced_transliterated_cutover_query.get("max_rank"), 1)

    def test_beginner_read_after_write_symptom_query_is_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("read_after_write_korean_saved_but_old_value_visible", queries_by_id)
        symptom_query = queries_by_id["read_after_write_korean_saved_but_old_value_visible"]
        self.assertEqual(symptom_query["prompt"], "저장했는데 옛값이 보인다")
        self.assertEqual(
            symptom_query["expected_path"],
            "contents/database/replica-lag-read-after-write-strategies.md",
        )
        self.assertEqual(symptom_query.get("experience_level"), "beginner")
        self.assertEqual(symptom_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", symptom_query)

        self.assertIn("read_after_write_korean_cache_vs_replica_confusion", queries_by_id)
        disambiguation_query = queries_by_id["read_after_write_korean_cache_vs_replica_confusion"]
        self.assertIn("캐시인지 리플리카인지 모르겠음", disambiguation_query["prompt"])
        self.assertEqual(
            disambiguation_query["expected_path"],
            "contents/database/replica-lag-read-after-write-strategies.md",
        )
        self.assertEqual(disambiguation_query.get("experience_level"), "beginner")
        self.assertEqual(disambiguation_query.get("max_rank"), 1)
        self.assertNotIn("acceptable_paths", disambiguation_query)

    def test_korean_cqrs_beginner_synonym_query_tracks_schema_survey_as_companion_only(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        self.assertIn("projection_freshness_intro_korean_synonyms", queries_by_id)
        synonym_query = queries_by_id["projection_freshness_intro_korean_synonyms"]
        self.assertIn("CQRS 읽기 모델을 처음 배우는데", synonym_query["prompt"])
        self.assertIn("롤백 윈도우", synonym_query["prompt"])
        self.assertIn("쓴 직후 읽기 보장", synonym_query["prompt"])
        self.assertEqual(synonym_query.get("experience_level"), "beginner")
        self.assertEqual(
            synonym_query["expected_path"],
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        self.assertEqual(synonym_query.get("max_rank"), 1)
        self.assertEqual(
            synonym_query.get("companion_paths"),
            ["contents/database/schema-migration-partitioning-cdc-cqrs.md"],
        )
        self.assertEqual(synonym_query.get("companion_max_rank"), 5)
        self.assertNotIn("acceptable_paths", synonym_query)

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

        self.assertIn("java_completablefuture_allof_join_timeout_hazards", queries_by_id)
        allof_timeout_query = queries_by_id["java_completablefuture_allof_join_timeout_hazards"]
        self.assertIn("allOf", allof_timeout_query["prompt"])
        self.assertIn("orTimeout", allof_timeout_query["prompt"])
        self.assertIn("whenComplete", allof_timeout_query["prompt"])
        self.assertIn("common pool 실행 모델 말고", allof_timeout_query["prompt"])
        self.assertEqual(
            allof_timeout_query["expected_path"],
            "contents/language/java/completablefuture-allof-join-timeout-exception-handling-hazards.md",
        )
        self.assertEqual(allof_timeout_query.get("experience_level"), "beginner")
        self.assertEqual(
            allof_timeout_query.get("companion_paths"),
            [
                "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
                "contents/language/java/completablefuture-cancellation-semantics.md",
            ],
        )
        self.assertEqual(allof_timeout_query.get("companion_max_rank"), 4)
        self.assertEqual(allof_timeout_query.get("max_rank"), 1)

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
        self.assertIn("wait graph", deadlock_query["prompt"])
        self.assertIn("lock ordering", deadlock_query["prompt"])
        self.assertEqual(deadlock_query["learning_points"], [])
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

    def test_beginner_curriculum_foundation_primer_queries_are_tracked_explicitly(self) -> None:
        payload = _load_fixture_payload()
        queries_by_id = {query["id"]: query for query in payload["queries"]}

        cases = {
            "beginner_spring_dispatcherservlet_primer": {
                "prompt_terms": ["DispatcherServlet", "처음 배우는데", "bean 컨테이너"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_network_keepalive_primer": {
                "prompt_terms": ["keep-alive", "처음 배우는데", "connection reuse"],
                "expected_path": "contents/network/keepalive-connection-reuse-basics.md",
            },
            "beginner_database_connection_pool_primer": {
                "prompt_terms": ["connection pool", "처음 배우는데", "왜 필요한지"],
                "expected_path": "contents/database/connection-pool-basics.md",
            },
            "beginner_spring_transactional_basics": {
                "prompt_terms": ["@Transactional", "처음 배우는데", "동작 원리"],
                "expected_path": "contents/spring/spring-transactional-basics.md",
            },
            "beginner_spring_di_vs_ioc_primer": {
                "prompt_terms": ["DI vs IoC", "처음 배우는데", "스프링 기준"],
                "expected_path": "contents/spring/spring-ioc-di-basics.md",
            },
            "beginner_session_vs_jwt_primer": {
                "prompt_terms": ["세션이랑 JWT", "처음 배우는데", "로그인 흐름"],
                "expected_path": "contents/security/authentication-authorization-session-foundations.md",
            },
            "beginner_dispatcherservlet_shortform_lockin": {
                "prompt_terms": ["DispatcherServlet", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_dispatcher_servlet_spacing_shortform_lockin": {
                "prompt_terms": ["Dispatcher Servlet", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_dispatcher_servlet_lowercase_shortform_lockin": {
                "prompt_terms": ["dispatcher servlet", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_dispatcherservlet_colloquial_shortform_lockin": {
                "prompt_terms": ["DispatcherServlet", "뭔데"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "spring_mvc_shortform_beginner_primer": {
                "prompt_terms": ["Spring", "MVC", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "spring_mvc_shortform_spacing_beginner_primer": {
                "prompt_terms": ["Spring", "M V C", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "spring_mvc_shortform_korean_spacing_beginner_primer": {
                "prompt_terms": ["스프링", "M V C", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "spring_mvc_shortform_korean_alias_beginner_primer": {
                "prompt_terms": ["스프링", "MVC", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_transactional_shortform_lockin": {
                "prompt_terms": ["@Transactional", "뭐야"],
                "expected_path": "contents/spring/spring-transactional-basics.md",
            },
            "beginner_transactional_colloquial_shortform_lockin": {
                "prompt_terms": ["@Transactional", "뭔데"],
                "expected_path": "contents/spring/spring-transactional-basics.md",
            },
            "beginner_transactional_english_shortform_lockin": {
                "prompt_terms": ["What is", "@Transactional"],
                "expected_path": "contents/spring/spring-transactional-basics.md",
            },
            "beginner_transactional_english_meaning_alias_lockin": {
                "prompt_terms": ["What does transactional mean", "Spring"],
                "expected_path": "contents/spring/spring-transactional-basics.md",
            },
            "beginner_mvcc_english_why_use_lockin": {
                "prompt_terms": ["Why use", "MVCC"],
                "expected_path": "contents/database/transaction-isolation-locking.md",
            },
            "beginner_di_vs_ioc_shortform_lockin": {
                "prompt_terms": ["DI vs IoC", "차이가 뭐야"],
                "expected_path": "contents/spring/spring-ioc-di-basics.md",
            },
            "beginner_di_vs_ioc_colloquial_shortform_lockin": {
                "prompt_terms": ["DI vs IoC", "차이가 뭔데"],
                "expected_path": "contents/spring/spring-ioc-di-basics.md",
            },
            "beginner_ioc_english_shortform_lockin": {
                "prompt_terms": ["What is", "IoC", "Spring"],
                "expected_path": "contents/spring/spring-ioc-di-basics.md",
            },
            "beginner_dependency_injection_english_shortform_lockin": {
                "prompt_terms": ["What is", "dependency injection", "Spring"],
                "expected_path": "contents/spring/spring-ioc-di-basics.md",
            },
            "beginner_spring_aop_english_why_use_lockin": {
                "prompt_terms": ["Why use", "Spring AOP"],
                "expected_path": "contents/spring/spring-aop-basics.md",
            },
            "beginner_beanfactory_shortform_lockin": {
                "prompt_terms": ["BeanFactory", "뭐야"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_beanfactory_english_meaning_shortform_lockin": {
                "prompt_terms": ["What does", "BeanFactory", "mean", "Spring"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_beanfactory_english_role_shortform_lockin": {
                "prompt_terms": ["What does", "BeanFactory", "do", "Spring"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_bean_factory_spacing_english_shortform_lockin": {
                "prompt_terms": ["What is", "Bean Factory", "Spring"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_spring_bean_english_meaning_shortform_lockin": {
                "prompt_terms": ["What does", "Spring bean", "mean"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_spring_bean_english_role_shortform_lockin": {
                "prompt_terms": ["What does", "Spring bean", "do"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_component_scan_english_meaning_shortform_lockin": {
                "prompt_terms": ["What does", "component scan", "mean", "Spring"],
                "expected_path": "contents/spring/spring-bean-di-basics.md",
            },
            "beginner_component_scanning_english_shortform_lockin": {
                "prompt_terms": ["What is", "component scanning", "Spring"],
                "expected_path": "contents/spring/spring-bean-di-basics.md",
            },
            "beginner_applicationcontext_english_meaning_shortform_lockin": {
                "prompt_terms": ["What does", "ApplicationContext", "mean", "Spring"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_applicationcontext_english_role_shortform_lockin": {
                "prompt_terms": ["What does", "ApplicationContext", "do", "Spring"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_application_context_spacing_english_shortform_lockin": {
                "prompt_terms": ["What is", "Application Context", "Spring"],
                "expected_path": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
            },
            "beginner_keepalive_shortform_lockin": {
                "prompt_terms": ["keep-alive", "뭐야"],
                "expected_path": "contents/network/keepalive-connection-reuse-basics.md",
            },
            "beginner_keepalive_colloquial_shortform_lockin": {
                "prompt_terms": ["keep-alive", "뭔데"],
                "expected_path": "contents/network/keepalive-connection-reuse-basics.md",
            },
            "beginner_keep_alive_spacing_shortform_lockin": {
                "prompt_terms": ["keep alive", "뭐야"],
                "expected_path": "contents/network/keepalive-connection-reuse-basics.md",
            },
            "beginner_connection_pool_shortform_lockin": {
                "prompt_terms": ["connection pool", "뭐야"],
                "expected_path": "contents/database/connection-pool-basics.md",
            },
            "beginner_connection_pool_colloquial_shortform_lockin": {
                "prompt_terms": ["connection pool", "뭔데"],
                "expected_path": "contents/database/connection-pool-basics.md",
            },
            "beginner_connection_pooling_shortform_lockin": {
                "prompt_terms": ["connection pooling", "뭐야"],
                "expected_path": "contents/database/connection-pool-basics.md",
            },
            "beginner_di_and_ioc_shortform_lockin": {
                "prompt_terms": ["DI와 IoC", "차이가 뭐야"],
                "expected_path": "contents/spring/spring-ioc-di-basics.md",
            },
            "beginner_session_vs_jwt_shortform_lockin": {
                "prompt_terms": ["세션이랑 JWT", "차이가 뭐야"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
            "beginner_session_shortform_lockin": {
                "prompt_terms": ["세션이", "뭐야"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
            "beginner_session_english_shortform_lockin": {
                "prompt_terms": ["What is", "session"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
            "beginner_session_vs_jwt_colloquial_shortform_lockin": {
                "prompt_terms": ["세션이랑 JWT", "차이가 뭔데"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
            "beginner_session_vs_jwt_english_shortform_lockin": {
                "prompt_terms": ["session vs JWT", "difference"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
            "beginner_session_vs_jwt_cookie_login_state_lockin": {
                "prompt_terms": ["JWT가 쿠키", "로그인 상태"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
            "beginner_session_vs_jwt_login_persistence_colloquial_lockin": {
                "prompt_terms": ["JWT랑 쿠키", "로그인 유지"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
            "beginner_session_vs_jwt_cookie_login_state_english_lockin": {
                "prompt_terms": ["JWT", "stay logged in", "cookies"],
                "expected_path": "contents/security/session-cookie-jwt-basics.md",
            },
        }

        for query_id, case in cases.items():
            with self.subTest(query_id=query_id):
                self.assertIn(query_id, queries_by_id)
                query = queries_by_id[query_id]
                for term in case["prompt_terms"]:
                    self.assertIn(term, query["prompt"])
                self.assertEqual(query.get("experience_level"), "beginner")
                self.assertEqual(query["expected_path"], case["expected_path"])
                self.assertEqual(query.get("max_rank"), 1)
                self.assertNotIn("acceptable_paths", query)

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
        try:
            _require_live_full_mode_readiness()
        except AssertionError as exc:
            message = str(exc)
            if (
                "state=stale" in message
                and "knowledge/cs/contents" in message
                and "Non-indexed markdown files still counted by the live hash" in message
            ):
                self.skipTest(
                    "Live index hash scope still includes non-indexed markdown; "
                    "stable beginner golden fixtures remain the authoritative regression check."
                )
            raise


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
        family_contract_query_ids = _generic_companion_family_contract_query_ids()
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
            companion_paths = q.get("companion_paths") or []
            if companion_paths and q["id"] not in family_contract_query_ids:
                ranked_companions = [
                    (path, paths.index(path) + 1) for path in companion_paths if path in paths
                ]
                require_all_companion_paths = bool(q.get("require_all_companion_paths"))
                if require_all_companion_paths and len(ranked_companions) != len(companion_paths):
                    missing_companions = [
                        path for path in companion_paths if path not in {match[0] for match in ranked_companions}
                    ]
                    failures.append(
                        f"{q['id']}: expected every companion path in {companion_paths} "
                        f"within top-{self.top_k} but missing {missing_companions} from {paths}"
                    )
                    continue
                if not ranked_companions:
                    failures.append(
                        f"{q['id']}: expected companion path in {companion_paths} "
                        f"within top-{self.top_k} {paths}"
                    )
                else:
                    companion_max_rank = int(q.get("companion_max_rank", self.top_k))
                    if require_all_companion_paths:
                        for companion_path, companion_rank in ranked_companions:
                            if companion_rank > companion_max_rank:
                                failures.append(
                                    f"{q['id']}: expected companion path {companion_path} within "
                                    f"top-{companion_max_rank} but ranked #{companion_rank} in {paths}"
                                )
                            if rank >= companion_rank:
                                failures.append(
                                    f"{q['id']}: expected primary path {matched_path} to stay ahead of "
                                    f"companion {companion_path} but saw ranks #{rank} and "
                                    f"#{companion_rank} in {paths}"
                                )
                    else:
                        companion_path, companion_rank = min(
                            ranked_companions,
                            key=lambda item: item[1],
                        )
                        if companion_rank > companion_max_rank:
                            failures.append(
                                f"{q['id']}: expected companion path in {companion_paths} "
                                f"within top-{companion_max_rank} "
                                f"(best match {companion_path}) but ranked #{companion_rank} in {paths}"
                            )
                        if rank >= companion_rank:
                            failures.append(
                                f"{q['id']}: expected primary path {matched_path} to stay ahead of "
                                f"companion {companion_path} but saw ranks #{rank} and #{companion_rank} "
                                f"in {paths}"
                            )
            top3_category = q.get("top3_category")
            if top3_category:
                top_categories = [hit.get("category") for hit in hits[:3]]
                if len(top_categories) < 3 or any(category != top3_category for category in top_categories):
                    failures.append(
                        f"{q['id']}: expected top-3 categories to stay {top3_category} "
                        f"but saw {top_categories} for {paths[:3]}"
                    )
        if failures:
            self.fail("\n".join(failures))

    def test_projection_symptom_only_batch_keeps_beginner_primer_family_visible(self) -> None:
        queries_by_id = {query["id"]: query for query in self.queries}
        contract = _load_projection_symptom_only_primer_family_batch_contract()
        family_paths = set(contract.get("family_paths") or [])
        canonical_query_ids = set(contract.get("canonical_query_ids") or [])
        canonical_primer_path = contract.get("canonical_primer_path")
        canonical_max_rank = int(contract.get("canonical_max_rank", self.top_k))
        family_top_k = int(contract.get("family_top_k", 3))
        min_family_hits = int(contract.get("min_family_hits", 1))
        failures: list[str] = []

        for query_id in contract.get("query_ids", []):
            q = queries_by_id[query_id]
            hits = self.searcher.search(
                q["prompt"],
                learning_points=q.get("learning_points") or None,
                top_k=self.top_k,
                experience_level=q.get("experience_level"),
            )
            paths = [hit["path"] for hit in hits]
            top_family_hits = [path for path in paths[:family_top_k] if path in family_paths]
            if len(top_family_hits) < min_family_hits:
                failures.append(
                    f"{query_id}: expected at least {min_family_hits} primer-family hits in "
                    f"top-{family_top_k} but saw {top_family_hits} within {paths[:family_top_k]}"
                )
            if not paths or paths[0] not in family_paths:
                failures.append(
                    f"{query_id}: expected top hit to stay inside the beginner primer family "
                    f"but saw {paths[:1]} from {paths}"
                )
            if query_id in canonical_query_ids:
                if canonical_primer_path not in paths:
                    failures.append(
                        f"{query_id}: expected canonical primer {canonical_primer_path} "
                        f"within top-{self.top_k} but saw {paths}"
                    )
                    continue
                rank = paths.index(canonical_primer_path) + 1
                if rank > canonical_max_rank:
                    failures.append(
                        f"{query_id}: expected canonical primer {canonical_primer_path} within "
                        f"top-{canonical_max_rank} but ranked #{rank} in {paths}"
                    )

        if failures:
            self.fail("\n".join(failures))

    def test_projection_symptom_only_search_regression_sweep_keeps_primer_in_top_family(
        self,
    ) -> None:
        queries_by_id = {query["id"]: query for query in self.queries}
        contract = _load_projection_symptom_only_search_regression_sweep_contract()
        family_paths = set(contract.get("family_paths") or [])
        primer_path = contract.get("primer_path")
        family_top_k = int(contract.get("family_top_k", 3))
        primer_max_rank = int(contract.get("primer_max_rank", family_top_k))
        failures: list[str] = []

        for query_id in contract.get("query_ids", []):
            q = queries_by_id[query_id]
            hits = self.searcher.search(
                q["prompt"],
                learning_points=q.get("learning_points") or None,
                top_k=self.top_k,
                experience_level=q.get("experience_level"),
            )
            paths = [hit["path"] for hit in hits]
            top_family_paths = [path for path in paths[:family_top_k] if path in family_paths]
            if not top_family_paths:
                failures.append(
                    f"{query_id}: expected beginner primer family hit in top-{family_top_k} "
                    f"but saw {paths[:family_top_k]}"
                )
            if primer_path not in paths:
                failures.append(
                    f"{query_id}: expected primer {primer_path} within top-{self.top_k} "
                    f"but saw {paths}"
                )
                continue
            primer_rank = paths.index(primer_path) + 1
            if primer_rank > primer_max_rank:
                failures.append(
                    f"{query_id}: expected primer {primer_path} within top-{primer_max_rank} "
                    f"but ranked #{primer_rank} in {paths}"
                )

        if failures:
            self.fail("\n".join(failures))

    def test_projection_korean_failover_visibility_contrast_sweep_keeps_primer_first(
        self,
    ) -> None:
        queries_by_id = {query["id"]: query for query in self.queries}
        contract = _load_projection_korean_failover_visibility_contrast_sweep_contract()
        primer_path = contract.get("primer_path")
        companion_path = contract.get("companion_path")
        primer_max_rank = int(contract.get("primer_max_rank", self.top_k))
        companion_max_rank = int(contract.get("companion_max_rank", self.top_k))
        failures: list[str] = []

        for query_id in contract.get("query_ids", []):
            q = queries_by_id[query_id]
            hits = self.searcher.search(
                q["prompt"],
                learning_points=q.get("learning_points") or None,
                top_k=self.top_k,
                experience_level=q.get("experience_level"),
            )
            paths = [hit["path"] for hit in hits]

            if primer_path not in paths:
                failures.append(
                    f"{query_id}: expected primer {primer_path} within top-{self.top_k} but saw {paths}"
                )
                continue

            primer_rank = paths.index(primer_path) + 1
            if primer_rank > primer_max_rank:
                failures.append(
                    f"{query_id}: expected primer {primer_path} within top-{primer_max_rank} "
                    f"but ranked #{primer_rank} in {paths}"
                )

            if companion_path not in paths:
                failures.append(
                    f"{query_id}: expected failover companion {companion_path} within top-{self.top_k} "
                    f"but saw {paths}"
                )
                continue

            companion_rank = paths.index(companion_path) + 1
            if companion_rank > companion_max_rank:
                failures.append(
                    f"{query_id}: expected failover companion {companion_path} within top-{companion_max_rank} "
                    f"but ranked #{companion_rank} in {paths}"
                )
            if primer_rank >= companion_rank:
                failures.append(
                    f"{query_id}: expected primer {primer_path} ahead of failover companion "
                    f"{companion_path} but saw ranks #{primer_rank} and #{companion_rank} in {paths}"
                )

        if failures:
            self.fail("\n".join(failures))

    def test_stateful_failover_beginner_contrast_sweep_keeps_stateful_doc_ahead_of_global(
        self,
    ) -> None:
        queries_by_id = {query["id"]: query for query in self.queries}
        contract = _load_stateful_failover_beginner_contrast_sweep_contract()
        primary_path = contract.get("primary_path")
        companion_path = contract.get("companion_path")
        primary_max_rank = int(contract.get("primary_max_rank", self.top_k))
        companion_max_rank = int(contract.get("companion_max_rank", self.top_k))
        failures: list[str] = []

        for query_id in contract.get("query_ids", []):
            q = queries_by_id[query_id]
            hits = self.searcher.search(
                q["prompt"],
                learning_points=q.get("learning_points") or None,
                top_k=self.top_k,
                experience_level=q.get("experience_level"),
            )
            paths = [hit["path"] for hit in hits]

            if primary_path not in paths:
                failures.append(
                    f"{query_id}: expected stateful primary {primary_path} within top-{self.top_k} "
                    f"but saw {paths}"
                )
                continue

            primary_rank = paths.index(primary_path) + 1
            if primary_rank > primary_max_rank:
                failures.append(
                    f"{query_id}: expected stateful primary {primary_path} within top-{primary_max_rank} "
                    f"but ranked #{primary_rank} in {paths}"
                )

            if companion_path not in paths:
                failures.append(
                    f"{query_id}: expected global failover sibling {companion_path} within top-{self.top_k} "
                    f"but saw {paths}"
                )
                continue

            companion_rank = paths.index(companion_path) + 1
            if companion_rank > companion_max_rank:
                failures.append(
                    f"{query_id}: expected global failover sibling {companion_path} within top-{companion_max_rank} "
                    f"but ranked #{companion_rank} in {paths}"
                )
            if primary_rank >= companion_rank:
                failures.append(
                    f"{query_id}: expected stateful sibling {primary_path} ahead of generic global sibling "
                    f"{companion_path} but saw ranks #{primary_rank} and #{companion_rank} in {paths}"
                )

        if failures:
            self.fail("\n".join(failures))


if __name__ == "__main__":
    unittest.main()
