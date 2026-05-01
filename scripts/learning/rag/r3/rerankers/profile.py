"""Runtime profiler for R3 reranker candidates."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .cross_encoder import default_model_factory


@dataclass(frozen=True)
class RerankerRuntimeProfile:
    model_id: str
    pair_count: int
    machine: str
    python_version: str
    load_ms: float
    score_ms: float
    per_pair_p50_ms: float
    per_pair_p95_ms: float
    rss_peak_mb: float

    def to_dict(self) -> dict:
        return asdict(self)


def _rss_peak_mb() -> float:
    # macOS reports bytes; Linux reports KiB.
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if platform.system() == "Darwin":
        return value / (1024 * 1024)
    return value / 1024


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=20, method="inclusive")[18]


def profile_reranker(
    model_id: str,
    pairs: list[list[str]],
    *,
    model_factory=None,
) -> RerankerRuntimeProfile:
    """Measure load time, scoring time, per-pair latency, and RSS peak."""

    started = time.perf_counter()
    factory = model_factory or default_model_factory
    model = factory(model_id)
    load_ms = (time.perf_counter() - started) * 1000.0

    per_pair_ms: list[float] = []
    score_started = time.perf_counter()
    for pair in pairs:
        pair_started = time.perf_counter()
        model.predict([pair], show_progress_bar=False)
        per_pair_ms.append((time.perf_counter() - pair_started) * 1000.0)
    score_ms = (time.perf_counter() - score_started) * 1000.0

    return RerankerRuntimeProfile(
        model_id=model_id,
        pair_count=len(pairs),
        machine=platform.machine(),
        python_version=platform.python_version(),
        load_ms=round(load_ms, 3),
        score_ms=round(score_ms, 3),
        per_pair_p50_ms=round(statistics.median(per_pair_ms), 3) if per_pair_ms else 0.0,
        per_pair_p95_ms=round(_p95(per_pair_ms), 3),
        rss_peak_mb=round(_rss_peak_mb(), 3),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--pairs-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    pairs = json.loads(args.pairs_json.read_text(encoding="utf-8"))
    if not isinstance(pairs, list):
        raise ValueError("--pairs-json must contain a list of [query, passage] pairs")
    profile = profile_reranker(args.model_id, pairs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote reranker profile to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
