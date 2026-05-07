"""CLI for assistant response-quality telemetry."""

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
    parser = argparse.ArgumentParser(
        description="Record compact assistant response-quality telemetry.",
    )
    parser.add_argument("--source-event-id", required=True)
    parser.add_argument("--turn-id", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--response-summary", required=True)
    parser.add_argument("--response-text", default=None)
    parser.add_argument(
        "--response-file",
        default=None,
        help="Read response text from a file. Use '-' to read stdin.",
    )
    parser.add_argument("--expected-citation", action="append", default=[])
    parser.add_argument("--declared-citation", action="append", default=[])
    parser.add_argument("--quality-flag", action="append", default=[])
    parser.add_argument("--contract-flag", action="append", default=[])
    parser.add_argument("--strategy", action="append", default=[])
    parser.add_argument("--model-runtime", default=None)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--note", default=None)
    parser.add_argument("--require-rag-header", action="store_true")
    parser.add_argument("--silent", action="store_true")
    args = parser.parse_args(argv)

    response_text = args.response_text
    if args.response_file == "-":
        response_text = sys.stdin.read()
    elif args.response_file:
        response_text = Path(args.response_file).read_text(encoding="utf-8")

    sys.path.insert(0, str(repo_root))
    from scripts.workbench.core import response_quality  # noqa: WPS433

    try:
        paths = response_quality.append_response_quality(
            source_event_id=args.source_event_id,
            turn_id=args.turn_id,
            prompt=args.prompt,
            response_text=response_text,
            response_summary=args.response_summary,
            citation_paths_expected=args.expected_citation,
            citation_paths_declared=args.declared_citation,
            quality_flags=args.quality_flag,
            contract_flags=args.contract_flag,
            answer_strategy=args.strategy,
            model_runtime=args.model_runtime,
            repo=args.repo,
            repo_root=repo_root,
            note=args.note,
            require_rag_header=args.require_rag_header,
        )
    except ValueError as exc:
        print(f"[learn-response-quality] {exc}", file=sys.stderr)
        return 2

    if not args.silent:
        print(json.dumps(
            {
                "recorded": True,
                "source_event_id": args.source_event_id,
                "turn_id": args.turn_id,
                "paths": [str(path) for path in paths],
            },
            ensure_ascii=False,
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
