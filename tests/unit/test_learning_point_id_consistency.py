"""Regression guard — category_mapping keys must match
candidate_interpretation.LEARNING_POINT_RULES ids.

If anyone renames or adds a learning-point rule without updating the
CS category mapping, this test fails loudly before the drift can hide
inside runtime fallbacks.
"""

import unittest

from scripts.learning.rag import category_mapping
from scripts.workbench.core.candidate_interpretation import LEARNING_POINT_RULES


class LearningPointIdConsistencyTest(unittest.TestCase):
    def test_every_rule_id_has_a_category_mapping(self) -> None:
        rule_ids = {rule["id"] for rule in LEARNING_POINT_RULES}
        mapping_ids = set(category_mapping.LEARNING_POINT_TO_CS_CATEGORY.keys())

        missing_in_mapping = rule_ids - mapping_ids
        stray_in_mapping = mapping_ids - rule_ids

        self.assertFalse(
            missing_in_mapping,
            f"learning-point ids without CS category mapping: {sorted(missing_in_mapping)}",
        )
        self.assertFalse(
            stray_in_mapping,
            f"category_mapping keys without a learning-point rule: {sorted(stray_in_mapping)}",
        )

    def test_rule_ids_are_underscore_lowercase(self) -> None:
        for rule in LEARNING_POINT_RULES:
            rule_id = rule["id"]
            self.assertEqual(
                rule_id,
                rule_id.lower(),
                f"learning-point id must be lowercase: {rule_id}",
            )
            self.assertNotIn(
                "-", rule_id, f"use underscore, not hyphen: {rule_id}"
            )

    def test_categories_are_non_empty_lists(self) -> None:
        for lp_id, cats in category_mapping.LEARNING_POINT_TO_CS_CATEGORY.items():
            self.assertIsInstance(cats, list, f"{lp_id} categories must be a list")
            self.assertTrue(cats, f"{lp_id} has an empty category list")
            for cat in cats:
                self.assertIsInstance(cat, str)
                self.assertTrue(cat, f"{lp_id} has an empty category name")


if __name__ == "__main__":
    unittest.main()
