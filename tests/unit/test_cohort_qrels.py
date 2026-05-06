"""Unit tests for ``scripts/learning/rag/r3/eval/cohort_qrels.py``.

Covers:
- CohortQuery validation: cohort_tag enum, primary required for standard
  cohorts but optional for refusal cohorts, primary ⊥ forbidden disjoint
- Suite I/O roundtrip with metadata preservation
- by_cohort grouping
- Loading the real seed file at tests/fixtures/r3_qrels_real_v0_seed.json
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.learning.rag.r3.eval.cohort_qrels import (
    VALID_COHORTS,
    CohortQrelSuite,
    CohortQuery,
    load_cohort_qrels,
    write_cohort_qrels,
)


class CohortQueryValidationTest(unittest.TestCase):
    def test_minimal_query_accepted(self):
        q = CohortQuery(
            query_id="x",
            prompt="DI?",
            language="ko",
            intent="definition",
            level="beginner",
            cohort_tag="paraphrase_human",
            primary_paths=("contents/spring/spring-bean-di-basics.md",),
        )
        self.assertEqual(q.cohort_tag, "paraphrase_human")

    def test_unknown_cohort_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown cohort_tag"):
            CohortQuery(
                query_id="x", prompt="DI?", language="ko", intent="definition",
                level="beginner", cohort_tag="bogus_cohort",
                primary_paths=("a.md",),
            )

    def test_empty_prompt_rejected(self):
        with self.assertRaisesRegex(ValueError, "prompt"):
            CohortQuery(
                query_id="x", prompt="", language="ko", intent="definition",
                level="beginner", cohort_tag="paraphrase_human",
                primary_paths=("a.md",),
            )

    def test_missing_primary_for_standard_cohort_rejected(self):
        with self.assertRaisesRegex(ValueError, "primary_path"):
            CohortQuery(
                query_id="x", prompt="DI?", language="ko",
                intent="definition", level="beginner",
                cohort_tag="paraphrase_human",
                primary_paths=(),
            )

    def test_missing_primary_for_refusal_cohort_accepted(self):
        """corpus_gap_probe and forbidden_neighbor cohorts may legitimately
        have no primary — the *correct* outcome is no hit."""
        for tag in ("corpus_gap_probe", "forbidden_neighbor"):
            with self.subTest(cohort_tag=tag):
                q = CohortQuery(
                    query_id="x", prompt="some refusal-shaped question",
                    language="ko", intent="definition", level="beginner",
                    cohort_tag=tag,
                    primary_paths=(),
                    forbidden_paths=("contents/x.md",),
                )
                self.assertEqual(q.cohort_tag, tag)

    def test_primary_forbidden_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "primary ⊥ forbidden"):
            CohortQuery(
                query_id="x", prompt="DI?", language="ko",
                intent="definition", level="beginner",
                cohort_tag="paraphrase_human",
                primary_paths=("a.md",),
                forbidden_paths=("a.md",),
            )

    def test_to_dict_roundtrip(self):
        q = CohortQuery(
            query_id="x",
            prompt="DI?",
            language="ko",
            intent="definition",
            level="beginner",
            cohort_tag="paraphrase_human",
            primary_paths=("a.md",),
            failure_focus=("paraphrase_robustness",),
        )
        blob = q.to_dict()
        self.assertEqual(blob["query_id"], "x")
        self.assertEqual(blob["primary_paths"], ["a.md"])
        self.assertEqual(blob["failure_focus"], ["paraphrase_robustness"])


class SuiteGroupingTest(unittest.TestCase):
    def test_by_cohort_groups_correctly(self):
        queries = (
            CohortQuery(query_id="q1", prompt="p1", language="ko",
                        intent="definition", level="beginner",
                        cohort_tag="paraphrase_human",
                        primary_paths=("a.md",)),
            CohortQuery(query_id="q2", prompt="p2", language="ko",
                        intent="definition", level="beginner",
                        cohort_tag="paraphrase_human",
                        primary_paths=("b.md",)),
            CohortQuery(query_id="q3", prompt="p3", language="ko",
                        intent="comparison", level="intermediate",
                        cohort_tag="confusable_pairs",
                        primary_paths=("c.md",)),
        )
        suite = CohortQrelSuite(schema_version=1, queries=queries)
        grouped = suite.by_cohort()
        self.assertEqual(len(grouped["paraphrase_human"]), 2)
        self.assertEqual(len(grouped["confusable_pairs"]), 1)
        # Empty cohorts must still appear with zero queries
        self.assertEqual(grouped["mission_bridge"], [])

    def test_cohort_counts(self):
        queries = (
            CohortQuery(query_id="q1", prompt="p1", language="ko",
                        intent="definition", level="beginner",
                        cohort_tag="paraphrase_human",
                        primary_paths=("a.md",)),
        )
        suite = CohortQrelSuite(schema_version=1, queries=queries)
        counts = suite.cohort_counts()
        self.assertEqual(counts["paraphrase_human"], 1)
        self.assertEqual(counts["confusable_pairs"], 0)


class IORoundtripTest(unittest.TestCase):
    def test_write_then_load_preserves_queries_and_metadata(self):
        queries = (
            CohortQuery(
                query_id="q1", prompt="DI?", language="ko",
                intent="definition", level="beginner",
                cohort_tag="paraphrase_human",
                primary_paths=("contents/spring/di.md",),
                failure_focus=("paraphrase_robustness",),
                rationale="test",
            ),
        )
        suite = CohortQrelSuite(
            schema_version=1, queries=queries,
            metadata={"author": "ai-session", "curation_status": "draft"},
        )
        with TemporaryDirectory() as td:
            path = Path(td) / "qrels.json"
            write_cohort_qrels(suite, path)
            loaded = load_cohort_qrels(path)
            self.assertEqual(loaded.schema_version, 1)
            self.assertEqual(len(loaded.queries), 1)
            self.assertEqual(loaded.queries[0].query_id, "q1")
            self.assertEqual(loaded.metadata["author"], "ai-session")

    def test_load_root_list_format(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "qrels.json"
            path.write_text(json.dumps([
                {
                    "query_id": "q1",
                    "prompt": "DI?",
                    "language": "ko",
                    "intent": "definition",
                    "level": "beginner",
                    "cohort_tag": "paraphrase_human",
                    "primary_paths": ["contents/spring/di.md"],
                },
            ]), encoding="utf-8")
            loaded = load_cohort_qrels(path)
            self.assertEqual(len(loaded.queries), 1)

    def test_duplicate_query_ids_rejected(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "qrels.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "queries": [
                    {
                        "query_id": "q1",
                        "prompt": "DI?",
                        "language": "ko",
                        "intent": "definition",
                        "level": "beginner",
                        "cohort_tag": "paraphrase_human",
                        "primary_paths": ["contents/spring/di.md"],
                    },
                    {
                        "query_id": "q1",
                        "prompt": "Factory?",
                        "language": "ko",
                        "intent": "definition",
                        "level": "beginner",
                        "cohort_tag": "paraphrase_human",
                        "primary_paths": ["contents/design-pattern/factory.md"],
                    },
                ],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate query_ids"):
                load_cohort_qrels(path)

    def test_declared_query_count_mismatch_rejected(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "qrels.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "query_count": 2,
                "queries": [
                    {
                        "query_id": "q1",
                        "prompt": "DI?",
                        "language": "ko",
                        "intent": "definition",
                        "level": "beginner",
                        "cohort_tag": "paraphrase_human",
                        "primary_paths": ["contents/spring/di.md"],
                    },
                ],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "query_count mismatch"):
                load_cohort_qrels(path)


class RealSeedLoadTest(unittest.TestCase):
    """The Phase 3 Real qrel seed at tests/fixtures/r3_qrels_real_v0_seed.json
    must load without error. This catches schema drift between the seed
    file and the dataclass."""

    def test_seed_loads(self):
        repo_root = Path(__file__).resolve().parents[2]
        seed = repo_root / "tests" / "fixtures" / "r3_qrels_real_v0_seed.json"
        if not seed.exists():
            self.skipTest("seed file not present")
        suite = load_cohort_qrels(seed)
        self.assertEqual(len(suite.queries), 40)
        # All 6 cohorts present
        counts = suite.cohort_counts()
        for tag in VALID_COHORTS:
            self.assertGreater(counts[tag], 0,
                               f"cohort {tag} empty in seed: {counts}")


if __name__ == "__main__":
    unittest.main()
