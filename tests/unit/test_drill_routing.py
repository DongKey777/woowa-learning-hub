"""drill engine: route, score, offer, TTL, persistence."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from scripts.learning import drill


PENDING_FIXTURE = {
    "drill_session_id": "drill-test-1",
    "question": "Repository가 트랜잭션 경계를 왜 몰라야 하는지 설명해 보세요.",
    "linked_learning_point": "repository_boundary",
    "source_doc": {"category": "database"},
    "expected_terms": ["repository", "트랜잭션", "경계", "application"],
    "created_at": "2026-04-01T00:00:00+00:00",
    "ttl_turns": 3,
}


class RouteAnswerTest(unittest.TestCase):
    def test_no_pending_never_routes(self) -> None:
        is_answer, signals = drill.route_answer("아무 말이나", None)
        self.assertFalse(is_answer)
        self.assertFalse(signals["has_pending"])

    def test_short_question_is_not_an_answer(self) -> None:
        is_answer, _ = drill.route_answer("그거 뭐야?", PENDING_FIXTURE)
        self.assertFalse(is_answer)

    def test_long_declarative_answer_routes(self) -> None:
        body = (
            "Repository가 영속성 추상화이고 트랜잭션 경계를 왜 application layer가 "
            "몰라야 하는지 설명한다. 내부적으로 aggregate root 단위만 관리한다."
        )
        is_answer, signals = drill.route_answer(body, PENDING_FIXTURE)
        self.assertTrue(is_answer)
        self.assertTrue(signals["length_ok"])
        self.assertTrue(signals["not_question"])
        self.assertGreaterEqual(signals["token_overlap"], 0.2)

    def test_long_but_question_phrased_does_not_route(self) -> None:
        body = (
            "Repository가 트랜잭션 경계를 몰라야 하는 이유가 뭐야? 왜 그런지 알려줘?"
        )
        is_answer, _ = drill.route_answer(body, PENDING_FIXTURE)
        self.assertFalse(is_answer)


class TtlTest(unittest.TestCase):
    def test_decrement_ttl_reduces_counter(self) -> None:
        out = drill.decrement_ttl(dict(PENDING_FIXTURE))
        self.assertEqual(out["ttl_turns"], 2)

    def test_decrement_ttl_expires(self) -> None:
        pending = dict(PENDING_FIXTURE, ttl_turns=0)
        self.assertIsNone(drill.decrement_ttl(pending))

    def test_decrement_none(self) -> None:
        self.assertIsNone(drill.decrement_ttl(None))


class BuildOfferTest(unittest.TestCase):
    def test_refuses_when_pending_exists(self) -> None:
        unified = {
            "reconciled": {"priority_focus": ["repository_boundary"]},
            "coach_view": {"repeated_points": ["repository_boundary"]},
        }
        offer = drill.build_offer_if_due(
            unified,
            pre_intent="mission_only",
            pending={"drill_session_id": "x"},
        )
        self.assertIsNone(offer)

    def test_refuses_on_drill_answer_turn(self) -> None:
        unified = {"reconciled": {"priority_focus": ["x"]}}
        offer = drill.build_offer_if_due(
            unified, pre_intent="drill_answer", pending=None
        )
        self.assertIsNone(offer)

    def test_refuses_without_focus(self) -> None:
        unified = {"reconciled": {}, "coach_view": {}}
        offer = drill.build_offer_if_due(
            unified, pre_intent="mission_only", pending=None
        )
        self.assertIsNone(offer)

    def test_generates_offer_with_priority_focus(self) -> None:
        unified = {
            "reconciled": {"priority_focus": ["repository_boundary"]},
            "coach_view": {},
        }
        offer = drill.build_offer_if_due(
            unified, pre_intent="mission_only", pending=None
        )
        self.assertIsNotNone(offer)
        self.assertEqual(offer["linked_learning_point"], "repository_boundary")
        self.assertEqual(offer["ttl_turns"], drill.DEFAULT_TTL_TURNS)
        self.assertIn("repository_boundary", offer["question"])

    def test_expected_terms_includes_weak_tags(self) -> None:
        unified = {
            "reconciled": {"priority_focus": ["repository_boundary"]},
            "coach_view": {},
            "cs_view": {"weak_tags": ["practicality_markers", "depth_markers"]},
        }
        offer = drill.build_offer_if_due(
            unified,
            pre_intent="mission_only",
            pending=None,
            session_payload={"primary_topic": "repository"},
        )
        self.assertIsNotNone(offer)
        self.assertIn("repository", offer["expected_terms"])
        self.assertIn("practicality_markers", offer["expected_terms"])
        self.assertIn("depth_markers", offer["expected_terms"])

    def test_pick_focus_prefers_active_recency(self) -> None:
        unified = {
            "reconciled": {
                "priority_focus": ["db_modeling", "repository_boundary"]
            },
            "coach_view": {
                "recency_by_point": {
                    "db_modeling": "dormant",
                    "repository_boundary": "active",
                }
            },
        }
        offer = drill.build_offer_if_due(
            unified, pre_intent="mission_only", pending=None
        )
        self.assertIsNotNone(offer)
        self.assertEqual(offer["linked_learning_point"], "repository_boundary")

    def test_pick_focus_keeps_first_when_no_recency(self) -> None:
        unified = {
            "reconciled": {
                "priority_focus": ["db_modeling", "repository_boundary"]
            },
            "coach_view": {},
        }
        offer = drill.build_offer_if_due(
            unified, pre_intent="mission_only", pending=None
        )
        self.assertEqual(offer["linked_learning_point"], "db_modeling")

    def test_expected_terms_dedupes_weak_tag_matching_topic(self) -> None:
        unified = {
            "reconciled": {"priority_focus": ["repository_boundary"]},
            "coach_view": {},
            "cs_view": {"weak_tags": ["repository", "depth_markers"]},
        }
        offer = drill.build_offer_if_due(
            unified,
            pre_intent="mission_only",
            pending=None,
            session_payload={"primary_topic": "repository"},
        )
        self.assertEqual(offer["expected_terms"].count("repository"), 1)


class ScorePendingAnswerTest(unittest.TestCase):
    def test_score_applies_expected_terms(self) -> None:
        answer = (
            "Repository는 영속성 추상화이고 트랜잭션 경계는 application layer가 "
            "책임진다. 내부적으로 aggregate root 단위로 관리한다. "
            "실제로 운영에서 롤백과 타임아웃 경계를 다룰 때 이 분리가 중요하다."
        )
        result = drill.score_pending_answer(answer, PENDING_FIXTURE)
        self.assertEqual(result["drill_session_id"], "drill-test-1")
        self.assertEqual(result["linked_learning_point"], "repository_boundary")
        self.assertGreaterEqual(result["dimensions"]["accuracy"], 2)
        self.assertGreaterEqual(result["total_score"], 5)

    def test_due_at_set_after_score(self) -> None:
        result = drill.score_pending_answer("트랜잭션 경계는 application layer가 책임진다.", PENDING_FIXTURE)

        scored_at = datetime.fromisoformat(result["scored_at"])
        due_at = datetime.fromisoformat(result["due_at"])

        self.assertEqual(due_at, scored_at + timedelta(days=3))
        self.assertEqual(result["review_of_session_id"], "drill-test-1")
        self.assertEqual(result["review_count"], 0)
        self.assertEqual(result["last_outcome"], result["level"])

    def test_env_adjustable_bands(self) -> None:
        pending = dict(PENDING_FIXTURE, review_count=1)
        with mock.patch.dict("os.environ", {"WOOWA_SPACED_REPETITION_BANDS": "1,2,4"}):
            result = drill.score_pending_answer("트랜잭션 경계는 application layer가 책임진다.", pending)

        scored_at = datetime.fromisoformat(result["scored_at"])
        due_at = datetime.fromisoformat(result["due_at"])

        self.assertEqual(due_at, scored_at + timedelta(days=2))


class ReviewOfferTest(unittest.TestCase):
    def test_review_offer_surfaces_when_due(self) -> None:
        now = datetime(2026, 5, 7, tzinfo=timezone.utc)
        history = [
            {
                "drill_session_id": "drill-old",
                "question": "Repository 경계를 설명해 보세요.",
                "linked_learning_point": "repository_boundary",
                "source_doc": {"category": "database"},
                "weak_tags": ["transaction_boundary"],
                "due_at": (now - timedelta(minutes=1)).isoformat(),
                "review_count": 0,
            }
        ]

        offer = drill.build_review_offer_if_due(history, now=now)

        self.assertIsNotNone(offer)
        self.assertEqual(offer["question"], "Repository 경계를 설명해 보세요.")
        self.assertEqual(offer["review_of_session_id"], "drill-old")
        self.assertEqual(offer["review_count"], 1)
        self.assertEqual(offer["expected_terms"], ["transaction_boundary"])

    def test_review_offer_skipped_when_pending(self) -> None:
        now = datetime(2026, 5, 7, tzinfo=timezone.utc)
        history = [
            {
                "drill_session_id": "drill-old",
                "question": "Repository 경계를 설명해 보세요.",
                "due_at": (now - timedelta(days=1)).isoformat(),
            }
        ]

        offer = drill.build_review_offer_if_due(
            history,
            pending={"drill_session_id": "open"},
            now=now,
        )

        self.assertIsNone(offer)

    def test_review_count_increments_on_consecutive_review(self) -> None:
        pending = dict(
            PENDING_FIXTURE,
            drill_session_id="drill-review-1",
            review_of_session_id="drill-original",
            review_count=1,
        )
        result = drill.score_pending_answer(
            "트랜잭션 경계는 application layer가 책임지고 repository는 영속성만 다룬다.",
            pending,
        )
        scored_at = datetime.fromisoformat(result["scored_at"])
        due_at = datetime.fromisoformat(result["due_at"])

        self.assertEqual(result["review_of_session_id"], "drill-original")
        self.assertEqual(result["review_count"], 1)
        self.assertEqual(due_at, scored_at + timedelta(days=7))

        now = due_at + timedelta(minutes=1)
        next_offer = drill.build_review_offer_if_due([result], now=now)

        self.assertIsNotNone(next_offer)
        self.assertEqual(next_offer["review_of_session_id"], "drill-original")
        self.assertEqual(next_offer["review_count"], 2)


class PersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = "fixture-repo"
        memory_root = Path(self._tmp.name) / "memory"
        memory_root.mkdir(parents=True, exist_ok=True)
        self._patch = mock.patch(
            "scripts.learning.drill.repo_memory_dir",
            return_value=memory_root,
        )
        self._patch.start()
        self.addCleanup(self._patch.stop)

    def test_save_and_load_pending_roundtrip(self) -> None:
        path = drill.save_pending(self.repo, dict(PENDING_FIXTURE))
        self.assertTrue(path.exists())
        loaded = drill.load_pending(self.repo)
        self.assertEqual(loaded["drill_session_id"], "drill-test-1")

    def test_clear_pending_removes_file(self) -> None:
        drill.save_pending(self.repo, dict(PENDING_FIXTURE))
        drill.clear_pending(self.repo)
        self.assertIsNone(drill.load_pending(self.repo))

    def test_append_and_load_history(self) -> None:
        drill.append_history(self.repo, {"drill_session_id": "d1", "total_score": 7})
        drill.append_history(self.repo, {"drill_session_id": "d2", "total_score": 4})
        history = drill.load_history(self.repo)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["drill_session_id"], "d1")

    def test_load_history_missing_returns_empty(self) -> None:
        self.assertEqual(drill.load_history(self.repo), [])


if __name__ == "__main__":
    unittest.main()
