"""Qdrant backend probe and adapter skeleton for R3."""

from __future__ import annotations

import importlib.util
import time
from dataclasses import asdict, dataclass
from functools import cached_property
from pathlib import Path
from typing import Literal

from ..candidate import R3Document


QdrantMode = Literal["memory", "local", "server"]
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


@dataclass(frozen=True)
class QdrantStoreConfig:
    mode: QdrantMode
    collection_name: str = "cs_rag_r3"
    vector_size: int = 1024
    path: Path | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        if self.mode == "local" and self.path is None:
            raise ValueError("Qdrant local mode requires path")
        if self.mode == "server" and not self.url:
            raise ValueError("Qdrant server mode requires url")
        if self.vector_size <= 0:
            raise ValueError("vector_size must be positive")

    def to_dict(self) -> dict:
        blob = asdict(self)
        if self.path is not None:
            blob["path"] = str(self.path)
        return blob


@dataclass(frozen=True)
class QdrantSparseVocab:
    """Deterministic term-id mapping for Qdrant sparse vectors."""

    terms: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(set(self.terms)) != len(self.terms):
            raise ValueError("sparse vocab terms must be unique")

    @cached_property
    def term_to_index(self) -> dict[str, int]:
        return {term: index for index, term in enumerate(self.terms)}

    @classmethod
    def from_documents(cls, documents: list[R3Document] | tuple[R3Document, ...]):
        terms = sorted(
            {
                term.casefold()
                for document in documents
                for term, weight in document.sparse_terms.items()
                if weight > 0
            }
        )
        return cls(terms=tuple(terms))

    def index(self, term: str) -> int:
        try:
            return self.term_to_index[term.casefold()]
        except KeyError as exc:
            raise KeyError(term) from exc

    def to_dict(self) -> dict:
        return {"terms": list(self.terms)}


@dataclass(frozen=True)
class QdrantSparseVector:
    indices: tuple[int, ...]
    values: tuple[float, ...]

    def to_dict(self) -> dict:
        return {"indices": list(self.indices), "values": list(self.values)}


@dataclass(frozen=True)
class QdrantPoint:
    point_id: str
    vector: dict
    payload: dict

    def to_dict(self) -> dict:
        return {
            "id": self.point_id,
            "vector": self.vector,
            "payload": self.payload,
        }


def qdrant_dependency_available() -> bool:
    return importlib.util.find_spec("qdrant_client") is not None


def create_qdrant_client(config: QdrantStoreConfig):
    """Create a Qdrant client for one explicit runtime mode."""

    from qdrant_client import QdrantClient  # type: ignore

    if config.mode == "memory":
        return QdrantClient(":memory:")
    if config.mode == "local":
        return QdrantClient(path=str(config.path))
    return QdrantClient(url=config.url)


def build_sparse_vocab(documents: list[R3Document] | tuple[R3Document, ...]) -> QdrantSparseVocab:
    return QdrantSparseVocab.from_documents(documents)


def _point_id(document: R3Document) -> str:
    if document.chunk_id:
        return f"{document.path}#{document.chunk_id}"
    return document.path


def _sparse_vector(document: R3Document, vocab: QdrantSparseVocab) -> QdrantSparseVector | None:
    pairs = []
    for term, weight in document.sparse_terms.items():
        if weight <= 0:
            continue
        pairs.append((vocab.index(term), float(weight)))
    if not pairs:
        return None
    pairs.sort(key=lambda item: item[0])
    return QdrantSparseVector(
        indices=tuple(index for index, _ in pairs),
        values=tuple(weight for _, weight in pairs),
    )


def document_to_qdrant_point(
    document: R3Document,
    *,
    sparse_vocab: QdrantSparseVocab,
    dense_vector_name: str = DENSE_VECTOR_NAME,
    sparse_vector_name: str = SPARSE_VECTOR_NAME,
) -> QdrantPoint:
    """Materialize one R3 document/chunk as a Qdrant dense+sparse point."""

    vector: dict = {}
    if document.dense_vector is not None:
        vector[dense_vector_name] = list(document.dense_vector)
    sparse = _sparse_vector(document, sparse_vocab)
    if sparse is not None:
        vector[sparse_vector_name] = sparse.to_dict()
    payload = {
        "path": document.path,
        "chunk_id": document.chunk_id,
        "title": document.title,
        "section_title": document.section_title,
        "aliases": list(document.aliases),
        "signals": list(document.signals),
        "metadata": dict(document.metadata),
    }
    return QdrantPoint(point_id=_point_id(document), vector=vector, payload=payload)


def build_qdrant_points(
    documents: list[R3Document] | tuple[R3Document, ...],
    *,
    sparse_vocab: QdrantSparseVocab | None = None,
) -> tuple[list[QdrantPoint], QdrantSparseVocab]:
    vocab = sparse_vocab or build_sparse_vocab(documents)
    points = [
        document_to_qdrant_point(document, sparse_vocab=vocab)
        for document in documents
        if document.dense_vector is not None or document.sparse_terms
    ]
    return points, vocab


def recreate_qdrant_collection(
    client,
    config: QdrantStoreConfig,
    *,
    dense_vector_name: str = DENSE_VECTOR_NAME,
    sparse_vector_name: str = SPARSE_VECTOR_NAME,
) -> None:
    """Create a dense+sparse Qdrant collection with named vectors."""

    from qdrant_client import models  # type: ignore

    client.recreate_collection(
        collection_name=config.collection_name,
        vectors_config={
            dense_vector_name: models.VectorParams(
                size=config.vector_size,
                distance=models.Distance.COSINE,
            )
        },
        sparse_vectors_config={sparse_vector_name: models.SparseVectorParams()},
    )


def _to_point_struct(point: QdrantPoint):
    from qdrant_client import models  # type: ignore

    return models.PointStruct(
        id=point.point_id,
        vector=point.vector,
        payload=point.payload,
    )


def upsert_qdrant_points(
    client,
    config: QdrantStoreConfig,
    points: list[QdrantPoint],
    *,
    batch_size: int = 128,
) -> int:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    written = 0
    for start in range(0, len(points), batch_size):
        batch = points[start : start + batch_size]
        client.upsert(
            collection_name=config.collection_name,
            points=[_to_point_struct(point) for point in batch],
        )
        written += len(batch)
    return written


def rebuild_qdrant_collection(
    client,
    config: QdrantStoreConfig,
    documents: list[R3Document] | tuple[R3Document, ...],
    *,
    batch_size: int = 128,
) -> dict:
    """Recreate and populate the R3 Qdrant dense+sparse collection."""

    start = time.perf_counter()
    points, vocab = build_qdrant_points(documents)
    recreate_qdrant_collection(client, config)
    written = upsert_qdrant_points(client, config, points, batch_size=batch_size)
    return {
        "collection_name": config.collection_name,
        "point_count": written,
        "sparse_vocab_size": len(vocab.terms),
        "sparse_vocab": vocab.to_dict(),
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
    }


def probe_qdrant_modes(configs: list[QdrantStoreConfig]) -> list[dict]:
    """Probe dependency/client creation for candidate local runtime modes."""

    available = qdrant_dependency_available()
    results: list[dict] = []
    for config in configs:
        item = {
            "mode": config.mode,
            "config": config.to_dict(),
            "dependency_available": available,
            "client_created": False,
            "error": None,
        }
        if available:
            try:
                create_qdrant_client(config)
                item["client_created"] = True
            except Exception as exc:  # pragma: no cover - depends on local qdrant
                item["error"] = str(exc)
        results.append(item)
    return results
