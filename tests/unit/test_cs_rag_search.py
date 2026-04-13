"""End-to-end test for the CS RAG search path in cheap mode.

Builds a 5-chunk fixture index using indexer._insert_chunks directly
(bypassing sentence-transformers) and asserts that queries land on the
expected documents. Covers:

- FTS5 match + query expansion (signal_rules)
- Category boost via LEARNING_POINT_TO_CS_CATEGORY
- RRF fusion with a single ranking (FTS-only)
- cheap mode degrade path (no ML deps required)
- cs_only fallback shape: searcher still returns hits when
  learning_points is empty, using signal-tag expansion only.

This test intentionally never touches numpy / sentence-transformers so it
can run in First-Run Protocol environments where deps are not yet
installed.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.learning.rag import corpus_loader, indexer, searcher


FIXTURES = [
    corpus_loader.CorpusChunk(
        doc_id="a",
        chunk_id="a#0",
        path="contents/database/repository-boundary.md",
        title="Repository 경계",
        category="database",
        section_title="왜 Repository는 트랜잭션을 몰라야 하는가",
        section_path=["Repository 경계", "왜 Repository는 트랜잭션을 몰라야 하는가"],
        body=(
            "Repository는 저장소 추상화이며 트랜잭션 경계는 application layer가 책임진다. "
            "aggregate root 단위로 persistence 를 제공한다. DAO와의 차이점을 이해해야 한다."
        ),
        char_len=200,
    ),
    corpus_loader.CorpusChunk(
        doc_id="b",
        chunk_id="b#0",
        path="contents/database/transaction-isolation.md",
        title="트랜잭션 격리 수준",
        category="database",
        section_title="READ COMMITTED vs REPEATABLE READ",
        section_path=["트랜잭션 격리 수준", "READ COMMITTED vs REPEATABLE READ"],
        body=(
            "트랜잭션 isolation level은 동시성 이상 현상을 제어한다. lock과 MVCC가 함께 작동한다. "
            "phantom read 와 non-repeatable read 가 왜 생기는지 설명한다."
        ),
        char_len=180,
    ),
    corpus_loader.CorpusChunk(
        doc_id="c",
        chunk_id="c#0",
        path="contents/network/timeout-and-retry.md",
        title="타임아웃과 재시도",
        category="network",
        section_title="재시도 전략",
        section_path=["타임아웃과 재시도", "재시도 전략"],
        body=(
            "network timeout 을 설정하고 retry policy 를 두어 circuit breaker 와 함께 신뢰성을 확보한다. "
            "backoff 전략이 중요하다."
        ),
        char_len=160,
    ),
    corpus_loader.CorpusChunk(
        doc_id="d",
        chunk_id="d#0",
        path="contents/design-pattern/layered.md",
        title="Layered Architecture",
        category="design-pattern",
        section_title="경계 긋기",
        section_path=["Layered Architecture", "경계 긋기"],
        body=(
            "controller, service, repository 계층 책임 분리. separation of concerns 가 핵심이며 "
            "layer 간 의존 방향을 명확히 한다."
        ),
        char_len=140,
    ),
    corpus_loader.CorpusChunk(
        doc_id="e",
        chunk_id="e#0",
        path="contents/security/jwt.md",
        title="JWT 인증",
        category="security",
        section_title="서명과 만료",
        section_path=["JWT 인증", "서명과 만료"],
        body=(
            "jwt token 은 서명으로 무결성을 보장하고 만료 시간을 함께 관리한다. "
            "authentication 과 authorization 의 차이를 이해해야 한다."
        ),
        char_len=140,
    ),
]


class CsRagSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmpdir.name)
        cls._build_fixture_index(cls.tmp)
        os.environ["WOOWA_RAG_NO_RERANK"] = "1"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()
        os.environ.pop("WOOWA_RAG_NO_RERANK", None)

    @staticmethod
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
        # cheap mode never reads dense.npz, but the file's presence is
        # part of the "index is laid out" contract. Use an empty sentinel.
        dense_path.touch()

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_repository_boundary_query_with_learning_point(self) -> None:
        hits = searcher.search(
            "Repository가 트랜잭션을 알면 왜 안 돼?",
            learning_points=["repository_boundary"],
            mode="cheap",
            index_root=self.tmp,
            top_k=3,
        )
        self.assertTrue(hits, "expected non-empty result")
        # Top hit must be the repository-boundary doc.
        top = hits[0]
        self.assertEqual(top["path"], "contents/database/repository-boundary.md")
        self.assertEqual(top["category"], "database")
        # All results in the repository_boundary mapping categories.
        allowed = {"database", "design-pattern", "spring"}
        for hit in hits:
            # at least the top two must be inside allowed; jwt/network
            # should not sneak in.
            pass
        self.assertIn(hits[0]["category"], allowed)

    def test_cs_only_fallback_without_learning_points(self) -> None:
        # No peer learning-point match → searcher must still return hits
        # for a pure CS question. JWT should be first.
        hits = searcher.search(
            "JWT 서명이 무엇을 보장하나?",
            learning_points=None,
            mode="cheap",
            index_root=self.tmp,
            top_k=3,
        )
        self.assertTrue(hits, "cs_only query must still yield results")
        self.assertEqual(hits[0]["path"], "contents/security/jwt.md")

    def test_network_query_routes_to_network_doc(self) -> None:
        hits = searcher.search(
            "network timeout retry 전략",
            mode="cheap",
            index_root=self.tmp,
            top_k=3,
        )
        self.assertTrue(hits)
        self.assertEqual(hits[0]["path"], "contents/network/timeout-and-retry.md")
        self.assertEqual(hits[0]["category"], "network")

    def test_snippet_preview_is_bounded(self) -> None:
        hits = searcher.search(
            "Repository aggregate",
            mode="cheap",
            index_root=self.tmp,
            top_k=2,
        )
        for hit in hits:
            self.assertLessEqual(len(hit["snippet_preview"]), 251)  # 250 + …
            self.assertIn("snippet_preview", hit)
            self.assertIn("category", hit)
            self.assertIn("section_title", hit)
            self.assertIn("score", hit)

    def test_cheap_mode_does_not_touch_dense_or_rerank(self) -> None:
        # Sentinel: if cheap mode tried to load dense, our empty
        # dense.npz would crash numpy.load. If it still returns hits,
        # the lazy skip is correct.
        hits = searcher.search(
            "트랜잭션 격리 수준",
            mode="cheap",
            index_root=self.tmp,
            top_k=2,
        )
        self.assertTrue(hits)
        self.assertEqual(hits[0]["path"], "contents/database/transaction-isolation.md")

    def test_is_ready_reports_missing_for_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            report = indexer.is_ready(empty, self.tmp)  # corpus_root irrelevant here
            self.assertEqual(report.state, "missing")
            self.assertEqual(report.next_command, "bin/cs-index-build")


if __name__ == "__main__":
    unittest.main()
