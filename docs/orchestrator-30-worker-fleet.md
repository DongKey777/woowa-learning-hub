# 30-Worker CS Quality Repair Fleet

This document defines the production worker topology for preparing the Woowacourse backend CS database.

The active fleet is no longer a "30 writers at once" expansion setup. It is a quality-repair system: category QA, primer-contract lint repair, link/anchor cleanup, RAG ranking regression work, index readiness, and release gating. The goal is to stop quality debt from growing while the corpus is already large.

## Principles

- Treat Woowacourse as a mission-based backend learning path, not a generic CS encyclopedia.
- Prefer beginner-safe entrypoints before advanced deep dives.
- Repair existing beginner primer contracts before adding new content.
- Keep authoring-lint, README return paths, retrieval anchors, signal rules, golden fixtures, and release gates owned by specialized workers.
- Use `write_scopes` instead of lane-level locking so independent workers can share a broad lane without editing the same ownership surface.
- Keep queue growth disabled for the quality fleet; workers may report follow-up gaps, but their `next_candidates` are not enqueued.

## Worker Groups

| Group | Count | Purpose |
|---|---:|---|
| QA | 21 | Repair category docs, primer contracts, anchors, return paths, follow-up ladders, and cross-category links. |
| RAG | 6 | Fix projection/JWT/transaction ranking regressions, signal rules, golden fixtures, and index readiness. |
| Ops | 3 | Control queue growth, run release gates, and prevent new quality debt from being batched. |

## Profile Fields

Each worker profile in `scripts/workbench/core/orchestrator_workers.py` has:

- `name`: stable worker id.
- `lane`: broad queue lane to claim from.
- `role`: `qa`, `rag`, or `ops` in the active quality fleet.
- `mode`: `write`, `fix`, `report`, `script`, `queue`, or `ops`.
- `claim_tags`: optional task filter. Empty means the worker claims any task in its QA lane.
- `write_scopes`: lock keys used to prevent conflicting writes.
- `target_paths`: path ownership shown in the prompt.
- `quality_gates`: checks the worker must keep in mind.
- `can_enqueue`: whether worker `next_candidates` are accepted.

## Locking Model

The orchestrator still stores queue items by lane, but workers are no longer blocked by lane alone. A worker can claim a task only when no other active lease has an overlapping `lease_write_scopes` value.

Examples:

- `runtime-qa-content-database` uses `qa:content:database`.
- `runtime-qa-primer-contract-database` uses the same scope, so both cannot repair database primer files at the same time.
- `runtime-rag-ranking-jwt` and `runtime-rag-ranking-projection` use separate ranking scopes, but `runtime-rag-signal-rules` owns the singleton `rag:signal_rules` surface.

## Operational Gates

- QA tasks should make the smallest patch that reduces a named failing contract.
- `next_candidates` are ignored for this fleet because `can_enqueue=false` on every profile.
- A Beginner primer is not ready until it satisfies the authoring contract: H1, `> 한 줄 요약`, exact difficulty, `관련 문서:` with at least three bullets, 8..15 lowercase `retrieval-anchor-keywords`, H2 bodies under 1600 characters, and final `## 한 줄 정리`.
- Golden fixtures and signal rules are singleton surfaces.
- Release is not ready until link checks, authoring lint, RAG unit/golden tests, and `bin/cs-index-build` are green.

## Rollout

1. Drain the old fleet by writing `state/orchestrator/stop.request` and letting active leases finish.
2. Review the drained content changes and current failing quality gates.
3. Start the new profile fleet with `bin/orchestrator fleet-start`.
4. Check `bin/orchestrator fleet-status`; it should show 30 profiled workers.
5. Run a short soak first and inspect `ACTIVE_ERROR_WORKERS`, `blocked`, primer lint pass rate, and RAG regression failure count.
6. Rebuild the CS index only after corpus churn drops; otherwise the live index will immediately become stale again.
