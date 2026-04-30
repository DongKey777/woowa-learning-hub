"""Schema regression tests for the query-rewrite-v1 AI Behavior Contract.

Validates *form* only — the AI's content quality is tracked through
learner feedback (P7.1), not pytest. See
``docs/ai-behavior-contracts.md`` §query-rewrite-v1 for the canonical
schema.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.learning import cli_rag_rewrite_prepare as W


# ---------------------------------------------------------------------------
# Mode inference
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "prompt,expected",
    [
        ("스프링 빈 뭐야?", "normalize"),
        ("스프링 빈 뭐임", "normalize"),
        ("DI랑 IoC 차이가 뭐고 언제 써야 해?", "decompose"),
        ("MVCC가 격리수준이랑 무슨 관계야?", "decompose"),
        ("Hibernate dirty checking이 어떻게 동작하는지 설명", "hyde"),
    ],
)
def test_infer_mode_picks_expected_default(prompt, expected):
    assert W.infer_mode(prompt) == expected


def test_infer_mode_empty_prompt_falls_back_to_hyde():
    assert W.infer_mode("") == "hyde"
    assert W.infer_mode("   ") == "hyde"


# ---------------------------------------------------------------------------
# prompt_hash determinism
# ---------------------------------------------------------------------------

def test_prompt_hash_deterministic_for_same_input():
    h1 = W.compute_prompt_hash("스프링 빈 뭐야?", "normalize")
    h2 = W.compute_prompt_hash("스프링 빈 뭐야?", "normalize")
    assert h1 == h2
    assert len(h1) == 40  # sha1 hex


def test_prompt_hash_differs_when_mode_changes():
    h1 = W.compute_prompt_hash("스프링 빈 뭐야?", "normalize")
    h2 = W.compute_prompt_hash("스프링 빈 뭐야?", "hyde")
    assert h1 != h2


def test_prompt_hash_strips_whitespace():
    h1 = W.compute_prompt_hash("스프링 빈 뭐야?", "normalize")
    h2 = W.compute_prompt_hash("  스프링 빈 뭐야?\n", "normalize")
    assert h1 == h2


# ---------------------------------------------------------------------------
# learner_context normalization
# ---------------------------------------------------------------------------

def test_normalize_learner_context_fills_defaults():
    out = W.normalize_learner_context(None)
    assert out == {
        "experience_level": None,
        "mastered_concepts": [],
        "uncertain_concepts": [],
        "recent_topics": [],
    }


def test_normalize_learner_context_preserves_keys():
    raw = {
        "experience_level": "beginner",
        "mastered_concepts": ["spring/bean"],
        "uncertain_concepts": ["database/mvcc"],
        "recent_topics": ["DI", "IoC"],
    }
    out = W.normalize_learner_context(raw)
    assert out == raw
    # Returned lists are copies, not aliases.
    assert out["mastered_concepts"] is not raw["mastered_concepts"]


# ---------------------------------------------------------------------------
# Input artifact: schema + side effects
# ---------------------------------------------------------------------------

def test_write_input_artifact_creates_schema_compliant_file(tmp_path):
    input_path, output_path, prompt_hash = W.write_input_artifact(
        prompt="스프링 빈 뭐야?",
        mode="normalize",
        learner_context={"experience_level": "beginner"},
        out_root=tmp_path,
        now=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert input_path.exists()
    assert not output_path.exists()  # caller (AI session) writes the output
    assert input_path.name == f"{prompt_hash}.input.json"
    assert output_path.name == f"{prompt_hash}.output.json"

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "query-rewrite-v1.input"
    assert payload["prompt_hash"] == prompt_hash
    assert payload["prompt"] == "스프링 빈 뭐야?"
    assert payload["mode"] == "normalize"
    assert payload["produced_at"] == "2026-04-30T12:00:00+00:00"

    lc = payload["learner_context"]
    assert lc["experience_level"] == "beginner"
    assert lc["mastered_concepts"] == []
    assert lc["uncertain_concepts"] == []
    assert lc["recent_topics"] == []


def test_write_input_artifact_creates_directory(tmp_path):
    nested = tmp_path / "nested" / "query_rewrites"
    input_path, _, _ = W.write_input_artifact(
        prompt="hello",
        mode="hyde",
        learner_context={},
        out_root=nested,
    )
    assert input_path.parent == nested
    assert nested.exists()


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def test_cli_main_writes_artifact_and_prints_paths(tmp_path, capsys):
    rc = W.main([
        "스프링 빈 뭐야?",
        "--mode", "normalize",
        "--out", str(tmp_path),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["schema_id"] == "query-rewrite-v1.input"
    assert payload["mode"] == "normalize"
    assert Path(payload["input_path"]).exists()
    assert Path(payload["input_path"]).parent == tmp_path
    # output_path is *expected*, not yet written
    assert not Path(payload["output_path"]).exists()


def test_cli_main_auto_mode_infers(tmp_path, capsys):
    rc = W.main([
        "DI랑 IoC 차이가 뭐고 언제 써야 해?",
        "--out", str(tmp_path),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "decompose"


def test_cli_main_rejects_empty_prompt(tmp_path, capsys):
    rc = W.main(["   ", "--out", str(tmp_path)])
    assert rc == 2


def test_cli_main_rejects_invalid_learner_context(tmp_path, capsys):
    rc = W.main([
        "spring bean?",
        "--out", str(tmp_path),
        "--learner-context", "not-json",
    ])
    assert rc == 2


def test_cli_main_accepts_learner_context_json(tmp_path, capsys):
    rc = W.main([
        "MVCC?",
        "--out", str(tmp_path),
        "--learner-context",
        '{"experience_level": "intermediate", "uncertain_concepts": ["database/mvcc"]}',
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    artifact = json.loads(Path(payload["input_path"]).read_text(encoding="utf-8"))
    assert artifact["learner_context"]["experience_level"] == "intermediate"
    assert artifact["learner_context"]["uncertain_concepts"] == ["database/mvcc"]


# ---------------------------------------------------------------------------
# Output schema validation (downstream consumer side)
# ---------------------------------------------------------------------------

def _valid_output(prompt_hash: str) -> dict:
    return {
        "schema_id": "query-rewrite-v1.output",
        "prompt_hash": prompt_hash,
        "rewrites": [
            {"text": "스프링 빈의 정의", "rationale": "조사를 제거해 dense 검색에 친화적"},
        ],
        "confidence": 0.7,
        "scored_by": "ai_session",
        "produced_at": "2026-04-30T12:05:00+00:00",
    }


def validate_output(payload: dict, *, expected_prompt_hash: str) -> list[str]:
    """Form-only validator — mirrors the rules in
    docs/ai-behavior-contracts.md. Returns a list of violation messages
    (empty list = valid)."""
    errors: list[str] = []
    if payload.get("schema_id") != "query-rewrite-v1.output":
        errors.append("schema_id mismatch")
    if payload.get("prompt_hash") != expected_prompt_hash:
        errors.append("prompt_hash does not match input")
    rewrites = payload.get("rewrites")
    if not isinstance(rewrites, list) or not (1 <= len(rewrites) <= 3):
        errors.append("rewrites must be a list of length 1..3")
    else:
        for i, item in enumerate(rewrites):
            if not isinstance(item, dict):
                errors.append(f"rewrites[{i}] not an object")
                continue
            if not isinstance(item.get("text"), str) or not item["text"].strip():
                errors.append(f"rewrites[{i}].text empty")
            if not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
                errors.append(f"rewrites[{i}].rationale empty")
    conf = payload.get("confidence")
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        errors.append("confidence out of [0, 1]")
    if payload.get("scored_by") != "ai_session":
        errors.append("scored_by must be literal 'ai_session'")
    if not isinstance(payload.get("produced_at"), str):
        errors.append("produced_at missing")
    return errors


def test_output_validator_accepts_well_formed(tmp_path):
    payload = _valid_output("abc123")
    assert validate_output(payload, expected_prompt_hash="abc123") == []


def test_output_validator_rejects_mismatched_hash():
    payload = _valid_output("abc123")
    errors = validate_output(payload, expected_prompt_hash="ZZZ")
    assert any("prompt_hash" in e for e in errors)


def test_output_validator_rejects_empty_rewrites():
    payload = _valid_output("abc")
    payload["rewrites"] = []
    errors = validate_output(payload, expected_prompt_hash="abc")
    assert any("rewrites" in e for e in errors)


def test_output_validator_rejects_too_many_rewrites():
    payload = _valid_output("abc")
    payload["rewrites"] = [
        {"text": f"q{i}", "rationale": "r"} for i in range(4)
    ]
    errors = validate_output(payload, expected_prompt_hash="abc")
    assert any("rewrites" in e for e in errors)


def test_output_validator_rejects_blank_text():
    payload = _valid_output("abc")
    payload["rewrites"] = [{"text": "   ", "rationale": "r"}]
    errors = validate_output(payload, expected_prompt_hash="abc")
    assert any("text empty" in e for e in errors)


def test_output_validator_rejects_blank_rationale():
    payload = _valid_output("abc")
    payload["rewrites"] = [{"text": "q", "rationale": ""}]
    errors = validate_output(payload, expected_prompt_hash="abc")
    assert any("rationale empty" in e for e in errors)


def test_output_validator_rejects_confidence_out_of_range():
    payload = _valid_output("abc")
    payload["confidence"] = 1.5
    errors = validate_output(payload, expected_prompt_hash="abc")
    assert any("confidence" in e for e in errors)


def test_output_validator_rejects_wrong_scored_by():
    payload = _valid_output("abc")
    payload["scored_by"] = "human"
    errors = validate_output(payload, expected_prompt_hash="abc")
    assert any("scored_by" in e for e in errors)
