"""Scoped reranker swap — bind a candidate cross-encoder for the
duration of a with-block.

Plan §P3.1 — production reranker.py / RERANK_MODEL must stay
untouched (P8 cutover only). The challenge mirrors P2's ABRetriever:
``reranker._model`` is a module-level lazy cache bound to production
RERANK_MODEL. To run A/B without modifying reranker.py we use a
scoped context manager that:

1. Builds the candidate model via an injected factory (or accepts a
   pre-loaded model for tests).
2. Swaps ``reranker._model`` AND ``reranker.RERANK_MODEL`` to the
   candidate for the duration of the context.
3. Restores both on exit, even on exception.

The RERANK_MODEL string swap matters for downstream manifest
recording: searcher.search() doesn't read it directly, but
ab_sweep's run report stores ``reranker_model`` in the manifest, and
the most reliable source of that field is whatever value is live at
measure time.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Callable


class RerankerSwap(AbstractContextManager):
    """Bind a candidate reranker model for the duration of a with-block.

    Args:
        model_id: HF model id (e.g. ``"BAAI/bge-reranker-v2-m3"``).
            Recorded into reranker.RERANK_MODEL during the context so
            downstream manifest writers see the right value.
        model: optional pre-loaded model instance (anything with
            ``.predict([(q, p), ...])``). Tests can pass a fake.
        model_factory: callable(model_id) -> instance. Production
            uses default_cross_encoder_factory below; tests can pass
            a fake factory.

    Exactly one of ``model`` or ``model_factory`` must be provided.
    """

    def __init__(
        self,
        *,
        model_id: str,
        model: Any | None = None,
        model_factory: Callable[[str], Any] | None = None,
    ) -> None:
        if model is None and model_factory is None:
            raise ValueError(
                "RerankerSwap: either model or model_factory must be provided"
            )
        if model is not None and model_factory is not None:
            raise ValueError(
                "RerankerSwap: pass model OR model_factory, not both"
            )
        self.model_id = model_id
        self._provided_model = model
        self._model_factory = model_factory
        self._original_model: Any = None
        self._original_model_id: str | None = None
        self._entered = False

    def __enter__(self) -> Any:
        from scripts.learning.rag import reranker

        # Build (or use provided) candidate
        if self._provided_model is not None:
            candidate = self._provided_model
        else:
            assert self._model_factory is not None
            candidate = self._model_factory(self.model_id)

        # Capture originals for restore
        self._original_model = reranker._model
        self._original_model_id = reranker.RERANK_MODEL

        # Swap
        reranker._model = candidate
        reranker.RERANK_MODEL = self.model_id
        self._entered = True
        return candidate

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._entered:
            return None
        from scripts.learning.rag import reranker

        reranker._model = self._original_model
        if self._original_model_id is not None:
            reranker.RERANK_MODEL = self._original_model_id
        self._original_model = None
        self._original_model_id = None
        self._entered = False
        # Propagate exception
        return None


def default_cross_encoder_factory(device: str = "cpu") -> Callable[[str], Any]:
    """Production factory: lazy-imports CrossEncoder and binds device."""

    def _factory(model_id: str):
        from sentence_transformers import CrossEncoder  # type: ignore

        return CrossEncoder(model_id, device=device)

    return _factory
