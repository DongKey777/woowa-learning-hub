---
schema_version: 3
title: Reservation, Hold, and Expiry as a Consistency Seam
concept_id: design-pattern/reservation-hold-expiry-consistency-seam
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- reservation-hold-expiry
- consistency-seam
- confirm-release-workflow
aliases:
- reservation pattern
- hold expiry
- inventory reservation
- temporary claim
- consistency seam
- confirm or release
- reservation expiry
- seat hold
- coupon hold
- stock hold before payment
symptoms:
- 주문, 재고, 결제를 한 트랜잭션으로 묶으려다 aggregate boundary가 커지고 외부 실패를 rollback으로 해결하려 한다
- hold를 만들었지만 confirm, release, expire 책임자가 불명확해 임시 점유가 영구 잠김으로 남는다
- 만료된 hold에 뒤늦은 결제 성공이나 retry가 도착했을 때 stale confirm을 막는 상태 전이 규칙이 없다
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/semantic-lock-pending-state-pattern
next_docs:
- design-pattern/compensation-vs-reconciliation-pattern
- design-pattern/process-manager-state-store-recovery
- design-pattern/aggregate-version-optimistic-concurrency-pattern
linked_paths:
- contents/design-pattern/aggregate-boundary-vs-transaction-boundary.md
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/workflow-owner-vs-participant-context.md
- contents/design-pattern/semantic-lock-pending-state-pattern.md
- contents/design-pattern/saga-coordinator-pattern-language.md
- contents/design-pattern/process-manager-vs-saga-coordinator.md
- contents/design-pattern/aggregate-invariant-guard-pattern.md
- contents/design-pattern/compensation-vs-reconciliation-pattern.md
- contents/design-pattern/aggregate-version-optimistic-concurrency-pattern.md
confusable_with:
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/semantic-lock-pending-state-pattern
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/compensation-vs-reconciliation-pattern
forbidden_neighbors: []
expected_queries:
- reservation hold expiry 패턴은 주문과 재고를 한 transaction으로 묶지 않고 어떻게 consistency seam을 만들까?
- hold를 만들 때 confirm, release, expire 책임을 같이 설계해야 하는 이유가 뭐야?
- 결제 성공 이벤트가 hold 만료 후 늦게 도착하면 왜 stale confirm을 거부해야 해?
- 재고나 좌석처럼 일시 점유 가능한 자원에서 reservation id와 expiry token이 필요한 이유가 뭐야?
- cross aggregate 즉시 일관성이 비쌀 때 reservation seam과 process manager deadline을 어떻게 결합해?
contextual_chunk_prefix: |
  이 문서는 Reservation, Hold, and Expiry as a Consistency Seam playbook으로,
  주문/재고/좌석/쿠폰처럼 cross-aggregate 즉시 일관성을 강제하기 어려운 흐름에서
  임시 권리인 hold를 만들고 deadline, confirm, release, expiry, stale signal guard로
  consistency seam을 설계하는 방법을 설명한다.
---
# Reservation, Hold, and Expiry as a Consistency Seam

> 한 줄 요약: cross-aggregate 즉시 일관성을 억지로 강제하기 어렵다면, reservation/hold/expiry 패턴으로 일시적 권리를 먼저 확보하고 이후 confirm 또는 release로 일관성 seam을 설계할 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Boundary vs Transaction Boundary](./aggregate-boundary-vs-transaction-boundary.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Semantic Lock and Pending State Pattern](./semantic-lock-pending-state-pattern.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)

---

## 핵심 개념

실무에서 가장 자주 나오는 어려운 질문 중 하나는 이거다.

- 주문과 재고를 어떻게 같이 맞출까
- 쿠폰 사용과 결제를 어떻게 동시에 안전하게 처리할까
- 좌석 점유와 결제 승인 사이의 틈을 어떻게 메울까

모든 걸 한 transaction에 넣을 수 없고, aggregate도 억지로 합치기 어렵다면 **일시적 권리 확보**라는 중간 단계를 두는 방식이 자주 등장한다.

- reserve
- hold
- expire
- confirm
- release

이 패턴은 완전한 즉시 일관성 대신, **시간이 포함된 일관성 seam**을 설계하게 해준다.

그래서 hold는 "재고를 잠깐 빼는 테이블"이 아니라 `reservationId`, `expiresAt`, 현재 상태, confirm/release command의 idempotency key가 함께 움직이는 작은 workflow로 보는 편이 안전하다.

### Retrieval Anchors

- `reservation pattern`
- `hold expiry`
- `consistency seam`
- `inventory reservation`
- `temporary claim`
- `confirm or release`
- `workflow owner`

---

## 깊이 들어가기

### 1. reservation은 최종 확정이 아니라 임시 권리다

예약/홀드는 자원을 영구 소비한 것이 아니다.

- 재고를 확정 차감하지 않고 일정 시간 점유
- 좌석을 완전 판매하지 않고 잠시 홀드
- 쿠폰을 사용 완료가 아니라 사용 대기 상태로 둠

이렇게 하면 confirm 전까지 취소/실패/timeout에 대응할 공간이 생긴다.

### 2. 핵심은 "confirm or release"를 명확히 가지는 것이다

reservation이 악취가 되는 순간은 임시 상태만 만들고 종료 경로가 흐릴 때다.

- 언제 만료되는가
- 누가 만료를 판단하는가
- 성공 시 누가 확정하는가
- 실패 시 누가 release하는가

즉 reservation은 상태를 하나 더 늘리는 게 아니라 **수명 주기와 종료 책임을 명시하는 패턴**이다.

### 3. consistency seam은 보통 deadline과 함께 온다

reservation은 시간 없는 개념이 아니다.

- 10분 안에 결제 없으면 release
- 30초 안에 좌석 확정 없으면 expire
- 24시간 안에 승인 없으면 요청 종료

그래서 reservation pattern은 process manager, deadline, scheduler와 잘 붙는다.

### 4. aggregate 내부 규칙과 cross-boundary seam을 구분해야 한다

재고 aggregate 안에서는 "동일 수량을 두 번 reserve하면 안 된다" 같은 규칙이 즉시 일관성일 수 있다.  
하지만 주문 aggregate와 재고 aggregate 사이의 "결제 성공 시 최종 차감"은 별도의 seam이다.

이 둘을 섞으면 다음 문제가 생긴다.

- aggregate를 과도하게 키움
- transaction을 과도하게 길게 잡음
- 외부 실패를 rollback으로 해결하려 듦

### 5. reservation은 idempotency와 중복 해제까지 같이 봐야 한다

성공/실패보다 더 무서운 건 중복 메시지와 늦은 응답이다.

- 이미 확정된 hold를 다시 release
- 이미 만료된 hold를 뒤늦게 confirm
- retry 때문에 reserve가 중복 생성

그래서 reservation 식별자, 상태 전이 규칙, expire token 같은 운영 요소가 같이 필요하다.

---

## 실전 시나리오

### 시나리오 1: 주문과 재고

주문 생성 시 재고를 즉시 차감하지 않고 `InventoryReservation`을 만든다.  
결제 승인 시 confirm, 결제 실패나 timeout 시 release한다.

### 시나리오 2: 콘서트 좌석 홀드

좌석은 매우 짧은 시간 동안 hold되고, 시간이 지나면 자동 release된다.  
이때 stale payment success가 뒤늦게 와도 이미 만료된 hold면 확정하지 않아야 한다.

### 시나리오 3: 쿠폰 선점

한정 쿠폰은 결제 직전 선점하고, checkout 실패 시 반환한다.  
무기한 점유가 되지 않도록 expiry를 반드시 같이 둬야 한다.

---

## 코드로 보기

### reservation aggregate 감각

```java
public class InventoryReservation {
    private ReservationStatus status;
    private Instant expiresAt;

    public static InventoryReservation hold(
        ReservationId reservationId,
        ProductId productId,
        int quantity,
        Instant expiresAt
    ) {
        return new InventoryReservation(reservationId, productId, quantity, expiresAt);
    }

    public void confirm(Instant now) {
        if (now.isAfter(expiresAt)) {
            throw new IllegalStateException("reservation expired");
        }
        status = ReservationStatus.CONFIRMED;
    }

    public void release() {
        if (status == ReservationStatus.CONFIRMED) {
            throw new IllegalStateException("confirmed reservation cannot be released");
        }
        status = ReservationStatus.RELEASED;
    }
}
```

### process manager와 결합

```java
public class CheckoutProcessManager {
    public void on(OrderPlaced event) {
        commandBus.dispatch(new HoldInventoryCommand(event.orderId(), event.items()));
        commandBus.dispatch(new ScheduleReservationExpiryCommand(event.orderId(), event.expiresAt()));
    }

    public void on(PaymentApproved event) {
        commandBus.dispatch(new ConfirmInventoryReservationCommand(event.orderId()));
    }

    public void on(ReservationExpired event) {
        commandBus.dispatch(new CancelOrderCommand(event.orderId()));
    }
}
```

### seam 원칙

```java
// reserve는 최종 확정이 아니다.
// confirm 또는 release가 반드시 뒤따라야 한다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 일관성 강제 | 개념적으로 단순해 보인다 | 경계가 커지고 transaction이 길어진다 | 정말 같은 aggregate여야 할 때 |
| Reservation/Hold/Expiry | 경계를 유지한 채 실패를 흡수한다 | 상태와 타이머 관리가 필요하다 | 재고, 좌석, 쿠폰처럼 일시 점유가 가능한 자원 |
| 완전 낙관적 eventual consistency | 구조는 단순하다 | oversell/중복 사용 제어가 어려울 수 있다 | 충돌 비용이 낮고 보상이 쉬울 때 |

판단 기준은 다음과 같다.

- cross-boundary 즉시 일관성이 비싸면 reservation seam을 본다
- hold에는 expiry와 종료 책임을 반드시 붙인다
- confirm/release 흐름은 idempotent하게 설계한다

---

## 꼬리질문

> Q: reservation을 두면 결국 상태만 더 복잡해지는 것 아닌가요?
> 의도: 상태 추가와 실패 면적 감소의 교환을 이해하는지 본다.
> 핵심: 복잡도는 늘지만, 분산 실패와 time gap을 명시적으로 다룰 수 있게 된다.

> Q: reservation expiry는 누가 가져야 하나요?
> 의도: time boundary ownership을 생각하는지 본다.
> 핵심: 보통 장기 프로세스를 조율하는 process manager나 reservation owner가 명시적으로 소유해야 한다.

> Q: 이미 만료된 hold에 결제 성공 이벤트가 오면 어떻게 하나요?
> 의도: stale signal 처리 감각을 보는 질문이다.
> 핵심: confirm을 거부하고 보상/환불/재동기화 흐름으로 넘겨야 한다.

## 한 줄 정리

Reservation/Hold/Expiry는 cross-aggregate 즉시 일관성을 억지로 만들기보다, 임시 권리와 시간 경계를 통해 confirm-or-release seam을 설계하게 해주는 패턴이다.
