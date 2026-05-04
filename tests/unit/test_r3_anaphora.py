"""Phase 9.1 — multi-turn anaphora detection in production R3.

Pre-9.1: r3/search.py used `semantic_query = reformulated_query or
prompt` and ignored learner_context. The legacy lance path had a
regex-only follow_up detector but R3 was unreachable for production
turns.

Phase 9.1 introduces ``detect_follow_up`` which combines two signal
sources:

  1. **AI-session reformulation (primary)** — when the AI session
     emits ``reformulated_query``, that string already folds prior-
     turn context per the regulation in
     ``docs/agent-query-reformulation-contract.md``. We use it
     verbatim and suppress the regex fallback to avoid double-folding.

  2. **Regex + learner_context (fallback)** — short anaphoric prompts
     ('그럼 IoC는?') matched by the legacy ``is_follow_up`` regex are
     enriched with up to 2 prior topics from
     ``learner_context.recent_rag_ask_context`` or
     ``learner_context.recent_topics``. The augmented semantic query
     becomes "이전 맥락: <topics>\\n현재 질문: <prompt>".

Graceful degradation:

  * No reformulation, regex no match → raw prompt unchanged.
  * Regex match but no prior topics → raw prompt unchanged
    (kills false-positives like "그럼 안녕").
  * learner_context = None / wrong type → raw prompt unchanged.
"""

from __future__ import annotations

import unittest

from scripts.learning.rag.r3 import anaphora


class FollowUpDecisionShapeTest(unittest.TestCase):
    def test_decision_has_required_fields(self):
        decision = anaphora.detect_follow_up(
            prompt="Spring DI가 뭐야?",
            reformulated_query=None,
            learner_context=None,
        )
        self.assertIsInstance(decision.is_follow_up, bool)
        self.assertIn(decision.detected_via, {"reformulated_query", "regex", "none"})
        self.assertIsInstance(decision.prior_topics, list)
        self.assertIsInstance(decision.augmented_semantic_query, str)


class ReformulatedQueryShortCircuitTest(unittest.TestCase):
    def test_reformulated_query_is_used_verbatim(self):
        decision = anaphora.detect_follow_up(
            prompt="그럼 IoC는?",
            reformulated_query="Spring IoC inversion of control basics",
            learner_context={"recent_rag_ask_context": ["spring/bean"]},
        )
        self.assertEqual(decision.detected_via, "reformulated_query")
        # Suppress regex even when prompt would have matched
        self.assertFalse(decision.is_follow_up)
        # Empty list — AI handled fold-in upstream
        self.assertEqual(decision.prior_topics, [])
        self.assertEqual(
            decision.augmented_semantic_query,
            "Spring IoC inversion of control basics",
        )

    def test_blank_reformulation_treated_as_absent(self):
        decision = anaphora.detect_follow_up(
            prompt="Spring DI가 뭐야?",
            reformulated_query="   ",
            learner_context=None,
        )
        self.assertEqual(decision.detected_via, "none")
        self.assertEqual(decision.augmented_semantic_query, "Spring DI가 뭐야?")


class RegexAnaphoraTest(unittest.TestCase):
    def test_short_korean_anaphora_with_prior_topics_folds_in(self):
        decision = anaphora.detect_follow_up(
            prompt="그럼 IoC는?",
            reformulated_query=None,
            learner_context={"recent_rag_ask_context": ["spring/bean", "spring/di"]},
        )
        self.assertEqual(decision.detected_via, "regex")
        self.assertTrue(decision.is_follow_up)
        self.assertEqual(decision.prior_topics, ["spring/bean", "spring/di"])
        self.assertIn("spring/bean", decision.augmented_semantic_query)
        self.assertIn("그럼 IoC는?", decision.augmented_semantic_query)
        self.assertIn("이전 맥락", decision.augmented_semantic_query)

    def test_caps_prior_topics_at_two(self):
        decision = anaphora.detect_follow_up(
            prompt="그럼?",
            reformulated_query=None,
            learner_context={
                "recent_rag_ask_context": ["a", "b", "c", "d", "e"],
            },
        )
        self.assertEqual(len(decision.prior_topics), 2)
        self.assertEqual(decision.prior_topics, ["a", "b"])

    def test_falls_back_to_recent_topics_key(self):
        decision = anaphora.detect_follow_up(
            prompt="그래서?",
            reformulated_query=None,
            learner_context={"recent_topics": ["spring/transaction"]},
        )
        self.assertEqual(decision.detected_via, "regex")
        self.assertEqual(decision.prior_topics, ["spring/transaction"])

    def test_english_anaphora_also_detected(self):
        decision = anaphora.detect_follow_up(
            prompt="then?",
            reformulated_query=None,
            learner_context={"recent_rag_ask_context": ["spring/bean"]},
        )
        self.assertEqual(decision.detected_via, "regex")
        self.assertIn("spring/bean", decision.augmented_semantic_query)


class FalsePositiveRejectionTest(unittest.TestCase):
    def test_short_korean_greeting_with_no_prior_topics_unchanged(self):
        """'그럼 안녕' matches the regex but has no prior context to
        fold — must not pollute the semantic query."""
        decision = anaphora.detect_follow_up(
            prompt="그럼 안녕",
            reformulated_query=None,
            learner_context={"recent_rag_ask_context": []},
        )
        # is_follow_up still True (regex matched) but augmented = raw
        self.assertEqual(decision.augmented_semantic_query, "그럼 안녕")
        self.assertEqual(decision.prior_topics, [])

    def test_long_prompt_not_marked_anaphora(self):
        """Regex requires < 25 chars. Standalone full-length question
        should not be treated as follow-up regardless of context."""
        long_prompt = "Spring 트랜잭션 격리 수준은 어떻게 결정되는가?"
        decision = anaphora.detect_follow_up(
            prompt=long_prompt,
            reformulated_query=None,
            learner_context={"recent_rag_ask_context": ["spring/bean"]},
        )
        self.assertEqual(decision.detected_via, "none")
        self.assertEqual(decision.augmented_semantic_query, long_prompt)


class GracefulDegradationTest(unittest.TestCase):
    def test_none_learner_context(self):
        decision = anaphora.detect_follow_up(
            prompt="그럼?",
            reformulated_query=None,
            learner_context=None,
        )
        # Regex matched but no context to fold — raw prompt
        self.assertEqual(decision.augmented_semantic_query, "그럼?")
        self.assertEqual(decision.prior_topics, [])

    def test_dict_with_wrong_keys(self):
        decision = anaphora.detect_follow_up(
            prompt="그럼?",
            reformulated_query=None,
            learner_context={"unrelated_key": ["x"]},
        )
        self.assertEqual(decision.augmented_semantic_query, "그럼?")

    def test_non_list_value(self):
        """If recent_rag_ask_context is malformed (string instead of
        list), treat as no context."""
        decision = anaphora.detect_follow_up(
            prompt="그럼?",
            reformulated_query=None,
            learner_context={"recent_rag_ask_context": "spring/bean"},
        )
        self.assertEqual(decision.prior_topics, [])

    def test_empty_string_topics_filtered(self):
        decision = anaphora.detect_follow_up(
            prompt="그럼?",
            reformulated_query=None,
            learner_context={"recent_rag_ask_context": ["", "  ", "spring/bean"]},
        )
        self.assertEqual(decision.prior_topics, ["spring/bean"])


if __name__ == "__main__":
    unittest.main()
