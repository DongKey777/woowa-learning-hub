from __future__ import annotations

import json
from pathlib import Path

from scripts.learning.rag import corpus_loader, indexer, searcher


def _chunk(
    doc_id: str,
    path: str,
    title: str,
    category: str,
    body: str,
    *,
    anchors: list[str] | None = None,
) -> corpus_loader.CorpusChunk:
    return corpus_loader.CorpusChunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}#0",
        path=path,
        title=title,
        category=category,
        section_title="Primer",
        section_path=[title, "Primer"],
        body=body,
        char_len=len(body),
        anchors=anchors or [],
    )


def _build_legacy_index(index_root: Path) -> None:
    sqlite_path, _, manifest_path = indexer._paths(index_root)
    conn = indexer._open_sqlite(sqlite_path)
    try:
        indexer._insert_chunks(
            conn,
            [
                _chunk(
                    "latency",
                    "contents/network/latency-primer.md",
                    "Latency Primer",
                    "network",
                    "latency response time timeout tail latency",
                    anchors=["latency", "지연 시간"],
                ),
                _chunk(
                    "oop",
                    "contents/language/java/oop.md",
                    "OOP Primer",
                    "language",
                    "class object polymorphism",
                ),
                _chunk(
                    "latency_deep",
                    "contents/network/latency-deep-dive.md",
                    "Latency Deep Dive",
                    "network",
                    "latency queueing model advanced internals",
                ),
            ],
        )
    finally:
        conn.close()
    manifest_path.write_text(
        json.dumps(
            {
                "index_version": indexer.INDEX_VERSION,
                "embed_model": "fixture",
                "embed_dim": 0,
                "row_count": 3,
                "corpus_hash": "fixture",
                "corpus_root": "fixture",
            }
        ),
        encoding="utf-8",
    )


def test_r3_backend_reads_legacy_index_and_returns_traced_hits(tmp_path):
    _build_legacy_index(tmp_path)
    debug: dict = {}

    hits = searcher.search(
        "latency가 뭐야?",
        backend="r3",
        index_root=tmp_path,
        top_k=1,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/latency-primer.md"
    assert hits[0]["r3_sources"]
    assert debug["backend"] == "r3"
    assert debug["r3_query_plan"]["language"] == "mixed"
    assert debug["r3_candidate_count"] > 0
    assert debug["r3_trace"]["final_paths"] == [
        "contents/network/latency-primer.md"
    ]


def test_r3_backend_reranks_only_when_explicitly_enabled(tmp_path, monkeypatch):
    _build_legacy_index(tmp_path)

    class FakeReranker:
        model_id = "fake-reranker"

        def rerank(self, query, candidates, *, top_n):
            del query, top_n
            return sorted(
                candidates,
                key=lambda candidate: candidate.path == "contents/network/latency-deep-dive.md",
                reverse=True,
            )

    monkeypatch.setattr(
        "scripts.learning.rag.r3.search.CrossEncoderReranker.for_language",
        lambda language: FakeReranker(),
    )
    debug: dict = {}

    hits = searcher.search(
        "latency가 뭐야?",
        backend="r3",
        index_root=tmp_path,
        top_k=1,
        use_reranker=True,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/latency-deep-dive.md"
    assert debug["r3_reranker_model"] == "fake-reranker"
