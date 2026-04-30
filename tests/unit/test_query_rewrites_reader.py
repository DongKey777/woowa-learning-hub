"""Tests for the query-rewrite-v1 output reader (P4.2 consumer side)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.learning.rag import query_rewrites as Q
from scripts.learning import cli_rag_rewrite_prepare as W


# ---------------------------------------------------------------------------
# Hash compatibility with the wrapper
# ---------------------------------------------------------------------------

def test_hash_matches_wrapper_implementation():
    """Reader and wrapper must compute the same prompt_hash so the
    reader can find what the wrapper wrote."""
    h_w = W.compute_prompt_hash("스프링 빈?", "normalize")
    h_r = Q.compute_prompt_hash("스프링 빈?", "normalize")
    assert h_w == h_r


def test_output_path_matches_wrapper_layout(tmp_path):
    storage = tmp_path / "rw"
    p_reader = Q.output_path_for("MVCC?", "hyde", repo_root=tmp_path, storage=storage)
    # The wrapper writes <prompt_hash>.output.json in the storage root
    assert p_reader.name.endswith(".output.json")
    assert p_reader.parent == storage


# ---------------------------------------------------------------------------
# read_rewrites: happy path
# ---------------------------------------------------------------------------

def _valid_payload(prompt_hash: str) -> dict:
    return {
        "schema_id": "query-rewrite-v1.output",
        "prompt_hash": prompt_hash,
        "rewrites": [
            {"text": "스프링 빈의 정의", "rationale": "조사 제거"},
            {"text": "spring bean lifecycle", "rationale": "영문 dense에 친화적"},
        ],
        "confidence": 0.7,
        "scored_by": "ai_session",
        "produced_at": "2026-04-30T12:00:00+00:00",
    }


def test_read_rewrites_returns_typed_output(tmp_path):
    storage = tmp_path / "rw"
    storage.mkdir(parents=True, exist_ok=True)
    h = Q.compute_prompt_hash("스프링 빈 뭐야?", "normalize")
    (storage / f"{h}.output.json").write_text(
        json.dumps(_valid_payload(h)), encoding="utf-8",
    )

    out = Q.read_rewrites(
        "스프링 빈 뭐야?", "normalize", repo_root=tmp_path, storage=storage,
    )
    assert out is not None
    assert out.prompt_hash == h
    assert len(out.rewrites) == 2
    assert out.rewrites[0].text == "스프링 빈의 정의"
    assert out.rewrites[1].rationale == "영문 dense에 친화적"
    assert out.confidence == 0.7
    assert out.texts == ("스프링 빈의 정의", "spring bean lifecycle")


# ---------------------------------------------------------------------------
# Cache miss + corruption resilience
# ---------------------------------------------------------------------------

def test_read_rewrites_returns_none_on_missing_file(tmp_path):
    out = Q.read_rewrites(
        "anything", "hyde", repo_root=tmp_path, storage=tmp_path / "missing",
    )
    assert out is None


def test_read_rewrites_returns_none_on_corrupt_json(tmp_path):
    storage = tmp_path / "rw"
    storage.mkdir(parents=True, exist_ok=True)
    h = Q.compute_prompt_hash("x", "hyde")
    (storage / f"{h}.output.json").write_text("not valid json", encoding="utf-8")

    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


def test_read_rewrites_returns_none_on_payload_array(tmp_path):
    """Top-level JSON arrays are valid JSON but not the contract shape."""
    storage = tmp_path / "rw"
    storage.mkdir(parents=True, exist_ok=True)
    h = Q.compute_prompt_hash("x", "hyde")
    (storage / f"{h}.output.json").write_text("[1, 2, 3]", encoding="utf-8")

    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


# ---------------------------------------------------------------------------
# Schema validation (mirrors wrapper-side rules)
# ---------------------------------------------------------------------------

@pytest.fixture
def storage(tmp_path):
    s = tmp_path / "rw"
    s.mkdir(parents=True, exist_ok=True)
    return s


def _write_payload(storage: Path, prompt: str, mode: str, payload: dict) -> str:
    h = Q.compute_prompt_hash(prompt, mode)
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8",
    )
    return h


def test_validation_rejects_wrong_schema_id(tmp_path, storage):
    payload = _valid_payload("placeholder")
    h = _write_payload(storage, "x", "hyde", payload)
    payload["schema_id"] = "different-schema"
    payload["prompt_hash"] = h
    storage_path = storage
    (storage_path / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_mismatched_prompt_hash(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    payload = _valid_payload("zzzz")  # wrong hash
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_zero_rewrites(tmp_path, storage):
    h = _write_payload(storage, "x", "hyde", _valid_payload("placeholder"))
    payload = _valid_payload(h)
    payload["rewrites"] = []
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_more_than_three_rewrites(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    payload = _valid_payload(h)
    payload["rewrites"] = [{"text": str(i), "rationale": "r"} for i in range(4)]
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_blank_text_or_rationale(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    payload = _valid_payload(h)
    payload["rewrites"] = [{"text": "  ", "rationale": "r"}]
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_confidence_out_of_range(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    payload = _valid_payload(h)
    payload["confidence"] = 1.5
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


def test_validation_rejects_wrong_scored_by(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    payload = _valid_payload(h)
    payload["scored_by"] = "human"
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out = Q.read_rewrites("x", "hyde", repo_root=tmp_path, storage=storage)
    assert out is None


# ---------------------------------------------------------------------------
# read_with_validation_errors — surfaces *why* it failed
# ---------------------------------------------------------------------------

def test_read_with_errors_surfaces_file_not_found(tmp_path):
    out, errors = Q.read_with_validation_errors(
        "missing", "hyde", repo_root=tmp_path, storage=tmp_path / "nope",
    )
    assert out is None
    assert errors == ["file_not_found"]


def test_read_with_errors_surfaces_json_decode_error(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    (storage / f"{h}.output.json").write_text("garbage", encoding="utf-8")
    out, errors = Q.read_with_validation_errors(
        "x", "hyde", repo_root=tmp_path, storage=storage,
    )
    assert out is None
    assert any("json_decode_error" in e for e in errors)


def test_read_with_errors_surfaces_validation_failures(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    payload = _valid_payload(h)
    payload["confidence"] = -1
    payload["scored_by"] = "human"
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out, errors = Q.read_with_validation_errors(
        "x", "hyde", repo_root=tmp_path, storage=storage,
    )
    assert out is None
    assert len(errors) >= 2  # both confidence + scored_by violations


def test_read_with_errors_returns_typed_output_when_valid(tmp_path, storage):
    h = Q.compute_prompt_hash("x", "hyde")
    payload = _valid_payload(h)
    (storage / f"{h}.output.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )
    out, errors = Q.read_with_validation_errors(
        "x", "hyde", repo_root=tmp_path, storage=storage,
    )
    assert errors == []
    assert out is not None
    assert out.prompt_hash == h


# ---------------------------------------------------------------------------
# Round-trip: wrapper writes input → AI writes output → reader picks up
# ---------------------------------------------------------------------------

def test_round_trip_with_wrapper(tmp_path, storage):
    """End-to-end: simulate the wrapper writing input, the AI session
    writing output, then the reader picking up the rewrites."""
    # Step 1: wrapper writes input artifact
    in_path, out_path, h = W.write_input_artifact(
        prompt="MVCC가 격리수준이랑 무슨 관계?",
        mode="hyde",
        learner_context={"experience_level": "intermediate"},
        out_root=storage,
    )
    assert in_path.exists()
    assert not out_path.exists()

    # Step 2: AI session "writes" the output
    ai_payload = {
        "schema_id": "query-rewrite-v1.output",
        "prompt_hash": h,
        "rewrites": [
            {
                "text": "MVCC는 격리수준 구현 방식 중 하나이며, 스냅샷을 통해 일관된 읽기를 제공한다",
                "rationale": "hyde 가설 답변 — 도메인 키워드를 포함",
            },
        ],
        "confidence": 0.6,
        "scored_by": "ai_session",
        "produced_at": "2026-04-30T12:30:00+00:00",
    }
    out_path.write_text(json.dumps(ai_payload, ensure_ascii=False), encoding="utf-8")

    # Step 3: reader picks it up
    out = Q.read_rewrites(
        "MVCC가 격리수준이랑 무슨 관계?", "hyde",
        repo_root=tmp_path, storage=storage,
    )
    assert out is not None
    assert out.prompt_hash == h
    assert len(out.rewrites) == 1
    assert "MVCC" in out.rewrites[0].text
