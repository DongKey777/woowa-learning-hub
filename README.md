# woowa-learning-hub

우아한테크코스 미션 학습과 CS 개념 학습을 한국어 AI 세션 안에서 처리하는
워크벤치입니다. 학습자가 한국어로 질문을 입력하면 AI가 PR 데이터, CS 자료,
학습 테스트 결과, drill 채점을 묶어 응답합니다.

학습자는 명령어를 직접 입력하지 않습니다. AI 세션이 `bin/*` 래퍼를
호출합니다.

## 사용법

```bash
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
```

저장소 루트에서 AI CLI를 엽니다.

| AI | 명령 |
|---|---|
| Claude Code | `claude --dangerously-skip-permissions` |
| Codex | `codex --full-auto` |
| Gemini CLI | `gemini --yolo` |

자동 승인 옵션은 신뢰 저장소에서만 사용합니다. 옵션 없이 실행해도 동작은
같으며 명령마다 승인 prompt가 추가됩니다.

첫 세션에서 AI가 의존성, 모델 캐시, RAG 인덱스를 자동 다운로드합니다.

질문 예시:

- "Spring Bean이 뭐야?"
- "MVCC랑 락 차이는?"
- "spring-core-1 모듈 시작하자."
- "내 미션 저장소 코칭해줘. https://github.com/내계정/java-janggi, upstream은 woowacourse/java-janggi."
- "DI drill 풀어볼래."

## 기능

**peer PR 코칭** — 학습자 미션 저장소와 upstream `woowacourse/<repo>`를
등록하면 같은 미션 PR과 멘토 리뷰를 SQLite에 수집합니다. 같은 단계 PR
기준으로 학습 포인트를 도출해 응답합니다.

**CS RAG 응답** — `knowledge/cs/` 안의 markdown 문서에서 BGE-M3 dense +
sparse + cross-encoder 재랭크로 답을 찾습니다. 문서에 없는 주제는 일반
지식으로 답하되 코퍼스 출처가 아니라는 표시(`tier_downgrade`)를 붙입니다.
`bin/rag-ask`는 daemon warm service를 기본 사용하고, checkout fingerprint가
바뀌면 stale daemon을 자동 재시작합니다.

**학습 테스트** — `spring-learning-test` 모듈을 자동 클론합니다. JUnit XML을
파싱해 모듈별 통과율을 누적합니다.

**Drill 채점** — 4문장 답변 요구 질문에 대해 정확도/깊이/실전성/완결성 4축
0-10점 채점, 평균 8점 이상 ×2회 + 학습 테스트 통과 시 mastered 표시.

**프로필 누적** — 같은 개념을 7일 내 3회 이상 질문하면 응답이 더 깊어지고,
mastered 처리된 개념은 기본 정의를 생략합니다. 다음 행동 제안은 현재 질문의
개념과 겹칠 때만 강제 hint로 올라와 무관한 drill이 섞이지 않게 합니다.

**자연스러운 품질 개선 루프** — 학습자에게 매번 피드백을 요구하지 않고,
`rag_ask`의 `source_event_id` / `turn_id`로 질문, 라우팅, 검색, 답변 품질
로그를 조용히 연결합니다. AI 답변 전문은 기본 저장하지 않고 요약, redacted
excerpt, citation mismatch, duplicate text 같은 품질 flag만
`state/learner/response-quality.jsonl`에 남겨 이후 개선 파이프라인에서
분석합니다.

**v4 인지 트리거** — `coach-run`이 한 턴에 하나만 자기점검, 복습 드릴,
후속 질문 중 선택합니다. 자기점검은 calibration으로만 기록되고, 복습 드릴은
spaced repetition 일정에 따라 다시 제안됩니다.

**출처 grounding** — CS 근거 블록의 source path가 실제 RAG verifier hit 또는
citation path에 있는지 검사하고, 어긋나면 응답에 경고로 드러냅니다.

## 디렉터리

```
bin/                 명령 래퍼 (AI 호출용)
  rag-ask              CS 개념 질문 → Tier 0~3 → RAG 응답
  coach-run            PR 코칭 (peer 분석 + 멘토 맥락)
  learn-test           JUnit XML → test_result event
  learn-drill          4축 drill (offer / answer / status)
  learn-self-assess    pending 자기점검 답변 → self_assessment event
  learn-response-quality RAG 답변 품질 telemetry 기록
  response-quality-mine  답변 품질 flag / citation mismatch 분석
  cs-index-build       CS 인덱스 빌드 (첫 세션 자동)
  doctor               환경 점검
scripts/workbench/   파이프라인 엔진
scripts/learning/    RAG / drill / profile 로직
knowledge/cs/        CS markdown (Spring, DB, 디자인 패턴 등)
schemas/             JSON 스키마
docs/                운영 문서
state/               런타임 상태 (gitignored)
missions/            학습자 미션 저장소 (gitignored)
```

## 기술 구조

```
[학습자 질문]
    │
    ▼
[AI CLI: Claude Code / Codex / Gemini]
    │  (CLAUDE.md / AGENTS.md / GEMINI.md 시작 파일 자동 로드)
    ▼
[bin/* 래퍼]   ← bin/_rag_env.sh로 production env 강제
    │
    ▼
[scripts/workbench/cli.py]
    │   ├─ interactive_rag_router  → Tier 0~3 분류
    │   │   (safe lexicon + study-intent + corpus signal_rules bridge)
    │   ├─ integration.augment     → CS RAG (state/cs_rag)
    │   └─ coach_run               → PR 코칭 파이프라인
    │
    ▼
[데이터 백엔드]
    state/cs_rag/         LanceDB 인덱스 (BGE-M3 dense + sparse 28,773 row)
    state/repos/<repo>/   archive/prs.sqlite3, packets/*.json, contexts/*.json
    state/learner/        history.jsonl, profile.json, response-quality.jsonl
```

핵심 외부 의존:

- BGE-M3 (dense + sparse 임베딩, 1024차원)
- cross-encoder/bge-reranker-v2-m3 (재랭크, Phase 9.3 거부 임계값 0.10)
- LanceDB (벡터 인덱스), SQLite (PR archive), JSONL (events / drill history)
- gh CLI (PR 수집), HuggingFace Hub (모델 캐시)

## 환경

- Python 3.10 이상
- `git`, `gh` CLI (`gh auth login`)
- macOS / Linux / WSL2 / Windows native

운영체제 분기는 AI가 처리합니다 (`bin/*` 또는 `.\bin\*.ps1`).

## 점검 명령

학습 흐름엔 사용하지 않습니다. 환경이 깨졌을 때만:

```bash
bin/doctor                          # Python / gh / 디렉터리 상태
bin/cs-index-build                  # 인덱스 다시 받기
bin/learner-profile clear --yes     # 학습 데이터 초기화
```

## AI 시작 파일

| AI | 시작 파일 | 비고 |
|---|---|---|
| Claude Code | [`CLAUDE.md`](CLAUDE.md) | `.claude/agents/`, `.claude/commands/` |
| Codex | [`AGENTS.md`](AGENTS.md) | `skills/` |
| Gemini | [`GEMINI.md`](GEMINI.md) | `gemini-skills/` |

권장 모델과 첫 응답 모델 확인 규약은 각 시작 파일에 있습니다.

## 더 읽기

- [`docs/onboarding.md`](docs/onboarding.md) — 학습 흐름 7단계
- [`docs/rag-runtime.md`](docs/rag-runtime.md) — Tier 분류 + RAG 런타임
- [`docs/agent-operating-contract.md`](docs/agent-operating-contract.md) — Response Contract, First-Run Protocol
- [`docs/learning-system-v4.md`](docs/learning-system-v4.md) — v4 인지 트리거, 자기점검, 복습 drill, citation grounding
- [`docs/architecture.md`](docs/architecture.md) — 파이프라인 구조

## 라이선스

[MIT](LICENSE).
