"""Source_priority post-fusion weighting (cycle 1 fix).

RRF treats every retriever rank evenly, so a fleet-new chooser that
matches 3-4 retrievers at once outranks a baseline canonical primer
that matches 1-2 — even though the v3 contract awards the primer a
higher source_priority. Multiplying the fused score by
``source_priority / 100`` restores the contract's authority gradient
as a borderline-tie-breaker.

This module pins:
  · path_to_source_priority loader handles missing/malformed catalog
  · weighting actually flips canonical primer above chooser when
    fused scores are close
  · weighting preserves Candidate identity (path / chunk_id / metadata)
  · trace metadata (source_priority_weight, pre_priority_score) added
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.learning.rag.r3.candidate import Candidate
from scripts.learning.rag.r3.priority_weighting import (
    DEFAULT_SOURCE_PRIORITY,
    apply_source_priority_weighting,
    load_path_to_source_priority,
)


def _cand(path: str, score: float, **kwargs) -> Candidate:
    return Candidate(
        path=path,
        retriever=kwargs.pop("retriever", "test"),
        rank=kwargs.pop("rank", 1),
        score=score,
        chunk_id=kwargs.pop("chunk_id", f"{path}#0"),
        metadata=kwargs.pop("metadata", {}),
    )


class LoadPathToSourcePriorityTest(unittest.TestCase):
    def test_missing_catalog_dir_returns_empty(self) -> None:
        self.assertEqual(load_path_to_source_priority(None), {})
        with TemporaryDirectory() as td:
            self.assertEqual(load_path_to_source_priority(Path(td)), {})

    def test_loads_from_concepts_v3_json(self) -> None:
        with TemporaryDirectory() as td:
            catalog_dir = Path(td)
            (catalog_dir / "concepts.v3.json").write_text(json.dumps({
                "concepts": {
                    "spring/bean-di-basics": {
                        "doc_path": "spring/spring-bean-di-basics.md",
                        "source_priority": 92,
                    },
                    "design-pattern/registry-vs-locator": {
                        "doc_path": "design-pattern/registry-vs-locator.md",
                        "source_priority": 86,
                    },
                }
            }))
            mapping = load_path_to_source_priority(catalog_dir)
        self.assertEqual(mapping["contents/spring/spring-bean-di-basics.md"], 92)
        self.assertEqual(
            mapping["contents/design-pattern/registry-vs-locator.md"], 86,
        )

    def test_skips_entries_without_source_priority(self) -> None:
        with TemporaryDirectory() as td:
            catalog_dir = Path(td)
            (catalog_dir / "concepts.v3.json").write_text(json.dumps({
                "concepts": {
                    "stub/has-no-priority": {
                        "doc_path": "stub/has-no-priority.md",
                    },
                }
            }))
            mapping = load_path_to_source_priority(catalog_dir)
        self.assertNotIn("contents/stub/has-no-priority.md", mapping)


class ApplySourcePriorityWeightingTest(unittest.TestCase):
    def test_primer_pulls_ahead_of_chooser_on_tie(self) -> None:
        """The cycle 1 regression case in miniature. Both candidates
        have the same RRF score (e.g. fleet chooser caught up to
        baseline primer). Source_priority multiplier should restore
        primer-first ordering."""
        primer = _cand("contents/spring/spring-bean-di-basics.md", score=0.10)
        chooser = _cand(
            "contents/design-pattern/registry-vs-locator.md", score=0.10,
        )
        path_to_priority = {
            "contents/spring/spring-bean-di-basics.md": 92,
            "contents/design-pattern/registry-vs-locator.md": 86,
        }
        out = apply_source_priority_weighting(
            [chooser, primer], path_to_priority=path_to_priority,
        )
        self.assertEqual(out[0].path, "contents/spring/spring-bean-di-basics.md")
        self.assertGreater(out[0].score, out[1].score)

    def test_does_not_flip_clear_winner(self) -> None:
        """When the fused-score gap exceeds what 92→86 lift can close,
        the chooser remains on top. Weighting only nudges borderline
        cases, not strong-signal ones."""
        chooser = _cand(
            "contents/design-pattern/registry-vs-locator.md", score=0.20,
        )
        primer = _cand("contents/spring/spring-bean-di-basics.md", score=0.10)
        path_to_priority = {
            "contents/spring/spring-bean-di-basics.md": 92,
            "contents/design-pattern/registry-vs-locator.md": 86,
        }
        out = apply_source_priority_weighting(
            [chooser, primer], path_to_priority=path_to_priority,
        )
        # 0.20 * 0.86 = 0.172 vs 0.10 * 0.92 = 0.092 → chooser still on top.
        self.assertEqual(out[0].path, "contents/design-pattern/registry-vs-locator.md")

    def test_default_priority_for_unknown_paths(self) -> None:
        """When catalog has no entry for a path, candidate gets the
        default priority (80) — neutral baseline."""
        unknown = _cand("contents/legacy/no-frontmatter.md", score=0.10)
        primer = _cand("contents/spring/spring-bean-di-basics.md", score=0.10)
        path_to_priority = {
            "contents/spring/spring-bean-di-basics.md": 92,
        }
        out = apply_source_priority_weighting(
            [unknown, primer], path_to_priority=path_to_priority,
        )
        self.assertEqual(out[0].path, "contents/spring/spring-bean-di-basics.md")
        # 0.10 * 0.92 vs 0.10 * 0.80 → primer wins
        unknown_after = next(c for c in out if c.path == "contents/legacy/no-frontmatter.md")
        self.assertEqual(
            unknown_after.metadata["source_priority"],
            DEFAULT_SOURCE_PRIORITY,
        )

    def test_preserves_candidate_identity(self) -> None:
        cand = _cand(
            "contents/spring/spring-bean-di-basics.md",
            score=0.10,
            chunk_id="chunk-x",
            retriever="dense",
            rank=3,
            metadata={"existing": "field"},
        )
        out = apply_source_priority_weighting(
            [cand],
            path_to_priority={"contents/spring/spring-bean-di-basics.md": 92},
        )
        self.assertEqual(out[0].path, cand.path)
        self.assertEqual(out[0].chunk_id, cand.chunk_id)
        self.assertEqual(out[0].retriever, cand.retriever)
        self.assertEqual(out[0].rank, cand.rank)
        self.assertEqual(out[0].metadata["existing"], "field")

    def test_trace_metadata_added(self) -> None:
        cand = _cand("contents/spring/spring-bean-di-basics.md", score=0.10)
        out = apply_source_priority_weighting(
            [cand],
            path_to_priority={"contents/spring/spring-bean-di-basics.md": 92},
        )
        meta = out[0].metadata
        self.assertEqual(meta["source_priority"], 92)
        self.assertAlmostEqual(meta["source_priority_weight"], 0.92)
        self.assertAlmostEqual(meta["pre_priority_score"], 0.10)

    def test_empty_path_to_priority_no_op_in_order(self) -> None:
        """When the catalog mapping is empty (unmigrated repo), every
        candidate gets DEFAULT_SOURCE_PRIORITY (uniform multiplier),
        so the order is preserved."""
        c1 = _cand("contents/a/x.md", score=0.20)
        c2 = _cand("contents/b/y.md", score=0.10)
        out = apply_source_priority_weighting([c1, c2], path_to_priority={})
        self.assertEqual(out[0].path, "contents/a/x.md")
        self.assertEqual(out[1].path, "contents/b/y.md")


if __name__ == "__main__":
    unittest.main()
