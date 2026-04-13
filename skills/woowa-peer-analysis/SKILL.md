---
name: "woowa-peer-analysis"
description: "Use when the learner asks how other crews approached the same mission, wants peer comparison, or needs learning-point-specific PR recommendations."
---

# Woowa Peer Analysis Skill

## When to use

- Peer comparison questions
- Concept explanation through peer examples
- "Which PR should I study?" questions

## Workflow

1. Read `contexts/coach-candidate-interpretation.json`.
2. Use `contexts/coach-focus.json` to understand shortlist rationale.
3. Use `packets/topic-*.json` only as supporting context, and only when interpretation + focus are insufficient.
4. Use `packets/compare-*.json` only for explicit two-PR comparison.
5. Organize the answer by learning point.

Consult `docs/token-budget.md` before opening any packet file.

## Evidence rules

- Quote from `mentor_comment_samples` or the last mentor turn in `thread_samples`.
- Treat `crew_response_samples` as the learner's prior reply, not mentor feedback.
- Never cite bot rows.
- If a recommendation lacks a grounded mentor quote, do not make it primary.

## Output requirements

- Say which PR is good for which learning point.
- Prefer real mentor review comment evidence over generic PR body text.
- Cite a specific path and role when possible.
- Separate:
  - deepen current repeated learning point
  - broaden underexplored learning point

## Do not do this

- Do not present raw shortlist score as the final recommendation.
- Do not batch-open multiple packet files.

## Related docs

- `docs/evidence-roles.md`
- `docs/token-budget.md`
