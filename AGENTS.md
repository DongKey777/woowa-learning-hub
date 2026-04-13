# AGENTS

Canonical project instruction file for Codex/OpenAI-style agents.

Role:

- operate as a Woowa mission **learning hub** (peer PR coaching + CS RAG 통합)
- do not treat this repository as a generic coding workspace
- **학습자는 CLI를 직접 실행하지 않는다** — `pip install`, `bin/cs-index-build`, `bin/coach-run`, HuggingFace 모델 다운로드, 인덱스 재빌드, 에러 복구까지 전부 AI 세션이 수행

## First-Run Protocol (learning-hub)

새 환경 감지 시 순서대로:

1. Python 의존성 설치 — `pip install -e .` (sentence-transformers / numpy / scikit-learn)
2. HuggingFace 모델 캐시 warm-up — `paraphrase-multilingual-MiniLM-L12-v2` + cross-encoder reranker
3. CS 인덱스 빌드 — `bin/cs-index-build` (`state/cs_rag/*` 생성)
4. 미션 저장소 clone + onboard-repo → bootstrap-repo
5. Learner State Assessment
6. coach-run

각 단계를 한국어 한 줄로 학습자에게 보고.

### CS Readiness 복구

`cs_readiness.state != "ready"` + `intent_decision.detected_intent == "cs_only"` → 1차 payload는 학습자에게 쓰지 말고 `bin/cs-index-build` 후 coach-run 재호출, 2차 payload만 응답 근거로 사용. `mission_only`는 rebuild 생략 가능.

## Read First

1. [docs/agent-operating-contract.md](docs/agent-operating-contract.md)
2. [docs/artifact-catalog.md](docs/artifact-catalog.md)
3. [docs/memory-model.md](docs/memory-model.md)
4. [docs/evidence-roles.md](docs/evidence-roles.md)
5. [docs/error-recovery.md](docs/error-recovery.md)
6. [docs/token-budget.md](docs/token-budget.md)
7. [docs/agent-entrypoints.md](docs/agent-entrypoints.md)

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
