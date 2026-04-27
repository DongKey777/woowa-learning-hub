"""Regression tests for `suggest_next()` priority logic."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core.concept_catalog import load_catalog, reset_cache  # noqa: E402
from core.learner_memory import suggest_next  # noqa: E402


def _profile(**kwargs) -> dict:
    base: dict = {
        "schema_version": "v3",
        "total_events": 5,
        "experience_level": {"current": "beginner", "confidence": "high",
                             "rolling_window": "last_20_events", "evidence": []},
        "concepts": {
            "mastered": [], "uncertain": [], "underexplored": [],
            "encountered_count": {},
        },
        "activity": {"current_module": "spring-core-1",
                     "current_stage": "spring-core",
                     "modules_progress": {}},
        "next_recommendations": [],
        "preferences": {},
    }
    base["concepts"].update(kwargs.get("concepts", {}))
    if "current_stage" in kwargs:
        base["activity"]["current_stage"] = kwargs["current_stage"]
    if "current_module" in kwargs:
        base["activity"]["current_module"] = kwargs["current_module"]
    return base


class SuggestNextTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_cache()
        self.catalog = load_catalog()

    def test_empty_profile_returns_no_suggestions(self) -> None:
        self.assertEqual(suggest_next(None, self.catalog), [])
        self.assertEqual(suggest_next({}, self.catalog), [])

    def test_uncertain_no_drill_yields_drill_recommendation(self) -> None:
        prof = _profile(concepts={
            "uncertain": [
                {"concept_id": "concept:spring/di",
                 "evidence": {"ask_count_7d": 4, "last_drill_score": None}},
            ],
        })
        suggestions = suggest_next(prof, self.catalog)
        self.assertTrue(suggestions)
        top = suggestions[0]
        self.assertEqual(top["type"], "drill")
        self.assertEqual(top["value"], "concept:spring/di")
        self.assertGreater(top["priority"], 0.7)

    def test_uncertain_with_drill_score_skips_drill_rec(self) -> None:
        prof = _profile(concepts={
            "uncertain": [
                {"concept_id": "concept:spring/di",
                 "evidence": {"ask_count_7d": 4, "last_drill_score": 7}},
            ],
        })
        suggestions = suggest_next(prof, self.catalog)
        self.assertFalse(any(s["type"] == "drill" for s in suggestions))

    def test_underexplored_in_current_stage_surfaces(self) -> None:
        prof = _profile(concepts={
            "underexplored": [
                {"concept_id": "concept:spring/component-scan",
                 "stage": "spring-core", "reason": "stage gap"},
            ],
        })
        suggestions = suggest_next(prof, self.catalog)
        ids = {s["value"] for s in suggestions if s["type"] == "concept"}
        self.assertIn("concept:spring/component-scan", ids)

    def test_next_module_priority_when_prereqs_met(self) -> None:
        prof = _profile(
            concepts={
                "mastered": [
                    {"concept_id": "concept:spring/bean", "evidence": {}},
                    {"concept_id": "concept:spring/di", "evidence": {}},
                    {"concept_id": "concept:spring/ioc", "evidence": {}},
                    {"concept_id": "concept:spring/dispatcher-servlet", "evidence": {}},
                    {"concept_id": "concept:spring/handler-mapping", "evidence": {}},
                    {"concept_id": "concept:spring/handler-adapter", "evidence": {}},
                    {"concept_id": "concept:spring/jdbc-template", "evidence": {}},
                    {"concept_id": "concept:spring/transactional", "evidence": {}},
                ],
            },
            current_stage="spring-jdbc",
            current_module="spring-jdbc-1",
        )
        suggestions = suggest_next(prof, self.catalog)
        module_recs = [s for s in suggestions if s["type"] == "module"]
        self.assertTrue(module_recs)
        self.assertEqual(module_recs[0]["value"], "spring-data-jpa-1")
        self.assertEqual(module_recs[0]["blockers"], [])

    def test_next_module_blocked_when_prereqs_missing(self) -> None:
        prof = _profile(
            current_stage="spring-jdbc",
            current_module="spring-jdbc-1",
        )
        suggestions = suggest_next(prof, self.catalog)
        module_recs = [s for s in suggestions if s["type"] == "module"]
        self.assertTrue(module_recs)
        # Prereq for jpa-entity is transactional — not mastered → blocker.
        self.assertEqual(module_recs[0]["value"], "spring-data-jpa-1")
        self.assertIn("concept:spring/transactional", module_recs[0]["blockers"])
        self.assertLess(module_recs[0]["priority"], 0.7)

    def test_max_n_truncates(self) -> None:
        prof = _profile(concepts={
            "uncertain": [
                {"concept_id": "concept:spring/di",
                 "evidence": {"ask_count_7d": 4, "last_drill_score": None}},
            ],
            "underexplored": [
                {"concept_id": "concept:spring/component-scan",
                 "stage": "spring-core", "reason": "stage gap"},
                {"concept_id": "concept:spring/configuration",
                 "stage": "spring-core", "reason": "stage gap"},
            ],
        })
        suggestions = suggest_next(prof, self.catalog, max_n=2)
        self.assertEqual(len(suggestions), 2)


if __name__ == "__main__":
    unittest.main()
