---
schema_version: 3
title: 'roomescape 예약 생성/삭제에서 @Transactional 경계 결정'
concept_id: spring/roomescape-transactional-boundary-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- transactional-boundary
- service-vs-repository-tx
- single-statement-tx
aliases:
- roomescape Transactional
- ReservationService 트랜잭션
- 룸이스케이프 예약 트랜잭션
- 예약 삭제 트랜잭션 경계
- ReservationService @Transactional 어디
intents:
- mission_bridge
- design
prerequisites:
- spring/transactional-basics
linked_paths:
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-service-layer-transaction-boundary-patterns.md
forbidden_neighbors:
- contents/spring/spring-self-invocation-transactional-only-misconception-primer.md
expected_queries:
- 룸이스케이프 ReservationService에 @Transactional 붙여야 해?
- 예약 한 줄짜리 INSERT만 있는데 트랜잭션 필요해?
- create랑 delete 메소드 어디에 트랜잭션을 그어야 해?
- repository에 @Transactional을 붙이면 안 되는 이유가 뭐야?
---

# roomescape 예약 생성/삭제에서 @Transactional 경계 결정

> 한 줄 요약: 트랜잭션 경계는 *비즈니스 의미 단위*에 그어야 하므로 `ReservationService.create()` / `delete()` 같은 Service 메소드 위에 `@Transactional`을 둔다. INSERT 한 줄짜리라도 *Service 단위*가 맞고, Repository에 트랜잭션을 두면 의미 단위가 깨진다.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: spring-roomescape-admin (Woowa Spring 트랙) — 4단계 이후

관련 문서:

- [Spring @Transactional 기초](./spring-transactional-basics.md) — 일반 개념
- [Service Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md) — 패턴 모음

## 미션의 어디에 트랜잭션 경계 결정이 필요한가

`ReservationService`의 두 핵심 메소드를 보자:

```java
@Service
public class ReservationService {
    private final ReservationRepository reservationRepository;
    private final ReservationTimeRepository reservationTimeRepository;

    public Reservation create(ReservationRequest request) {
        ReservationTime time = reservationTimeRepository
            .findById(request.timeId())
            .orElseThrow();                      // 조회
        Reservation reservation = new Reservation(
            null, request.name(), request.date(), time);
        return reservationRepository.save(reservation);  // 저장
    }

    public void delete(Long id) {
        reservationRepository.deleteById(id);
    }
}
```

`create()`는 *조회 → 검증 → 저장* 세 단계가 하나의 비즈니스 의미("예약 한 건 만들기")를 이룬다. `delete()`는 한 줄짜리지만 *"예약 취소"*라는 의미 단위다. 이 두 곳이 트랜잭션 경계 후보다.

## 왜 트랜잭션 경계가 *Service*에 그어지는가

### 경계는 의미 단위

트랜잭션은 *원자성을 보장해야 하는 단위*다. roomescape 5~6단계로 가면 같은 메소드 안에서 *여러 테이블*을 만지게 된다 (예: 예약 저장 + 멤버 통계 갱신). 그때 *"세 INSERT가 모두 성공하거나 모두 실패해야 한다"*는 보장이 필요하다. Service 메소드가 그 *의미 단위*를 표현한다.

### Repository에 두면 안 되는 이유

```java
@Repository
public class JdbcReservationRepository implements ReservationRepository {
    @Transactional  // ❌ 잘못된 위치
    public Reservation save(Reservation reservation) { ... }
}
```

이렇게 두면 두 가지 문제가 생긴다:

1. **Service가 두 Repository를 호출하면 트랜잭션이 둘로 쪼개진다** — 첫 INSERT 후 두 번째 INSERT 실패 시 첫 INSERT는 이미 commit. 의미 단위가 깨진다.
2. **재사용이 깨진다** — 같은 `save()`를 호출하는 모든 코드가 *원치 않는 새 트랜잭션*을 매번 시작한다.

### 한 줄짜리 메소드도 Service에 둬야 하나

`delete(Long id)`처럼 INSERT/DELETE 한 줄짜리라도 Service에 `@Transactional`을 둔다. 이유:

- 일관성 — 모든 Service 메소드가 트랜잭션 경계라면 *어디까지 원자성이 보장되는지* 클래스 레벨에서 즉시 알 수 있다.
- 확장성 — 나중에 *"삭제 전 권한 체크 + 로그 남기기"*가 추가되면 그대로 *원자 단위*로 묶인다.

## 미션 PR에서 자주 보는 세 가지 패턴

### 패턴 1 — 클래스 레벨 `@Transactional`

```java
@Service
@Transactional(readOnly = true)
public class ReservationService {
    @Transactional
    public Reservation create(ReservationRequest request) { ... }
    @Transactional
    public void delete(Long id) { ... }
    public List<Reservation> findAll() { ... }  // readOnly=true 그대로
}
```

읽기 메소드는 `readOnly=true`로 가볍게, 쓰기 메소드는 명시적으로 `@Transactional`로 덮어쓴다. 멘토가 자주 권장하는 모양.

### 패턴 2 — 컨트롤러 위에 `@Transactional`

```java
@RestController
@Transactional   // ❌
public class ReservationController { ... }
```

컨트롤러는 *HTTP 경계*다. 트랜잭션 경계가 아니다. 요청 lifecycle과 트랜잭션 lifecycle이 섞이면 디버깅 난이도가 올라간다.

### 패턴 3 — `private` 메소드에 `@Transactional`

```java
@Service
public class ReservationService {
    public Reservation create(ReservationRequest request) {
        return doCreate(request);  // self-invocation
    }
    @Transactional  // ❌ 동작 안 함
    private Reservation doCreate(ReservationRequest request) { ... }
}
```

Spring AOP는 *프록시*로 동작하므로 *같은 클래스 안의 self-invocation*에는 트랜잭션이 적용되지 않는다. 미션에서 자주 발생하는 함정.

## 자가 점검

- [ ] `@Transactional`이 Service 메소드(또는 클래스) 위에만 있나?
- [ ] Repository나 Controller에는 `@Transactional`이 *없는가*?
- [ ] 읽기 전용 메소드에 `readOnly = true`를 표시했나?
- [ ] `private` 메소드에 `@Transactional`을 붙이지 않았나?
- [ ] Service 메소드 하나가 *두 개 이상의 Repository*를 호출하면 그 메소드 위에 `@Transactional`이 있는가?

## 다음 문서

- 더 큰 그림: [Spring @Transactional 기초](./spring-transactional-basics.md)
- Self-invocation 함정: [Self-invocation @Transactional 미신](./spring-self-invocation-transactional-only-misconception-primer.md)
- 동시성 처리로 넘어가면 *roomescape 예약 동시성 브리지*도 함께 본다 (별도 문서)
