"""CLI for drill-grade-v1 wrapper (plan §P7.3 / §9 element 3).

Deterministic placeholder factory: writes the input artifact for an AI
drill grading turn and prints the expected output path. The AI session
follows ``skills/woowa-drill-grade/SKILL.md`` to fill the output. The
downstream caller appends the validated output (one JSON object) as a
JSONL row to ``state/repos/<repo>/memory/drill-history.jsonl``.

Schema (canonical): ``docs/ai-behavior-contracts.md`` §drill-grade-v1.

This file never calls an LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_ID_INPUT = "drill-grade-v1.input"
DEFAULT_OUT_REL = "state/cs_rag/drill_grade"

# Restrict drill_session_id to characters safe for filenames so we can
# use it directly as the artifact basename without sanitisation
# surprises. Allow letters, digits, hyphen, underscore, dot.
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


# ---------------------------------------------------------------------------
# parsing helpers
# ---------------------------------------------------------------------------

def parse_expected_terms(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tok.strip() for tok in raw.split(",") if tok.strip()]


def validate_drill_session_id(drill_session_id: str) -> None:
    if not drill_session_id or not _SAFE_ID_RE.match(drill_session_id):
        raise ValueError(
            "drill_session_id must match [A-Za-z0-9._-]+ (got %r)" % drill_session_id
        )


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "knowledge" / "cs").exists() and (parent / "scripts").exists():
            return parent
    return here.parents[2]


def write_input_artifact(
    *,
    drill_session_id: str,
    question: str,
    answer: str,
    expected_terms: list[str],
    learning_point: str | None,
    source_doc: str | None,
    out_root: Path,
    now: datetime | None = None,
) -> tuple[Path, Path]:
    """Write input artifact and return (input_path, output_path)."""
    validate_drill_session_id(drill_session_id)
    if not question or not question.strip():
        raise ValueError("question must not be empty")
    if not answer or not answer.strip():
        raise ValueError("answer must not be empty")

    out_root.mkdir(parents=True, exist_ok=True)
    input_path = out_root / f"{drill_session_id}.input.json"
    output_path = out_root / f"{drill_session_id}.output.json"
    payload = {
        "schema_id": SCHEMA_ID_INPUT,
        "drill_session_id": drill_session_id,
        "question": question,
        "answer": answer,
        "expected_terms": list(expected_terms),
        "learning_point": learning_point,
        "source_doc": source_doc,
        "produced_at": (now or datetime.now(timezone.utc)).isoformat(),
    }
    input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return input_path, output_path


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(
        description=(
            "drill-grade-v1 wrapper. Writes the input artifact and "
            "prints the expected output path. The AI session is "
            "responsible for filling the output (see "
            "skills/woowa-drill-grade/SKILL.md)."
        )
    )
    parser.add_argument("--drill-session-id", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--answer", required=True)
    parser.add_argument(
        "--expected-terms",
        default="",
        help="Comma-separated expected terms (used for accuracy weighting).",
    )
    parser.add_argument("--learning-point", default=None, help="concept_id (optional).")
    parser.add_argument("--source-doc", default=None, help="Source doc path (optional).")
    parser.add_argument(
        "--out",
        default=str(repo_root / DEFAULT_OUT_REL),
        help=f"Storage root (default: {DEFAULT_OUT_REL}).",
    )
    args = parser.parse_args(argv)

    try:
        input_path, output_path = write_input_artifact(
            drill_session_id=args.drill_session_id,
            question=args.question,
            answer=args.answer,
            expected_terms=parse_expected_terms(args.expected_terms),
            learning_point=args.learning_point,
            source_doc=args.source_doc,
            out_root=Path(args.out),
        )
    except ValueError as exc:
        print(f"[drill-grade-prepare] {exc}", file=sys.stderr)
        return 2

    print(json.dumps(
        {
            "schema_id": SCHEMA_ID_INPUT,
            "drill_session_id": args.drill_session_id,
            "input_path": str(input_path),
            "output_path": str(output_path),
        },
        ensure_ascii=False,
    ))
    return 0


# ---------------------------------------------------------------------------
# Output validation (form-only — for the downstream consumer)
# ---------------------------------------------------------------------------

VALID_DIMENSIONS = ("accuracy", "depth", "practicality", "completeness")
DIMENSION_CEILINGS = {"accuracy": 4, "depth": 3, "practicality": 2, "completeness": 1}
LEVEL_BY_TOTAL = {  # mirror of scripts/learning/scoring.py:LEVEL_TABLE
    0: "L1", 1: "L1", 2: "L1",
    3: "L2", 4: "L2",
    5: "L3", 6: "L3",
    7: "L4", 8: "L4",
    9: "L5", 10: "L5",
}


def validate_output(payload: dict, *, expected_drill_session_id: str) -> list[str]:
    """Form-only validator that mirrors docs/ai-behavior-contracts.md
    §drill-grade-v1. Returns a list of violation messages (empty list
    = valid). Used by the downstream consumer + by the schema
    regression test."""
    errors: list[str] = []
    if payload.get("schema_id") != "drill-grade-v1.output":
        errors.append("schema_id mismatch")
    if payload.get("drill_session_id") != expected_drill_session_id:
        errors.append("drill_session_id does not match input")

    scores = payload.get("scores")
    if not isinstance(scores, dict):
        errors.append("scores must be an object")
        scores = {}
    sum_scores = 0
    for dim in VALID_DIMENSIONS:
        v = scores.get(dim)
        if not isinstance(v, int):
            errors.append(f"scores.{dim} must be int")
            continue
        ceil = DIMENSION_CEILINGS[dim]
        if not (0 <= v <= ceil):
            errors.append(f"scores.{dim} out of [0, {ceil}]")
        sum_scores += v

    total = payload.get("total")
    if not isinstance(total, int):
        errors.append("total must be int")
    elif total != sum_scores:
        errors.append(f"total ({total}) != sum(scores) ({sum_scores})")

    level = payload.get("level")
    if level not in {"L1", "L2", "L3", "L4", "L5"}:
        errors.append("level out of enum")
    elif isinstance(total, int) and 0 <= total <= 10 and level != LEVEL_BY_TOTAL[total]:
        errors.append(f"level {level} does not match total {total} (expected {LEVEL_BY_TOTAL[total]})")

    weak = payload.get("weak_dimensions")
    if not isinstance(weak, list):
        errors.append("weak_dimensions must be list")
    else:
        bad = [d for d in weak if d not in VALID_DIMENSIONS]
        if bad:
            errors.append(f"weak_dimensions contains unknown: {bad}")

    rationale = payload.get("rationale")
    if not isinstance(rationale, dict):
        errors.append("rationale must be object")
    else:
        for dim in VALID_DIMENSIONS:
            v = rationale.get(dim)
            if not isinstance(v, str) or not v.strip():
                errors.append(f"rationale.{dim} empty")

    if payload.get("scored_by") not in {"ai_session", "rule_baseline"}:
        errors.append("scored_by must be 'ai_session' or 'rule_baseline'")

    if not isinstance(payload.get("produced_at"), str):
        errors.append("produced_at missing")

    return errors


if __name__ == "__main__":
    raise SystemExit(main())
