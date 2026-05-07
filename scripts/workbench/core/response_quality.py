"""Assistant response-quality telemetry.

This log is intentionally separate from ``state/learner/history.jsonl``:
history drives long-term learner personalization, while this module records
compact answer-quality evidence for later system improvement.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .learner_memory import _redact_text
from .memory import _append_with_lock
from .paths import learner_response_quality_path
from .schema_validation import validate_payload


SCHEMA_ID = "assistant-response-quality-v1"
MAX_EXCERPT_CHARS = 1000
DEFAULT_OVERLONG_THRESHOLD = 6000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_text(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()


def _normalize_path_list(paths: Iterable[str | dict] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in paths or []:
        if isinstance(item, dict):
            path = item.get("path")
        else:
            path = item
        if not path:
            continue
        value = str(path)
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _excerpt(text: str | None, *, max_chars: int = MAX_EXCERPT_CHARS) -> str:
    redacted = _redact_text(text or "") or ""
    if len(redacted) <= max_chars:
        return redacted
    return redacted[:max_chars].rstrip() + "..."


def _has_duplicate_text(response_text: str | None) -> bool:
    if not response_text:
        return False
    paragraphs = [
        re.sub(r"\s+", " ", part.strip())
        for part in re.split(r"\n\s*\n", response_text)
        if len(part.strip()) >= 80
    ]
    seen: set[str] = set()
    for paragraph in paragraphs:
        key = paragraph.lower()
        if key in seen:
            return True
        seen.add(key)
    sentences = [
        re.sub(r"\s+", " ", part.strip())
        for part in re.split(r"(?<=[.!?。])\s+|(?<=다\.)\s+", response_text)
        if len(part.strip()) >= 120
    ]
    seen.clear()
    for sentence in sentences:
        key = sentence.lower()
        if key in seen:
            return True
        seen.add(key)
    return False


def infer_quality_flags(
    *,
    response_text: str | None,
    citation_paths_expected: Iterable[str | dict] | None,
    citation_paths_declared: Iterable[str | dict] | None,
    base_flags: Iterable[str] | None = None,
    require_rag_header: bool = False,
    overlong_threshold: int = DEFAULT_OVERLONG_THRESHOLD,
) -> list[str]:
    flags = set(str(flag) for flag in (base_flags or []) if flag)
    expected = set(_normalize_path_list(citation_paths_expected))
    declared = set(_normalize_path_list(citation_paths_declared))
    if expected and not declared:
        flags.add("missing_citation")
    if expected and declared and expected.isdisjoint(declared):
        flags.add("citation_mismatch")
    if require_rag_header and response_text and not response_text.lstrip().startswith("[RAG:"):
        flags.add("missing_rag_header")
    if _has_duplicate_text(response_text):
        flags.add("duplicate_text")
    if response_text and len(response_text) > overlong_threshold:
        flags.add("overlong_answer")
    return sorted(flags)


def build_response_quality_row(
    *,
    source_event_id: str,
    turn_id: str | None,
    prompt: str | None,
    response_text: str | None,
    response_summary: str,
    citation_paths_expected: Iterable[str | dict] | None = None,
    citation_paths_declared: Iterable[str | dict] | None = None,
    quality_flags: Iterable[str] | None = None,
    contract_flags: Iterable[str] | None = None,
    answer_strategy: Iterable[str] | None = None,
    model_runtime: str | None = None,
    repo: str | None = None,
    note: str | None = None,
    require_rag_header: bool = False,
    now: datetime | None = None,
) -> dict:
    if not source_event_id:
        raise ValueError("source_event_id is required")
    if not response_summary or not response_summary.strip():
        raise ValueError("response_summary is required")
    expected = _normalize_path_list(citation_paths_expected)
    declared = _normalize_path_list(citation_paths_declared)
    redacted_prompt = _redact_text(prompt) if prompt is not None else None
    redacted_summary = _redact_text(response_summary) or ""
    flags = infer_quality_flags(
        response_text=response_text,
        citation_paths_expected=expected,
        citation_paths_declared=declared,
        base_flags=quality_flags,
        require_rag_header=require_rag_header,
    )
    row = {
        "schema_id": SCHEMA_ID,
        "logged_at": (now or datetime.now(timezone.utc)).isoformat(),
        "source_event_id": source_event_id,
        "turn_id": turn_id,
        "repo": repo or "",
        "model_runtime": model_runtime or "",
        "prompt": redacted_prompt,
        "prompt_hash": _hash_text(redacted_prompt),
        "response_summary": redacted_summary,
        "response_excerpt": _excerpt(response_text),
        "response_hash": _hash_text(response_text) if os.environ.get("WOOWA_RESPONSE_HASH_ENABLED", "1") != "0" else None,
        "response_length_chars": len(response_text or ""),
        "answer_strategy": [str(item) for item in (answer_strategy or []) if item],
        "citation_paths_expected": expected,
        "citation_paths_declared": declared,
        "quality_flags": flags,
        "contract_flags": [str(item) for item in (contract_flags or []) if item],
        "note": _redact_text(note) or "",
        "redaction_applied": True,
    }
    validate_payload("assistant-response-quality", row)
    return row


def resolve_log_paths(*, repo: str | None, repo_root: Path | None = None) -> list[Path]:
    paths = [learner_response_quality_path()]
    if repo and repo_root is not None:
        paths.append(repo_root / "state" / "repos" / repo / "logs" / "response_quality.jsonl")
    return paths


def append_response_quality(
    *,
    source_event_id: str,
    turn_id: str | None,
    prompt: str | None,
    response_text: str | None,
    response_summary: str,
    citation_paths_expected: Iterable[str | dict] | None = None,
    citation_paths_declared: Iterable[str | dict] | None = None,
    quality_flags: Iterable[str] | None = None,
    contract_flags: Iterable[str] | None = None,
    answer_strategy: Iterable[str] | None = None,
    model_runtime: str | None = None,
    repo: str | None = None,
    repo_root: Path | None = None,
    note: str | None = None,
    require_rag_header: bool = False,
    now: datetime | None = None,
) -> list[Path]:
    row = build_response_quality_row(
        source_event_id=source_event_id,
        turn_id=turn_id,
        prompt=prompt,
        response_text=response_text,
        response_summary=response_summary,
        citation_paths_expected=citation_paths_expected,
        citation_paths_declared=citation_paths_declared,
        quality_flags=quality_flags,
        contract_flags=contract_flags,
        answer_strategy=answer_strategy,
        model_runtime=model_runtime,
        repo=repo,
        note=note,
        require_rag_header=require_rag_header,
        now=now,
    )
    written: list[Path] = []
    for path in resolve_log_paths(repo=repo, repo_root=repo_root):
        path.parent.mkdir(parents=True, exist_ok=True)
        _append_with_lock(path, json.dumps(row, ensure_ascii=False) + "\n")
        written.append(path)
    return written


def iter_response_quality_rows(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if row.get("schema_id") == SCHEMA_ID:
                yield row


def summarize_quality_flags(rows: Iterable[dict]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in rows:
        for flag in row.get("quality_flags") or []:
            counts[flag] = counts.get(flag, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def citation_mismatch_candidates(rows: Iterable[dict]) -> list[tuple[str, str, str, int]]:
    counts: dict[tuple[str, str, str], int] = {}
    for row in rows:
        if "citation_mismatch" not in (row.get("quality_flags") or []):
            continue
        prompt = row.get("prompt") or ""
        expected = ", ".join(row.get("citation_paths_expected") or [])
        declared = ", ".join(row.get("citation_paths_declared") or [])
        key = (prompt, expected, declared)
        counts[key] = counts.get(key, 0) + 1
    return sorted(
        ((prompt, expected, declared, count) for (prompt, expected, declared), count in counts.items()),
        key=lambda item: (-item[3], item[0], item[1], item[2]),
    )
