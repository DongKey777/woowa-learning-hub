---
schema_version: 3
title: Spring Payment Approval DB Failure Compensation Idempotency Primer
concept_id: spring/payment-approval-db-failure-compensation-idempotency-primer
canonical: true
category: spring
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 78
review_feedback_tags:
- payment-approval-db
- failure-compensation-idempotency
- failure
- external-approval-compensation
aliases:
- payment approval DB failure
- external approval compensation
- payment idempotency key
- rollback cannot cancel external payment
- after commit outbox payment
- 결제 승인 DB 실패 보상 멱등성
intents:
- mission_bridge
- design
- troubleshooting
linked_paths:
- contents/spring/spring-service-layer-external-io-after-commit-outbox-primer.md
- contents/spring/spring-transaction-propagation-required-requires-new-rollbackonly-primer.md
- contents/spring/spring-persistence-context-flush-clear-detach-boundaries.md
- contents/database/idempotency-key-status-contract-examples.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/outbox-saga-eventual-consistency.md
- contents/database/transaction-boundary-external-io-checklist-card.md
mission_ids:
- missions/shopping-cart
- missions/payment
confusable_with:
- spring/service-layer-external-io-after-commit-outbox-primer
- database/idempotency-key-status-contract-examples
- database/idempotency-key-and-deduplication
- database/outbox-saga-eventual-consistency
expected_queries:
- 외부 결제 승인 성공 후 DB 저장이 실패하면 rollback으로 해결돼?
- 결제 승인과 주문 저장을 같은 트랜잭션처럼 보면 왜 위험해?
- paymentAttemptKey와 idempotency key는 어디에 저장해야 해?
- 승인 성공 뒤 DB 실패 보상 취소 경로를 초급자에게 설명해줘
contextual_chunk_prefix: |
  이 문서는 외부 결제 승인 성공과 내부 DB commit이 원자적이지 않다는 점을 초급자에게
  bridge한다. rollback이 외부 승인을 취소하지 못하므로 보상 취소, 멱등성 키, outbox,
  재시도 상태 계약으로 실패 경계를 닫는 방법을 설명한다.
---
# Spring Beginner Bridge: 외부 승인 성공 뒤 DB 저장이 실패하면 rollback보다 보상 + 멱등성으로 닫기

> 한 줄 요약: 결제사 승인 성공과 우리 DB commit은 같은 트랜잭션이 아니므로, "외부 승인 성공 -> 이후 DB 실패"는 rollback으로 끝나는 문제가 아니라 **보상 취소 경로**와 **재시도 멱등성**을 같이 설계해야 닫힌다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md)
- [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [Idempotency Key Status Contract Examples](../database/idempotency-key-status-contract-examples.md)
- [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
- [Outbox, Saga, Eventual Consistency](../database/outbox-saga-eventual-consistency.md)
- [트랜잭션 경계 체크리스트 카드](../database/transaction-boundary-external-io-checklist-card.md)

retrieval-anchor-keywords: payment approval db failure beginner, rollback does not cancel payment, approve then db fail basics, payment compensation what is, cancel api idempotency beginner, payment retry what is, 결제 승인 후 db 실패, 결제 취소 보상 처음, 왜 롤백으로 결제 취소 안됨, payment approval local commit mismatch, approval id what is, payment attempt key basics

## 핵심 개념

이 장면은 "영수증이 두 장"이라고 보면 쉽다.

- 영수증 1: 외부 결제사가 승인했다
- 영수증 2: 우리 DB가 승인 사실을 저장했다

두 영수증은 같은 트랜잭션이 아니다. 그래서 DB rollback이 나도 외부 승인까지 같이 취소되지는 않는다.

초급자 기준 첫 문장은 이것이면 충분하다.

> `승인 성공 -> DB 실패`는 rollback 설명보다 보상(compensation) 설명이 먼저다.

## 한눈에 보기

| 지금 보인 상태 | 먼저 해야 할 판단 | 바로 피해야 할 반응 |
|---|---|---|
| 외부 승인 성공, DB 저장 실패 | "외부 성공 / 로컬 미반영" 상태로 본다 | rollback이면 결제도 끝났다고 생각 |
| 같은 요청이 다시 들어옴 | `paymentAttemptKey`나 `approvalId`로 먼저 조회한다 | 승인 API부터 다시 호출 |
| 취소 호출이 한 번 실패함 | 취소도 멱등하게 다시 시도할 준비를 한다 | 중복 취소를 무시하고 무작정 재호출 |

짧게 외우면 `승인 확인 -> 로컬 저장 확인 -> 보상 또는 재조회` 순서다.

## 왜 처음에 헷갈리나

| 흔한 기대 | 실제로는 |
|---|---|
| `@Transactional`이 실패했으니 결제도 같이 취소될 것이다 | 외부 결제사는 같은 로컬 트랜잭션에 묶여 있지 않다 |
| `flush()`를 했으니 거의 저장된 셈이다 | `flush`는 commit이 아니다 |
| 재시도면 같은 승인 API를 다시 부르면 된다 | 먼저 기존 승인 흔적과 멱등 키를 조회해야 한다 |

헷갈림의 원인은 기술이 많아서가 아니라, "외부 승인"과 "로컬 commit"을 한 덩어리로 보기 때문이다.

## 초급자 기본 대응 3단계

1. 승인 성공 응답의 `approvalId`와 요청 키(`paymentAttemptKey`)를 남긴다.
2. DB 저장이 실패하면 "결제가 남았을 수 있다"는 전제로 취소 보상 경로를 탄다.
3. 같은 요청이 다시 오면 새 승인보다 기존 상태 조회를 먼저 한다.

이 문서에서 초급자가 챙길 기본값은 아래 표 정도면 충분하다.

| 챙길 값 | 왜 필요한가 |
|---|---|
| `approvalId` | 외부에서 이미 승인된 건인지 확인하기 위해 |
| `paymentAttemptKey` | 같은 요청 재시도인지 구분하기 위해 |
| `cancel:{paymentAttemptKey}` 같은 취소 키 | 보상 재시도 때 중복 취소를 줄이기 위해 |

## 작은 예시

```java
public PaymentResult confirmPayment(ConfirmPaymentCommand command) {
    Approval approval = paymentGateway.approve(
        command.paymentToken(),
        command.paymentAttemptKey()
    ); // 외부 승인

    try {
        paymentTxService.recordApproval(command.orderId(), approval);
        return PaymentResult.completed(approval.approvalId());
    } catch (RuntimeException e) {
        compensationService.cancelApprovedPayment(
            approval.approvalId(),
            "cancel:" + command.paymentAttemptKey()
        );
        throw e;
    }
}
```

이 코드에서 초급자가 읽어야 할 핵심은 두 줄이다.

- 승인 호출과 DB 저장은 같은 단계가 아니다.
- DB 저장이 실패하면 새 승인보다 취소 보상 또는 상태 조회가 먼저다.

## 흔한 오해와 첫 교정

- "DB rollback이 났으니 결제도 자동 취소됐을 것이다"
  실제로는 외부 승인 상태가 남아 있을 수 있다.
- "취소 API는 한 번만 부를 테니 멱등 키가 필요 없다"
  재시도 상황에서는 취소도 중복 호출될 수 있다.
- "원인 분석이 끝날 때까지 그냥 에러만 내보내면 된다"
  돈이 걸린 흐름이라면 보상 task나 재조회 경로가 먼저 있어야 한다.

## 더 깊이 가려면

이 문서는 초급자 첫 판단까지만 다룬다. 아래부터는 일부러 다음 문서로 넘긴다.

- 외부 I/O를 왜 메인 트랜잭션 밖으로 빼는지: [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md)
- `flush`와 commit 차이가 왜 헷갈리는지: [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- 멱등 응답 상태를 더 자세히 보고 싶을 때: [Idempotency Key Status Contract Examples](../database/idempotency-key-status-contract-examples.md)
- reconciliation, outbox, saga 같은 더 큰 복구 그림: [Outbox, Saga, Eventual Consistency](../database/outbox-saga-eventual-consistency.md)
- 멱등 키 저장소 자체를 더 깊게 보고 싶을 때: [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)

## 한 줄 정리

결제 승인 뒤 DB 저장이 실패하면 "`@Transactional`이 왜 깨졌지?"보다 **승인은 남았는지, 기존 승인 키를 먼저 조회할지, 취소 보상을 어떻게 멱등하게 보낼지**를 먼저 생각하는 편이 초급자에게 안전하다.
