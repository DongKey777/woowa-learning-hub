from __future__ import annotations

import sys
import types

import pytest

from scripts.learning.rag.r3.index.qdrant_store import (
    QdrantStoreConfig,
    build_qdrant_points,
    create_qdrant_client,
    probe_qdrant_modes,
    rebuild_qdrant_collection,
)
from scripts.learning.rag.r3.candidate import R3Document


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


def test_build_qdrant_points_materializes_dense_sparse_payload():
    points, vocab = build_qdrant_points(
        [
            R3Document(
                path="contents/network/latency.md",
                chunk_id="latency#0",
                title="Latency",
                section_title="Primer",
                aliases=("지연 시간",),
                dense_vector=(0.1, 0.2),
                sparse_terms={"latency": 2.0, "tail": 0.5},
                signals=("network",),
                metadata={"level": "beginner"},
            )
        ]
    )

    assert vocab.to_dict() == {"terms": ["latency", "tail"]}
    assert points[0].point_id == "contents/network/latency.md#latency#0"
    assert points[0].vector["dense"] == [0.1, 0.2]
    assert points[0].vector["sparse"] == {
        "indices": [0, 1],
        "values": [2.0, 0.5],
    }
    assert points[0].payload["path"] == "contents/network/latency.md"
    assert points[0].payload["aliases"] == ["지연 시간"]


def test_rebuild_qdrant_collection_recreates_dense_sparse_collection(monkeypatch):
    calls = []

    class FakeDistance:
        COSINE = "Cosine"

    class FakeVectorParams:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeSparseVectorParams:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakePointStruct:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeClient:
        def recreate_collection(self, **kwargs):
            calls.append(("recreate", kwargs))

        def upsert(self, **kwargs):
            calls.append(("upsert", kwargs))

    fake_models = types.SimpleNamespace(
        Distance=FakeDistance,
        VectorParams=FakeVectorParams,
        SparseVectorParams=FakeSparseVectorParams,
        PointStruct=FakePointStruct,
    )
    fake_module = types.ModuleType("qdrant_client")
    fake_module.models = fake_models
    monkeypatch.setitem(sys.modules, "qdrant_client", fake_module)

    result = rebuild_qdrant_collection(
        FakeClient(),
        QdrantStoreConfig(mode="memory", vector_size=2),
        [
            R3Document(
                path="contents/network/latency.md",
                dense_vector=(0.1, 0.2),
                sparse_terms={"latency": 1.0},
            )
        ],
        batch_size=1,
    )

    assert result["point_count"] == 1
    assert result["sparse_vocab_size"] == 1
    assert calls[0][0] == "recreate"
    assert calls[0][1]["vectors_config"]["dense"].kwargs == {
        "size": 2,
        "distance": "Cosine",
    }
    assert "sparse" in calls[0][1]["sparse_vectors_config"]
    assert calls[1][0] == "upsert"
    assert calls[1][1]["points"][0].kwargs["vector"]["sparse"] == {
        "indices": [0],
        "values": [1.0],
    }
