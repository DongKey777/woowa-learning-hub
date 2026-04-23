# Process Manager State Store and Recovery Pattern

> 한 줄 요약: long-running workflow를 조율하는 process manager는 메모리 객체가 아니라 durable state store와 recovery 전략을 함께 가져야 하며, 그렇지 않으면 재시작 순간 흐름 소유권이 사라진다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Compensation vs Reconciliation Pattern](./compensation-vs-reconciliation-pattern.md)
> - [Checkpoint / Snapshot Pattern](./checkpoint-snapshot-pattern.md)
> - [Command Bus Pattern](./command-bus-pattern.md)

---

## 핵심 개념

long-running workflow를 process manager로 모델링했다면 다음 질문이 남는다.

- 이 상태를 어디에 저장할까
- 프로세스가 죽었다 살아나면 어디서 이어갈까
- 중복 이벤트가 오면 어떻게 복원할까
- 스케줄된 deadline과 현재 상태를 어떻게 다시 연결할까

이 문제를 덮고 "클래스 하나로 흐름을 표현했다"에서 멈추면, 재시작 순간 설계가 무너진다.

Process Manager State Store and Recovery 패턴은 다음을 함께 본다.

- durable workflow state store
- correlation key로 인스턴스 복원
- recovery 시 stale timer/event 무시
- resume 가능한 command emission

### Retrieval Anchors

- `process manager state store`
- `workflow recovery`
- `durable workflow state`
- `correlation key restore`
- `resume after restart`
- `workflow instance rehydration`
- `stale timer recovery`

---

## 깊이 들어가기

### 1. process manager는 객체보다 workflow instance에 가깝다

코드에서는 클래스 하나처럼 보여도 운영에서는 보통 많은 인스턴스가 동시에 돈다.

- 주문마다 하나
- 대출 심사 케이스마다 하나
- 구독 청구 흐름마다 하나

그래서 중요한 건 클래스 구조보다 **instance identity와 상태 저장 방식**이다.

### 2. correlation key가 없으면 recovery가 안 된다

이벤트를 받았을 때 어떤 workflow instance를 찾아야 하는지 명확해야 한다.

- orderId
- caseId
- subscriptionId
- reservationId

이 correlation key가 durable state store lookup의 핵심이 된다.

### 3. recovery는 단순 재기동이 아니라 현재 세계와 state를 다시 맞추는 과정이다

restart 후 process manager는 보통 이런 문제를 만난다.

- 타이머는 이미 갔는데 state는 옛날 상태
- 이벤트가 중복 재전달됨
- command는 이미 보냈는데 ack 기록이 안 남음
- participant 응답이 먼저 왔는데 state store flush가 늦었음

따라서 recovery는 "메모리 복원"보다 **state, timers, sent commands의 재동기화**에 가깝다.

### 4. state store는 현재 상태만이 아니라 최소한의 해석 맥락을 가져야 한다

보통 다음 정보가 같이 필요하다.

- current workflow status
- last processed event id/version
- outstanding deadlines
- last emitted command ids
- retry / attempt metadata

그래야 재시작 후 중복 이벤트/명령을 다시 해석할 수 있다.

### 5. process manager recovery는 saga log와 비슷한 감각을 가진다

꼭 full event sourcing이 아니더라도, 최소한 "어디까지 처리했는가"를 남겨야 한다.

- last seen event sequence
- deadline token
- command dispatch record

이 기록이 없으면 recovery 시 중복 실행과 누락 실행을 구분하기 어렵다.

---

## 실전 시나리오

### 시나리오 1: 주문 결제 대기 프로세스 재시작

서버 재기동 후 `PENDING_PAYMENT` 주문들의 deadline을 다시 로드하고, 이미 만료된 것과 아직 남은 것을 구분해 재스케줄링해야 한다.

### 시나리오 2: 대출 심사 워크플로

며칠짜리 심사 흐름은 프로세스 재시작이 여러 번 있을 수 있다.  
인메모리 상태만 믿으면 수동 승인 대기나 reminder cadence가 유실된다.

### 시나리오 3: 구독 청구 재시도

재시작 후 이전에 보낸 `RetryPaymentCommand`가 성공했는지 모르면 동일 청구를 중복 발행할 위험이 있다.

---

## 코드로 보기

### state store 감각

```java
public record WorkflowInstanceState(
    String workflowId,
    String status,
    String correlationKey,
    long lastProcessedSequence,
    Instant nextDeadlineAt,
    String lastCommandId
) {}
```

### recovery load

```java
public class BillingRetryWorkflowRecovery {
    public void resume(String subscriptionId) {
        WorkflowInstanceState state = store.findByCorrelationKey(subscriptionId).orElseThrow();
        if (state.nextDeadlineAt() != null && state.nextDeadlineAt().isBefore(Instant.now())) {
            commandBus.dispatch(new ResumeExpiredBillingWorkflow(subscriptionId));
        }
    }
}
```

### duplicate event guard

```java
public void on(BillingEvent event) {
    WorkflowInstanceState state = store.findByCorrelationKey(event.subscriptionId()).orElseThrow();
    if (event.sequence() <= state.lastProcessedSequence()) {
        return;
    }
    // handle and persist new state
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 인메모리 manager | 구현이 빠르다 | 재시작과 scale-out에 약하다 | 아주 짧고 휘발성 플로우 |
| durable state store | recovery와 scale-out이 가능하다 | 상태 모델링과 저장 비용이 든다 | long-running workflow 대부분 |
| full event-sourced workflow | audit와 replay가 강하다 | 복잡도가 높다 | 규제/감사/재현 요구가 매우 큰 경우 |

판단 기준은 다음과 같다.

- 흐름이 프로세스 수명을 넘으면 durable state store가 필요하다
- correlation key와 last processed cursor를 함께 둔다
- recovery는 timer와 command 재동기화까지 포함해 설계한다

---

## 꼬리질문

> Q: process manager 상태를 DB에 저장하기만 하면 recovery가 끝인가요?
> 의도: 저장과 재동기화를 구분하는지 본다.
> 핵심: 아니다. deadline, last processed event, emitted command도 함께 해석할 수 있어야 한다.

> Q: 왜 correlation key가 중요한가요?
> 의도: workflow instance identity를 이해하는지 본다.
> 핵심: 어떤 이벤트가 어떤 workflow instance에 속하는지 찾아야 recovery가 가능하다.

> Q: event sourcing을 안 쓰면 process manager recovery가 약한가요?
> 의도: full event sourcing만 정답으로 보지 않는지 확인한다.
> 핵심: 아니다. durable state + cursor + command log만 잘 둬도 충분히 강해질 수 있다.

## 한 줄 정리

Process manager는 클래스가 아니라 durable workflow instance로 다뤄야 하며, state store와 recovery 전략이 있어야 long-running ownership이 재시작 이후에도 유지된다.
