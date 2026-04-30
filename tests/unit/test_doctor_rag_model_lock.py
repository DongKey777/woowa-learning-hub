from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.workbench import cli as CLI


MODEL_ID = "BAAI/bge-m3"
MODEL_VERSION = "BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181"


def _write_lock_config(
    root: Path,
    *,
    index_version: int = 3,
    model_id: str = MODEL_ID,
    model_version: str = MODEL_VERSION,
    modalities: list[str] | None = None,
    row_count: int = 27155,
) -> None:
    config_path = root / "config" / "rag_models.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps({
            "index": {
                "index_version": index_version,
                "modalities": modalities or ["fts", "dense", "sparse"],
                "row_count": row_count,
            },
            "encoder": {
                "model_id": model_id,
                "model_version": model_version,
            },
        }),
        encoding="utf-8",
    )


def _write_manifest(
    root: Path,
    *,
    index_version: int = 3,
    model_id: str = MODEL_ID,
    model_version: str = MODEL_VERSION,
    modalities: list[str] | None = None,
    row_count: int = 27155,
) -> None:
    manifest_path = root / "state" / "cs_rag" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({
            "index_version": index_version,
            "row_count": row_count,
            "encoder": {
                "model_id": model_id,
                "model_version": model_version,
            },
            "modalities": modalities or ["dense", "sparse", "fts"],
        }),
        encoding="utf-8",
    )


def test_rag_model_lock_report_ok_when_manifest_matches_config(tmp_path: Path) -> None:
    _write_lock_config(tmp_path)
    _write_manifest(tmp_path)

    report = CLI._rag_model_lock_report(tmp_path)

    assert report["status"] == "OK"
    assert report["line"].startswith("OK rag_model_lock:")
    assert report["warnings"] == []
    assert set(report["compared"]) == {
        "index_version",
        "encoder.model_id",
        "encoder.model_version",
        "modalities",
        "row_count",
    }


def test_rag_model_lock_report_warns_on_manifest_mismatches(tmp_path: Path) -> None:
    _write_lock_config(tmp_path)
    _write_manifest(
        tmp_path,
        index_version=2,
        model_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_version="old-model@sha",
        modalities=["dense"],
        row_count=123,
    )

    report = CLI._rag_model_lock_report(tmp_path)

    assert report["status"] == "WARN"
    assert report["line"] == "WARN rag_model_lock: 5 mismatch(es) against config/rag_models.json"
    assert len(report["warnings"]) == 5
    assert any("index_version expected 3, got 2" in warning for warning in report["warnings"])
    assert any("encoder.model_id expected" in warning for warning in report["warnings"])
    assert any("encoder.model_version expected" in warning for warning in report["warnings"])
    assert any("modalities expected" in warning for warning in report["warnings"])
    assert any("row_count expected 27155, got 123" in warning for warning in report["warnings"])


def test_rag_model_lock_report_warns_when_manifest_missing(tmp_path: Path) -> None:
    _write_lock_config(tmp_path)

    report = CLI._rag_model_lock_report(tmp_path)

    assert report["status"] == "WARN"
    assert "state/cs_rag/manifest.json missing" in report["line"]


def test_rag_model_lock_report_skips_when_config_missing(tmp_path: Path) -> None:
    report = CLI._rag_model_lock_report(tmp_path)

    assert report["status"] == "SKIP"
    assert report["warnings"] == []
    assert report["line"] == "SKIP rag_model_lock: config/rag_models.json missing"


def test_cmd_doctor_includes_rag_model_lock_without_ml_deps(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    _write_lock_config(tmp_path)
    _write_manifest(tmp_path)
    missions_dir = tmp_path / "missions"
    registry_path = tmp_path / "state" / "repo-registry.json"
    pr_archive_dir = tmp_path / "scripts" / "pr_archive"
    missions_dir.mkdir()
    registry_path.parent.mkdir(exist_ok=True)
    registry_path.write_text(json.dumps({"repos": []}), encoding="utf-8")
    pr_archive_dir.mkdir(parents=True)

    monkeypatch.setattr(CLI, "ROOT", tmp_path)
    monkeypatch.setattr(CLI, "MISSIONS_DIR", missions_dir)
    monkeypatch.setattr(CLI, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(CLI, "PR_ARCHIVE_DIR", pr_archive_dir)
    monkeypatch.setattr(CLI, "ensure_global_layout", lambda: None)
    monkeypatch.setattr(
        CLI.shutil,
        "which",
        lambda name: "/usr/bin/python3" if name == "python3" else None,
    )

    assert CLI.cmd_doctor(argparse.Namespace()) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["rag_model_lock"]["status"] == "OK"
    assert payload["rag_model_lock"]["line"].startswith("OK rag_model_lock:")
    assert payload["gh_auth"] is None
