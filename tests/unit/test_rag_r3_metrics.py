from __future__ import annotations

from scripts.learning.rag.r3.eval.metrics import (
    RerankerComparison,
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
    assert summary["by_level"]["beginner"]["total"] == 2
    assert summary["by_category"]["network"]["rate"] == 1.0
    assert summary["demoted_query_ids"] == ["ko-1"]


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
