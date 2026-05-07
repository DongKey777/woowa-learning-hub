"""Learner hit-relevance feedback channel (plan §P7.1 + §P7.2).

After a coaching turn that surfaced CS docs, the learner can leave a
one-line signal on whether those docs actually helped. Recorded as
JSONL rows so a later analysis pass (``bin/feedback-mine``) can:

- Find frequent ``not_helpful`` (prompt, doc) pairs → corpus
  cleanup or signal_rules.py refinement candidates.
- Promote ``helpful`` pairs into the eval golden set (P1.1 fixture
  schema) — closes the loop *without* an LLM.

Pure data layer. ``bin/learn-feedback`` is the writer wrapper;
``bin/feedback-mine`` is the analyzer. ``searcher.search()`` does
not consume this file directly — the closed loop is offline.

## Schema

One JSONL row per feedback signal::

    {
      "schema_id": "rag-feedback-v1",
      "logged_at": "2026-04-30T...",
      "repo": "tobys-mission-1" | "",
      "prompt": "<learner question>",
      "prompt_hash": "<sha1 hex>",
      "signal": "helpful" | "not_helpful" | "unclear",
      "hits": [
        {"path": "knowledge/cs/contents/spring/bean.md", "section": "..."},
        ...
      ],
      "note": "<optional one-line note from learner>"
    }

## Storage

- Default: ``state/cs_rag/feedback.jsonl`` (corpus-wide signal)
- With ``--repo``: also mirrored to
  ``state/repos/<repo>/logs/rag_feedback.jsonl`` so per-repo analysis
  can correlate with mission context.

Append-only; corruption-resistant reader (skips bad lines).

Tested in ``tests/unit/test_rag_feedback.py``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCHEMA_ID = "rag-feedback-v1"
DEFAULT_GLOBAL_REL = Path("state") / "cs_rag" / "feedback.jsonl"
VALID_SIGNALS = ("helpful", "not_helpful", "unclear")


# ---------------------------------------------------------------------------
# prompt hashing — same shape as query-rewrite-v1 so cross-stage
# analysis can join feedback to AI rewrites by prompt_hash
# ---------------------------------------------------------------------------

def compute_prompt_hash(prompt: str) -> str:
    """Stable hash of the trimmed prompt. No mode component (unlike
    query-rewrite-v1) — this is a learner-facing identifier."""
    return hashlib.sha1(prompt.strip().encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeedbackHit:
    path: str
    section: str | None = None

    def to_dict(self) -> dict:
        d: dict = {"path": self.path}
        if self.section:
            d["section"] = self.section
        return d


# ---------------------------------------------------------------------------
# Build + write
# ---------------------------------------------------------------------------

def build_feedback_row(
    *,
    prompt: str,
    signal: str,
    hits: Iterable[FeedbackHit | dict],
    repo: str | None = None,
    note: str | None = None,
    source_event_id: str | None = None,
    turn_id: str | None = None,
    now: datetime | None = None,
) -> dict:
    if signal not in VALID_SIGNALS:
        raise ValueError(f"signal must be one of {VALID_SIGNALS} (got {signal!r})")
    if not prompt or not prompt.strip():
        raise ValueError("prompt must not be empty")

    norm_hits: list[dict] = []
    for h in hits:
        if isinstance(h, FeedbackHit):
            norm_hits.append(h.to_dict())
        elif isinstance(h, dict) and "path" in h:
            entry = {"path": h["path"]}
            if h.get("section"):
                entry["section"] = h["section"]
            norm_hits.append(entry)
        elif isinstance(h, str):
            norm_hits.append({"path": h})
        else:
            raise ValueError(f"unsupported hit shape: {h!r}")

    return {
        "schema_id": SCHEMA_ID,
        "logged_at": (now or datetime.now(timezone.utc)).isoformat(),
        "repo": repo or "",
        "source_event_id": source_event_id,
        "turn_id": turn_id,
        "prompt": prompt,
        "prompt_hash": compute_prompt_hash(prompt),
        "signal": signal,
        "hits": norm_hits,
        "note": note or "",
    }


def resolve_log_paths(
    *,
    repo: str | None,
    repo_root: Path,
    global_path: Path | None = None,
) -> list[Path]:
    """Return all paths the row should be appended to.

    The global feedback log gets every entry; the per-repo log only
    gets entries with a non-empty repo.
    """
    paths = [global_path or (repo_root / DEFAULT_GLOBAL_REL)]
    if repo:
        paths.append(repo_root / "state" / "repos" / repo / "logs" / "rag_feedback.jsonl")
    return paths


def append_feedback(
    *,
    prompt: str,
    signal: str,
    hits: Iterable[FeedbackHit | dict],
    repo: str | None,
    repo_root: Path,
    note: str | None = None,
    source_event_id: str | None = None,
    turn_id: str | None = None,
    now: datetime | None = None,
) -> list[Path]:
    """Append the row to all relevant log files. Returns the list of
    paths written. Best-effort — IO exceptions bubble up."""
    row = build_feedback_row(
        prompt=prompt, signal=signal, hits=hits,
        repo=repo, note=note, source_event_id=source_event_id,
        turn_id=turn_id, now=now,
    )
    written: list[Path] = []
    for path in resolve_log_paths(repo=repo, repo_root=repo_root):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False))
            fh.write("\n")
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# Read + analyse (used by bin/feedback-mine)
# ---------------------------------------------------------------------------

def iter_feedback_rows(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("schema_id") == SCHEMA_ID and row.get("signal") in VALID_SIGNALS:
                yield row


def summarize_signals(rows: Iterable[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        s = r.get("signal", "")
        counts[s] = counts.get(s, 0) + 1
    return counts


def aggregate_pair_counts(
    rows: Iterable[dict],
    *,
    signal: str,
) -> list[tuple[str, str, int]]:
    """Return ``(prompt, doc_path, count)`` triples for the requested
    signal, sorted desc by count then asc by (prompt, path) for
    determinism."""
    if signal not in VALID_SIGNALS:
        raise ValueError(f"signal must be one of {VALID_SIGNALS}")
    counts: dict[tuple[str, str], int] = {}
    for r in rows:
        if r.get("signal") != signal:
            continue
        prompt = r.get("prompt", "")
        for h in r.get("hits", []):
            path = h.get("path") if isinstance(h, dict) else None
            if not path:
                continue
            key = (prompt, path)
            counts[key] = counts.get(key, 0) + 1
    return sorted(
        ((p, d, n) for (p, d), n in counts.items()),
        key=lambda t: (-t[2], t[0], t[1]),
    )


def golden_promotion_candidates(
    rows: Iterable[dict],
    *,
    min_helpful: int = 2,
) -> list[tuple[str, str, int]]:
    """Pairs that have been marked ``helpful`` ≥ ``min_helpful`` times
    *and* never marked ``not_helpful``. Strong candidates for
    promotion into the P1.1 eval golden set."""
    rows_list = list(rows)
    pos = {(p, d): n for p, d, n in aggregate_pair_counts(rows_list, signal="helpful")}
    neg = {(p, d) for p, d, _ in aggregate_pair_counts(rows_list, signal="not_helpful")}
    keep: list[tuple[str, str, int]] = []
    for (p, d), n in pos.items():
        if n >= min_helpful and (p, d) not in neg:
            keep.append((p, d, n))
    return sorted(keep, key=lambda t: (-t[2], t[0], t[1]))


def cleanup_candidates(
    rows: Iterable[dict],
    *,
    min_not_helpful: int = 2,
) -> list[tuple[str, str, int]]:
    """Pairs marked ``not_helpful`` ≥ ``min_not_helpful`` times. Each
    surfaces a doc that retrieves but consistently misses for that
    prompt — corpus-edit or signal_rules-tweak target."""
    return [
        (p, d, n)
        for p, d, n in aggregate_pair_counts(rows, signal="not_helpful")
        if n >= min_not_helpful
    ]
