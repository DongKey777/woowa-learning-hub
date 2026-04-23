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

from scripts.learning.rag import indexer

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


def _full_mode_index_ready() -> bool:
    try:
        return indexer.is_ready(indexer.DEFAULT_INDEX_ROOT).state == "ready"
    except Exception:
        return False


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

    raise AssertionError(
        f"CS RAG index is not fresh enough for integration smoke verification "
        f"(state={report.state}, reason={report.reason}). "
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
        primer_paths = {
            fixture["expected_path"],
            "contents/database/transaction-isolation-locking.md",
        }
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
        self.assertTrue(primer_paths & set(paths[:2]), paths[:2])
        if decision_doc in paths:
            primer_rank = min(paths.index(path) for path in primer_paths if path in paths)
            self.assertLess(primer_rank, paths.index(decision_doc), paths)


if __name__ == "__main__":
    unittest.main()
