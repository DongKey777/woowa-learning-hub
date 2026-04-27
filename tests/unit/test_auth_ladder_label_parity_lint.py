from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

WORKBENCH = Path(__file__).resolve().parents[2]
DOCS = WORKBENCH / "docs"

if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import auth_ladder_label_parity_lint


class AuthLadderLabelParityLintTest(unittest.TestCase):
    def write_fixture(self, root: Path, relative_path: str, content: str) -> None:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_missing_canonical_label_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.write_fixture(
                root,
                "knowledge/cs/README.md",
                "\n".join(
                    [
                        "# Root",
                        "cookie-missing",
                        "server-anonymous",
                        "[Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md)",
                        "[Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md)",
                    ]
                ),
            )
            self.write_fixture(
                root,
                "knowledge/cs/contents/security/README.md",
                "\n".join(
                    [
                        "cookie-missing",
                        "server-anonymous",
                        "[Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)",
                        "[Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)",
                    ]
                ),
            )
            self.write_fixture(
                root,
                "knowledge/cs/rag/README.md",
                "\n".join(
                    [
                        auth_ladder_label_parity_lint.CANONICAL_LABEL,
                        "Login Redirect / SavedRequest",
                        "Browser 401 vs 302",
                        "cookie-missing",
                        "server-anonymous",
                        "Security README: Browser / Session Troubleshooting Path",
                    ]
                ),
            )
            self.write_fixture(
                root,
                "knowledge/cs/rag/cross-domain-bridge-map.md",
                "\n".join(
                    [
                        auth_ladder_label_parity_lint.CANONICAL_LABEL,
                        "login-redirect-hidden-jsessionid-savedrequest-primer.md",
                        "browser-401-vs-302-login-redirect-guide.md",
                        "cookie-missing",
                        "server-anonymous",
                    ]
                ),
            )

            findings = auth_ladder_label_parity_lint.scan_targets(root)

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].label, "root ladder")
            self.assertIn(
                auth_ladder_label_parity_lint.CANONICAL_LABEL,
                findings[0].missing_snippets,
            )

    def test_repo_contract_passes_with_current_docs(self) -> None:
        findings = auth_ladder_label_parity_lint.scan_targets(WORKBENCH)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
