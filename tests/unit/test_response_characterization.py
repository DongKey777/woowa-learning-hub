"""Characterization tests for build_response / render_response_markdown.

These pin the public output shape of the response module so the PR#6
decomposition (5-module sibling split with a thin façade) cannot
silently change behavior. The shape assertions are intentionally
structural — they cover the dict keys, type contracts, and markdown
heading order rather than exact strings, so legitimate copy edits in
templates do not break the suite.
"""

from __future__ import annotations

import unittest

from scripts.workbench.core.response import build_response, render_response_markdown


def _minimal_context(intent: str = "concept_explanation") -> dict:
    return {
        "repo": "test-repo",
        "prompt": "Repository 경계가 뭐야?",
        "primary_intent": intent,
        "primary_topic": "Repository",
        "topic_inference_reasons": ["prompt:repository"],
        "learner_profile": {"experience_level": "intermediate"},
        "git_context": {"diff_files": ["src/Cart.java"]},
        "current_pr": {"number": 42},
        "reviewer": "mentor-a",
        "mission_map_summary": ["JVM/Java mission with 5 packages"],
        "archive_status": {
            "data_confidence": "ready",
            "signals": {"total_prs": 30},
        },
        "learning_memory_profile": {
            "confidence": "medium",
            "dominant_learning_points": [
                {
                    "learning_point": "repository_boundary",
                    "label": "Repository 경계",
                    "count": 5,
                    "confidence": "medium",
                    "recency_status": "active",
                },
            ],
            "repeated_learning_points": [],
            "recent_learning_streak": {"learning_point": "repository_boundary", "count": 1},
            "repeated_question_patterns": [],
        },
    }


def _minimal_next_actions() -> dict:
    return {
        "next_actions": [
            {
                "priority": 1,
                "title": "Cart.java의 save 호출 경계 확인",
                "why": "도메인 복원과 저장 기술 세부가 섞였는지 본다",
                "action": {"kind": "open_artifact", "artifact": "packets/topic-repository.json"},
            },
        ],
    }


REQUIRED_TOP_LEVEL_KEYS = {
    "response_type", "response_role", "repo", "generated_at", "intent",
    "question_focus", "memory_policy", "experience_level", "level_notes",
    "usage_guidance", "summary", "answer", "teaching_points", "sections",
    "evidence", "next_actions", "postpone", "follow_up_question",
}


class BuildResponseShapeTest(unittest.TestCase):
    def test_top_level_keys_present(self) -> None:
        out = build_response(_minimal_context(), _minimal_next_actions())
        self.assertEqual(REQUIRED_TOP_LEVEL_KEYS - out.keys(), set())
        self.assertEqual(out["response_type"], "coach_response")
        self.assertEqual(out["response_role"], "reference")
        self.assertEqual(out["repo"], "test-repo")
        self.assertEqual(out["intent"], "concept_explanation")
        self.assertIn(out["memory_policy"]["mode"], {"neutral", "deepen", "broaden"})

    def test_sections_have_title_and_items(self) -> None:
        out = build_response(_minimal_context(), _minimal_next_actions())
        self.assertIsInstance(out["sections"], list)
        for section in out["sections"]:
            self.assertIn("title", section)
            self.assertIn("items", section)
            self.assertIsInstance(section["items"], list)

    def test_evidence_entries_have_type(self) -> None:
        out = build_response(_minimal_context(), _minimal_next_actions())
        self.assertIsInstance(out["evidence"], list)
        for entry in out["evidence"]:
            self.assertIn("type", entry)

    def test_seven_intent_templates_all_render(self) -> None:
        intents = [
            "review_triage", "concept_explanation", "peer_comparison",
            "pr_response", "reviewer_lens", "implementation_planning",
            "testing_strategy",
        ]
        for intent in intents:
            with self.subTest(intent=intent):
                out = build_response(_minimal_context(intent), _minimal_next_actions())
                self.assertEqual(out["intent"], intent)
                self.assertIsInstance(out["answer"], list)
                self.assertIsInstance(out["postpone"], list)
                self.assertTrue(out["follow_up_question"])

    def test_unknown_intent_falls_back(self) -> None:
        out = build_response(_minimal_context("totally_unknown"), _minimal_next_actions())
        self.assertEqual(out["intent"], "totally_unknown")
        self.assertTrue(out["sections"])


class RenderMarkdownShapeTest(unittest.TestCase):
    def test_render_contains_canonical_headings_in_order(self) -> None:
        out = build_response(_minimal_context(), _minimal_next_actions())
        md = render_response_markdown(out)
        expected_order = [
            "# Coach Response: test-repo",
            "## Intent",
            "## Summary",
            "## Teaching Points",
            "## Answer",
            "## Sections",
            "## Evidence",
            "## Next Actions",
            "## Postpone",
            "## Follow-up",
        ]
        last_pos = -1
        for heading in expected_order:
            pos = md.find(heading)
            self.assertGreaterEqual(pos, 0, f"heading {heading!r} missing")
            self.assertGreater(pos, last_pos, f"heading {heading!r} out of order")
            last_pos = pos


if __name__ == "__main__":
    unittest.main()
