"""True sparse retriever prototype backed by an in-memory inverted index."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

from ..candidate import Candidate, R3Document
from ..query_plan import QueryPlan


class SparseRetriever:
    """Sparse first-stage candidate generator independent of lexical/dense."""

    def __init__(self, documents: Iterable[R3Document], *, limit: int = 100) -> None:
        self.documents = tuple(documents)
        self.limit = limit
        self._by_key = {(doc.path, doc.chunk_id): doc for doc in self.documents}
        self._postings: dict[str, list[tuple[tuple[str, str | None], float]]] = defaultdict(list)
        for doc in self.documents:
            for term, weight in doc.sparse_terms.items():
                if weight <= 0:
                    continue
                self._postings[term.casefold()].append(((doc.path, doc.chunk_id), float(weight)))

    def retrieve(
        self,
        query_plan: QueryPlan,
        *,
        query_terms: Mapping[str, float] | None = None,
    ) -> list[Candidate]:
        weighted_terms = (
            {term.casefold(): float(weight) for term, weight in query_terms.items()}
            if query_terms is not None
            else {term: 1.0 for term in query_plan.lexical_terms}
        )
        scores: dict[tuple[str, str | None], float] = {}
        matched: dict[tuple[str, str | None], set[str]] = defaultdict(set)
        for term, query_weight in weighted_terms.items():
            if query_weight <= 0:
                continue
            for doc_key, doc_weight in self._postings.get(term, []):
                scores[doc_key] = scores.get(doc_key, 0.0) + query_weight * doc_weight
                matched[doc_key].add(term)
        ranked = sorted(
            scores.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1] or ""),
        )
        candidates: list[Candidate] = []
        for rank, (doc_key, score) in enumerate(ranked[: self.limit], start=1):
            doc = self._by_key[doc_key]
            candidates.append(
                Candidate(
                    path=doc.path,
                    chunk_id=doc.chunk_id,
                    retriever="sparse",
                    rank=rank,
                    score=float(score),
                    title=doc.title,
                    section_title=doc.section_title,
                    metadata={"matched_terms": sorted(matched[doc_key])},
                )
            )
        return candidates
