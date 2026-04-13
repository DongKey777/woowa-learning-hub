"""cs_block is a view of cs_augmentation — sources must reference real hits."""

import unittest

from scripts.workbench.core import response_contract


def _augment(**overrides):
    base = {
        "by_learning_point": {},
        "by_fallback_key": {},
        "fallback_reason": None,
        "cs_categories_hit": [],
        "sidecar_path": None,
        "meta": {"rag_ready": True, "mode_used": "cheap", "reason": "ready", "latency_ms": 1},
    }
    base.update(overrides)
    return base


class CsBlockIsViewTest(unittest.TestCase):
    def test_empty_augmentation_yields_no_hits_reason(self) -> None:
        block = response_contract.build_cs_block(_augment())
        self.assertIsNone(block["markdown"])
        self.assertEqual(block["reason"], "no_hits")
        self.assertEqual(block["sources"], [])

    def test_learning_point_hits_feed_markdown_and_sources(self) -> None:
        augment = _augment(
            by_learning_point={
                "repository_boundary": [
                    {
                        "path": "contents/database/repository-boundary.md",
                        "category": "database",
                        "section_title": "경계",
                        "score": 0.9,
                        "snippet_preview": "Repository는 트랜잭션을 몰라야 한다.",
                    }
                ]
            }
        )
        block = response_contract.build_cs_block(augment, applicability_hint="primary")
        self.assertEqual(block["reason"], "ready")
        self.assertIn("이번 질문의 CS 근거", block["markdown"])
        self.assertIn("repository-boundary.md", block["markdown"])
        self.assertEqual(len(block["sources"]), 1)
        src = block["sources"][0]
        self.assertEqual(src["path"], "contents/database/repository-boundary.md")
        self.assertEqual(src["category"], "database")
        self.assertEqual(block["applicability_hint"], "primary")

    def test_fallback_reason_prefers_fallback_bucket(self) -> None:
        augment = _augment(
            by_learning_point={},
            by_fallback_key={
                "database:transaction_isolation": [
                    {
                        "path": "contents/database/transaction-isolation.md",
                        "category": "database",
                        "section_title": None,
                        "score": 0.7,
                        "snippet_preview": "격리 수준.",
                    }
                ]
            },
            fallback_reason="cs_only_no_peer_learning_point",
        )
        block = response_contract.build_cs_block(augment)
        self.assertEqual(block["reason"], "ready")
        self.assertEqual(len(block["sources"]), 1)
        self.assertEqual(block["sources"][0]["bucket"], "database:transaction_isolation")

    def test_skip_mode_degrades(self) -> None:
        augment = _augment(meta={"rag_ready": False, "mode_used": "skip", "reason": "skip_mode"})
        block = response_contract.build_cs_block(augment)
        self.assertEqual(block["reason"], "rag_skip")
        self.assertIsNone(block["markdown"])

    def test_sources_only_reference_augmentation_paths(self) -> None:
        # Invariant: every cs_block.source path must come from the augment_result.
        augment = _augment(
            by_learning_point={
                "lp_a": [
                    {"path": "a.md", "category": "x", "section_title": "s1", "score": 0.5, "snippet_preview": "body"},
                    {"path": "b.md", "category": "y", "section_title": "s2", "score": 0.4, "snippet_preview": "body"},
                ]
            }
        )
        block = response_contract.build_cs_block(augment)
        all_paths = {h["path"] for hits in augment["by_learning_point"].values() for h in hits}
        for src in block["sources"]:
            self.assertIn(src["path"], all_paths)


if __name__ == "__main__":
    unittest.main()
