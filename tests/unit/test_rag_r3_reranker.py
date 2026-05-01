from __future__ import annotations

import sys
from types import SimpleNamespace

from scripts.learning.rag.r3.candidate import Candidate
from scripts.learning.rag.r3.config import R3Config
from scripts.learning.rag.r3.rerankers import (
    CrossEncoderReranker,
    default_model_factory,
    reranker_chain_for_language,
)


class FakeCrossEncoder:
    def predict(self, pairs, show_progress_bar=False):
        del show_progress_bar
        return [len(pair[1]) for pair in pairs]


def test_korean_and_mixed_reranker_chain_excludes_english_only_mxbai():
    config = R3Config()

    for language in ("ko", "mixed"):
        chain = reranker_chain_for_language(language, config)
        assert chain[0] == "BAAI/bge-reranker-v2-m3"
        assert "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1" in chain
        assert len(chain) == len(set(chain))
        assert "mixedbread-ai/mxbai-rerank-base-v1" not in chain


def test_english_chain_can_include_mxbai_experiment():
    chain = reranker_chain_for_language("en", R3Config())

    assert chain[0] == "BAAI/bge-reranker-v2-m3"
    assert "mixedbread-ai/mxbai-rerank-base-v1" in chain


def test_default_model_factory_allows_remote_code_only_for_gte(monkeypatch):
    calls = []

    class FakeFactory:
        def __init__(self, model_id, **kwargs):
            calls.append((model_id, kwargs))

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(CrossEncoder=FakeFactory),
    )

    default_model_factory("BAAI/bge-reranker-v2-m3")
    default_model_factory("Alibaba-NLP/gte-multilingual-reranker-base")

    assert calls[0] == ("BAAI/bge-reranker-v2-m3", {})
    assert calls[1] == (
        "Alibaba-NLP/gte-multilingual-reranker-base",
        {"trust_remote_code": True, "device": "cpu"},
    )


def test_cross_encoder_reranker_sorts_candidates_and_keeps_metadata():
    candidates = [
        Candidate(
            path="short.md",
            retriever="fusion",
            rank=1,
            score=0.2,
            title="Short",
            metadata={"passage": "tiny"},
        ),
        Candidate(
            path="long.md",
            retriever="fusion",
            rank=2,
            score=0.1,
            title="Long",
            metadata={"passage": "much longer passage"},
        ),
    ]
    reranker = CrossEncoderReranker(
        model_id="BAAI/bge-reranker-v2-m3",
        model_factory=lambda _: FakeCrossEncoder(),
    )

    reranked = reranker.rerank("latency가 뭐야?", candidates, top_n=2)

    assert [candidate.path for candidate in reranked] == ["long.md", "short.md"]
    assert reranked[0].retriever == "reranker:BAAI/bge-reranker-v2-m3"
    assert reranked[0].metadata["reranker_model"] == "BAAI/bge-reranker-v2-m3"
    assert reranked[0].metadata["pre_rerank_rank"] == 2
