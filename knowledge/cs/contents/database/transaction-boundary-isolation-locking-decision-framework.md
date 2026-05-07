---
schema_version: 3
title: Transaction Boundary, Isolation, and Locking Decision Framework
concept_id: database/transaction-boundary-isolation-locking-framework
canonical: true
category: database
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- transaction-boundary
- isolation-level
- locking
- consistency
- decision-framework
aliases:
- transaction boundary
- isolation level selection
- locking strategy
- optimistic lock
- pessimistic lock
- serializable
- invariant protection
- select for update
- contention control
- backend consistency framework
symptoms:
- transaction boundary, isolation level, locking strategy를 한 번에 섞어서 판단하고 있어
- 같이 commit/rollback해야 할 상태 변화와 외부 side effect를 구분해야 해
- constraint, atomic SQL, optimistic lock, pessimistic lock, advisory lock, serializable 중 무엇을 고를지 결정해야 해
intents:
- comparison
- design
- deep_dive
prerequisites:
- database/transaction-isolation-locking
- database/transaction-boundary-external-io-checklist
next_docs:
- database/queue-consumer-transaction-boundaries
- database/compare-and-swap-vs-pessimistic-locks
- database/advisory-locks-vs-row-locks
linked_paths:
- contents/database/transaction-isolation-locking.md
- contents/database/queue-consumer-transaction-boundaries.md
- contents/database/compare-and-swap-vs-pessimistic-locks.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/advisory-locks-vs-row-locks.md
- contents/design-pattern/aggregate-boundary-vs-transaction-boundary.md
- contents/spring/spring-service-layer-transaction-boundary-patterns.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
confusable_with:
- database/transaction-boundary-external-io-checklist
- database/compare-and-swap-vs-pessimistic-locks
- database/advisory-locks-vs-row-locks
- database/transaction-isolation-locking
forbidden_neighbors: []
expected_queries:
- 트랜잭션 경계, 격리수준, 락 전략을 어떤 순서로 결정해야 해?
- 함께 실패해야 하는 상태 변화만 transaction boundary에 넣는다는 기준을 예시로 설명해줘
- READ COMMITTED, REPEATABLE READ, SERIALIZABLE은 막아야 할 anomaly 기준으로 어떻게 고르나?
- optimistic lock, pessimistic lock, constraint, atomic SQL, advisory lock은 경합 패턴에 따라 어떻게 선택해?
- 외부 API 호출이 있으면 isolation이나 lock choice보다 boundary choice를 먼저 봐야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 transaction boundary, isolation level, locking strategy를 invariant, anomaly, contention/retry cost 기준으로 고르는 advanced chooser다.
  optimistic vs pessimistic lock, serializable, select for update, advisory lock, boundary decision framework 질문이 본 문서에 매핑된다.
---
# Transaction Boundary, Isolation, and Locking Decision Framework

> 한 줄 요약: 트랜잭션 경계는 "함께 실패해야 하는 상태 변화"로 정하고, 격리수준은 "막아야 할 이상 현상"으로 정하고, 락 전략은 "충돌 비용을 대기와 재시도 중 어디에 둘지"로 고른다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
> - [Queue Consumer Transaction Boundaries](./queue-consumer-transaction-boundaries.md)
> - [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
> - [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
> - [Advisory Locks와 Row Locks](./advisory-locks-vs-row-locks.md)
> - [Aggregate Boundary vs Transaction Boundary](../design-pattern/aggregate-boundary-vs-transaction-boundary.md)
> - [Spring Service-Layer Transaction Boundary Patterns](../spring/spring-service-layer-transaction-boundary-patterns.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)

retrieval-anchor-keywords: transaction boundary, isolation level selection, locking strategy, optimistic lock, pessimistic lock, serializable, invariant protection, select for update, contention control, backend consistency

## 핵심 개념

백엔드에서 동시성 설계는 보통 세 가지 질문으로 나뉜다.

- 무엇을 한 번에 commit/rollback해야 하는가
- 어떤 이상 현상까지 허용할 수 없는가
- 경쟁이 났을 때 기다리게 할지, 실패시키고 재시도하게 할지

이 세 질문을 섞으면 문제가 생긴다.

- 트랜잭션 경계를 서비스 메서드 크기대로 잡아 lock을 오래 쥔다
- 격리수준을 습관적으로 높여 serialization failure만 늘린다
- lock 전략 없이 `FOR UPDATE`를 붙여 병목을 만든다

핵심은 다음 순서다.

1. 불변식과 실패 단위를 먼저 정한다
2. 그 불변식을 지키는 최소 transaction boundary를 자른다
3. 필요한 anomaly만 막는 isolation을 고른다
4. 경합 패턴에 맞게 lock, CAS, constraint, advisory lock을 선택한다

## 깊이 들어가기

### 1. transaction boundary는 "같이 실패해야 하는 상태 변화"만 묶는다

좋은 boundary는 비즈니스 불변식을 보호하는 최소 범위다.

같이 묶어야 하는 것:

- 주문 상태를 `PAID`로 바꾸는 일과 결제 레코드 확정
- 재고 차감과 예약 row 생성
- inbox dedup insert와 이벤트 처리 결과 저장

분리해야 하는 것:

- 알림 발송
- 검색 인덱싱
- 외부 API 호출 결과 대기
- 분석 로그 적재

트랜잭션 안에 오래 걸리는 I/O가 들어가면 boundary는 정합성보다 대기를 보존하는 장치가 된다.  
짧고 결정적인 DB 상태 변화만 안에 두고, 나머지는 outbox나 후속 작업으로 빼는 편이 안전하다.

### 2. isolation level은 "막아야 하는 이상 현상"으로 고른다

격리수준은 높을수록 좋은 옵션이 아니라, 허용할 수 없는 anomaly를 지정하는 옵션이다.

- `READ COMMITTED`
  - 최신 커밋 데이터만 보면 충분하고, 최종 write에서 조건부 update나 constraint로 검증할 수 있을 때
- `REPEATABLE READ`
  - 같은 transaction 안에서 여러 번 읽은 기준이 흔들리면 안 되거나, snapshot 일관성이 중요한 계산일 때
- `SERIALIZABLE`
  - 범위 부재나 집합 불변식 때문에 "동시에 실행되면 안 되는 의사결정" 자체를 막아야 할 때

중요한 감각은 "읽기 일관성"과 "정합성 보장 수단"을 분리하는 것이다.  
단일 row 재고 차감은 꼭 serializable이 아니라도, 조건부 update나 row lock으로 충분할 수 있다.  
반대로 "이 시간대 예약 합계가 100명을 넘으면 안 된다"처럼 범위나 집합 규칙은 낮은 isolation만으로는 구멍이 남기 쉽다.

### 3. lock strategy는 경합 빈도와 retry 비용으로 고른다

충돌을 다루는 방법은 크게 네 가지다.

- 제약조건 또는 원자적 SQL
  - 가능하면 가장 먼저 고려한다
  - `UNIQUE`, `CHECK`, `UPDATE ... WHERE stock > 0`
- optimistic lock 또는 CAS
  - 충돌이 드물고 재시도가 싸면 유리하다
  - 사용자 프로필, 설정 수정, 비교적 느슨한 관리 화면
- pessimistic row 또는 range lock
  - 충돌이 잦고 한 번의 중복 성공이 치명적이면 유리하다
  - hot SKU 재고, 좌석 선점, 순서가 중요한 상태 전이
- advisory lock
  - row 정합성보다 "같은 작업의 중복 실행"을 막고 싶을 때 맞다
  - 배치, 테넌트별 job, 마이그레이션 entry gate

판단 기준은 단순하다.

- 충돌이 낮고 retry가 안전한가 -> optimistic
- 충돌이 높고 retry가 비싸거나 사용자 체감 실패가 큰가 -> pessimistic
- 데이터 자체보다 작업 단위를 직렬화해야 하는가 -> advisory
- SQL 한 문장이나 constraint로 invariant를 끝낼 수 있는가 -> lock보다 먼저 constraint나 atomic SQL

### 4. constraint와 atomic SQL이 있으면, isolation을 올리기 전에 먼저 쓴다

시니어 관점에서 자주 하는 실수는 "정합성이 중요하니 isolation부터 높이자"다.  
하지만 많은 문제는 더 단순한 장치로 끝난다.

- 중복 예약 금지 -> `UNIQUE(resource_id, slot)`
- 음수 재고 금지 -> `UPDATE ... SET stock = stock - 1 WHERE sku = ? AND stock > 0`
- lost update 방지 -> `version` column 기반 CAS

이 방식의 장점은 명확하다.

- transaction이 짧다
- lock 범위가 줄어든다
- retry 정책이 단순해진다

반대로 "읽고 판단하고 애플리케이션에서 update" 흐름을 그대로 두면, 격리수준을 높여도 경합 비용이 커진다.

### 5. 외부 호출이 들어가면 boundary를 나누고 멱등성을 같이 설계한다

결제, 메일, 브로커 ack, 다른 서비스 호출은 DB transaction과 수명이 다르다.

이때 필요한 원칙은 다음이다.

- 외부 호출 전후에 잡고 있는 DB lock을 최소화한다
- commit과 side effect 순서를 명시한다
- 재시도 시 중복 부작용이 없도록 idempotency key를 둔다
- queue consumer라면 보통 `commit -> ack` 순서를 기본으로 둔다

긴 외부 호출을 트랜잭션 안에 넣으면 isolation이나 lock choice보다 먼저 boundary choice가 틀린 것이다.

### 6. 실무용 결정 순서

다음 질문을 위에서 아래로 내려가며 보면 선택이 빨라진다.

1. 어떤 불변식이 깨지면 안 되는가
2. 그 불변식을 DB constraint나 원자적 SQL로 직접 표현할 수 있는가
3. 판단이 단일 row인지, 범위나 집합인지
4. 충돌이 드문가, 자주 나는가
5. 실패 시 재시도가 싼가, 비싼가
6. 외부 I/O 없이 짧게 끝낼 수 있는가

간단한 결정 매핑은 다음처럼 볼 수 있다.

| 상황 | 우선 선택 | 이유 | 경계 신호 |
|------|------|------|------|
| 단일 row 조건부 변경 | 짧은 tx + atomic update + `READ COMMITTED` | SQL 한 문장으로 invariant를 지킬 수 있다 | 재고, 카운터 |
| 충돌 적고 재시도 쉬움 | optimistic lock + retry | lock 대기보다 재시도가 싸다 | 프로필, 설정 수정 |
| 충돌 많고 중복 성공이 치명적 | pessimistic row lock | 실패보다 queueing이 낫다 | hot row, 좌석 선점 |
| 범위나 부재 기반 규칙 | range lock, constraint, serializable 검토 | point lock만으로 구멍이 남는다 | 예약 가능 슬롯, 집합 상한 |
| 긴 workflow entry 직렬화 | advisory lock + 짧은 DB tx | 데이터보다 작업 단위를 보호한다 | 배치, 마이그레이션 |

## 실전 시나리오

### 시나리오 1. 플래시 세일 재고 차감

상품 하나를 두고 수천 요청이 몰린다.

추천 선택:

- transaction boundary
  - 재고 차감과 주문 예약 row 생성까지만 한 transaction으로 묶는다
  - 결제 승인, 알림, 이벤트 발행은 밖으로 뺀다
- isolation
  - 단일 SKU row라면 `READ COMMITTED` + 조건부 update로 충분한 경우가 많다
- locking
  - `UPDATE ... WHERE stock > 0`로 끝나면 explicit lock보다 atomic SQL이 낫다
  - hot row에서 후속 읽기와 검증이 필요하면 `FOR UPDATE`를 검토한다

틀린 선택 신호:

- lock wait timeout이 급증한다
- 외부 결제 대기 동안 재고 row를 잡고 있다
- 실패 재시도가 중복 주문을 만든다

### 시나리오 2. 사용자 프로필 또는 설정 수정

같은 사용자가 드물게 동시에 수정한다.

추천 선택:

- transaction boundary
  - 프로필 row와 audit row 정도만 짧게 묶는다
- isolation
  - 보통 `READ COMMITTED`
- locking
  - version column 기반 optimistic lock
  - 충돌 시 사용자에게 다시 시도를 안내하거나 자동 merge 정책을 둔다

여기서 pessimistic lock을 기본으로 두면, 얻는 안전보다 대기 비용이 더 클 수 있다.

### 시나리오 3. 좌석 예약이나 순번 선점

같은 자원을 두고 충돌이 잦고, 한 번의 중복 성공이 치명적이다.

추천 선택:

- transaction boundary
  - 좌석 점유 확인과 예약 확정 row 생성까지 묶는다
- isolation
  - 범위나 부재 확인이면 constraint나 `SERIALIZABLE`을 검토한다
- locking
  - 특정 좌석 row가 있으면 pessimistic lock
  - "비어 있는 첫 좌석"처럼 absence 기반이면 unique constraint나 범위 보호가 더 중요하다

핵심은 row 하나를 잠그는 것만으로 충분한지, 아니면 "존재하지 않음" 자체를 보호해야 하는지 구분하는 것이다.

### 시나리오 4. queue consumer의 상태 전이 처리

메시지 하나를 받아 주문 상태를 `SHIPPED`로 바꾸고 이벤트를 기록한다.

추천 선택:

- transaction boundary
  - inbox dedup insert, 주문 상태 전이, outbox insert를 한 transaction으로 묶는다
- isolation
  - 대부분은 `READ COMMITTED` 또는 엔진 기본값으로 충분하다
- locking
  - 주문 row 상태 전이가 경쟁하면 row lock 또는 version check
  - broker ack는 commit 뒤에 보낸다

여기서 핵심 문제는 isolation보다 boundary다.  
ack를 먼저 보내거나 외부 호출을 트랜잭션 안에 넣으면 락 전략을 잘 골라도 정합성이 흔들린다.

## 코드로 보기

### 1. atomic SQL이 우선인 경우

```sql
UPDATE inventory
SET stock = stock - 1
WHERE sku = :sku
  AND stock > 0;
```

영향받은 row 수가 `1`이면 성공, `0`이면 품절로 본다.  
이 패턴은 짧은 transaction과 잘 맞는다.

### 2. 충돌이 잦아 pessimistic lock이 필요한 경우

```sql
START TRANSACTION;

SELECT status
FROM seats
WHERE concert_id = :concertId
  AND seat_no = :seatNo
FOR UPDATE;

UPDATE seats
SET status = 'HELD'
WHERE concert_id = :concertId
  AND seat_no = :seatNo;

COMMIT;
```

같은 seat에 대한 경쟁이 매우 뜨겁고, 중복 성공이 치명적일 때 쓴다.

### 3. 충돌이 드물어 optimistic lock이 맞는 경우

```sql
UPDATE user_profile
SET nickname = :nickname,
    version = version + 1
WHERE user_id = :userId
  AND version = :expectedVersion;
```

실패 시 최신 상태를 다시 읽고 재시도하거나 사용자에게 충돌을 노출한다.

### 4. 빠른 판단을 위한 체크리스트

```text
if invariant fits in constraint or atomic SQL:
    keep transaction short
    prefer READ COMMITTED or engine default
elif conflicts are rare and retry is safe:
    use optimistic lock + retry
elif conflicts are frequent and duplicate success is unacceptable:
    use pessimistic row or range lock
elif invariant depends on absence, range, or set-wide totals:
    consider unique or range protection, or SERIALIZABLE
if workflow includes remote I/O:
    split boundary and move side effects out with idempotency or outbox
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| short tx + atomic SQL | 가장 단순하고 빠르다 | SQL로 invariant를 표현해야 한다 | 재고, 카운터, 중복 방지 |
| optimistic lock + retry | 락 대기가 적다 | 충돌 시 재시도와 UX 설계가 필요하다 | 충돌이 낮은 CRUD |
| pessimistic row lock | 중복 성공을 강하게 막는다 | lock wait, deadlock, pool 압박이 생긴다 | hot row, 좌석, 순번 |
| serializable 또는 강한 범위 보호 | 집합 규칙까지 강하게 지킨다 | serialization failure와 성능 비용이 크다 | 범위, 부재 기반 불변식 |
| advisory lock | 작업 단위 직렬화가 쉽다 | 데이터 정합성을 직접 보장하진 못한다 | 배치, 테넌트 작업, 리더 작업 |

좋은 설계는 가장 강한 장치를 쓰는 설계가 아니라, 불변식을 만족하는 가장 좁고 짧은 장치를 쓰는 설계다.

## 꼬리질문

> Q: transaction boundary와 isolation level 중 무엇을 먼저 정해야 하나요?
> 의도: 문제를 어떤 레이어에서 정의하는지 확인
> 핵심: 먼저 "같이 실패해야 하는 상태 변화"를 정하고, 그다음 필요한 anomaly만 막는 isolation을 고른다

> Q: 왜 serializable을 기본값으로 두지 않나요?
> 의도: 강한 격리와 운영 비용의 균형을 이해하는지 확인
> 핵심: 많은 문제는 constraint, atomic SQL, row lock으로 더 싸게 해결되고, serializable은 serialization failure와 비용을 늘린다

> Q: optimistic lock과 pessimistic lock은 어떤 기준으로 나누나요?
> 의도: 경합 빈도와 retry 비용을 함께 보는지 확인
> 핵심: 충돌이 드물고 retry가 싸면 optimistic, 충돌이 잦고 중복 성공이 치명적이면 pessimistic이 맞다

> Q: 외부 API 호출이 길어질 때 가장 먼저 의심해야 할 것은 무엇인가요?
> 의도: 격리수준보다 boundary 설계가 먼저라는 점을 이해하는지 확인
> 핵심: lock 전략보다 transaction boundary가 너무 넓은지부터 본다

## 한 줄 정리

트랜잭션 경계는 불변식 보호 범위로, 격리수준은 막아야 할 이상 현상으로, 락 전략은 경합 비용의 지불 방식으로 고르면 선택이 흔들리지 않는다.
