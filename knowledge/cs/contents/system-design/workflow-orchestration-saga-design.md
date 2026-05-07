---
schema_version: 3
title: Workflow Orchestration + Saga 설계
concept_id: system-design/workflow-orchestration-saga-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- workflow orchestration
- saga
- compensation
- state machine
aliases:
- workflow orchestration
- saga
- compensation
- state machine
- approval workflow
- human in the loop
- repair campaign
- long running operation
- orchestration engine
- timeout policy
- Workflow Orchestration + Saga 설계
- workflow orchestration saga design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/system-design-framework.md
- contents/system-design/back-of-envelope-estimation.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/database/transaction-case-studies.md
- contents/database/idempotency-key-and-deduplication.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/system-design/replay-repair-orchestration-control-plane-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Workflow Orchestration + Saga 설계 설계 핵심을 설명해줘
- workflow orchestration가 왜 필요한지 알려줘
- Workflow Orchestration + Saga 설계 실무 트레이드오프는 뭐야?
- workflow orchestration 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Workflow Orchestration + Saga 설계를 다루는 deep_dive 문서다. 여러 서비스가 관여하는 업무 흐름은 하나의 트랜잭션으로 묶지 말고, orchestration과 compensation으로 상태 전이를 관리해야 한다. 검색 질의가 workflow orchestration, saga, compensation, state machine처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Workflow Orchestration + Saga 설계

> 한 줄 요약: 여러 서비스가 관여하는 업무 흐름은 하나의 트랜잭션으로 묶지 말고, orchestration과 compensation으로 상태 전이를 관리해야 한다.

retrieval-anchor-keywords: workflow orchestration, saga, compensation, state machine, approval workflow, human in the loop, repair campaign, long running operation, orchestration engine, timeout policy

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Outbox, Saga, Eventual Consistency](../software-engineering/outbox-inbox-domain-events.md)
> - [Transaction 실전 시나리오](../database/transaction-case-studies.md)
> - [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)

---

## 핵심 개념

워크플로우 오케스트레이션은 "업무 순서"를 코드/상태 머신으로 관리하는 것이다.  
Saga는 그 과정에서 여러 로컬 트랜잭션을 묶고, 실패 시 compensation으로 되돌리는 패턴이다.

이 패턴이 필요한 이유는 명확하다.

- 결제, 재고, 배송, 알림이 서로 다른 서비스에 있다.
- 하나의 DB 트랜잭션으로 묶을 수 없다.
- 중간 실패를 허용하면서도 사용자 경험을 유지해야 한다.

### 두 가지 스타일

| 방식 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Orchestration | 흐름이 명시적이다 | 오케스트레이터가 복잡해진다 | 업무 순서가 중요할 때 |
| Choreography | 서비스 간 결합이 낮다 | 흐름 추적이 어렵다 | 이벤트 중심 도메인 |

---

## 깊이 들어가기

### 1. 상태 머신

Saga는 결국 상태 머신이다.

- `PENDING`
- `PAYMENT_DONE`
- `RESERVED`
- `SHIPPED`
- `COMPENSATED`
- `FAILED`

각 단계는 로컬 트랜잭션이어야 하고, 각 이벤트는 idempotent해야 한다.

### 2. Orchestrator 역할

오케스트레이터는 다음을 담당한다.

- 다음 단계 호출
- 타임아웃 관리
- 재시도 정책
- 보상 트리거
- 최종 상태 기록

오케스트레이터가 너무 똑똑해지면, 결국 분산 모놀리스가 된다.  
그래서 흐름은 명시하되 비즈니스 규칙은 각 서비스에 남겨야 한다.

### 3. 실패와 보상

모든 실패가 rollback은 아니다.

- 결제 성공 후 재고 실패 -> 결제 취소
- 재고 성공 후 배송 실패 -> 재고 복구
- 알림 실패 -> 보상보다 재시도/보류가 적절할 수 있음

보상은 "원래 상태로 완전히 되돌리기"가 아니라 **업무적으로 허용 가능한 수정 작업**이다.

### 4. Outbox와 Inbox

Saga는 이벤트 전달이 안정적이어야 한다.  
그때 필요한 것이 outbox/inbox다.

- outbox: 로컬 트랜잭션과 이벤트 발행을 같이 기록
- inbox: 중복 메시지를 한 번만 처리

이 문맥은 [Outbox, Saga, Eventual Consistency](../software-engineering/outbox-inbox-domain-events.md)와 직결된다.

### 5. 장애 허용 구간

워크플로우 설계에서 중요한 질문은 "어디까지 기다릴 수 있는가"다.

- 결제는 즉시성 요구가 높다.
- 배송은 몇 초~몇 분 지연이 허용될 수 있다.
- 알림은 eventual하게 도달하면 된다.

따라서 step별 SLA가 달라야 한다.

### 6. 관측성

워크플로우는 추적이 어려우므로 다음이 필요하다.

- correlation id
- step별 상태 로그
- timeout/ retry count
- dead letter queue
- 운영 대시보드

---

## 실전 시나리오

### 시나리오 1: 주문-결제-재고-배송

흐름:

1. 주문 생성
2. 결제 승인
3. 재고 예약
4. 배송 요청
5. 완료

실패 시:

- 결제 실패 -> 주문 실패
- 재고 실패 -> 결제 취소
- 배송 실패 -> 재고 해제 + 결제 취소 여부 판단

### 시나리오 2: 환불 워크플로우

환불은 역순 처리와 보상이 섞인다.

- 결제 취소
- 포인트 회수
- 쿠폰 복구
- 알림 발송

### 시나리오 3: 휴먼 인 더 루프

일부 워크플로우는 자동 실패보다 승인 대기 상태가 더 적절하다.

- 이상 거래 검토
- 수동 환불 승인
- 운영자 재처리

---

## 코드로 보기

```pseudo
state = getState(orderId)

switch state:
  case PENDING:
    callPayment()
  case PAYMENT_DONE:
    reserveInventory()
  case RESERVED:
    requestShipping()
  case SHIPPED:
    markComplete()
```

```java
public void advance(String orderId) {
    WorkflowState state = workflowRepository.get(orderId);
    switch (state) {
        case PENDING -> paymentService.approve(orderId);
        case PAYMENT_DONE -> inventoryService.reserve(orderId);
        case RESERVED -> shippingService.request(orderId);
        case SHIPPED -> workflowRepository.complete(orderId);
        default -> throw new IllegalStateException("invalid state");
    }
}
```

### 보상 예시

```java
public void compensate(String orderId, WorkflowState failedAt) {
    if (failedAt.ordinal() >= WorkflowState.PAYMENT_DONE.ordinal()) {
        paymentService.cancel(orderId);
    }
    if (failedAt.ordinal() >= WorkflowState.RESERVED.ordinal()) {
        inventoryService.release(orderId);
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Saga orchestration | 흐름이 명확하다 | 오케스트레이터가 커진다 | 주문/환불/승인 흐름 |
| Choreography | 결합이 낮다 | 디버깅이 어렵다 | 이벤트 중심 도메인 |
| 강한 분산 트랜잭션 | 일관성이 높다 | 사실상 확장 어렵다 | 매우 제한적 |
| 단순 async chain | 구현이 쉽다 | 실패 복구가 약하다 | 작은 비즈니스 흐름 |

핵심은 "분산 트랜잭션을 대체하는 패턴"이 아니라, **업무적으로 허용 가능한 실패 모델을 설계하는 방식**이라는 점이다.

---

## 꼬리질문

> Q: Saga면 결국 롤백이 되는 건가요?
> 의도: compensation과 rollback을 구분하는지 확인
> 핵심: 아니다. compensation은 업무 보정이고, DB rollback과 다르다.

> Q: choreography보다 orchestration이 항상 낫나요?
> 의도: 패턴 선택 기준 이해 여부 확인
> 핵심: 아니다. 흐름 추적과 제어가 중요하면 orchestration, 결합 최소화가 중요하면 choreography다.

## 한 줄 정리

Saga는 분산 시스템에서 로컬 트랜잭션과 보상 작업을 조합해 업무 흐름을 안전하게 전진시키는 상태 머신이다.
