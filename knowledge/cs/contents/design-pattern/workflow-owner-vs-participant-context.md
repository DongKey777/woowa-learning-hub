# Workflow Owner vs Participant Context

> 한 줄 요약: long-running workflow에서는 모든 서비스가 흐름을 함께 소유하는 게 아니라, owner context가 상태와 시간 정책을 가지고 participant context는 자기 로컬 규칙과 응답만 책임지는 편이 안전하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Human Approval and Manual Review Workflow Pattern](./human-approval-manual-review-workflow-pattern.md)
> - [Escalation, Reassignment, and Queue Ownership Pattern](./escalation-reassignment-queue-ownership-pattern.md)
> - [Reservation, Hold, and Expiry as a Consistency Seam](./reservation-hold-expiry-consistency-seam.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Bounded Context Relationship Patterns](./bounded-context-relationship-patterns.md)

---

## 핵심 개념

여러 bounded context가 하나의 비즈니스 흐름에 참여하면 자주 이런 혼란이 생긴다.

- 누가 전체 상태를 들고 있지
- timeout 정책은 어느 서비스가 아나
- 실패 후 다음 단계를 누가 결정하지
- participant가 다음 participant를 직접 호출해도 되나

이때 중요한 구분이 `workflow owner`와 `participant context`다.

- workflow owner: 전체 흐름 상태, deadline, handoff 정책을 소유
- participant context: 자기 로컬 규칙을 수행하고 결과를 응답

이 구분이 없으면 "다 같이 흐름을 조금씩 안다"는 상태가 되고, 결국 어느 누구도 전체를 책임지지 않게 된다.

### Retrieval Anchors

- `workflow owner`
- `participant context`
- `long running workflow ownership`
- `handoff policy`
- `time boundary ownership`
- `orchestration owner`
- `review queue ownership`

---

## 깊이 들어가기

### 1. owner는 전체 상태를, participant는 로컬 사실을 소유한다

예를 들어 주문-결제-배송 흐름에서:

- owner는 `CHECKOUT_PENDING`, `PAYMENT_WAITING`, `FAILED`, `COMPLETED` 같은 전체 진행 상태를 안다
- participant는 `PaymentAuthorized`, `ShipmentCreated` 같은 자기 사실만 안다

participant가 전체 워크플로 의미까지 품기 시작하면 경계가 흐려진다.

### 2. 시간 정책은 owner가 갖는 편이 안전하다

특히 deadline/reminder/expiry는 participant에 흩어지면 위험하다.

- 결제 서비스가 주문 만료 정책까지 앎
- 알림 서비스가 리마인드 cadence를 최종 결정
- 재고 서비스가 checkout 전체 timeout을 판단

이렇게 되면 시간 정책이 여러 서비스에 복제되고 drift가 생긴다.  
보통은 owner context가 기다림의 정책을 가지고, participant는 응답만 반환하는 편이 낫다.

### 3. participant는 다음 participant를 직접 오케스트레이션하지 않는 편이 좋다

참여 서비스가 자기 일을 마친 뒤 또 다른 서비스를 직접 호출하기 시작하면, 숨은 owner가 늘어난다.

- Payment가 성공 후 Shipment를 직접 생성
- Inventory가 실패 후 Order 취소를 직접 호출
- Notification이 재시도 정책까지 결정

이 패턴은 빠르게 흐름을 만들 수는 있지만, 시간이 지나면 handoff 경로가 분산된다.

### 4. owner가 모든 로컬 규칙까지 가져가면 또 다른 God Coordinator가 된다

반대로 owner가 각 participant의 상세 규칙까지 가져오면 이것도 문제다.

- 결제 한도 규칙
- 재고 할당 알고리즘
- 배송사 라우팅 규칙

owner는 전체 흐름을 책임지되, participant 내부 규칙은 participant가 가져야 한다.

### 5. handoff는 명령과 응답의 의미를 명시해야 한다

owner와 participant 사이에서는 보통 다음이 선명해야 한다.

- owner가 어떤 명령/요청을 보냈는가
- participant가 어떤 사실/결과를 응답하는가
- 실패/재시도/timeout을 owner가 어떻게 해석하는가

즉 owner-participant 관계는 단순 RPC 호출보다 **경계 있는 상태 전환 계약**에 가깝다.

---

## 실전 시나리오

### 시나리오 1: checkout owner와 payment participant

checkout context가 전체 주문 마감과 timeout 정책을 소유하고, payment context는 승인/실패 사실만 제공한다.  
결제 서비스가 주문 만료 시점을 직접 판단하지 않는 편이 더 안전하다.

### 시나리오 2: 대출 심사 owner와 외부 심사 participant

대출 심사 프로세스는 owner가 서류 수집, SLA, 수동 승인 경로를 가진다.  
신용 조회 시스템은 결과 응답만 책임지고, 다음 단계 개시는 owner가 판단한다.

### 시나리오 3: 좌석 예약 owner와 inventory participant

예약 hold의 만료와 confirm/release는 owner가 해석하고, inventory는 홀드 생성/확정/해제 요청을 수행하는 participant로 두는 편이 명확하다.

---

## 코드로 보기

### owner context 감각

```java
public class CheckoutWorkflowManager {
    private CheckoutWorkflowStatus status;

    public void start(CheckoutRequested event) {
        status = CheckoutWorkflowStatus.PAYMENT_WAITING;
        commandBus.dispatch(new RequestPaymentAuthorization(event.orderId(), event.amount()));
    }

    public void on(PaymentAuthorized event) {
        status = CheckoutWorkflowStatus.FULFILLMENT_WAITING;
        commandBus.dispatch(new RequestShipment(event.orderId()));
    }
}
```

### participant context 감각

```java
public class PaymentApplicationService {
    public void authorize(RequestPaymentAuthorization command) {
        // 결제 승인 로컬 규칙 수행
        eventBus.publish(new PaymentAuthorized(command.orderId(), paymentId));
    }
}
```

### ownership 원칙

```java
// owner는 전체 흐름과 시간 정책을 소유하고,
// participant는 자기 도메인 사실과 로컬 규칙을 소유한다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| owner context 명확화 | 상태와 timeout 정책이 선명하다 | owner 설계가 필요하다 | 장기 워크플로, 사람 개입, SLA가 있는 흐름 |
| participant가 서로 직접 호출 | 처음엔 빠르다 | 숨은 오케스트레이션이 늘어난다 | 짧고 단순한 내부 플로우 정도 |
| 중앙 owner가 모든 세부 규칙 소유 | 흐름이 한곳에 모인다 | God Coordinator가 된다 | 보통 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- 전체 상태와 시간 정책은 owner가 가진다
- 로컬 규칙은 participant가 가진다
- participant 간 숨은 handoff가 늘어나면 owner 경계를 다시 본다

---

## 꼬리질문

> Q: participant가 다음 participant를 직접 호출하면 왜 안 좋나요?
> 의도: 숨은 오케스트레이션의 확산을 보는 질문이다.
> 핵심: handoff 경로가 분산되고 전체 상태 책임이 흐려진다.

> Q: owner가 있으면 participant는 단순 adapter인가요?
> 의도: 로컬 규칙 소유권을 놓치지 않는지 본다.
> 핵심: 아니다. participant는 자기 도메인 규칙과 상태를 여전히 강하게 가진다.

> Q: timeout 정책은 누가 가져야 하나요?
> 의도: long-running workflow ownership을 생각하는지 본다.
> 핵심: 보통 전체 프로세스와 SLA를 소유한 owner context가 가져가는 편이 안전하다.

## 한 줄 정리

Workflow owner와 participant context를 구분하면, long-running workflow에서 전체 상태/시간 정책과 로컬 도메인 규칙의 소유권을 더 건강하게 나눌 수 있다.
