"""Lexical retriever wrapper around the field-aware sidecar."""

from __future__ import annotations

from ..candidate import Candidate
from ..index.lexical_store import LexicalStore
from ..query_plan import QueryPlan


class LexicalRetriever:
    def __init__(self, store: LexicalStore, *, limit_per_field: int = 20) -> None:
        self.store = store
        self.limit_per_field = limit_per_field

    def retrieve(self, query_plan: QueryPlan) -> list[Candidate]:
        return self.store.search(query_plan, limit_per_field=self.limit_per_field)
