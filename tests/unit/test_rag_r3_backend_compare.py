from __future__ import annotations

import json

from scripts.learning.rag.r3.eval.backend_compare import (
    BackendSpec,
    run_backend_comparison,
    write_backend_traces,
)
from scripts.learning.rag.r3.eval.qrels import R3Qrel, R3QueryJudgement


def _qrels() -> list[R3QueryJudgement]:
    return [
        R3QueryJudgement(
            query_id="latency:mixed",
            prompt="latency가 뭐야?",
            qrels=(
                R3Qrel(
                    path="contents/network/latency.md",
                    grade=3,
                    role="primary",
                ),
                R3Qrel(
                    path="contents/network/latency-overview.md",
                    grade=2,
                    role="acceptable",
                ),
            ),
            forbidden_paths=("contents/network/throughput.md",),
            tags=("level:beginner", "category:network"),
        )
    ]


def test_backend_comparison_uses_r3_trace_fused_paths_for_candidate_recall():
    def fake_search(prompt, **kwargs):
        assert prompt == "latency가 뭐야?"
        assert kwargs["use_reranker"] is False
        debug = kwargs["debug"]
        debug["r3_trace"] = {
            "trace_id": "debug-id",
            "query_plan": {
                "raw_query": prompt,
                "normalized_query": prompt,
                "language": "mixed",
                "lexical_terms": ["latency"],
                "route_tags": [],
                "metadata_filters": {},
            },
            "candidates": [],
            "final_paths": ["contents/network/other.md"],
            "stage_ms": {},
            "metadata": {
                "fused_paths": [
                    "contents/network/latency-overview.md",
                    "contents/network/latency.md",
                ]
            },
        }
        return [{"path": "contents/network/other.md"}]

    report = run_backend_comparison(
        [BackendSpec(name="r3", backend="r3")],
        _qrels(),
        top_k=2,
        windows=(1, 2),
        search_fn=fake_search,
    )

    summary = report["backends"][0]["summary"]["overall"]
    assert summary["candidate_recall_primary"]["1"] == 0.0
    assert summary["candidate_recall_primary"]["2"] == 1.0
    assert summary["candidate_recall_relevant"]["1"] == 1.0
    assert summary["final_hit_primary"]["2"] == 0.0
    assert report["backends"][0]["traces"][0]["trace_id"] == "latency:mixed"
    assert report["backends"][0]["traces"][0]["metadata"]["backend_spec"]["backend"] == "r3"


def test_backend_comparison_falls_back_to_hit_paths_for_non_r3_backends():
    def fake_search(prompt, **kwargs):
        del prompt, kwargs
        return [
            {"path": "contents/network/throughput.md"},
            {"path": "contents/network/latency.md"},
        ]

    report = run_backend_comparison(
        [BackendSpec(name="legacy", backend="legacy")],
        _qrels(),
        top_k=2,
        windows=(1, 2),
        forbidden_window=1,
        search_fn=fake_search,
    )

    summary = report["backends"][0]["summary"]["overall"]
    assert summary["candidate_recall_primary"]["2"] == 1.0
    assert summary["forbidden_rate"] == 1.0
    assert report["backends"][0]["traces"][0]["metadata"]["backend"] == "legacy"


def test_backend_comparison_reports_reranker_demotion_from_trace():
    def fake_search(prompt, **kwargs):
        debug = kwargs["debug"]
        debug["r3_trace"] = {
            "trace_id": "debug-id",
            "query_plan": {
                "raw_query": prompt,
                "normalized_query": prompt,
                "language": "mixed",
                "lexical_terms": ["latency"],
                "route_tags": [],
                "metadata_filters": {},
            },
            "candidates": [],
            "final_paths": [
                "contents/network/other.md",
                "contents/network/latency.md",
            ],
            "stage_ms": {},
            "metadata": {
                "fused_paths": [
                    "contents/network/latency.md",
                    "contents/network/other.md",
                ]
            },
        }
        return [{"path": "contents/network/other.md"}]

    report = run_backend_comparison(
        [BackendSpec(name="r3-rerank", backend="r3", use_reranker=True)],
        _qrels(),
        top_k=2,
        windows=(1, 2),
        search_fn=fake_search,
    )

    demotion = report["backends"][0]["reranker_demotion"]
    assert demotion["overall"]["total"] == 1
    assert demotion["overall"]["demoted"] == 1
    assert demotion["by_language"]["mixed"]["rate"] == 1.0
    assert demotion["demoted_query_ids"] == ["latency:mixed"]


def test_write_backend_traces_emits_jsonl(tmp_path):
    report = run_backend_comparison(
        [BackendSpec(name="legacy", backend="legacy")],
        _qrels(),
        top_k=1,
        search_fn=lambda prompt, **kwargs: [{"path": "contents/network/latency.md"}],
    )

    paths = write_backend_traces(report, tmp_path)

    assert paths == [tmp_path / "legacy.jsonl"]
    lines = paths[0].read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["trace_id"] == "latency:mixed"
