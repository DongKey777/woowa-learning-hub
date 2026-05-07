---
schema_version: 3
title: 멱등성 키와 중복 방지
concept_id: database/idempotency-key-and-deduplication
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 89
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- idempotency-key-deduplication
- retry-safe-api
- unique-key-arbitration
aliases:
- idempotency key and deduplication
- idempotency key
- duplicate suppression
- retry safe API
- processed event table
- request fingerprint
- unique key arbitration
- pending row recovery
- 멱등성 키
- 중복 요청 방지
symptoms:
- 네트워크 재시도나 메시지 redelivery가 생기면 트랜잭션만으로 중복 side effect가 막힌다고 오해한다
- idempotency key와 business unique key를 같은 값으로 취급해 재시도 식별자와 도메인 식별자를 구분하지 못한다
- PENDING PROCESSING SUCCESS 상태 계약 없이 insert-if-absent만 두고 timeout 이후 복구 흐름을 설계하지 않는다
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- database/transaction-basics
- database/unique-vs-idempotency-key-vs-pending-row-recovery-decision-guide
next_docs:
- database/pending-row-recovery-primer
- database/duplicate-suppression-windows
- database/idempotent-transaction-retry-envelopes
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
linked_paths:
- contents/database/pending-row-recovery-primer.md
- contents/database/upsert-contention-unique-index-locking.md
- contents/database/mysql-on-duplicate-key-update-safety-primer.md
- contents/database/transactional-inbox-dedup-design.md
- contents/database/exactly-once-myths-db-queue.md
- contents/database/cdc-replay-verification-idempotency-runbook.md
- contents/database/cdc-gap-repair-reconciliation-playbook.md
- contents/database/duplicate-suppression-windows.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
- contents/system-design/replay-repair-orchestration-control-plane-design.md
- contents/security/token-misuse-detection-replay-containment.md
- contents/security/replay-store-outage-degradation-recovery.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/proxy-retry-budget-discipline.md
confusable_with:
- database/duplicate-suppression-windows
- database/pending-row-recovery-primer
- database/transactional-inbox-dedup-design
- database/exactly-once-myths-db-queue
- system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
forbidden_neighbors: []
expected_queries:
- idempotency key는 retry safe API에서 어떤 중복 요청을 막아?
- 멱등성 키와 business unique key는 왜 항상 같은 값이 아니야?
- 같은 key 같은 payload와 같은 key 다른 payload는 각각 어떻게 처리해야 해?
- PENDING row가 남은 뒤 timeout이 나면 재실행보다 recovery를 먼저 봐야 하는 이유가 뭐야?
- 트랜잭션은 원자성을 보장하지만 요청 재전송 중복을 왜 없애주지 못해?
contextual_chunk_prefix: |
  이 문서는 idempotency key와 deduplication deep dive로, 네트워크 retry,
  API gateway 재전송, message redelivery에서 같은 side effect가 여러 번
  실행되지 않도록 request fingerprint, unique key arbitration, pending row
  recovery, processed event table, replay-safe response를 설계한다.
---
# 멱등성 키와 중복 방지

**난이도: 🔴 Advanced**

> 네트워크는 한 번만 보내도, 서버는 두 번 받을 수 있다. 이 문서는 그 차이를 다루기 위한 정리다.

관련 문서: [PENDING Row Recovery Primer](./pending-row-recovery-primer.md), [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md), [MySQL `ON DUPLICATE KEY UPDATE` Safety Primer](./mysql-on-duplicate-key-update-safety-primer.md), [Transactional Inbox와 Dedup 설계](./transactional-inbox-dedup-design.md), [Exactly-Once Myths in DB Queue](./exactly-once-myths-db-queue.md), [CDC Replay Verification, Idempotency, and Acceptance Runbook](./cdc-replay-verification-idempotency-runbook.md), [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md), [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md), [Replay / Repair Orchestration Control Plane 설계](../system-design/replay-repair-orchestration-control-plane-design.md), [Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md), [Replay Store Outage / Degradation Recovery](../security/replay-store-outage-degradation-recovery.md), [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md), [Proxy Retry Budget Discipline](../network/proxy-retry-budget-discipline.md)
retrieval-anchor-keywords: idempotency key, duplicate suppression, request hash, upsert, unique key arbitration, processed event table, retry safe API, cdc replay dedup, replay-safe consumer, repair window, pending row recovery, processing row takeover, idempotency lease heartbeat

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [멱등성이란](#멱등성이란)
- [중복이 생기는 지점](#중복이-생기는-지점)
- [멱등성 키 설계](#멱등성-키-설계)
- [중복 방지 구현 패턴](#중복-방지-구현-패턴)
- [실무에서 자주 놓치는 것](#실무에서-자주-놓치는-것)
- [체크리스트](#체크리스트)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 왜 이 문서가 필요한가

중복 요청은 생각보다 자주 발생한다.

- 클라이언트 재시도
- 네트워크 timeout
- 응답은 실패했지만 서버는 성공한 경우
- 메시지 소비 재시도

문제는 같은 요청이 두 번 들어와도 비즈니스적으로는 한 번만 반영돼야 하는 경우가 많다는 점이다. 결제, 적립, 쿠폰 발급, 주문 생성은 대표적이다.

트랜잭션은 DB 내부의 원자성을 보장하지만, 요청 재전송 자체를 없애주지는 못한다. 그래서 **멱등성 키**와 **중복 방지 저장소**를 같이 설계해야 한다.

---

## 멱등성이란

멱등성은 같은 요청을 여러 번 실행해도 결과가 같아야 한다는 뜻이다.

예를 들어:

- `POST /payments`를 두 번 보내도 결제는 한 번만 생성돼야 한다
- `POST /orders`를 재시도해도 주문 번호는 하나만 만들어져야 한다

이때 중요한 것은 “응답이 같은가”보다 “상태 변화가 한 번만 일어나는가”다.

---

## 중복이 생기는 지점

중복은 보통 아래 지점에서 생긴다.

1. 클라이언트가 응답을 못 받아 재시도한다.
2. API Gateway나 LB가 타임아웃 후 재전송을 유도한다.
3. 메시지 브로커가 at-least-once delivery를 제공한다.
4. 배치나 스케줄러가 같은 작업을 중복 실행한다.

즉 중복은 예외가 아니라 기본값에 가깝다.

---

## 멱등성 키 설계

멱등성 키는 “같은 의미의 요청”을 식별하는 값이다.

보통 다음 방식 중 하나를 쓴다.

- 클라이언트가 UUID를 생성해서 보낸다
- 서버가 요청의 의미를 해석해 고유 키를 만든다
- 외부 연동에서는 `provider_request_id` 같은 외부 키를 저장한다

설계할 때는 다음을 구분해야 한다.

- 요청 식별자: 재시도 구분용
- 비즈니스 식별자: 주문 번호, 결제 번호 같은 실제 도메인 키

둘이 항상 같은 것은 아니다. 같은 주문에 대해 여러 결제 시도가 있을 수 있고, 반대로 같은 결제 시도는 여러 번 재전송될 수 있다.

## 상태 이름을 먼저 고정하자

초보자 문서에서 가장 자주 섞이는 단어가 `PENDING`, `PROCESSING`, `SUCCESS`/`SUCCEEDED`다.

이 저장소에서는 beginner 기준으로 아래처럼 읽으면 헷갈림이 줄어든다.

| 이름 | 어디에서 쓰나 | 초보자 해석 |
|---|---|---|
| `PENDING` | idempotency row 저장 상태 | 선점은 끝났지만 최종 성공 결과는 아직 저장 전 |
| `PROCESSING` | 중복 요청에 대한 API 응답 표현 | 기존 `PENDING` row가 아직 살아 있어서 새 실행을 막는 안내 |
| `SUCCEEDED` | idempotency row 저장 상태 | 같은 key의 최종 성공 결과가 이미 저장됨 |

짧은 흐름은 이렇다.

- 첫 winner는 보통 row를 `PENDING`으로 만든다
- 뒤 요청은 그 `PENDING` row를 보고 `PROCESSING` 또는 `in-progress` 응답을 받을 수 있다
- 최종 성공이 저장되면 row는 `SUCCEEDED`가 되고, 같은 요청 재전송에는 replay 응답을 준다

아래 예시도 이 용어에 맞춰 읽는 편이 beginner에게 가장 덜 헷갈린다.

---

## 중복 방지 구현 패턴

### 1. 멱등성 키 테이블

가장 흔한 방식은 별도 테이블에 요청을 선점하는 것이다.

예:

```sql
CREATE TABLE idempotency_keys (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    idem_key VARCHAR(100) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_body TEXT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_idem_key (idem_key)
);
```

흐름은 보통 이렇다.

1. `idem_key`로 먼저 조회한다.
2. 없으면 insert한다.
3. 처리 중이면 이전 응답이나 처리 중 상태를 반환한다.
4. 성공하면 결과와 상태를 저장한다.

핵심은 **중복을 후처리로 지우지 말고, 처음부터 선점해서 막는 것**이다.

### 2. 유니크 제약으로 선점

비즈니스 테이블에 직접 유니크 제약을 두는 방식도 있다.

예:

- `orders.external_order_id UNIQUE`
- `payments.idempotency_key UNIQUE`

이 방식은 단순하다. 같은 키가 다시 들어오면 insert가 실패하므로 중복을 막을 수 있다.

다만 실패했을 때 어떤 응답을 줄지, 이미 성공한 요청인지 어떻게 판별할지 정책이 필요하다.
구현을 `upsert`로 단순화하더라도, "최초 값을 보존할지", "다른 payload면 충돌로 볼지" 같은 병합 규칙은 별도로 정해야 한다.

### 3. 상태 전이 기반 중복 방지

상태값을 두고 허용되는 전이만 인정하는 방식도 있다.

예:

- `PENDING -> SUCCEEDED`
- `PENDING -> FAILED`

이미 `SUCCEEDED`인 요청은 다시 성공 처리하지 않는다.

이 방식은 단순한 중복 방지 이상으로, 도메인 상태를 명확히 관리할 때 유용하다.

---

## 실무에서 자주 놓치는 것

### 1. 요청 본문이 달라졌는데 키만 같다

같은 `idem_key`로 다른 금액이나 다른 주문을 보내면 위험하다.
그래서 보통 `request_hash`를 함께 저장하고, 같은 키인데 본문이 달라지면 거절한다.

### 2. 성공 응답만 캐시하고 실패는 무시한다

실패도 의미가 있다. 예를 들어 외부 결제사 timeout 후 내부는 성공했을 수 있다. 그래서 단순 성공/실패보다 `PENDING`, `SUCCEEDED`, `FAILED` 같은 저장 상태와, 필요하면 호출자에게 보여 주는 `PROCESSING` 응답 표현을 함께 설계해야 한다.

### 3. TTL이 없다

멱등성 키를 영원히 저장하면 테이블이 불필요하게 커진다. 반대로 너무 빨리 지우면 재시도 구간을 못 막는다.

보통은 비즈니스 특성에 맞게 보존 기간을 정한다.

### 4. 트랜잭션 범위가 너무 넓다

멱등성 키 선점, 도메인 저장, 외부 호출, 응답 저장을 하나의 긴 트랜잭션에 넣으면 락과 커넥션 점유가 길어진다.

외부 호출은 가급적 트랜잭션 밖으로 빼고, DB에는 상태 전이만 남기는 편이 안전하다.

### 5. replay는 API retry보다 훨씬 늦게 다시 온다

HTTP 재시도는 보통 수초~수분 안에 끝나지만, CDC replay나 queue redrive는 몇 시간 또는 며칠 뒤에도 같은 작업을 다시 밀어 넣을 수 있다.

그래서 replay-safe idempotency는 단순히 "중복 요청을 잠깐 막는다"보다 더 넓게 봐야 한다.

- dedup 보존 기간이 binlog/WAL retention 및 repair window보다 짧지 않아야 한다
- `processed_event`와 consumer checkpoint가 서로 어긋나지 않아야 한다
- 같은 `event_id`라도 다른 repair run에서 재평가 중인지 알 수 있도록 `operation_id`나 `repair_run_id`를 남기는 편이 좋다
- 외부 side effect는 API idempotency와 별도 key space를 가져야 한다

즉 replay를 운영하는 시스템에서는 멱등성 저장소가 API middleware 부품이 아니라, **재처리와 복구를 견디는 운영 계약**이 된다.

---

## 체크리스트

- 이 API는 재시도될 수 있는가?
- 같은 요청을 여러 번 받아도 결과가 같아야 하는가?
- 중복 판별 키는 무엇인가?
- 요청 본문이 다르지만 키가 같은 경우를 어떻게 처리할 것인가?
- 성공, 실패, 처리 중 상태를 구분할 것인가?
- 멱등성 키 보존 기간은 얼마인가?
- CDC replay나 DLQ redrive가 늦게 들어와도 dedup window가 충분한가?
- 외부 시스템 호출을 트랜잭션 안에 넣고 있지 않은가?

---

## 시니어 관점 질문

- 멱등성은 DB 제약으로 해결할 수 있는가, 아니면 애플리케이션 상태 관리가 필요한가?
- 중복 요청과 진짜 재처리를 어떻게 구분할 것인가?
- 실패 응답도 저장해야 하는가?
- 멱등성 키를 어디까지 보존할 것인가?
- replay-safe consumer라면 dedup 기록과 checkpoint를 어떤 단위로 함께 검증할 것인가?
- 외부 호출 실패 후 재시도 시 정합성을 어떻게 유지할 것인가?
