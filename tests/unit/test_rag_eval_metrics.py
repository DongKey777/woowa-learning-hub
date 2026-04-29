"""Unit tests for scripts.learning.rag.eval.metrics.

Strategy: known small inputs with hand-computed expected outputs. Use
math.isclose for floating point. Coverage targets:
- DCG / IDCG / nDCG arithmetic (Burges-style gain, log2 discount)
- primary_nDCG truly ignores grade-1/2 paths
- MRR, hit@k, recall@k respect the grade>=2 threshold
- companion_coverage and forbidden_rate are independent signals
- Edge cases: empty qrels, k=0, no relevant paths, k larger than ranking
"""

from __future__ import annotations

import math

import pytest

from scripts.learning.rag.eval import metrics as M


def _close(a: float, b: float, rel_tol: float = 1e-9, abs_tol: float = 1e-12) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


# ---------------------------------------------------------------------------
# Threshold projection
# ---------------------------------------------------------------------------

def test_relevant_paths_default_threshold_is_grade_2():
    qrels = {"a.md": 3, "b.md": 2, "c.md": 1, "d.md": 0}
    assert M.relevant_paths_from_qrels(qrels) == {"a.md", "b.md"}


def test_relevant_paths_custom_threshold():
    qrels = {"a.md": 3, "b.md": 2, "c.md": 1}
    assert M.relevant_paths_from_qrels(qrels, min_grade=3) == {"a.md"}
    assert M.relevant_paths_from_qrels(qrels, min_grade=1) == {"a.md", "b.md", "c.md"}


# ---------------------------------------------------------------------------
# Graded DCG / IDCG / nDCG
# ---------------------------------------------------------------------------

def test_graded_dcg_at_k_perfect_ranking():
    qrels = {"a.md": 3, "b.md": 2, "c.md": 1}
    ranked = ["a.md", "b.md", "c.md"]
    expected = 7 * 1.0 + 3 * (1 / math.log2(3)) + 1 * 0.5
    assert _close(M.graded_dcg_at_k(ranked, qrels, k=3), expected)


def test_graded_dcg_at_k_irrelevant_paths_contribute_zero():
    qrels = {"a.md": 3}
    ranked = ["x.md", "y.md", "a.md"]
    assert _close(M.graded_dcg_at_k(ranked, qrels, k=3), 7 * 0.5)


def test_graded_dcg_at_k_zero_when_k_zero():
    qrels = {"a.md": 3}
    assert M.graded_dcg_at_k(["a.md"], qrels, k=0) == 0.0


def test_graded_dcg_at_k_truncates_at_k():
    qrels = {"a.md": 3, "b.md": 3}
    ranked = ["a.md", "b.md"]
    assert _close(M.graded_dcg_at_k(ranked, qrels, k=1), 7 * 1.0)


def test_graded_idcg_at_k_sorts_grades_desc():
    qrels = {"a.md": 1, "b.md": 3, "c.md": 2}
    expected = 7 * 1.0 + 3 * (1 / math.log2(3)) + 1 * 0.5
    assert _close(M.graded_idcg_at_k(qrels, k=3), expected)


def test_graded_idcg_at_k_zero_for_empty_qrels():
    assert M.graded_idcg_at_k({}, k=10) == 0.0


def test_graded_ndcg_perfect_ranking_is_one():
    qrels = {"a.md": 3, "b.md": 2, "c.md": 1}
    ranked = ["a.md", "b.md", "c.md"]
    assert _close(M.graded_ndcg_at_k(ranked, qrels, k=3), 1.0)


def test_graded_ndcg_reversed_ranking_is_less_than_one():
    qrels = {"a.md": 3, "b.md": 2, "c.md": 1}
    reversed_ranked = ["c.md", "b.md", "a.md"]
    score = M.graded_ndcg_at_k(reversed_ranked, qrels, k=3)
    assert 0.0 < score < 1.0


def test_graded_ndcg_zero_for_empty_qrels():
    assert M.graded_ndcg_at_k(["a.md"], {}, k=5) == 0.0


# ---------------------------------------------------------------------------
# primary_nDCG — only grade==3 counts
# ---------------------------------------------------------------------------

def test_primary_ndcg_ignores_acceptable_and_companion():
    qrels = {"primary.md": 3, "acceptable.md": 2, "companion.md": 1}
    ranked = ["primary.md", "acceptable.md", "companion.md"]
    assert _close(M.primary_ndcg_at_k(ranked, qrels, k=3), 1.0)


def test_primary_ndcg_drops_when_primary_is_buried():
    qrels = {"primary.md": 3, "acceptable.md": 2}
    ranked = ["acceptable.md", "other.md", "primary.md"]
    assert M.primary_ndcg_at_k(ranked, qrels, k=3) < 1.0


def test_primary_ndcg_zero_when_no_primary_in_qrels():
    qrels = {"acceptable.md": 2, "companion.md": 1}
    ranked = ["acceptable.md", "companion.md"]
    assert M.primary_ndcg_at_k(ranked, qrels, k=3) == 0.0


# ---------------------------------------------------------------------------
# MRR / hit@k / recall@k — binary relevance via grade>=2
# ---------------------------------------------------------------------------

def test_mrr_first_relevant_at_rank_1():
    qrels = {"a.md": 3}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert M.mrr(["a.md", "b.md"], relevant) == 1.0


def test_mrr_first_relevant_at_rank_3():
    qrels = {"a.md": 2}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert _close(M.mrr(["x.md", "y.md", "a.md"], relevant), 1.0 / 3.0)


def test_mrr_zero_when_no_relevant_in_ranking():
    qrels = {"a.md": 3}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert M.mrr(["x.md", "y.md"], relevant) == 0.0


def test_mrr_zero_when_no_relevant_paths():
    assert M.mrr(["a.md"], set()) == 0.0


def test_companion_grade_1_excluded_from_binary_metrics():
    qrels = {"primary.md": 3, "companion.md": 1}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert "companion.md" not in relevant
    assert _close(M.mrr(["companion.md", "primary.md"], relevant), 0.5)


def test_hit_at_k_true_when_relevant_in_topk():
    qrels = {"a.md": 3}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert M.hit_at_k(["x.md", "a.md", "y.md"], relevant, k=2) == 1.0
    assert M.hit_at_k(["x.md", "a.md", "y.md"], relevant, k=1) == 0.0


def test_hit_at_k_zero_for_zero_k():
    qrels = {"a.md": 3}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert M.hit_at_k(["a.md"], relevant, k=0) == 0.0


def test_recall_at_k_partial():
    qrels = {"a.md": 3, "b.md": 2, "c.md": 2}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert _close(M.recall_at_k(["a.md", "b.md", "x.md"], relevant, k=2), 2.0 / 3.0)


def test_recall_at_k_full():
    qrels = {"a.md": 3, "b.md": 2}
    relevant = M.relevant_paths_from_qrels(qrels)
    assert M.recall_at_k(["a.md", "b.md"], relevant, k=2) == 1.0


def test_recall_at_k_zero_when_no_relevant_paths():
    assert M.recall_at_k(["a.md"], set(), k=5) == 0.0


# ---------------------------------------------------------------------------
# companion_coverage & forbidden_rate
# ---------------------------------------------------------------------------

def test_companion_coverage_partial():
    companion = {"c1.md", "c2.md", "c3.md"}
    ranked = ["other.md", "c1.md", "c3.md"]
    assert _close(M.companion_coverage_at_k(ranked, companion, k=3), 2.0 / 3.0)


def test_companion_coverage_zero_when_none_present():
    assert M.companion_coverage_at_k(["a.md"], {"c1.md"}, k=5) == 0.0


def test_companion_coverage_zero_for_empty_companion_set():
    assert M.companion_coverage_at_k(["a.md"], set(), k=5) == 0.0


def test_forbidden_rate_counts_top_k_slots():
    forbidden = {"bad.md"}
    ranked = ["good.md", "bad.md", "ok.md"]
    assert _close(M.forbidden_rate_at_k(ranked, forbidden, k=3), 1.0 / 3.0)


def test_forbidden_rate_zero_for_empty_forbidden_set():
    assert M.forbidden_rate_at_k(["a.md"], set(), k=5) == 0.0


def test_forbidden_rate_zero_for_zero_k():
    assert M.forbidden_rate_at_k(["bad.md"], {"bad.md"}, k=0) == 0.0


# ---------------------------------------------------------------------------
# Sanity: graded vs primary nDCG on a companion-heavy fixture
# ---------------------------------------------------------------------------

def test_primary_ndcg_more_discriminating_than_graded_on_companion_heavy_qrels():
    qrels = {
        "primary.md": 3,
        "comp1.md": 1,
        "comp2.md": 1,
        "comp3.md": 1,
        "comp4.md": 1,
    }
    ranked = ["comp1.md", "comp2.md", "comp3.md", "primary.md"]
    graded = M.graded_ndcg_at_k(ranked, qrels, k=3)
    primary = M.primary_ndcg_at_k(ranked, qrels, k=3)
    assert primary == 0.0
    assert graded > 0.0
