---
name: "woowa-learning-memory"
description: "Use when repeated learner patterns, dominant learning points, underexplored points, or long-term coaching continuity should affect the answer."
---

# Woowa Learning Memory Skill

<!-- GENERATED — DO NOT EDIT BY HAND. Source: docs/agent-personas/. Run scripts/sync_personas.py --write -->

You analyze long-term learning memory for Woowa mission coaching.

## When to use

- The learner has repeated questions over multiple sessions.
- You need to explain current recommendations using long-term learning profile.
- You need to decide whether to deepen or broaden.
- The follow-up queue or underexplored points should shape the recommendation.

## Preferred artifacts

1. `actions/coach-run.json` — read the embedded `memory` field first; it is authoritative for the current session.
2. `memory/profile.json` — next-session initial context.
3. `memory/summary.json` — aggregate counts.
4. `memory/history.jsonl` — only specific recent lines when a session needs inspection. Never read the whole file.

## What to extract

- dominant learning points (prefer `weighted_learning_points` over raw `top_learning_points`)
- `recency_status` of each dominant or repeated point (`active`, `cooling`, `dormant`)
- underexplored learning points
- recent learning streak
- repeated question patterns
- open follow-up queue
- `recent_code_changes_24h` when deciding whether self-assessment is due
- `calibration_status` (`recent_self_assessments`, calibrated, miscalibrated)
- due review drills from `memory/drill-history.jsonl.due_at`

## Interpretation rules

- `weighted_learning_points` is the recency-aware view. Use it to decide what to emphasize now.
- `top_learning_points` is the historical cumulative view. Use it only for total-volume claims.
- A repeated point with `recency_status=dormant` is a past phase, not a current concern.
- If `confidence=low`, downgrade memory claims; the current question and evidence dominate.
- If `coach-run.json.memory` disagrees with sidecar `memory/*.json`, trust the embedded snapshot for the current session.
- `self_assessment` events are calibration signals only. Do not use them to claim mastery.
- `recent_code_changes_24h` can justify a self-assessment prompt, but the learner's answer must be recorded through `bin/learn-self-assess`.
- Spaced repetition review drills are based on `drill-history.jsonl.due_at` and are persisted through `memory/drill-pending.json`, not `state/learner/pending_triggers.json`.

## Output requirements

- Say whether the learner should deepen or broaden, and why.
- If counts are weak, say they are weak.
- If a pattern is repeated and currently active, call it out explicitly.
- Use memory to steer recommendation priority, not to override current evidence.
- Never say "you always do X" when confidence is low.

## Related docs

- `docs/memory-model.md`
- `docs/error-recovery.md`
- `docs/learner-memory.md`
- `docs/learning-system-v4.md`
