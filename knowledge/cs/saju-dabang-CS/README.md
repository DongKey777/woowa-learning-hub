# saju-dabang-CS

> 사주다방 프로젝트를 실제 사례로 삼아 CS를 공부하고, 면접 답변까지 연결하기 위한 독립 학습 저장소

## 한 줄 소개

이 저장소는 CS 이론을 따로 외우는 데서 끝내지 않고, **실제 서비스 코드에 연결해서 이해하고 설명할 수 있게 만드는 것**을 목표로 한다.

기준 프로젝트:
- 프론트엔드: `/Users/idonghun/IdeaProjects/saju-dabang/app`
- 활성 백엔드: `/Users/idonghun/IdeaProjects/saju-dabang/server-java`
- legacy 비교용 백엔드: `/Users/idonghun/IdeaProjects/saju-dabang/archive/legacy-node-api`

## 왜 사주다방으로 공부하나

사주다방은 단순한 CRUD 서비스가 아니다.

- 토스 로그인
- 인앱 결제
- 코인 정합성
- Redis queue
- SSE
- PostgreSQL 트랜잭션
- Docker 기반 prelaunch runtime
- Java/Spring 백엔드 전환

즉 취준 CS에서 자주 나오는 주제가 실제 코드 안에 다 들어 있다.

이 저장소는 아래를 연결한다.

1. **CS 이론**
2. **사주다방 코드**
3. **면접 답변**

## 이 저장소의 사용 방식

각 문서는 기본적으로 아래 흐름을 따른다.

1. 개념 정리
2. 사주다방 코드에서 어디에 쓰이는지
3. 코드 스니펫으로 다시 보기
4. 면접에서 어떻게 설명할지
5. 꼬리질문까지 대비하기

즉 목표는 “읽고 끝”이 아니라,

`개념 -> 코드 -> 설명 -> 답변`

으로 연결하는 것이다.

## 추천 학습 순서

### 1단계. 전체 시스템 감 잡기

1. [01-system-map.md](./01-system-map.md)
2. [02-network-http-sse.md](./02-network-http-sse.md)
3. [03-database-transaction-consistency.md](./03-database-transaction-consistency.md)
4. [04-operating-system-concurrency.md](./04-operating-system-concurrency.md)
5. [05-security-auth-crypto.md](./05-security-auth-crypto.md)
6. [06-software-engineering-architecture.md](./06-software-engineering-architecture.md)
7. [07-interview-questions.md](./07-interview-questions.md)

### 2단계. 세부 주제별 깊게 파기

#### Network
- [network/README.md](./network/README.md)
- [network/01-http-rest.md](./network/01-http-rest.md)
- [network/02-sse-replay.md](./network/02-sse-replay.md)
- [network/03-dns-https-mtls.md](./network/03-dns-https-mtls.md)
- [network/04-request-response-lifecycle.md](./network/04-request-response-lifecycle.md)
- [network/05-private-prelaunch-flow.md](./network/05-private-prelaunch-flow.md)

#### Database
- [database/README.md](./database/README.md)
- [database/01-schema-overview.md](./database/01-schema-overview.md)
- [database/02-transaction-idempotency.md](./database/02-transaction-idempotency.md)
- [database/03-reserve-capture-refund.md](./database/03-reserve-capture-refund.md)
- [database/04-race-condition-locking.md](./database/04-race-condition-locking.md)
- [database/05-ledger-vs-transaction-log.md](./database/05-ledger-vs-transaction-log.md)

#### Operating System / Concurrency
- [operating-system/README.md](./operating-system/README.md)
- [operating-system/01-process-thread-model.md](./operating-system/01-process-thread-model.md)
- [operating-system/02-virtual-thread-worker.md](./operating-system/02-virtual-thread-worker.md)
- [operating-system/03-reliable-queue-recovery.md](./operating-system/03-reliable-queue-recovery.md)
- [operating-system/04-blocking-vs-nonblocking.md](./operating-system/04-blocking-vs-nonblocking.md)
- [operating-system/05-failure-recovery-lifecycle.md](./operating-system/05-failure-recovery-lifecycle.md)

#### Security
- [security/README.md](./security/README.md)
- [security/01-auth-flow.md](./security/01-auth-flow.md)
- [security/02-session-cache-fallback.md](./security/02-session-cache-fallback.md)
- [security/03-token-encryption-mtls.md](./security/03-token-encryption-mtls.md)
- [security/04-auth-step-by-step.md](./security/04-auth-step-by-step.md)
- [security/05-iap-server-verification.md](./security/05-iap-server-verification.md)

#### Software Engineering
- [software-engineering/README.md](./software-engineering/README.md)
- [software-engineering/01-layered-architecture.md](./software-engineering/01-layered-architecture.md)
- [software-engineering/02-bounded-context-port-adapter.md](./software-engineering/02-bounded-context-port-adapter.md)
- [software-engineering/03-cutover-archive-strategy.md](./software-engineering/03-cutover-archive-strategy.md)
- [software-engineering/04-java-migration-strategy.md](./software-engineering/04-java-migration-strategy.md)
- [software-engineering/05-testing-strategy.md](./software-engineering/05-testing-strategy.md)

#### Interview
- [interview/README.md](./interview/README.md)
- [interview/01-network-answers.md](./interview/01-network-answers.md)
- [interview/02-database-answers.md](./interview/02-database-answers.md)
- [interview/03-operating-system-answers.md](./interview/03-operating-system-answers.md)
- [interview/04-security-answers.md](./interview/04-security-answers.md)
- [interview/05-architecture-answers.md](./interview/05-architecture-answers.md)

#### Flashcards
- [flashcards/README.md](./flashcards/README.md)
- [flashcards/network.md](./flashcards/network.md)
- [flashcards/database.md](./flashcards/database.md)
- [flashcards/operating-system.md](./flashcards/operating-system.md)
- [flashcards/security.md](./flashcards/security.md)
- [flashcards/architecture.md](./flashcards/architecture.md)

#### Mock Interview
- [mock-interview/README.md](./mock-interview/README.md)
- [mock-interview/50-questions.md](./mock-interview/50-questions.md)

## 공부 루틴 추천

### 루틴 A. 개념부터

1. 해당 카테고리 문서 읽기
2. 관련 사주다방 코드 파일 열기
3. 코드 스니펫 다시 읽기
4. 면접 답변 30초 버전 말해보기
5. 꼬리질문 답해보기

### 루틴 B. 코드부터

1. 사주다방 코드 파일부터 읽기
2. “여기서 쓰인 CS 개념이 뭐지?” 질문하기
3. 이 저장소 문서에서 해당 개념 확인
4. 다시 코드로 돌아와 설명하기

## 이 저장소를 어떻게 관리할까

### 원칙

- 이론만 적지 않는다
- 반드시 코드 연결을 남긴다
- 가능하면 코드 스니펫을 넣는다
- 면접에서 말할 수 있는 문장으로 마무리한다
- 꼬리질문까지 같이 적는다

### 문서 품질 기준

- “개념 설명”만 있으면 미완성
- “코드 위치”만 있으면 미완성
- “면접 답변”만 있으면 미완성

세 가지가 같이 있어야 완성으로 본다.

## 현재 상태

- 개요 문서: 있음
- 세부 카테고리 문서: 있음
- 핵심 문서: 코드 스니펫 + 꼬리질문 반영
- 면접 답변 문서: 30초 / 2분 중심
- flashcards: 있음
- mock interview: 있음

## 앞으로 확장할 것

1. 면접 답변을 `30초 / 2분 / 5분` 버전으로 전부 확장
2. 세부 문서 전체에 코드 스니펫/꼬리질문 비율 확대
3. mock interview 답안지 세트 만들기
4. 주제별 다이어그램 추가

## 핵심 철학

이 저장소의 목적은 “CS를 많이 읽는 것”이 아니라,

**사주다방 코드를 이용해서 CS를 설명 가능한 수준까지 끌어올리는 것**

이다.
