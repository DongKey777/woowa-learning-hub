"""Unit tests for ``scripts/learning/rag/r3/eval/cohort_eval.py``.

Covers:
- Outcome classification per cohort_tag (standard / corpus_gap_probe / forbidden_neighbor)
- Pass/fail accounting for each outcome
- Per-cohort metric aggregation (recall@k, MRR, forbidden_hit_rate)
- Failure taxonomy classification from failure_focus tags
- evaluate_suite end-to-end with a fake search_fn
"""

from __future__ import annotations

import unittest

from scripts.learning.rag.r3.eval.cohort_qrels import (
    CohortQrelSuite,
    CohortQuery,
)
from scripts.learning.rag.r3.eval.cohort_eval import (
    _is_refusal_clean_outcome,
    _classify_failure,
    _classify_outcome,
    evaluate_cohort_query,
    evaluate_suite,
)


def _q(
    cohort: str,
    *,
    primary: tuple[str, ...] = (),
    acceptable: tuple[str, ...] = (),
    forbidden: tuple[str, ...] = (),
    failure_focus: tuple[str, ...] = (),
) -> CohortQuery:
    return CohortQuery(
        query_id="qx",
        prompt="some prompt",
        language="ko",
        intent="definition",
        level="beginner",
        cohort_tag=cohort,
        primary_paths=primary,
        acceptable_paths=acceptable,
        forbidden_paths=forbidden,
        failure_focus=failure_focus,
    )


def _fake_search(returned_paths: list[str]):
    """Build a search_fn that returns the given paths in order."""
    def _fn(prompt, *, debug=None, **kwargs):
        if debug is not None:
            debug["r3_final_paths"] = list(returned_paths)
        return [{"path": p, "score": 1.0 - 0.01 * i}
                for i, p in enumerate(returned_paths)]
    return _fn


class StandardCohortClassifierTest(unittest.TestCase):
    def test_primary_in_top_k_pass(self):
        out = _classify_outcome(
            cohort_tag="paraphrase_human",
            final_paths=("a.md", "primary.md"),
            primary_paths=("primary.md",),
            acceptable_paths=(),
            forbidden_paths=(),
            top_k=5,
        )
        expected, actual, pass_status, prim_rank, *_ = out
        self.assertEqual(expected, "primary_in_top_k")
        self.assertEqual(actual, "primary_hit")
        self.assertTrue(pass_status)
        self.assertEqual(prim_rank, 2)

    def test_acceptable_only_is_partial_credit_fail(self):
        out = _classify_outcome(
            cohort_tag="paraphrase_human",
            final_paths=("acc.md", "noise.md"),
            primary_paths=("primary.md",),
            acceptable_paths=("acc.md",),
            forbidden_paths=(),
            top_k=5,
        )
        _, actual, pass_status, prim, acc, _ = out
        self.assertEqual(actual, "acceptable_hit")
        self.assertFalse(pass_status)
        self.assertIsNone(prim)
        self.assertEqual(acc, 1)

    def test_miss_when_neither_primary_nor_acceptable(self):
        out = _classify_outcome(
            cohort_tag="paraphrase_human",
            final_paths=("noise.md",),
            primary_paths=("primary.md",),
            acceptable_paths=(),
            forbidden_paths=(),
            top_k=5,
        )
        _, actual, pass_status, *_ = out
        self.assertEqual(actual, "miss")
        self.assertFalse(pass_status)

    def test_forbidden_hit_overrides_primary(self):
        """Even if primary is in top_k, a forbidden hit fails the query."""
        out = _classify_outcome(
            cohort_tag="paraphrase_human",
            final_paths=("forbidden.md", "primary.md"),
            primary_paths=("primary.md",),
            acceptable_paths=(),
            forbidden_paths=("forbidden.md",),
            top_k=5,
        )
        _, actual, pass_status, *_ = out
        self.assertEqual(actual, "forbidden_hit")
        self.assertFalse(pass_status)


class RefusalCohortClassifierTest(unittest.TestCase):
    def test_corpus_gap_probe_clean_refusal_passes(self):
        out = _classify_outcome(
            cohort_tag="corpus_gap_probe",
            final_paths=("noise.md",),
            primary_paths=(),
            acceptable_paths=(),
            forbidden_paths=("forbidden.md",),
            top_k=5,
        )
        _, actual, pass_status, *_ = out
        self.assertEqual(actual, "refusal_clean")
        self.assertTrue(pass_status)

    def test_corpus_gap_probe_forbidden_hit_fails(self):
        out = _classify_outcome(
            cohort_tag="corpus_gap_probe",
            final_paths=("forbidden.md",),
            primary_paths=(),
            acceptable_paths=(),
            forbidden_paths=("forbidden.md",),
            top_k=5,
        )
        _, actual, pass_status, *_ = out
        self.assertEqual(actual, "forbidden_hit")
        self.assertFalse(pass_status)

    def test_tier_downgraded_counts_as_refusal_clean_metric(self):
        self.assertTrue(_is_refusal_clean_outcome("tier_downgraded"))
        self.assertTrue(_is_refusal_clean_outcome("refusal_clean"))
        self.assertFalse(_is_refusal_clean_outcome("silent_failure"))

    def test_forbidden_neighbor_no_forbidden_passes(self):
        out = _classify_outcome(
            cohort_tag="forbidden_neighbor",
            final_paths=("anything-else.md",),
            primary_paths=("primary.md",),
            acceptable_paths=(),
            forbidden_paths=("forbidden.md",),
            top_k=5,
        )
        _, actual, pass_status, *_ = out
        self.assertEqual(actual, "miss_clean")
        self.assertTrue(pass_status)

    def test_forbidden_neighbor_forbidden_hit_fails(self):
        out = _classify_outcome(
            cohort_tag="forbidden_neighbor",
            final_paths=("forbidden.md",),
            primary_paths=("primary.md",),
            acceptable_paths=(),
            forbidden_paths=("forbidden.md",),
            top_k=5,
        )
        _, actual, pass_status, *_ = out
        self.assertEqual(actual, "forbidden_hit")
        self.assertFalse(pass_status)


class FailureClassifierTest(unittest.TestCase):
    def test_passing_query_returns_none(self):
        self.assertIsNone(_classify_failure(
            actual_outcome="primary_hit", pass_status=True,
            failure_focus=(), debug={},
        ))

    def test_forbidden_pollution(self):
        self.assertEqual(
            _classify_failure(
                actual_outcome="forbidden_hit", pass_status=False,
                failure_focus=(), debug={},
            ),
            "forbidden_polluted",
        )

    def test_acceptable_only_is_qrel_incomplete(self):
        self.assertEqual(
            _classify_failure(
                actual_outcome="acceptable_hit", pass_status=False,
                failure_focus=(), debug={},
            ),
            "qrel_incomplete",
        )

    def test_paraphrase_focus_maps_to_query_understood_badly(self):
        self.assertEqual(
            _classify_failure(
                actual_outcome="miss", pass_status=False,
                failure_focus=("paraphrase_robustness",), debug={},
            ),
            "query_understood_badly",
        )

    def test_default_for_miss_without_focus(self):
        self.assertEqual(
            _classify_failure(
                actual_outcome="miss", pass_status=False,
                failure_focus=(), debug={},
            ),
            "candidate_absent",
        )


class HarnessTest(unittest.TestCase):
    def test_evaluate_cohort_query_pass_path(self):
        q = _q(
            "paraphrase_human",
            primary=("contents/spring/di.md",),
        )
        result = evaluate_cohort_query(
            q,
            _fake_search(["contents/spring/di.md", "contents/x.md"]),
            top_k=5,
        )
        self.assertTrue(result.pass_status)
        self.assertEqual(result.primary_rank, 1)
        self.assertEqual(result.actual_outcome, "primary_hit")
        self.assertIsNone(result.failure_class)

    def test_evaluate_cohort_query_failure_path(self):
        q = _q(
            "paraphrase_human",
            primary=("contents/spring/di.md",),
            failure_focus=("paraphrase_robustness",),
        )
        result = evaluate_cohort_query(
            q,
            _fake_search(["contents/x.md", "contents/y.md"]),
            top_k=5,
        )
        self.assertFalse(result.pass_status)
        self.assertEqual(result.failure_class, "query_understood_badly")

    def test_evaluate_suite_aggregates_per_cohort(self):
        queries = (
            _q("paraphrase_human", primary=("primary.md",)),
            _q("paraphrase_human", primary=("primary.md",)),
            _q("confusable_pairs", primary=("conf.md",),
               forbidden=("forbidden.md",)),
        )
        # Override query_id collisions
        queries = (
            CohortQuery(**{**queries[0].to_dict(), "query_id": "p1",
                           "primary_paths": ("primary.md",)}),
            CohortQuery(**{**queries[1].to_dict(), "query_id": "p2",
                           "primary_paths": ("primary.md",)}),
            CohortQuery(**{**queries[2].to_dict(), "query_id": "c1",
                           "primary_paths": ("conf.md",),
                           "forbidden_paths": ("forbidden.md",)}),
        )
        suite = CohortQrelSuite(schema_version=1, queries=queries)
        # Search returns primary for the first 2, forbidden for the 3rd
        # We need a stateful fake that depends on the prompt — but our
        # fake queries all have prompt "some prompt". So make it return
        # primary.md, primary.md, forbidden.md by call count.
        call_count = {"n": 0}
        def _stateful(prompt, *, debug=None, **kwargs):
            call_count["n"] += 1
            n = call_count["n"]
            if n == 1:
                paths = ["primary.md"]
            elif n == 2:
                paths = ["primary.md"]
            else:
                paths = ["forbidden.md", "conf.md"]
            if debug is not None:
                debug["r3_final_paths"] = list(paths)
            return [{"path": p, "score": 1.0} for p in paths]
        report = evaluate_suite(suite, _stateful, top_k=5)
        self.assertEqual(report.query_count, 3)
        self.assertEqual(report.per_cohort["paraphrase_human"].total, 2)
        self.assertEqual(report.per_cohort["paraphrase_human"].pass_count, 2)
        self.assertEqual(report.per_cohort["confusable_pairs"].total, 1)
        self.assertEqual(report.per_cohort["confusable_pairs"].pass_count, 0)
        self.assertEqual(report.per_cohort["confusable_pairs"].forbidden_hit_top_k, 1)
        # Overall pass: 2/3
        self.assertAlmostEqual(report.overall_pass_rate, 2 / 3, places=4)

    def test_metrics_dict_recall_and_mrr(self):
        q = _q("paraphrase_human", primary=("primary.md",))
        suite = CohortQrelSuite(schema_version=1, queries=(q,))
        # primary at rank 2 → MRR 0.5, recall@5 1.0
        report = evaluate_suite(
            suite, _fake_search(["x.md", "primary.md"]), top_k=5,
        )
        cohort = report.per_cohort["paraphrase_human"].to_dict(top_k=5)
        self.assertEqual(cohort["recall_at_5"], 1.0)
        self.assertEqual(cohort["mrr"], 0.5)


if __name__ == "__main__":
    unittest.main()
