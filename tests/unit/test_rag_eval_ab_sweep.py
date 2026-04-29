"""Unit tests for scripts.learning.rag.eval.ab_sweep.

Coverage targets:
- aggregate_to_candidate_score pulls fields off RunReport blob
- baseline_from_quality_blob pulls fields off baseline_quality.json
- run_one_candidate builds index when missing
- run_one_candidate reuses index when present (no rebuild)
- run_one_candidate force_rebuild=True overrides reuse
- run_ab_sweep iterates all candidates and produces an ABReport
- run_ab_sweep applies pareto_select among passers
- run_ab_sweep selected_candidate_id is None when nobody passes
- ab_report_to_dict round-trips through json.dumps
- progress callback fired on candidate_start / candidate_done
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag.eval import ab_sweep as S
from scripts.learning.rag.eval.candidates import EmbeddingCandidate
from scripts.learning.rag.eval.dataset import (
    Bucket,
    GradedQuery,
    Qrel,
    RankBudget,
)
from scripts.learning.rag.eval.gate import (
    BaselineScore,
    GateThresholds,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeEnc:
    """Returns deterministic vectors so retrieval is repeatable."""

    def __init__(self, dim: int = 4):
        self._dim = dim

    def encode(self, sentences, **kwargs):
        import numpy as np
        vecs = np.zeros((len(sentences), self._dim), dtype="float32")
        for i in range(len(sentences)):
            vecs[i, i % self._dim] = 1.0
        return vecs


def _fake_factory(*_):
    return _FakeEnc(dim=4)


@pytest.fixture
def fake_corpus(tmp_path):
    """Same shape as the index_builder tests'."""
    corpus_root = tmp_path / "corpus"
    cat = corpus_root / "contents" / "spring"
    cat.mkdir(parents=True)
    body = (
        "Spring Bean은 IoC 컨테이너에 의해 관리되는 객체이다. "
        "@Component, @Service 등의 어노테이션 또는 @Bean으로 등록한다. "
        "라이프사이클은 컨테이너 시작 시 결정되며 의존성 주입을 받는다."
    )
    (cat / "bean.md").write_text(f"# Bean\n\n## 정의\n\n{body}\n", encoding="utf-8")
    (cat / "ioc.md").write_text(f"# IoC\n\n## 정의\n\nIoC: {body}\n", encoding="utf-8")
    return corpus_root


def _candidate(cid="test-cand", dim=4, size=100.0, is_control=False):
    return EmbeddingCandidate(
        candidate_id=cid,
        hf_model_id=f"fake/{cid}",
        embed_dim=dim,
        approx_size_mb=size,
        is_control=is_control,
        notes="test fake",
    )


def _query(qid="q1", path="contents/spring/bean.md"):
    return GradedQuery(
        query_id=qid,
        prompt="Spring Bean이 뭐야",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=Bucket("spring", "beginner", "ko", "definition"),
        qrels=(Qrel(path, 3, "primary"),),
        forbidden_paths=(),
        rank_budget=RankBudget(10, 10),
        bucket_source="auto",
    )


def _baseline():
    return BaselineScore(
        primary_ndcg_macro=0.0,
        primary_ndcg_by_category={"spring": 0.0},
        primary_ndcg_category_counts={"spring": 10},
        forbidden_rate_overall=0.0,
        hard_regression_failures=0,
    )


# ---------------------------------------------------------------------------
# aggregate_to_candidate_score / baseline_from_quality_blob
# ---------------------------------------------------------------------------

def _runreport_blob():
    return {
        "manifest": {
            "corpus_hash": "x",
            "index_version": 2,
            "embedding_model": "fake/m",
            "model_revision": None,
            "embedding_dim": 4,
            "device": "cpu",
            "reranker_model": None,
            "fusion_weights": {"k": 60, "w_bm25": 1.0, "w_dense": 1.0},
            "top_k": 10,
            "mode": "full",
            "latency_p50_warm": 50.0,
            "latency_p95_warm": 120.0,
            "cold_start_ms": 1000.0,
        },
        "macro_reports": {
            "primary_ndcg": {
                "category": {
                    "axis": "category",
                    "macro_mean": 0.95,
                    "micro_mean": 0.94,
                    "per_bucket_mean": {"spring": 0.96, "database": 0.85},
                    "per_bucket_count": {"spring": 50, "database": 20},
                    "included_buckets": ["spring", "database"],
                    "excluded_buckets": [],
                }
            }
        },
        "overall_means": {
            "primary_ndcg": 0.94,
            "graded_ndcg": 0.95,
            "mrr": 0.92,
            "hit": 1.0,
            "recall": 0.99,
            "companion_coverage": 0.5,
            "forbidden_rate": 0.0,
        },
        "regression_summary": {
            "total": 70,
            "passed_count": 65,
            "failed_count": 5,
            "all_passed": False,
            "violations_by_kind": {},
            "warnings_by_kind": {},
            "failed_query_ids": [],
        },
    }


def test_aggregate_pulls_macro_fields():
    cand = _candidate(cid="x", dim=4, size=200)
    score = S.aggregate_to_candidate_score(
        cand, _runreport_blob(), rss_mb=2500.0
    )
    assert score.candidate_id == "x"
    assert score.primary_ndcg_macro == 0.95
    assert score.primary_ndcg_by_category == {"spring": 0.96, "database": 0.85}
    assert score.primary_ndcg_category_counts == {"spring": 50, "database": 20}
    assert score.forbidden_rate_overall == 0.0
    assert score.hard_regression_failures == 5
    assert score.warm_p95_ms == 120.0
    assert score.rss_mb == 2500.0
    assert score.model_size_mb == 200


def test_baseline_from_quality_blob():
    base = S.baseline_from_quality_blob(_runreport_blob())
    assert base.primary_ndcg_macro == 0.95
    assert base.hard_regression_failures == 5


# ---------------------------------------------------------------------------
# run_one_candidate
# ---------------------------------------------------------------------------

def test_run_one_candidate_builds_index_when_missing(tmp_path, fake_corpus, monkeypatch):
    # Point corpus_loader at our fake corpus
    from scripts.learning.rag import corpus_loader

    monkeypatch.setattr(corpus_loader, "DEFAULT_CORPUS_ROOT", fake_corpus)

    cand = _candidate(cid="ml", dim=4)
    blob, rss = S.run_one_candidate(
        cand, [_query()],
        base_dir=tmp_path / "ab",
        top_k=5, forbidden_window=2,
        device="cpu", mode="cheap",
        model_factory=_fake_factory,
    )
    # Index was built
    idx_root = tmp_path / "ab" / "ml"
    assert (idx_root / "manifest.json").exists()
    # Run report has shape
    assert "manifest" in blob
    assert blob["manifest"]["embedding_model"] == "fake/ml"
    assert blob["manifest"]["embedding_dim"] == 4
    assert rss > 0


def test_run_one_candidate_reuses_existing_index(tmp_path, fake_corpus, monkeypatch):
    from scripts.learning.rag import corpus_loader
    monkeypatch.setattr(corpus_loader, "DEFAULT_CORPUS_ROOT", fake_corpus)

    cand = _candidate(cid="reuse", dim=4)
    base = tmp_path / "ab"

    # First run builds
    S.run_one_candidate(
        cand, [_query()], base_dir=base, top_k=5,
        forbidden_window=2, device="cpu", mode="cheap",
        model_factory=_fake_factory,
    )
    manifest_path = base / "reuse" / "manifest.json"
    first_mtime = manifest_path.stat().st_mtime

    # Second run with force_rebuild=False should NOT rebuild
    import time as _t; _t.sleep(0.01)  # ensure mtime would change if rebuilt
    S.run_one_candidate(
        cand, [_query()], base_dir=base, top_k=5,
        forbidden_window=2, device="cpu", mode="cheap",
        model_factory=_fake_factory, force_rebuild=False,
    )
    second_mtime = manifest_path.stat().st_mtime
    assert first_mtime == second_mtime  # not rebuilt


def test_run_one_candidate_force_rebuild_overrides_reuse(tmp_path, fake_corpus, monkeypatch):
    from scripts.learning.rag import corpus_loader
    monkeypatch.setattr(corpus_loader, "DEFAULT_CORPUS_ROOT", fake_corpus)

    cand = _candidate(cid="frb", dim=4)
    base = tmp_path / "ab"

    S.run_one_candidate(
        cand, [_query()], base_dir=base, top_k=5,
        forbidden_window=2, device="cpu", mode="cheap",
        model_factory=_fake_factory,
    )
    manifest_path = base / "frb" / "manifest.json"
    first_mtime = manifest_path.stat().st_mtime

    import time as _t; _t.sleep(0.01)
    S.run_one_candidate(
        cand, [_query()], base_dir=base, top_k=5,
        forbidden_window=2, device="cpu", mode="cheap",
        model_factory=_fake_factory, force_rebuild=True,
    )
    second_mtime = manifest_path.stat().st_mtime
    assert second_mtime > first_mtime  # rebuilt


def test_run_one_candidate_requires_factory():
    cand = _candidate()
    with pytest.raises(ValueError, match="model_factory"):
        S.run_one_candidate(cand, [_query()])


def test_run_one_candidate_rejects_empty_queries():
    cand = _candidate()
    with pytest.raises(ValueError, match="queries is empty"):
        S.run_one_candidate(
            cand, [], model_factory=_fake_factory,
        )


# ---------------------------------------------------------------------------
# run_ab_sweep
# ---------------------------------------------------------------------------

def test_run_ab_sweep_iterates_and_returns_report(tmp_path, fake_corpus, monkeypatch):
    from scripts.learning.rag import corpus_loader
    monkeypatch.setattr(corpus_loader, "DEFAULT_CORPUS_ROOT", fake_corpus)

    candidates = [_candidate(cid="a"), _candidate(cid="b")]
    queries = [_query()]
    baseline = _baseline()

    # Loose thresholds so at least one passes (fake retrieval is poor)
    thresholds = GateThresholds(
        min_primary_uplift=-1.0,  # any uplift accepted
        max_p95_warm_ms=1e9,
        max_rss_mb=1e9,
    )

    report = S.run_ab_sweep(
        candidates, queries, baseline,
        base_dir=tmp_path / "ab",
        top_k=5, forbidden_window=2,
        device="cpu", mode="cheap",
        thresholds=thresholds,
        model_factory=_fake_factory,
    )

    assert len(report.candidates) == 2
    ids = {c.candidate.candidate_id for c in report.candidates}
    assert ids == {"a", "b"}
    # Some pareto_order or selection happened
    assert report.selection_rationale  # non-empty


def test_run_ab_sweep_no_passers_yields_no_selection(tmp_path, fake_corpus, monkeypatch):
    from scripts.learning.rag import corpus_loader
    monkeypatch.setattr(corpus_loader, "DEFAULT_CORPUS_ROOT", fake_corpus)

    # Strict thresholds so nobody passes
    thresholds = GateThresholds(
        min_primary_uplift=10.0,  # impossible
    )

    report = S.run_ab_sweep(
        [_candidate(cid="z")], [_query()],
        _baseline(),
        base_dir=tmp_path / "ab",
        top_k=5, forbidden_window=2,
        thresholds=thresholds,
        model_factory=_fake_factory,
    )
    assert report.selected_candidate_id is None
    assert report.pareto_order == ()
    assert "stay on baseline" in report.selection_rationale


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def test_ab_report_to_dict_round_trips_json(tmp_path, fake_corpus, monkeypatch):
    from scripts.learning.rag import corpus_loader
    monkeypatch.setattr(corpus_loader, "DEFAULT_CORPUS_ROOT", fake_corpus)

    report = S.run_ab_sweep(
        [_candidate(cid="x")], [_query()],
        _baseline(),
        base_dir=tmp_path / "ab",
        top_k=5, forbidden_window=2,
        thresholds=GateThresholds(min_primary_uplift=-1.0,
                                   max_p95_warm_ms=1e9, max_rss_mb=1e9),
        model_factory=_fake_factory,
    )
    blob = S.ab_report_to_dict(report)
    serialised = json.dumps(blob)
    assert json.loads(serialised) == blob

    # Top-level structure
    assert "baseline" in blob
    assert "thresholds" in blob
    assert "candidates" in blob
    assert "pareto_order" in blob
    assert "selected_candidate_id" in blob
    assert "selection_rationale" in blob

    # Per-candidate structure
    cand_blob = blob["candidates"][0]
    assert cand_blob["candidate_id"] == "x"
    assert "score" in cand_blob
    assert "gate" in cand_blob
    assert "run_report" in cand_blob


# ---------------------------------------------------------------------------
# Progress callback
# ---------------------------------------------------------------------------

def test_progress_called_on_candidate_lifecycle(tmp_path, fake_corpus, monkeypatch):
    from scripts.learning.rag import corpus_loader
    monkeypatch.setattr(corpus_loader, "DEFAULT_CORPUS_ROOT", fake_corpus)

    events: list[tuple[str, dict]] = []

    def progress(stage, info):
        events.append((stage, info))

    S.run_ab_sweep(
        [_candidate(cid="p")], [_query()],
        _baseline(),
        base_dir=tmp_path / "ab",
        top_k=5, forbidden_window=2,
        thresholds=GateThresholds(min_primary_uplift=-1.0,
                                   max_p95_warm_ms=1e9, max_rss_mb=1e9),
        model_factory=_fake_factory,
        progress=progress,
    )

    stages = [e[0] for e in events]
    assert "candidate_start" in stages
    assert "candidate_done" in stages
