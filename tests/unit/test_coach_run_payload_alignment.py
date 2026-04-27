"""Coach-run hook 후속 패치 회귀 테스트.

Peer review가 짚은 두 가지 미스매치를 막는다:

  1. 실제 `session_payload`는 `learning_point_recommendations` 형태로 오는데
     초기 builder가 `primary_learning_points` 키만 보고 있어 production에서
     concept_ids가 비어 채워지는 버그.
  2. `had_negative_feedback`이 flat top-level 필드만 봤기 때문에 실제로
     review 정보가 nested된 `current_pr.review_decision` / `pr_report_evidence`
     에 있을 때 시그널을 놓치는 문제.

또한 `bin/learn-test --path`만 줬을 때 모듈 추론이 동작하는지(Medium 3)도
함께 검증.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

import cli as workbench_cli  # noqa: E402
from core import concept_catalog, learner_memory  # noqa: E402


JUNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="cholog.BeanTest" tests="1" failures="0" errors="0" skipped="0" time="0.1">
  <testcase name="registerBean" classname="cholog.BeanTest" time="0.1"/>
</testsuite>
"""


class _Isolated(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.learner_dir = tmp_root / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)
        history = self.learner_dir / "history.jsonl"
        profile = self.learner_dir / "profile.json"
        summary = self.learner_dir / "summary.json"
        identity = self.learner_dir / "identity.json"
        self.history_path = history

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "alignment-tester"

        def _restore_env() -> None:
            if prev_env is None:
                os.environ.pop("WOOWA_LEARNER_ID", None)
            else:
                os.environ["WOOWA_LEARNER_ID"] = prev_env
        self.addCleanup(_restore_env)

        for p in [
            patch.object(learner_memory, "LEARNER_DIR", self.learner_dir),
            patch.object(learner_memory, "ensure_learner_layout", lambda: self.learner_dir),
            patch.object(learner_memory, "learner_history_path", lambda: history),
            patch.object(learner_memory, "learner_profile_path", lambda: profile),
            patch.object(learner_memory, "learner_summary_path", lambda: summary),
            patch.object(learner_memory, "learner_identity_path", lambda: identity),
        ]:
            p.start()
            self.addCleanup(p.stop)
        concept_catalog.reset_cache()

    def _events(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class CoachRunBuilderProductionShapeTests(_Isolated):
    """`session_payload`의 실제 production 모양(session.py:107)으로 테스트."""

    def test_concept_ids_extracted_from_learning_point_recommendations(self) -> None:
        catalog = concept_catalog.load_catalog()
        # 실제 session_payload — primary_learning_points 키 자체가 없음.
        production_payload = {
            "session_type": "session_start",
            "repo": "spring-roomescape-admin",
            "mode": "coach",
            "current_pr": {"number": 14},
            "learning_point_recommendations": [
                {
                    "learning_point": "transaction_consistency",
                    "label": "트랜잭션",
                    "primary_candidate": {"pr_number": 100, "title": "..."},
                },
                {
                    "learning_point": "db_modeling",
                    "label": "DB 모델링",
                    "primary_candidate": {"pr_number": 200},
                },
            ],
            "response": {"summary": [], "answer": []},
        }
        event = learner_memory.build_coach_run_event(
            session_payload=production_payload,
            learner_id="alignment-tester",
            catalog=catalog,
        )
        self.assertIn("concept:spring/transactional", event["concept_ids"])
        self.assertIn("concept:spring/jpa-entity", event["concept_ids"])  # db_modeling
        self.assertEqual(
            event["primary_learning_points"],
            ["transaction_consistency", "db_modeling"],
        )

    def test_falls_back_to_primary_learning_points_for_fixture_callers(self) -> None:
        # 일부 호출자는 builder를 직접 부르며 primary_learning_points만 넘김.
        catalog = concept_catalog.load_catalog()
        fixture_payload = {
            "repo": "x",
            "current_pr": {"number": 1},
            "primary_learning_points": ["transaction_consistency"],
        }
        event = learner_memory.build_coach_run_event(
            session_payload=fixture_payload,
            learner_id="alignment-tester",
            catalog=catalog,
        )
        self.assertIn("concept:spring/transactional", event["concept_ids"])


class NegativeFeedbackNestedSignalsTests(_Isolated):
    def test_nested_current_pr_review_decision_picks_up_negative(self) -> None:
        catalog = concept_catalog.load_catalog()
        payload = {
            "repo": "x",
            "current_pr": {"number": 7, "review_decision": "REQUEST_CHANGES"},
            "learning_point_recommendations": [
                {"learning_point": "transaction_consistency"}
            ],
        }
        event = learner_memory.build_coach_run_event(
            session_payload=payload, learner_id="alignment-tester", catalog=catalog,
        )
        self.assertTrue(event["had_negative_feedback"])

    def test_evidence_packet_mentor_comments_picks_up_negative(self) -> None:
        catalog = concept_catalog.load_catalog()
        payload = {
            "repo": "x",
            "current_pr": {"number": 7},
            "pr_report_evidence": {
                "mentor_comment_samples": [
                    {"body": "여기 트랜잭션 다시 봐 주세요"},
                ]
            },
            "learning_point_recommendations": [
                {"learning_point": "transaction_consistency"}
            ],
        }
        event = learner_memory.build_coach_run_event(
            session_payload=payload, learner_id="alignment-tester", catalog=catalog,
        )
        self.assertTrue(event["had_negative_feedback"])

    def test_no_signals_returns_false(self) -> None:
        catalog = concept_catalog.load_catalog()
        payload = {
            "repo": "x",
            "current_pr": {"number": 7},
            "learning_point_recommendations": [
                {"learning_point": "transaction_consistency"}
            ],
        }
        event = learner_memory.build_coach_run_event(
            session_payload=payload, learner_id="alignment-tester", catalog=catalog,
        )
        self.assertFalse(event["had_negative_feedback"])


class LearnTestPathOnlyInfersModuleTests(_Isolated):
    def setUp(self) -> None:
        super().setUp()
        # 실제 mission 디렉토리 모양과 동일하게 임시 디렉토리 구성.
        self.mission_results = (
            Path(self.tmp.name)
            / "missions"
            / "spring-learning-test"
            / "spring-jdbc-1"
            / "build"
            / "test-results"
            / "test"
        )
        self.mission_results.mkdir(parents=True, exist_ok=True)
        (self.mission_results / "TEST-cholog.JdbcTest.xml").write_text(
            JUNIT_XML, encoding="utf-8"
        )
        self._stdout = io.StringIO()
        self._stdout_patch = patch.object(sys, "stdout", self._stdout)
        self._stdout_patch.start()
        self.addCleanup(self._stdout_patch.stop)

    def test_path_only_call_records_with_inferred_module(self) -> None:
        ns = argparse.Namespace(
            module=None,
            path=str(self.mission_results),
            no_record=False,
        )
        rc = workbench_cli.cmd_learn_test(ns)
        self.assertEqual(rc, 0)
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["module"], "spring-jdbc-1")
        self.assertEqual(events[0]["module_context"], "spring-jdbc-1")
        # JSON output also reflects the inferred module.
        out = json.loads(self._stdout.getvalue().strip().splitlines()[-1])
        self.assertEqual(out["module"], "spring-jdbc-1")


if __name__ == "__main__":
    unittest.main()
