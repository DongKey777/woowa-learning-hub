# Question Decomposition Examples

> 한 줄 요약: 사용자의 질문을 `도메인`, `의도`, `제약`, `답변 형태`로 쪼개는 예시를 모아둔 문서다.

## 기본 분해 템플릿

질문을 받을 때 아래 네 항목으로 쪼개면 검색 품질이 안정적이다.

1. `Domain`: 어느 카테고리인가
2. `Intent`: 정의, 비교, 장애, 설계, 코드 중 무엇인가
3. `Constraint`: 버전, DB 엔진, 프레임워크, 환경 제약이 있는가
4. `Answer Shape`: 한 줄 정의, 표, 코드, 운영 절차 중 무엇이 필요한가

## 예시 1: Spring

질문:

`@Transactional이 같은 클래스 내부 호출에서 왜 안 먹나요?`

분해:

- `Domain`: `spring`
- `Intent`: 동작 원리 + 장애 사례
- `Constraint`: 프록시 기반 AOP
- `Answer Shape`: 흐름 설명 + 코드

검색 순서:

1. [AOP와 프록시 메커니즘](../contents/spring/aop-proxy-mechanism.md)
2. [@Transactional 깊이 파기](../contents/spring/transactional-deep-dive.md)
3. [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)

## 예시 2: Network + Security

질문:

`gRPC를 브라우저에서 바로 못 쓰는 이유가 뭐예요?`

분해:

- `Domain`: `network` + `security`
- `Intent`: 비교
- `Constraint`: browser compatibility, HTTP/2, proxy
- `Answer Shape`: trade-off table

검색 순서:

1. [gRPC vs REST](../contents/network/grpc-vs-rest.md)
2. [HTTP/2 Multiplexing과 HOL Blocking](../contents/network/http2-multiplexing-hol-blocking.md)
3. [OAuth2 Authorization Code Grant](../contents/security/oauth2-authorization-code-grant.md)

## 예시 3: Database + System Design

질문:

`페이지네이션이 offset보다 seek이 왜 좋은가요?`

분해:

- `Domain`: `database`
- `Intent`: 성능 + 구현
- `Constraint`: large table, pagination
- `Answer Shape`: 비교 + SQL

검색 순서:

1. [인덱스와 실행 계획](../contents/database/index-and-explain.md)
2. [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md)
3. [System Design 면접 프레임워크](../contents/system-design/system-design-framework.md)

## 예시 4: OS + Java

질문:

`Virtual Threads가 많아도 되는 이유는 뭔가요?`

분해:

- `Domain`: `language/java`
- `Intent`: 원리 + trade-off
- `Constraint`: blocking I/O, pinning
- `Answer Shape`: 설명 + 운영 주의점

검색 순서:

1. [Virtual Threads(Project Loom)](../contents/language/java/virtual-threads-project-loom.md)
2. [I/O 모델과 이벤트 루프](../contents/operating-system/io-models-and-event-loop.md)
3. [컨텍스트 스위칭, 데드락, lock-free](../contents/operating-system/context-switching-deadlock-lockfree.md)

## 예시 5: Architecture + RAG

질문:

`MSA로 가기 전에 뭘 먼저 점검해야 하나요?`

분해:

- `Domain`: `software-engineering`
- `Intent`: 설계 판단
- `Constraint`: 조직/경계/기술 부채
- `Answer Shape`: checklist + trade-off

검색 순서:

1. [Monolith -> MSA Failure Patterns](../contents/software-engineering/monolith-to-msa-failure-patterns.md)
2. [DDD Bounded Context Failure Patterns](../contents/software-engineering/ddd-bounded-context-failure-patterns.md)
3. [RAG Topic Map](./topic-map.md)

## 분해 팁

- 질문이 길면 먼저 동사를 찾는다.
- `왜`, `어떻게`, `언제`, `무엇과 비교`를 구분한다.
- 버전, 엔진, 환경이 있으면 반드시 메타데이터로 남긴다.
- 질문이 흔들리면 답을 만들지 말고 다시 쪼갠다.

## 한 줄 정리

좋은 검색은 긴 질문을 한 번에 찾는 게 아니라, `도메인 + 의도 + 제약 + 답변 형태`로 분해하는 데서 시작한다.
