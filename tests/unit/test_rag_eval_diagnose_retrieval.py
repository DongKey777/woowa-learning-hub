from scripts.learning.rag.eval import diagnose_retrieval as D


def test_rank_of_returns_first_primary_match() -> None:
    assert D._rank_of(["a.md", "b.md", "c.md"], {"c.md", "x.md"}) == 3
    assert D._rank_of(["a.md", "b.md"], {"x.md"}) is None


def test_format_hits_derives_category_from_path() -> None:
    hits = [
        {
            "path": "contents/database/transaction-isolation-basics.md",
            "category": "wrong",
            "title": "Transaction Isolation",
            "section_title": "MVCC",
            "score": 0.5,
        }
    ]

    assert D._format_hits(hits, top_k=10) == [
        {
            "rank": 1,
            "path": "contents/database/transaction-isolation-basics.md",
            "category": "database",
            "title": "Transaction Isolation",
            "section_title": "MVCC",
            "score": 0.5,
        }
    ]


def test_summarize_records_groups_rank_and_cross_category_outcomes() -> None:
    records = [
        {
            "query_id": "q1",
            "expected": {"category": "spring"},
            "legacy": {
                "primary_rank": 1,
                "primary_in_top_k": True,
                "primary_at_1": True,
                "top1_cross_category": False,
                "top1": {"category": "spring"},
            },
            "lance": {
                "primary_rank": 1,
                "primary_in_top_k": True,
                "primary_at_1": True,
                "top1_cross_category": False,
                "top1": {"category": "spring"},
            },
        },
        {
            "query_id": "q2",
            "expected": {"category": "database"},
            "legacy": {
                "primary_rank": 1,
                "primary_in_top_k": True,
                "primary_at_1": True,
                "top1_cross_category": False,
                "top1": {"category": "database"},
            },
            "lance": {
                "primary_rank": 2,
                "primary_in_top_k": True,
                "primary_at_1": False,
                "top1_cross_category": True,
                "top1": {"category": "language"},
            },
        },
        {
            "query_id": "q3",
            "expected": {"category": "security"},
            "legacy": {
                "primary_rank": None,
                "primary_in_top_k": False,
                "primary_at_1": False,
                "top1_cross_category": False,
                "top1": {"category": "security"},
            },
            "lance": {
                "primary_rank": 1,
                "primary_in_top_k": True,
                "primary_at_1": True,
                "top1_cross_category": False,
                "top1": {"category": "security"},
            },
        },
    ]

    summary = D._summarize(records, top_k=10)

    assert summary["primary_at_1"] == {"legacy": 2, "lance": 2}
    assert summary["primary_in_top_k"] == {"legacy": 2, "lance": 3}
    assert summary["primary_missing_top_k"] == {"legacy": 1, "lance": 0}
    assert summary["top1_cross_category"] == {"legacy": 0, "lance": 1}
    assert summary["rank_comparison"] == {
        "legacy_better": 1,
        "lance_better": 1,
        "tie": 1,
    }
    assert summary["lance_failure_classes"] == {
        "pass_rank1": 2,
        "top1_cross_category": 1,
    }
    assert summary["lance_top1_confusion"] == {"database->language": 1}
    assert summary["query_sets"]["legacy_only_primary_at_1"] == ["q2"]
    assert summary["query_sets"]["lance_only_primary_at_1"] == ["q3"]
