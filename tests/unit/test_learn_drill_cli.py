"""Standalone drill CLI 회귀.

학습 흐름:
  offer   → drill-pending.json 생성 + 학습자에게 question 노출
  answer  → score_pending_answer 호출 → drill_answer event append → pending 클리어
  status  → 현재 pending 보기
  cancel  → pending 폐기

회귀 대상:
- 명시 concept_id로 offer
- profile.uncertain에서 자동 picking
- pending 이미 있으면 force 없이는 거부
- answer 시 drill_answer 이벤트가 history.jsonl에 기록되는지
- 채점 결과(점수/약점)가 stdout JSON으로 노출되는지
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


class _DrillIsolated(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.learner_dir = tmp_root / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.learner_dir / "history.jsonl"
        self.profile_path = self.learner_dir / "profile.json"
        self.summary_path = self.learner_dir / "summary.json"
        self.identity_path = self.learner_dir / "identity.json"
        self.pending_path = self.learner_dir / "drill-pending.json"

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "drill-tester"

        def _restore_env() -> None:
            if prev_env is None:
                os.environ.pop("WOOWA_LEARNER_ID", None)
            else:
                os.environ["WOOWA_LEARNER_ID"] = prev_env
        self.addCleanup(_restore_env)

        # learner_memory는 import 시점에 path helper들을 그대로 들고 있으니
        # 동일한 함수 객체를 cli에서도 쓰도록 patch.
        for p in [
            patch.object(learner_memory, "LEARNER_DIR", self.learner_dir),
            patch.object(learner_memory, "ensure_learner_layout", lambda: self.learner_dir),
            patch.object(learner_memory, "learner_history_path", lambda: self.history_path),
            patch.object(learner_memory, "learner_profile_path", lambda: self.profile_path),
            patch.object(learner_memory, "learner_summary_path", lambda: self.summary_path),
            patch.object(learner_memory, "learner_identity_path", lambda: self.identity_path),
        ]:
            p.start()
            self.addCleanup(p.stop)

        # cli의 helper들이 `from core.paths import learner_drill_pending_path`
        # 처럼 새로 import할 때 우리 학습자 디렉토리를 가리키도록 paths 모듈 자체에도 stamp.
        from core import paths as paths_module
        for p in [
            patch.object(paths_module, "LEARNER_DIR", self.learner_dir),
            patch.object(paths_module, "learner_drill_pending_path", lambda: self.pending_path),
            patch.object(paths_module, "learner_history_path", lambda: self.history_path),
            patch.object(paths_module, "learner_profile_path", lambda: self.profile_path),
            patch.object(paths_module, "learner_summary_path", lambda: self.summary_path),
            patch.object(paths_module, "learner_identity_path", lambda: self.identity_path),
        ]:
            p.start()
            self.addCleanup(p.stop)

        concept_catalog.reset_cache()

        self._stdout = io.StringIO()
        self._stdout_patch = patch.object(sys, "stdout", self._stdout)
        self._stdout_patch.start()
        self.addCleanup(self._stdout_patch.stop)

    def _events(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _stdout_json(self) -> dict:
        out = self._stdout.getvalue().strip().splitlines()[-1]
        # 마지막 라인이 JSON이 아니라 첫 라인부터 multi-line일 수도 있으니 fallback.
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return json.loads(self._stdout.getvalue())


class OfferTests(_DrillIsolated):
    def test_offer_with_explicit_concept_writes_pending(self) -> None:
        ns = argparse.Namespace(
            drill_command="offer",
            concept="concept:spring/di",
            force=False,
        )
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 0)
        self.assertTrue(self.pending_path.exists())
        pending = json.loads(self.pending_path.read_text(encoding="utf-8"))
        self.assertEqual(pending["concept_id"], "concept:spring/di")
        self.assertIn("question", pending)
        self.assertGreater(len(pending["expected_terms"]), 0)

    def test_offer_picks_uncertain_when_no_concept_arg(self) -> None:
        # 자연스러운 시스템 흐름: history에 ≥3 rag_ask가 누적되면 그 concept이
        # uncertain으로 잡히고, drill offer가 그걸 자동 선택.
        from datetime import datetime, timedelta, timezone

        def _ts(days_ago: float) -> str:
            return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(
                timespec="seconds"
            )
        events = [
            {
                "event_type": "rag_ask",
                "event_id": f"e{i}",
                "ts": _ts(i * 0.1),
                "learner_id": "drill-tester",
                "concept_ids": ["concept:spring/jpa-entity"],
                "prompt": f"jpa entity 질문 {i}",
                "question_fingerprint": f"q{i}",
                "tier": 1,
                "rag_mode": "cheap",
                "experience_level_inferred": "beginner",
                "category_hits": [],
                "top_paths": [],
                "rag_ready": True,
                "blocked": False,
            }
            for i in range(4)
        ]
        with self.history_path.open("w", encoding="utf-8") as fh:
            for e in events:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        learner_memory.recompute_learner_profile()

        ns = argparse.Namespace(drill_command="offer", concept=None, force=False)
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 0)
        pending = json.loads(self.pending_path.read_text(encoding="utf-8"))
        self.assertEqual(pending["concept_id"], "concept:spring/jpa-entity")

    def test_offer_refuses_when_pending_exists_without_force(self) -> None:
        self.pending_path.write_text(json.dumps({"existing": True}), encoding="utf-8")
        ns = argparse.Namespace(
            drill_command="offer",
            concept="concept:spring/di",
            force=False,
        )
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 2)

    def test_offer_with_force_overwrites_pending(self) -> None:
        self.pending_path.write_text(json.dumps({"existing": True}), encoding="utf-8")
        ns = argparse.Namespace(
            drill_command="offer",
            concept="concept:spring/di",
            force=True,
        )
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 0)
        pending = json.loads(self.pending_path.read_text(encoding="utf-8"))
        self.assertEqual(pending["concept_id"], "concept:spring/di")

    def test_offer_unknown_concept_returns_error(self) -> None:
        ns = argparse.Namespace(
            drill_command="offer",
            concept="concept:fake/nonexistent",
            force=False,
        )
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 2)


class AnswerTests(_DrillIsolated):
    def _seed_pending(self, concept_id: str = "concept:spring/di") -> dict:
        catalog = concept_catalog.load_catalog()
        concept = catalog["concepts"][concept_id]
        offer = {
            "drill_session_id": "test-sid-1",
            "concept_id": concept_id,
            "linked_learning_point": concept_id,
            "question": "DI를 설명하세요",
            "expected_terms": [a.lower() for a in concept["aliases"]][:5],
            "source_doc": None,
            "created_at": "2026-04-28T00:00:00+00:00",
            "ttl_turns": 5,
        }
        self.pending_path.write_text(
            json.dumps(offer, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return offer

    def test_answer_scores_appends_event_clears_pending(self) -> None:
        self._seed_pending()
        rich_answer = (
            "Dependency Injection은 객체가 필요로 하는 다른 객체(의존성)를 컨테이너가 "
            "외부에서 주입해 주는 방식이다. constructor injection으로 final 필드에 받으면 "
            "테스트하기 쉽고 불변성이 보장된다. 예를 들어 OrderService가 OrderRepository를 "
            "생성자 파라미터로 받으면 컨테이너가 적절한 구현체를 찾아 주입한다. "
            "@Autowired 어노테이션으로도 표시할 수 있고, setter 주입도 가능하지만 "
            "필수 의존성은 생성자 주입이 권장된다."
        )
        ns = argparse.Namespace(drill_command="answer", answer=rich_answer)
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 0)
        # pending cleared
        self.assertFalse(self.pending_path.exists())
        # event recorded
        events = self._events()
        drill_events = [e for e in events if e["event_type"] == "drill_answer"]
        self.assertEqual(len(drill_events), 1)
        self.assertIn("concept:spring/di", drill_events[0]["concept_ids"])
        self.assertGreaterEqual(drill_events[0]["total_score"], 1)

    def test_answer_without_pending_returns_error(self) -> None:
        ns = argparse.Namespace(drill_command="answer", answer="something")
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 2)

    def test_answer_empty_text_returns_error(self) -> None:
        self._seed_pending()
        ns = argparse.Namespace(drill_command="answer", answer="")
        with patch.object(sys, "stdin", io.StringIO("")):
            rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 2)
        # pending should still exist (not consumed)
        self.assertTrue(self.pending_path.exists())


class StatusCancelTests(_DrillIsolated):
    def test_status_no_pending(self) -> None:
        ns = argparse.Namespace(drill_command="status")
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 0)
        out = json.loads(self._stdout.getvalue().strip())
        self.assertFalse(out["pending"])

    def test_status_with_pending_returns_question(self) -> None:
        self.pending_path.write_text(
            json.dumps(
                {
                    "drill_session_id": "x",
                    "concept_id": "concept:spring/di",
                    "question": "Q?",
                    "ttl_turns": 5,
                    "created_at": "2026-04-28T00:00:00+00:00",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        ns = argparse.Namespace(drill_command="status")
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 0)
        out = json.loads(self._stdout.getvalue().strip())
        self.assertTrue(out["pending"])
        self.assertEqual(out["concept_id"], "concept:spring/di")

    def test_cancel_clears_pending(self) -> None:
        self.pending_path.write_text("{}", encoding="utf-8")
        ns = argparse.Namespace(drill_command="cancel")
        rc = workbench_cli.cmd_learn_drill(ns)
        self.assertEqual(rc, 0)
        self.assertFalse(self.pending_path.exists())


if __name__ == "__main__":
    unittest.main()
