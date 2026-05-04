"""Phase 9.3 Step C — augment detects R3 sentinel → tier downgrade signal.

When ``searcher.search`` returns a single hit with
``hit["sentinel"] == "no_confident_match"``, ``integration.augment``
must:

  * empty ``all_hits`` / ``by_learning_point`` / ``by_fallback_key``
    (so AI session has no doc context to mistakenly cite)
  * set ``response_hints.tier_downgrade``,
    ``response_hints.fallback_disclaimer``,
    and force ``response_hints.citation_markdown = None``
  * record ``meta.fallback_reason`` so trace + telemetry is honest

This is the bridge between R3 sentinel and the rag-ask tier 0 force
in Step D.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.learning import integration
from scripts.learning.rag import indexer, searcher


class _ReadyReport:
    state = "ready"
    reason = "ready"
    corpus_hash = "fixture"
    index_manifest_hash = "fixture"
    next_command = None


def _write_manifest(index_root: Path) -> None:
    index_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "index_version": indexer.LANCE_INDEX_VERSION,
        "row_count": 1,
        "corpus_hash": "fixture",
        "corpus_root": "fixture",
        "encoder": {"model_id": "BAAI/bge-m3"},
        "lancedb": {"table_name": indexer.LANCE_TABLE_NAME},
        "modalities": ["fts", "dense", "sparse"],
    }
    (index_root / indexer.MANIFEST_NAME).write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _sentinel_hit() -> dict:
    return {
        "row_id": None,
        "doc_id": None,
        "chunk_id": None,
        "path": "<sentinel:no_confident_match>",
        "title": "",
        "category": "",
        "section_title": "",
        "section_path": [],
        "score": -1.5,
        "snippet_preview": "",
        "anchors": [],
        "r3_sources": [],
        "sentinel": "no_confident_match",
        "rejected_top": "knowledge/cs/contents/spring/random.md",
        "rejected_score": -1.5,
        "threshold": 0.0,
    }


def _normal_hit() -> dict:
    return {
        "path": "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "title": "Spring Bean DI Basics",
        "category": "spring",
        "section_title": "핵심 개념",
        "section_path": ["Spring Bean DI Basics", "핵심 개념"],
        "score": 0.92,
        "snippet_preview": "Spring DI 정의",
    }


def test_augment_translates_sentinel_to_tier_downgrade(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [_sentinel_hit()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="rare topic",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    # No corpus context for the AI session to cite
    assert result["by_learning_point"] == {}
    assert result["by_fallback_key"] == {}

    # Response hints carry the downgrade signal
    rh = result["response_hints"]
    assert rh["tier_downgrade"] == "corpus_gap_no_confident_match"
    assert rh["fallback_disclaimer"], "disclaimer must be a non-empty Korean string"
    assert "코퍼스" in rh["fallback_disclaimer"]
    assert "일반 지식" in rh["fallback_disclaimer"]
    assert rh["citation_markdown"] is None
    assert rh["citation_paths"] == []

    # Telemetry — meta.fallback_reason mirrors the discriminator
    assert result["meta"]["fallback_reason"] == "corpus_gap_no_confident_match"


def test_augment_normal_hits_have_no_tier_downgrade(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [_normal_hit()]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh.get("tier_downgrade") is None
    assert rh.get("fallback_disclaimer") is None
    # Citation block is rendered as before
    assert rh["citation_markdown"] is not None
    assert "knowledge/cs/contents/spring/spring-bean-di-basics.md" in rh["citation_markdown"]


def test_augment_empty_hits_have_no_tier_downgrade(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return []

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="rare topic",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    # Empty hits is NOT the same as sentinel — no tier downgrade
    # (this distinguishes "RAG ran but found nothing relevant" vs
    # "RAG ran, top-1 was below confidence threshold")
    assert rh.get("tier_downgrade") is None
    assert rh["citation_markdown"] is None
