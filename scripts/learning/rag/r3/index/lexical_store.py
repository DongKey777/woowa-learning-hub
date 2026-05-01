"""Field-aware lexical sidecar prototype for R3."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from ..candidate import Candidate, R3Document
from ..query_plan import QueryPlan
from ..tokenization import tokenize_text


FIELD_WEIGHTS = {
    "title": 3.0,
    "section": 2.0,
    "aliases": 2.5,
    "body": 1.0,
}


def tokenize(text: str) -> tuple[str, ...]:
    return tokenize_text(text)


@dataclass(frozen=True)
class LexicalFieldHit:
    document: R3Document
    field: str
    score: float
    matched_terms: tuple[str, ...]


class LexicalStore:
    """Small in-memory field index used before backend lock-in."""

    def __init__(self, documents: Iterable[R3Document]) -> None:
        self._documents = tuple(documents)
        self._field_terms: dict[tuple[str, str | None, str], Counter[str]] = {}
        for doc in self._documents:
            self._field_terms[(doc.path, doc.chunk_id, "title")] = Counter(tokenize(doc.title))
            self._field_terms[(doc.path, doc.chunk_id, "section")] = Counter(
                tokenize(doc.section_title)
            )
            self._field_terms[(doc.path, doc.chunk_id, "aliases")] = Counter(
                term
                for alias in doc.aliases
                for term in tokenize(alias)
            )
            self._field_terms[(doc.path, doc.chunk_id, "body")] = Counter(tokenize(doc.body))

    @classmethod
    def from_documents(cls, documents: Iterable[R3Document]) -> "LexicalStore":
        return cls(documents)

    def search_field(
        self,
        query_plan: QueryPlan,
        *,
        field: str,
        limit: int = 20,
    ) -> list[Candidate]:
        if field not in FIELD_WEIGHTS:
            raise ValueError(f"unknown lexical field: {field}")
        query_terms = set(query_plan.lexical_terms)
        if not query_terms:
            return []

        hits: list[LexicalFieldHit] = []
        for doc in self._documents:
            counts = self._field_terms[(doc.path, doc.chunk_id, field)]
            matched = tuple(sorted(query_terms & set(counts)))
            if not matched:
                continue
            score = sum(counts[term] for term in matched) * FIELD_WEIGHTS[field]
            hits.append(
                LexicalFieldHit(
                    document=doc,
                    field=field,
                    score=float(score),
                    matched_terms=matched,
                )
            )
        hits.sort(key=lambda hit: (-hit.score, hit.document.path, hit.document.chunk_id or ""))
        return [
            Candidate(
                path=hit.document.path,
                chunk_id=hit.document.chunk_id,
                retriever=f"lexical:{field}",
                rank=rank,
                score=hit.score,
                title=hit.document.title,
                section_title=hit.document.section_title,
                metadata={
                    "field": field,
                    "matched_terms": list(hit.matched_terms),
                    "document": dict(hit.document.metadata),
                },
            )
            for rank, hit in enumerate(hits[:limit], start=1)
        ]

    def search(self, query_plan: QueryPlan, *, limit_per_field: int = 20) -> list[Candidate]:
        candidates: list[Candidate] = []
        for field in ("title", "section", "aliases", "body"):
            candidates.extend(
                self.search_field(query_plan, field=field, limit=limit_per_field)
            )
        return candidates
