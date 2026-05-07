"""Tests for rag-ask's feedback_hint output (P7.1 closed-loop wiring).

The CLI command `cmd_rag_ask` now appends ``feedback_hint`` to its
output JSON when retrieval returned hits. Verifies that the hint:

1. Is None when there are no hits (Tier 0, Tier 3 coach handoff,
   error response).
2. Builds a ready-to-paste shell command for each signal value.
3. Lists every unique doc path the augment surfaced (no duplicates).
4. Quotes prompts and repos safely (special characters / spaces).
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

import pytest


def _import_cli():
    import sys
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if str(repo_root / "scripts" / "workbench") not in sys.path:
        sys.path.insert(0, str(repo_root / "scripts" / "workbench"))
    from scripts.workbench import cli  # type: ignore  # noqa: WPS433
    return cli


def _args(prompt: str = "스프링 빈 뭐야?", repo: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(prompt=prompt, repo=repo)


# ---------------------------------------------------------------------------
# Empty / no-hit paths
# ---------------------------------------------------------------------------

def test_feedback_hint_none_when_hits_missing():
    cli = _import_cli()
    out = {"hits": None}
    assert cli._build_feedback_hint(_args(), out) is None


def test_feedback_hint_none_for_error_hits():
    cli = _import_cli()
    out = {"hits": {"error": "TypeError: x"}}
    # Error responses are dicts but have no by_learning_point / by_fallback_key
    assert cli._build_feedback_hint(_args(), out) is None


def test_feedback_hint_none_when_buckets_empty():
    cli = _import_cli()
    out = {"hits": {"by_learning_point": {}, "by_fallback_key": {}}}
    assert cli._build_feedback_hint(_args(), out) is None


# ---------------------------------------------------------------------------
# Standard hits
# ---------------------------------------------------------------------------

def test_feedback_hint_built_from_by_learning_point():
    cli = _import_cli()
    out = {"hits": {
        "by_learning_point": {
            "spring/bean": [
                {"path": "knowledge/cs/contents/spring/bean.md"},
                {"path": "knowledge/cs/contents/spring/component-scan.md"},
            ],
        },
        "by_fallback_key": {},
    }, "telemetry": {"source_event_id": "event-1234", "turn_id": "turn-event-1234"}}
    hint = cli._build_feedback_hint(_args(), out)
    assert hint is not None
    cmds = hint["commands"]
    assert set(cmds.keys()) == {"helpful", "not_helpful", "unclear"}
    # Both paths should be in the helpful command
    assert "knowledge/cs/contents/spring/bean.md" in cmds["helpful"]
    assert "knowledge/cs/contents/spring/component-scan.md" in cmds["helpful"]
    assert "--source-event-id event-1234" in cmds["helpful"]
    assert "--turn-id turn-event-1234" in cmds["helpful"]
    # Korean instructions present
    assert "한 줄" in hint["instructions"] or "신호" in hint["instructions"]


def test_feedback_hint_dedupes_paths_across_buckets():
    cli = _import_cli()
    out = {"hits": {
        "by_learning_point": {"x": [{"path": "a.md"}]},
        "by_fallback_key": {"k": [{"path": "a.md"}, {"path": "b.md"}]},
    }}
    hint = cli._build_feedback_hint(_args(), out)
    assert hint is not None
    # `a.md` should appear exactly once in the command, not twice
    assert hint["commands"]["helpful"].count("--hit ") == 2
    assert "a.md" in hint["commands"]["helpful"]
    assert "b.md" in hint["commands"]["helpful"]


def test_feedback_hint_quotes_prompt_with_special_chars():
    cli = _import_cli()
    out = {"hits": {
        "by_learning_point": {"x": [{"path": "a.md"}]},
        "by_fallback_key": {},
    }}
    args = _args(prompt="what's $PATH and `whoami`?")
    hint = cli._build_feedback_hint(args, out)
    assert hint is not None
    # shlex.quote produces a single-quoted form, never a raw $PATH
    cmd = hint["commands"]["helpful"]
    assert "$PATH" not in cmd or shlex.quote(args.prompt) in cmd


def test_feedback_hint_includes_repo_when_set():
    cli = _import_cli()
    out = {"hits": {
        "by_learning_point": {"x": [{"path": "a.md"}]},
        "by_fallback_key": {},
    }}
    hint = cli._build_feedback_hint(_args(repo="tobys-mission-1"), out)
    assert hint is not None
    for sig in ("helpful", "not_helpful", "unclear"):
        assert "--repo tobys-mission-1" in hint["commands"][sig]


def test_feedback_hint_omits_repo_when_unset():
    cli = _import_cli()
    out = {"hits": {
        "by_learning_point": {"x": [{"path": "a.md"}]},
        "by_fallback_key": {},
    }}
    hint = cli._build_feedback_hint(_args(repo=None), out)
    assert hint is not None
    assert "--repo" not in hint["commands"]["helpful"]


def test_feedback_hint_unclear_signal_does_not_include_hits():
    """The unclear command is for ambiguous cases — no doc selection
    needed, just record that retrieval was opaque to the learner."""
    cli = _import_cli()
    out = {"hits": {
        "by_learning_point": {"x": [{"path": "a.md"}, {"path": "b.md"}]},
        "by_fallback_key": {},
    }}
    hint = cli._build_feedback_hint(_args(), out)
    assert hint is not None
    assert "--hit" not in hint["commands"]["unclear"]
    # But helpful/not_helpful do include hit args
    assert "--hit" in hint["commands"]["helpful"]
    assert "--hit" in hint["commands"]["not_helpful"]


def test_response_quality_hint_uses_telemetry_and_expected_citations():
    cli = _import_cli()
    out = {
        "telemetry": {"source_event_id": "event-1234", "turn_id": "turn-event-1234"},
        "response_hints": {
            "citation_paths": [
                "contents/spring/aop-proxy-mechanism.md",
                "contents/spring/README.md",
            ],
        },
        "hits": None,
    }

    hint = cli._build_response_quality_hint(_args(prompt="AOP 프록시가 뭐야?"), out)

    assert hint is not None
    cmd = hint["command_template"]
    assert "--source-event-id event-1234" in cmd
    assert "--turn-id turn-event-1234" in cmd
    assert "--expected-citation contents/spring/aop-proxy-mechanism.md" in cmd
    assert "--response-file -" in cmd
    assert hint["expected_citation_paths"] == [
        "contents/spring/aop-proxy-mechanism.md",
        "contents/spring/README.md",
    ]


def test_cmd_rag_ask_passes_learner_context_to_augment(monkeypatch, capsys):
    cli = _import_cli()
    from core import interactive_rag_router, learner_memory  # type: ignore  # noqa: WPS433
    from scripts.learning import integration  # type: ignore  # noqa: WPS433
    from scripts.learning.rag import indexer as rag_indexer  # type: ignore  # noqa: WPS433

    expected_context = {"recent_rag_ask_context": ["concepts=concept:spring/bean"]}
    captured: dict = {}

    class ReadyReport:
        state = "ready"
        reason = "ready"
        corpus_hash = "fixture"
        index_manifest_hash = "fixture"
        next_command = None

    monkeypatch.setattr(
        interactive_rag_router,
        "classify",
        lambda *args, **kwargs: interactive_rag_router.RouterDecision(
            tier=1,
            mode="cheap",
            reason="fixture",
            experience_level="beginner",
            override_active=False,
        ),
    )
    monkeypatch.setattr(learner_memory, "load_learner_profile", lambda: {"total_events": 1})
    monkeypatch.setattr(
        learner_memory,
        "build_learner_context",
        lambda *args, **kwargs: expected_context,
    )
    monkeypatch.setattr(rag_indexer, "is_ready", lambda *args, **kwargs: ReadyReport())

    def fake_augment(**kwargs):
        captured.update(kwargs)
        return {"by_learning_point": {}, "by_fallback_key": {}, "cs_categories_hit": []}

    monkeypatch.setattr(integration, "augment", fake_augment)
    monkeypatch.setattr(cli, "_record_rag_ask_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "_record_routing_log", lambda *args, **kwargs: None)

    rc = cli.cmd_rag_ask(
        argparse.Namespace(prompt="Bean이 뭐야?", repo=None, module=None),
    )

    assert rc == 0
    assert captured["learner_context"] == expected_context
    out = capsys.readouterr().out
    assert '"learner_context"' in out
