from __future__ import annotations

import json
from pathlib import Path

from scripts.learning.rag import corpus_loader, indexer, searcher
from scripts.learning.rag.r3 import search as r3_search
from scripts.learning.rag.r3.candidate import R3Document
from scripts.learning.rag.r3.index.lexical_sidecar import LoadedLexicalSidecar
from scripts.learning.rag.r3.index.lexical_store import LexicalStore
from scripts.learning.rag.r3.index.runtime_loader import (
    load_lance_documents,
    load_runtime_dense_candidates,
)


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
        use_reranker=False,
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


def test_r3_backend_reranks_full_mode_by_default(tmp_path, monkeypatch):
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
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/latency-deep-dive.md"
    assert debug["r3_reranker_enabled"] is True
    assert debug["r3_reranker_model"] == "fake-reranker"


def test_r3_backend_skips_reranker_in_cheap_mode(tmp_path, monkeypatch):
    _build_legacy_index(tmp_path)

    monkeypatch.setattr(
        "scripts.learning.rag.r3.search.CrossEncoderReranker.for_language",
        lambda language: (_ for _ in ()).throw(AssertionError("reranker loaded")),
    )
    debug: dict = {}

    hits = searcher.search(
        "latency가 뭐야?",
        backend="r3",
        index_root=tmp_path,
        mode="cheap",
        top_k=1,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/latency-primer.md"
    assert debug["r3_reranker_enabled"] is False
    assert debug["r3_reranker_model"] is None


def test_r3_lance_runtime_loader_reads_lightweight_columns(monkeypatch, tmp_path):
    captured = {}

    class FakeFrame:
        def to_dict(self, orient):
            assert orient == "records"
            return [
                {
                    "chunk_id": "latency#0",
                    "path": "contents/network/latency-bandwidth-throughput-basics.md",
                    "title": "Latency",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Latency", "Primer"]',
                    "body": "latency bandwidth throughput",
                    "search_terms": "latency 지연 처리량",
                    "anchors": '["latency", "지연"]',
                    "sparse_vec": {"indices": [101, 202], "values": [2.5, 1.25]},
                }
            ]

    class FakeTable:
        version = 7

        def to_pandas(self, **kwargs):
            captured["columns"] = kwargs["columns"]
            return FakeFrame()

    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.read_manifest_v3",
        lambda root: {"corpus_hash": "hash"},
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )

    documents = load_lance_documents(tmp_path)

    assert captured["columns"] == [
        "chunk_id",
        "path",
        "title",
        "category",
        "difficulty",
        "section_path",
        "body",
        "search_terms",
        "anchors",
        "sparse_vec",
    ]
    assert documents[0].path == "contents/network/latency-bandwidth-throughput-basics.md"
    assert documents[0].section_title == "Primer"
    assert documents[0].aliases == ("latency", "지연")
    assert documents[0].sparse_terms == {"101": 2.5, "202": 1.25}
    assert documents[0].metadata["index_backend"] == "lance"
    assert documents[0].metadata["body"] == "latency bandwidth throughput"
    assert documents[0].metadata["aliases"] == ("latency", "지연")


def test_r3_lance_sparse_sidecar_omits_body_for_full_sparse_scan(
    monkeypatch,
    tmp_path,
):
    captured = {}

    class FakeFrame:
        def to_dict(self, orient):
            assert orient == "records"
            return [
                {
                    "chunk_id": "sparse#0",
                    "path": "contents/network/sparse-only.md",
                    "title": "Sparse Only",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Sparse Only"]',
                    "search_terms": "",
                    "anchors": "[]",
                    "sparse_vec": {"indices": [42], "values": [9.0]},
                }
            ]

    class FakeTable:
        version = 9

        def to_pandas(self, **kwargs):
            captured["columns"] = kwargs["columns"]
            return FakeFrame()

    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.read_manifest_v3",
        lambda root: {"corpus_hash": "hash"},
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )

    documents = load_lance_documents(tmp_path, sparse_sidecar=True)

    assert captured["columns"] == [
        "chunk_id",
        "path",
        "title",
        "category",
        "difficulty",
        "section_path",
        "search_terms",
        "anchors",
        "sparse_vec",
    ]
    assert documents[0].body == ""
    assert documents[0].sparse_terms == {"42": 9.0}


def test_r3_lance_sparse_sidecar_cache_survives_query_prefetches(
    monkeypatch,
    tmp_path,
):
    counts = {"to_pandas": 0}

    class FakeSearch:
        def __init__(self, query):
            self.query = query

        def limit(self, value):
            return self

        def to_list(self):
            return [
                {
                    "chunk_id": f"{self.query}#0",
                    "path": f"contents/network/{self.query}.md",
                    "title": self.query,
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": f'["{self.query}"]',
                    "body": self.query,
                    "search_terms": self.query,
                    "anchors": "[]",
                    "sparse_vec": {"indices": [1], "values": [1.0]},
                }
            ]

    class FakeFrame:
        def to_dict(self, orient):
            assert orient == "records"
            return [
                {
                    "chunk_id": "sparse#0",
                    "path": "contents/network/sparse.md",
                    "title": "Sparse",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Sparse"]',
                    "search_terms": "",
                    "anchors": "[]",
                    "sparse_vec": {"indices": [42], "values": [9.0]},
                }
            ]

    class FakeTable:
        version = 12

        def search(self, query, *, query_type):
            return FakeSearch(query)

        def to_pandas(self, **kwargs):
            counts["to_pandas"] += 1
            return FakeFrame()

    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.read_manifest_v3",
        lambda root: {"corpus_hash": "cache-hash"},
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )

    load_lance_documents(tmp_path, sparse_sidecar=True)
    for idx in range(40):
        load_lance_documents(tmp_path, query=f"q{idx}", limit=1)
    load_lance_documents(tmp_path, sparse_sidecar=True)

    assert counts["to_pandas"] == 1


def test_r3_sparse_retriever_cache_reuses_inverted_index():
    documents = [
        R3Document(
            path="contents/network/latency.md",
            chunk_id="latency#0",
            title="Latency",
            sparse_terms={"101": 2.0},
        )
    ]

    first, first_hit = r3_search._cached_sparse_retriever(documents)
    second, second_hit = r3_search._cached_sparse_retriever(documents)

    assert first is second
    assert first_hit is False
    assert second_hit is True


def test_r3_search_uses_prebuilt_lexical_sidecar(monkeypatch, tmp_path):
    documents = [
        R3Document(
            path="contents/network/latency-sidecar.md",
            chunk_id="latency#0",
            title="Latency Sidecar",
            body="tail latency timeout",
            metadata={"body": "tail latency timeout", "category": "network"},
        )
    ]
    loaded = LoadedLexicalSidecar(
        store=LexicalStore.from_documents(documents),
        metadata={"path": str(tmp_path / "r3_lexical_sidecar.json"), "document_count": 1},
    )
    monkeypatch.setattr(r3_search, "load_runtime_documents", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "encode_runtime_query", lambda *a, **kw: {})
    monkeypatch.setattr(r3_search, "load_runtime_dense_candidates", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "load_runtime_sparse_documents", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "load_lexical_sidecar", lambda *a, **kw: loaded)

    debug: dict = {}
    hits = r3_search.search(
        "latency가 뭐야?",
        index_root=tmp_path,
        top_k=1,
        mode="cheap",
        use_reranker=False,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/latency-sidecar.md"
    assert debug["r3_lexical_sidecar_used"] is True
    assert debug["r3_lexical_sidecar"]["document_count"] == 1


def test_r3_auto_policy_skips_reranker_when_sidecar_is_available(
    monkeypatch,
    tmp_path,
):
    documents = [
        R3Document(
            path="contents/network/latency-sidecar.md",
            chunk_id="latency#0",
            title="Latency Sidecar",
            body="tail latency timeout",
            metadata={"body": "tail latency timeout", "category": "network"},
        )
    ]
    loaded = LoadedLexicalSidecar(
        store=LexicalStore.from_documents(documents),
        metadata={"path": str(tmp_path / "r3_lexical_sidecar.json"), "document_count": 1},
    )
    monkeypatch.setattr(r3_search, "load_runtime_documents", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "encode_runtime_query", lambda *a, **kw: {})
    monkeypatch.setattr(r3_search, "load_runtime_dense_candidates", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "load_runtime_sparse_documents", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "load_lexical_sidecar", lambda *a, **kw: loaded)
    monkeypatch.setattr(
        "scripts.learning.rag.r3.search.CrossEncoderReranker.for_language",
        lambda language: (_ for _ in ()).throw(AssertionError("reranker loaded")),
    )

    debug: dict = {}
    hits = r3_search.search(
        "latency가 뭐야?",
        index_root=tmp_path,
        top_k=1,
        mode="full",
        use_reranker=None,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/latency-sidecar.md"
    assert debug["r3_reranker_enabled"] is False
    assert debug["r3_reranker_skip_reason"] == "policy_auto_sidecar_first_stage_gate"


def test_r3_explicit_reranker_overrides_auto_sidecar_skip(monkeypatch, tmp_path):
    documents = [
        R3Document(
            path="contents/network/latency-sidecar.md",
            chunk_id="latency#0",
            title="Latency Sidecar",
            body="tail latency timeout",
            metadata={"body": "tail latency timeout", "category": "network"},
        )
    ]
    loaded = LoadedLexicalSidecar(
        store=LexicalStore.from_documents(documents),
        metadata={"path": str(tmp_path / "r3_lexical_sidecar.json"), "document_count": 1},
    )

    class FakeReranker:
        model_id = "fake-reranker"

        def rerank(self, query, candidates, *, top_n):
            return list(candidates[:top_n])

    monkeypatch.setattr(r3_search, "load_runtime_documents", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "encode_runtime_query", lambda *a, **kw: {})
    monkeypatch.setattr(r3_search, "load_runtime_dense_candidates", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "load_runtime_sparse_documents", lambda *a, **kw: [])
    monkeypatch.setattr(r3_search, "load_lexical_sidecar", lambda *a, **kw: loaded)
    monkeypatch.setattr(
        "scripts.learning.rag.r3.search.CrossEncoderReranker.for_language",
        lambda language: FakeReranker(),
    )

    debug: dict = {}
    r3_search.search(
        "latency가 뭐야?",
        index_root=tmp_path,
        top_k=1,
        mode="full",
        use_reranker=True,
        debug=debug,
    )

    assert debug["r3_reranker_enabled"] is True
    assert debug["r3_reranker_model"] == "fake-reranker"


def test_r3_lance_runtime_loader_can_prefetch_with_fts_query(monkeypatch, tmp_path):
    captured = {}

    class FakeSearch:
        def limit(self, value):
            captured["limit"] = value
            return self

        def to_list(self):
            return [
                {
                    "chunk_id": "latency#0",
                    "path": "contents/network/latency-bandwidth-throughput-basics.md",
                    "title": "Latency",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Latency", "Primer"]',
                    "body": "latency",
                    "search_terms": "latency",
                    "anchors": "[]",
                    "sparse_vec": {"indices": [7], "values": [1.0]},
                }
            ]

    class FakeTable:
        version = 8

        def search(self, query, *, query_type):
            captured["query"] = query
            captured["query_type"] = query_type
            return FakeSearch()

    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.read_manifest_v3",
        lambda root: {"corpus_hash": "hash"},
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )

    documents = load_lance_documents(tmp_path, query="latency가 뭐야?", limit=25)

    assert captured == {
        "query": "latency가 뭐야?",
        "query_type": "fts",
        "limit": 25,
    }
    assert documents[0].path == "contents/network/latency-bandwidth-throughput-basics.md"


def test_r3_lance_dense_candidates_use_vector_search(monkeypatch, tmp_path):
    captured = {}

    class FakeSearch:
        def limit(self, value):
            captured["limit"] = value
            return self

        def to_list(self):
            return [
                {
                    "chunk_id": "dense#0",
                    "path": "contents/network/dense.md",
                    "title": "Dense",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Dense"]',
                    "body": "dense body",
                    "anchors": '["dense"]',
                    "_distance": 0.25,
                }
            ]

    class FakeTable:
        def search(self, query, *, vector_column_name):
            captured["query"] = query
            captured["vector_column_name"] = vector_column_name
            return FakeSearch()

    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.load_manifest",
        lambda root: {"index_version": indexer.LANCE_INDEX_VERSION},
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )

    candidates = load_runtime_dense_candidates(tmp_path, [0.1, 0.2], limit=7)

    assert captured == {
        "query": [0.1, 0.2],
        "vector_column_name": "dense_vec",
        "limit": 7,
    }
    assert candidates[0].path == "contents/network/dense.md"
    assert candidates[0].retriever == "dense"
    assert candidates[0].score == 0.8
    assert candidates[0].metadata["document"]["body"] == "dense body"


def test_r3_sparse_sidecar_can_return_candidate_absent_from_fts_prefetch(
    monkeypatch,
    tmp_path,
):
    class FakeSearch:
        def limit(self, value):
            return self

        def to_list(self):
            return [
                {
                    "chunk_id": "prefetch#0",
                    "path": "contents/network/prefetch-only.md",
                    "title": "Prefetch Only",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Prefetch Only"]',
                    "body": "surface terms only",
                    "search_terms": "surface terms",
                    "anchors": "[]",
                    "sparse_vec": {"indices": [11], "values": [1.0]},
                }
            ]

    class FakeFrame:
        def to_dict(self, orient):
            assert orient == "records"
            return [
                {
                    "chunk_id": "prefetch#0",
                    "path": "contents/network/prefetch-only.md",
                    "title": "Prefetch Only",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Prefetch Only"]',
                    "search_terms": "surface terms",
                    "anchors": "[]",
                    "sparse_vec": {"indices": [11], "values": [1.0]},
                },
                {
                    "chunk_id": "sparse#0",
                    "path": "contents/network/sparse-only.md",
                    "title": "Sparse Only",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Sparse Only"]',
                    "search_terms": "",
                    "anchors": "[]",
                    "sparse_vec": {"indices": [42], "values": [8.0]},
                },
            ]

    class FakeTable:
        version = 10

        def search(self, query, *, query_type):
            return FakeSearch()

        def to_pandas(self, **kwargs):
            return FakeFrame()

    manifest = {
        "index_version": indexer.LANCE_INDEX_VERSION,
        "corpus_hash": "hash",
        "encoder": {"model_id": "BAAI/bge-m3", "model_version": "fixture"},
    }
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.load_manifest",
        lambda root: manifest,
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.read_manifest_v3",
        lambda root: manifest,
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.search.encode_runtime_query",
        lambda root, query: {"sparse_terms": {"42": 5.0}},
    )
    debug: dict = {}

    hits = searcher.search(
        "opaque-query",
        backend="r3",
        index_root=tmp_path,
        mode="full",
        top_k=1,
        use_reranker=False,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/sparse-only.md"
    assert hits[0]["r3_sources"] == [{"retriever": "sparse", "rank": 1, "score": 40.0}]
    assert debug["r3_sparse_source"] == "bge_m3_sparse_vec_sidecar"
    assert debug["r3_sparse_sidecar_document_count"] == 2
    assert debug["r3_sparse_query_terms_count"] == 1
    assert debug["r3_dense_candidate_count"] == 0


def test_r3_dense_candidate_can_return_candidate_absent_from_fts_prefetch(
    monkeypatch,
    tmp_path,
):
    class FakeSearch:
        def __init__(self, rows):
            self.rows = rows

        def limit(self, value):
            return self

        def to_list(self):
            return self.rows

    class FakeTable:
        version = 13

        def search(self, query, **kwargs):
            if kwargs.get("query_type") == "fts":
                return FakeSearch(
                    [
                        {
                            "chunk_id": "prefetch#0",
                            "path": "contents/network/prefetch-only.md",
                            "title": "Prefetch Only",
                            "category": "network",
                            "difficulty": "beginner",
                            "section_path": '["Prefetch Only"]',
                            "body": "surface terms only",
                            "search_terms": "surface terms",
                            "anchors": "[]",
                            "sparse_vec": {"indices": [11], "values": [1.0]},
                        }
                    ]
                )
            assert kwargs == {"vector_column_name": "dense_vec"}
            return FakeSearch(
                [
                    {
                        "chunk_id": "dense#0",
                        "path": "contents/network/dense-only.md",
                        "title": "Dense Only",
                        "category": "network",
                        "difficulty": "beginner",
                        "section_path": '["Dense Only"]',
                        "body": "semantic candidate",
                        "anchors": "[]",
                        "_score": 0.99,
                    }
                ]
            )

    manifest = {
        "index_version": indexer.LANCE_INDEX_VERSION,
        "corpus_hash": "dense-hash",
        "encoder": {"model_id": "BAAI/bge-m3", "model_version": "fixture"},
    }
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.load_manifest",
        lambda root: manifest,
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.read_manifest_v3",
        lambda root: manifest,
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.search.encode_runtime_query",
        lambda root, query: {"dense": [0.1, 0.2]},
    )
    debug: dict = {}

    hits = searcher.search(
        "semantic-query",
        backend="r3",
        index_root=tmp_path,
        mode="full",
        top_k=1,
        use_reranker=False,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/dense-only.md"
    assert hits[0]["r3_sources"] == [{"retriever": "dense", "rank": 1, "score": 0.99}]
    assert debug["r3_dense_candidate_count"] == 1


def test_r3_cheap_mode_does_not_load_sparse_encoder(monkeypatch, tmp_path):
    class FakeSearch:
        def limit(self, value):
            return self

        def to_list(self):
            return [
                {
                    "chunk_id": "latency#0",
                    "path": "contents/network/latency.md",
                    "title": "Latency",
                    "category": "network",
                    "difficulty": "beginner",
                    "section_path": '["Latency"]',
                    "body": "latency",
                    "search_terms": "latency",
                    "anchors": "[]",
                    "sparse_vec": {"indices": [42], "values": [1.0]},
                }
            ]

    class FakeTable:
        version = 11

        def search(self, query, *, query_type):
            return FakeSearch()

    manifest = {
        "index_version": indexer.LANCE_INDEX_VERSION,
        "corpus_hash": "hash",
        "encoder": {"model_id": "BAAI/bge-m3", "model_version": "fixture"},
    }
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.load_manifest",
        lambda root: manifest,
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.read_manifest_v3",
        lambda root: manifest,
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.index.runtime_loader.indexer.open_lance_table",
        lambda root: FakeTable(),
    )
    monkeypatch.setattr(
        "scripts.learning.rag.r3.search.encode_runtime_query",
        lambda root, query: (_ for _ in ()).throw(AssertionError("encoder loaded")),
    )
    debug: dict = {}

    hits = searcher.search(
        "latency가 뭐야?",
        backend="r3",
        index_root=tmp_path,
        mode="cheap",
        top_k=1,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/network/latency.md"
    assert debug["r3_sparse_encoder_allowed"] is False
    assert debug["r3_sparse_source"] == "lexical_terms"
