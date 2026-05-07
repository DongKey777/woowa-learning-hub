from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts.workbench.core import response_quality


def test_build_response_quality_row_redacts_and_detects_citation_mismatch():
    row = response_quality.build_response_quality_row(
        source_event_id="event-1234",
        turn_id="turn-event-1234",
        prompt="AOP 프록시가 뭐야? email me foo@example.com",
        response_text="[RAG: tier-2]\nAOP 설명입니다.",
        response_summary="AOP proxy 설명",
        citation_paths_expected=["contents/spring/aop-proxy-mechanism.md"],
        citation_paths_declared=["contents/spring/README.md"],
        model_runtime="codex",
        require_rag_header=True,
        now=datetime(2026, 5, 7, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert row["schema_id"] == "assistant-response-quality-v1"
    assert row["logged_at"] == "2026-05-07T12:00:00+00:00"
    assert row["prompt"] == "AOP 프록시가 뭐야? email me ***REDACTED***"
    assert "citation_mismatch" in row["quality_flags"]
    assert "missing_rag_header" not in row["quality_flags"]
    assert row["redaction_applied"] is True


def test_infer_quality_flags_detects_missing_header_and_duplicate_text():
    repeated = "같은 문단입니다. " * 12
    text = f"{repeated}\n\n{repeated}"
    flags = response_quality.infer_quality_flags(
        response_text=text,
        citation_paths_expected=["doc.md"],
        citation_paths_declared=[],
        require_rag_header=True,
    )

    assert "missing_citation" in flags
    assert "missing_rag_header" in flags
    assert "duplicate_text" in flags


def test_append_response_quality_writes_global_and_repo_logs(tmp_path):
    learner_log = tmp_path / "state" / "learner" / "response-quality.jsonl"
    repo_root = tmp_path
    with mock.patch.object(response_quality, "learner_response_quality_path", lambda: learner_log):
        paths = response_quality.append_response_quality(
            source_event_id="event-abc",
            turn_id="turn-event-abc",
            prompt="Bean이 뭐야?",
            response_text="[RAG: tier-1]\nBean 설명",
            response_summary="Bean 정의 설명",
            citation_paths_expected=["contents/spring/ioc-di-container.md"],
            citation_paths_declared=["contents/spring/ioc-di-container.md"],
            repo="spring-roomescape-member",
            repo_root=repo_root,
        )

    assert learner_log in paths
    repo_log = repo_root / "state" / "repos" / "spring-roomescape-member" / "logs" / "response_quality.jsonl"
    assert repo_log in paths
    assert learner_log.exists()
    assert repo_log.exists()
    row = json.loads(learner_log.read_text(encoding="utf-8").strip())
    assert row["source_event_id"] == "event-abc"
    assert row["quality_flags"] == []


def test_mining_helpers_summarize_flags_and_mismatches():
    rows = [
        {
            "quality_flags": ["citation_mismatch", "duplicate_text"],
            "prompt": "Q",
            "citation_paths_expected": ["expected.md"],
            "citation_paths_declared": ["declared.md"],
        },
        {
            "quality_flags": ["citation_mismatch"],
            "prompt": "Q",
            "citation_paths_expected": ["expected.md"],
            "citation_paths_declared": ["declared.md"],
        },
    ]

    assert response_quality.summarize_quality_flags(rows) == [
        ("citation_mismatch", 2),
        ("duplicate_text", 1),
    ]
    assert response_quality.citation_mismatch_candidates(rows) == [
        ("Q", "expected.md", "declared.md", 2),
    ]
