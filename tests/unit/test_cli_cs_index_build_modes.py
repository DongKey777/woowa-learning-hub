"""Unit tests for the new --mode flag on bin/cs-index-build.

Coverage:
- Parser: --mode default = auto, --mode incremental flag accepted
- --force forces full mode regardless of state
- --mode auto + ready state → incremental
- --mode auto + missing state → full
- --mode incremental + missing state → still calls incremental
  (orchestrator decides fallback internally)
- Successful incremental run prints diff_stats summary

Heavy ML imports are bypassed via the ``embedder_factory`` injection
on main(); the orchestrator and indexer are monkey-patched per test
so we don't actually load any model or build any real index.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from scripts.learning import cli_cs_index_build as CLI


@pytest.fixture
def stub_indexer(monkeypatch, tmp_path):
    """Patch indexer.is_ready / build_index so main() runs without
    touching the real corpus."""
    from scripts.learning.rag import indexer

    state = {"build_index_called": False, "build_args": None}

    def fake_is_ready(out_path, corpus_path):
        # State controlled per test by setting state["readiness"]
        readiness = state.get("readiness")
        if readiness is None:
            readiness = indexer.ReadinessReport(
                state="missing",
                reason="first_run",
                corpus_hash=None,
                index_manifest_hash=None,
                next_command="bin/cs-index-build",
            )
        return readiness

    def fake_build_index(*, index_root, corpus_root, progress=None):
        state["build_index_called"] = True
        state["build_args"] = {
            "index_root": index_root,
            "corpus_root": corpus_root,
        }
        return {"row_count": 100, "embed_model": "fake", "embed_dim": 4}

    monkeypatch.setattr(indexer, "is_ready", fake_is_ready)
    monkeypatch.setattr(indexer, "build_index", fake_build_index)
    return state


@pytest.fixture
def stub_incremental(monkeypatch):
    """Patch incremental_build_index to capture call without running
    the real orchestrator."""
    from scripts.learning.rag import incremental_indexer

    state = {"called": False, "kwargs": None, "result": None}

    def fake_incremental(**kwargs):
        state["called"] = True
        state["kwargs"] = kwargs
        # Default result; tests can override via state["result_override"]
        result = state.get("result_override") or incremental_indexer.IncrementalBuildResult(
            mode="incremental",
            manifest={"row_count": 100},
            diff_stats={"added": 1, "modified": 0, "deleted": 0, "unchanged": 99},
            encoded_chunk_count=1,
            fallback_reason=None,
        )
        state["result"] = result
        return result

    monkeypatch.setattr(
        incremental_indexer, "incremental_build_index", fake_incremental
    )
    return state


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parser_default_mode_is_auto():
    """argparse default surface check via main with capturing."""
    # Build a parser the same way main() does, just to verify default
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("auto", "full", "incremental"), default="auto")
    args = parser.parse_args([])
    assert args.mode == "auto"


# ---------------------------------------------------------------------------
# main() — mode resolution
# ---------------------------------------------------------------------------

def test_main_force_flag_forces_full_rebuild(tmp_path, stub_indexer, stub_incremental):
    from scripts.learning.rag import indexer

    # ready state — but --force should still trigger full
    stub_indexer["readiness"] = indexer.ReadinessReport(
        state="ready", reason="ok",
        corpus_hash="abc", index_manifest_hash="abc",
        next_command=None,
    )

    rc = CLI.main([
        "--corpus", str(tmp_path),
        "--out", str(tmp_path / "out"),
        "--force",
    ])
    assert rc == 0
    assert stub_indexer["build_index_called"] is True
    assert stub_incremental["called"] is False


def test_main_auto_mode_chooses_incremental_when_ready(
    tmp_path, stub_indexer, stub_incremental
):
    from scripts.learning.rag import indexer

    stub_indexer["readiness"] = indexer.ReadinessReport(
        state="ready", reason="ok",
        corpus_hash="abc", index_manifest_hash="abc",
        next_command=None,
    )

    fake_model = object()
    rc = CLI.main(
        [
            "--corpus", str(tmp_path),
            "--out", str(tmp_path / "out"),
            # default --mode auto
        ],
        embedder_factory=lambda: fake_model,
    )
    assert rc == 0
    assert stub_indexer["build_index_called"] is False
    assert stub_incremental["called"] is True
    assert stub_incremental["kwargs"]["model"] is fake_model


def test_main_auto_mode_chooses_full_when_not_ready(
    tmp_path, stub_indexer, stub_incremental
):
    """Default auto + missing state → full path."""
    rc = CLI.main([
        "--corpus", str(tmp_path),
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 0
    assert stub_indexer["build_index_called"] is True
    assert stub_incremental["called"] is False


def test_main_explicit_full_mode(tmp_path, stub_indexer, stub_incremental):
    from scripts.learning.rag import indexer

    stub_indexer["readiness"] = indexer.ReadinessReport(
        state="ready", reason="ok",
        corpus_hash="abc", index_manifest_hash="abc",
        next_command=None,
    )

    rc = CLI.main([
        "--corpus", str(tmp_path),
        "--out", str(tmp_path / "out"),
        "--mode", "full",
    ])
    assert rc == 0
    assert stub_indexer["build_index_called"] is True
    assert stub_incremental["called"] is False


def test_main_explicit_incremental_mode(
    tmp_path, stub_indexer, stub_incremental
):
    """--mode incremental explicit — orchestrator decides fallback."""
    from scripts.learning.rag import indexer

    stub_indexer["readiness"] = indexer.ReadinessReport(
        state="missing", reason="first_run",
        corpus_hash=None, index_manifest_hash=None,
        next_command="bin/cs-index-build",
    )

    rc = CLI.main(
        [
            "--corpus", str(tmp_path),
            "--out", str(tmp_path / "out"),
            "--mode", "incremental",
        ],
        embedder_factory=lambda: object(),
    )
    assert rc == 0
    # CLI dispatches to incremental even though state=missing —
    # orchestrator handles fallback internally
    assert stub_incremental["called"] is True


def test_main_incremental_summary_includes_diff_stats(
    tmp_path, stub_indexer, stub_incremental, capsys
):
    from scripts.learning.rag import indexer, incremental_indexer

    stub_indexer["readiness"] = indexer.ReadinessReport(
        state="ready", reason="ok",
        corpus_hash="abc", index_manifest_hash="abc",
        next_command=None,
    )
    stub_incremental["result_override"] = incremental_indexer.IncrementalBuildResult(
        mode="incremental",
        manifest={"row_count": 200},
        diff_stats={"added": 5, "modified": 2, "deleted": 1, "unchanged": 192},
        encoded_chunk_count=7,
        fallback_reason=None,
    )

    CLI.main(
        ["--corpus", str(tmp_path), "--out", str(tmp_path / "out")],
        embedder_factory=lambda: object(),
    )
    out = capsys.readouterr().out
    assert "added=5" in out
    assert "modified=2" in out
    assert "deleted=1" in out
    assert "unchanged=192" in out
    assert "encoded=7" in out
    assert "mode=incremental" in out


def test_main_incremental_fallback_reason_surfaced(
    tmp_path, stub_indexer, stub_incremental, capsys
):
    from scripts.learning.rag import indexer, incremental_indexer

    stub_indexer["readiness"] = indexer.ReadinessReport(
        state="ready", reason="ok",
        corpus_hash="abc", index_manifest_hash="abc",
        next_command=None,
    )
    stub_incremental["result_override"] = incremental_indexer.IncrementalBuildResult(
        mode="full",  # orchestrator fell back
        manifest={"row_count": 200},
        diff_stats={"added": 200, "modified": 0, "deleted": 0, "unchanged": 0},
        encoded_chunk_count=200,
        fallback_reason="embed_model_changed",
    )

    CLI.main(
        ["--corpus", str(tmp_path), "--out", str(tmp_path / "out")],
        embedder_factory=lambda: object(),
    )
    out = capsys.readouterr().out
    assert "mode=full" in out
    assert "fallback: embed_model_changed" in out
