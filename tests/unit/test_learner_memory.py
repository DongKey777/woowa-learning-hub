"""Unit tests for `scripts/workbench/core/learner_memory`.

Tests group:
  * append_learner_event basic shape + validation
  * dispatch validator (per-event-type required fields)
  * builders (rag_ask, coach_run, drill_answer, test_result, code_attempt)
  * privacy redaction (email, token, password, stack/diff truncation)
  * recompute_learner_profile aggregation (concept events, mastery,
    uncertainty, experience level, streak)
  * deterministic event_id (idempotent across re-build)

Disk isolation: each test class swaps `state/learner/` to a temp dir and
points the path helpers at that dir; the LRU-cached learner identity is
also reset so tests don't share a cached learner_id.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core import concept_catalog, learner_memory  # noqa: E402
from core.concept_catalog import load_catalog  # noqa: E402


def _iso(days_ago: float = 0) -> str:
    """Helper for crafting timestamps relative to now."""
    return (
        datetime.now(timezone.utc) - timedelta(days=days_ago)
    ).isoformat(timespec="seconds")


class _DiskIsolated(unittest.TestCase):
    """Base class — points learner state at a per-test tempdir."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.tmp_learner = tmp_root / "learner"
        self.tmp_learner.mkdir(parents=True, exist_ok=True)
        self._prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "test-learner"
        self.addCleanup(self._restore_env)

        # Stamp the helpers inside learner_memory to point at our tmp dir.
        history = self.tmp_learner / "history.jsonl"
        profile = self.tmp_learner / "profile.json"
        summary = self.tmp_learner / "summary.json"
        identity = self.tmp_learner / "identity.json"
        self._patches = [
            patch.object(learner_memory, "LEARNER_DIR", self.tmp_learner),
            patch.object(learner_memory, "ensure_learner_layout", lambda: self.tmp_learner),
            patch.object(learner_memory, "learner_history_path", lambda: history),
            patch.object(learner_memory, "learner_profile_path", lambda: profile),
            patch.object(learner_memory, "learner_summary_path", lambda: summary),
            patch.object(learner_memory, "learner_identity_path", lambda: identity),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)
        concept_catalog.reset_cache()

    def _restore_env(self) -> None:
        if self._prev_env is None:
            os.environ.pop("WOOWA_LEARNER_ID", None)
        else:
            os.environ["WOOWA_LEARNER_ID"] = self._prev_env


class AppendAndValidateTests(_DiskIsolated):
    def test_append_creates_history_with_required_fields(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_rag_ask_event(
            prompt="Bean이 뭐야?",
            tier=1,
            mode="cheap",
            experience_level="beginner",
            rag_result=None,
            repo=None,
            module="spring-core-1",
            learner_id="test-learner",
            blocked=False,
            catalog=catalog,
        )
        learner_memory.append_learner_event(event)
        history_path = learner_memory.learner_history_path()
        self.assertTrue(history_path.exists())
        line = history_path.read_text(encoding="utf-8").strip()
        decoded = json.loads(line)
        self.assertEqual(decoded["event_type"], "rag_ask")
        self.assertEqual(decoded["learner_id"], "test-learner")
        self.assertIn("event_id", decoded)
        self.assertIn("ts", decoded)

    def test_append_rejects_event_without_event_type(self) -> None:
        with self.assertRaises(ValueError):
            learner_memory.append_learner_event(
                {"event_id": "abc", "ts": _iso(), "learner_id": "x"}
            )

    def test_append_rejects_unknown_event_type(self) -> None:
        with self.assertRaises(ValueError):
            learner_memory.append_learner_event(
                {
                    "event_type": "bogus",
                    "event_id": "abc12345",
                    "ts": _iso(),
                    "learner_id": "x",
                }
            )

    def test_dispatch_validator_enforces_per_type_required(self) -> None:
        # rag_ask is missing `tier` & `rag_mode` & `concept_ids` & `blocked`.
        with self.assertRaisesRegex(ValueError, "missing required field for rag_ask"):
            learner_memory.validate_learner_event(
                {
                    "event_type": "rag_ask",
                    "event_id": "abc12345",
                    "ts": _iso(),
                    "learner_id": "x",
                    "prompt": "?",
                }
            )

    def test_append_preserves_existing_entries(self) -> None:
        catalog = load_catalog()
        for i in range(3):
            event = learner_memory.build_rag_ask_event(
                prompt=f"Bean question {i}",
                tier=1,
                mode="cheap",
                experience_level="beginner",
                rag_result=None,
                repo=None,
                module=None,
                learner_id="test-learner",
                blocked=False,
                catalog=catalog,
            )
            learner_memory.append_learner_event(event)
        history_path = learner_memory.learner_history_path()
        lines = [
            ln for ln in history_path.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
        self.assertEqual(len(lines), 3)


class BuilderTests(_DiskIsolated):
    def test_rag_ask_event_extracts_concept_ids(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_rag_ask_event(
            prompt="Spring Bean과 DI 차이",
            tier=2,
            mode="full",
            experience_level=None,
            rag_result={
                "by_fallback_key": {"x": [{"path": "knowledge/cs/contents/spring/ioc-di-container.md", "category": "spring"}]},
                "meta": {"rag_ready": True, "cs_categories_hit": ["spring"]},
            },
            repo=None,
            module="spring-core-1",
            learner_id="test-learner",
            blocked=False,
            catalog=catalog,
        )
        self.assertIn("concept:spring/bean", event["concept_ids"])
        self.assertIn("concept:spring/di", event["concept_ids"])
        self.assertEqual(event["category_hits"], ["spring"])
        self.assertEqual(event["top_paths"], ["knowledge/cs/contents/spring/ioc-di-container.md"])
        self.assertTrue(event["rag_ready"])

    def test_rag_ask_event_blocked_flag(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_rag_ask_event(
            prompt="내 PR 리뷰해줘",
            tier=3,
            mode=None,
            experience_level=None,
            rag_result=None,
            repo=None,
            module=None,
            learner_id="test-learner",
            blocked=True,
            catalog=catalog,
        )
        self.assertEqual(event["tier"], 3)
        self.assertTrue(event["blocked"])
        self.assertIsNone(event["rag_mode"])

    def test_rag_ask_event_stores_reformulated_query_when_provided(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_rag_ask_event(
            prompt="그럼 IoC는?",
            reformulated_query="Spring IoC inversion of control basics",
            tier=2,
            mode="full",
            experience_level=None,
            rag_result=None,
            repo=None,
            module=None,
            learner_id="test-learner",
            blocked=False,
            catalog=catalog,
        )
        self.assertEqual(
            event["reformulated_query"],
            "Spring IoC inversion of control basics",
        )
        learner_memory.append_learner_event(event)

    def test_rag_ask_event_omits_reformulated_query_when_not_provided(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_rag_ask_event(
            prompt="Bean이 뭐야?",
            tier=1,
            mode="cheap",
            experience_level=None,
            rag_result=None,
            repo=None,
            module=None,
            learner_id="test-learner",
            blocked=False,
            catalog=catalog,
        )
        self.assertNotIn("reformulated_query", event)
        learner_memory.append_learner_event(event)

    def test_coach_run_event_picks_up_negative_feedback(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_coach_run_event(
            session_payload={
                "repo": "spring-roomescape-admin",
                "current_pr": {"number": 42},
                "primary_learning_points": ["transaction_consistency"],
                "review_state": "request_changes",
                "response": {"summary": ["...요약..."], "answer": ["...본문..."]},
            },
            learner_id="test-learner",
            catalog=catalog,
        )
        self.assertEqual(event["pr_number"], 42)
        self.assertTrue(event["had_negative_feedback"])
        self.assertIn("concept:spring/transactional", event["concept_ids"])

    def test_coach_run_event_stores_reformulated_query_when_provided(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_coach_run_event(
            session_payload={
                "repo": "spring-roomescape-admin",
                "current_pr": {"number": 42},
                "primary_learning_points": ["transaction_consistency"],
                "reformulated_query": "roomescape service transaction boundary",
                "response": {"summary": ["...요약..."], "answer": ["...본문..."]},
            },
            learner_id="test-learner",
            catalog=catalog,
        )
        self.assertEqual(
            event["reformulated_query"],
            "roomescape service transaction boundary",
        )
        learner_memory.append_learner_event(event)

    def test_required_fields_enforcement_unchanged_for_reformulated_query(self) -> None:
        self.assertNotIn("reformulated_query", learner_memory.EVENT_REQUIRED_FIELDS["rag_ask"])
        self.assertNotIn("reformulated_query", learner_memory.EVENT_REQUIRED_FIELDS["coach_run"])

    def test_drill_answer_event_links_concept(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_drill_answer_event(
            drill_record={
                "scored_at": _iso(),
                "drill_session_id": "drill-1",
                "linked_learning_point": "transaction_consistency",
                "total_score": 9,
                "dimensions": {"accuracy": 9, "depth": 8},
                "weak_tags": [],
            },
            learner_id="test-learner",
            repo="spring-roomescape-admin",
            catalog=catalog,
        )
        self.assertEqual(event["total_score"], 9)
        self.assertIn("concept:spring/transactional", event["concept_ids"])

    def test_test_result_event_redacts_failure_excerpt(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_test_result_event(
            junit_test={
                "class": "cholog.BeanTest",
                "name": "registerBean",
                "duration_ms": 245,
                "failure": {
                    "message": "AssertionError: my email is foo@bar.com",
                    "stack_trace": "\n".join(f"line-{i}" for i in range(20)),
                },
            },
            learner_id="test-learner",
            module="spring-core-1",
            catalog=catalog,
        )
        self.assertFalse(event["pass"])
        self.assertIn("***REDACTED***", event["failure_message"])
        self.assertEqual(event["stack_trace_excerpt"].count("\n") + 1, 5)

    def test_code_attempt_event_truncates_diff(self) -> None:
        catalog = load_catalog()
        big_diff = "x" * 2000
        event = learner_memory.build_code_attempt_event(
            file_path="missions/spring-learning-test/spring-core-1/initial/Bean.java",
            diff_summary=big_diff,
            lines_added=10,
            lines_removed=2,
            linked_test=None,
            learner_id="test-learner",
            module="spring-core-1",
            catalog=catalog,
        )
        self.assertLessEqual(len(event["diff_summary"]), 503)
        self.assertEqual(event["lines_added"], 10)


class PrivacyRedactionTests(unittest.TestCase):
    def test_email_redacted(self) -> None:
        out = learner_memory._redact_text("contact me at foo.bar@example.org now")
        self.assertNotIn("foo.bar@example.org", out)
        self.assertIn("***REDACTED***", out)

    def test_github_token_redacted(self) -> None:
        out = learner_memory._redact_text("token: ghp_aaaaaaaaaaaaaaaaaaaaaa")
        self.assertNotIn("ghp_aaaaaaaaaaaaaaaaaaaaaa", out)

    def test_password_assignment_redacted(self) -> None:
        out = learner_memory._redact_text("password=hunter2 and api_key: zzzzzzzzzzzzzzzz")
        self.assertNotIn("hunter2", out)
        self.assertNotIn("zzzzzzzzzzzzzzzz", out)


class RecomputeAggregationTests(_DiskIsolated):
    def _seed(self, events: list[dict]) -> None:
        history_path = learner_memory.learner_history_path()
        with history_path.open("w", encoding="utf-8") as fh:
            for event in events:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _rag_ask(self, ts: str, *, tier: int = 1, blocked: bool = False, concept_ids=None, prompt="Bean이 뭐야?", level="beginner", module="spring-core-1") -> dict:
        return {
            "event_type": "rag_ask",
            "event_id": f"id-{ts}-{prompt[:6]}",
            "ts": ts,
            "learner_id": "test-learner",
            "repo_context": None,
            "module_context": module,
            "concept_ids": list(concept_ids or ["concept:spring/bean"]),
            "prompt": prompt,
            "question_fingerprint": prompt.lower(),
            "tier": tier,
            "rag_mode": "cheap" if tier == 1 else None,
            "experience_level_inferred": level,
            "category_hits": [],
            "top_paths": [],
            "rag_ready": True,
            "blocked": blocked,
        }

    def test_recompute_with_empty_history_returns_skeleton(self) -> None:
        history_path = learner_memory.learner_history_path()
        history_path.write_text("", encoding="utf-8")
        # load returns None (zero-byte file)
        self.assertIsNone(learner_memory.load_learner_profile())

    def test_recompute_aggregates_event_counts(self) -> None:
        self._seed([
            self._rag_ask(_iso(0)),
            self._rag_ask(_iso(0), prompt="DI는?", concept_ids=["concept:spring/di"]),
            self._rag_ask(_iso(0), tier=0, prompt="Gradle?", concept_ids=[]),
        ])
        profile = learner_memory.recompute_learner_profile()
        self.assertEqual(profile["total_events"], 3)
        self.assertEqual(profile["activity"]["events_by_type"].get("rag_ask"), 3)
        # tier_distribution counts both 0 and 1
        self.assertIn("0", profile["activity"]["tier_distribution"])
        self.assertIn("1", profile["activity"]["tier_distribution"])

    def test_uncertain_concept_threshold(self) -> None:
        # 4 asks within 7d on the same concept → should be uncertain.
        self._seed([
            self._rag_ask(_iso(0), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(1), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(2), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(3), concept_ids=["concept:spring/bean"]),
        ])
        profile = learner_memory.recompute_learner_profile()
        uncertain_ids = {c["concept_id"] for c in profile["concepts"]["uncertain"]}
        self.assertIn("concept:spring/bean", uncertain_ids)

    def test_underexplored_includes_unseen_stage_concept(self) -> None:
        # User is in spring-core-1, has touched only Bean. Other spring-core
        # concepts (di, ioc, component-scan, configuration) should appear
        # in `underexplored`.
        self._seed([
            self._rag_ask(_iso(0), concept_ids=["concept:spring/bean"]),
        ])
        profile = learner_memory.recompute_learner_profile()
        underexplored_ids = {
            c["concept_id"] for c in profile["concepts"]["underexplored"]
        }
        self.assertIn("concept:spring/component-scan", underexplored_ids)
        self.assertNotIn("concept:spring/bean", underexplored_ids)

    def test_mastery_drill_then_test_pass(self) -> None:
        # 2 high-score drills (+2) + 1 strict test_result pass (+2) = 4 ≥ 3 → mastered.
        self._seed([
            {
                "event_type": "drill_answer",
                "event_id": "d1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s1",
                "linked_learning_point": "x",
                "total_score": 9,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "drill_answer",
                "event_id": "d2",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s2",
                "linked_learning_point": "x",
                "total_score": 8,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "test_result",
                "event_id": "t1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "strict",
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "register",
                "pass": True,
            },
        ])
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertIn("concept:spring/bean", mastered)

    def test_pr_negative_feedback_blocks_mastered(self) -> None:
        # Score is high (drill 2 + strict test pass 2 = 4 ≥ 3) but pr_neg blocks.
        self._seed([
            {
                "event_type": "drill_answer",
                "event_id": "d1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/transactional"],
                "drill_session_id": "s1",
                "linked_learning_point": "x",
                "total_score": 9,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "drill_answer",
                "event_id": "d2",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/transactional"],
                "drill_session_id": "s2",
                "linked_learning_point": "x",
                "total_score": 8,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "test_result",
                "event_id": "t-tx",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/transactional"],
                "concept_match_mode": "strict",
                "module": "spring-jdbc-1",
                "test_class": "TransactionalTest",
                "test_method": "rollback",
                "pass": True,
            },
            {
                "event_type": "coach_run",
                "event_id": "c1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/transactional"],
                "pr_number": 7,
                "primary_learning_points": ["transaction_consistency"],
                "had_negative_feedback": True,
            },
        ])
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertNotIn("concept:spring/transactional", mastered)

    def test_mastery_via_strict_test_pass_and_ask_decline_with_activity(self) -> None:
        # No drills. 1 strict test pass (+2) + ask decline + activity (+1) = 3 → mastered.
        self._seed([
            # 4 prior asks 10 days ago (within days 8-21)
            self._rag_ask(_iso(10), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(11), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(12), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(13), concept_ids=["concept:spring/bean"]),
            # No asks in last 7 days. Activity in same module 1 day ago:
            {
                "event_type": "test_result",
                "event_id": "t-bean",
                "ts": _iso(1),
                "learner_id": "test-learner",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "strict",
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "register",
                "pass": True,
            },
        ])
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertIn("concept:spring/bean", mastered)

    def test_mastery_blocked_by_recent_test_fail_even_when_score_high(self) -> None:
        # High score (drill 2 + strict pass 2 = 4) but recent test_fail (within 7d) blocks.
        self._seed([
            {
                "event_type": "drill_answer",
                "event_id": "d1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s1",
                "linked_learning_point": "x",
                "total_score": 9,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "drill_answer",
                "event_id": "d2",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s2",
                "linked_learning_point": "x",
                "total_score": 9,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "test_result",
                "event_id": "t-pass",
                "ts": _iso(2),
                "learner_id": "test-learner",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "strict",
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "registerOk",
                "pass": True,
            },
            {
                "event_type": "test_result",
                "event_id": "t-fail",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "strict",
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "registerEdge",
                "pass": False,
            },
        ])
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertNotIn("concept:spring/bean", mastered)

    def test_mastery_via_fallback_test_pass_requires_two_passes(self) -> None:
        # 2 high-score drills (+2) + 1 fallback test pass (+0) = 2 → not mastered.
        # Adding a second fallback pass → +2 → 4 ≥ 3 → mastered.
        seed_one_fallback = [
            {
                "event_type": "drill_answer",
                "event_id": "d1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s1",
                "linked_learning_point": "x",
                "total_score": 9,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "drill_answer",
                "event_id": "d2",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s2",
                "linked_learning_point": "x",
                "total_score": 8,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "test_result",
                "event_id": "t-fb1",
                "ts": _iso(1),
                "learner_id": "test-learner",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "fallback",
                "module": "spring-core-1",
                "test_class": "MysteryTest",
                "test_method": "x",
                "pass": True,
            },
        ]
        self._seed(seed_one_fallback)
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertNotIn("concept:spring/bean", mastered)

        seed_two_fallback = seed_one_fallback + [
            {
                "event_type": "test_result",
                "event_id": "t-fb2",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "fallback",
                "module": "spring-core-1",
                "test_class": "MysteryTest",
                "test_method": "y",
                "pass": True,
            },
        ]
        self._seed(seed_two_fallback)
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertIn("concept:spring/bean", mastered)

    def test_ask_decline_alone_no_activity_does_not_score(self) -> None:
        # Asks declined but NO activity in last 7d in same module → ask_decline=False.
        # Plus 1 strict pass would score 2, but with ask_decline blocked stays at 2 < 3.
        self._seed([
            self._rag_ask(_iso(10), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(11), concept_ids=["concept:spring/bean"]),
            self._rag_ask(_iso(12), concept_ids=["concept:spring/bean"]),
            {
                "event_type": "test_result",
                "event_id": "t-bean",
                "ts": _iso(8),  # outside last 7d, so no activity-in-last-7d
                "learner_id": "test-learner",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "strict",
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "register",
                "pass": True,
            },
        ])
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertNotIn("concept:spring/bean", mastered)

    def test_test_failure_marks_concept_uncertain(self) -> None:
        self._seed([
            {
                "event_type": "test_result",
                "event_id": "t1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "register",
                "pass": False,
            },
        ])
        profile = learner_memory.recompute_learner_profile()
        uncertain_ids = {c["concept_id"] for c in profile["concepts"]["uncertain"]}
        self.assertIn("concept:spring/bean", uncertain_ids)

    def test_streak_days_two_consecutive(self) -> None:
        self._seed([
            self._rag_ask(_iso(0)),  # today
            self._rag_ask(_iso(1)),  # yesterday
        ])
        profile = learner_memory.recompute_learner_profile()
        self.assertEqual(profile["activity"]["streak_days"], 2)

    def test_module_progress_tracks_test_results(self) -> None:
        self._seed([
            {
                "event_type": "test_result",
                "event_id": "t1",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/bean"],
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "r1",
                "pass": True,
            },
            {
                "event_type": "test_result",
                "event_id": "t2",
                "ts": _iso(0),
                "learner_id": "test-learner",
                "concept_ids": ["concept:spring/di"],
                "module": "spring-core-1",
                "test_class": "DITest",
                "test_method": "c1",
                "pass": False,
            },
        ])
        profile = learner_memory.recompute_learner_profile()
        progress = profile["activity"]["modules_progress"]["spring-core-1"]
        self.assertEqual(progress["tests_passed"], 1)
        self.assertEqual(progress["tests_failed"], 1)
        self.assertGreater(progress["completion_estimate"], 0)

    def test_lazy_recompute_when_history_newer(self) -> None:
        catalog = load_catalog()
        event = learner_memory.build_rag_ask_event(
            prompt="Bean이 뭐야?",
            tier=1,
            mode="cheap",
            experience_level="beginner",
            rag_result=None,
            repo=None,
            module="spring-core-1",
            learner_id="test-learner",
            blocked=False,
            catalog=catalog,
        )
        learner_memory.append_learner_event(event)
        # First call triggers recompute; ensures profile.json now exists.
        first = learner_memory.load_learner_profile()
        self.assertIsNotNone(first)
        self.assertEqual(first["total_events"], 1)


class DeterministicEventIdTests(unittest.TestCase):
    def test_same_inputs_same_id(self) -> None:
        e1 = {"event_type": "rag_ask", "ts": "2026-04-27T15:00:00+00:00", "prompt": "x"}
        e2 = {"event_type": "rag_ask", "ts": "2026-04-27T15:00:00+00:00", "prompt": "x"}
        self.assertEqual(
            learner_memory._deterministic_event_id(e1),
            learner_memory._deterministic_event_id(e2),
        )

    def test_different_prompts_different_ids(self) -> None:
        e1 = {"event_type": "rag_ask", "ts": "2026-04-27T15:00:00+00:00", "prompt": "x"}
        e2 = {"event_type": "rag_ask", "ts": "2026-04-27T15:00:00+00:00", "prompt": "y"}
        self.assertNotEqual(
            learner_memory._deterministic_event_id(e1),
            learner_memory._deterministic_event_id(e2),
        )


if __name__ == "__main__":
    unittest.main()
