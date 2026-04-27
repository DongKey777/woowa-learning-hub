#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path.cwd().resolve()
CANONICAL_LABEL = "[canonical beginner entry route: login-loop]"


@dataclass(frozen=True)
class LabelContract:
    label: str
    snippets: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    path: Path
    label: str
    missing_snippets: tuple[str, ...]


DEFAULT_CONTRACTS = (
    LabelContract(
        label="root ladder",
        snippets=(
            CANONICAL_LABEL,
            "[Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md)",
            "[Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md)",
            "cookie-missing",
            "server-anonymous",
        ),
    ),
    LabelContract(
        label="security ladder",
        snippets=(
            "[Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)",
            "[Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)",
            "cookie-missing",
            "server-anonymous",
        ),
    ),
    LabelContract(
        label="rag routing readme",
        snippets=(
            CANONICAL_LABEL,
            "Login Redirect / SavedRequest",
            "Browser 401 vs 302",
            "cookie-missing",
            "server-anonymous",
            "Security README: Browser / Session Troubleshooting Path",
        ),
    ),
    LabelContract(
        label="cross-domain bridge map",
        snippets=(
            CANONICAL_LABEL,
            "login-redirect-hidden-jsessionid-savedrequest-primer.md",
            "browser-401-vs-302-login-redirect-guide.md",
            "cookie-missing",
            "server-anonymous",
        ),
    ),
)


DEFAULT_TARGETS = (
    ("knowledge/cs/README.md", DEFAULT_CONTRACTS[0]),
    ("knowledge/cs/contents/security/README.md", DEFAULT_CONTRACTS[1]),
    ("knowledge/cs/rag/README.md", DEFAULT_CONTRACTS[2]),
    ("knowledge/cs/rag/cross-domain-bridge-map.md", DEFAULT_CONTRACTS[3]),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flag login-loop beginner route label drift between the CS root README, "
            "security README ladder, and RAG routing docs."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repository root to scan. Defaults to the current working directory.",
    )
    return parser.parse_args()


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_targets(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []

    for relative_path, contract in DEFAULT_TARGETS:
        path = repo_root / relative_path
        if not path.exists():
            findings.append(
                Finding(
                    path=path,
                    label=contract.label,
                    missing_snippets=("file missing",),
                )
            )
            continue

        text = path.read_text(encoding="utf-8")
        missing = tuple(snippet for snippet in contract.snippets if snippet not in text)
        if missing:
            findings.append(
                Finding(
                    path=path,
                    label=contract.label,
                    missing_snippets=missing,
                )
            )

    return findings


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    findings = scan_targets(repo_root)

    if findings:
        print(
            "login-loop beginner route label drift detected between root/security/RAG docs.",
            file=sys.stderr,
        )
        for finding in findings:
            print(
                f"{display_path(finding.path, repo_root)} [{finding.label}]",
                file=sys.stderr,
            )
            for snippet in finding.missing_snippets:
                print(f"  missing: {snippet}", file=sys.stderr)
        print(
            "Keep the canonical label in root/RAG docs, preserve the same primer -> "
            "primer bridge order in the security ladder, and align the normalized child "
            "labels plus security README return-path wording.",
            file=sys.stderr,
        )
        return 1

    print("Auth ladder label parity looks aligned across root/security/RAG docs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
