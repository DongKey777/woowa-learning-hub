---
schema_version: 3
title: Saga / Coordinator Pattern Language
concept_id: design-pattern/saga-coordinator-pattern-language
canonical: true
category: design-pattern
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- saga-coordinator
- distributed-workflow
- compensation
aliases:
- saga coordinator
- saga pattern
- distributed workflow compensation
- local transaction
- distributed transaction boundary
- cross aggregate workflow
- orchestration vs choreography
- process manager
- workflow owner
- 보상 트랜잭션
symptoms:
- 여러 서비스에 걸친 주문 결제 재고 배송 흐름을 하나의 전역 DB transaction처럼 rollback하려고 한다
- 이미 commit된 local transaction을 되돌리는 비즈니스 보상을 DB rollback과 같은 것으로 설명한다
- Saga Coordinator에 모든 단계, 정책, 재시도, 보상을 몰아넣어 또 다른 God Object가 된다
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/unit-of-work-pattern
- design-pattern/domain-events-vs-integration-events
next_docs:
- design-pattern/process-manager-vs-saga-coordinator
- design-pattern/orchestration-vs-choreography-failure-handling
- design-pattern/compensation-vs-reconciliation-pattern
linked_paths:
- contents/design-pattern/aggregate-boundary-vs-transaction-boundary.md
- contents/design-pattern/unit-of-work-pattern.md
- contents/design-pattern/domain-events-vs-integration-events.md
- contents/design-pattern/domain-event-translation-pipeline.md
- contents/design-pattern/outbox-relay-idempotent-publisher.md
- contents/design-pattern/orchestration-vs-choreography-failure-handling.md
- contents/design-pattern/compensation-vs-reconciliation-pattern.md
- contents/design-pattern/process-manager-vs-saga-coordinator.md
- contents/design-pattern/process-manager-deadlines-timeouts.md
confusable_with:
- design-pattern/process-manager-vs-saga-coordinator
- design-pattern/orchestration-vs-choreography-pattern-language
- design-pattern/compensation-vs-reconciliation-pattern
- design-pattern/aggregate-boundary-vs-transaction-boundary
forbidden_neighbors: []
expected_queries:
- Saga Coordinator는 여러 local transaction을 전역 transaction 대신 단계 실행과 compensation으로 어떻게 조율해?
- Saga의 보상 작업은 이미 commit된 일을 비즈니스적으로 상쇄하는 것이지 DB rollback이 아닌 이유가 뭐야?
- 주문 결제 재고 배송처럼 단계 순서와 실패 보상이 중요한 플로우에는 왜 coordinator가 유리해?
- Saga와 choreography는 failure visibility와 tracing 관점에서 어떻게 달라?
- Coordinator가 비대해지면 state machine이나 process manager로 나눠야 하는 신호는 뭐야?
contextual_chunk_prefix: |
  이 문서는 Saga / Coordinator Pattern Language deep dive로, 한 DB transaction으로
  묶을 수 없는 주문, 결제, 재고, 배송 같은 distributed workflow를 local transaction,
  step execution, compensation command, outbox/event, workflow owner로 조율하는 패턴을 설명한다.
---
# Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어

> 한 줄 요약: Saga와 Coordinator는 여러 서비스에 걸친 비즈니스 흐름을 전역 트랜잭션 대신 단계적 보상과 상태 관리로 다루는 패턴 언어다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Boundary vs Transaction Boundary](./aggregate-boundary-vs-transaction-boundary.md)
> - [Unit of Work Pattern: 트랜잭션 경계 안에서 변경을 모으기](./unit-of-work-pattern.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Orchestration vs Choreography Failure Handling](./orchestration-vs-choreography-failure-handling.md)
> - [Compensation vs Reconciliation Pattern](./compensation-vs-reconciliation-pattern.md)
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Reservation, Hold, and Expiry as a Consistency Seam](./reservation-hold-expiry-consistency-seam.md)
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [Command Pattern, Undo, Queue](./command-pattern-undo-queue.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Saga는 **여러 로컬 트랜잭션을 순서대로 실행하고, 중간 실패 시 보상 작업으로 되돌리는 분산 워크플로**다.  
Coordinator는 이 흐름을 중앙에서 오케스트레이션하는 역할을 한다.

둘은 패턴 하나로만 이해하면 부족하다. 실제 backend에서는 다음 요소들이 함께 움직인다.

- 상태 패턴으로 각 단계의 전이 상태를 관리한다
- Command 패턴으로 각 작업과 보상을 캡슐화한다
- 이벤트로 단계 간 통지를 전달한다
- 포트와 어댑터로 외부 시스템을 분리한다

### Retrieval Anchors

- `saga coordinator`
- `distributed workflow compensation`
- `local transaction`
- `distributed transaction boundary`
- `cross aggregate workflow`
- `orchestration vs choreography`
- `process manager`
- `integration event`
- `outbox pattern`
- `deadline workflow`
- `reservation pattern`
- `at least once publish`
- `workflow owner`
- `compensation vs reconciliation`
- `retry ownership`

---

## 깊이 들어가기

### 1. 전역 트랜잭션이 안 될 때 등장한다

마이크로서비스나 외부 시스템 연동에서는 한 번의 DB 트랜잭션으로 모든 것을 묶기 어렵다.
그럴 때 Saga가 등장한다.

- 주문 생성
- 재고 예약
- 결제 승인
- 배송 요청

이 중 하나라도 실패하면 앞 단계의 성공을 되돌리는 보상이 필요하다.

### 2. Coordinator와 Choreography는 다르다

| 구분 | Coordinator | Choreography |
|---|---|---|
| 제어 방식 | 중앙에서 흐름을 지휘 | 이벤트로 각 서비스가 자율 반응 |
| 추적성 | 높다 | 낮아질 수 있다 |
| 결합도 | 상대적으로 높다 | 상대적으로 낮다 |
| 운영 난이도 | 흐름은 명확 | 분산 추적이 필요하다 |

대형 결제/주문 흐름은 Coordinator가, 느슨한 도메인 통지는 Choreography가 더 맞는 경우가 많다.

### 3. 보상은 rollback과 다르다

보상 작업은 데이터베이스 rollback이 아니다.

- 이미 커밋된 로컬 트랜잭션을 상쇄한다
- 외부 시스템에는 역행 동작이 없을 수도 있다
- 완전한 원상복구가 아니라 비즈니스적으로 상쇄한다

그래서 보상은 "취소", "반려", "환불" 같은 도메인 언어로 모델링해야 한다.

---

## 실전 시나리오

### 시나리오 1: 주문-결제-재고-배송

주문 서비스가 중앙에서 흐름을 관리하고, 각 서비스는 자기 일만 처리한다.
결제 실패 시 재고 예약을 취소하고 주문을 실패 상태로 바꾼다.

### 시나리오 2: 환불 워크플로

환불 승인, PG 환불, 포인트 회수, 쿠폰 회수는 각각 실패 가능성이 다르다.
Saga를 쓰면 단계별 보상을 명시할 수 있다.

### 시나리오 3: 외부 API가 느리거나 불안정할 때

동기 체인으로 전부 묶으면 타임아웃이 커진다.
Coordinator와 outbox를 함께 쓰면 재시도와 추적이 쉬워진다.

---

## 코드로 보기

### 단순한 Coordinator

```java
@Service
public class OrderSagaCoordinator {
    private final InventoryPort inventoryPort;
    private final PaymentPort paymentPort;
    private final ShippingPort shippingPort;

    public OrderSagaCoordinator(
        InventoryPort inventoryPort,
        PaymentPort paymentPort,
        ShippingPort shippingPort
    ) {
        this.inventoryPort = inventoryPort;
        this.paymentPort = paymentPort;
        this.shippingPort = shippingPort;
    }

    public void placeOrder(OrderSagaContext context) {
        inventoryPort.reserve(context.orderId(), context.items());
        try {
            paymentPort.pay(context.paymentRequest());
            shippingPort.createShipment(context.shippingRequest());
        } catch (RuntimeException ex) {
            inventoryPort.release(context.orderId());
            throw ex;
        }
    }
}
```

### 보상 명령

```java
public interface SagaStep {
    void execute();
    void compensate();
}

public class ReserveInventoryStep implements SagaStep {
    @Override
    public void execute() {
        // 재고 예약
    }

    @Override
    public void compensate() {
        // 예약 해제
    }
}
```

### 이벤트 기반 단계

```java
@Component
public class OrderPlacedListener {
    @EventListener
    public void on(OrderPlacedEvent event) {
        // 다음 단계 트리거
    }
}
```

여기서 중요한 것은 "이벤트를 쓰느냐"가 아니라 **어떤 단계가 실패해도 안전하게 이어질 수 있는가**다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 DB 트랜잭션 | 단순하고 강하다 | 경계를 넘지 못한다 | 한 서비스 안에서 끝날 때 |
| Saga + Coordinator | 흐름 제어가 쉽다 | 오케스트레이터가 비대해질 수 있다 | 주문/결제/재고처럼 명확한 플로우 |
| Choreography | 서비스 자율성이 높다 | 추적과 장애 분석이 어렵다 | 이벤트 기반 도메인 통지 |

판단 기준은 다음과 같다.

- 실패 시 보상이 필요하면 Saga를 본다
- 단계 순서가 중요하면 Coordinator를 본다
- 서비스 간 독립성이 더 중요하면 Choreography를 본다

---

## 꼬리질문

> Q: Saga와 DB 트랜잭션의 차이는 무엇인가요?
> 의도: 데이터베이스 롤백과 비즈니스 보상을 혼동하지 않는지 확인한다.
> 핵심: Saga는 이미 커밋된 단계들을 도메인적으로 상쇄한다.

> Q: Coordinator가 커지면 왜 문제가 되나요?
> 의도: 오케스트레이터가 또 다른 God Object가 될 수 있음을 아는지 확인한다.
> 핵심: 단계가 많아지면 흐름 자체를 상태 머신이나 서브 워크플로로 나눠야 한다.

> Q: Saga를 쓰면 무조건 이벤트가 필요한가요?
> 의도: 패턴 조합을 절대 규칙으로 외우지 않는지 확인한다.
> 핵심: 아니다. 동기 조율도 가능하지만, 재시도와 분산 추적을 위해 이벤트가 자주 함께 쓰인다.

## 한 줄 정리

Saga와 Coordinator는 분산 환경에서 전역 트랜잭션 대신 단계별 실행과 보상을 설계하게 해주는 패턴 언어다.
