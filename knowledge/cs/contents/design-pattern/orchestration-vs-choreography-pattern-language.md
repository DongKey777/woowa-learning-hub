---
schema_version: 3
title: Orchestration vs Choreography Pattern Language
concept_id: design-pattern/orchestration-vs-choreography-pattern-language
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- orchestration-vs-choreography
- distributed-workflow-design
- event-driven-autonomy
aliases:
- orchestration vs choreography
- central coordinator
- event driven workflow
- distributed workflow design
- process manager
- service autonomy
- retry ownership
- workflow choreography
- 중앙 오케스트레이션
- 이벤트 자율 반응
symptoms:
- 분산 워크플로를 모두 중앙 coordinator로 몰거나, 반대로 핵심 상태 전이까지 owner 없는 choreography로 흩어버린다
- 알림/검색/통계 같은 부가 반응과 결제/재고/주문 같은 핵심 보상 경로를 같은 제어 방식으로 설계한다
- choreography의 낮은 결합도만 보고 전체 흐름 추적과 장애 분석 비용을 과소평가한다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- design-pattern/saga-coordinator-pattern-language
- design-pattern/domain-events-vs-integration-events
- design-pattern/observer-pubsub-application-events
next_docs:
- design-pattern/orchestration-vs-choreography-failure-handling
- design-pattern/process-manager-vs-saga-coordinator
- design-pattern/workflow-owner-vs-participant-context
linked_paths:
- contents/design-pattern/saga-coordinator-pattern-language.md
- contents/design-pattern/process-manager-vs-saga-coordinator.md
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/orchestration-vs-choreography-failure-handling.md
- contents/design-pattern/observer-pubsub-application-events.md
- contents/design-pattern/chain-of-responsibility-filters-interceptors.md
- contents/design-pattern/state-machine-library-vs-state-pattern.md
confusable_with:
- design-pattern/saga-coordinator-pattern-language
- design-pattern/orchestration-vs-choreography-failure-handling
- design-pattern/process-manager-vs-saga-coordinator
- design-pattern/observer-pubsub-application-events
forbidden_neighbors: []
expected_queries:
- Orchestration과 Choreography는 중앙 coordinator가 지휘하는 방식과 서비스가 이벤트에 자율 반응하는 방식으로 어떻게 달라?
- 결제 재고 주문처럼 실패 보상과 순서가 중요한 핵심 플로우는 orchestration이 더 맞는 이유가 뭐야?
- 주문 완료 후 알림 검색 인덱스 통계 같은 부가 반응은 choreography가 잘 맞는 이유가 뭐야?
- choreography는 결합도가 낮지만 전체 흐름 tracing과 장애 분석이 어려워지는 이유가 뭐야?
- 실무에서 핵심 경로는 orchestration, 부가 반응은 choreography로 혼합하는 기준은 뭐야?
contextual_chunk_prefix: |
  이 문서는 Orchestration vs Choreography chooser로, 분산 workflow에서 중앙 coordinator가
  step order와 compensation을 지휘하는 orchestration과 각 service가 integration event에 자율적으로
  반응하는 choreography를 제어 방식, coupling, tracing, failure ownership 기준으로 비교한다.
---
# Orchestration vs Choreography Pattern Language

> 한 줄 요약: Orchestration은 중앙이 흐름을 지휘하고, Choreography는 각 서비스가 이벤트에 반응하며 스스로 흐름을 맞춘다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Orchestration vs Choreography Failure Handling](./orchestration-vs-choreography-failure-handling.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [State Machine Library vs State Pattern](./state-machine-library-vs-state-pattern.md)

---

## 핵심 개념

분산 시스템에서 흐름을 맞추는 방식은 크게 둘이다.

- Orchestration: 중앙의 coordinator가 다음 단계를 지시한다
- Choreography: 각 서비스가 이벤트를 듣고 자기 일을 한다

둘은 단순한 구현 차이가 아니라 **책임 배치 방식**이다.

### Retrieval Anchors

- `orchestration vs choreography`
- `central coordinator`
- `event driven workflow`
- `distributed workflow design`
- `process manager`
- `time boundary ownership`
- `service autonomy`
- `retry ownership`

---

## 깊이 들어가기

### 1. Orchestration은 흐름이 선명하다

중앙 제어자가 있으면 다음이 쉬워진다.

- 실패 지점 파악
- 보상 순서 정의
- 운영 화면 구성

대신 coordinator가 비대해질 수 있다.

### 2. Choreography는 자율성이 높다

각 서비스가 이벤트에 반응하므로 결합도가 낮아진다.  
하지만 흐름 전체를 이해하기 어렵고, 장애 분석이 복잡해진다.

### 3. 정답은 도메인 복잡도에 따라 달라진다

- 단순하고 순서가 중요한 워크플로: orchestration
- 서비스 자율성이 중요한 이벤트 반응: choreography

---

## 실전 시나리오

### 시나리오 1: 주문 결제 플로우

오류 복구와 보상이 중요하면 orchestration이 좋다.

### 시나리오 2: 후속 알림과 집계

주문 완료 후 알림, 검색 인덱스 갱신, 통계 집계는 choreography가 잘 맞는다.

### 시나리오 3: 대규모 분산 시스템

둘을 혼합해 핵심 플로우는 orchestration, 부가 반응은 choreography로 분리할 수 있다.

---

## 코드로 보기

### Orchestration

```java
@Service
public class OrderCoordinator {
    public void placeOrder(OrderContext context) {
        reserveInventory(context);
        capturePayment(context);
        shipOrder(context);
    }
}
```

### Choreography

```java
@Component
public class OrderPlacedListener {
    @EventListener
    public void on(OrderPlacedEvent event) {
        // 각 서비스가 자기 일을 수행
    }
}
```

### 혼합

```java
// 핵심 흐름은 orchestration, 후속 반응은 choreography
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Orchestration | 흐름이 명확하다 | 중앙이 비대해진다 | 보상/순서가 중요할 때 |
| Choreography | 결합도가 낮다 | 흐름 추적이 어렵다 | 서비스 자율성이 중요할 때 |
| 혼합 | 균형이 좋다 | 설계가 복잡하다 | 대형 시스템 |

판단 기준은 다음과 같다.

- 실패와 보상이 핵심이면 orchestration
- 이벤트 반응이 핵심이면 choreography
- 둘 다 필요하면 혼합한다

---

## 꼬리질문

> Q: orchestration과 saga는 같은 건가요?
> 의도: 아키텍처 스타일과 패턴 언어를 구분하는지 확인한다.
> 핵심: saga는 워크플로 패턴이고 orchestration은 제어 방식이다.

> Q: choreography가 왜 디버깅이 어렵나요?
> 의도: 분산 이벤트 흐름의 추적 비용을 아는지 확인한다.
> 핵심: 이벤트가 여러 서비스로 흩어지기 때문이다.

> Q: 혼합 모델은 왜 자주 쓰이나요?
> 의도: 단일 해법의 한계를 이해하는지 확인한다.
> 핵심: 핵심 경로와 부가 반응의 요구가 다르기 때문이다.

## 한 줄 정리

Orchestration은 중앙이 흐름을 지휘하고, Choreography는 서비스가 이벤트에 반응하며 자율적으로 맞춘다.
