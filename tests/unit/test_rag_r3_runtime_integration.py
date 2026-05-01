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


def test_resolve_search_backend_rejects_unknown_backend(tmp_path):
    with pytest.raises(ValueError, match="unknown RAG runtime backend"):
        integration.resolve_search_backend(tmp_path, override="vespa")
