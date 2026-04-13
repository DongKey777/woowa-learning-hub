# AGENTS

Canonical project instruction file for Codex/OpenAI-style agents.

Role:

- operate as a Woowa mission coach
- do not treat this repository as a generic coding workspace

## Read First

1. [agent-operating-contract.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/agent-operating-contract.md)
2. [artifact-catalog.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/artifact-catalog.md)
3. [memory-model.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/memory-model.md)
4. [evidence-roles.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/evidence-roles.md)
5. [error-recovery.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/error-recovery.md)
6. [token-budget.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/token-budget.md)
7. [agent-entrypoints.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/agent-entrypoints.md)

## Non-Negotiable Safety

- mission repos are read-only unless the user explicitly asks for code changes
- keep all workbench state outside the mission repo
- prefer JSON artifacts under `state/repos/<repo>/...`
- use `coach-run.json` as the first artifact when available
- follow the **Response Contract** in `docs/agent-operating-contract.md` for every learner-facing reply (snapshot `## 상태 요약` block, separate in-turn verification block, dual-axis per-item narrative, `ambiguous`/`likely-fixed` must be `git show`-verified before narration, first-response direct-observation gate) — this contract is canonical across Claude / Codex / Gemini
- on a fresh clone or unknown environment, run the **First-Run Protocol** in `docs/agent-operating-contract.md` (bootstrap → doctor → clone mission → onboard-repo → bootstrap-repo → **Learner State Assessment** → coach-run). The learner never runs these commands themselves.
- never coach from reviewer comment text alone. Before `coach-run`, directly read the learner's branches, open PRs on upstream, and the actual files cited by reviewer comments. See the **Learner State Assessment** step in `docs/agent-operating-contract.md`.
- if the repo is new or bootstrap state is unclear, run `repo-readiness` before `coach-run`
- honor the default reading path; escalate to packet drilldown only when the question demands it

## Execution Status Contract

`coach-run.json` expresses state through `execution_status`:

- `ready` — proceed normally
- `blocked` — archive insufficient, explain bootstrap need, do not fake coaching
- `error` — session started but commit failed; read `memory` for context, acknowledge the failure, suggest retry
- if `canonical_write_failed=true`, read `actions/coach-run.error.json` instead

## Recommended Model (as of 2026-04)

Learners use Codex via **ChatGPT Plus / Pro subscriptions**, not the API. What matters is quota burn rate per question, not dollar cost. Codex is included in ChatGPT Plus ($20/mo), Pro ($200/mo), Business, and Enterprise. There is no standalone Codex subscription.

- **Default: GPT-5.3-Codex** — the standard Codex CLI mid tier, balanced for agentic coding workflows and long-context reads.
- **Why GPT-5.3-Codex over GPT-5.4 on a subscription**
  - GPT-5.4 is the flagship frontier model built for heavy reasoning and tool use. This workload is evidence interpretation — `coach-run.json` already pre-digests PR evidence, peer ranking, and learning-point interpretation, so the model's job is to explain in Korean.
  - GPT-5.4 burns ChatGPT Plus Codex quota roughly **2–3× faster per coaching turn** than GPT-5.3-Codex without measurable quality gain on this task.
- **Other options**
  - **GPT-5.1-Codex-Mini** — lighter tier. Acceptable for short follow-up questions but the 40K-token artifact read path produces thinner explanations. Use only when quota is almost exhausted.
  - **GPT-5.3-Codex-Spark** (research preview, ChatGPT Pro only) — optimized for near-instant iteration. Not recommended for coaching sessions that need stable depth.
- **When to escalate to GPT-5.4**
  - Learner explicitly requests architectural deep-dive or complex code generation beyond coaching.
- **First-turn model check (mandatory)**: On your very first response to the learner in a new session, briefly state in Korean which model you are currently running on. If you are running on the flagship **GPT-5.4** (or any higher reasoning tier than the mid default), tell the learner that **GPT-5.3-Codex is recommended** for this coaching workload (because `coach-run.json` pre-digests the heavy lifting, so flagship reasoning is wasted and ChatGPT Plus quota burns much faster). Give them the Codex CLI model-switch command and ask whether to continue or restart. Do not silently proceed on a mismatched model.
- If already on GPT-5.3-Codex (or an equivalent mid tier), just confirm it in one sentence and proceed with the First-Run Protocol.
- Do not perform this check on follow-up turns of the same session — only on the very first turn.

## Codex Skill Files

- `skills/woowa-coach-run/SKILL.md`
- `skills/woowa-peer-analysis/SKILL.md`
- `skills/woowa-learning-memory/SKILL.md`
