"""Phase 9.4 — Citation block contract.

Pre-renders a `참고:` markdown block in `bin/rag-ask` output so the AI
session can copy it verbatim instead of authoring citation by hand.

Contract:
  * `integration.augment()` return dict gains `response_hints`
    sub-dict with two keys:
      - `citation_markdown`: paste-ready string for tier ≥ 1 with
        hits, else None
      - `citation_paths`: deduplicated list of hit paths used in
        citation_markdown (max 3)
  * `bin/rag-ask` JSON output gains a top-level `response_hints`
    field surfaced from augment.

These tests guard the contract — if a refactor drops the field,
they fail. AGENTS.md / CLAUDE.md regulation switches from
"AI 세션이 `참고:` 인용" to "verbatim copy of
`response_hints.citation_markdown`".
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.learning import integration
from scripts.learning.rag import indexer, searcher


class _ReadyReport:
    state = "ready"
    reason = "ready"
    corpus_hash = "fixture"
    index_manifest_hash = "fixture"
    next_command = None


def _write_manifest(index_root: Path) -> None:
    index_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "index_version": indexer.LANCE_INDEX_VERSION,
        "row_count": 1,
        "corpus_hash": "fixture",
        "corpus_root": "fixture",
        "encoder": {"model_id": "BAAI/bge-m3"},
        "lancedb": {"table_name": indexer.LANCE_TABLE_NAME},
        "modalities": ["fts", "dense", "sparse"],
    }
    (index_root / indexer.MANIFEST_NAME).write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _hit(path: str, score: float = 1.0) -> dict:
    return {
        "path": path,
        "title": Path(path).stem,
        "category": Path(path).parent.name,
        "section_title": "핵심 개념",
        "section_path": [Path(path).stem, "핵심 개념"],
        "score": score,
        "snippet_preview": "preview",
    }


def test_augment_emits_citation_markdown_when_hits_present(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit("knowledge/cs/contents/spring/spring-bean-di-basics.md", 0.92),
            _hit("knowledge/cs/contents/spring/ioc-di-container.md", 0.81),
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    assert "response_hints" in result
    rh = result["response_hints"]

    assert rh["citation_markdown"] is not None
    assert rh["citation_markdown"].startswith("참고:\n"), \
        f"unexpected citation prefix: {rh['citation_markdown'][:40]!r}"

    # Every hit path appears in the markdown
    for path in (
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "knowledge/cs/contents/spring/ioc-di-container.md",
    ):
        assert path in rh["citation_markdown"], \
            f"{path} missing from citation"

    # citation_paths reflects hits in order, deduplicated, max 3
    assert rh["citation_paths"] == [
        "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "knowledge/cs/contents/spring/ioc-di-container.md",
    ]


def test_augment_caps_citation_at_three_paths(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return [
            _hit(f"knowledge/cs/contents/spring/x{i}.md", 1.0 - i * 0.05)
            for i in range(7)
        ]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert len(rh["citation_paths"]) == 3
    # Only the top three are in the markdown
    for i in range(3):
        assert f"x{i}.md" in rh["citation_markdown"]
    for i in range(3, 7):
        assert f"x{i}.md" not in rh["citation_markdown"]


def test_augment_dedupes_repeated_paths_in_citation(tmp_path, monkeypatch):
    """When the same path appears in by_learning_point AND by_fallback_key
    buckets, citation_paths should still list it once."""
    index_root = tmp_path / "index"
    _write_manifest(index_root)
    same_path = "knowledge/cs/contents/spring/spring-bean-di-basics.md"

    def fake_search(prompt, **kwargs):
        # augment dedupes by `seen_paths` so this naturally tests
        # citation_paths not duplicating.
        return [_hit(same_path, 0.92)]

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_paths"].count(same_path) == 1


def test_augment_empty_hits_returns_none_citation(tmp_path, monkeypatch):
    index_root = tmp_path / "index"
    _write_manifest(index_root)

    def fake_search(prompt, **kwargs):
        return []

    monkeypatch.setattr(searcher, "search", fake_search)

    result = integration.augment(
        prompt="rare topic",
        learning_points=None,
        cs_search_mode="full",
        index_root=index_root,
        readiness=_ReadyReport(),
    )

    rh = result["response_hints"]
    assert rh["citation_markdown"] is None
    assert rh["citation_paths"] == []


def test_augment_skip_mode_returns_none_response_hints():
    result = integration.augment(
        prompt="Spring DI가 뭐야?",
        learning_points=None,
        cs_search_mode="skip",
    )
    # Even in skip mode the response_hints field exists with None
    # citation — keeps the contract uniform.
    rh = result.get("response_hints")
    assert rh is not None
    assert rh["citation_markdown"] is None
    assert rh["citation_paths"] == []


# ---------------------------------------------------------------------------
# `bin/rag-ask` surface — top-level response_hints contract
# ---------------------------------------------------------------------------

def _import_cli():
    import sys
    repo_root = Path(__file__).resolve().parents[2]
    for entry in (repo_root, repo_root / "scripts" / "workbench"):
        if str(entry) not in sys.path:
            sys.path.insert(0, str(entry))
    from scripts.workbench import cli  # noqa: WPS433
    return cli


def _patch_classify(monkeypatch, decision):
    """cli.build_rag_ask_output performs `from core.interactive_rag_router
    import classify` via sys.path entry — patch BOTH possible module
    aliases (`core.*` and `scripts.workbench.core.*`) so the local-scope
    rebind sees our fake."""
    cli_mod = _import_cli()  # ensures sys.path is set
    import importlib

    def fake_classify(prompt, **kwargs):
        return decision

    for module_name in (
        "core.interactive_rag_router",
        "scripts.workbench.core.interactive_rag_router",
    ):
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            continue
        monkeypatch.setattr(mod, "classify", fake_classify)


def test_rag_ask_output_has_response_hints_stub_for_tier_0(monkeypatch):
    """Tier 0 / blocked / tier 3 turns must still carry the
    `response_hints` key so downstream code can read a uniform shape."""
    cli = _import_cli()
    from scripts.workbench.core.interactive_rag_router import RouterDecision

    _patch_classify(monkeypatch, RouterDecision(
        tier=0, mode=None, reason="tool/build question, no CS domain",
        experience_level=None, override_active=False, blocked=False,
        promoted_by_profile=False,
    ))

    args = type("Args", (), {
        "prompt": "git log 어떻게 써?",
        "repo": None,
        "module": None,
        "rag_backend": None,
        "reformulated_query": None,
    })()
    out = cli.build_rag_ask_output(args)

    assert "response_hints" in out
    assert out["response_hints"]["citation_markdown"] is None
    assert out["response_hints"]["citation_paths"] == []


def test_rag_ask_output_surfaces_augment_response_hints(tmp_path, monkeypatch):
    """When tier ∈ {1,2}, build_rag_ask_output should mirror
    augment's response_hints to the top-level rag-ask payload."""
    cli = _import_cli()
    from scripts.workbench.core.interactive_rag_router import RouterDecision
    from scripts.learning import integration as integration_mod

    _patch_classify(monkeypatch, RouterDecision(
        tier=1, mode="cheap", reason="domain definition",
        experience_level=None, override_active=False, blocked=False,
        promoted_by_profile=False,
    ))

    captured_hints = {
        "citation_markdown":
            "참고:\n- knowledge/cs/contents/spring/spring-bean-di-basics.md",
        "citation_paths":
            ["knowledge/cs/contents/spring/spring-bean-di-basics.md"],
    }

    def fake_augment(**kwargs):
        return {
            "by_learning_point": {},
            "by_fallback_key": {"definition": [
                {"path": "knowledge/cs/contents/spring/spring-bean-di-basics.md"}
            ]},
            "fallback_reason": None,
            "cs_categories_hit": ["spring"],
            "sidecar": None,
            "meta": {
                "latency_ms": 1, "rag_ready": True, "reason": "ready",
                "mode_used": "cheap", "backend": "r3",
                "category_filter_fallback": False,
            },
            "response_hints": captured_hints,
        }

    monkeypatch.setattr(integration_mod, "augment", fake_augment)

    args = type("Args", (), {
        "prompt": "Spring DI가 뭐야?",
        "repo": None,
        "module": None,
        "rag_backend": None,
        "reformulated_query": None,
    })()
    out = cli.build_rag_ask_output(args)

    assert out["decision"]["tier"] == 1
    assert out["response_hints"] == captured_hints
    # Citation markdown is paste-ready — exact string match guards the
    # AI session contract.
    assert out["response_hints"]["citation_markdown"].startswith("참고:\n- ")
