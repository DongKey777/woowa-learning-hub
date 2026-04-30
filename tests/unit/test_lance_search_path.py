from __future__ import annotations

from pathlib import Path

import numpy as np

from scripts.learning.rag import indexer, searcher


class FakeMultiModalEncoder:
    model_id = "fake/bge-m3"
    model_version = "fake/bge-m3@test"
    dense_dim = 8
    colbert_dim = 8
    sparse_vocab_size = 128

    def encode_corpus(
        self,
        texts,
        *,
        batch_size=16,
        max_length=8192,
        modalities=("dense", "sparse", "colbert"),
        progress=None,
    ):
        dense = np.zeros((len(texts), self.dense_dim), dtype=np.float32)
        sparse = []
        colbert = []
        for i, text in enumerate(texts):
            dense[i, i % self.dense_dim] = 1.0
            if "트랜잭션" in text:
                sparse.append({10: 1.0, 42: 0.5})
            elif "스프링" in text or "Spring" in text:
                sparse.append({20: 1.0, 42: 0.25})
            else:
                sparse.append({99: 1.0})
            colbert.append(np.full((2, self.colbert_dim), i + 1, dtype=np.float16))
        return {"dense": dense, "sparse": sparse, "colbert": colbert}

    def encode_query(self, text, *, modalities=("dense", "sparse", "colbert")):
        dense = np.zeros((1, self.dense_dim), dtype=np.float32)
        dense[0, 0] = 1.0
        sparse = [{10: 1.0, 42: 0.5}] if "트랜잭션" in text else [{20: 1.0}]
        colbert = [np.ones((2, self.colbert_dim), dtype=np.float16)]
        return {"dense": dense, "sparse": sparse, "colbert": colbert}


def _write_doc(root: Path, category: str, slug: str, title: str, body: str) -> None:
    path = root / "contents" / category / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# {title}

**난이도: 🟢 Beginner**

retrieval-anchor-keywords:
- {title.lower()} basics
- {title} 처음 배우는데

## 핵심 개념

{body}
""",
        encoding="utf-8",
    )


def _fake_corpus(tmp_path: Path) -> Path:
    root = tmp_path / "corpus"
    _write_doc(
        root,
        "database",
        "transaction-basics",
        "트랜잭션 기초",
        "트랜잭션은 커밋과 롤백을 하나의 작업 단위로 묶는 데이터베이스 약속입니다. " * 4,
    )
    _write_doc(
        root,
        "spring",
        "bean-basics",
        "Spring Bean 기초",
        "스프링 빈은 컨테이너가 생성하고 의존성을 연결하는 객체입니다. " * 4,
    )
    return root


def test_lance_candidate_search_returns_formatted_hits(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )
    table = indexer.open_lance_table(index_root)

    hits = searcher._lance_candidate_search(
        table,
        "트랜잭션이 뭐예요?",
        query_encoding=encoder.encode_query("트랜잭션이 뭐예요?"),
        modalities=("fts", "dense", "sparse"),
        top_k=2,
    )

    assert hits
    assert hits[0]["path"] == "contents/database/transaction-basics.md"
    assert hits[0]["category"] == "database"
    assert hits[0]["score"] > 0
    assert "트랜잭션" in hits[0]["snippet_preview"]


def test_lance_candidate_search_returns_empty_when_modalities_miss(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )
    table = indexer.open_lance_table(index_root)

    assert (
        searcher._lance_candidate_search(
            table,
            "트랜잭션",
            query_encoding=None,
            modalities=("dense",),
            top_k=2,
        )
        == []
    )


def test_sparse_rescore_promotes_matching_sparse_tokens():
    scored = [(1, 0.1), (2, 0.2)]
    chunks = {
        1: {"sparse_vec": {"indices": [10], "values": [10.0]}},
        2: {"sparse_vec": {"indices": [20], "values": [1.0]}},
    }

    rescored = searcher._sparse_rescore(scored, chunks, {10: 1.0}, weight=0.05)

    assert rescored[0][0] == 1
