"""Pure helpers for context-aware multi-query retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

RRF_K = 60


@dataclass(frozen=True)
class QueryCandidate:
    text: str
    kind: str
    weight: float


QUERY_WEIGHTS = {
    "original": 1.0,
    "follow_up": 0.9,
    "rewrite": 0.8,
    "hyde": 0.7,
    "prf": 0.5,
}


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def _append_unique(
    out: list[QueryCandidate],
    seen: set[str],
    *,
    text: str,
    kind: str,
    weight: float,
) -> None:
    cleaned = text.strip()
    if not cleaned:
        return
    key = _normalize(cleaned)
    if key in seen:
        return
    seen.add(key)
    out.append(QueryCandidate(text=cleaned, kind=kind, weight=weight))


def build_query_candidates(
    prompt: str,
    *,
    topic_hints: Iterable[str] | None = None,
    rewrites: Iterable[str] | None = None,
    follow_up_context: Iterable[str] | None = None,
    prf_terms: Iterable[str] | None = None,
    max_candidates: int = 4,
) -> list[QueryCandidate]:
    """Build a bounded query list for weighted RRF retrieval."""
    out: list[QueryCandidate] = []
    seen: set[str] = set()

    hints = [hint.strip() for hint in (topic_hints or []) if hint and hint.strip()]
    original_text = prompt.strip()
    if hints:
        original_text = f"{original_text}\n\n" + "\n".join(hints)
    _append_unique(
        out,
        seen,
        text=original_text,
        kind="original",
        weight=QUERY_WEIGHTS["original"],
    )

    context = [item.strip() for item in (follow_up_context or []) if item and item.strip()]
    if context:
        _append_unique(
            out,
            seen,
            text="Previous context: " + " / ".join(context) + f"\nCurrent question: {prompt}",
            kind="follow_up",
            weight=QUERY_WEIGHTS["follow_up"],
        )

    for rewrite in rewrites or []:
        _append_unique(
            out,
            seen,
            text=str(rewrite),
            kind="rewrite",
            weight=QUERY_WEIGHTS["rewrite"],
        )
        if len(out) >= max_candidates:
            return out[:max_candidates]

    prf_text = " ".join(str(term).strip() for term in (prf_terms or []) if str(term).strip())
    if prf_text:
        _append_unique(
            out,
            seen,
            text=f"{prompt}\n\n{prf_text}",
            kind="prf",
            weight=QUERY_WEIGHTS["prf"],
        )

    return out[:max_candidates]


def weighted_rrf_merge(
    rankings: Iterable[tuple[Iterable[tuple[int, float]], float]],
    *,
    k: int = RRF_K,
) -> list[tuple[int, float]]:
    """Merge rankings with weighted reciprocal rank fusion.

    Input scores are intentionally ignored, matching the existing RRF semantics
    in ``searcher._rrf_merge``. The second tuple value is the source weight.
    """
    fused: dict[int, float] = {}
    for ranking, weight in rankings:
        if weight <= 0:
            continue
        for rank, (row_id, _) in enumerate(ranking, start=1):
            fused[row_id] = fused.get(row_id, 0.0) + weight / (k + rank)
    return sorted(fused.items(), key=lambda item: (-item[1], item[0]))
