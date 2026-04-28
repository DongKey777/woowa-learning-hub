from __future__ import annotations

import json
import os
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .candidate_interpretation import LEARNING_POINT_RULES
from .file_lock import lock_exclusive, unlock
from .paths import repo_memory_dir
from .schema_validation import validate_payload

HALF_LIFE_DAYS = 14.0


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _history_path(repo_name: str) -> Path:
    return repo_memory_dir(repo_name) / "history.jsonl"


def _summary_path(repo_name: str) -> Path:
    return repo_memory_dir(repo_name) / "summary.json"


def _profile_path(repo_name: str) -> Path:
    return repo_memory_dir(repo_name) / "profile.json"


def _question_fingerprint(prompt: str | None) -> str | None:
    if not prompt:
        return None
    lowered = prompt.lower()
    collapsed = re.sub(r"[^0-9a-z가-힣]+", " ", lowered)
    normalized = " ".join(collapsed.split())
    return normalized or None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _decay_weight(created_at: str | None) -> float:
    parsed = _parse_iso(created_at)
    if parsed is None:
        return 1.0
    age_seconds = max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds())
    age_days = age_seconds / 86400.0
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def _diff_fingerprint(session_payload: dict) -> str | None:
    signature = session_payload.get("focus_local_path_signature") or {}
    paths = signature.get("paths") or []
    if paths:
        return "|".join(sorted(paths[:12]))
    current_pr = session_payload.get("current_pr") or {}
    if current_pr.get("number") is not None:
        return f"pr:{current_pr['number']}"
    return None


def _recommendation_digest(session_payload: dict) -> list[dict]:
    result = []
    for item in session_payload.get("learning_point_recommendations", [])[:5]:
        primary = item.get("primary_candidate") or {}
        result.append({
            "learning_point": item.get("learning_point"),
            "label": item.get("label"),
            "primary_candidate_pr": primary.get("pr_number"),
            "primary_candidate_title": primary.get("title"),
            "primary_candidate_author": primary.get("author_login"),
        })
    return result


def _entry_learning_points(session_payload: dict) -> list[str]:
    return [
        item.get("learning_point")
        for item in session_payload.get("learning_point_recommendations", [])[:5]
        if item.get("learning_point")
    ]


def _memory_entry(session_payload: dict) -> dict:
    response = session_payload.get("response", {})
    evidence = response.get("evidence", [])
    highlights: list[str] = []
    for item in evidence:
        for highlight in item.get("highlights", [])[:2]:
            if highlight not in highlights:
                highlights.append(highlight)

    learning_points = _entry_learning_points(session_payload)

    return {
        "entry_type": "learning_memory_entry",
        "repo": session_payload["repo"],
        "mode": session_payload.get("mode"),
        "created_at": session_payload.get("generated_at") or _timestamp(),
        "prompt": session_payload.get("prompt"),
        "question_fingerprint": _question_fingerprint(session_payload.get("prompt")),
        "diff_fingerprint": _diff_fingerprint(session_payload),
        "primary_intent": session_payload.get("primary_intent"),
        "primary_topic": session_payload.get("primary_topic"),
        "primary_learning_points": learning_points[:3],
        "learning_point_recommendations": _recommendation_digest(session_payload),
        "reviewer": session_payload.get("reviewer"),
        "current_pr": session_payload.get("current_pr"),
        "summary": response.get("summary", []),
        "answer": response.get("answer", []),
        "follow_up_question": response.get("follow_up_question"),
        "next_action_titles": [item.get("title") for item in response.get("next_actions", []) if item.get("title")],
        "evidence_highlights": highlights[:6],
    }


def _load_history(repo_name: str) -> list[dict]:
    path = _history_path(repo_name)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            entries.append(json.loads(text))
        except json.JSONDecodeError:
            continue
    return entries


def _entry_pattern_key(entry: dict) -> tuple[str | None, str | None]:
    return (
        entry.get("question_fingerprint"),
        entry.get("diff_fingerprint"),
    )


def _learning_point_counter(entries: list[dict]) -> Counter:
    counts = Counter()
    seen_by_point: dict[str, set[tuple[str | None, str | None]]] = {}
    for entry in entries:
        pattern_key = _entry_pattern_key(entry)
        for learning_point in entry.get("primary_learning_points", []):
            seen = seen_by_point.setdefault(learning_point, set())
            if pattern_key in seen:
                continue
            seen.add(pattern_key)
            counts[learning_point] += 1
    return counts


def _weighted_learning_point_counts(entries: list[dict]) -> dict[str, float]:
    counts: dict[str, float] = {}
    seen_by_point: dict[str, set[tuple[str | None, str | None]]] = {}
    for entry in reversed(entries):
        pattern_key = _entry_pattern_key(entry)
        weight = _decay_weight(entry.get("created_at"))
        for learning_point in entry.get("primary_learning_points", []):
            seen = seen_by_point.setdefault(learning_point, set())
            if pattern_key in seen:
                continue
            seen.add(pattern_key)
            counts[learning_point] = counts.get(learning_point, 0.0) + weight
    return counts


def _repeated_learning_point_counts(entries: list[dict]) -> Counter:
    counts = Counter()
    patterns_by_point: dict[str, set[tuple[str | None, str | None]]] = {}
    for entry in entries:
        fingerprint = _entry_pattern_key(entry)
        for learning_point in entry.get("primary_learning_points", []):
            patterns_by_point.setdefault(learning_point, set()).add(fingerprint)
    for learning_point, patterns in patterns_by_point.items():
        counts[learning_point] = len(patterns)
    return counts


_CONFIDENCE_ORDER = ("low", "medium", "high")


def _shift_level(level: str, delta: int) -> str:
    try:
        idx = _CONFIDENCE_ORDER.index(level)
    except ValueError:
        return level
    shifted = max(0, min(len(_CONFIDENCE_ORDER) - 1, idx + delta))
    return _CONFIDENCE_ORDER[shifted]


def _confidence_level(
    count: int,
    weighted_count: float,
    avg_drill_score: float | None = None,
) -> str:
    if count >= 4 or weighted_count >= 3.0:
        level = "high"
    elif count >= 2 or weighted_count >= 1.5:
        level = "medium"
    else:
        level = "low"
    if avg_drill_score is None:
        return level
    if avg_drill_score >= 7.0:
        return _shift_level(level, +1)
    if avg_drill_score < 5.0:
        return _shift_level(level, -1)
    return level


def _question_pattern_counter(entries: list[dict]) -> Counter:
    return Counter(entry.get("question_fingerprint") for entry in entries if entry.get("question_fingerprint"))


def _recent_learning_points(entries: list[dict], limit: int = 5) -> list[dict]:
    recent = []
    for entry in reversed(entries[-5:]):
        recent.append({
            "created_at": entry.get("created_at"),
            "prompt": entry.get("prompt"),
            "learning_points": entry.get("primary_learning_points", []),
        })
        if len(recent) >= limit:
            break
    return recent


def _open_follow_ups(entries: list[dict], limit: int = 5) -> list[dict]:
    items = []
    for entry in reversed(entries):
        question = entry.get("follow_up_question")
        if not question:
            continue
        items.append({
            "created_at": entry.get("created_at"),
            "question": question,
            "prompt": entry.get("prompt"),
            "learning_points": entry.get("primary_learning_points", []),
        })
        if len(items) >= limit:
            break
    return items


def _summarize_history(repo_name: str, entries: list[dict]) -> dict:
    topic_counts = Counter(entry.get("primary_topic") for entry in entries if entry.get("primary_topic"))
    intent_counts = Counter(entry.get("primary_intent") for entry in entries if entry.get("primary_intent"))
    reviewer_counts = Counter(entry.get("reviewer") for entry in entries if entry.get("reviewer"))
    learning_point_counts = _learning_point_counter(entries)
    weighted_learning_point_counts = _weighted_learning_point_counts(entries)
    repeated_learning_point_counts = _repeated_learning_point_counts(entries)
    question_pattern_counts = _question_pattern_counter(entries)

    path_counts = Counter()
    for entry in entries:
        for highlight in entry.get("evidence_highlights", []):
            path_counts[highlight] += 1

    recent_entries = entries[-5:]
    recent_questions = [entry.get("prompt") for entry in reversed(recent_entries) if entry.get("prompt")]
    open_follow_ups = [item["question"] for item in _open_follow_ups(entries)]

    summary = {
        "summary_type": "learning_memory_summary",
        "repo": repo_name,
        "updated_at": _timestamp(),
        "total_sessions": len(entries),
        "top_topics": [{"topic": topic, "count": count} for topic, count in topic_counts.most_common(5)],
        "top_intents": [{"intent": intent, "count": count} for intent, count in intent_counts.most_common(5)],
        "top_learning_points": [
            {
                "learning_point": point,
                "count": count,
                "weighted_count": round(weighted_learning_point_counts.get(point, 0.0), 3),
                "confidence": _confidence_level(count, weighted_learning_point_counts.get(point, 0.0)),
            }
            for point, count in learning_point_counts.most_common(8)
        ],
        "repeated_learning_points": [
            {
                "learning_point": point,
                "count": count,
                "weighted_count": round(weighted_learning_point_counts.get(point, 0.0), 3),
                "confidence": _confidence_level(count, weighted_learning_point_counts.get(point, 0.0)),
            }
            for point, count in repeated_learning_point_counts.most_common(8)
            if count >= 2
        ],
        "learning_point_confidence": [
            {
                "learning_point": point,
                "count": learning_point_counts.get(point, 0),
                "weighted_count": round(weighted_learning_point_counts.get(point, 0.0), 3),
                "confidence": _confidence_level(learning_point_counts.get(point, 0), weighted_learning_point_counts.get(point, 0.0)),
            }
            for point in sorted(set(learning_point_counts) | set(weighted_learning_point_counts))
        ],
        "weighted_learning_points": [
            {
                "learning_point": point,
                "count": learning_point_counts.get(point, 0),
                "weighted_count": round(wc, 3),
                "confidence": _confidence_level(learning_point_counts.get(point, 0), wc),
            }
            for point, wc in sorted(weighted_learning_point_counts.items(), key=lambda x: -x[1])[:8]
            if wc > 0
        ],
        "top_reviewers": [{"reviewer": reviewer, "count": count} for reviewer, count in reviewer_counts.most_common(5)],
        "recurring_paths": [{"path": path, "count": count} for path, count in path_counts.most_common(8)],
        "recent_questions": recent_questions[:5],
        "recent_learning_points": _recent_learning_points(entries),
        "repeated_question_patterns": [
            {"question_fingerprint": question, "count": count}
            for question, count in question_pattern_counts.most_common(5)
        ],
        "open_follow_ups": open_follow_ups[:5],
        "recent_sessions": recent_entries[-3:],
    }
    return summary


def _recent_learning_streak(entries: list[dict]) -> dict | None:
    if not entries:
        return None
    deduped: list[dict] = []
    previous_key = None
    for entry in entries:
        key = (_entry_pattern_key(entry), tuple(entry.get("primary_learning_points", [])))
        if key == previous_key:
            continue
        deduped.append(entry)
        previous_key = key
    latest_points = deduped[-1].get("primary_learning_points", []) if deduped else []
    if not latest_points:
        return None
    target = latest_points[0]
    streak = 0
    for entry in reversed(deduped):
        if target not in entry.get("primary_learning_points", []):
            break
        streak += 1
    return {"learning_point": target, "count": streak}


def _learning_point_catalog() -> dict[str, dict]:
    return {rule["id"]: rule for rule in LEARNING_POINT_RULES}


def _build_profile(
    repo_name: str,
    summary: dict,
    entries: list[dict],
    *,
    avg_drill_score: float | None = None,
) -> dict:
    catalog = _learning_point_catalog()
    confidence_map = {
        item["learning_point"]: item
        for item in summary.get("learning_point_confidence", [])
    }
    underexplored = []
    for rule in LEARNING_POINT_RULES:
        count = confidence_map.get(rule["id"], {}).get("count", 0)
        if count == 0:
            underexplored.append({
                "learning_point": rule["id"],
                "label": rule["label"],
                "count": count,
            })

    weighted_map = {
        item["learning_point"]: item
        for item in summary.get("weighted_learning_points", [])
    }

    dominant_learning_points = []
    for item in summary.get("top_learning_points", [])[:5]:
        lp_id = item["learning_point"]
        count = item["count"]
        wc = item.get("weighted_count", 0) or 0
        ratio = wc / count if count > 0 else 0.0
        if ratio > 0.7:
            recency = "active"
        elif ratio >= 0.3:
            recency = "cooling"
        else:
            recency = "dormant"
        dominant_learning_points.append({
            "learning_point": lp_id,
            "label": catalog.get(lp_id, {}).get("label"),
            "count": count,
            "weighted_count": wc,
            "confidence": item.get("confidence"),
            "recency_status": recency,
        })

    repeated_learning_points = []
    for item in summary.get("repeated_learning_points", [])[:5]:
        lp_id = item["learning_point"]
        count = item["count"]
        wc = item.get("weighted_count", 0) or 0
        ratio = wc / count if count > 0 else 0.0
        if ratio > 0.7:
            recency = "active"
        elif ratio >= 0.3:
            recency = "cooling"
        else:
            recency = "dormant"
        repeated_learning_points.append({
            "learning_point": lp_id,
            "label": catalog.get(lp_id, {}).get("label"),
            "count": count,
            "weighted_count": wc,
            "confidence": item.get("confidence"),
            "recency_status": recency,
        })
    global_confidence = "low"
    if any(item.get("confidence") == "high" for item in repeated_learning_points[:2]):
        global_confidence = "high"
    elif repeated_learning_points or any(item.get("confidence") == "medium" for item in dominant_learning_points[:2]):
        global_confidence = "medium"

    # Drill performance is a second signal: strong drill answers promote the
    # confidence we show the learner even when history is thin, and weak
    # drill answers demote it even when history looks dense.
    if avg_drill_score is not None:
        if avg_drill_score >= 7.0:
            global_confidence = _shift_level(global_confidence, +1)
        elif avg_drill_score < 5.0:
            global_confidence = _shift_level(global_confidence, -1)

    profile = {
        "profile_type": "learning_memory_profile",
        "repo": repo_name,
        "updated_at": _timestamp(),
        "total_sessions": summary.get("total_sessions", 0),
        "confidence": global_confidence,
        "dominant_topics": summary.get("top_topics", [])[:3],
        "dominant_intents": summary.get("top_intents", [])[:3],
        "dominant_learning_points": dominant_learning_points,
        "repeated_learning_points": repeated_learning_points,
        "underexplored_learning_points": underexplored[:6],
        "recent_learning_streak": _recent_learning_streak(entries),
        "repeated_question_patterns": summary.get("repeated_question_patterns", [])[:5],
        "open_follow_up_queue": _open_follow_ups(entries),
    }
    return profile


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    closed = False
    try:
        os.write(fd, content.encode("utf-8"))
        os.fsync(fd)
        os.close(fd)
        closed = True
        os.rename(tmp, path)
    except BaseException:
        if not closed:
            os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _append_with_lock(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        lock_exclusive(handle)
        try:
            handle.write(line)
        finally:
            unlock(handle)


def compute_memory_update(
    repo_name: str,
    session_payload: dict,
    *,
    learning_projection: dict | None = None,
) -> dict:
    """Compute history/summary/profile updates for this turn.

    ``learning_projection`` carries the CS/drill fields that profile.json
    should persist as source-of-truth. The coach_run pipeline derives it
    via profile_merge.unify() against the drill_history jsonl + the
    optional this-turn drill_result, then hands the compact fields here
    so the persisted profile matches the per-turn projection.

    Expected keys (all optional):
      - ``cs_view`` — {avg_score, level, weak_dimensions, weak_tags,
                       low_categories, recent_drills} or None
      - ``drill_history`` — compact list of recent drill entries
      - ``reconciled`` — {priority_focus, empirical_only_gaps,
                          theoretical_only_gaps} or None
    """
    entry = _memory_entry(session_payload)
    validate_payload("learning-memory-entry", entry)

    existing_entries = _load_history(repo_name)
    projected_entries = existing_entries + [entry]

    summary = _summarize_history(repo_name, projected_entries)
    validate_payload("learning-memory-summary", summary)

    avg_drill_score: float | None = None
    if learning_projection:
        cs_view = learning_projection.get("cs_view") or {}
        raw = cs_view.get("avg_score") if isinstance(cs_view, dict) else None
        if isinstance(raw, (int, float)):
            avg_drill_score = float(raw)

    profile = _build_profile(
        repo_name,
        summary,
        projected_entries,
        avg_drill_score=avg_drill_score,
    )
    if learning_projection:
        for field in ("cs_view", "drill_history", "reconciled"):
            if field in learning_projection:
                profile[field] = learning_projection[field]
    validate_payload("learning-memory-profile", profile)

    return {
        "repo": repo_name,
        "history_path": str(_history_path(repo_name)),
        "summary_path": str(_summary_path(repo_name)),
        "profile_path": str(_profile_path(repo_name)),
        "entry": entry,
        "summary": summary,
        "profile": profile,
    }


def commit_history_entry(repo_name: str, memory_update: dict) -> None:
    entry = memory_update["entry"]
    history_path = _history_path(repo_name)
    _append_with_lock(history_path, json.dumps(entry, ensure_ascii=False) + "\n")


def commit_memory_snapshot(repo_name: str, memory_update: dict) -> None:
    summary = memory_update["summary"]
    profile = memory_update["profile"]
    summary_path = _summary_path(repo_name)
    _atomic_write(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    profile_path = _profile_path(repo_name)
    _atomic_write(profile_path, json.dumps(profile, ensure_ascii=False, indent=2) + "\n")


def commit_memory_update(repo_name: str, memory_update: dict) -> None:
    commit_history_entry(repo_name, memory_update)
    commit_memory_snapshot(repo_name, memory_update)


def needs_recompute(repo_name: str) -> bool:
    history_path = _history_path(repo_name)
    summary_path = _summary_path(repo_name)
    profile_path = _profile_path(repo_name)
    if not history_path.exists():
        return False
    if history_path.stat().st_size == 0:
        return False
    if not summary_path.exists() or not profile_path.exists():
        return True
    history_mtime = history_path.stat().st_mtime
    summary_mtime = summary_path.stat().st_mtime
    profile_mtime = profile_path.stat().st_mtime
    if history_mtime > summary_mtime or history_mtime > profile_mtime:
        return True
    if abs(summary_mtime - profile_mtime) > 1.0:
        return True
    return False


def recompute_from_history(repo_name: str) -> dict | None:
    entries = _load_history(repo_name)
    if not entries:
        return None
    summary = _summarize_history(repo_name, entries)
    validate_payload("learning-memory-summary", summary)
    profile = _build_profile(repo_name, summary, entries)
    validate_payload("learning-memory-profile", profile)

    summary_path = _summary_path(repo_name)
    _atomic_write(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    profile_path = _profile_path(repo_name)
    _atomic_write(profile_path, json.dumps(profile, ensure_ascii=False, indent=2) + "\n")

    return {"summary": summary, "profile": profile}


def update_learning_memory(repo_name: str, session_payload: dict) -> dict:
    result = compute_memory_update(repo_name, session_payload)
    commit_memory_update(repo_name, result)
    return result


def _default_summary(repo_name: str) -> dict:
    return {
        "summary_type": "learning_memory_summary",
        "repo": repo_name,
        "updated_at": _timestamp(),
        "total_sessions": 0,
        "top_topics": [],
        "top_intents": [],
        "top_learning_points": [],
        "repeated_learning_points": [],
        "learning_point_confidence": [],
        "weighted_learning_points": [],
        "top_reviewers": [],
        "recurring_paths": [],
        "recent_questions": [],
        "recent_learning_points": [],
        "repeated_question_patterns": [],
        "open_follow_ups": [],
        "recent_sessions": [],
    }


def _default_profile(repo_name: str) -> dict:
    return {
        "profile_type": "learning_memory_profile",
        "repo": repo_name,
        "updated_at": _timestamp(),
        "total_sessions": 0,
        "confidence": "low",
        "dominant_topics": [],
        "dominant_intents": [],
        "dominant_learning_points": [],
        "repeated_learning_points": [],
        "underexplored_learning_points": [
            {
                "learning_point": rule["id"],
                "label": rule["label"],
                "count": 0,
            }
            for rule in LEARNING_POINT_RULES[:6]
        ],
        "recent_learning_streak": None,
        "repeated_question_patterns": [],
        "open_follow_up_queue": [],
    }


def load_learning_memory(repo_name: str) -> dict:
    summary_path = _summary_path(repo_name)
    profile_path = _profile_path(repo_name)
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else _default_summary(repo_name)
    profile = json.loads(profile_path.read_text(encoding="utf-8")) if profile_path.exists() else _default_profile(repo_name)
    return {
        "repo": repo_name,
        "history_path": str(_history_path(repo_name)),
        "summary_path": str(summary_path),
        "profile_path": str(profile_path),
        "summary": summary,
        "profile": profile,
    }
