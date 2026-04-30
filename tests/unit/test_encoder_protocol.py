"""Tests for the encoder protocol (v4 plan §H0).

Locks the contract so a future module can rely on:
- ``ModalEncoding`` is a TypedDict with exactly three keys
- ``EncoderProtocol`` is `runtime_checkable` (isinstance works for
  duck-typed implementations including the fake encoder used by
  every modal-aware unit test in H1+)

These tests load nothing heavy — no torch, no HF model. They only
verify the protocol shape so that breaking changes surface fast.
"""

from __future__ import annotations

import numpy as np

from scripts.learning.rag.encoders import EncoderProtocol, ModalEncoding


# ---------------------------------------------------------------------------
# ModalEncoding TypedDict
# ---------------------------------------------------------------------------

def test_modal_encoding_required_keys():
    """Locks the keys downstream modules read."""
    annotations = ModalEncoding.__annotations__
    assert set(annotations.keys()) == {"dense", "sparse", "colbert"}


def test_modal_encoding_constructable_from_dict():
    """A plain dict with the right keys + value types satisfies the
    TypedDict — this is how production code passes encodings around
    (no class instantiation overhead)."""
    enc: ModalEncoding = {
        "dense": np.zeros((2, 8), dtype=np.float32),
        "sparse": [{1: 0.5, 7: 0.2}, {2: 0.9}],
        "colbert": [np.zeros((4, 8), dtype=np.float16),
                    np.zeros((3, 8), dtype=np.float16)],
    }
    # No exception — TypedDict is a structural check at type-check
    # time, runtime treats it as a dict
    assert enc["dense"].shape == (2, 8)
    assert enc["sparse"][0][1] == 0.5
    assert enc["colbert"][1].shape == (3, 8)


# ---------------------------------------------------------------------------
# EncoderProtocol — runtime_checkable + duck-type compatibility
# ---------------------------------------------------------------------------

class _MinimalDuckEncoder:
    """Smallest possible class that satisfies EncoderProtocol via
    duck-typing. Used by the test below to verify isinstance works."""

    model_id = "duck/test"
    model_version = "duck/test@v0"
    dense_dim = 8
    colbert_dim = 8
    sparse_vocab_size = 100

    def encode_corpus(self, texts, *, batch_size=16, max_length=8192,
                      modalities=("dense", "sparse", "colbert"),
                      progress=None):
        n = len(list(texts))
        return ModalEncoding(
            dense=np.zeros((n, self.dense_dim), dtype=np.float32),
            sparse=[{} for _ in range(n)],
            colbert=[np.zeros((1, self.colbert_dim), dtype=np.float16)
                     for _ in range(n)],
        )

    def encode_query(self, text, *, modalities=("dense", "sparse", "colbert")):
        return self.encode_corpus([text], modalities=modalities)


def test_encoder_protocol_is_runtime_checkable():
    """A class that *structurally* matches the protocol must pass
    isinstance — this is what lets ``_FakeMultiModalEncoder`` slot
    into production code without inheritance."""
    enc = _MinimalDuckEncoder()
    assert isinstance(enc, EncoderProtocol)


def test_encoder_protocol_attribute_contract():
    """All five attributes are mandatory on any conforming encoder."""
    enc = _MinimalDuckEncoder()
    for attr in ("model_id", "model_version", "dense_dim",
                 "colbert_dim", "sparse_vocab_size"):
        assert hasattr(enc, attr), f"missing required attr: {attr}"


def test_encoder_protocol_methods_callable():
    enc = _MinimalDuckEncoder()
    out_corpus = enc.encode_corpus(["hello", "world"])
    assert out_corpus["dense"].shape == (2, 8)
    assert len(out_corpus["sparse"]) == 2
    assert len(out_corpus["colbert"]) == 2

    out_query = enc.encode_query("query")
    assert out_query["dense"].shape == (1, 8)
    assert len(out_query["sparse"]) == 1
    assert len(out_query["colbert"]) == 1


def test_encoder_protocol_default_modalities_includes_all_three():
    """Default value of the ``modalities`` parameter must select all
    three modalities — H1+ relies on this for legacy compatibility."""
    import inspect
    sig = inspect.signature(_MinimalDuckEncoder.encode_corpus)
    default = sig.parameters["modalities"].default
    assert set(default) == {"dense", "sparse", "colbert"}
