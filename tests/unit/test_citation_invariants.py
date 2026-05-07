"""Artifact-bounded citation invariant tests."""

from __future__ import annotations

from unittest import mock

from scripts.workbench.core import coach_run as cr
from scripts.workbench.core.citation_verifier import verify_citation_invariants
from scripts.workbench.core.response_contract import build_cs_block


def _hit(path: str, *, title: str = "Doc") -> dict:
    return {
        "path": path,
        "title": title,
        "category": "spring",
        "section_title": "핵심",
        "score": 0.9,
        "snippet_preview": "본문 요약",
    }


def _augment_with_source(
    source_path: str,
    *,
    verifier_hits: list[dict] | None = None,
    citation_paths: list[str] | None = None,
) -> dict:
    return {
        "by_learning_point": {"spring/bean": [_hit(source_path)]},
        "by_fallback_key": {},
        "fallback_reason": None,
        "cs_categories_hit": ["spring"],
        "sidecar_path": "contexts/cs-augmentation.json",
        "meta": {
            "rag_ready": True,
            "mode_used": "cheap",
            "reason": "ready",
            "latency_ms": 1,
        },
        "verifier_hits": verifier_hits or [],
        "citation_paths": citation_paths or [],
    }


def test_grounded_citation_passes() -> None:
    block = build_cs_block(
        _augment_with_source(
            "knowledge/cs/contents/spring/bean.md",
            verifier_hits=[{"path": "knowledge/cs/contents/spring/bean.md"}],
        )
    )

    assert block["grounding_check"] == {
        "ok": True,
        "ungrounded_paths": [],
        "severity": "ok",
    }
    assert "출처 검증 안 됨" not in block["markdown"]


def test_orphan_path_in_cs_block_sources_flagged() -> None:
    block = build_cs_block(
        _augment_with_source(
            "knowledge/cs/contents/spring/orphan.md",
            verifier_hits=[{"path": "knowledge/cs/contents/spring/bean.md"}],
        )
    )

    assert block["grounding_check"]["ok"] is False
    assert block["grounding_check"]["severity"] == "warn"
    assert block["grounding_check"]["ungrounded_paths"] == [
        "knowledge/cs/contents/spring/orphan.md"
    ]


def test_warning_does_not_block_response() -> None:
    block = build_cs_block(
        _augment_with_source(
            "knowledge/cs/contents/spring/orphan.md",
            verifier_hits=[{"path": "knowledge/cs/contents/spring/bean.md"}],
        ),
        applicability_hint="primary",
    )

    assert block["reason"] == "ready"
    assert block["applicability_hint"] == "primary"
    assert block["sources"]
    assert block["markdown"].startswith("## 이번 질문의 CS 근거")
    assert "출처 검증 안 됨" in block["markdown"]


def test_verifier_does_not_inspect_response_text() -> None:
    result = verify_citation_invariants(
        {
            "markdown": "본문에는 knowledge/cs/contents/spring/not-a-source.md가 언급됨",
            "sources": [{"path": "knowledge/cs/contents/spring/bean.md"}],
        },
        verifier_hits=[{"path": "knowledge/cs/contents/spring/bean.md"}],
        citation_paths=[],
    )

    assert result["ok"] is True
    assert result["ungrounded_paths"] == []


def test_compact_augmentation_includes_verifier_hits_from_sidecar() -> None:
    augment_result = {
        "by_learning_point": {"spring/bean": [_hit("sidecar.md")]},
        "by_fallback_key": {},
        "fallback_reason": None,
        "cs_categories_hit": ["spring"],
        "sidecar": {"hits": [{"path": "sidecar.md", "title": "Sidecar"}]},
        "response_hints": {"citation_paths": ["sidecar.md"]},
        "meta": {"rag_ready": True, "mode_used": "cheap", "reason": "ready"},
    }

    phase = _run_pre_augment_with(augment_result)

    compact = phase["cs_augmentation_compact"]
    assert compact["verifier_hits"] == [{"path": "sidecar.md", "title": "Sidecar"}]
    assert compact["citation_paths"] == ["sidecar.md"]


def test_top_level_hits_not_used() -> None:
    augment_result = {
        "by_learning_point": {"spring/bean": [_hit("sidecar.md")]},
        "by_fallback_key": {},
        "fallback_reason": None,
        "cs_categories_hit": ["spring"],
        "sidecar": {"hits": [{"path": "sidecar.md", "title": "Sidecar"}]},
        "hits": [{"path": "top-level.md", "title": "Top Level"}],
        "response_hints": {"citation_paths": ["sidecar.md"]},
        "meta": {"rag_ready": True, "mode_used": "cheap", "reason": "ready"},
    }

    phase = _run_pre_augment_with(augment_result)

    compact = phase["cs_augmentation_compact"]
    assert compact["verifier_hits"] == [{"path": "sidecar.md", "title": "Sidecar"}]
    assert {"path": "top-level.md", "title": "Top Level"} not in compact["verifier_hits"]


def _run_pre_augment_with(augment_result: dict) -> dict:
    with (
        mock.patch.object(cr, "_load_cross_learner_context", return_value=None),
        mock.patch.object(
            cr,
            "intent_pre_decide",
            return_value={"pre_intent": "cs_only", "cs_search_mode": "cheap"},
        ),
        mock.patch.object(
            cr,
            "_check_cs_readiness",
            return_value={
                "state": "ready",
                "reason": "ok",
                "next_command": None,
                "corpus_hash": None,
                "index_manifest_hash": None,
            },
        ),
        mock.patch("scripts.learning.integration.augment", return_value=augment_result),
        mock.patch("scripts.workbench.core.profile.load_profile", return_value={}),
        mock.patch("scripts.workbench.core.concept_catalog.load_catalog", return_value={}),
    ):
        return cr._pre_augment_phase(
            prompt="Spring Bean이 뭐야?",
            reformulated_query="spring bean",
            learner_state_full={},
            session_payload={
                "repo": "demo-repo",
                "learning_point_recommendations": [],
                "primary_topic": "spring",
            },
            pending_drill=None,
        )
