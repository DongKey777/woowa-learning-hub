"""Unit tests for sampled H8 ablation corpus materialisation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag.eval import sampled_ablation as S
from scripts.learning.rag.eval.dataset import Bucket, GradedQuery, Qrel, RankBudget


def _write_doc(root: Path, rel: str, body: str = "**난이도: 🟢 Beginner**") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Doc\n\n{body}\n\n## 본문\n\n내용입니다.\n", encoding="utf-8")


def _query(
    *,
    qid: str = "q1",
    category: str = "spring",
    path: str = "contents/spring/bean.md",
) -> GradedQuery:
    return GradedQuery(
        query_id=qid,
        prompt="Spring Bean이 뭐야",
        mode="full",
        experience_level="beginner",
        learning_points=(),
        bucket=Bucket(category, "beginner", "ko", "definition"),
        qrels=(Qrel(path, 3, "primary"),),
        forbidden_paths=(),
        rank_budget=RankBudget(10, 10),
        bucket_source="manual",
    )


def test_parse_categories_defaults_and_dedupes():
    assert "spring" in S.parse_categories(None)
    assert S.parse_categories("spring,database,spring") == ("spring", "database")
    with pytest.raises(ValueError, match="at least one category"):
        S.parse_categories("")


def test_materialize_sampled_corpus_copies_qrels_and_extra_docs(tmp_path):
    source = tmp_path / "source"
    _write_doc(source, "contents/spring/bean.md")
    _write_doc(source, "contents/spring/ioc.md")
    _write_doc(source, "contents/database/tx.md")

    result = S.materialize_sampled_corpus(
        source_corpus_root=source,
        target_root=tmp_path / "sample",
        queries=[
            _query(path="contents/spring/bean.md"),
            _query(qid="q2", category="database", path="contents/database/tx.md"),
        ],
        categories=("spring",),
        extra_docs_per_category=1,
    )

    assert result.categories == ("spring",)
    assert len(result.queries) == 1
    assert result.required_doc_paths == ("contents/spring/bean.md",)
    assert result.extra_doc_paths == ("contents/spring/ioc.md",)
    assert (result.corpus_root / "contents/spring/bean.md").exists()
    assert (result.corpus_root / "contents/spring/ioc.md").exists()
    assert not (result.corpus_root / "contents/database/tx.md").exists()

    fixture = json.loads(result.fixture_path.read_text(encoding="utf-8"))
    assert fixture["queries"][0]["query_id"] == "q1"
    assert result.to_summary()["doc_count"] == 2


def test_materialize_sampled_corpus_rejects_empty_query_selection(tmp_path):
    source = tmp_path / "source"
    _write_doc(source, "contents/spring/bean.md")

    with pytest.raises(ValueError, match="no queries matched"):
        S.materialize_sampled_corpus(
            source_corpus_root=source,
            target_root=tmp_path / "sample",
            queries=[_query(category="spring")],
            categories=("database",),
        )


def test_select_extra_docs_prefers_beginner_then_intermediate(tmp_path):
    source = tmp_path / "source"
    _write_doc(source, "contents/spring/advanced.md", "**난이도: 🔴 Advanced**")
    _write_doc(source, "contents/spring/beginner.md", "**난이도: 🟢 Beginner**")
    _write_doc(source, "contents/spring/intermediate.md", "**난이도: 🟡 Intermediate**")

    out = S.select_extra_docs(
        source,
        categories=("spring",),
        required_doc_paths=(),
        per_category=2,
    )
    assert out == (
        "contents/spring/beginner.md",
        "contents/spring/intermediate.md",
    )
