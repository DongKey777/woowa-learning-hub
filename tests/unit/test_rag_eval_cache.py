"""Unit tests for scripts.learning.rag.eval.cache.

Coverage targets:
- Same (model_id, device) reuses one instance (idempotent get)
- Different model_id keeps instances separate (no contamination)
- Different device keeps instances separate
- clear() resets the cache and forces rebuild on next get
- has(), len(), keys() observability
- Empty model_id / device rejected
- Builder is called exactly once per unique key (cached)
- Fail-fast: model mismatch raises IndexCompatibilityError naming the field
- Fail-fast: dim mismatch
- Fail-fast: index_version mismatch
- Multiple mismatches all reported in one error message
- IndexCompatibilityError is a ValueError subclass (catch-compat)
"""

from __future__ import annotations

import pytest

from scripts.learning.rag.eval import cache as C


# ---------------------------------------------------------------------------
# EmbedderCache
# ---------------------------------------------------------------------------

class _FakeModel:
    """Stand-in for SentenceTransformer; tracks construction."""

    instances_built = 0

    def __init__(self, model_id: str, device: str):
        self.model_id = model_id
        self.device = device
        type(self).instances_built += 1


def _builder(model_id: str, device: str) -> _FakeModel:
    return _FakeModel(model_id, device)


def setup_function() -> None:
    _FakeModel.instances_built = 0


def test_same_key_returns_same_instance():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    a = cache.get("model-x", "mps")
    b = cache.get("model-x", "mps")
    assert a is b
    assert _FakeModel.instances_built == 1


def test_different_model_id_yields_different_instance():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    a = cache.get("model-A", "mps")
    b = cache.get("model-B", "mps")
    assert a is not b
    assert a.model_id == "model-A"
    assert b.model_id == "model-B"
    assert _FakeModel.instances_built == 2


def test_different_device_yields_different_instance():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    cpu = cache.get("model-x", "cpu")
    mps = cache.get("model-x", "mps")
    assert cpu is not mps
    assert cpu.device == "cpu"
    assert mps.device == "mps"


def test_clear_resets_cache_and_rebuilds_on_next_get():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    a = cache.get("m", "mps")
    cache.clear()
    assert len(cache) == 0
    b = cache.get("m", "mps")
    assert a is not b
    assert _FakeModel.instances_built == 2


def test_has_reflects_population():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    assert not cache.has("m", "mps")
    cache.get("m", "mps")
    assert cache.has("m", "mps")
    assert not cache.has("m", "cpu")


def test_keys_iterates_known_entries():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    cache.get("a", "cpu")
    cache.get("b", "mps")
    assert set(cache.keys()) == {("a", "cpu"), ("b", "mps")}


def test_len_tracks_unique_keys():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    cache.get("m", "mps")
    cache.get("m", "mps")  # idempotent
    cache.get("m", "cpu")
    assert len(cache) == 2


def test_empty_model_id_rejected():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    with pytest.raises(ValueError, match="model_id"):
        cache.get("", "mps")


def test_empty_device_rejected():
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    with pytest.raises(ValueError, match="device"):
        cache.get("m", "")


def test_builder_called_exactly_once_per_key():
    """Defends against subtle bugs where keys collide unintentionally
    (e.g. dict not hashable correctly) — the test fails immediately if
    the cache silently rebuilds."""
    cache: C.EmbedderCache[_FakeModel] = C.EmbedderCache(_builder)
    for _ in range(10):
        cache.get("m", "mps")
    assert _FakeModel.instances_built == 1


# ---------------------------------------------------------------------------
# assert_index_compat — fail-fast manifest gate
# ---------------------------------------------------------------------------

_GOOD = dict(
    manifest_embed_model="bge-m3",
    manifest_embed_dim=1024,
    manifest_index_version=3,
    runtime_embed_model="bge-m3",
    runtime_embed_dim=1024,
    runtime_index_version=3,
)


def test_assert_index_compat_passes_when_all_match():
    C.assert_index_compat(**_GOOD)


def test_assert_index_compat_raises_on_model_mismatch():
    bad = dict(_GOOD, runtime_embed_model="MiniLM-L12")
    with pytest.raises(C.IndexCompatibilityError, match="embed_model"):
        C.assert_index_compat(**bad)


def test_assert_index_compat_raises_on_dim_mismatch():
    bad = dict(_GOOD, runtime_embed_dim=384)
    with pytest.raises(C.IndexCompatibilityError, match="embedding_dim"):
        C.assert_index_compat(**bad)


def test_assert_index_compat_raises_on_index_version_mismatch():
    bad = dict(_GOOD, runtime_index_version=2)
    with pytest.raises(C.IndexCompatibilityError, match="index_version"):
        C.assert_index_compat(**bad)


def test_assert_index_compat_reports_all_mismatches_at_once():
    """All three fields disagree → error message names all three so the
    operator sees the full picture in one shot."""
    bad = dict(
        manifest_embed_model="bge-m3",
        manifest_embed_dim=1024,
        manifest_index_version=3,
        runtime_embed_model="MiniLM-L12",
        runtime_embed_dim=384,
        runtime_index_version=2,
    )
    with pytest.raises(C.IndexCompatibilityError) as exc_info:
        C.assert_index_compat(**bad)
    msg = str(exc_info.value)
    assert "embed_model" in msg
    assert "embedding_dim" in msg
    assert "index_version" in msg


def test_index_compatibility_error_is_value_error_subclass():
    """Existing code with ``except ValueError:`` still catches us."""
    assert issubclass(C.IndexCompatibilityError, ValueError)


def test_assert_index_compat_message_includes_actual_values():
    """Operator should be able to copy-paste the values from the
    error message — don't truncate."""
    bad = dict(_GOOD, runtime_embed_model="OTHER-MODEL")
    with pytest.raises(C.IndexCompatibilityError) as exc_info:
        C.assert_index_compat(**bad)
    msg = str(exc_info.value)
    assert "bge-m3" in msg  # manifest value
    assert "OTHER-MODEL" in msg  # runtime value
