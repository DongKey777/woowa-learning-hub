"""runpod_direct_build must pass --no-release-fetch to cli_cs_index_build.

Without this flag the build short-circuits into downloading the
*previously published* GitHub release tar.zst, skipping the actual
fresh build that the RunPod cycle paid for.

Real silent failure observed 2026-05-06 r3-direct-9a7c218 build —
the manifest came back with corpus_hash=34b9577 (the OLD release
shipped 2026-05-04) instead of the new commit's corpus, making
cohort_eval against it identical to baseline.

Equivalent fix already pinned for runpod_rag_full_build by
``test_pilot_paths_in_v3_prompt.py`` companion regressions; this
test pins the same contract for direct_build.
"""

from __future__ import annotations

import unittest

from scripts.remote.runpod_direct_build import build_remote_commands


class DirectBuildNoReleaseFetchTest(unittest.TestCase):
    def _build_cmd(self) -> str:
        commands = build_remote_commands(
            commit_sha="abc1234",
            modalities=("fts", "dense", "sparse", "colbert"),
            run_id="r3-direct-test",
            lance_max_length=512,
            lance_batch_size=256,
        )
        for label, cmd in commands:
            if "scripts.learning.cli_cs_index_build" in cmd:
                return cmd
        self.fail(
            "no cli_cs_index_build command emitted by build_remote_commands; "
            "step layout changed?"
        )

    def test_build_command_includes_no_release_fetch(self) -> None:
        cmd = self._build_cmd()
        self.assertIn(
            "--no-release-fetch", cmd,
            f"build_command missing --no-release-fetch flag — release-fetch "
            f"short-circuit will skip fresh build:\n  {cmd}",
        )

    def test_build_command_passes_modalities_through(self) -> None:
        cmd = self._build_cmd()
        self.assertIn("--modalities fts,dense,sparse,colbert", cmd)

    def test_build_command_targets_workspace_cs_rag(self) -> None:
        cmd = self._build_cmd()
        self.assertIn("--out /workspace/cs_rag/", cmd)


if __name__ == "__main__":
    unittest.main()
