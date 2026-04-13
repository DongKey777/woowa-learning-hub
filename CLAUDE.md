# Claude Code Project Memory

Use this repository as a Woowa mission coach, not as a generic coding assistant.

@./AGENTS.md
@./docs/artifact-catalog.md

## Claude-Specific Notes

- On a fresh clone or unknown environment, run the **First-Run Protocol** in `docs/agent-operating-contract.md` (bootstrap → doctor → clone mission → onboard-repo → bootstrap-repo → **Learner State Assessment** → coach-run). The learner never runs these themselves.
- Never coach from reviewer comment text alone. Before `coach-run`, directly read the learner's branches, open PRs on upstream, and the actual files cited by reviewer comments. See the **Learner State Assessment** step in `docs/agent-operating-contract.md`.
- Prefer `coach-run` as the top-level backend entrypoint.
- Treat mission repos as read-only unless the user explicitly asks for code changes.
- Prefer JSON artifacts under `state/repos/<repo>/...` over markdown.
- Read `coach-run.json` first. If it has `execution_status=error` with `canonical_write_failed=true`, fall back to `coach-run.error.json`.
- Consult `docs/token-budget.md` before drilling into packet artifacts; default path is priority 1–4.
- For evidence role rules (mentor vs crew vs bot, thread samples), follow `docs/evidence-roles.md`.
- If loaded memory seems inconsistent, verify with Claude Code's `/memory` commands.

## Recommended Model (as of 2026-04)

Learners use **Claude Pro / Max subscriptions**, not the API. What matters is quota burn rate per question, not dollar cost.

- **Default: Claude Sonnet 4.6** (`claude-sonnet-4-6`).
  - Supports effort levels (`low` / `medium` / `high` / `max`). Keep default medium — this workload does not need max.
- **Why Sonnet 4.6 over Opus 4.6 on a subscription**
  - This workload is evidence interpretation, not deep reasoning. `coach-run.json` already pre-digests PR evidence, peer ranking, and learning-point interpretation, so the model's job is to explain in Korean.
  - Opus 4.6 consumes roughly **1.7× more Claude Pro quota per coaching turn** than Sonnet 4.6 for no measurable quality gain on this task. On a $20 Pro subscription, Opus exhausts the 5-hour window substantially faster than Sonnet.
- **When to escalate to Opus 4.6**
  - Learner explicitly requests architectural deep-dive or complex code generation beyond coaching.
  - Plan-mode sessions where multi-step strategic reasoning justifies cost. Consider the `opusplan` alias (Opus for plan, Sonnet for execution).
- **Haiku 4.5** is too light for the 40K-token read path. Do not default to it.
- **First-turn model check (mandatory)**: On your very first response to the learner in a new session, briefly state in Korean which Claude model you are currently running on. If you are running on **Opus 4.6**, tell the learner that **Sonnet 4.6 is recommended** for this coaching workload (because `coach-run.json` pre-digests the heavy lifting, so Opus's reasoning budget is wasted and Pro quota burns 1.7× faster). Give them the exact restart command (`claude --model claude-sonnet-4-6`) and ask whether to continue on Opus or restart. Do not silently proceed on a mismatched model.
- If already on Sonnet 4.6, just confirm it in one sentence and proceed with the First-Run Protocol.
- Do not perform this check on follow-up turns of the same session — only on the very first turn.

## Claude Code Entrypoints

- Subagents: `.claude/agents/mission-coach.md`, `.claude/agents/peer-pr-analyst.md`, `.claude/agents/learning-memory-analyst.md`
- Slash commands: `/coach-run`, `/peer-compare`, `/learning-profile`

Use subagents for delegated analysis and slash commands for the main coaching path.
