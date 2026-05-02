"""bge-m3 encoder wrapper for the v3 CS RAG index.

This module is intentionally lazy: importing it must not load torch,
transformers, or the HuggingFace model.  The heavy dependency is imported
only when ``BgeM3Encoder`` encodes text.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from . import ModalEncoding


DEFAULT_MODEL_ID = "BAAI/bge-m3"
DEFAULT_DENSE_DIM = 1024
DEFAULT_COLBERT_DIM = 1024
DEFAULT_SPARSE_VOCAB_SIZE = 250_002


class EncoderDependencyMissing(RuntimeError):
    """Raised when the optional bge-m3 runtime dependency is unavailable."""


def _hf_cache_model_ref(model_id: str) -> str | None:
    """Return the cached HuggingFace ref SHA when available.

    This avoids importing ``huggingface_hub`` just to build a deterministic
    model version string.  If the cache is absent, callers still get a stable
    ``model_id@unknown`` version and the real model loader can decide whether
    to download.
    """
    cache_name = "models--" + model_id.replace("/", "--")
    ref_path = Path.home() / ".cache" / "huggingface" / "hub" / cache_name / "refs" / "main"
    try:
        ref = ref_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return ref or None


def _coerce_sparse_weights(raw_weights) -> dict[int, float]:
    """Normalize FlagEmbedding lexical weights to ``{token_id: weight}``.

    ``FlagEmbedding`` currently returns string token ids.  The downstream
    sparse rescore path is cheaper and less error-prone with integer keys, so
    this wrapper locks the internal contract to ``int``.
    """
    out: dict[int, float] = {}
    for key, value in dict(raw_weights).items():
        try:
            token_id = int(key)
        except (TypeError, ValueError):
            # Keep the representation deterministic even if a future
            # FlagEmbedding release returns token strings instead of ids.
            token_id = abs(hash(str(key))) % DEFAULT_SPARSE_VOCAB_SIZE
        out[token_id] = float(value)
    return out


@dataclass
class BgeM3Encoder:
    """Thin production wrapper around ``FlagEmbedding.BGEM3FlagModel``."""

    model_id: str = DEFAULT_MODEL_ID
    devices: str | list[str] | None = None
    cache_dir: str | None = None
    use_fp16: bool = False
    dense_dim: int = DEFAULT_DENSE_DIM
    colbert_dim: int = DEFAULT_COLBERT_DIM
    sparse_vocab_size: int = DEFAULT_SPARSE_VOCAB_SIZE
    colbert_storage_dtype: str = "float16"
    query_instruction_for_retrieval: str | None = None
    max_length: int = 8192
    batch_size: int = 16

    def __post_init__(self) -> None:
        ref = _hf_cache_model_ref(self.model_id)
        self.model_version = f"{self.model_id}@{ref or 'unknown'}"
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from FlagEmbedding import BGEM3FlagModel  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on optional dep
            raise EncoderDependencyMissing(
                "FlagEmbedding is not installed. Run `.venv/bin/python -m pip install FlagEmbedding`."
            ) from exc

        self._model = BGEM3FlagModel(
            self.model_id,
            normalize_embeddings=True,
            use_fp16=self.use_fp16,
            devices=self.devices,
            cache_dir=self.cache_dir,
            query_instruction_for_retrieval=self.query_instruction_for_retrieval,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=True,
            passage_max_length=self.max_length,
            query_max_length=self.max_length,
        )
        return self._model

    def encode_corpus(
        self,
        texts: Iterable[str],
        *,
        batch_size: int | None = None,
        max_length: int | None = None,
        modalities: tuple[str, ...] = ("dense", "sparse", "colbert"),
        progress=None,
    ) -> ModalEncoding:
        text_list = list(texts)
        total = len(text_list)
        want_dense = "dense" in modalities
        want_sparse = "sparse" in modalities
        want_colbert = "colbert" in modalities
        effective_batch_size = batch_size or self.batch_size

        if total == 0:
            return {
                "dense": np.zeros((0, self.dense_dim), dtype=np.float32),
                "sparse": [],
                "colbert": [],
            }
        if not want_dense and not want_sparse and not want_colbert:
            return {
                "dense": np.zeros((total, self.dense_dim), dtype=np.float32),
                "sparse": [{} for _ in range(total)],
                "colbert": [
                    np.zeros((0, self.colbert_dim), dtype=np.float16)
                    for _ in range(total)
                ],
            }

        model = self._load_model()
        dense_parts: list[np.ndarray] = []
        sparse_parts: list[dict[int, float]] = []
        colbert_parts: list[np.ndarray] = []
        start = time.time()

        for offset in range(0, total, effective_batch_size):
            batch = text_list[offset : offset + effective_batch_size]
            raw = model.encode(
                batch,
                batch_size=effective_batch_size,
                max_length=max_length or self.max_length,
                return_dense=want_dense,
                return_sparse=want_sparse,
                return_colbert_vecs=want_colbert,
            )

            if want_dense:
                dense = np.asarray(raw.get("dense_vecs"), dtype=np.float32)
                if dense.ndim == 1:
                    dense = dense.reshape(1, -1)
                dense_parts.append(dense)

            if want_sparse:
                sparse_parts.extend(
                    _coerce_sparse_weights(weights)
                    for weights in raw.get("lexical_weights", [])
                )

            if want_colbert:
                colbert_dtype = np.float16 if self.colbert_storage_dtype == "float16" else np.float32
                colbert_parts.extend(
                    np.asarray(vecs, dtype=colbert_dtype)
                    for vecs in raw.get("colbert_vecs", [])
                )

            done = min(offset + len(batch), total)
            if progress is not None:
                elapsed = time.time() - start
                rate = (done / elapsed) if elapsed > 0 else 0.0
                eta = ((total - done) / rate) if rate > 0 else 0.0
                try:
                    progress(
                        "encode_progress",
                        {
                            "done": done,
                            "total": total,
                            "elapsed_s": round(elapsed, 1),
                            "eta_s": round(eta, 1),
                            "rate_per_s": round(rate, 2),
                        },
                    )
                except Exception:
                    pass

        dense_out = (
            np.concatenate(dense_parts, axis=0)
            if want_dense and dense_parts
            else np.zeros((total, self.dense_dim), dtype=np.float32)
        )
        sparse_out = sparse_parts if want_sparse else [{} for _ in range(total)]
        colbert_out = (
            colbert_parts
            if want_colbert
            else [np.zeros((0, self.colbert_dim), dtype=np.float16) for _ in range(total)]
        )
        return {"dense": dense_out, "sparse": sparse_out, "colbert": colbert_out}

    def encode_corpus_streaming(
        self,
        texts: Iterable[str],
        *,
        batch_size: int | None = None,
        max_length: int | None = None,
        modalities: tuple[str, ...] = ("dense", "sparse", "colbert"),
        progress=None,
    ):
        """Stream a corpus in fixed-size batches without ever materialising
        the full encoding in memory.

        Unlike ``encode_corpus`` (which keeps every chunk's output in
        ``dense_parts`` / ``sparse_parts`` / ``colbert_parts`` Python lists
        and returns one combined ``ModalEncoding``), this method yields one
        ``(start, stop, ModalEncoding)`` triple per batch. The caller is
        expected to consume the triple and free it before the next yield.

        Memory: O(batch_size) instead of O(corpus_size). For 27 K chunks
        with 384-token ColBERT vectors at fp16, the AS-IS encode_corpus
        accumulates ~21 GB; this streaming variant peaks at ~100 MB per
        batch (batch_size=128) — over 200× lower.

        Yields:
            (start, stop, ModalEncoding) where ``ModalEncoding`` is the
            same shape ``encode_corpus`` returns but for ``[start:stop]``
            of the input texts only.
        """
        text_list = list(texts)
        total = len(text_list)
        want_dense = "dense" in modalities
        want_sparse = "sparse" in modalities
        want_colbert = "colbert" in modalities
        effective_batch_size = batch_size or self.batch_size

        if total == 0:
            return

        if not want_dense and not want_sparse and not want_colbert:
            # Nothing requested — emit zero-shape batches to keep the
            # contract uniform with encode_corpus's empty-modality path.
            for offset in range(0, total, effective_batch_size):
                stop = min(offset + effective_batch_size, total)
                size = stop - offset
                yield offset, stop, {
                    "dense": np.zeros((size, self.dense_dim), dtype=np.float32),
                    "sparse": [{} for _ in range(size)],
                    "colbert": [
                        np.zeros((0, self.colbert_dim), dtype=np.float16)
                        for _ in range(size)
                    ],
                }
            return

        model = self._load_model()
        start_time = time.time()
        for offset in range(0, total, effective_batch_size):
            stop = min(offset + effective_batch_size, total)
            batch = text_list[offset:stop]
            raw = model.encode(
                batch,
                batch_size=effective_batch_size,
                max_length=max_length or self.max_length,
                return_dense=want_dense,
                return_sparse=want_sparse,
                return_colbert_vecs=want_colbert,
            )

            if want_dense:
                dense = np.asarray(raw.get("dense_vecs"), dtype=np.float32)
                if dense.ndim == 1:
                    dense = dense.reshape(1, -1)
            else:
                dense = np.zeros((len(batch), self.dense_dim), dtype=np.float32)

            if want_sparse:
                sparse_list = [
                    _coerce_sparse_weights(weights)
                    for weights in raw.get("lexical_weights", [])
                ]
            else:
                sparse_list = [{} for _ in range(len(batch))]

            if want_colbert:
                colbert_dtype = (
                    np.float16 if self.colbert_storage_dtype == "float16" else np.float32
                )
                colbert_list = [
                    np.asarray(vecs, dtype=colbert_dtype)
                    for vecs in raw.get("colbert_vecs", [])
                ]
            else:
                colbert_list = [
                    np.zeros((0, self.colbert_dim), dtype=np.float16)
                    for _ in range(len(batch))
                ]

            if progress is not None:
                elapsed = time.time() - start_time
                rate = (stop / elapsed) if elapsed > 0 else 0.0
                eta = ((total - stop) / rate) if rate > 0 else 0.0
                try:
                    progress(
                        "encode_progress",
                        {
                            "done": stop,
                            "total": total,
                            "elapsed_s": round(elapsed, 1),
                            "eta_s": round(eta, 1),
                            "rate_per_s": round(rate, 2),
                        },
                    )
                except Exception:
                    pass

            yield offset, stop, {
                "dense": dense,
                "sparse": sparse_list,
                "colbert": colbert_list,
            }
            # Caller is expected to drop its reference to the yielded
            # ModalEncoding before requesting the next one. Local
            # references die when the loop iterates.
            del dense, sparse_list, colbert_list, raw

    def encode_query(
        self,
        text: str,
        *,
        modalities: tuple[str, ...] = ("dense", "sparse", "colbert"),
    ) -> ModalEncoding:
        return self.encode_corpus([text], batch_size=1, modalities=modalities)
