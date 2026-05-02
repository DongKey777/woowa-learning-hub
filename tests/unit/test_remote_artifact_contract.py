from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.remote.artifact_contract import (
    ArtifactVerificationError,
    verify_artifact_dir,
)


def _write_artifact(tmp_path: Path, *, strict: bool = True) -> Path:
    artifact_dir = tmp_path / "artifact"
    artifact_dir.mkdir()
    archive = artifact_dir / "cs_rag_index_root.tar.zst"
    archive.write_bytes(b"fake archive")
    sidecar_bytes = b'{"corpus_hash":"sha256:corpus","row_count":100,"document_count":1}'
    extra = {}
    if strict:
        extra = {
            "build_command": "bin/cs-index-build --backend r3",
            "package_lock": "requirements-lock:fake",
            "qrel_hash": "sha256:qrels",
            "local_runtime_profile": {
                "machine": "M5 MacBook Air 13",
                "memory_gb": 16,
                "accelerator": "Apple Silicon MPS",
            },
        }
    manifest = {
        "schema_id": "rag-build-artifact-v1",
        "run_id": "r3-test",
        "archive": {
            "path": archive.name,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        },
        "index_root_summary": {
            "index_version": 3,
            "encoder": {"model_id": "BAAI/bge-m3", "model_version": "fake"},
            "corpus_hash": "sha256:corpus",
            "r3": {
                "query_plan_version": "r3.0",
                "retrievers": {
                    "lexical_sidecar": "metadata-bm25-v1",
                    "dense": "bge-m3-dense:fake",
                    "sparse_sidecar": "bge-m3-sparse:fake",
                    "signal": "route-tags-v1",
                    "fusion": "weighted-rrf-doc-diversity-v1",
                },
                "concept_catalog": {"sha256": "0" * 64},
                "qrels": {
                    "sha256": "1" * 64,
                    "query_count": 208,
                },
            },
            "r3_sidecars": {
                "lexical": {
                    "path": "r3_lexical_sidecar.json",
                    "sha256": hashlib.sha256(sidecar_bytes).hexdigest(),
                    "corpus_hash": "sha256:corpus",
                    "row_count": 100,
                    "document_count": 1,
                }
            },
        },
        "environment": {"python_version": "3.12.0"},
        "git_state": {"commit_sha": "abc123"},
        "extra": extra,
    }
    (artifact_dir / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return artifact_dir


def test_verify_artifact_dir_accepts_strict_r3_manifest(tmp_path):
    artifact_dir = _write_artifact(tmp_path, strict=True)

    result = verify_artifact_dir(artifact_dir, strict_r3=True)

    assert result["strict_r3"] is True
    assert result["index_version"] == 3
    assert result["commit_sha"] == "abc123"


def test_verify_artifact_dir_rejects_checksum_mismatch(tmp_path):
    artifact_dir = _write_artifact(tmp_path, strict=True)
    (artifact_dir / "cs_rag_index_root.tar.zst").write_bytes(b"changed")

    with pytest.raises(ArtifactVerificationError, match="sha256 mismatch"):
        verify_artifact_dir(artifact_dir, strict_r3=True)


def test_verify_artifact_dir_rejects_missing_strict_metadata(tmp_path):
    artifact_dir = _write_artifact(tmp_path, strict=False)

    with pytest.raises(ArtifactVerificationError, match="extra.build_command"):
        verify_artifact_dir(artifact_dir, strict_r3=True)
