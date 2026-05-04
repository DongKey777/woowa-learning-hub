"""Unit tests for H7 LanceDB modality ablation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag import indexer, searcher
from scripts.learning.rag.eval import ablation as A
from scripts.learning.rag.eval.dataset import Bucket, GradedQuery, Qrel, RankBudget


def _query(qid: str = "q1") -> GradedQuery:
    return GradedQuery(
        query_id=qid,
        prompt="Spring Bean이 뭐야",
        mode="full",
        experience_level="beginner",
        learning_points=(),
        bucket=Bucket("spring", "beginner", "ko", "definition"),
        qrels=(Qrel("contents/spring/bean.md", 3, "primary"),),
        forbidden_paths=(),
        rank_budget=RankBudget(10, 10),
        bucket_source="manual",
    )


def _lance_manifest(root: Path) -> None:
    root.mkdir(parents=True)
    manifest = {
        "index_version": indexer.LANCE_INDEX_VERSION,
        "schema_uri": "https://woowa-learning-hub/schemas/cs-index-manifest-v3.json",
        "row_count": 1,
        "corpus_hash": "hash",
        "corpus_root": "corpus",
        "built_at": "2026-04-30T00:00:00Z",
        "encoder": {
            "model_id": "BAAI/bge-m3",
            "model_version": "BAAI/bge-m3@test",
            "max_length": 8192,
        },
        "lancedb": {
            "version": "0.30.2",
            "table_name": indexer.LANCE_TABLE_NAME,
            "indices": {"dense": {"type": "unindexed"}},
        },
        "modalities": ["fts", "dense", "sparse", "colbert"],
        "ingest": {"chunk_max_chars": 1600, "chunk_overlap": 0},
    }
    (root / indexer.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def test_parse_modality_sets_defaults_to_singletons_pairs_and_full():
    sets = A.parse_modality_sets(None)
    assert ("fts",) in sets
    assert ("dense",) in sets
    assert ("fts", "dense") in sets
    assert ("fts", "dense", "sparse", "colbert") in sets
    assert len(sets) == 11


def test_parse_modality_sets_canonicalizes_cli_values():
    sets = A.parse_modality_sets(["dense,fts", "fts,dense", "colbert"])
    assert sets == (("fts", "dense"), ("colbert",))


def test_parse_modality_sets_rejects_unknown():
    with pytest.raises(ValueError, match="unknown modalities"):
        A.parse_modality_sets(["fts,bogus"])


def test_run_modality_ablation_scores_each_subset(monkeypatch, tmp_path):
    from scripts.learning.rag.reranker import RERANK_MODEL

    monkeypatch.delenv("WOOWA_RAG_NO_RERANK", raising=False)
    root = tmp_path / "idx"
    _lance_manifest(root)
    calls: list[tuple[str, ...]] = []

    def fake_search(prompt, **kwargs):
        modalities = kwargs["modalities"]
        calls.append(modalities)
        if modalities == ("fts", "dense"):
            return [{"path": "contents/spring/bean.md"}]
        return [{"path": "contents/spring/other.md"}]

    monkeypatch.setattr(searcher, "search", fake_search)
    report = A.run_modality_ablation(
        [_query()],
        index_root=root,
        encoder=object(),
        modality_sets=(("fts",), ("fts", "dense")),
        device="cpu",
    )

    assert report.query_count == 1
    assert [run.modalities for run in report.runs] == [("fts",), ("fts", "dense")]
    assert report.runs[0].primary_ndcg_macro == 0.0
    assert report.runs[1].primary_ndcg_macro == 1.0
    assert report.best_modalities == ("fts", "dense")
    # Each modality gets one cold warm-up call plus one measured eval call.
    assert calls == [("fts",), ("fts",), ("fts", "dense"), ("fts", "dense")]

    blob = A.ablation_report_to_dict(report)
    assert blob["runs"][1]["run_report"]["manifest"]["backend"] == "lance"
    assert blob["runs"][1]["run_report"]["manifest"]["modalities"] == ["fts", "dense"]
    assert blob["runs"][1]["run_report"]["manifest"]["reranker_model"] == RERANK_MODEL
    assert blob["runs"][1]["run_report"]["manifest"]["cold_start_ms"] >= 0.0
