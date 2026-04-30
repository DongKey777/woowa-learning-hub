"""CLI: surface negative + positive feedback pairs (plan §P7.2).

Reads either the global ``state/cs_rag/feedback.jsonl`` or the
per-repo ``state/repos/<repo>/logs/rag_feedback.jsonl`` and prints:

- Signal distribution (helpful / not_helpful / unclear).
- Top-N "not_helpful" (prompt, doc) pairs — corpus cleanup or
  signal_rules tweak candidates.
- Top-N "helpful" (prompt, doc) pairs that are *clean* (never marked
  not_helpful) — golden eval promotion candidates.
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


def _resolve_log_path(repo: str | None, repo_root: Path) -> Path:
    if repo:
        return repo_root / "state" / "repos" / repo / "logs" / "rag_feedback.jsonl"
    return repo_root / "state" / "cs_rag" / "feedback.jsonl"


def main(argv: list[str] | None = None) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(description="Mine the learner feedback log (plan §P7.2).")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--top-n", type=int, default=15)
    parser.add_argument("--min-helpful", type=int, default=2)
    parser.add_argument("--min-not-helpful", type=int, default=2)
    parser.add_argument("--log-path", default=None, help="Override log file path.")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(repo_root))
    from scripts.learning.rag import feedback  # noqa: WPS433

    path = Path(args.log_path) if args.log_path else _resolve_log_path(args.repo, repo_root)

    if not path.exists():
        print(f"[feedback-mine] no log at {path}", file=sys.stderr)
        return 1

    rows = list(feedback.iter_feedback_rows(path))
    if not rows:
        print(f"[feedback-mine] {path} contains 0 valid rows", file=sys.stderr)
        return 1

    print(f"# feedback-mine — {path}")
    print(f"# rows: {len(rows)}")

    print()
    print("## Signal distribution")
    counts = feedback.summarize_signals(rows)
    for sig in ("helpful", "not_helpful", "unclear"):
        print(f"  {sig}: {counts.get(sig, 0)}")

    print()
    print(f"## Top-{args.top_n} not_helpful (prompt, doc) pairs (≥ {args.min_not_helpful})")
    cleanup = feedback.cleanup_candidates(rows, min_not_helpful=args.min_not_helpful)
    if not cleanup:
        print("  (none)")
    else:
        for prompt, doc, n in cleanup[: args.top_n]:
            preview = prompt if len(prompt) <= 60 else prompt[:57] + "..."
            print(f"  {n:3d}  [{doc}] {preview}")

    print()
    print(
        f"## Top-{args.top_n} helpful pairs — never marked not_helpful "
        f"(≥ {args.min_helpful})"
    )
    promotions = feedback.golden_promotion_candidates(rows, min_helpful=args.min_helpful)
    if not promotions:
        print("  (none)")
    else:
        for prompt, doc, n in promotions[: args.top_n]:
            preview = prompt if len(prompt) <= 60 else prompt[:57] + "..."
            print(f"  {n:3d}  [{doc}] {preview}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
