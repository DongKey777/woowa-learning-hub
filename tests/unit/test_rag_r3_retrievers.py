from __future__ import annotations

from scripts.learning.rag.r3.candidate import R3Document
from scripts.learning.rag.r3.fusion import fuse_candidates
from scripts.learning.rag.r3.index.lexical_store import LexicalStore
from scripts.learning.rag.r3.query_plan import build_query_plan
from scripts.learning.rag.r3.retrievers import (
    DenseRetriever,
    LexicalRetriever,
    SignalRetriever,
    SparseRetriever,
)


def _docs() -> list[R3Document]:
    return [
        R3Document(
            path="contents/network/latency-primer.md",
            chunk_id="latency#1",
            title="Latency Primer",
            section_title="Tail latency",
            body="response time and timeout basics",
            aliases=("latency", "지연 시간"),
            dense_vector=(1.0, 0.0),
            sparse_terms={"latency": 1.0, "tail": 0.7},
            signals=("language:mixed",),
        ),
        R3Document(
            path="contents/database/sparse-only.md",
            chunk_id="sparse#1",
            title="Storage Internals",
            section_title="Queueing model",
            body="content without the query anchor",
            dense_vector=(0.0, 1.0),
            sparse_terms={"latency": 3.0},
            signals=(),
        ),
        R3Document(
            path="contents/java/oop.md",
            chunk_id="oop#1",
            title="OOP",
            section_title="Class design",
            body="object polymorphism inheritance",
            aliases=("객체지향",),
            dense_vector=(0.1, 0.1),
            sparse_terms={"object": 1.0},
            signals=("java_oop_basics",),
        ),
    ]


def test_lexical_retriever_keeps_field_provenance_visible():
    plan = build_query_plan("latency가 뭐야?")
    retriever = LexicalRetriever(LexicalStore.from_documents(_docs()))

    hits = retriever.retrieve(plan)

    retrievers = {hit.retriever for hit in hits}
    assert "lexical:title" in retrievers
    assert "lexical:aliases" in retrievers
    assert all("field" in hit.metadata for hit in hits)


def test_lexical_retriever_uses_symmetric_korean_tokenization():
    docs = [
        R3Document(
            path="contents/spring/di.md",
            title="DI Primer",
            body="의존성 주입 기본 개념",
        )
    ]
    plan = build_query_plan("의존성주입이 뭐야?")

    hits = LexicalRetriever(LexicalStore.from_documents(docs)).retrieve(plan)

    assert hits
    assert hits[0].path == "contents/spring/di.md"


def test_sparse_retriever_can_discover_doc_absent_from_lexical_results():
    plan = build_query_plan("latency가 뭐야?")
    docs = _docs()

    lexical_paths = {hit.path for hit in LexicalRetriever(LexicalStore.from_documents(docs)).retrieve(plan)}
    sparse_hits = SparseRetriever(docs).retrieve(plan)

    assert "contents/database/sparse-only.md" not in lexical_paths
    assert sparse_hits[0].path == "contents/database/sparse-only.md"
    assert sparse_hits[0].retriever == "sparse"


def test_dense_and_signal_retrievers_emit_independent_candidates():
    docs = _docs()

    dense_hits = DenseRetriever(docs).retrieve((1.0, 0.0))
    signal_hits = SignalRetriever(docs).retrieve(["java_oop_basics"])

    assert dense_hits[0].path == "contents/network/latency-primer.md"
    assert dense_hits[0].retriever == "dense"
    assert signal_hits[0].path == "contents/java/oop.md"
    assert signal_hits[0].metadata["matched_signals"] == ["java_oop_basics"]


def test_fusion_preserves_retriever_sources_and_doc_diversity():
    plan = build_query_plan("latency가 뭐야?")
    docs = _docs()
    candidates = [
        *LexicalRetriever(LexicalStore.from_documents(docs)).retrieve(plan),
        *SparseRetriever(docs).retrieve(plan),
        *DenseRetriever(docs).retrieve((1.0, 0.0)),
    ]

    fused = fuse_candidates(candidates, limit=5)

    assert len({candidate.path for candidate in fused}) == len(fused)
    assert fused[0].retriever == "fusion"
    assert fused[0].metadata["sources"]
    source_names = {
        source["retriever"]
        for candidate in fused
        for source in candidate.metadata["sources"]
    }
    assert {"sparse", "dense"} <= source_names
