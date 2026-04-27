from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[2]
DOCS = WORKBENCH / "docs"

if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import local_doc_target_lint


class LocalDocTargetLintTest(unittest.TestCase):
    def test_missing_local_markdown_target_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        "[missing guide](./guides/release-guide.md)",
                    ]
                ),
                encoding="utf-8",
            )

            findings = local_doc_target_lint.scan_file(fixture)

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].issue, "missing-doc")
            self.assertEqual(findings[0].target, "./guides/release-guide.md")

    def test_stale_anchor_on_existing_markdown_target_gets_suggestion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            target = Path(tmpdir) / "guide.md"
            target.write_text(
                "\n".join(
                    [
                        "# Guide",
                        "",
                        "## Release Gate",
                        "",
                        "ok",
                    ]
                ),
                encoding="utf-8",
            )
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        "[stale anchor](./guide.md#release-gates)",
                    ]
                ),
                encoding="utf-8",
            )

            findings = local_doc_target_lint.scan_file(fixture)

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].issue, "stale-anchor")
            self.assertEqual(findings[0].anchor, "release-gates")
            self.assertIsNotNone(findings[0].suggestion)
            self.assertEqual(findings[0].suggestion.anchor, "release-gate")

    def test_same_file_anchor_and_html_doc_href_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            guide = Path(tmpdir) / "guide.md"
            guide.write_text(
                "\n".join(
                    [
                        "# Guide",
                        "",
                        "## Return Path",
                        "",
                        "ok",
                    ]
                ),
                encoding="utf-8",
            )
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        "## Overview",
                        "",
                        '[same file ok](#overview) and <a href="./guide.md#return-path">guide</a>',
                        '<a href="./guide.md#missing-path">broken</a>',
                    ]
                ),
                encoding="utf-8",
            )

            findings = local_doc_target_lint.scan_file(fixture)

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].kind, "html-doc-link")
            self.assertEqual(findings[0].issue, "stale-anchor")
            self.assertEqual(findings[0].anchor, "missing-path")


if __name__ == "__main__":
    unittest.main()
