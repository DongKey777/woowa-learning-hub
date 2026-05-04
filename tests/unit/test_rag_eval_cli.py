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
    assert args.backend == "auto"
    assert args.index_root == CLI.DEFAULT_EMBEDDING_INDEX_ROOT
    assert args.legacy_archive is None
    assert args.eval_split == "full"


def test_parser_baseline_only_runtime_overrides(tmp_path):
    parser = CLI.build_parser()
    args = parser.parse_args([
        "--baseline-only",
        "--index-root", str(tmp_path / "idx"),
        "--backend", "lance",
        "--legacy-archive", str(tmp_path / "legacy"),
        "--eval-split", "holdout",
    ])
    assert args.index_root == tmp_path / "idx"
    assert args.backend == "lance"
    assert args.legacy_archive == tmp_path / "legacy"
    assert args.eval_split == "holdout"


def test_parser_ablate_mode():
    parser = CLI.build_parser()
    args = parser.parse_args(["--ablate", "--ablation-modalities", "fts,dense"])
    assert args.ablate is True
    assert args.ablation_split == "tune"
    assert args.ablation_modalities == ["fts,dense"]


def test_parser_sampled_ablate_mode():
    parser = CLI.build_parser()
    args = parser.parse_args([
        "--sampled-ablate",
        "--sample-categories", "spring,database",
        "--sample-extra-docs-per-category", "3",
        "--ablation-modalities", "fts",
    ])
    assert args.sampled_ablate is True
    assert args.sample_categories == "spring,database"
    assert args.sample_extra_docs_per_category == 3
    assert args.ablation_modalities == ["fts"]


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
# --baseline-only runtime wiring
# ---------------------------------------------------------------------------

def test_run_baseline_only_uses_explicit_legacy_index_root(tmp_path, monkeypatch):
    from scripts.learning.rag import indexer, searcher

    index_root = tmp_path / "legacy_idx"
    index_root.mkdir()
    (index_root / indexer.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "index_version": indexer.INDEX_VERSION,
                "corpus_hash": "legacy-hash",
                "embed_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "embed_dim": 384,
            }
        ),
        encoding="utf-8",
    )

    calls: list[dict] = []

    def fake_search(prompt, **kwargs):
        calls.append(kwargs)
        kwargs["debug"].update(
            {
                "backend": kwargs["backend"],
                "modalities": ["fts", "dense"],
                "reranker_enabled": True,
                "rerank_top_n": 20,
                "rerank_input_count": 1,
                "stage_ms": {"legacy_candidate_pool": 1.25},
            }
        )
        return [{"path": "contents/spring/bean.md"}]

    monkeypatch.setattr(searcher, "search", fake_search)
    out_quality = tmp_path / "quality.json"
    out_machine = tmp_path / "machine.json"
    args = CLI.build_parser().parse_args([
        "--baseline-only",
        "--fixture", str(_legacy_fixture(tmp_path)),
        "--index-root", str(index_root),
        "--backend", "legacy",
        "--out-quality", str(out_quality),
        "--out-machine", str(out_machine),
        "--device", "cpu",
    ])

    rc = CLI.run_baseline_only(args)

    assert rc == 0
    assert calls
    assert all(call["backend"] == "legacy" for call in calls)
    assert all(call["index_root"] == index_root for call in calls)

    quality = json.loads(out_quality.read_text(encoding="utf-8"))
    assert quality["manifest"]["backend"] == "legacy"
    assert quality["manifest"]["modalities"] == ["fts", "dense"]
    assert quality["manifest"]["embedding_dim"] == 384

    machine = json.loads(out_machine.read_text(encoding="utf-8"))
    assert machine["runtime"]["backend"] == "legacy"
    assert machine["runtime"]["index_root"] == str(index_root)
    assert machine["runtime_debug"][0]["rerank_input_count"] == 1
    assert machine["runtime_summary"]["modalities"] == {"fts,dense": 2}
    assert machine["runtime_summary"]["stage_ms"]["legacy_candidate_pool"]["count"] == 2
    assert machine["runtime_summary"]["stage_ms"]["legacy_candidate_pool"]["p95_ms"] == 1.25


def test_run_baseline_only_supports_lance_v3_manifest(tmp_path, monkeypatch):
    from scripts.learning.rag import indexer, searcher

    index_root = tmp_path / "lance_idx"
    index_root.mkdir()
    (index_root / indexer.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "index_version": indexer.LANCE_INDEX_VERSION,
                "schema_uri": "https://woowa-learning-hub/schemas/cs-index-manifest-v3.json",
                "row_count": 1,
                "corpus_hash": "v3-hash",
                "corpus_root": "corpus",
                "built_at": "2026-05-01T00:00:00Z",
                "encoder": {
                    "model_id": "BAAI/bge-m3",
                    "model_version": "BAAI/bge-m3@test",
                    "dense_dim": 1024,
                    "max_length": 512,
                },
                "lancedb": {
                    "version": "0.30.2",
                    "table_name": indexer.LANCE_TABLE_NAME,
                    "indices": {},
                },
                "modalities": ["fts", "dense", "sparse"],
                "ingest": {"chunk_max_chars": 1600, "chunk_overlap": 0},
            }
        ),
        encoding="utf-8",
    )

    calls: list[dict] = []

    def fake_search(prompt, **kwargs):
        calls.append(kwargs)
        kwargs["debug"].update(
            {
                "backend": "lance",
                "modalities": ["fts", "dense", "sparse"],
                "reranker_enabled": True,
                "rerank_top_n": 20,
                "rerank_input_count": 1,
                "stage_ms": {"lance_candidate_plan": 2.5},
            }
        )
        return [{"path": "contents/spring/bean.md"}]

    monkeypatch.setattr(searcher, "search", fake_search)
    out_quality = tmp_path / "quality.json"
    args = CLI.build_parser().parse_args([
        "--baseline-only",
        "--fixture", str(_legacy_fixture(tmp_path)),
        "--index-root", str(index_root),
        "--backend", "auto",
        "--out-quality", str(out_quality),
        "--out-machine", str(tmp_path / "machine.json"),
        "--device", "cpu",
    ])

    rc = CLI.run_baseline_only(args)

    assert rc == 0
    assert calls[0]["backend"] == "lance"
    assert calls[0]["index_root"] == index_root

    quality = json.loads(out_quality.read_text(encoding="utf-8"))
    assert quality["manifest"]["backend"] == "lance"
    assert quality["manifest"]["embedding_model"] == "BAAI/bge-m3"
    assert quality["manifest"]["embedding_dim"] == 1024
    assert quality["manifest"]["modalities"] == ["fts", "dense", "sparse"]


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


def test_parser_modes_are_mutually_exclusive_for_expensive_modes():
    parser = CLI.build_parser()
    pairs = [
        ["--fast", "--reranker-ab"],
        ["--baseline-only", "--reranker-ab"],
        ["--embedding-precheck", "--reranker-ab"],
        ["--embedding-ab", "--reranker-ab"],
        ["--ablate", "--sampled-ablate"],
        ["--reranker-ab", "--sampled-ablate"],
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


def test_run_ablate_invokes_modal_ablation_and_writes_report(tmp_path, monkeypatch):
    from scripts.learning.rag.eval import ablation as A

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
    fake_report = A.AblationReport(
        index_root=str(tmp_path / "idx"),
        split="tune",
        query_count=1,
        top_k=10,
        forbidden_window=5,
        mode="full",
        runs=(),
        best_modalities=("fts", "dense"),
        selection_rationale="fake",
    )

    def fake_ablate(queries, **kwargs):
        captured["query_count"] = len(list(queries))
        captured["index_root"] = kwargs["index_root"]
        captured["modality_sets"] = kwargs["modality_sets"]
        captured["embedding_dim"] = kwargs["embedding_dim"]
        return fake_report

    monkeypatch.setattr(A, "run_modality_ablation", fake_ablate)

    out = tmp_path / "ablation.json"
    args = CLI.build_parser().parse_args([
        "--ablate",
        "--fixture", str(fixture_path),
        "--embedding-index-root", str(tmp_path / "idx"),
        "--ablation-out", str(out),
        "--ablation-modalities", "fts,dense",
    ])
    rc = CLI.run_ablate(args, encoder_factory=lambda: object())

    assert rc == 0
    assert captured["query_count"] == 1
    assert captured["modality_sets"] == (("fts", "dense"),)
    assert captured["embedding_dim"] == 1024
    blob = json.loads(out.read_text(encoding="utf-8"))
    assert blob["best_modalities"] == ["fts", "dense"]


def test_run_sampled_ablate_builds_sample_index_and_skips_encoder_for_fts_only(
    tmp_path,
    monkeypatch,
):
    from scripts.learning.rag.eval import ablation as A
    from scripts.learning.rag.eval import sampled_ablation as S

    fixture_path = _graded_fixture(tmp_path)
    sample_root = tmp_path / "sample"
    captured: dict = {}

    def fake_materialize(**kwargs):
        sample_corpus = sample_root / "corpus"
        sample_corpus.mkdir(parents=True)
        captured["categories"] = kwargs["categories"]
        captured["extra_docs_per_category"] = kwargs["extra_docs_per_category"]
        return S.SampledCorpusResult(
            corpus_root=sample_corpus,
            fixture_path=sample_root / "fixture.json",
            categories=("spring",),
            queries=tuple(kwargs["queries"]),
            required_doc_paths=("contents/spring/bean.md",),
            extra_doc_paths=("contents/spring/ioc.md",),
        )

    def fake_build(build_args):
        captured["build_args"] = build_args
        return 0

    fake_report = A.AblationReport(
        index_root=str(sample_root / "index"),
        split="full",
        query_count=1,
        top_k=10,
        forbidden_window=5,
        mode="full",
        runs=(),
        best_modalities=("fts",),
        selection_rationale="fake",
    )

    def fake_ablate(queries, **kwargs):
        captured["query_count"] = len(list(queries))
        captured["index_root"] = kwargs["index_root"]
        captured["encoder"] = kwargs["encoder"]
        captured["modality_sets"] = kwargs["modality_sets"]
        return fake_report

    def fail_encoder_factory():
        raise AssertionError("FTS-only sampled ablation must not load bge-m3")

    monkeypatch.setattr(S, "materialize_sampled_corpus", fake_materialize)
    monkeypatch.setattr(CLI, "_lance_index_ready_for_modalities", lambda *_a, **_k: False)
    monkeypatch.setattr(A, "run_modality_ablation", fake_ablate)

    out = tmp_path / "sampled-ablation.json"
    args = CLI.build_parser().parse_args([
        "--sampled-ablate",
        "--fixture", str(fixture_path),
        "--sample-root", str(sample_root),
        "--sample-categories", "spring",
        "--sample-extra-docs-per-category", "2",
        "--ablation-split", "full",
        "--ablation-out", str(out),
        "--ablation-modalities", "fts",
        "--device", "cpu",
    ])
    rc = CLI.run_sampled_ablate(
        args,
        encoder_factory=fail_encoder_factory,
        build_main=fake_build,
    )

    assert rc == 0
    assert captured["categories"] == ("spring",)
    assert captured["extra_docs_per_category"] == 2
    assert "--backend" in captured["build_args"]
    assert captured["build_args"][captured["build_args"].index("--modalities") + 1] == "fts"
    assert captured["query_count"] == 1
    assert captured["modality_sets"] == (("fts",),)
    assert captured["encoder"].__class__ is object

    blob = json.loads(out.read_text(encoding="utf-8"))
    assert blob["best_modalities"] == ["fts"]
    assert blob["sample"]["doc_count"] == 2
    assert blob["sample"]["index_modalities"] == ["fts"]


def test_run_sampled_ablate_reuses_matching_sample_index(tmp_path, monkeypatch):
    from scripts.learning.rag.eval import ablation as A
    from scripts.learning.rag.eval import sampled_ablation as S

    fixture_path = _graded_fixture(tmp_path)
    sample_root = tmp_path / "sample"

    def fake_materialize(**kwargs):
        sample_corpus = sample_root / "corpus"
        sample_corpus.mkdir(parents=True)
        return S.SampledCorpusResult(
            corpus_root=sample_corpus,
            fixture_path=sample_root / "fixture.json",
            categories=("spring",),
            queries=tuple(kwargs["queries"]),
            required_doc_paths=("contents/spring/bean.md",),
            extra_doc_paths=(),
        )

    def fail_build(_build_args):
        raise AssertionError("matching sampled index should be reused")

    fake_report = A.AblationReport(
        index_root=str(sample_root / "index"),
        split="full",
        query_count=1,
        top_k=10,
        forbidden_window=5,
        mode="full",
        runs=(),
        best_modalities=("fts",),
        selection_rationale="fake",
    )

    monkeypatch.setattr(S, "materialize_sampled_corpus", fake_materialize)
    monkeypatch.setattr(CLI, "_lance_index_ready_for_modalities", lambda *_a, **_k: True)
    monkeypatch.setattr(A, "run_modality_ablation", lambda queries, **kwargs: fake_report)

    args = CLI.build_parser().parse_args([
        "--sampled-ablate",
        "--fixture", str(fixture_path),
        "--sample-root", str(sample_root),
        "--sample-categories", "spring",
        "--ablation-split", "full",
        "--ablation-out", str(tmp_path / "sampled-ablation.json"),
        "--ablation-modalities", "fts",
    ])
    assert CLI.run_sampled_ablate(args, build_main=fail_build) == 0


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
