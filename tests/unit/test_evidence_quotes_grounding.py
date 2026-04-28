"""T2 — _evidence_quotes filter regression for cascade incident.

Pins the fix where retrieval-vocabulary-driven matched_terms intersection
was the sole gate, dropping all learning points except testing_strategy.

See plan: /Users/idonghun/.claude/plans/gentle-conjuring-spring.md

Commit 1 of the PR contains behavior cases only (1, 2, 4, 5, 6, 7, 8) so
the test file is collection-safe before helpers exist. Commit 2 adds the
helper imports and Cases 3a/3b that exercise _extract_point_terms directly.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.workbench.core.candidate_interpretation import (
    _evidence_quotes,
    _extract_point_terms,
    _sample_matches_point,
    build_candidate_interpretation,
)


def _comment_sample(body: str, matched_terms: list[str], **extra) -> dict:
    return {
        "user_login": extra.get("user_login", "mentor"),
        "path": extra.get("path"),
        "line": extra.get("line"),
        "matched_terms": matched_terms,
        "body_excerpt": body,
    }


def _candidate(samples: list[dict] | None = None, focus_excerpt: str = "") -> dict:
    return {
        "pr_number": 99,
        "title": "fixture PR",
        "author_login": "crew",
        "focus_excerpt": focus_excerpt,
        "matched_comment_samples": samples or [],
        "matched_review_samples": [],
        "matched_issue_comment_samples": [],
        "matched_paths": [],
        "path_examples": [],
    }


class EvidenceQuotesFallbackTest(unittest.TestCase):
    """Case 1 — the smoking gun: responsibility_boundary recovers via body scan."""

    def test_responsibility_boundary_recovers_via_body_scan(self) -> None:
        sample = _comment_sample(
            body="controller와 service의 책임 분리를 어디서 잡으시나요?",
            matched_terms=["domain", "test"],
        )
        candidate = _candidate(samples=[sample])
        point = {
            "id": "responsibility_boundary",
            "reasons": ["text:책임", "text:controller", "text:분리"],
        }
        quotes = _evidence_quotes(candidate, point)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["source"], "review_comment")


class EvidenceQuotesFastPathTest(unittest.TestCase):
    """Case 2 — fast path unchanged when matched_terms intersect."""

    def test_testing_strategy_unchanged_when_matched_terms_intersect(self) -> None:
        sample = _comment_sample(
            body="테스트 전략을 어떻게 잡으셨나요?",
            matched_terms=["test", "테스트"],
        )
        candidate = _candidate(samples=[sample])
        point = {
            "id": "testing_strategy",
            "reasons": ["text:test", "text:테스트", "profile:underexplored"],
        }
        quotes = _evidence_quotes(candidate, point)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["source"], "review_comment")


class PointTermsSanitizationTest(unittest.TestCase):
    """Case 3 — profile-only reasons must NOT leak into body-scan.

    Production scenarios are usually mixed (text + profile reasons), so
    test the mixed case as the primary; profile-only is a corner case kept
    as a secondary smoke check.
    """

    def test_profile_only_reasons_yield_empty_point_terms(self) -> None:
        # 보조 case — profile-only reasons (production 에선 드뭄)
        point = {
            "id": "responsibility_boundary",
            "reasons": ["profile:underexplored", "profile:repeated"],
        }
        terms = _extract_point_terms(point)
        self.assertEqual(terms, set())

    def test_mixed_reasons_strip_profile_but_keep_text_path(self) -> None:
        # Primary scenario — text/path + profile mixed reasons.
        # profile suffix ("underexplored", "repeated", "active", "dominant")
        # must NOT make it into point_terms; otherwise body-scan would
        # falsely match comments containing those literal words.
        point = {
            "id": "testing_strategy",
            "reasons": [
                "text:test",
                "text:테스트",
                "path:test",
                "profile:underexplored",
                "profile:repeated",
            ],
        }
        terms = _extract_point_terms(point)
        self.assertIn("test", terms)
        self.assertIn("테스트", terms)
        self.assertNotIn("underexplored", terms)
        self.assertNotIn("repeated", terms)
        self.assertNotIn("active", terms)
        self.assertNotIn("dominant", terms)

        # Also verify at the filter layer: a body containing the profile
        # suffix words must NOT match when no real keyword is present.
        sample = _comment_sample(
            body="이 영역은 underexplored 인데 repeated 한 측면이 있습니다",
            matched_terms=["domain"],  # test 와 무관
        )
        # Sanity: helper-level check
        self.assertFalse(_sample_matches_point(sample, terms))
        # End-to-end: _evidence_quotes returns empty (and pr_body fallback
        # is not triggered because focus_excerpt is empty).
        candidate = _candidate(samples=[sample])
        quotes = _evidence_quotes(candidate, point)
        self.assertEqual(quotes, [])


class EmptyBodyTest(unittest.TestCase):
    """Case 4 — empty body_excerpt + non-overlapping matched_terms drops gracefully."""

    def test_empty_body_excerpt_does_not_match(self) -> None:
        sample = _comment_sample(body="", matched_terms=["domain"])
        candidate = _candidate(samples=[sample])
        point = {
            "id": "responsibility_boundary",
            "reasons": ["text:책임", "text:controller"],
        }
        quotes = _evidence_quotes(candidate, point)
        # No matched_terms intersection AND empty body → reject.
        # Falls through to pr_body fallback (focus_excerpt is "" so no fallback).
        self.assertEqual(quotes, [])


class PrBodyGroundingStillStrictTest(unittest.TestCase):
    """Case 5 — pr_body fallback alone is still NOT review-grounded.

    _evidence_quotes itself still emits the pr_body source when no comment
    samples qualify; the strict check happens in _has_review_grounding which
    filters out pr_body. This test pins the source emission contract;
    the recommendations builder honors that contract elsewhere.
    """

    def test_pr_body_grounding_still_emitted_but_not_review_grounded(self) -> None:
        candidate = _candidate(
            samples=[],
            focus_excerpt="repository 경계를 다시 봐야 합니다",
        )
        point = {"id": "repository_boundary", "reasons": ["text:repository"]}
        quotes = _evidence_quotes(candidate, point)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["source"], "pr_body")


class QuoteCapTest(unittest.TestCase):
    """Case 6 — len(quotes) >= 3 break still respected after fallback."""

    def test_quote_cap_of_three_respected(self) -> None:
        samples = [
            _comment_sample(body=f"책임 분리 {i}", matched_terms=["domain"])
            for i in range(5)
        ]
        candidate = _candidate(samples=samples)
        point = {
            "id": "responsibility_boundary",
            "reasons": ["text:책임", "text:분리"],
        }
        quotes = _evidence_quotes(candidate, point)
        self.assertEqual(len(quotes), 3)


class PassThroughBehaviorTest(unittest.TestCase):
    """Case 7 (optional) — empty matched_terms still passes through."""

    def test_path_only_match_with_empty_matched_terms_still_passes(self) -> None:
        sample = _comment_sample(body="아무 내용이나", matched_terms=[])
        candidate = _candidate(samples=[sample])
        point = {
            "id": "responsibility_boundary",
            "reasons": ["text:책임", "text:controller"],
        }
        quotes = _evidence_quotes(candidate, point)
        self.assertEqual(len(quotes), 1)


class PipelineIntegrationTest(unittest.TestCase):
    """Case 8 — pipeline-level: build_candidate_interpretation 까지 통과.

    Helper unit tests alone are insufficient — quote 가 생겨도 recommendations
    builder 의 sort + grounded filter 단계에서 drop 될 수 있음. pipeline
    전체까지 회귀 보호.

    build_candidate_interpretation writes to
    state/repos/<repo_name>/contexts/<mode>-candidate-interpretation.json,
    so monkeypatch repo_context_dir to a tmp dir to avoid workspace pollution.
    """

    def setUp(self) -> None:
        from scripts.workbench.core import candidate_interpretation as ci_mod

        self._tmpdir = tempfile.TemporaryDirectory()
        tmp_path = Path(self._tmpdir.name)
        self._patcher = mock.patch.object(
            ci_mod,
            "repo_context_dir",
            lambda repo_name: tmp_path / repo_name / "contexts",
        )
        self._patcher.start()
        (tmp_path / "fixture-repo" / "contexts").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._patcher.stop()
        self._tmpdir.cleanup()

    def test_responsibility_boundary_appears_in_recommendations_via_pipeline(self) -> None:
        focus_payload = {
            "candidates": [
                {
                    "pr_number": 99,
                    "title": "[1-3단계] crew mission",
                    "author_login": "crew",
                    "score": 30,
                    "focus_excerpt": "controller / domain / repository 책임 분리 설계",
                    "matched_paths": ["src/main/java/roomescape/controller/Foo.java"],
                    "path_examples": [],
                    "matched_comment_samples": [
                        {
                            "user_login": "mentor",
                            "path": "src/main/java/roomescape/controller/Foo.java",
                            "line": 42,
                            "matched_terms": ["domain"],
                            "body_excerpt": (
                                "controller와 service의 책임 분리를 어디서 잡으시나요? "
                                "이 부분은 domain 안으로 들어가야 합니다."
                            ),
                        },
                    ],
                    "matched_review_samples": [],
                    "matched_issue_comment_samples": [],
                    "created_year": 2025,
                    "cohort_caveat": False,
                },
            ],
            "candidate_count": 1,
        }
        learning_profile = {
            "underexplored_learning_points": [
                {"learning_point": "testing_strategy"}
            ],
        }
        result = build_candidate_interpretation(
            repo_name="fixture-repo",
            mode="coach",
            focus_payload=focus_payload,
            db_path=None,
            learning_profile=learning_profile,
        )
        rec_ids = [r["learning_point"] for r in result["learning_point_recommendations"]]
        self.assertIn(
            "responsibility_boundary",
            rec_ids,
            f"responsibility_boundary missing from recommendations: {rec_ids}",
        )
        rb_rec = next(
            r for r in result["learning_point_recommendations"]
            if r["learning_point"] == "responsibility_boundary"
        )
        sources = [
            q["source"] for q in rb_rec["primary_candidate"]["evidence_quotes"]
        ]
        self.assertIn(
            "review_comment",
            sources,
            f"responsibility_boundary primary candidate not review-grounded: {sources}",
        )


if __name__ == "__main__":
    unittest.main()
