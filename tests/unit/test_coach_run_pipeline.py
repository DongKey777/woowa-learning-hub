"""Direct unit coverage for ``coach_run.run_coach``.

Strategy: patch upper-layer seams in the ``coach_run`` module namespace
(``resolve_repo_input``, ``compute_archive_status``, ``ensure_repo_archive``,
``start_session``, ``compute_memory_update``, ``build_response_contract``,
``validate_payload``, ``commit_history_entry``, ``commit_memory_snapshot``,
``repo_action_dir``, ``repo_context_dir``, ``_learner_state_snapshot``,
``_pre_augment_phase``, ``_check_cs_readiness``) so the pipeline runs
end-to-end without touching disk archives, ML deps, or the schema layer.

Goals:
- Lock in the actual blocked branch (`bootstrap_state == "uninitialized"`).
- Lock in the (currently uncovered) `ensure_repo_archive` raise propagation.
- Cover the canonical-write → sidecar-fallback ladder, narrowly: only
  ``coach-run.json`` / ``coach-run.error.json`` writes are simulated to fail.
- Lock in the Phase-2 write order documented at coach_run.py:855-861.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.workbench.core import coach_run as cr


def _ok_response_contract(*_args, **_kwargs) -> dict:
    """Minimal RC payload that satisfies ``_assert_response_contract``.

    snapshot_block.reason="no_target_pr" skips the deep ready-state check,
    while still honoring the structural assertions.
    """
    return {
        "snapshot_block": {
            "reason": "no_target_pr",
            "markdown": None,
            "counts": None,
            "computed_at": None,
            "target_pr_number": None,
            "target_pr_selection_reason": None,
        },
        "verification": {
            "required_count": 0,
            "thread_refs": [],
            "stub_markdown": None,
        },
        "cs_block": {"reason": "no_augmentation", "markdown": None,
                     "sources": [], "applicability_hint": "omit"},
        "drill_block": {"reason": "none", "markdown": None,
                        "applicability_hint": "omit"},
        "drill_result_block": {"reason": "none", "markdown": None,
                               "applicability_hint": "omit"},
    }


def _fake_session_payload() -> dict:
    return {
        "mode": "coach",
        "prompt": "테스트 질문",
        "response": {"summary": "ok", "answer": "ok"},
        "primary_intent": "ask",
        "primary_topic": "general",
        "learning_point_recommendations": [],
        "focus_candidates": [],
        "mission_map_summary": [],
    }


def _fake_memory(profile_extra: dict | None = None) -> dict:
    profile = {"confidence": "low", "dominant_learning_points": []}
    if profile_extra:
        profile.update(profile_extra)
    return {
        "history_path": None,
        "summary_path": None,
        "profile_path": None,
        "summary": {"top_learning_points": []},
        "profile": profile,
    }


def _install_common_patches(stack: "ExitStack", *, action_dir: Path,
                            context_dir: Path,
                            archive_status: dict,
                            ensure_archive_side_effect=None,
                            cs_readiness: dict | None = None) -> dict:
    """Install the seam patches shared by every scenario.

    Returns a dict of named MagicMocks so individual tests can assert on
    ``mock_calls``/order without re-deriving them.
    """
    repo_obj = {"name": "demo-repo", "path": None, "upstream": None}
    resolution = {"source": "registry"}

    mocks = {}
    mocks["resolve_repo_input"] = stack.enter_context(
        mock.patch.object(cr, "resolve_repo_input",
                          return_value=(repo_obj, resolution))
    )
    mocks["needs_recompute"] = stack.enter_context(
        mock.patch.object(cr, "needs_recompute", return_value=False)
    )
    mocks["recompute_from_history"] = stack.enter_context(
        mock.patch.object(cr, "recompute_from_history", return_value=None)
    )
    mocks["load_learning_memory"] = stack.enter_context(
        mock.patch.object(cr, "load_learning_memory", return_value=_fake_memory())
    )
    mocks["_learner_state_snapshot"] = stack.enter_context(
        mock.patch.object(cr, "_learner_state_snapshot",
                          return_value=(None, None))
    )
    mocks["compute_archive_status"] = stack.enter_context(
        mock.patch.object(cr, "compute_archive_status",
                          return_value=archive_status)
    )
    mocks["write_archive_status"] = stack.enter_context(
        mock.patch.object(cr, "write_archive_status", return_value=None)
    )
    mocks["ensure_repo_archive"] = stack.enter_context(
        mock.patch.object(
            cr, "ensure_repo_archive",
            side_effect=ensure_archive_side_effect,
            return_value={"skipped": False, "mode": "incremental"},
        )
    )
    if ensure_archive_side_effect is None:
        # mock.patch with both side_effect and return_value: side_effect=None
        # means "use return_value", which is what we want.
        pass
    mocks["start_session"] = stack.enter_context(
        mock.patch.object(cr, "start_session", return_value=_fake_session_payload())
    )
    mocks["_pre_augment_phase"] = stack.enter_context(
        mock.patch.object(
            cr, "_pre_augment_phase",
            return_value={
                "pre_result": {"pre_intent": "mission_only",
                               "cs_search_mode": "skip"},
                "cs_readiness": cs_readiness or {"state": "ready",
                                                  "reason": "ok",
                                                  "next_command": None,
                                                  "corpus_hash": None,
                                                  "index_manifest_hash": None},
                "cs_augmentation_compact": None,
                "sidecar": None,
                "drill_result": None,
                "consumed_pending_id": None,
                "route_signals": {},
            },
        )
    )
    mocks["_check_cs_readiness"] = stack.enter_context(
        mock.patch.object(
            cr, "_check_cs_readiness",
            return_value=cs_readiness or {"state": "ready", "reason": "ok",
                                          "next_command": None,
                                          "corpus_hash": None,
                                          "index_manifest_hash": None},
        )
    )
    mocks["_build_learning_projection"] = stack.enter_context(
        mock.patch.object(cr, "_build_learning_projection", return_value=None)
    )
    mocks["compute_memory_update"] = stack.enter_context(
        mock.patch.object(
            cr, "compute_memory_update",
            return_value={
                "history_path": None, "summary_path": None, "profile_path": None,
                "summary": {"top_learning_points": []},
                "profile": {"confidence": "low", "dominant_learning_points": []},
            },
        )
    )
    mocks["_build_unified_profile"] = stack.enter_context(
        mock.patch.object(cr, "_build_unified_profile", return_value=None)
    )
    mocks["intent_finalize"] = stack.enter_context(
        mock.patch.object(
            cr, "intent_finalize",
            return_value={
                "detected_intent": "mission_only",
                "pre_intent": "mission_only",
                "cs_search_mode": "skip",
                "signals": {},
                "block_plan": {"snapshot_block": "primary", "cs_block": "omit",
                               "verification": "omit", "drill_block": "omit"},
            },
        )
    )
    mocks["_render_coach_reply"] = stack.enter_context(
        mock.patch.object(cr, "_render_coach_reply", return_value="# reply")
    )
    mocks["build_response_contract"] = stack.enter_context(
        mock.patch.object(cr, "build_response_contract",
                          side_effect=_ok_response_contract)
    )
    mocks["build_verification_block"] = stack.enter_context(
        mock.patch.object(cr, "build_verification_block",
                          return_value={"required_count": 0, "thread_refs": [],
                                        "stub_markdown": None})
    )
    mocks["enforce_budget"] = stack.enter_context(
        mock.patch.object(cr, "enforce_budget", side_effect=lambda x: x)
    )
    mocks["validate_payload"] = stack.enter_context(
        mock.patch.object(cr, "validate_payload", return_value=None)
    )
    mocks["commit_history_entry"] = stack.enter_context(
        mock.patch.object(cr, "commit_history_entry", return_value=None)
    )
    mocks["commit_memory_snapshot"] = stack.enter_context(
        mock.patch.object(cr, "commit_memory_snapshot", return_value=None)
    )
    mocks["repo_action_dir"] = stack.enter_context(
        mock.patch.object(cr, "repo_action_dir", return_value=action_dir)
    )
    mocks["repo_context_dir"] = stack.enter_context(
        mock.patch.object(cr, "repo_context_dir", return_value=context_dir)
    )
    return mocks


# ExitStack import kept local to avoid polluting the module top with rarely
# used imports.
from contextlib import ExitStack  # noqa: E402


class CoachRunPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.action_dir = Path(self._tmp.name) / "actions"
        self.context_dir = Path(self._tmp.name) / "contexts"
        self.action_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Scenario 1 — happy path
    # ------------------------------------------------------------------
    def test_happy_path_writes_canonical_payload(self) -> None:
        with ExitStack() as stack:
            mocks = _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "ready",
                                "data_confidence": "ready",
                                "signals": {}, "thresholds": {}},
            )

            payload = cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertEqual(payload["execution_status"], "ready")
        self.assertIn("response_contract", payload)
        rc = payload["response_contract"]
        for key in ("snapshot_block", "verification", "cs_block",
                    "drill_block", "drill_result_block"):
            self.assertIn(key, rc)

        canonical_path = self.action_dir / "coach-run.json"
        self.assertTrue(canonical_path.exists(),
                        "coach-run.json must be written on happy path")
        on_disk = json.loads(canonical_path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["execution_status"], "ready")

        # ensure_repo_archive was reached (proves we passed the blocked branch)
        self.assertEqual(mocks["ensure_repo_archive"].call_count, 1)
        # validate_payload runs after enforce_budget
        self.assertEqual(mocks["validate_payload"].call_count, 1)

    def test_review_due_offer_is_persisted_as_drill_pending(self) -> None:
        history = [{"drill_session_id": "drill-old", "question": "복습 질문"}]
        review_offer = {
            "drill_session_id": "drill-review",
            "question": "복습 질문",
            "ttl_turns": 3,
            "review_of_session_id": "drill-old",
            "review_count": 1,
        }
        with ExitStack() as stack:
            mocks = _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "ready",
                                "data_confidence": "ready",
                                "signals": {}, "thresholds": {}},
            )
            stack.enter_context(
                mock.patch("scripts.learning.drill.load_pending", return_value=None)
            )
            stack.enter_context(
                mock.patch("scripts.learning.drill.load_history", return_value=history)
            )
            build_review = stack.enter_context(
                mock.patch(
                    "scripts.learning.drill.build_review_offer_if_due",
                    return_value=review_offer,
                )
            )
            build_regular = stack.enter_context(
                mock.patch("scripts.learning.drill.build_offer_if_due", return_value=None)
            )
            save_pending = stack.enter_context(
                mock.patch("scripts.learning.drill.save_pending", return_value=None)
            )

            payload = cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertEqual(payload["execution_status"], "ready")
        self.assertEqual(payload["cognitive_trigger"]["reason"], "drill_offer_present")
        build_review.assert_called_once_with(history, pending=None)
        build_regular.assert_not_called()
        save_pending.assert_called_once_with("demo-repo", review_offer)
        self.assertIs(
            mocks["build_response_contract"].call_args.kwargs["drill_offer"],
            review_offer,
        )

    # ------------------------------------------------------------------
    # Scenario 2 — bootstrap_state=uninitialized → blocked branch
    # ------------------------------------------------------------------
    def test_uninitialized_archive_returns_blocked_payload(self) -> None:
        with ExitStack() as stack:
            mocks = _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "uninitialized",
                                "data_confidence": "bootstrap",
                                "signals": {}, "thresholds": {}},
            )

            payload = cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertEqual(payload["execution_status"], "blocked")
        self.assertTrue(payload["archive_sync"]["blocked"])
        self.assertIn("coach_reply", payload)
        # Blocked branch must NOT call ensure_repo_archive / start_session.
        mocks["ensure_repo_archive"].assert_not_called()
        mocks["start_session"].assert_not_called()
        # but it does write the canonical artifact (line 679).
        self.assertTrue((self.action_dir / "coach-run.json").exists())
        # And it touches write_archive_status to refresh status.json.
        mocks["write_archive_status"].assert_called_once()

    # ------------------------------------------------------------------
    # Scenario 3 — ensure_repo_archive exception propagates (known gap)
    # ------------------------------------------------------------------
    def test_ensure_repo_archive_exception_propagates(self) -> None:
        """Locks in the known gap: raises from ``ensure_repo_archive`` are
        currently NOT caught by ``run_coach``. Future fix can flip this to
        an error-payload assertion; for now we assert the raise so any
        accidental swallowing surfaces immediately.
        """
        boom = RuntimeError("archive boom")
        with ExitStack() as stack:
            _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "ready",
                                "data_confidence": "ready",
                                "signals": {}, "thresholds": {}},
                ensure_archive_side_effect=boom,
            )

            with self.assertRaises(RuntimeError) as ctx:
                cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertIs(ctx.exception, boom)
        # No coach-run.json should have been produced for this code path.
        self.assertFalse((self.action_dir / "coach-run.json").exists())

    # ------------------------------------------------------------------
    # Scenario 4 — canonical write fails → sidecar fallback fires
    # ------------------------------------------------------------------
    def test_canonical_write_failure_falls_back_to_sidecar(self) -> None:
        original_write_text = Path.write_text

        def selective_write(self, data, *args, **kwargs):
            if self.name == "coach-run.json":
                raise OSError("simulated canonical write failure")
            return original_write_text(self, data, *args, **kwargs)

        with ExitStack() as stack:
            _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "ready",
                                "data_confidence": "ready",
                                "signals": {}, "thresholds": {}},
            )
            stack.enter_context(
                mock.patch.object(Path, "write_text", selective_write)
            )

            payload = cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertEqual(payload["execution_status"], "error")
        self.assertTrue(payload.get("canonical_write_failed"))
        self.assertEqual(payload["error_detail"]["phase"], "coach_run_write")
        sidecar = self.action_dir / "coach-run.error.json"
        self.assertTrue(sidecar.exists(),
                        "fallback sidecar must be written when canonical fails")
        self.assertEqual(payload["error_detail"]["sidecar_path"], str(sidecar))
        self.assertEqual(payload["json_path"], str(sidecar))
        # Canonical file must not exist (write was simulated to fail).
        self.assertFalse((self.action_dir / "coach-run.json").exists())

    # ------------------------------------------------------------------
    # Scenario 5 — both canonical and sidecar writes fail
    # ------------------------------------------------------------------
    def test_canonical_and_sidecar_both_fail(self) -> None:
        def deny_both(self, data, *args, **kwargs):
            if self.name in ("coach-run.json", "coach-run.error.json"):
                raise OSError(f"simulated failure for {self.name}")
            return None  # other writes are no-ops in tests

        with ExitStack() as stack:
            _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "ready",
                                "data_confidence": "ready",
                                "signals": {}, "thresholds": {}},
            )
            stack.enter_context(
                mock.patch.object(Path, "write_text", deny_both)
            )

            payload = cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertEqual(payload["execution_status"], "error")
        self.assertTrue(payload.get("canonical_write_failed"))
        self.assertTrue(payload.get("write_fallback_exhausted"))
        self.assertIsNone(payload["error_detail"]["sidecar_path"])

    # ------------------------------------------------------------------
    # Scenario 6 — cs_readiness=missing must NOT downgrade execution_status
    # ------------------------------------------------------------------
    def test_cs_readiness_missing_keeps_ready_status(self) -> None:
        with ExitStack() as stack:
            _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "ready",
                                "data_confidence": "ready",
                                "signals": {}, "thresholds": {}},
                cs_readiness={"state": "missing", "reason": "deps_missing",
                              "next_command": "pip install -e .",
                              "corpus_hash": None,
                              "index_manifest_hash": None},
            )

            payload = cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertEqual(payload["execution_status"], "ready")
        self.assertEqual(payload["cs_readiness"]["state"], "missing")

    # ------------------------------------------------------------------
    # Scenario 7 — Phase 2 write order: history → coach-run → memory snapshot
    # ------------------------------------------------------------------
    def test_phase_two_write_order(self) -> None:
        order: list[str] = []
        with ExitStack() as stack:
            _install_common_patches(
                stack,
                action_dir=self.action_dir,
                context_dir=self.context_dir,
                archive_status={"bootstrap_state": "ready",
                                "data_confidence": "ready",
                                "signals": {}, "thresholds": {}},
            )
            stack.enter_context(
                mock.patch.object(
                    cr, "commit_history_entry",
                    side_effect=lambda *a, **k: order.append("history"),
                )
            )
            original_write_text = Path.write_text

            def tracking_write(self, data, *args, **kwargs):
                if self.name == "coach-run.json":
                    order.append("coach_run_write")
                return original_write_text(self, data, *args, **kwargs)

            stack.enter_context(
                mock.patch.object(Path, "write_text", tracking_write)
            )
            stack.enter_context(
                mock.patch.object(
                    cr, "commit_memory_snapshot",
                    side_effect=lambda *a, **k: order.append("memory_snapshot"),
                )
            )

            payload = cr.run_coach(repo_name="demo-repo", prompt="hi")

        self.assertEqual(payload["execution_status"], "ready")
        self.assertEqual(order, ["history", "coach_run_write", "memory_snapshot"])


if __name__ == "__main__":
    unittest.main()
