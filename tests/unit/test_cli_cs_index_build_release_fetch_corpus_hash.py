"""Pin: bin/cs-index-build cross-checks release corpus_hash against the
working tree's config lock.

Background — cycle 2 baseline incident (2026-05-06).
A fresh worktree ran ``bin/cs-index-build`` without ``--no-release-fetch``.
``release_fetch`` returned ``fetched`` and dropped a 2026-05-04 release
into ``state/cs_rag`` with ``corpus_hash 34b9577…`` (27,238 docs).
However the working tree's ``config/rag_models.json`` declared a
*different* expected lock — ``corpus_hash d5d8991…`` (28,108 docs) from
the 2026-05-06 build that was never re-published. The fleet measured a
baseline against an obsolete corpus and stopped.

The CLI had no verification of downloaded vs expected corpus_hash, so
the divergence was silent.

This module pins the post-fix contract:

  · ``_verify_release_corpus_hash`` returns ``"ok"`` when manifest +
    config corpus_hash agree, when either side is missing, or when the
    ``corpus_hash`` field is absent.
  · It returns ``"mismatch_warned"`` and prints to stderr when they
    differ and strict mode is off (default).
  · It returns ``"mismatch_strict"`` and prints to stderr when they
    differ and strict mode is on; the caller is expected to ``return 1``.
  · ``main`` exits 1 when ``--strict-release-fetch`` is set and the
    downloaded corpus_hash does not match.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.learning.cli_cs_index_build import (
    _verify_release_corpus_hash,
    main,
)


def _write_manifest(out_dir: Path, corpus_hash: str | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"row_count": 27238}
    if corpus_hash is not None:
        payload["corpus_hash"] = corpus_hash
    (out_dir / "manifest.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )


def _write_config(repo_root: Path, corpus_hash: str | None) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    payload: dict = {"schema_version": 1, "index": {"backend": "r3"}}
    if corpus_hash is not None:
        payload["index"]["corpus_hash"] = corpus_hash
    (config_dir / "rag_models.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )


class VerifyReleaseCorpusHashTest(unittest.TestCase):
    def test_match_returns_ok_no_stderr(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            _write_manifest(out_dir, "deadbeef" * 8)
            _write_config(root, "deadbeef" * 8)
            buf = io.StringIO()
            with redirect_stderr(buf):
                outcome = _verify_release_corpus_hash(
                    out_dir, root, strict=False,
                )
            self.assertEqual(outcome, "ok")
            self.assertEqual(buf.getvalue(), "")

    def test_mismatch_default_warns_and_continues(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            _write_manifest(out_dir, "34b95775" + "0" * 56)
            _write_config(root, "d5d8991b" + "0" * 56)
            buf = io.StringIO()
            with redirect_stderr(buf):
                outcome = _verify_release_corpus_hash(
                    out_dir, root, strict=False,
                )
            self.assertEqual(outcome, "mismatch_warned")
            err = buf.getvalue()
            self.assertIn("34b95775", err)
            self.assertIn("d5d8991b", err)
            self.assertIn("--strict-release-fetch", err)

    def test_mismatch_strict_returns_strict_signal(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            _write_manifest(out_dir, "34b95775" + "0" * 56)
            _write_config(root, "d5d8991b" + "0" * 56)
            buf = io.StringIO()
            with redirect_stderr(buf):
                outcome = _verify_release_corpus_hash(
                    out_dir, root, strict=True,
                )
            self.assertEqual(outcome, "mismatch_strict")
            err = buf.getvalue()
            self.assertIn("Aborting", err)
            self.assertIn("--no-release-fetch", err)

    def test_missing_manifest_returns_ok(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            out_dir.mkdir(parents=True)
            _write_config(root, "deadbeef" * 8)
            outcome = _verify_release_corpus_hash(
                out_dir, root, strict=False,
            )
            self.assertEqual(outcome, "ok")

    def test_missing_config_returns_ok(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            _write_manifest(out_dir, "deadbeef" * 8)
            outcome = _verify_release_corpus_hash(
                out_dir, root, strict=False,
            )
            self.assertEqual(outcome, "ok")

    def test_manifest_missing_corpus_hash_returns_ok(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            _write_manifest(out_dir, None)
            _write_config(root, "deadbeef" * 8)
            outcome = _verify_release_corpus_hash(
                out_dir, root, strict=False,
            )
            self.assertEqual(outcome, "ok")

    def test_config_missing_corpus_hash_returns_ok(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            _write_manifest(out_dir, "deadbeef" * 8)
            _write_config(root, None)
            outcome = _verify_release_corpus_hash(
                out_dir, root, strict=False,
            )
            self.assertEqual(outcome, "ok")

    def test_corrupt_json_returns_ok(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            out_dir.mkdir(parents=True)
            (out_dir / "manifest.json").write_text("{not valid", encoding="utf-8")
            _write_config(root, "deadbeef" * 8)
            outcome = _verify_release_corpus_hash(
                out_dir, root, strict=False,
            )
            self.assertEqual(outcome, "ok")


class MainStrictReleaseFetchExitCodeTest(unittest.TestCase):
    """End-to-end: --strict-release-fetch should make main() return 1
    when release_fetch claims fetched but the corpus_hash mismatches."""

    def _run_with_mismatch(self, *, strict_flag: bool) -> int:
        with TemporaryDirectory() as td:
            root = Path(td)
            out_dir = root / "state" / "cs_rag"
            _write_manifest(out_dir, "34b95775" + "0" * 56)
            _write_config(root, "d5d8991b" + "0" * 56)

            with mock.patch(
                "scripts.learning.cli_cs_index_build._find_repo_root",
                return_value=root,
            ), mock.patch(
                "scripts.learning.rag.release_fetch.fetch_index_release",
                return_value="fetched",
            ):
                argv = ["--out", str(out_dir), "--corpus", str(root / "knowledge")]
                if strict_flag:
                    argv.append("--strict-release-fetch")
                buf = io.StringIO()
                with redirect_stderr(buf):
                    return main(argv)

    def test_strict_flag_exits_1_on_mismatch(self) -> None:
        self.assertEqual(self._run_with_mismatch(strict_flag=True), 1)

    def test_default_proceeds_to_zero_on_mismatch(self) -> None:
        # Without strict, main returns 0 (warn-and-continue path).
        self.assertEqual(self._run_with_mismatch(strict_flag=False), 0)


if __name__ == "__main__":
    unittest.main()
