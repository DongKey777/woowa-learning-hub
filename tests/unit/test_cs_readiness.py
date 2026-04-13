"""is_ready() × integration.augment() degrade path coverage."""

import tempfile
import unittest
from pathlib import Path

from scripts.learning import integration
from scripts.learning.rag import indexer


class IsReadyTest(unittest.TestCase):
    def test_missing_for_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            report = indexer.is_ready(empty, empty)
            self.assertEqual(report.state, "missing")
            self.assertEqual(report.next_command, "bin/cs-index-build")

    def test_ready_for_fixture_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sqlite_path, dense_path, manifest_path = indexer._paths(Path(tmp))
            conn = indexer._open_sqlite(sqlite_path)
            try:
                indexer._insert_chunks(conn, [])
            finally:
                conn.close()
            import json
            manifest_path.write_text(
                json.dumps({
                    "index_version": indexer.INDEX_VERSION,
                    "embed_model": "fixture",
                    "embed_dim": 0,
                    "row_count": 0,
                    "corpus_hash": "fixture",
                    "corpus_root": "fixture",
                }),
                encoding="utf-8",
            )
            dense_path.touch()
            report = indexer.is_ready(tmp, corpus_root=tmp)
            # state may be 'ready' or 'stale' depending on hash comparison,
            # but must never be 'missing' when files exist.
            self.assertNotEqual(report.state, "missing")


class IntegrationAugmentDegradeTest(unittest.TestCase):
    def test_skip_mode_returns_empty(self) -> None:
        result = integration.augment(
            prompt="anything",
            cs_search_mode="skip",
        )
        self.assertEqual(result["meta"]["reason"], "skip_mode")
        self.assertEqual(result["meta"]["mode_used"], "skip")
        self.assertEqual(result["by_learning_point"], {})
        self.assertFalse(result["meta"]["rag_ready"])

    def test_not_ready_returns_empty(self) -> None:
        class FakeReport:
            state = "missing"
            reason = "first_run"
            corpus_hash = None
            index_manifest_hash = None
            next_command = "bin/cs-index-build"

        result = integration.augment(
            prompt="트랜잭션",
            cs_search_mode="cheap",
            readiness=FakeReport(),
        )
        self.assertEqual(result["meta"]["reason"], "first_run")
        self.assertFalse(result["meta"]["rag_ready"])

    def test_invalid_mode_raises(self) -> None:
        with self.assertRaises(ValueError):
            integration.augment(prompt="x", cs_search_mode="bogus")


if __name__ == "__main__":
    unittest.main()
