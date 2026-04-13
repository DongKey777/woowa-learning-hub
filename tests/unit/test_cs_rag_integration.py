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

Skips cleanly when the index or ML deps are missing so First-Run Protocol
environments stay green. Complements ``test_cs_rag_golden.py`` (which
exercises ``searcher.search`` directly) by also verifying the integration
facade's bucketing contract.
"""

from __future__ import annotations

import unittest

from scripts.learning.rag import indexer


def _index_ready() -> bool:
    try:
        return indexer.is_ready(indexer.DEFAULT_INDEX_ROOT).state == "ready"
    except Exception:
        return False


@unittest.skipUnless(_index_ready(), "CS RAG index not built — run bin/cs-index-build")
class AugmentAgainstRealIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import numpy  # noqa: F401
            import sentence_transformers  # noqa: F401
        except ImportError as exc:
            raise unittest.SkipTest(f"ML deps missing: {exc}")
        from scripts.learning.integration import augment
        cls.augment = staticmethod(augment)

    def test_skip_mode_returns_empty_without_search(self) -> None:
        result = self.augment(
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
        result = self.augment(
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

    def test_cs_only_path_populates_fallback_key_with_signal_tag(self) -> None:
        result = self.augment(
            prompt="JWT 토큰 내부 구조랑 서명 검증이 궁금해",
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
        # Key shape: "<category>:<signal_tag>" — enforced by integration.py.
        key = next(iter(result["by_fallback_key"]))
        self.assertIn(":", key, f"fallback key missing category:tag separator: {key}")
        category, _, tag = key.partition(":")
        self.assertTrue(category)
        self.assertTrue(tag)


if __name__ == "__main__":
    unittest.main()
