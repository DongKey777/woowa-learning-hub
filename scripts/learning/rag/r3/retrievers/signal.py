"""Signal/canonical candidate generator."""

from __future__ import annotations

from typing import Iterable

from ..candidate import Candidate, R3Document


class SignalRetriever:
    def __init__(self, documents: Iterable[R3Document], *, limit: int = 20) -> None:
        self.documents = tuple(documents)
        self.limit = limit

    def retrieve(self, route_tags: Iterable[str]) -> list[Candidate]:
        requested = {tag for tag in route_tags if tag}
        if not requested:
            return []
        hits: list[tuple[R3Document, int]] = []
        for doc in self.documents:
            matched = requested & set(doc.signals)
            if not matched:
                continue
            hits.append((doc, len(matched)))
        hits.sort(key=lambda item: (-item[1], item[0].path, item[0].chunk_id or ""))
        return [
            Candidate(
                path=doc.path,
                chunk_id=doc.chunk_id,
                retriever="signal",
                rank=rank,
                score=float(score),
                title=doc.title,
                section_title=doc.section_title,
                metadata={"matched_signals": sorted(requested & set(doc.signals))},
            )
            for rank, (doc, score) in enumerate(hits[: self.limit], start=1)
        ]
