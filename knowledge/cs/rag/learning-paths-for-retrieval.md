# Learning Paths For Retrieval

> 한 줄 요약: RAG가 학습 사용자의 의도를 더 잘 따라가도록, 질문 유형별 retrieval 경로를 정리한 문서다.

## 왜 필요한가

이 repo는 단순 목차형 저장소가 아니라, 질문 의도에 따라 다른 경로로 읽어야 하는 지식 베이스다.
그래서 retrieval path를 미리 정해두면 다음이 쉬워진다.

- 질문이 들어왔을 때 어디서 시작할지
- 어떤 문서를 우선 붙일지
- 학습 흐름을 개념 -> 실전 -> 비교 -> 검증으로 유지할지

## Retrieval Paths

### 1. Junior Onboarding

경로:

`README.md` -> `JUNIOR-BACKEND-ROADMAP.md` -> `contents/language/` -> `contents/operating-system/` -> `contents/network/`

목적:

- 기초 개념을 빠르게 익히고
- 정의 중심 답변을 만들고
- 이후 심화 축으로 이동한다

### 2. Debugging Path

경로:

`contents/database/slow-query-analysis-playbook.md` -> `contents/network/timeout-types-connect-read-write.md` -> `contents/spring/spring-transaction-debugging-playbook.md` -> 관련 README

목적:

- 장애를 먼저 보고
- 원인 후보를 줄이고
- 재현과 검증을 붙인다

### 3. Architecture Path

경로:

`contents/software-engineering/README.md` -> `ddd-bounded-context-failure-patterns.md` -> `monolith-to-msa-failure-patterns.md` -> `contents/system-design/README.md`

목적:

- 경계와 책임을 먼저 정하고
- 그 다음 확장성/운영성을 붙인다

### 4. Security Path

경로:

`contents/security/README.md` -> `authentication-vs-authorization.md` -> `jwt-deep-dive.md` -> `oauth2-authorization-code-grant.md` -> `contents/spring/spring-oauth2-jwt-integration.md`

목적:

- 인증과 인가를 분리하고
- 토큰/세션/외부 로그인 경계를 연결한다

### 5. Runtime Performance Path

경로:

`contents/language/README.md` -> `virtual-threads-project-loom.md` -> `g1-vs-zgc.md` -> `reflection-cost-and-alternatives.md` -> `contents/operating-system/`

목적:

- JVM과 OS를 함께 보고
- 지연 시간과 처리량을 분리해서 이해한다

### 6. Distributed System Path

경로:

`contents/system-design/README.md` -> `system-design-framework.md` -> `back-of-envelope-estimation.md` -> `distributed-cache-design.md` -> `chat-system-design.md`

목적:

- 숫자 감각을 만들고
- 일관성과 가용성의 경계를 잡는다

## Query Expansion Rules

RAG 질의가 짧으면 다음처럼 확장한다.

- 개념어 1개 -> 관련 비교어 추가
- 기술명 1개 -> 장애 키워드 추가
- 설계명 1개 -> 트레이드오프 키워드 추가

예:

- `JWT` -> `JWT refresh token theft replay`
- `rate limiter` -> `token bucket sliding window redis`
- `spring transaction` -> `rollback self invocation debugging`

## Retrieval Checklist

응답 전에 아래를 확인한다.

1. 정의 문서가 있는가
2. 실전 문서가 있는가
3. 비교 문서가 있는가
4. 상위 README 링크가 있는가
5. 시니어 질문으로 검증 가능한가

## Learning Style Mapping

| 스타일 | 우선 경로 |
|---|---|
| 개념 먼저 | README -> 기본 문서 -> 질문집 |
| 장애 먼저 | playbook -> root cause -> trade-off |
| 설계 먼저 | system design -> architecture -> security |
| 성능 먼저 | OS -> Java -> Database -> Network |

## Final Rule

질문을 받았을 때 가장 먼저 해야 할 일은 답을 쓰는 게 아니라, **어느 문서 축이 그 질문을 가장 정확하게 설명하는지 고르는 것**이다.
