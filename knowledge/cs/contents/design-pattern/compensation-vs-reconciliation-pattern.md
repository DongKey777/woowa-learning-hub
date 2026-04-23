# Compensation vs Reconciliation Pattern

> 한 줄 요약: 분산 실패를 모두 즉시 보상으로 덮으려 하지 말고, 되돌릴 수 있는 건 compensation으로, 이미 세계가 갈라진 건 reconciliation으로 다루는 것이 운영적으로 더 안전하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Reservation, Hold, and Expiry as a Consistency Seam](./reservation-hold-expiry-consistency-seam.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Process Manager State Store and Recovery Pattern](./process-manager-state-store-recovery.md)

---

## 핵심 개념

분산 흐름이 실패하면 많은 팀이 reflex처럼 "보상하면 되지"를 떠올린다.  
하지만 실제 운영에서는 모든 실패가 보상만으로 닫히지 않는다.

- 취소 가능한 작업
- 이미 외부에 노출된 작업
- 성공 여부가 불명확한 작업
- 사람 확인이 필요한 작업

이때 중요한 구분이 있다.

- compensation: 이미 일어난 일을 상쇄하는 도메인 액션
- reconciliation: 현재 세계의 불일치를 검사하고 설명 가능한 방식으로 다시 맞춤

보상은 흐름 설계의 일부이고, reconciliation은 운영 루프의 일부에 더 가깝다.

### Retrieval Anchors

- `compensation vs reconciliation`
- `corrective workflow`
- `unknown external state`
- `operational repair loop`
- `business rollback limit`
- `manual repair path`
- `compensating action`
- `reconciliation`

---

## 깊이 들어가기

### 1. compensation은 rollback이 아니다

보상은 단순 undo가 아니다.

- 재고 예약 해제
- 주문 취소
- 포인트 회수
- 환불 요청

즉 이미 커밋된 현실을 도메인적으로 상쇄하는 행위다.

### 2. reconciliation은 "무슨 일이 일어났는지 다시 확인"하는 단계다

어떤 실패는 보상 전에 사실 확인이 필요하다.

- 외부 PG 승인 성공 여부 불명확
- webhook 유실 여부 불명확
- participant 응답이 없지만 실제 작업은 됐을 수도 있음

이 경우 섣부른 보상은 이중 취소, 이중 환불, 잘못된 release를 만들 수 있다.  
먼저 truth를 다시 맞추는 reconciliation 단계가 더 안전하다.

### 3. unknown state는 compensation보다 reconciliation에 가깝다

다음 같은 상태는 흔하다.

- timeout
- broker ack 불명확
- 외부 시스템 500 응답
- callback 미도착

이걸 곧바로 "실패"로 단정하면 오히려 오류를 키울 수 있다.  
unknown state를 명시적으로 두고 조회, 재확인, manual review로 넘기는 편이 낫다.

### 4. owner context는 어떤 실패를 compensation으로, 어떤 실패를 reconciliation으로 보낼지 결정해야 한다

workflow owner는 실패 분류 정책을 가져야 한다.

- 즉시 보상 가능한가
- 외부 상태 재조회가 필요한가
- 사람 개입이 필요한가
- 보상보다 correction entry가 필요한가

이 구분이 없으면 모든 실패가 retry 또는 cancel로만 흘러간다.

### 5. reconciliation은 배치가 아니라 설계된 corrective path여야 한다

reconciliation을 "나중에 배치 한 번" 정도로 생각하면 안 된다.

- 누가 실행하는가
- 어떤 truth source와 비교하는가
- 차이를 어떻게 설명하는가
- correction을 어떻게 기록하는가

즉 reconciliation도 workflow의 연장선에 있는 운영 패턴이다.

---

## 실전 시나리오

### 시나리오 1: 결제 승인 timeout

PG 응답이 timeout 났다고 바로 주문 취소/재고 release를 하면, 실제로는 승인된 결제를 놓칠 수 있다.  
이 경우 먼저 reconciliation query로 PG 상태를 재확인하는 편이 더 안전하다.

### 시나리오 2: 배송 생성 실패

배송 API가 명확히 실패했고 side effect도 없었다면 compensation이 자연스럽다.  
주문을 실패 상태로 돌리고 hold를 release하면 된다.

### 시나리오 3: webhook 누락

외부 상태는 진행됐는데 callback만 누락되었다면, compensation보다 periodic reconciliation이 더 맞다.

---

## 코드로 보기

### failure classification 감각

```java
public enum FailureHandlingMode {
    COMPENSATE,
    RECONCILE,
    MANUAL_REVIEW
}
```

### owner decision

```java
public FailureHandlingMode classify(PaymentAttemptResult result) {
    if (result.isExplicitFailure()) {
        return FailureHandlingMode.COMPENSATE;
    }
    if (result.isUnknownState()) {
        return FailureHandlingMode.RECONCILE;
    }
    return FailureHandlingMode.MANUAL_REVIEW;
}
```

### reconciliation path

```java
public void on(PaymentStatusUnknown event) {
    commandBus.dispatch(new ReconcilePaymentStateCommand(event.orderId(), event.paymentId()));
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 compensation | 흐름이 단순하다 | unknown state에서 오히려 잘못된 상쇄를 만들 수 있다 | 실패가 명확하고 reversible할 때 |
| reconciliation 우선 | 잘못된 보상을 줄인다 | 지연과 운영 루프가 필요하다 | 외부 상태가 불명확할 때 |
| manual review 포함 | 안전성이 높다 | 처리 비용과 운영 부담이 크다 | 금액이 크거나 규제/고객 영향이 큰 경우 |

판단 기준은 다음과 같다.

- 실패가 명확하면 compensation
- 세계 상태가 불명확하면 reconciliation
- 자동 결정이 위험하면 manual review

---

## 꼬리질문

> Q: saga가 있으면 reconciliation은 필요 없나요?
> 의도: workflow 패턴과 운영 repair 루프를 구분하는지 본다.
> 핵심: 아니다. saga는 보상 구조를 주지만, unknown external state는 reconciliation이 더 적절할 수 있다.

> Q: timeout이 나면 왜 바로 보상하면 안 되나요?
> 의도: unknown state의 위험을 보는 질문이다.
> 핵심: timeout은 실패가 아니라 상태 불명확일 수 있기 때문이다.

> Q: reconciliation은 실패 설계를 미룬 것 아닌가요?
> 의도: corrective path도 설계의 일부라는 점을 이해하는지 본다.
> 핵심: 아니다. 오히려 분산 현실을 인정한 명시적 운영 패턴이다.

## 한 줄 정리

Compensation은 되돌릴 수 있는 일을 상쇄하는 패턴이고, reconciliation은 이미 갈라졌거나 불명확해진 세계 상태를 다시 맞추는 운영 패턴이다.
