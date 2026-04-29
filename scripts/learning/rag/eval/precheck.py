"""Pre-flight measurement of an embedding candidate.

Plan §10 §P2 진입 전 — measure cold-load time, warm-encode latency,
and RSS before committing to a full corpus build (~30 min per
candidate). Provides early signal whether a candidate would even pass
the gate's warm_p95 / rss budgets.

Output is a PrecheckResult dataclass; the CLI wraps measure_candidate
to write a JSON report under state/cs_rag/embedding_precheck.json.

Design decisions:
- model_factory is dependency-injected so tests can pass a fake
  without loading SentenceTransformer.
- RSS uses stdlib resource.getrusage; ru_maxrss units differ by OS
  (Darwin: bytes, Linux: KB) so we normalise to MB.
- Warm-up: one untimed encode before measurement so PyTorch JIT /
  MPS stream setup don't poison the first warm sample.
- Determinism: warm timings are sorted before percentile picks; the
  N=encode_iterations parameter controls confidence.
"""

from __future__ import annotations

import resource
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any


def get_process_rss_mb() -> float:
    """Return current process maximum RSS in MB.

    macOS reports ru_maxrss in bytes; Linux reports it in kilobytes.
    The "max" semantics mean this number only ever climbs — useful
    for measuring peak footprint after model load, not for tracking
    moment-to-moment usage.
    """
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return rss / (1024 * 1024)  # bytes → MB
    return rss / 1024  # KB → MB


@dataclass(frozen=True)
class PrecheckResult:
    """One candidate's pre-flight measurements."""

    candidate_id: str
    hf_model_id: str
    embed_dim: int
    model_load_ms: float
    warm_encode_p50_ms: float
    warm_encode_p95_ms: float
    rss_after_load_mb: float
    rss_after_encode_mb: float
    encode_iterations: int

    def to_dict(self) -> dict:
        return asdict(self)


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Inclusive percentile pick on a pre-sorted list. ``pct`` in [0, 100]."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = max(0, min(len(sorted_values) - 1, int(round((pct / 100) * (len(sorted_values) - 1)))))
    return sorted_values[idx]


def measure_candidate(
    candidate: Any,  # EmbeddingCandidate, duck-typed
    *,
    model_factory: Callable[[str, int], Any],
    sample_query: str = "Spring Bean이 뭐야?",
    encode_iterations: int = 10,
) -> PrecheckResult:
    """Load ``candidate`` via model_factory, measure cold + warm + RSS.

    Args:
        candidate: must have .candidate_id, .hf_model_id, .embed_dim.
        model_factory: callable(hf_model_id, embed_dim) -> encoder.
            Real production uses a SentenceTransformer factory; tests
            pass a fake.
        sample_query: short query used for warm-encode timing.
        encode_iterations: warm-encode samples after the warm-up call.
            P50 / P95 are picked from these samples.

    Returns:
        PrecheckResult with all measured fields. Caller decides
        whether the numbers pass plan §P2.1 gate budgets — this
        module just measures.
    """
    rss_before = get_process_rss_mb()
    t0 = time.perf_counter()
    model = model_factory(candidate.hf_model_id, candidate.embed_dim)
    model_load_ms = (time.perf_counter() - t0) * 1000.0
    rss_after_load = get_process_rss_mb()

    # Warm-up: untimed first call so JIT / device-stream setup doesn't
    # contaminate the first measured sample.
    model.encode(
        [sample_query],
        batch_size=1,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    timings: list[float] = []
    for _ in range(encode_iterations):
        t0 = time.perf_counter()
        model.encode(
            [sample_query],
            batch_size=1,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        timings.append((time.perf_counter() - t0) * 1000.0)

    rss_after_encode = get_process_rss_mb()

    timings.sort()
    p50 = _percentile(timings, 50)
    p95 = _percentile(timings, 95)

    return PrecheckResult(
        candidate_id=candidate.candidate_id,
        hf_model_id=candidate.hf_model_id,
        embed_dim=candidate.embed_dim,
        model_load_ms=model_load_ms,
        warm_encode_p50_ms=p50,
        warm_encode_p95_ms=p95,
        rss_after_load_mb=rss_after_load,
        rss_after_encode_mb=rss_after_encode,
        encode_iterations=encode_iterations,
    )
