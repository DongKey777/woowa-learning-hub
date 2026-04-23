"""Snapshot tests for the centralized intent_tokens vocabularies."""

from __future__ import annotations

import unittest

from scripts.workbench.core import intent_tokens


class IntentTokensTest(unittest.TestCase):
    def test_constants_are_frozensets(self) -> None:
        self.assertIsInstance(intent_tokens.MISSION_TOKENS, frozenset)
        self.assertIsInstance(intent_tokens.CS_TOKENS, frozenset)
        self.assertIsInstance(intent_tokens.DRILL_ANSWER_NEGATIVE_KEYWORDS, frozenset)

    def test_drill_answer_negative_keywords_canonical(self) -> None:
        # PR#4 canonicalized on the 11-keyword set (was 7 in drill.py).
        # English question words must include which/when/where so English
        # phrasings route correctly.
        for kw in ("what", "why", "how", "explain",
                   "which", "when", "where"):
            self.assertIn(kw, intent_tokens.DRILL_ANSWER_NEGATIVE_KEYWORDS)
        for kw in ("뭐야", "어떻게", "왜", "알려줘", "설명해", "차이", "무엇"):
            self.assertIn(kw, intent_tokens.DRILL_ANSWER_NEGATIVE_KEYWORDS)

    def test_mission_tokens_have_pr_signal(self) -> None:
        for kw in ("pr", "리뷰", "review", "thread"):
            self.assertIn(kw, intent_tokens.MISSION_TOKENS)

    def test_cs_tokens_have_concept_signal(self) -> None:
        for kw in ("개념", "이론", "concept", "synchronized"):
            self.assertIn(kw, intent_tokens.CS_TOKENS)

    def test_no_overlap_between_mission_and_cs(self) -> None:
        # Drift guard: a token that signals BOTH would defeat the
        # mission_score vs cs_score comparison in pre_decide.
        overlap = intent_tokens.MISSION_TOKENS & intent_tokens.CS_TOKENS
        self.assertEqual(overlap, frozenset())


if __name__ == "__main__":
    unittest.main()
