from __future__ import annotations

import unittest

from scripts.learning.rag.index_smoke import _synced_rebuild_trigger_payload


class SyncedRebuildTriggerPayloadTest(unittest.TestCase):
    def test_updates_live_corpus_snapshot_and_diff_from_report(self):
        report = {
            "generated_at": "2026-05-05T14:20:00Z",
            "indexed_corpus_diff": {
                "available": True,
                "changed_path_count": 579,
            },
            "rebuild_trigger": {
                "generated_at": "2026-05-05T14:00:00Z",
                "live_corpus": {
                    "indexed_corpus_hash": "old-indexed",
                    "full_corpus_hash": "old-full",
                    "non_indexed_markdown_count": 90,
                },
                "verification": {
                    "indexed_corpus_diff": {
                        "available": True,
                        "changed_path_count": 567,
                    }
                },
            },
            "rebuild_trigger_consistency": {
                "current_live_corpus_snapshot": {
                    "indexed_corpus_hash": "new-indexed",
                    "full_corpus_hash": "new-full",
                    "non_indexed_markdown_count": 89,
                }
            },
        }

        synced = _synced_rebuild_trigger_payload(report)

        assert synced is not None
        self.assertEqual(synced["generated_at"], "2026-05-05T14:20:00Z")
        self.assertEqual(
            synced["live_corpus"],
            {
                "indexed_corpus_hash": "new-indexed",
                "full_corpus_hash": "new-full",
                "non_indexed_markdown_count": 89,
            },
        )
        self.assertEqual(
            synced["verification"]["indexed_corpus_diff"],
            {
                "available": True,
                "changed_path_count": 579,
            },
        )

    def test_returns_none_without_rebuild_trigger_payload(self):
        self.assertIsNone(_synced_rebuild_trigger_payload({"generated_at": "now"}))


if __name__ == "__main__":
    unittest.main()
