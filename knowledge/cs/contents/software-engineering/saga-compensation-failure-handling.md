# Saga Compensation Failure Handling

> 한 줄 요약: Saga의 진짜 난점은 실패를 되돌리는 것이 아니라, compensation 자체가 또 실패할 때 시스템을 어떻게 안전하게 멈추고 복구할지 정하는 데 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Workflow Orchestration + Saga 설계](../system-design/workflow-orchestration-saga-design.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [API Design, Error Handling](./api-design-error-handling.md)

> retrieval-anchor-keywords:
> - saga compensation
> - compensation failure
> - idempotent rollback
> - manual recovery
> - reconciliation job
> - dead letter queue
> - partial failure
> - orchestration state machine

## 핵심 개념

Saga는 여러 로컬 트랜잭션을 묶는 분산 업무 흐름이다.
여기서 compensation은 일반적인 rollback이 아니라, 이미 진행된 작업을 **업무적으로 되돌리는 별도 작업**이다.

그런데 compensation도 실패할 수 있다.

- 취소 API가 timeout 난다
- 반대 방향 상태가 이미 바뀌었다
- 외부 시스템이 부분적으로만 취소된다
- 재시도는 되지만 같은 요청이 또 꼬인다

따라서 핵심 질문은 "되돌릴 수 있는가"가 아니라 **되돌리는 과정이 실패했을 때 어떻게 수습할 것인가**다.

---

## 깊이 들어가기

### 1. compensation은 rollback이 아니다

트랜잭션 rollback은 데이터베이스가 상태를 되감는다.
Saga compensation은 업무 규칙에 따라 상쇄 작업을 수행한다.

예:

- 결제 승인 후 -> 결제 취소
- 재고 예약 후 -> 재고 해제
- 배송 요청 후 -> 배송 취소 요청

이 순서가 같아 보여도, 각 시스템의 취소 의미는 다를 수 있다.

### 2. compensation failure는 별도 상태로 모델링해야 한다

보통 saga 상태는 이런 식이다.

- `PENDING`
- `STEP_1_DONE`
- `STEP_2_DONE`
- `COMPENSATING`
- `COMPENSATED`
- `COMPENSATION_FAILED`

`FAILED` 하나로 뭉개면 운영자가 무엇을 해야 하는지 알 수 없다.

### 3. 실패 유형을 나눠야 한다

compensation failure는 원인이 다르다.

| 유형 | 특징 | 대응 |
|---|---|---|
| transient | timeout, 5xx | retry |
| semantic | 이미 취소됨, 상태 불일치 | 재조회 후 판정 |
| destructive | 외부 시스템 일부만 반영됨 | 수동 보정 |
| unknown | 원인 추적 불가 | 격리 후 조사 |

같은 retry로 다 해결하려고 하면 오히려 중복 취소나 상태 충돌이 커진다.

### 4. idempotent compensation이 핵심이다

보상 작업은 한 번만 실행된다는 보장이 없다.

그래서 아래가 필요하다.

- idempotency key
- 중복 실행 감지
- 이미 상쇄된 상태 확인
- 순서 역전에도 안전한 처리

보상 API는 "실행되면 취소"가 아니라 **몇 번 호출돼도 같은 결과를 향해 수렴**해야 한다.

### 5. compensation이 막히면 운영 경로가 필요하다

모든 compensation을 자동으로 끝낼 수는 없다.

그때 필요한 운영 장치:

- dead letter queue
- manual recovery queue
- reconciliation job
- 운영자 대시보드
- 재처리 버튼/명령

즉 saga는 코드만이 아니라 **운영 절차까지 포함한 시스템**이다.

---

## 실전 시나리오

### 시나리오 1: 결제는 성공했는데 재고 예약이 실패한다

흐름:

1. 결제 승인 성공
2. 재고 예약 실패
3. 결제 취소 compensation 시도
4. 결제 취소도 timeout

이때 운영자는:

- 재시도 가능한지 본다
- 결제사 상태를 재조회한다
- 이미 취소된 상태면 종료한다
- 아니면 수동 처리 큐로 보낸다

### 시나리오 2: 배송 취소가 부분적으로만 반영된다

배송사 시스템은 이미 출고된 건 취소를 못 한다.
이 경우 compensation은 기술적 rollback이 아니라 **대체 업무 흐름**이 된다.

- 회수 요청
- 고객 안내
- 환불 승인
- 운영자 승인 대기

### 시나리오 3: 중복 메시지 때문에 compensation이 두 번 돈다

Inbox 없이 보상 이벤트를 처리하면 같은 취소 명령이 두 번 도착할 수 있다.

그래서 compensation endpoint도 본 경로와 마찬가지로 idempotent해야 한다.

---

## 코드로 보기

```java
public class SagaRecoveryService {
    public void compensate(OrderSaga saga) {
        if (saga.isCompensated()) {
            return;
        }

        try {
            paymentClient.cancel(saga.paymentId());
            inventoryClient.release(saga.inventoryReservationId());
            saga.markCompensated();
        } catch (TransientException e) {
            saga.markCompensationRetryable(e.getMessage());
            retryQueue.enqueue(saga.id());
        } catch (Exception e) {
            saga.markCompensationFailed(e.getMessage());
            manualRecoveryQueue.enqueue(saga.id());
        }
    }
}
```

이 코드는 단순해 보이지만 핵심은 예외 처리 자체보다 **상태 전이의 분기**다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자동 재시도 중심 | 구현이 쉽다 | 잘못된 상태를 반복할 수 있다 | transient failure 위주일 때 |
| 상태 분리 + 수동 복구 | 복잡한 실패에 강하다 | 운영 부담이 늘어난다 | 재정/물류처럼 실패 비용이 큰 경우 |
| 재조정(reconciliation) 중심 | 장기적으로 안정적이다 | 즉시 복구는 어렵다 | 외부 시스템과 상태가 자주 어긋날 때 |

Saga의 품질은 "실패 없음"이 아니라 **실패 후에도 수습 가능한가**로 판단해야 한다.

---

## 꼬리질문

- compensation이 실패하면 언제 자동 재시도하고 언제 멈출 것인가?
- 어떤 실패는 보상 대신 reconciliation이 더 적절한가?
- 보상 API도 idempotent하다는 보장이 있는가?
- 수동 복구가 필요한 상태를 어떻게 운영자가 보기 쉽게 만들 것인가?

## 한 줄 정리

Saga compensation의 핵심은 되돌림 자체가 아니라, 되돌림이 실패했을 때도 상태를 잃지 않고 재시도·수동 복구·재조정으로 수렴하게 만드는 것이다.
