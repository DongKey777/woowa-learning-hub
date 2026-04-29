"""Unit tests for scripts.learning.rag.eval.ab_retriever.

Coverage targets:
- ABRetriever swaps searcher._QUERY_EMBEDDER on enter
- Restores original on exit (even when an exception fires)
- Uses outside ``with`` raises RuntimeError
- Manifest mismatch raises IndexCompatibilityError before swap
- Retrieve calls searcher.search with the correct kwargs
- Retrieve returns ``path`` field of each hit
- Multiple sequential retrievers don't leak state across contexts
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag import indexer, searcher
from scripts.learning.rag.eval import ab_retriever as AB
from scripts.learning.rag.eval.cache import IndexCompatibilityError


def _fake_query():
    """Duck-typed minimal GradedQuery for retrieval calls."""
    class _Q:
        prompt = "test prompt"
        learning_points = ()
        mode = "cheap"
        experience_level = "beginner"
    return _Q()


def _good_manifest(tmp_path: Path, *, model: str, dim: int) -> Path:
    root = tmp_path / "idx"
    root.mkdir()
    manifest = {
        "index_version": indexer.INDEX_VERSION,
        "embed_model": model,
        "embed_dim": dim,
        "row_count": 0,
        "corpus_hash": "x",
        "corpus_root": "x",
    }
    (root / indexer.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# Swap + restore semantics
# ---------------------------------------------------------------------------

def test_swap_on_enter_restore_on_exit(monkeypatch, tmp_path):
    sentinel = object()
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", sentinel)

    fake_model = object()
    root = _good_manifest(tmp_path, model="m", dim=4)

    with AB.ABRetriever(
        index_root=root, model=fake_model, model_id="m",
        embed_dim=4, top_k=5,
    ):
        # Inside context: swapped
        assert searcher._QUERY_EMBEDDER is fake_model

    # After exit: restored
    assert searcher._QUERY_EMBEDDER is sentinel


def test_restore_on_exception(monkeypatch, tmp_path):
    sentinel = object()
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", sentinel)

    fake_model = object()
    root = _good_manifest(tmp_path, model="m", dim=4)

    with pytest.raises(RuntimeError, match="boom"):
        with AB.ABRetriever(
            index_root=root, model=fake_model, model_id="m",
            embed_dim=4, top_k=5,
        ):
            raise RuntimeError("boom")

    # Even on exception, original embedder must be restored
    assert searcher._QUERY_EMBEDDER is sentinel


def test_use_outside_with_block_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", object())
    root = _good_manifest(tmp_path, model="m", dim=4)
    retriever = AB.ABRetriever(
        index_root=root, model=object(), model_id="m",
        embed_dim=4, top_k=5,
    )
    with pytest.raises(RuntimeError, match="outside its context"):
        retriever._retrieve(_fake_query())


def test_sequential_retrievers_dont_leak(monkeypatch, tmp_path):
    """Two ABRetriever contexts in sequence should each restore the
    pre-context embedder, not stack on top of each other."""
    original = object()
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", original)

    model_a = object()
    model_b = object()
    root = _good_manifest(tmp_path, model="m", dim=4)

    with AB.ABRetriever(
        index_root=root, model=model_a, model_id="m",
        embed_dim=4, top_k=5,
    ):
        assert searcher._QUERY_EMBEDDER is model_a
    assert searcher._QUERY_EMBEDDER is original

    with AB.ABRetriever(
        index_root=root, model=model_b, model_id="m",
        embed_dim=4, top_k=5,
    ):
        assert searcher._QUERY_EMBEDDER is model_b
    assert searcher._QUERY_EMBEDDER is original


# ---------------------------------------------------------------------------
# Manifest mismatch fail-fast
# ---------------------------------------------------------------------------

def test_manifest_mismatch_blocks_swap(monkeypatch, tmp_path):
    sentinel = object()
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", sentinel)

    root = _good_manifest(tmp_path, model="manifest-model", dim=4)

    # Try to bind a candidate that disagrees with the manifest
    with pytest.raises(IndexCompatibilityError, match="embed_model"):
        with AB.ABRetriever(
            index_root=root, model=object(), model_id="other-model",
            embed_dim=4, top_k=5,
        ):
            pass

    # Swap must NOT have happened
    assert searcher._QUERY_EMBEDDER is sentinel


def test_manifest_dim_mismatch_blocks_swap(monkeypatch, tmp_path):
    sentinel = object()
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", sentinel)

    root = _good_manifest(tmp_path, model="m", dim=384)

    with pytest.raises(IndexCompatibilityError, match="embedding_dim"):
        with AB.ABRetriever(
            index_root=root, model=object(), model_id="m",
            embed_dim=1024, top_k=5,
        ):
            pass

    assert searcher._QUERY_EMBEDDER is sentinel


# ---------------------------------------------------------------------------
# Retrieve plumbing
# ---------------------------------------------------------------------------

def test_retrieve_calls_searcher_with_correct_kwargs(monkeypatch, tmp_path):
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", None)
    root = _good_manifest(tmp_path, model="m", dim=4)

    captured: dict = {}

    def fake_search(prompt, *, learning_points, top_k, mode,
                     experience_level, index_root, **kwargs):
        captured.update(
            prompt=prompt,
            learning_points=learning_points,
            top_k=top_k,
            mode=mode,
            experience_level=experience_level,
            index_root=index_root,
        )
        return [{"path": "a.md"}, {"path": "b.md"}]

    monkeypatch.setattr(searcher, "search", fake_search)

    fake_model = object()
    with AB.ABRetriever(
        index_root=root, model=fake_model, model_id="m",
        embed_dim=4, top_k=7, mode="full",
    ) as retrieve:
        result = retrieve(_fake_query())

    assert result == ["a.md", "b.md"]
    assert captured["prompt"] == "test prompt"
    assert captured["top_k"] == 7
    assert captured["mode"] == "full"  # retriever mode wins, not query.mode
    assert captured["experience_level"] == "beginner"
    assert captured["index_root"] == root


def test_retrieve_extracts_path_field_only(monkeypatch, tmp_path):
    monkeypatch.setattr(searcher, "_QUERY_EMBEDDER", None)
    root = _good_manifest(tmp_path, model="m", dim=4)

    monkeypatch.setattr(
        searcher, "search",
        lambda *a, **kw: [
            {"path": "x.md", "score": 0.9, "title": "X"},
            {"path": "y.md", "score": 0.5, "title": "Y"},
        ],
    )

    with AB.ABRetriever(
        index_root=root, model=object(), model_id="m",
        embed_dim=4, top_k=5,
    ) as retrieve:
        assert retrieve(_fake_query()) == ["x.md", "y.md"]
