# woowa-learning-hub

우아한테크코스 미션 학습과 CS 이론 학습을 하나의 한국어 대화 세션으로 묶어주는 AI 코칭 워크벤치입니다. `woowa-mission-coach`의 peer PR 코칭 파이프라인 위에 CS RAG(하이브리드 검색 + 4차원 채점 + drill 루프) 서브시스템을 얹은 상위 버전입니다.

AI 세션(Claude Code / Gemini / Codex 등)이 이 저장소를 백엔드로 사용해 다른 크루의 PR과 리뷰를 분석하고, 학습자의 질문에 관련된 peer 사례와 학습 포인트를 정리합니다. 학습자는 AI와 한국어로 대화하는 형태로 코칭을 받게 됩니다.

---

## 무엇을 하는가

- 학습자의 현재 저장소 상태(브랜치, 열린 PR, 미해결 리뷰 thread)를 매 세션 시작 시 직접 관찰합니다.
- 미션 저장소를 분석하고 upstream의 다른 크루 PR을 수집합니다.
- 현재 질문과 같은 단계에 있는 peer PR을 고르고, 멘토 리뷰 맥락을 근거로 학습 포인트를 추출합니다.
- 세션이 이어지면 학습 이력을 누적해 어떤 주제를 더 볼지 / 아직 다루지 않았는지를 함께 고려합니다.

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

- Python 3.10 이상. 코치 파이프라인은 표준 라이브러리만으로 동작하고, CS RAG 서브시스템은 `sentence-transformers`, `numpy`, `scikit-learn`을 추가로 사용합니다 (lazy import — 미설치 시 peer-only 경로로 degrade). 설치는 `pip install -e .`로 AI 세션이 First-Run Protocol에서 수행합니다.
- `gh` CLI, 로그인된 상태 (`gh auth login`)
- `git`
- AI CLI 중 하나: Claude Code, Gemini, Codex
- macOS 또는 Linux 셸

---

## 설치

```bash
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
```

초기 디렉터리 생성, 환경 점검, 미션 등록, 데이터 수집은 첫 세션에서 AI가 순차적으로 수행합니다.

---

## 시작하기

### 1. 저장소 루트에서 AI 세션을 연다

```bash
cd woowa-learning-hub
claude   # 또는 gemini, codex
```

AI는 시작 파일(`CLAUDE.md` / `GEMINI.md` / `AGENTS.md`)을 읽고 이 저장소를 Woowa 미션 코치로 사용하도록 설정됩니다.

### 2. 첫 요청을 한국어로 전달한다

예:

> "내 미션 저장소를 코칭해줘. 저장소는 `https://github.com/내계정/java-janggi`이고, upstream은 `woowacourse/java-janggi`, 지금은 사이클2를 진행 중이야."

이 요청을 받으면 AI는 다음 단계를 순서대로 진행합니다.

1. 기본 디렉터리와 상태 파일 생성 (최초 실행인 경우)
2. Python / `gh` 인증 / 디렉터리 상태 점검
3. 미션 저장소를 `missions/` 아래에 클론 (필요한 경우)
4. 저장소를 내부 registry에 등록
5. upstream에서 PR, 리뷰, 코멘트 수집 — 저장소 크기에 따라 수 분 소요
6. 첫 코칭 세션 시작

### 3. 이후 질문

예:

> "이 PR 기준으로 지금 무엇을 먼저 보면 좋을까?"
>
> "다른 크루들은 Repository 경계를 어떻게 잡았어?"
>
> "최근에 반복해서 놓치고 있는 학습 포인트가 있어?"

AI는 수집된 peer PR과 멘토 리뷰를 근거로 답합니다.

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
bin/                 # 명령어 래퍼 (AI가 호출)
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

---

## 기여 / 피드백

개선 제안, 버그 리포트, 실제 코칭 세션에서의 사용 후기는 이슈로 남겨주시면 참고하겠습니다. 아직 초기 단계라 미흡한 부분이 많습니다.
