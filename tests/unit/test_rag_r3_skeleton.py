from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag import searcher
from scripts.learning.rag.r3.candidate import Candidate
from scripts.learning.rag.r3.config import resolve_rerank_input_window
from scripts.learning.rag.r3.eval.qrels import R3Qrel, load_qrels
from scripts.learning.rag.r3.eval.trace import R3Trace, read_jsonl, write_jsonl
from scripts.learning.rag.r3.eval.trace_fixture import build_traces_from_qrels, main
from scripts.learning.rag.r3.query_plan import build_query_plan


def test_query_plan_preserves_korean_first_mixed_terms():
    plan = build_query_plan("latency가 뭐야?")

    assert plan.language == "mixed"
    assert "latency" in plan.lexical_terms
    assert plan.preserved_english_terms == ("latency",)
    assert "korean_first_mixed" in plan.route_tags


def test_query_plan_classifies_korean_and_english():
    assert build_query_plan("트랜잭션 격리 수준이 뭐야?").language == "ko"
    assert build_query_plan("what is latency").language == "en"


def test_candidate_requires_retriever_provenance():
    candidate = Candidate(
        path="contents/network/timeout-retry-backoff-practical.md",
        retriever="lexical",
        rank=1,
        score=2.5,
        chunk_id="chunk-1",
    )

    assert candidate.candidate_id.endswith("#chunk-1")
    assert candidate.to_dict()["retriever"] == "lexical"

    with pytest.raises(ValueError, match="retriever"):
        Candidate(path="a.md", retriever="", rank=1, score=1.0)


def test_trace_jsonl_roundtrip(tmp_path):
    plan = build_query_plan("read model이랑 projection 차이가 뭐야?")
    trace = R3Trace(
        trace_id="trace-1",
        query_plan=plan,
        candidates=(
            Candidate(
                path="contents/design-pattern/read-model-staleness-read-your-writes.md",
                retriever="sparse",
                rank=1,
                score=4.0,
            ),
        ),
        final_paths=("contents/design-pattern/read-model-staleness-read-your-writes.md",),
        stage_ms={"query_plan": 1.25},
        metadata={"backend": "r3"},
    )
    path = tmp_path / "trace.jsonl"

    write_jsonl([trace], path)
    loaded = read_jsonl(path)

    assert loaded == [trace]
    assert json.loads(path.read_text(encoding="utf-8").splitlines()[0])["trace_id"] == "trace-1"


def test_r3_qrel_fixture_validates_primary_and_forbidden_paths():
    queries = load_qrels(Path("tests/fixtures/r3_qrels_pilot.json"))

    assert len(queries) == 1
    query = queries[0]
    assert query.primary_paths() == {"contents/network/timeout-retry-backoff-practical.md"}
    assert query.acceptable_paths() == {"contents/system-design/service-latency-slo-basics.md"}
    assert "contents/language/java/object-oriented-core-principles.md" in query.forbidden_paths


def test_r3_qrel_rejects_role_grade_mismatch():
    with pytest.raises(ValueError, match="requires grade"):
        R3Qrel(path="a.md", grade=1, role="primary")


def test_searcher_explicit_r3_backend_routes_without_index():
    debug: dict = {}

    results = searcher.search("latency가 뭐야?", backend="r3", debug=debug)

    assert results == []
    assert debug["backend"] == "r3"
    assert debug["r3_skeleton"] is True
    assert debug["r3_query_plan"]["language"] == "mixed"


def test_rerank_input_window_is_profile_configurable(monkeypatch):
    assert resolve_rerank_input_window(5) == 10

    monkeypatch.setenv("WOOWA_RAG_RERANK_INPUT_WINDOW", "50")
    assert resolve_rerank_input_window(5) == 50

    monkeypatch.setenv("WOOWA_RAG_RERANK_INPUT_WINDOW", "not-an-int")
    assert resolve_rerank_input_window(5) == 10


def test_trace_fixture_cli_writes_jsonl(tmp_path):
    out = tmp_path / "r3_trace.jsonl"

    exit_code = main(
        [
            "--qrels",
            "tests/fixtures/r3_qrels_pilot.json",
            "--out",
            str(out),
        ]
    )

    assert exit_code == 0
    traces = read_jsonl(out)
    assert traces[0].trace_id == "r3-mixed-latency-definition"
    assert traces[0].query_plan.language == "mixed"
    assert traces[0].metadata["forbidden_paths"]


def test_build_traces_from_qrels_keeps_qrel_metadata():
    traces = build_traces_from_qrels(Path("tests/fixtures/r3_qrels_pilot.json"))

    assert traces[0].metadata["qrels"][0]["role"] == "primary"
