"""4-condition routing matrix for ``answer_classifier.classify_drill_answer``.

These tests pin the canonical heuristic so future tweaks land in one place
and any drift between drill.route_answer (which now delegates) and the
classifier surfaces immediately.
"""

from __future__ import annotations

import unittest

from scripts.workbench.core.answer_classifier import (
    classify_drill_answer,
    is_question_like,
    tokenize,
)


PENDING = {
    "drill_session_id": "drill-1",
    "question": "Repository가 트랜잭션 경계를 왜 몰라야 하는지 설명해 보세요.",
}


class TokenizeTest(unittest.TestCase):
    def test_keeps_korean_english_underscore(self) -> None:
        toks = tokenize("Repository_root transaction 경계 를 모른다")
        self.assertIn("repository_root", toks)
        self.assertIn("transaction", toks)
        self.assertIn("경계", toks)

    def test_empty_input(self) -> None:
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize(None), [])  # type: ignore[arg-type]


class IsQuestionLikeTest(unittest.TestCase):
    def test_trailing_question_mark(self) -> None:
        self.assertTrue(is_question_like("뭐가 다른가?"))
        self.assertTrue(is_question_like("really？"))

    def test_question_word(self) -> None:
        self.assertTrue(is_question_like("which one applies here"))
        self.assertTrue(is_question_like("어떻게 동작해"))

    def test_declarative(self) -> None:
        self.assertFalse(is_question_like(
            "Repository는 영속성 추상화이고 트랜잭션 경계를 모른다"))


class ClassifyDrillAnswerTest(unittest.TestCase):
    def test_no_pending_never_routes(self) -> None:
        is_answer, signals = classify_drill_answer("anything", None)
        self.assertFalse(is_answer)
        self.assertFalse(signals["has_pending"])

    def test_short_question_phrased(self) -> None:
        is_answer, signals = classify_drill_answer("그게 뭐야?", PENDING)
        self.assertFalse(is_answer)
        self.assertFalse(signals["length_ok"])
        self.assertFalse(signals["not_question"])
        self.assertFalse(signals["no_question_word"])

    def test_long_declarative_answer_routes(self) -> None:
        body = (
            "Repository가 영속성 추상화이고 트랜잭션 경계를 왜 application layer가 "
            "몰라야 하는지 설명한다. 내부적으로 aggregate root 단위만 관리한다."
        )
        is_answer, signals = classify_drill_answer(body, PENDING)
        self.assertTrue(is_answer)
        self.assertTrue(signals["length_ok"])
        self.assertTrue(signals["not_question"])
        self.assertGreaterEqual(signals["token_overlap"], 0.2)

    def test_long_but_question_phrased_blocks(self) -> None:
        body = (
            "Repository가 트랜잭션 경계를 몰라야 하는 이유가 뭐야? 왜 그런지 알려줘?"
        )
        is_answer, _ = classify_drill_answer(body, PENDING)
        self.assertFalse(is_answer)

    def test_english_which_keyword_blocks_routing(self) -> None:
        # PR#4 added which/when/where to the canonical 11-keyword set.
        # Pre-PR#4, drill.py's 7-keyword set would have routed this prompt.
        body = (
            "Tell me which one of these patterns is the right answer here "
            "for the repository boundary case in this mission"
        )
        is_answer, signals = classify_drill_answer(body, PENDING)
        self.assertFalse(signals["no_question_word"])
        self.assertFalse(is_answer)


if __name__ == "__main__":
    unittest.main()
