from __future__ import annotations

import pytest

from scripts.learning import integration
from scripts.learning.rag import indexer


def _ready() -> indexer.ReadinessReport:
    return indexer.ReadinessReport(
        state="ready",
        reason="ready",
        corpus_hash="hash",
        index_manifest_hash="hash",
        next_command=None,
    )


def _fake_hit():
    return {
        "path": "contents/network/latency-bandwidth-throughput-basics.md",
        "title": "Latency",
        "category": "network",
        "section_title": "Primer",
        "section_path": ["Latency", "Primer"],
        "score": 1.0,
        "snippet_preview": "latency",
        "anchors": [],
    }


def test_augment_can_force_r3_backend(monkeypatch, tmp_path):
    captured = {}

    def fake_search(prompt, **kwargs):
        captured["prompt"] = prompt
        captured["kwargs"] = kwargs
        kwargs["debug"]["backend"] = kwargs["backend"]
        return [_fake_hit()]

    monkeypatch.setattr("scripts.learning.rag.searcher.search", fake_search)

    result = integration.augment(
        prompt="latency가 뭐야?",
        cs_search_mode="cheap",
        index_root=tmp_path,
        readiness=_ready(),
        backend="r3",
    )

    assert captured["kwargs"]["backend"] == "r3"
    assert result["meta"]["backend"] == "r3"
    assert result["sidecar"]["backend"] == "r3"


def test_augment_can_force_r3_backend_from_env(monkeypatch, tmp_path):
    captured = {}

    def fake_search(prompt, **kwargs):
        del prompt
        captured["backend"] = kwargs["backend"]
        return [_fake_hit()]

    monkeypatch.setenv("WOOWA_RAG_RUNTIME_BACKEND", "r3")
    monkeypatch.setattr("scripts.learning.rag.searcher.search", fake_search)

    result = integration.augment(
        prompt="latency가 뭐야?",
        cs_search_mode="cheap",
        index_root=tmp_path,
        readiness=_ready(),
    )

    assert captured["backend"] == "r3"
    assert result["meta"]["backend"] == "r3"


def test_augment_surfaces_r3_runtime_debug(monkeypatch, tmp_path):
    def fake_search(prompt, **kwargs):
        del prompt
        kwargs["debug"].update(
            {
                "backend": "r3",
                "mode": "full",
                "r3_reranker_enabled": True,
                "r3_reranker_model": "BAAI/bge-reranker-v2-m3",
                "rerank_input_window": 20,
                "r3_sparse_source": "bge_m3_sparse_vec_sidecar",
                "r3_sparse_sidecar_document_count": 27170,
                "r3_sparse_query_terms_count": 11,
                "r3_dense_candidate_count": 100,
            }
        )
        return [_fake_hit()]

    monkeypatch.setattr("scripts.learning.rag.searcher.search", fake_search)

    result = integration.augment(
        prompt="RAG로 깊게 latency가 뭐야?",
        cs_search_mode="full",
        index_root=tmp_path,
        readiness=_ready(),
        backend="r3",
    )

    runtime_debug = result["meta"]["runtime_debug"]
    assert runtime_debug["backend"] == "r3"
    assert runtime_debug["r3_reranker_enabled"] is True
    assert runtime_debug["r3_reranker_model"] == "BAAI/bge-reranker-v2-m3"
    assert runtime_debug["rerank_input_window"] == 20
    assert runtime_debug["r3_sparse_source"] == "bge_m3_sparse_vec_sidecar"


def test_resolve_search_backend_rejects_unknown_backend(tmp_path):
    with pytest.raises(ValueError, match="unknown RAG runtime backend"):
        integration.resolve_search_backend(tmp_path, override="vespa")
