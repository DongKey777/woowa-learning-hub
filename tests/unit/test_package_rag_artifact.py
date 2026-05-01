"""Unit tests for the artifact packager (plan v5 §H0 task v5-4)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
from argparse import Namespace
from pathlib import Path

import pytest

from scripts.remote import package_rag_artifact as P
from scripts.remote.artifact_contract import verify_artifact_dir


# ---------------------------------------------------------------------------
# Helpers — synthesize a minimal LanceDB-style index root
# ---------------------------------------------------------------------------

def _build_fake_index_root(tmp_path: Path, *, valid: bool = True) -> Path:
    """Create a directory that *looks* like an index root v3.

    `valid=True`: includes manifest.json + lance/ + chunk_hashes_per_model.json
    `valid=False`: missing manifest.json → expect IndexRootInvalid
    """
    root = tmp_path / "cs_rag"
    root.mkdir()
    (root / "lance").mkdir()
    (root / "lance" / "fake_table.lance").write_bytes(b"\x00" * 1024)
    (root / "chunk_hashes_per_model.json").write_text(
        json.dumps({"BAAI/bge-m3@fake": {"chunk_001": "sha1:abc"}}),
        encoding="utf-8",
    )
    if valid:
        (root / "manifest.json").write_text(
            json.dumps({
                "index_version": 3,
                "encoder": {
                    "model_id": "BAAI/bge-m3",
                    "model_version": "BAAI/bge-m3@fake",
                },
                "modalities": ["fts", "dense"],
                "row_count": 100,
                "corpus_hash": "sha1:fake",
                "lancedb": {"version": "0.30.2"},
            }),
            encoding="utf-8",
        )
    return root


# ---------------------------------------------------------------------------
# validate_index_root
# ---------------------------------------------------------------------------

def test_validate_accepts_well_formed_root(tmp_path):
    root = _build_fake_index_root(tmp_path)
    P.validate_index_root(root)  # no raise


def test_validate_rejects_missing_dir(tmp_path):
    with pytest.raises(P.IndexRootInvalid):
        P.validate_index_root(tmp_path / "does_not_exist")


def test_validate_rejects_missing_manifest(tmp_path):
    root = _build_fake_index_root(tmp_path, valid=False)
    with pytest.raises(P.IndexRootInvalid, match="manifest.json"):
        P.validate_index_root(root)


def test_validate_rejects_missing_lance_dir(tmp_path):
    root = _build_fake_index_root(tmp_path)
    shutil.rmtree(root / "lance")
    with pytest.raises(P.IndexRootInvalid, match="lance"):
        P.validate_index_root(root)


def test_validate_rejects_v2_manifest(tmp_path):
    root = _build_fake_index_root(tmp_path)
    (root / "manifest.json").write_text(
        json.dumps({"index_version": 2}), encoding="utf-8"
    )
    with pytest.raises(P.IndexRootInvalid, match="index_version"):
        P.validate_index_root(root)


def test_validate_rejects_corrupt_manifest(tmp_path):
    root = _build_fake_index_root(tmp_path)
    (root / "manifest.json").write_text("not json", encoding="utf-8")
    with pytest.raises(P.IndexRootInvalid, match="corrupt"):
        P.validate_index_root(root)


# ---------------------------------------------------------------------------
# zstd availability
# ---------------------------------------------------------------------------

def test_check_zstd_passes_when_available():
    """This environment has zstd installed (verified at session start)."""
    P._check_zstd_available()  # no raise


def test_check_zstd_fails_when_missing(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(P.PackagingError, match="zstd CLI not found"):
        P._check_zstd_available()


# ---------------------------------------------------------------------------
# tar.zst round-trip
# ---------------------------------------------------------------------------

def test_create_tar_zst_round_trip(tmp_path):
    root = _build_fake_index_root(tmp_path)
    output = tmp_path / "archive.tar.zst"
    meta = P._create_tar_zst(source_dir=root, output_path=output)
    assert output.exists()
    assert meta["tar_bytes"] > 0
    assert meta["zst_bytes"] > 0
    assert len(meta["sha256"]) == 64

    # Decompress + extract round-trip
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    subprocess.run(
        ["zstd", "-d", "-q", str(output), "-o", str(tmp_path / "archive.tar")],
        check=True,
    )
    with tarfile.open(tmp_path / "archive.tar") as tf:
        tf.extractall(extracted, filter="data")

    extracted_root = extracted / root.name
    assert (extracted_root / "manifest.json").exists()
    assert (extracted_root / "lance" / "fake_table.lance").exists()
    assert (extracted_root / "chunk_hashes_per_model.json").exists()

    # Manifest content survived
    assert json.loads((extracted_root / "manifest.json").read_text())["index_version"] == 3


def test_create_tar_zst_cleans_up_tmp_tar(tmp_path):
    """The intermediate .tar should be removed even on success."""
    root = _build_fake_index_root(tmp_path)
    output = tmp_path / "archive.tar.zst"
    P._create_tar_zst(source_dir=root, output_path=output)
    # No stray .tar should remain next to the .zst output
    leftover = list(output.parent.glob("*.tar"))
    assert leftover == []


# ---------------------------------------------------------------------------
# Environment + git capture
# ---------------------------------------------------------------------------

def test_capture_environment_includes_python_version():
    env = P.capture_environment()
    assert env["schema_id"] == "rag-build-environment-v1"
    assert "python_version" in env
    assert env["python_version"].startswith(("3.", "4."))  # forward compatible


def test_capture_environment_merges_extra():
    env = P.capture_environment(extra={"gpu_type": "RTX A5000", "cuda_version": "12.4"})
    assert env["gpu_type"] == "RTX A5000"
    assert env["cuda_version"] == "12.4"


def test_capture_environment_records_dep_versions():
    """Best-effort dep versions — not_installed is a valid value."""
    env = P.capture_environment()
    # numpy is required by the project; should be present
    assert env.get("dep_numpy") not in (None, "not_installed")


def test_capture_git_state_returns_schema_id(tmp_path):
    """Even outside a git repo, the schema is consistent."""
    state = P.capture_git_state(tmp_path)
    assert state["schema_id"] == "rag-build-git-state-v1"
    assert "commit_sha" in state
    assert "is_dirty" in state


# ---------------------------------------------------------------------------
# package_artifact orchestrator
# ---------------------------------------------------------------------------

def test_package_artifact_produces_expected_layout(tmp_path):
    root = _build_fake_index_root(tmp_path)
    out_parent = tmp_path / "artifacts"

    result = P.package_artifact(
        index_root=root,
        run_id="r0-test-2026-05-01T0830",
        r_phase="r0",
        output_parent=out_parent,
        repo_root=tmp_path,
        extra_environment={"gpu_type": "RTX A5000"},
        compression_level=3,  # fast for tests
    )

    out_dir = result.output_dir
    assert out_dir.name == "r0-test-2026-05-01T0830"
    assert out_dir.parent == out_parent

    # Required files
    assert (out_dir / "cs_rag_index_root.tar.zst").exists()
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "environment.json").exists()
    assert (out_dir / "run.log").exists()
    assert (out_dir / "repo.commit_or_diff.txt").exists()

    # Manifest schema
    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["schema_id"] == "rag-build-artifact-v1"
    assert manifest["run_id"] == "r0-test-2026-05-01T0830"
    assert manifest["r_phase"] == "r0"
    assert manifest["archive"]["sha256"] == result.sha256
    assert manifest["index_root_summary"]["index_version"] == 3
    assert manifest["index_root_summary"]["modalities"] == ["fts", "dense"]
    assert manifest["environment"]["gpu_type"] == "RTX A5000"
    assert "git_state" in manifest


def test_package_artifact_rejects_invalid_index_root(tmp_path):
    invalid = tmp_path / "nope"
    with pytest.raises(P.IndexRootInvalid):
        P.package_artifact(
            index_root=invalid,
            run_id="x",
            r_phase="r0",
            output_parent=tmp_path / "art",
        )


def test_package_artifact_rejects_unknown_r_phase(tmp_path):
    root = _build_fake_index_root(tmp_path)
    with pytest.raises(P.PackagingError, match="r_phase"):
        P.package_artifact(
            index_root=root,
            run_id="x",
            r_phase="r99",
            output_parent=tmp_path / "art",
        )


def test_package_artifact_extra_metadata_passed_through(tmp_path):
    root = _build_fake_index_root(tmp_path)
    result = P.package_artifact(
        index_root=root,
        run_id="r1-fake",
        r_phase="r1",
        output_parent=tmp_path / "art",
        extra_metadata={"build_started_at": "2026-05-01T07:00Z", "encoder_revision": "abc123"},
        compression_level=3,
    )
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["extra"]["build_started_at"] == "2026-05-01T07:00Z"
    assert manifest["extra"]["encoder_revision"] == "abc123"


def test_strict_r3_metadata_requires_all_fields():
    args = Namespace(
        strict_r3=True,
        build_command="bin/cs-index-build --backend lance",
        package_lock=None,
        qrel_hash="sha256:qrels",
        local_runtime_machine="M5 MacBook Air 13",
        local_runtime_memory_gb=16,
        local_runtime_accelerator="Apple Silicon MPS",
    )

    with pytest.raises(P.PackagingError, match="--package-lock"):
        P._strict_r3_metadata_from_args(args)


def test_package_cli_strict_r3_output_passes_import_contract(tmp_path, capsys):
    root = _build_fake_index_root(tmp_path)
    out_parent = tmp_path / "art"

    rc = P.main(
        [
            "--index-root",
            str(root),
            "--run-id",
            "r3-strict-test",
            "--r-phase",
            "r3",
            "--output-parent",
            str(out_parent),
            "--compression-level",
            "3",
            "--strict-r3",
            "--build-command",
            "bin/cs-index-build --backend lance",
            "--package-lock",
            "requirements-lock:fake",
            "--qrel-hash",
            "sha256:qrels",
            "--local-runtime-machine",
            "M5 MacBook Air 13",
            "--local-runtime-memory-gb",
            "16",
            "--local-runtime-accelerator",
            "Apple Silicon MPS",
        ]
    )

    assert rc == 0
    assert "r3-strict-test" in capsys.readouterr().out
    result = verify_artifact_dir(out_parent / "r3-strict-test", strict_r3=True)
    assert result["strict_r3"] is True


def test_package_artifact_compression_actually_compresses(tmp_path):
    """For a directory with bytes that compress well, ratio < 1.0."""
    root = _build_fake_index_root(tmp_path)
    # Make lance/ much larger so compression has something to work with
    big_data = b"A" * 100_000  # repeating bytes — highly compressible
    (root / "lance" / "big.lance").write_bytes(big_data)

    result = P.package_artifact(
        index_root=root,
        run_id="r-test",
        r_phase="r0",
        output_parent=tmp_path / "art",
        compression_level=3,
    )
    # ratio = compressed/uncompressed; for repeating bytes should be tiny
    assert result.bytes_compressed < result.bytes_uncompressed * 0.5


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_main_round_trip(tmp_path, capsys):
    root = _build_fake_index_root(tmp_path)
    rc = P.main([
        "--index-root", str(root),
        "--run-id", "r0-cli-test",
        "--r-phase", "r0",
        "--output-parent", str(tmp_path / "art"),
        "--compression-level", "3",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["schema_id"] == "rag-build-artifact-v1"
    assert payload["run_id"] == "r0-cli-test"
    assert "sha256" in payload
    assert Path(payload["archive_path"]).exists()


def test_cli_main_returns_2_on_packaging_error(tmp_path, capsys):
    rc = P.main([
        "--index-root", str(tmp_path / "missing"),
        "--run-id", "x",
        "--r-phase", "r0",
        "--output-parent", str(tmp_path / "art"),
    ])
    assert rc == 2


def test_cli_main_passes_gpu_metadata(tmp_path, capsys):
    root = _build_fake_index_root(tmp_path)
    rc = P.main([
        "--index-root", str(root),
        "--run-id", "r1-cli-gpu",
        "--r-phase", "r1",
        "--output-parent", str(tmp_path / "art"),
        "--gpu-type", "RTX A6000",
        "--cuda-version", "12.4",
        "--compression-level", "3",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    manifest = json.loads(Path(payload["archive_path"]).parent.joinpath("manifest.json").read_text())
    assert manifest["environment"]["gpu_type"] == "RTX A6000"
    assert manifest["environment"]["cuda_version"] == "12.4"
