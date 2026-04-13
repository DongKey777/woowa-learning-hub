#!/usr/bin/env python3
"""GitHub CLI wrapper for PR archive collection."""

from __future__ import annotations

import json
import subprocess
from typing import Any


class GitHubCLIError(RuntimeError):
    """Raised when a gh command fails."""


class GitHubCLIClient:
    def __init__(self, owner: str, repo: str) -> None:
        self.owner = owner
        self.repo = repo

    def fetch_authenticated_user(self) -> dict[str, Any]:
        return self._run_api("user")

    def fetch_pull_requests(self, state: str = "all") -> list[dict[str, Any]]:
        endpoint = f"repos/{self.owner}/{self.repo}/pulls?state={state}&per_page=100"
        return self._run_api(endpoint, paginate=True)

    def fetch_pull_request_detail(self, number: int) -> dict[str, Any]:
        endpoint = f"repos/{self.owner}/{self.repo}/pulls/{number}"
        return self._run_api(endpoint)

    def fetch_pull_request_files(self, number: int) -> list[dict[str, Any]]:
        endpoint = f"repos/{self.owner}/{self.repo}/pulls/{number}/files?per_page=100"
        return self._run_api(endpoint, paginate=True)

    def fetch_pull_request_reviews(self, number: int) -> list[dict[str, Any]]:
        endpoint = f"repos/{self.owner}/{self.repo}/pulls/{number}/reviews?per_page=100"
        return self._run_api(endpoint, paginate=True)

    def fetch_pull_request_review_comments(self, number: int) -> list[dict[str, Any]]:
        endpoint = f"repos/{self.owner}/{self.repo}/pulls/{number}/comments?per_page=100"
        return self._run_api(endpoint, paginate=True)

    def fetch_pull_request_issue_comments(self, number: int) -> list[dict[str, Any]]:
        endpoint = f"repos/{self.owner}/{self.repo}/issues/{number}/comments?per_page=100"
        return self._run_api(endpoint, paginate=True)

    def _run_api(self, endpoint: str, paginate: bool = False) -> Any:
        command = ["gh", "api", endpoint]
        if paginate:
            command.extend(["--paginate", "--slurp"])

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise GitHubCLIError(result.stderr.strip() or f"gh api failed: {endpoint}")

        output = result.stdout.strip()
        if not output:
            return [] if paginate else {}

        payload = json.loads(output)
        if not paginate:
            return payload
        return self._flatten_pages(payload)

    def _flatten_pages(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            return [payload]

        flattened: list[dict[str, Any]] = []
        for page in payload:
            if isinstance(page, list):
                flattened.extend(page)
                continue
            flattened.append(page)
        return flattened
