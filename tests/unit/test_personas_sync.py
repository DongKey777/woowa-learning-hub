"""Persona sync sanity test.

Ensures that the rendered Claude/Codex/Gemini persona files match the
single-source bodies + per-host headers in ``docs/agent-personas/``. Any
hand-edit to one of the rendered files will fail this test, forcing the
edit back into the canonical body or header fragment.
"""

from __future__ import annotations

import unittest

from scripts.sync_personas import cmd_check


class PersonaSyncTest(unittest.TestCase):
    def test_personas_in_sync(self) -> None:
        self.assertEqual(cmd_check(), 0)


if __name__ == "__main__":
    unittest.main()
