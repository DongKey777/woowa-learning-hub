"""R3 qrel schema with primary/acceptable/forbidden path validation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal


QrelRole = Literal["primary", "acceptable", "companion"]
VALID_ROLES = {"primary", "acceptable", "companion"}
VALID_GRADES = {1, 2, 3}


@dataclass(frozen=True)
class R3Qrel:
    path: str
    grade: int
    role: QrelRole

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("qrel path is required")
        if self.grade not in VALID_GRADES:
            raise ValueError(f"invalid qrel grade: {self.grade!r}")
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid qrel role: {self.role!r}")
        expected_grade = {"primary": 3, "acceptable": 2, "companion": 1}[self.role]
        if self.grade != expected_grade:
            raise ValueError(
                f"qrel role {self.role!r} requires grade {expected_grade}, got {self.grade}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R3QueryJudgement:
    query_id: str
    prompt: str
    qrels: tuple[R3Qrel, ...]
    forbidden_paths: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.query_id:
            raise ValueError("query_id is required")
        if not self.prompt:
            raise ValueError(f"prompt is required for query {self.query_id!r}")
        primary = self.primary_paths()
        if not primary:
            raise ValueError(f"query {self.query_id!r} must have at least one primary qrel")
        qrel_paths = {q.path for q in self.qrels}
        forbidden = set(self.forbidden_paths)
        overlap = qrel_paths & forbidden
        if overlap:
            raise ValueError(
                f"query {self.query_id!r} has qrel/forbidden overlap: {sorted(overlap)}"
            )

    def primary_paths(self) -> set[str]:
        return {q.path for q in self.qrels if q.role == "primary"}

    def acceptable_paths(self) -> set[str]:
        return {q.path for q in self.qrels if q.role == "acceptable"}

    def companion_paths(self) -> set[str]:
        return {q.path for q in self.qrels if q.role == "companion"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "prompt": self.prompt,
            "qrels": [q.to_dict() for q in self.qrels],
            "forbidden_paths": list(self.forbidden_paths),
            "tags": list(self.tags),
        }


def _record_to_query(record: dict[str, Any]) -> R3QueryJudgement:
    return R3QueryJudgement(
        query_id=str(record["query_id"]),
        prompt=str(record["prompt"]),
        qrels=tuple(
            R3Qrel(
                path=str(q["path"]),
                grade=int(q["grade"]),
                role=q["role"],
            )
            for q in record.get("qrels", [])
        ),
        forbidden_paths=tuple(record.get("forbidden_paths") or ()),
        tags=tuple(record.get("tags") or ()),
    )


def load_qrels(path: Path) -> list[R3QueryJudgement]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        records = payload.get("queries")
    else:
        records = payload
    if not isinstance(records, list):
        raise ValueError(f"unexpected qrel root in {path}")
    return [_record_to_query(record) for record in records]
