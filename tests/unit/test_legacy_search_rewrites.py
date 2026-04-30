from __future__ import annotations

import json
from pathlib import Path

from scripts.learning import integration
from scripts.learning.rag import corpus_loader, indexer, query_rewrites, searcher


class ReadyReport:
    state = "ready"
    reason = "ready"
    corpus_hash = "fixture"
    index_manifest_hash = "fixture"
    next_command = None


def _chunk(
    doc_id: str,
    path: str,
    title: str,
    category: str,
    body: str,
) -> corpus_loader.CorpusChunk:
    return corpus_loader.CorpusChunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}#0",
        path=path,
        title=title,
        category=category,
        section_title="핵심 개념",
        section_path=[title, "핵심 개념"],
        body=body,
        char_len=len(body),
    )


def _build_legacy_index(
    index_root: Path,
    chunks: list[corpus_loader.CorpusChunk],
) -> list[int]:
    index_root.mkdir(parents=True, exist_ok=True)
    sqlite_path, dense_path, manifest_path = indexer._paths(index_root)
    conn = indexer._open_sqlite(sqlite_path)
    try:
        row_ids = indexer._insert_chunks(conn, chunks)
    finally:
        conn.close()
    manifest_path.write_text(
        json.dumps(
            {
                "index_version": indexer.INDEX_VERSION,
                "embed_model": "fixture",
                "embed_dim": 0,
                "row_count": len(chunks),
                "corpus_hash": "fixture",
                "corpus_root": "fixture",
            }
        ),
        encoding="utf-8",
    )
    dense_path.touch()
    return [int(row_id) for row_id in row_ids]


def _write_cached_rewrite(
    repo_root: Path,
    *,
    prompt: str,
    mode: str,
    texts: list[str],
) -> None:
    storage = repo_root / "state" / "cs_rag" / "query_rewrites"
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


def test_augment_legacy_uses_cached_rewrite_candidate(tmp_path):
    index_root = tmp_path / "state" / "cs_rag"
    _build_legacy_index(
        index_root,
        [
            _chunk(
                "projection",
                "contents/design-pattern/read-model-staleness-read-your-writes.md",
                "Read Model Staleness",
                "design-pattern",
                "read model staleness read your writes projection lag after write",
            ),
            _chunk(
                "spring",
                "contents/spring/spring-bean-di-basics.md",
                "Spring Bean Basics",
                "spring",
                "spring bean container dependency injection component scan",
            ),
        ],
    )
    prompt = "그거 왜 안 보여?"
    _write_cached_rewrite(
        tmp_path,
        prompt=prompt,
        mode="normalize",
        texts=["read model staleness read your writes projection lag"],
    )

    result = integration.augment(
        prompt=prompt,
        learning_points=None,
        cs_search_mode="cheap",
        index_root=index_root,
        readiness=ReadyReport(),
        top_k=1,
    )

    assert result["meta"]["backend"] == "legacy"
    bucket_hits = next(iter(result["by_fallback_key"].values()))
    assert bucket_hits[0]["path"] == (
        "contents/design-pattern/read-model-staleness-read-your-writes.md"
    )


def test_legacy_search_cache_miss_keeps_single_query_path(tmp_path, monkeypatch):
    index_root = tmp_path / "state" / "cs_rag"
    _build_legacy_index(
        index_root,
        [
            _chunk(
                "tx",
                "contents/database/transaction-isolation-basics.md",
                "Transaction Isolation Basics",
                "database",
                "transaction isolation basics commit rollback",
            ),
        ],
    )

    def fail_weighted_rrf(_rankings, *, k=searcher.RRF_K):
        raise AssertionError("cache miss should keep the legacy single-query path")

    monkeypatch.setattr(searcher, "weighted_rrf_merge", fail_weighted_rrf)
    debug = {}

    hits = searcher.search(
        "transaction isolation",
        mode="cheap",
        index_root=index_root,
        top_k=1,
        debug=debug,
    )

    assert hits[0]["path"] == "contents/database/transaction-isolation-basics.md"
    assert "query_candidate_kinds" not in debug


def test_legacy_full_mode_runs_dense_for_cached_rewrite_candidates(
    tmp_path,
    monkeypatch,
):
    index_root = tmp_path / "state" / "cs_rag"
    row_ids = _build_legacy_index(
        index_root,
        [
            _chunk(
                "surface",
                "contents/general/surface-original.md",
                "Surface Original",
                "general",
                "surface term original wording",
            ),
            _chunk(
                "semantic",
                "contents/database/semantic-dense-target.md",
                "Vector Target",
                "database",
                "chosen by fake vector search",
            ),
        ],
    )
    prompt = "surface term"
    _write_cached_rewrite(
        tmp_path,
        prompt=prompt,
        mode="normalize",
        texts=["semantic rewrite"],
    )
    dense_calls = []

    def fake_dense_search(root, query_text, topic_hints, limit):
        dense_calls.append((root, query_text, topic_hints, limit))
        if query_text == "semantic rewrite":
            return [(row_ids[1], 0.99)]
        return []

    monkeypatch.setattr(searcher, "_dense_search", fake_dense_search)
    debug = {}

    hits = searcher.search(
        prompt,
        mode="full",
        index_root=index_root,
        topic_hints=["legacy-topic"],
        top_k=2,
        use_reranker=False,
        debug=debug,
    )

    assert debug["query_candidate_kinds"] == ["original", "rewrite"]
    assert [call[1:3] for call in dense_calls] == [
        ("surface term", ["legacy-topic"]),
        ("semantic rewrite", None),
    ]
    assert [hit["path"] for hit in hits] == [
        "contents/general/surface-original.md",
        "contents/database/semantic-dense-target.md",
    ]
