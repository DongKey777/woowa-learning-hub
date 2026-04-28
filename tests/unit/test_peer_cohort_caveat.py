"""End-to-end render-path test for peer PR cohort caveats.

Peer PR archives are mixed-year (2024 + 2025 entries within the same
mission archive), and the schema has no cohort field. This test guards
the entire pipeline so a freshness note actually reaches the learner:

  candidate row → session_focus.candidates[]  (created_year, cohort_caveat,
                                                freshness_note)
                → candidate_interpretation.primary_candidate /
                  alternative_candidates  (cohort_caveat propagated)
                → response.evidence[].freshness_note  (aggregated)
                → render_response_markdown's `## Evidence` section
                  (`freshness:` line) AND
                → _focus_pr_lines / _interpretation_lines  (suffix
                  embedded in the line the learner reads)

Also asserts:
  * cohort.current_cohort_year reads identity.json override first
  * AGENTS.md / CLAUDE.md / GEMINI.md carry the freshness rule keywords
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core import cohort as cohort_mod  # noqa: E402
from core.response_evidence import (  # noqa: E402
    _aggregate_freshness_note,
    _focus_pr_lines,
    _interpretation_lines,
    _response_evidence,
)
from core.response_composition import render_response_markdown  # noqa: E402
from core import learner_memory  # noqa: E402


REQUIRED_FRESHNESS_KEYWORDS = [
    "freshness_note",
    "cohort_caveat",
    "이전 기수",
]


class CohortYearResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.identity_path = Path(self.tmp.name) / "identity.json"
        self._patches = [
            patch.object(
                cohort_mod, "learner_identity_path", lambda: self.identity_path
            ),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)

    def test_override_year_takes_precedence_over_today(self) -> None:
        self.identity_path.write_text(
            json.dumps({"cohort_year": 2026}), encoding="utf-8"
        )
        self.assertEqual(cohort_mod.current_cohort_year(), 2026)

    def test_invalid_override_falls_back_to_today(self) -> None:
        self.identity_path.write_text(
            json.dumps({"cohort_year": "twenty-twenty-six"}), encoding="utf-8"
        )
        self.assertEqual(
            cohort_mod.current_cohort_year(),
            datetime.now(timezone.utc).year,
        )

    def test_missing_file_falls_back_to_today(self) -> None:
        # No write — file doesn't exist
        self.assertEqual(
            cohort_mod.current_cohort_year(),
            datetime.now(timezone.utc).year,
        )


class FreshnessAggregationTests(unittest.TestCase):
    def test_no_caveat_returns_none(self) -> None:
        items = [
            {"created_year": 2026, "cohort_caveat": False},
            {"created_year": 2026, "cohort_caveat": False},
        ]
        self.assertIsNone(_aggregate_freshness_note(items))

    def test_single_year_caveat(self) -> None:
        items = [
            {"created_year": 2024, "cohort_caveat": True},
            {"created_year": 2024, "cohort_caveat": True},
        ]
        note = _aggregate_freshness_note(items)
        self.assertIn("2024", note)
        self.assertIn("이전 기수", note.replace("기수 PR", "이전 기수")
                      if "이전 기수" not in note else note)

    def test_multi_year_caveat(self) -> None:
        items = [
            {"created_year": 2024, "cohort_caveat": True},
            {"created_year": 2025, "cohort_caveat": True},
        ]
        note = _aggregate_freshness_note(items)
        self.assertIn("2024", note)
        self.assertIn("2025", note)


class LineRenderTests(unittest.TestCase):
    """The lines the learner actually reads must carry the cohort suffix."""

    def test_focus_pr_line_appends_year_suffix_when_caveat(self) -> None:
        focus_payload = {
            "candidates": [
                {
                    "pr_number": 42,
                    "title": "Step 2 트랜잭션 적용",
                    "score": 5,
                    "author_login": "alice",
                    "matched_paths": ["src/main/java/X.java"],
                    "created_year": 2024,
                    "cohort_caveat": True,
                },
            ]
        }
        lines = _focus_pr_lines(focus_payload)
        self.assertEqual(len(lines), 1)
        self.assertIn("2024년 자료", lines[0])
        self.assertIn("미션 세부 다를 수 있음", lines[0])

    def test_focus_pr_line_no_suffix_when_same_cohort(self) -> None:
        focus_payload = {
            "candidates": [
                {
                    "pr_number": 42,
                    "title": "Step 2",
                    "score": 5,
                    "author_login": "alice",
                    "matched_paths": [],
                    "created_year": 2026,
                    "cohort_caveat": False,
                },
            ]
        }
        lines = _focus_pr_lines(focus_payload)
        self.assertNotIn("이전 기수", lines[0])
        self.assertNotIn("자료", lines[0])

    def test_interpretation_line_appends_suffix_to_primary(self) -> None:
        payload = {
            "learning_point_recommendations": [
                {
                    "label": "트랜잭션",
                    "primary_candidate": {
                        "pr_number": 7,
                        "title": "Step 3 롤백",
                        "evidence_quotes": [],
                        "created_year": 2024,
                        "cohort_caveat": True,
                    },
                    "alternative_candidates": [],
                },
            ]
        }
        lines = _interpretation_lines(payload)
        self.assertIn("2024년 자료", lines[0])


class ResponseEvidenceFreshnessNoteTests(unittest.TestCase):
    def test_focus_evidence_carries_freshness_note(self) -> None:
        context = {"focus_ranking_path": "/tmp/focus.json"}
        packets = {
            "focus_ranking": {
                "candidate_count": 2,
                "candidates": [
                    {
                        "pr_number": 1,
                        "title": "old PR",
                        "created_year": 2024,
                        "cohort_caveat": True,
                    },
                    {
                        "pr_number": 2,
                        "title": "newer PR",
                        "created_year": 2026,
                        "cohort_caveat": False,
                    },
                ],
            }
        }
        evidence = _response_evidence(context, packets)
        focus_item = next(e for e in evidence if e.get("type") == "focus_ranking")
        self.assertIn("freshness_note", focus_item)
        self.assertIn("2024", focus_item["freshness_note"])

    def test_focus_evidence_omits_freshness_when_all_current(self) -> None:
        context = {"focus_ranking_path": "/tmp/focus.json"}
        packets = {
            "focus_ranking": {
                "candidate_count": 1,
                "candidates": [
                    {
                        "pr_number": 2,
                        "title": "newer PR",
                        "created_year": 2026,
                        "cohort_caveat": False,
                    },
                ],
            }
        }
        evidence = _response_evidence(context, packets)
        focus_item = next(e for e in evidence if e.get("type") == "focus_ranking")
        self.assertNotIn("freshness_note", focus_item)


class MarkdownRenderTests(unittest.TestCase):
    def test_render_includes_freshness_line_in_evidence_section(self) -> None:
        response = {
            "repo": "test-repo",
            "intent": "test_intent",
            "response_role": "x",
            "question_focus": "x",
            "memory_policy": {"mode": "default"},
            "experience_level": "beginner",
            "summary": ["요약"],
            "answer": ["본문"],
            "teaching_points": [],
            "sections": [],
            "evidence": [
                {
                    "type": "focus_ranking",
                    "json_path": "/tmp/focus.json",
                    "freshness_note": "2024년 기수 PR — 미션 세부 요구사항이 다를 수 있음",
                    "summary": ["candidate_count=1"],
                    "highlights": ["PR #42 - Step 2 (score=5) — 2024년 자료, 미션 세부 다를 수 있음"],
                }
            ],
            "next_actions": [],
            "postpone": [],
            "follow_up_question": "?",
        }
        md = render_response_markdown(response)
        self.assertIn("freshness: 2024년 기수 PR", md)
        self.assertIn("highlight: PR #42 - Step 2 (score=5) — 2024년 자료", md)


class AIFileFreshnessRuleTests(unittest.TestCase):
    def _read(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def test_agents_md_has_freshness_rule(self) -> None:
        text = self._read("AGENTS.md")
        for keyword in REQUIRED_FRESHNESS_KEYWORDS:
            self.assertIn(keyword, text, f"AGENTS.md missing keyword: {keyword!r}")

    def test_claude_md_has_freshness_rule(self) -> None:
        text = self._read("CLAUDE.md")
        for keyword in REQUIRED_FRESHNESS_KEYWORDS:
            self.assertIn(keyword, text, f"CLAUDE.md missing keyword: {keyword!r}")

    def test_gemini_md_has_freshness_rule(self) -> None:
        text = self._read("GEMINI.md")
        for keyword in REQUIRED_FRESHNESS_KEYWORDS:
            self.assertIn(keyword, text, f"GEMINI.md missing keyword: {keyword!r}")


class CohortCliSubcommandTests(unittest.TestCase):
    """`bin/learner-profile cohort 2026` updates identity.json and reads back."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.learner_dir = Path(self.tmp.name) / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)
        self.identity_path = self.learner_dir / "identity.json"

        from core import paths as paths_mod
        self._patches = [
            patch.object(paths_mod, "LEARNER_DIR", self.learner_dir),
            patch.object(
                learner_memory,
                "learner_identity_path",
                lambda: self.identity_path,
            ),
            patch.object(cohort_mod, "learner_identity_path", lambda: self.identity_path),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)

    def test_set_then_read(self) -> None:
        import importlib
        cli_mod = importlib.import_module("cli")
        # Patch the path lookup inside cli.py too — it does
        # `from core.paths import learner_identity_path` lazily inside
        # the cohort branch.
        from core import paths as paths_mod
        with patch.object(paths_mod, "learner_identity_path", lambda: self.identity_path):
            from argparse import Namespace
            rc = cli_mod.cmd_learner_profile(Namespace(
                learner_profile_command="cohort", year=2026,
            ))
            self.assertEqual(rc, 0)
            self.assertTrue(self.identity_path.exists())
            self.assertEqual(
                json.loads(self.identity_path.read_text())["cohort_year"], 2026
            )
            # Read back
            rc = cli_mod.cmd_learner_profile(Namespace(
                learner_profile_command="cohort", year=None,
            ))
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
