---
schema_version: 3
title: Process Manager vs Saga Coordinator
concept_id: design-pattern/process-manager-vs-saga-coordinator
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- process-manager
- saga-coordinator
- long-running-workflow
aliases:
- process manager
- saga coordinator
- process manager vs saga coordinator
- long running workflow
- event driven process state
- compensation orchestration
- timeout reminder workflow
- deadline signal
- workflow recovery
- human approval workflow
symptoms:
- Saga Coordinator와 Process Manager를 모두 긴 흐름 조율이라고만 보고 보상 중심인지 장기 상태/타이머 중심인지 구분하지 못한다
- 며칠 동안 이어지는 approval, timeout, retry state를 단발성 coordinator 메서드 안에 억지로 넣는다
- Process Manager라는 이름 아래 상태 저장, 이벤트 해석, 명령 발행, 보상 정책을 한 클래스에 몰아넣는다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- design-pattern/saga-coordinator-pattern-language
- design-pattern/orchestration-vs-choreography-pattern-language
- design-pattern/command-bus-pattern
next_docs:
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/process-manager-state-store-recovery
- design-pattern/human-approval-manual-review-workflow-pattern
linked_paths:
- contents/design-pattern/saga-coordinator-pattern-language.md
- contents/design-pattern/orchestration-vs-choreography-pattern-language.md
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/process-manager-state-store-recovery.md
- contents/design-pattern/human-approval-manual-review-workflow-pattern.md
- contents/design-pattern/workflow-owner-vs-participant-context.md
- contents/design-pattern/reservation-hold-expiry-consistency-seam.md
- contents/design-pattern/state-machine-library-vs-state-pattern.md
- contents/design-pattern/command-bus-pattern.md
- contents/design-pattern/domain-events-vs-integration-events.md
confusable_with:
- design-pattern/saga-coordinator-pattern-language
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/process-manager-state-store-recovery
- design-pattern/workflow-owner-vs-participant-context
forbidden_neighbors: []
expected_queries:
- Process Manager와 Saga Coordinator는 보상 중심 step orchestration과 장기 event-driven state 관리 관점에서 어떻게 달라?
- 며칠 이상 이어지는 workflow, timeout, reminder, human approval이 있으면 Process Manager가 더 맞는 이유가 뭐야?
- 짧고 명확한 주문 결제 재고 보상 플로우는 Saga Coordinator로 보는 기준이 뭐야?
- Process Manager가 모든 정책을 빨아들이는 God Object가 되지 않게 상태 모델과 decision policy를 어떻게 나눠?
- Saga와 Process Manager를 함께 쓰는 hand-off 지점은 어떻게 정해?
contextual_chunk_prefix: |
  이 문서는 Process Manager vs Saga Coordinator chooser로, Saga Coordinator는
  단계 실행, 보상, 재시도를 지휘하는 짧은 distributed workflow에 가깝고, Process Manager는
  이벤트를 받으며 장기 상태, timeout, reminder, human approval, recovery를 기억하고 다음 command를
  결정하는 프로세스 상태 기계에 가깝다는 기준을 설명한다.
---
# Process Manager vs Saga Coordinator

> 한 줄 요약: Saga Coordinator는 단계 실행과 보상을 지휘하는 데 초점을 두고, Process Manager는 이벤트를 들으며 장기 상태를 유지하고 다음 명령을 결정하는 도메인 프로세스에 가깝다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Orchestration vs Choreography Pattern Language](./orchestration-vs-choreography-pattern-language.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Process Manager State Store and Recovery Pattern](./process-manager-state-store-recovery.md)
> - [Human Approval and Manual Review Workflow Pattern](./human-approval-manual-review-workflow-pattern.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Reservation, Hold, and Expiry as a Consistency Seam](./reservation-hold-expiry-consistency-seam.md)
> - [State Machine Library vs State Pattern](./state-machine-library-vs-state-pattern.md)
> - [Command Bus Pattern](./command-bus-pattern.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)

---

## 핵심 개념

두 용어는 모두 "긴 흐름을 조율한다"는 점 때문에 자주 섞인다.  
하지만 중심 관심사가 다르다.

- Saga Coordinator: 여러 local transaction의 순서, 보상, 재시도를 중앙에서 지휘
- Process Manager: 이벤트를 받으며 장기 상태를 기억하고 다음 커맨드를 결정

즉 saga coordinator가 **실행 순서와 실패 보상**에 더 가깝다면, process manager는 **시간을 가로지르는 도메인 프로세스의 상태 기계**에 더 가깝다.

### Retrieval Anchors

- `process manager`
- `saga coordinator`
- `long running workflow`
- `event driven process state`
- `compensation orchestration`
- `timeout reminder workflow`
- `deadline signal`
- `timer version`
- `reservation seam`
- `workflow owner`
- `participant context`
- `workflow recovery`
- `human approval workflow`

---

## 깊이 들어가기

### 1. Saga Coordinator는 보통 step 중심으로 사고한다

Coordinator는 다음 질문에 강하다.

- 지금 어떤 단계를 실행해야 하는가
- 실패하면 어떤 보상을 호출해야 하는가
- 전체 플로우 진행 상황을 어디서 추적할 것인가

주문, 결제, 재고, 배송처럼 명확한 단계형 플로우에서는 이해하기 쉽다.

### 2. Process Manager는 이벤트와 시간의 흐름을 다룬다

Process Manager는 단발성 요청보다 더 긴 맥락을 기억한다.

- KYC 제출 후 24시간 내 미응답이면 리마인드 발송
- 대출 심사 서류가 모두 모이면 다음 단계 시작
- 결제 재시도 후 3회 실패하면 수동 검토 큐로 보냄

이 경우 핵심은 즉시 보상보다 "어떤 사건이 누적되면 다음 명령을 낼까"다.

### 3. 경계 신호가 다르다

다음 신호면 Saga Coordinator가 더 잘 맞는다.

- 단계 순서가 뚜렷하다
- 실패 시 보상 순서가 명확하다
- 전체 플로우가 비교적 짧다

다음 신호면 Process Manager가 더 잘 맞는다.

- 며칠 이상 이어지는 장기 프로세스다
- 외부 이벤트가 비동기적으로 도착한다
- timeout, reminder, human approval이 섞인다
- 중간 상태를 저장하고 재개해야 한다

### 4. Process Manager도 결국 God Object가 될 수 있다

Process Manager라는 이름만 붙이고 모든 정책을 한 클래스에 몰아넣으면 coordinator 비대화와 같은 문제가 생긴다.

- 상태 저장 책임
- 이벤트 해석 책임
- 명령 발행 책임
- 보상 정책

이걸 한 클래스가 모두 가지면 다시 거대한 workflow object가 된다.  
상태 모델, decision policy, command emitter를 나누는 편이 낫다.

### 5. 둘은 배타적이지 않다

실무에서는 process manager가 saga step을 시작하거나, saga가 특정 단계에서 process manager에 hand-off할 수 있다.

예를 들어:

- checkout 승인 흐름은 saga coordinator
- 미입금 30분 타임아웃과 재알림은 process manager

즉 핵심 질문은 "이 흐름의 중심 복잡도가 보상인가, 장기 상태 관리인가"다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 후 재고/결제/배송

즉시 단계 실행과 보상이 핵심이라면 Saga Coordinator가 자연스럽다.

### 시나리오 2: 대출 심사 워크플로

서류 제출, 신용 조회, 수동 승인, 추가 문서 요청, 기한 초과 처리는 Process Manager가 더 어울린다.  
며칠 동안 상태를 기억해야 하기 때문이다.

### 시나리오 3: 멤버십 결제 실패 재시도

실패 후 1일, 3일, 7일 재시도 정책과 알림, 최종 해지가 붙으면 Process Manager 성격이 강해진다.  
초기 결제 승인 자체는 saga step으로 볼 수 있다.

---

## 코드로 보기

### Saga Coordinator의 감각

```java
public class CheckoutSagaCoordinator {
    public void execute(CheckoutContext context) {
        inventoryPort.reserve(context.orderId(), context.items());
        try {
            paymentPort.approve(context.paymentRequest());
            shippingPort.createShipment(context.shippingRequest());
        } catch (RuntimeException ex) {
            inventoryPort.release(context.orderId());
            throw ex;
        }
    }
}
```

### Process Manager의 감각

```java
public class BillingRetryProcessManager {
    private RetryState state;

    public void on(PaymentFailed event) {
        state = state.registerFailure(event.failedAt());
        commandBus.send(new ScheduleRetryCommand(event.subscriptionId(), state.nextRetryAt()));
    }

    public void on(RetryTimeoutExpired event) {
        if (state.canRetryNow()) {
            commandBus.send(new RetryPaymentCommand(event.subscriptionId()));
        }
    }

    public void on(PaymentSucceeded event) {
        state = state.markCompleted(event.succeededAt());
    }
}
```

### 상태 저장이 핵심

```java
// Process Manager는 "현재 몇 번째 실패인지", "다음 타이머가 언제인지" 같은
// 장기 상태를 저장하고 재개할 수 있어야 한다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Saga Coordinator | 단계와 보상이 선명하다 | 장기 상태와 타이머 처리에는 어색할 수 있다 | 짧고 명확한 분산 워크플로 |
| Process Manager | 장기 상태, 타이머, 인간 개입을 다루기 쉽다 | 상태 모델링과 운영 복잡도가 크다 | 며칠 이상 이어지는 프로세스 |
| 혼합 | 복잡도를 역할별로 분산한다 | 경계 설계가 필요하다 | 짧은 보상 흐름과 긴 후속 흐름이 함께 있을 때 |

판단 기준은 다음과 같다.

- 보상과 단계 순서가 중심이면 saga coordinator
- 시간, 이벤트 누적, 재개 가능성이 중심이면 process manager
- 두 복잡도가 모두 있으면 hand-off 지점을 명시한다

---

## 꼬리질문

> Q: Process Manager와 Saga는 같은 말 아닌가요?
> 의도: 긴 흐름 조율 패턴을 더 세밀하게 구분하는지 본다.
> 핵심: 겹치는 부분은 있지만 초점이 다르다. saga는 보상 중심, process manager는 장기 상태와 의사결정 중심이다.

> Q: Coordinator에 타이머만 추가하면 Process Manager가 되나요?
> 의도: 용어 바꾸기로 설계 문제를 덮지 않는지 본다.
> 핵심: 아니다. 핵심은 장기 상태 모델과 이벤트 기반 의사결정 구조다.

> Q: 둘을 같이 써도 괜찮나요?
> 의도: 패턴 조합을 자연스럽게 보는지 확인한다.
> 핵심: 괜찮다. 짧은 즉시 보상 흐름과 긴 후속 관리 흐름을 나누면 오히려 더 선명해진다.

## 한 줄 정리

Saga Coordinator는 단계 실행과 보상을 지휘하고, Process Manager는 이벤트를 따라 장기 상태를 유지하며 다음 명령을 결정한다.
