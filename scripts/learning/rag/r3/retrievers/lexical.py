"""Lexical retriever wrapper around the field-aware sidecar."""

from __future__ import annotations

from typing import Sequence

from ..candidate import Candidate
from ..index.lexical_store import LEXICAL_FIELDS, LexicalStore
from ..query_plan import QueryPlan


class LexicalRetriever:
    def __init__(
        self,
        store: LexicalStore,
        *,
        limit_per_field: int = 20,
        fields: Sequence[str] = LEXICAL_FIELDS,
        retriever_namespace: str = "lexical",
    ) -> None:
        self.store = store
        self.limit_per_field = limit_per_field
        self.fields = tuple(fields)
        self.retriever_namespace = retriever_namespace

    def retrieve(self, query_plan: QueryPlan) -> list[Candidate]:
        hits = self.store.search(
            query_plan,
            limit_per_field=self.limit_per_field,
            fields=self.fields,
        )
        if self.retriever_namespace == "lexical":
            return hits
        out: list[Candidate] = []
        for hit in hits:
            field = str(hit.metadata.get("field") or hit.retriever.split(":")[-1])
            out.append(
                Candidate(
                    path=hit.path,
                    chunk_id=hit.chunk_id,
                    retriever=f"{self.retriever_namespace}:{field}",
                    rank=hit.rank,
                    score=hit.score,
                    title=hit.title,
                    section_title=hit.section_title,
                    metadata=dict(hit.metadata),
                )
            )
        return out
