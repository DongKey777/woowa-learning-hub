# Gemini Skill: Peer Analysis

Use this module when the learner asks how other crews handled the same mission.

## Focus

- use `contexts/coach-candidate-interpretation.json`
- use `contexts/coach-focus.json` only as shortlist support
- use `packets/topic-*.json` or `packets/compare-*.json` only when interpretation is insufficient
- explain recommendations by learning point
- prefer mentor review comment and thread evidence over generic PR body text

## Evidence rules

- Quote from `mentor_comment_samples` or the last mentor turn in `thread_samples`.
- Treat `crew_response_samples` as the learner's prior reply, not mentor feedback.
- Never cite bot rows.
- If a recommendation lacks a grounded mentor quote, do not make it primary.

## Budget

Before opening a `packets/*.json`, verify that interpretation + focus are not enough. See `docs/token-budget.md`.

See `docs/evidence-roles.md`.
