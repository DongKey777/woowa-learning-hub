"""Source_priority post-fusion weighting.

Cycle 1 cohort_eval analysis (2026-05-06) showed that the fused
ranking — Reciprocal Rank Fusion of FTS / dense / sparse / catalog
retrievers — ignores the v3 contract's ``source_priority`` gradient
entirely. RRF aggregates rank position only, so a fleet-new chooser
with multiple-channel matches (BM25 alias + dense
contextual_chunk_prefix + catalog mission_ids) outranks the
canonical primer of the same area despite the contract awarding the
primer a higher source_priority (90 vs 86).

This module restores the contract's design intent by multiplying the
fused score by ``source_priority / 100`` before rerank consumption.
The multiplication is small (e.g. primer 92 vs chooser 86 = 1.07x)
but decisive on borderline ranking ties — exactly the queries where
we observe regression in cycle 1.

Symmetrical to ``personalization.py:apply_score_adjustments`` — same
Candidate-list-in / Candidate-list-out shape, same metadata trace
fields.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from .candidate import Candidate


DEFAULT_SOURCE_PRIORITY = 80
"""Fallback for paths absent from the catalog. Matches the v3
DEFAULT_SOURCE_PRIORITY in ``migrate_frontmatter_v3.py`` for
``deep_dive``/``unknown`` roles — neutral baseline that does not
artificially demote unmigrated docs."""


def load_path_to_source_priority(catalog_dir: Path | None) -> dict[str, int]:
    """Build ``contents/<category>/<slug>.md → source_priority`` from
    ``concepts.v3.json``.

    Catalog stores ``doc_path`` without the ``contents/`` prefix; we
    normalize to the prefixed form so candidate.path matches.

    Returns an empty dict when the catalog is missing or unreadable
    (the caller treats every candidate as ``DEFAULT_SOURCE_PRIORITY``).
    """
    if catalog_dir is None:
        return {}
    catalog_path = catalog_dir / "concepts.v3.json"
    if not catalog_path.exists():
        return {}
    try:
        blob = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, int] = {}
    for entry in blob.get("concepts", {}).values():
        doc_path = entry.get("doc_path")
        priority = entry.get("source_priority")
        if not doc_path or priority is None:
            continue
        try:
            priority_int = int(priority)
        except (TypeError, ValueError):
            continue
        full_path = (
            doc_path if doc_path.startswith("contents/") else f"contents/{doc_path}"
        )
        out[full_path] = priority_int
    return out


def apply_source_priority_weighting(
    candidates: Sequence[Candidate],
    *,
    path_to_priority: dict[str, int],
    default_priority: int = DEFAULT_SOURCE_PRIORITY,
) -> list[Candidate]:
    """Multiply each candidate's fused score by its
    ``source_priority / 100``.

    The candidate's identity (path, chunk_id, retriever, rank, title)
    is preserved; only ``score`` and two trace metadata fields
    (``source_priority_weight``, ``pre_priority_score``) change.

    No-op when ``path_to_priority`` is empty (catalog missing) — the
    rebuilt list is a copy with weights of 1.0 recorded for trace
    completeness, but the order is unchanged.
    """
    rebuilt: list[Candidate] = []
    for cand in candidates:
        priority = path_to_priority.get(cand.path, default_priority)
        weight = priority / 100.0
        new_score = float(cand.score) * weight
        rebuilt.append(
            Candidate(
                path=cand.path,
                retriever=cand.retriever,
                rank=cand.rank,
                score=new_score,
                chunk_id=cand.chunk_id,
                title=cand.title,
                section_title=cand.section_title,
                metadata={
                    **cand.metadata,
                    "source_priority_weight": weight,
                    "pre_priority_score": float(cand.score),
                    "source_priority": priority,
                },
            )
        )
    rebuilt.sort(key=lambda c: (-c.score, c.path))
    return rebuilt
