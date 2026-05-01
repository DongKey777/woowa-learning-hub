"""R3 qrel schema with primary/acceptable/forbidden path validation."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from scripts.learning.rag.corpus_lint import parse_frontmatter


QrelRole = Literal["primary", "acceptable", "companion"]
VALID_ROLES = {"primary", "acceptable", "companion"}
VALID_GRADES = {1, 2, 3}
_QUERY_ID_RE = re.compile(r"[^a-zA-Z0-9_.:/-]+")


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


def write_qrels(qrels: list[R3QueryJudgement], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "query_count": len(qrels),
        "queries": [query.to_dict() for query in qrels],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _query_id(concept_id: str, index: int) -> str:
    safe = _QUERY_ID_RE.sub("-", concept_id.strip()).strip("-")
    return f"{safe}:expected:{index + 1}"


def qrels_from_frontmatter_doc(
    file_path: Path,
    text: str,
    *,
    corpus_root: Path | None = None,
) -> list[R3QueryJudgement]:
    """Generate primary/forbidden qrel seeds from Corpus v2 frontmatter."""

    fm = parse_frontmatter(text)
    if not fm or str(fm.get("schema_version")) != "2":
        return []
    concept_id = str(fm.get("concept_id") or "").strip()
    expected_queries = fm.get("expected_queries") or []
    if not concept_id or not isinstance(expected_queries, list):
        return []

    if corpus_root is not None:
        try:
            qrel_path = str(file_path.relative_to(corpus_root))
        except ValueError:
            qrel_path = str(file_path)
    else:
        qrel_path = str(file_path)
    if not qrel_path.startswith("contents/") and corpus_root is not None:
        qrel_path = f"contents/{qrel_path}"

    forbidden = tuple(str(path) for path in (fm.get("forbidden_neighbors") or []))
    tags = tuple(
        str(tag)
        for tag in (
            "corpus_v2",
            f"concept:{concept_id}",
            f"doc_role:{fm.get('doc_role', 'unknown')}",
            f"level:{fm.get('level', 'unknown')}",
        )
    )
    out: list[R3QueryJudgement] = []
    for index, prompt in enumerate(expected_queries):
        if not isinstance(prompt, str) or not prompt.strip():
            continue
        out.append(
            R3QueryJudgement(
                query_id=_query_id(concept_id, index),
                prompt=prompt.strip(),
                qrels=(R3Qrel(path=qrel_path, grade=3, role="primary"),),
                forbidden_paths=forbidden,
                tags=tags,
            )
        )
    return out


def qrels_from_corpus(corpus_root: Path) -> list[R3QueryJudgement]:
    out: list[R3QueryJudgement] = []
    for path in sorted(corpus_root.rglob("*.md")):
        out.extend(
            qrels_from_frontmatter_doc(
                path,
                path.read_text(encoding="utf-8"),
                corpus_root=corpus_root,
            )
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    qrels = qrels_from_corpus(args.corpus_root)
    write_qrels(qrels, args.out)
    print(f"wrote {len(qrels)} R3 qrel(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
