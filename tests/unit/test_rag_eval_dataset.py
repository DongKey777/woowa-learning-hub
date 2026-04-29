"""Unit tests for scripts.learning.rag.eval.dataset.

Coverage targets:
- Dataclass validation (grade/role/mode enums)
- Bucket inference: category, language, intent, difficulty
- Legacy → graded conversion: grade mapping, rank_budget defaults, dedupe
- Loader: JSON envelope, JSONL, plain list
- Round-trip: graded_query_to_dict → _record_to_graded preserves all fields
- Real fixture: convert all 338 legacy entries without raising
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag.eval import dataset as D


REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cs_rag_golden_queries.json"


# ---------------------------------------------------------------------------
# Dataclass validation
# ---------------------------------------------------------------------------

def test_qrel_rejects_invalid_grade():
    with pytest.raises(ValueError, match="invalid grade"):
        D.Qrel(path="a.md", grade=4, role="primary")


def test_qrel_rejects_invalid_role():
    with pytest.raises(ValueError, match="invalid role"):
        D.Qrel(path="a.md", grade=3, role="bogus")


def test_qrel_accepts_all_valid_grades():
    for grade, role in zip((1, 2, 3), ("companion", "acceptable", "primary")):
        q = D.Qrel(path="a.md", grade=grade, role=role)
        assert q.grade == grade


def test_graded_query_path_helpers():
    q = D.GradedQuery(
        query_id="q1",
        prompt="p",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=D.Bucket("x", "x", "x", "x"),
        qrels=(
            D.Qrel("a.md", 3, "primary"),
            D.Qrel("b.md", 2, "acceptable"),
            D.Qrel("c.md", 1, "companion"),
        ),
        forbidden_paths=(),
        rank_budget=D.RankBudget(1, 4),
        bucket_source="auto",
    )
    assert q.primary_paths() == {"a.md"}
    assert q.acceptable_paths() == {"b.md"}
    assert q.companion_paths() == {"c.md"}
    assert q.qrels_dict() == {"a.md": 3, "b.md": 2, "c.md": 1}


# ---------------------------------------------------------------------------
# Bucket inference: category
# ---------------------------------------------------------------------------

def test_infer_category_from_contents_path():
    assert D.infer_category("contents/database/transaction-isolation.md") == "database"
    assert D.infer_category("contents/spring/bean-di-basics.md") == "spring"


def test_infer_category_from_full_knowledge_path():
    assert (
        D.infer_category("knowledge/cs/contents/network/http2-server-push.md")
        == "network"
    )


def test_infer_category_unknown_for_unconventional_path():
    assert D.infer_category("docs/something.md") == "unknown"
    assert D.infer_category("") == "unknown"


# ---------------------------------------------------------------------------
# Bucket inference: language
# ---------------------------------------------------------------------------

def test_infer_language_korean_dominant():
    assert D.infer_language("스프링 빈이 뭐야?") == "ko"


def test_infer_language_english_only():
    assert D.infer_language("what is a spring bean") == "en"


def test_infer_language_mixed():
    assert D.infer_language("Spring Bean 의 역할은 무엇인가") == "mixed"


def test_infer_language_treats_acronym_only_as_korean_when_dominant():
    # Lots of Korean + a single 'DI' acronym → still ko (latin < 3)
    assert D.infer_language("DI 가 뭔지 한국어로만 설명해줘 자세히 해주세요") == "ko"


def test_infer_language_unknown_for_blank():
    assert D.infer_language("") == "unknown"


# ---------------------------------------------------------------------------
# Bucket inference: intent
# ---------------------------------------------------------------------------

def test_infer_intent_definition():
    assert D.infer_intent("스프링 빈이란?") == "definition"
    assert D.infer_intent("Spring Bean 뭐야") == "definition"
    assert D.infer_intent("what is a spring bean") == "definition"


def test_infer_intent_comparison():
    assert D.infer_intent("BeanFactory vs ApplicationContext") == "comparison"
    assert D.infer_intent("이 둘의 차이가 뭐야") == "comparison"


def test_infer_intent_symptom():
    assert D.infer_intent("스프링 빈 등록이 왜 안 돼") == "symptom"
    assert D.infer_intent("ApplicationContext 시작 시 에러가 떠") == "symptom"


def test_infer_intent_deep_dive():
    assert D.infer_intent("Spring 컨테이너의 동작 원리를 알려줘") == "deep-dive"
    assert D.infer_intent("어떻게 동작하는지 설명") == "deep-dive"


def test_infer_intent_unknown_for_no_match():
    assert D.infer_intent("그냥 평범한 문장") == "unknown"


def test_intent_comparison_takes_priority_over_definition():
    # "vs" should beat "뭐야"
    assert D.infer_intent("Bean vs Component 가 뭐야") == "comparison"


# ---------------------------------------------------------------------------
# Bucket inference: difficulty
# ---------------------------------------------------------------------------

def test_infer_difficulty_uses_explicit_experience_level():
    assert D.infer_difficulty("intermediate", "anything") == "intermediate"
    assert D.infer_difficulty("advanced", "primer text") == "advanced"


def test_infer_difficulty_falls_back_to_prompt_hint():
    assert D.infer_difficulty(None, "초급자를 위한 primer") == "beginner"
    assert D.infer_difficulty(None, "advanced deep dive") == "advanced"


def test_infer_difficulty_unknown_when_no_signal():
    assert D.infer_difficulty(None, "그냥 질문") == "unknown"


# ---------------------------------------------------------------------------
# Legacy → graded conversion
# ---------------------------------------------------------------------------

_MIN_LEGACY = {
    "id": "q1",
    "prompt": "스프링 빈이 뭐야?",
    "learning_points": [],
    "expected_path": "contents/spring/bean-di-basics.md",
}


def test_convert_legacy_query_minimum_fields():
    g = D.convert_legacy_query(_MIN_LEGACY)
    assert g.query_id == "q1"
    assert g.mode == "full"
    assert g.experience_level is None
    assert g.bucket.category == "spring"
    assert g.bucket.intent == "definition"
    assert g.bucket.language == "ko"
    assert g.qrels == (
        D.Qrel(path="contents/spring/bean-di-basics.md", grade=3, role="primary"),
    )
    assert g.rank_budget == D.RankBudget(primary_max_rank=1, companion_max_rank=4)
    assert g.bucket_source == "auto"


def test_convert_legacy_query_full_grade_mapping():
    legacy = {
        "id": "q2",
        "prompt": "p",
        "learning_points": ["spring/bean"],
        "expected_path": "contents/spring/p.md",
        "acceptable_paths": ["contents/spring/a1.md", "contents/spring/a2.md"],
        "companion_paths": ["contents/spring/c1.md"],
        "max_rank": 2,
        "companion_max_rank": 6,
        "experience_level": "intermediate",
    }
    g = D.convert_legacy_query(legacy)
    assert g.primary_paths() == {"contents/spring/p.md"}
    assert g.acceptable_paths() == {"contents/spring/a1.md", "contents/spring/a2.md"}
    assert g.companion_paths() == {"contents/spring/c1.md"}
    assert g.rank_budget.primary_max_rank == 2
    assert g.rank_budget.companion_max_rank == 6
    assert g.bucket.difficulty == "intermediate"


def test_convert_legacy_query_dedupes_overlapping_paths():
    # If the same path appears in expected and acceptable, take the higher grade
    legacy = {
        **_MIN_LEGACY,
        "id": "q_dup",
        "acceptable_paths": [_MIN_LEGACY["expected_path"], "contents/spring/other.md"],
    }
    g = D.convert_legacy_query(legacy)
    assert len(g.qrels) == 2  # primary + 1 acceptable, expected_path not duplicated
    grades_for_expected = [q.grade for q in g.qrels if q.path == _MIN_LEGACY["expected_path"]]
    assert grades_for_expected == [3]  # primary wins


def test_convert_legacy_query_raises_without_expected_path():
    bad = {"id": "q", "prompt": "p", "learning_points": []}
    with pytest.raises(ValueError, match="expected_path"):
        D.convert_legacy_query(bad)


def test_convert_legacy_query_raises_without_id_or_prompt():
    with pytest.raises(ValueError, match="id/prompt"):
        D.convert_legacy_query({"prompt": "p"})


# ---------------------------------------------------------------------------
# Real fixture conversion smoke
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not LEGACY_FIXTURE.exists(),
    reason="legacy golden fixture not present",
)
def test_convert_real_legacy_payload_succeeds_for_all_338():
    legacy_payload = json.loads(LEGACY_FIXTURE.read_text(encoding="utf-8"))
    graded = D.convert_legacy_payload(legacy_payload)
    assert len(graded) == 338
    # Every query has at least one primary qrel
    for g in graded:
        assert g.primary_paths(), f"{g.query_id} has no primary path"
    # No two queries share the same id
    ids = [g.query_id for g in graded]
    assert len(set(ids)) == len(ids)


@pytest.mark.skipif(
    not LEGACY_FIXTURE.exists(),
    reason="legacy golden fixture not present",
)
def test_real_payload_bucket_categories_are_known_cs_categories():
    legacy_payload = json.loads(LEGACY_FIXTURE.read_text(encoding="utf-8"))
    graded = D.convert_legacy_payload(legacy_payload)
    cats = {g.bucket.category for g in graded}
    # Most should resolve to a real category (database/spring/network/...)
    # Allow at most a handful of 'unknown' for unconventional paths.
    unknown_count = sum(1 for g in graded if g.bucket.category == "unknown")
    assert unknown_count < len(graded) * 0.1, (
        f"too many unknown categories: {unknown_count}/{len(graded)}; "
        f"distinct cats: {sorted(cats)}"
    )


# ---------------------------------------------------------------------------
# Loader: JSON envelope / JSONL / plain list
# ---------------------------------------------------------------------------

def _sample_graded_record() -> dict:
    return {
        "query_id": "g1",
        "prompt": "p",
        "mode": "full",
        "experience_level": "beginner",
        "learning_points": [],
        "bucket": {
            "category": "spring",
            "difficulty": "beginner",
            "language": "ko",
            "intent": "definition",
        },
        "qrels": [{"path": "a.md", "grade": 3, "role": "primary"}],
        "forbidden_paths": [],
        "rank_budget": {"primary_max_rank": 1, "companion_max_rank": 4},
        "bucket_source": "auto",
    }


def test_loader_reads_json_envelope(tmp_path):
    path = tmp_path / "fx.json"
    path.write_text(
        json.dumps({"queries": [_sample_graded_record()]}, ensure_ascii=False),
        encoding="utf-8",
    )
    queries = D.load_graded_fixture(path)
    assert len(queries) == 1
    assert queries[0].query_id == "g1"


def test_loader_reads_plain_json_list(tmp_path):
    path = tmp_path / "fx.json"
    path.write_text(json.dumps([_sample_graded_record()], ensure_ascii=False), encoding="utf-8")
    queries = D.load_graded_fixture(path)
    assert len(queries) == 1


def test_loader_reads_jsonl(tmp_path):
    path = tmp_path / "fx.jsonl"
    rec = _sample_graded_record()
    path.write_text(
        json.dumps(rec, ensure_ascii=False) + "\n\n" + json.dumps(rec, ensure_ascii=False),
        encoding="utf-8",
    )
    queries = D.load_graded_fixture(path)
    assert len(queries) == 2


def test_loader_rejects_invalid_root(tmp_path):
    path = tmp_path / "fx.json"
    path.write_text(json.dumps("not a list or dict-with-queries"), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected fixture root"):
        D.load_graded_fixture(path)


def test_loader_rejects_invalid_mode(tmp_path):
    path = tmp_path / "fx.json"
    rec = _sample_graded_record()
    rec["mode"] = "bogus"
    path.write_text(json.dumps({"queries": [rec]}, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid mode"):
        D.load_graded_fixture(path)


# ---------------------------------------------------------------------------
# Round-trip: graded_query_to_dict → _record_to_graded
# ---------------------------------------------------------------------------

def test_round_trip_preserves_all_fields(tmp_path):
    original = D.convert_legacy_query({
        **_MIN_LEGACY,
        "acceptable_paths": ["contents/spring/a.md"],
        "companion_paths": ["contents/spring/c.md"],
        "max_rank": 2,
        "companion_max_rank": 5,
        "experience_level": "beginner",
    })
    serialised = D.graded_query_to_dict(original)
    fixture = tmp_path / "round.json"
    fixture.write_text(json.dumps({"queries": [serialised]}, ensure_ascii=False), encoding="utf-8")
    loaded = D.load_graded_fixture(fixture)[0]
    assert loaded == original


def test_dump_and_load_round_trip(tmp_path):
    queries = [
        D.convert_legacy_query(_MIN_LEGACY),
        D.convert_legacy_query({**_MIN_LEGACY, "id": "q3"}),
    ]
    path = tmp_path / "dump.json"
    D.dump_graded_fixture(queries, path)
    reloaded = D.load_graded_fixture(path)
    assert reloaded == queries
