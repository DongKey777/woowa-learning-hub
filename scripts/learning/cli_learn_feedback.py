"""CLI for the rag-feedback writer (plan §P7.1)."""

from __future__ import annotations

import argparse
import json
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
    parser = argparse.ArgumentParser(description="Record learner hit-relevance feedback (plan §P7.1).")
    parser.add_argument("prompt", help="Original learner question.")
    parser.add_argument(
        "--signal",
        choices=("helpful", "not_helpful", "unclear"),
        required=True,
    )
    parser.add_argument(
        "--hit",
        action="append",
        default=[],
        help="Doc path that was returned to the learner. Repeat for multiple.",
    )
    parser.add_argument("--note", default=None)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--source-event-id", default=None)
    parser.add_argument("--turn-id", default=None)
    args = parser.parse_args(argv)

    sys.path.insert(0, str(repo_root))
    from scripts.learning.rag import feedback  # noqa: WPS433

    if not args.prompt or not args.prompt.strip():
        print("[learn-feedback] prompt is empty", file=sys.stderr)
        return 2

    try:
        paths = feedback.append_feedback(
            prompt=args.prompt,
            signal=args.signal,
            hits=[{"path": h} for h in args.hit],
            repo=args.repo,
            repo_root=repo_root,
            note=args.note,
            source_event_id=args.source_event_id,
            turn_id=args.turn_id,
        )
    except ValueError as exc:
        print(f"[learn-feedback] {exc}", file=sys.stderr)
        return 2

    print(json.dumps(
        {
            "recorded": True,
            "signal": args.signal,
            "hits": len(args.hit),
            "paths": [str(p) for p in paths],
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
