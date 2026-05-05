"""Regression: a single task-level `blocked` outcome must NOT escalate
to a fleet-wide stop.

Pre-fix bug (commit before this regression test): the worker loop in
``orchestrator_workers._run_worker_loop`` called
``orchestrator.request_stop()`` whenever a single completion gate
returned ``blocked=True`` (e.g. Pilot lock violation). That single
escalation wrote the ``state/orchestrator/stop.request`` flag, the
supervisor polled it, and 60 workers shut down for one rogue codex
output. This test pins the corrected contract: *blocked* stays on the
queue item; the fleet stays alive.
"""

from __future__ import annotations

import inspect

from scripts.workbench.core import orchestrator_workers as OW


def test_worker_loop_does_not_call_request_stop_on_blocked():
    """Source-level pin — the orchestrator_workers worker-loop
    function must not contain `request_stop()` inside the blocked
    branch. We assert on the source rather than running a full fleet
    because spawning codex is heavy; this catches the regression at
    import time.
    """
    src = inspect.getsource(OW)
    # The pre-fix line was:
    #     if blocked:
    #         orchestrator.request_stop()
    # That sequence anywhere in the module re-introduces the bug.
    bug_pattern_a = "if blocked:\n                        orchestrator.request_stop()"
    bug_pattern_b = "if blocked:\n        orchestrator.request_stop()"
    assert bug_pattern_a not in src, (
        "BUG REGRESSION: 'if blocked: orchestrator.request_stop()' is back. "
        "A single task-level blocked outcome must not call fleet-wide stop."
    )
    assert bug_pattern_b not in src, (
        "BUG REGRESSION: 'if blocked: orchestrator.request_stop()' (alt indent) is back."
    )


def test_request_stop_only_callsites_are_explicit_user_actions():
    """``request_stop()`` should only be called from the explicit
    fleet-stop CLI path (cli.cmd_orchestrator_fleet_stop) and from
    ``stop_fleet()`` helper. Any other call site is suspicious."""
    src = inspect.getsource(OW)
    # Count *non-comment* call sites — strip comment-only lines first
    # so the regression-explanation comment in the worker loop doesn't
    # trip this guard.
    code_lines = [
        line for line in src.splitlines()
        if ".request_stop(" in line and not line.lstrip().startswith("#")
    ]
    # Only `stop_fleet()` should call it (fleet-stop CLI path).
    # If the worker loop adds another call, this assertion catches it.
    assert len(code_lines) <= 1, (
        f"Unexpected orchestrator.request_stop() call sites in "
        f"orchestrator_workers.py:\n  " + "\n  ".join(code_lines) +
        f"\nexpected ≤ 1 (the stop_fleet helper)."
    )
