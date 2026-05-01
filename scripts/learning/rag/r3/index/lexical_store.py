"""Field-aware lexical sidecar prototype for R3."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from ..candidate import Candidate, R3Document
from ..query_plan import QueryPlan
from ..tokenization import tokenize_text


FIELD_WEIGHTS = {
    "title": 3.0,
    "section": 2.0,
    "aliases": 2.5,
    "body": 1.0,
}
LEXICAL_FIELDS = tuple(FIELD_WEIGHTS)


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

    def __init__(
        self,
        documents: Iterable[R3Document],
        *,
        field_terms: Mapping[tuple[str, str | None, str], Counter[str]] | None = None,
    ) -> None:
        self._documents = tuple(documents)
        self._field_terms: dict[tuple[str, str | None, str], Counter[str]] = {}
        if field_terms is not None:
            self._field_terms = {
                key: Counter(value)
                for key, value in field_terms.items()
            }
        for doc in self._documents:
            for field, terms in self._terms_for_document(doc).items():
                self._field_terms.setdefault((doc.path, doc.chunk_id, field), Counter(terms))

    @classmethod
    def from_documents(cls, documents: Iterable[R3Document]) -> "LexicalStore":
        return cls(documents)

    @classmethod
    def from_precomputed(
        cls,
        documents: Iterable[R3Document],
        field_terms: Mapping[tuple[str, str | None, str], Iterable[str] | Mapping[str, int]],
    ) -> "LexicalStore":
        counters = {
            key: Counter(value)
            for key, value in field_terms.items()
        }
        return cls(documents, field_terms=counters)

    @property
    def documents(self) -> tuple[R3Document, ...]:
        return self._documents

    @staticmethod
    def _terms_for_document(document: R3Document) -> dict[str, tuple[str, ...]]:
        return {
            "title": tokenize(document.title),
            "section": tokenize(document.section_title),
            "aliases": tuple(
                term
                for alias in document.aliases
                for term in tokenize(alias)
            ),
            "body": tokenize(document.body),
        }

    def field_terms_for(self, document: R3Document) -> dict[str, tuple[str, ...]]:
        terms: dict[str, tuple[str, ...]] = {}
        for field in LEXICAL_FIELDS:
            counter = self._field_terms.get((document.path, document.chunk_id, field), Counter())
            terms[field] = tuple(counter)
        return terms

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

    def search(
        self,
        query_plan: QueryPlan,
        *,
        limit_per_field: int = 20,
        fields: Sequence[str] = LEXICAL_FIELDS,
    ) -> list[Candidate]:
        candidates: list[Candidate] = []
        for field in fields:
            candidates.extend(
                self.search_field(query_plan, field=field, limit=limit_per_field)
            )
        return candidates
