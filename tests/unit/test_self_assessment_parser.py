from __future__ import annotations

from scripts.learning import self_assessment


def test_self_assessment_score_extracted() -> None:
    parsed = self_assessment.parse_response(
        "8점이고 막힌 데는 transaction 경계야",
        {
            "trigger_session_id": "sa-1",
            "payload": {"concept_ids": ["concept:spring/transactional"]},
        },
    )
    assert parsed is not None
    assert parsed["score"] == 8
    assert parsed["trigger_session_id"] == "sa-1"
    assert parsed["concept_ids"] == ["concept:spring/transactional"]
    assert "transaction" in parsed["free_text"]


def test_random_self_assessment_rejected_without_pending() -> None:
    assert self_assessment.parse_response("8점이야", None) is None
    assert self_assessment.route_response("8점이야", None, {}) is False


def test_self_assessment_requires_score() -> None:
    parsed = self_assessment.parse_response(
        "아직 애매해",
        {"trigger_session_id": "sa-1", "payload": {"concept_ids": []}},
    )
    assert parsed is None

