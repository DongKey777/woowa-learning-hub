"""Cohort-aware qrel loader for the Real qrel suite (Phase 3 / Pilot
measurement gate).

The legacy ``qrels.py`` schema (R3QueryJudgement / R3Qrel) was designed
for the Corpus v2 / expected_queries-derived qrels. The Real qrel suite
(human-curated, cohort-stratified) uses a different schema per
``docs/worklogs/rag-r3-pilot-50-docs-selection.md`` Phase 3:

* ``query_id``, ``prompt``, ``language``, ``intent``, ``level``
* ``cohort_tag``  — one of paraphrase_human / confusable_pairs /
                    symptom_to_cause / mission_bridge / corpus_gap_probe /
                    forbidden_neighbor
* ``primary_paths`` / ``acceptable_paths`` / ``forbidden_paths``
* ``expected_concepts`` (concept_ids the answer should reference)
* ``failure_focus`` (free-form failure tag list — feeds the failure
  taxonomy classifier in Phase 6.3)
* ``rationale`` (human-authored explanation for QA review)

This module owns the dataclass + JSON loader. The eval harness in
``cohort_eval.py`` consumes ``CohortQuery`` records and never touches
the raw JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VALID_COHORTS = frozenset({
    "paraphrase_human",
    "confusable_pairs",
    "symptom_to_cause",
    "mission_bridge",
    "corpus_gap_probe",
    "forbidden_neighbor",
})


@dataclass(frozen=True)
class CohortQuery:
    """One human-curated query in the Real qrel suite."""

    query_id: str
    prompt: str
    language: str
    intent: str
    level: str
    cohort_tag: str
    primary_paths: tuple[str, ...]
    acceptable_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()
    expected_concepts: tuple[str, ...] = ()
    failure_focus: tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.query_id:
            raise ValueError("query_id is required")
        if not self.prompt:
            raise ValueError(f"prompt is required for {self.query_id!r}")
        if self.cohort_tag not in VALID_COHORTS:
            raise ValueError(
                f"unknown cohort_tag {self.cohort_tag!r} (valid: "
                f"{sorted(VALID_COHORTS)})"
            )
        # corpus_gap_probe and forbidden_neighbor cohorts may legitimately
        # have empty primary_paths (the answer should be a refusal) so we
        # do not enforce primary_paths ≥ 1 universally.
        if self.cohort_tag not in {"corpus_gap_probe", "forbidden_neighbor"}:
            if not self.primary_paths:
                raise ValueError(
                    f"{self.query_id!r}: cohort {self.cohort_tag!r} requires "
                    f"at least one primary_path"
                )
        # primary ⊥ forbidden invariant (case-sensitive — paths are exact)
        overlap = set(self.primary_paths) & set(self.forbidden_paths)
        if overlap:
            raise ValueError(
                f"{self.query_id!r}: primary ⊥ forbidden violated "
                f"(overlap: {sorted(overlap)})"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "prompt": self.prompt,
            "language": self.language,
            "intent": self.intent,
            "level": self.level,
            "cohort_tag": self.cohort_tag,
            "primary_paths": list(self.primary_paths),
            "acceptable_paths": list(self.acceptable_paths),
            "forbidden_paths": list(self.forbidden_paths),
            "expected_concepts": list(self.expected_concepts),
            "failure_focus": list(self.failure_focus),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class CohortQrelSuite:
    schema_version: int
    queries: tuple[CohortQuery, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_cohort(self) -> dict[str, list[CohortQuery]]:
        out: dict[str, list[CohortQuery]] = {tag: [] for tag in VALID_COHORTS}
        for q in self.queries:
            out[q.cohort_tag].append(q)
        return out

    def cohort_counts(self) -> dict[str, int]:
        return {tag: len(qs) for tag, qs in self.by_cohort().items()}


def _record_to_query(record: dict[str, Any]) -> CohortQuery:
    return CohortQuery(
        query_id=str(record["query_id"]),
        prompt=str(record["prompt"]),
        language=str(record.get("language", "ko")),
        intent=str(record.get("intent", "definition")),
        level=str(record.get("level", "beginner")),
        cohort_tag=str(record["cohort_tag"]),
        primary_paths=tuple(record.get("primary_paths") or ()),
        acceptable_paths=tuple(record.get("acceptable_paths") or ()),
        forbidden_paths=tuple(record.get("forbidden_paths") or ()),
        expected_concepts=tuple(record.get("expected_concepts") or ()),
        failure_focus=tuple(record.get("failure_focus") or ()),
        rationale=str(record.get("rationale") or ""),
    )


def load_cohort_qrels(path: Path) -> CohortQrelSuite:
    """Load a cohort-tagged qrel JSON. Accepts either:
    - root list of records, or
    - {"queries": [...], "schema_version": N, ...} envelope
    """
    blob = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(blob, list):
        records = blob
        schema_version = 1
        metadata: dict[str, Any] = {}
    elif isinstance(blob, dict):
        records = blob.get("queries") or []
        schema_version = int(blob.get("schema_version", 1))
        # Carry every non-queries top-level field as metadata so the
        # author / generator hash / curation_status etc travel with the
        # suite into eval reports.
        metadata = {k: v for k, v in blob.items() if k != "queries"}
    else:
        raise ValueError(f"unexpected JSON root in {path}")
    if not isinstance(records, list):
        raise ValueError(f"{path}: 'queries' must be a list")
    queries = tuple(_record_to_query(r) for r in records)
    return CohortQrelSuite(
        schema_version=schema_version,
        queries=queries,
        metadata=metadata,
    )


def write_cohort_qrels(suite: CohortQrelSuite, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **suite.metadata,
        "schema_version": suite.schema_version,
        "query_count": len(suite.queries),
        "queries": [q.to_dict() for q in suite.queries],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
