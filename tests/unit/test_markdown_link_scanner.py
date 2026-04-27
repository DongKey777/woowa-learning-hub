"""Regression tests for markdown link scanner false-positive guards."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[2]
DOCS = WORKBENCH / "docs"

if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import asset_filename_lint
import markdown_link_scanner
import stale_asset_reverse_link_check


class MarkdownLinkScannerRegressionTest(unittest.TestCase):
    def test_html_srcset_candidates_are_scanned_as_distinct_local_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            img_dir = Path(tmpdir) / "img"
            img_dir.mkdir()
            (img_dir / "release-safe.png").write_text("ok", encoding="utf-8")
            (img_dir / "release(qa).PNG").write_text("ok", encoding="utf-8")
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        '<source srcset="./img/release-safe.png 1x, ./img/release(qa).PNG 2x">',
                    ]
                ),
                encoding="utf-8",
            )

            findings = asset_filename_lint.scan_file(fixture)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].kind, "html-srcset")
            self.assertEqual(findings[0].target, "./img/release(qa).PNG")

            self.assertEqual(
                stale_asset_reverse_link_check.collect_file_references(fixture),
                {},
            )

    def test_local_html_anchor_href_is_treated_as_repo_local_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            html_dir = Path(tmpdir) / "fixtures"
            html_dir.mkdir()
            (html_dir / "release-guide.html").write_text("<h1>ok</h1>", encoding="utf-8")
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        '<a href="./fixtures/release-guide.html">safe local html</a>',
                        '<a href="./fixtures/release-guide(v2).html">missing local html</a>',
                    ]
                ),
                encoding="utf-8",
            )

            findings = asset_filename_lint.scan_file(fixture)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].kind, "html-asset")
            self.assertEqual(findings[0].target, "./fixtures/release-guide(v2).html")

            references = stale_asset_reverse_link_check.collect_file_references(fixture)
            self.assertEqual(len(references), 1)
            missing_target = next(iter(references))
            self.assertTrue(missing_target.endswith("/fixtures/release-guide(v2).html"))
            self.assertEqual(len(references[missing_target]), 1)
            self.assertEqual(references[missing_target][0].kind, "html-asset")

    def test_video_poster_attr_is_treated_as_local_asset_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "teaser.mp4").write_text("ok", encoding="utf-8")
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        '<video controls poster="./media/preview(qa).PNG" src="./media/teaser.mp4"></video>',
                    ]
                ),
                encoding="utf-8",
            )

            findings = asset_filename_lint.scan_file(fixture)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].kind, "html-asset")
            self.assertEqual(findings[0].target, "./media/preview(qa).PNG")

            references = stale_asset_reverse_link_check.collect_file_references(fixture)
            self.assertEqual(len(references), 1)
            missing_target = next(iter(references))
            self.assertTrue(missing_target.endswith("/media/preview(qa).PNG"))
            self.assertEqual(len(references[missing_target]), 1)
            self.assertEqual(references[missing_target][0].kind, "html-asset")

    def test_video_and_audio_src_tags_join_local_asset_reverse_link_sweep(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "voice-track.mp3").write_text("ok", encoding="utf-8")
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        '<video src="./media/release-teaser(v2).mp4"></video>',
                        '<audio src="./media/voice-track.mp3"></audio>',
                    ]
                ),
                encoding="utf-8",
            )

            references = stale_asset_reverse_link_check.collect_file_references(fixture)
            self.assertEqual(len(references), 1)
            missing_target = next(iter(references))
            self.assertTrue(missing_target.endswith("/media/release-teaser(v2).mp4"))
            self.assertEqual(len(references[missing_target]), 1)
            self.assertEqual(references[missing_target][0].kind, "html-asset")

    def test_source_src_and_track_src_tags_join_local_asset_lint_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            media_dir = Path(tmpdir) / "media"
            captions_dir = Path(tmpdir) / "captions"
            media_dir.mkdir()
            captions_dir.mkdir()
            (media_dir / "release-safe.webm").write_text("ok", encoding="utf-8")
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        '<source src="./media/release-safe.webm" type="video/webm">',
                        '<track src="./captions/release(ko).VTT" kind="captions">',
                    ]
                ),
                encoding="utf-8",
            )

            findings = asset_filename_lint.scan_file(fixture)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].kind, "html-asset")
            self.assertEqual(findings[0].target, "./captions/release(ko).VTT")

            references = stale_asset_reverse_link_check.collect_file_references(fixture)
            self.assertEqual(len(references), 1)
            missing_target = next(iter(references))
            self.assertTrue(missing_target.endswith("/captions/release(ko).VTT"))
            self.assertEqual(len(references[missing_target]), 1)
            self.assertEqual(references[missing_target][0].kind, "html-asset")

    def test_inline_code_punctuation_heavy_asset_examples_do_not_trigger_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        "Literal markdown stays inline-coded:",
                        "`![diagram](./img/release(qa)-v1.2.png)`",
                        "`[download](./code/retry&rollback.v2.pdf)`",
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(asset_filename_lint.scan_file(fixture), [])
            self.assertEqual(
                stale_asset_reverse_link_check.collect_file_references(fixture),
                {},
            )

    def test_inline_code_html_asset_examples_do_not_trigger_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "fixture.md"
            fixture.write_text(
                "\n".join(
                    [
                        "# Fixture",
                        "",
                        "Literal HTML stays inline-coded:",
                        '`<img src="./img/release(qa)-v1.2.png" alt="qa">`',
                        '`<source srcset="./img/release(qa)-v1.2.png 1x, ./img/release(qa)-v2.0.png 2x">`',
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(asset_filename_lint.scan_file(fixture), [])
            self.assertEqual(
                stale_asset_reverse_link_check.collect_file_references(fixture),
                {},
            )

    def test_balanced_paren_markdown_links_keep_full_target(self) -> None:
        line = (
            '[scanner note](./guides/link-fixture(v2).md#balanced-(paren)-target "Fixture Title")'
        )

        targets = markdown_link_scanner.iter_markdown_targets(line)

        self.assertEqual(len(targets), 1)
        self.assertEqual(
            markdown_link_scanner.normalize_target(targets[0].raw_target),
            "./guides/link-fixture(v2).md#balanced-(paren)-target",
        )


if __name__ == "__main__":
    unittest.main()
