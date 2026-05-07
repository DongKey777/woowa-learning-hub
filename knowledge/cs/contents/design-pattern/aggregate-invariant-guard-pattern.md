---
schema_version: 3
title: Aggregate Invariant Guard Pattern
concept_id: design-pattern/aggregate-invariant-guard-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- aggregate-invariant-guard
- domain-invariant
- rich-domain-model
aliases:
- aggregate invariant guard
- domain invariant guard
- state transition guard
- behavior rich aggregate
- collection mutation guard
- invariant preserving command
- aggregate consistency protection
- 애그리거트 불변식
- 도메인 불변식 가드
symptoms:
- service layer에서 aggregate 내부 컬렉션을 직접 수정해 도메인 불변식 검증이 여러 곳에 흩어진다
- DTO validation과 aggregate invariant를 같은 것으로 보고 현재 상태에서 허용되지 않는 전이를 놓친다
- public setter나 getLines().add 같은 API 때문에 root를 통하지 않는 상태 변경이 가능하다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/transaction-script-vs-rich-domain-model
- design-pattern/layered-validation-pattern
next_docs:
- design-pattern/invariant-preserving-command-model
- design-pattern/specification-pattern
- design-pattern/state-pattern-workflow-payment
linked_paths:
- contents/design-pattern/aggregate-boundary-vs-transaction-boundary.md
- contents/design-pattern/aggregate-root-vs-unit-of-work.md
- contents/design-pattern/invariant-preserving-command-model.md
- contents/design-pattern/transaction-script-vs-rich-domain-model.md
- contents/design-pattern/layered-validation-pattern.md
- contents/design-pattern/specification-pattern.md
confusable_with:
- design-pattern/layered-validation-pattern
- design-pattern/transaction-script-vs-rich-domain-model
- design-pattern/specification-pattern
- design-pattern/aggregate-boundary-vs-transaction-boundary
forbidden_neighbors: []
expected_queries:
- Aggregate Invariant Guard는 service layer로 도메인 규칙이 새지 않게 어떻게 막아?
- DTO validation과 aggregate invariant는 형식 검증과 상태 전이 규칙 관점에서 어떻게 달라?
- public setter 대신 markPaid나 changeShippingAddress 같은 의도 메서드를 쓰는 이유가 뭐야?
- aggregate 내부 컬렉션을 getLines().add로 열면 어떤 불변식 누수가 생겨?
- 외부 정책이 필요한 규칙은 aggregate guard와 specification을 어떻게 조합해?
contextual_chunk_prefix: |
  이 문서는 Aggregate Invariant Guard Pattern playbook으로, aggregate root를
  통해서만 상태 전이와 컬렉션 변경을 허용하고 DTO validation과 다른 domain
  invariant를 intent method와 policy/specification 조합으로 보호하는 방법을 설명한다.
---
# Aggregate Invariant Guard Pattern

> 한 줄 요약: Aggregate Invariant Guard는 aggregate의 상태 전이와 컬렉션 변경을 오직 의도 있는 메서드로만 통제해, 도메인 불변식이 서비스 계층으로 새지 않게 막는 설계다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Boundary vs Transaction Boundary](./aggregate-boundary-vs-transaction-boundary.md)
> - [Aggregate Root vs Unit of Work](./aggregate-root-vs-unit-of-work.md)
> - [Invariant-Preserving Command Model](./invariant-preserving-command-model.md)
> - [Transaction Script vs Rich Domain Model](./transaction-script-vs-rich-domain-model.md)
> - [Layered Validation Pattern](./layered-validation-pattern.md)
> - [Specification Pattern](./specification-pattern.md)
> - [State Pattern: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)

---

## 핵심 개념

Aggregate를 쓰기로 했다면 제일 먼저 지켜야 하는 건 "root를 통해서만 상태가 바뀐다"는 규칙이다.  
하지만 실제 코드에서는 종종 이렇게 무너진다.

- 서비스가 내부 컬렉션을 직접 수정한다
- setter가 public으로 열려 있다
- 검증이 controller, service, repository에 중복된다

Aggregate Invariant Guard 패턴은 이런 누수를 막는 실전 규칙 모음에 가깝다.

- 생성 시점의 guard
- 상태 전이 guard
- 컬렉션 변경 guard
- 외부 정책과 결합할 때의 guard

### Retrieval Anchors

- `aggregate invariant guard`
- `domain invariant`
- `state transition guard`
- `behavior rich aggregate`
- `collection mutation guard`
- `aggregate consistency protection`
- `invariant preserving command`

---

## 깊이 들어가기

### 1. 불변식은 DTO validation과 다르다

입력값 validation은 "형식이 맞는가"를 본다.  
Aggregate invariant는 "이 상태 변화가 지금 허용되는가"를 본다.

예를 들면 이런 차이다.

- DTO validation: 수량이 1 이상인가
- Aggregate invariant: 이미 확정된 주문에 항목을 추가해도 되는가

둘은 겹칠 수 있지만, 대체 관계는 아니다.

### 2. Guard는 메서드 시그니처에서 시작한다

Aggregate가 진짜 경계라면 상태 변경은 intent를 드러내는 메서드로만 열려야 한다.

- `setStatus(PAID)` 보다 `markPaid(paymentId)`
- `getLines().add(...)` 보다 `addLine(productId, quantity)`
- `setAddress(...)` 보다 `changeShippingAddress(newAddress)`

즉 "필드 변경"이 아니라 "도메인 행위"를 API로 만든다.

### 3. 모든 규칙을 aggregate 혼자 다 알 필요는 없다

일부 규칙은 외부 정책을 필요로 한다.

- 취소 수수료 계산
- 회원 등급별 할인 한도
- 시간대별 예약 허용 정책

이때 aggregate가 repository나 외부 API를 직접 알면 안 된다.  
대신 policy, specification, decision object 같은 입력을 받아 판단하는 편이 안전하다.

### 4. cross-aggregate 규칙은 guard 패턴의 예외가 아니라 경계 확인 신호다

"주문 total과 결제 승인 금액이 항상 같아야 한다" 같은 규칙을 보면 많은 팀이 aggregate를 키우려 한다.  
하지만 이건 종종 두 aggregate를 같은 것으로 착각한 결과다.

Senior 기준은 먼저 이 질문을 던진다.

- 정말 메서드 반환 직후 즉시 참이어야 하는가
- 아니면 process manager, saga, retry로 맞출 수 있는가

Aggregate Guard는 **하나의 aggregate 내부 즉시 일관성**을 지키는 패턴이지, 모든 시스템 규칙을 즉시 동기화하는 패턴이 아니다.

### 5. Guard 실패를 예외만으로 표현할지 결과 객체로 표현할지는 맥락 문제다

내부 규칙 위반이면 예외가 자연스러울 수 있다.  
사용자에게 설명 가능한 거절이라면 decision/result 타입이 더 나을 수 있다.

중요한 건 표현 방식이 아니라 guard 책임이 서비스 밖으로 새지 않는 것이다.

---

## 실전 시나리오

### 시나리오 1: 배송 시작 이후 주소 변경 금지

주소 형식 validation은 입력 계층에서도 가능하지만, 배송 시작 이후 변경 금지는 `Order` aggregate가 보장해야 한다.

### 시나리오 2: 쿠폰 최대 사용 수량

수량 합계와 최대 할인 금액 검사는 장바구니 계산 서비스가 아니라 aggregate의 변경 메서드 안에 두는 편이 안전하다.

### 시나리오 3: 티켓 예약 좌석 점유

좌석 상태가 `RESERVED` 또는 `SOLD`일 때는 다시 점유할 수 없어야 한다.  
이 전이 규칙이 서비스 메서드마다 흩어지면 race 상황에서 누락되기 쉽다.

---

## 코드로 보기

### 누수된 aggregate

```java
public class Order {
    private OrderStatus status;
    private final List<OrderLine> lines = new ArrayList<>();

    public List<OrderLine> getLines() {
        return lines;
    }

    public void setStatus(OrderStatus status) {
        this.status = status;
    }
}
```

외부가 아무 제약 없이 상태를 망가뜨릴 수 있다.

### Guard가 있는 aggregate

```java
public class Order {
    private OrderStatus status;
    private final List<OrderLine> lines = new ArrayList<>();

    public void addLine(ProductId productId, int quantity) {
        ensureEditable();
        if (quantity <= 0) {
            throw new IllegalArgumentException("quantity must be positive");
        }
        lines.add(new OrderLine(productId, quantity));
    }

    public void markPaid(PaymentId paymentId) {
        if (status != OrderStatus.PENDING_PAYMENT) {
            throw new IllegalStateException("payment not allowed");
        }
        status = OrderStatus.PAID;
    }

    public void changeShippingAddress(Address newAddress) {
        ensureEditable();
        // address replacement
    }

    private void ensureEditable() {
        if (status == OrderStatus.SHIPPED || status == OrderStatus.CANCELLED) {
            throw new IllegalStateException("order is no longer editable");
        }
    }
}
```

### 정책과 함께 쓰는 방식

```java
public void cancel(CancelReason reason, RefundPolicy refundPolicy) {
    if (!refundPolicy.isCancellable(this, reason)) {
        throw new IllegalStateException("refund policy rejected cancellation");
    }
    status = OrderStatus.CANCELLED;
}
```

Aggregate는 상태 전이를 통제하고, 외부 정책은 판단 재료를 제공한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 서비스 계층 검증 | 구현이 빠르다 | 규칙이 흩어지고 누락되기 쉽다 | 아주 단순한 CRUD |
| Aggregate Invariant Guard | 즉시 일관성이 선명하다 | 모델링과 테스트 비용이 든다 | 상태 전이와 불변식이 중요한 도메인 |
| 정책/사양과 조합한 Guard | 복잡한 규칙을 분리할 수 있다 | 추상화가 과해질 수 있다 | 외부 조건이 섞이는 복잡한 도메인 |

판단 기준은 다음과 같다.

- 메서드 종료 직후 항상 참이어야 하는 규칙이면 aggregate 안에서 guard
- 경계 밖 정보가 필요하면 policy/specification과 조합
- cross-aggregate 규칙은 더 큰 aggregate가 아니라 별도 프로세스를 먼저 검토

---

## 꼬리질문

> Q: 입력 validation이 있는데 aggregate guard까지 꼭 필요할까요?
> 의도: 형식 검증과 도메인 규칙을 분리해서 보는지 확인한다.
> 핵심: 필요하다. 입력이 정상이더라도 현재 상태에서 허용되지 않는 전이는 많다.

> Q: setter를 private으로만 바꾸면 해결되나요?
> 의도: 캡슐화와 의미 있는 행위 모델링의 차이를 보는 질문이다.
> 핵심: 일부는 해결되지만, intent를 드러내는 메서드와 전이 규칙이 함께 있어야 한다.

> Q: cross-aggregate 규칙도 aggregate guard로 막아야 하나요?
> 의도: aggregate 경계를 과도하게 키우지 않는지 확인한다.
> 핵심: 보통 아니다. saga, process manager, retry, reservation으로 풀어야 하는 경우가 많다.

## 한 줄 정리

Aggregate Invariant Guard는 aggregate 안에서만 허용되는 상태 전이와 변경 규칙을 명시적으로 가두어, 일관성 책임이 서비스 계층으로 새는 것을 막는다.
