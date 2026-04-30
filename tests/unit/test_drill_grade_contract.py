"""Schema regression tests for the drill-grade-v1 AI Behavior Contract.

Validates *form* only — the AI's grading quality is tracked through
learner feedback (P7.1) + auto-surface when the AI score diverges from
the rule baseline by ≥ 3 points. See ``docs/ai-behavior-contracts.md``
§drill-grade-v1.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.learning import cli_drill_grade_prepare as W


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _valid_output(drill_session_id: str = "drill-001") -> dict:
    return {
        "schema_id": "drill-grade-v1.output",
        "drill_session_id": drill_session_id,
        "scores": {
            "accuracy": 3,
            "depth": 2,
            "practicality": 1,
            "completeness": 1,
        },
        "total": 7,
        "level": "L4",
        "weak_dimensions": ["practicality"],
        "rationale": {
            "accuracy": "DI 정의 정확",
            "depth": "메커니즘은 있으나 trade-off 미언급",
            "practicality": "@Component 언급은 있으나 사용 시점 없음",
            "completeness": "결론에서 한 번 정리해 흐름이 닫힘",
        },
        "improvement_notes": "다음 drill로 prototype scope 동시성 함정",
        "scored_by": "ai_session",
        "produced_at": "2026-04-30T13:30:00+00:00",
    }


# ---------------------------------------------------------------------------
# drill_session_id validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("good", ["drill-001", "abc_123", "session.42", "uuid-style-1234"])
def test_validate_drill_session_id_accepts(good):
    W.validate_drill_session_id(good)  # no raise


@pytest.mark.parametrize("bad", ["", " ", "has space", "../etc/passwd", "name/slash", "한글", "name?wat"])
def test_validate_drill_session_id_rejects(bad):
    with pytest.raises(ValueError):
        W.validate_drill_session_id(bad)


# ---------------------------------------------------------------------------
# expected_terms parsing
# ---------------------------------------------------------------------------

def test_parse_expected_terms_empty():
    assert W.parse_expected_terms("") == []
    assert W.parse_expected_terms(None) == []


def test_parse_expected_terms_strips_whitespace():
    assert W.parse_expected_terms("a, b ,c") == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# write_input_artifact
# ---------------------------------------------------------------------------

def test_write_input_artifact_creates_schema_compliant_file(tmp_path):
    input_path, output_path = W.write_input_artifact(
        drill_session_id="drill-001",
        question="스프링 빈이 뭔가요?",
        answer="컨테이너가 관리하는 객체이고 DI로 주입됩니다.",
        expected_terms=["bean", "DI"],
        learning_point="spring/bean",
        source_doc="knowledge/cs/contents/spring/bean.md",
        out_root=tmp_path,
        now=datetime(2026, 4, 30, 13, 0, 0, tzinfo=timezone.utc),
    )
    assert input_path.exists()
    assert not output_path.exists()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "drill-grade-v1.input"
    assert payload["drill_session_id"] == "drill-001"
    assert payload["expected_terms"] == ["bean", "DI"]
    assert payload["learning_point"] == "spring/bean"
    assert payload["source_doc"] == "knowledge/cs/contents/spring/bean.md"


def test_write_input_artifact_rejects_empty_question(tmp_path):
    with pytest.raises(ValueError):
        W.write_input_artifact(
            drill_session_id="x", question="", answer="a",
            expected_terms=[], learning_point=None, source_doc=None,
            out_root=tmp_path,
        )


def test_write_input_artifact_rejects_empty_answer(tmp_path):
    with pytest.raises(ValueError):
        W.write_input_artifact(
            drill_session_id="x", question="q", answer=" ",
            expected_terms=[], learning_point=None, source_doc=None,
            out_root=tmp_path,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_main_writes_artifact_and_prints_paths(tmp_path, capsys):
    rc = W.main([
        "--drill-session-id", "drill-001",
        "--question", "Spring Bean이 뭐야?",
        "--answer", "컨테이너가 관리하는 객체",
        "--expected-terms", "bean,컨테이너",
        "--learning-point", "spring/bean",
        "--out", str(tmp_path),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["drill_session_id"] == "drill-001"
    assert Path(payload["input_path"]).exists()
    assert not Path(payload["output_path"]).exists()


def test_cli_main_rejects_unsafe_session_id(tmp_path, capsys):
    rc = W.main([
        "--drill-session-id", "../escape",
        "--question", "q", "--answer", "a",
        "--out", str(tmp_path),
    ])
    assert rc == 2


# ---------------------------------------------------------------------------
# Output validator
# ---------------------------------------------------------------------------

def test_output_validator_accepts_well_formed():
    assert W.validate_output(_valid_output(), expected_drill_session_id="drill-001") == []


def test_output_validator_rejects_mismatched_session_id():
    payload = _valid_output()
    errors = W.validate_output(payload, expected_drill_session_id="drill-other")
    assert any("drill_session_id" in e for e in errors)


def test_output_validator_rejects_dimension_over_ceiling():
    payload = _valid_output()
    payload["scores"]["accuracy"] = 5  # ceiling = 4
    payload["total"] = 9
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("accuracy" in e and "out of" in e for e in errors)


def test_output_validator_rejects_total_mismatch():
    payload = _valid_output()
    payload["total"] = 99
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("total" in e for e in errors)


def test_output_validator_rejects_level_inconsistent_with_total():
    payload = _valid_output()
    payload["level"] = "L1"  # total=7 should map to L4
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("level" in e for e in errors)


@pytest.mark.parametrize("total,expected_level", [
    (0, "L1"), (2, "L1"),
    (3, "L2"), (4, "L2"),
    (5, "L3"), (6, "L3"),
    (7, "L4"), (8, "L4"),
    (9, "L5"), (10, "L5"),
])
def test_output_validator_level_mapping_matches_table(total, expected_level):
    assert W.LEVEL_BY_TOTAL[total] == expected_level


def test_output_validator_rejects_unknown_weak_dimension():
    payload = _valid_output()
    payload["weak_dimensions"] = ["accuracy", "speed"]  # speed not a dimension
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("weak_dimensions" in e for e in errors)


def test_output_validator_rejects_missing_rationale_key():
    payload = _valid_output()
    payload["rationale"].pop("practicality")
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("rationale.practicality" in e for e in errors)


def test_output_validator_rejects_blank_rationale():
    payload = _valid_output()
    payload["rationale"]["depth"] = "  "
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("rationale.depth" in e for e in errors)


def test_output_validator_rejects_unknown_scored_by():
    payload = _valid_output()
    payload["scored_by"] = "human"
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("scored_by" in e for e in errors)


def test_output_validator_accepts_rule_baseline_scored_by():
    payload = _valid_output()
    payload["scored_by"] = "rule_baseline"
    assert W.validate_output(payload, expected_drill_session_id="drill-001") == []


def test_output_validator_rejects_negative_score():
    payload = _valid_output()
    payload["scores"]["depth"] = -1
    payload["total"] = 4
    errors = W.validate_output(payload, expected_drill_session_id="drill-001")
    assert any("depth" in e and "out of" in e for e in errors)
