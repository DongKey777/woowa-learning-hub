"""Unit tests for scripts.learning.rag.eval.index_builder.

Coverage targets:
- Builds a complete index with a fake encoder (no SentenceTransformer
  load needed)
- Manifest fields (index_version, embed_model, embed_dim, row_count,
  corpus_hash, corpus_root) are populated correctly
- Wrong embed_dim aborts the build BEFORE writing dense
- Empty corpus raises RuntimeError
- Clean slate: pre-existing index files in target dir are wiped
- Progress callback is invoked at expected stages
- eval_index_root_for replaces "/" in HF ids
- Built index is round-trip readable via indexer.load_dense /
  indexer.load_manifest (lockstep schema with production)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def fake_corpus(tmp_path):
    """Create a minimal corpus tree mirroring the project layout.

    Each H2 section needs at least MIN_CHARS_PER_CHUNK (60) of body
    text to survive corpus_loader chunking — pad accordingly.
    """
    corpus_root = tmp_path / "corpus"
    cat = corpus_root / "contents" / "spring"
    cat.mkdir(parents=True)
    long_body = (
        "Spring Bean은 Spring IoC 컨테이너에 의해 생성되고 관리되는 객체이다. "
        "@Component, @Service 등의 어노테이션 또는 @Bean 메서드로 등록한다. "
        "라이프사이클은 컨테이너 시작 시 결정되며 의존성 주입을 받는다."
    )
    (cat / "bean.md").write_text(
        f"# Spring Bean\n\n## 정의\n\n{long_body}\n",
        encoding="utf-8",
    )
    (cat / "ioc.md").write_text(
        f"# IoC\n\n## 정의\n\nInversion of Control: {long_body}\n",
        encoding="utf-8",
    )
    return corpus_root


class _FakeEncoder:
    """Minimal SentenceTransformer-shaped fake."""

    def __init__(self, dim: int = 4):
        self._dim = dim
        self.call_count = 0
        self.last_args: dict = {}

    def encode(self, sentences, *, batch_size, show_progress_bar,
               normalize_embeddings, convert_to_numpy):
        import numpy as np

        self.call_count += 1
        self.last_args = {
            "batch_size": batch_size,
            "show_progress_bar": show_progress_bar,
            "normalize_embeddings": normalize_embeddings,
            "convert_to_numpy": convert_to_numpy,
        }
        # Deterministic per-text vector: one-hot on hash mod dim
        vecs = np.zeros((len(sentences), self._dim), dtype="float32")
        for i, _ in enumerate(sentences):
            vecs[i, i % self._dim] = 1.0
        return vecs


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_build_eval_index_creates_full_index(tmp_path, fake_corpus):
    from scripts.learning.rag.eval.index_builder import build_eval_index
    from scripts.learning.rag import indexer

    index_root = tmp_path / "eval-idx"
    encoder = _FakeEncoder(dim=4)
    manifest = build_eval_index(
        model=encoder,
        model_id="fake/test-model",
        embed_dim=4,
        index_root=index_root,
        corpus_root=fake_corpus,
    )

    # Files exist
    assert (index_root / indexer.SQLITE_NAME).exists()
    assert (index_root / indexer.DENSE_NAME).exists()
    assert (index_root / indexer.MANIFEST_NAME).exists()

    # Manifest fields
    assert manifest["embed_model"] == "fake/test-model"
    assert manifest["embed_dim"] == 4
    assert manifest["index_version"] == indexer.INDEX_VERSION
    assert manifest["row_count"] == 2
    assert manifest["corpus_hash"]  # non-empty
    assert manifest["corpus_root"] == str(fake_corpus)

    # Manifest round-trips through production loader
    loaded = indexer.load_manifest(index_root)
    assert loaded == manifest

    # Dense round-trips
    embeddings, row_ids = indexer.load_dense(index_root)
    assert embeddings.shape == (2, 4)
    assert len(row_ids) == 2


def test_build_eval_index_invokes_progress_callback(tmp_path, fake_corpus):
    from scripts.learning.rag.eval.index_builder import build_eval_index

    stages: list[str] = []

    def progress(stage, info):
        stages.append(stage)

    build_eval_index(
        model=_FakeEncoder(),
        model_id="m",
        embed_dim=4,
        index_root=tmp_path / "idx",
        corpus_root=fake_corpus,
        progress=progress,
    )
    # Expected stage order
    assert "load_corpus" in stages
    assert "load_corpus_done" in stages
    assert "encode" in stages
    assert "write_dense" in stages
    assert "write_manifest" in stages


def test_build_eval_index_passes_batch_size_to_encoder(tmp_path, fake_corpus):
    from scripts.learning.rag.eval.index_builder import build_eval_index

    encoder = _FakeEncoder()
    build_eval_index(
        model=encoder,
        model_id="m",
        embed_dim=4,
        index_root=tmp_path / "idx",
        corpus_root=fake_corpus,
        batch_size=8,
    )
    assert encoder.last_args["batch_size"] == 8
    assert encoder.last_args["normalize_embeddings"] is True


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_build_eval_index_aborts_on_dim_mismatch(tmp_path, fake_corpus):
    from scripts.learning.rag.eval.index_builder import build_eval_index

    # Encoder produces dim=4 but we declare dim=8
    with pytest.raises(RuntimeError, match="unexpected embedding shape"):
        build_eval_index(
            model=_FakeEncoder(dim=4),
            model_id="m",
            embed_dim=8,
            index_root=tmp_path / "bad",
            corpus_root=fake_corpus,
        )


def test_build_eval_index_empty_corpus_raises(tmp_path):
    from scripts.learning.rag.eval.index_builder import build_eval_index

    empty = tmp_path / "empty-corpus"
    (empty / "contents" / "spring").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="empty"):
        build_eval_index(
            model=_FakeEncoder(),
            model_id="m",
            embed_dim=4,
            index_root=tmp_path / "idx",
            corpus_root=empty,
        )


def test_build_eval_index_wipes_previous_files(tmp_path, fake_corpus):
    from scripts.learning.rag.eval.index_builder import build_eval_index
    from scripts.learning.rag import indexer

    index_root = tmp_path / "idx"
    index_root.mkdir()

    # Pre-existing junk files at the canonical names
    (index_root / indexer.MANIFEST_NAME).write_text("stale", encoding="utf-8")
    (index_root / indexer.DENSE_NAME).write_bytes(b"stale-bytes")

    build_eval_index(
        model=_FakeEncoder(),
        model_id="m",
        embed_dim=4,
        index_root=index_root,
        corpus_root=fake_corpus,
    )

    # Old garbage replaced with valid manifest JSON
    blob = json.loads((index_root / indexer.MANIFEST_NAME).read_text())
    assert blob["embed_model"] == "m"


# ---------------------------------------------------------------------------
# Naming helper
# ---------------------------------------------------------------------------

def test_eval_index_root_for_replaces_slash_in_hf_id():
    from scripts.learning.rag.eval.index_builder import eval_index_root_for

    p = eval_index_root_for("BAAI/bge-m3", base="state/cs_rag_eval")
    assert p == Path("state/cs_rag_eval/BAAI__bge-m3")


def test_eval_index_root_for_handles_no_slash_id():
    from scripts.learning.rag.eval.index_builder import eval_index_root_for

    p = eval_index_root_for("MiniLM-L12", base="state/cs_rag_eval")
    assert p == Path("state/cs_rag_eval/MiniLM-L12")
