"""Single-source-of-truth memory for the learner across all activities.

History stream: `state/learner/history.jsonl` — append-only event log with
five `event_type`s (rag_ask, coach_run, drill_answer, test_result,
code_attempt).

Profile: `state/learner/profile.json` — derived view (rolling experience
level, concept mastery/uncertainty/encounter counts, activity stats, next
recommendations). Always re-derivable from the history stream.

Validation strategy (peer AI #2): the `learner-event.schema.json` is a
*flat* schema — common required fields only. Per-event-type required
fields are enforced by `validate_learner_event()` here in Python because
`schema_validation._validate` does not handle JSON-Schema `oneOf`. The
dispatch table sits next to the call site so changes stay visible.

Reuses `memory.py` primitives:
  * `_append_with_lock(path, line: str)` for atomic JSONL append (caller
    must serialize and add a newline)
  * `_atomic_write(path, content: str)` for tempfile+rename writes
  * `_question_fingerprint` for prompt normalization
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .concept_catalog import (
    extract_concept_ids,
    infer_concepts_from_path,
    infer_concepts_from_test,
    lp_to_concept_id,
)
from .memory import _append_with_lock, _atomic_write, _question_fingerprint
from .paths import (
    ensure_learner_layout,
    learner_history_path,
    learner_identity_path,
    learner_profile_path,
    learner_summary_path,
    LEARNER_DIR,
)
from .schema_validation import validate_payload

LEARNER_PROFILE_SCHEMA_VERSION = "v3"
HISTORY_ROLLING_WINDOW = 200

# === Type-specific required fields enforced by Python dispatch ============
EVENT_REQUIRED_FIELDS: dict[str, list[str]] = {
    "rag_ask": ["prompt", "tier", "rag_mode", "concept_ids", "blocked"],
    "coach_run": [
        "pr_number",
        "primary_learning_points",
        "concept_ids",
        "had_negative_feedback",
    ],
    "drill_answer": [
        "drill_session_id",
        "linked_learning_point",
        "total_score",
        "concept_ids",
    ],
    "test_result": ["module", "test_class", "test_method", "pass", "concept_ids"],
    "code_attempt": ["file_path", "diff_summary", "concept_ids"],
}

VALID_EVENT_TYPES = frozenset(EVENT_REQUIRED_FIELDS)


# === Privacy redaction ====================================================
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
)
_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{16,}|"
    r"gho_[A-Za-z0-9]{16,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"AKIA[0-9A-Z]{12,}|Bearer\s+[A-Za-z0-9_\-\.=]+)"
)
_PASSWORD_RE = re.compile(
    r"(?i)(password|passwd|secret|api[_\-]?key)\s*[:=]\s*[^\s,;]+",
)
_REDACTED = "***REDACTED***"


def _redact_text(text: str | None) -> str | None:
    if not text:
        return text
    redacted = _PASSWORD_RE.sub(lambda m: f"{m.group(1)}={_REDACTED}", text)
    redacted = _TOKEN_RE.sub(_REDACTED, redacted)
    redacted = _EMAIL_RE.sub(_REDACTED, redacted)
    return redacted


def _redact_stack_trace(stack: str | None, *, max_lines: int = 5) -> str | None:
    if not stack:
        return None
    lines = stack.splitlines()[:max_lines]
    return _redact_text("\n".join(lines))


def _redact_diff(summary: str | None, *, max_chars: int = 500) -> str | None:
    redacted = _redact_text(summary)
    if redacted and len(redacted) > max_chars:
        return redacted[:max_chars] + "..."
    return redacted


# === Identity =============================================================
def _git_config_email() -> str | None:
    try:
        output = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        value = (output.stdout or "").strip()
        return value or None
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def _gh_api_login() -> str | None:
    try:
        output = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        value = (output.stdout or "").strip()
        return value or None
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def _resolve_learner_id() -> str:
    """Resolve learner_id with cache.

    Priority: identity.json → WOOWA_LEARNER_ID → git config user.email →
    `gh api user --jq .login` → "default". The first successful resolution
    is cached in `state/learner/identity.json` so subsequent calls do not
    shell out.
    """
    ensure_learner_layout()
    cache_path = learner_identity_path()
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            value = cached.get("learner_id")
            if value:
                return value
        except (json.JSONDecodeError, OSError):
            pass
    learner_id = os.environ.get("WOOWA_LEARNER_ID") or ""
    if not learner_id:
        learner_id = _git_config_email() or _gh_api_login() or "default"
    try:
        _atomic_write(
            cache_path,
            json.dumps({"learner_id": learner_id}, ensure_ascii=False) + "\n",
        )
    except OSError:
        pass
    return learner_id


# === Time + identity helpers =============================================
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _within(ts: str | None, *, days: int) -> bool:
    parsed = _parse_iso(ts)
    if parsed is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return parsed >= cutoff


def _deterministic_event_id(event: dict) -> str:
    """SHA1 over (event_type, ts, identifying field). Stable across reruns
    so migration can dedupe legacy entries."""
    keys = [event.get("event_type", ""), event.get("ts", "")]
    keys.append(
        event.get("prompt")
        or str(event.get("pr_number") or "")
        or event.get("drill_session_id")
        or event.get("file_path")
        or f"{event.get('test_class', '')}.{event.get('test_method', '')}"
        or ""
    )
    digest = hashlib.sha1("|".join(keys).encode("utf-8")).hexdigest()
    return digest[:16]


# === Schema validation ====================================================
def validate_learner_event(event: dict) -> None:
    """Per-event-type required-field enforcement.

    Always called by `append_learner_event` before disk write, so callers
    cannot accidentally pollute the stream by skipping it.
    """
    common = ["event_type", "event_id", "ts", "learner_id"]
    for field in common:
        if field not in event:
            raise ValueError(f"missing required common field: {field}")
    et = event.get("event_type")
    if et not in VALID_EVENT_TYPES:
        raise ValueError(f"unknown event_type: {et!r}")
    for field in EVENT_REQUIRED_FIELDS[et]:
        if field not in event:
            raise ValueError(f"missing required field for {et}: {field}")
    # Lightweight JSON Schema check — flat schema only validates
    # common+optional types, not the per-type required map.
    try:
        validate_payload("learner-event", event)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"learner-event schema validation failed: {exc}") from exc


# === Append / read ========================================================
def append_learner_event(event: dict[str, Any]) -> dict:
    """Append `event` to history.jsonl with fcntl lock + schema validation.

    Mutates `event` to ensure `ts`, `event_id` are populated. Returns the
    finalized event.
    """
    ensure_learner_layout()
    if "ts" not in event:
        event["ts"] = _now_iso()
    if "event_id" not in event:
        event["event_id"] = _deterministic_event_id(event)
    validate_learner_event(event)
    line = json.dumps(event, ensure_ascii=False) + "\n"
    _append_with_lock(learner_history_path(), line)
    return event


def _load_history(*, limit: int | None = None) -> list[dict]:
    """Read history.jsonl. Tolerates corrupted lines (skips silently).

    `limit=None` reads the full file; an int reads the last N entries
    (rolling window for cheap recompute)."""
    path = learner_history_path()
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            out.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    if limit is not None and len(out) > limit:
        return out[-limit:]
    return out


def load_learner_profile() -> dict | None:
    """Return profile.json, recomputing lazily when history is newer.

    Returns None when there is no history at all (cold-start case).
    """
    history_path = learner_history_path()
    profile_path = learner_profile_path()
    if not history_path.exists() or history_path.stat().st_size == 0:
        return None
    if (
        not profile_path.exists()
        or history_path.stat().st_mtime > profile_path.stat().st_mtime
    ):
        return recompute_learner_profile()
    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return recompute_learner_profile()


def recompute_learner_profile() -> dict:
    """Rebuild summary + profile from the current history stream."""
    ensure_learner_layout()
    history = _load_history()
    summary = _summarize_learner_history(history)
    profile = _build_learner_profile(history, summary)
    _atomic_write(
        learner_summary_path(),
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    )
    _atomic_write(
        learner_profile_path(),
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
    )
    return profile


def clear_learner_state() -> dict:
    """Privacy reset — wipe the entire `state/learner/` directory."""
    deleted: list[str] = []
    if LEARNER_DIR.exists():
        for child in sorted(LEARNER_DIR.iterdir()):
            try:
                if child.is_file():
                    child.unlink()
                else:
                    for sub in child.rglob("*"):
                        if sub.is_file():
                            sub.unlink()
                    child.rmdir()
                deleted.append(child.name)
            except OSError:
                pass
    return {"cleared": deleted}


def redact_substring(needle: str) -> dict:
    """Drop every history entry containing `needle`. Returns counts."""
    if not needle:
        return {"removed": 0, "kept": 0}
    path = learner_history_path()
    if not path.exists():
        return {"removed": 0, "kept": 0}
    kept_lines: list[str] = []
    removed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if needle in line:
            removed += 1
            continue
        kept_lines.append(line)
    _atomic_write(path, "\n".join(kept_lines) + ("\n" if kept_lines else ""))
    recompute_learner_profile()
    return {"removed": removed, "kept": len(kept_lines)}


# === Event builders =======================================================
def build_rag_ask_event(
    *,
    prompt: str,
    tier: int,
    mode: str | None,
    experience_level: str | None,
    rag_result: dict | None,
    repo: str | None,
    module: str | None,
    learner_id: str,
    blocked: bool,
    catalog: dict,
) -> dict:
    redacted_prompt = _redact_text(prompt) or ""
    return {
        "event_type": "rag_ask",
        "ts": _now_iso(),
        "learner_id": learner_id,
        "repo_context": repo,
        "module_context": module,
        "concept_ids": extract_concept_ids(prompt, catalog),
        "prompt": redacted_prompt,
        "question_fingerprint": _question_fingerprint(redacted_prompt),
        "tier": int(tier),
        "rag_mode": mode,
        "experience_level_inferred": experience_level,
        "category_hits": _extract_categories(rag_result),
        "top_paths": _extract_top_paths(rag_result),
        "rag_ready": _extract_rag_ready(rag_result),
        "blocked": bool(blocked),
    }


def build_coach_run_event(
    *,
    session_payload: dict,
    learner_id: str,
    catalog: dict,
) -> dict:
    # Real session payloads only carry `learning_point_recommendations` (see
    # scripts/workbench/core/session.py). Some fixtures and direct-API
    # callers pass `primary_learning_points` instead — accept both so PR
    # coach events actually populate concept_ids in production.
    learning_points = list(session_payload.get("primary_learning_points") or [])
    if not learning_points:
        learning_points = [
            item.get("learning_point")
            for item in session_payload.get("learning_point_recommendations") or []
            if isinstance(item, dict) and item.get("learning_point")
        ]
    concept_ids = []
    for lp in learning_points:
        cid = lp_to_concept_id(lp, catalog)
        if cid:
            concept_ids.append(cid)
    response = session_payload.get("response") or {}
    current_pr = session_payload.get("current_pr") or {}
    pr_number = current_pr.get("number") or session_payload.get("pr_number")
    return {
        "event_type": "coach_run",
        "ts": _now_iso(),
        "learner_id": learner_id,
        "repo_context": session_payload.get("repo"),
        "module_context": None,
        "pr_number": pr_number,
        "concept_ids": sorted(set(concept_ids)),
        "had_negative_feedback": _detect_negative_feedback(session_payload),
        "prompt": _redact_text(session_payload.get("prompt")),
        "primary_learning_points": learning_points,
        "learning_point_recommendations": _coach_recommendation_digest(
            session_payload
        ),
        "summary": response.get("summary") or session_payload.get("summary"),
        "answer": response.get("answer") or session_payload.get("answer"),
        "follow_up_question": response.get("follow_up_question")
        or session_payload.get("follow_up_question"),
    }


def build_drill_answer_event(
    *,
    drill_record: dict,
    learner_id: str,
    repo: str | None,
    catalog: dict,
) -> dict:
    lp = drill_record.get("linked_learning_point")
    concept_id = lp_to_concept_id(lp, catalog) if lp else None
    return {
        "event_type": "drill_answer",
        "ts": drill_record.get("scored_at") or _now_iso(),
        "learner_id": learner_id,
        "repo_context": repo,
        "module_context": None,
        "concept_ids": [concept_id] if concept_id else [],
        "drill_session_id": drill_record.get("drill_session_id"),
        "linked_learning_point": lp,
        "total_score": drill_record.get("total_score"),
        "dimensions": drill_record.get("dimensions") or {},
        "weak_tags": drill_record.get("weak_tags") or [],
    }


def build_test_result_event(
    *,
    junit_test: dict,
    learner_id: str,
    module: str | None,
    catalog: dict,
) -> dict:
    test_class = junit_test.get("class") or ""
    test_method = junit_test.get("name") or ""
    failure = junit_test.get("failure")
    passed = failure is None
    stack = (failure or {}).get("stack_trace") if isinstance(failure, dict) else None
    message = (failure or {}).get("message") if isinstance(failure, dict) else None
    concept_ids, concept_match_mode = infer_concepts_from_test(
        test_class, test_method, module, catalog
    )
    return {
        "event_type": "test_result",
        "ts": _now_iso(),
        "learner_id": learner_id,
        "repo_context": None,
        "module_context": module,
        "concept_ids": concept_ids,
        "concept_match_mode": concept_match_mode,
        "module": module or "",
        "test_class": test_class,
        "test_method": test_method,
        "pass": passed,
        "duration_ms": junit_test.get("duration_ms"),
        "failure_message": _redact_text(message) if not passed else None,
        "stack_trace_excerpt": _redact_stack_trace(stack) if not passed else None,
    }


def build_code_attempt_event(
    *,
    file_path: str,
    diff_summary: str,
    lines_added: int,
    lines_removed: int,
    linked_test: str | None,
    learner_id: str,
    module: str | None,
    catalog: dict,
) -> dict:
    return {
        "event_type": "code_attempt",
        "ts": _now_iso(),
        "learner_id": learner_id,
        "repo_context": None,
        "module_context": module,
        "concept_ids": infer_concepts_from_path(file_path, module, catalog),
        "file_path": file_path,
        "diff_summary": _redact_diff(diff_summary) or "",
        "lines_added": int(lines_added or 0),
        "lines_removed": int(lines_removed or 0),
        "linked_test": linked_test,
    }


# === Internal helpers for builders =======================================
def _extract_categories(rag_result: dict | None) -> list[str]:
    if not isinstance(rag_result, dict):
        return []
    if "error" in rag_result:
        return []
    meta = rag_result.get("meta") or {}
    cats = meta.get("cs_categories_hit")
    if isinstance(cats, list):
        return [str(c) for c in cats][:8]
    bucket = rag_result.get("by_fallback_key") or {}
    seen: list[str] = []
    if isinstance(bucket, dict):
        for hits in bucket.values():
            if not isinstance(hits, list):
                continue
            for hit in hits:
                cat = (hit or {}).get("category")
                if cat and cat not in seen:
                    seen.append(cat)
    return seen[:8]


def _extract_top_paths(rag_result: dict | None) -> list[str]:
    if not isinstance(rag_result, dict) or "error" in rag_result:
        return []
    bucket = rag_result.get("by_fallback_key") or rag_result.get("by_learning_point") or {}
    paths: list[str] = []
    if isinstance(bucket, dict):
        for hits in bucket.values():
            if not isinstance(hits, list):
                continue
            for hit in hits:
                p = (hit or {}).get("path")
                if p and p not in paths:
                    paths.append(p)
    return paths[:6]


def _extract_rag_ready(rag_result: dict | None) -> bool:
    if not isinstance(rag_result, dict):
        return False
    if "error" in rag_result:
        return False
    return bool((rag_result.get("meta") or {}).get("rag_ready", True))


def _coach_recommendation_digest(session_payload: dict) -> list[dict]:
    out: list[dict] = []
    for item in (session_payload.get("learning_point_recommendations") or [])[:5]:
        primary = (item or {}).get("primary_candidate") or {}
        out.append(
            {
                "learning_point": item.get("learning_point"),
                "label": item.get("label"),
                "primary_candidate_pr": primary.get("pr_number"),
            }
        )
    return out


_NEGATIVE_PHRASES = (
    "rejected", "needs_changes", "needs changes",
    "다시 봐", "수정 필요", "재요청", "rework",
    "request changes", "request_changes",
)


def _detect_negative_feedback(session_payload: dict) -> bool:
    """Best-effort signal: did the mentor flag this PR for changes?

    Real session payloads keep review state nested under `current_pr` and
    `pr_report_evidence`. The exact shape comes from
    `scripts/workbench/core/packets.py` and `thread_builder.py`:

      * mentor comments use `body_excerpt` (not `body`) — see `_comment_sample`
      * threads live under `thread_samples` (not `review_threads`),
        with bodies at `participants[*].body_excerpt`
      * `review_summary.changes_requested_count > 0` is a strong count signal

    Some fixtures still pass flat top-level fields (`review_state`,
    `mentor_verdict`, etc.) — we sweep both shapes so prod and tests align.
    False by default; mastery only flips to True on a positive signal so a
    silent miss here keeps the system conservative, not over-eager.
    """
    current_pr = session_payload.get("current_pr") or {}
    evidence = session_payload.get("pr_report_evidence") or {}

    # 1) Flat / nested decision strings.
    flat_sources = [
        session_payload.get("mentor_verdict"),
        session_payload.get("review_state"),
        session_payload.get("review_decision"),
        current_pr.get("review_decision"),
        current_pr.get("review_state"),
        current_pr.get("merge_state_status"),
        evidence.get("review_decision"),
    ]
    flat = " ".join(str(v) for v in flat_sources if v).lower()
    if any(phrase in flat for phrase in _NEGATIVE_PHRASES):
        return True

    # 2) Count signal — `review_summary.changes_requested_count > 0`.
    review_summary = evidence.get("review_summary") or {}
    if (review_summary.get("changes_requested_count") or 0) > 0:
        return True

    # 3) Mentor comment text — accept both `body` (legacy/fixture) and
    #    `body_excerpt` (real packets) keys.
    comment_buckets = [
        session_payload.get("mentor_comment_samples") or [],
        evidence.get("mentor_comment_samples") or [],
    ]
    for bucket in comment_buckets:
        for sample in (bucket or [])[:8]:
            text = (
                (sample or {}).get("body_excerpt")
                or (sample or {}).get("body")
                or ""
            ).lower()
            if any(phrase in text for phrase in _NEGATIVE_PHRASES):
                return True

    # 4) Thread participants — `thread_samples[*].participants[*].body_excerpt`.
    thread_buckets = [
        session_payload.get("thread_samples") or [],
        evidence.get("thread_samples") or [],
        evidence.get("review_threads") or [],  # backward-compat fixture key
    ]
    for bucket in thread_buckets:
        for thread in (bucket or [])[:6]:
            for participant in ((thread or {}).get("participants") or [])[:8]:
                text = (
                    (participant or {}).get("body_excerpt")
                    or (participant or {}).get("body")
                    or ""
                ).lower()
                if any(phrase in text for phrase in _NEGATIVE_PHRASES):
                    return True

    return False


# === Aggregation: summary + profile ======================================
def _summarize_learner_history(history: list[dict]) -> dict:
    by_type: Counter = Counter()
    tier_dist: Counter = Counter()
    blocked_count = 0
    last_active: str | None = None
    for event in history:
        et = event.get("event_type")
        by_type[et] += 1
        if et == "rag_ask":
            tier = event.get("tier")
            if event.get("blocked"):
                tier_dist["3_blocked"] += 1
            elif tier is not None:
                tier_dist[str(int(tier))] += 1
            if event.get("blocked"):
                blocked_count += 1
        ts = event.get("ts")
        if ts and (last_active is None or ts > last_active):
            last_active = ts
    return {
        "schema_version": LEARNER_PROFILE_SCHEMA_VERSION,
        "summary_type": "learner_summary",
        "updated_at": _now_iso(),
        "total_events": len(history),
        "events_by_type": dict(by_type),
        "tier_distribution": dict(tier_dist),
        "blocked_count": blocked_count,
        "last_active_at": last_active,
    }


def _experience_level_view(history: list[dict]) -> dict:
    window = history[-20:]
    beginner = sum(
        1
        for e in window
        if e.get("event_type") == "rag_ask"
        and e.get("experience_level_inferred") == "beginner"
    )
    test_events = [e for e in window if e.get("event_type") == "test_result"]
    test_pass_rate: float | None = None
    if test_events:
        passes = sum(1 for e in test_events if e.get("pass"))
        test_pass_rate = round(passes / len(test_events), 2)
    if window and beginner / max(len(window), 1) >= 0.5:
        current = "beginner"
        confidence = "high" if beginner >= 6 else "medium"
    elif beginner > 0:
        current = "beginner"
        confidence = "low"
    else:
        current = "unknown"
        confidence = "low"
    evidence: list[dict] = []
    if beginner:
        evidence.append(
            {"signal": "BEGINNER_HINT 매치", "count": beginner, "from": "rag_ask"}
        )
    if test_pass_rate is not None:
        evidence.append(
            {
                "signal": "test_result 통과율",
                "value": f"{int(test_pass_rate * 100)}%",
                "from": "test_result",
            }
        )
    return {
        "current": current,
        "confidence": confidence,
        "rolling_window": "last_20_events",
        "evidence": evidence,
    }


def _events_for_concept(history: list[dict], concept_id: str) -> list[dict]:
    return [
        event
        for event in history
        if concept_id in (event.get("concept_ids") or [])
    ]


def _has_test_fail_in_window(
    history: list[dict], concept_id: str, days: int = 7
) -> bool:
    return any(
        e.get("event_type") == "test_result"
        and e.get("pass") is False
        and _within(e.get("ts"), days=days)
        for e in _events_for_concept(history, concept_id)
    )


def _test_pass_strict_count(concept_id: str, history: list[dict]) -> int:
    return sum(
        1
        for e in _events_for_concept(history, concept_id)
        if e.get("event_type") == "test_result"
        and e.get("pass") is True
        and e.get("concept_match_mode") == "strict"
    )


def _test_pass_fallback_count(concept_id: str, history: list[dict]) -> int:
    return sum(
        1
        for e in _events_for_concept(history, concept_id)
        if e.get("event_type") == "test_result"
        and e.get("pass") is True
        and e.get("concept_match_mode") in ("fallback", "unknown", None)
    )


def _ask_decline_with_activity_evidence(
    concept_id: str, history: list[dict]
) -> bool:
    """Concept asked >= 3x in days 8–21 ago, 0 in last 7d, and *some* activity
    in the last 7d in the same module — i.e. learner moved on rather than left."""
    concept_events = _events_for_concept(history, concept_id)
    asks_recent = [
        e for e in concept_events
        if e.get("event_type") == "rag_ask" and _within(e.get("ts"), days=7)
    ]
    if asks_recent:
        return False
    asks_prior = [
        e for e in concept_events
        if e.get("event_type") == "rag_ask"
        and _within(e.get("ts"), days=21)
        and not _within(e.get("ts"), days=7)
    ]
    if len(asks_prior) < 3:
        return False
    prior_modules = [m for m in (e.get("module_context") for e in asks_prior) if m]
    if not prior_modules:
        return False
    from collections import Counter
    dominant_module = Counter(prior_modules).most_common(1)[0][0]
    for ev in history:
        if not _within(ev.get("ts"), days=7):
            continue
        if ev.get("module_context") != dominant_module:
            continue
        et = ev.get("event_type")
        if et == "test_result" and ev.get("pass"):
            return True
        if et in ("code_attempt", "coach_run"):
            return True
    return False


def _code_attempt_with_passing_test(
    concept_id: str, history: list[dict]
) -> bool:
    concept_events = _events_for_concept(history, concept_id)
    for ev in concept_events:
        if ev.get("event_type") != "code_attempt":
            continue
        linked = ev.get("linked_test")
        if not linked:
            continue
        for tr in concept_events:
            if tr.get("event_type") != "test_result" or not tr.get("pass"):
                continue
            tr_id = f"{tr.get('test_class', '')}.{tr.get('test_method', '')}"
            if tr_id == linked or linked in tr_id or tr_id in linked:
                return True
    return False


def _is_mastered(concept_id: str, history: list[dict]) -> tuple[bool, dict]:
    concept_events = _events_for_concept(history, concept_id)
    drills = [e for e in concept_events if e.get("event_type") == "drill_answer"][-5:]
    drill_high_scores = sum(1 for e in drills if (e.get("total_score") or 0) >= 8)
    pr_neg = any(
        e.get("event_type") == "coach_run"
        and e.get("had_negative_feedback")
        and _within(e.get("ts"), days=7)
        for e in concept_events
    )
    test_pass_strict = _test_pass_strict_count(concept_id, history)
    test_pass_fallback = _test_pass_fallback_count(concept_id, history)
    ask_decline_active = _ask_decline_with_activity_evidence(concept_id, history)
    code_attempt_test_pass = _code_attempt_with_passing_test(concept_id, history)
    no_recent_test_fail = not _has_test_fail_in_window(history, concept_id, days=7)

    signal_score = 0
    if drill_high_scores >= 2:
        signal_score += 2
    if test_pass_strict >= 1:
        signal_score += 2
    elif test_pass_fallback >= 2:
        signal_score += 2
    if ask_decline_active:
        signal_score += 1
    if code_attempt_test_pass:
        signal_score += 1

    mastered = (signal_score >= 3) and (not pr_neg) and no_recent_test_fail
    return mastered, {
        "signal_score": signal_score,
        "drill_high_scores": drill_high_scores,
        "test_pass_strict": test_pass_strict,
        "test_pass_fallback": test_pass_fallback,
        "ask_decline_with_activity": ask_decline_active,
        "code_attempt_with_passing_test": code_attempt_test_pass,
        "no_recent_pr_negative": not pr_neg,
        "no_recent_test_fail": no_recent_test_fail,
    }


def _is_uncertain(concept_id: str, history: list[dict]) -> tuple[bool, dict]:
    concept_events = _events_for_concept(history, concept_id)
    asks_7d = sum(
        1
        for e in concept_events
        if e.get("event_type") == "rag_ask" and _within(e.get("ts"), days=7)
    )
    drills_14d = [
        e
        for e in concept_events
        if e.get("event_type") == "drill_answer" and _within(e.get("ts"), days=14)
    ]
    last_drill_score = drills_14d[-1].get("total_score") if drills_14d else None
    low_drill = bool(drills_14d) and (drills_14d[-1].get("total_score") or 0) < 6
    test_fail_7d = any(
        e.get("event_type") == "test_result"
        and not e.get("pass")
        and _within(e.get("ts"), days=7)
        for e in concept_events
    )
    uncertain = (asks_7d >= 3) or low_drill or test_fail_7d
    return uncertain, {
        "ask_count_7d": asks_7d,
        "last_drill_score": last_drill_score,
        "test_fail_recent": test_fail_7d,
    }


def _is_underexplored(
    concept_id: str,
    history: list[dict],
    catalog: dict,
    current_stage: str | None,
) -> bool:
    stages = catalog.get("stages") or {}
    if not current_stage or current_stage not in stages:
        return False
    if concept_id not in (stages[current_stage].get("concepts") or []):
        return False
    return not any(
        concept_id in (event.get("concept_ids") or []) for event in history
    )


def _activity_view(history: list[dict]) -> dict:
    by_type: Counter = Counter(e.get("event_type") for e in history)
    tier_dist: Counter = Counter()
    modules: dict[str, dict] = {}
    streak_dates: set[str] = set()
    last_active: str | None = None
    for event in history:
        et = event.get("event_type")
        if et == "rag_ask":
            if event.get("blocked"):
                tier_dist["3_blocked"] += 1
            else:
                tier = event.get("tier")
                if tier is not None:
                    tier_dist[str(int(tier))] += 1
        ts = event.get("ts")
        if ts:
            streak_dates.add(ts[:10])
            if last_active is None or ts > last_active:
                last_active = ts
        module = event.get("module_context") or event.get("module")
        if module:
            mod = modules.setdefault(
                module,
                {
                    "turns": 0,
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "first_active": ts,
                    "last_active": ts,
                },
            )
            mod["turns"] += 1
            if et == "test_result":
                if event.get("pass"):
                    mod["tests_passed"] += 1
                else:
                    mod["tests_failed"] += 1
            if ts:
                mod["last_active"] = ts
                if mod.get("first_active") is None or ts < mod["first_active"]:
                    mod["first_active"] = ts
    for mod in modules.values():
        total_tests = mod["tests_passed"] + mod["tests_failed"]
        mod["completion_estimate"] = (
            round(mod["tests_passed"] / total_tests, 2) if total_tests else 0.0
        )
    current_module = None
    if last_active is not None:
        for event in reversed(history):
            mod = event.get("module_context") or event.get("module")
            if mod:
                current_module = mod
                break
    return {
        "streak_days": _streak_from_dates(streak_dates),
        "last_active_at": last_active,
        "events_by_type": dict(by_type),
        "tier_distribution": dict(tier_dist),
        "modules_progress": modules,
        "current_module": current_module,
    }


def _streak_from_dates(dates: Iterable[str]) -> int:
    parsed = sorted(
        {datetime.strptime(d, "%Y-%m-%d").date() for d in dates if d},
        reverse=True,
    )
    if not parsed:
        return 0
    today = datetime.now(timezone.utc).date()
    if (today - parsed[0]).days > 1:
        return 0
    streak = 1
    cursor = parsed[0]
    for d in parsed[1:]:
        if (cursor - d).days == 1:
            streak += 1
            cursor = d
        else:
            break
    return streak


def _build_learner_profile(history: list[dict], summary: dict) -> dict:
    catalog: dict
    try:
        from .concept_catalog import load_catalog as _load_catalog
        catalog = _load_catalog()
    except Exception:  # noqa: BLE001
        catalog = {"concepts": {}, "stages": {}}
    activity = _activity_view(history)
    current_module = activity.get("current_module")
    current_stage = None
    if current_module:
        for stage_id, stage in (catalog.get("stages") or {}).items():
            if current_module in (stage.get("modules") or []):
                current_stage = stage_id
                break
    encountered: Counter = Counter()
    for event in history:
        for cid in event.get("concept_ids") or []:
            encountered[cid] += 1
    mastered: list[dict] = []
    uncertain: list[dict] = []
    underexplored: list[dict] = []
    seen_concepts: set[str] = set(encountered.keys())
    if catalog.get("concepts"):
        for concept_id in catalog["concepts"]:
            seen_concepts.add(concept_id)
    for concept_id in sorted(seen_concepts):
        is_mastered, mastered_evidence = _is_mastered(concept_id, history)
        is_uncertain, uncertain_evidence = _is_uncertain(concept_id, history)
        if is_mastered:
            mastered.append(
                {
                    "concept_id": concept_id,
                    "evidence": mastered_evidence,
                    "since": _now_iso()[:10],
                }
            )
        if is_uncertain:
            first_ts = next(
                (
                    e.get("ts")
                    for e in history
                    if concept_id in (e.get("concept_ids") or [])
                ),
                None,
            )
            uncertain.append(
                {
                    "concept_id": concept_id,
                    "evidence": uncertain_evidence,
                    "first_signal_at": first_ts,
                }
            )
        if _is_underexplored(concept_id, history, catalog, current_stage):
            underexplored.append(
                {
                    "concept_id": concept_id,
                    "stage": current_stage,
                    "reason": "current stage gap (haven't touched yet)",
                }
            )
    activity["current_stage"] = current_stage
    profile = {
        "schema_version": LEARNER_PROFILE_SCHEMA_VERSION,
        "profile_type": "learner_profile_v3",
        "learner_id": _resolve_learner_id(),
        "updated_at": _now_iso(),
        "total_events": summary.get("total_events", len(history)),
        "experience_level": _experience_level_view(history),
        "concepts": {
            "mastered": mastered,
            "uncertain": uncertain,
            "underexplored": underexplored,
            "encountered_count": dict(encountered),
        },
        "activity": activity,
        "next_recommendations": [],
        "preferences": {
            "experience_level": None,
            "preferred_depth": None,
            "focus": [],
            "skip_concepts": [],
        },
    }
    # Phase 4 — fill next_recommendations using the freshly-built profile.
    try:
        profile["next_recommendations"] = suggest_next(profile, catalog)
    except Exception:  # noqa: BLE001
        profile["next_recommendations"] = []
    return profile


def default_profile() -> dict:
    """Skeleton profile when no events have been recorded yet."""
    return _build_learner_profile([], {"total_events": 0})


# === Active Guidance — suggest_next (v3 Phase 4) ==========================
def suggest_next(
    profile: dict | None,
    catalog: dict,
    *,
    max_n: int = 3,
) -> list[dict]:
    """Compute the next-step recommendations from a learner profile.

    Priority order (matches plan v3 §Suggest-Next 알고리즘):

      1. Drill an uncertain concept that hasn't been drilled yet (~0.85)
      2. Surface an underexplored concept in the current stage (~0.6)
      3. Advance to the next stage's first module when prereqs met (~0.9)
         — when prereqs are unmet, still surface the module with the
         missing concepts as `blockers` (~0.5).
    """
    if not profile or not catalog:
        return []
    suggestions: list[dict] = []
    concepts = profile.get("concepts") or {}
    mastered_ids = {
        (c or {}).get("concept_id") for c in concepts.get("mastered") or []
    }
    mastered_ids.discard(None)
    activity = profile.get("activity") or {}
    current_stage = activity.get("current_stage")

    # Rule 1 — drill uncertain concepts.
    for entry in concepts.get("uncertain") or []:
        cid = entry.get("concept_id")
        evidence = entry.get("evidence") or {}
        last_drill_score = evidence.get("last_drill_score")
        if cid is None:
            continue
        if last_drill_score is not None:
            continue
        suggestions.append(
            {
                "type": "drill",
                "value": cid,
                "reason": f"asked {evidence.get('ask_count_7d') or 0}x in 7d, no drill yet",
                "priority": 0.85,
            }
        )

    # Rule 2 — same-stage underexplored concepts.
    for entry in concepts.get("underexplored") or []:
        cid = entry.get("concept_id")
        if cid is None:
            continue
        if entry.get("stage") and entry["stage"] != current_stage:
            continue
        suggestions.append(
            {
                "type": "concept",
                "value": cid,
                "reason": f"{current_stage or 'current stage'} stage gap",
                "priority": 0.6,
            }
        )

    # Rule 3 — advance to next stage when prereqs are met.
    from .concept_catalog import next_stage as _next_stage  # local import
    from .concept_catalog import stage_first_module as _first_module
    if current_stage:
        next_id = _next_stage(catalog, current_stage)
        if next_id:
            next_module = _first_module(catalog, next_id)
            stage = (catalog.get("stages") or {}).get(next_id) or {}
            # Prereqs that are themselves part of the next stage are
            # things the learner is about to study, not gates to entry —
            # only earlier-stage concepts count as blockers.
            stage_concepts: set[str] = set(stage.get("concepts") or [])
            prereq_ids: set[str] = set()
            for cid in stage_concepts:
                concept = (catalog.get("concepts") or {}).get(cid) or {}
                for pid in concept.get("prerequisites") or []:
                    if pid not in stage_concepts:
                        prereq_ids.add(pid)
            unmet = [pid for pid in prereq_ids if pid not in mastered_ids]
            if next_module:
                if not unmet:
                    suggestions.append(
                        {
                            "type": "module",
                            "value": next_module,
                            "reason": f"{current_stage} prerequisites met, ready for {next_id}",
                            "priority": 0.9,
                            "blockers": [],
                        }
                    )
                else:
                    suggestions.append(
                        {
                            "type": "module",
                            "value": next_module,
                            "reason": f"prereqs not yet mastered: {unmet}",
                            "priority": 0.5,
                            "blockers": list(unmet),
                        }
                    )

    suggestions.sort(key=lambda s: -float(s.get("priority") or 0))
    return suggestions[:max_n]


# === Adaptive Response — learner_context (v3 closed loop) =================
def build_learner_context(
    profile: dict | None,
    *,
    prompt: str | None = None,
    decision: dict | None = None,
    catalog: dict | None = None,
) -> dict | None:
    """Compute the per-turn `learner_context` block for `bin/rag-ask`.

    Returns None when the profile is missing or has no usable signal
    (cold-start). When returned, AI sessions must consume `response_hints`
    so the response actually adapts — see `docs/learner-memory.md` and
    the AGENTS.md / CLAUDE.md adaptive response rule.
    """
    if not profile:
        return None
    if (profile.get("total_events") or 0) == 0:
        return None
    catalog = catalog or {}
    if not catalog:
        try:
            from .concept_catalog import load_catalog as _load_catalog
            catalog = _load_catalog()
        except Exception:
            catalog = {}
    concepts = profile.get("concepts") or {}
    mastered = list(concepts.get("mastered") or [])
    uncertain = list(concepts.get("uncertain") or [])
    underexplored = list(concepts.get("underexplored") or [])
    activity = profile.get("activity") or {}
    current_module = activity.get("current_module")
    current_stage = activity.get("current_stage")
    prompt_concepts: set[str] = set()
    if prompt:
        try:
            from .concept_catalog import extract_concept_ids as _extract
            prompt_concepts = set(_extract(prompt, catalog))
        except Exception:
            prompt_concepts = set()

    skip_basics_for: list[str] = sorted({
        c.get("concept_id") for c in mastered if c.get("concept_id") in prompt_concepts
    } - {None})
    deepen_for: list[str] = sorted({
        c.get("concept_id") for c in uncertain if c.get("concept_id") in prompt_concepts
    } - {None})

    suggested_depth = "medium"
    if deepen_for:
        suggested_depth = "deep"
    elif decision and decision.get("tier") == 1 and not skip_basics_for:
        suggested_depth = "shallow"

    next_recommendations = list(profile.get("next_recommendations") or [])
    next_rec = next_recommendations[0] if next_recommendations else None
    if next_rec is None and deepen_for:
        next_rec = {
            "type": "drill",
            "value": deepen_for[0],
            "reason": "uncertain — drill recommended",
            "priority": 0.85,
        }

    must_include_phrases: list[str] = []
    for cid in deepen_for:
        evidence = next(
            (e for e in uncertain if e.get("concept_id") == cid), {}
        ).get("evidence", {})
        ask_count = evidence.get("ask_count_7d") or 0
        if ask_count >= 3:
            must_include_phrases.append(f"{ask_count}번째 질문이야")
            break
    must_skip_explanations_of = list(skip_basics_for)
    header_required_tags: list[str] = []
    if skip_basics_for:
        header_required_tags.append(
            "skip-basics(" + ",".join(c.split("/")[-1] for c in skip_basics_for) + ")"
        )
    if deepen_for:
        header_required_tags.append(
            "deepen(" + ",".join(c.split("/")[-1] for c in deepen_for) + ")"
        )
    must_offer_next_action = (
        f"{next_rec['type']}:{next_rec['value']}" if next_rec else None
    )

    return {
        "experience_level": profile.get("experience_level") or {},
        "current_module": current_module,
        "current_stage": current_stage,
        "module_progress": (activity.get("modules_progress") or {}).get(current_module)
        if current_module
        else None,
        "mastered_concepts": [
            {"id": c.get("concept_id"), "evidence": c.get("evidence")}
            for c in mastered
        ],
        "uncertain_concepts": [
            {
                "id": c.get("concept_id"),
                "ask_count_7d": (c.get("evidence") or {}).get("ask_count_7d"),
                "guidance": "asked frequently — go deeper, surface common misconceptions",
            }
            for c in uncertain
        ],
        "underexplored_in_current_stage": [
            {"id": c.get("concept_id"), "reason": c.get("reason")}
            for c in underexplored
        ],
        "skip_basics_for": skip_basics_for,
        "deepen_for": deepen_for,
        "tie_to_module": current_module,
        "suggested_depth": suggested_depth,
        "next_recommendation": next_rec,
        "response_hints": {
            "must_include_phrases": must_include_phrases,
            "must_skip_explanations_of": must_skip_explanations_of,
            "header_required_tags": header_required_tags,
            "must_offer_next_action": must_offer_next_action,
        },
    }


# === Migration from per-repo memory (Commit 3 / Phase 2) ==================
def _legacy_entry_event_id(entry: dict, repo: str) -> str:
    """Stable id for a per-repo legacy entry.

    Uses the entry's created_at + repo + question_fingerprint or current_pr
    so re-running migration on the same legacy file produces the same id.
    """
    keys = [
        "coach_run",
        entry.get("created_at") or "",
        repo,
        entry.get("question_fingerprint")
        or str((entry.get("current_pr") or {}).get("number") or "")
        or (entry.get("prompt") or ""),
    ]
    digest = hashlib.sha1("|".join(keys).encode("utf-8")).hexdigest()
    return digest[:16]


def _normalize_legacy_entry(
    entry: dict,
    *,
    repo: str,
    learner_id: str,
    catalog: dict,
    source_path: Path,
    source_line: int,
) -> dict:
    """Map a per-repo `learning_memory_entry` to a v3 `coach_run` event.

    The legacy entry shape comes from `memory._memory_entry`; its fields
    map to v3 as follows:

      created_at   → ts
      repo         → repo_context
      current_pr   → pr_number (extracted)
      primary_learning_points → primary_learning_points
      learning_point_recommendations → learning_point_recommendations
      summary / answer / follow_up_question → preserved verbatim

    `had_negative_feedback` defaults to False because the legacy entry
    doesn't keep raw mentor comment text; mastery rule treats this as
    "no negative signal", which is correct for events that successfully
    completed coach-run.
    """
    ts = entry.get("ts") or entry.get("created_at") or _now_iso()
    pr_number = (entry.get("current_pr") or {}).get("number")
    if pr_number is None:
        pr_number = entry.get("pr_number")
    learning_points = list(entry.get("primary_learning_points") or [])
    concept_ids: list[str] = []
    for lp in learning_points:
        cid = lp_to_concept_id(lp, catalog)
        if cid:
            concept_ids.append(cid)
    out = {
        "event_type": "coach_run",
        "ts": ts,
        "learner_id": learner_id,
        "repo_context": entry.get("repo") or repo,
        "module_context": None,
        "pr_number": pr_number,
        "concept_ids": sorted(set(concept_ids)),
        "had_negative_feedback": bool(entry.get("had_negative_feedback")),
        "prompt": _redact_text(entry.get("prompt")),
        "primary_learning_points": learning_points,
        "learning_point_recommendations": entry.get(
            "learning_point_recommendations"
        )
        or [],
        "summary": entry.get("summary"),
        "answer": entry.get("answer"),
        "follow_up_question": entry.get("follow_up_question"),
        "source_path": str(source_path),
        "source_line": source_line,
        "source_event_id": entry.get("entry_id")
        or _legacy_entry_event_id(entry, repo),
    }
    out["event_id"] = _deterministic_event_id(out)
    return out


def _existing_event_ids() -> set[str]:
    path = learner_history_path()
    if not path.exists():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        ev_id = event.get("event_id")
        if ev_id:
            ids.add(ev_id)
    return ids


def migrate_from_repos(state_repos_dir: Path) -> dict:
    """Merge every `state/repos/<repo>/memory/history.jsonl` into the
    learner stream. Idempotent — re-running yields the same final state.

    Returns a counts dict: `{migrated, skipped_duplicates, repos_visited}`.
    """
    ensure_learner_layout()
    from .concept_catalog import load_catalog as _load_catalog
    catalog = _load_catalog()
    learner_id = _resolve_learner_id()
    seen_ids = _existing_event_ids()
    migrated = 0
    skipped = 0
    repos_visited = 0
    if not state_repos_dir.exists():
        return {"migrated": 0, "skipped_duplicates": 0, "repos_visited": 0}
    candidates: list[dict] = []
    for repo_dir in sorted(state_repos_dir.iterdir()):
        if not repo_dir.is_dir():
            continue
        history = repo_dir / "memory" / "history.jsonl"
        if not history.exists():
            continue
        repos_visited += 1
        for line_num, line in enumerate(
            history.read_text(encoding="utf-8").splitlines(), start=1
        ):
            text = line.strip()
            if not text:
                continue
            try:
                entry = json.loads(text)
            except json.JSONDecodeError:
                continue
            event = _normalize_legacy_entry(
                entry,
                repo=repo_dir.name,
                learner_id=learner_id,
                catalog=catalog,
                source_path=history,
                source_line=line_num,
            )
            candidates.append(event)
    candidates.sort(key=lambda e: e.get("ts") or "")
    for event in candidates:
        if event["event_id"] in seen_ids:
            skipped += 1
            continue
        try:
            append_learner_event(event)
            seen_ids.add(event["event_id"])
            migrated += 1
        except ValueError:
            # Legacy entry missing a v3 required field; skip but count as
            # a duplicate so the migration still terminates cleanly.
            skipped += 1
    if migrated:
        recompute_learner_profile()
    return {
        "migrated": migrated,
        "skipped_duplicates": skipped,
        "repos_visited": repos_visited,
    }
