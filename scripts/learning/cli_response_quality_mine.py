"""CLI: mine assistant response-quality telemetry."""

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
        return repo_root / "state" / "repos" / repo / "logs" / "response_quality.jsonl"
    return repo_root / "state" / "learner" / "response-quality.jsonl"


def _preview(text: str, limit: int = 70) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main(argv: list[str] | None = None) -> int:
    repo_root = _find_repo_root()
    parser = argparse.ArgumentParser(
        description="Mine assistant response-quality telemetry.",
    )
    parser.add_argument("--repo", default=None)
    parser.add_argument("--top-n", type=int, default=15)
    parser.add_argument("--log-path", default=None)
    args = parser.parse_args(argv)

    sys.path.insert(0, str(repo_root))
    from scripts.workbench.core import response_quality  # noqa: WPS433

    path = Path(args.log_path) if args.log_path else _resolve_log_path(args.repo, repo_root)
    if not path.exists():
        print(f"[response-quality-mine] no log at {path}", file=sys.stderr)
        return 1

    rows = list(response_quality.iter_response_quality_rows(path))
    if not rows:
        print(f"[response-quality-mine] {path} contains 0 valid rows", file=sys.stderr)
        return 1

    print(f"# response-quality-mine — {path}")
    print(f"# rows: {len(rows)}")

    print()
    print("## Quality flag distribution")
    flags = response_quality.summarize_quality_flags(rows)
    if not flags:
        print("  (none)")
    else:
        for flag, count in flags[: args.top_n]:
            print(f"  {count:3d}  {flag}")

    print()
    print(f"## Top-{args.top_n} citation mismatch candidates")
    mismatches = response_quality.citation_mismatch_candidates(rows)
    if not mismatches:
        print("  (none)")
    else:
        for prompt, expected, declared, count in mismatches[: args.top_n]:
            print(f"  {count:3d}  prompt={_preview(prompt)}")
            print(f"       expected={_preview(expected)}")
            print(f"       declared={_preview(declared)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
