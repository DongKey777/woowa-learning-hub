"""End-to-end smoke for ``scripts.learning.integration.augment``.

Most CS RAG tests mock the searcher so they can run in dependency-free
environments. This suite runs the **real facade against the real on-disk
index**, covering the glue code between coach_run and the RAG pipeline:

- the peer-learning-point path populates ``by_learning_point``
- the cs_only path (empty learning_points) populates ``by_fallback_key``
  with a ``<category>:<signal_tag>`` key
- the ``cs_search_mode="skip"`` fast path returns an empty result
  without importing the searcher
- the sidecar payload mirrors every hit once

Only a genuinely missing first-run index skips. A stale or corrupt index
must fail the readiness contract so corpus churn cannot silently bypass
the real-index full-mode augment verification path.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.learning.rag import corpus_loader, indexer

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "cs_rag_golden_queries.json"


def _load_fixture_payload() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_fixture_query(query_id: str) -> dict:
    payload = _load_fixture_payload()
    for query in payload.get("queries", []):
        if query.get("id") == query_id:
            return query
    raise KeyError(f"unknown CS RAG golden query fixture: {query_id}")


def _load_readiness_contract() -> dict[str, str]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("live_readiness_contract", {})


def _load_live_readiness_diagnostics_contract() -> dict[str, object]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("live_readiness_diagnostics", {})


def _load_empty_learning_points_parity_contract() -> dict[str, str]:
    payload = _load_fixture_payload()
    return payload.get("_meta", {}).get("empty_learning_points_cs_only_parity", {})


def _full_mode_index_ready() -> bool:
    try:
        return indexer.is_ready(indexer.DEFAULT_INDEX_ROOT).state == "ready"
    except Exception:
        return False


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
                "CS RAG readiness probe failed before integration smoke verification; "
                "do not treat readiness errors as skippable."
            ) from exc

    if report.state == "ready":
        return report

    next_command = report.next_command or "bin/cs-index-build"
    if contract.get(report.state, "fail") == "skip":
        raise unittest.SkipTest(f"CS RAG index not built — run {next_command}")

    detail = ""
    if report.state == "stale":
        detail = _live_readiness_stale_diagnostic()

    raise AssertionError(
        f"CS RAG index is not fresh enough for integration smoke verification "
        f"(state={report.state}, reason={report.reason}).{detail} "
        "Stale or corrupt indexes can hide full-mode augment regressions after "
        "corpus churn; only a genuinely missing first-run index may skip. "
        f"Next step: {next_command}"
    )


class CsRagAugmentReadinessGuardContract(unittest.TestCase):
    def test_readiness_contract_marks_stale_as_a_failure_not_a_skip(self) -> None:
        contract = _load_readiness_contract()

        self.assertEqual(contract.get("missing"), "skip")
        self.assertEqual(contract.get("stale"), "fail")
        self.assertEqual(contract.get("corrupt"), "fail")
        self.assertIn("Stale or corrupt indexes", contract.get("rationale", ""))

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

        with self.assertRaisesRegex(AssertionError, "integration smoke verification"):
            _require_live_full_mode_readiness(report)

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

    def test_rebuild_turns_stale_index_back_to_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus_root = root / "corpus"
            index_root = root / "index"
            corpus_root.mkdir()
            index_root.mkdir()
            (corpus_root / "projection.md").write_text(
                "# Projection rebuild\n\nfresh corpus content",
                encoding="utf-8",
            )

            sqlite_path, dense_path, manifest_path = indexer._paths(index_root)
            sqlite_conn = indexer._open_sqlite(sqlite_path)
            sqlite_conn.close()
            dense_path.touch()
            manifest_path.write_text(
                json.dumps(
                    {
                        "index_version": indexer.INDEX_VERSION,
                        "embed_model": "fixture",
                        "embed_dim": 0,
                        "row_count": 1,
                        "corpus_hash": "outdated",
                        "corpus_root": str(corpus_root),
                    }
                ),
                encoding="utf-8",
            )

            stale_report = indexer.is_ready(index_root, corpus_root)
            self.assertEqual(stale_report.state, "stale")
            self.assertEqual(stale_report.reason, "corpus_changed")
            self.assertEqual(stale_report.next_command, "bin/cs-index-build")

            manifest_path.write_text(
                json.dumps(
                    {
                        "index_version": indexer.INDEX_VERSION,
                        "embed_model": "fixture",
                        "embed_dim": 0,
                        "row_count": 1,
                        "corpus_hash": stale_report.corpus_hash,
                        "corpus_root": str(corpus_root),
                    }
                ),
                encoding="utf-8",
            )

            ready_report = indexer.is_ready(index_root, corpus_root)
            self.assertEqual(ready_report.state, "ready")
            self.assertEqual(ready_report.reason, "ready")
            self.assertEqual(ready_report.index_manifest_hash, stale_report.corpus_hash)
            self.assertIsNone(ready_report.next_command)
            self.assertIs(_require_live_full_mode_readiness(ready_report), ready_report)


class CsRagAugmentLiveIndexContract(unittest.TestCase):
    def test_live_index_is_fresh_or_explicitly_missing(self) -> None:
        _require_live_full_mode_readiness()


@unittest.skipUnless(
    _full_mode_index_ready(),
    "CS RAG index not ready for integration smoke checks — run bin/cs-index-build",
)
class AugmentAgainstRealIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        report = _require_live_full_mode_readiness()
        try:
            import numpy  # noqa: F401
            import sentence_transformers  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(f"ML deps missing: {exc}")
        from scripts.learning.integration import augment
        cls.augment = staticmethod(augment)
        # Freeze the readiness snapshot we decided to exercise so concurrent
        # corpus churn does not flip the live probe to stale mid-test.
        cls.readiness = report

    def _augment(self, **kwargs):
        return self.augment(readiness=self.readiness, **kwargs)

    def test_skip_mode_returns_empty_without_search(self) -> None:
        result = self._augment(
            prompt="anything",
            learning_points=["repository_boundary"],
            cs_search_mode="skip",
        )
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(result["by_fallback_key"], {})
        self.assertIsNone(result["sidecar"])
        self.assertEqual(result["meta"]["mode_used"], "skip")
        self.assertEqual(result["meta"]["reason"], "skip_mode")
        self.assertFalse(result["meta"]["rag_ready"])

    def test_peer_learning_point_path_populates_by_learning_point(self) -> None:
        result = self._augment(
            prompt="Repository 경계가 뭐고 트랜잭션까지 알아야 해?",
            learning_points=["repository_boundary"],
            cs_search_mode="full",
            top_k=5,
        )
        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["meta"]["reason"], "ready")
        self.assertEqual(result["meta"]["mode_used"], "full")
        self.assertEqual(result["by_fallback_key"], {})
        self.assertIn("repository_boundary", result["by_learning_point"])
        hits = result["by_learning_point"]["repository_boundary"]
        self.assertTrue(hits, "expected at least one hit for repository_boundary")
        paths = [h["path"] for h in hits]
        self.assertIn(
            "contents/design-pattern/repository-pattern-vs-antipattern.md",
            paths,
        )
        # cs_categories_hit is the deduped, sorted union of hit categories.
        self.assertEqual(
            result["cs_categories_hit"],
            sorted({h["category"] for h in hits}),
        )
        # Sidecar mirrors the compact hits (deduped by path).
        self.assertIsNotNone(result["sidecar"])
        sidecar_paths = [h["path"] for h in result["sidecar"]["hits"]]
        self.assertEqual(sorted(sidecar_paths), sorted(set(sidecar_paths)))
        self.assertTrue(set(sidecar_paths).issuperset(set(paths)))

    def test_cs_only_path_populates_expected_security_fallback_key(self) -> None:
        result = self._augment(
            prompt="JWKS kid miss 가 날 때 issuer audience signature validation 을 어디부터 봐야 해?",
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )
        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertTrue(
            result["by_fallback_key"],
            f"expected fallback bucket for cs_only turn, got meta={result['meta']}",
        )
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        key = next(iter(result["by_fallback_key"]))
        self.assertEqual(key, "security:security_token_validation")

    def test_cs_only_gap_lock_path_populates_database_lock_fallback_family(self) -> None:
        result = self._augment(
            prompt="MySQL gap lock next-key lock 어떻게 동작해?",
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )
        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["database:mysql_gap_locking"],
        )
        hits = result["by_fallback_key"]["database:mysql_gap_locking"]
        self.assertTrue(hits, "expected real-index hits for gap-lock fallback bucket")
        self.assertEqual(hits[0]["path"], "contents/database/gap-lock-next-key-lock.md")
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_cs_only_cdc_contract_evolution_prompt_uses_storage_contract_fallback_key(
        self,
    ) -> None:
        result = self._augment(
            prompt=(
                "CDC schema evolution 에서 old consumer 와 new connector 를 같이 운영할 때 "
                "contract phase 를 어떻게 잡아야 해?"
            ),
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )
        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["database:storage_contract_evolution"],
        )
        self.assertNotIn("database:db_modeling", result["by_fallback_key"])
        hits = result["by_fallback_key"]["database:storage_contract_evolution"]
        self.assertTrue(
            hits,
            "expected real-index hits for CDC storage-contract fallback bucket",
        )
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_cs_only_overlap_gap_lock_prompt_keeps_database_lock_fallback_key(self) -> None:
        result = self._augment(
            prompt="예약 겹침 검사에서 select for update 했는데 insert blocked 되는 이유가 뭐야?",
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )
        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["database:mysql_gap_locking"],
        )
        hits = result["by_fallback_key"]["database:mysql_gap_locking"]
        self.assertTrue(
            hits,
            "expected real-index hits for overlap-style gap-lock fallback bucket",
        )
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])
        self.assertTrue(
            {
                "contents/database/gap-lock-next-key-lock.md",
                "contents/database/engine-fallbacks-overlap-enforcement.md",
            }
            & {hit["path"] for hit in hits[:3]},
            hits[:3],
        )

    def test_cs_only_beginner_transaction_intro_prompt_uses_anomaly_fallback_family(
        self,
    ) -> None:
        fixture = _load_fixture_query("tx_intro_isolation_locking_primer")
        prompt = fixture["prompt"]
        anomaly_doc = fixture["expected_path"]
        locking_primer = "contents/database/transaction-isolation-locking.md"
        decision_doc = (
            "contents/database/transaction-boundary-isolation-locking-decision-framework.md"
        )

        result = self._augment(
            prompt=prompt,
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )

        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["database:transaction_anomaly_patterns"],
        )
        self.assertNotIn("database:transaction_isolation", result["by_fallback_key"])
        hits = result["by_fallback_key"]["database:transaction_anomaly_patterns"]
        self.assertTrue(
            hits,
            "expected real-index hits for beginner transaction anomaly fallback bucket",
        )
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])
        paths = [hit["path"] for hit in hits]
        self.assertEqual(paths[0], anomaly_doc, paths)
        self.assertIn(locking_primer, paths[:3], paths[:3])
        self.assertLess(paths.index(anomaly_doc), paths.index(locking_primer), paths)
        if decision_doc in paths:
            self.assertLess(paths.index(anomaly_doc), paths.index(decision_doc), paths)

    def test_empty_learning_points_matches_none_for_beginner_transaction_fallback_family(
        self,
    ) -> None:
        contract = _load_empty_learning_points_parity_contract()
        fixture = _load_fixture_query(contract["query_id"])
        prompt = fixture["prompt"]

        none_result = self._augment(
            prompt=prompt,
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )
        empty_result = self._augment(
            prompt=prompt,
            learning_points=[],
            cs_search_mode="full",
            top_k=5,
        )

        none_keys = list(none_result["by_fallback_key"])
        empty_keys = list(empty_result["by_fallback_key"])

        self.assertEqual(none_keys, [contract["expected_fallback_key"]])
        self.assertEqual(empty_keys, none_keys)
        self.assertEqual(
            none_result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            empty_result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(none_result["by_learning_point"], {})
        self.assertEqual(empty_result["by_learning_point"], {})

        none_paths = [hit["path"] for hit in none_result["by_fallback_key"][none_keys[0]][:3]]
        empty_paths = [hit["path"] for hit in empty_result["by_fallback_key"][empty_keys[0]][:3]]
        self.assertEqual(none_paths[0], contract["expected_top_path"])
        self.assertEqual(empty_paths, none_paths)
        self.assertEqual(empty_result["cs_categories_hit"], none_result["cs_categories_hit"])

    def test_cs_only_beginner_projection_vs_transaction_rollback_compare_keeps_freshness_primer_first(
        self,
    ) -> None:
        fixture = _load_fixture_query(
            "projection_freshness_intro_rollback_window_vs_transaction_rollback"
        )
        prompt = fixture["prompt"]
        overview_doc = fixture["expected_path"]
        tx_doc = "contents/database/transaction-isolation-locking.md"

        result = self._augment(
            prompt=prompt,
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )

        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["design-pattern:projection_freshness"],
        )
        hits = result["by_fallback_key"]["design-pattern:projection_freshness"]
        self.assertTrue(
            hits,
            "expected real-index hits for beginner projection freshness contrast bucket",
        )
        paths = [hit["path"] for hit in hits]
        self.assertEqual(paths[0], overview_doc)
        self.assertIn(tx_doc, paths, paths)
        self.assertLess(paths.index(overview_doc), paths.index(tx_doc), paths)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_cs_only_beginner_projection_vs_korean_transaction_rollback_compare_keeps_freshness_primer_first(
        self,
    ) -> None:
        fixture = _load_fixture_query(
            "projection_freshness_intro_rollback_window_vs_korean_transaction_rollback"
        )
        prompt = fixture["prompt"]
        overview_doc = fixture["expected_path"]
        tx_doc = "contents/database/transaction-isolation-locking.md"

        result = self._augment(
            prompt=prompt,
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )

        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["design-pattern:projection_freshness"],
        )
        hits = result["by_fallback_key"]["design-pattern:projection_freshness"]
        self.assertTrue(
            hits,
            "expected real-index hits for beginner Korean projection freshness contrast bucket",
        )
        paths = [hit["path"] for hit in hits]
        self.assertEqual(paths[0], overview_doc)
        self.assertIn(tx_doc, paths, paths)
        self.assertLess(paths.index(overview_doc), paths.index(tx_doc), paths)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_cs_only_beginner_full_korean_projection_vs_transaction_rollback_compare_keeps_freshness_primer_first(
        self,
    ) -> None:
        fixture = _load_fixture_query(
            "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_compare"
        )
        prompt = fixture["prompt"]
        overview_doc = fixture["expected_path"]
        tx_doc = "contents/database/transaction-isolation-locking.md"

        result = self._augment(
            prompt=prompt,
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )

        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["design-pattern:projection_freshness"],
        )
        hits = result["by_fallback_key"]["design-pattern:projection_freshness"]
        self.assertTrue(
            hits,
            "expected real-index hits for fully Korean beginner projection freshness contrast bucket",
        )
        paths = [hit["path"] for hit in hits]
        self.assertEqual(paths[0], overview_doc)
        self.assertIn(tx_doc, paths, paths)
        self.assertLess(paths.index(overview_doc), paths.index(tx_doc), paths)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_cs_only_beginner_full_korean_projection_rollback_distinguish_keeps_freshness_primer_first(
        self,
    ) -> None:
        fixture = _load_fixture_query(
            "projection_freshness_intro_full_korean_rollback_window_transaction_rollback_distinguish"
        )
        prompt = fixture["prompt"]
        overview_doc = fixture["expected_path"]
        tx_doc = "contents/database/transaction-isolation-locking.md"

        result = self._augment(
            prompt=prompt,
            learning_points=None,
            cs_search_mode="full",
            top_k=5,
        )

        self.assertTrue(result["meta"]["rag_ready"])
        self.assertEqual(result["by_learning_point"], {})
        self.assertEqual(
            result["fallback_reason"],
            "cs_only_no_peer_learning_point",
        )
        self.assertEqual(
            list(result["by_fallback_key"]),
            ["design-pattern:projection_freshness"],
        )
        hits = result["by_fallback_key"]["design-pattern:projection_freshness"]
        self.assertTrue(
            hits,
            "expected real-index hits for fully Korean beginner rollback distinguish bucket",
        )
        paths = [hit["path"] for hit in hits]
        self.assertEqual(paths[0], overview_doc)
        self.assertIn(tx_doc, paths, paths)
        self.assertLess(paths.index(overview_doc), paths.index(tx_doc), paths)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])


if __name__ == "__main__":
    unittest.main()
