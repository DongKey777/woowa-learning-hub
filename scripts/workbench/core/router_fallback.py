"""Reader for router-fallback-v1 output JSON (plan §P4.4 consumer side).

When the heuristic Tier classifier's confidence is low (see
``scripts/workbench/core/routing_confidence.py``), the AI session
runs ``bin/rag-route-fallback`` and writes its tier choice to
``state/cs_rag/router_fallback/<prompt_hash>.output.json``. This
module is the consumer-side helper: it reads the file, validates it
against the form rules in ``docs/ai-behavior-contracts.md`` §
router-fallback-v1, and returns a typed ``RouterFallbackOutput`` (or
None on miss / corruption / contract violation).

Pure read path. Same fail-soft contract as ``query_rewrites.py`` —
None on any failure so the caller falls back to the heuristic raw
decision (with ``ai_unavailable=true`` recorded in the routing log).

Tested in ``tests/unit/test_router_fallback_reader.py``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


SCHEMA_ID_OUTPUT = "router-fallback-v1.output"
DEFAULT_STORAGE_REL = Path("state") / "cs_rag" / "router_fallback"

# Tier ↔ mode pairing (hard contract — see Skill step 4)
VALID_TIER_MODE = {0: "skip", 1: "cheap", 2: "full", 3: "coach"}
VALID_MODES = frozenset({"skip", "cheap", "full", "coach"})


@dataclass(frozen=True)
class RouterFallbackOutput:
    prompt_hash: str
    tier: int
    mode: str
    confidence: float
    rationale: str
    scored_by: str
    produced_at: str


# ---------------------------------------------------------------------------
# Hashing — must match cli_rag_route_fallback.compute_prompt_hash
# ---------------------------------------------------------------------------

def compute_prompt_hash(prompt: str, candidate_tiers: tuple[int, ...]) -> str:
    """Mirror of ``cli_rag_route_fallback.compute_prompt_hash``.

    Same wire format as the wrapper: candidate_tiers sorted + joined
    by comma, then ``\\x1f``, then trimmed prompt. Reader must
    reproduce this exactly to find the file the wrapper wrote.
    """
    norm = prompt.strip()
    tiers = ",".join(str(t) for t in sorted(set(candidate_tiers)))
    payload = f"{tiers}\x1f{norm}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def output_path_for(
    prompt: str,
    candidate_tiers: tuple[int, ...],
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> Path:
    h = compute_prompt_hash(prompt, candidate_tiers)
    base = storage or (repo_root / DEFAULT_STORAGE_REL)
    return base / f"{h}.output.json"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_payload(
    payload: dict,
    *,
    expected_prompt_hash: str,
    candidate_tiers: tuple[int, ...],
) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_id") != SCHEMA_ID_OUTPUT:
        errors.append("schema_id mismatch")
    if payload.get("prompt_hash") != expected_prompt_hash:
        errors.append("prompt_hash does not match input")
    tier = payload.get("tier")
    if tier not in candidate_tiers:
        errors.append(f"tier {tier!r} not in candidate_tiers {candidate_tiers}")
    mode = payload.get("mode")
    if mode not in VALID_MODES:
        errors.append("mode out of enum")
    expected_mode = VALID_TIER_MODE.get(tier)
    if expected_mode and mode != expected_mode:
        errors.append(f"tier {tier} requires mode '{expected_mode}', got {mode!r}")
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


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------

def read_decision(
    prompt: str,
    candidate_tiers: tuple[int, ...],
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> RouterFallbackOutput | None:
    """Read + validate the AI router fallback output for
    ``(prompt, candidate_tiers)``.

    Returns None when:
    - the file does not exist (AI hasn't written; cache miss)
    - the JSON fails to parse (corrupt file)
    - the payload fails form validation (contract violation)

    The caller treats None as "AI unavailable" and records
    ``ai_unavailable=true`` in the routing log.
    """
    path = output_path_for(prompt, candidate_tiers, repo_root=repo_root, storage=storage)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    expected_hash = compute_prompt_hash(prompt, candidate_tiers)
    errors = _validate_payload(
        payload,
        expected_prompt_hash=expected_hash,
        candidate_tiers=tuple(sorted(set(candidate_tiers))),
    )
    if errors:
        return None
    return RouterFallbackOutput(
        prompt_hash=payload["prompt_hash"],
        tier=int(payload["tier"]),
        mode=payload["mode"],
        confidence=float(payload["confidence"]),
        rationale=payload["rationale"].strip(),
        scored_by=payload["scored_by"],
        produced_at=payload["produced_at"],
    )


def read_with_validation_errors(
    prompt: str,
    candidate_tiers: tuple[int, ...],
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> tuple[RouterFallbackOutput | None, list[str]]:
    """Like ``read_decision`` but also returns the validation error
    list. Useful for debug routing log entries when the AI was
    expected but produced a malformed output."""
    path = output_path_for(prompt, candidate_tiers, repo_root=repo_root, storage=storage)
    if not path.exists():
        return None, ["file_not_found"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"json_decode_error: {exc}"]
    if not isinstance(payload, dict):
        return None, ["payload_not_object"]
    expected_hash = compute_prompt_hash(prompt, candidate_tiers)
    errors = _validate_payload(
        payload,
        expected_prompt_hash=expected_hash,
        candidate_tiers=tuple(sorted(set(candidate_tiers))),
    )
    if errors:
        return None, errors
    return RouterFallbackOutput(
        prompt_hash=payload["prompt_hash"],
        tier=int(payload["tier"]),
        mode=payload["mode"],
        confidence=float(payload["confidence"]),
        rationale=payload["rationale"].strip(),
        scored_by=payload["scored_by"],
        produced_at=payload["produced_at"],
    ), []
