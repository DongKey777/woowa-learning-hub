"""JSONL trace contract for R3 retrieval stages."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..candidate import Candidate
from ..query_plan import QueryPlan


@dataclass(frozen=True)
class R3Trace:
    trace_id: str
    query_plan: QueryPlan
    candidates: tuple[Candidate, ...] = ()
    final_paths: tuple[str, ...] = ()
    stage_ms: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_query_plan(cls, query_plan: QueryPlan) -> "R3Trace":
        return cls(trace_id=str(uuid.uuid4()), query_plan=query_plan)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "query_plan": self.query_plan.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "final_paths": list(self.final_paths),
            "stage_ms": dict(self.stage_ms),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, blob: dict[str, Any]) -> "R3Trace":
        return cls(
            trace_id=str(blob["trace_id"]),
            query_plan=QueryPlan.from_dict(blob["query_plan"]),
            candidates=tuple(
                Candidate.from_dict(candidate)
                for candidate in blob.get("candidates", [])
            ),
            final_paths=tuple(blob.get("final_paths") or ()),
            stage_ms={k: float(v) for k, v in (blob.get("stage_ms") or {}).items()},
            metadata=dict(blob.get("metadata") or {}),
        )


def write_jsonl(traces: Iterable[R3Trace], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for trace in traces:
            fh.write(json.dumps(trace.to_dict(), ensure_ascii=False, sort_keys=True))
            fh.write("\n")


def read_jsonl(path: Path) -> list[R3Trace]:
    traces: list[R3Trace] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            traces.append(R3Trace.from_dict(json.loads(line)))
    return traces
