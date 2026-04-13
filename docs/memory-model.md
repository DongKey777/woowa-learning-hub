# Memory Model

## Purpose

This document explains how learning memory is modeled and how another AI should interpret it.

The system stores two memory views:

- `summary`: aggregated counts and recent patterns
- `profile`: coaching-oriented long-term interpretation

## Memory Layers

### 1. History

File:

- `memory/history.jsonl`

Meaning:

- append-only session log
- each line is one completed coaching session

Important fields:

- `prompt`
- `question_fingerprint`
- `diff_fingerprint`
- `primary_topic`
- `primary_intent`
- `primary_learning_points`
- `learning_point_recommendations`
- `follow_up_question`

### 2. Summary

File:

- `memory/summary.json`

Meaning:

- descriptive aggregate over history
- mostly count-oriented

Important fields:

- `top_topics`
- `top_intents`
- `top_learning_points` (raw cumulative counts)
- `weighted_learning_points` (time-decayed counts, half-life 14 days)
- `repeated_learning_points`
- `learning_point_confidence`
- `recent_learning_points`
- `repeated_question_patterns`
- `recurring_paths`

`top_learning_points` is the historical cumulative view. `weighted_learning_points` is the recency-aware view and is the preferred source when choosing what to emphasize now.

### 3. Profile

File:

- `memory/profile.json`

Meaning:

- coaching-oriented interpretation of summary/history
- what should influence future recommendations

Important fields:

- `confidence`
- `dominant_learning_points`
- `repeated_learning_points`
- `underexplored_learning_points`
- `recent_learning_streak`
- `open_follow_up_queue`

Each dominant or repeated learning point carries a `recency_status` derived from the ratio of weighted count to raw count:

- `active` — weighted/raw > 0.7 (the learner is currently engaged with the point)
- `cooling` — 0.3 ≤ weighted/raw ≤ 0.7 (engagement is fading)
- `dormant` — weighted/raw < 0.3 (the point shows up in history but not recent sessions)

Use `recency_status` to decide whether "repeated" means "currently repeating" or "was a phase".

## How To Use Memory

### Use `summary` for:

- seeing raw frequency
- identifying repeated topics and intents
- checking whether a question pattern is stable

### Use `profile` for:

- deciding whether to deepen or broaden
- choosing what to emphasize in the next answer
- identifying neglected learning points

## Recommended Interpretation Rules

### If `repeated_learning_points` is non-empty

Interpretation:

- the learner is returning to the same conceptual surface
- likely needs deeper examples, not only wider coverage
- this should be trusted more when confidence is `medium` or `high`

Action:

- recommend at least one "deepen" example

### If `underexplored_learning_points` is non-empty

Interpretation:

- the learner has blind spots or hasn't diversified enough

Action:

- recommend one "broaden" example when the current question allows it

### If `recent_learning_streak` exists

Interpretation:

- the learner is in a short-term repetition loop

Action:

- explicitly decide whether to continue the streak or interrupt it with a broader point

### If `confidence` is `low`

Interpretation:

- long-term memory is still weak
- the current question and current evidence should dominate

Action:

- avoid strong “you always do X” style claims
- treat memory as hint only

### If `repeated_question_patterns` is high

Interpretation:

- the learner may be stuck on one recurring framing

Action:

- rephrase the same issue using a different learning point or evidence type

## Important Caveats

- counts are not truth
- low counts should be described as weak signals
- memory should steer recommendation priority, not override current evidence
- if current evidence strongly conflicts with long-term profile, current evidence wins
- repeated learning points should be interpreted using both:
  - `question_fingerprint`
  - `diff_fingerprint`
  so the system can separate learner repetition from repeated processing of the same diff
- decay matters: older sessions should weigh less than recent sessions

## Practical Rule

Use memory to answer:

- what this learner keeps returning to
- what this learner rarely touches
- whether this session should deepen or broaden

Do not use memory to answer:

- which PR is objectively best
- which design is objectively correct

## Write Ordering and Recovery

Memory state is persisted by `coach-run` in a best-effort 2-phase write. Details are in [error-recovery.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/error-recovery.md). Key points for memory consumers:

- `coach-run.json` embeds the authoritative memory snapshot for the current session
- `memory/summary.json` and `memory/profile.json` are the next-session initial context
- if `history.jsonl` mtime is newer than `summary.json` or `profile.json`, the next session automatically recomputes both from history via `needs_recompute()`
- an agent should trust `coach-run.json.memory` as authoritative for the current session even if sidecar files are stale
