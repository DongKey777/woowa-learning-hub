# Token Budget

## Purpose

The learner never runs the CLI, but the agent reads artifacts on their behalf. Every artifact byte the agent opens becomes a token the learner pays for. This document describes the cost of each reading path and the rules an agent should apply before drilling down.

Approximate conversion for JSON with mixed Korean and ASCII: **1 token ≈ 3.5 bytes**.

## Artifact Sizes (java-janggi reference, 230 PRs / 9,977 comments)

| Priority | Artifact | Size | ≈ Tokens |
|---|---|---|---|
| 1 | `actions/coach-run.json` | ~140 KB | ~40K |
| 2 | `analysis/mission-map.json` | ~9 KB | ~2.5K |
| 3 | `memory/profile.json` | ~5 KB | ~1.5K |
| 4 | `memory/summary.json` | ~17 KB | ~5K |
| 5 | `contexts/coach-candidate-interpretation.json` | ~37 KB | ~10K |
| 6 | `contexts/coach-focus.json` | ~41 KB | ~12K |
| 7 | `actions/coach-response.json` (optional) | ~25 KB | ~7K |
| drilldown | `packets/topic-*.json` | ~60–92 KB | ~17–26K |
| drilldown | `packets/pr-<n>-report.json` | ~150–190 KB | ~43–54K |
| avoid | `memory/history.jsonl` | ~230 KB | ~65K |

Sizes grow linearly with archive volume. Numbers above are ceiling references, not fixed budgets.

## Pre-coach-run Direct Read Budget

Before `coach-run` produces any artifact, the **Learner State Assessment** in `agent-operating-contract.md` runs a direct-read scan of the learner's git state and upstream PR. That scan has its own budget, separate from the artifact reading paths below.

| Scope | Cap |
|---|---|
| PRs deep-dived (full comment + file read) | 1 (the `target_pr`) |
| Other open PRs | list metadata only, no deep read |
| Unresolved threads read on `target_pr` | ≤ 20 most recent |
| File regions read (±20 lines each) | ≤ 10 |
| `gh` / GraphQL calls total | ≤ 8 |
| Wall-clock | ~60s soft limit |
| Approximate token cost | ~8K–15K |

If any cap is hit, the assessment writes `contexts/learner-state.json` with `coverage: "partial"` and a `skipped` list, then proceeds to `coach-run`. Never block the session on a full scan.

On subsequent turns of the same session, re-read `learner-state.json` instead of re-running the scan. Re-run if **any** of these changed: `git HEAD` SHA, `target_pr` head SHA, `working_copy.fingerprint` (`sha256` of `git status --porcelain=v1`), or >10 minutes elapsed since `computed_at`. The fingerprint catches the common case where the learner edits files without committing.

## Reading Paths

### Minimum path (simple concept question)

- read only `coach-run.json`
- estimated cost: **~40K tokens**
- coach-run.json embeds the memory snapshot, focus candidates, and mission map summary, so it is usually self-sufficient

### Typical path (PR-anchored question)

- read `coach-run.json` + `mission-map.json`
- estimated cost: **~42K–45K tokens**
- use this as the default path for most sessions
- the memory snapshot embedded in `coach-run.json.memory` is authoritative; do not re-open `memory/profile.json` or `memory/summary.json` unless a field is missing

### Evidence confirmation path

- add `coach-candidate-interpretation.json` + `coach-focus.json`
- estimated cost: **~65K–70K tokens**
- use when the learner asks "why this PR?" or "what did other crews do?"

### Drilldown path (worst case)

- add one `topic-*.json` or one `pr-<n>-report.json`
- estimated cost: **~90K–120K tokens**
- use only when the evidence confirmation path is insufficient and a specific PR or topic needs inspection

### Forbidden

- never read `memory/history.jsonl` in full — it is append-only and grows unbounded
- never open multiple `pr-*-report.json` files in a single session unless the task is an explicit multi-PR comparison
- never open multiple `topic-*.json` packets in a single session

## Cost Hot Spots

1. **`coach-run.json` alone accounts for ~80% of the minimum-path cost.** It embeds `memory.summary` and `memory.profile`, so reading those sidecar files redundantly wastes tokens unless the session needs the full-fidelity versions.
2. **`pr-<n>-report.json` and `topic-*.json` each exceed the entire minimum path.** Drilling into one of these is an explicit budget decision.
3. **`coach-focus.json` + `coach-candidate-interpretation.json` together are ~22K tokens.** Read them together only when the question is actually about peer comparison or learning-point recommendation.

## Agent Rules

1. **Default to the minimum or typical path.** Do not open priority 5–6 files unless the question demands peer evidence.
2. **Drilldown requires justification.** Before opening a `pr-*-report.json` or `topic-*.json`, state the reason (e.g., "the learner asked about a specific review in PR #270").
3. **Never batch-open all packets to survey the repo.** Use `mission-map.json` for that purpose — it is ~3K tokens and exists precisely to avoid wide scans.
4. **Reuse within a session.** Once `coach-run.json` is read, do not re-open it to look up a field; parse it once and keep the relevant fields in working memory.
5. **Prefer `coach-run.json.memory` over sidecar memory files.** The embedded snapshot is authoritative for the current session and reading `summary.json`/`profile.json` separately duplicates cost.
6. **Only open `coach-response.json` as a reference hint.** It is a draft suggestion, not the final answer, and costs ~7K for marginal value.

## Budget Signals the Agent Should Surface

When a session crosses into the drilldown path, the agent should tell the learner implicitly by the depth of evidence cited. If the agent has read a `pr-report.json`, it should cite at least one specific review comment from that report. Otherwise the drilldown was wasted budget.

## Related Documents

- [artifact-catalog.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/artifact-catalog.md) — artifact reading priority
- [agent-operating-contract.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/agent-operating-contract.md) — canonical artifact order
- [memory-model.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/memory-model.md) — why memory snapshot is embedded in coach-run.json
