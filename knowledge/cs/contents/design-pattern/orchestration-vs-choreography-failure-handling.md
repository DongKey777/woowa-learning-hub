---
schema_version: 3
title: Orchestration vs Choreography Failure Handling
concept_id: design-pattern/orchestration-vs-choreography-failure-handling
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- workflow-failure-ownership
- retry-compensation-ownership
- reconciliation-owner
aliases:
- orchestration failure handling
- choreography failure handling
- retry ownership
- compensation ownership
- failure visibility
- distributed unknown state
- reconciliation ownership
- workflow failure owner
- local retry vs global semantics
- unknown state reconciliation
symptoms:
- orchestration과 choreography를 중앙 vs 분산 제어 방식으로만 보고 실패 감지, retry, compensation, reconciliation owner를 명시하지 않는다
- choreography에서 각 consumer가 알아서 retry하면 된다고 생각해 global business failure story가 분산된다
- unknown state를 누가 소유하고 reconciliation을 시작할지 정하지 않아 결제/재고/주문 상태가 서로 다르게 남는다
intents:
- troubleshooting
- design
- comparison
prerequisites:
- design-pattern/orchestration-vs-choreography-pattern-language
- design-pattern/saga-coordinator-pattern-language
- design-pattern/compensation-vs-reconciliation-pattern
next_docs:
- design-pattern/workflow-owner-vs-participant-context
- design-pattern/process-manager-vs-saga-coordinator
- design-pattern/reservation-hold-expiry-consistency-seam
linked_paths:
- contents/design-pattern/orchestration-vs-choreography-pattern-language.md
- contents/design-pattern/saga-coordinator-pattern-language.md
- contents/design-pattern/process-manager-vs-saga-coordinator.md
- contents/design-pattern/compensation-vs-reconciliation-pattern.md
- contents/design-pattern/workflow-owner-vs-participant-context.md
confusable_with:
- design-pattern/orchestration-vs-choreography-pattern-language
- design-pattern/compensation-vs-reconciliation-pattern
- design-pattern/workflow-owner-vs-participant-context
- design-pattern/process-manager-vs-saga-coordinator
forbidden_neighbors: []
expected_queries:
- Orchestration과 Choreography의 차이는 failure visibility와 retry compensation reconciliation ownership에서 어떻게 드러나?
- choreography에서 각 서비스가 local retry를 하면 global failure semantics가 왜 더 중요해져?
- 결제 unknown state와 재고 release 시점을 누가 판단해야 하는지 workflow owner를 정해야 하는 이유가 뭐야?
- 핵심 금전 재고 상태 변경은 central failure policy에 두고 알림 검색 통계는 local best-effort로 둘 수 있는 기준은 뭐야?
- unknown state를 reconciliation trigger로 넘길 owner가 없으면 어떤 운영 문제가 생겨?
contextual_chunk_prefix: |
  이 문서는 Orchestration vs Choreography Failure Handling playbook으로, 중앙 제어냐
  이벤트 자율 반응이냐보다 실패를 누가 감지하고 retry, compensation, reconciliation, unknown state
  decision을 소유하는지가 더 중요하다는 기준을 설명한다.
---
# Orchestration vs Choreography Failure Handling

> 한 줄 요약: orchestration과 choreography의 차이는 흐름 제어 방식만이 아니라, 실패를 어디서 감지하고 누가 retry/compensation/reconciliation을 책임지는가의 차이이기도 하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Orchestration vs Choreography Pattern Language](./orchestration-vs-choreography-pattern-language.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Compensation vs Reconciliation Pattern](./compensation-vs-reconciliation-pattern.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)

---

## 핵심 개념

많은 자료가 orchestration과 choreography를 "중앙 vs 분산" 정도로만 설명한다.  
실무에서 더 중요한 차이는 실패 처리다.

- 누가 실패를 감지하는가
- 누가 retry 정책을 가진가
- 누가 compensation을 시작하는가
- unknown state를 누가 reconciliation으로 넘기는가

즉 제어 방식 차이는 곧 failure-handling ownership 차이이기도 하다.

### Retrieval Anchors

- `orchestration failure handling`
- `choreography failure handling`
- `retry ownership`
- `compensation ownership`
- `failure visibility`
- `distributed unknown state`

---

## 깊이 들어가기

### 1. orchestration은 failure visibility가 높다

중앙 coordinator/owner가 있으면 다음이 쉽다.

- 어느 단계에서 실패했는지 추적
- 어떤 보상을 시작할지 결정
- timeout/unknown state를 한곳에서 해석

대신 owner가 failure policy까지 빨아들이며 비대해질 수 있다.

### 2. choreography는 local autonomy 대신 failure interpretation이 흩어진다

각 서비스가 이벤트에 반응하면 결합은 낮다.  
하지만 실패 의미도 여러 곳으로 퍼진다.

- 한 consumer는 retry
- 다른 consumer는 skip
- 또 다른 consumer는 unknown을 dead-letter

이렇게 되면 전체 비즈니스 흐름 관점의 failure story를 설명하기 어려워진다.

### 3. unknown state는 choreography에서 특히 더 위험하다

이벤트 누락/지연/순서 뒤바뀜이 생기면 각 participant는 자기 local truth만 본다.

- 누군가는 이미 완료로 봄
- 누군가는 아직 대기 중으로 봄
- 누군가는 실패로 간주

이때 owner 없는 choreography는 reconciliation trigger를 놓치기 쉽다.

### 4. retry를 분산시키면 성공률은 오르지만 blast radius도 커진다

choreography에서는 각 consumer가 독립 retry하기 쉽다.  
하지만 그 결과:

- 중복 호출이 여러 방향으로 생기고
- backoff 전략이 제각각이며
- compensation 시점이 어긋난다

반대로 orchestration은 retry 정책을 중앙화할 수 있지만, throughput과 coupling 비용이 있다.

### 5. hybrid model에서는 failure ownership을 명시해야 한다

실무에서는 보통 혼합 모델이 많다.

- 핵심 금전 흐름: orchestration
- 부가 반응: choreography

이때 중요한 건 어디까지가 central failure policy인지, 어디부터 local best-effort인지 문서화하는 것이다.

---

## 실전 시나리오

### 시나리오 1: 결제-재고-배송

핵심 단계와 보상이 중요한 흐름은 orchestration이 더 적합하다.  
결제 unknown state와 재고 release 시점을 한 owner가 판단하는 편이 낫다.

### 시나리오 2: 알림, 검색 인덱스, 통계

주문 완료 후 부가 반응은 choreography가 잘 맞는다.  
실패 시 전체 비즈니스 흐름을 되돌릴 필요가 없기 때문이다.

### 시나리오 3: 외부 webhook 기반 확장

외부 consumer가 많은 이벤트는 choreography가 자연스럽지만, 핵심 도메인 state까지 그에 기대면 failure diagnosis가 어려워진다.

---

## 코드로 보기

### orchestration failure ownership

```java
public class CheckoutCoordinator {
    public void onPaymentFailed(PaymentFailed event) {
        commandBus.dispatch(new ReleaseInventoryReservation(event.orderId()));
        commandBus.dispatch(new MarkCheckoutFailed(event.orderId()));
    }
}
```

### choreography local failure ownership

```java
public class SearchProjectionConsumer {
    public void on(OrderCompleted event) {
        // local retry / dead-letter / rebuild
    }
}
```

### hybrid rule

```java
// 금전/재고/법적 상태를 바꾸는 핵심 경로는 중앙 실패 정책,
// 알림/통계/검색은 local best-effort로 두는 식의 구분이 흔하다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Orchestration 중심 | failure visibility와 compensation ownership이 선명하다 | 중앙이 비대해질 수 있다 | 핵심 상태 전이, 금전 흐름 |
| Choreography 중심 | 자율성과 확장성이 높다 | failure story가 분산된다 | 부가 반응, 느슨한 이벤트 반응 |
| Hybrid | 균형이 좋다 | ownership 문서화가 필요하다 | 대부분의 실무 시스템 |

판단 기준은 다음과 같다.

- 실패 해석이 비즈니스 상태를 크게 바꾸면 orchestration 쪽
- local best-effort면 choreography 쪽
- unknown state와 reconciliation trigger owner를 명시한다

---

## 꼬리질문

> Q: choreography면 각 서비스가 알아서 retry하면 되는 것 아닌가요?
> 의도: local retry와 global failure semantics를 구분하는지 본다.
> 핵심: 아니다. retry가 많아질수록 전체 비즈니스 흐름 관점의 해석이 더 중요해진다.

> Q: orchestration이 항상 더 안전한가요?
> 의도: 중앙화의 비용도 같이 보는지 본다.
> 핵심: 아니다. 핵심 경로엔 좋지만 모든 부가 반응까지 중앙화하면 coupling이 커진다.

> Q: unknown state는 누가 가져야 하나요?
> 의도: reconciliation ownership을 생각하는지 본다.
> 핵심: 보통 workflow owner나 central failure policy가 가져가는 편이 더 설명 가능하다.

## 한 줄 정리

Orchestration과 choreography의 핵심 차이는 제어 방식뿐 아니라, 실패를 누가 해석하고 retry/compensation/reconciliation을 누가 책임지는가에 있다.
