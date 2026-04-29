"""Model+device keyed embedder cache + fail-fast manifest compatibility check.

Plan §P1.1 step 5 — two failure modes the existing module-level
``_QUERY_EMBEDDER`` (searcher.py:200-210) does NOT prevent:

1. **Cross-model contamination during A/B**: a single cached instance
   means evaluating ``model_A`` then ``model_B`` in the same process
   silently reuses ``model_A`` for ``model_B``'s queries. Detected
   today only by suspicious metric output.

2. **Index/embedder mismatch**: a query embedder vectorising with
   different model/dim/INDEX_VERSION than the on-disk index produces
   garbage similarities, but no error is raised — corrupted scores
   look like "the model just got worse".

This module provides:

- :class:`EmbedderCache` — dict[(model_id, device), instance] keyed
  cache with dependency-injected builder (so tests don't have to load
  real ML models).
- :func:`assert_index_compat` — boundary check that explodes loudly
  when manifest fields don't match runtime fields, naming exactly
  which field disagrees.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class EmbedderCache(Generic[T]):
    """Cache keyed by (model_id, device) so A/B runs cannot collide.

    The builder is injected so this module has no hard dependency on
    sentence-transformers (and tests can pass a fake). For production
    use, see :func:`default_embedder_builder` below.
    """

    def __init__(self, builder: Callable[[str, str], T]) -> None:
        self._builder = builder
        self._cache: dict[tuple[str, str], T] = {}

    def get(self, model_id: str, device: str) -> T:
        """Return the cached instance for (model_id, device); build on miss."""
        if not model_id:
            raise ValueError("model_id must be non-empty")
        if not device:
            raise ValueError("device must be non-empty")
        key = (model_id, device)
        if key not in self._cache:
            self._cache[key] = self._builder(model_id, device)
        return self._cache[key]

    def has(self, model_id: str, device: str) -> bool:
        return (model_id, device) in self._cache

    def clear(self) -> None:
        """Drop all cached instances. Useful when memory pressure climbs
        during multi-model A/B sweeps."""
        self._cache.clear()

    def keys(self) -> Iterator[tuple[str, str]]:
        return iter(self._cache.keys())

    def __len__(self) -> int:
        return len(self._cache)


# ---------------------------------------------------------------------------
# Fail-fast manifest/runtime compatibility gate
# ---------------------------------------------------------------------------

class IndexCompatibilityError(ValueError):
    """Raised when on-disk index and runtime embedder disagree.

    Subclass of ValueError so existing ``except ValueError:`` blocks
    still catch it, but tests can assert on the specific type.
    """


def assert_index_compat(
    *,
    manifest_embed_model: str,
    manifest_embed_dim: int,
    manifest_index_version: int,
    runtime_embed_model: str,
    runtime_embed_dim: int,
    runtime_index_version: int,
) -> None:
    """Compare the index manifest's identity against the runtime embedder.

    Raises IndexCompatibilityError listing every mismatched field. All
    three fields are checked even when the first one fails so the
    error message is maximally informative for debugging.

    Plan §P1.1 step 5 — silent corruption is the headline risk this
    function exists to prevent.
    """
    mismatches: list[str] = []
    if manifest_embed_model != runtime_embed_model:
        mismatches.append(
            f"embed_model: manifest={manifest_embed_model!r} "
            f"runtime={runtime_embed_model!r}"
        )
    if manifest_embed_dim != runtime_embed_dim:
        mismatches.append(
            f"embedding_dim: manifest={manifest_embed_dim} "
            f"runtime={runtime_embed_dim}"
        )
    if manifest_index_version != runtime_index_version:
        mismatches.append(
            f"index_version: manifest={manifest_index_version} "
            f"runtime={runtime_index_version}"
        )
    if mismatches:
        raise IndexCompatibilityError(
            "index/runtime mismatch — " + " | ".join(mismatches)
        )


# ---------------------------------------------------------------------------
# Default builder (production wiring)
# ---------------------------------------------------------------------------

def default_embedder_builder(model_id: str, device: str) -> Any:
    """Production builder for SentenceTransformer instances.

    Lazy imports sentence_transformers so test environments without
    the heavy dep can still import this module.
    """
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer(model_id, device=device)
