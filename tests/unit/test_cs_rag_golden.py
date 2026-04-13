"""Golden query → expected-path regression for the real CS RAG index.

Each entry in ``tests/fixtures/cs_rag_golden_queries.json`` asserts that
the expected path shows up in the top-K results for a handcrafted
prompt + learning_points pair. The fixture is the source of truth for
retrieval quality baselines — adding a new curated query here is how
we lock in a tuning win or catch a regression.

This test requires the full index (FTS + dense + reranker) and the
ML deps (numpy, sentence-transformers). When the index or deps are
missing — which is the default on fresh clones and CI without model
cache — the test skips cleanly so First-Run Protocol environments are
not blocked.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.learning.rag import indexer

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "cs_rag_golden_queries.json"


def _index_ready() -> bool:
    try:
        return indexer.is_ready(indexer.DEFAULT_INDEX_ROOT).state == "ready"
    except Exception:
        return False


@unittest.skipUnless(_index_ready(), "CS RAG index not built — run bin/cs-index-build")
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
        with FIXTURE_PATH.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        cls.top_k = int(payload.get("_meta", {}).get("top_k", 5))
        cls.queries = payload["queries"]

    def test_every_query_returns_expected_path_in_top_k(self) -> None:
        failures: list[str] = []
        for q in self.queries:
            hits = self.searcher.search(
                q["prompt"],
                learning_points=q.get("learning_points") or None,
                top_k=self.top_k,
            )
            paths = [h["path"] for h in hits]
            if q["expected_path"] not in paths:
                failures.append(
                    f"{q['id']}: expected {q['expected_path']} "
                    f"not in top-{self.top_k} {paths}"
                )
        if failures:
            self.fail("\n".join(failures))


if __name__ == "__main__":
    unittest.main()
