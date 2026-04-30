"""Tests for the drill-grade-v1 output reader (P7.3 consumer side)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag import drill_grade as DG
from scripts.learning import cli_drill_grade_prepare as W


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def test_output_path_uses_drill_session_id_basename(tmp_path):
    p = DG.output_path_for("drill-001", repo_root=tmp_path, storage=tmp_path / "dg")
    assert p.name == "drill-001.output.json"
    assert p.parent == tmp_path / "dg"


def test_output_path_rejects_unsafe_session_id(tmp_path):
    with pytest.raises(ValueError):
        DG.output_path_for(
            "../escape", repo_root=tmp_path, storage=tmp_path / "dg",
        )


# ---------------------------------------------------------------------------
# Happy path round-trip with the wrapper
# ---------------------------------------------------------------------------

def _valid_payload(drill_session_id: str = "drill-001") -> dict:
    return {
        "schema_id": "drill-grade-v1.output",
        "drill_session_id": drill_session_id,
        "scores": {"accuracy": 3, "depth": 2, "practicality": 1, "completeness": 1},
        "total": 7,
        "level": "L4",
        "weak_dimensions": ["practicality"],
        "rationale": {
            "accuracy": "DI 정의 정확",
            "depth": "trade-off 미언급",
            "practicality": "@Component 언급은 있으나 사용 시점 없음",
            "completeness": "결론에서 한 번 정리",
        },
        "improvement_notes": "다음 drill: prototype scope 동시성 함정",
        "scored_by": "ai_session",
        "produced_at": "2026-04-30T13:30:00+00:00",
    }


def test_read_grade_returns_typed_output(tmp_path):
    storage = tmp_path / "dg"
    storage.mkdir(parents=True, exist_ok=True)
    (storage / "drill-001.output.json").write_text(
        json.dumps(_valid_payload(), ensure_ascii=False),
        encoding="utf-8",
    )
    out = DG.read_grade("drill-001", repo_root=tmp_path, storage=storage)
    assert out is not None
    assert out.drill_session_id == "drill-001"
    assert out.scores == {"accuracy": 3, "depth": 2, "practicality": 1, "completeness": 1}
    assert out.total == 7
    assert out.level == "L4"
    assert "practicality" in out.weak_dimensions
    assert out.rationale["accuracy"] == "DI 정의 정확"
    assert out.scored_by == "ai_session"


def test_round_trip_with_wrapper(tmp_path):
    storage = tmp_path / "dg"
    storage.mkdir(parents=True, exist_ok=True)

    in_path, out_path = W.write_input_artifact(
        drill_session_id="round-trip-1",
        question="Spring Bean이 뭐야?",
        answer="Bean은 컨테이너가 관리하는 객체이고 DI로 주입됩니다.",
        expected_terms=["bean", "DI"],
        learning_point="spring/bean",
        source_doc=None,
        out_root=storage,
    )
    assert in_path.exists()
    assert not out_path.exists()

    # AI fills the output
    out_path.write_text(
        json.dumps(_valid_payload("round-trip-1"), ensure_ascii=False),
        encoding="utf-8",
    )
    grade = DG.read_grade("round-trip-1", repo_root=tmp_path, storage=storage)
    assert grade is not None
    assert grade.total == 7
    assert grade.level == "L4"


# ---------------------------------------------------------------------------
# Cache miss + corruption
# ---------------------------------------------------------------------------

def test_read_grade_returns_none_on_missing_file(tmp_path):
    out = DG.read_grade(
        "missing-id", repo_root=tmp_path, storage=tmp_path / "missing",
    )
    assert out is None


def test_read_grade_returns_none_on_corrupt_json(tmp_path):
    storage = tmp_path / "dg"
    storage.mkdir(parents=True, exist_ok=True)
    (storage / "drill-002.output.json").write_text("garbage", encoding="utf-8")
    out = DG.read_grade("drill-002", repo_root=tmp_path, storage=storage)
    assert out is None


def test_read_grade_returns_none_for_unsafe_drill_id(tmp_path):
    """Unsafe drill_session_id is the wrapper's safety boundary —
    reader returns None instead of raising."""
    out = DG.read_grade(
        "../escape", repo_root=tmp_path, storage=tmp_path / "dg",
    )
    assert out is None


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

def _write_payload(storage, drill_session_id, payload):
    (storage / f"{drill_session_id}.output.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8",
    )


@pytest.fixture
def storage(tmp_path):
    s = tmp_path / "dg"
    s.mkdir(parents=True, exist_ok=True)
    return s


def test_validation_rejects_dimension_over_ceiling(tmp_path, storage):
    payload = _valid_payload()
    payload["scores"]["accuracy"] = 5  # ceiling = 4
    payload["total"] = 9
    _write_payload(storage, "drill-001", payload)
    out = DG.read_grade("drill-001", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_total_mismatch(tmp_path, storage):
    payload = _valid_payload()
    payload["total"] = 99
    _write_payload(storage, "drill-001", payload)
    out = DG.read_grade("drill-001", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_level_inconsistent_with_total(tmp_path, storage):
    payload = _valid_payload()
    payload["level"] = "L1"  # total=7 should map to L4
    _write_payload(storage, "drill-001", payload)
    out = DG.read_grade("drill-001", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_missing_rationale_key(tmp_path, storage):
    payload = _valid_payload()
    payload["rationale"].pop("practicality")
    _write_payload(storage, "drill-001", payload)
    out = DG.read_grade("drill-001", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_unknown_scored_by(tmp_path, storage):
    payload = _valid_payload()
    payload["scored_by"] = "human"
    _write_payload(storage, "drill-001", payload)
    out = DG.read_grade("drill-001", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_accepts_rule_baseline_scored_by(tmp_path, storage):
    """Both ai_session and rule_baseline are valid scored_by values
    (the wrapper's validate_output accepts both)."""
    payload = _valid_payload()
    payload["scored_by"] = "rule_baseline"
    _write_payload(storage, "drill-001", payload)
    out = DG.read_grade("drill-001", repo_root=tmp_path, storage=storage)
    assert out is not None
    assert out.scored_by == "rule_baseline"


# ---------------------------------------------------------------------------
# Errors API
# ---------------------------------------------------------------------------

def test_read_with_errors_surfaces_file_not_found(tmp_path):
    out, errors = DG.read_with_validation_errors(
        "missing", repo_root=tmp_path, storage=tmp_path / "missing",
    )
    assert out is None
    assert errors == ["file_not_found"]


def test_read_with_errors_surfaces_unsafe_id(tmp_path):
    out, errors = DG.read_with_validation_errors(
        "has space", repo_root=tmp_path, storage=tmp_path / "dg",
    )
    assert out is None
    assert any("unsafe_drill_session_id" in e for e in errors)


def test_read_with_errors_returns_typed_output_on_valid(tmp_path, storage):
    _write_payload(storage, "drill-001", _valid_payload())
    out, errors = DG.read_with_validation_errors(
        "drill-001", repo_root=tmp_path, storage=storage,
    )
    assert errors == []
    assert out is not None
    assert out.total == 7
