"""A/B retriever — query an eval index built by index_builder.

Plan §P2.1 — production searcher.py / EMBED_MODEL must stay
untouched. The challenge: ``searcher.search()`` reads
``searcher._QUERY_EMBEDDER`` (a module-level cache) which is bound to
production EMBED_MODEL. To run A/B without modifying searcher we use
a scoped context manager that:

1. Asserts the eval index's manifest matches the candidate model
   (via eval.cache.assert_index_compat — same fail-fast contract as
   production).
2. Swaps ``searcher._QUERY_EMBEDDER`` to the candidate's encoder for
   the duration of the context.
3. Restores the original value on exit, even if an exception fires.

Usage::

    with ABRetriever(index_root=..., model=..., model_id="...", embed_dim=...) as retrieve:
        per_query, regs, timings = evaluate_queries(queries, retrieve, top_k=10)

The swap is intentionally narrow-scope (one with-block per candidate
in an A/B sweep). Concurrent retrievers in the same process are NOT
supported — the module global is shared.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Callable

from scripts.learning.rag import indexer, searcher
from scripts.learning.rag.eval.cache import assert_index_compat


class ABRetriever(AbstractContextManager):
    """Bind a candidate (model, index_root) and yield a retrieve_fn.

    Args:
        index_root: directory built by build_eval_index. Must contain
            manifest.json with matching embed_model/embed_dim.
        model: an encoder instance with ``.encode(...)`` matching
            SentenceTransformer semantics. Tests can pass a fake.
        model_id: the HF id this candidate is registered under;
            cross-checked against the manifest.
        embed_dim: declared dim; cross-checked against manifest.
        top_k: forwarded to searcher.search.
        mode: "cheap" | "full". Defaults to "full".

    Returns (via __enter__): a callable
    ``(GradedQuery) -> list[str]`` suitable for
    ``runner.evaluate_queries``.
    """

    def __init__(
        self,
        *,
        index_root: Path | str,
        model: Any,
        model_id: str,
        embed_dim: int,
        top_k: int = 10,
        mode: str = "full",
    ) -> None:
        self.index_root = Path(index_root)
        self.model = model
        self.model_id = model_id
        self.embed_dim = embed_dim
        self.top_k = top_k
        self.mode = mode
        self._original_embedder: Any = None
        self._entered = False

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> Callable[[Any], list[str]]:
        # 1. Manifest compat (fail-fast before binding the swap)
        manifest = indexer.load_manifest(self.index_root)
        assert_index_compat(
            manifest_embed_model=manifest["embed_model"],
            manifest_embed_dim=int(manifest["embed_dim"]),
            manifest_index_version=int(manifest["index_version"]),
            runtime_embed_model=self.model_id,
            runtime_embed_dim=self.embed_dim,
            runtime_index_version=indexer.INDEX_VERSION,
        )

        # 2. Swap the module-level query embedder
        self._original_embedder = searcher._QUERY_EMBEDDER
        searcher._QUERY_EMBEDDER = self.model
        self._entered = True
        return self._retrieve

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._entered:
            return
        # Always restore, even on exception
        searcher._QUERY_EMBEDDER = self._original_embedder
        self._original_embedder = None
        self._entered = False
        # Do not swallow — propagate exceptions
        return None

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def _retrieve(self, query: Any) -> list[str]:
        """Run searcher.search bound to this A/B index + embedder.

        ``query`` is a GradedQuery (duck-typed — only .prompt,
        .learning_points, .mode, .experience_level are read).
        """
        if not self._entered:
            raise RuntimeError(
                "ABRetriever used outside its context manager scope"
            )
        # GradedQuery.mode may differ from self.mode (the eval mode);
        # honour the retriever-level configuration so an A/B sweep
        # measures all candidates uniformly.
        hits = searcher.search(
            query.prompt,
            learning_points=list(query.learning_points),
            top_k=self.top_k,
            mode=self.mode,
            experience_level=query.experience_level,
            index_root=self.index_root,
        )
        return [h["path"] for h in hits]
