# Claude Code Project Memory

Use this repository as a Woowa mission **learning hub** — peer PR coaching + CS RAG 통합 워크벤치. Not a generic coding assistant.

@./AGENTS.md
@./docs/artifact-catalog.md
@./docs/learning-system-v4.md

## Claude-Specific Notes

- **학습자는 CLI를 직접 실행하지 않는다.** `pip install`, `bin/cs-index-build`, `bin/coach-run`, HuggingFace 모델 다운로드, 인덱스 재빌드, 에러 복구까지 **모두 AI 세션이 대신 수행**한다. 학습자에게는 한국어로 짧게 보고만.
- On a fresh clone or unknown environment, run the **First-Run Protocol** below (Python deps → HF model cache → CS index build → mission clone → onboard → Learner State Assessment → coach-run).

## First-Run Protocol (learning-hub)

새 환경(fresh clone 또는 의존성/인덱스 미구성)을 감지하면 AI 세션이 순서대로 수행. **모든 명령은 AI가 자동 호출하고 학습자가 외울 명령은 0개**:

0. **OS 감지 + Windows 셋업** — `uname` 실패 또는 `$env:OS == "Windows_NT"`이면 native Windows. 학습자에게 한국어로 동의 받은 후 `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` 자동 호출 (PowerShell, 한 번만). 이후 명령은 OS별 자동 분기 — `bin/<cmd>` (Unix) / `.\bin\<cmd>.ps1` (Windows native) / `python scripts/workbench/cli.py <cmd>` (universal fallback).
1. **Python 의존성 설치** — `pip install -e .` (sentence-transformers, FlagEmbedding, LanceDB, numpy, scikit-learn). 이미 설치돼 있으면 skip.
2. **GitHub 인증** — `gh auth status` 확인 후 미인증이면 `gh auth login` 트리거 (브라우저 자동 열림).
3. **HuggingFace 모델 캐시** — 첫 검색 시 자동 다운로드되지만, `BAAI/bge-m3` 와 `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` 를 미리 warm-up.
4. **CS 인덱스 빌드** — `bin/cs-index-build` (또는 Windows native `.ps1`). 기본값은 LanceDB v3이며 `state/cs_rag/manifest.json`, `state/cs_rag/lance/` 생성.
5. **미션 저장소 클론 + onboard** — 학습자가 지정한 mission repo를 `missions/` 아래로 clone, `repo-registry.json`에 등록.
6. **Learner State Assessment** — 학습자의 브랜치/PR/미해결 스레드를 직접 관찰해 `contexts/learner-state.json` 생성.
7. **coach-run 호출** — 이 모든 셋업이 끝난 뒤에야 첫 코칭 응답 생성.

각 단계는 한국어 한 줄로 학습자에게 진행 상황 보고 (예: *"CS 인덱스 빌드 중…"*). 실패 시 한국어로 원인 설명.

### CS Readiness 복구 규칙

- `coach-run.json.cs_readiness.state != "ready"` + `intent_decision.detected_intent == "cs_only"` → **AI는 1차 payload를 학습자에게 사용하지 말고** `bin/cs-index-build` 실행 후 coach-run 재호출, 2차 payload만 사용한다.
- `mission_only`면 인덱스 없이도 peer-only 응답 가능 (rebuild 생략).
- `mixed` / `drill_answer`는 AI 판단.

## Learning System v4-MVP (0.2.0)

Shared truth lives in `AGENTS.md` and `docs/learning-system-v4.md`. Claude sessions must follow the same v4 contract as Codex/Gemini:

- `coach-run.json` includes `learner_context`, `cognitive_trigger`, and `response_contract.cognitive_block`.
- Include `cognitive_block.markdown` when `applicability_hint != "omit"`.
- Do not also surface `follow_up_block` when `cognitive_block.trigger_type` is `self_assessment`, `review_drill`, or `follow_up`.
- If the learner answers a pending self-assessment prompt, run `bin/learn-self-assess --silent --trigger-session-id <id> "<response>"` automatically. Random scores without a pending trigger are ignored.
- Treat self-assessment as calibration only, not mastery.
- Review drills persist through `memory/drill-pending.json`; self-assessment pending state lives in `state/learner/pending_triggers.json`.
- Surface `cs_block.grounding_check.severity == "warn"` as a grounding caveat instead of overstating unverified CS source paths.

## Interactive Learning RAG Routing

대화형 CS 학습 질문(미션 PR 코칭 외, 학습자가 개념을 묻거나 학습 테스트를 풀다 막혔을 때)에는 `bin/rag-ask "$prompt"`를 호출해 Tier 0~3을 결정한다. 매 응답 첫 줄에 `[RAG: tier-N — <reason>]` 헤더 표기, Tier 1+이면 답변 끝에 출력의 `response_hints.citation_markdown`을 verbatim 복붙(스스로 `참고:` 작성 ❌). Tier 3이고 `blocked=false`면 `next_command` 별도 실행해 `bin/coach-run`으로 위임. 도구/빌드 질문(Tier 0)은 RAG 호출 없이 훈련 지식으로 답. 일반 dev 작업(학습 세션 외)에는 헤더 표기 안 함.

**Phase 9.4 citation contract**: `bin/rag-ask` 출력 최상위에 `response_hints.citation_markdown`이 항상 존재한다. tier 1+에서 hits가 있으면 paste-ready `참고:\n- <path>\n- <path>` 문자열로 채워짐 (최대 3개). AI 세션은 이 문자열을 verbatim 복사 — 손으로 path 작성 ❌. null이면 인용 출력 ❌. 회귀 테스트: `tests/unit/test_citation_contract.py`.

**Phase 9.3 tier downgrade contract**: R3가 cross-encoder top-1 점수가 `WOOWA_RAG_REFUSAL_THRESHOLD` 미만이면 sentinel hit을 emit하고, `bin/rag-ask`는 `decision.tier=0`으로 강제 + `response_hints.tier_downgrade="corpus_gap_no_confident_match"` + `response_hints.fallback_disclaimer`(한국어 한 줄)를 surface한다. AI 세션 행동:
1. 헤더: `[RAG: tier-0 — corpus_gap, 훈련지식 기반]`
2. 첫 줄: `fallback_disclaimer` verbatim
3. 본문: 훈련지식으로 답변
4. `참고:` 출력 ❌
5. 마지막 줄: "이 답은 일반 지식 기반이라 정확성이 corpus-grounded보다 낮을 수 있어. 출처 확인이 필요하면 알려줘."

활성화: `WOOWA_RAG_REFUSAL_THRESHOLD=<float>` 또는 `off` (default off). Calibration 스크립트: `scripts/learning/rag/r3/eval/calibrate_refusal_threshold.py`. 회귀 테스트: `test_r3_refusal_threshold.py`, `test_integration_tier_downgrade.py`, `test_rag_ask_forces_tier_0_on_downgrade.py`, `test_cohort_eval_silent_failure.py`.

**Phase 9.1 anaphora**: R3가 멀티턴 follow-up을 직접 처리한다.
- AI 세션이 `--reformulated-query`를 넘기면 prior turn 맥락이 이미 fold됐다고 보고 verbatim 사용 (정상 흐름).
- reformulation 없이 짧은 anaphora prompt ("그럼 IoC는?", "then?")가 들어오면 regex 매치 + `learner_context.recent_rag_ask_context`에서 직전 topic 최대 2개를 dense embed query에 fold (`이전 맥락: ...\n현재 질문: ...`).
- prior topic 없으면 raw prompt — false-positive 방지 ("그럼 안녕" 같은 짧은 인사는 regex 매치되어도 fold 없이 통과).

회귀 테스트: `tests/unit/test_r3_anaphora.py`.

**Phase 8 v3 migration fleet** (60-worker, ChatGPT Pro): 학습자/사용자가 *"migration_v3_60 시작해"* / *"v3 마이그레이션 시작"* 같은 의도를 표하면 `bin/migration-v3-60-start` 자동 호출. wrapper가 branch 격리(main 보전, 학습자 production 무중단) + preflight 회귀 + baseline cohort_eval + fleet-start 처리. 상세: `docs/migration-v3-runbook.md`.

**Phase 9.2 personalization-aware ranking** (wrapper default ON post-c12a0f5): R3가 fusion 후 rerank 전에 candidate score 조정.
- `mastered_concepts`의 concept_id 매칭 → -0.15 (이미 mastered된 개념 demote).
- `uncertain_concepts` / `underexplored_in_current_stage` 매칭 → +0.10 (약한 영역 boost).
- `concept:spring/bean` 접두사는 자동 strip → `spring/bean`으로 v3 frontmatter 매칭.
- Cycle3 (2026-05-07, c12a0f5) 이후 corpus concept_id 매핑률 99% 달성 → `bin/_rag_env.sh`가 `WOOWA_RAG_PERSONALIZATION_ENABLED=1`을 wrapper default로 export. 직접 호출(wrapper 우회)은 여전히 default off라 env 명시 필요.
- R3 hit / ranking은 top-level `concept_id`와 retriever metadata의 `document.concept_id`를 모두 읽는다. `concept:spring/bean` ↔ `spring/bean-di-basics`처럼 같은 category의 slug family는 같은 학습 concept family로 본다.
- `must_offer_next_action`은 현재 질문에서 추출된 concept과 추천 concept이 겹칠 때만 채워진다. 전역 `next_recommendation`이 있어도 무관한 질문에는 강제 제안하지 않는다.

회귀 테스트: `tests/unit/test_r3_personalization_ranking.py`.

상세: `docs/rag-runtime.md`. Latency 회피 위해 `export HF_HUB_OFFLINE=1` 권장.

### Query Reformulation (Pilot baseline 95.5%의 +5pp 책임)

학습자의 raw 자연어 prompt와 함께, AI 세션이 *corpus 친화적 표현으로 reformulate한 query*를 같이 넘기면 dense BGE-M3 + cross-encoder 매핑이 정확해진다. 200q × 6 cohort 측정에서 reformulation lever만으로 paraphrase 96 → 100%, symptom_to_cause 80 → 96.7%, OVERALL +5pp.

- `bin/rag-ask "$prompt" --reformulated-query "$ref"` 형식
- `$ref` 작성 규칙 + 적용/미적용 분기 + 이전 turn context fold-in: `docs/agent-query-reformulation-contract.md` (필수)
- 적용 안 하면 graceful degradation — Pilot baseline 95.5% → 90.5%
- raw prompt의 override/tool-only/coach 판단은 유지하되, domain/depth/definition 감지는 reformulated query도 함께 본다. 좋은 reformulation은 raw prompt가 모호해서 Tier 0으로 떨어지는 것을 구제할 수 있다.

요지: AI 세션이 `bin/rag-ask` 호출 직전에 학습자 자연어 ↔ corpus 어휘 통역 한 번 emit. 학습자에게 보이는 답변 톤은 raw prompt 기준 유지.

### Daemon Warm Service (cold 25s → warm 1.3s)

`bin/rag-ask`는 daemon 모드 default — wrapper가 `--via-daemon` 자동 추가. 첫 호출 시 daemon spawn해서 BGE-M3 + reranker를 메모리에 keep, 두 번째 호출부터 학습자 query latency 25s → 1.3s.

- AI 세션이 First-Run 끝에 `bin/rag-daemon start` 호출 권장 — 첫 질문도 warm
- 학습자가 외울 명령 = 0. wrapper가 daemon ensure
- 비활성: `WOOWA_RAG_NO_DAEMON=1 bin/rag-ask "..."`
- 상태/로그: `bin/rag-daemon status`, `state/rag-daemon.{json,log}`
- daemon state/health에는 startup `runtime_fingerprint`가 들어간다. wrapper ensure는 현재 checkout과 fingerprint가 다르면 자동 재시작해 merge 이후 stale daemon을 막는다.

### Production R3 env defaults

`bin/rag-ask` / `bin/coach-run` / `bin/cs-index-build` / `bin/cohort-eval` wrapper는 `bin/_rag_env.sh`를 source해서 6 env var를 default로 export — `WOOWA_RAG_R3_ENABLED=1`, `WOOWA_RAG_R3_RERANK_POLICY=always`, `WOOWA_RAG_R3_FORBIDDEN_FILTER=1`, `HF_HUB_OFFLINE=1`, `WOOWA_RAG_REFUSAL_THRESHOLD=off` (production-safe), `WOOWA_RAG_PERSONALIZATION_ENABLED=1` (post-c12a0f5). 닫혀 있으면 silent 후퇴 — wrapper 진입 시점에 강제. override는 calling shell의 `export`로.

### RAG performance closed loop (cycle3+)

성능 측정·개선·릴리스 cycle은 `docs/runbooks/rag-perf-loop.md` 표준화 9-step. 측정 wrapper는 `bin/cohort-eval --mode {production,eval}`. 학습자 정합 baseline은 **active 5-cohort 평균 92.7%** (cycle3 c12a0f5, M2 production). cycle1 91.5%는 측정 환경 미공개라 historical reference만, 직접 비교 ❌. 상세: `reports/rag_eval/cycle3_closing_report.md`.

## Adaptive Response (v3 closed loop)

`bin/rag-ask` 출력에 `learner_context`가 들어 있으면 (cold-start가 아닐 때) **무시하지 말고** 다음 규약을 따른다:

- `response_hints.must_skip_explanations_of` 안의 concept_id에 해당하는 기본 정의 반복 금지 (학습자가 이미 mastered).
- `response_hints.must_include_phrases`의 표현(예: "4번째 질문이야") 본문에 포함 — 시스템이 학습자를 기억하고 있다는 체감 신호.
- 헤더는 `[RAG: tier-N — <reason> · 적용: <header_required_tags 모두>]` 형식. `header_required_tags`가 비어 있으면 `· 적용:`을 만들지 않는다. 태그가 있으면 빠짐없이 surface한다.
- `response_hints.must_offer_next_action`이 있으면 답변 끝에 자연스럽게 surface (예: "다음 턴에 DI drill 한 번 풀어볼까?"). 비어 있으면 `next_recommendation`만 보고 unrelated drill을 제안하지 않는다.
- `focus_ranking` / `candidate_interpretation` / `response.evidence` 항목에 `freshness_note`가 채워져 있거나 candidate에 `cohort_caveat=true`가 있으면 본문에 자연어로 명시 — 이전 기수 PR이라는 사실과 미션 세부가 다를 수 있음을 학습자에게 알린다 (예: "2024년 기수 PR이지만 접근 방식 참고로..."). 누락하면 회귀 테스트 실패.

이 규약은 testable — `tests/unit/test_personalization_loop.py`가 `build_learner_context()`의 출력을 검증한다. `learner_context`가 null이면 v2.2 톤 그대로 진행하고, override 키워드가 들어오면 override가 우선.

## Code Attempt Recording

학습자가 미션 코드를 작성/수정하고 AI가 검토할 때, 다음 두 조건 중 하나가 만족되면 AI는 자동으로
`bin/learn-record-code --silent --file-path <path> --summary <one-line> --lines-added N --lines-removed M [--linked-test <Class.method>]`를 호출한다:

1. AI가 학습자의 미션 파일을 **실제로 수정/생성**한 경우 (Write/Edit tool 사용 후)
2. 학습자가 **명시적으로 파일 경로를 지목**해 검토를 요청한 경우 (예: "`Reservation.java` 어때?", "내 ReservationController 봐줘")

- "코드 어때?" 같은 모호한 요청 단독으로는 트리거하지 않음 — 파일 경로/라인 수가 불명확하면 기록하지 않는다
- linked-test: 같은 turn 또는 직전 turn에 `bin/learn-test` 결과를 봤다면 해당 `test_class.test_method`를 연계
- 학습자가 외울 명령 = 0 (AI 자동)
- `--silent` 플래그는 stdout을 억제하되 이벤트는 정상 기록한다 — 학습자에게 노이즈 없이 closed-loop 데이터가 쌓이도록

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
