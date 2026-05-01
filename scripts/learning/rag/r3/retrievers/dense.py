"""Dense candidate generator prototype."""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from ..candidate import Candidate, R3Document


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


class DenseRetriever:
    def __init__(self, documents: Iterable[R3Document], *, limit: int = 100) -> None:
        self.documents = tuple(documents)
        self.limit = limit

    def retrieve(self, query_vector: Sequence[float]) -> list[Candidate]:
        hits: list[tuple[R3Document, float]] = []
        for doc in self.documents:
            if doc.dense_vector is None:
                continue
            score = _cosine(query_vector, doc.dense_vector)
            if score <= 0.0:
                continue
            hits.append((doc, score))
        hits.sort(key=lambda item: (-item[1], item[0].path, item[0].chunk_id or ""))
        return [
            Candidate(
                path=doc.path,
                chunk_id=doc.chunk_id,
                retriever="dense",
                rank=rank,
                score=float(score),
                title=doc.title,
                section_title=doc.section_title,
            )
            for rank, (doc, score) in enumerate(hits[: self.limit], start=1)
        ]
