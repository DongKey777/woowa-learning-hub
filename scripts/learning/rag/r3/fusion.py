"""Fusion helpers for independent R3 candidate generators."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .candidate import Candidate


DEFAULT_RETRIEVER_WEIGHTS = {
    "lexical:title": 1.2,
    "lexical:section": 1.0,
    "lexical:aliases": 1.2,
    "lexical:body": 0.8,
    "dense": 1.0,
    "sparse": 1.1,
    "signal": 0.7,
}


@dataclass(frozen=True)
class FusionSource:
    retriever: str
    rank: int
    score: float

    def to_dict(self) -> dict:
        return {"retriever": self.retriever, "rank": self.rank, "score": self.score}


def fuse_candidates(
    candidates: Iterable[Candidate],
    *,
    limit: int = 120,
    k: int = 60,
    weights: dict[str, float] | None = None,
) -> list[Candidate]:
    """Fuse candidates with weighted RRF while preserving provenance."""

    effective_weights = {**DEFAULT_RETRIEVER_WEIGHTS, **(weights or {})}
    scores: dict[tuple[str, str | None], float] = {}
    exemplars: dict[tuple[str, str | None], Candidate] = {}
    sources: dict[tuple[str, str | None], list[FusionSource]] = defaultdict(list)

    for candidate in candidates:
        key = (candidate.path, candidate.chunk_id)
        weight = effective_weights.get(candidate.retriever, 1.0)
        if weight <= 0:
            continue
        scores[key] = scores.get(key, 0.0) + weight / (k + candidate.rank)
        exemplars.setdefault(key, candidate)
        sources[key].append(
            FusionSource(
                retriever=candidate.retriever,
                rank=candidate.rank,
                score=candidate.score,
            )
        )

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0][0], item[0][1] or ""))
    fused: list[Candidate] = []
    seen_paths: set[str] = set()
    for key, score in ranked:
        exemplar = exemplars[key]
        if exemplar.path in seen_paths:
            continue
        seen_paths.add(exemplar.path)
        metadata = {
            key: value
            for key, value in exemplar.metadata.items()
            if key != "sources"
        }
        metadata["sources"] = [source.to_dict() for source in sources[key]]
        fused.append(
            Candidate(
                path=exemplar.path,
                chunk_id=exemplar.chunk_id,
                retriever="fusion",
                rank=len(fused) + 1,
                score=float(score),
                title=exemplar.title,
                section_title=exemplar.section_title,
                metadata=metadata,
            )
        )
        if len(fused) >= limit:
            break
    return fused
