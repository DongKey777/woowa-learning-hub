"""Reader for drill-grade-v1 output JSON (plan §P7.3 consumer side).

After ``bin/drill-grade-prepare`` writes the input artifact and the
AI session writes the grading output to
``state/cs_rag/drill_grade/<drill_session_id>.output.json``, the
scoring code reads it back through this module. Validation mirrors
``cli_drill_grade_prepare.validate_output`` and the form rules in
``docs/ai-behavior-contracts.md`` § drill-grade-v1.

Returns a typed ``DrillGradeOutput`` on hit, None on miss /
corruption / contract violation. The caller (scoring pipeline)
treats None as "AI unavailable" and falls back to
``scripts/learning/scoring.py:score_answer``.

Pure read path. Same fail-soft contract as the other v1 readers.

Tested in ``tests/unit/test_drill_grade_reader.py``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Reuse the validator + level table from the wrapper so the reader
# and writer agree on form by construction.
from scripts.learning import cli_drill_grade_prepare as _W


SCHEMA_ID_OUTPUT = "drill-grade-v1.output"
DEFAULT_STORAGE_REL = Path("state") / "cs_rag" / "drill_grade"


@dataclass(frozen=True)
class DrillGradeOutput:
    drill_session_id: str
    scores: dict
    total: int
    level: str
    weak_dimensions: tuple[str, ...]
    rationale: dict
    improvement_notes: str
    scored_by: str
    produced_at: str


def output_path_for(
    drill_session_id: str,
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> Path:
    """Resolve expected output path. Reuses the wrapper's basename
    rule (``drill_session_id.output.json``)."""
    _W.validate_drill_session_id(drill_session_id)
    base = storage or (repo_root / DEFAULT_STORAGE_REL)
    return base / f"{drill_session_id}.output.json"


def read_grade(
    drill_session_id: str,
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> DrillGradeOutput | None:
    """Read + validate the AI drill grading output.

    Returns None when:
    - drill_session_id contains characters outside [A-Za-z0-9._-] (the
      wrapper's basename safety rule)
    - the file does not exist (AI hasn't written; cache miss)
    - the JSON fails to parse (corrupt file)
    - the payload fails form validation (contract violation)

    Caller falls back to the rule baseline (``score_answer``) on None.
    """
    try:
        path = output_path_for(
            drill_session_id, repo_root=repo_root, storage=storage,
        )
    except ValueError:
        return None
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    errors = _W.validate_output(
        payload, expected_drill_session_id=drill_session_id,
    )
    if errors:
        return None
    return DrillGradeOutput(
        drill_session_id=payload["drill_session_id"],
        scores=dict(payload["scores"]),
        total=int(payload["total"]),
        level=payload["level"],
        weak_dimensions=tuple(payload.get("weak_dimensions", [])),
        rationale=dict(payload["rationale"]),
        improvement_notes=payload.get("improvement_notes", "") or "",
        scored_by=payload["scored_by"],
        produced_at=payload["produced_at"],
    )


def read_with_validation_errors(
    drill_session_id: str,
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> tuple[DrillGradeOutput | None, list[str]]:
    """Like ``read_grade`` but also returns the validation error
    list."""
    try:
        path = output_path_for(
            drill_session_id, repo_root=repo_root, storage=storage,
        )
    except ValueError as exc:
        return None, [f"unsafe_drill_session_id: {exc}"]
    if not path.exists():
        return None, ["file_not_found"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"json_decode_error: {exc}"]
    if not isinstance(payload, dict):
        return None, ["payload_not_object"]
    errors = _W.validate_output(
        payload, expected_drill_session_id=drill_session_id,
    )
    if errors:
        return None, errors
    return DrillGradeOutput(
        drill_session_id=payload["drill_session_id"],
        scores=dict(payload["scores"]),
        total=int(payload["total"]),
        level=payload["level"],
        weak_dimensions=tuple(payload.get("weak_dimensions", [])),
        rationale=dict(payload["rationale"]),
        improvement_notes=payload.get("improvement_notes", "") or "",
        scored_by=payload["scored_by"],
        produced_at=payload["produced_at"],
    ), []
