---
schema_version: 3
title: Upsert Contention, Unique Index Arbitration, and Locking
concept_id: database/upsert-contention-unique-index-locking
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- upsert
- unique-index
- contention
- idempotency
- locking
aliases:
- upsert
- insert on duplicate key update
- on conflict do update
- unique index arbitration
- insert race
- duplicate key retry
- hot unique key
- idempotent write path
- guard row upsert
- unique vs upsert outcome
symptoms:
- upsert를 중복이면 알아서 합쳐지는 문법 설탕으로 보고 hot key lock/update path 비용을 놓치고 있어
- SELECT 후 INSERT/UPDATE race를 unique index arbitration으로 줄이는 이유를 설명해야 해
- duplicate key와 deadlock, lock timeout을 같은 retry 정책으로 묶어 중복 side effect가 생길 수 있어
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- database/idempotency-key-and-deduplication
- database/unique-vs-locking-read-duplicate-primer
next_docs:
- database/mysql-on-duplicate-key-update-safety-primer
- database/ordered-guard-row-upsert-patterns-postgresql-mysql
- database/exactly-once-myths-db-queue
linked_paths:
- contents/database/idempotency-key-and-deduplication.md
- contents/database/mysql-on-duplicate-key-update-safety-primer.md
- contents/database/compare-and-set-version-columns.md
- contents/database/compare-and-swap-vs-pessimistic-locks.md
- contents/database/deadlock-case-study.md
- contents/database/read-before-write-race-timeline-mysql-postgresql.md
- contents/database/ordered-guard-row-upsert-patterns-postgresql-mysql.md
- contents/database/exactly-once-myths-db-queue.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
confusable_with:
- database/unique-vs-locking-read-duplicate-primer
- database/mysql-on-duplicate-key-update-safety-primer
- database/ordered-guard-row-upsert-patterns-postgresql-mysql
forbidden_neighbors: []
expected_queries:
- upsert는 중복이면 알아서 합쳐지는 문법이 아니라 unique index arbitration이라는 뜻이 뭐야?
- INSERT ON DUPLICATE KEY UPDATE나 ON CONFLICT DO UPDATE에서 hot unique key가 병목이 되는 이유는?
- upsert가 read-before-write race window를 줄이지만 외부 side effect까지 idempotent하게 만들지는 못하는 이유를 설명해줘
- duplicate key, deadlock, lock timeout은 upsert 경로에서 retry 정책과 metric을 어떻게 분리해야 해?
- 같은 idempotency_key에 payload가 다르면 upsert update path가 결과를 오염시킬 수 있는 예시를 알려줘
contextual_chunk_prefix: |
  이 문서는 upsert contention을 unique index arbitration, hot unique key, duplicate key retry, deadlock retry, idempotent write path 관점으로 설명하는 advanced deep dive다.
  ON DUPLICATE KEY UPDATE, ON CONFLICT DO UPDATE, unique vs upsert outcome 질문이 본 문서에 매핑된다.
---
# Upsert Contention, Unique Index Arbitration, and Locking

> 한 줄 요약: `upsert`는 "중복이면 알아서 합쳐진다"는 문법 설탕이 아니라, unique index 충돌을 어떤 락과 재시도로 흡수할지 정하는 쓰기 경로 설계다.

**난이도: 🔴 Advanced**

관련 문서:

- [Idempotency Key and Deduplication](./idempotency-key-and-deduplication.md)
- [MySQL `ON DUPLICATE KEY UPDATE` Safety Primer](./mysql-on-duplicate-key-update-safety-primer.md)
- [Compare-and-Set Version Columns](./compare-and-set-version-columns.md)
- [Compare-and-Swap과 Pessimistic Locks](./compare-and-swap-vs-pessimistic-locks.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Read-Before-Write Race Timeline Across MySQL and PostgreSQL](./read-before-write-race-timeline-mysql-postgresql.md)
- [Ordered Guard-Row Upsert Patterns Across PostgreSQL and MySQL](./ordered-guard-row-upsert-patterns-postgresql-mysql.md)
- [Exactly-Once Myths in DB Queue](./exactly-once-myths-db-queue.md)

retrieval-anchor-keywords: upsert, insert on duplicate key update, on conflict do update, unique index arbitration, insert race, duplicate key retry, deadlock retry, idempotent write path, hot unique key, guard row upsert, ordered upsert plus lock, pre-seeded guard row, guard creation deadlock, read before write race, check then insert race, unique vs upsert outcome

## 핵심 개념

`upsert`는 보통 다음 요구에서 등장한다.

- 같은 요청이 두 번 들어와도 row를 하나만 만들고 싶다
- 존재하면 갱신하고, 없으면 생성하고 싶다
- 중복 key 충돌을 애플리케이션 분기 대신 SQL 한 문장으로 처리하고 싶다

문제는 `upsert`가 "경쟁 상태를 없애는 마법"은 아니라는 점이다.

- 어떤 unique index가 충돌을 판정하는지 알아야 한다
- 충돌 시 update가 새로운 경합과 락 순서를 만든다
- hot key에서는 insert보다 update path가 더 비싸질 수 있다
- statement는 원자적이어도 외부 side effect까지 멱등해지지는 않는다

핵심은 "`SELECT` 후 `INSERT`/`UPDATE`"를 없애는 데 있고, 동시에 **unique index가 직렬화 지점이 된다는 사실**을 이해하는 데 있다.

## 깊이 들어가기

### 1. `upsert`가 필요한 이유는 read-before-write 경쟁을 없애기 위해서다

가장 흔한 안티패턴은 다음 흐름이다.

1. `SELECT`로 존재 여부 확인
2. 없으면 `INSERT`
3. 있으면 `UPDATE`

동시 요청이 들어오면 두 트랜잭션이 모두 "없다"고 보고 동시에 `INSERT`를 시도할 수 있다.
이 문제를 애플리케이션에서 if/else로 막으려 하면 race window가 남는다.

`upsert`는 이 판정을 unique index가 맡게 해서 race window를 줄인다.

### 2. 직렬화 지점은 SQL이 아니라 unique index다

예를 들어 `payments(idempotency_key)`에 unique index가 있으면, 사실상 이 인덱스가 "누가 먼저 이 키를 선점했는지"를 결정한다.

- 먼저 들어온 쓰기가 insert path를 탄다
- 뒤늦게 들어온 쓰기는 duplicate key를 만나 update path로 들어간다
- update path가 다시 다른 secondary index를 바꾸면 lock 범위가 넓어진다

즉 `upsert`를 이해할 때는 "insert or update"보다 **"어느 unique constraint가 arbitration을 하느냐"**가 더 중요하다.

### 3. `upsert`는 멱등성과 동일하지 않다

동일 key에 대해 한 row만 남는다고 해서 비즈니스 결과가 안전한 것은 아니다.

예를 들어:

- 첫 요청은 `amount=1000`
- 두 번째 중복 요청은 버그로 `amount=3000`

이때 `ON DUPLICATE KEY UPDATE amount = VALUES(amount)`를 쓰면 중복 제거는 됐지만 결과는 오염될 수 있다.

따라서 idempotency write path는 보통 다음 중 하나를 택한다.

- 최초 값을 보존하고 이후 중복은 no-op 처리
- payload hash를 비교해 동일 요청만 허용
- 상태 전이가 허용되는 경우에만 제한된 컬럼만 갱신

핵심은 "중복 요청을 어떻게 병합할 것인가"를 SQL 수준에서 명시하는 것이다.

### 4. hot unique key에서는 update path가 병목이 된다

`upsert`가 자주 충돌하는 키에 몰리면 실제 실행은 "insert 시도 후 대부분 update"가 된다.

이때 생길 수 있는 문제:

- 같은 key를 두고 row lock 대기가 길어진다
- update가 secondary index maintenance를 유발한다
- deadlock retry가 늘어난다
- auto increment를 쓰면 insert intent 경쟁까지 겹친다

그래서 hot key 카운터, 잔액 누적, 인기 상품 집계 같은 경로에서는 `upsert` 하나로 끝내기보다 다음을 다시 검토해야 한다.

- counter sharding
- append-only ledger 후 비동기 합산
- atomic `UPDATE` 중심 설계
- key space 분산

### 5. deadlock과 duplicate key retry를 같은 실패 클래스로 다루면 안 된다

`upsert` 실패는 크게 두 가지다.

- duplicate key
  - 경쟁이 있었지만 비즈니스상 정상일 수 있다
  - 기존 row 조회 후 결과를 재사용하면 된다
- deadlock / lock timeout / serialization failure
  - lock 순서 경쟁 또는 높은 경합 신호다
  - 전체 transaction retry가 필요할 수 있다

둘을 모두 "아무튼 재시도"로 묶으면 중복 side effect가 생기거나 tail latency가 악화된다.
실무에서는 실패 사유별로 retry 정책과 metrics를 분리하는 편이 안전하다.

### 6. `upsert` 바깥의 side effect는 별도로 멱등화해야 한다

DB row가 하나로 정리돼도 다음은 여전히 중복될 수 있다.

- 이메일 발송
- 포인트 적립 이벤트 발행
- 외부 결제 승인 호출

따라서 `upsert`로 DB 상태를 선점한 뒤:

- outbox에 한 번만 기록하거나
- processed-event table로 dedup 하거나
- idempotency key를 외부 시스템에도 전달해야 한다

DB `upsert`는 쓰기 경합의 출발점이지, 시스템 전체 exactly-once 보장의 종착점이 아니다.

## 실전 시나리오

### 시나리오 1. 결제 API idempotency key 저장

`payments(idempotency_key)` unique index로 같은 요청의 중복 생성을 막는다.

추천 방식:

- 최초 요청은 `PENDING` row 생성
- 중복 요청은 기존 row를 그대로 반환
- payload가 다르면 conflict로 처리

이때 중복 요청이 기존 row를 덮어쓰게 두면, "멱등성"이 아니라 "마지막 요청 승리"가 된다.

### 시나리오 2. 일별 집계 테이블 누적

`daily_stats(date, metric)` unique key에 `count = count + ?` 형태 `upsert`를 걸면 구현은 단순하다.
하지만 인기 지표 하나에 트래픽이 몰리면 hot key 병목이 된다.

이 경우는:

- 샤드된 partial counter를 만든 뒤 합산하거나
- append-only event를 쌓고 비동기 집계하는 편이 낫다

### 시나리오 3. 소비자 중복 처리 테이블

메시지 consumer가 `processed_message(message_id)`에 `INSERT` 또는 `upsert`를 사용한다.

중요한 점:

- dedup row 생성과 비즈니스 상태 변경을 같은 transaction에 묶어야 한다
- duplicate key를 "이미 처리됨"으로 해석해야 한다
- outbox나 ack 순서까지 같이 맞춰야 한다

## 코드로 보기

```sql
CREATE TABLE payment_request (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  idempotency_key VARCHAR(64) NOT NULL,
  request_hash CHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL,
  response_payload JSON NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  UNIQUE KEY uk_payment_request_idem (idempotency_key)
);
```

```sql
INSERT INTO payment_request (
  idempotency_key,
  request_hash,
  status,
  response_payload,
  created_at,
  updated_at
) VALUES (?, ?, 'SUCCEEDED', ?, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  updated_at = NOW();
```

위 예시는 "최초 결과를 보존하고 timestamp만 갱신"하는 보수적 전략이다.
중복 요청 payload가 같은지 확인하려면 재조회 후 `request_hash`를 비교해야 한다.

```java
try {
    repository.insertOrKeepFirst(key, requestHash, responsePayload);
} catch (DuplicateKeyException e) {
    PaymentRequest existing = repository.findByIdempotencyKey(key);
    if (!existing.hasSameHash(requestHash)) {
        throw new ConflictingIdempotencyRequestException();
    }
    return existing.toResponse();
}
```

핵심은 duplicate key를 예외가 아니라 **경쟁이 있었음을 알려주는 정상 제어 흐름**으로 해석하는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| `SELECT` 후 `INSERT/UPDATE` | 로직이 눈에 보인다 | race window가 남는다 | 단일 쓰레드성 작업만 있을 때 |
| `INSERT ... ON DUPLICATE KEY UPDATE` | read-before-write를 줄인다 | 충돌 시 lock path를 이해해야 한다 | 단일 row dedup, 간단한 병합 |
| duplicate key + 재조회 | 결과 보존이 명확하다 | round trip이 하나 더 든다 | 멱등성 API, 최초 응답 재사용 |
| append-only + 비동기 집계 | hot key 확장성이 좋다 | 읽기 모델이 복잡해진다 | 충돌이 매우 높은 카운터/집계 |

## 꼬리질문

> Q: `upsert`를 쓰면 race condition이 완전히 사라지나요?
> 의도: unique index arbitration을 이해하는지 확인
> 핵심: read-before-write 경쟁은 줄지만, unique key 충돌과 lock 경합은 여전히 존재한다

> Q: `upsert`와 idempotency는 같은 말인가요?
> 의도: row dedup과 비즈니스 멱등성의 차이를 아는지 확인
> 핵심: 한 row만 남는다고 외부 side effect와 payload 충돌까지 안전해지는 것은 아니다

> Q: hot key에서 `upsert`가 느려지면 무엇을 바꿔야 하나요?
> 의도: atomic SQL 외의 구조적 대안을 아는지 확인
> 핵심: counter sharding, append-only ledger, key 분산 같은 설계 변경을 검토해야 한다

## 한 줄 정리

`upsert`의 본질은 unique index를 직렬화 지점으로 삼아 read-before-write 경쟁을 줄이는 것이고, 실제 운영 안정성은 그 충돌을 어떤 병합 규칙과 retry 정책으로 다루느냐에 달려 있다.
