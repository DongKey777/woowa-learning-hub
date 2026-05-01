"""Candidate records with explicit retriever provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class R3Document:
    """Minimal document/chunk shape consumed by R3 retriever prototypes."""

    path: str
    chunk_id: str | None = None
    title: str = ""
    section_title: str = ""
    body: str = ""
    aliases: tuple[str, ...] = ()
    dense_vector: tuple[float, ...] | None = None
    sparse_terms: dict[str, float] = field(default_factory=dict)
    signals: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("document path is required")


@dataclass(frozen=True)
class Candidate:
    """One document/chunk candidate emitted by an independent retriever."""

    path: str
    retriever: str
    rank: int
    score: float
    chunk_id: str | None = None
    title: str | None = None
    section_title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("candidate path is required")
        if not self.retriever:
            raise ValueError("candidate retriever is required")
        if self.rank < 1:
            raise ValueError("candidate rank must be >= 1")

    @property
    def candidate_id(self) -> str:
        return f"{self.path}#{self.chunk_id or 'doc'}"

    def to_dict(self) -> dict[str, Any]:
        blob = asdict(self)
        blob["candidate_id"] = self.candidate_id
        return blob

    @classmethod
    def from_dict(cls, blob: dict[str, Any]) -> "Candidate":
        return cls(
            path=str(blob["path"]),
            retriever=str(blob["retriever"]),
            rank=int(blob["rank"]),
            score=float(blob["score"]),
            chunk_id=blob.get("chunk_id"),
            title=blob.get("title"),
            section_title=blob.get("section_title"),
            metadata=dict(blob.get("metadata") or {}),
        )
