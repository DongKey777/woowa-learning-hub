"""Phase 9.3 Step D — bin/rag-ask forces decision.tier = 0 on
tier_downgrade.

When ``integration.augment`` returns a result with
``response_hints.tier_downgrade = "corpus_gap_no_confident_match"``,
``build_rag_ask_output`` must replace the original tier 1/2 decision
with a synthetic tier-0 decision so the AI session reads a single
unambiguous signal: "no corpus context, fall back to training
knowledge with the disclaimer".

The hits payload is preserved (carries the empty buckets from
augment), but the top-level decision is overridden.
"""

from __future__ import annotations

import importlib
from pathlib import Path


def _import_cli():
    import sys
    repo_root = Path(__file__).resolve().parents[2]
    for entry in (repo_root, repo_root / "scripts" / "workbench"):
        if str(entry) not in sys.path:
            sys.path.insert(0, str(entry))
    from scripts.workbench import cli  # noqa: WPS433
    return cli


def _patch_classify(monkeypatch, decision):
    _import_cli()
    fake_classify = lambda prompt, **kwargs: decision  # noqa: E731
    for module_name in (
        "core.interactive_rag_router",
        "scripts.workbench.core.interactive_rag_router",
    ):
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            continue
        monkeypatch.setattr(mod, "classify", fake_classify)


def test_tier_downgrade_forces_decision_tier_to_0(tmp_path, monkeypatch):
    cli = _import_cli()
    from scripts.workbench.core.interactive_rag_router import RouterDecision
    from scripts.learning import integration as integration_mod

    # Router would normally classify as tier 1 (definition intent)
    _patch_classify(monkeypatch, RouterDecision(
        tier=1, mode="cheap", reason="domain definition",
        experience_level=None, override_active=False, blocked=False,
        promoted_by_profile=False,
    ))

    sentinel_augment = {
        "by_learning_point": {},
        "by_fallback_key": {},
        "fallback_reason": "corpus_gap_no_confident_match",
        "cs_categories_hit": [],
        "sidecar": None,
        "meta": {
            "latency_ms": 1, "rag_ready": True, "reason": "ready",
            "mode_used": "cheap", "backend": "r3",
            "category_filter_fallback": False,
            "fallback_reason": "corpus_gap_no_confident_match",
        },
        "response_hints": {
            "citation_markdown": None,
            "citation_paths": [],
            "tier_downgrade": "corpus_gap_no_confident_match",
            "fallback_disclaimer":
                "코퍼스에 이 주제의 신뢰할 만한 자료가 없어 일반 지식 기반으로 답한다.",
        },
    }
    monkeypatch.setattr(integration_mod, "augment", lambda **kwargs: sentinel_augment)

    args = type("Args", (), {
        "prompt": "고차원 벡터 양자화 RVQ vs PQ vs OPQ 차이가 뭐야?",
        "repo": None,
        "module": None,
        "rag_backend": None,
        "reformulated_query": None,
    })()
    out = cli.build_rag_ask_output(args)

    # Tier was forced from 1 to 0
    assert out["decision"]["tier"] == 0
    assert out["decision"]["reason"] == "corpus_gap_no_confident_match"
    assert out["decision"]["blocked"] is False

    # Surface the disclaimer + null citation so AI session can read
    assert out["response_hints"]["tier_downgrade"] == "corpus_gap_no_confident_match"
    assert "코퍼스" in out["response_hints"]["fallback_disclaimer"]
    assert out["response_hints"]["citation_markdown"] is None


def test_normal_tier_1_decision_preserved_when_no_downgrade(monkeypatch):
    cli = _import_cli()
    from scripts.workbench.core.interactive_rag_router import RouterDecision
    from scripts.learning import integration as integration_mod

    _patch_classify(monkeypatch, RouterDecision(
        tier=1, mode="cheap", reason="domain definition",
        experience_level=None, override_active=False, blocked=False,
        promoted_by_profile=False,
    ))

    normal_augment = {
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
        "response_hints": {
            "citation_markdown":
                "참고:\n- knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "citation_paths":
                ["knowledge/cs/contents/spring/spring-bean-di-basics.md"],
        },
    }
    monkeypatch.setattr(integration_mod, "augment", lambda **kwargs: normal_augment)

    args = type("Args", (), {
        "prompt": "Spring DI가 뭐야?",
        "repo": None,
        "module": None,
        "rag_backend": None,
        "reformulated_query": None,
    })()
    out = cli.build_rag_ask_output(args)

    # Tier 1 preserved — no downgrade
    assert out["decision"]["tier"] == 1
    assert out["decision"]["reason"] == "domain definition"
    # Citation is rendered as before
    assert out["response_hints"]["citation_markdown"].startswith("참고:\n- ")
