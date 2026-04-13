# @Transactional 깊이 파기

> 한 줄 요약: Spring 트랜잭션은 프록시 기반으로 동작하므로, 전파 규칙과 롤백 규칙, `readOnly`, 격리수준, 경계 설계를 같이 봐야 제대로 쓸 수 있다.

**난이도: 🔴 Advanced**

> 이 주제의 IoC/DI 관점은 [IoC 컨테이너와 DI](./ioc-di-container.md)를, 프록시 기반 동작 원리는 [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)를 함께 보면 이해가 빨라진다.

> 관련 문서:
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring Multiple Transaction Managers and Qualifier Boundaries](./spring-multiple-transaction-managers-qualifier-boundaries.md)
> - [Spring Transactional Test Rollback Misconceptions](./spring-transactional-test-rollback-misconceptions.md)
> - [Spring EventListener, TransactionalEventListener, and Outbox](./spring-eventlistener-transaction-phase-outbox.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

retrieval-anchor-keywords: transaction boundary, propagation, rollback rules, isolation level, transaction manager, synchronization callback, afterCommit, savepoint, rollback-only, qualifier, test rollback

---

## 핵심 개념

`@Transactional`은 "메서드 앞뒤로 트랜잭션을 열고 닫는 기능"처럼 보이지만, 실제로는 **Spring AOP 프록시가 메서드 호출을 가로채는 방식**으로 동작한다.

핵심은 다음 네 가지다.

- 트랜잭션은 보통 메서드 단위로 시작하고 종료된다.
- 프록시를 거친 호출에서만 트랜잭션 어드바이스가 적용된다.
- 전파 규칙(propagation)은 "이미 트랜잭션이 있으면 어떻게 할지"를 정한다.
- 롤백 규칙은 "예외가 났을 때 실제로 롤백할지"를 정한다.

Spring의 기본 롤백 규칙은 생각보다 단순하다.

- `RuntimeException`, `Error`는 기본적으로 롤백
- 체크 예외(`Exception` 계열)는 기본적으로 커밋

이 차이를 모르면 "예외가 났는데 왜 DB가 반영됐지?" 같은 버그를 만나기 쉽다.

---

## 깊이 들어가기

### 1. 프록시가 트랜잭션을 건다

`@Transactional`은 실제 객체에 직접 붙는 마법이 아니라, 프록시가 메서드 호출을 감싸는 방식이다.

즉 아래 흐름이다.

1. 클라이언트가 빈을 호출한다.
2. 실제 빈이 아니라 프록시가 먼저 호출을 받는다.
3. 프록시가 트랜잭션을 시작한다.
4. 타깃 메서드를 실행한다.
5. 정상 종료면 커밋, 예외면 규칙에 따라 롤백한다.

이 때문에 같은 클래스 내부에서 `this.someMethod()`로 호출하면 프록시를 거치지 않아 트랜잭션이 적용되지 않는다.

### 2. propagation은 트랜잭션 합류 전략이다

자주 쓰는 전파 옵션은 아래와 같다.

| 옵션 | 의미 | 사용 감각 |
|------|------|-----------|
| `REQUIRED` | 기존 트랜잭션이 있으면 합류, 없으면 새로 생성 | 기본값, 대부분의 서비스 계층 |
| `REQUIRES_NEW` | 기존 트랜잭션을 잠시 보류하고 새 트랜잭션 생성 | 감사 로그, 보조 기록, 외부 알림 저장 |
| `NESTED` | savepoint 기반 중첩 트랜잭션 | JDBC/DB 지원이 필요, 제한적으로 사용 |
| `SUPPORTS` | 있으면 참여, 없으면 비트랜잭션 | 조회성 메서드 |
| `MANDATORY` | 반드시 기존 트랜잭션이 있어야 함 | 하위 계층 보호 |
| `NEVER` | 트랜잭션이 있으면 예외 | 트랜잭션 밖에서만 동작해야 할 때 |
| `NOT_SUPPORTED` | 기존 트랜잭션을 잠시 중단 | 아주 드문 케이스 |

실무에서는 `REQUIRED`와 `REQUIRES_NEW`를 가장 많이 구분해서 쓴다.

전파를 선택할 때는 "같이 실패해야 하는가"와 "독립 커밋이 필요한가"를 먼저 본다.

- 감사 로그처럼 남아야 하면 `REQUIRES_NEW`
- 같은 결제/재고 정합성처럼 같이 묶여야 하면 `REQUIRED`
- 배치에서 일부만 되돌려야 하면 `NESTED`와 savepoint를 검토

### 3. rollback 규칙은 예외 종류를 본다

롤백 기준을 명시하지 않으면 Spring은 기본적으로 런타임 예외에만 롤백한다.

```java
@Transactional
public void placeOrder() {
    orderRepository.save(order);
    throw new IllegalStateException("재고 부족");
}
```

위 코드는 롤백된다. 하지만 아래는 기본적으로 커밋될 수 있다.

```java
@Transactional
public void placeOrder() throws Exception {
    orderRepository.save(order);
    throw new Exception("체크 예외");
}
```

체크 예외도 롤백하고 싶으면 명시해야 한다.

```java
@Transactional(rollbackFor = Exception.class)
public void placeOrder() throws Exception {
    orderRepository.save(order);
    throw new Exception("체크 예외");
}
```

### 4. `readOnly`는 "조회만 하겠다"는 힌트다

`readOnly = true`는 단순 주석이 아니다. Spring과 JPA 구현체가 이를 활용해 불필요한 변경 감지를 줄이거나, flush 전략을 보수적으로 바꾸는 데 도움을 준다.

다만 이것만으로 DB 수준에서 완전한 읽기 전용이 보장되는 것은 아니다.

- 애플리케이션 레벨 힌트로 이해하는 것이 안전하다.
- 조회 성능 최적화에 유리하지만, 쓰기를 막아주는 보안 장치로 믿으면 안 된다.
- 쓰기 시도가 섞이면 기대와 다르게 동작할 수 있으므로 조회 전용 메서드로만 쓰는 편이 낫다.

현실적으로는 `readOnly`를 "안전장치"로 믿기보다, **조회 전용 메서드의 의도 표시와 최적화 힌트**로 보는 편이 정확하다.

### 5. isolation은 동시성 충돌의 해상도다

격리수준은 트랜잭션이 서로를 얼마나 보지 못하게 할지 정한다.

- `READ_COMMITTED`: 커밋된 데이터만 읽는다.
- `REPEATABLE_READ`: 같은 트랜잭션 내에서는 같은 값을 다시 읽는다.
- `SERIALIZABLE`: 가장 엄격하지만 비용이 크다.

중요한 점은, **이론과 실제 DB 구현이 다를 수 있다**는 것이다. 특히 MySQL InnoDB는 표준 SQL 설명만 보면 헷갈리는 부분이 있으므로, "내 DB가 실제로 어떤 락을 잡는가"까지 봐야 한다.

### 6. transaction manager 선택도 경계다

여러 transaction manager가 공존하면 `@Transactional`이 어떤 manager를 쓰는지 명시해야 한다.

```java
@Transactional(transactionManager = "jdbcTxManager")
public void writeLedger() {
}
```

이 문맥은 [Spring Multiple Transaction Managers and Qualifier Boundaries](./spring-multiple-transaction-managers-qualifier-boundaries.md)와 같이 봐야 한다.

### 7. synchronization callback은 커밋 뒤 실행 경계다

트랜잭션 안에서 완료 시점에 맞춰 후속 작업을 붙일 수 있지만, `afterCommit`은 이미 커밋이 끝난 뒤라는 점을 잊으면 안 된다.

이건 [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)와 연결된다.

---

## 실전 시나리오

### 시나리오 1: self-invocation 때문에 트랜잭션이 안 걸림

```java
@Service
public class OrderService {
    public void placeOrder() {
        createOrder(); // 프록시를 거치지 않음
    }

    @Transactional
    public void createOrder() {
        // 트랜잭션이 기대대로 적용되지 않을 수 있다
    }
}
```

이 코드는 `placeOrder()` 내부 호출이므로 `createOrder()`의 `@Transactional`이 무시될 수 있다.

해결은 보통 셋 중 하나다.

- 메서드를 다른 빈으로 분리한다.
- 외부에서 프록시를 통해 호출되도록 구조를 바꾼다.
- 정말 필요한 경우에만 AOP 노출 방식을 검토한다.

### 시나리오 2: 예외가 났는데 데이터가 남음

체크 예외를 던졌는데 롤백이 안 된 경우다.

```java
@Transactional
public void updateProfile() throws IOException {
    userRepository.save(user);
    throw new IOException("외부 파일 저장 실패");
}
```

이 경우 기본 규칙상 커밋될 수 있다. 그래서 외부 시스템 연동처럼 체크 예외가 자주 나오는 코드라면 `rollbackFor`를 명시적으로 지정해야 한다.

### 시나리오 3: `REQUIRES_NEW`로 보조 로그를 남김

주문 저장이 실패해도 감사 로그는 남겨야 할 수 있다.

```java
@Service
public class AuditService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void writeAudit(String message) {
        auditRepository.save(new AuditLog(message));
    }
}
```

이렇게 하면 바깥 트랜잭션이 롤백돼도 감사 로그는 별도 트랜잭션으로 커밋될 수 있다.

하지만 남용하면 트랜잭션이 쪼개져 정합성 추적이 어려워진다.

---

## 코드로 보기

### 전파와 롤백을 함께 보는 예시

```java
@Service
public class PaymentService {
    private final OrderRepository orderRepository;
    private final AuditService auditService;

    public PaymentService(OrderRepository orderRepository, AuditService auditService) {
        this.orderRepository = orderRepository;
        this.auditService = auditService;
    }

    @Transactional
    public void pay(Long orderId) {
        orderRepository.markPaid(orderId);
        auditService.writeAudit("paid: " + orderId);
        throw new IllegalStateException("결제 후 검증 실패");
    }
}
```

동작 관점:

- `pay()`는 `REQUIRED` 기본값이라 하나의 트랜잭션으로 열린다.
- `writeAudit()`은 `REQUIRES_NEW`라 별도 트랜잭션으로 커밋된다.
- `pay()`에서 예외가 나면 바깥 주문 상태는 롤백된다.
- 감사 로그는 남는다.

이 패턴은 유용하지만, "왜 주문은 롤백됐는데 로그는 남았지?" 같은 질문이 생기므로 의도를 문서화해야 한다.

### 시나리오 4: 테스트가 롤백된 줄 알았는데 side effect가 남음

`@Transactional` 테스트는 DB 트랜잭션만 롤백한다.

- async 작업
- 파일 생성
- 외부 API 호출
- 다른 transaction manager 커밋

이것들은 그대로 남을 수 있다.

이 문맥은 [Spring Transactional Test Rollback Misconceptions](./spring-transactional-test-rollback-misconceptions.md)와 같이 봐야 한다.

### `readOnly` 조회 예시

```java
@Transactional(readOnly = true)
public OrderDto findOrder(Long orderId) {
    Order order = orderRepository.findById(orderId)
        .orElseThrow(() -> new IllegalArgumentException("not found"));
    return new OrderDto(order.getId(), order.getStatus());
}
```

조회 전용 메서드는 이렇게 분리하면 좋다.

- 변경 감지를 줄일 수 있다.
- 의도가 명확해진다.
- 실수로 쓰기 로직을 넣는 것을 경계하기 쉽다.

### `TransactionSynchronizationManager`로 현재 상태를 확인하는 예

```java
if (TransactionSynchronizationManager.isActualTransactionActive()) {
    log.info("tx active");
}
```

디버깅할 때는 "트랜잭션이 있어 보인다"가 아니라, 실제 active 상태와 propagation 결과를 로그로 확인하는 편이 좋다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 큰 서비스 메서드 하나에 트랜잭션 | 단순하다 | 경계가 넓어져 락과 롤백 범위가 커진다 | 아주 작은 변경 |
| 세부 작업마다 작은 트랜잭션 | 실패 범위가 작다 | 정합성 보장이 어려워질 수 있다 | 독립적인 작업 |
| `REQUIRES_NEW` 활용 | 실패 격리가 된다 | 흐름 추적이 어려워진다 | 감사 로그, 보조 기록 |
| 강한 격리수준 사용 | 동시성 버그를 줄인다 | 성능과 충돌 비용이 커진다 | 정말 중요한 정합성 |
| `readOnly` 적극 사용 | 조회 의도가 선명해진다 | 쓰기 로직 섞이면 오해를 부른다 | 조회 전용 API |

경계 설계의 핵심은 "모든 것을 하나로 묶는 것"이 아니라, **같이 실패해야 하는 것만 같은 트랜잭션에 넣는 것**이다.

---

## 꼬리질문

> Q: `@Transactional`이 같은 클래스 내부 호출에서 안 먹는 이유는?
> 의도: 프록시 기반 AOP를 이해하는지 확인
> 핵심: 프록시를 거치지 않으면 어드바이스가 실행되지 않는다.

> Q: 체크 예외가 왜 기본 롤백이 아닌가?
> 의도: Spring의 예외 철학과 롤백 규칙을 아는지 확인
> 핵심: 체크 예외는 호출자가 복구 가능하다고 보는 설계라 기본 커밋이다.

> Q: `readOnly = true`를 걸면 DB가 무조건 읽기 전용이 되나?
> 의도: 애플리케이션 힌트와 DB 보장을 구분하는지 확인
> 핵심: 보통 최적화 힌트이며, DB 권한/설정과는 별개다.

> Q: `REQUIRES_NEW`는 왜 위험할 수 있나?
> 의도: 트랜잭션 분리의 부작용을 아는지 확인
> 핵심: 흐름이 쪼개져 정합성과 디버깅 난도가 올라간다.

> Q: 트랜잭션 경계는 어떻게 잡아야 하나?
> 의도: 설계 판단 기준을 보는 질문
> 핵심: 같이 성공/실패해야 하는 작업 단위로 묶고, 외부 연동은 분리한다.

> Q: 여러 transaction manager가 있을 때 어떤 걸 쓰는지 어떻게 정하는가?
> 의도: qualifier 기반 경계 선택 확인
> 핵심: `@Transactional(transactionManager=...)`와 bean qualifier로 명시한다.

> Q: 테스트에서 `@Transactional`이 있다고 해서 왜 모든 side effect가 사라지지 않는가?
> 의도: 테스트 롤백 한계 이해 확인
> 핵심: DB 경계 밖의 작업은 롤백 대상이 아니다.

---

## 한 줄 정리

`@Transactional`은 "DB에 붙는 주석"이 아니라, 프록시가 메서드 경계를 가로채서 전파, 롤백, 읽기 전용, 격리수준을 적용하는 실행 정책이다.
