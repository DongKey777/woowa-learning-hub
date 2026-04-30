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


def test_public_search_can_use_explicit_lance_backend(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )
    monkeypatch.setattr(searcher, "_get_lance_query_encoder", lambda _root: encoder)
    debug = {}

    hits = searcher.search(
        "트랜잭션이 뭐예요?",
        mode="full",
        backend="lance",
        index_root=index_root,
        modalities=("fts", "dense", "sparse", "colbert"),
        top_k=1,
        use_reranker=False,
        experience_level="beginner",
        debug=debug,
    )

    assert hits[0]["path"] == "contents/database/transaction-basics.md"
    assert debug["backend"] == "lance"
    assert debug["modalities"] == ["fts", "dense", "sparse", "colbert"]


def test_lance_default_modalities_enable_dense_for_measured_categories():
    out = searcher._resolve_lance_modalities(
        manifest_modalities=("fts", "dense", "sparse", "colbert"),
        requested_modalities=None,
        mode="full",
        learning_points=None,
        signals=[{"category": "database"}],
    )

    assert out == ("fts", "dense")


def test_lance_default_modalities_global_dense_on_after_r1_holdout():
    """R1 holdout (artifact c352271, 101 queries) confirmed dense
    modality production-ready globally: primary_nDCG@10 0.6862 → 0.7890
    (+0.103). Policy schema_version 2 lifts dense from per-category
    (sampled) to global default. Spring specifically: n=26, fts 0.7429
    vs fts+dense 0.7415 — neutral. We keep dense ON globally for
    consistency and let routing skip dense per-call when needed."""
    out = searcher._resolve_lance_modalities(
        manifest_modalities=("fts", "dense", "sparse", "colbert"),
        requested_modalities=None,
        mode="full",
        learning_points=None,
        signals=[{"category": "spring"}],
    )

    assert out == ("fts", "dense")


def test_lance_default_modalities_honor_explicit_ablation_request():
    out = searcher._resolve_lance_modalities(
        manifest_modalities=("fts", "dense", "sparse", "colbert"),
        requested_modalities=("fts", "dense", "sparse"),
        mode="full",
        learning_points=None,
        signals=[{"category": "spring"}],
    )

    assert out == ("fts", "dense", "sparse")


def test_lance_default_modalities_can_change_with_policy_file(tmp_path, monkeypatch):
    policy = tmp_path / "lance_modalities_policy.json"
    policy.write_text(
        """{
          "cheap_default_modalities": ["fts"],
          "full_default_modalities": ["fts"],
          "dense_default_modalities": ["fts", "dense"],
          "dense_default_categories": ["spring"]
        }""",
        encoding="utf-8",
    )
    monkeypatch.setattr(searcher, "LANCE_MODALITY_POLICY_PATH", policy)
    monkeypatch.setattr(searcher, "_LANCE_MODALITY_POLICY_CACHE", None)

    out = searcher._resolve_lance_modalities(
        manifest_modalities=("fts", "dense", "sparse", "colbert"),
        requested_modalities=None,
        mode="full",
        learning_points=None,
        signals=[{"category": "spring"}],
    )

    assert out == ("fts", "dense")


def test_lance_default_modalities_load_encoder_for_global_dense(
    tmp_path,
    monkeypatch,
):
    """After R1 holdout schema-v2 update: global dense ON. Spring is no
    longer a special case — encoder loads, retrieval mixes FTS + dense.

    Use a minimal spy encoder so the call is recorded but cheap. The
    older 'fail_if_loaded' guard would have asserted the sampled-era
    policy which is no longer correct."""
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )

    encoder_load_calls = []
    real_encoder = searcher._get_lance_query_encoder

    def spy_encoder(root):
        encoder_load_calls.append(str(root))
        return real_encoder(root)

    monkeypatch.setattr(searcher, "_get_lance_query_encoder", spy_encoder)
    debug = {}

    hits = searcher.search(
        "Spring Bean이 뭐야?",
        mode="full",
        backend="lance",
        index_root=index_root,
        top_k=1,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/spring/bean-basics.md"
    assert "fts" in debug["modalities"]
    assert "dense" in debug["modalities"]
    assert len(encoder_load_calls) >= 1


def test_public_lance_cheap_mode_does_not_require_query_encoder(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )

    def fail_if_loaded(_root):
        raise AssertionError("cheap LanceDB mode should use FTS only")

    monkeypatch.setattr(searcher, "_get_lance_query_encoder", fail_if_loaded)

    hits = searcher.search(
        "트랜잭션",
        mode="cheap",
        backend="lance",
        index_root=index_root,
        top_k=1,
    )

    assert hits[0]["path"] == "contents/database/transaction-basics.md"


def test_sparse_rescore_promotes_matching_sparse_tokens():
    scored = [(1, 0.1), (2, 0.2)]
    chunks = {
        1: {"sparse_vec": {"indices": [10], "values": [10.0]}},
        2: {"sparse_vec": {"indices": [20], "values": [1.0]}},
    }

    rescored = searcher._sparse_rescore(scored, chunks, {10: 1.0}, weight=0.05)

    assert rescored[0][0] == 1


def test_colbert_maxsim_uses_best_doc_token_per_query_token():
    query = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    doc = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)

    assert searcher._colbert_maxsim(query, doc) == 0.5


def test_colbert_rescore_promotes_candidate_with_higher_maxsim():
    scored = [(1, 0.2), (2, 0.2)]
    query = np.array([[1.0, 0.0]], dtype=np.float32)
    chunks = {
        1: {"colbert_tokens": np.array([[0.0, 1.0]], dtype=np.float32)},
        2: {"colbert_tokens": np.array([[1.0, 0.0]], dtype=np.float32)},
    }

    rescored = searcher._colbert_rescore(scored, chunks, query, weight=0.03)

    assert rescored[0][0] == 2
