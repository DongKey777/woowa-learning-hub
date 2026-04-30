"""is_ready() × integration.augment() degrade path coverage."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.learning import integration
from scripts.learning.rag import corpus_loader, indexer


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

    def test_non_indexed_markdown_churn_can_flip_live_readiness_back_to_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus_root = root / "knowledge" / "cs"
            index_root = root / "state" / "cs_rag"
            contents_root = corpus_root / "contents" / "design-pattern"
            contents_root.mkdir(parents=True)
            index_root.mkdir(parents=True)

            primer_path = contents_root / "read-model-staleness.md"
            primer_path.write_text(
                "# Read model staleness\n\n## Primer\n\n"
                "same indexed content that is long enough to survive the minimum "
                "chunk-size filter for readiness debugging coverage.",
                encoding="utf-8",
            )
            meta_path = corpus_root / "README.md"
            meta_path.write_text("# Corpus notes\n\nfirst pass", encoding="utf-8")

            sqlite_path, dense_path, manifest_path = indexer._paths(index_root)
            conn = indexer._open_sqlite(sqlite_path)
            try:
                indexer._insert_chunks(conn, corpus_loader.load_corpus(corpus_root))
            finally:
                conn.close()
            dense_path.touch()

            initial_hash = corpus_loader.corpus_hash(corpus_root)
            manifest_path.write_text(
                json.dumps(
                    {
                        "index_version": indexer.INDEX_VERSION,
                        "embed_model": "fixture",
                        "embed_dim": 0,
                        "row_count": 1,
                        "corpus_hash": initial_hash,
                        "corpus_root": str(corpus_root),
                    }
                ),
                encoding="utf-8",
            )

            ready_report = indexer.is_ready(index_root, corpus_root)
            indexed_paths_before = [chunk.path for chunk in corpus_loader.iter_corpus(corpus_root)]
            self.assertEqual(ready_report.state, "ready")
            self.assertEqual(
                indexed_paths_before,
                ["contents/design-pattern/read-model-staleness.md"],
            )

            meta_path.write_text("# Corpus notes\n\nsecond pass", encoding="utf-8")

            stale_report = indexer.is_ready(index_root, corpus_root)
            indexed_paths_after = [chunk.path for chunk in corpus_loader.iter_corpus(corpus_root)]
            churned_hash = corpus_loader.corpus_hash(corpus_root)

            self.assertEqual(indexed_paths_after, indexed_paths_before)
            self.assertEqual(stale_report.state, "stale")
            self.assertEqual(stale_report.reason, "corpus_changed")
            self.assertEqual(stale_report.index_manifest_hash, initial_hash)
            self.assertEqual(stale_report.corpus_hash, churned_hash)
            self.assertNotEqual(churned_hash, initial_hash)
            self.assertEqual(stale_report.next_command, "bin/cs-index-build")

    def test_rebuild_can_flip_back_to_stale_immediately_when_non_indexed_markdown_changes_again(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus_root = root / "knowledge" / "cs"
            index_root = root / "state" / "cs_rag"
            contents_root = corpus_root / "contents" / "design-pattern"
            contents_root.mkdir(parents=True)
            index_root.mkdir(parents=True)

            (contents_root / "read-model-staleness.md").write_text(
                "# Read model staleness\n\n## Primer\n\n"
                "same indexed content that is long enough to survive the minimum "
                "chunk-size filter for readiness debugging coverage.",
                encoding="utf-8",
            )
            meta_path = corpus_root / "README.md"
            meta_path.write_text("# Corpus notes\n\nbefore rebuild", encoding="utf-8")

            sqlite_path, dense_path, manifest_path = indexer._paths(index_root)
            conn = indexer._open_sqlite(sqlite_path)
            try:
                indexer._insert_chunks(conn, corpus_loader.load_corpus(corpus_root))
            finally:
                conn.close()
            dense_path.touch()

            first_hash = corpus_loader.corpus_hash(corpus_root)
            manifest_path.write_text(
                json.dumps(
                    {
                        "index_version": indexer.INDEX_VERSION,
                        "embed_model": "fixture",
                        "embed_dim": 0,
                        "row_count": 1,
                        "corpus_hash": first_hash,
                        "corpus_root": str(corpus_root),
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(indexer.is_ready(index_root, corpus_root).state, "ready")

            meta_path.write_text("# Corpus notes\n\nafter rebuild", encoding="utf-8")
            rebuild_hash = corpus_loader.corpus_hash(corpus_root)
            manifest_path.write_text(
                json.dumps(
                    {
                        "index_version": indexer.INDEX_VERSION,
                        "embed_model": "fixture",
                        "embed_dim": 0,
                        "row_count": 1,
                        "corpus_hash": rebuild_hash,
                        "corpus_root": str(corpus_root),
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(indexer.is_ready(index_root, corpus_root).state, "ready")

            meta_path.write_text("# Corpus notes\n\nchanged again right away", encoding="utf-8")

            flipped_report = indexer.is_ready(index_root, corpus_root)
            self.assertEqual(flipped_report.state, "stale")
            self.assertEqual(flipped_report.reason, "corpus_changed")
            self.assertEqual(flipped_report.index_manifest_hash, rebuild_hash)
            self.assertNotEqual(flipped_report.corpus_hash, rebuild_hash)


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


class LanceReadinessTest(unittest.TestCase):
    def test_lance_v3_manifest_with_lance_store_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus_root = root / "corpus"
            index_root = root / "index"
            corpus_root.mkdir()
            index_root.mkdir()
            (index_root / indexer.LANCE_DIR_NAME).mkdir()
            (corpus_root / "tx.md").write_text("# TX\n\n트랜잭션", encoding="utf-8")
            corpus_hash = corpus_loader.corpus_hash(corpus_root)
            (index_root / indexer.MANIFEST_NAME).write_text(
                json.dumps(
                    {
                        "index_version": indexer.LANCE_INDEX_VERSION,
                        "row_count": 1,
                        "corpus_hash": corpus_hash,
                        "corpus_root": str(corpus_root),
                        "encoder": {"model_id": "BAAI/bge-m3"},
                        "lancedb": {"table_name": indexer.LANCE_TABLE_NAME},
                        "modalities": ["fts", "dense", "sparse"],
                    }
                ),
                encoding="utf-8",
            )

            report = indexer.is_ready(index_root, corpus_root)

        self.assertEqual(report.state, "ready")
        self.assertEqual(report.reason, "ready")
        self.assertEqual(report.index_manifest_hash, corpus_hash)

    def test_lance_v3_manifest_without_lance_store_is_corrupt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            corpus_root = root / "corpus"
            index_root = root / "index"
            corpus_root.mkdir()
            index_root.mkdir()
            (corpus_root / "tx.md").write_text("# TX\n\n트랜잭션", encoding="utf-8")
            corpus_hash = corpus_loader.corpus_hash(corpus_root)
            (index_root / indexer.MANIFEST_NAME).write_text(
                json.dumps(
                    {
                        "index_version": indexer.LANCE_INDEX_VERSION,
                        "row_count": 1,
                        "corpus_hash": corpus_hash,
                        "corpus_root": str(corpus_root),
                        "encoder": {"model_id": "BAAI/bge-m3"},
                        "lancedb": {"table_name": indexer.LANCE_TABLE_NAME},
                    }
                ),
                encoding="utf-8",
            )

            report = indexer.is_ready(index_root, corpus_root)

        self.assertEqual(report.state, "corrupt")
        self.assertEqual(report.reason, "index_corrupt")
        self.assertEqual(report.next_command, "bin/cs-index-build")


if __name__ == "__main__":
    unittest.main()
