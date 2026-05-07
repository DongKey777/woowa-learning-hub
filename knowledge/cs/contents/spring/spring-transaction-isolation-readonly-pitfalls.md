---
schema_version: 3
title: Spring Transaction Isolation ReadOnly Pitfalls
concept_id: spring/transaction-isolation-readonly-pitfalls
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- transaction-isolation-readonly
- pitfalls
- transactional-readonly-pitfalls
- transaction-isolation
aliases:
- @Transactional readOnly pitfalls
- transaction isolation Spring
- read only transaction not enforcement
- flush mode readonly
- replica routing readonly
- isolation consistency cost
intents:
- deep_dive
- troubleshooting
- design
linked_paths:
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-transaction-debugging-playbook.md
- contents/spring/spring-persistence-context-flush-clear-detach-boundaries.md
- contents/spring/spring-routing-datasource-read-write-transaction-boundaries.md
- contents/spring/spring-open-session-in-view-tradeoffs.md
- contents/database/transaction-isolation-basics.md
symptoms:
- readOnly=true인데 쓰기 시도가 완전히 막히지 않거나 flush behavior만 달라진다.
- isolation level을 높였더니 latency, lock, throughput 비용이 커진다.
- readOnly transaction을 replica routing 신호로 쓰다가 read-after-write 문제가 생긴다.
expected_queries:
- @Transactional(readOnly=true)는 DB write를 항상 막아?
- Spring transaction isolation은 어떤 일관성과 비용 tradeoff야?
- readOnly와 replica routing을 연결할 때 어떤 pitfall이 있어?
- isolation level을 높이면 왜 lock이나 latency 비용이 커질 수 있어?
contextual_chunk_prefix: |
  이 문서는 @Transactional(readOnly=true)와 isolation을 편의 옵션이 아니라 consistency,
  flush behavior, DB enforcement, replica routing, lock/latency cost를 정하는 계약으로 설명한다.
---
# Spring Transaction Isolation / ReadOnly Pitfalls

> 한 줄 요약: `@Transactional(readOnly = true)`와 isolation은 편의 옵션이 아니라, 어떤 일관성과 어떤 비용을 감수할지 정하는 계약이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
> - [Spring Routing DataSource Read/Write Transaction Boundaries](./spring-routing-datasource-read-write-transaction-boundaries.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
> - [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)
> - [Spring Batch Chunk / Retry / Skip](./spring-batch-chunk-retry-skip.md)

retrieval-anchor-keywords: transactional isolation, readOnly, flush mode, dirty checking, read committed, repeatable read, serializable, phantom read, lost update, write skew

## 핵심 개념

`readOnly`와 isolation은 둘 다 트랜잭션에 붙지만 책임이 다르다.

- `readOnly = true`는 "이 메서드는 조회 중심이다"라는 힌트다
- `isolation`은 "동시성 충돌을 어느 수준까지 허용할 것인가"를 정한다

둘을 같이 쓰지 않으면 실무에서 다음 착각이 나온다.

- readOnly니까 절대 쓰기 안 되겠지
- repeatable read니까 모든 이상 현상이 사라지겠지
- serializable은 정답이니까 무조건 안전하겠지

실제론 그렇지 않다.

`readOnly`는 강한 보안 장치가 아니고, isolation은 데이터베이스와 드라이버 구현에 따라 체감이 달라진다.

## 깊이 들어가기

### 1. `readOnly`는 금지령이 아니다

`readOnly = true`는 보통 다음을 돕는다.

- 불필요한 dirty checking 감소
- flush 전략 조정
- 조회 메서드 의도 표현

하지만 이것만으로 DB 쓰기를 물리적으로 막는다고 믿으면 안 된다.

```java
@Transactional(readOnly = true)
public UserDto find(Long id) {
    User user = userRepository.findById(id).orElseThrow();
    user.changeName("oops");
    return UserDto.from(user);
}
```

이 코드는 "readOnly니까 안전하겠지"라는 착각을 깨기 좋다.

JPA 구현체와 DB 조합에 따라 실제 반영 여부는 다를 수 있고, 무엇보다 코드 의도가 이미 틀어져 있다.

### 2. dirty checking과 flush timing을 같이 봐야 한다

readOnly는 영속성 컨텍스트의 변경 감지와 flush 타이밍에 영향을 줄 수 있다.

문제는 개발자가 "조회 메서드"라고 믿고 있어도, 내부에서 다른 엔티티가 변경되면 flush가 섞일 수 있다는 점이다.

특히 다음이 위험하다.

- 조회 메서드가 다른 서비스의 save를 호출한다
- 엔티티를 반환한 뒤 OSIV로 view 단계에서 변경이 보인다
- 이벤트 리스너가 같은 컨텍스트를 건드린다

이 문맥은 [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)와 같이 봐야 한다.

### 3. isolation은 "무슨 이상 현상을 안 볼 것인가"다

대표적인 격리수준 감각은 다음과 같다.

| 수준 | 핵심 의미 | 남는 위험 |
|---|---|---|
| `READ_COMMITTED` | 커밋된 값만 읽는다 | non-repeatable read, phantom 가능 |
| `REPEATABLE_READ` | 같은 트랜잭션 내 재조회 일관성이 높다 | write skew, DB 구현 의존 |
| `SERIALIZABLE` | 가장 강한 순차성에 가깝다 | 성능 저하, 충돌 증가 |

중요한 점은 isolation이 "정확히 같은 SQL 표준 효과"를 언제나 보장하지 않는다는 것이다.

예를 들어 MySQL InnoDB는 락 구현과 MVCC가 결합되어 표준 설명만으로는 감이 안 오는 상황이 많다.

### 4. isolation을 높이면 안전해질까

항상 그렇지 않다.

- 읽기 충돌은 줄어들 수 있다
- 하지만 잠금이 늘어날 수 있다
- 경합이 커지면 throughput이 떨어진다
- 앱 레벨의 재시도와 충돌 처리도 필요할 수 있다

즉 isolation은 "더 세게"의 문제가 아니라 **어떤 이상 현상을 막고, 어떤 성능을 포기할지**의 문제다.

## 실전 시나리오

### 시나리오 1: readOnly 조회인데 값이 바뀌어 버린다

```java
@Transactional(readOnly = true)
public OrderSummary getSummary(Long id) {
    Order order = orderRepository.findById(id).orElseThrow();
    order.markViewed(); // 의도치 않은 변경
    return OrderSummary.from(order);
}
```

이 코드는 조회 메서드가 사실상 쓰기 메서드가 된 사례다.

readOnly가 있어도 코드가 잘못되면 의도는 지켜지지 않는다.

### 시나리오 2: 두 사용자가 동시에 같은 재고를 줄인다

한 사용자는 조회한 뒤 감소시키고, 다른 사용자도 동시에 같은 값을 갱신하면 lost update가 생길 수 있다.

이 경우 필요한 것은 단순한 readOnly가 아니라, isolation 수준, 낙관적 락, 비관적 락 중 무엇을 쓸지의 판단이다.

### 시나리오 3: phantom read 때문에 집계 결과가 흔들린다

같은 조건으로 두 번 조회했는데 중간에 insert가 끼어들면 count가 달라질 수 있다.

이런 집계성 메서드는 readOnly만으로는 부족하고, 격리수준과 쿼리 패턴을 같이 봐야 한다.

### 시나리오 4: serializable로 올렸는데 더 느려진다

가장 안전한 수준을 고르면 무조건 맞을 것 같지만, 실제로는 lock contention과 throughput 저하가 더 크게 드러날 수 있다.

`serializable`은 "기본값으로 쓰기 좋은 수준"이 아니라, 정말 필요한 영역에서만 골라야 하는 선택지다.

## 코드로 보기

### 읽기 전용 조회 메서드

```java
@Transactional(readOnly = true, isolation = Isolation.READ_COMMITTED)
public AccountDto findAccount(Long id) {
    Account account = accountRepository.findById(id).orElseThrow();
    return AccountDto.from(account);
}
```

### 동시성 충돌을 의식한 갱신

```java
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void transfer(Long fromId, Long toId, BigDecimal amount) {
    Account from = accountRepository.findById(fromId).orElseThrow();
    Account to = accountRepository.findById(toId).orElseThrow();

    from.withdraw(amount);
    to.deposit(amount);
}
```

이 코드 자체가 안전하다는 뜻은 아니다.
실제로는 계좌별 락, 버전 컬럼, 유니크 제약, 재시도 전략까지 같이 봐야 한다.

### 읽기 모델과 쓰기 모델 분리

```java
@Service
public class OrderQueryService {

    @Transactional(readOnly = true)
    public List<OrderRow> findOrders() {
        return orderRepository.findRows();
    }
}
```

```java
@Service
public class OrderCommandService {

    @Transactional
    public void placeOrder(PlaceOrderCommand command) {
        orderRepository.save(new Order(command));
    }
}
```

조회와 변경을 분리하면 readOnly와 isolation을 더 명확하게 적용할 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `readOnly = true` | 의도가 분명하다 | 쓰기를 물리적으로 막지 못한다 | 조회 전용 메서드 |
| `READ_COMMITTED` | 일반적으로 빠르고 무난하다 | 반복 읽기 일관성이 약하다 | 대부분의 조회/갱신 |
| `REPEATABLE_READ` | 같은 트랜잭션 내 재조회가 안정적이다 | DB 구현 차이와 락 비용이 있다 | 정산/계산성 로직 |
| `SERIALIZABLE` | 가장 강한 보호를 준다 | 성능 비용이 크다 | 정말 깨지면 안 되는 좁은 구간 |

핵심은 더 강한 설정이 항상 더 좋은 것이 아니라, **정확성이 필요한 만큼만 비용을 지불하는 것**이다.

## 꼬리질문

> Q: `readOnly = true`가 실제로 보장하는 것은 무엇인가?
> 의도: 힌트와 보장 구분 확인
> 핵심: 주로 flush/dirty checking 최적화와 의도 표현이다.

> Q: isolation을 높이면 왜 무조건 안전하지 않은가?
> 의도: 성능과 경합 비용 이해 확인
> 핵심: 락과 충돌이 늘어 throughput이 떨어질 수 있다.

> Q: repeatable read에서도 이상 현상이 남을 수 있는가?
> 의도: DB 구현과 write skew 이해 확인
> 핵심: DB에 따라 write skew 같은 문제가 남을 수 있다.

> Q: 조회/명령을 분리하면 어떤 점이 좋아지는가?
> 의도: 애플리케이션 설계와 트랜잭션 경계 이해 확인
> 핵심: readOnly와 isolation을 더 명확히 설계할 수 있다.

## 한 줄 정리

`readOnly`는 조회 의도 표현이고, isolation은 동시성 비용을 고르는 계약이므로 둘 다 "안전 장치"로 과신하면 안 된다.
