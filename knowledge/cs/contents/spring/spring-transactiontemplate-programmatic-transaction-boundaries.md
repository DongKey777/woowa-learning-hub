# Spring `TransactionTemplate` and Programmatic Transaction Boundaries

> 한 줄 요약: `TransactionTemplate`은 선언형 트랜잭션의 대체재가 아니라, 반복 처리·부분 커밋·재시도·비동기 경계처럼 메서드 단위 `@Transactional`만으로는 표현이 어색한 상황에서 명시적으로 경계를 자르는 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Template 클래스 입문: `JdbcTemplate`, `RestTemplate`, `TransactionTemplate` 큰 그림](./spring-template-classes-beginner-primer.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
> - [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
> - [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
> - [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

retrieval-anchor-keywords: TransactionTemplate, programmatic transaction, PlatformTransactionManager, transaction callback, partial commit loop, imperative transaction boundary, transaction status setRollbackOnly, requires new alternative, transaction per item, 처음 배우는데 TransactionTemplate 뭐예요, TransactionTemplate 언제 쓰는지, 코드 블록 트랜잭션 입문, 템플릿 클래스 예시, 트랜잭션 경계 직접 자르기, @Transactional 말고 TransactionTemplate

## 이 문서 전에 큰 그림이 필요하면

- "`TransactionTemplate`가 왜 template 계열인지"부터 짧게 잡고 싶다면 [Spring Template 클래스 입문: `JdbcTemplate`, `RestTemplate`, `TransactionTemplate` 큰 그림](./spring-template-classes-beginner-primer.md)을 먼저 본다.

## 핵심 개념

Spring에서 트랜잭션은 보통 `@Transactional`로 시작한다.

하지만 모든 경계가 메서드 단위로 깔끔하게 떨어지는 것은 아니다.

예를 들면 이런 경우다.

- 루프 안에서 아이템별로 커밋하고 싶다
- 재시도마다 새로운 트랜잭션을 열고 싶다
- 비동기 worker 안에서 명시적으로 DB 경계를 자르고 싶다
- 외부 흐름은 비트랜잭션으로 두고, 일부 구간만 짧게 트랜잭션을 열고 싶다

이럴 때 `TransactionTemplate`이 유용하다.

핵심은 `TransactionTemplate`을 "옛날 방식"으로 보지 않는 것이다.

이 도구의 가치는 선언형 트랜잭션을 부정하는 데 있지 않고, **트랜잭션 경계를 코드 흐름 속에서 더 세밀하게 자를 수 있다는 점**에 있다.

## 깊이 들어가기

### 1. `@Transactional`은 메서드 경계에 강하고, `TransactionTemplate`은 코드 블록 경계에 강하다

`@Transactional`의 장점:

- 선언이 간단하다
- 서비스 계층 경계와 잘 맞는다
- 프록시 기반으로 일관되게 적용된다

`TransactionTemplate`의 장점:

- 메서드 전체가 아니라 필요한 블록만 감싼다
- 루프 안에서 아이템별 트랜잭션을 만들기 쉽다
- 반환값과 예외 흐름을 코드에서 더 직접 다룬다

즉 둘은 경쟁 관계라기보다, **잘 맞는 경계가 다른 도구**다.

### 2. 반복 처리와 부분 커밋에 특히 강하다

`@Transactional` 메서드 안에서 1,000건을 한 번에 처리하면, 길고 무거운 트랜잭션이 되기 쉽다.

반면 `TransactionTemplate`으로 루프 안 경계를 자르면 item-per-transaction 패턴이 자연스럽다.

```java
for (OrderCommand command : commands) {
    transactionTemplate.executeWithoutResult(status -> orderService.processOne(command));
}
```

이 방식의 장점:

- 일부 아이템 실패가 전체를 반드시 날리지 않아도 된다
- 락 점유와 메모리 사용을 줄이기 쉽다
- 실패 재처리를 아이템 단위로 설계하기 쉽다

물론 정합성을 함께 가져가야 하는 유스케이스에는 오히려 해롭다.

### 3. `setRollbackOnly()`를 명시적으로 다룰 수 있다

선언형 트랜잭션에서는 예외로 롤백을 유도하는 경우가 많다.

`TransactionTemplate`에서는 `TransactionStatus`를 받아 직접 롤백 마킹을 할 수 있다.

```java
transactionTemplate.execute(status -> {
    if (!policy.allows(command)) {
        status.setRollbackOnly();
        return false;
    }
    repository.save(entity);
    return true;
});
```

이건 "예외를 안 던지고도 롤백"이 가능하다는 뜻이지만, 남용하면 실패가 조용해질 수 있다.

즉 명시성이 높아지는 만큼, **실패 관측도 함께 설계해야 한다**.

### 4. 재시도와 결합할 때 경계가 더 선명해진다

재시도는 보통 "실패한 작업을 다시 시도"한다.

이때 중요한 건 같은 트랜잭션을 다시 쓰는 게 아니라, **시도마다 새 트랜잭션을 열어야 한다**는 점이다.

`TransactionTemplate`은 이 의도를 코드로 드러내기 좋다.

```java
for (int attempt = 0; attempt < 3; attempt++) {
    try {
        return transactionTemplate.execute(status -> paymentService.charge(command));
    } catch (TransientDataAccessException ex) {
        // retry
    }
}
```

이 문맥은 retry, outbox relay, 배치성 워커와 잘 맞는다.

### 5. 비동기/스케줄러/워커에서는 오히려 더 자연스러울 수 있다

`@Async`나 scheduler 안에서 서비스 메서드에 `@Transactional`을 붙이는 것도 가능하다.

하지만 다음이 헷갈릴 수 있다.

- 프록시 경계를 제대로 탔는가
- worker thread에서 어떤 tx manager를 쓰는가
- 어느 블록까지 트랜잭션이어야 하는가

이런 경우 `TransactionTemplate`은 worker 코드 안에서 직접 경계를 잘라 더 명시적으로 만들 수 있다.

즉 프록시 기반 선언형 방식이 어색한 흐름에서는, **programmatic boundary가 오히려 더 읽기 쉬울 수 있다**.

### 6. 하지만 서비스 계층 기본값으로 밀어붙이면 오히려 시끄러워진다

모든 서비스에서 `TransactionTemplate`를 기본으로 쓰기 시작하면 다음 문제가 생긴다.

- 중복 보일러플레이트 증가
- 트랜잭션 정책이 여기저기 흩어진다
- 선언형 일관성이 깨진다

그래서 보통 권장 기준은 이렇다.

- 기본 경계: `@Transactional`
- 예외적인 세밀한 경계 제어: `TransactionTemplate`

핵심은 더 강력한 도구라기보다, **예외적인 흐름을 명시적으로 표현하는 도구**라는 점이다.

## 실전 시나리오

### 시나리오 1: 배치에서 한 건 실패해도 나머지는 계속 처리하고 싶다

메서드 전체를 `@Transactional`로 묶으면 전체 롤백이 되기 쉽다.

item-per-transaction 구조가 맞다면 `TransactionTemplate`이 더 자연스럽다.

### 시나리오 2: 재시도마다 새 트랜잭션을 열어야 한다

특히 DB transient error 재시도에서는 시도마다 깨끗한 트랜잭션 경계가 필요하다.

이 경우 `TransactionTemplate`은 retry loop와 궁합이 좋다.

### 시나리오 3: 워커 스레드 안에서 아주 짧게만 DB를 잡고 싶다

비동기 작업 전체를 트랜잭션으로 묶기보다, DB 접근 블록만 트랜잭션으로 감싸고 나머지 네트워크/CPU 작업은 밖으로 빼기 쉽다.

### 시나리오 4: 서비스 계층이 전부 `TransactionTemplate` 투성이가 됐다

이건 보통 경계를 과도하게 수동화한 신호다.

기본은 선언형으로 두고, 정말 필요한 곳만 programmatic boundary로 올리는 편이 유지보수에 낫다.

## 코드로 보기

### 반환값 있는 실행

```java
String result = transactionTemplate.execute(status -> {
    orderRepository.save(order);
    return "ok";
});
```

### 반환값 없는 실행

```java
transactionTemplate.executeWithoutResult(status -> {
    auditRepository.save(new AuditLog("done"));
});
```

### 루프 안 아이템별 트랜잭션

```java
for (SettlementLine line : lines) {
    transactionTemplate.executeWithoutResult(status -> settlementService.process(line));
}
```

### 조건부 롤백

```java
Boolean saved = transactionTemplate.execute(status -> {
    if (!validator.isValid(command)) {
        status.setRollbackOnly();
        return false;
    }
    repository.save(entity);
    return true;
});
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@Transactional` | 선언이 단순하고 일관되다 | 메서드보다 세밀한 경계 제어는 어색하다 | 대부분의 서비스 계층 |
| `TransactionTemplate` | 블록 단위 경계 제어가 가능하다 | 코드가 더 장황해진다 | 루프, 재시도, 워커, 부분 커밋 |
| `REQUIRES_NEW` 남발 | 선언형으로 분리 커밋을 표현한다 | 커넥션과 의미가 복잡해진다 | 제한적 보조 기록 |
| 비트랜잭션 처리 | 단순할 수 있다 | 일관성과 실패 복구가 약하다 | DB 경계가 불필요할 때 |

핵심은 `TransactionTemplate`을 선언형 트랜잭션의 경쟁자로 보지 않고, **메서드 경계보다 세밀한 트랜잭션이 필요한 예외적 흐름의 도구**로 보는 것이다.

## 꼬리질문

> Q: `@Transactional`보다 `TransactionTemplate`가 더 나은 상황은 언제인가?
> 의도: 경계 표현력 차이 이해 확인
> 핵심: 루프, 재시도, 비동기 worker처럼 메서드보다 작은 블록 단위 경계가 필요할 때다.

> Q: `TransactionTemplate`에서 `setRollbackOnly()`는 무엇을 해결하는가?
> 의도: 예외 없는 롤백 표현 이해 확인
> 핵심: 조건부 실패를 예외 없이도 트랜잭션에 명시할 수 있다.

> Q: 모든 서비스에 `TransactionTemplate`를 쓰면 왜 안 좋은가?
> 의도: 기본값과 예외값 구분 확인
> 핵심: 정책이 흩어지고 선언형 일관성이 깨지기 때문이다.

> Q: retry와 `TransactionTemplate`가 잘 맞는 이유는 무엇인가?
> 의도: 시도별 경계 이해 확인
> 핵심: 재시도마다 새 트랜잭션을 명시적으로 열기 쉽기 때문이다.

## 한 줄 정리

`TransactionTemplate`은 트랜잭션을 더 잘게 자르고 싶을 때 쓰는 도구이지, 서비스 계층 기본 패턴을 전부 대체하는 도구는 아니다.
