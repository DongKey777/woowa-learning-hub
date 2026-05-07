---
schema_version: 3
title: Duplicate Key vs Busy Response Mapping
concept_id: database/duplicate-key-vs-busy-response-mapping
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
- duplicate-key-response
- busy-response
- retryable-response
- http-mapping
aliases:
- duplicate key vs busy response mapping
- duplicate key http response
- lock timeout http response
- deadlock http response
- serialization failure http response
- service layer outcome mapping
- already exists busy retryable http choice
- duplicate key conflict or success
- busy 429 503 choice
- duplicate key 409 아니에요
symptoms:
- duplicate key와 busy를 모두 conflict로 보고 HTTP 409로 뭉개 서비스 의미를 잃는다
- lock timeout이나 pool wait를 already exists처럼 사용자에게 말해 winner가 있는지 없는지 혼동시킨다
- deadlock과 40001을 클라이언트 재시도 책임으로 넘기고 서버 내부 bounded retry 기회를 놓친다
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- database/three-bucket-terms-common
- database/insert-if-absent-retry-outcome-guide
next_docs:
- database/duplicate-key-fresh-read-classifier-mini-card
- database/busy-fail-fast-vs-one-short-retry-card
- database/spring-jpa-lock-timeout-deadlock-exception-mapping
linked_paths:
- contents/database/idempotency-key-status-contract-examples.md
- contents/database/three-bucket-terms-common-card.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/duplicate-key-fresh-read-classifier-mini-card.md
- contents/database/lock-duplicate-three-bucket-mini-bridge.md
- contents/database/spring-jpa-lock-timeout-deadlock-exception-mapping.md
- contents/database/busy-fail-fast-vs-one-short-retry-card.md
confusable_with:
- database/db-signal-service-result-http-bridge
- database/db-error-signal-beginner-result-language-mini-card
- database/busy-fail-fast-vs-one-short-retry-card
- database/insert-if-absent-retry-outcome-guide
forbidden_neighbors: []
expected_queries:
- duplicate key와 busy를 service label로 먼저 나눈 뒤 HTTP 200 201 409 429 503을 고르는 기준은 뭐야?
- DuplicateKeyException은 같은 idempotent 요청이면 200 201 replay가 될 수 있고 다른 payload면 409인 이유를 알려줘
- lock timeout은 already exists가 아니라 busy라서 503 또는 429로 매핑하는 기준을 설명해줘
- deadlock과 PostgreSQL 40001은 HTTP 전에 서버 내부 bounded retry를 먼저 하는 이유가 뭐야?
- PROCESSING winner row를 fresh read했을 때 202 Accepted로 표현할 수 있는 경우를 알려줘
contextual_chunk_prefix: |
  이 문서는 Duplicate Key vs Busy Response Mapping beginner chooser로, duplicate key는 already exists,
  lock timeout/pool wait는 busy, deadlock/40001은 retryable로 service outcome을 나눈 뒤
  idempotent replay, conflict, 429/503, internal retry HTTP response를 선택하는 기준을 설명한다.
---
# Duplicate Key vs Busy Response Mapping

> 한 줄 요약: 초보자는 DB 예외를 바로 HTTP로 번역하지 말고, 먼저 `already exists` / `busy` / `retryable` 서비스 라벨로 바꾼 뒤 그다음 `200`/`202`/`409`/`429`/`503` 같은 응답 선택으로 내려가면 덜 흔들린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Idempotency Key Status Contract Examples](./idempotency-key-status-contract-examples.md)
- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [`busy`는 언제 즉시 실패하고, 언제 한 번만 짧게 재시도할까?](./busy-fail-fast-vs-one-short-retry-card.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: duplicate key vs busy response mapping, duplicate key http response, lock timeout http response, deadlock http response, serialization failure http response, service layer outcome mapping, spring duplicatekeyexception response, mysql 1062 1205 1213 response, postgresql 23505 55p03 40p01 40001 response, beginner api error mapping db concurrency, already exists busy retryable http choice, duplicate key conflict or success, busy 429 503 choice, retryable internal retry http response, duplicate key vs busy response mapping basics

## 먼저 멘탈모델

초보자가 가장 많이 헷갈리는 지점은 이것이다.

- DB는 `duplicate key`, `lock timeout`, `deadlock`, `40001`처럼 말한다
- 서비스 레이어는 `already exists`, `busy`, `retryable`처럼 말한다
- HTTP는 `200`, `202`, `409`, `429`, `503`처럼 말한다

즉 **한 번에 번역하지 말고 두 단계로 번역**해야 한다.

1. DB 신호 -> 서비스 라벨
2. 서비스 라벨 -> HTTP 응답

짧게 외우면:

- `duplicate key` = 이미 승자가 있다
- `lock timeout` = 아직 막혀 있어 결과를 못 봤다
- `deadlock` / `serialization failure` = 이번 시도만 버리고 새로 시작해야 한다

## 30초 연결표

| DB 신호 | 서비스 라벨 | 서비스 기본 동작 | HTTP 기본 선택 |
|---|---|---|---|
| MySQL `1062`, PostgreSQL `23505`, `DuplicateKeyException` | `already exists` | fresh read로 기존 winner 의미 확인 | 같은 요청 재전송이면 `200`/`201` replay, 다른 payload면 `409 Conflict` |
| MySQL `1205`, PostgreSQL `55P03`, `lock timeout` | `busy` | 즉시 무한 retry 말고 혼잡으로 분류 | 보통 `503 Service Unavailable`, 의도적 per-key 혼잡 제어면 `429 Too Many Requests` |
| MySQL `1213`, PostgreSQL `40P01`, `deadlock` | `retryable` | 서버 안에서 bounded retry | retry 성공 시 정상 응답, retry 예산 소진 시 보통 `503` |
| PostgreSQL `40001`, `CannotSerializeTransactionException` | `retryable` | 서버 안에서 whole-transaction retry | retry 성공 시 정상 응답, retry 예산 소진 시 보통 `503` |

이 표의 핵심은 하나다.

> `duplicate key`와 `busy`는 둘 다 "실패처럼 보이는 신호"지만, HTTP에서 같은 `409`로 뭉개면 의미가 섞인다.

## 왜 서비스 라벨을 먼저 거치나

예를 들어 `lock timeout`을 바로 `409 Conflict`로 보내면 초보자가 이런 오해를 하기 쉽다.

- "이미 같은 데이터가 있어서 막혔구나"
- "duplicate key랑 같은 종류구나"

하지만 `lock timeout`은 보통 **이미 존재함을 확인한 것**이 아니라 **아직 결론을 못 본 것**이다.

반대로 `duplicate key`는 이미 winner가 있는 신호라서, 같은 요청 재전송이라면 `409`보다 **기존 성공 replay**가 더 자연스러울 수 있다.

그래서 먼저 이렇게 닫는다.

- 이미 winner가 보이면 `already exists`
- 아직 결론을 못 보면 `busy`
- 이번 시도만 버리면 되면 `retryable`

그다음에야 HTTP를 고른다.

## 입문: 서비스 라벨별 HTTP 선택

| 서비스 라벨 | 초보자용 질문 | 자주 쓰는 HTTP 선택 | 언제 그렇게 고르나 |
|---|---|---|---|
| `already exists` | "이미 있는 결과를 그대로 돌려줄 수 있나?" | `200 OK` / `201 Created` replay | 같은 멱등 요청이 이미 성공했고, 이전 결과를 재사용할 수 있을 때 |
| `already exists` | "같은 key를 다른 뜻으로 재사용했나?" | `409 Conflict` | 같은 idempotency key 또는 unique key를 다른 payload가 차지했을 때 |
| `busy` | "지금은 혼잡해서 잠깐 못 처리한 건가?" | `503 Service Unavailable` | DB lock 대기, pool 대기, 일시적 포화처럼 서버가 지금 못 받는 상황일 때 |
| `busy` | "이 경로를 일부러 짧게 거절하고 있나?" | `429 Too Many Requests` | 같은 key에 대한 짧은 중복 요청 억제, per-key throttling처럼 정책적으로 늦추는 경우 |
| `retryable` | "서버가 안에서 다시 시도할 수 있나?" | 우선 HTTP를 내보내지 않고 내부 retry | deadlock, serialization failure는 보통 서버가 먼저 2~3회 다시 시도한다 |
| `retryable` | "내부 retry 예산도 다 썼나?" | `503 Service Unavailable` | 최종적으로 이번 요청을 지금 처리하지 못했을 때 |

짧게 기억하면:

- `409`는 "이미 다른 의미가 확정됐다"
- `503`는 "지금 서버가 처리 못 한다"
- `429`는 "잠깐 천천히 와 달라"에 가깝다

`PROCESSING` / completed replay / hash-mismatch conflict를 헤더와 JSON body까지 포함해 한 장으로 보고 싶다면 [Idempotency Key Status Contract Examples](./idempotency-key-status-contract-examples.md)를 같이 보면 된다.

## 가장 작은 예시

결제 API가 `idempotency_key`를 받는다고 하자.

| 장면 | 서비스 라벨 | HTTP 예시 | 왜 이렇게 보나 |
|---|---|---|---|
| 같은 key, 같은 payload로 재전송했고 이미 성공 row가 있다 | `already exists` | `200 OK` 또는 기존 `201 Created` replay | 이미 끝난 같은 요청이다 |
| 같은 key인데 payload가 다르다 | `already exists` | `409 Conflict` | 같은 열쇠를 다른 뜻으로 썼다 |
| 선행 요청이 row를 오래 잡아 후행 요청이 `lock timeout` | `busy` | `503 Service Unavailable` + 필요 시 `Retry-After` | winner를 확정하지 못한 혼잡 상태다 |
| deadlock victim이 나왔지만 서버 내부 2번째 retry에서 성공 | `retryable` | 최종 `201 Created` | 클라이언트는 deadlock을 몰라도 된다 |
| PostgreSQL `40001`이 3번 연속 나서 내부 retry 예산 소진 | `retryable` | `503 Service Unavailable` | 서버가 새 snapshot 재시도를 다 써도 못 끝냈다 |

## Spring 서비스 코드에서의 역할 분리

초보자는 아래 역할만 먼저 고정하면 된다.

| 층 | 해야 할 일 |
|---|---|
| repository/DB | `DuplicateKeyException`, `CannotAcquireLockException`, `CannotSerializeTransactionException` 같은 신호를 올린다 |
| service classifier | root SQL 코드까지 보고 `already exists` / `busy` / `retryable`로 번역한다 |
| retry envelope | `retryable`만 새 트랜잭션으로 2~3회 다시 시도한다 |
| controller/adaptor | 마지막 서비스 라벨을 HTTP `200`/`202`/`409`/`429`/`503`로 번역한다 |

핵심은 이것이다.

- service는 **의미 라벨**을 만든다
- controller는 **채널 표현(HTTP)** 을 고른다

즉 `DuplicateKeyException`을 controller에서 바로 `409`로 박아 버리면, 같은 요청 replay 기회를 잃기 쉽다.

## 초급자용 기본 매핑 표

| Spring/DB에서 보인 것 | 먼저 붙일 서비스 의미 | HTTP 기본값 | 흔한 대안 |
|---|---|---|---|
| `DuplicateKeyException` + winner row가 같은 요청 성공 | `already exists` | `200 OK` | `201 Created` replay |
| `DuplicateKeyException` + winner row가 다른 요청 의미 | `already exists` | `409 Conflict` | 없음 |
| `DuplicateKeyException` + winner row가 아직 `PROCESSING` | `busy` | `202 Accepted` | `409 in-progress`, `503` |
| `CannotAcquireLockException` + MySQL `1205` / PostgreSQL `55P03` | `busy` | `503 Service Unavailable` | `429 Too Many Requests` |
| deadlock (`1213` / `40P01`) | `retryable` | 우선 내부 retry | 실패 시 `503` |
| serialization failure (`40001`) | `retryable` | 우선 내부 retry | 실패 시 `503` |

여기서 `202 Accepted`가 나오는 자리는 중요하다.

- duplicate 자체가 `202`인 것이 아니다
- **fresh read 결과가 `PROCESSING`일 때만** "같은 요청이 아직 처리 중"이라는 뜻으로 `busy`를 `202`로 표현할 수 있다

## 자주 하는 오해

- "`duplicate key`면 무조건 `409 Conflict`다"
  - 아니다. 같은 멱등 요청 재전송이면 `200`/`201` replay가 더 자연스럽다.
- "`lock timeout`도 conflict니까 `409`다"
  - 보통 아니다. `lock timeout`은 winner를 확인한 것이 아니라 혼잡을 본 것이다.
- "`deadlock`이 나왔으면 클라이언트에게 바로 재시도하라고 하면 된다"
  - 보통 서버가 먼저 내부 bounded retry를 하는 편이 낫다.
- "`40001`은 클라이언트가 잘못 보낸 요청이다"
  - 아니다. 주로 동시성 snapshot 충돌이라 서버 안 재시도 후보에 가깝다.
- "`429`와 `503`은 아무거나 써도 된다"
  - 아니다. `429`는 정책적 rate limiting 쪽, `503`는 서버가 지금 처리 불가한 혼잡 쪽에 더 가깝다.

## 초보자용 한 줄 규칙

1. `duplicate key`는 먼저 winner read를 하고, 같은 요청이면 replay를 우선 검토한다.
2. `lock timeout`은 `409`보다 `busy`로 읽고, 보통 `503` 쪽에서 시작한다.
3. `deadlock`과 `40001`은 HTTP 전에 서버 내부 retry를 먼저 붙인다.
4. HTTP는 DB 예외 이름이 아니라 서비스 의미 라벨에서 고른다.

## 다음에 이어서 볼 문서

- duplicate 뒤 fresh read 분기를 더 자세히 보면 [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- `busy`에서 `503`와 짧은 1회 retry를 어떻게 나누는지 보려면 [`busy`는 언제 즉시 실패하고, 언제 한 번만 짧게 재시도할까?](./busy-fail-fast-vs-one-short-retry-card.md)
- Spring/JPA 표면 예외와 root SQL 코드 차이를 보려면 [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)

## 한 줄 정리

초보자는 DB 예외를 바로 HTTP로 번역하지 말고, 먼저 `already exists` / `busy` / `retryable` 서비스 라벨로 바꾼 뒤 그다음 `200`/`202`/`409`/`429`/`503` 같은 응답 선택으로 내려가면 덜 흔들린다.
