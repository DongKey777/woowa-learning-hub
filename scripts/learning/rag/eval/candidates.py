"""Embedding candidate registry for the P2.1 A/B sweep.

Plan §3 SOTA gap mapping + §P2.1 candidate list — four candidates,
one is control, three are upgrade options across the size/quality
spectrum. The CLI sweep iterates this list; tests look candidates up
by id.

Sizing notes are approximate (HF model card numbers + ~10% margin
for tokenizer files). They feed Pareto comparison only — actual RSS
is measured at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingCandidate:
    """One embedding model entrant in the A/B sweep."""

    candidate_id: str
    hf_model_id: str
    embed_dim: int
    approx_size_mb: float
    is_control: bool
    notes: str

    def index_dir_name(self) -> str:
        """Filesystem-safe name for the eval index directory.

        Mirrors index_builder.eval_index_root_for behaviour but tied
        to candidate_id (which is already filesystem-safe) rather
        than hf_model_id (which contains '/')."""
        return self.candidate_id


CANDIDATES: tuple[EmbeddingCandidate, ...] = (
    EmbeddingCandidate(
        candidate_id="MiniLM-L12-v2",
        hf_model_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        embed_dim=384,
        approx_size_mb=470,
        is_control=True,
        notes="Production baseline (2020). 50+ languages.",
    ),
    EmbeddingCandidate(
        candidate_id="multilingual-e5-base",
        hf_model_id="intfloat/multilingual-e5-base",
        embed_dim=768,
        approx_size_mb=280,
        is_control=False,
        notes="Lighter than baseline; 100+ languages, dim 768. Smallest viable upgrade.",
    ),
    EmbeddingCandidate(
        candidate_id="Qwen3-Embedding-0.6B",
        hf_model_id="Qwen/Qwen3-Embedding-0.6B",
        embed_dim=1024,
        approx_size_mb=1200,
        is_control=False,
        notes="2025 model, 100+ languages, 1024-dim. Pareto sweet-spot candidate.",
    ),
    EmbeddingCandidate(
        candidate_id="bge-m3",
        hf_model_id="BAAI/bge-m3",
        embed_dim=1024,
        approx_size_mb=2270,
        is_control=False,
        notes="Korean-strong dense+sparse+multivector (BAAI 2024). Largest candidate.",
    ),
)
"""The full P2.1 sweep — index 0 is the control."""


_BY_ID = {c.candidate_id: c for c in CANDIDATES}


def get(candidate_id: str) -> EmbeddingCandidate:
    """Look up a candidate by id. Raises ValueError on unknown id."""
    if candidate_id not in _BY_ID:
        known = sorted(_BY_ID)
        raise ValueError(
            f"unknown candidate_id: {candidate_id!r}. Known: {known}"
        )
    return _BY_ID[candidate_id]


def control() -> EmbeddingCandidate:
    """Return the single is_control=True candidate.

    Asserts exactly one — multiple controls would corrupt the
    baseline-vs-candidate framing of the gate.
    """
    controls = [c for c in CANDIDATES if c.is_control]
    if len(controls) != 1:
        raise RuntimeError(
            f"expected exactly one control candidate; got {len(controls)}"
        )
    return controls[0]


def upgrades() -> tuple[EmbeddingCandidate, ...]:
    """All non-control candidates, in CANDIDATES declaration order."""
    return tuple(c for c in CANDIDATES if not c.is_control)
