---
schema_version: 3
title: '같은 시간대 예약 동시 요청 — 락 vs 유니크 제약 vs 낙관적 락 결정'
concept_id: database/roomescape-reservation-concurrency-bridge
canonical: false
category: database
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- reservation-concurrency
- unique-constraint-vs-lock
- optimistic-vs-pessimistic
aliases:
- roomescape 예약 동시성
- 룸이스케이프 동일 시간 예약
- 예약 중복 방지
- 같은 시간 예약 락
- 예약 unique 제약
intents:
- mission_bridge
- design
prerequisites:
- database/lock-basics
linked_paths:
- contents/database/lock-basics.md
- contents/database/constraint-first-booking-primer.md
forbidden_neighbors:
- contents/database/deadlock-vs-lock-wait-timeout-primer.md
expected_queries:
- 룸이스케이프에서 같은 시간 예약이 두 개 들어오면 어떻게 막아?
- 예약 중복을 락으로 막을지 unique 제약으로 막을지 어떻게 골라?
- 비관적 락이랑 낙관적 락 중에 어떤 게 미션에 맞아?
- @Transactional만 걸어도 동시 예약 막히는 거 아니야?
---

# 같은 시간대 예약 동시 요청 — 락 vs 유니크 제약 vs 낙관적 락 결정

> 한 줄 요약: roomescape 예약 중복 방지의 *기본 도구*는 `(date, time_id)` 유니크 제약이다. 비관적 락(SELECT FOR UPDATE)은 *예약 외 다른 자원도 함께 갱신*해야 할 때, 낙관적 락은 *충돌 빈도가 낮고 재시도가 가능*할 때 추가로 고른다.

**난이도: 🟡 Intermediate**

**미션 컨텍스트**: spring-roomescape-admin (Woowa Spring 트랙) — 예약 동시성 단계

관련 문서:

- [DB Lock 기초](./lock-basics.md) — 일반 개념
- [Constraint-first booking primer](./constraint-first-booking-primer.md) — 유니크 제약 우선 전략

## 미션의 어디에 동시성 문제가 보이는가

`ReservationService.create()`가 *두 사용자가 동시에* 같은 (날짜, 시간)으로 호출하면 다음 시퀀스가 가능하다:

```
T1: SELECT count(*) FROM reservation WHERE date='2026-05-10' AND time_id=3 → 0
T2: SELECT count(*) FROM reservation WHERE date='2026-05-10' AND time_id=3 → 0
T1: INSERT INTO reservation (...)  → OK
T2: INSERT INTO reservation (...)  → OK (둘 다 들어감 ❌)
```

`@Transactional` 하나로는 이 race condition이 막히지 않는다. *기본 isolation level (READ_COMMITTED)*은 *팬텀 read*를 막지 않는다. 의미 단위만 묶일 뿐이다.

## 세 가지 도구의 분기

### 도구 1 — UNIQUE 제약 (1순위)

```sql
ALTER TABLE reservation
ADD CONSTRAINT uk_date_time UNIQUE (date, time_id);
```

DB가 *원자적으로* 보장한다. 두 트랜잭션이 같은 (date, time_id)로 INSERT하면 *둘 중 하나는 무조건 실패*. Spring에서 `DataIntegrityViolationException`이 올라온다.

**언제 골라야 하나** — 중복 방지가 *유일한* 동시성 요구사항일 때. roomescape 미션의 기본 답이다.

**장점** — 추가 코드 0줄. 락 잡는 비용 없음. 가장 빠르고 단순.

**단점** — 충돌 시 *예외*로 통보된다. UI에서는 *"이미 예약된 시간입니다"* 메시지로 변환해야 하므로 ControllerAdvice 한 줄이 필요.

### 도구 2 — 비관적 락 (SELECT FOR UPDATE)

```java
@Transactional
public Reservation create(ReservationRequest request) {
    // 같은 시간 슬롯의 row를 락
    ReservationTime time = reservationTimeRepository
        .findByIdForUpdate(request.timeId());
    // 이 안에서는 같은 time row를 다른 트랜잭션이 못 만짐
    if (reservationRepository.existsByDateAndTimeId(request.date(), time.getId())) {
        throw new DuplicateReservationException();
    }
    return reservationRepository.save(...);
}
```

ReservationTime row를 *읽으면서 락*을 잡는다. 같은 time을 보려는 다른 트랜잭션은 *대기*한다.

**언제 골라야 하나** — 예약 INSERT만이 아니라 *시간 슬롯 자체의 카운터/잔여 좌석*도 함께 갱신해야 할 때 (예: "한 시간에 4명까지").

**단점** — 락 대기 시간만큼 throughput 하락. deadlock 위험. 미션 초기 단계에서는 과한 도구다.

### 도구 3 — 낙관적 락 (@Version)

```java
@Entity
public class ReservationTime {
    @Version
    private Long version;
}
```

JPA의 `@Version`은 UPDATE 시 *버전 일치*를 검증한다. 일치 안 하면 `OptimisticLockException`.

**언제 골라야 하나** — 충돌이 *드물고*, *재시도*가 자연스러운 시나리오. roomescape는 동일 시간 예약 빈도가 *높을 가능성*이 있어 (특히 인기 시간) 낙관적 락의 가정과 안 맞을 수 있다.

**단점** — 충돌 시 사용자가 *재시도해야* 한다. 단순 INSERT 중복 방지에는 over-engineering.

## roomescape에서 자주 보이는 잘못된 설계

### 잘못 1 — Service에서 `existsBy` + `save` 조합만으로 검증

```java
public Reservation create(ReservationRequest request) {
    if (reservationRepository.existsByDateAndTimeId(request.date(), request.timeId())) {
        throw new DuplicateReservationException();
    }
    return reservationRepository.save(...);  // race window!
}
```

`existsBy`와 `save` 사이에 *다른 트랜잭션이 INSERT*하면 막을 수 없다. 이 패턴 단독으로는 race condition이 살아있다. UNIQUE 제약이 백업으로 있어야 한다.

### 잘못 2 — `synchronized` 메소드

```java
public synchronized Reservation create(...) { ... }  // ❌
```

JVM 내 락은 *같은 인스턴스*에서만 동작한다. *서버 두 대*면 무용지물. DB 레벨 보장이 정답이다.

### 잘못 3 — Isolation level을 SERIALIZABLE로 올리기

```java
@Transactional(isolation = SERIALIZABLE)  // ❌ 과한 처방
```

격리 수준은 *전역적으로* throughput을 떨어뜨린다. 한 가지 race를 막으려고 격리를 올리면 다른 모든 트랜잭션이 영향받는다.

## 자가 점검

- [ ] `(date, time_id)` UNIQUE 제약을 schema.sql에 넣었나?
- [ ] `DataIntegrityViolationException`을 *비즈니스 예외*로 변환하는 핸들러가 있나?
- [ ] `existsBy + save` 조합만으로 중복 검증을 마쳤다고 생각하지 않았는가?
- [ ] 비관적 락이나 낙관적 락이 *진짜 필요한 추가 갱신*이 있는가? 없으면 UNIQUE 하나로 충분.
- [ ] 서버 다중화 가능성을 고려해 *DB 레벨* 보장을 택했나? (`synchronized` 금지)

## 다음 문서

- 더 큰 그림: [DB Lock 기초](./lock-basics.md)
- 제약 우선 전략의 디자인: [Constraint-first booking primer](./constraint-first-booking-primer.md)
- 락 타임아웃 디버깅: [Connection Timeout vs Lock Timeout Card](./connection-timeout-vs-lock-timeout-card.md)
