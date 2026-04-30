"""CLI: analyse routing decision logs (plan §P5.2).

Reads ``state/repos/<repo>/logs/routing.jsonl`` (or
``state/cs_rag/logs/routing.jsonl`` for ad-hoc invocations) and prints
a one-shot summary so a human (or weekly cron) can see:

- tier distribution — are we routing too many prompts to Tier 0?
- top-N matched tokens per bucket — which keywords carry the
  classifier? are there single tokens dominating that should be
  promoted into a more nuanced rule?

Pure analysis — no LLM calls, no writes. Output is plain text on
stdout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "knowledge" / "cs").exists() and (parent / "scripts").exists():
            return parent
    return here.parents[2]


def main(argv: list[str] | None = None) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(description="Routing log analyzer (plan §P5.2)")
    parser.add_argument("--repo", default=None, help="Repo id; omit for ad-hoc log.")
    parser.add_argument("--top-n", type=int, default=10, help="Top-N tokens per bucket.")
    parser.add_argument(
        "--log-path",
        default=None,
        help="Override log file path (skips repo resolution).",
    )
    args = parser.parse_args(argv)

    sys.path.insert(0, str(repo_root))
    from scripts.workbench.core import routing_log  # noqa: WPS433

    if args.log_path:
        path = Path(args.log_path)
    else:
        path = routing_log.resolve_log_path(repo=args.repo, repo_root=repo_root)

    if not path.exists():
        print(f"[routing-analyze] no log file at {path}", file=sys.stderr)
        return 1

    rows = list(routing_log.iter_log_rows(path))
    if not rows:
        print(f"[routing-analyze] log at {path} contains 0 rows", file=sys.stderr)
        return 1

    print(f"# routing-analyze — {path}")
    print(f"# rows: {len(rows)}")
    print()
    print("## Tier distribution")
    counts = routing_log.summarize_tier_distribution(rows)
    for tier_key in ("tier0", "tier1", "tier2", "tier3", "tier3_blocked", "unknown"):
        if tier_key in counts:
            print(f"  {tier_key}: {counts[tier_key]}")

    print()
    print(f"## Top-{args.top_n} matched tokens per bucket")
    for bucket in ("definition", "depth", "cs_domain", "learning_concept", "coach_request", "tool"):
        top = routing_log.summarize_token_match_frequency(rows, bucket=bucket, top_n=args.top_n)
        if not top:
            continue
        print(f"  [{bucket}]")
        for tok, count in top:
            print(f"    {count:4d}  {tok}")

    # Override summary
    print()
    print("## Override usage")
    override_counts: dict[str, int] = {}
    for r in rows:
        key = (r.get("matched_tokens") or {}).get("override")
        if key:
            override_counts[key] = override_counts.get(key, 0) + 1
    if not override_counts:
        print("  (no overrides recorded)")
    else:
        for key, n in sorted(override_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {key}: {n}")

    # AI fallback usage (P4.4 will start populating ai_unavailable=True)
    ai_unavail = sum(1 for r in rows if r.get("ai_unavailable"))
    print()
    print(f"## AI fallback unavailable: {ai_unavail} / {len(rows)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
