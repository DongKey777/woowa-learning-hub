# DDD, Hexagonal Architecture, Consistency Boundary

> 한 줄 요약: DDD는 도메인 경계를, Hexagonal Architecture는 의존 경계를, Consistency Boundary는 정합성 경계를 다루며, 세 가지를 함께 봐야 설계와 운영이 같은 방향으로 맞는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)

> retrieval-anchor-keywords:
> - DDD
> - hexagonal architecture
> - ports and adapters
> - bounded context
> - aggregate
> - consistency boundary
> - eventual consistency
> - anti-corruption layer
> - domain model

## 핵심 개념

이 세 가지는 서로 다른 문제를 푼다.

- DDD는 무엇을 하나의 모델로 볼지 정한다
- Hexagonal Architecture는 무엇이 안쪽이고 바깥쪽인지 정한다
- Consistency Boundary는 어디까지를 한 번에 강하게 맞출지 정한다

이걸 구분하지 않으면, 도메인 모델링, 의존성 제어, 트랜잭션 설계가 뒤섞여서 구조가 흐려진다.

---

## 깊이 들어가기

### 1. DDD는 모델링의 문제다

DDD는 비즈니스 규칙을 코드 구조와 용어에 반영하는 접근이다.

핵심 질문:

- 같은 단어가 같은 의미인가
- 어디까지를 같은 모델로 봐야 하는가
- 어떤 규칙이 가장 자주 바뀌는가

DDD가 잘 맞으면 도메인 언어가 코드에 자연스럽게 드러난다.

### 2. Hexagonal Architecture는 경계와 의존 방향의 문제다

핵심은 도메인이 중심에 있고, 외부 시스템은 포트와 어댑터로 감싸는 것이다.

좋은 효과:

- DB, MQ, 외부 API 교체가 쉬워진다
- 테스트가 쉬워진다
- 도메인이 인프라 세부에 오염되지 않는다

즉 hexagonal은 설계의 중심을 도메인으로 되돌린다.

### 3. Consistency Boundary는 정합성의 비용을 줄이는 문제다

모든 것을 하나의 트랜잭션으로 묶을 수는 없다.

그래서 다음을 구분해야 한다.

- 즉시 일관성이 필요한 경계
- eventual consistency로 충분한 경계
- 보상 처리가 가능한 경계

이 경계를 잘못 잡으면 락과 분산 트랜잭션 비용이 늘어난다.

### 4. Aggregate는 consistency boundary의 후보다

aggregate는 하나의 일관성 규칙 안에서 함께 바뀌어야 하는 객체 묶음이다.

하지만 aggregate를 서비스 경계와 1:1로 무조건 맞출 필요는 없다.
중요한 건 **같이 바뀌어야 하는 것**을 같이 묶는 것이다.

### 5. ACL과 Outbox는 경계 운영의 현실 도구다

외부 시스템은 도메인 언어와 다를 수 있다.
그럴 때 ACL이 필요하다.

경계를 넘어 상태를 전달해야 할 때는 outbox/inbox가 정합성과 전달 보장을 돕는다.

이 문맥은 [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)와 [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)와 연결된다.

---

## 실전 시나리오

### 시나리오 1: 주문, 결제, 재고를 한 모델로 묶고 싶다

DDD 관점에서는 용어가 다르면 다른 bounded context일 수 있다.
Hexagonal 관점에서는 각 context가 포트로만 통신해야 한다.
Consistency 관점에서는 결제와 재고를 같은 트랜잭션으로 묶지 않고 saga로 처리할 수 있다.

### 시나리오 2: 외부 배송사 API가 계속 바뀐다

ACL로 외부 모델을 내부 도메인에서 분리하고, 계약 테스트로 호환성을 지킨다.

### 시나리오 3: 모놀리스에서 서비스로 옮긴다

먼저 도메인 경계를 정리하고, 그다음 hexagonal 구조로 외부 의존을 감싼 뒤, consistency boundary를 기준으로 분리한다.

---

## 코드로 보기

```java
public interface OrderPort {
    OrderSummary findOrder(long orderId);
}

public class OrderService {
    private final OrderPort orderPort;

    public OrderService(OrderPort orderPort) {
        this.orderPort = orderPort;
    }
}
```

도메인 안쪽은 포트만 보고, 구현 세부는 바깥에 둔다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DDD만 적용 | 도메인 용어가 선명하다 | 인프라 경계가 약할 수 있다 | 규칙이 복잡할 때 |
| Hexagonal만 적용 | 교체와 테스트가 쉽다 | 경계 의미가 흐릴 수 있다 | 기술 교체가 잦을 때 |
| DDD + Hexagonal + consistency boundary | 모델과 운영이 정렬된다 | 설계 비용이 든다 | 변경이 크고 오래가는 시스템 |

세 가지를 함께 봐야 "좋은 설계"가 운영 가능한 구조가 된다.

---

## 꼬리질문

- 같은 용어가 다른 context에서 같은 의미인가?
- 어디까지를 한 consistency boundary로 묶을 것인가?
- 외부 시스템 변화는 ACL로 얼마나 흡수할 수 있는가?
- 도메인 모델과 인프라 의존 방향이 뒤집히지 않았는가?

## 한 줄 정리

DDD, Hexagonal Architecture, Consistency Boundary는 각각 도메인, 의존성, 정합성의 경계를 다루는 개념이며, 함께 써야 설계와 운영이 서로 어긋나지 않는다.
