"""Unit tests for scripts.learning.rag.eval.reranker_candidates.

Coverage targets:
- Registry has 3 candidates with unique ids
- Exactly one control (mmarco)
- HF id format
- get() / control() / upgrades() / low_memory_only() helpers
- high_memory_risk flag classifies bge-reranker-v2-m3 correctly
- index_dir_name has 'reranker__' prefix to avoid collision with
  embedding A/B index dirs
"""

from __future__ import annotations

import re

import pytest

from scripts.learning.rag.eval import reranker_candidates as RC


def test_registry_has_three_candidates():
    assert len(RC.CANDIDATES) == 3


def test_unique_candidate_ids():
    ids = [c.candidate_id for c in RC.CANDIDATES]
    assert len(set(ids)) == len(ids)


def test_exactly_one_control_is_mmarco():
    controls = [c for c in RC.CANDIDATES if c.is_control]
    assert len(controls) == 1
    assert controls[0].candidate_id == "mmarco-mMiniLMv2"


def test_control_helper_returns_mmarco():
    assert RC.control().candidate_id == "mmarco-mMiniLMv2"


def test_upgrades_excludes_control():
    upgrades = RC.upgrades()
    assert len(upgrades) == 2
    assert all(not c.is_control for c in upgrades)
    upgrade_ids = {c.candidate_id for c in upgrades}
    assert upgrade_ids == {"mxbai-rerank-base-v1", "bge-reranker-v2-m3"}


def test_low_memory_only_excludes_high_risk():
    safe = RC.low_memory_only()
    safe_ids = {c.candidate_id for c in safe}
    assert "bge-reranker-v2-m3" not in safe_ids  # too big for 16GB
    assert "mxbai-rerank-base-v1" in safe_ids
    assert "mmarco-mMiniLMv2" in safe_ids


def test_high_memory_flag_set_correctly():
    by_id = {c.candidate_id: c for c in RC.CANDIDATES}
    assert by_id["bge-reranker-v2-m3"].high_memory_risk is True
    assert by_id["mxbai-rerank-base-v1"].high_memory_risk is False
    assert by_id["mmarco-mMiniLMv2"].high_memory_risk is False


def test_hf_model_ids_well_formed():
    pattern = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
    for c in RC.CANDIDATES:
        assert pattern.match(c.hf_model_id), (
            f"{c.candidate_id} has malformed hf id: {c.hf_model_id!r}"
        )


def test_approx_size_positive_and_known():
    by_id = {c.candidate_id: c.approx_size_mb for c in RC.CANDIDATES}
    assert by_id["mmarco-mMiniLMv2"] > 0
    assert by_id["mxbai-rerank-base-v1"] < 500  # safe size class
    assert by_id["bge-reranker-v2-m3"] > 1000  # high memory class


def test_index_dir_name_has_reranker_prefix():
    """Reranker eval dirs must not collide with embedding eval dirs
    (state/cs_rag_eval/MiniLM-L12-v2/ vs reranker__mmarco-...)."""
    for c in RC.CANDIDATES:
        name = c.index_dir_name()
        assert name.startswith("reranker__")
        assert "/" not in name


def test_get_lookup():
    c = RC.get("mxbai-rerank-base-v1")
    assert c.hf_model_id == "mixedbread-ai/mxbai-rerank-base-v1"
    assert c.is_control is False


def test_get_unknown_raises():
    with pytest.raises(ValueError, match="unknown reranker candidate_id"):
        RC.get("nope")
