---
schema_version: 3
title: Invariant-Preserving Command Model
concept_id: design-pattern/invariant-preserving-command-model
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- invariant-preserving-command
- intent-rich-command
- patch-command-smell
aliases:
- invariant preserving command
- intent rich command
- command precondition
- patch vs command model
- expected version command
- aggregate safe input model
- command model design
- partial dto smell
- 화면 patch vs command
- command granularity
symptoms:
- HTTP PATCH DTO나 화면 form을 그대로 command로 써 nullable field 조합 해석이 service 계층으로 샌다
- expected version, actor, reason, idempotency key 같은 실행 전제조건 없이 aggregate가 안전하게 상태 전이를 판단하게 만든다
- 하나의 UpdateEverything command가 여러 business intent를 섞어 aggregate invariant guard가 약해진다
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- design-pattern/command-handler-pattern
- design-pattern/aggregate-invariant-guard-pattern
- design-pattern/layered-validation-pattern
next_docs:
- design-pattern/aggregate-version-optimistic-concurrency-pattern
- design-pattern/transaction-script-vs-rich-domain-model
- design-pattern/domain-service-vs-pattern-abuse
linked_paths:
- contents/design-pattern/command-handler-pattern.md
- contents/design-pattern/aggregate-invariant-guard-pattern.md
- contents/design-pattern/aggregate-version-optimistic-concurrency-pattern.md
- contents/design-pattern/transaction-script-vs-rich-domain-model.md
- contents/design-pattern/layered-validation-pattern.md
- contents/design-pattern/state-pattern-workflow-payment.md
confusable_with:
- design-pattern/command-handler-pattern
- design-pattern/aggregate-invariant-guard-pattern
- design-pattern/transaction-script-vs-rich-domain-model
- design-pattern/layered-validation-pattern
forbidden_neighbors: []
expected_queries:
- Invariant preserving command model은 화면 patch DTO 대신 business intent와 precondition을 담는다는 게 무슨 뜻이야?
- UpdateOrderPatch처럼 nullable field를 나열하면 service가 조합 해석과 invariant 검증을 떠안는 이유가 뭐야?
- expectedVersion, actorId, reason, idempotencyKey는 command에 담아도 business logic 누수가 아닌 이유가 뭐야?
- command granularity를 하나의 business sentence 단위로 맞추는 기준은 뭐야?
- read DTO를 write command로 재사용하면 read concern이 aggregate invariant를 오염시키는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Invariant-Preserving Command Model playbook으로, generic patch DTO나
  nullable field list 대신 aggregate가 불변식을 지키며 해석할 수 있는 intent-rich command와
  expectedVersion, actor, reason, idempotencyKey 같은 precondition을 설계하는 기준을 설명한다.
---
# Invariant-Preserving Command Model

> 한 줄 요약: 좋은 command model은 화면 patch를 그대로 운반하지 않고, aggregate가 불변식을 지키며 해석할 수 있는 의도와 전제조건을 담아 서비스 계층의 규칙 누수를 줄인다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Command Handler Pattern](./command-handler-pattern.md)
> - [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)
> - [Aggregate Version and Optimistic Concurrency Pattern](./aggregate-version-optimistic-concurrency-pattern.md)
> - [Transaction Script vs Rich Domain Model](./transaction-script-vs-rich-domain-model.md)
> - [Layered Validation Pattern](./layered-validation-pattern.md)

---

## 핵심 개념

나쁜 command model은 보통 UI form이나 HTTP patch를 그대로 들고 온다.

- nullable field 나열
- `setX`, `setY`, `setZ`
- 무엇을 바꾸려는지보다 무엇이 들어왔는지 중심

이 구조는 service 계층에서 다음을 강요한다.

- 어떤 필드를 어떻게 해석할지 판단
- 어떤 조합이 유효한지 검증
- 어떤 상태에서 허용되는지 분기

Invariant-Preserving Command Model은 command가 aggregate 불변식을 지키는 방향으로 **의도와 전제조건을 먼저 드러내는 입력 모델**이어야 한다는 관점이다.

좋은 command 이름은 대개 "무엇을 바꾼다"보다 "무슨 일을 요청한다"에 가깝다. `status=CANCELLED`보다 `RequestOrderCancellation`이 aggregate에게 더 많은 의미와 검증 지점을 제공한다.

### Retrieval Anchors

- `invariant preserving command`
- `intent rich command`
- `command precondition`
- `patch vs command model`
- `expected version command`
- `aggregate safe input model`

---

## 깊이 들어가기

### 1. command는 partial DTO가 아니라 domain intent여야 한다

다음 둘은 다르다.

- `UpdateOrderRequest(address, memo, status)`
- `RequestCancellation(reason, expectedVersion)`

앞은 patch에 가깝고, 뒤는 의도에 가깝다.  
aggregate는 의도 중심 command를 훨씬 안전하게 해석할 수 있다.

### 2. command에는 precondition이 포함될 수 있다

불변식을 지키려면 입력 자체에 전제조건을 담는 편이 유리하다.

- expected version
- actor role
- requested at
- reason / justification
- idempotency key

이건 business logic을 command로 밀어 넣는 게 아니라, aggregate가 규칙을 해석하는 데 필요한 문맥을 주는 것이다.

### 3. nullable patch는 invariant bypass 통로가 되기 쉽다

이런 구조는 smell이다.

- `status`가 오면 바꾸고
- `address`가 있으면 바꾸고
- `couponCode`가 있으면 적용하고

그러면 service가 모든 조합을 해석해야 하고, aggregate guard가 약해진다.

### 4. command granularity는 use case granularity와 비슷해야 한다

하나의 command가 여러 의도를 섞으면 곧 모호해진다.

- `UpdateOrderEverything`
- `PatchPaymentAndShipping`

반대로 너무 쪼개도 orchestration 비용이 늘어난다.  
핵심은 **하나의 business sentence로 읽히는가**다.

### 5. command model은 read model 요구와 분리해야 한다

read 화면에 필요한 모든 필드가 command에도 필요한 건 아니다.

- 화면은 풍부한 표현
- command는 실행에 필요한 최소 의미

그래서 command를 read DTO에서 자동 생성하려 들면 invariants가 약해지기 쉽다.

---

## 실전 시나리오

### 시나리오 1: 주문 취소

`PatchOrder(status=CANCELLED)`보다 `RequestOrderCancellation(reason, expectedVersion)`이 더 안전하다.

### 시나리오 2: 주소 변경

주소 변경은 단순 field patch처럼 보여도, 배송 시작 여부와 actor 권한이 중요할 수 있다.  
`ChangeShippingAddress(newAddress, actorId, expectedVersion)`가 더 낫다.

### 시나리오 3: 결제 승인 반영

외부 응답을 그대로 patch하지 말고 `RecordPaymentAuthorization(paymentId, approvedAmount, approvedAt)`처럼 의미를 드러내는 command가 aggregate와 잘 맞는다.

---

## 코드로 보기

### patch smell

```java
public record UpdateOrderPatch(
    String status,
    String address,
    String memo
) {}
```

### intent-rich command

```java
public record RequestOrderCancellation(
    String orderId,
    String reason,
    long expectedVersion,
    String actorId
) {}
```

### handler

```java
public void handle(RequestOrderCancellation command) {
    Order order = orderRepository.findById(command.orderId()).orElseThrow();
    order.requestCancellation(command.reason(), command.actorId());
    orderRepository.save(order, command.expectedVersion());
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| generic patch model | 구현이 빠르다 | invariants가 서비스로 샌다 | 단순 CRUD |
| intent-rich command model | 규칙과 전제조건이 선명하다 | command 종류가 늘어난다 | 상태 전이와 불변식이 중요한 도메인 |
| read DTO 재사용 | 중복이 적어 보인다 | read concern이 write model을 오염시킨다 | 보통 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- command는 use case 의도를 드러내야 한다
- expected version/idempotency key 등 실행 전제조건을 포함할 수 있다
- patch 조합 해석이 커지면 command model을 다시 본다

---

## 꼬리질문

> Q: command에 expected version을 넣으면 business logic이 새는 것 아닌가요?
> 의도: 실행 전제조건과 도메인 규칙을 구분하는지 본다.
> 핵심: 아니다. 충돌 감지를 위한 문맥이며, 규칙 해석은 여전히 aggregate/handler가 맡는다.

> Q: patch model이 항상 나쁜가요?
> 의도: 과도한 일반화를 경계하는지 본다.
> 핵심: 단순 CRUD에는 괜찮지만 상태 전이와 invariants가 커지면 quickly 한계가 온다.

> Q: command가 너무 많아지면 어떡하죠?
> 의도: granularity 균형을 보는 질문이다.
> 핵심: business sentence 단위로 맞추고, 여러 의도가 섞인 command를 먼저 의심해 본다.

## 한 줄 정리

Invariant-Preserving Command Model은 aggregate가 불변식을 지키며 해석할 수 있도록, 화면 patch 대신 의도와 전제조건을 담은 command를 설계하게 해준다.
