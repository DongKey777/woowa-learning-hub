"""Schema-level guards for the tightened learning-memory schemas.

PR#3 added items structure to ``learning-memory-profile.schema.json`` and
``learning-memory-summary.schema.json``. These tests both:

1. Verify that real ``memory.py`` output continues to validate (golden path).
2. Verify that drift introduces clear errors (recency_status missing,
   confidence enum violation, weighted_count of wrong type).
"""

from __future__ import annotations

import copy
import unittest

from scripts.workbench.core.schema_validation import (
    SchemaValidationError,
    validate_payload,
)


_GOOD_PROFILE = {
    "profile_type": "learning_memory_profile",
    "repo": "demo-repo",
    "updated_at": "2026-04-14T00:00:00+00:00",
    "total_sessions": 3,
    "confidence": "low",
    "dominant_topics": [],
    "dominant_intents": [],
    "dominant_learning_points": [
        {
            "learning_point": "naming.intent",
            "label": "이름으로 의도 표현",
            "count": 3,
            "weighted_count": 2.4,
            "confidence": "medium",
            "recency_status": "active",
        }
    ],
    "repeated_learning_points": [
        {
            "learning_point": "naming.intent",
            "label": None,
            "count": 2,
            "weighted_count": 1.0,
            "confidence": "low",
            "recency_status": "cooling",
        }
    ],
    "underexplored_learning_points": [
        {"learning_point": "tdd.refactor", "label": None, "count": 0}
    ],
    "recent_learning_streak": None,
    "repeated_question_patterns": [],
    "open_follow_up_queue": [],
}


_GOOD_SUMMARY = {
    "summary_type": "learning_memory_summary",
    "repo": "demo-repo",
    "updated_at": "2026-04-14T00:00:00+00:00",
    "total_sessions": 3,
    "top_topics": [{"topic": "naming", "count": 2}],
    "top_intents": [{"intent": "ask", "count": 3}],
    "top_learning_points": [
        {
            "learning_point": "naming.intent",
            "count": 3,
            "weighted_count": 2.4,
            "confidence": "medium",
        }
    ],
    "repeated_learning_points": [],
    "learning_point_confidence": [
        {
            "learning_point": "naming.intent",
            "count": 3,
            "weighted_count": 2.4,
            "confidence": "medium",
        }
    ],
    "top_reviewers": [{"reviewer": "alice", "count": 4}],
    "recurring_paths": [{"path": "src/Foo.kt", "count": 2}],
    "recent_questions": ["what about naming?"],
    "recent_learning_points": [],
    "repeated_question_patterns": [],
    "open_follow_ups": [],
    "recent_sessions": [],
    "weighted_learning_points": [
        {
            "learning_point": "naming.intent",
            "count": 3,
            "weighted_count": 2.4,
            "confidence": "medium",
        }
    ],
}


class LearningMemoryProfileSchemaTest(unittest.TestCase):
    def test_golden_payload_validates(self) -> None:
        validate_payload("learning-memory-profile", _GOOD_PROFILE)

    def test_missing_recency_status_rejected(self) -> None:
        bad = copy.deepcopy(_GOOD_PROFILE)
        del bad["dominant_learning_points"][0]["recency_status"]
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_payload("learning-memory-profile", bad)
        self.assertIn("recency_status", str(ctx.exception))

    def test_invalid_recency_status_rejected(self) -> None:
        bad = copy.deepcopy(_GOOD_PROFILE)
        bad["dominant_learning_points"][0]["recency_status"] = "fresh"
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_payload("learning-memory-profile", bad)
        self.assertIn("recency_status", str(ctx.exception))

    def test_weighted_count_must_be_number(self) -> None:
        bad = copy.deepcopy(_GOOD_PROFILE)
        bad["dominant_learning_points"][0]["weighted_count"] = "2.4"
        with self.assertRaises(SchemaValidationError):
            validate_payload("learning-memory-profile", bad)

    def test_label_may_be_null(self) -> None:
        ok = copy.deepcopy(_GOOD_PROFILE)
        ok["dominant_learning_points"][0]["label"] = None
        validate_payload("learning-memory-profile", ok)


class LearningMemorySummarySchemaTest(unittest.TestCase):
    def test_golden_payload_validates(self) -> None:
        validate_payload("learning-memory-summary", _GOOD_SUMMARY)

    def test_top_topics_requires_topic_field(self) -> None:
        bad = copy.deepcopy(_GOOD_SUMMARY)
        bad["top_topics"] = [{"name": "naming", "count": 2}]
        with self.assertRaises(SchemaValidationError):
            validate_payload("learning-memory-summary", bad)

    def test_confidence_enum_enforced(self) -> None:
        bad = copy.deepcopy(_GOOD_SUMMARY)
        bad["top_learning_points"][0]["confidence"] = "extreme"
        with self.assertRaises(SchemaValidationError):
            validate_payload("learning-memory-summary", bad)

    def test_weighted_count_accepts_int_and_float(self) -> None:
        ok = copy.deepcopy(_GOOD_SUMMARY)
        ok["weighted_learning_points"][0]["weighted_count"] = 3
        validate_payload("learning-memory-summary", ok)


if __name__ == "__main__":
    unittest.main()
