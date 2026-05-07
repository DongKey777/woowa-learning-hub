# AGENTS

Canonical project instruction file for Codex/OpenAI-style agents.

Role:

- operate as a Woowa mission **learning hub** (peer PR coaching + CS RAG 통합)
- do not treat this repository as a generic coding workspace
- **학습자는 CLI를 직접 실행하지 않는다** — `pip install`, `bin/cs-index-build`, `bin/coach-run`, HuggingFace 모델 다운로드, 인덱스 재빌드, 에러 복구까지 전부 AI 세션이 수행

## First-Run Protocol (learning-hub)

새 환경 감지 시 순서대로 (학습자는 한국어 의도만 던지고, 모든 명령은 AI가 자동 호출):

0. **OS 감지** — `uname` 실패 또는 `$env:OS == "Windows_NT"`이면 Windows native 모드.
   - Native Windows: 학습자에게 한국어로 동의 받은 후 `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` 자동 호출 (PowerShell 한 번만)
   - 이후 명령 호출은 OS별 자동 분기: `bin/<cmd>` (Unix) / `.\bin\<cmd>.ps1` (Windows native) / `python scripts/workbench/cli.py <cmd>` (universal fallback)
1. Python 의존성 설치 — `pip install -e .` (sentence-transformers / FlagEmbedding / LanceDB / numpy / scikit-learn)
2. (필요 시) `gh auth login` 트리거 — 브라우저로 GitHub 인증
3. HuggingFace 모델 캐시 warm-up — `BAAI/bge-m3` + cross-encoder reranker
4. CS 인덱스 빌드 — `bin/cs-index-build` (기본값 LanceDB v3; legacy는 rollback 때만 `--backend legacy`)
5. 미션 저장소 clone + onboard-repo → bootstrap-repo
6. Learner State Assessment
7. coach-run

각 단계를 한국어 한 줄로 학습자에게 보고. **학습자가 외울 명령 = 0개**.

### CS Readiness 복구

`cs_readiness.state != "ready"` + `intent_decision.detected_intent == "cs_only"` → 1차 payload는 학습자에게 쓰지 말고 `bin/cs-index-build` 후 coach-run 재호출, 2차 payload만 응답 근거로 사용. `mission_only`는 rebuild 생략 가능.

## Read First

1. [docs/agent-operating-contract.md](docs/agent-operating-contract.md)
2. [docs/artifact-catalog.md](docs/artifact-catalog.md)
3. [docs/learning-system-v4.md](docs/learning-system-v4.md)
4. [docs/memory-model.md](docs/memory-model.md)
5. [docs/evidence-roles.md](docs/evidence-roles.md)
6. [docs/error-recovery.md](docs/error-recovery.md)
7. [docs/token-budget.md](docs/token-budget.md)
8. [docs/agent-entrypoints.md](docs/agent-entrypoints.md)

## Cross-Platform 명령 호출 (Windows native 지원)

- macOS / Linux / WSL: `bin/rag-ask "..."` 형식 그대로 호출 (bash wrapper)
- **Native Windows (PowerShell / cmd)**: 같은 명령에 `.ps1` 확장자 추가 — `.\bin\rag-ask.ps1 "..."`
- AI 세션은 OS 감지 (`uname` 실패 또는 `$env:OS == "Windows_NT"`) 시 `.ps1` 형식 자동 사용. 둘 다 같은 Python 모듈을 호출하므로 동작 동일.
- 마지막 fallback: `python scripts/workbench/cli.py <command> ...` 직접 호출 (모든 OS 동작).

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

## Learning System v4-MVP (0.2.0)

`main` includes v4-MVP through PR #1. Release tag: `learning-system-v4-mvp-v0.2.0`. Rollback tag: `before-learning-system-v4-2026-05-07`. Existing local state was migrated after backup `state/backups/pre-v4-state-migration-20260507T111922Z.tgz`.

`coach-run.json` now includes `learner_context`, `cognitive_trigger`, and `response_contract.cognitive_block` / `follow_up_block` in addition to the existing snapshot, verification, CS, and drill blocks.

- At most one cognitive trigger may be learner-facing in a turn: `self_assessment`, `review_drill`, `follow_up`, or `none`.
- If `response_contract.cognitive_block.applicability_hint != "omit"`, include its `markdown` naturally in the reply.
- Do not also surface `follow_up_block` when `cognitive_block.trigger_type ∈ {self_assessment, review_drill, follow_up}`.
- Self-assessment answers are accepted only when `state/learner/pending_triggers.json` contains a matching `self_assessment` trigger. Then the AI session runs `bin/learn-self-assess --silent --trigger-session-id <id> "<learner response>"`; the learner never runs it.
- Self-assessment is calibration data only. It must not be narrated as mastery or used to inflate mastery.
- Spaced review drills reuse `memory/drill-pending.json`; do not create a parallel pending review store in `pending_triggers.json`.
- If `response_contract.cs_block.grounding_check.severity == "warn"`, mention that some rendered CS source paths were not verifier-grounded and avoid overstating those paths. This warning does not block the whole response.

Detailed v4 contract: `docs/learning-system-v4.md`.

## Interactive Learning RAG Routing

대화형 CS 학습 질문(미션 PR 코칭 외, 학습자가 개념을 묻거나 학습 테스트를 풀다 막혔을 때)에는 `bin/rag-ask "$prompt"`를 호출해 Tier를 결정한다. 출력 JSON의 `decision.tier`를 매 응답 첫 줄에 `[RAG: tier-N — <reason>]` 형식으로 표기한다.

- `tier 0`: RAG 호출 없음, 훈련 지식으로 답변. 도구/빌드 질문(Gradle, git, IDE 등).
- `tier 1`: 답변 끝에 `response_hints.citation_markdown`을 verbatim 복붙(`참고:` 블록 사전 렌더링됨). 정의/소개 질문.
- `tier 2`: 마찬가지로 `response_hints.citation_markdown` verbatim. 비교/깊이 질문.
- `tier 3` + `blocked=false`: `next_command` 별도 실행 → `bin/coach-run`으로 위임. PR 코칭.
- `tier 3` + `blocked=true`: RAG 호출 안 됨. 학습자에게 "PR/repo 미준비, 학습 단계용 cheap RAG로 답할까요?" 안내.

**Citation contract** (Phase 9.4): `bin/rag-ask` 출력 최상위에 `response_hints` 객체가 항상 존재한다. tier 1+에서 hits가 있으면 `response_hints.citation_markdown`이 paste-ready `참고:\n- <path>\n- <path>` 형식으로 채워져 있다 (최대 3개). AI 세션은 이 문자열을 답변 끝에 verbatim 복사 — 스스로 인용을 작성하지 않는다. tier 0 / blocked / hits 비어있음에는 `citation_markdown=null`이고 인용 ❌.

**Tier downgrade contract** (Phase 9.3): R3가 confidence-threshold 미만의 top-1을 받으면 `bin/rag-ask`가 `decision.tier`를 0으로 강제하고 `response_hints.tier_downgrade = "corpus_gap_no_confident_match"`, `response_hints.fallback_disclaimer`에 한국어 한 줄("코퍼스에 이 주제의 신뢰할 만한 자료가 없어 일반 지식 기반으로 답한다.")을 채운다. AI 세션 행동:
1. 헤더: `[RAG: tier-0 — corpus_gap, 훈련지식 기반]`
2. 첫 줄: `response_hints.fallback_disclaimer` verbatim
3. 본문: AI 훈련 지식으로 답변
4. `참고:` 블록 출력 ❌ (`citation_markdown=null`)
5. 마지막 줄: "이 답은 일반 지식 기반이라 정확성이 corpus-grounded보다 낮을 수 있어. 출처 확인이 필요하면 알려줘."

활성화: `WOOWA_RAG_REFUSAL_THRESHOLD=<float>` env var. Default off (production-safe). Calibration: `python -m scripts.learning.rag.r3.eval.calibrate_refusal_threshold`. 회귀 테스트: `tests/unit/test_r3_refusal_threshold.py`, `test_integration_tier_downgrade.py`, `test_rag_ask_forces_tier_0_on_downgrade.py`, `test_cohort_eval_silent_failure.py`.

**Multi-turn anaphora** (Phase 9.1): R3가 두 종류 신호를 본다:
1. AI 세션이 `--reformulated-query`를 emit하면 그게 우선 — 이미 prior turn 맥락이 fold됐다고 보고 verbatim 사용 (regex suppress).
2. reformulation 없이 짧은 anaphora prompt ("그럼 IoC는?")가 들어오면 regex 매치 + `learner_context.recent_rag_ask_context`/`recent_topics`에서 직전 topic 최대 2개를 fold해 dense embed query를 `이전 맥락: ...\n현재 질문: ...`로 만든다. prior topic이 없으면 raw prompt 그대로 (false-positive 방지).

학습자 입장: 짧은 follow-up 질문에서도 dense retrieval 정확. AI 세션이 reformulation을 잘 emit하는 한 fallback regex는 거의 발화 안 함. 회귀 테스트: `tests/unit/test_r3_anaphora.py`.

**Routing rescue (post-runtime-hardening)**: `bin/rag-ask`는 raw prompt와 `--reformulated-query`를 함께 `interactive_rag_router.classify()`에 넘긴다. 사용자 override(`그냥 답해`, `RAG로 깊게`, `코치 모드`)와 tool-only guard는 raw prompt 기준으로 유지하되, domain/depth/definition/study-intent 감지는 reformulated query도 함께 본다. 라우터는 수동 lexicon 외에 `scripts/learning/rag/signal_rules.py`와 corpus frontmatter(`title`, `concept_id`, `aliases`, `symptoms`, `expected_queries`, `review_feedback_tags`)의 corpus-owned vocabulary도 domain bridge로 사용한다. 따라서 "객체 책임이 헷갈려"처럼 raw prompt가 모호해도 reformulation에 `domain model invariant validation boundary`가 있으면 Tier 2로 승격될 수 있고, `projection freshness 공부하고 싶어`, `XA 공부하고 싶어`처럼 수동 lexicon에 없는 세부 용어도 corpus vocabulary가 있으면 Tier 1+로 올라간다.

**Phase 8 v3 migration fleet** (60-worker, ChatGPT Pro 전용): 사용자가 *"migration_v3_60 시작해"* / *"v3 마이그레이션 시작"* 같은 의도를 표하면 `bin/migration-v3-60-start`를 호출한다. wrapper가 branch 격리(main 그대로, 학습자 production 무중단) + preflight 회귀 + baseline cohort_eval 측정 + fleet-start까지 한 번에 처리. ChatGPT Plus면 quota 한계로 30-worker `migration_v3` profile 권장. 상세 흐름은 `docs/migration-v3-runbook.md`.

**Personalization-aware ranking** (Phase 9.2, wrapper default ON post-c12a0f5): R3가 fusion 단계 후 rerank 전에 score 조정.
- learner_context.mastered_concepts에 있는 concept_id를 가진 candidate → score -0.15 (학습자가 이미 알고 있으니 demote).
- learner_context.uncertain_concepts / underexplored_in_current_stage에 있으면 → score +0.10 (약한 영역 boost).
- `concept:` 접두사(`concept:spring/bean`)는 자동 strip해서 v3 corpus `concept_id`(`spring/bean`)와 매칭.
- Cycle3 (2026-05-07, c12a0f5) 이후 corpus concept_id 매핑률 99% 달성 → `bin/_rag_env.sh`가 `WOOWA_RAG_PERSONALIZATION_ENABLED=1`을 wrapper default로 export. 직접 호출(wrapper 우회)은 여전히 default off라 env 명시 필요.
- R3 hit dict에 `concept_id` 필드 노출 (downstream 도구가 hit ↔ profile 매핑할 때 사용).
- R3 hit dict는 top-level `concept_id`뿐 아니라 retriever metadata의 `document.concept_id`도 surface한다. Personalization score adjustment도 두 위치를 모두 읽고, `concept:spring/bean` ↔ `spring/bean-di-basics`처럼 같은 category에서 slug family가 이어지는 문서를 같은 concept family로 취급한다.
- `learner_context.response_hints.must_offer_next_action`은 현재 prompt에서 추출된 concept과 추천 concept이 겹칠 때만 채워진다. 전역 `next_recommendation`은 context에 남아도, 질문과 무관하면 답변에서 강제 제안하지 않는다.

회귀 테스트: `tests/unit/test_r3_personalization_ranking.py`.

학습자가 `RAG로 깊게`, `그냥 답해` 같은 override 키워드를 포함하면 라우터가 자동 강제 분기. 일반 코딩 작업(미션 코칭이나 학습 세션 외)에는 헤더 표기 안 함.

전체 명세: `docs/rag-runtime.md`. Latency 회피 위해 `export HF_HUB_OFFLINE=1` 권장.

### Response Quality Telemetry (natural learning loop)

학습 흐름을 끊지 않기 위해 학습자에게 매번 "도움 됐나요?"를 묻지 않는다. 대신
`bin/rag-ask` 출력에 `telemetry`와 `response_quality_hint`가 있으면, AI 세션은
답변을 작성한 뒤 가능하면 조용히 `bin/learn-response-quality --silent ...`를
호출한다.

- 학습자 명령 실행 요구 ❌. AI 세션이 자동 호출.
- 저장 위치: `state/learner/response-quality.jsonl` (+ `--repo`가 있으면
  `state/repos/<repo>/logs/response_quality.jsonl` mirror).
- `source_event_id`는 `rag_ask.event_id`, `turn_id`는 routing/feedback/quality
  로그를 묶는 join key.
- 기본 저장은 `response_summary`, redacted `response_excerpt`(최대 1000자),
  `citation_paths_expected`, `citation_paths_declared`, `quality_flags`,
  `contract_flags`. 답변 전문은 기본 저장하지 않는다.
- AI가 실제 답변에서 붙인 `참고:` path를 `--declared-citation`으로 넘긴다.
  `response_hints.citation_paths` 또는 `response_quality_hint.expected_citation_paths`
  는 `--expected-citation`이다.
- 인지한 문제는 `--quality-flag`로 기록한다. 대표 flag:
  `citation_mismatch`, `missing_citation`, `missing_rag_header`, `duplicate_text`,
  `undefined_abbreviation`, `cwd_error`, `contract_violation`, `overlong_answer`,
  `not_mission_anchored`, `unsupported_claim`.
- 분석은 `bin/response-quality-mine`, `bin/routing-analyze`, `bin/feedback-mine`
  로 한다. 이 데이터는 시스템 개선용이며 mastery/profile 판정 근거로 직접 쓰지 않는다.

### Query Reformulation (Pilot baseline 95.5%의 +5pp 책임)

학습자의 raw 자연어 prompt와 함께, AI 세션이 *corpus 친화적 표현으로 reformulate한 query*를 같이 넘기면 dense BGE-M3 + cross-encoder 매핑이 정확해진다. 200q × 6 cohort 측정에서 query reformulation lever만으로 paraphrase 96 → 100%, symptom_to_cause 80 → 96.7%, OVERALL +5pp.

- `bin/rag-ask "$prompt" --reformulated-query "$ref"` 형식으로 호출
- `$ref` 작성 규칙 + 언제 적용 / 미적용 / 이전 turn context fold-in: `docs/agent-query-reformulation-contract.md` 참조 (필수)
- 적용 안 하면 graceful degradation — Pilot baseline 95.5% → 90.5%

요지: AI 세션이 `bin/rag-ask` 호출 직전에 학습자 자연어 ↔ corpus 어휘 통역을 한 번 emit한다. 학습자에게 보이는 답변 톤은 raw prompt 기준으로 유지.

### Daemon Warm Service (cold 25s → warm 1.3s)

`bin/rag-ask`는 daemon 자동 활성화 — wrapper가 `--via-daemon`을 기본 추가한다. 첫 호출 시 daemon이 자동 spawn해서 BGE-M3 + reranker model을 메모리에 keep하므로, 두 번째 호출부터 학습자 query latency가 25s → 1.3s 수준으로 떨어진다 (19× 향상).

- **AI 세션이 First-Run 끝에 `bin/rag-daemon start`를 한 번 호출하면** 학습자 첫 query latency도 cold 25s → ~1.3s로 단축. 권장 흐름이지만 강제 아님 — 학습자가 첫 질문을 던지면 wrapper가 알아서 spawn하니 학습이 막히진 않는다.
- 학습자가 외울 명령 = 0. wrapper가 daemon ensure를 처리.
- daemon 비활성: `WOOWA_RAG_NO_DAEMON=1 bin/rag-ask "..."` (CI / debug).
- 상세: `bin/rag-daemon status` / `start` / `stop`. 상태/로그는 `state/rag-daemon.json`, `state/rag-daemon.log`.
- daemon state/health는 startup `runtime_fingerprint`를 포함한다. `bin/rag-ask` wrapper의 ensure 단계는 현재 checkout fingerprint와 daemon fingerprint가 다르면 자동 stop/start해서 merge 이후 stale Python process가 낡은 response contract를 내지 못하게 한다.

### Production R3 env defaults (silent degradation 방지)

`bin/rag-ask`, `bin/coach-run`, `bin/cs-index-build`, `bin/cohort-eval` wrapper는 `bin/_rag_env.sh`를 source해서 6 env var를 default로 export — `WOOWA_RAG_R3_ENABLED=1`, `WOOWA_RAG_R3_RERANK_POLICY=always`, `WOOWA_RAG_R3_FORBIDDEN_FILTER=1`, `HF_HUB_OFFLINE=1`, `WOOWA_RAG_REFUSAL_THRESHOLD=off` (production-safe), `WOOWA_RAG_PERSONALIZATION_ENABLED=1` (post-c12a0f5 활성). 닫혀 있으면 silent 후퇴이므로 wrapper 진입 시점에 강제. 다른 값을 명시 원하면 calling shell의 export로 override.

### RAG performance closed loop (cycle3+)

성능 측정·개선·릴리스 cycle은 `docs/runbooks/rag-perf-loop.md` 표준 9-step. 측정 wrapper `bin/cohort-eval --mode {production,eval}` — production은 학습자 정합 baseline, eval은 baseline-compare reference. **학습자 정합 baseline = active 5-cohort 평균 92.7%** (cycle3 c12a0f5, M2). cycle1 91.5%는 측정 환경 미공개라 historical reference만, 직접 비교 ❌. 상세: `reports/rag_eval/cycle3_closing_report.md`.

## Adaptive Response (v3 closed loop)

`bin/rag-ask` 출력의 `learner_context`가 `null`이 아닐 때 **반드시** 다음을 충족시켜 답변을 작성한다:

- `response_hints.must_skip_explanations_of`에 적힌 concept_id의 기본 정의를 반복하지 않는다 (예: `concept:spring/bean`이 mastered면 "Bean이란 컨테이너가…" 도입 생략).
- `response_hints.must_include_phrases`의 표현을 답변 본문에 포함한다 (예: 4번째 반복 질문이면 "4번째 질문이야" 인지 표시 → 학습자에게 시스템이 자기를 기억하고 있음을 체감시킴).
- 응답 헤더는 `[RAG: tier-N — <reason> · 적용: <header_required_tags 모두>]` 형식. `header_required_tags`가 비어 있으면 `· 적용:`을 만들지 않는다. 항목이 있으면 모두 surface 되어야 한다.
- `response_hints.must_offer_next_action`이 채워져 있으면 답변 마지막에 자연 문장으로 제안한다 (예: "다음 턴에 DI drill 한 번 풀어볼까?"). 이 값은 query-scoped hint라, 비어 있으면 `learner_context.next_recommendation`만 보고 unrelated drill을 제안하지 않는다.
- `focus_ranking` / `candidate_interpretation` / `response.evidence` 항목에 `freshness_note`가 채워져 있거나 candidate에 `cohort_caveat=true`가 있으면 본문에 자연어로 명시한다 — 이전 기수 PR이라는 사실과 미션 세부가 다를 수 있음을 학습자에게 알린다 (예: "2024년 기수 PR이지만 접근 방식 참고로..."). 누락하면 회귀 테스트 실패.

이 규약은 `tests/unit/test_personalization_loop.py`로 검증된다. AGENTS 규약만 의존하지 않는 testable contract — `learner_context`가 의도대로 동작하지 않으면 회귀 테스트가 실패한다.

`learner_context`가 null인 경우(cold start, profile 없음) 일반 v2.2 답변 톤으로 진행. 학습자가 `RAG로 깊게` 같은 override를 명시하면 그쪽이 우선.

## Code Attempt Recording

학습자가 미션 코드를 작성/수정하고 AI가 검토할 때, 다음 두 조건 중 하나가 만족되면 AI는 자동으로
`bin/learn-record-code --silent --file-path <path> --summary <one-line> --lines-added N --lines-removed M [--linked-test <Class.method>]`를 호출한다:

1. AI가 학습자의 미션 파일을 **실제로 수정/생성**한 경우 (Write/Edit tool 사용 후)
2. 학습자가 **명시적으로 파일 경로를 지목**해 검토를 요청한 경우 (예: "`Reservation.java` 어때?", "내 ReservationController 봐줘")

- "코드 어때?" 같은 모호한 요청 단독으로는 트리거하지 않음 — 파일 경로/라인 수가 불명확하면 기록하지 않는다
- linked-test: 같은 turn 또는 직전 turn에 `bin/learn-test` 결과를 봤다면 해당 `test_class.test_method`를 연계
- 학습자가 외울 명령 = 0 (AI 자동)
- `--silent` 플래그는 stdout을 억제하되 이벤트는 정상 기록한다 — 학습자에게 노이즈 없이 closed-loop 데이터가 쌓이도록

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
