# woowa-learning-hub

우아한테크코스 미션 학습 + CS 이론 학습을 한국어 대화 한 곳에서 처리하는 AI 코칭 워크벤치.
**학습자가 외울 명령은 0개**, 외울 prompt는 1개. AI 세션이 의존성 설치, CS RAG 인덱스 빌드,
미션 저장소 클론, peer PR 수집, drill 채점까지 자동 처리하고, 학습자는 한국어로 의도만 던진다.

---

## 무엇을 하는가

이 시스템은 **네 가지 학습 입력을 한 곳에 모아** 개인화된 코칭으로 변환한다.

1. **다른 크루들의 PR + 리뷰** (peer 학습 데이터) — upstream `woowacourse/<repo>`에서 같은
   미션을 푼 다른 학습자들의 PR / 리뷰 / 멘토 코멘트를 SQLite 아카이브로 수집. 학습자가
   질문하면 **같은 단계 peer PR**을 골라 멘토 리뷰 맥락을 근거로 학습 포인트를 추출.
2. **CS 지식 베이스** (24,407 청크 / 384-dim 임베딩) — 하이브리드 검색(FTS + dense + rerank)
   + Tier 0~3 자동 라우팅. 정의 질문은 cheap 모드, 비교/깊이 질문은 full 모드.
3. **학습 테스트 결과** — `spring-learning-test` 모듈의 JUnit XML을 자동 파싱해 모듈별
   완료율 / pass-fail / concept 매핑으로 누적.
4. **Drill 채점** — 학습자가 자기 말로 답한 내용을 4차원(정확도 / 깊이 / 실전성 / 완결성)
   으로 채점해 mastery / uncertainty 산출.

이 네 입력이 **단일 학습자 stream**(`state/learner/`)에 누적되며 cross-mission 패턴까지 인식.
같은 개념을 반복 질문하면 답이 자동으로 깊어지고, 정착된 개념은 기본 정의를 생략한다 (closed-loop).

---

## 1분 안에 시작

**1) 이 저장소만 직접 클론** (한 번만, 위치 자유)

```bash
cd ~/IdeaProjects                                       # 또는 원하는 위치
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
```

**2) AI 세션 열기** — 권한 자동 승인 옵션으로 시작 (학습자가 매 명령마다 y/n 안 묻게)

| AI | 명령 | 비고 |
|---|---|---|
| **Claude Code** | `claude --dangerously-skip-permissions` | 모든 권한 자동 승인 |
| **Codex (OpenAI)** | `codex --full-auto` | full-auto 모드 |
| **Gemini CLI** | `gemini --yolo` | YOLO 모드 (자동 승인) |

> **주의**: 권한 자동 승인은 **신뢰하는 저장소에서만** 사용. 이 워크벤치는 `bin/`, `scripts/`,
> `state/`, `missions/` 만 건드리고 시스템 설정/외부 API 호출은 학습자에게 명시적으로
> 묻는다. 의심스러우면 옵션 빼고 일반 모드로 시작해도 동작은 동일 — 권한 prompt만 늘어남.

**3) 한국어 의도 한 줄 던지기**

> *"이 저장소로 학습 시작하자. spring-core-1부터 가고 싶어."*

AI가 자동: `pip install -e .` → HuggingFace 모델 warm-up → `bin/cs-index-build` (CS 인덱스
87초) → `missions/` 안에 학습 테스트 클론 → 첫 학습 가이드. 이후 학습자는 답변 따라 한국어로
진행.

---

## 학습자 노트북 배치

```
woowa-learning-hub/                  ← (1) 직접 클론
├─ bin/, scripts/, knowledge/        ← 도구
├─ state/                            ← AI 자동 생성 (gitignored, 노트북에만)
└─ missions/                         ← AI 자동 클론 (gitignored)
   ├─ spring-learning-test/          ← (2) 학습 테스트 (자동)
   └─ <자기 미션 fork>/              ← (3) 자기 fork — PR 보낼 곳 (자동)
```

| 저장소 | 역할 | 누가 클론 |
|---|---|---|
| **woowa-learning-hub** | AI 코칭 워크벤치 | 학습자 직접 (1회) |
| **spring-learning-test** | Spring 개념 검증용 학습 테스트 | AI 자동 |
| **자기 미션 fork** (java-janggi 등) | PR 보낼 자기 저장소. upstream은 `woowacourse/<repo>` | AI 자동 |

이미 다른 곳에 미션 저장소 클론해뒀으면 한국어로 경로만 알려주면 됨:
*"내 미션 저장소는 `~/code/java-janggi`에 있어."* → AI가 `--path`로 등록.

---

## 필요한 것

- Python 3.10+, `git`, `gh` CLI (`gh auth login` 완료)
- AI CLI 한 종류 (Claude Code / Codex / Gemini)
- macOS 또는 Linux 셸

의존성 / 모델 / 인덱스는 첫 세션에서 AI가 자동 처리.

---

## 학습 흐름

학습자는 모두 한국어 의도만 던지고, AI가 자동으로 적절한 명령을 호출한다.

**개념 학습** — *"Bean이 뭐야?"* → AI가 Tier 0~3 자동 분류 + RAG 답변 + 학습자 history 누적.
같은 개념 7일 내 ≥3회 질문하면 다음 답변이 자동으로 깊어진다.

**학습 테스트** — *"spring-core-1 모듈 시작하자"* → AI가 `missions/spring-learning-test`
클론 + 첫 도전 안내. 코드 짜고 *"테스트 통과했어"* → AI가 JUnit XML 자동 파싱 → 결과 기록.

**Drill (이해도 객관 검증)** — *"DI drill 풀어볼래"* → AI가 4문장 답변 요구 질문 발행 →
학습자 답 → 4차원 채점 (정확도 / 깊이 / 실전성 / 완결성). 8점 ×2 + 테스트 통과 → mastered.

**PR 코칭 (peer 데이터 활용)** — *"내 미션 저장소를 코칭해줘.
https://github.com/내계정/java-janggi, upstream은 woowacourse/java-janggi"* → AI가
다음을 자동 처리:

- 학습자 자기 fork를 `missions/`에 클론 + upstream `woowacourse/java-janggi` 등록
- upstream에서 **다른 크루들의 PR / 리뷰 / 멘토 코멘트**를 SQLite로 수집
  (`state/repos/<repo>/archive/prs.sqlite3`)
- 학습자 브랜치 + 열린 PR + 미해결 리뷰 thread 직접 관찰
  (`contexts/learner-state.json`)
- 학습자 질문에 따라 **같은 단계 peer PR** 추출 → 멘토 리뷰 맥락에서 **학습 포인트 도출**
  → 학습자 코드와 비교 → 답변 생성

후속 질문 예시: *"다른 크루들은 Repository 경계를 어떻게 잡았어?"*, *"이 리뷰 기준 다음
액션 뭐야?"*, *"같은 단계에서 자주 지적된 학습 포인트가 뭐야?"* — 모두 peer PR 데이터에
근거해 답.

세부 명세: [`docs/agent-operating-contract.md`](docs/agent-operating-contract.md) (Response
Contract, Learner State Assessment), [`docs/artifact-catalog.md`](docs/artifact-catalog.md)
(coach-run.json + packets 구조).

**프로필 확인** — *"지금까지 뭘 학습했어?"* / *"다음에 뭐 하면 좋을까?"* → mastered /
uncertain / underexplored 분석 + 다음 동선 추천.

전체 명세: [`docs/onboarding.md`](docs/onboarding.md).

---

## 환경 점검 / 복구

학습 흐름엔 불필요. 환경이 깨졌을 때만:

```bash
bin/doctor                          # Python / gh 인증 / 디렉터리 상태
bin/cs-index-build                  # CS 인덱스 강제 재빌드
bin/learner-profile clear --yes     # 학습 데이터 초기화 (privacy reset)
bin/learner-profile redact "..."    # 특정 문자열 포함 이벤트 제거
HF_HUB_OFFLINE=1 bin/rag-ask "..."  # HF 네트워크 차단 (cold latency 절약)
```

`state/`, `missions/`는 모두 `.gitignore` — 노트북에만 존재, 절대 커밋 안 됨.

---

## AI 시작 파일

저장소 루트에서 AI를 실행하면 해당 시작 파일을 자동으로 읽는다.

| AI | 시작 파일 | 스킬 / 에이전트 |
|---|---|---|
| Claude Code | [`CLAUDE.md`](CLAUDE.md) | [`.claude/agents/`](.claude/agents/), [`.claude/commands/`](.claude/commands/) |
| Codex (OpenAI) | [`AGENTS.md`](AGENTS.md) | [`skills/`](skills/) |
| Gemini | [`GEMINI.md`](GEMINI.md) | [`gemini-skills/`](gemini-skills/) |

각 시작 파일에 권장 모델 / 첫 응답 모델 확인 규약이 명시되어 있다.

---

## 저장소 구조

```
bin/                  명령어 래퍼 (AI가 호출 — 학습자가 직접 실행 X)
  rag-ask                개념 질문 → Tier 0~3 자동 분류 + RAG 답변
  coach-run              PR 코칭 (peer 분석 + 멘토 맥락)
  learn-test             JUnit XML → test_result event 자동 기록
  learn-drill            4차원 채점 drill (offer / answer / status / cancel)
  learn-record-code      AI가 코드 수정 도움 시 code_attempt event 기록
  learner-profile        프로필 (show / suggest / clear / redact / set)
  cs-index-build         CS RAG 인덱스 빌드 (첫 세션 자동)
  doctor                 환경 점검
scripts/workbench/    파이프라인 엔진
schemas/              JSON 스키마
knowledge/cs/         CS 지식 베이스 (24,407 청크 / 384-dim 임베딩)
docs/                 운영 문서
.claude/, gemini-skills/, skills/   AI별 에이전트/스킬
missions/             학습자 미션 저장소 (gitignored)
state/                런타임 상태: archive, packets, memory, learner (gitignored)
```

---

## 더 읽을거리

- [`docs/onboarding.md`](docs/onboarding.md) — 학습 흐름 7단계 (학습자 prompt + AI 자동 호출)
- [`docs/learner-memory.md`](docs/learner-memory.md) — 학습자 단일 source of truth
- [`docs/rag-runtime.md`](docs/rag-runtime.md) — Tier 분류 + RAG 런타임
- [`docs/agent-operating-contract.md`](docs/agent-operating-contract.md) — Response Contract,
  Learner State Assessment, First-Run Protocol
- [`docs/artifact-catalog.md`](docs/artifact-catalog.md) — 생성되는 artifact 카탈로그
- [`docs/architecture.md`](docs/architecture.md) — 파이프라인 구조

---

## 라이선스 / 피드백

[MIT License](LICENSE). 우테코 학습 도구라 자유 사용/포크/변경/재배포.

개선 제안 / 버그 / 사용 후기는 이슈로. 아직 초기 단계라 미흡한 부분 많습니다.
