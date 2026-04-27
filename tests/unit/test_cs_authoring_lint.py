import tempfile
import unittest
from pathlib import Path

from scripts.lint_cs_authoring import lint_file


class CsAuthoringLintTest(unittest.TestCase):
    def test_advanced_docs_are_not_forced_into_beginner_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep-dive.md"
            path.write_text(
                "\n".join(
                    [
                        "# Deep Dive",
                        "",
                        "**난이도: 🔴 Advanced**",
                        "",
                        "## 긴 분석",
                        "",
                        "legacy deep-dive body",
                    ]
                ),
                encoding="utf-8",
            )

            errors, warnings = lint_file(path)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_beginner_docs_still_require_authoring_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "beginner.md"
            path.write_text(
                "\n".join(
                    [
                        "# Beginner Note",
                        "",
                        "**난이도: 🟢 Beginner**",
                        "",
                        "## 내용",
                        "",
                        "missing required beginner structure",
                    ]
                ),
                encoding="utf-8",
            )

            errors, warnings = lint_file(path)

        self.assertTrue(errors)
        self.assertTrue(any("한 줄 요약" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
