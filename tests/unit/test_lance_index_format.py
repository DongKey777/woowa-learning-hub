from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import validate

from scripts.learning.rag import indexer


def _manifest_v3() -> dict:
    return {
        "index_version": 3,
        "schema_uri": "https://woowa-learning-hub/schemas/cs-index-manifest-v3.json",
        "row_count": 2,
        "corpus_hash": "sha1:test",
        "corpus_root": "knowledge/cs",
        "built_at": "2026-04-30T00:00:00Z",
        "encoder": {
            "model_id": "BAAI/bge-m3",
            "model_version": "BAAI/bge-m3@abc",
            "max_length": 8192,
        },
        "lancedb": {
            "version": "0.30.2",
            "table_name": "cs_chunks",
            "indices": {
                "dense": {
                    "type": "IVF_PQ",
                    "num_partitions": 256,
                    "num_sub_vectors": 64,
                },
                "fts": {
                    "type": "tantivy",
                    "tokenizer": "ngram",
                },
                "colbert": {
                    "type": "MULTI_VECTOR",
                    "metric": "max_sim",
                    "dtype": "float16",
                },
            },
        },
        "modalities": ["dense", "sparse", "colbert", "fts"],
        "ingest": {
            "chunk_max_chars": 1600,
            "chunk_overlap": 0,
        },
    }


def test_cs_index_manifest_v3_schema_accepts_probe_resolved_shape():
    schema = json.loads(Path("schemas/cs-index-manifest-v3.json").read_text(encoding="utf-8"))
    validate(_manifest_v3(), schema)


def test_read_manifest_v3_rejects_legacy_v2(tmp_path):
    (tmp_path / indexer.MANIFEST_NAME).write_text(
        json.dumps({"index_version": 2, "corpus_hash": "sha1:test"}),
        encoding="utf-8",
    )

    with pytest.raises(indexer.IncompatibleIndexError, match="expected LanceDB index_version 3"):
        indexer.read_manifest_v3(tmp_path)


def test_open_lance_table_opens_existing_v3_table(tmp_path):
    import lancedb
    import pyarrow as pa

    (tmp_path / indexer.MANIFEST_NAME).write_text(
        json.dumps(_manifest_v3()),
        encoding="utf-8",
    )
    db = lancedb.connect(tmp_path / indexer.LANCE_DIR_NAME)
    db.create_table(
        indexer.LANCE_TABLE_NAME,
        data=[{"chunk_id": "c1", "body": "hello"}],
        schema=pa.schema([("chunk_id", pa.string()), ("body", pa.string())]),
        mode="overwrite",
    )

    table = indexer.open_lance_table(tmp_path)

    assert table.count_rows() == 1

