"""Schema regression tests for the router-fallback-v1 AI Behavior
Contract. Validates *form* only — the AI's content quality is tracked
through learner feedback. See ``docs/ai-behavior-contracts.md``
§router-fallback-v1.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.learning import cli_rag_route_fallback as W


VALID_TIER_MODE = {0: "skip", 1: "cheap", 2: "full", 3: "coach"}


# ---------------------------------------------------------------------------
# candidate_tiers parsing
# ---------------------------------------------------------------------------

def test_parse_candidate_tiers_default():
    assert W.parse_candidate_tiers("0,1,2,3") == (0, 1, 2, 3)


def test_parse_candidate_tiers_subset_sorted():
    assert W.parse_candidate_tiers("2,1") == (1, 2)


def test_parse_candidate_tiers_dedupe():
    assert W.parse_candidate_tiers("1,1,2") == (1, 2)


def test_parse_candidate_tiers_rejects_empty():
    with pytest.raises(ValueError):
        W.parse_candidate_tiers("")


def test_parse_candidate_tiers_rejects_non_integer():
    with pytest.raises(ValueError):
        W.parse_candidate_tiers("1,a,3")


def test_parse_candidate_tiers_rejects_out_of_range():
    with pytest.raises(ValueError):
        W.parse_candidate_tiers("0,1,4")


# ---------------------------------------------------------------------------
# prompt_hash determinism
# ---------------------------------------------------------------------------

def test_prompt_hash_deterministic():
    h1 = W.compute_prompt_hash("스프링 빈?", (0, 1, 2, 3))
    h2 = W.compute_prompt_hash("스프링 빈?", (0, 1, 2, 3))
    assert h1 == h2
    assert len(h1) == 40


def test_prompt_hash_changes_with_candidate_tiers():
    h1 = W.compute_prompt_hash("어떤 거야?", (0, 1, 2, 3))
    h2 = W.compute_prompt_hash("어떤 거야?", (0, 1, 2))  # tier 3 blocked
    assert h1 != h2


def test_prompt_hash_invariant_to_candidate_tier_order():
    h1 = W.compute_prompt_hash("hi", (0, 1, 2, 3))
    h2 = W.compute_prompt_hash("hi", (3, 0, 2, 1))
    assert h1 == h2


# ---------------------------------------------------------------------------
# write_input_artifact
# ---------------------------------------------------------------------------

def test_write_input_artifact_creates_schema_compliant_file(tmp_path):
    input_path, output_path, prompt_hash = W.write_input_artifact(
        prompt="MVCC가 격리수준이랑 무슨 관계야?",
        heuristic_tier=1,
        heuristic_confidence=0.42,
        matched_tokens=["격리수준"],
        candidate_tiers=(0, 1, 2, 3),
        history_summary="이전 turn: 트랜잭션 격리 단계",
        out_root=tmp_path,
        now=datetime(2026, 4, 30, 13, 0, 0, tzinfo=timezone.utc),
    )

    assert input_path.exists()
    assert not output_path.exists()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    assert payload["schema_id"] == "router-fallback-v1.input"
    assert payload["prompt_hash"] == prompt_hash
    assert payload["candidate_tiers"] == [0, 1, 2, 3]
    assert payload["heuristic_decision"]["tier"] == 1
    assert payload["heuristic_decision"]["confidence"] == 0.42
    assert payload["heuristic_decision"]["matched_tokens"] == ["격리수준"]
    assert payload["history_summary"] == "이전 turn: 트랜잭션 격리 단계"


def test_write_input_artifact_rejects_invalid_tier(tmp_path):
    with pytest.raises(ValueError):
        W.write_input_artifact(
            prompt="x",
            heuristic_tier=4,  # invalid
            heuristic_confidence=0.5,
            matched_tokens=[],
            candidate_tiers=(0, 1, 2, 3),
            history_summary=None,
            out_root=tmp_path,
        )


def test_write_input_artifact_rejects_invalid_confidence(tmp_path):
    with pytest.raises(ValueError):
        W.write_input_artifact(
            prompt="x",
            heuristic_tier=1,
            heuristic_confidence=1.5,  # invalid
            matched_tokens=[],
            candidate_tiers=(0, 1, 2, 3),
            history_summary=None,
            out_root=tmp_path,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_main_writes_artifact_and_prints_paths(tmp_path, capsys):
    rc = W.main([
        "스프링 빈?",
        "--heuristic-tier", "1",
        "--heuristic-confidence", "0.4",
        "--matched-tokens", "스프링,빈",
        "--out", str(tmp_path),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_id"] == "router-fallback-v1.input"
    assert payload["candidate_tiers"] == [0, 1, 2, 3]
    assert Path(payload["input_path"]).exists()
    assert not Path(payload["output_path"]).exists()


def test_cli_main_handles_blocked_tier3(tmp_path, capsys):
    rc = W.main([
        "내 PR 어때?",
        "--heuristic-tier", "3",
        "--heuristic-confidence", "0.3",
        "--candidate-tiers", "0,1,2",
        "--out", str(tmp_path),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["candidate_tiers"] == [0, 1, 2]


def test_cli_main_rejects_empty_prompt(tmp_path, capsys):
    rc = W.main([
        "  ",
        "--heuristic-tier", "0",
        "--heuristic-confidence", "0.1",
        "--out", str(tmp_path),
    ])
    assert rc == 2


def test_cli_main_rejects_bad_candidate_tiers(tmp_path, capsys):
    rc = W.main([
        "x",
        "--heuristic-tier", "1",
        "--heuristic-confidence", "0.4",
        "--candidate-tiers", "1,bogus",
        "--out", str(tmp_path),
    ])
    assert rc == 2


# ---------------------------------------------------------------------------
# Output validator (mirrors docs/ai-behavior-contracts.md)
# ---------------------------------------------------------------------------

def _valid_output(prompt_hash: str, *, tier: int = 1, mode: str = "cheap") -> dict:
    return {
        "schema_id": "router-fallback-v1.output",
        "prompt_hash": prompt_hash,
        "tier": tier,
        "mode": mode,
        "confidence": 0.7,
        "rationale": "정의 시그널만 있고 비교/깊이 없음 → tier 1",
        "scored_by": "ai_session",
        "produced_at": "2026-04-30T13:05:00+00:00",
    }


def validate_output(
    payload: dict,
    *,
    expected_prompt_hash: str,
    candidate_tiers: list[int],
) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_id") != "router-fallback-v1.output":
        errors.append("schema_id mismatch")
    if payload.get("prompt_hash") != expected_prompt_hash:
        errors.append("prompt_hash does not match input")
    tier = payload.get("tier")
    if tier not in candidate_tiers:
        errors.append(f"tier {tier} not in candidate_tiers")
    mode = payload.get("mode")
    if mode not in {"skip", "cheap", "full", "coach"}:
        errors.append("mode out of enum")
    # Tier-mode pairing (hard contract — see Skill step 4)
    expected_mode = VALID_TIER_MODE.get(tier)
    if expected_mode and mode != expected_mode:
        errors.append(f"tier {tier} requires mode '{expected_mode}', got '{mode}'")
    conf = payload.get("confidence")
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        errors.append("confidence out of [0, 1]")
    rat = payload.get("rationale")
    if not isinstance(rat, str) or not rat.strip():
        errors.append("rationale empty")
    if payload.get("scored_by") != "ai_session":
        errors.append("scored_by must be literal 'ai_session'")
    if not isinstance(payload.get("produced_at"), str):
        errors.append("produced_at missing")
    return errors


def test_output_validator_accepts_well_formed():
    payload = _valid_output("abc")
    assert validate_output(payload, expected_prompt_hash="abc", candidate_tiers=[0, 1, 2, 3]) == []


def test_output_validator_rejects_tier_outside_candidates():
    payload = _valid_output("abc", tier=3, mode="coach")
    errors = validate_output(payload, expected_prompt_hash="abc", candidate_tiers=[0, 1, 2])
    assert any("tier" in e and "candidate" in e for e in errors)


def test_output_validator_rejects_tier_mode_mismatch():
    payload = _valid_output("abc", tier=1, mode="full")  # tier 1 requires "cheap"
    errors = validate_output(payload, expected_prompt_hash="abc", candidate_tiers=[0, 1, 2, 3])
    assert any("requires mode" in e for e in errors)


def test_output_validator_rejects_unknown_mode():
    payload = _valid_output("abc")
    payload["mode"] = "deep"
    errors = validate_output(payload, expected_prompt_hash="abc", candidate_tiers=[0, 1, 2, 3])
    assert any("mode out of enum" in e for e in errors)


def test_output_validator_rejects_blank_rationale():
    payload = _valid_output("abc")
    payload["rationale"] = "   "
    errors = validate_output(payload, expected_prompt_hash="abc", candidate_tiers=[0, 1, 2, 3])
    assert any("rationale" in e for e in errors)


def test_output_validator_rejects_wrong_scored_by():
    payload = _valid_output("abc")
    payload["scored_by"] = "rule"
    errors = validate_output(payload, expected_prompt_hash="abc", candidate_tiers=[0, 1, 2, 3])
    assert any("scored_by" in e for e in errors)


def test_output_validator_rejects_confidence_out_of_range():
    payload = _valid_output("abc")
    payload["confidence"] = -0.1
    errors = validate_output(payload, expected_prompt_hash="abc", candidate_tiers=[0, 1, 2, 3])
    assert any("confidence" in e for e in errors)
