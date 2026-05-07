---
schema_version: 3
title: UNIQUE vs Locking-Read Duplicate Primer
concept_id: database/unique-vs-locking-read-duplicate-primer
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 92
mission_ids: []
review_feedback_tags:
- unique-constraint
- locking-read
- duplicate-key
- insert-if-absent
- beginner
aliases:
- unique vs locking read
- unique constraint vs select for update
- duplicate key beginner
- duplicate key vs lock timeout
- select for update duplicate key
- insert if absent basics
- already exists busy retryable mapping
- duplicate fresh read conflict mapping
- exact duplicate primer
- UNIQUE랑 FOR UPDATE 차이
symptoms:
- duplicate key, lock timeout, deadlock을 모두 같은 장애처럼 보고 있어
- SELECT FOR UPDATE를 넣었는데도 duplicate key가 나는 이유를 이해하지 못해
- exact duplicate의 최종 승자는 UNIQUE가 정하고 locking read는 queueing 보조라는 첫 그림이 필요해
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- database/three-bucket-terms-common
- database/exact-key-pre-check-decision-card
next_docs:
- database/empty-result-locking-cheat-sheet-postgresql-mysql
- database/unique-claim-existing-row-reuse-primer
- database/upsert-contention-unique-index-locking
linked_paths:
- contents/database/exact-key-pre-check-decision-card.md
- contents/database/three-bucket-terms-common-card.md
- contents/database/lock-timeout-not-already-exists-common-confusion-card.md
- contents/database/unique-claim-existing-row-reuse-primer.md
- contents/database/for-share-vs-for-update-duplicate-check-note.md
- contents/database/empty-result-locking-cheat-sheet-postgresql-mysql.md
- contents/database/duplicate-key-fresh-read-classifier-mini-card.md
- contents/database/mysql-duplicate-key-retry-handling-cheat-sheet.md
- contents/database/mysql-rr-exact-key-probe-visual-guide.md
- contents/database/mysql-rc-duplicate-check-pitfall-note.md
- contents/database/read-before-write-race-timeline-mysql-postgresql.md
- contents/database/upsert-contention-unique-index-locking.md
- contents/database/unique-vs-slot-row-vs-guard-row-quick-chooser.md
- contents/database/insert-if-absent-retry-outcome-guide.md
- contents/database/postgresql-serializable-retry-playbook.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/spring-jpa-lock-timeout-deadlock-exception-mapping.md
- contents/database/pool-metrics-lock-wait-timeout-mini-bridge.md
- contents/spring/spring-transactional-basics.md
confusable_with:
- database/empty-result-locking-cheat-sheet-postgresql-mysql
- database/upsert-contention-unique-index-locking
- database/unique-claim-existing-row-reuse-primer
forbidden_neighbors: []
expected_queries:
- UNIQUE와 SELECT FOR UPDATE locking read는 duplicate insert 방지에서 역할이 어떻게 달라?
- select for update를 넣었는데 왜 duplicate key가 여전히 날 수 있어?
- exact duplicate correctness는 UNIQUE가 맡고 locking read는 앞단 queue 보조라는 뜻을 초보자에게 설명해줘
- duplicate key는 already exists, lock timeout은 busy, deadlock은 retryable로 번역하는 이유가 뭐야?
- 0 row FOR UPDATE가 absence를 항상 예약하지 못하고 write 시점 UNIQUE가 최종 승자를 정하는 예시를 알려줘
contextual_chunk_prefix: |
  이 문서는 exact duplicate에서 UNIQUE constraint와 locking read pre-probe의 역할을 beginner primer로 설명한다.
  duplicate key, select for update duplicate, already exists busy retryable, UNIQUE vs FOR UPDATE 질문이 본 문서에 매핑된다.
---
# UNIQUE vs Locking-Read Duplicate Primer

> 한 줄 요약: exact duplicate에서는 `UNIQUE`가 진짜 승자를 정하는 hard gate이고, locking read pre-probe는 경우에 따라 앞단 queue를 조금 만들어 줄 뿐이다. 그래서 애플리케이션은 `connection timeout`/`duplicate key`/`deadlock`을 `busy`/`already exists`/`retryable`로 먼저 고정 번역해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Exact-Key Pre-Check Decision Card](./exact-key-pre-check-decision-card.md)
- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [UNIQUE Claim + Existing-Row Reuse Primer](./unique-claim-existing-row-reuse-primer.md)
- [FOR SHARE vs FOR UPDATE Duplicate Check Note](./for-share-vs-for-update-duplicate-check-note.md)
- [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md)
- [Read-Before-Write Race Timeline Across MySQL and PostgreSQL](./read-before-write-race-timeline-mysql-postgresql.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md)
- [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: unique vs locking read, unique constraint vs select for update, duplicate key 뭐예요, duplicate key랑 lock timeout 차이, unique 랑 for update 뭐가 달라요, select for update 넣었는데 왜 duplicate key 나요, insert if absent 처음 배우는데, exact duplicate 큰 그림, 중복 insert 헷갈려요, duplicate key handling beginner, already exists busy retryable mapping, duplicate fresh read conflict mapping, connection timeout deadlock duplicate key mapping, insert if absent 기초, why duplicate key after for update

## 이 문서가 먼저 맞는 질문

아래처럼 **처음 개념을 묻는 질문**이면 deep dive보다 이 primer가 먼저 맞다.

- "`duplicate key`가 뭐예요?"
- "`UNIQUE`랑 `FOR UPDATE`는 뭐가 달라요?"
- "`select for update` 넣었는데 왜 아직도 중복이 나요?"
- "`lock timeout`이랑 `duplicate key`를 같은 장애로 봐도 되나요?"

짧게 먼저 고정하면 이렇다.

- exact duplicate를 최종 차단하는 문은 보통 `UNIQUE`다
- locking read는 이미 있는 row를 순서대로 다루게 도와줄 수는 있어도, 없는 row를 항상 미리 잠가 주는 만능 duplicate 방지 장치는 아니다
- 그래서 첫 질문에서는 "`누가 승자를 확정하나?`"를 먼저 보고, 그다음에 "`대기열을 앞단에서 만들 필요가 있나?`"를 본다

## 핵심 개념

먼저 머릿속에 문 두 개만 둔다.

- `UNIQUE`: **입구의 개찰구**다. 여러 요청이 동시에 달려와도 write 시점에 딱 한 명만 통과시킨다.
- locking read pre-probe: **입구 앞 대기줄**이다. 어떤 경우에는 먼저 온 요청 뒤에 줄을 세우지만, 잠글 대상이 없으면 줄 자체가 잘 안 생긴다.

그래서 beginner 기준 기본 원칙은 이렇다.

> exact duplicate correctness는 `UNIQUE`가 맡고, locking read는 있더라도 queueing/UX 보조 수단으로만 본다.

이 차이가 애플리케이션 에러 처리도 바꾼다.

- `UNIQUE`에서 패배한 요청: 보통 `duplicate key`가 난다
- locking read queue에서 막힌 요청: 보통 lock wait, lock timeout, deadlock, 재조회 경로가 먼저 보인다
- `SERIALIZABLE` 경쟁에서 밀린 요청: `serialization failure`가 나고 새 snapshot 재판단이 필요하다
- pre-probe가 `0 row`면: 결국 `UNIQUE`가 다시 마지막 승자를 정한다

<a id="unique-vs-locking-read-comparison"></a>

## 한눈에 보기

| 비교 축 | `UNIQUE` constraint | locking read pre-probe |
|---|---|---|
| 무엇을 보장하나 | 같은 exact key 중복 생성을 write 시점에 차단 | 때때로 앞단에서 contender를 줄 세움 |
| 잘 맞는 상황 | `idempotency_key`, `(user_id, coupon_id)`, `email` | 이미 있는 row를 한 명씩 읽고 갱신하거나 상태를 넘겨받아야 할 때 |
| 패배 요청의 대표 신호 | `duplicate key`, unique violation | lock wait, lock timeout, deadlock, 나중 재조회 |
| 애플리케이션 기본 대응 | 기존 row 재조회, idem 결과 반환, `409` 등 | bounded retry, busy 응답, lock 예외 분리 |
| 가장 위험한 오해 | `duplicate key`는 시스템 장애다 | `FOR UPDATE`를 넣었으니 duplicate 처리 코드는 필요 없다 |

핵심 기억법:

- "`한 명만 성공`"의 진짜 계약은 `UNIQUE`
- "`조금 먼저 줄 세우기`"는 locking read
- 둘은 역할이 다르다

## Beginner 연결표 (같은 축에서 바로 옆 문서로 이동)

`exact duplicate` 축을 처음 잡을 때는 아래 표처럼 "지금 막히는 질문" 기준으로 옆 문서로 이동하면 덜 헷갈린다.

| 지금 궁금한 것 | 바로 볼 문서 | 연결 포인트 |
|---|---|---|
| "애초에 pre-check를 넣을지 말지부터 빨리 고르고 싶다" | [Exact-Key Pre-Check Decision Card](./exact-key-pre-check-decision-card.md) | `UNIQUE` only / locking pre-check / pre-check 생략을 먼저 가른다 |
| "`0 row FOR UPDATE`가 왜 duplicate 방지를 끝내 주지 못하지?" | [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md) | absence check와 existing-row lock을 먼저 분리한다 |
| "service에서 `duplicate key` / `lock timeout` / `deadlock`을 어떻게 같은 언어로 번역하지?" | [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md) | `already exists` / `busy` / `retryable` 3버킷으로 고정한다 |
| "PostgreSQL `40001`도 duplicate처럼 보면 되나?" | [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md) | duplicate 확정 신호가 아니라 whole-transaction retry 신호임을 분리한다 |

## 용어 교차표: `winner` / `already exists` / `conflict` / `busy`

먼저 아주 짧게 고정하면 이렇다.

- `winner`: DB 안에서 먼저 자리를 차지한 요청 또는 row다.
- `already exists`: 그 winner가 이미 확정됐다고 서비스가 붙이는 결과 버킷이다.
- `conflict`: `already exists` 안쪽에서 "같은 key를 다른 뜻으로 썼다"를 더 좁게 말하는 API 응답이다.
- `busy`: winner가 있는지조차 아직 확정하지 못한 상태다.

즉 `winner`는 **DB 현실**, `already exists`/`busy`는 **서비스 분류**, `conflict`는 **그중 일부를 더 세게 설명한 응답**이다.

| 지금 본 말 | 어느 층의 말인가 | 초급자 번역 | 보통 같이 오는 신호 | 다음 행동 |
|---|---|---|---|---|
| `winner` | DB 상태 | "누가 먼저 선점했다" | `duplicate key`, fresh read에서 기존 row 확인 | 그 row가 내 요청과 같은 의미인지 읽어 본다 |
| `already exists` | 서비스 결과 버킷 | "승자는 이미 확정됐다" | `duplicate key`, same-key winner read | 기존 결과 replay 또는 기존 resource 반환 |
| `409 conflict` | API/도메인 응답 | "같은 key를 다른 의미로 재사용했다" | same key + different payload/hash | retry보다 계약 위반으로 응답한다 |
| `busy` | 서비스 결과 버킷 | "아직 결론을 못 냈다" | `connection timeout`, `lock timeout`, same-key winner가 아직 `PROCESSING` | fresh read, 짧은 retry, 혼잡 확인 |

작은 예시 하나로 같이 보면 더 쉽다.

| 장면 | 먼저 떠올릴 말 | 왜 그렇게 읽나 |
|---|---|---|
| B가 `duplicate key`를 받았고 fresh read에서 A의 완료 row를 봄 | `winner` -> `already exists` | 이미 같은 key 승자가 확정됐다 |
| B가 같은 key를 다른 payload로 보냈고 fresh read에서 A의 row를 봄 | `winner` -> `already exists` -> `409 conflict` | winner는 있지만 내 요청과 같은 뜻이 아니다 |
| B가 `lock timeout`을 받고 winner row도 아직 못 봄 | `busy` | 아직 승패를 확정할 근거가 없다 |
| B가 `DuplicateKeyException` 뒤 fresh read에서 `PROCESSING` row를 봄 | `busy` | winner 후보는 보이지만 내 최종 결과는 아직 안 끝났다 |

헷갈릴 때 한 줄 규칙:

## 용어 교차표: `winner` / `already exists` / `conflict` / `busy` (계속 2)

- `winner`를 봤다고 항상 바로 `409 conflict`는 아니다.
- `already exists`와 `409 conflict`는 같은 층의 말이 아니다.
- `busy`는 "이미 졌다"가 아니라 "아직 판단 보류"에 가깝다.

더 자세한 후속 표:

- fresh read 뒤 `idem success` / `in-progress` / `409 conflict`를 가르려면 [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- MySQL `1062`에서 `already exists` 안쪽 replay/`409 conflict` 분기를 더 보려면 [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)

## 실패 신호 번역 3버킷 표 (초급자 고정)

용어 뜻이 먼저 필요하면 [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)를 보고, 여기서는 exact duplicate 문맥에 맞는 번역을 읽으면 된다.

- 더 자세한 3버킷 결정표가 바로 필요하면 [Insert-if-Absent Retry Outcome Guide의 3버킷 먼저 고정](./insert-if-absent-retry-outcome-guide.md#three-bucket-decision-table)으로 바로 이동한다.
- Spring/JPA 예외 이름까지 같이 보고 싶으면 [초급자용 30초 분류표](./spring-jpa-lock-timeout-deadlock-exception-mapping.md#초급자용-30초-분류표-db-신호---서비스-결과-3버킷)로 바로 내려간다.

| 실패 신호 | 서비스 레이어 결과 | 초급자 해석 |
|---|---|---|
| `connection timeout` (pool borrow timeout) | `busy` | 지금 자원이 꽉 차서 이번 요청을 바로 처리하지 못했다 |
| `deadlock` | `retryable` | 이번 트랜잭션 시도만 희생됐다. 새 시도로 다시 가능하다 |
| `duplicate key` | `already exists` | 같은 key의 승자가 이미 확정됐다 |

짧은 체크:

- `connection timeout`은 "이미 생성됨" 신호가 아니다. 그래서 `already exists`로 번역하지 않는다.
- `lock timeout`을 `already exists`로 읽는 오해는 [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md) 5줄만 먼저 고정해도 바로 줄어든다.
- `deadlock`은 "중복 확정"이 아니라 "시도 실패" 신호다. 그래서 `retryable`이다.
- `duplicate key`는 보통 "승자 확정" 신호다. 그래서 기본값은 `already exists`다.

## 초급자 결과 언어 고정표

먼저 DB 용어를 서비스 결과 언어 3개로 고정한다.
이 표는 "권장"이 아니라 **고정 사전**처럼 쓴다.

한 장짜리 결정을 먼저 보고 돌아오고 싶다면 [3버킷 결정표 앵커](./insert-if-absent-retry-outcome-guide.md#three-bucket-decision-table)를 먼저 열어도 된다.

- `already exists`: 이미 승자가 확정됨
- `busy`: 아직 승패 미확정(지금 혼잡함)
- `retryable`: 이번 시도만 실패, 새 트랜잭션으로 다시 가능

| DB 신호(원문) | 결과 언어(고정) | 초급자 해석 한 줄 | 기본 처리 | 절대 하지 말 것 |
|---|---|---|---|---|
| `duplicate key` (unique violation) | `already exists` | 이미 같은 key가 먼저 성공했다 | 기존 row/결과 재조회, idem 응답 | 장애로 분류해서 에러 알람만 올림 |
| `lock timeout` | `busy` | 현재 잠금 대기 중이라 결론을 못 냈다 | 짧은 한정 retry 또는 즉시 busy 응답 | 무조건 무한 retry |
| `deadlock` | `retryable` | 이번 트랜잭션이 victim으로 취소됐다 | 트랜잭션 전체 재시도 | `already exists`로 잘못 번역 |
| `serialization failure` | `retryable` | snapshot 판단이 충돌해 무효 처리됐다 | 새 snapshot으로 트랜잭션 전체 재시도 | 부분 쿼리만 재시도 |

분류 순서(헷갈릴 때 이 순서만 기억):

1. `duplicate key`면 바로 `already exists`로 끝낸다.
2. `lock timeout`이면 `busy`로 보고 짧은 retry budget 안에서만 재시도한다.
3. `deadlock`/`serialization failure`면 `retryable`로 보고 트랜잭션 처음부터 다시 시작한다.

실무 고정 규칙(초급자 버전, 위 표와 동일):

1. `duplicate key`는 `already exists`로 즉시 종결한다.
2. `lock timeout`은 먼저 `busy`로 분류하고, retry budget을 짧게 둔다.
3. `deadlock`/`serialization failure`는 같은 `retryable`로 묶고 "전체 트랜잭션 재시도"를 지킨다.

작은 응답 예시(쿠폰 `issueIfAbsent`):

- `duplicate key` -> `already exists` ("이미 발급된 요청입니다")
- `lock timeout` -> `busy` ("지금 요청이 몰려 있습니다. 잠시 후 다시 시도해 주세요")
- `deadlock`/`serialization failure` -> `retryable` (내부 bounded retry 후에도 실패하면 `busy` 또는 정책 오류로 반환)

자주 생기는 혼동 3개:

## 초급자 결과 언어 고정표 (계속 2)

- `lock timeout`은 winner 확정 신호가 아니다. 그래서 `already exists`로 번역하지 않는다.
- `deadlock`은 "충돌이 있었음"이지 "중복이 확정됨"이 아니다. 그래서 `retryable`이다.
- `serialization failure`는 부분 쿼리 재시도가 아니라 트랜잭션 전체 재시도 신호다.

## exact duplicate에서 실제로 무슨 일이 생기나

중복 쿠폰 발급을 막는 가장 흔한 예를 보자.

```sql
ALTER TABLE coupon_issue
ADD CONSTRAINT uq_coupon_issue_coupon_member
UNIQUE (coupon_id, member_id);
```

이제 두 요청이 동시에 같은 `(coupon_id, member_id)`를 넣어도 DB는 한쪽만 통과시킨다.

```sql
INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (:coupon_id, :member_id);
```

애플리케이션 입장에서는 loser signal이 비교적 단순하다.

1. 한 요청은 성공한다.
2. 다른 요청은 `duplicate key`를 받는다.
3. 서비스는 그 예외를 "정상적인 중복 경쟁 결과"로 해석한다.

예를 들면 이런 흐름이다.

```java
try {
    couponIssueRepository.insert(couponId, memberId);
    return IssueResult.issued();
} catch (DuplicateKeyException e) {
    return IssueResult.alreadyIssued();
}
```

이 경로의 핵심은 `duplicate key`를 장애 알림이 아니라 **중복 요청이 패배했다는 제어 흐름**으로 보는 것이다.

## locking read pre-probe는 언제 다른 신호를 만들까

팀이 종종 이런 pre-check를 먼저 둔다.

```sql
SELECT id
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR UPDATE;
```

이 코드는 두 상황에서 전혀 다르게 보인다.

### 1. row가 이미 있는 경우

이미 존재하는 row를 다른 트랜잭션이 `FOR UPDATE`로 잡고 있다면, 뒤 요청은 같은 `SELECT ... FOR UPDATE`에서 기다릴 수 있다.

그러면 loser signal이 `duplicate key`보다 앞에서 바뀐다.

- lock wait
- lock timeout
- deadlock
- commit 후 재조회해서 "이미 있음" 확인

즉 이때 애플리케이션은 duplicate handling만이 아니라 **lock-related retry/busy 정책**도 필요하다.

### 2. row가 아직 없는 경우

두 요청이 거의 동시에 들어와 둘 다 `0 row`를 보면, pre-probe queue는 약하거나 아예 없을 수 있다.

- PostgreSQL에서는 보통 missing row 자체를 잠그지 못한다
- MySQL `READ COMMITTED`도 search gap queue를 기대하면 안 된다
- MySQL `REPEATABLE READ`는 exact-key probe에서 잠깐 줄을 세우는 것처럼 보일 수 있지만, 엔진/인덱스 경로 의존성이 크다
- `FOR SHARE`와 `FOR UPDATE` 차이는 existing row에서는 커도, empty-result duplicate pre-check에서는 예상보다 작다

그래서 이 장면에서는 pre-probe가 있더라도 마지막 승자는 여전히 `UNIQUE`가 정한다.

즉 **locking read를 넣어도 duplicate-key handling이 사라지지 않는다.**

## 애플리케이션 에러 처리는 어디서 갈리나

| 설계 | DB에서 먼저 보이는 신호 | 애플리케이션 기본 해석 |
|---|---|---|
| `INSERT` + `UNIQUE` | `duplicate key` / unique violation | expected duplicate. 기존 row 재조회 또는 idem 응답 반환 |
| existing row에 대한 locking read | lock wait, timeout, deadlock, 이후 재조회 | in-flight owner가 있거나 hot row 경합. retry/busy 판단 필요 |
| `SERIALIZABLE` 트랜잭션 경합 | serialization failure (`40001`) | 같은 판단을 동시에 확정할 수 없어 새 시도 필요 |
| `0 row` pre-probe + `UNIQUE` | 여전히 나중에 `duplicate key` 가능 | pre-probe는 보조일 뿐. duplicate handling 유지 |
| `0 row` pre-probe + no `UNIQUE` | 둘 다 insert 성공 가능 | 설계 결함. 중복 생성 버그 |

초보자가 특히 구분해야 할 것은 세 가지다.

- `duplicate key`는 대개 **이미 승자가 있는 business duplicate**
- `lock timeout`은 **아직 결론을 못 본 busy 상태**
- deadlock/serialization failure는 **이번 시도를 버리고 다시 시작해야 하는 retryable 상태**

즉 신호를 하나로 뭉개면 운영에서 원인 분리가 어려워진다.

## 어떤 경우에 무엇을 먼저 고르나

### `UNIQUE`를 먼저 고르는 경우

아래 셋 중 하나면 거의 항상 여기서 시작한다.

- 같은 exact key는 하나만 있어야 한다
- 패배 요청을 명확히 duplicate로 끝낼 수 있다
- 기존 성공 결과를 재사용하거나 `already issued`처럼 짧게 응답할 수 있다

예:

- `idempotency_key`
- `(coupon_id, member_id)`
- `external_order_id`

### locking read를 추가로 고려하는 경우

아래처럼 **이미 있는 row의 상태를 이어받아야 할 때** 보조로 붙인다.

- 누군가가 만든 `PENDING` row를 뒤 요청이 기다렸다가 재사용해야 한다
- 같은 row의 상태 전이를 한 번에 한 요청만 진행해야 한다
- duplicate 자체보다 "진행 중인 기존 처리"를 관찰하는 UX가 중요하다

이 경우에도 보통 구조는 "`UNIQUE`로 선점 + existing row locking read로 상태 관찰" 쪽이 더 흔들림이 적다.

### locking read만으로 끝내면 안 되는 경우

- missing row duplicate check
- overlap booking
- capacity/count 같은 집합 규칙

이 문제들은 "`없다`를 잠근다"는 발상만으로 닫히지 않는다. `UNIQUE`, slot row, guard row, exclusion constraint, `SERIALIZABLE` retry 같은 다른 도구가 필요하다.

## 흔한 오해

- "`FOR UPDATE`를 넣었으니 duplicate 예외 처리는 지워도 된다"
  - 아니다. `0 row` pre-probe에서는 여전히 `UNIQUE` 패배가 뒤에서 난다.
- "`duplicate key`는 DB가 불안정하다는 뜻이다"
  - 아니다. exact duplicate path에서는 흔히 정상 경쟁 결과다.
- "lock timeout이 났으니 이미 다른 요청이 성공했겠지"
  - 아니다. 단지 오래 잠겨 있었거나 deadlock이 있었을 수 있다.
- "deadlock/serialization failure도 `already exists`로 내보내면 되지 않나"
  - 아니다. 둘은 winner 확정 신호가 아니라, 새 트랜잭션 시도로 다시 판단해야 하는 신호다.
- "MySQL RR에서 잘 됐으니 다른 엔진도 비슷하다"
  - 특히 틀리기 쉽다. empty-result locking은 엔진 차이가 크다.

## 더 이어서 보면 좋은 문서

- empty-result absence check 직관부터 다지고 싶다면 [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- MySQL exact-key pre-probe가 왜 가끔 queue처럼 보이는지 보려면 [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- `FOR SHARE`와 `FOR UPDATE`가 exact-key duplicate check에서 언제 진짜 갈리고 언제 거의 안 갈리는지 보려면 [FOR SHARE vs FOR UPDATE Duplicate Check Note](./for-share-vs-for-update-duplicate-check-note.md)
- RC 전환 뒤 duplicate-key와 retry가 왜 더 자주 surface되는지 보려면 [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md)
- `duplicate key`/lock timeout/deadlock/serialization failure를 결과 언어로 더 자세히 분류하려면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- duplicate arbitration을 SQL write path 관점에서 더 깊게 보려면 [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- PostgreSQL `40001` whole-transaction retry 경계를 보려면 [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- exception translation까지 내려가려면 [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)

## 한 줄 정리

exact duplicate에서는 `UNIQUE`가 hard gate라서 loser를 `duplicate key`로 다루는 쪽이 기본이며, 서비스 결과 언어는 `duplicate key`는 `already exists`, `lock timeout`은 `busy`, `deadlock`/`serialization failure`는 `retryable`로 고정해 두는 편이 가장 덜 흔들린다.
