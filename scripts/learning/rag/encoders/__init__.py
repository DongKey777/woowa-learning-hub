"""Encoder abstraction for the bge-m3 풀-hybrid plan (v4 plan §H0).

Defines the single interface every downstream module talks to:
``EncoderProtocol`` returns ``ModalEncoding`` — dense + sparse + colbert
in one shape. ``indexer.py``, ``searcher.py``, ``incremental_indexer.py``,
and ``eval/index_builder.py`` all depend on this protocol so the actual
encoder implementation (``encoders.bge_m3.BgeM3Encoder``) is swappable
for testing or future model upgrades.

The protocol is intentionally narrow:
- Methods: ``encode_corpus(texts, ...) -> ModalEncoding`` and
  ``encode_query(text, ...) -> ModalEncoding``.
- Attributes: ``model_id``, ``model_version`` (HF revision SHA pin),
  ``dense_dim``, ``colbert_dim``, ``sparse_vocab_size``.

Test fakes live in ``tests/unit/_fakes.py:_FakeMultiModalEncoder``
and conform to this protocol via duck-typing — no inheritance needed.

Schema reference: plan §H0 (encoder interface), §H1 (manifest
encoder block).
"""

from __future__ import annotations

from typing import Iterable, Protocol, TypedDict, runtime_checkable

import numpy as np


__all__ = ["ModalEncoding", "EncoderProtocol"]


class ModalEncoding(TypedDict):
    """Output of ``EncoderProtocol.encode_corpus`` / ``encode_query``.

    All three modalities are aligned by row index. ``dense[i]``,
    ``sparse[i]``, and ``colbert[i]`` describe the same input text.

    Field shapes (for bge-m3, the canonical implementation):
    - ``dense``: ``(N, dense_dim)`` ``float32``, L2-normalised per row.
    - ``sparse``: per-doc ``{token_id: weight}`` dict. Typically 50–200
      non-zero tokens per doc for bge-m3 (vocab 250,002).
    - ``colbert``: per-doc ``(T_i, colbert_dim)`` array where ``T_i`` is
      the doc's token count after the tokenizer + truncation. dtype is
      ``float16`` for bge-m3 (storage efficiency); H0 capability probe
      verifies whether LanceDB / PyArrow handle ``float16`` round-trip
      end-to-end. If not, the encoder falls back to ``float32`` and
      records the choice in ``state/cs_rag/dep_probe.json``.

    Future modalities can be added by extending this TypedDict; the
    protocol's ``modalities`` parameter selects which are populated.
    """

    dense: np.ndarray
    sparse: list[dict[int, float]]
    colbert: list[np.ndarray]


@runtime_checkable
class EncoderProtocol(Protocol):
    """The contract every downstream module agrees on.

    Implementations:
    - ``encoders.bge_m3.BgeM3Encoder`` — production wrapper around
      ``FlagEmbedding.BGEM3FlagModel`` (single forward pass produces
      all three modalities).
    - ``tests.unit._fakes._FakeMultiModalEncoder`` — deterministic
      fake for unit tests, no torch/MPS/HF dependency.

    ``model_version`` is an HF revision SHA pin
    (``"BAAI/bge-m3@<commit-sha>"``). It threads through manifest +
    ``chunk_hashes_per_model.json`` so an upgrade triggers a full
    re-encode (per-model fingerprints become stale, all chunks marked
    "modified" by the orchestrator).
    """

    model_id: str
    model_version: str
    dense_dim: int
    colbert_dim: int
    sparse_vocab_size: int

    def encode_corpus(
        self,
        texts: Iterable[str],
        *,
        batch_size: int = 16,
        max_length: int = 8192,
        modalities: tuple[str, ...] = ("dense", "sparse", "colbert"),
        progress=None,
    ) -> ModalEncoding: ...

    def encode_query(
        self,
        text: str,
        *,
        modalities: tuple[str, ...] = ("dense", "sparse", "colbert"),
    ) -> ModalEncoding: ...
