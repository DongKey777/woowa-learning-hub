"""CLI helper to generate R3 skeleton traces from a qrel fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..query_plan import build_query_plan
from .qrels import load_qrels
from .trace import R3Trace, write_jsonl


def build_traces_from_qrels(qrels_path: Path) -> list[R3Trace]:
    traces: list[R3Trace] = []
    for query in load_qrels(qrels_path):
        plan = build_query_plan(query.prompt)
        traces.append(
            R3Trace(
                trace_id=query.query_id,
                query_plan=plan,
                metadata={
                    "qrels": [qrel.to_dict() for qrel in query.qrels],
                    "forbidden_paths": list(query.forbidden_paths),
                    "tags": list(query.tags),
                },
            )
        )
    return traces


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    traces = build_traces_from_qrels(args.qrels)
    write_jsonl(traces, args.out)
    print(f"wrote {len(traces)} R3 trace(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
