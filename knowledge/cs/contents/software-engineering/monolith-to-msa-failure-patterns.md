# Monolith to MSA Failure Patterns

> 한 줄 요약: 모놀리스를 MSA로 옮기는 건 배포 단위를 쪼개는 일이 아니라, 실패와 정합성의 책임을 재배치하는 일이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [시스템 설계 면접 프레임워크](../system-design/system-design-framework.md)

---

## 핵심 개념

MSA 전환은 기술 선택이라기보다 **운영 모델의 변경**이다.
하나의 프로세스 안에서 함수 호출로 끝나던 일이, 이제는 네트워크 호출, 재시도, 장애, 관측성, 버전 관리 문제로 바뀐다.

전환이 실패하는 이유는 보통 이 사실을 과소평가하기 때문이다.

---

## 깊이 들어가기

### 1. 서비스 경계가 아니라 데이터 경계부터 깨진다

가장 흔한 실패는 "코드는 나눴는데 DB는 같이 쓰는" 상태다.

증상:

- 서비스가 서로의 테이블을 직접 참조한다
- 조인 없는 서비스 분리가 불가능하다
- 배포는 분리됐지만 장애는 같이 난다

이건 MSA가 아니라 **배포만 분리된 모놀리스**다.

### 2. 동기 호출 체인이 길어진다

모놀리스에서는 함수 호출이었던 것이 MSA에서는 RPC 체인이 된다.

```text
API -> Order -> Payment -> Inventory -> Notification
```

한 단계만 느려져도 전체 체인이 느려진다.
실패가 전파되는 속도도 빨라진다.

### 3. 분산 트랜잭션을 늦게 고민한다

전환 초반에 "일단 API만 나누자"로 시작하면, 나중에 가장 먼저 부딪히는 건 정합성이다.

- 주문은 생성됐는데 결제가 실패
- 결제는 성공했는데 재고가 부족
- 알림은 두 번 나감

이 문제는 `@Transactional`로 해결되지 않는다.
Outbox, Inbox, Saga, eventual consistency를 선택해야 한다.

### 4. 관측성 없이 쪼개면 디버깅이 불가능하다

서비스가 나뉘면 로그 하나로 끝나지 않는다.

- correlation id
- distributed tracing
- retry count
- timeout 구간
- 장애 재현용 시나리오

이 없으면 "어디가 느린지"가 아니라 "어디서 끊겼는지"도 모른다.

### 5. 조직 구조가 바뀌지 않으면 MSA가 무너진다

서비스를 나눈다는 건 팀의 소유권도 나누는 일이다.
팀 경계 없이 서비스만 나누면:

- 누가 소유하는지 애매하다
- 배포 책임이 겹친다
- 장애 대응이 느려진다

즉, MSA는 코드 리팩토링만이 아니다.

---

## 실전 시나리오

### 시나리오 1: 모놀리스를 서비스별로 잘랐는데 여전히 한 DB를 공유

```java
// order-service
public void placeOrder() {
    jdbcTemplate.update("insert into orders ...");
    jdbcTemplate.update("update inventory ..."); // 다른 서비스 테이블 직접 접근
}
```

이 구조는 서비스 경계가 없다.
DB 공유는 장애 전파와 릴리즈 결합을 그대로 남긴다.

### 시나리오 2: 동기 호출이 과도하게 늘어남

주문 생성이 여러 서비스의 응답을 기다리게 되면, 전체 SLA는 가장 느린 서비스에 맞춰진다.
전환 후 지연이 늘어난 이유가 "네트워크가 느려서"가 아니라, **동기 경로가 길어졌기 때문**일 수 있다.

### 시나리오 3: 이벤트만 던지고 재처리가 없음

Outbox 없이 브로커에 바로 발행하면, 저장은 성공하고 발행은 실패하는 구간이 생긴다.
반대로 Inbox 없이 소비하면 중복 전달에 취약하다.

### 시나리오 4: 모듈 분리 없이 서비스명만 바꿈

`order-service`, `payment-service`라는 이름만 붙이고 코드와 데이터는 여전히 섞여 있으면, 운영 비용만 늘어난다.

---

## 코드로 보기

### 모놀리스에서의 암묵적 결합

```java
public class OrderService {
    public void placeOrder() {
        orderRepository.save(order);
        paymentRepository.save(payment);
        inventoryRepository.reserve(item);
    }
}
```

하나의 트랜잭션으로 끝나서 편해 보이지만, 경계는 없다.

### MSA 전환 후의 명시적 경계

```java
public class OrderApplicationService {
    public OrderId placeOrder(CreateOrderCommand command) {
        Order order = orderFactory.create(command);
        orderRepository.save(order);
        outboxPublisher.publish(new OrderPlaced(order.id()));
        return order.id();
    }
}
```

```java
public class PaymentEventHandler {
    public void on(OrderPlaced event) {
        paymentClient.requestApproval(event.orderId());
    }
}
```

경계가 생기면 호출은 느려질 수 있지만, 실패 책임이 명확해진다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 모놀리스 유지 | 단순하고 빠르다 | 코드베이스가 커지면 결합이 커진다 | 조직/도메인이 아직 작다 |
| 모듈러 모놀리스 | 경계를 연습할 수 있다 | 규칙을 안 지키면 금방 섞인다 | MSA 전 단계로 좋다 |
| 부분적 MSA | 필요한 곳만 분리한다 | 복잡도가 혼재한다 | 특정 병목만 독립화할 때 |
| 완전 MSA | 팀별 독립 배포가 가능하다 | 운영/관측성 비용이 높다 | 팀과 도메인 경계가 명확할 때 |

핵심은 "MSA가 좋다"가 아니라, **지금의 문제를 해결하는 최소한의 분리 수준**을 고르는 것이다.

---

## 꼬리질문

> Q: 모놀리스를 언제 MSA로 바꿔야 하나요?
> 의도: 유행이 아니라 신호를 기준으로 판단하는지 확인
> 핵심: 팀/도메인/배포/장애 책임이 더 이상 한 덩어리로 유지되지 않을 때다

> Q: 서비스 분리 후 가장 먼저 깨지는 것은 무엇인가요?
> 의도: 정합성과 운영 복잡도를 이해하는지 확인
> 핵심: 데이터 일관성, 호출 지연, 디버깅 난이도 순으로 흔들린다

> Q: MSA로 가기 전에 먼저 해야 할 것은 무엇인가요?
> 의도: 과도한 분해를 피할 수 있는지 확인
> 핵심: 모듈 경계를 명확히 하고, DB/의존성/배포 단위를 정리하는 것이다

## 한 줄 정리

모놀리스에서 MSA로 가는 실패는 코드 분할이 아니라, 데이터·호출·책임·운영 경계를 제대로 다시 그리지 못해서 생긴다.
