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

retrieval-anchor-keywords: payment approval db failure compensation primer, external approval succeeded local transaction failed, spring payment compensation beginner, approve then db fail cancel payment, payment cancel idempotency beginner, transactional payment approval gap, rollback does not cancel payment, external approval local commit mismatch, payment compensation retry key, cancel api idempotency key, approval success db rollback beginner, spring payment approval compensation bridge, 결제 승인 후 db 실패, 결제 승인 후 취소 보상, 롤백으로 결제 취소 안됨, 승인 성공 후 저장 실패, 결제 멱등성 키 입문, 취소 api 멱등성, 승인 id 중복 방지, payment approval reconciliation beginner

## 먼저 mental model 한 줄

초급자는 이 장면을 "영수증이 두 장이다"로 보면 쉽다.

- 영수증 1: 외부 결제사가 승인했다
- 영수증 2: 우리 DB가 승인 사실을 commit했다

문제는 두 영수증이 **같이 찢어지지 않는다**는 점이다.

그래서 `승인 성공 -> DB 실패`가 나오면,

- DB rollback은 우리 쪽 기록만 되돌린다
- 결제사 승인 자체는 그대로 남을 수 있다

즉 이 상황의 기본 언어는 "`@Transactional` 실패"가 아니라 **보상(compensation)** 이다.

## 30초 그림

```text
1. paymentGateway.approve(...) 성공
2. 우리 서비스가 payment/order 상태를 DB에 저장하려고 함
3. 여기서 unique/lock/timeout/connection 문제로 tx 실패
4. DB rollback 발생
5. 하지만 결제사 승인 상태는 남아 있을 수 있음
6. 그래서 cancel/refund 같은 보상 작업이 따로 필요
```

핵심 한 줄:

> 외부 승인 성공 뒤의 DB 실패는 "같이 rollback될까?"가 아니라 "승인을 어떻게 안전하게 취소하거나 복구할까?"를 묻는 문제다.

## 왜 초급자가 특히 헷갈리나

보통은 이런 기대가 섞여 있기 때문이다.

| 흔한 기대 | 실제로는 |
|---|---|
| `@Transactional`이 실패했으니 결제도 같이 취소될 것이다 | 외부 결제사는 같은 로컬 트랜잭션에 묶여 있지 않다 |
| `flush()`를 했으니 거의 확정된 것 같다 | `flush`는 commit이 아니다 |
| 재시도하면 다시 승인 호출해도 되겠지 | 중복 승인 위험이 있으므로 먼저 멱등 키와 기존 승인 조회가 필요하다 |
| 일단 에러만 던지고 로그 남기면 된다 | 사용자 돈이 걸린 경우라 보상 경로와 재시도 계약이 필요하다 |

## 이 장면에서 먼저 나눌 3가지

| 상자 | 질문 | 초급자용 기본값 |
|---|---|---|
| 승인 | 외부 결제사는 이미 성공했는가 | 승인 응답의 `approvalId`와 승인 요청 멱등 키를 잡아 둔다 |
| 로컬 기록 | 우리 DB는 승인 사실을 commit했는가 | 실패하면 "외부 성공 / 로컬 미반영" 상태로 본다 |
| 복구 | 이 어긋남을 어떻게 닫을까 | 취소 API 보상 또는 별도 reconciliation 작업을 준비한다 |

이 세 상자를 섞지 않으면 판단이 쉬워진다.

## 가장 안전한 초급자 기본 흐름

### 1. 승인 호출은 트랜잭션 밖에서 한다

외부 승인은 보통 짧은 로컬 DB 트랜잭션과 분리한다.

```java
public PaymentResult confirmPayment(ConfirmPaymentCommand command) {
    Approval approval = paymentGateway.approve(
        command.paymentToken(),
        command.paymentAttemptKey()
    ); // external I/O, tx 밖

    try {
        paymentTxService.recordApproval(command.orderId(), approval, command.paymentAttemptKey());
        return PaymentResult.completed(approval.approvalId());
    } catch (RuntimeException e) {
        compensationService.compensateApprovalFailure(command.orderId(), approval, command.paymentAttemptKey(), e);
        throw e;
    }
}
```

```java
@Service
public class PaymentTxService {

    @Transactional
    public void recordApproval(Long orderId, Approval approval, String paymentAttemptKey) {
        paymentRepository.save(
            Payment.approved(orderId, approval.approvalId(), paymentAttemptKey)
        );
        orderRepository.markPaid(orderId, approval.approvalId());
    }
}
```

여기서 초급자가 먼저 읽어야 할 포인트는 이것이다.

- 외부 승인과 로컬 DB commit은 애초에 다른 단계다.
- DB 기록 실패는 `catch` 바깥에서 별도 복구 흐름으로 다뤄야 한다.

### 2. DB 저장이 실패하면 보상 경로를 즉시 탄다

보상은 보통 이런 뜻이다.

- 승인했다면 `cancel` 또는 `refund` API를 호출한다
- 취소가 바로 안 되면 재시도 가능한 compensation task를 남긴다

```java
public void compensateApprovalFailure(
    Long orderId,
    Approval approval,
    String paymentAttemptKey,
    RuntimeException cause
) {
    String cancelRequestKey = "cancel:" + paymentAttemptKey;

    paymentGateway.cancel(approval.approvalId(), cancelRequestKey);
    recoveryTxService.recordCompensated(orderId, approval.approvalId(), cause.getMessage());
}
```

이때 중요한 것은 **원래 실패한 트랜잭션에 다시 기대지 않는 것**이다.

- 원래 tx는 이미 rollback됐다
- 취소 호출과 복구 기록은 별도 경계에서 움직여야 한다

### 3. 취소도 멱등하게 설계한다

초급자는 승인 멱등성만 떠올리고 취소 멱등성은 빼먹기 쉽다.

하지만 재시도 시나리오에서는 취소도 여러 번 호출될 수 있다.

| 작업 | 멱등 키 예시 | 왜 필요한가 |
|---|---|---|
| 승인 요청 | `paymentAttemptKey` | 네트워크 재시도나 사용자 중복 클릭으로 승인 두 번 나는 것을 줄인다 |
| 승인 결과 저장 | `approvalId UNIQUE` 또는 `paymentAttemptKey UNIQUE` | 같은 승인 응답을 우리 DB에 두 번 적지 않기 위해 |
| 취소 요청 | `cancelRequestKey = cancel:{paymentAttemptKey}` | 보상 재시도 중 중복 취소를 막기 위해 |
| 사용자 재요청 처리 | `paymentAttemptKey` fresh read | "이미 승인됐나 / 이미 취소됐나 / 아직 처리중인가"를 판별하기 위해 |

짧게 외우면:

- 승인도 멱등
- 취소도 멱등
- 로컬 저장도 멱등

## 재시도할 때 무엇부터 확인하나

실패 뒤 같은 요청이 다시 들어오면 초급자는 "다시 승인 호출"부터 하기 쉽다.
하지만 기본 순서는 그 반대다.

1. `paymentAttemptKey`로 우리 idempotency/payment row를 먼저 찾는다.
2. 이미 승인 저장이 끝났으면 기존 결과를 replay한다.
3. 로컬 기록은 없는데 `approvalId` 또는 외부 거래 키가 남아 있으면 결제사 상태를 조회한다.
4. 외부 승인만 있고 로컬 기록이 없으면 cancel 보상 또는 reconciliation 흐름으로 보낸다.
5. 정말 아무 흔적이 없을 때만 새 승인 시도를 검토한다.

핵심은:

> retry의 첫 질문은 "다시 호출할까?"가 아니라 "이미 어디까지 갔나?"다.

## `REQUIRES_NEW`를 여기서 어떻게 이해하면 되나

초급자 기준으로는 이렇게만 기억하면 충분하다.

| 상황 | `REQUIRES_NEW`에 기대할 수 있는 것 | 기대하면 안 되는 것 |
|---|---|---|
| 보상 이력, 장애 메모, recovery task를 별도 로컬 commit으로 남기기 | 가능 | 외부 결제 승인과 원자적으로 묶기 |
| 취소 API 호출 결과를 별도 감사 로그로 저장하기 | 가능 | "새 tx니까 외부 승인도 자동 복구"라는 기대 |

즉 `REQUIRES_NEW`는 **보상 기록을 따로 남기는 도구**일 수는 있어도,
결제사 승인과 우리 DB를 한 몸으로 만드는 도구는 아니다.

## 자주 하는 오해 5개

- "DB rollback이 났으니 결제도 자동으로 취소됐을 것이다"
- "`flush`를 했으니 승인 후 저장 실패는 거의 없을 것이다"
- "재시도면 같은 승인 API를 한 번 더 때리면 된다"
- "취소 API는 한 번만 부를 거라 멱등 키가 필요 없다"
- "보상 실패는 로그만 남겨 두고 나중에 수동 대응하면 된다"

위 다섯 개는 초급자 코드리뷰에서 자주 막아야 하는 오해다.

## 초급자용 1페이지 대응표

| 지금 관찰한 상태 | 바로 해야 할 생각 | 피해야 할 반응 |
|---|---|---|
| 외부 승인 성공, DB 저장 실패 | 보상 취소 경로를 탄다 | rollback이면 끝났다고 생각 |
| 같은 요청이 다시 들어옴 | idempotency row / 승인 ID부터 조회 | 곧바로 승인 API 재호출 |
| 취소 API가 timeout | 취소 멱등 키로 재시도 가능하게 만든다 | 중복 취소를 무시하고 무작정 반복 |
| 원인 분석이 오래 걸림 | recovery task나 reconciliation 대상으로 남긴다 | 로그만 찍고 유실 |

## 여기서 어디로 가면 되나

| 지금 더 필요한 것 | 다음 문서 |
|---|---|
| 왜 외부 I/O를 메인 tx 밖으로 빼야 하는지 먼저 다시 보고 싶다 | [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](./spring-service-layer-external-io-after-commit-outbox-primer.md) |
| `flush`와 commit 차이 때문에 "거의 저장된 것 같은데?"가 계속 헷갈린다 | [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md) |
| duplicate 뒤 fresh read 응답을 어떻게 닫는지 보고 싶다 | [Idempotency Key Status Contract Examples](../database/idempotency-key-status-contract-examples.md) |
| 보상/사가를 더 넓은 그림으로 보고 싶다 | [Outbox, Saga, Eventual Consistency](../database/outbox-saga-eventual-consistency.md) |

## 한 줄 정리

외부 결제 승인 뒤 DB 저장이 실패하면, 초급자는 "`@Transactional`이 왜 rollback됐지?"보다 **승인 사실은 남았는가, 취소 보상은 어떻게 멱등하게 보낼 것인가, 같은 요청이 다시 오면 어디까지 진행됐는지 먼저 조회할 것인가**를 먼저 생각해야 한다.
