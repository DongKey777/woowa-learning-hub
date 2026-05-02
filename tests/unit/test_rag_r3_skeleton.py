from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag import searcher
from scripts.learning.rag.r3.candidate import Candidate
from scripts.learning.rag.r3.config import R3Config, resolve_rerank_input_window
from scripts.learning.rag.r3.eval.qrels import (
    R3Qrel,
    load_qrels,
    main as qrels_main,
    qrels_from_corpus,
    qrels_from_frontmatter_doc,
    write_qrels,
)
from scripts.learning.rag.r3.eval.trace import R3Trace, read_jsonl, write_jsonl
from scripts.learning.rag.r3.eval.trace_fixture import build_traces_from_qrels, main
from scripts.learning.rag.r3.query_plan import build_query_plan


def test_query_plan_preserves_korean_first_mixed_terms():
    plan = build_query_plan("latency가 뭐야?")

    assert plan.version == "r3.0"
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


def test_searcher_explicit_r3_backend_routes_without_index(tmp_path):
    debug: dict = {}

    results = searcher.search(
        "latency가 뭐야?",
        backend="r3",
        index_root=tmp_path / "missing",
        debug=debug,
    )

    assert results == []
    assert debug["backend"] == "r3"
    assert debug["r3_skeleton"] is True
    assert debug["r3_query_plan"]["version"] == "r3.0"
    assert debug["r3_query_plan"]["language"] == "mixed"


def test_rerank_input_window_is_profile_configurable(monkeypatch):
    assert resolve_rerank_input_window(5) == 10

    monkeypatch.setenv("WOOWA_RAG_RERANK_INPUT_WINDOW", "50")
    assert resolve_rerank_input_window(5) == 50

    monkeypatch.setenv("WOOWA_RAG_RERANK_INPUT_WINDOW", "not-an-int")
    assert resolve_rerank_input_window(5) == 10


def test_r3_lance_prefetch_limit_defaults_to_local_runtime_budget(monkeypatch):
    monkeypatch.delenv("WOOWA_RAG_R3_LANCE_PREFETCH_LIMIT", raising=False)
    assert R3Config.from_env().runtime_lance_prefetch_limit == 100

    monkeypatch.setenv("WOOWA_RAG_R3_LANCE_PREFETCH_LIMIT", "25")
    assert R3Config.from_env().runtime_lance_prefetch_limit == 25


def test_r3_local_rerank_window_defaults_to_verified_m5_budget(monkeypatch):
    monkeypatch.delenv("WOOWA_RAG_R3_LOCAL_RERANK_INPUT_WINDOW", raising=False)
    assert R3Config.from_env().local_rerank_input_window == 20

    monkeypatch.setenv("WOOWA_RAG_R3_LOCAL_RERANK_INPUT_WINDOW", "50")
    assert R3Config.from_env().local_rerank_input_window == 50


def test_r3_rerank_policy_defaults_to_auto(monkeypatch):
    monkeypatch.delenv("WOOWA_RAG_R3_RERANK_POLICY", raising=False)
    assert R3Config.from_env().local_rerank_policy == "auto"

    monkeypatch.setenv("WOOWA_RAG_R3_RERANK_POLICY", "always")
    assert R3Config.from_env().local_rerank_policy == "always"

    monkeypatch.setenv("WOOWA_RAG_R3_RERANK_POLICY", "off")
    assert R3Config.from_env().local_rerank_policy == "off"

    monkeypatch.setenv("WOOWA_RAG_R3_RERANK_POLICY", "bad")
    assert R3Config.from_env().local_rerank_policy == "auto"


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


def test_qrels_from_corpus_v2_expected_queries(tmp_path):
    corpus = tmp_path / "contents"
    spring = corpus / "spring"
    spring.mkdir(parents=True)
    doc = spring / "di.md"
    doc.write_text(
        "---\n"
        "schema_version: 2\n"
        "concept_id: spring/di\n"
        "doc_role: primer\n"
        "level: beginner\n"
        "aliases: [DI]\n"
        "expected_queries:\n"
        "  - DI가 뭐야?\n"
        "acceptable_neighbors:\n"
        "  - contents/software-engineering/dependency-injection-basics.md\n"
        "companion_neighbors:\n"
        "  - contents/spring/ioc-di-container.md\n"
        "forbidden_neighbors:\n"
        "  - contents/design-pattern/service-locator.md\n"
        "---\n\nbody",
        encoding="utf-8",
    )

    qrels = qrels_from_corpus(corpus)

    assert len(qrels) == 1
    assert qrels[0].query_id == "spring/di:expected:1"
    assert qrels[0].prompt == "DI가 뭐야?"
    assert qrels[0].primary_paths() == {"contents/spring/di.md"}
    assert qrels[0].acceptable_paths() == {
        "contents/software-engineering/dependency-injection-basics.md"
    }
    assert qrels[0].companion_paths() == {"contents/spring/ioc-di-container.md"}
    assert qrels[0].forbidden_paths == (
        "contents/design-pattern/service-locator.md",
    )


def test_write_qrels_roundtrips_with_schema_wrapper(tmp_path):
    out = tmp_path / "qrels.json"
    qrel = R3Qrel(path="contents/spring/di.md", grade=3, role="primary")

    write_qrels(
        [
            qrels_from_frontmatter_doc(
                tmp_path / "contents" / "spring" / "di.md",
                "---\n"
                "schema_version: 2\n"
                "concept_id: spring/di\n"
                "doc_role: primer\n"
                "level: beginner\n"
                "aliases: [DI]\n"
                "expected_queries: [DI가 뭐야?]\n"
                "---\n\nbody",
                corpus_root=tmp_path / "contents",
            )[0]
        ],
        out,
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["query_count"] == 1
    assert load_qrels(out)[0].qrels == (qrel,)


def test_qrels_cli_writes_corpus_qrels(tmp_path):
    corpus = tmp_path / "contents"
    doc = corpus / "spring" / "di.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(
        "---\n"
        "schema_version: 2\n"
        "concept_id: spring/di\n"
        "doc_role: primer\n"
        "level: beginner\n"
        "aliases: [DI]\n"
        "expected_queries: [DI가 뭐야?]\n"
        "---\n\nbody",
        encoding="utf-8",
    )
    out = tmp_path / "reports" / "qrels.json"

    assert qrels_main(["--corpus-root", str(corpus), "--out", str(out)]) == 0
    assert load_qrels(out)[0].query_id == "spring/di:expected:1"


def test_qrels_from_frontmatter_doc_ignores_non_v2(tmp_path):
    doc = tmp_path / "x.md"

    assert qrels_from_frontmatter_doc(doc, "# no frontmatter") == []
