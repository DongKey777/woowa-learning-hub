"""Unit tests for scripts.learning.rag.eval.manifest.

Coverage targets:
- Round-trip: dataclass → dict → dataclass preserves all fields
- Schema rejects missing required fields
- Schema rejects bad enum (device, mode)
- Schema rejects negative latency / RSS / dim
- Schema rejects extra unknown properties
- File I/O: dump_manifest writes valid JSON, load_manifest validates
- model_revision and reranker_model accept null (optional pin)
"""

from __future__ import annotations

import json

import jsonschema
import pytest

from scripts.learning.rag.eval import manifest as M


def _good_blob() -> dict:
    """Schema-valid manifest blob for positive tests."""
    return {
        "corpus_hash": "abc123",
        "index_version": 2,
        "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "model_revision": "0a8f1e",
        "embedding_dim": 384,
        "device": "mps",
        "reranker_model": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        "fusion_weights": {"k": 60, "w_bm25": 1.0, "w_dense": 1.0},
        "top_k": 5,
        "mode": "full",
        "latency_p50_warm": 120.5,
        "latency_p95_warm": 350.0,
        "cold_start_ms": 1800.0,
    }


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_validate_good_manifest_passes():
    M.validate_manifest(_good_blob())


def test_validate_rejects_missing_required_field():
    blob = _good_blob()
    del blob["embedding_dim"]
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_unknown_property():
    blob = _good_blob()
    blob["surprise"] = "noop"
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_bad_device():
    blob = _good_blob()
    blob["device"] = "tpu"
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_bad_mode():
    blob = _good_blob()
    blob["mode"] = "bogus"
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_negative_latency():
    blob = _good_blob()
    blob["latency_p50_warm"] = -1
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_zero_top_k():
    blob = _good_blob()
    blob["top_k"] = 0
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_negative_dim():
    blob = _good_blob()
    blob["embedding_dim"] = -1
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_accepts_null_model_revision():
    """We allow null pins so the first-run baseline can document an
    unpinned model state."""
    blob = _good_blob()
    blob["model_revision"] = None
    M.validate_manifest(blob)


def test_validate_accepts_null_reranker():
    """A pipeline run with reranker disabled still produces a manifest."""
    blob = _good_blob()
    blob["reranker_model"] = None
    M.validate_manifest(blob)


def test_validate_accepts_h7_modal_blocks():
    """H7 ablation reports must capture the measured backend, modality
    subset, encoder identity, and LanceDB index metadata."""
    blob = _good_blob()
    blob.update(
        {
            "backend": "lance",
            "modalities": ["fts", "dense", "sparse", "colbert"],
            "encoder": {
                "model_id": "BAAI/bge-m3",
                "model_version": "BAAI/bge-m3@sha",
            },
            "lancedb": {
                "version": "0.30.2",
                "table_name": "chunks",
                "indices": {"dense": {"type": "unindexed"}},
            },
        }
    )
    M.validate_manifest(blob)


def test_validate_rejects_unknown_modality():
    blob = _good_blob()
    blob["modalities"] = ["fts", "bogus"]
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_fusion_weights_missing_k():
    blob = _good_blob()
    blob["fusion_weights"] = {"w_bm25": 1.0, "w_dense": 1.0}
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


def test_validate_rejects_negative_fusion_weight():
    blob = _good_blob()
    blob["fusion_weights"] = {"k": 60, "w_bm25": -0.1, "w_dense": 1.0}
    with pytest.raises(jsonschema.ValidationError):
        M.validate_manifest(blob)


# ---------------------------------------------------------------------------
# Dataclass round-trip
# ---------------------------------------------------------------------------

def test_dict_to_manifest_preserves_all_fields():
    blob = _good_blob()
    manifest = M.dict_to_manifest(blob)
    assert manifest.corpus_hash == "abc123"
    assert manifest.embedding_dim == 384
    assert manifest.device == "mps"
    assert manifest.fusion_weights.k == 60
    assert manifest.fusion_weights.w_bm25 == 1.0
    assert manifest.top_k == 5
    assert manifest.mode == "full"
    assert manifest.backend == "legacy"
    assert manifest.modalities == ()


def test_dict_to_manifest_preserves_h7_modal_blocks():
    blob = _good_blob()
    blob.update(
        {
            "backend": "lance",
            "modalities": ["fts", "dense"],
            "encoder": {"model_id": "BAAI/bge-m3"},
            "lancedb": {"table_name": "chunks"},
        }
    )
    manifest = M.dict_to_manifest(blob)
    assert manifest.backend == "lance"
    assert manifest.modalities == ("fts", "dense")
    assert manifest.encoder == {"model_id": "BAAI/bge-m3"}
    assert manifest.lancedb == {"table_name": "chunks"}


def test_round_trip_dataclass_to_dict_to_dataclass():
    blob = _good_blob()
    m1 = M.dict_to_manifest(blob)
    blob2 = M.manifest_to_dict(m1)
    m2 = M.dict_to_manifest(blob2)
    assert m1 == m2


def test_manifest_to_dict_validates_output():
    """Constructing a malformed dataclass and serialising should fail
    validation rather than silently emit garbage. We check this by
    bypassing the dataclass invariants and forcing an invalid mode."""
    m = M.RunManifest(
        corpus_hash="x",
        index_version=2,
        embedding_model="m",
        model_revision=None,
        embedding_dim=384,
        device="mps",
        reranker_model=None,
        fusion_weights=M.FusionWeights.default(),
        top_k=5,
        mode="bogus",  # invalid; passes dataclass but fails schema
        latency_p50_warm=0.0,
        latency_p95_warm=0.0,
        cold_start_ms=0.0,
    )
    with pytest.raises(jsonschema.ValidationError):
        M.manifest_to_dict(m)


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def test_dump_and_load_manifest(tmp_path):
    manifest = M.dict_to_manifest(_good_blob())
    path = tmp_path / "manifest.json"
    M.dump_manifest(manifest, path)

    # File parses as JSON, validates, and round-trips
    blob = json.loads(path.read_text(encoding="utf-8"))
    M.validate_manifest(blob)
    reloaded = M.load_manifest(path)
    assert reloaded == manifest


def test_load_invalid_manifest_raises(tmp_path):
    path = tmp_path / "broken.json"
    bad = _good_blob()
    bad["device"] = "tpu"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(jsonschema.ValidationError):
        M.load_manifest(path)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def test_default_fusion_weights_match_current_searcher():
    """Sanity: the default mirrors searcher.py's static RRF."""
    fw = M.FusionWeights.default()
    assert fw.k == 60
    assert fw.w_bm25 == 1.0
    assert fw.w_dense == 1.0
