"""Reranker candidate registry for the P3.1 A/B sweep.

Plan §3 SOTA gap mapping + §P3.1 — reranker is the second ML
component in the retrieval stack (after embedding). The current
production reranker is from 2021; SOTA in 2026 is bge-reranker-v2-m3
or jina-reranker-v2.

Sizing constraints from this session's measured OOM events on M4 16GB:
- bge-reranker-v2-m3 (568M params, ~2.27GB fp32) stacked on a 1024-dim
  embedding (e5-base 5GB RSS, Qwen3 ~6GB) cannot coexist in 16GB
  unified memory. Trying causes the OOM-killer to take the process.
- mxbai-rerank-base-v1 (~120MB) is the safe upgrade candidate; can
  coexist with any P2 embedding without memory pressure.
- bge-reranker-v2-m3 requires either a single-candidate sweep with
  cleanup (free embedding RAM between encode & rerank) or running
  on a machine with more RAM.

This module enumerates the candidates; ab_sweep is responsible for
honouring the OOM constraint when scheduling actual measurements.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RerankerCandidate:
    """One reranker entrant in the A/B sweep."""

    candidate_id: str
    hf_model_id: str
    approx_size_mb: float
    is_control: bool
    high_memory_risk: bool
    """True if this candidate's RAM footprint is large enough that
    stacking with a 1024-dim embedding on 16GB unified memory triggers
    OOM-kill. ab_sweep can refuse to schedule it alongside large
    embeddings, or fall back to a single-candidate cleanup-after run."""
    notes: str

    def index_dir_name(self) -> str:
        """Filesystem-safe sub-directory under state/cs_rag_eval/."""
        return f"reranker__{self.candidate_id}"


CANDIDATES: tuple[RerankerCandidate, ...] = (
    RerankerCandidate(
        candidate_id="mmarco-mMiniLMv2",
        hf_model_id="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        approx_size_mb=120,
        is_control=True,
        high_memory_risk=False,
        notes="Production baseline (2021). 384-dim cross-encoder; multilingual MS MARCO.",
    ),
    RerankerCandidate(
        candidate_id="mxbai-rerank-base-v1",
        hf_model_id="mixedbread-ai/mxbai-rerank-base-v1",
        approx_size_mb=120,
        is_control=False,
        high_memory_risk=False,
        notes="Lighter SOTA candidate (mid-2024). Same memory class as control; safest upgrade.",
    ),
    RerankerCandidate(
        candidate_id="bge-reranker-v2-m3",
        hf_model_id="BAAI/bge-reranker-v2-m3",
        approx_size_mb=2270,
        is_control=False,
        high_memory_risk=True,
        notes="SOTA Korean-strong reranker (BAAI 2024, 568M params). High memory; "
               "schedule with single-candidate cleanup-after sweep on 16GB machines.",
    ),
)
"""The full P3.1 sweep — index 0 is control."""


_BY_ID = {c.candidate_id: c for c in CANDIDATES}


def get(candidate_id: str) -> RerankerCandidate:
    """Look up a candidate by id. Raises ValueError on unknown id."""
    if candidate_id not in _BY_ID:
        known = sorted(_BY_ID)
        raise ValueError(
            f"unknown reranker candidate_id: {candidate_id!r}. Known: {known}"
        )
    return _BY_ID[candidate_id]


def control() -> RerankerCandidate:
    """Return the single is_control=True candidate.

    Asserts exactly one — multiple controls would corrupt the
    baseline-vs-candidate framing of the gate.
    """
    controls = [c for c in CANDIDATES if c.is_control]
    if len(controls) != 1:
        raise RuntimeError(
            f"expected exactly one control reranker; got {len(controls)}"
        )
    return controls[0]


def upgrades() -> tuple[RerankerCandidate, ...]:
    """All non-control candidates, in CANDIDATES declaration order."""
    return tuple(c for c in CANDIDATES if not c.is_control)


def low_memory_only() -> tuple[RerankerCandidate, ...]:
    """Candidates safe to evaluate alongside any P2 embedding without
    triggering OOM on 16GB machines. Use this for the default sweep on
    constrained hardware; high_memory_risk candidates need a separate
    single-candidate run."""
    return tuple(c for c in CANDIDATES if not c.high_memory_risk)
