"""End-to-end personalization scenarios from plan v3 §Phase 6.

These tests run the FULL closed loop on seeded `history.jsonl` fixtures:

    fixture history → recompute_learner_profile()
                    → classify(prompt, learner_profile=...)
                    → build_learner_context(...)

Each scenario asserts the *user-visible* effect, not just one module's
output, so a regression anywhere in the chain is caught.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core import concept_catalog, learner_memory  # noqa: E402
from core.interactive_rag_router import classify  # noqa: E402


def _iso(days_ago: float = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(
        timespec="seconds"
    )


def _rag_ask(*, prompt: str, concepts: list[str], days_ago: float = 0,
             tier: int = 1, blocked: bool = False, level: str | None = "beginner",
             module: str | None = "spring-core-1") -> dict:
    ts = _iso(days_ago)
    return {
        "event_type": "rag_ask",
        "event_id": f"r-{prompt[:6]}-{ts}",
        "ts": ts,
        "learner_id": "scenario",
        "repo_context": None,
        "module_context": module,
        "concept_ids": list(concepts),
        "prompt": prompt,
        "question_fingerprint": prompt.lower(),
        "tier": tier,
        "rag_mode": "cheap" if tier == 1 else None,
        "experience_level_inferred": level,
        "category_hits": [],
        "top_paths": [],
        "rag_ready": True,
        "blocked": blocked,
    }


def _drill(*, score: int, concept: str, days_ago: float = 0) -> dict:
    ts = _iso(days_ago)
    return {
        "event_type": "drill_answer",
        "event_id": f"d-{concept[:6]}-{ts}",
        "ts": ts,
        "learner_id": "scenario",
        "concept_ids": [concept],
        "drill_session_id": f"sid-{ts}",
        "linked_learning_point": "x",
        "total_score": score,
        "dimensions": {},
        "weak_tags": [],
    }


def _test_result(*, concept: str, passed: bool, days_ago: float = 0,
                 module: str = "spring-core-1",
                 match_mode: str = "strict") -> dict:
    ts = _iso(days_ago)
    return {
        "event_type": "test_result",
        "event_id": f"t-{concept[:6]}-{ts}",
        "ts": ts,
        "learner_id": "scenario",
        "concept_ids": [concept],
        "concept_match_mode": match_mode,
        "module": module,
        "test_class": "T",
        "test_method": "m",
        "pass": passed,
    }


def _coach_run(*, concepts: list[str], negative: bool = False, days_ago: float = 0) -> dict:
    ts = _iso(days_ago)
    return {
        "event_type": "coach_run",
        "event_id": f"c-{ts}",
        "ts": ts,
        "learner_id": "scenario",
        "repo_context": "spring-roomescape-admin",
        "pr_number": 1,
        "concept_ids": list(concepts),
        "primary_learning_points": ["transaction_consistency"],
        "had_negative_feedback": negative,
    }


class _ScenarioBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.learner_dir = tmp_root / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)

        history = self.learner_dir / "history.jsonl"
        profile = self.learner_dir / "profile.json"
        summary = self.learner_dir / "summary.json"
        identity = self.learner_dir / "identity.json"
        self.history_path = history

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "scenario"

        def _restore_env() -> None:
            if prev_env is None:
                os.environ.pop("WOOWA_LEARNER_ID", None)
            else:
                os.environ["WOOWA_LEARNER_ID"] = prev_env
        self.addCleanup(_restore_env)

        for p in [
            patch.object(learner_memory, "LEARNER_DIR", self.learner_dir),
            patch.object(learner_memory, "ensure_learner_layout", lambda: self.learner_dir),
            patch.object(learner_memory, "learner_history_path", lambda: history),
            patch.object(learner_memory, "learner_profile_path", lambda: profile),
            patch.object(learner_memory, "learner_summary_path", lambda: summary),
            patch.object(learner_memory, "learner_identity_path", lambda: identity),
        ]:
            p.start()
            self.addCleanup(p.stop)
        concept_catalog.reset_cache()

    def _seed(self, events: list[dict]) -> dict:
        with self.history_path.open("w", encoding="utf-8") as fh:
            for event in events:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        return learner_memory.recompute_learner_profile()


class PlanV3Scenarios(_ScenarioBase):
    def test_bean_repeated_4x_promotes_to_tier2(self) -> None:
        prof = self._seed([
            _rag_ask(prompt="Bean이 뭐야?", concepts=["concept:spring/bean"], days_ago=0.4),
            _rag_ask(prompt="Bean 다시 알려줘", concepts=["concept:spring/bean"], days_ago=0.3),
            _rag_ask(prompt="Bean 헷갈려", concepts=["concept:spring/bean"], days_ago=0.2),
            _rag_ask(prompt="Bean 한 번 더", concepts=["concept:spring/bean"], days_ago=0.1),
        ])
        decision = classify("Bean이 뭐야?", learner_profile=prof)
        self.assertEqual(decision.tier, 2)
        self.assertTrue(decision.promoted_by_profile)

    def test_mastered_concept_skipped_in_response(self) -> None:
        prof = self._seed([
            _drill(score=9, concept="concept:spring/bean", days_ago=2),
            _drill(score=8, concept="concept:spring/bean", days_ago=1),
            _test_result(concept="concept:spring/bean", passed=True, days_ago=0),
        ])
        ctx = learner_memory.build_learner_context(
            prof,
            prompt="Bean과 DI 차이",
        )
        self.assertIn("concept:spring/bean", ctx["skip_basics_for"])

    def test_underexplored_concept_appears_in_recommendation(self) -> None:
        prof = self._seed([
            _rag_ask(prompt="Bean이 뭐야?", concepts=["concept:spring/bean"], days_ago=0),
        ])
        ids = {
            c["concept_id"] for c in prof["concepts"]["underexplored"]
        }
        # Spring-core stage has 5 concepts; touched bean → 4 remain.
        self.assertIn("concept:spring/component-scan", ids)
        self.assertIn("concept:spring/configuration", ids)
        # And the suggestion list mentions one of them as `concept` type.
        suggestion_concepts = {
            s["value"] for s in prof["next_recommendations"] if s["type"] == "concept"
        }
        self.assertTrue(suggestion_concepts)

    def test_test_failure_triggers_uncertainty(self) -> None:
        prof = self._seed([
            _test_result(concept="concept:spring/bean", passed=False, days_ago=0),
        ])
        uncertain_ids = {c["concept_id"] for c in prof["concepts"]["uncertain"]}
        self.assertIn("concept:spring/bean", uncertain_ids)

    def test_streak_increments_consecutive_days(self) -> None:
        prof = self._seed([
            _rag_ask(prompt="day-2", concepts=["concept:spring/bean"], days_ago=1),
            _rag_ask(prompt="day-1", concepts=["concept:spring/bean"], days_ago=0),
        ])
        self.assertGreaterEqual(prof["activity"]["streak_days"], 2)

    def test_module_progress_tracks_test_results(self) -> None:
        prof = self._seed([
            _test_result(concept="concept:spring/bean", passed=True, days_ago=0),
            _test_result(concept="concept:spring/di", passed=False, days_ago=0),
        ])
        progress = prof["activity"]["modules_progress"]["spring-core-1"]
        self.assertEqual(progress["tests_passed"], 1)
        self.assertEqual(progress["tests_failed"], 1)

    def test_cold_start_no_profile_falls_back_to_v22(self) -> None:
        decision = classify("Spring Bean이 뭐야?", learner_profile=None)
        self.assertEqual(decision.tier, 1)
        self.assertFalse(decision.promoted_by_profile)

    def test_pr_negative_feedback_blocks_mastered_status(self) -> None:
        prof = self._seed([
            _drill(score=9, concept="concept:spring/transactional", days_ago=2),
            _drill(score=8, concept="concept:spring/transactional", days_ago=1),
            _coach_run(concepts=["concept:spring/transactional"], negative=True, days_ago=0),
        ])
        mastered_ids = {c["concept_id"] for c in prof["concepts"]["mastered"]}
        self.assertNotIn("concept:spring/transactional", mastered_ids)


if __name__ == "__main__":
    unittest.main()
