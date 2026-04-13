"""Unit tests for scripts.workbench.core.response_contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.workbench.core.response_contract import (  # noqa: E402
    build_response_contract,
    build_snapshot_block,
    build_verification_block,
)
from scripts.workbench.core.schema_validation import validate_payload  # noqa: E402


def _thread(
    *,
    tid,
    classification: str,
    path: str = "src/Foo.java",
    line: int | None = 10,
    reason: str | None = "heuristic",
    reactions=None,
    self_reply: str | None = None,
    learner_acknowledged=None,
) -> dict:
    participants: list[dict] = []
    if self_reply is not None:
        participants.append({"role": "self", "body_excerpt": self_reply})
    return {
        "id": tid,
        "path": path,
        "line": line,
        "classification": classification,
        "classification_reason": reason,
        "participants": participants,
        "learner_reactions": reactions or [],
        "learner_acknowledged": learner_acknowledged,
    }


def _snapshot(threads: list[dict]) -> dict:
    return {
        "computed_at": "2026-04-13T00:00:00Z",
        "head_branch": "step2",
        "target_pr_number": 346,
        "target_pr_selection_reason": "latest_open_pr",
        "target_pr_detail": {"threads": threads},
    }


class SnapshotBlockTest(unittest.TestCase):
    def test_full_shape_and_markdown(self) -> None:
        threads = [
            _thread(tid=1, classification="still-applies"),
            _thread(tid=2, classification="likely-fixed", reactions=[{"content": "THUMBS_UP"}]),
            _thread(tid=3, classification="already-fixed", self_reply="applied"),
            _thread(tid=4, classification="ambiguous", learner_acknowledged="unknown"),
            _thread(tid=5, classification="unread"),
        ]
        block = build_snapshot_block(_snapshot(threads), "ready")

        self.assertEqual(block["reason"], "ready")
        self.assertEqual(block["target_pr_number"], 346)
        self.assertEqual(block["computed_at"], "2026-04-13T00:00:00Z")

        counts = block["counts"]
        self.assertEqual(counts["total"], 5)
        self.assertEqual(counts["classification"]["still-applies"], 1)
        self.assertEqual(counts["classification"]["likely-fixed"], 1)
        self.assertEqual(counts["classification"]["already-fixed"], 1)
        self.assertEqual(counts["classification"]["ambiguous"], 1)
        self.assertEqual(counts["classification"]["unread"], 1)
        self.assertEqual(sum(counts["classification"].values()), 5)

        # reply axis priority: self body → text, then reactions → emoji,
        # then learner_acknowledged=="unknown" → unknown, else none.
        self.assertEqual(counts["reply_axis"]["text"], 1)
        self.assertEqual(counts["reply_axis"]["emoji"], 1)
        self.assertEqual(counts["reply_axis"]["unknown"], 1)
        self.assertEqual(counts["reply_axis"]["none"], 2)
        self.assertEqual(sum(counts["reply_axis"].values()), 5)

        md = block["markdown"]
        self.assertIsNotNone(md)
        self.assertTrue(md.startswith("## 상태 요약 (snapshot, computed_at=2026-04-13T00:00:00Z)"))
        self.assertIn("- 스레드 5개:", md)
        self.assertIn("  - still-applies: 1", md)
        self.assertIn("  - unread: 1", md)
        self.assertIn("  - 텍스트 답글: 1", md)
        self.assertIn("  - 불명: 1", md)

    def test_unexpected_classification_raises(self) -> None:
        threads = [_thread(tid=1, classification="bogus-bucket")]
        with self.assertRaises(ValueError):
            build_snapshot_block(_snapshot(threads), "ready")

    def test_blocked_returns_null_markdown(self) -> None:
        block = build_snapshot_block(_snapshot([]), "blocked")
        self.assertIsNone(block["markdown"])
        self.assertIsNone(block["counts"])
        self.assertEqual(block["reason"], "blocked")

    def test_no_target_pr(self) -> None:
        snap = {
            "computed_at": "2026-04-13T00:00:00Z",
            "target_pr_number": None,
            "target_pr_selection_reason": "no_open_pr",
            "target_pr_detail": None,
        }
        block = build_snapshot_block(snap, "ready")
        self.assertIsNone(block["markdown"])
        self.assertIsNone(block["counts"])
        self.assertEqual(block["reason"], "no_target_pr")


class VerificationBlockTest(unittest.TestCase):
    def test_only_likely_fixed_and_ambiguous(self) -> None:
        threads = [
            _thread(tid=1, classification="still-applies", path="a.java", line=1),
            _thread(tid=2, classification="likely-fixed", path="b.java", line=2, reason="hunk_overlap"),
            _thread(tid=3, classification="already-fixed", path="c.java", line=3),
            _thread(tid=4, classification="ambiguous", path="a.java", line=9, reason="no_hunk"),
            _thread(tid=5, classification="unread", path="d.java", line=4),
        ]
        block = build_verification_block(_snapshot(threads), "ready")

        self.assertEqual(block["required_count"], 2)
        self.assertEqual(len(block["thread_refs"]), 2)
        # Deterministic sort: ambiguous first, then likely-fixed;
        # inside a class, by path ascending.
        self.assertEqual(
            [r["classification"] for r in block["thread_refs"]],
            ["ambiguous", "likely-fixed"],
        )
        self.assertEqual(block["thread_refs"][0]["path"], "a.java")
        self.assertEqual(block["thread_refs"][0]["line"], 9)
        self.assertIn("a.java", block["stub_markdown"])
        self.assertIn("b.java", block["stub_markdown"])
        self.assertTrue(block["stub_markdown"].startswith("## 수동 확인 필요"))

    def test_empty_when_none_required(self) -> None:
        threads = [
            _thread(tid=1, classification="still-applies"),
            _thread(tid=2, classification="already-fixed"),
        ]
        block = build_verification_block(_snapshot(threads), "ready")
        self.assertEqual(block["required_count"], 0)
        self.assertEqual(block["thread_refs"], [])
        self.assertIsNone(block["stub_markdown"])

    def test_blocked_returns_empty(self) -> None:
        block = build_verification_block(_snapshot([]), "blocked")
        self.assertEqual(block, {"required_count": 0, "thread_refs": [], "stub_markdown": None})


class BuildResponseContractTest(unittest.TestCase):
    def _make_minimal_valid_payload(self, snapshot: dict | None, status: str) -> dict:
        return {
            "run_type": "coach_run",
            "execution_status": status,
            "generated_at": "2026-04-13T00:00:00Z",
            "repo": "java-janggi",
            "repo_resolution": {},
            "archive_sync": {},
            "archive_status": {
                "bootstrap_state": "ready",
                "data_confidence": "ready",
            },
            "session": {},
            "memory": {},
            "coach_reply": {
                "memory_notes": [],
                "response": {},
                "markdown": "stub\n",
            },
            "response_contract": build_response_contract(snapshot, status),
        }

    def test_wrapper_ready_passes_validator(self) -> None:
        threads = [
            _thread(tid=1, classification="still-applies"),
            _thread(tid=2, classification="likely-fixed"),
        ]
        payload = self._make_minimal_valid_payload(_snapshot(threads), "ready")
        # Raises on failure.
        validate_payload("coach-run-result", payload)

        rc = payload["response_contract"]
        self.assertEqual(rc["verification"]["required_count"], 1)
        self.assertIsNotNone(rc["snapshot_block"]["markdown"])

    def test_wrapper_blocked_with_none_snapshot_passes_validator(self) -> None:
        payload = self._make_minimal_valid_payload(None, "blocked")
        validate_payload("coach-run-result", payload)

        rc = payload["response_contract"]
        self.assertIsNone(rc["snapshot_block"]["markdown"])
        self.assertEqual(rc["verification"]["required_count"], 0)
        self.assertEqual(rc["verification"]["thread_refs"], [])


if __name__ == "__main__":
    unittest.main()
