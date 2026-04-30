"""Unit tests for scripts.learning.rag.eval.reranker_swap.

Coverage targets:
- Swap on enter, restore on exit (model + RERANK_MODEL string)
- Restore even when exception fires inside the context
- Sequential RerankerSwap contexts don't leak state
- Mutually exclusive: must pass model OR model_factory, not both/neither
- Pre-loaded model bypasses factory
- Factory called with model_id when no pre-loaded model
"""

from __future__ import annotations

import pytest

from scripts.learning.rag import reranker
from scripts.learning.rag.eval.reranker_swap import RerankerSwap


@pytest.fixture(autouse=True)
def _restore_reranker_globals():
    """Snapshot + restore the module-level globals so a failing test
    can't leak state into the next test."""
    original_model = reranker._model
    original_id = reranker.RERANK_MODEL
    yield
    reranker._model = original_model
    reranker.RERANK_MODEL = original_id


# ---------------------------------------------------------------------------
# Swap + restore semantics
# ---------------------------------------------------------------------------

def test_swap_replaces_model_on_enter():
    sentinel = object()
    fake_model = object()

    reranker._model = sentinel
    reranker.RERANK_MODEL = "old-model-id"

    with RerankerSwap(model_id="new-model-id", model=fake_model):
        assert reranker._model is fake_model
        assert reranker.RERANK_MODEL == "new-model-id"


def test_swap_restores_on_exit():
    sentinel = object()
    fake_model = object()

    reranker._model = sentinel
    reranker.RERANK_MODEL = "production-rerank"

    with RerankerSwap(model_id="candidate", model=fake_model):
        pass  # just enter and exit

    assert reranker._model is sentinel
    assert reranker.RERANK_MODEL == "production-rerank"


def test_swap_restores_on_exception():
    sentinel = object()
    fake_model = object()

    reranker._model = sentinel
    reranker.RERANK_MODEL = "production-rerank"

    with pytest.raises(RuntimeError, match="boom"):
        with RerankerSwap(model_id="candidate", model=fake_model):
            raise RuntimeError("boom")

    assert reranker._model is sentinel
    assert reranker.RERANK_MODEL == "production-rerank"


def test_sequential_swaps_dont_leak():
    sentinel = object()
    model_a = object()
    model_b = object()

    reranker._model = sentinel
    reranker.RERANK_MODEL = "production"

    with RerankerSwap(model_id="A", model=model_a):
        assert reranker._model is model_a
        assert reranker.RERANK_MODEL == "A"
    assert reranker._model is sentinel
    assert reranker.RERANK_MODEL == "production"

    with RerankerSwap(model_id="B", model=model_b):
        assert reranker._model is model_b
        assert reranker.RERANK_MODEL == "B"
    assert reranker._model is sentinel
    assert reranker.RERANK_MODEL == "production"


def test_factory_called_with_model_id():
    sentinel = object()
    reranker._model = sentinel

    captured: dict = {}

    def factory(model_id):
        captured["model_id"] = model_id
        return object()

    with RerankerSwap(model_id="org/test-model", model_factory=factory) as m:
        assert captured["model_id"] == "org/test-model"
        assert reranker._model is m


def test_must_provide_model_or_factory():
    with pytest.raises(ValueError, match="model or model_factory"):
        RerankerSwap(model_id="x")


def test_cannot_provide_both_model_and_factory():
    with pytest.raises(ValueError, match="model OR model_factory"):
        RerankerSwap(model_id="x", model=object(), model_factory=lambda _id: object())


def test_returns_candidate_from_enter():
    sentinel = object()
    candidate = object()
    reranker._model = sentinel

    with RerankerSwap(model_id="x", model=candidate) as returned:
        assert returned is candidate
