"""Tests for encode-progress visibility (`_encode_all` callback contract).

Earlier sweeps were running blind — `model.encode(...)` was a single
opaque call with `show_progress_bar=False`, so a 4-hour CPU encode
produced no intermediate output. This test locks the new contract:

1. ``_encode_all`` slices texts into ``progress_chunk`` batches.
2. Between batches, it emits ``progress("encode_progress", info)``.
3. ``info`` carries ``done`` / ``total`` / ``elapsed_s`` / ``eta_s`` /
   ``rate_per_s``.
4. Output is bit-equivalent to the pre-progress single-call encode
   (concatenation preserves order).
"""

from __future__ import annotations

import numpy as np
import pytest

from scripts.learning.rag import indexer


class _FakeEncoder:
    """SentenceTransformer-shaped stub. Each call records the text
    list it received so we can verify slice ordering."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.calls: list[list[str]] = []

    def encode(self, texts, *, batch_size, show_progress_bar,
               normalize_embeddings, convert_to_numpy):
        self.calls.append(list(texts))
        # Embed each text as a deterministic vector based on its index
        # (text is `f"text-{idx}"` from the fixtures below)
        n = len(texts)
        out = np.zeros((n, self.dim), dtype="float32")
        for i, t in enumerate(texts):
            # Map "text-42" → 42 so we can verify order preservation
            try:
                idx = int(t.split("-")[-1])
            except ValueError:
                idx = i
            out[i, 0] = float(idx)
        return out


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

def test_encode_empty_returns_zero_shape_and_emits_no_progress():
    enc = _FakeEncoder()
    calls: list[tuple[str, dict]] = []
    out = indexer._encode_all(enc, [], progress=lambda s, i: calls.append((s, i)))
    assert out.shape == (0, indexer.EMBED_DIM)
    assert calls == []
    assert enc.calls == []


# ---------------------------------------------------------------------------
# Slicing + ordering
# ---------------------------------------------------------------------------

def test_encode_preserves_input_order():
    enc = _FakeEncoder()
    texts = [f"text-{i}" for i in range(7)]
    out = indexer._encode_all(enc, texts, progress_chunk=3)
    # Verify out[i, 0] == i (the encoder embedded index into channel 0)
    for i in range(7):
        assert out[i, 0] == float(i), f"row {i} out of order"


def test_encode_calls_model_in_chunks_of_progress_chunk():
    enc = _FakeEncoder()
    texts = [f"text-{i}" for i in range(7)]
    indexer._encode_all(enc, texts, progress_chunk=3)
    # 7 texts with chunk=3 → 3 calls (3, 3, 1)
    assert len(enc.calls) == 3
    assert [len(c) for c in enc.calls] == [3, 3, 1]


def test_encode_passes_through_batch_size():
    """The internal batch_size argument the wrapper passes to
    model.encode must reach the encoder."""
    class _BatchSpy(_FakeEncoder):
        def __init__(self):
            super().__init__()
            self.batch_sizes: list[int] = []

        def encode(self, texts, *, batch_size, **kwargs):  # type: ignore[override]
            self.batch_sizes.append(batch_size)
            return super().encode(texts, batch_size=batch_size, **kwargs)

    enc = _BatchSpy()
    indexer._encode_all(enc, [f"text-{i}" for i in range(5)],
                        progress_chunk=2, encode_batch_size=8)
    assert all(b == 8 for b in enc.batch_sizes)


# ---------------------------------------------------------------------------
# Progress callback contract
# ---------------------------------------------------------------------------

def test_progress_callback_fires_per_chunk():
    enc = _FakeEncoder()
    calls: list[tuple[str, dict]] = []
    texts = [f"text-{i}" for i in range(7)]
    indexer._encode_all(
        enc, texts,
        progress=lambda s, info: calls.append((s, info)),
        progress_chunk=3,
    )
    # 3 chunks → 3 progress callbacks
    assert len(calls) == 3
    assert all(s == "encode_progress" for s, _ in calls)


def test_progress_info_shape():
    enc = _FakeEncoder()
    calls: list[tuple[str, dict]] = []
    texts = [f"text-{i}" for i in range(10)]
    indexer._encode_all(
        enc, texts,
        progress=lambda s, info: calls.append((s, info)),
        progress_chunk=4,
    )
    last_info = calls[-1][1]
    assert last_info["done"] == 10
    assert last_info["total"] == 10
    assert "elapsed_s" in last_info
    assert "eta_s" in last_info
    assert "rate_per_s" in last_info


def test_progress_done_is_monotonic_and_caps_at_total():
    enc = _FakeEncoder()
    calls: list[tuple[str, dict]] = []
    texts = [f"text-{i}" for i in range(11)]
    indexer._encode_all(
        enc, texts,
        progress=lambda s, info: calls.append((s, info)),
        progress_chunk=4,
    )
    dones = [info["done"] for _, info in calls]
    assert dones == sorted(dones), "done counter must be monotonic"
    assert dones[-1] == 11, "final done must equal total"
    assert all(d <= 11 for d in dones), "done must never exceed total"


def test_progress_callback_exception_does_not_break_encode():
    """Bad progress callbacks must never abort the encode."""
    enc = _FakeEncoder()
    def buggy(stage, info):
        raise RuntimeError("buggy callback")

    out = indexer._encode_all(
        enc,
        [f"text-{i}" for i in range(5)],
        progress=buggy,
        progress_chunk=2,
    )
    assert out.shape == (5, indexer.EMBED_DIM)


def test_no_progress_callback_still_works():
    """progress=None should still produce correct output."""
    enc = _FakeEncoder()
    out = indexer._encode_all(
        enc, [f"text-{i}" for i in range(5)], progress_chunk=2,
    )
    assert out.shape == (5, indexer.EMBED_DIM)


# ---------------------------------------------------------------------------
# Output equivalence with the pre-progress code path
# ---------------------------------------------------------------------------

def test_concat_output_matches_single_encode_call():
    """Output of progressive encode must equal the output of a
    single model.encode call on the full texts list (so behavior on
    the wire is unchanged — only progress reporting was added)."""
    enc = _FakeEncoder()
    texts = [f"text-{i}" for i in range(13)]
    progressive = indexer._encode_all(enc, texts, progress_chunk=4)

    enc2 = _FakeEncoder()
    single = enc2.encode(
        texts, batch_size=32, show_progress_bar=False,
        normalize_embeddings=True, convert_to_numpy=True,
    ).astype("float32")
    np.testing.assert_array_equal(progressive, single)


def test_dtype_is_float32():
    """Manifest + dense.npz both expect float32 — must not regress."""
    enc = _FakeEncoder()
    out = indexer._encode_all(enc, [f"text-{i}" for i in range(5)])
    assert out.dtype == np.float32
