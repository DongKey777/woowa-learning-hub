from __future__ import annotations

import json

import pytest

from scripts.learning.rag import indexer
from scripts.learning.rag.eval.runtime_index import resolve_runtime_index_info


def test_resolve_runtime_index_info_reads_legacy_manifest(tmp_path):
    (tmp_path / indexer.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "index_version": indexer.INDEX_VERSION,
                "corpus_hash": "legacy-hash",
                "embed_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "embed_dim": 384,
            }
        ),
        encoding="utf-8",
    )

    info = resolve_runtime_index_info(tmp_path, backend="auto")

    assert info.backend == "legacy"
    assert info.embedding_dim == 384
    assert info.embedding_model.endswith("MiniLM-L12-v2")
    assert info.modalities == ()


def test_resolve_runtime_index_info_reads_lance_manifest_dense_dim(tmp_path):
    (tmp_path / indexer.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "index_version": indexer.LANCE_INDEX_VERSION,
                "schema_uri": "https://woowa-learning-hub/schemas/cs-index-manifest-v3.json",
                "row_count": 1,
                "corpus_hash": "hash",
                "corpus_root": "corpus",
                "built_at": "2026-05-01T00:00:00Z",
                "encoder": {
                    "model_id": "BAAI/bge-m3",
                    "model_version": "BAAI/bge-m3@test",
                    "dense_dim": 1024,
                    "max_length": 512,
                },
                "lancedb": {
                    "version": "0.30.2",
                    "table_name": indexer.LANCE_TABLE_NAME,
                    "indices": {},
                },
                "modalities": ["fts", "dense"],
                "ingest": {"chunk_max_chars": 1600, "chunk_overlap": 0},
            }
        ),
        encoding="utf-8",
    )

    info = resolve_runtime_index_info(tmp_path, backend="auto")

    assert info.backend == "lance"
    assert info.embedding_model == "BAAI/bge-m3"
    assert info.model_revision == "BAAI/bge-m3@test"
    assert info.embedding_dim == 1024
    assert info.modalities == ("fts", "dense")
    assert info.encoder["dense_dim"] == 1024


def test_resolve_runtime_index_info_uses_matching_model_lock_for_old_v3_manifest(tmp_path):
    (tmp_path / indexer.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "index_version": indexer.LANCE_INDEX_VERSION,
                "schema_uri": "https://woowa-learning-hub/schemas/cs-index-manifest-v3.json",
                "row_count": 1,
                "corpus_hash": "hash",
                "corpus_root": "corpus",
                "built_at": "2026-05-01T00:00:00Z",
                "encoder": {
                    "model_id": "custom/model",
                    "model_version": "custom/model@abc",
                    "max_length": 512,
                },
                "lancedb": {"version": "0.30.2", "table_name": "cs_chunks", "indices": {}},
                "modalities": ["fts", "dense"],
                "ingest": {"chunk_max_chars": 1600, "chunk_overlap": 0},
            }
        ),
        encoding="utf-8",
    )
    lock = tmp_path / "rag_models.json"
    lock.write_text(
        json.dumps(
            {
                "index": {"corpus_hash": "hash"},
                "encoder": {"model_id": "custom/model", "dense_dim": 768},
            }
        ),
        encoding="utf-8",
    )

    info = resolve_runtime_index_info(tmp_path, backend="auto", model_lock_path=lock)

    assert info.embedding_dim == 768


def test_resolve_runtime_index_info_rejects_backend_mismatch(tmp_path):
    (tmp_path / indexer.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "index_version": indexer.INDEX_VERSION,
                "corpus_hash": "legacy-hash",
                "embed_model": "m",
                "embed_dim": 384,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match"):
        resolve_runtime_index_info(tmp_path, backend="lance")
