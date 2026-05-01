from __future__ import annotations

from scripts.learning.rag.r3.eval.metrics import (
    RetrievalEvaluationQuery,
    RerankerComparison,
    retrieval_summary,
    reranker_demotion_summary,
)


def test_reranker_demotion_summary_buckets_by_language_level_category():
    summary = reranker_demotion_summary(
        [
            RerankerComparison(
                query_id="ko-1",
                language="mixed",
                level="beginner",
                category="network",
                primary_paths=("latency.md",),
                before_paths=("latency.md", "other.md"),
                after_paths=("other.md", "latency.md"),
            ),
            RerankerComparison(
                query_id="en-1",
                language="en",
                level="beginner",
                category="database",
                primary_paths=("tx.md",),
                before_paths=("other.md", "tx.md"),
                after_paths=("tx.md", "other.md"),
            ),
        ]
    )

    assert summary["overall"]["total"] == 2
    assert summary["overall"]["demoted"] == 1
    assert summary["overall"]["rate"] == 0.5
    assert summary["by_language"]["mixed"]["demoted"] == 1
    assert summary["by_language"]["mixed"]["lost_top5"] == 0
    assert summary["by_level"]["beginner"]["total"] == 2
    assert summary["by_category"]["network"]["rate"] == 1.0
    assert summary["demoted_query_ids"] == ["ko-1"]
    assert summary["lost_top5_query_ids"] == []


def test_reranker_demotion_counts_missing_after_as_demoted():
    summary = reranker_demotion_summary(
        [
            RerankerComparison(
                query_id="missing",
                language="ko",
                level="beginner",
                category="spring",
                primary_paths=("bean.md",),
                before_paths=("bean.md",),
                after_paths=("other.md",),
            )
        ]
    )

    assert summary["overall"]["demoted"] == 1
    assert summary["overall"]["missing_after"] == 1
    assert summary["overall"]["lost_top5"] == 1
    assert summary["overall"]["lost_top20"] == 1
    assert summary["lost_top5_query_ids"] == ["missing"]


def test_retrieval_summary_reports_candidate_final_and_forbidden_rates():
    summary = retrieval_summary(
        [
            RetrievalEvaluationQuery(
                query_id="mixed-ok",
                language="mixed",
                level="beginner",
                category="network",
                primary_paths=("latency.md",),
                acceptable_paths=("latency-overview.md",),
                forbidden_paths=("throughput.md",),
                candidate_paths=("latency-overview.md", "latency.md"),
                final_paths=("latency.md", "other.md"),
            ),
            RetrievalEvaluationQuery(
                query_id="ko-forbidden",
                language="ko",
                level="beginner",
                category="spring",
                primary_paths=("di.md",),
                acceptable_paths=(),
                forbidden_paths=("service-locator.md",),
                candidate_paths=("other.md",),
                final_paths=("service-locator.md",),
            ),
        ],
        windows=(1, 2),
        forbidden_window=1,
    )

    assert summary["overall"]["total"] == 2
    assert summary["overall"]["candidate_recall_primary"]["1"] == 0.0
    assert summary["overall"]["candidate_recall_primary"]["2"] == 0.5
    assert summary["overall"]["candidate_recall_relevant"]["1"] == 0.5
    assert summary["overall"]["final_hit_primary"]["1"] == 0.5
    assert summary["overall"]["forbidden_rate"] == 0.5
    assert summary["by_language"]["mixed"]["candidate_recall_primary"]["2"] == 1.0
    assert summary["missing_candidate_primary_query_ids"] == ["ko-forbidden"]
    assert summary["forbidden_query_ids"] == ["ko-forbidden"]
