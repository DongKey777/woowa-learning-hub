"""Regression tests for _fetch_thread_graph fallback paths.

Guards the invariant that every ``graph_ok=False`` return leaves a
``budget.skipped[]`` entry so operators can trace why tri-state fields
collapsed to ``"unknown"``.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.workbench.core import learner_state  # noqa: E402


class ForcedGraphFailTest(unittest.TestCase):
    def test_forced_fail_logs_skipped_and_returns_empty(self) -> None:
        budget = learner_state._Budget()
        with mock.patch.dict(os.environ, {"WOOWA_FORCE_GRAPHQL_FAIL": "test"}):
            resolved, reactions, ok = learner_state._fetch_thread_graph(
                "woowacourse/java-janggi", 1, budget
            )
        self.assertEqual(resolved, {})
        self.assertEqual(reactions, {})
        self.assertFalse(ok)
        self.assertTrue(
            any(
                s.get("what") == "graphql reviewThreads"
                and s.get("reason", "").startswith("forced:")
                for s in budget.skipped
            ),
            f"expected forced:* skipped entry, got {budget.skipped!r}",
        )

    def test_invalid_upstream_logs_skipped(self) -> None:
        budget = learner_state._Budget()
        # Ensure the forced env hook is not set so we fall through to the
        # upstream parse branch.
        env = {k: v for k, v in os.environ.items() if k != "WOOWA_FORCE_GRAPHQL_FAIL"}
        with mock.patch.dict(os.environ, env, clear=True):
            resolved, reactions, ok = learner_state._fetch_thread_graph(
                "no-slash-here", 1, budget
            )
        self.assertEqual(resolved, {})
        self.assertEqual(reactions, {})
        self.assertFalse(ok)
        self.assertTrue(
            any(
                s.get("what") == "graphql reviewThreads"
                and s.get("reason") == "invalid_upstream"
                for s in budget.skipped
            ),
            f"expected invalid_upstream skipped entry, got {budget.skipped!r}",
        )


if __name__ == "__main__":
    unittest.main()
