---
schema_version: 3
title: Semantic Lock and Pending State Pattern
concept_id: design-pattern/semantic-lock-pending-state-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- semantic-lock
- pending-state-guard
- workflow-state-gate
aliases:
- semantic lock
- pending state pattern
- business lock
- in progress state guard
- pending approval state
- long running state gate
- manual review lock
- pending payment state
- workflow state guard
- business pending state
symptoms:
- 외부 응답이나 사람 검토를 기다리는 동안 주문 수정, 취소, 재시도가 동시에 열려 중복 전이가 생긴다
- PENDING_PAYMENT 같은 상태를 추가했지만 그 상태에서 금지되는 행동, timeout, stale response 처리 규칙이 없다
- optimistic locking으로 stale write만 막으면 장기 workflow의 행동 제한까지 해결된다고 오해한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/state-pattern-workflow-payment
- design-pattern/aggregate-version-optimistic-concurrency-pattern
- design-pattern/process-manager-deadlines-timeouts
next_docs:
- design-pattern/human-approval-manual-review-workflow-pattern
- design-pattern/reservation-hold-expiry-consistency-seam
- design-pattern/process-manager-state-store-recovery
linked_paths:
- contents/design-pattern/state-pattern-workflow-payment.md
- contents/design-pattern/reservation-hold-expiry-consistency-seam.md
- contents/design-pattern/aggregate-version-optimistic-concurrency-pattern.md
- contents/design-pattern/human-approval-manual-review-workflow-pattern.md
- contents/design-pattern/saga-coordinator-pattern-language.md
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/workflow-owner-vs-participant-context.md
confusable_with:
- design-pattern/aggregate-version-optimistic-concurrency-pattern
- design-pattern/state-pattern-workflow-payment
- design-pattern/reservation-hold-expiry-consistency-seam
- design-pattern/human-approval-manual-review-workflow-pattern
forbidden_neighbors: []
expected_queries:
- semantic lock은 DB lock이 아니라 PENDING 상태로 어떤 행동을 막는 패턴이야?
- PENDING_PAYMENT 상태에서 주소 변경이나 중복 결제 시도를 막아야 하는 이유가 뭐야?
- optimistic concurrency가 있어도 long-running workflow에서 semantic lock이 필요한 이유가 뭐야?
- pending state에는 guard, timeout, release, stale response 처리 규칙이 함께 있어야 하는 이유가 뭐야?
- manual review 중 자동 취소나 자동 환불을 막으려면 UNDER_REVIEW 상태를 어떻게 semantic lock으로 써야 해?
contextual_chunk_prefix: |
  이 문서는 Semantic Lock and Pending State Pattern playbook으로, DB lock을 오래 잡을 수 없는
  long-running workflow에서 PENDING_PAYMENT, UNDER_REVIEW 같은 도메인 상태를 semantic lock으로
  사용해 특정 행동을 제한하고 timeout, release, stale response guard, optimistic concurrency를
  함께 설계하는 방법을 설명한다.
---
# Semantic Lock and Pending State Pattern

> 한 줄 요약: distributed workflow에서 DB lock을 오래 잡을 수 없다면, `PENDING_*` 같은 의미 있는 중간 상태를 두어 후속 행동을 제한하는 semantic lock 패턴이 충돌과 중복 진행을 줄여 준다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [State Pattern: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [Reservation, Hold, and Expiry as a Consistency Seam](./reservation-hold-expiry-consistency-seam.md)
> - [Aggregate Version and Optimistic Concurrency Pattern](./aggregate-version-optimistic-concurrency-pattern.md)
> - [Human Approval and Manual Review Workflow Pattern](./human-approval-manual-review-workflow-pattern.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)

---

## 핵심 개념

긴 워크플로에서 실제 DB lock을 잡은 채 외부 응답을 기다릴 수는 없다.  
그렇다고 아무 표식 없이 상태를 열어 두면 다음 문제가 생긴다.

- 중복 승인 요청
- 취소와 승인 동시 진행
- 사람 승인 대기 중 다른 전이 허용
- 외부 처리 중인데 사용자 편집 계속 허용

이때 자주 쓰는 패턴이 semantic lock이다.

- `PENDING_PAYMENT`
- `CANCELLATION_REQUESTED`
- `UNDER_REVIEW`
- `FULFILLMENT_LOCKED`

이런 상태는 기술적 lock이 아니라 **도메인 의미를 가진 임시 잠금 상태**다.

따라서 semantic lock을 설계할 때는 상태 이름보다 먼저 "이 상태에서 어떤 command를 거부하고, 어떤 signal이 오면 풀리며, 늦게 온 signal은 어떤 기준으로 무시하는가"를 정해야 한다.

### Retrieval Anchors

- `semantic lock`
- `pending state pattern`
- `business lock`
- `in progress state guard`
- `pending approval state`
- `long running state gate`
- `manual review lock`

---

## 깊이 들어가기

### 1. semantic lock은 동시성 제어를 도메인 언어로 드러낸다

기술적 lock은 DB나 분산 락 시스템 안에 숨는다.  
semantic lock은 사용자와 서비스가 이해할 수 있는 상태로 드러난다.

- 지금 결제 처리 중이다
- 지금 취소 검토 중이다
- 지금 외부 승인 대기 중이다

즉 "왜 다른 행동이 막히는가"가 설명 가능해진다.

### 2. pending state는 행동 제한 규칙과 함께 와야 한다

상태만 하나 추가한다고 끝나지 않는다.

- 이 상태에서 금지되는 행동은 무엇인가
- timeout 시 어디로 전이하는가
- 성공/실패 응답이 오면 어디로 가는가
- stale 응답은 어떻게 무시하는가

pending state가 진짜 semantic lock이 되려면 **guard + timeout + release 규칙**이 함께 있어야 한다.

### 3. semantic lock은 optimistic concurrency를 대체하지 않는다

둘은 다르다.

- semantic lock: 장기 흐름 중 특정 행동을 논리적으로 막음
- optimistic concurrency: stale write를 version으로 감지

실무에서는 둘을 함께 쓰는 경우가 많다.

- `PENDING_PAYMENT` 상태로 후속 행동 제한
- 저장 시 version check로 stale update 감지

### 4. 지나치게 많은 pending state는 또 다른 state explosion이 된다

모든 중간 상황을 새 상태로 만들면 모델이 무거워진다.

- `PAYMENT_PENDING_SENT`
- `PAYMENT_PENDING_RETRYING`
- `PAYMENT_PENDING_CALLBACK_WAITING`

핵심은 "행동 제한 의미가 있는가"다.  
운영 디테일만 표현하려는 상태는 process metadata로 분리하는 편이 낫다.

### 5. semantic lock은 manual review와도 잘 맞는다

사람 승인/검토가 들어가는 순간, pending state는 더욱 중요해진다.

- 검토 중에는 자동 취소 금지
- 검토 중에는 금액 수정 금지
- 승인 결론이 날 때까지 다음 participant 호출 금지

즉 human-in-the-loop도 결국 semantic lock의 특수한 형태로 볼 수 있다.

---

## 실전 시나리오

### 시나리오 1: 결제 승인 대기

주문이 `PENDING_PAYMENT` 상태일 때 주소 변경이나 중복 결제 시도를 막을 수 있다.  
결제 결과가 오면 `PAID` 또는 `FAILED`로 전이한다.

### 시나리오 2: 환불 검토 중

고액 환불이 수동 검토 중이라면, 중복 환불 요청이나 자동 재시도를 막아야 한다.  
`UNDER_REFUND_REVIEW` 상태가 semantic lock 역할을 한다.

### 시나리오 3: 출고 확정 직전

외부 물류 할당 요청 중에는 주문 수정/취소를 제한할 필요가 있다.  
기술적 lock 대신 `FULFILLMENT_LOCKED` 같은 상태가 의미를 드러낼 수 있다.

---

## 코드로 보기

### pending state guard

```java
public class Order {
    private OrderStatus status;

    public void requestPayment() {
        if (status != OrderStatus.CREATED) {
            throw new IllegalStateException("payment already started");
        }
        status = OrderStatus.PENDING_PAYMENT;
    }

    public void changeAddress(Address address) {
        if (status == OrderStatus.PENDING_PAYMENT || status == OrderStatus.FULFILLMENT_LOCKED) {
            throw new IllegalStateException("order temporarily locked");
        }
        // change address
    }
}
```

### timeout release

```java
public void on(PaymentTimeout event) {
    if (order.status() == OrderStatus.PENDING_PAYMENT) {
        order.markPaymentFailed();
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 기술적 lock만 사용 | 구현이 단순해 보인다 | 긴 외부 대기에는 부적합하다 | 짧은 로컬 트랜잭션 |
| semantic lock / pending state | 행동 제한 의미가 선명하다 | 상태 수와 timeout 규칙이 늘어난다 | 장기 외부 대기, 수동 승인, 중복 진행 방지 |
| 아무 잠금 상태 없이 진행 | 모델은 단순하다 | 중복 전이와 경합에 취약하다 | 충돌 비용이 매우 낮은 흐름 |

판단 기준은 다음과 같다.

- 외부 응답이나 사람 개입 동안 행동 제한이 필요하면 semantic lock
- pending state는 guard와 release 규칙을 함께 둔다
- 운영 메타만 표현하는 상태는 남용하지 않는다

---

## 꼬리질문

> Q: semantic lock은 그냥 status enum 하나 더 늘린 건가요?
> 의도: 상태 추가와 의미 있는 행동 제한의 차이를 보는 질문이다.
> 핵심: 아니다. 핵심은 그 상태가 다른 행동을 막는 도메인 규칙을 가진다는 점이다.

> Q: optimistic concurrency가 있으면 semantic lock이 필요 없나요?
> 의도: stale write 감지와 장기 상태 게이트를 구분하는지 본다.
> 핵심: 아니다. 둘은 다른 문제를 해결한다.

> Q: pending state가 너무 많아지면 어떻게 하나요?
> 의도: state explosion을 경계하는지 본다.
> 핵심: 행동 제한 의미가 없는 상태는 메타데이터나 로그로 내리고, 진짜 게이트만 상태로 남긴다.

## 한 줄 정리

Semantic lock은 장기 워크플로에서 기술적 lock 대신 의미 있는 pending state로 행동을 제한해, 중복 진행과 경합을 도메인 언어로 통제하게 해주는 패턴이다.
