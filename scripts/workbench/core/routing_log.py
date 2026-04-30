"""Routing decision logger (plan §P5.2).

Every ``classify()`` decision is appended as one JSONL row so we can
later analyse Tier distribution, oft-mis-classified prompts, and the
fraction of decisions that round-tripped through the AI fallback
(P4.4).

Pure I/O helper. The classifier itself stays I/O-free — the runtime
caller (``scripts/workbench/cli.py:cmd_rag_ask``) is responsible for
calling ``record_routing_decision`` after ``classify()`` returns.

## Schema

One JSONL row per classify call::

    {
      "schema_id": "routing-log-v1",
      "logged_at": "2026-04-30T12:34:56+00:00",
      "repo": "tobys-mission-1",
      "prompt": "스프링 빈 뭐야?",
      "tier": 1,
      "mode": "cheap",
      "reason": "domain + definition signal",
      "experience_level": "beginner" | null,
      "override_active": false,
      "blocked": false,
      "promoted_by_profile": false,
      "matched_tokens": {
        "definition": ["뭐야"],
        "depth": [],
        "cs_domain": [],
        "learning_concept": ["bean"],
        "coach_request": [],
        "tool": [],
        "override": null
      },
      "ai_unavailable": false
    }

``ai_unavailable=true`` is recorded by P4.4 when the AI session was
not available to classify a low-confidence prompt — used to filter
log analysis by "would have asked AI but couldn't".

## Storage

``state/repos/<repo>/logs/routing.jsonl`` (append-only). When ``repo``
is empty/None we fall back to ``state/cs_rag/logs/routing.jsonl`` so
ad-hoc shell calls outside a mission still produce a log.

## Atomic append

JSONL is naturally append-only on POSIX — concurrent appends from
different processes interleave by line, never corrupting an existing
row. We open with ``"a"`` and write a single ``json.dumps()`` line
followed by ``\\n``. No fsync — durability is best-effort, the goal
is *aggregate* analysis, not per-row correctness.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from . import lexicon


SCHEMA_ID = "routing-log-v1"
DEFAULT_AD_HOC_LOG_REL = Path("state") / "cs_rag" / "logs" / "routing.jsonl"


def _matched_tokens(prompt: str, tokens: Iterable[str]) -> list[str]:
    """Return the tokens from ``tokens`` that match ``prompt`` under
    the word-boundary contract. Sorted for determinism."""
    return sorted(
        [t for t in tokens if lexicon.match_word_boundary_one(prompt, t)],
    )


def _matched_override(prompt: str) -> str | None:
    """Return the override key whose token matched ``prompt``, or None."""
    for key, tokens in lexicon.OVERRIDE_TOKENS.items():
        if lexicon.match_word_boundary(prompt, tokens):
            return key
    return None


def collect_matched_tokens(prompt: str) -> dict[str, list[str] | str | None]:
    """Snapshot of which token sets matched the prompt.

    Useful for post-hoc analysis: "the heuristic chose Tier 1 because
    ``뭐야`` matched DEFINITION_SIGNALS and ``bean`` matched
    LEARNING_CONCEPT_TOKENS." Stored alongside the decision.
    """
    return {
        "definition": _matched_tokens(prompt, lexicon.DEFINITION_SIGNALS),
        "depth": _matched_tokens(prompt, lexicon.DEPTH_SIGNALS),
        "cs_domain": _matched_tokens(prompt, lexicon.CS_DOMAIN_TOKENS),
        "learning_concept": _matched_tokens(prompt, lexicon.LEARNING_CONCEPT_TOKENS),
        "coach_request": _matched_tokens(prompt, lexicon.COACH_REQUEST_TOKENS),
        "tool": _matched_tokens(prompt, lexicon.TOOL_TOKENS),
        "override": _matched_override(prompt),
    }


def resolve_log_path(
    *,
    repo: str | None,
    repo_root: Path,
    ad_hoc_path: Path | None = None,
) -> Path:
    """Return the JSONL path to append to.

    ``repo`` is the mission repo identifier (string registered in
    repo-registry). When set, logs go under
    ``state/repos/<repo>/logs/routing.jsonl``; otherwise to
    ``state/cs_rag/logs/routing.jsonl`` (ad-hoc / shell-direct
    invocations).
    """
    if repo:
        return repo_root / "state" / "repos" / repo / "logs" / "routing.jsonl"
    return ad_hoc_path or (repo_root / DEFAULT_AD_HOC_LOG_REL)


def build_log_row(
    *,
    prompt: str,
    decision,
    repo: str | None,
    ai_unavailable: bool = False,
    now: datetime | None = None,
) -> dict:
    """Build a single JSONL row from a classify() decision.

    ``decision`` is duck-typed: must expose tier/mode/reason/
    experience_level/override_active/blocked/promoted_by_profile, or
    be a dataclass / mapping with those keys. RouterDecision is the
    canonical shape but a plain dict works too (eases downstream
    consumers like rag-ask cli wrapping).
    """
    if is_dataclass(decision):
        d = asdict(decision)
    elif isinstance(decision, dict):
        d = decision
    else:
        d = {
            "tier": getattr(decision, "tier", None),
            "mode": getattr(decision, "mode", None),
            "reason": getattr(decision, "reason", None),
            "experience_level": getattr(decision, "experience_level", None),
            "override_active": getattr(decision, "override_active", False),
            "blocked": getattr(decision, "blocked", False),
            "promoted_by_profile": getattr(decision, "promoted_by_profile", False),
        }
    return {
        "schema_id": SCHEMA_ID,
        "logged_at": (now or datetime.now(timezone.utc)).isoformat(),
        "repo": repo or "",
        "prompt": prompt,
        "tier": d.get("tier"),
        "mode": d.get("mode"),
        "reason": d.get("reason"),
        "experience_level": d.get("experience_level"),
        "override_active": bool(d.get("override_active", False)),
        "blocked": bool(d.get("blocked", False)),
        "promoted_by_profile": bool(d.get("promoted_by_profile", False)),
        "matched_tokens": collect_matched_tokens(prompt),
        "ai_unavailable": bool(ai_unavailable),
    }


def record_routing_decision(
    *,
    prompt: str,
    decision,
    repo: str | None,
    repo_root: Path,
    ai_unavailable: bool = False,
    now: datetime | None = None,
) -> Path:
    """Append a row to the routing JSONL log. Returns the path written.

    Best-effort: any I/O exception bubbles up. The caller in
    ``cmd_rag_ask`` should treat logging as non-critical and catch.
    """
    row = build_log_row(
        prompt=prompt,
        decision=decision,
        repo=repo,
        ai_unavailable=ai_unavailable,
        now=now,
    )
    path = resolve_log_path(repo=repo, repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False))
        fh.write("\n")
    return path


# ---------------------------------------------------------------------------
# Analysis helpers (used by bin/routing-analyze)
# ---------------------------------------------------------------------------

def iter_log_rows(path: Path) -> Iterable[dict]:
    """Yield validated JSONL rows from ``path``. Skips lines that fail
    to parse (corrupt, partial write) — analysis must be resilient."""
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
            if row.get("schema_id") == SCHEMA_ID:
                yield row


def summarize_tier_distribution(rows: Iterable[dict]) -> dict[str, int]:
    """Count rows by tier label. Returns a dict like ``{"tier0": 14,
    "tier1": 5, "tier2": 8, "tier3": 2, "tier3_blocked": 1}``."""
    counts: dict[str, int] = {}
    for r in rows:
        tier = r.get("tier")
        blocked = r.get("blocked", False)
        if tier == 3 and blocked:
            key = "tier3_blocked"
        elif tier in (0, 1, 2, 3):
            key = f"tier{tier}"
        else:
            key = "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def summarize_token_match_frequency(
    rows: Iterable[dict],
    *,
    bucket: str,
    top_n: int = 20,
) -> list[tuple[str, int]]:
    """Return the top-N most frequently matched tokens in
    ``matched_tokens[bucket]`` across rows. Sorted desc by count, then
    asc by token for determinism."""
    counts: dict[str, int] = {}
    for r in rows:
        tokens = (r.get("matched_tokens") or {}).get(bucket) or []
        if not isinstance(tokens, list):
            continue
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
