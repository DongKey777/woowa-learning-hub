# Onboarding

학습자 시각 + AI 세션 자동 호출 흐름으로 정리된 onboarding 가이드. **학습자는 한국어 의도만
던지고, 명령은 AI가 자동 호출**한다. 각 단계는 `학습자 한국어` → `AI 자동 호출` →
`예상 결과` → `막혔을 때` 4단 구조.

> **AGENTS 원칙**: 학습자는 CLI를 직접 실행하지 않는다. README의 "1분 안에 시작" 박스를 따라
> AI 세션 한 번 열고, 한국어로 의도만 던지면 끝. 이 문서는 AI가 어떤 흐름을 자동으로
> 처리하는지를 학습자에게 보여주는 시각화 — 학습자가 외울 명령은 없다.

---

## 1. 공통 준비 — First-Run Protocol (AI 세션이 자동 처리)

### 사전 단계 (학습자가 직접) — 단 한 번

```bash
cd ~/IdeaProjects                                          # 자기 노트북 원하는 위치
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
claude    # 또는 codex, gemini
```

`woowa-learning-hub`는 한 번만 직접 클론. 이후 학습 테스트와 자기 미션 저장소는 **AI가
첫 세션에서 `missions/` 아래에 자동 클론**한다 (학습자가 직접 받을 필요 없음).

### 학습자 노트북 디렉토리 배치

```
woowa-learning-hub/                    ← 학습자가 직접 클론
└─ missions/                           ← AI가 자동 클론 (gitignored)
   ├─ spring-learning-test/              학습 테스트 (Spring 개념 검증)
   └─ <자기 미션>/                       자기 fork — PR 보낼 곳
```

### 학습자 한국어 prompt

> *"이 저장소로 학습 시작하자. spring-core-1부터 가고 싶어."*
> 또는 PR 코칭부터 가고 싶으면:
> *"내 미션 저장소를 코칭해줘. https://github.com/내계정/java-janggi, upstream은
> woowacourse/java-janggi, 사이클2 진행 중."*

### AI 세션 자동 호출 흐름

시작 파일(`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`)의 First-Run Protocol에 따라:

1. `pip install -e .` — Python 의존성 설치 (sentence-transformers / numpy / scikit-learn)
2. HuggingFace 모델 warm-up — `paraphrase-multilingual-MiniLM-L12-v2` + cross-encoder
   (첫 실행만 온라인, 이후 캐시 재사용)
3. `bin/cs-index-build` — CS RAG 인덱스 생성 (`state/cs_rag/index.sqlite3`,
   `dense.npz`, `manifest.json`). 87초 정도 소요 (cold)
4. **학습 테스트 / 미션 저장소 자동 클론** (학습자 의도에 따라):
   - 학습 테스트 흐름: `cd missions && git clone https://github.com/woowacourse/spring-learning-test.git`
   - PR 코칭 흐름: 학습자 fork (`https://github.com/내계정/<repo>.git`)을 `missions/<repo>/`에 클론
     → `bin/onboard-repo` 등록 (upstream `woowacourse/<repo>` 명시)
5. (PR 코칭) Learner State Assessment — 학습자 브랜치/PR/스레드 직접 관찰
6. 첫 학습 가이드 시작

**예상 결과**: AI가 각 단계를 한국어 한 줄씩 보고 (예: *"CS 인덱스 빌드 중…"*). 모두
끝나면 학습자에게 "어디서부터 시작할까?" 묻거나 직전 의도(spring-core-1 등)에 따라 바로 첫
도전 과제 안내.

### 이미 다른 곳에 미션 저장소가 있다면

`missions/` 권장이지만, 학습자가 이미 다른 위치 (예: `~/code/java-janggi`)에 클론해뒀으면
한국어로 위치만 알려주면 됨:

> *"내 미션 저장소는 `~/code/java-janggi`에 이미 있어."*

→ AI 자동: `bin/onboard-repo --path ~/code/java-janggi --upstream woowacourse/java-janggi ...`

**막혔을 때** (수동 진단):

```bash
bin/doctor                  # Python / gh 인증 / 디렉터리 상태
bin/cs-index-build          # CS 인덱스 강제 재빌드
HF_HUB_OFFLINE=1 ...        # HF Hub 네트워크 차단 (cold latency 절약)
```

---

## 2. 학습 테스트로 시작하기 (`spring-learning-test`)

`missions/spring-learning-test`의 모듈 (spring-core-1, spring-core-2, spring-mvc-1, …)을
풀면서 Spring 핵심 개념을 코드로 검증. 학습자가 코드를 짜고 테스트를 돌리면 AI가 결과를
자동 기록.

**학습자 한국어 prompt**:

> *"spring-core-1 모듈 시작하자."*
> 또는 코드 짠 후 *"테스트 돌렸어 통과했어."*

**AI 세션 자동 호출**:

```bash
bin/learn-test --module spring-core-1                  # JUnit XML 자동 파싱
# 또는
bin/learn-test --path <build/test-results/test 경로>    # 명시 경로
```

각 `<testcase>`마다 `test_result` event가 `state/learner/history.jsonl`에 기록됨
(pass/fail, duration, redacted 실패 메시지, 자동 추출된 concept_ids).

**예상 결과**:

```json
{"module": "spring-core-1", "scanned": 6, "recorded": 6, "passed": 6, "failed": 0}
```

모듈의 모든 테스트가 통과되면 `modules_progress.spring-core-1.completion_estimate = 1.0`.
프로필이 자동 업데이트되어 다음 모듈 추천 시 prereq 충족 신호로 사용됨.

**막혔을 때**:

```bash
bin/learn-test --no-record --module spring-core-1   # 채점만 하고 기록 안 함 (dry-run)
```

---

## 3. 개념 질문하기 (한국어 → `bin/rag-ask` 자동 라우팅)

학습자가 학습 중 막히면 한국어로 질문만 하면 됨. AI가 router로 Tier 0~3 자동 분류 +
적절한 RAG 호출 + 답변 생성 + 학습자 history 누적.

**학습자 한국어 prompt 예시**:

| Prompt | 자동 분류 |
|---|---|
| *"Bean이 뭐야?"* | Tier 1 (cheap RAG, 정의) |
| *"DI vs Service Locator 차이가 뭐야?"* | Tier 2 (full RAG, 비교/깊이) |
| *"Gradle 멀티 프로젝트 어떻게 설정해?"* | Tier 0 (도구 질문, RAG 미사용) |
| *"내 PR 리뷰해줘"* | Tier 3 (PR 코칭, `bin/coach-run`으로 위임) |

**AI 세션 자동 호출**:

```bash
bin/rag-ask "Bean이 뭐야?" --module spring-core-1
```

출력 JSON에 `decision.tier`, `hits.by_fallback_key` (Tier 1/2의 doc paths),
`learner_context` (cold-start 후엔 mastered/uncertain/skip_basics_for/deepen_for 포함)
모두 포함. AI는 이걸 읽어 답변 톤·깊이·생략을 자동 조정 (closed-loop).

### 같은 개념 반복 시 자동 격상

7일 내 같은 concept을 3번 이상 물으면 router가 Tier 1 → Tier 2로 자동 격상하고,
다음 답변에 `"n번째 질문이야"` 인지 표시가 자연스럽게 들어감.

### Override 키워드

| 표현 | 효과 |
|---|---|
| `"RAG로 깊게"`, `"심도 있게"` | Tier 2 강제 |
| `"RAG로 답해"`, `"근거 보여줘"` | 최소 Tier 1 강제 |
| `"그냥 답해"`, `"RAG 빼고"` | Tier 0 강제 |
| `"코치 모드"` | Tier 3 시도 |

전체 명세: [`docs/rag-runtime.md`](rag-runtime.md).

**막혔을 때**:

```bash
HF_HUB_OFFLINE=1 bin/rag-ask "..."   # cold path latency ~7s → ~500ms
```

---

## 4. Drill 풀기 (이해도 객관 검증)

같은 개념을 여러 번 물어봤지만 정말 이해했는지 객관 검증하고 싶을 때. 4차원 채점
(정확도 / 깊이 / 실전성 / 완결성, 각 dimension에 점수 → 총 0~10점).

**학습자 한국어 prompt**:

> *"DI drill 풀어볼래."*

**AI 세션 자동 호출**:

```bash
bin/learn-drill offer --concept concept:spring/di
# (또는 concept 생략 시 uncertain 1순위 자동 선택)
```

학습자에게 한국어 질문 노출 (예: *"Dependency Injection이 무엇이고, 왜 그렇게 동작하며,
실제 코드에서 어떻게 사용되는지 자기 말로 설명해 보세요. 최소 3-4문장 이상."*).

학습자가 답하면:

```bash
bin/learn-drill answer "..."   # 4차원 채점 + drill_answer event 기록 + pending 클리어
```

**예상 결과**:

```json
{
  "drill_session_id": "...",
  "concept_id": "concept:spring/di",
  "total_score": 8,
  "level": "L4",
  "dimensions": {"accuracy": 3, "depth": 2, "practicality": 2, "completeness": 1},
  "weak_tags": ["깊이"],
  "improvement_notes": ["왜 그런지/내부 원리를 한 문장 더 풀어서 설명하면 깊이가 올라갑니다."]
}
```

**Mastery 승격 조건**: drill 8점 이상 ×2 + 테스트 통과 + PR 부정 피드백 없음 → 그 concept이
`profile.concepts.mastered`로 이동. 다음 답변부터 기본 정의 자동 생략.

**막혔을 때**:

```bash
bin/learn-drill status         # 현재 pending drill 조회
bin/learn-drill cancel         # pending 폐기 (재시도하고 싶을 때)
```

---

## 5. 프로필 확인하기

학습자가 자기 학습 흐름을 메타로 보고 싶을 때.

**학습자 한국어 prompt**:

> *"내가 지금까지 뭘 학습했어?"* / *"다음에 뭐 하면 좋을까?"*

**AI 세션 자동 호출**:

```bash
bin/learner-profile show                    # 전체 프로필 dump
bin/learner-profile suggest --format text   # 다음 학습 동선 추천
```

**예상 결과** (요약):

- `mastered` / `uncertain` / `underexplored` concept 분류
- `modules_progress` (모듈별 통과율 / completion_estimate)
- `tier_distribution` (Tier 0/1/2/3-blocked 사용 분포)
- `next_recommendations`: drill / underexplored concept / next module (priority 순)

**데이터 위치 + 프라이버시**:

- 모든 데이터는 `state/learner/` 안 (gitignore — 절대 커밋 안 됨)
- 매 이벤트 자동 redaction: 이메일 / GH 토큰 / 비밀번호 후보 패턴 → `***REDACTED***`
- 학습자 통제권:
  ```bash
  bin/learner-profile clear --yes        # 전체 삭제
  bin/learner-profile redact "<문자열>"  # 특정 문자열 포함 이벤트 제거
  bin/learner-profile recompute          # history → profile 강제 재계산
  ```

전체 명세: [`docs/learner-memory.md`](learner-memory.md).

---

## 6. PR 코칭 (peer 리뷰 기반)

미션 저장소를 클론받아 다른 크루의 PR / 리뷰 / 멘토 코멘트를 분석. 학습자의 현재 상태와
peer 패턴을 비교해서 학습 포인트 추출.

**학습자 한국어 prompt**:

> *"내 미션 저장소를 코칭해줘. 저장소는 `https://github.com/내계정/java-janggi`이고,
>    upstream은 `woowacourse/java-janggi`, 사이클2를 진행 중이야."*

**AI 세션 자동 호출**:

```bash
# 1) 클론 (이미 있으면 skip)
cd missions && git clone https://github.com/내계정/java-janggi.git && cd ..

# 2) 등록
bin/onboard-repo \
  --path missions/java-janggi \
  --upstream woowacourse/java-janggi \
  --track java \
  --mission java-janggi \
  --title-contains "사이클2"

# 3) PR 아카이브 부트스트랩 (수 분 소요 — peer PR 수집)
bin/bootstrap-repo --repo java-janggi

# 4) 코치 실행
bin/coach-run --repo java-janggi --prompt "이 리뷰 기준 다음 액션 뭐야?"
```

**예상 결과**: `state/repos/java-janggi/actions/coach-run.json`에 다음이 들어감 — 학습자
브랜치 직접 관찰 (`contexts/learner-state.json`), 같은 단계 peer PR 후보, 멘토 리뷰 맥락,
학습 포인트별 추천, `response_contract` (상태 요약 / 검증 필요 스레드 / CS evidence).

후속 질문은 한국어로 자연스럽게:

> *"이 PR 기준으로 지금 무엇을 먼저 보면 좋을까?"*
> *"다른 크루들은 Repository 경계를 어떻게 잡았어?"*
> *"최근에 반복해서 놓치고 있는 학습 포인트가 있어?"*

**막혔을 때**:

```bash
bin/archive-status --repo java-janggi    # PR 아카이브 부트스트랩 상태
bin/repo-readiness --path missions/java-janggi   # 등록/인증/디렉터리 점검
bin/sync-prs --repo java-janggi --mode full      # PR 강제 재수집
```

---

## 7. 개발자 검증 도구 (스키마/회귀/일반화)

저장소 자체에 기여하거나 디버깅할 때만 사용. 학습 흐름과 무관.

```bash
bin/validate-state --repo java-janggi       # 현재 artifact가 schema 계약 만족하는지
bin/mission-map --repo java-janggi          # mission 분석 artifact 구조 검증
bin/golden                                  # coach-run 핵심 필드 회귀 안전망
bin/registry-audit                          # 여러 미션 repo 일반화 점검
```

전체 회귀 테스트:

```bash
HF_HUB_OFFLINE=1 python3 -m unittest discover -s tests/unit -p 'test_*.py'
```

`HF_HUB_OFFLINE=1` 필수 — 안 켜면 sentence-transformers가 HuggingFace HEAD 재시도로
장시간 멈출 수 있음.

---

## 더 깊이 가고 싶다면

- [`docs/agent-operating-contract.md`](agent-operating-contract.md) — Response Contract,
  Learner State Assessment, First-Run Protocol 정밀 명세
- [`docs/learner-memory.md`](learner-memory.md) — `state/learner/` 단일 source of truth,
  5 event types, mastery 알고리즘
- [`docs/rag-runtime.md`](rag-runtime.md) — Tier 분류 + RAG 런타임 운영
- [`docs/artifact-catalog.md`](artifact-catalog.md) — `coach-run.json` 등 artifact 카탈로그
- [`docs/architecture.md`](architecture.md) — 파이프라인 구조 전체
