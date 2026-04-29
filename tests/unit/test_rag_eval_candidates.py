"""Unit tests for scripts.learning.rag.eval.candidates.

Coverage targets:
- Registry lists exactly four candidates with unique ids
- Exactly one control candidate (MiniLM-L12-v2)
- All hf_model_ids well-formed (org/model)
- get() returns by id; raises on unknown
- control() returns the single control
- upgrades() returns three candidates in declaration order
- index_dir_name is filesystem-safe (no slashes)
- approx_size_mb / embed_dim sanity (positive)
"""

from __future__ import annotations

import re

import pytest

from scripts.learning.rag.eval import candidates as C


def test_registry_has_four_candidates():
    assert len(C.CANDIDATES) == 4


def test_candidate_ids_are_unique():
    ids = [c.candidate_id for c in C.CANDIDATES]
    assert len(ids) == len(set(ids))


def test_exactly_one_control_candidate():
    controls = [c for c in C.CANDIDATES if c.is_control]
    assert len(controls) == 1
    assert controls[0].candidate_id == "MiniLM-L12-v2"


def test_control_helper_returns_minilm():
    assert C.control().candidate_id == "MiniLM-L12-v2"


def test_upgrades_excludes_control_and_has_three_entries():
    upgrades = C.upgrades()
    assert len(upgrades) == 3
    assert all(not c.is_control for c in upgrades)


def test_upgrades_preserves_declaration_order():
    upgrade_ids = [c.candidate_id for c in C.upgrades()]
    # In CANDIDATES order: e5-base → Qwen3 → bge-m3
    assert upgrade_ids == [
        "multilingual-e5-base",
        "Qwen3-Embedding-0.6B",
        "bge-m3",
    ]


def test_hf_model_ids_have_org_slash_model_form():
    pattern = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
    for c in C.CANDIDATES:
        assert pattern.match(c.hf_model_id), (
            f"{c.candidate_id} has malformed hf id: {c.hf_model_id!r}"
        )


def test_embed_dim_positive_and_known_values():
    # The four candidates use known dims
    by_id = {c.candidate_id: c.embed_dim for c in C.CANDIDATES}
    assert by_id["MiniLM-L12-v2"] == 384
    assert by_id["multilingual-e5-base"] == 768
    assert by_id["Qwen3-Embedding-0.6B"] == 1024
    assert by_id["bge-m3"] == 1024


def test_approx_size_positive():
    for c in C.CANDIDATES:
        assert c.approx_size_mb > 0


def test_index_dir_name_is_filesystem_safe():
    for c in C.CANDIDATES:
        name = c.index_dir_name()
        assert "/" not in name
        assert name == c.candidate_id


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

def test_get_returns_candidate_by_id():
    c = C.get("bge-m3")
    assert c.hf_model_id == "BAAI/bge-m3"
    assert c.embed_dim == 1024


def test_get_raises_on_unknown_id():
    with pytest.raises(ValueError, match="unknown candidate_id"):
        C.get("nope")


def test_get_error_message_lists_known_ids():
    with pytest.raises(ValueError) as exc_info:
        C.get("nonexistent")
    msg = str(exc_info.value)
    assert "MiniLM-L12-v2" in msg or "bge-m3" in msg
