"""Tests for the embedding-cosine dedupe candidate finder (plan §P5.4)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pytest

from scripts.learning.rag import dedupe as D
from scripts.learning.rag import indexer


# ---------------------------------------------------------------------------
# aggregate_by_path
# ---------------------------------------------------------------------------

def test_aggregate_by_path_means_chunks():
    embs = np.array(
        [[1.0, 0.0], [3.0, 0.0],   # path A → mean = (2, 0)
         [0.0, 4.0]],              # path B → mean = (0, 4)
        dtype="float32",
    )
    paths = ["a.md", "a.md", "b.md"]
    out_paths, out_means = D.aggregate_by_path(embs, paths)
    assert out_paths == ["a.md", "b.md"]
    np.testing.assert_array_almost_equal(out_means, [[2.0, 0.0], [0.0, 4.0]])


def test_aggregate_by_path_preserves_first_occurrence_order():
    embs = np.array([[1.0], [2.0], [3.0]], dtype="float32")
    paths = ["c.md", "a.md", "c.md"]
    out_paths, _ = D.aggregate_by_path(embs, paths)
    assert out_paths == ["c.md", "a.md"]


def test_aggregate_by_path_rejects_length_mismatch():
    embs = np.array([[1.0]], dtype="float32")
    with pytest.raises(ValueError):
        D.aggregate_by_path(embs, ["a.md", "b.md"])


# ---------------------------------------------------------------------------
# find_near_duplicate_pairs
# ---------------------------------------------------------------------------

def test_find_near_duplicates_identifies_obvious_pair():
    """Three docs: A and B are near-identical, C is orthogonal."""
    embs = np.array([
        [1.0, 0.0, 0.0],   # a.md
        [0.95, 0.31, 0.0], # b.md — cosine ≈ 0.95 with a.md
        [0.0, 0.0, 1.0],   # c.md — cosine 0 with both
    ], dtype="float32")
    paths = ["a.md", "b.md", "c.md"]
    pairs = D.find_near_duplicate_pairs(embs, paths, threshold=0.9)
    assert len(pairs) == 1
    assert pairs[0].path_a == "a.md"
    assert pairs[0].path_b == "b.md"
    assert pairs[0].cosine >= 0.9


def test_find_near_duplicates_threshold_filters():
    embs = np.array([
        [1.0, 0.0],
        [0.7, 0.7],   # cosine ≈ 0.707 with above
    ], dtype="float32")
    pairs_strict = D.find_near_duplicate_pairs(embs, ["a.md", "b.md"], threshold=0.9)
    pairs_loose = D.find_near_duplicate_pairs(embs, ["a.md", "b.md"], threshold=0.5)
    assert pairs_strict == []
    assert len(pairs_loose) == 1


def test_find_near_duplicates_orders_pair_alphabetically():
    """Output pair must use lexicographic order regardless of input
    ordering, so the same dedupe pair never appears twice with swapped
    a/b roles."""
    embs = np.array([[1.0], [1.0]], dtype="float32")
    p1 = D.find_near_duplicate_pairs(embs, ["zzz.md", "aaa.md"], threshold=0.99)
    p2 = D.find_near_duplicate_pairs(embs, ["aaa.md", "zzz.md"], threshold=0.99)
    assert p1[0].path_a == "aaa.md"
    assert p1[0].path_b == "zzz.md"
    assert p1[0] == p2[0]


def test_find_near_duplicates_sorts_by_cosine_desc():
    embs = np.array([
        [1.0, 0.0],
        [0.95, 0.31],   # ~0.95 with first
        [0.85, 0.53],   # ~0.85 with first
    ], dtype="float32")
    pairs = D.find_near_duplicate_pairs(
        embs, ["a.md", "b.md", "c.md"], threshold=0.5,
    )
    cosines = [p.cosine for p in pairs]
    assert cosines == sorted(cosines, reverse=True)


def test_find_near_duplicates_aggregates_chunks_per_path():
    """Multiple chunks per doc should be averaged, not surfaced as
    separate pairs."""
    embs = np.array([
        [1.0, 0.0],   # a.md chunk 1
        [1.0, 0.0],   # a.md chunk 2
        [1.0, 0.0],   # b.md chunk 1
    ], dtype="float32")
    paths = ["a.md", "a.md", "b.md"]
    pairs = D.find_near_duplicate_pairs(embs, paths, threshold=0.99)
    # Just one pair (a.md, b.md), not three from chunk-level
    assert len(pairs) == 1


def test_find_near_duplicates_empty_input():
    embs = np.zeros((0, 4), dtype="float32")
    assert D.find_near_duplicate_pairs(embs, []) == []


def test_find_near_duplicates_single_doc():
    embs = np.array([[1.0, 0.0]], dtype="float32")
    assert D.find_near_duplicate_pairs(embs, ["only.md"]) == []


def test_find_near_duplicates_zero_vectors_no_div_by_zero():
    """Pure-zero embeddings shouldn't crash _normalize_rows."""
    embs = np.zeros((2, 4), dtype="float32")
    pairs = D.find_near_duplicate_pairs(embs, ["a.md", "b.md"])
    # Zero-zero "cosine" stays 0, so no pair surfaces
    assert pairs == []


def test_find_near_duplicates_rejects_invalid_threshold():
    embs = np.zeros((1, 1), dtype="float32")
    with pytest.raises(ValueError):
        D.find_near_duplicate_pairs(embs, ["a.md"], threshold=1.5)


# ---------------------------------------------------------------------------
# scope_fn — same-category scope
# ---------------------------------------------------------------------------

def test_same_category_scope_groups_by_first_segment():
    assert D.same_category_scope(
        "knowledge/cs/contents/spring/bean.md",
        "knowledge/cs/contents/spring/component.md",
    ) is True
    assert D.same_category_scope(
        "knowledge/cs/contents/spring/bean.md",
        "knowledge/cs/contents/algorithm/dfs.md",
    ) is False


def test_same_category_scope_handles_missing_contents_prefix():
    """Bare paths (no ``contents/`` segment) fall back to first
    segment matching."""
    assert D.same_category_scope("spring/a.md", "spring/b.md") is True
    assert D.same_category_scope("spring/a.md", "db/b.md") is False


def test_find_near_duplicates_respects_scope_fn():
    embs = np.array([
        [1.0, 0.0],
        [1.0, 0.0],   # same vector, different category
    ], dtype="float32")
    paths = [
        "knowledge/cs/contents/spring/a.md",
        "knowledge/cs/contents/algorithm/b.md",
    ]
    pairs_no_scope = D.find_near_duplicate_pairs(embs, paths, threshold=0.99)
    pairs_scoped = D.find_near_duplicate_pairs(
        embs, paths, threshold=0.99, scope_fn=D.same_category_scope,
    )
    assert len(pairs_no_scope) == 1   # without scope, perfect match
    assert pairs_scoped == []         # with scope, different category → skipped


# ---------------------------------------------------------------------------
# Runner — load real-shape index + invoke dedupe
# ---------------------------------------------------------------------------

def _build_synthetic_index(tmp_path: Path) -> Path:
    """Create a minimal state/cs_rag-style index for runner tests:
    SQLite with chunks(rowid, path, ...) + dense.npz with embeddings
    + row_ids."""
    index_root = tmp_path / "cs_rag"
    index_root.mkdir(parents=True, exist_ok=True)

    sqlite_path = index_root / "index.sqlite3"
    conn = sqlite3.connect(sqlite_path)
    conn.execute("CREATE TABLE chunks (path TEXT)")
    paths = [
        "knowledge/cs/contents/spring/bean.md",
        "knowledge/cs/contents/spring/bean-lifecycle.md",
        "knowledge/cs/contents/algorithm/dfs.md",
    ]
    row_ids = []
    for p in paths:
        cur = conn.execute("INSERT INTO chunks(path) VALUES (?)", (p,))
        row_ids.append(cur.lastrowid)
    conn.commit()
    conn.close()

    embs = np.array([
        [1.0, 0.0, 0.0],
        [0.95, 0.31, 0.0],   # near-dup of bean.md
        [0.0, 0.0, 1.0],     # orthogonal
    ], dtype="float32")
    np.savez(index_root / "dense.npz",
             embeddings=embs,
             row_ids=np.asarray(row_ids, dtype="int64"))
    return index_root


class FakeDedupeLanceEncoder:
    model_id = "fake/bge-m3"
    model_version = "fake/bge-m3@dedupe"
    dense_dim = 4
    colbert_dim = 4
    sparse_vocab_size = 128
    max_length = 512
    batch_size = 32

    def encode_corpus(
        self,
        texts,
        *,
        batch_size=16,
        max_length=8192,
        modalities=("dense", "sparse", "colbert"),
        progress=None,
    ):
        dense = np.zeros((len(texts), self.dense_dim), dtype=np.float32)
        sparse = []
        colbert = []
        for i, text in enumerate(texts):
            if "Spring Bean" in text:
                dense[i] = np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
            else:
                dense[i] = np.asarray([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
            sparse.append({i + 1: 1.0})
            colbert.append(np.full((1, self.colbert_dim), float(i + 1), dtype=np.float16))
        return {"dense": dense, "sparse": sparse, "colbert": colbert}

    def encode_query(self, text, *, modalities=("dense", "sparse", "colbert")):
        return self.encode_corpus([text], modalities=modalities)


def _write_lance_doc(root: Path, category: str, slug: str, title: str, body: str) -> None:
    path = root / "contents" / category / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# {title}

> 한 줄 요약: 테스트용 문서입니다.

**난이도: 🟢 Beginner**

retrieval-anchor-keywords:
- {title} basics
- {title} 처음 배우는데

## 핵심 개념

{body}
""",
        encoding="utf-8",
    )


def _build_synthetic_lance_index(tmp_path: Path) -> Path:
    corpus_root = tmp_path / "lance-corpus"
    _write_lance_doc(
        corpus_root,
        "spring",
        "bean-basics",
        "Spring Bean basics",
        "Spring Bean은 컨테이너가 관리하는 객체입니다. " * 4,
    )
    _write_lance_doc(
        corpus_root,
        "spring",
        "bean-lifecycle",
        "Spring Bean lifecycle",
        "Spring Bean lifecycle은 생성과 초기화 흐름을 다룹니다. " * 4,
    )
    _write_lance_doc(
        corpus_root,
        "algorithm",
        "dfs",
        "DFS basics",
        "DFS는 그래프를 깊이 우선으로 탐색하는 알고리즘입니다. " * 4,
    )

    index_root = tmp_path / "lance-index"
    indexer.build_lance_index(
        index_root=index_root,
        corpus_root=corpus_root,
        encoder=FakeDedupeLanceEncoder(),
    )
    return index_root


def test_runner_loads_paths_aligned_with_embeddings(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    idx = _build_synthetic_index(tmp_path)
    paths, embs = R.load_index_paths_and_embeddings(idx)
    assert len(paths) == 3
    assert paths[0].endswith("/bean.md")
    assert embs.shape == (3, 3)


def test_runner_loads_paths_aligned_with_lance_embeddings(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    idx = _build_synthetic_lance_index(tmp_path)
    paths, embs = R.load_index_paths_and_embeddings(idx)
    assert len(paths) >= 3
    assert len(set(paths)) == 3
    assert any(path.endswith("/bean-basics.md") for path in paths)
    assert embs.shape == (len(paths), FakeDedupeLanceEncoder.dense_dim)


def test_runner_finds_pair_in_synthetic_index(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    idx = _build_synthetic_index(tmp_path)
    result = R.find_dedupe_candidates(
        index_root=idx, threshold=0.9, same_category_only=True,
    )
    assert len(result.pairs) == 1
    assert result.pairs[0].path_a.endswith("/bean-lifecycle.md")
    assert result.pairs[0].path_b.endswith("/bean.md")
    assert result.embedding_count == 3
    assert result.unique_path_count == 3
    assert result.threshold == 0.9


def test_runner_finds_pair_in_synthetic_lance_index(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    idx = _build_synthetic_lance_index(tmp_path)
    result = R.find_dedupe_candidates(
        index_root=idx, threshold=0.99, same_category_only=True,
    )
    assert len(result.pairs) == 1
    assert result.pairs[0].path_a.endswith("/bean-basics.md")
    assert result.pairs[0].path_b.endswith("/bean-lifecycle.md")
    assert result.embedding_count >= 3
    assert result.unique_path_count == 3


def test_runner_same_category_only_filters_cross_domain(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    # Force a cross-domain near-dup: spring/bean.md and algorithm/bean.md
    index_root = tmp_path / "cs_rag"
    index_root.mkdir(parents=True, exist_ok=True)
    sqlite_path = index_root / "index.sqlite3"
    conn = sqlite3.connect(sqlite_path)
    conn.execute("CREATE TABLE chunks (path TEXT)")
    p1 = "knowledge/cs/contents/spring/bean.md"
    p2 = "knowledge/cs/contents/algorithm/dfs.md"
    cur1 = conn.execute("INSERT INTO chunks(path) VALUES (?)", (p1,))
    cur2 = conn.execute("INSERT INTO chunks(path) VALUES (?)", (p2,))
    conn.commit()
    conn.close()

    embs = np.array([[1.0, 0.0], [1.0, 0.0]], dtype="float32")
    np.savez(index_root / "dense.npz",
             embeddings=embs,
             row_ids=np.asarray([cur1.lastrowid, cur2.lastrowid], dtype="int64"))

    same_cat = R.find_dedupe_candidates(
        index_root=index_root, threshold=0.99, same_category_only=True,
    )
    cross = R.find_dedupe_candidates(
        index_root=index_root, threshold=0.99, same_category_only=False,
    )
    assert len(same_cat.pairs) == 0
    assert len(cross.pairs) == 1


def test_runner_missing_index_raises_filenotfound(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    with pytest.raises(FileNotFoundError):
        R.load_index_paths_and_embeddings(tmp_path / "no-such-index")


# ---------------------------------------------------------------------------
# corpus_lint integration
# ---------------------------------------------------------------------------

def test_lint_callback_emits_violations_per_pair(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    idx = _build_synthetic_index(tmp_path)
    callback = R.make_lint_callback(index_root=idx, threshold=0.9)
    violations = callback([])  # files arg unused — paths come from index
    assert len(violations) == 1
    v = violations[0]
    assert v.check == "dedupe_candidates"
    assert "near-duplicate" in v.message
    assert "cosine=" in v.message


def test_lint_callback_handles_missing_index_gracefully(tmp_path):
    from scripts.learning.rag import corpus_dedupe_runner as R
    callback = R.make_lint_callback(
        index_root=tmp_path / "nope", threshold=0.92,
    )
    violations = callback([])
    # One synthetic violation explaining the index is missing
    assert len(violations) == 1
    assert "not built" in violations[0].message
