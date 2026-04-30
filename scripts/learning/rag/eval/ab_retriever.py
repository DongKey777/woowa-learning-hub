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
from scripts.learning.rag.eval.cache import IndexCompatibilityError, assert_index_compat


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
        backend: str = "legacy",
        modalities: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        self.index_root = Path(index_root)
        self.model = model
        self.model_id = model_id
        self.embed_dim = embed_dim
        self.top_k = top_k
        self.mode = mode
        self.backend = backend
        self.modalities = tuple(modalities) if modalities is not None else None
        self._original_embedder: Any = None
        self._original_lance_encoder: Any = None
        self._lance_cache_key: str | None = None
        self._lance_cache_had_key = False
        self._entered = False

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> Callable[[Any], list[str]]:
        # 1. Manifest compat (fail-fast before binding the swap)
        if self.backend == "legacy":
            manifest = indexer.load_manifest(self.index_root)
            assert_index_compat(
                manifest_embed_model=manifest["embed_model"],
                manifest_embed_dim=int(manifest["embed_dim"]),
                manifest_index_version=int(manifest["index_version"]),
                runtime_embed_model=self.model_id,
                runtime_embed_dim=self.embed_dim,
                runtime_index_version=indexer.INDEX_VERSION,
            )

            # 2a. Swap the legacy module-level query embedder.
            self._original_embedder = searcher._QUERY_EMBEDDER
            searcher._QUERY_EMBEDDER = self.model
        elif self.backend == "lance":
            manifest = indexer.read_manifest_v3(self.index_root)
            encoder = manifest.get("encoder") or {}
            manifest_model = str(encoder.get("model_id") or "")
            if manifest_model != self.model_id:
                raise IndexCompatibilityError(
                    f"embed_model mismatch: manifest={manifest_model!r} "
                    f"runtime={self.model_id!r}"
                )

            # 2b. Bind the LanceDB modal query encoder cache to the candidate.
            # searcher._get_lance_query_encoder resolves this exact key from
            # the v3 manifest, so no production BGE-M3 load happens during
            # tests or scoped A/B runs.
            model_version = str(encoder.get("model_version") or manifest_model)
            cache_key = model_version or manifest_model
            self._lance_cache_key = cache_key
            self._lance_cache_had_key = cache_key in searcher._LANCE_QUERY_ENCODER_CACHE
            self._original_lance_encoder = searcher._LANCE_QUERY_ENCODER_CACHE.get(cache_key)
            searcher._LANCE_QUERY_ENCODER_CACHE[cache_key] = self.model
        else:
            raise ValueError(f"unknown backend: {self.backend}")
        self._entered = True
        return self._retrieve

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._entered:
            return
        # Always restore, even on exception.
        if self.backend == "legacy":
            searcher._QUERY_EMBEDDER = self._original_embedder
        elif self.backend == "lance" and self._lance_cache_key is not None:
            if self._lance_cache_had_key:
                searcher._LANCE_QUERY_ENCODER_CACHE[self._lance_cache_key] = (
                    self._original_lance_encoder
                )
            else:
                searcher._LANCE_QUERY_ENCODER_CACHE.pop(self._lance_cache_key, None)
        self._original_embedder = None
        self._original_lance_encoder = None
        self._lance_cache_key = None
        self._lance_cache_had_key = False
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
            backend=self.backend,
            modalities=self.modalities,
            experience_level=query.experience_level,
            index_root=self.index_root,
        )
        return [h["path"] for h in hits]
