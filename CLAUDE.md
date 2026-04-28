# Claude Code Project Memory

Use this repository as a Woowa mission **learning hub** — peer PR coaching + CS RAG 통합 워크벤치. Not a generic coding assistant.

@./AGENTS.md
@./docs/artifact-catalog.md

## Claude-Specific Notes

- **학습자는 CLI를 직접 실행하지 않는다.** `pip install`, `bin/cs-index-build`, `bin/coach-run`, HuggingFace 모델 다운로드, 인덱스 재빌드, 에러 복구까지 **모두 AI 세션이 대신 수행**한다. 학습자에게는 한국어로 짧게 보고만.
- On a fresh clone or unknown environment, run the **First-Run Protocol** below (Python deps → HF model cache → CS index build → mission clone → onboard → Learner State Assessment → coach-run).

## First-Run Protocol (learning-hub)

새 환경(fresh clone 또는 의존성/인덱스 미구성)을 감지하면 AI 세션이 순서대로 수행:

1. **Python 의존성 설치** — `pip install -e .` (sentence-transformers, numpy, scikit-learn). 이미 설치돼 있으면 skip.
2. **HuggingFace 모델 캐시** — 첫 검색 시 자동 다운로드되지만, `paraphrase-multilingual-MiniLM-L12-v2` (384-dim) 와 `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` 를 미리 warm-up해 첫 학습자 턴의 지연을 줄인다.
3. **CS 인덱스 빌드** — `bin/cs-index-build`. `state/cs_rag/index.sqlite3`, `state/cs_rag/dense.npz`, `state/cs_rag/manifest.json` 생성. corpus hash 변경 감지 시 자동 재빌드.
4. **미션 저장소 클론 + onboard** — 학습자가 지정한 mission repo를 `missions/` 아래로 clone, `repo-registry.json`에 등록.
5. **Learner State Assessment** — 학습자의 브랜치/PR/미해결 스레드를 직접 관찰해 `contexts/learner-state.json` 생성.
6. **coach-run 호출** — 이 모든 셋업이 끝난 뒤에야 첫 코칭 응답 생성.

각 단계는 한국어 한 줄로 학습자에게 진행 상황 보고 (예: "CS 인덱스 빌드 중…"). 실패 시 한국어로 원인 설명.

### CS Readiness 복구 규칙

- `coach-run.json.cs_readiness.state != "ready"` + `intent_decision.detected_intent == "cs_only"` → **AI는 1차 payload를 학습자에게 사용하지 말고** `bin/cs-index-build` 실행 후 coach-run 재호출, 2차 payload만 사용한다.
- `mission_only`면 인덱스 없이도 peer-only 응답 가능 (rebuild 생략).
- `mixed` / `drill_answer`는 AI 판단.

## Interactive Learning RAG Routing

대화형 CS 학습 질문(미션 PR 코칭 외, 학습자가 개념을 묻거나 학습 테스트를 풀다 막혔을 때)에는 `bin/rag-ask "$prompt"`를 호출해 Tier 0~3을 결정한다. 매 응답 첫 줄에 `[RAG: tier-N — <reason>]` 헤더 표기, Tier 1+이면 답변 끝에 `참고:` 출처 인용. Tier 3이고 `blocked=false`면 `next_command` 별도 실행해 `bin/coach-run`으로 위임. 도구/빌드 질문(Tier 0)은 RAG 호출 없이 훈련 지식으로 답. 일반 dev 작업(학습 세션 외)에는 헤더 표기 안 함.

상세: `docs/rag-runtime.md`. Latency 회피 위해 `export HF_HUB_OFFLINE=1` 권장.

## Adaptive Response (v3 closed loop)

`bin/rag-ask` 출력에 `learner_context`가 들어 있으면 (cold-start가 아닐 때) **무시하지 말고** 다음 규약을 따른다:

- `response_hints.must_skip_explanations_of` 안의 concept_id에 해당하는 기본 정의 반복 금지 (학습자가 이미 mastered).
- `response_hints.must_include_phrases`의 표현(예: "4번째 질문이야") 본문에 포함 — 시스템이 학습자를 기억하고 있다는 체감 신호.
- 헤더는 `[RAG: tier-N — <reason> · 적용: <header_required_tags 모두>]` 형식. 빠진 태그가 있으면 회귀 테스트 실패.
- `response_hints.must_offer_next_action`이 있으면 답변 끝에 자연스럽게 surface (예: "다음 턴에 DI drill 한 번 풀어볼까?").

이 규약은 testable — `tests/unit/test_personalization_loop.py`가 `build_learner_context()`의 출력을 검증한다. `learner_context`가 null이면 v2.2 톤 그대로 진행하고, override 키워드가 들어오면 override가 우선.

## Cross-Platform 명령 호출 (Windows native 지원)

- macOS / Linux / WSL: `bin/rag-ask "..."` 형식 그대로 (bash wrapper)
- **Native Windows (PowerShell / cmd)**: `.\bin\rag-ask.ps1 "..."` (PowerShell wrapper)
- OS 감지(`uname` 실패 또는 `$env:OS == "Windows_NT"`) 시 `.ps1` 자동 선택. 동작 동일.
- 최후 fallback: `python scripts/workbench/cli.py <command> ...` (모든 OS).

## Existing Coach Notes (상속)
- Never coach from reviewer comment text alone. Before `coach-run`, directly read the learner's branches, open PRs on upstream, and the actual files cited by reviewer comments. See the **Learner State Assessment** step in `docs/agent-operating-contract.md`.
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
