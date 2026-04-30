"""Unit tests for scripts.learning.cli_rag_eval (the bin/rag-eval CLI).

The --fast path is the headline contract. --baseline-only requires
live retrieval and is exercised by an integration smoke (or by hand).
We only unit-test the argument parsing, fixture loading, and fast-path
exit codes here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning import cli_rag_eval as CLI


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def test_parser_requires_mode():
    parser = CLI.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_fast_mode():
    parser = CLI.build_parser()
    args = parser.parse_args(["--fast"])
    assert args.fast is True
    assert args.baseline_only is False


def test_parser_baseline_only_mode():
    parser = CLI.build_parser()
    args = parser.parse_args(["--baseline-only"])
    assert args.baseline_only is True
    assert args.fast is False


def test_parser_modes_are_mutually_exclusive():
    parser = CLI.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--fast", "--baseline-only"])


def test_parser_top_k_and_window_defaults():
    parser = CLI.build_parser()
    args = parser.parse_args(["--fast"])
    assert args.top_k == 10
    assert args.forbidden_window == 5
    assert args.device == "auto"


# ---------------------------------------------------------------------------
# Fixture loading: legacy detection
# ---------------------------------------------------------------------------

def _legacy_fixture(tmp_path) -> Path:
    payload = {
        "queries": [
            {
                "id": "q1",
                "prompt": "스프링 빈이 뭐야?",
                "learning_points": [],
                "expected_path": "contents/spring/bean.md",
            }
        ]
    }
    p = tmp_path / "legacy.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


def _graded_fixture(tmp_path) -> Path:
    payload = {
        "queries": [
            {
                "query_id": "g1",
                "prompt": "p",
                "mode": "full",
                "experience_level": None,
                "learning_points": [],
                "bucket": {
                    "category": "spring",
                    "difficulty": "beginner",
                    "language": "ko",
                    "intent": "definition",
                },
                "qrels": [{"path": "a.md", "grade": 3, "role": "primary"}],
                "forbidden_paths": [],
                "rank_budget": {"primary_max_rank": 1, "companion_max_rank": 4},
                "bucket_source": "auto",
            }
        ]
    }
    p = tmp_path / "graded.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


def test_load_queries_handles_legacy_format(tmp_path):
    queries = CLI.load_queries(_legacy_fixture(tmp_path))
    assert len(queries) == 1
    assert queries[0].query_id == "q1"
    assert queries[0].primary_paths() == {"contents/spring/bean.md"}


def test_load_queries_handles_graded_format(tmp_path):
    queries = CLI.load_queries(_graded_fixture(tmp_path))
    assert len(queries) == 1
    assert queries[0].query_id == "g1"


def test_load_queries_rejects_empty(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps({"queries": []}, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="no queries"):
        CLI.load_queries(p)


def test_load_queries_rejects_unknown_format(tmp_path):
    p = tmp_path / "weird.json"
    p.write_text(
        json.dumps({"queries": [{"prompt": "p", "no_grade_no_expected": True}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unrecognised fixture format"):
        CLI.load_queries(p)


# ---------------------------------------------------------------------------
# --fast end-to-end (no live retrieval)
# ---------------------------------------------------------------------------

def test_fast_passes_on_legacy_fixture(tmp_path):
    args = CLI.build_parser().parse_args(
        ["--fast", "--fixture", str(_legacy_fixture(tmp_path))]
    )
    assert CLI.run_fast(args) == 0


def test_fast_fails_on_empty_fixture(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps({"queries": []}), encoding="utf-8")
    args = CLI.build_parser().parse_args(["--fast", "--fixture", str(p)])
    # load_queries raises on empty → CLI translates to non-zero exit
    with pytest.raises(ValueError):
        CLI.run_fast(args)


def test_fast_runs_on_real_legacy_fixture():
    """Smoke test against the actual 338-query golden fixture.

    The default fixture path is repo-relative and should always exist
    in this checkout. This test makes sure --fast works without
    arguments in the canonical environment.
    """
    args = CLI.build_parser().parse_args(["--fast"])
    assert CLI.run_fast(args) == 0


# ---------------------------------------------------------------------------
# Device resolution
# ---------------------------------------------------------------------------

def test_resolve_device_passthrough():
    assert CLI._resolve_device("cpu") == "cpu"
    assert CLI._resolve_device("cuda") == "cuda"
    assert CLI._resolve_device("mps") == "mps"


def test_resolve_device_auto_returns_string():
    """Auto resolution either lands on 'mps' (Apple Silicon + MPS
    available) or 'cpu' (everything else / fallback). We only assert
    it's one of the supported values — the exact answer depends on
    the test machine."""
    resolved = CLI._resolve_device("auto")
    assert resolved in ("cpu", "mps")


# ---------------------------------------------------------------------------
# --embedding-precheck mode
# ---------------------------------------------------------------------------

class _FakeEnc:
    """Lightweight fake encoder for precheck CLI tests."""

    def encode(self, sentences, **kwargs):
        import numpy as np
        return np.zeros((len(sentences), 4), dtype="float32")


def test_parser_embedding_precheck_mode():
    args = CLI.build_parser().parse_args(["--embedding-precheck"])
    assert args.embedding_precheck is True
    assert args.fast is False
    assert args.baseline_only is False


def test_parser_precheck_defaults(tmp_path):
    args = CLI.build_parser().parse_args(["--embedding-precheck"])
    assert args.encode_iterations == 10
    assert args.precheck_out == CLI.DEFAULT_PRECHECK_OUT


def test_parser_precheck_three_way_mutually_exclusive():
    parser = CLI.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--fast", "--embedding-precheck"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--baseline-only", "--embedding-precheck"])


def test_run_embedding_precheck_writes_json_for_all_candidates(tmp_path):
    """End-to-end with injected fake factory — measures all four
    candidates and writes the report file."""
    out = tmp_path / "precheck.json"
    args = CLI.build_parser().parse_args([
        "--embedding-precheck",
        "--precheck-out", str(out),
        "--encode-iterations", "3",
    ])
    rc = CLI.run_embedding_precheck(args, model_factory=lambda *_: _FakeEnc())
    assert rc == 0
    assert out.exists()

    blob = json.loads(out.read_text())
    assert "device" in blob
    assert blob["encode_iterations"] == 3
    assert len(blob["candidates"]) == 4
    ids = [c["candidate_id"] for c in blob["candidates"]]
    assert "MiniLM-L12-v2" in ids
    assert "bge-m3" in ids
    # Each candidate carries the precheck fields
    for entry in blob["candidates"]:
        assert "model_load_ms" in entry
        assert "warm_encode_p50_ms" in entry
        assert "rss_after_load_mb" in entry


def test_run_embedding_precheck_creates_parent_dir(tmp_path):
    out = tmp_path / "nested" / "deep" / "precheck.json"
    args = CLI.build_parser().parse_args([
        "--embedding-precheck",
        "--precheck-out", str(out),
        "--encode-iterations", "2",
    ])
    rc = CLI.run_embedding_precheck(args, model_factory=lambda *_: _FakeEnc())
    assert rc == 0
    assert out.exists()


# ---------------------------------------------------------------------------
# --embedding-ab mode
# ---------------------------------------------------------------------------

def test_parser_embedding_ab_mode():
    args = CLI.build_parser().parse_args(["--embedding-ab"])
    assert args.embedding_ab is True


def test_parser_ab_defaults():
    args = CLI.build_parser().parse_args(["--embedding-ab"])
    assert args.ab_out == CLI.DEFAULT_AB_OUT
    assert args.ab_base_dir == CLI.DEFAULT_AB_BASE_DIR
    assert args.baseline_quality_path == CLI.DEFAULT_BASELINE_QUALITY_PATH
    assert args.candidate_id is None
    assert args.force_rebuild is False


def test_parser_candidate_id_repeatable():
    args = CLI.build_parser().parse_args([
        "--embedding-ab",
        "--candidate-id", "MiniLM-L12-v2",
        "--candidate-id", "bge-m3",
    ])
    assert args.candidate_id == ["MiniLM-L12-v2", "bge-m3"]


def test_parser_force_rebuild_flag():
    args = CLI.build_parser().parse_args(["--embedding-ab", "--force-rebuild"])
    assert args.force_rebuild is True


def test_run_embedding_ab_fails_when_baseline_missing(tmp_path):
    args = CLI.build_parser().parse_args([
        "--embedding-ab",
        "--baseline-quality-path", str(tmp_path / "missing.json"),
        "--ab-out", str(tmp_path / "ab.json"),
    ])
    rc = CLI.run_embedding_ab(args, model_factory=lambda *_: _FakeEnc())
    assert rc == 2  # missing baseline → exit 2


# ---------------------------------------------------------------------------
# --reranker-ab mode
# ---------------------------------------------------------------------------

def test_parser_reranker_ab_mode():
    args = CLI.build_parser().parse_args(["--reranker-ab"])
    assert args.reranker_ab is True


def test_parser_reranker_ab_defaults():
    args = CLI.build_parser().parse_args(["--reranker-ab"])
    assert args.reranker_out == CLI.DEFAULT_RERANKER_AB_OUT
    assert args.embedding_index_root == CLI.DEFAULT_EMBEDDING_INDEX_ROOT
    assert args.reranker_candidate_id is None
    assert args.reranker_include_high_memory is False


def test_parser_reranker_candidate_id_repeatable():
    args = CLI.build_parser().parse_args([
        "--reranker-ab",
        "--reranker-candidate-id", "mxbai-rerank-base-v1",
        "--reranker-candidate-id", "bge-reranker-v2-m3",
    ])
    assert args.reranker_candidate_id == [
        "mxbai-rerank-base-v1",
        "bge-reranker-v2-m3",
    ]


def test_parser_five_way_mutually_exclusive():
    parser = CLI.build_parser()
    pairs = [
        ["--fast", "--reranker-ab"],
        ["--baseline-only", "--reranker-ab"],
        ["--embedding-precheck", "--reranker-ab"],
        ["--embedding-ab", "--reranker-ab"],
    ]
    for pair in pairs:
        with pytest.raises(SystemExit):
            parser.parse_args(pair)


def test_run_reranker_ab_fails_when_baseline_missing(tmp_path):
    args = CLI.build_parser().parse_args([
        "--reranker-ab",
        "--baseline-quality-path", str(tmp_path / "missing.json"),
        "--reranker-out", str(tmp_path / "ra.json"),
    ])
    rc = CLI.run_reranker_ab(args, model_factory=lambda _id: object())
    assert rc == 2


def test_run_reranker_ab_invokes_sweep(tmp_path, monkeypatch):
    """CLI-level smoke: --reranker-ab loads baseline, restricts
    candidates by low_memory_only default, calls reranker_ab_sweep,
    writes the report. Sweep itself is monkey-patched so this test
    doesn't load any reranker model."""
    from scripts.learning.rag.eval import reranker_ab
    from scripts.learning.rag.eval.gate import (
        BaselineScore,
        GateThresholds,
    )

    # Synthetic baseline JSON
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({
            "macro_reports": {
                "primary_ndcg": {
                    "category": {
                        "axis": "category", "macro_mean": 0.95,
                        "micro_mean": 0.95,
                        "per_bucket_mean": {"spring": 0.95},
                        "per_bucket_count": {"spring": 50},
                        "included_buckets": ["spring"], "excluded_buckets": [],
                    }
                }
            },
            "overall_means": {"forbidden_rate": 0.0},
            "regression_summary": {"failed_count": 5},
        }),
        encoding="utf-8",
    )

    # Fixture
    fixture_path = tmp_path / "fx.json"
    fixture_path.write_text(
        json.dumps({"queries": [{
            "id": "q1",
            "prompt": "test",
            "learning_points": [],
            "expected_path": "contents/spring/bean.md",
            "max_rank": 10,
        }]}, ensure_ascii=False),
        encoding="utf-8",
    )

    captured: dict = {}

    fake_report = reranker_ab.RerankerABReport(
        baseline=BaselineScore(
            primary_ndcg_macro=0.95,
            primary_ndcg_by_category={"spring": 0.95},
            primary_ndcg_category_counts={"spring": 50},
            forbidden_rate_overall=0.0,
            hard_regression_failures=5,
        ),
        thresholds=GateThresholds(),
        embedding_index_root=str(tmp_path),
        candidates=(),
        pareto_order=("mxbai-rerank-base-v1",),
        selected_candidate_id="mxbai-rerank-base-v1",
        selection_rationale="fake",
    )

    def fake_sweep(candidates, queries, baseline, **kwargs):
        captured["candidate_ids"] = [c.candidate_id for c in candidates]
        captured["embedding_index_root"] = kwargs.get("embedding_index_root")
        return fake_report

    monkeypatch.setattr(reranker_ab, "run_reranker_ab_sweep", fake_sweep)

    out = tmp_path / "ra.json"
    args = CLI.build_parser().parse_args([
        "--reranker-ab",
        "--fixture", str(fixture_path),
        "--baseline-quality-path", str(baseline_path),
        "--reranker-out", str(out),
        "--embedding-index-root", str(tmp_path / "fake_index"),
    ])
    rc = CLI.run_reranker_ab(args, model_factory=lambda _id: object())

    assert rc == 0
    # Default = low_memory_only → bge-reranker-v2-m3 excluded
    assert "bge-reranker-v2-m3" not in captured["candidate_ids"]
    assert "mxbai-rerank-base-v1" in captured["candidate_ids"]
    assert "mmarco-mMiniLMv2" in captured["candidate_ids"]

    # Report written
    assert out.exists()
    blob = json.loads(out.read_text())
    assert blob["selected_candidate_id"] == "mxbai-rerank-base-v1"


def test_run_reranker_ab_include_high_memory_flag(tmp_path, monkeypatch):
    """--reranker-include-high-memory adds bge-reranker-v2-m3."""
    from scripts.learning.rag.eval import reranker_ab
    from scripts.learning.rag.eval.gate import BaselineScore, GateThresholds

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({
            "macro_reports": {"primary_ndcg": {"category": {
                "axis": "category", "macro_mean": 0.95, "micro_mean": 0.95,
                "per_bucket_mean": {"spring": 0.95},
                "per_bucket_count": {"spring": 50},
                "included_buckets": ["spring"], "excluded_buckets": [],
            }}},
            "overall_means": {"forbidden_rate": 0.0},
            "regression_summary": {"failed_count": 5},
        }),
        encoding="utf-8",
    )

    fixture_path = tmp_path / "fx.json"
    fixture_path.write_text(
        json.dumps({"queries": [{
            "id": "q", "prompt": "p", "learning_points": [],
            "expected_path": "contents/spring/x.md", "max_rank": 10,
        }]}),
        encoding="utf-8",
    )

    captured: dict = {}

    def fake_sweep(candidates, queries, baseline, **kwargs):
        captured["candidate_ids"] = [c.candidate_id for c in candidates]
        return reranker_ab.RerankerABReport(
            baseline=BaselineScore(0.95, {"spring": 0.95}, {"spring": 50}, 0.0, 5),
            thresholds=GateThresholds(),
            embedding_index_root=str(tmp_path),
            candidates=(),
            pareto_order=(),
            selected_candidate_id=None,
            selection_rationale="none",
        )

    monkeypatch.setattr(reranker_ab, "run_reranker_ab_sweep", fake_sweep)

    args = CLI.build_parser().parse_args([
        "--reranker-ab",
        "--fixture", str(fixture_path),
        "--baseline-quality-path", str(baseline_path),
        "--reranker-out", str(tmp_path / "ra.json"),
        "--reranker-include-high-memory",
    ])
    CLI.run_reranker_ab(args, model_factory=lambda _id: object())

    # All 3 candidates present (control + mxbai + bge-reranker)
    assert set(captured["candidate_ids"]) == {
        "mmarco-mMiniLMv2",
        "mxbai-rerank-base-v1",
        "bge-reranker-v2-m3",
    }


def test_run_embedding_ab_invokes_sweep_and_writes_report(tmp_path, monkeypatch):
    """CLI-level smoke: --embedding-ab loads baseline, restricts
    candidates, calls ab_sweep, writes the report. The sweep itself
    is monkey-patched to a fake so this test doesn't build any
    indexes — sweep behaviour is covered by test_rag_eval_ab_sweep."""
    from scripts.learning.rag.eval import ab_sweep
    from scripts.learning.rag.eval.gate import (
        BaselineScore,
        GateThresholds,
    )

    # Synthetic baseline JSON (matches baseline_from_quality_blob shape)
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({
            "macro_reports": {
                "primary_ndcg": {
                    "category": {
                        "axis": "category", "macro_mean": 0.95,
                        "micro_mean": 0.95,
                        "per_bucket_mean": {"spring": 0.95},
                        "per_bucket_count": {"spring": 50},
                        "included_buckets": ["spring"], "excluded_buckets": [],
                    }
                }
            },
            "overall_means": {"forbidden_rate": 0.0},
            "regression_summary": {"failed_count": 5},
        }),
        encoding="utf-8",
    )

    # Fixture (real legacy or graded — load_queries handles both)
    fixture_path = tmp_path / "fx.json"
    fixture_path.write_text(
        json.dumps({"queries": [{
            "id": "q1",
            "prompt": "test",
            "learning_points": [],
            "expected_path": "contents/spring/bean.md",
            "max_rank": 10,
        }]}, ensure_ascii=False),
        encoding="utf-8",
    )

    # Capture call args + return a fake report
    captured: dict = {}

    fake_report = ab_sweep.ABReport(
        baseline=BaselineScore(
            primary_ndcg_macro=0.95,
            primary_ndcg_by_category={"spring": 0.95},
            primary_ndcg_category_counts={"spring": 50},
            forbidden_rate_overall=0.0,
            hard_regression_failures=5,
        ),
        thresholds=GateThresholds(),
        candidates=(),
        pareto_order=("MiniLM-L12-v2",),
        selected_candidate_id="MiniLM-L12-v2",
        selection_rationale="fake",
    )

    def fake_sweep(candidates, queries, baseline, **kwargs):
        captured["candidate_ids"] = [c.candidate_id for c in candidates]
        captured["query_count"] = len(list(queries))
        captured["baseline_macro"] = baseline.primary_ndcg_macro
        return fake_report

    monkeypatch.setattr(ab_sweep, "run_ab_sweep", fake_sweep)

    ab_out = tmp_path / "ab.json"
    args = CLI.build_parser().parse_args([
        "--embedding-ab",
        "--fixture", str(fixture_path),
        "--baseline-quality-path", str(baseline_path),
        "--ab-out", str(ab_out),
        "--ab-base-dir", str(tmp_path / "ab_base"),
        "--candidate-id", "MiniLM-L12-v2",
    ])
    rc = CLI.run_embedding_ab(args, model_factory=lambda *_: _FakeEnc())

    # Selection set → exit 0
    assert rc == 0
    # Sweep invoked with restricted candidates
    assert captured["candidate_ids"] == ["MiniLM-L12-v2"]
    assert captured["query_count"] == 1
    assert captured["baseline_macro"] == 0.95

    # Report written
    assert ab_out.exists()
    blob = json.loads(ab_out.read_text())
    assert blob["selected_candidate_id"] == "MiniLM-L12-v2"


# ---------------------------------------------------------------------------
# encode_progress formatter (P2/P3 visibility fix)
# ---------------------------------------------------------------------------

class TestFormatEncodeProgress:
    def test_renders_basic_fields(self):
        out = CLI._format_encode_progress({
            "done": 1024, "total": 27155,
            "elapsed_s": 60.0, "eta_s": 1500.0, "rate_per_s": 17.07,
        })
        assert "1024/27155" in out
        assert "3.8%" in out  # 1024/27155
        assert "rate=17.07/s" in out

    def test_long_eta_formatted_as_min_sec(self):
        out = CLI._format_encode_progress({
            "done": 100, "total": 1000,
            "elapsed_s": 10.0, "eta_s": 1230.0, "rate_per_s": 10.0,
        })
        # 1230s = 20m30s
        assert "eta=20m30s" in out

    def test_short_eta_formatted_as_seconds(self):
        out = CLI._format_encode_progress({
            "done": 950, "total": 1000,
            "elapsed_s": 95.0, "eta_s": 5.0, "rate_per_s": 10.0,
        })
        assert "eta=5.0s" in out

    def test_zero_total_does_not_divide_by_zero(self):
        """Defensive — total==0 shouldn't blow up the formatter."""
        out = CLI._format_encode_progress({
            "done": 0, "total": 0,
            "elapsed_s": 0, "eta_s": 0, "rate_per_s": 0,
        })
        assert "0/0" in out
        # No exception, no inf/nan in output
        assert "inf" not in out
        assert "nan" not in out
