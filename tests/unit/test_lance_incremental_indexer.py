from __future__ import annotations

from pathlib import Path

import numpy as np

from scripts.learning.rag import corpus_loader, incremental_indexer, indexer


class FakeMultiModalEncoder:
    model_id = "fake/bge-m3"
    model_version = "fake/bge-m3@test"
    dense_dim = 8
    colbert_dim = 8
    sparse_vocab_size = 128

    def __init__(self) -> None:
        self.encode_calls = []

    def encode_corpus(
        self,
        texts,
        *,
        batch_size=16,
        max_length=8192,
        modalities=("dense", "sparse", "colbert"),
        progress=None,
    ):
        self.encode_calls.append(list(texts))
        want_dense = "dense" in modalities
        want_sparse = "sparse" in modalities
        want_colbert = "colbert" in modalities
        dense = np.zeros((len(texts), self.dense_dim), dtype=np.float32)
        sparse = []
        colbert = []
        for i, text in enumerate(texts):
            if want_dense:
                dense[i, i % self.dense_dim] = 1.0
            sparse.append({i + 1: 1.0, 42: 0.25} if want_sparse else {})
            if want_colbert:
                token_value = float((len(text) % 7) + 1)
                colbert.append(np.full((2, self.colbert_dim), token_value, dtype=np.float16))
            else:
                colbert.append(np.zeros((0, self.colbert_dim), dtype=np.float16))
        return {"dense": dense, "sparse": sparse, "colbert": colbert}

    def encode_query(self, text, *, modalities=("dense", "sparse", "colbert")):
        return self.encode_corpus([text], modalities=modalities)


def _write_doc(root: Path, category: str, slug: str, title: str, body: str) -> None:
    path = root / "contents" / category / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# {title}

**난이도: 🟢 Beginner**

retrieval-anchor-keywords:
- {title.lower()} basics
- {title} 처음 배우는데

## 핵심 개념

{body}
""",
        encoding="utf-8",
    )


def _fake_corpus(tmp_path: Path) -> Path:
    root = tmp_path / "corpus"
    _write_doc(
        root,
        "database",
        "transaction-basics",
        "트랜잭션 기초",
        "트랜잭션은 커밋과 롤백을 하나의 작업 단위로 묶는 약속입니다. " * 4,
    )
    _write_doc(
        root,
        "spring",
        "bean-basics",
        "Spring Bean 기초",
        "스프링 빈은 컨테이너가 생성하고 관리하는 객체입니다. " * 4,
    )
    return root


def test_model_chunk_hash_sidecar_is_per_model_and_atomic(tmp_path):
    index_root = tmp_path / "index"

    incremental_indexer.atomic_save_model_chunk_hashes(
        index_root=index_root,
        model_version="model-a@1",
        fingerprints={"a": "sha1:a"},
    )
    incremental_indexer.atomic_save_model_chunk_hashes(
        index_root=index_root,
        model_version="model-b@1",
        fingerprints={"b": "sha1:b"},
    )

    assert incremental_indexer.load_model_chunk_hashes(index_root, "model-a@1") == {
        "a": "sha1:a"
    }
    assert incremental_indexer.load_model_chunk_hashes(index_root, "model-b@1") == {
        "b": "sha1:b"
    }


def test_incremental_lance_build_full_fallback_then_noop(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    expected_count = len(corpus_loader.load_corpus(corpus_root))

    first = incremental_indexer.incremental_lance_build_index(
        encoder=encoder,
        index_root=index_root,
        corpus_root=corpus_root,
    )

    assert first.mode == "full"
    assert first.fallback_reason == "no_manifest"
    assert first.encoded_chunk_count == expected_count
    assert first.lance_version_after is not None
    assert indexer.open_lance_table(index_root).count_rows() == expected_count
    assert incremental_indexer.load_model_chunk_hashes(
        index_root, encoder.model_version
    )

    second = incremental_indexer.incremental_lance_build_index(
        encoder=encoder,
        index_root=index_root,
        corpus_root=corpus_root,
    )

    assert second.mode == "incremental"
    assert second.encoded_chunk_count == 0
    assert second.diff_stats["unchanged"] == expected_count
    assert second.lance_version_before == second.lance_version_after
    assert indexer.open_lance_table(index_root).count_rows() == expected_count


def test_incremental_lance_build_handles_add_and_pure_delete(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    initial = incremental_indexer.incremental_lance_build_index(
        encoder=encoder,
        index_root=index_root,
        corpus_root=corpus_root,
    )
    initial_count = initial.manifest["row_count"]

    _write_doc(
        corpus_root,
        "network",
        "http-basics",
        "HTTP 기초",
        "HTTP는 클라이언트와 서버가 요청과 응답을 주고받는 규칙입니다. " * 4,
    )
    added_expected = len(corpus_loader.load_corpus(corpus_root)) - initial_count
    added = incremental_indexer.incremental_lance_build_index(
        encoder=encoder,
        index_root=index_root,
        corpus_root=corpus_root,
    )

    assert added.mode == "incremental"
    assert added.diff_stats["added"] == added_expected
    assert added.encoded_chunk_count == added_expected
    assert added.lance_version_after > added.lance_version_before
    assert indexer.open_lance_table(index_root).count_rows() == initial_count + added_expected

    (corpus_root / "contents" / "network" / "http-basics.md").unlink()
    deleted = incremental_indexer.incremental_lance_build_index(
        encoder=encoder,
        index_root=index_root,
        corpus_root=corpus_root,
    )

    assert deleted.mode == "incremental"
    assert deleted.diff_stats["deleted"] == added_expected
    assert deleted.encoded_chunk_count == 0
    assert deleted.lance_version_after > deleted.lance_version_before
    assert indexer.open_lance_table(index_root).count_rows() == initial_count


def test_incremental_lance_build_handles_sparse_without_colbert_modalities(tmp_path):
    corpus_root = _fake_corpus(tmp_path)
    index_root = tmp_path / "index"
    encoder = FakeMultiModalEncoder()
    initial = incremental_indexer.incremental_lance_build_index(
        encoder=encoder,
        index_root=index_root,
        corpus_root=corpus_root,
        modalities=("fts", "dense", "sparse"),
    )
    initial_count = initial.manifest["row_count"]

    _write_doc(
        corpus_root,
        "network",
        "latency-basics",
        "Latency 기초",
        "Latency는 요청과 응답 사이에 걸리는 시간입니다. " * 4,
    )
    added = incremental_indexer.incremental_lance_build_index(
        encoder=encoder,
        index_root=index_root,
        corpus_root=corpus_root,
        modalities=("fts", "dense", "sparse"),
    )
    final_count = indexer.open_lance_table(index_root).count_rows()

    assert added.mode == "incremental"
    assert added.encoded_chunk_count == final_count - initial_count
    assert final_count > initial_count
