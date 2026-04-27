"""Tests for the v3 closed-loop adaptive response.

Two surfaces:
  * `interactive_rag_router.classify(learner_profile=...)` — three
    utilization rules + cold-start fallback + `promoted_by_profile` flag.
  * `learner_memory.build_learner_context()` — produces the
    `response_hints` block AI sessions are required to consume.

These tests are seeded directly off in-memory profile dicts so they run
without disk I/O.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core.interactive_rag_router import classify  # noqa: E402
from core.learner_memory import build_learner_context  # noqa: E402


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _profile(
    *,
    total_events: int = 10,
    experience_level: dict | None = None,
    mastered: list[dict] | None = None,
    uncertain: list[dict] | None = None,
    underexplored: list[dict] | None = None,
    current_module: str | None = "spring-core-1",
    current_stage: str | None = "spring-core",
    modules_progress: dict | None = None,
    next_recommendations: list[dict] | None = None,
) -> dict:
    return {
        "schema_version": "v3",
        "total_events": total_events,
        "experience_level": experience_level
        or {"current": "beginner", "confidence": "high", "rolling_window": "last_20_events", "evidence": []},
        "concepts": {
            "mastered": mastered or [],
            "uncertain": uncertain or [],
            "underexplored": underexplored or [],
            "encountered_count": {},
        },
        "activity": {
            "current_module": current_module,
            "current_stage": current_stage,
            "modules_progress": modules_progress
            or ({current_module: {"turns": total_events, "tests_passed": 0, "tests_failed": 0}} if current_module else {}),
            "events_by_type": {"rag_ask": total_events},
            "tier_distribution": {},
            "streak_days": 0,
            "last_active_at": _now_iso(),
        },
        "next_recommendations": next_recommendations or [],
        "preferences": {},
    }


class CompatibilityTests(unittest.TestCase):
    def test_classify_with_no_learner_profile_matches_v22_behavior(self) -> None:
        d = classify("Spring Bean이 뭐야?")
        self.assertEqual(d.tier, 1)
        self.assertFalse(d.promoted_by_profile)

    def test_cold_start_under_three_events_does_not_promote(self) -> None:
        prof = _profile(
            total_events=2,
            uncertain=[{
                "concept_id": "concept:spring/bean",
                "evidence": {"ask_count_7d": 4},
            }],
        )
        d = classify("Spring Bean이 뭐야?", learner_profile=prof)
        self.assertEqual(d.tier, 1)
        self.assertFalse(d.promoted_by_profile)


class TierPromotionTests(unittest.TestCase):
    def test_uncertain_concept_promotes_tier1_to_tier2(self) -> None:
        prof = _profile(
            uncertain=[{
                "concept_id": "concept:spring/bean",
                "evidence": {"ask_count_7d": 4},
            }],
        )
        d = classify("Spring Bean이 뭐야?", learner_profile=prof)
        self.assertEqual(d.tier, 2)
        self.assertEqual(d.mode, "full")
        self.assertTrue(d.promoted_by_profile)

    def test_uncertain_concept_not_in_prompt_does_not_promote(self) -> None:
        # Profile uncertain about Bean, but prompt is about DI — no overlap.
        prof = _profile(
            uncertain=[{
                "concept_id": "concept:spring/bean",
                "evidence": {"ask_count_7d": 4},
            }],
        )
        d = classify("DI가 뭐야?", learner_profile=prof)
        self.assertEqual(d.tier, 1)
        self.assertFalse(d.promoted_by_profile)

    def test_tier2_question_stays_tier2_without_promotion_flag(self) -> None:
        prof = _profile(
            uncertain=[{
                "concept_id": "concept:spring/bean",
                "evidence": {"ask_count_7d": 4},
            }],
        )
        d = classify("DI vs Service Locator 차이가 뭐예요", learner_profile=prof)
        self.assertEqual(d.tier, 2)
        self.assertFalse(d.promoted_by_profile)


class ExperienceLevelTests(unittest.TestCase):
    def test_high_confidence_beginner_overrides_neutral_prompt(self) -> None:
        # Prompt has no BEGINNER_HINT keywords, but profile says beginner.
        prof = _profile(
            experience_level={"current": "beginner", "confidence": "high",
                              "rolling_window": "last_20_events", "evidence": []},
        )
        d = classify("DI vs Service Locator 차이", learner_profile=prof)
        self.assertEqual(d.experience_level, "beginner")

    def test_low_confidence_does_not_override(self) -> None:
        prof = _profile(
            experience_level={"current": "beginner", "confidence": "low",
                              "rolling_window": "last_20_events", "evidence": []},
        )
        d = classify("DI vs Service Locator 차이", learner_profile=prof)
        # Low-confidence rolling level does not override; prompt-only inference returns None.
        self.assertIsNone(d.experience_level)


class LearnerContextTests(unittest.TestCase):
    def test_returns_none_for_zero_event_profile(self) -> None:
        prof = _profile(total_events=0)
        ctx = build_learner_context(prof, prompt="Bean이 뭐야?")
        self.assertIsNone(ctx)

    def test_skip_basics_for_mastered_concept(self) -> None:
        prof = _profile(
            mastered=[{"concept_id": "concept:spring/bean", "evidence": {}}],
        )
        ctx = build_learner_context(prof, prompt="Bean과 DI 차이")
        self.assertIn("concept:spring/bean", ctx["skip_basics_for"])
        self.assertIn("concept:spring/bean", ctx["response_hints"]["must_skip_explanations_of"])
        self.assertIn(
            "skip-basics(bean)",
            ctx["response_hints"]["header_required_tags"],
        )

    def test_deepen_for_uncertain_concept_with_must_include_phrase(self) -> None:
        prof = _profile(
            uncertain=[{
                "concept_id": "concept:spring/di",
                "evidence": {"ask_count_7d": 4},
            }],
        )
        ctx = build_learner_context(prof, prompt="DI 알려줘")
        self.assertIn("concept:spring/di", ctx["deepen_for"])
        phrases = ctx["response_hints"]["must_include_phrases"]
        self.assertTrue(any("4번째 질문" in p for p in phrases))
        self.assertEqual(ctx["response_hints"]["must_offer_next_action"], "drill:concept:spring/di")

    def test_underexplored_surfaces_in_context(self) -> None:
        prof = _profile(
            underexplored=[{
                "concept_id": "concept:spring/component-scan",
                "stage": "spring-core",
                "reason": "current stage gap",
            }],
        )
        ctx = build_learner_context(prof, prompt="Bean이 뭐야?")
        ids = {c["id"] for c in ctx["underexplored_in_current_stage"]}
        self.assertIn("concept:spring/component-scan", ids)

    def test_module_progress_attached(self) -> None:
        prof = _profile(
            modules_progress={
                "spring-core-1": {"turns": 8, "tests_passed": 3, "tests_failed": 1},
            },
        )
        ctx = build_learner_context(prof, prompt="Bean이 뭐야?")
        self.assertEqual(ctx["module_progress"]["tests_passed"], 3)
        self.assertEqual(ctx["tie_to_module"], "spring-core-1")


if __name__ == "__main__":
    unittest.main()
