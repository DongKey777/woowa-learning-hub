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
