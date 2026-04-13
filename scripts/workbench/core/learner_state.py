"""Direct-observation snapshot of a learner's mission repository.

Produces `state/repos/<repo>/contexts/learner-state.json`, the artifact the
mission coach reads before calling `coach-run`. See:

- `docs/agent-operating-contract.md` First-Run Protocol step 6
- `schemas/learner-state.schema.json`
- `docs/token-budget.md` Pre-coach-run Direct Read Budget

Budget caps (hard limits, enforced here — not by callers):

- 1 target PR deep-dived; others listed only
- <= 20 most recent unresolved threads read on the target PR
- <= 10 file regions read (±20 lines each)
- <= 8 gh/GraphQL calls total
- ~60s wall-clock soft limit
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import repo_context_dir
from .registry import find_repo
from .shell import run_capture


MAX_THREADS = 20
MAX_FILE_READS = 10
MAX_GH_CALLS = 8
WALLCLOCK_SOFT_LIMIT_S = 60
FILE_REGION_HALF_LINES = 20
BOT_LOGINS = {"coderabbitai", "coderabbitai[bot]", "github-actions[bot]", "dependabot[bot]"}
CYCLE_HINT_RE = re.compile(r"(step[-_]?(\d+)|cycle[-_]?(\d+)|main[-_]?(\d+))", re.IGNORECASE)
# GitHub reaction content values treated as "learner acknowledged" signals.
# All 8 GitHub reaction types count — 👎/😕 also mean "saw it with an objection",
# which is still an acknowledgment. Downstream narrative can split positive vs.
# dissenting using the raw content values kept in `learner_reactions`.
ACKNOWLEDGMENT_REACTIONS = {
    "THUMBS_UP", "THUMBS_DOWN", "LAUGH", "HOORAY",
    "CONFUSED", "HEART", "ROCKET", "EYES",
}


class _BudgetExceeded(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class _Budget:
    started_at: float = field(default_factory=time.monotonic)
    gh_calls: int = 0
    file_reads: int = 0
    threads_read: int = 0
    skipped: list[dict[str, str]] = field(default_factory=list)

    def record_gh_call(self) -> None:
        self.gh_calls += 1

    def check_wallclock(self) -> None:
        if time.monotonic() - self.started_at > WALLCLOCK_SOFT_LIMIT_S:
            raise _BudgetExceeded("wallclock_cap")

    def can_gh(self) -> bool:
        return self.gh_calls < MAX_GH_CALLS

    def note_skipped(self, what: str, reason: str) -> None:
        self.skipped.append({"what": what, "reason": reason})


def _run_git(repo_path: Path, args: list[str]) -> tuple[int, str, str]:
    result = run_capture(["git", "-C", str(repo_path), *args])
    return result.returncode, result.stdout, result.stderr


def _run_gh(budget: _Budget, args: list[str]) -> tuple[int, str, str]:
    # Wall-clock is a hard cap documented in agent-operating-contract.md. Check
    # it here so a slow gh/graphql call cannot silently push the assessment
    # past the 60s budget. The caller's try/except around _BudgetExceeded
    # degrades the snapshot to `coverage=partial` cleanly.
    budget.check_wallclock()
    if not budget.can_gh():
        raise _BudgetExceeded("gh_call_cap")
    budget.record_gh_call()
    result = run_capture(["gh", *args])
    return result.returncode, result.stdout, result.stderr


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_owner_from_origin(url: str) -> str | None:
    url = url.strip()
    if url.startswith("git@"):
        # git@github.com:owner/repo.git
        _, _, tail = url.partition(":")
        if "/" in tail:
            return tail.split("/", 1)[0]
        return None
    if url.startswith(("https://", "http://", "ssh://")):
        # strip protocol
        after = url.split("//", 1)[1]
        parts = after.split("/")
        if len(parts) >= 3:
            # host/owner/repo
            return parts[1]
    return None


def _derive_cycle_hint(head_ref: str | None) -> str | None:
    if not head_ref:
        return None
    match = CYCLE_HINT_RE.search(head_ref)
    if not match:
        return None
    for group in match.groups()[1:]:
        if group:
            return f"cycle-{int(group)}"
    return match.group(0).lower()


def _parse_porcelain_branch(porcelain: str) -> tuple[int, int, list[str], list[str]]:
    ahead = 0
    behind = 0
    uncommitted: list[str] = []
    untracked: list[str] = []
    for line in porcelain.splitlines():
        if line.startswith("## "):
            match = re.search(r"\[ahead (\d+)(?:, behind (\d+))?\]", line)
            if match:
                ahead = int(match.group(1))
                behind = int(match.group(2) or 0)
            else:
                match = re.search(r"\[behind (\d+)\]", line)
                if match:
                    behind = int(match.group(1))
            continue
        if not line.strip():
            continue
        code = line[:2]
        path = line[3:]
        if code == "??":
            untracked.append(path)
        else:
            uncommitted.append(path)
    return ahead, behind, uncommitted, untracked


def _section_a_topology(
    repo_path: Path,
    upstream_owner_repo: str | None,
    budget: _Budget,
) -> dict[str, Any]:
    def _list_remotes() -> dict[str, str]:
        rc, out, _ = _run_git(repo_path, ["remote", "-v"])
        found: dict[str, str] = {}
        if rc == 0:
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0] not in found:
                    found[parts[0]] = parts[1]
        return found

    remotes = _list_remotes()

    # If we know the upstream owner/repo and there's no remote pointing at it,
    # add one. The contract's First-Run Protocol step A.1 explicitly allows
    # this; it's idempotent.
    if upstream_owner_repo and _resolve_upstream_remote(remotes, upstream_owner_repo) not in _matching_remotes(remotes, upstream_owner_repo):
        # No remote URL matches the upstream slug. Add one.
        upstream_url = f"https://github.com/{upstream_owner_repo}.git"
        _run_git(repo_path, ["remote", "add", "upstream", upstream_url])
        remotes = _list_remotes()

    upstream_remote = _resolve_upstream_remote(remotes, upstream_owner_repo)

    rc, _, _ = _run_git(repo_path, ["fetch", "--all", "--prune"])
    fetch_state = "fresh" if rc == 0 else "stale"
    if rc != 0:
        budget.note_skipped("git fetch --all", "network_or_auth_failure")

    return {
        "remotes": remotes,
        "upstream_remote": upstream_remote,
        "fetch_state": fetch_state,
    }


def _matching_remotes(remotes: dict[str, str], upstream_owner_repo: str | None) -> list[str]:
    if not upstream_owner_repo:
        return []
    slug = upstream_owner_repo.lower()
    return [
        name for name, url in remotes.items()
        if slug in url.lower() or slug.replace("/", ":") in url.lower()
    ]


def _section_b_working_copy(repo_path: Path) -> tuple[dict[str, Any], str, str]:
    rc, porcelain, _ = _run_git(repo_path, ["status", "--porcelain=v1", "-b"])
    porcelain = porcelain if rc == 0 else ""
    ahead, behind, uncommitted, untracked = _parse_porcelain_branch(porcelain)
    rc, head_branch_out, _ = _run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
    head_branch = head_branch_out.strip() if rc == 0 else "HEAD"
    rc, head_sha_out, _ = _run_git(repo_path, ["rev-parse", "HEAD"])
    head_sha = head_sha_out.strip() if rc == 0 else ""

    working_copy = {
        "clean": not (uncommitted or untracked),
        "ahead": ahead,
        "behind": behind,
        "uncommitted_files": uncommitted,
        "untracked_files": untracked,
        "fingerprint": _sha256(porcelain),
    }
    return working_copy, head_branch, head_sha


def _section_c_identity(repo_path: Path) -> str | None:
    rc, url, _ = _run_git(repo_path, ["remote", "get-url", "origin"])
    if rc != 0:
        return None
    return _parse_owner_from_origin(url)


def _section_d_prs(
    upstream_owner_repo: str,
    learner_login: str,
    budget: _Budget,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    open_prs: list[dict[str, Any]] = []
    closed_prs: list[dict[str, Any]] = []

    try:
        rc, out, _ = _run_gh(
            budget,
            [
                "pr", "list",
                "--repo", upstream_owner_repo,
                "--author", learner_login,
                "--state", "open",
                "--json", "number,title,headRefName,baseRefName,url,reviewDecision,isDraft,headRefOid,createdAt,updatedAt",
            ],
        )
        if rc == 0:
            open_prs = json.loads(out or "[]")
    except _BudgetExceeded:
        budget.note_skipped("gh pr list --state open", "gh_call_cap")

    try:
        rc, out, _ = _run_gh(
            budget,
            [
                "pr", "list",
                "--repo", upstream_owner_repo,
                "--author", learner_login,
                "--state", "closed",
                "--limit", "10",
                "--json", "number,title,headRefName,baseRefName,url,mergedAt,closedAt",
            ],
        )
        if rc == 0:
            closed_prs = json.loads(out or "[]")
    except _BudgetExceeded:
        budget.note_skipped("gh pr list --state closed", "gh_call_cap")

    return open_prs, closed_prs


def _pr_row(raw: dict[str, Any], state: str) -> dict[str, Any]:
    head_ref = raw.get("headRefName")
    return {
        "number": raw.get("number"),
        "title": raw.get("title", ""),
        "head_ref": head_ref or "",
        "base_ref": raw.get("baseRefName", ""),
        "head_sha": raw.get("headRefOid"),
        "review_decision": raw.get("reviewDecision"),
        "state": state,
        "cycle_hint": _derive_cycle_hint(head_ref),
        "url": raw.get("url"),
    }


def _select_target(
    open_prs: list[dict[str, Any]],
    prompt: str | None,
    head_branch: str,
) -> tuple[int | None, str]:
    if prompt:
        for token in re.findall(r"#(\d+)", prompt):
            number = int(token)
            if any(pr.get("number") == number for pr in open_prs):
                return number, "prompt_reference"

    branch_matches = [pr for pr in open_prs if pr.get("headRefName") == head_branch]
    if len(branch_matches) == 1:
        return branch_matches[0].get("number"), "head_matches_single_open_pr"

    if open_prs:
        most_recent = max(open_prs, key=lambda pr: pr.get("updatedAt") or "")
        return most_recent.get("number"), "most_recently_updated"

    return None, "no_open_pr"


def _section_e_target_detail(
    upstream_owner_repo: str,
    target_number: int,
    learner_login: str | None,
    repo_path: Path,
    budget: _Budget,
) -> dict[str, Any] | None:
    detail: dict[str, Any] = {
        "number": target_number,
        "threads": [],
        "status_check_rollup": None,
        "head_sha": None,
        "head_ref": None,
        "base_ref": None,
    }

    try:
        rc, out, _ = _run_gh(
            budget,
            [
                "pr", "view", str(target_number),
                "--repo", upstream_owner_repo,
                "--json", "number,title,body,headRefName,baseRefName,headRefOid,reviewDecision,reviews,reviewRequests,files,commits,statusCheckRollup",
            ],
        )
        if rc == 0:
            view = json.loads(out or "{}")
            detail["status_check_rollup"] = view.get("statusCheckRollup")
            detail["head_sha"] = view.get("headRefOid")
            detail["head_ref"] = view.get("headRefName")
            detail["base_ref"] = view.get("baseRefName")
    except _BudgetExceeded:
        budget.note_skipped("gh pr view", "gh_call_cap")
        return detail

    try:
        rc, out, _ = _run_gh(
            budget,
            [
                "api",
                f"repos/{upstream_owner_repo}/pulls/{target_number}/comments",
                "--paginate",
            ],
        )
        comments = json.loads(out or "[]") if rc == 0 else []
    except _BudgetExceeded:
        budget.note_skipped("gh api comments", "gh_call_cap")
        comments = []

    # Fetch resolved status + reactions BEFORE root selection so unresolved
    # threads win the MAX_THREADS budget over resolved ones. On GraphQL failure
    # we get empty maps; in that fallback case resolved status is "unknown" for
    # all threads, reactions are absent, and the sort collapses to newest-first
    # (pre-fix behavior).
    resolved_map, reactions_map, graph_ok = _fetch_thread_graph(
        upstream_owner_repo, target_number, budget,
    )

    # --- Thread reconstruction (in_reply_to_id chains) ---
    by_id: dict[int, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []
    for raw in comments:
        comment_id = raw.get("id")
        if comment_id is None:
            continue
        node = {
            "id": comment_id,
            "in_reply_to_id": raw.get("in_reply_to_id"),
            "path": raw.get("path") or "",
            "line": raw.get("line") or raw.get("original_line"),
            "original_line": raw.get("original_line"),
            "commit_id": raw.get("commit_id"),
            "original_commit_id": raw.get("original_commit_id"),
            "author": (raw.get("user") or {}).get("login", ""),
            "body": raw.get("body") or "",
            "diff_hunk": raw.get("diff_hunk") or "",
        }
        by_id[comment_id] = node
        if not node["in_reply_to_id"]:
            roots.append(node)

    children: dict[int, list[dict[str, Any]]] = {}
    for node in by_id.values():
        parent = node.get("in_reply_to_id")
        if parent and parent in by_id:
            children.setdefault(parent, []).append(node)

    def _walk(root: dict[str, Any]) -> list[dict[str, Any]]:
        ordered: list[dict[str, Any]] = [root]
        queue = list(children.get(root["id"], []))
        queue.sort(key=lambda n: n["id"])
        while queue:
            head, *queue = queue
            ordered.append(head)
            tail = children.get(head["id"], [])
            queue = sorted(tail, key=lambda n: n["id"]) + queue
        return ordered

    def _role(author: str) -> str:
        if not author:
            return "unknown"
        lower = author.lower()
        if lower in BOT_LOGINS or author.endswith("[bot]"):
            return "bot"
        if learner_login and lower == learner_login.lower():
            return "self"
        return "mentor"

    # Unresolved-first, then most recent activity. Contract says "most recent
    # 20 unresolved threads". Recency must be measured by the latest comment
    # in the whole thread (including replies), not root creation — otherwise
    # an old root that the mentor is still actively replying on gets pushed
    # behind a brand-new root that no one has touched. Walk each thread once
    # to find its max comment id.
    def _latest_activity_id(root: dict[str, Any]) -> int:
        latest = int(root["id"])
        stack = list(children.get(root["id"], []))
        while stack:
            node = stack.pop()
            nid = int(node["id"])
            if nid > latest:
                latest = nid
            stack.extend(children.get(node["id"], []))
        return latest

    latest_by_root: dict[int, int] = {root["id"]: _latest_activity_id(root) for root in roots}

    # When resolved_map is empty (GraphQL failed) every thread is "unknown",
    # which collapses the sort to pure latest-activity-first and preserves
    # pre-fix behavior.
    def _resolution_rank(node_id: int) -> int:
        status = resolved_map.get(node_id)
        if status is False:
            return 0  # unresolved wins
        if status is None:
            return 1  # unknown (GraphQL missing/failed)
        return 2      # resolved last

    # Python's sort is stable: sort by secondary key first, then primary.
    roots.sort(key=lambda n: latest_by_root[n["id"]], reverse=True)     # latest activity first
    roots.sort(key=lambda n: _resolution_rank(n["id"]))                 # unresolved first
    selected_roots = roots[:MAX_THREADS]

    threads: list[dict[str, Any]] = []
    for root in selected_roots:
        # Check wall-clock between threads. File reads inside _classify_thread
        # are the dominant cost after the initial gh calls, so bailing here
        # protects the later threads from a runaway earlier one.
        budget.check_wallclock()
        ordered = _walk(root)
        participants: list[dict[str, Any]] = []
        for node in ordered:
            role = _role(node["author"])
            participant: dict[str, Any] = {
                "id": node["id"],
                "author": node["author"],
                "role": role,
                "body_excerpt": node["body"][:220],
            }
            reactions = reactions_map.get(node["id"])
            if reactions:
                participant["reactions"] = reactions
            participants.append(participant)
        role_sequence = "→".join(p["role"] for p in participants)
        resolved_raw = resolved_map.get(root["id"])
        if resolved_raw is True:
            resolved_flag: Any = True
        elif resolved_raw is False:
            resolved_flag = False
        else:
            resolved_flag = "unknown"

        # Derive learner reaction signal. A thread is "acknowledged" when the
        # learner (role=self) reacted to any non-self comment in the thread —
        # typically the mentor's. This lets the narrative distinguish
        # "replied with 👍" from "ignored".
        #
        # When the GraphQL fetch failed (`graph_ok=False`) we have no reaction
        # data at all — everything looks empty. Treat that as "unknown" (same
        # tri-state pattern as `resolved`) so downstream does not silently
        # render "답글 없음" from a fetch failure.
        learner_reactions: list[str] = []
        for p in participants:
            if p.get("role") == "self":
                continue
            for r in p.get("reactions") or []:
                user = (r.get("user") or "").lower()
                content = r.get("content")
                if not content:
                    continue
                if learner_login and user == learner_login.lower():
                    if content not in learner_reactions:
                        learner_reactions.append(content)
        if not graph_ok:
            learner_acknowledged: Any = "unknown"
        else:
            learner_acknowledged = bool(learner_reactions)

        # File-region read + classification (cap-gated)
        classification, classification_reason, evidence_snippet = _classify_thread(
            repo_path=repo_path,
            head_sha=detail.get("head_sha"),
            root=root,
            resolved=resolved_flag,
            budget=budget,
        )

        root_role = _role(root["author"])
        thread_entry: dict[str, Any] = {
            "id": root["id"],
            "path": root["path"],
            "line": root["line"],
            "author": root["author"],
            "role": root_role,
            "role_sequence": role_sequence,
            "participants": participants,
            "resolved": resolved_flag,
            "classification": classification,
            "classification_reason": classification_reason,
            "learner_reactions": learner_reactions,
            "learner_acknowledged": learner_acknowledged,
            "body_excerpt": root["body"][:220],
            "evidence_snippet": evidence_snippet,
        }
        threads.append(thread_entry)
        budget.threads_read += 1

    detail["threads"] = threads
    return detail


def _classify_thread(
    repo_path: Path,
    head_sha: str | None,
    root: dict[str, Any],
    resolved: Any,
    budget: _Budget,
) -> tuple[str, str | None, str | None]:
    """Decide still-applies / likely-fixed / already-fixed / ambiguous for one thread.

    Returns `(classification, reason, evidence_snippet)`. `reason` is a short
    machine tag the consumer can surface alongside the class.

    Why `likely-fixed` exists (see `docs/agent-operating-contract.md` step 21):
    `diff_hunk` on a review comment is the hunk **from the PR diff at review
    time**, not "the code the mentor wants." The `+` lines are the learner's
    current code (what the mentor commented on). The `-` lines are base-branch
    code the PR removed and are meaningless to match against the head file.
    So we can only reliably ask "are the cited `+` lines still in the learner's
    file?" — yes means still-applies, no means the learner changed that code,
    which is a **weak** signal of a fix. We cannot prove the change addresses
    the mentor's concern without semantic analysis. `likely-fixed` captures
    that uncertainty so downstream can surface it as "probably done, please
    verify with `git show`."

    Decision order:
      1. GraphQL `isResolved=true` → `already-fixed` (only strong signal).
      2. Read file at `head_sha`. Extract `+` tokens from `diff_hunk`.
      3. Cited `+` code present in region → `still-applies`.
      4. Cited code present globally but not region → `still-applies` (drifted).
      5. Cited code absent globally → `likely-fixed` (learner changed code; unverified).
      6. No tokens extractable → `ambiguous` (no basis for any class).
      7. File unreadable / budget skip / head missing → `ambiguous`.
    """
    if resolved is True:
        return "already-fixed", "isResolved", None
    if budget.file_reads >= MAX_FILE_READS:
        budget.note_skipped(f"classify thread {root['id']}", "file_read_cap")
        return "ambiguous", "file_read_cap", None
    if not head_sha or not root.get("path"):
        return "ambiguous", "head_or_path_missing", None

    text = _read_file_at(repo_path, head_sha, root["path"])
    budget.file_reads += 1
    if text is None:
        return "ambiguous", "file_unreadable", None

    lines = text.splitlines()
    cited_line = root.get("line") or root.get("original_line")
    if isinstance(cited_line, int) and 1 <= cited_line <= len(lines):
        lo = max(0, cited_line - 1 - FILE_REGION_HALF_LINES)
        hi = min(len(lines), cited_line + FILE_REGION_HALF_LINES)
        snippet_lines = lines[lo:hi]
    else:
        snippet_lines = lines[: 2 * FILE_REGION_HALF_LINES]

    region = "\n".join(snippet_lines)
    evidence = region[:400] if region else None

    # Extract `+` tokens only. `+` lines are the learner's PR code at review
    # time — the code the mentor is commenting about. `-` lines are base-branch
    # code that the PR already removed, so checking whether they "remain" in
    # head is meaningless. Drop `-` entirely.
    hunk = root.get("diff_hunk") or ""
    cited_tokens: list[str] = []
    for raw_line in hunk.splitlines():
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            stripped = raw_line[1:].strip()
            if len(stripped) >= 6:
                cited_tokens.append(stripped)

    if not cited_tokens:
        return "ambiguous", "tokens_missing", evidence

    if any(tok in region for tok in cited_tokens):
        return "still-applies", "cited_code_present_in_region", evidence

    if any(tok in text for tok in cited_tokens):
        # Code still in file but moved away from the cited line — still applies.
        return "still-applies", "cited_code_drift", evidence

    # Cited code is gone from the learner's file. That means the learner
    # changed it — but we cannot prove from tokens alone that the change
    # addresses the mentor's concern. Emit the weak positive class instead of
    # escalating to already-fixed.
    return "likely-fixed", "cited_code_removed", evidence


def _read_file_at(repo_path: Path, ref: str, file_path: str) -> str | None:
    rc, out, _ = _run_git(repo_path, ["show", f"{ref}:{file_path}"])
    if rc != 0:
        return None
    return out


def _fetch_thread_graph(
    upstream_owner_repo: str,
    target_number: int,
    budget: _Budget,
) -> tuple[dict[int, bool], dict[int, list[dict[str, str]]], bool]:
    """Fetch `isResolved` and reactions for each review comment via GraphQL.

    Returns `(resolved_map, reactions_map, graph_ok)`:
      - resolved_map: comment databaseId → thread isResolved bool
      - reactions_map: comment databaseId → list of {content, user}
      - graph_ok: False when the GraphQL call was skipped or failed. Downstream
        must treat reactions as "unknown" (not "absent") in that case, otherwise
        a fetch failure silently becomes "답글 없음" in the narrative.

    Reactions cover all 8 GitHub reaction types without filtering; consumers
    decide how to interpret them.
    """
    forced = os.environ.get("WOOWA_FORCE_GRAPHQL_FAIL")
    if forced:
        budget.note_skipped("graphql reviewThreads", f"forced:{forced}")
        return {}, {}, False
    owner, _, repo = upstream_owner_repo.partition("/")
    if not owner or not repo:
        budget.note_skipped("graphql reviewThreads", "invalid_upstream")
        return {}, {}, False
    query = (
        "query($owner:String!,$repo:String!,$number:Int!){"
        "repository(owner:$owner,name:$repo){"
        "pullRequest(number:$number){"
        "reviewThreads(first:50){nodes{isResolved comments(first:50){nodes{"
        "databaseId reactions(first:20){nodes{content user{login}}}"
        "}}}}"
        "}}}"
    )
    try:
        rc, out, _ = _run_gh(
            budget,
            [
                "api", "graphql",
                "-f", f"query={query}",
                "-F", f"owner={owner}",
                "-F", f"repo={repo}",
                "-F", f"number={target_number}",
            ],
        )
    except _BudgetExceeded:
        budget.note_skipped("graphql reviewThreads", "gh_call_cap")
        return {}, {}, False
    if rc != 0:
        budget.note_skipped("graphql reviewThreads", "graphql_failure")
        return {}, {}, False
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError:
        budget.note_skipped("graphql reviewThreads", "graphql_parse_failure")
        return {}, {}, False
    nodes = (
        data.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviewThreads", {})
        .get("nodes", [])
    )
    resolved_map: dict[int, bool] = {}
    reactions_map: dict[int, list[dict[str, str]]] = {}
    for node in nodes or []:
        resolved = bool(node.get("isResolved"))
        for comment in (node.get("comments", {}) or {}).get("nodes", []) or []:
            cid = comment.get("databaseId")
            if cid is None:
                continue
            cid_int = int(cid)
            resolved_map[cid_int] = resolved
            reaction_nodes = (comment.get("reactions", {}) or {}).get("nodes", []) or []
            reactions: list[dict[str, str]] = []
            for r in reaction_nodes:
                content = r.get("content")
                user_login = ((r.get("user") or {}).get("login") or "")
                if content:
                    reactions.append({"content": content, "user": user_login})
            if reactions:
                reactions_map[cid_int] = reactions
    return resolved_map, reactions_map, True


def _resolve_upstream_remote(
    remotes: dict[str, str],
    upstream_owner_repo: str | None,
) -> str:
    """Find the remote whose URL matches the upstream owner/repo.

    Does not assume the remote is named `upstream`. Falls back to `origin`
    (same-repo PR workflow) if no URL match is found.
    """
    if upstream_owner_repo:
        owner_repo_lc = upstream_owner_repo.lower()
        for name, url in remotes.items():
            lower = url.lower()
            if owner_repo_lc in lower or owner_repo_lc.replace("/", ":") in lower:
                return name
    if "upstream" in remotes:
        return "upstream"
    return "origin"


def _resolve_diff_refs(
    repo_path: Path,
    upstream_remote: str,
    upstream_owner_repo: str | None,
    target_pr: dict[str, Any] | None,
    open_prs_raw: list[dict[str, Any]],
    budget: _Budget,
) -> dict[str, Any]:
    if not target_pr:
        return {"base_ref": None, "head_ref": None}
    raw = next(
        (pr for pr in open_prs_raw if pr.get("number") == target_pr.get("number")),
        None,
    ) or {}
    base_ref_name = raw.get("baseRefName") or target_pr.get("base_ref")
    head_ref_name = raw.get("headRefName") or target_pr.get("head_ref")
    number = target_pr.get("number")
    if not base_ref_name or not head_ref_name:
        return {"base_ref": None, "head_ref": None}

    # --- base_ref: try upstream_remote/<base>, fall back to origin/<base> ---
    base_ref_full: str | None = None
    for candidate in (f"{upstream_remote}/{base_ref_name}", f"origin/{base_ref_name}"):
        rc, _, _ = _run_git(repo_path, ["rev-parse", "--verify", candidate])
        if rc == 0:
            base_ref_full = candidate
            break
    if base_ref_full is None:
        budget.note_skipped(f"diff.base_ref for PR #{number}", "base_ref_not_found")

    # --- head_ref: same-repo PR lookup first ---
    head_ref_full: str | None = None
    rc, _, _ = _run_git(repo_path, ["rev-parse", "--verify", f"{upstream_remote}/{head_ref_name}"])
    if rc == 0:
        head_ref_full = f"{upstream_remote}/{head_ref_name}"

    # --- origin/<head> (learner fork as origin) ---
    if head_ref_full is None:
        rc, _, _ = _run_git(repo_path, ["rev-parse", "--verify", f"origin/{head_ref_name}"])
        if rc == 0:
            head_ref_full = f"origin/{head_ref_name}"

    # --- fork PR: fetch pull/<n>/head into a local ref and use it ---
    if head_ref_full is None and number is not None and upstream_remote:
        local_ref = f"refs/pr/{number}/head"
        rc, _, err = _run_git(
            repo_path,
            ["fetch", upstream_remote, f"pull/{number}/head:{local_ref}"],
        )
        if rc == 0:
            head_ref_full = local_ref
        else:
            budget.note_skipped(
                f"diff.head_ref for PR #{number}",
                f"pull_head_fetch_failed: {err.strip()[:120]}",
            )

    if head_ref_full is None:
        budget.note_skipped(f"diff.head_ref for PR #{number}", "head_ref_not_found")

    return {"base_ref": base_ref_full, "head_ref": head_ref_full}


def build_learner_state(
    repo_name: str,
    repo_path: Path,
    prompt: str | None = None,
    upstream_owner_repo: str | None = None,
) -> dict[str, Any]:
    """Run sections A–G of the Learner State Assessment.

    This function is resilient: individual gh/git failures degrade into a
    `partial` coverage snapshot rather than raising.
    """
    budget = _Budget()
    coverage = "full"
    try:
        topo = _section_a_topology(repo_path, upstream_owner_repo, budget)
        working_copy, head_branch, head_sha = _section_b_working_copy(repo_path)
        learner_login = _section_c_identity(repo_path)

        open_prs_raw: list[dict[str, Any]] = []
        closed_prs_raw: list[dict[str, Any]] = []
        if upstream_owner_repo and learner_login:
            open_prs_raw, closed_prs_raw = _section_d_prs(upstream_owner_repo, learner_login, budget)
        elif not upstream_owner_repo:
            budget.note_skipped("upstream PR listing", "upstream_repo_not_provided")
        elif not learner_login:
            budget.note_skipped("upstream PR listing", "learner_login_not_resolved")

        prs_rows = [_pr_row(pr, "open") for pr in open_prs_raw]
        prs_rows.extend(_pr_row(pr, "closed") for pr in closed_prs_raw)

        target_number, selection_reason = _select_target(open_prs_raw, prompt, head_branch)
        target_detail: dict[str, Any] | None = None
        if target_number and upstream_owner_repo:
            try:
                target_detail = _section_e_target_detail(
                    upstream_owner_repo,
                    target_number,
                    learner_login,
                    repo_path,
                    budget,
                )
            except _BudgetExceeded as exc:
                budget.note_skipped("target_pr_detail", exc.reason)
                coverage = "partial"

        target_row = next(
            (r for r in prs_rows if r.get("number") == target_number and r.get("state") == "open"),
            None,
        )
        diff_refs = _resolve_diff_refs(
            repo_path,
            topo["upstream_remote"],
            upstream_owner_repo,
            target_row,
            open_prs_raw,
            budget,
        )

        if budget.skipped:
            coverage = "partial"

        snapshot: dict[str, Any] = {
            "computed_at": _now_iso(),
            "repo": repo_name,
            "mission_path": str(repo_path),
            "head_branch": head_branch,
            "head_sha": head_sha,
            "fetch_state": topo["fetch_state"],
            "upstream_remote": topo["upstream_remote"],
            "working_copy": working_copy,
            "prs": prs_rows,
            "target_pr_number": target_number,
            "target_pr_selection_reason": selection_reason,
            "target_pr_detail": target_detail,
            "diff": diff_refs,
            "coverage": coverage,
            "skipped": budget.skipped,
            "cycle_hint": _derive_cycle_hint(head_branch),
        }
        return snapshot
    except _BudgetExceeded as exc:
        return {
            "computed_at": _now_iso(),
            "repo": repo_name,
            "mission_path": str(repo_path),
            "head_branch": "",
            "head_sha": "",
            "fetch_state": "stale",
            "upstream_remote": "origin",
            "working_copy": {
                "clean": False,
                "ahead": 0,
                "behind": 0,
                "uncommitted_files": [],
                "untracked_files": [],
                "fingerprint": _sha256(""),
            },
            "prs": [],
            "target_pr_number": None,
            "target_pr_selection_reason": "no_open_pr",
            "target_pr_detail": None,
            "diff": {"base_ref": None, "head_ref": None},
            "coverage": "partial",
            "skipped": budget.skipped + [{"what": "full_assessment", "reason": exc.reason}],
            "cycle_hint": None,
        }


def write_learner_state(
    repo_name: str,
    repo_path: Path | None = None,
    prompt: str | None = None,
    upstream_owner_repo: str | None = None,
) -> dict[str, Any]:
    """Compute a learner-state snapshot and persist it to the contexts dir."""
    from .schema_validation import validate_payload

    repo_entry = find_repo(repo_name)
    path = Path(repo_path) if repo_path else Path(repo_entry["path"]).expanduser()
    upstream = upstream_owner_repo or repo_entry.get("upstream") or repo_entry.get("upstream_slug")

    payload = build_learner_state(
        repo_name=repo_name,
        repo_path=path,
        prompt=prompt,
        upstream_owner_repo=upstream,
    )

    # Fail fast at producer time. A schema drift here is structural (producer
    # forgot a field or emitted a bad enum) and should not silently ship to
    # disk where the AI session later blows up on read.
    validate_payload("learner-state", payload)

    out_path = repo_context_dir(repo_name) / "learner-state.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["_path"] = str(out_path)
    return payload


def load_learner_state(repo_name: str) -> dict[str, Any] | None:
    path = repo_context_dir(repo_name) / "learner-state.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_stale(
    snapshot: dict[str, Any],
    current_head_sha: str,
    current_fingerprint: str,
    current_target_head_sha: str | None,
    ttl_seconds: int = 600,
) -> bool:
    """Apply the re-scan cache-key rule from agent-operating-contract.md step 6."""
    if snapshot.get("head_sha") != current_head_sha:
        return True
    working_copy = snapshot.get("working_copy") or {}
    if working_copy.get("fingerprint") != current_fingerprint:
        return True
    detail = snapshot.get("target_pr_detail") or {}
    if current_target_head_sha is not None and detail.get("head_sha") != current_target_head_sha:
        return True
    computed_at = snapshot.get("computed_at")
    if not computed_at:
        return True
    try:
        ts = datetime.strptime(computed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    return age > ttl_seconds
