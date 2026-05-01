"""Qdrant backend probe and adapter skeleton for R3."""

from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


QdrantMode = Literal["memory", "local", "server"]


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
