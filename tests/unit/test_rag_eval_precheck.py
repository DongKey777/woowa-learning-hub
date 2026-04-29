"""Unit tests for scripts.learning.rag.eval.precheck.

Coverage targets:
- get_process_rss_mb returns a positive float
- measure_candidate calls factory once with (hf_model_id, embed_dim)
- Cold load timing reflects factory delay
- Warm timings exclude the warm-up call (one extra encode total)
- p50 / p95 picked from the measured samples
- Result dataclass round-trips via asdict
- _percentile boundaries (0 / 100, single sample, empty)
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pytest

from scripts.learning.rag.eval import precheck as P


@dataclass(frozen=True)
class _Candidate:
    """Duck-typed EmbeddingCandidate stand-in."""

    candidate_id: str
    hf_model_id: str
    embed_dim: int


class _SlowFakeEncoder:
    """Encoder fake whose encode() sleeps for ``encode_ms``.

    Lets us assert measurement semantics without booting torch.
    """

    def __init__(self, *, encode_ms: float = 1.0):
        self.encode_ms = encode_ms
        self.encode_calls = 0

    def encode(self, sentences, **kwargs):
        self.encode_calls += 1
        time.sleep(self.encode_ms / 1000.0)
        # Return shape (n, dim=4) of zeros
        import numpy as np
        return np.zeros((len(sentences), 4), dtype="float32")


# ---------------------------------------------------------------------------
# RSS helper
# ---------------------------------------------------------------------------

def test_get_process_rss_mb_returns_positive_float():
    rss = P.get_process_rss_mb()
    assert isinstance(rss, float)
    assert rss > 0


# ---------------------------------------------------------------------------
# _percentile
# ---------------------------------------------------------------------------

def test_percentile_empty_returns_zero():
    assert P._percentile([], 50) == 0.0


def test_percentile_single_sample_returns_it():
    assert P._percentile([42.0], 50) == 42.0
    assert P._percentile([42.0], 95) == 42.0


def test_percentile_picks_correct_index():
    sorted_vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert P._percentile(sorted_vals, 0) == 1.0
    assert P._percentile(sorted_vals, 100) == 5.0
    # 50th percentile of 5 samples: index round(0.5 * 4) = 2 → value 3.0
    assert P._percentile(sorted_vals, 50) == 3.0


# ---------------------------------------------------------------------------
# measure_candidate
# ---------------------------------------------------------------------------

def test_measure_calls_factory_with_candidate_fields():
    cand = _Candidate("c1", "org/repo", 4)
    captured = {}

    def factory(hf_id, dim):
        captured["hf_id"] = hf_id
        captured["dim"] = dim
        return _SlowFakeEncoder(encode_ms=0.1)

    P.measure_candidate(cand, model_factory=factory, encode_iterations=2)

    assert captured == {"hf_id": "org/repo", "dim": 4}


def test_measure_returns_filled_result():
    cand = _Candidate("c1", "org/repo", 4)
    result = P.measure_candidate(
        cand,
        model_factory=lambda *_: _SlowFakeEncoder(encode_ms=0.5),
        encode_iterations=3,
    )

    assert result.candidate_id == "c1"
    assert result.hf_model_id == "org/repo"
    assert result.embed_dim == 4
    assert result.encode_iterations == 3
    assert result.model_load_ms >= 0
    assert result.warm_encode_p50_ms > 0
    assert result.warm_encode_p95_ms >= result.warm_encode_p50_ms
    assert result.rss_after_load_mb > 0


def test_measure_runs_warmup_plus_iterations():
    cand = _Candidate("c", "x/y", 4)
    enc = _SlowFakeEncoder(encode_ms=0.1)
    P.measure_candidate(
        cand,
        model_factory=lambda *_: enc,
        encode_iterations=5,
    )
    # 1 warm-up + 5 measurements = 6 calls
    assert enc.encode_calls == 6


def test_measure_cold_load_reflects_factory_latency():
    """A factory that sleeps ~50ms should produce model_load_ms > 30."""
    cand = _Candidate("c", "x/y", 4)

    def slow_factory(*_):
        time.sleep(0.05)  # 50ms
        return _SlowFakeEncoder(encode_ms=0.0)

    result = P.measure_candidate(
        cand, model_factory=slow_factory, encode_iterations=2
    )
    assert result.model_load_ms >= 30  # generous lower bound


def test_measure_dict_round_trip():
    cand = _Candidate("c", "x/y", 4)
    result = P.measure_candidate(
        cand,
        model_factory=lambda *_: _SlowFakeEncoder(),
        encode_iterations=2,
    )
    blob = result.to_dict()
    assert set(blob) == {
        "candidate_id", "hf_model_id", "embed_dim",
        "model_load_ms", "warm_encode_p50_ms", "warm_encode_p95_ms",
        "rss_after_load_mb", "rss_after_encode_mb", "encode_iterations",
    }


def test_measure_default_iterations():
    cand = _Candidate("c", "x/y", 4)
    enc = _SlowFakeEncoder(encode_ms=0.1)
    result = P.measure_candidate(cand, model_factory=lambda *_: enc)
    # Default is 10
    assert result.encode_iterations == 10
    # 1 warm-up + 10 measurements
    assert enc.encode_calls == 11
