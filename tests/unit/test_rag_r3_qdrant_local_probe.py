from __future__ import annotations

from scripts.learning.rag.r3.eval.qdrant_local_probe import _rrf_fuse, _sparse_lists


def test_qdrant_probe_sparse_lists_keep_positive_terms():
    indices, values = _sparse_lists(
        {
            "indices": [10, "20", "bad", 30],
            "values": [1.5, "2.0", 3.0, 0.0],
        }
    )

    assert indices == [10, 20]
    assert values == [1.5, 2.0]


def test_qdrant_probe_rrf_fuse_is_stable_and_weighted():
    fused = _rrf_fuse(
        (
            (1.0, ("a", "b", "c")),
            (2.0, ("c", "b")),
        ),
        limit=3,
    )

    assert fused == ("c", "b", "a")
