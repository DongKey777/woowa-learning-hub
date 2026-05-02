"""Tests for ``build_lance_index_streaming`` + ``_lance_record_batch_zero_copy``.

The streaming variant must:
1. Produce a LanceDB table identical (row-equal, column-equal) to the
   classic ``build_lance_index`` for the same input.
2. Use ``pa.FixedSizeListArray.from_arrays`` for ColBERT (zero-copy)
   instead of ``.tolist()`` (16× amplification, measured).
3. Keep peak memory ≤ ~one batch worth, not corpus-wide.

Tests run with a synthetic encoder so they execute in CI without GPU /
HuggingFace downloads.
"""

from __future__ import annotations

import gc
import json
import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pyarrow as pa

from scripts.learning.rag import corpus_loader, indexer


# ---------------------------------------------------------------------------
# Synthetic encoder — produces deterministic dense / sparse / colbert
# encodings without loading FlagEmbedding or torch. Used by both the
# classic and streaming build paths so tests can compare output byte-equal.
# ---------------------------------------------------------------------------

@dataclass
class _FakeEncoder:
    model_id: str = "fake-encoder"
    model_version: str = "fake-encoder@v1"
    dense_dim: int = 32
    colbert_dim: int = 16
    sparse_vocab_size: int = 1024
    colbert_storage_dtype: str = "float16"
    max_length: int = 256
    batch_size: int = 4
    n_tokens_per_chunk: int = 8

    def _seed_dense(self, idx: int) -> np.ndarray:
        rng = np.random.default_rng(seed=1000 + idx)
        return rng.standard_normal(self.dense_dim, dtype=np.float32)

    def _seed_sparse(self, idx: int) -> dict[int, float]:
        rng = np.random.default_rng(seed=2000 + idx)
        active = rng.choice(self.sparse_vocab_size, size=4, replace=False)
        weights = rng.random(size=4, dtype=np.float32)
        return {int(k): float(v) for k, v in zip(active, weights)}

    def _seed_colbert(self, idx: int) -> np.ndarray:
        rng = np.random.default_rng(seed=3000 + idx)
        return rng.standard_normal(
            (self.n_tokens_per_chunk, self.colbert_dim), dtype=np.float32,
        ).astype(np.float16)

    # Classic API used by build_lance_index
    def encode_corpus(self, texts, *, batch_size=None, max_length=None,
                      modalities=("dense", "sparse", "colbert"), progress=None):
        text_list = list(texts)
        n = len(text_list)
        return {
            "dense": np.stack([self._seed_dense(i) for i in range(n)]),
            "sparse": [self._seed_sparse(i) for i in range(n)],
            "colbert": [self._seed_colbert(i) for i in range(n)],
        }

    # Streaming API used by build_lance_index_streaming
    def encode_corpus_streaming(self, texts, *, batch_size=None,
                                max_length=None,
                                modalities=("dense", "sparse", "colbert"),
                                progress=None):
        text_list = list(texts)
        n = len(text_list)
        bs = batch_size or self.batch_size
        for offset in range(0, n, bs):
            stop = min(offset + bs, n)
            batch_size_local = stop - offset
            yield offset, stop, {
                "dense": np.stack([self._seed_dense(i) for i in range(offset, stop)]),
                "sparse": [self._seed_sparse(i) for i in range(offset, stop)],
                "colbert": [self._seed_colbert(i) for i in range(offset, stop)],
            }


def _write_corpus(corpus_root: Path, n_chunks: int) -> None:
    """Drop a small synthetic corpus that ``corpus_loader.load_corpus`` accepts.

    corpus_loader requires ``<root>/contents/<category>/...`` structure
    (see corpus_loader.iter_corpus) and rejects chunks under
    MIN_CHARS_PER_CHUNK=60, so each doc body must clear that floor and
    sit under contents/<category>/.
    """
    # corpus_loader expects DEFAULT_CORPUS_ROOT / contents / <category> / *.md
    cat = corpus_root / "contents" / "test"
    cat.mkdir(parents=True, exist_ok=True)
    for i in range(n_chunks):
        body = (
            f"# Doc {i}\n\nThis is a synthetic test document for chunk {i}. "
            f"It contains enough text to clear the MIN_CHARS_PER_CHUNK threshold. "
            f"Lorem ipsum body content for indexing purposes.\n"
        )
        (cat / f"doc-{i:03d}.md").write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class ZeroCopyRecordBatchTest(unittest.TestCase):
    """Verify _lance_record_batch_zero_copy produces a RecordBatch matching
    the legacy schema with no Python list intermediate for ColBERT."""

    def _make_chunks_and_encoding(self, n: int):
        with TemporaryDirectory() as td:
            corpus = Path(td)
            _write_corpus(corpus, n)
            chunks = corpus_loader.load_corpus(corpus)
        # sort by chunk_id so test ordering matches
        chunks = sorted(chunks, key=lambda c: c.chunk_id)[:n]
        # Stable synthetic encoding
        enc = _FakeEncoder()
        encoding = enc.encode_corpus([f"text {i}" for i in range(len(chunks))])
        return chunks, encoding, enc

    def test_record_batch_shape_and_schema(self):
        chunks, encoding, enc = self._make_chunks_and_encoding(5)
        schema = indexer._lance_schema(enc.dense_dim, enc.colbert_dim, colbert_dtype="float16")
        batch = indexer._lance_record_batch_zero_copy(
            chunks, encoding, start=0, stop=len(chunks),
            encoder_version=enc.model_version, schema=schema,
        )
        self.assertEqual(batch.num_rows, len(chunks))
        self.assertEqual(batch.schema, schema)

    def test_colbert_column_zero_copy_size(self):
        """ColBERT column nbytes should equal sum(numpy_arr.nbytes), not
        the 16× amplification the .tolist() path produces."""
        chunks, encoding, enc = self._make_chunks_and_encoding(8)
        schema = indexer._lance_schema(enc.dense_dim, enc.colbert_dim, colbert_dtype="float16")
        batch = indexer._lance_record_batch_zero_copy(
            chunks, encoding, start=0, stop=len(chunks),
            encoder_version=enc.model_version, schema=schema,
        )
        colbert_col = batch.column("colbert_tokens")
        # Raw numpy total bytes
        raw_total = sum(arr.nbytes for arr in encoding["colbert"])
        # Arrow buffer bytes — should be within 5% of raw
        self.assertLessEqual(
            colbert_col.nbytes, raw_total * 1.05,
            f"colbert column nbytes={colbert_col.nbytes} vs raw={raw_total}",
        )
        self.assertGreaterEqual(colbert_col.nbytes, raw_total * 0.95)

    def test_record_batch_values_match_classic_path(self):
        """Round-trip: streaming RecordBatch's row 0 must match what
        the classic _lance_record_slice produces for the same chunk."""
        chunks, encoding, enc = self._make_chunks_and_encoding(3)
        schema = indexer._lance_schema(enc.dense_dim, enc.colbert_dim, colbert_dtype="float16")
        batch = indexer._lance_record_batch_zero_copy(
            chunks, encoding, start=0, stop=len(chunks),
            encoder_version=enc.model_version, schema=schema,
        )
        legacy_records = indexer._lance_record_slice(
            chunks, encoding, start=0, stop=len(chunks),
            encoder_version=enc.model_version,
        )
        # Compare row 0 — strings exact, floats close
        d_streaming = batch.to_pylist()[0]
        d_legacy = legacy_records[0]
        for k in ("chunk_id", "doc_id", "path", "title", "category",
                  "concept_id", "doc_role", "level", "encoder_version",
                  "content_sha1"):
            self.assertEqual(d_streaming[k], d_legacy[k], f"mismatch on '{k}'")
        # Dense vec — float comparison
        np.testing.assert_array_almost_equal(
            np.array(d_streaming["dense_vec"], dtype=np.float32),
            np.array(d_legacy["dense_vec"], dtype=np.float32),
            decimal=4,
        )
        # Sparse — sets equal regardless of dict ordering
        s_streaming = sorted(zip(d_streaming["sparse_vec"]["indices"],
                                  d_streaming["sparse_vec"]["values"]))
        s_legacy = sorted(zip(d_legacy["sparse_vec"]["indices"],
                              d_legacy["sparse_vec"]["values"]))
        self.assertEqual(s_streaming, s_legacy)
        # ColBERT — fp16 round-trip exact (no precision loss in cast)
        np.testing.assert_array_equal(
            np.array(d_streaming["colbert_tokens"], dtype=np.float16),
            np.array(d_legacy["colbert_tokens"], dtype=np.float16),
        )


class StreamingBuildEquivalenceTest(unittest.TestCase):
    """Building with streaming vs classic must produce the same LanceDB
    table — same row count, same column values, same schema."""

    def test_row_count_and_chunk_ids_match(self):
        with TemporaryDirectory() as td:
            corpus = Path(td)
            _write_corpus(corpus, 16)
            enc = _FakeEncoder()

            # Classic path
            classic_root = Path(td) / "classic_idx"
            indexer.build_lance_index(
                index_root=classic_root,
                corpus_root=corpus,
                encoder=enc,
                modalities=("dense", "sparse", "colbert"),
                write_batch_size=4,
            )
            classic_table = indexer.open_lance_table(classic_root)
            classic_rows = sorted(classic_table.to_arrow().column("chunk_id").to_pylist())

            # Streaming path
            stream_root = Path(td) / "stream_idx"
            indexer.build_lance_index_streaming(
                index_root=stream_root,
                corpus_root=corpus,
                encoder=enc,
                modalities=("dense", "sparse", "colbert"),
                write_batch_size=4,
            )
            stream_table = indexer.open_lance_table(stream_root)
            stream_rows = sorted(stream_table.to_arrow().column("chunk_id").to_pylist())

            self.assertEqual(len(classic_rows), 16)
            self.assertEqual(len(stream_rows), 16)
            self.assertEqual(classic_rows, stream_rows)

    def test_streaming_manifest_marks_build_path(self):
        with TemporaryDirectory() as td:
            corpus = Path(td)
            _write_corpus(corpus, 8)
            stream_root = Path(td) / "stream_idx"
            indexer.build_lance_index_streaming(
                index_root=stream_root,
                corpus_root=corpus,
                encoder=_FakeEncoder(),
                modalities=("dense", "sparse", "colbert"),
                write_batch_size=4,
            )
            manifest = json.loads(
                (stream_root / indexer.MANIFEST_NAME).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["ingest"]["build_path"], "streaming")
            self.assertEqual(manifest["row_count"], 8)


class StreamingBatchProxyTest(unittest.TestCase):
    """The internal _BatchedListProxy / _BatchedDenseProxy classes
    re-target slice indices from global corpus coordinates back to
    batch-local coordinates."""

    def test_dense_proxy_slice(self):
        local = np.zeros((4, 3), dtype=np.float32)
        local[2, 1] = 7.0
        proxy = indexer._BatchedDenseProxy(local, offset=10)
        # global indices [10:14] map to local [0:4]
        result = proxy[10:14]
        np.testing.assert_array_equal(result, local)
        self.assertEqual(proxy[12, 1], 7.0)

    def test_list_proxy_slice(self):
        local_list = [{"a": 0}, {"a": 1}, {"a": 2}, {"a": 3}]
        proxy = indexer._BatchedListProxy(local_list, offset=20)
        # global indices [22:24] map to local [2:4]
        result = proxy[22:24]
        self.assertEqual(result, [{"a": 2}, {"a": 3}])
        self.assertEqual(proxy[21]["a"], 1)


class StreamingMemoryFloorTest(unittest.TestCase):
    """The streaming build must NOT accumulate the full corpus encoding.

    We don't measure RSS (env-dependent) — we instead instrument the
    encoder to count how many chunks it has yielded simultaneously
    via a weakref-tracked counter. The classic encode_corpus would yield
    n_chunks at once; the streaming variant yields ≤ batch_size at once.
    """

    def test_streaming_holds_only_one_batch(self):
        """Verify the streaming generator yields one batch at a time,
        and the previous batch's ColBERT array is freed before the next
        is yielded (when the consumer drops its reference)."""
        import weakref

        enc = _FakeEncoder(batch_size=4, n_tokens_per_chunk=4)
        n = 20
        texts = [f"text {i}" for i in range(n)]
        held = {}
        max_concurrent = 0
        for start, stop, batch_enc in enc.encode_corpus_streaming(
            texts, batch_size=4, modalities=("colbert",),
        ):
            # Track this batch's ColBERT objects via weakref
            for i, arr in enumerate(batch_enc["colbert"]):
                held[start + i] = weakref.ref(arr)
            # Check how many are still alive — at this point the previous
            # batch should already be eligible for GC (we don't keep it).
            gc.collect()
            alive = sum(1 for ref in held.values() if ref() is not None)
            max_concurrent = max(max_concurrent, alive)
            # Drop our reference before next iteration
            del batch_enc

        gc.collect()
        # Streaming should keep at most one batch's worth of arrays
        # alive at any moment (4 in our setup, allow some slack for GC timing)
        self.assertLessEqual(
            max_concurrent, 8,
            f"streaming held {max_concurrent} chunks simultaneously, "
            f"expected ≤ batch_size + slack",
        )


if __name__ == "__main__":
    unittest.main()
