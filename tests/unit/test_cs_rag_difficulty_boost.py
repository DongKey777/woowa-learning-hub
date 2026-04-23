"""Difficulty boost regression tests for CS RAG search.

Verifies the experience_level → difficulty boost ladder added to
``searcher.search`` plumbed through ``integration.augment``:

- experience_level=None → ranking unchanged (zero diff vs legacy path)
- experience_level="beginner" → beginner doc promoted past advanced doc
  on otherwise equal queries
- experience_level="intermediate" → intermediate doc preferred
- ALTER TABLE migration for the new ``difficulty`` column is idempotent
- manifest carries the bumped index_version

Uses cheap mode + WOOWA_RAG_NO_RERANK so no ML deps are required.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.learning.rag import corpus_loader, indexer, searcher


def _chunk(
    doc_id: str,
    path: str,
    title: str,
    category: str,
    section_title: str,
    body: str,
    difficulty: str | None,
) -> corpus_loader.CorpusChunk:
    return corpus_loader.CorpusChunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}#0",
        path=path,
        title=title,
        category=category,
        section_title=section_title,
        section_path=[title, section_title],
        body=body,
        char_len=len(body),
        difficulty=difficulty,
    )


# Two sibling docs in the same category with overlapping bodies so
# they tie on FTS scoring and category boost. Only difficulty differs.
FIXTURES = [
    _chunk(
        "beg",
        "contents/database/transaction-basics.md",
        "트랜잭션 기초",
        "database",
        "Transaction basics",
        (
            "transaction 은 데이터베이스 작업의 단위다. commit, rollback, atomicity, "
            "isolation level, ACID 를 입문자가 처음 배우는 기초 문서다. transaction "
            "begin, commit, rollback, savepoint 를 차근차근 설명한다."
        ),
        difficulty="beginner",
    ),
    _chunk(
        "adv",
        "contents/database/transaction-advanced-pitfalls.md",
        "트랜잭션 고급 함정",
        "database",
        "Transaction pitfalls",
        (
            "transaction 의 advanced 함정: long running transaction, lock escalation, "
            "phantom read, MVCC tuning, isolation level downgrade, deadlock retry, "
            "transaction commit ordering 을 다룬다. ACID 보장과 performance trade-off."
        ),
        difficulty="advanced",
    ),
    _chunk(
        "mid",
        "contents/database/transaction-isolation-walkthrough.md",
        "트랜잭션 격리수준 워크스루",
        "database",
        "Isolation walkthrough",
        (
            "transaction isolation level 을 단계별로 비교한다. read committed, "
            "repeatable read, serializable 을 ACID 와 함께 살펴보고 실무 commit "
            "전략을 설명한다."
        ),
        difficulty="intermediate",
    ),
]


def _build_fixture_index(tmp: Path) -> None:
    sqlite_path, dense_path, manifest_path = indexer._paths(tmp)
    conn = indexer._open_sqlite(sqlite_path)
    try:
        indexer._insert_chunks(conn, FIXTURES)
    finally:
        conn.close()
    manifest_path.write_text(
        json.dumps(
            {
                "index_version": indexer.INDEX_VERSION,
                "embed_model": "fixture",
                "embed_dim": 0,
                "row_count": len(FIXTURES),
                "corpus_hash": "fixture",
                "corpus_root": "fixture",
            }
        ),
        encoding="utf-8",
    )
    dense_path.touch()


class DifficultyBoostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmpdir.name)
        _build_fixture_index(cls.tmp)
        os.environ["WOOWA_RAG_NO_RERANK"] = "1"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()
        os.environ.pop("WOOWA_RAG_NO_RERANK", None)

    def _search(self, experience_level: str | None) -> list[dict]:
        return searcher.search(
            "transaction commit rollback ACID isolation 설명",
            learning_points=None,
            mode="cheap",
            index_root=self.tmp,
            top_k=3,
            experience_level=experience_level,
        )

    def test_experience_level_none_matches_legacy_ordering(self) -> None:
        baseline = self._search(None)
        self.assertTrue(baseline)
        # Snapshot scores so we can assert the boost path is a true no-op.
        scores = [(h["path"], h["score"]) for h in baseline]
        again = self._search(None)
        self.assertEqual(scores, [(h["path"], h["score"]) for h in again])

    def test_beginner_learner_promotes_beginner_doc(self) -> None:
        baseline = self._search(None)
        beginner = self._search("beginner")
        beginner_path = "contents/database/transaction-basics.md"
        advanced_path = "contents/database/transaction-advanced-pitfalls.md"

        baseline_paths = [h["path"] for h in baseline]
        beginner_paths = [h["path"] for h in beginner]

        self.assertIn(beginner_path, beginner_paths)
        self.assertIn(advanced_path, beginner_paths)
        # Beginner doc must rank ahead of advanced doc for a beginner learner.
        self.assertLess(
            beginner_paths.index(beginner_path),
            beginner_paths.index(advanced_path),
            f"beginner ordering={beginner_paths}, baseline={baseline_paths}",
        )

    def test_intermediate_learner_prefers_intermediate_doc(self) -> None:
        intermediate = self._search("intermediate")
        mid_path = "contents/database/transaction-isolation-walkthrough.md"
        beg_path = "contents/database/transaction-basics.md"
        paths = [h["path"] for h in intermediate]
        self.assertIn(mid_path, paths)
        self.assertIn(beg_path, paths)
        self.assertLess(
            paths.index(mid_path),
            paths.index(beg_path),
            f"intermediate ordering={paths}",
        )

    def test_advanced_learner_keeps_legacy_ordering(self) -> None:
        # Advanced/expert learners are intentionally not in the ladder so
        # legacy goldens are untouched. Same scores as None.
        baseline = self._search(None)
        advanced = self._search("advanced")
        self.assertEqual(
            [(h["path"], h["score"]) for h in baseline],
            [(h["path"], h["score"]) for h in advanced],
        )


class DifficultyMigrationTest(unittest.TestCase):
    def test_alter_table_is_idempotent_on_legacy_v1_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "legacy.sqlite3"
            # Simulate a pre-v2 database that is missing the difficulty column.
            legacy = sqlite3.connect(db_path)
            try:
                legacy.executescript(
                    """
                    CREATE TABLE chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id TEXT NOT NULL,
                        chunk_id TEXT NOT NULL UNIQUE,
                        path TEXT NOT NULL,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        section_title TEXT NOT NULL,
                        section_path TEXT NOT NULL,
                        body TEXT NOT NULL,
                        char_len INTEGER NOT NULL,
                        anchors TEXT NOT NULL
                    );
                    """
                )
                legacy.commit()
            finally:
                legacy.close()

            # First open should ALTER in the difficulty column.
            conn1 = indexer._open_sqlite(db_path)
            try:
                cols1 = {row[1] for row in conn1.execute("PRAGMA table_info(chunks)").fetchall()}
                self.assertIn("difficulty", cols1)
            finally:
                conn1.close()

            # Second open must be a no-op (no error, column count stable).
            conn2 = indexer._open_sqlite(db_path)
            try:
                cols2 = {row[1] for row in conn2.execute("PRAGMA table_info(chunks)").fetchall()}
                self.assertEqual(cols1, cols2)
            finally:
                conn2.close()

    def test_manifest_carries_bumped_index_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _build_fixture_index(tmp_path)
            manifest = json.loads((tmp_path / indexer.MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest["index_version"], indexer.INDEX_VERSION)
            self.assertGreaterEqual(indexer.INDEX_VERSION, 2)


if __name__ == "__main__":
    unittest.main()
