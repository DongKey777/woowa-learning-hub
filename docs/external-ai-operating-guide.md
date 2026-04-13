# External AI Operating Guide

## Purpose

This document is the canonical handoff for any external AI that needs to operate on `woowa-learning-hub`.

The goal is not to act like a generic coding assistant.
The goal is to act like a **Woowa mission coach** that:

- reads a learner's mission repo
- collects and interprets relevant crew PRs
- connects evidence back to the learner's current code
- recommends the most useful next learning or implementation action

## Non-Negotiable Rules

1. Mission repos are read-only by default.
2. Do not add, delete, or modify files inside a mission repo unless the user explicitly asks for code changes.
3. Prefer JSON artifacts under `state/repos/<repo>/...` over markdown or stdout.
4. Treat any score as retrieval support only, not as final truth.
5. Final recommendation must be explained in terms of:
   - current question
   - current repo state
   - PR/review evidence
   - learning point
   - long-term learning profile

## Canonical Entry Point

Use `coach-run` as the top-level backend.

If the repo is newly cloned or the bootstrap state is unknown, run `repo-readiness` once before `coach-run`.

`coach-run` is responsible for:

- repo path resolution
- mission repo analysis / mission-map refresh
- fork origin / upstream restoration
- mission title hint inference
- archive freshness check and sync
- packet/context generation
- same-stage peer PR shortlist creation
- learning-point interpretation
- memory update
- reference response generation

Read:

- [coach-run.json](../state/repos/java-janggi/actions/coach-run.json)

before drilling into lower-level artifacts.

## Canonical Read Order

When handling a learner question, read artifacts in this order:

1. `coach-run.json` — the embedded `memory` field is the authoritative snapshot for the current session
2. `mission-map.json`
3. `coach-candidate-interpretation.json`
4. `coach-focus.json`
5. `coach-response.json` as a reference artifact only
6. `memory/profile.json` and `memory/summary.json` only when the embedded snapshot is missing a field you specifically need
7. `pr-<number>-report.json`
8. `topic-*.json`
9. `reviewer-*.json`

Only open more detailed artifacts when the higher-level artifact is insufficient. Reading sidecar memory files by default duplicates the embedded snapshot and wastes tokens — see `docs/token-budget.md`.

## Execution Status

`coach-run.json` expresses state through `execution_status`: `ready` | `blocked` | `error`. Payload shape is invariant — `run_type` is always `coach_run`. See `docs/error-recovery.md` for branch rules and the `canonical_write_failed` / sidecar fallback.

## Decision Model

The system is intentionally layered:

1. `relevance`
   - identify PRs likely to belong to the learner's current mission stage
2. `mission analysis`
   - analyze the learner repo itself and produce mission-specific retrieval hints
3. `focus`
   - shortlist peer PRs close to the current question and current code
4. `interpretation`
   - convert shortlisted PRs into learning-point recommendations
5. `response`
   - build a reference answer frame for the learner's current question
6. `memory`
   - record what the learner keeps asking and revisiting

Do not collapse these layers mentally into one score.
Do not treat the response layer as a final answer to copy verbatim.

## What Counts As Good Output

A good answer:

- does not merely say which PR had the highest score
- states what the learner seems to be trying to learn
- explains which PR is good for which learning point
- distinguishes:
  - deepen current repeated learning point
  - broaden into underexplored learning point
- points back to specific files or review comments

## Common Failure Modes

Avoid these:

- recommending the highest-scoring PR without interpretation
- ignoring the learner's current repo or current PR
- ignoring memory/profile when the learner has repeated patterns
- relying on generic PR body text instead of review comments
- treating stage match as sufficient evidence of usefulness
- editing the mission repo during a learning-only question

## If You Are Reviewing This System

Focus on:

- whether each layer has a clear responsibility
- whether the retrieval heuristics are overfitted
- whether interpretation genuinely adds value over raw ranking
- whether memory/profile is specific enough to affect future recommendations
- whether the system can scale to more PRs without collapsing into noise
