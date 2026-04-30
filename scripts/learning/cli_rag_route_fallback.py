"""CLI for router-fallback-v1 wrapper (plan §P4.4 / §9 element 3).

The wrapper is deterministic: it accepts the heuristic's decision (the
context the AI needs), computes a stable ``prompt_hash``, writes the
input artifact, and prints the expected output path. The AI session is
the *caller* — it runs this wrapper inside its turn, reads the input,
follows ``skills/woowa-rag-route/SKILL.md``, and writes the output
JSON. The downstream router caller validates the output, appends it
to ``state/repos/<repo>/logs/routing_ai_decisions.jsonl``, and uses
the chosen tier/mode.

This file never calls an LLM. It is a pure placeholder factory.

Schema (canonical): ``docs/ai-behavior-contracts.md``
§router-fallback-v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_ID_INPUT = "router-fallback-v1.input"
DEFAULT_OUT_REL = "state/cs_rag/router_fallback"
ALL_TIERS = (0, 1, 2, 3)


# ---------------------------------------------------------------------------
# prompt_hash
# ---------------------------------------------------------------------------

def compute_prompt_hash(prompt: str, candidate_tiers: tuple[int, ...]) -> str:
    """Hash the prompt + candidate_tiers so two routings of the same
    prompt with different tier preconditions (e.g. PR closed) produce
    different cache keys."""
    norm = prompt.strip()
    tiers = ",".join(str(t) for t in sorted(candidate_tiers))
    payload = f"{tiers}\x1f{norm}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


# ---------------------------------------------------------------------------
# parsing helpers
# ---------------------------------------------------------------------------

def parse_candidate_tiers(raw: str) -> tuple[int, ...]:
    """Parse "0,1,2,3" or "1,2" into a sorted tuple of ints. Empty raw
    string is rejected. Tiers must be a subset of {0,1,2,3}."""
    if not raw or not raw.strip():
        raise ValueError("candidate_tiers must not be empty")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    tiers: list[int] = []
    for p in parts:
        try:
            t = int(p)
        except ValueError as exc:
            raise ValueError(f"candidate_tiers contains non-integer: {p}") from exc
        if t not in ALL_TIERS:
            raise ValueError(f"candidate_tiers value {t} not in {ALL_TIERS}")
        tiers.append(t)
    if not tiers:
        raise ValueError("candidate_tiers parsed to empty list")
    # de-dupe + sort for canonical hashing
    return tuple(sorted(set(tiers)))


def parse_matched_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tok.strip() for tok in raw.split(",") if tok.strip()]


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "knowledge" / "cs").exists() and (parent / "scripts").exists():
            return parent
    return here.parents[2]


def write_input_artifact(
    *,
    prompt: str,
    heuristic_tier: int,
    heuristic_confidence: float,
    matched_tokens: list[str],
    candidate_tiers: tuple[int, ...],
    history_summary: str | None,
    out_root: Path,
    now: datetime | None = None,
) -> tuple[Path, Path, str]:
    """Write input artifact and return (input_path, output_path, prompt_hash)."""
    if heuristic_tier not in ALL_TIERS:
        raise ValueError(f"heuristic_tier {heuristic_tier} not in {ALL_TIERS}")
    if not (0.0 <= heuristic_confidence <= 1.0):
        raise ValueError("heuristic_confidence out of [0, 1]")

    prompt_hash = compute_prompt_hash(prompt, candidate_tiers)
    out_root.mkdir(parents=True, exist_ok=True)
    input_path = out_root / f"{prompt_hash}.input.json"
    output_path = out_root / f"{prompt_hash}.output.json"
    payload = {
        "schema_id": SCHEMA_ID_INPUT,
        "prompt_hash": prompt_hash,
        "prompt": prompt,
        "history_summary": history_summary,
        "candidate_tiers": list(candidate_tiers),
        "heuristic_decision": {
            "tier": heuristic_tier,
            "confidence": heuristic_confidence,
            "matched_tokens": list(matched_tokens),
        },
        "produced_at": (now or datetime.now(timezone.utc)).isoformat(),
    }
    input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return input_path, output_path, prompt_hash


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(
        description=(
            "router-fallback-v1 wrapper. Writes the input artifact "
            "and prints the expected output path. The AI session is "
            "responsible for filling the output (see "
            "skills/woowa-rag-route/SKILL.md)."
        )
    )
    parser.add_argument("prompt", help="Original learner question.")
    parser.add_argument("--heuristic-tier", type=int, required=True, choices=list(ALL_TIERS))
    parser.add_argument("--heuristic-confidence", type=float, required=True)
    parser.add_argument(
        "--matched-tokens",
        default="",
        help="Comma-separated tokens the heuristic matched (for AI context).",
    )
    parser.add_argument(
        "--candidate-tiers",
        default="0,1,2,3",
        help='Allowed tiers as "0,1,2,3" (default). Useful when tier 3 preconditions are missing.',
    )
    parser.add_argument(
        "--history-summary",
        default=None,
        help="Optional one-line summary of recent turn topics for context.",
    )
    parser.add_argument(
        "--out",
        default=str(repo_root / DEFAULT_OUT_REL),
        help=f"Storage root (default: {DEFAULT_OUT_REL}).",
    )
    args = parser.parse_args(argv)

    if not args.prompt or not args.prompt.strip():
        print("[rag-route-fallback] prompt is empty", file=sys.stderr)
        return 2

    try:
        candidate_tiers = parse_candidate_tiers(args.candidate_tiers)
    except ValueError as exc:
        print(f"[rag-route-fallback] --candidate-tiers: {exc}", file=sys.stderr)
        return 2

    matched_tokens = parse_matched_tokens(args.matched_tokens)

    try:
        input_path, output_path, prompt_hash = write_input_artifact(
            prompt=args.prompt,
            heuristic_tier=args.heuristic_tier,
            heuristic_confidence=args.heuristic_confidence,
            matched_tokens=matched_tokens,
            candidate_tiers=candidate_tiers,
            history_summary=args.history_summary,
            out_root=Path(args.out),
        )
    except ValueError as exc:
        print(f"[rag-route-fallback] {exc}", file=sys.stderr)
        return 2

    print(json.dumps(
        {
            "schema_id": SCHEMA_ID_INPUT,
            "prompt_hash": prompt_hash,
            "candidate_tiers": list(candidate_tiers),
            "input_path": str(input_path),
            "output_path": str(output_path),
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
