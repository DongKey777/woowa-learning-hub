from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts.learning.rag import indexer, query_rewrites, searcher


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


class SpyQueryEncoder(FakeMultiModalEncoder):
    def __init__(self):
        self.encode_corpus_calls = []
        self.encode_query_calls = []

    def encode_corpus(
        self,
        texts,
        *,
        batch_size=16,
        max_length=8192,
        modalities=("dense", "sparse", "colbert"),
        progress=None,
    ):
        text_list = list(texts)
        self.encode_corpus_calls.append(
            {
                "texts": text_list,
                "batch_size": batch_size,
                "modalities": modalities,
            }
        )
        return super().encode_corpus(
            text_list,
            batch_size=batch_size,
            max_length=max_length,
            modalities=modalities,
            progress=progress,
        )

    def encode_query(self, text, *, modalities=("dense", "sparse", "colbert")):
        self.encode_query_calls.append({"text": text, "modalities": modalities})
        raise AssertionError("Lance multi-query search should batch encode candidates")


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


def _write_cached_rewrite(
    repo_root: Path,
    *,
    prompt: str,
    mode: str,
    texts: list[str],
    storage: Path | None = None,
) -> None:
    storage = storage or repo_root / "state" / "cs_rag" / "query_rewrites"
    storage.mkdir(parents=True, exist_ok=True)
    prompt_hash = query_rewrites.compute_prompt_hash(prompt, mode)
    payload = {
        "schema_id": query_rewrites.SCHEMA_ID_OUTPUT,
        "prompt_hash": prompt_hash,
        "rewrites": [
            {"text": text, "rationale": "fixture rewrite"} for text in texts
        ],
        "confidence": 0.8,
        "scored_by": "ai_session",
        "produced_at": "2026-05-01T00:00:00+00:00",
    }
    (storage / f"{prompt_hash}.output.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_malformed_cached_rewrite(
    repo_root: Path,
    *,
    prompt: str,
    mode: str,
) -> None:
    storage = repo_root / "state" / "cs_rag" / "query_rewrites"
    storage.mkdir(parents=True, exist_ok=True)
    prompt_hash = query_rewrites.compute_prompt_hash(prompt, mode)
    (storage / f"{prompt_hash}.output.json").write_text(
        "{malformed json",
        encoding="utf-8",
    )


def test_lance_candidate_search_returns_formatted_hits(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
        modalities=("fts", "dense", "sparse", "colbert"),
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
        modalities=("fts", "dense", "sparse", "colbert"),
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


def test_lance_fts_adds_korean_search_terms_candidate(monkeypatch):
    def row(chunk_id: str, path: str, title: str) -> dict:
        return {
            "chunk_id": chunk_id,
            "doc_id": chunk_id.split("#", 1)[0],
            "path": path,
            "title": title,
            "category": "database",
            "difficulty": "beginner",
            "section_path": json.dumps([title]),
            "body": f"{title} body",
            "char_len": 20,
            "anchors": "[]",
            "_score": 1.0,
        }

    class FakeLanceQuery:
        def __init__(self, rows):
            self._rows = rows

        def select(self, _columns):
            return self

        def limit(self, _limit):
            return self

        def to_list(self):
            return self._rows

    class FakeLanceTable:
        def __init__(self):
            self.prompts = []

        def search(self, prompt, *, query_type="fts"):
            self.prompts.append((prompt, query_type))
            if prompt == "트랜잭션 격리 수준":
                return FakeLanceQuery(
                    [
                        row(
                            "terms#0",
                            "contents/database/transaction-isolation-locking.md",
                            "격리 수준",
                        )
                    ]
                )
            return FakeLanceQuery(
                [
                    row(
                        "raw#0",
                        "contents/database/read-committed-vs-repeatable-read-anomalies.md",
                        "트랜잭션 증상",
                    )
                ]
            )

    monkeypatch.setattr(
        searcher,
        "_korean_search_terms_query",
        lambda _prompt: "트랜잭션 격리 수준",
    )
    monkeypatch.setenv("WOOWA_KOREAN_FTS_TERMS_WEIGHT", "0.7")
    debug = {}
    table = FakeLanceTable()

    scored, chunks = searcher._lance_candidate_pool(
        table,
        "트랜잭션 격리수준이란",
        modalities=("fts",),
        debug=debug,
    )

    assert table.prompts == [
        ("트랜잭션 격리수준이란", "fts"),
        ("트랜잭션 격리 수준", "fts"),
    ]
    assert debug["fts_candidate_kinds"] == ["original", "korean_terms"]
    assert {chunks[row_id]["path"] for row_id, _ in scored} == {
        "contents/database/read-committed-vs-repeatable-read-anomalies.md",
        "contents/database/transaction-isolation-locking.md",
    }


def test_lance_fts_can_disable_korean_search_terms_candidate(monkeypatch):
    class EmptyLanceQuery:
        def select(self, _columns):
            return self

        def limit(self, _limit):
            return self

        def to_list(self):
            return []

    class SpyLanceTable:
        def __init__(self):
            self.prompts = []

        def search(self, prompt, *, query_type="fts"):
            self.prompts.append((prompt, query_type))
            return EmptyLanceQuery()

    monkeypatch.setenv("WOOWA_KOREAN_FTS_TERMS_WEIGHT", "0")
    monkeypatch.setattr(
        searcher,
        "_korean_search_terms_query",
        lambda _prompt: "트랜잭션 격리 수준",
    )
    table = SpyLanceTable()

    searcher._lance_candidate_pool(
        table,
        "트랜잭션 격리수준이란",
        modalities=("fts",),
    )

    assert table.prompts == [("트랜잭션 격리수준이란", "fts")]


def test_lance_fts_search_projects_light_payload_columns():
    class SpyLanceQuery:
        def __init__(self):
            self.selected = None
            self.limited = None

        def select(self, columns):
            self.selected = list(columns)
            return self

        def limit(self, limit):
            self.limited = limit
            return self

        def to_list(self):
            return []

    class SpyLanceTable:
        def __init__(self):
            self.query = SpyLanceQuery()

        def search(self, prompt, *, query_type="fts"):
            assert prompt == "latency"
            assert query_type == "fts"
            return self.query

    table = SpyLanceTable()

    searcher._lance_fts_search(table, "latency", 80)

    assert table.query.limited == 80
    assert "chunk_id" in table.query.selected
    assert "_score" in table.query.selected
    assert "dense_vec" not in table.query.selected
    assert "sparse_vec" not in table.query.selected
    assert "colbert_tokens" not in table.query.selected


def test_lance_colbert_rescore_fetches_only_window(monkeypatch):
    def row(idx: int) -> dict:
        return {
            "chunk_id": f"doc#{idx}",
            "doc_id": "doc",
            "path": f"contents/database/doc-{idx}.md",
            "title": f"Doc {idx}",
            "category": "database",
            "difficulty": "beginner",
            "section_path": json.dumps([f"Doc {idx}"]),
            "body": f"body {idx}",
            "char_len": 10,
            "anchors": "[]",
            "_score": float(10 - idx),
        }

    class FakeQuery:
        def __init__(self, rows, *, table=None, payload=False):
            self._rows = rows
            self._table = table
            self._payload = payload
            self._limit = len(rows)

        def select(self, columns):
            if self._payload:
                self._table.payload_selects.append(list(columns))
            return self

        def where(self, where):
            if self._payload:
                self._table.payload_wheres.append(where)
            return self

        def limit(self, limit):
            self._limit = limit
            if self._payload:
                self._table.payload_limits.append(limit)
            return self

        def to_list(self):
            return self._rows[: self._limit]

    class FakeLanceTable:
        def __init__(self):
            self.payload_selects = []
            self.payload_wheres = []
            self.payload_limits = []
            self.fts_rows = [row(i) for i in range(3)]
            self.payload_rows = [
                {
                    "chunk_id": f"doc#{i}",
                    "colbert_tokens": np.ones((2, 8), dtype=np.float16) * (i + 1),
                }
                for i in range(3)
            ]

        def search(self, prompt=None, *, query_type=None, **_kwargs):
            if prompt is None:
                return FakeQuery(self.payload_rows, table=self, payload=True)
            assert query_type == "fts"
            return FakeQuery(self.fts_rows)

    monkeypatch.setenv("WOOWA_RAG_LANCE_COLBERT_RESCORE_WINDOW", "1")
    debug = {}
    table = FakeLanceTable()

    scored, chunks = searcher._lance_candidate_pool(
        table,
        "latency",
        query_encoding={"colbert": [np.ones((2, 8), dtype=np.float16)]},
        modalities=("fts", "colbert"),
        pool_size=3,
        debug=debug,
    )

    assert scored
    assert debug["lance_colbert_rescore_window"] == 1
    assert table.payload_selects == [["chunk_id", "colbert_tokens"]]
    assert table.payload_limits == [1]
    assert "doc#0" in table.payload_wheres[0]
    assert "doc#1" not in table.payload_wheres[0]
    fetched = [
        chunk["chunk_id"]
        for chunk in chunks.values()
        if chunk.get("colbert_tokens") is not None
    ]
    assert fetched == ["doc#0"]


def test_public_search_can_use_explicit_lance_backend(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
        modalities=("fts", "dense", "sparse", "colbert"),
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
    assert debug["stage_ms"]["lance_candidate_plan"] >= 0.0
    assert debug["stage_ms"]["lance_query_encode"] >= 0.0
    assert debug["stage_ms"]["lance_dense_search"] >= 0.0


def test_lance_default_modalities_enable_sparse_with_dense_for_measured_categories():
    out = searcher._resolve_lance_modalities(
        manifest_modalities=("fts", "dense", "sparse", "colbert"),
        requested_modalities=None,
        mode="full",
        learning_points=None,
        signals=[{"category": "database"}],
    )

    assert out == ("fts", "dense", "sparse")


def test_lance_default_modalities_global_sparse_on_after_r2_decision():
    """R2 keeps sparse default-on while the next gate measures whether sparse
    should later become category-gated or weight-reduced."""
    out = searcher._resolve_lance_modalities(
        manifest_modalities=("fts", "dense", "sparse", "colbert"),
        requested_modalities=None,
        mode="full",
        learning_points=None,
        signals=[{"category": "spring"}],
    )

    assert out == ("fts", "dense", "sparse")


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


def test_lance_default_modalities_load_encoder_for_global_dense_sparse(
    tmp_path,
    monkeypatch,
):
    """After the R2 policy update: global dense+sparse ON. Spring is no
    longer a special case — encoder loads, retrieval mixes FTS + dense and
    sparse.

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
    assert "sparse" in debug["modalities"]
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


def test_public_lance_full_mode_applies_reranker_when_enabled(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )

    rerank_calls = []

    def fake_rerank(prompt, ranked, chunks, top_n):
        rerank_calls.append(
            {
                "prompt": prompt,
                "ranked_len": len(ranked),
                "top_n": top_n,
            }
        )
        return ranked

    monkeypatch.setattr(searcher, "_rerank_enabled", lambda flag: True)
    monkeypatch.setattr(searcher, "_rerank", fake_rerank)

    hits = searcher.search(
        "트랜잭션이 뭐예요?",
        mode="full",
        backend="lance",
        index_root=index_root,
        top_k=2,
        use_reranker=True,
    )

    assert hits
    assert rerank_calls
    assert rerank_calls[0]["top_n"] == 4


def test_lance_follow_up_query_uses_recent_context_candidate(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=encoder,
    )
    monkeypatch.setattr(
        searcher,
        "recent_rag_ask_context",
        lambda limit=2: ["concepts=concept:spring/bean"],
    )
    debug = {}

    hits = searcher.search(
        "그럼 왜 그래?",
        mode="cheap",
        backend="lance",
        index_root=index_root,
        top_k=1,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/spring/bean-basics.md"
    assert debug["query_candidate_kinds"] == ["original", "follow_up"]


def test_lance_query_plan_uses_learner_context_before_memory(monkeypatch):
    def fail_if_memory_read(limit=2):
        raise AssertionError("learner_context should provide the follow-up context")

    monkeypatch.setattr(searcher, "recent_rag_ask_context", fail_if_memory_read)

    context = searcher._follow_up_context_for_prompt(
        "그럼 왜 그래?",
        {"recent_rag_ask_context": ["concepts=concept:database/transaction"]},
    )

    assert context == ["concepts=concept:database/transaction"]


def test_lance_cached_rewrite_candidates_are_batch_encoded_once(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "state" / "cs_rag"
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=FakeMultiModalEncoder(),
    )
    prompt = "그거 왜 안 보여?"
    _write_cached_rewrite(
        tmp_path,
        prompt=prompt,
        mode="normalize",
        texts=["Spring Bean dependency injection"],
    )
    spy_encoder = SpyQueryEncoder()
    monkeypatch.setattr(searcher, "_get_lance_query_encoder", lambda _root: spy_encoder)
    monkeypatch.setattr(searcher, "recent_rag_ask_context", lambda limit=2: [])
    debug = {}

    hits = searcher.search(
        prompt,
        mode="full",
        backend="lance",
        index_root=index_root,
        modalities=("fts", "dense", "sparse"),
        top_k=2,
        use_reranker=False,
        debug=debug,
    )

    assert hits
    assert debug["query_candidate_kinds"] == ["original", "rewrite"]
    assert len(spy_encoder.encode_corpus_calls) == 1
    assert spy_encoder.encode_corpus_calls[0]["texts"] == [
        prompt,
        "Spring Bean dependency injection",
    ]
    assert spy_encoder.encode_corpus_calls[0]["batch_size"] == 2
    assert spy_encoder.encode_query_calls == []


def test_lance_cached_rewrite_can_use_env_storage_for_eval_index(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "scratch" / "lance"
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=FakeMultiModalEncoder(),
    )
    prompt = "그거 왜 안 보여?"
    rewrite_storage = tmp_path / "rewrite-cache"
    _write_cached_rewrite(
        tmp_path,
        prompt=prompt,
        mode="normalize",
        texts=["Spring Bean dependency injection"],
        storage=rewrite_storage,
    )
    spy_encoder = SpyQueryEncoder()
    monkeypatch.setattr(searcher, "_get_lance_query_encoder", lambda _root: spy_encoder)
    monkeypatch.setattr(searcher, "recent_rag_ask_context", lambda limit=2: [])
    monkeypatch.setenv("WOOWA_RAG_QUERY_REWRITE_ROOT", str(rewrite_storage))
    debug = {}

    hits = searcher.search(
        prompt,
        mode="full",
        backend="lance",
        index_root=index_root,
        modalities=("fts", "dense", "sparse"),
        top_k=2,
        use_reranker=False,
        debug=debug,
    )

    assert hits
    assert debug["query_candidate_kinds"] == ["original", "rewrite"]
    assert spy_encoder.encode_corpus_calls[0]["texts"] == [
        prompt,
        "Spring Bean dependency injection",
    ]


def test_lance_malformed_rewrite_keeps_single_query_path(tmp_path, monkeypatch):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "state" / "cs_rag"
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=FakeMultiModalEncoder(),
    )
    prompt = "트랜잭션이 뭐예요?"
    _write_malformed_cached_rewrite(tmp_path, prompt=prompt, mode="normalize")
    spy_encoder = SpyQueryEncoder()
    monkeypatch.setattr(searcher, "_get_lance_query_encoder", lambda _root: spy_encoder)
    debug = {}

    hits = searcher.search(
        prompt,
        mode="full",
        backend="lance",
        index_root=index_root,
        modalities=("fts", "dense"),
        top_k=1,
        use_reranker=False,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/database/transaction-basics.md"
    assert debug["query_candidate_kinds"] == ["original"]
    assert len(spy_encoder.encode_corpus_calls) == 1
    assert spy_encoder.encode_corpus_calls[0]["texts"] == [prompt]
    assert spy_encoder.encode_query_calls == []


def test_lance_original_candidate_encodes_topic_hints_without_rewriting_followups():
    assert (
        searcher._lance_encode_text_for_candidate(
            "Spring Bean이 뭐야?",
            "original",
            ["spring-core"],
        )
        == "Spring Bean이 뭐야?\n\nspring-core"
    )
    assert (
        searcher._lance_encode_text_for_candidate(
            "Previous context: concepts=concept:spring/bean\nCurrent question: 왜?",
            "follow_up",
            ["spring-core"],
        )
        == "Previous context: concepts=concept:spring/bean\nCurrent question: 왜?"
    )


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
