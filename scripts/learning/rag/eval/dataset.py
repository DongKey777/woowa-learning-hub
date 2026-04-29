"""Graded fixture schema, loader, and legacy-golden converter.

Fixture schema (per query) — see plan §P1.1 step 1::

    {
      "query_id": str,
      "prompt": str,
      "mode": "cheap" | "full",
      "experience_level": "beginner" | "intermediate" | "advanced" | None,
      "learning_points": list[str],
      "bucket": {"category": str, "difficulty": str, "language": str, "intent": str},
      "qrels": list[{"path": str, "grade": 1|2|3, "role": "primary"|"acceptable"|"companion"}],
      "forbidden_paths": list[str],
      "rank_budget": {"primary_max_rank": int, "companion_max_rank": int},
      "bucket_source": "auto" | "manual"
    }

Legacy golden conversion: ``expected_path → grade 3 (primary)``,
``acceptable_paths → grade 2 (acceptable)``, ``companion_paths → grade 1
(companion)``. Bucket fields are inferred from path/prompt heuristics
because YAML frontmatter is not introduced until P5.3.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable, Literal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRIMARY_GRADE = 3
ACCEPTABLE_GRADE = 2
COMPANION_GRADE = 1

DEFAULT_PRIMARY_MAX_RANK = 1
DEFAULT_COMPANION_MAX_RANK = 4
DEFAULT_MODE: Literal["full"] = "full"

VALID_GRADES = (1, 2, 3)
VALID_ROLES = ("primary", "acceptable", "companion")
VALID_MODES = ("cheap", "full")
VALID_INTENTS = ("definition", "comparison", "symptom", "deep-dive", "unknown")

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Qrel:
    """One judged document for a query."""

    path: str
    grade: int
    role: str

    def __post_init__(self) -> None:
        if self.grade not in VALID_GRADES:
            raise ValueError(f"invalid grade: {self.grade!r} (allowed: {VALID_GRADES})")
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role: {self.role!r} (allowed: {VALID_ROLES})")


@dataclass(frozen=True)
class Bucket:
    """Stratification axes used for macro averaging in eval/buckets.py."""

    category: str
    difficulty: str  # "beginner" | "intermediate" | "advanced" | "unknown"
    language: str  # "ko" | "en" | "mixed"
    intent: str  # see VALID_INTENTS


@dataclass(frozen=True)
class RankBudget:
    """Hard regression budget — primary must show within primary_max_rank."""

    primary_max_rank: int
    companion_max_rank: int


@dataclass(frozen=True)
class GradedQuery:
    """One fixture query in the graded-relevance schema (plan §P1.1 step 1)."""

    query_id: str
    prompt: str
    mode: str
    experience_level: str | None
    learning_points: tuple[str, ...]
    bucket: Bucket
    qrels: tuple[Qrel, ...]
    forbidden_paths: tuple[str, ...]
    rank_budget: RankBudget
    bucket_source: str  # "auto" | "manual"

    def primary_paths(self) -> set[str]:
        return {q.path for q in self.qrels if q.grade == PRIMARY_GRADE}

    def acceptable_paths(self) -> set[str]:
        return {q.path for q in self.qrels if q.grade == ACCEPTABLE_GRADE}

    def companion_paths(self) -> set[str]:
        return {q.path for q in self.qrels if q.grade == COMPANION_GRADE}

    def qrels_dict(self) -> dict[str, int]:
        return {q.path: q.grade for q in self.qrels}


# ---------------------------------------------------------------------------
# Bucket inference
# ---------------------------------------------------------------------------

# Path patterns: knowledge/cs/contents/<category>/... or contents/<category>/...
_CATEGORY_PATH_RE = re.compile(r"(?:knowledge/cs/)?contents/(?P<cat>[a-z][a-z0-9_-]+)/")

_HANGUL_RE = re.compile(r"[가-힯ᄀ-ᇿ㄰-㆏]")
_LATIN_LETTER_RE = re.compile(r"[A-Za-z]")

# Intent token patterns (plan §P1.1 step 3 examples)
_INTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Comparison first — these often subsume definition cues ("X vs Y가 뭐야")
    ("comparison", re.compile(r"(?:\bvs\b|차이|다른\s*점|어느\s*게\s*더|비교)", re.IGNORECASE)),
    ("symptom", re.compile(r"(?:왜\s*안|에러|fail|문제|오류|이상해|안\s*돼|exception|bug)", re.IGNORECASE)),
    ("deep-dive", re.compile(r"(?:어떻게\s*동작|원리|내부\s*구현|왜\s*그래|동작\s*과정|deep|internal)", re.IGNORECASE)),
    ("definition", re.compile(r"(?:란\??$|이란|뭐야|뭐예요|무엇|뜻|개념|정의|what\s+is)", re.IGNORECASE)),
)

# Intermediate / advanced markers in fixture prompts (used when experience_level is missing)
_DIFFICULTY_PROMPT_HINTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("beginner", re.compile(r"(?:초급|입문|기초|뭐야|뭐예요|primer|beginner)", re.IGNORECASE)),
    ("advanced", re.compile(r"(?:심화|고급|advanced|expert|deep\s*dive)", re.IGNORECASE)),
)


def infer_category(expected_path: str) -> str:
    """Extract category from ``contents/<category>/...`` path. Returns 'unknown'
    if the path does not match the conventional layout."""
    if not expected_path:
        return "unknown"
    match = _CATEGORY_PATH_RE.search(expected_path)
    if match:
        return match.group("cat")
    return "unknown"


def infer_language(prompt: str) -> str:
    """Classify prompt language by hangul/latin ratio.

    - hangul-only or hangul-dominant → 'ko'
    - latin-only → 'en'
    - both present in non-trivial amounts → 'mixed'
    """
    if not prompt:
        return "unknown"
    hangul = len(_HANGUL_RE.findall(prompt))
    latin = len(_LATIN_LETTER_RE.findall(prompt))
    if hangul == 0 and latin == 0:
        return "unknown"
    if hangul == 0:
        return "en"
    if latin == 0:
        return "ko"
    # Both present — call it mixed unless one side is trivial (<3 chars)
    if hangul < 3:
        return "en"
    if latin < 3:
        return "ko"
    return "mixed"


def infer_intent(prompt: str) -> str:
    """Heuristic intent classification — first matching pattern wins.

    Order matters: comparison and symptom are more specific than definition.
    """
    for label, pattern in _INTENT_PATTERNS:
        if pattern.search(prompt):
            return label
    return "unknown"


def infer_difficulty(experience_level: str | None, prompt: str) -> str:
    """Use ``experience_level`` when set; otherwise scan prompt for hints.

    Returns 'unknown' when nothing matches so bucket-macro avoids fabricating
    coverage for queries that do not declare a level.
    """
    if experience_level:
        return experience_level
    for label, pattern in _DIFFICULTY_PROMPT_HINTS:
        if pattern.search(prompt):
            return label
    return "unknown"


def infer_bucket(
    expected_path: str,
    prompt: str,
    experience_level: str | None,
) -> Bucket:
    """Compose a Bucket via the four heuristics above."""
    return Bucket(
        category=infer_category(expected_path),
        difficulty=infer_difficulty(experience_level, prompt),
        language=infer_language(prompt),
        intent=infer_intent(prompt),
    )


# ---------------------------------------------------------------------------
# Legacy golden conversion
# ---------------------------------------------------------------------------

def convert_legacy_query(legacy: dict[str, Any]) -> GradedQuery:
    """Convert one entry from ``cs_rag_golden_queries.json`` to GradedQuery.

    Mapping (plan §6 reusable assets):
    - expected_path → grade 3 (primary)
    - acceptable_paths → grade 2 (acceptable)
    - companion_paths → grade 1 (companion)
    - max_rank → rank_budget.primary_max_rank
    - companion_max_rank → rank_budget.companion_max_rank
    - bucket fields are inferred (bucket_source='auto')
    """
    query_id = legacy.get("id")
    prompt = legacy.get("prompt")
    if not query_id or not prompt:
        raise ValueError(f"legacy query missing id/prompt: keys={sorted(legacy)!r}")

    expected_path = legacy.get("expected_path")
    if not expected_path:
        raise ValueError(f"legacy query {query_id!r} has no expected_path")

    qrels: list[Qrel] = [Qrel(path=expected_path, grade=PRIMARY_GRADE, role="primary")]
    seen = {expected_path}

    for path in legacy.get("acceptable_paths") or []:
        if path in seen:
            continue
        qrels.append(Qrel(path=path, grade=ACCEPTABLE_GRADE, role="acceptable"))
        seen.add(path)

    for path in legacy.get("companion_paths") or []:
        if path in seen:
            continue
        qrels.append(Qrel(path=path, grade=COMPANION_GRADE, role="companion"))
        seen.add(path)

    primary_max_rank = int(legacy.get("max_rank") or DEFAULT_PRIMARY_MAX_RANK)
    companion_max_rank = int(
        legacy.get("companion_max_rank") or DEFAULT_COMPANION_MAX_RANK
    )

    experience_level = legacy.get("experience_level")  # may be None

    bucket = infer_bucket(
        expected_path=expected_path,
        prompt=prompt,
        experience_level=experience_level,
    )

    learning_points = tuple(legacy.get("learning_points") or ())

    return GradedQuery(
        query_id=str(query_id),
        prompt=str(prompt),
        mode=DEFAULT_MODE,
        experience_level=experience_level,
        learning_points=learning_points,
        bucket=bucket,
        qrels=tuple(qrels),
        forbidden_paths=tuple(legacy.get("forbidden_paths") or ()),
        rank_budget=RankBudget(
            primary_max_rank=primary_max_rank,
            companion_max_rank=companion_max_rank,
        ),
        bucket_source="auto",
    )


def convert_legacy_payload(legacy_payload: dict[str, Any]) -> list[GradedQuery]:
    """Convert the full ``cs_rag_golden_queries.json`` payload's ``queries``
    list into GradedQuery objects. ``_meta`` is ignored — buckets / contracts
    that depend on it can be reattached separately."""
    queries = legacy_payload.get("queries")
    if not isinstance(queries, list):
        raise ValueError("legacy payload missing 'queries' list")
    return [convert_legacy_query(q) for q in queries]


# ---------------------------------------------------------------------------
# Loader (graded fixture file → GradedQuery list)
# ---------------------------------------------------------------------------

def load_graded_fixture(path: Path) -> list[GradedQuery]:
    """Load a graded fixture from a JSON or JSONL file.

    JSON: top-level dict with ``queries: list[dict]`` or top-level list.
    JSONL: one graded-query JSON object per line (blank lines skipped).
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        records = [
            json.loads(line) for line in text.splitlines() if line.strip()
        ]
    else:
        payload = json.loads(text)
        if isinstance(payload, dict) and "queries" in payload:
            records = payload["queries"]
        elif isinstance(payload, list):
            records = payload
        else:
            raise ValueError(
                f"unexpected fixture root for {path}: "
                f"{type(payload).__name__}"
            )

    return [_record_to_graded(r) for r in records]


def _record_to_graded(record: dict[str, Any]) -> GradedQuery:
    """Materialise a graded-fixture dict (already in the new schema) into a
    GradedQuery dataclass, validating enum fields."""
    mode = record.get("mode", DEFAULT_MODE)
    if mode not in VALID_MODES:
        raise ValueError(f"invalid mode: {mode!r}")

    bucket_dict = record.get("bucket") or {}
    bucket = Bucket(
        category=str(bucket_dict.get("category", "unknown")),
        difficulty=str(bucket_dict.get("difficulty", "unknown")),
        language=str(bucket_dict.get("language", "unknown")),
        intent=str(bucket_dict.get("intent", "unknown")),
    )

    qrels = tuple(
        Qrel(path=q["path"], grade=int(q["grade"]), role=q["role"])
        for q in record.get("qrels", [])
    )

    rank_budget_dict = record.get("rank_budget") or {}
    rank_budget = RankBudget(
        primary_max_rank=int(
            rank_budget_dict.get("primary_max_rank", DEFAULT_PRIMARY_MAX_RANK)
        ),
        companion_max_rank=int(
            rank_budget_dict.get("companion_max_rank", DEFAULT_COMPANION_MAX_RANK)
        ),
    )

    return GradedQuery(
        query_id=str(record["query_id"]),
        prompt=str(record["prompt"]),
        mode=mode,
        experience_level=record.get("experience_level"),
        learning_points=tuple(record.get("learning_points") or ()),
        bucket=bucket,
        qrels=qrels,
        forbidden_paths=tuple(record.get("forbidden_paths") or ()),
        rank_budget=rank_budget,
        bucket_source=str(record.get("bucket_source", "auto")),
    )


# ---------------------------------------------------------------------------
# Serialisation (GradedQuery → dict for JSON dump)
# ---------------------------------------------------------------------------

def graded_query_to_dict(query: GradedQuery) -> dict[str, Any]:
    """Round-trippable dict form of a GradedQuery."""
    return {
        "query_id": query.query_id,
        "prompt": query.prompt,
        "mode": query.mode,
        "experience_level": query.experience_level,
        "learning_points": list(query.learning_points),
        "bucket": asdict(query.bucket),
        "qrels": [asdict(q) for q in query.qrels],
        "forbidden_paths": list(query.forbidden_paths),
        "rank_budget": asdict(query.rank_budget),
        "bucket_source": query.bucket_source,
    }


def dump_graded_fixture(queries: Iterable[GradedQuery], path: Path) -> None:
    """Write a list of GradedQuery to JSON file with ``queries`` envelope."""
    payload = {"queries": [graded_query_to_dict(q) for q in queries]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
