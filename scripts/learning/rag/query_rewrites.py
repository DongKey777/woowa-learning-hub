"""Reader for query-rewrite-v1 output JSON (plan §P4.2).

The AI session writes its rewrite output to
``state/cs_rag/query_rewrites/<prompt_hash>.output.json`` after running
``bin/rag-rewrite-prepare``. This module is the consumer-side helper:
it computes the same prompt_hash the wrapper uses, reads the output
file when present, validates it against the form rules in
``docs/ai-behavior-contracts.md`` § query-rewrite-v1, and returns a
typed ``RewriteOutput`` (or None on miss / corruption).

The retriever can then treat the rewrites as additional dense queries
(P5.7+ wiring lives outside this module). When the file is missing or
fails validation, the caller falls back to PRF (``prf.rm3_expand``) or
the original query alone.

Pure read path — never writes. The wrapper
(``cli_rag_rewrite_prepare.py``) owns the input artifact; the AI
session owns the output artifact; this module only reads.

Tested in ``tests/unit/test_query_rewrites_reader.py``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


SCHEMA_ID_OUTPUT = "query-rewrite-v1.output"
DEFAULT_STORAGE_REL = Path("state") / "cs_rag" / "query_rewrites"


@dataclass(frozen=True)
class Rewrite:
    text: str
    rationale: str


@dataclass(frozen=True)
class RewriteOutput:
    prompt_hash: str
    rewrites: tuple[Rewrite, ...]
    confidence: float
    scored_by: str
    produced_at: str

    @property
    def texts(self) -> tuple[str, ...]:
        return tuple(r.text for r in self.rewrites)


# ---------------------------------------------------------------------------
# Hashing — must match cli_rag_rewrite_prepare.compute_prompt_hash
# ---------------------------------------------------------------------------

def compute_prompt_hash(prompt: str, mode: str) -> str:
    """Mirror of ``cli_rag_rewrite_prepare.compute_prompt_hash``.

    The reader needs the same hash to find the file the wrapper wrote.
    Imported instead of duplicated when running inside the same
    process; this fallback is here so the reader can stand alone.
    """
    norm = prompt.strip()
    payload = f"{mode}\x1f{norm}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def output_path_for(
    prompt: str,
    mode: str,
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> Path:
    """Resolve the expected output path for a (prompt, mode) pair."""
    h = compute_prompt_hash(prompt, mode)
    base = storage or (repo_root / DEFAULT_STORAGE_REL)
    return base / f"{h}.output.json"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_payload(payload: dict, *, expected_prompt_hash: str) -> list[str]:
    """Mirror of the rule list in
    ``docs/ai-behavior-contracts.md`` § query-rewrite-v1. Returns a
    list of violation messages (empty list = valid)."""
    errors: list[str] = []
    if payload.get("schema_id") != SCHEMA_ID_OUTPUT:
        errors.append("schema_id mismatch")
    if payload.get("prompt_hash") != expected_prompt_hash:
        errors.append("prompt_hash does not match")
    rewrites = payload.get("rewrites")
    if not isinstance(rewrites, list) or not (1 <= len(rewrites) <= 3):
        errors.append("rewrites must be list of length 1..3")
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


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------

def read_rewrites(
    prompt: str,
    mode: str,
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> RewriteOutput | None:
    """Read + validate the rewrite output for ``(prompt, mode)``.

    Returns None when:
    - the file does not exist (AI hasn't written; cache miss)
    - the JSON fails to parse (corrupt file)
    - the payload fails form validation (contract violation)

    The caller treats None as "use PRF / original query". The reader
    intentionally does NOT raise on validation failure — that would
    make a transient AI mis-write break the search path.
    """
    path = output_path_for(prompt, mode, repo_root=repo_root, storage=storage)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    expected_hash = compute_prompt_hash(prompt, mode)
    errors = _validate_payload(payload, expected_prompt_hash=expected_hash)
    if errors:
        return None

    rewrites = tuple(
        Rewrite(text=r["text"].strip(), rationale=r["rationale"].strip())
        for r in payload["rewrites"]
    )
    return RewriteOutput(
        prompt_hash=payload["prompt_hash"],
        rewrites=rewrites,
        confidence=float(payload["confidence"]),
        scored_by=payload["scored_by"],
        produced_at=payload["produced_at"],
    )


def read_with_validation_errors(
    prompt: str,
    mode: str,
    *,
    repo_root: Path,
    storage: Path | None = None,
) -> tuple[RewriteOutput | None, list[str]]:
    """Like ``read_rewrites`` but also returns the validation error
    list. Useful for the routing log / debugging when an AI write was
    expected but came back malformed."""
    path = output_path_for(prompt, mode, repo_root=repo_root, storage=storage)
    if not path.exists():
        return None, ["file_not_found"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"json_decode_error: {exc}"]
    if not isinstance(payload, dict):
        return None, ["payload_not_object"]
    expected_hash = compute_prompt_hash(prompt, mode)
    errors = _validate_payload(payload, expected_prompt_hash=expected_hash)
    if errors:
        return None, errors
    rewrites = tuple(
        Rewrite(text=r["text"].strip(), rationale=r["rationale"].strip())
        for r in payload["rewrites"]
    )
    return RewriteOutput(
        prompt_hash=payload["prompt_hash"],
        rewrites=rewrites,
        confidence=float(payload["confidence"]),
        scored_by=payload["scored_by"],
        produced_at=payload["produced_at"],
    ), []
