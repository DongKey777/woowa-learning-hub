# woowa-learning-hub

우아한테크코스 미션 학습과 CS 이론 학습을 하나의 한국어 대화 세션으로 묶어주는 AI 코칭 워크벤치입니다. `woowa-mission-coach`의 peer PR 코칭 파이프라인 위에 CS RAG(하이브리드 검색 + 4차원 채점 + drill 루프) 서브시스템을 얹은 상위 버전입니다.

AI 세션(Claude Code / Gemini / Codex 등)이 이 저장소를 백엔드로 사용해 다른 크루의 PR과 리뷰를 분석하고, 학습자의 질문에 관련된 peer 사례와 학습 포인트를 정리합니다. 학습자는 AI와 한국어로 대화하는 형태로 코칭을 받게 됩니다.

---

## 1분 안에 시작

> **학습자가 외울 명령 = 0개. 외울 한국어 prompt = 1개.**
>
> 1. 저장소 루트에서 AI 세션 한 번 열기 (`claude` / `codex` / `gemini` 중 하나)
> 2. 한국어로 의도 한 줄: *"이 저장소로 학습 시작하자. spring-core-1부터 가고 싶어."*
> 3. AI가 자동 처리: `pip install -e .` → HuggingFace 모델 warm-up → CS 인덱스 빌드
>    → 미션 저장소 클론 → 첫 학습 가이드 제공
> 4. 학습자는 그저 답변 따라 한국어로 학습 진행
>
> AI 세션이 시작 파일(`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`)의 First-Run Protocol을
> 따라 순서대로 셋업한다. 학습자가 직접 `bin/...` 명령을 외울 일은 없다.

---

## 무엇을 하는가

- 학습자의 현재 저장소 상태(브랜치, 열린 PR, 미해결 리뷰 thread)를 매 세션 시작 시 직접 관찰합니다.
- 미션 저장소를 분석하고 upstream의 다른 크루 PR을 수집합니다.
- 현재 질문과 같은 단계에 있는 peer PR을 고르고, 멘토 리뷰 맥락을 근거로 학습 포인트를 추출합니다.
- 학습 이벤트(질문, 학습 테스트 결과, drill 답변, 코드 수정)를 모두 단일 stream으로 누적해 어떤 개념이 정착됐는지 / 아직 헷갈리는지를 자동 추적합니다.
- 동일 개념을 반복 질문하면 다음 답변이 자동으로 깊어지고, 정착된 개념은 기본 정의를 생략합니다 (closed-loop personalization).

---

## 학습자의 현재 코드를 본다

AI가 리뷰 코멘트만 읽고 "이미 고친 부분을 다시 지적"하거나 "네 브랜치에 없는 파일을 있는 것처럼 설명"하는 일을 막기 위해, 매 세션 시작 시 학습자의 저장소를 직접 훑어봅니다. 현재 브랜치, 작업 중인 PR, 아직 반영되지 않은 리뷰 지적이 어떤 파일에 있는지를 스냅샷으로 남기고, 코드가 수정되면 다음 질문 때 자동으로 다시 읽습니다.

즉 "이거 반영했는데 네가 아직 예전 코드 보고 답하네" 같은 상황이 발생하지 않고, 학습자는 "상태 업데이트해줘" 같은 명령을 할 필요 없이 코드만 계속 쓰면 됩니다. 내부 동작이 궁금하다면 [`docs/artifact-catalog.md`](docs/artifact-catalog.md)의 `contexts/learner-state.json` 절을 보세요.

---

## 응답 형식을 파이프라인이 미리 그려준다

매 턴 맨 앞에 붙는 `## 상태 요약` 블록(반영된 리뷰 / 아직 남은 리뷰 / 이모지·텍스트 답변 분포)과, `git show`로 직접 확인이 필요한 스레드 목록을 AI가 추측하지 않습니다. 파이프라인이 `contexts/learner-state.json`에서 집계해 `actions/coach-run.json`의 `response_contract` 필드에 미리 렌더해두고, AI는 그 markdown을 그대로 복사해 붙입니다.

이 덕분에 "AI가 카운트를 머릿속으로 세다가 버킷 하나를 누락"하거나 "이모지 응답을 텍스트 답글로 합쳐서 보고"하는 식의 불일치가 눈에 띄게 줄어듭니다. 다만 AI가 이 필드를 실제로 복사해 사용했는지까지 사후에 강제하지는 않습니다 — 파이프라인이 미리 그려서 AI가 추측할 여지를 없애는 *pre-rendered assistance* 수준이고, 응답 자체를 거부하는 hard enforcement는 별도의 후크 계층 몫입니다. 규칙과 필드 구조는 [`docs/agent-operating-contract.md`](docs/agent-operating-contract.md)의 Response Contract 절과 [`docs/artifact-catalog.md`](docs/artifact-catalog.md)의 `response_contract` 항목에서 볼 수 있습니다.

---

## 필요한 것

- **Python 3.10 이상** — 의존성(`sentence-transformers`, `numpy`, `scikit-learn`) 설치는 첫 AI 세션에서 자동 수행
- **`gh` CLI**, 로그인된 상태 (`gh auth login`)
- **`git`**
- **AI CLI 중 하나**: Claude Code, Gemini, Codex
- macOS 또는 Linux 셸

학습자가 직접 의존성 설치 / 모델 warm-up / 인덱스 빌드를 하지 않습니다. 첫 세션의 한국어 의도 한 줄로 AI가 모두 처리.

---

## 설치

```bash
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
```

초기 디렉터리 생성, 환경 점검, 미션 등록, 데이터 수집은 첫 세션에서 AI가 순차적으로 수행합니다.

---

## 시작하기

저장소 루트에서 AI 세션 (`claude` / `codex` / `gemini`)을 열고 한국어 의도를 던집니다. **명령은 모두 AI가 자동 호출** — 학습자는 한국어로 말하기만 하면 됩니다.

### 흐름 1: 학습 테스트 (개념 → 코드 → 검증)

> 학습자: *"spring-core-1 모듈로 Spring 학습 시작하자."*

AI가 자동 호출: `bin/cs-index-build` (필요 시) → `missions/spring-learning-test` 클론 → 모듈 README 읽고 첫 도전 과제 안내. 학습자가 코드를 짜면 AI가 `bin/learn-test --module spring-core-1`로 결과를 자동 기록 (pass/fail이 학습자 프로필에 누적).

### 흐름 2: 개념 학습 (한국어 질문)

> 학습자: *"`@Autowired`가 뭐야?"*

AI 자동: `bin/rag-ask "@Autowired가 뭐야?" --module spring-core-1` → Tier 0~3 자동 분류 (도구 질문이면 RAG 미사용 / 정의 질문이면 cheap RAG / 비교·깊이 질문이면 full RAG / PR 코칭이면 coach-run으로 위임). 답변 + 학습자 history 자동 누적.

같은 개념을 7일 내 3번 이상 물으면 다음 답변이 자동으로 깊어지고 "n번째 질문이야" 인지 표시가 붙습니다 (closed-loop).

### 흐름 3: Drill (이해도 객관 검증)

> 학습자: *"DI drill 풀어볼래."*

AI 자동: `bin/learn-drill offer --concept concept:spring/di` → 4문장 답변 요구 질문 발행. 학습자가 답하면 `bin/learn-drill answer "..."`로 4차원(정확도/깊이/실전성/완결성) 채점. 8점 이상 ×2 + 테스트 통과 + PR 부정 피드백 없음 → 그 개념이 mastered로 승격.

### 흐름 4: PR 코칭 (peer 리뷰 기반)

> 학습자: *"내 미션 저장소를 코칭해줘. https://github.com/내계정/java-janggi, upstream은 woowacourse/java-janggi."*

AI 자동: 미션 저장소 클론 → upstream PR/리뷰 수집 (수 분 소요) → 학습자 브랜치 직접 관찰 (`contexts/learner-state.json`) → `bin/coach-run`로 답변 생성. peer PR 근거 + 멘토 리뷰 맥락 + 학습자 cross-mission 프로필 합쳐서 답.

### 학습자 프로필 보기

> 학습자: *"내가 지금까지 뭘 학습했어?"* / *"다음에 뭐 하면 좋을까?"*

AI 자동: `bin/learner-profile show` / `bin/learner-profile suggest --format text` → 누적된 28+ 이벤트 기반 mastered / uncertain / underexplored 분석 + 다음 동선 추천 (drill / 다음 모듈 / 미접촉 개념).

---

## 환경 점검 / 복구

환경이 깨졌거나 상태를 직접 확인하고 싶을 때만 실행 (학습 흐름엔 불필요):

```bash
bin/doctor                          # Python / gh 인증 / 디렉터리 상태 점검
bin/cs-index-build                  # CS 인덱스 강제 재빌드 (corpus 변경 시)
bin/learner-profile clear --yes     # 학습 데이터 전체 초기화 (privacy reset)
bin/learner-profile redact "..."    # 특정 문자열 포함 이벤트 제거
HF_HUB_OFFLINE=1 bin/rag-ask "..."  # HF Hub 네트워크 차단 (cold latency 절약)
```

`state/learner/`와 `state/repos/`, `missions/`는 모두 `.gitignore`에 포함되어 절대 커밋되지 않습니다. 학습 데이터는 노트북에만 존재.

---

## 모델 선택

이 시스템은 `coach-run.json`에 PR 근거와 학습 포인트를 미리 정리해 AI에 전달합니다. 따라서 AI의 주된 작업은 근거 해석과 한국어 설명이며, 각 AI 계열의 mid-tier 모델로도 코칭 목적에는 일반적으로 충분합니다. 플래그십 모델은 월 구독 쿼터를 더 빠르게 소진하는 경향이 있습니다.

AI가 첫 응답에서 현재 실행 중인 모델을 확인하고, 플래그십으로 실행되어 있다면 mid-tier 모델로의 재시작을 안내합니다.

### 구독제별 모델 (2026-04 기준)

| 구독 | Mid-tier (권장) | 플래그십 |
|---|---|---|
| Claude Pro ($20/월) | Sonnet 4.6 | Opus 4.6 |
| ChatGPT Plus ($20/월) | GPT-5.3-Codex | GPT-5.4 |
| Google AI Pro ($20/월) | Gemini 2.5 Pro | Gemini 3.1 Pro |

각 AI별 근거와 대체 옵션은 시작 파일(`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`)의 *Recommended Model* 섹션에 있습니다.

---

## AI별 시작 파일

AI가 저장소 루트에서 실행되면 해당 파일을 자동으로 읽습니다.

| AI | 시작 파일 | 스킬 / 에이전트 |
|---|---|---|
| Claude Code | [`CLAUDE.md`](CLAUDE.md) | [`.claude/agents/`](.claude/agents/), [`.claude/commands/`](.claude/commands/) |
| Codex (OpenAI) | [`AGENTS.md`](AGENTS.md) | [`skills/`](skills/) |
| Gemini | [`GEMINI.md`](GEMINI.md) | [`gemini-skills/`](gemini-skills/) |

---

## 저장소 구조

```
bin/                 # 명령어 래퍼 — AI가 호출 (학습자가 직접 실행 X)
  rag-ask                # 개념 질문 → Tier 0~3 라우팅 + RAG 답변
  coach-run              # PR 코칭 (peer 분석 + 멘토 맥락)
  learn-test             # JUnit XML 결과 → test_result event 자동 기록
  learn-drill            # 4차원 채점 drill 워크플로 (offer / answer / status / cancel)
  learn-record-code      # AI가 코드 수정 도움 시 code_attempt event 기록
  learner-profile        # 학습자 프로필 (show / suggest / clear / redact / set)
  cs-index-build         # CS RAG 인덱스 빌드 (첫 실행 자동, 수동 강제 가능)
  doctor                 # 환경 점검 (Python / gh / 디렉터리)
  ...                    # PR 코칭 보조 명령들 (topic / reviewer / compare / my-pr 등)
scripts/workbench/   # 파이프라인 엔진
schemas/             # JSON 스키마
docs/                # 운영 문서
.claude/, gemini-skills/, skills/   # AI별 에이전트/스킬 정의
missions/            # 학습자가 클론한 미션 저장소 (gitignored)
state/               # 런타임 상태: archive, packets, memory (gitignored)
```

---

## 지속 오케스트레이션

CS 코퍼스 확장 같은 장기 작업은 `bin/orchestrator`로 지속 오케스트레이션할 수 있습니다.

```bash
bin/orchestrator start
bin/orchestrator status
bin/orchestrator claim --worker database-worker --limit 2
bin/orchestrator complete --worker database-worker --item-id database-00001 --summary "failover 문서 2개 추가"
bin/orchestrator fleet-start
bin/orchestrator fleet-status
```

이 오케스트레이터는 직접 LLM을 호출하지는 않고, `state/orchestrator/` 아래에 backlog, 현재 wave, worker lease, 완료 이력을 유지합니다. 즉 세션이 바뀌어도 “다음에 무엇을 할지”와 “누가 무엇을 잡고 있는지”를 계속 이어갈 수 있습니다. 자세한 구조는 [`docs/orchestrator.md`](docs/orchestrator.md)에 정리했습니다.

---

## 더 읽을거리

- [`docs/architecture.md`](docs/architecture.md) — 파이프라인 구조
- [`docs/capability-map.md`](docs/capability-map.md) — 내부 capability
- [`docs/artifact-catalog.md`](docs/artifact-catalog.md) — 생성되는 artifact
- [`docs/agent-operating-contract.md`](docs/agent-operating-contract.md) — AI 운영 계약
- [`docs/orchestrator.md`](docs/orchestrator.md) — 지속 오케스트레이터
- [`docs/onboarding.md`](docs/onboarding.md) — 새 미션 온보딩 가이드
- [`docs/learner-memory.md`](docs/learner-memory.md) — 학습자 단일 source of truth (state/learner) + adaptive response loop
- [`docs/rag-runtime.md`](docs/rag-runtime.md) — `bin/rag-ask` Tier 분류 + RAG 런타임 운영

---

## 기여 / 피드백

개선 제안, 버그 리포트, 실제 코칭 세션에서의 사용 후기는 이슈로 남겨주시면 참고하겠습니다. 아직 초기 단계라 미흡한 부분이 많습니다.
