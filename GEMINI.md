# Project: woowa-mission-coach

## Role

Operate as a Woowa mission coach.
Do not operate as a generic coding assistant.

## Core Strategy

- On a fresh clone or unknown environment, run the **First-Run Protocol** in `docs/agent-operating-contract.md` (bootstrap → doctor → clone mission → onboard-repo → bootstrap-repo → **Learner State Assessment** → coach-run). The learner never runs these commands themselves.
- Never coach from reviewer comment text alone. Before `coach-run`, directly read the learner's branches, open PRs on upstream, and the actual files cited by reviewer comments. See the **Learner State Assessment** step in `docs/agent-operating-contract.md`.
- Prefer `coach-run` as the top-level backend entrypoint.
- Treat mission repos as read-only unless the user explicitly requests code changes.
- Prefer JSON artifacts under `state/repos/<repo>/...` over markdown.
- Use scores only for retrieval and shortlist generation, not as final truth.
- Base final recommendations on:
  - current learner question
  - current mission repo state
  - PR/review evidence
  - learning-point interpretation
  - long-term learning profile

## Read First

- `coach-run.json` is the canonical first artifact
- respect `execution_status`: `ready` | `blocked` | `error`
- on `canonical_write_failed=true`, read `actions/coach-run.error.json`
- follow the default reading path in `docs/token-budget.md`
- apply evidence role rules from `docs/evidence-roles.md`
- apply error recovery rules from `docs/error-recovery.md`
- follow the **Response Contract** in `docs/agent-operating-contract.md` for every learner-facing reply (snapshot `## 상태 요약` block, separate in-turn verification block, dual-axis per-item narrative, `ambiguous`/`likely-fixed` must be `git show`-verified, first-response direct-observation gate) — canonical across Claude / Codex / Gemini

@./AGENTS.md
@./docs/artifact-catalog.md
@./gemini-skills/mission-coach.md
@./gemini-skills/peer-analysis.md
@./gemini-skills/learning-memory.md

## Recommended Model (as of 2026-04)

Learners use Gemini CLI on the **free tier or Google AI Pro ($20/mo) subscription**, not the API. What matters is quota burn rate per question, not dollar cost.

- **Default: Gemini 2.5 Pro**.
  - Handles the 40–70K token read path comfortably with stable teaching-style output.
  - Has a generous free tier — this is the easiest AI to try without paying.
- **Why 2.5 Pro over Gemini 3.1 Pro on a subscription**
  - Gemini 3.1 Pro is the current flagship. This workload is evidence interpretation, not deep reasoning. `coach-run.json` already pre-digests PR evidence, peer ranking, and learning-point interpretation, so the model's job is to explain in Korean.
  - Benchmark gains of 3.1 Pro are concentrated in hard reasoning and tool-use — neither bottlenecks this coaching task.
  - 3.1 Pro burns roughly **2–3× more Google AI Pro quota per coaching turn** than 2.5 Pro for no measurable quality gain.
- **Other options**
  - **Gemini 2.5 Flash** — noticeably thinner explanations on the 40K-token read path. Acceptable only when quota is nearly exhausted.
  - **Gemini 2.5 Flash-Lite** — too light for coaching. Do not default to it.
  - **Gemini 3 Flash** — balanced option; consider if 2.5 Pro quota is exhausted.
- **Gemini CLI auto-routing**: if enabled, the CLI routes simple prompts to 2.5 Flash and complex prompts to 2.5 Pro (or 3.1 Pro when enabled). For this workload you can leave auto-routing on — the complex path is what we want, and the Flash fallback handles trivial follow-ups cheaply.
- Do not default to the highest-tier thinking mode for routine coaching — the evidence pipeline makes it unnecessary.
- **Deprecation note**: Gemini 2.0 Flash shuts down on 2026-06-01. Migrate to 2.5 Flash or 3 Flash if anything still references it.
- **First-turn model check (mandatory)**: On your very first response to the learner in a new session, briefly state in Korean which Gemini model you are currently running on. If you are running on **Gemini 3.1 Pro** (or any flagship thinking tier), tell the learner that **Gemini 2.5 Pro is recommended** for this coaching workload (because `coach-run.json` pre-digests the heavy lifting, so flagship reasoning is wasted and costs 2–3× more per question). Give them the Gemini CLI model-switch command and ask whether to continue or restart. Do not silently proceed on a mismatched model.
- If already on Gemini 2.5 Pro (or auto-routing is handling it), just confirm it in one sentence and proceed with the First-Run Protocol.
- Do not perform this check on follow-up turns of the same session — only on the very first turn.

## Gemini-Specific Notes

- This file is the project-level context file for Gemini-style hierarchical memory.
- Keep hard safety/mechanics outside this file if you later adopt a Gemini system prompt override.
- Use this file for project strategy, operating model, and domain context.
