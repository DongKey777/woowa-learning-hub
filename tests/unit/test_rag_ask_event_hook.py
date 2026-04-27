"""End-to-end coverage for `cmd_rag_ask` learner-event recording.

The classifier itself has its own unit tests. This file confirms the
side effect: every classification — Tier 0, Tier 3 blocked, override
short-circuits — appends one row to `state/learner/history.jsonl`.

Tier 1 / 2 paths are intentionally skipped because they require the
sentence-transformers index; an integration test in Phase 5 / 8 covers
those.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

import cli as workbench_cli  # noqa: E402  (after sys.path tweak)
from core import concept_catalog, learner_memory  # noqa: E402


class _RagAskHookCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name) / "learner"
        tmp_root.mkdir(parents=True, exist_ok=True)
        history = tmp_root / "history.jsonl"
        profile = tmp_root / "profile.json"
        summary = tmp_root / "summary.json"
        identity = tmp_root / "identity.json"
        self.history_path = history

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "hook-tester"

        def _restore_env() -> None:
            if prev_env is None:
                os.environ.pop("WOOWA_LEARNER_ID", None)
            else:
                os.environ["WOOWA_LEARNER_ID"] = prev_env
        self.addCleanup(_restore_env)

        patches = [
            patch.object(learner_memory, "LEARNER_DIR", tmp_root),
            patch.object(learner_memory, "ensure_learner_layout", lambda: tmp_root),
            patch.object(learner_memory, "learner_history_path", lambda: history),
            patch.object(learner_memory, "learner_profile_path", lambda: profile),
            patch.object(learner_memory, "learner_summary_path", lambda: summary),
            patch.object(learner_memory, "learner_identity_path", lambda: identity),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        concept_catalog.reset_cache()
        self._stdout = io.StringIO()
        self._stdout_patch = patch.object(sys, "stdout", self._stdout)
        self._stdout_patch.start()
        self.addCleanup(self._stdout_patch.stop)

    def _ask(self, prompt: str, *, repo: str | None = None, module: str | None = None) -> dict:
        ns = argparse.Namespace(prompt=prompt, repo=repo, module=module)
        rc = workbench_cli.cmd_rag_ask(ns)
        self.assertEqual(rc, 0)
        line = self._stdout.getvalue().strip().splitlines()[-1]
        return json.loads(line)

    def _events(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class RecordsEveryTier(_RagAskHookCase):
    def test_tier0_question_records_event_with_module(self) -> None:
        out = self._ask("Gradle 멀티 프로젝트 어떻게", module="spring-core-1")
        self.assertEqual(out["decision"]["tier"], 0)
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tier"], 0)
        self.assertFalse(events[0]["blocked"])
        self.assertEqual(events[0]["module_context"], "spring-core-1")
        self.assertEqual(events[0]["concept_ids"], [])

    def test_tier3_blocked_records_event(self) -> None:
        out = self._ask("내 PR 리뷰해줘")
        self.assertEqual(out["decision"]["tier"], 3)
        self.assertTrue(out["decision"]["blocked"])
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tier"], 3)
        self.assertTrue(events[0]["blocked"])

    def test_override_skip_records_tier0(self) -> None:
        out = self._ask("그냥 답해 Bean이 뭐야")
        self.assertEqual(out["decision"]["tier"], 0)
        self.assertTrue(out["decision"]["override_active"])
        self.assertEqual(self._events()[0]["tier"], 0)

    def test_concept_ids_extracted_for_known_concept(self) -> None:
        # Tier 0 (Gradle, no domain) but prompt mentions Bean — the
        # router still classifies as Tier 1 because Spring matches the
        # learning-concept tokens. So this is actually a Tier 1 with
        # blocked=False. We assert the event still records concept_ids.
        out = self._ask("Bean이 뭐야?")
        self.assertEqual(out["decision"]["tier"], 1)
        # Tier 1 path attempts augment(); on a fresh test with no real
        # state/cs_rag available it may surface an error. Either way the
        # event is recorded with concept_ids extracted from the prompt.
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["tier"], 1)
        self.assertIn("concept:spring/bean", events[0]["concept_ids"])


class FullWalkAggregatesTierDistribution(_RagAskHookCase):
    def test_five_turn_walk_populates_tier_distribution(self) -> None:
        prompts = [
            ("Gradle 어떻게 설정", None, 0),
            ("Bean이 뭐야?", "spring-core-1", 1),
            ("내 PR 리뷰해줘", None, 3),
            ("그냥 답해 트랜잭션 뭐야", None, 0),
            ("코치 모드 봐줘", None, 3),
        ]
        for prompt, module, _expected_tier in prompts:
            self._ask(prompt, module=module)
        events = self._events()
        self.assertEqual(len(events), 5)
        from core.learner_memory import recompute_learner_profile
        profile = recompute_learner_profile()
        dist = profile["activity"]["tier_distribution"]
        self.assertEqual(dist.get("0", 0), 2)
        self.assertEqual(dist.get("1", 0), 1)
        self.assertEqual(dist.get("3_blocked", 0), 2)


if __name__ == "__main__":
    unittest.main()
