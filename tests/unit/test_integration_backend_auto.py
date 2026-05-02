from __future__ import annotations

import json
from pathlib import Path

from scripts.learning import integration
from scripts.learning.rag import indexer, searcher


class ReadyReport:
    state = "ready"
    reason = "ready"
    corpus_hash = "fixture"
    index_manifest_hash = "fixture"
    next_command = None


def _write_manifest(index_root: Path, version: int) -> None:
    index_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "index_version": version,
        "row_count": 1,
        "corpus_hash": "fixture",
        "corpus_root": "fixture",
    }
    if version >= indexer.LANCE_INDEX_VERSION:
        payload.update(
            {
                "encoder": {"model_id": "BAAI/bge-m3"},
                "lancedb": {"table_name": indexer.LANCE_TABLE_NAME},
                "modalities": ["fts", "dense", "sparse"],
            }
        )
    (index_root / indexer.MANIFEST_NAME).write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def _write_r3_sidecar(
    index_root: Path,
    *,
    corpus_hash: str = "fixture",
    row_count: int = 1,
    document_count: int = 1,
) -> None:
    (index_root / "r3_lexical_sidecar.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_kind": "r3_lexical_sidecar",
                "corpus_hash": corpus_hash,
                "row_count": row_count,
                "document_count": document_count,
                "fields": ["title", "section", "aliases", "body"],
            }
        ),
        encoding="utf-8",
    )


def _hit() -> dict:
    return {
        "path": "contents/database/transaction-isolation-basics.md",
        "title": "Transaction Isolation Basics",
        "category": "database",
        "section_title": "핵심 개념",
        "section_path": ["Transaction Isolation Basics", "핵심 개념"],
        "score": 1.0,
        "snippet_preview": "트랜잭션 격리수준",
    }


def test_augment_uses_legacy_backend_for_v2_manifest(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root, indexer.INDEX_VERSION)
    calls = []

    def fake_search(prompt, **kwargs):
        calls.append(kwargs)
        return [_hit()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="트랜잭션 격리수준이 뭐야?",
        learning_points=None,
        cs_search_mode="cheap",
        index_root=index_root,
        readiness=ReadyReport(),
    )

    assert result["meta"]["backend"] == "legacy"
    assert calls
    assert calls[0]["backend"] == "legacy"


def test_augment_uses_lance_backend_for_v3_manifest(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root, indexer.LANCE_INDEX_VERSION)
    calls = []

    def fake_search(prompt, **kwargs):
        calls.append(kwargs)
        return [_hit()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="트랜잭션 격리수준이 뭐야?",
        learning_points=None,
        cs_search_mode="cheap",
        index_root=index_root,
        readiness=ReadyReport(),
        learner_context={"experience_level": "beginner"},
    )

    assert result["meta"]["backend"] == "lance"
    assert result["sidecar"]["backend"] == "lance"
    assert calls
    assert calls[0]["backend"] == "lance"
    assert calls[0]["learner_context"] == {"experience_level": "beginner"}


def test_augment_promotes_v3_manifest_to_r3_when_sidecar_matches(
    tmp_path,
    monkeypatch,
):
    index_root = tmp_path / "index"
    _write_manifest(index_root, indexer.LANCE_INDEX_VERSION)
    _write_r3_sidecar(index_root)
    calls = []

    def fake_search(prompt, **kwargs):
        calls.append(kwargs)
        return [_hit()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="latency가 뭐야?",
        learning_points=None,
        cs_search_mode="cheap",
        index_root=index_root,
        readiness=ReadyReport(),
    )

    assert result["meta"]["backend"] == "r3"
    assert result["sidecar"]["backend"] == "r3"
    assert calls
    assert calls[0]["backend"] == "r3"


def test_augment_keeps_lance_when_r3_sidecar_is_stale(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root, indexer.LANCE_INDEX_VERSION)
    _write_r3_sidecar(index_root, corpus_hash="old-fixture")
    calls = []

    def fake_search(prompt, **kwargs):
        calls.append(kwargs)
        return [_hit()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="latency가 뭐야?",
        learning_points=None,
        cs_search_mode="cheap",
        index_root=index_root,
        readiness=ReadyReport(),
    )

    assert result["meta"]["backend"] == "lance"
    assert calls
    assert calls[0]["backend"] == "lance"


def test_augment_surfaces_query_candidate_debug_from_searcher(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root, indexer.LANCE_INDEX_VERSION)

    def fake_search(prompt, **kwargs):
        kwargs["debug"]["query_candidate_kinds"] = ["original", "rewrite"]
        return [_hit()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="그거 왜 안 보여?",
        learning_points=None,
        cs_search_mode="cheap",
        index_root=index_root,
        readiness=ReadyReport(),
    )

    assert result["meta"]["query_candidate_kinds"] == ["original", "rewrite"]
    assert result["meta"]["query_plans"] == [
        {
            "bucket": "fallback:general:그거",
            "query_candidate_kinds": ["original", "rewrite"],
        }
    ]
    assert result["sidecar"]["query_candidate_kinds"] == ["original", "rewrite"]
