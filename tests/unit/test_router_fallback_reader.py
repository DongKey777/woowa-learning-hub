"""Tests for the router-fallback-v1 output reader (P4.4 consumer side)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.workbench.core import router_fallback as RF
from scripts.learning import cli_rag_route_fallback as W


# ---------------------------------------------------------------------------
# Hash compatibility
# ---------------------------------------------------------------------------

def test_hash_matches_wrapper():
    h_w = W.compute_prompt_hash("스프링 빈?", (0, 1, 2, 3))
    h_r = RF.compute_prompt_hash("스프링 빈?", (0, 1, 2, 3))
    assert h_w == h_r


def test_hash_invariant_to_candidate_tier_order():
    h1 = RF.compute_prompt_hash("x", (0, 1, 2, 3))
    h2 = RF.compute_prompt_hash("x", (3, 0, 2, 1))
    assert h1 == h2


def test_hash_distinct_for_subset():
    h1 = RF.compute_prompt_hash("x", (0, 1, 2, 3))
    h2 = RF.compute_prompt_hash("x", (0, 1, 2))
    assert h1 != h2


# ---------------------------------------------------------------------------
# Happy path round-trip with the wrapper
# ---------------------------------------------------------------------------

def _valid_payload(prompt_hash: str, *, tier: int = 1, mode: str = "cheap") -> dict:
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


def test_read_decision_returns_typed_output(tmp_path):
    storage = tmp_path / "rf"
    storage.mkdir(parents=True, exist_ok=True)
    candidate_tiers = (0, 1, 2, 3)
    h = RF.compute_prompt_hash("스프링 빈?", candidate_tiers)
    (storage / f"{h}.output.json").write_text(
        json.dumps(_valid_payload(h)), encoding="utf-8",
    )

    out = RF.read_decision(
        "스프링 빈?", candidate_tiers,
        repo_root=tmp_path, storage=storage,
    )
    assert out is not None
    assert out.tier == 1
    assert out.mode == "cheap"
    assert out.confidence == 0.7
    assert "tier 1" in out.rationale


def test_round_trip_with_wrapper(tmp_path):
    storage = tmp_path / "rf"
    storage.mkdir(parents=True, exist_ok=True)
    candidate_tiers = (0, 1, 2, 3)

    in_path, out_path, h = W.write_input_artifact(
        prompt="MVCC가 격리수준이랑 무슨 관계?",
        heuristic_tier=1,
        heuristic_confidence=0.42,
        matched_tokens=["격리수준"],
        candidate_tiers=candidate_tiers,
        history_summary=None,
        out_root=storage,
    )
    assert in_path.exists()
    assert not out_path.exists()

    # AI fills the output
    out_path.write_text(json.dumps({
        "schema_id": "router-fallback-v1.output",
        "prompt_hash": h,
        "tier": 2,
        "mode": "full",
        "confidence": 0.8,
        "rationale": "도메인 토큰 + 비교 시그널 → tier 2",
        "scored_by": "ai_session",
        "produced_at": "2026-04-30T13:10:00+00:00",
    }), encoding="utf-8")

    decision = RF.read_decision(
        "MVCC가 격리수준이랑 무슨 관계?", candidate_tiers,
        repo_root=tmp_path, storage=storage,
    )
    assert decision is not None
    assert decision.tier == 2
    assert decision.mode == "full"


# ---------------------------------------------------------------------------
# Cache miss + corruption
# ---------------------------------------------------------------------------

def test_read_decision_returns_none_on_missing_file(tmp_path):
    out = RF.read_decision(
        "anything", (0, 1, 2, 3),
        repo_root=tmp_path, storage=tmp_path / "missing",
    )
    assert out is None


def test_read_decision_returns_none_on_corrupt_json(tmp_path):
    storage = tmp_path / "rf"
    storage.mkdir(parents=True, exist_ok=True)
    h = RF.compute_prompt_hash("x", (0, 1, 2, 3))
    (storage / f"{h}.output.json").write_text("garbage", encoding="utf-8")
    out = RF.read_decision(
        "x", (0, 1, 2, 3), repo_root=tmp_path, storage=storage,
    )
    assert out is None


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

@pytest.fixture
def storage(tmp_path):
    s = tmp_path / "rf"
    s.mkdir(parents=True, exist_ok=True)
    return s


def _write(storage, prompt, candidate_tiers, payload):
    h = RF.compute_prompt_hash(prompt, candidate_tiers)
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    return h


def test_validation_rejects_tier_outside_candidates(tmp_path, storage):
    candidate_tiers = (0, 1, 2)  # tier 3 blocked
    h = RF.compute_prompt_hash("x", candidate_tiers)
    payload = _valid_payload(h, tier=3, mode="coach")
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = RF.read_decision(
        "x", candidate_tiers, repo_root=tmp_path, storage=storage,
    )
    assert out is None


def test_validation_rejects_tier_mode_mismatch(tmp_path, storage):
    candidate_tiers = (0, 1, 2, 3)
    h = RF.compute_prompt_hash("x", candidate_tiers)
    payload = _valid_payload(h, tier=1, mode="full")  # tier 1 must be cheap
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = RF.read_decision(
        "x", candidate_tiers, repo_root=tmp_path, storage=storage,
    )
    assert out is None


def test_validation_rejects_unknown_mode(tmp_path, storage):
    candidate_tiers = (0, 1, 2, 3)
    h = RF.compute_prompt_hash("x", candidate_tiers)
    payload = _valid_payload(h)
    payload["mode"] = "deep"
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = RF.read_decision(
        "x", candidate_tiers, repo_root=tmp_path, storage=storage,
    )
    assert out is None


def test_validation_rejects_blank_rationale(tmp_path, storage):
    candidate_tiers = (0, 1, 2, 3)
    h = RF.compute_prompt_hash("x", candidate_tiers)
    payload = _valid_payload(h)
    payload["rationale"] = "   "
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = RF.read_decision(
        "x", candidate_tiers, repo_root=tmp_path, storage=storage,
    )
    assert out is None


def test_validation_rejects_wrong_scored_by(tmp_path, storage):
    candidate_tiers = (0, 1, 2, 3)
    h = RF.compute_prompt_hash("x", candidate_tiers)
    payload = _valid_payload(h)
    payload["scored_by"] = "human"
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = RF.read_decision(
        "x", candidate_tiers, repo_root=tmp_path, storage=storage,
    )
    assert out is None


# ---------------------------------------------------------------------------
# Errors API
# ---------------------------------------------------------------------------

def test_read_with_errors_surfaces_file_not_found(tmp_path):
    out, errors = RF.read_with_validation_errors(
        "x", (0, 1, 2, 3),
        repo_root=tmp_path, storage=tmp_path / "missing",
    )
    assert out is None
    assert errors == ["file_not_found"]


def test_read_with_errors_surfaces_validation_failures(tmp_path, storage):
    candidate_tiers = (0, 1, 2, 3)
    h = RF.compute_prompt_hash("x", candidate_tiers)
    payload = _valid_payload(h)
    payload["confidence"] = 1.5
    payload["scored_by"] = "human"
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out, errors = RF.read_with_validation_errors(
        "x", candidate_tiers, repo_root=tmp_path, storage=storage,
    )
    assert out is None
    assert len(errors) >= 2
