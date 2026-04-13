"""validate-state discovers CS/drill sidecars; missing is not_applicable."""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = REPO_ROOT / "scripts" / "workbench"
if str(WORKBENCH) not in sys.path:
    sys.path.insert(0, str(WORKBENCH))

cli = importlib.import_module("cli")


class DiscoverTargetsTest(unittest.TestCase):
    def _make_base(self) -> Path:
        tmp = tempfile.mkdtemp()
        base = Path(tmp)
        for sub in ("archive", "analysis", "profiles", "memory", "contexts", "actions", "packets"):
            (base / sub).mkdir(parents=True, exist_ok=True)
        return base

    def test_discover_includes_new_sidecars(self) -> None:
        base = self._make_base()
        targets = cli._discover_validation_targets(base)
        schemas = {schema for schema, _ in targets}
        self.assertIn("cs-augmentation", schemas)
        self.assertIn("drill-pending", schemas)
        # drill-history-entry is validated via _append_drill_history_validation,
        # not via _discover_validation_targets (it is jsonl, not a single dict).
        paths_by_schema = {schema: path for schema, path in targets}
        self.assertEqual(paths_by_schema["cs-augmentation"], base / "contexts" / "cs-augmentation.json")
        self.assertEqual(paths_by_schema["drill-pending"], base / "memory" / "drill-pending.json")

    def test_missing_optional_sidecars_are_not_applicable(self) -> None:
        base = self._make_base()
        validations: list[dict] = []
        for schema, path in cli._discover_validation_targets(base):
            if schema in {"cs-augmentation", "drill-pending"}:
                cli._append_validation(validations, schema, path)
        self.assertEqual(len(validations), 2)
        for entry in validations:
            self.assertFalse(entry["exists"])
            self.assertIsNone(entry["valid"])
            self.assertEqual(entry.get("status"), "not_applicable")

    def test_drill_history_missing_is_not_applicable(self) -> None:
        base = self._make_base()
        validations: list[dict] = []
        cli._append_drill_history_validation(validations, base / "memory" / "drill-history.jsonl")
        self.assertEqual(len(validations), 1)
        entry = validations[0]
        self.assertFalse(entry["exists"])
        self.assertEqual(entry.get("status"), "not_applicable")

    def test_drill_history_existing_lines_are_validated(self) -> None:
        base = self._make_base()
        path = base / "memory" / "drill-history.jsonl"
        entry = {
            "drill_session_id": "drill-1",
            "linked_learning_point": "repository_boundary",
            "question": "?",
            "answer": "because repository is a persistence abstraction and the layer above owns transactions",
            "total_score": 7,
            "level": "L3",
            "dimensions": {"accuracy": 3, "depth": 2, "practicality": 1, "completeness": 1},
            "scored_at": "2026-04-13T00:00:00+00:00",
        }
        path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        validations: list[dict] = []
        cli._append_drill_history_validation(validations, path)
        self.assertTrue(validations[0]["valid"])
        self.assertTrue(validations[0]["exists"])


if __name__ == "__main__":
    unittest.main()
