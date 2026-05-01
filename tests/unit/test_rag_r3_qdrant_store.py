from __future__ import annotations

import sys
import types

import pytest

from scripts.learning.rag.r3.index.qdrant_store import (
    QdrantStoreConfig,
    create_qdrant_client,
    probe_qdrant_modes,
)


def test_qdrant_config_validates_runtime_mode_requirements(tmp_path):
    QdrantStoreConfig(mode="memory")
    QdrantStoreConfig(mode="local", path=tmp_path / "qdrant")
    QdrantStoreConfig(mode="server", url="http://localhost:6333")

    with pytest.raises(ValueError, match="local mode requires path"):
        QdrantStoreConfig(mode="local")
    with pytest.raises(ValueError, match="server mode requires url"):
        QdrantStoreConfig(mode="server")


def test_create_qdrant_client_uses_explicit_mode(monkeypatch, tmp_path):
    calls = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

    fake_module = types.ModuleType("qdrant_client")
    fake_module.QdrantClient = FakeClient
    monkeypatch.setitem(sys.modules, "qdrant_client", fake_module)

    create_qdrant_client(QdrantStoreConfig(mode="memory"))
    create_qdrant_client(QdrantStoreConfig(mode="local", path=tmp_path / "qdrant"))
    create_qdrant_client(QdrantStoreConfig(mode="server", url="http://localhost:6333"))

    assert calls[0] == ((":memory:",), {})
    assert calls[1] == ((), {"path": str(tmp_path / "qdrant")})
    assert calls[2] == ((), {"url": "http://localhost:6333"})


def test_probe_qdrant_modes_reports_missing_dependency(monkeypatch):
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.qdrant_store.qdrant_dependency_available",
        lambda: False,
    )

    results = probe_qdrant_modes([QdrantStoreConfig(mode="memory")])

    assert results[0]["mode"] == "memory"
    assert results[0]["dependency_available"] is False
    assert results[0]["client_created"] is False
