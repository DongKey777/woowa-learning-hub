# Spring Persistence Context Flush / Clear / Detach Boundaries

> 한 줄 요약: 영속성 컨텍스트는 단순 캐시가 아니라 변경 감지와 쓰기 지연을 가진 작업 단위이므로, `flush`, `clear`, `detach`의 경계를 모르면 메모리 증가, stale state, 숨은 SQL 문제를 피하기 어렵다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Transaction Isolation / ReadOnly Pitfalls](./spring-transaction-isolation-readonly-pitfalls.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md)
> - [Spring Routing DataSource Read/Write Transaction Boundaries](./spring-routing-datasource-read-write-transaction-boundaries.md)

retrieval-anchor-keywords: persistence context, EntityManager, flush, clear, detach, dirty checking, first level cache, bulk update stale state, batch flush clear, managed entity, detached entity, save persist merge

## 핵심 개념

JPA를 Spring에서 쓸 때 가장 많이 오해하는 것 중 하나는 영속성 컨텍스트를 "그냥 1차 캐시" 정도로만 보는 것이다.

실제로는 더 많은 책임이 있다.

- 같은 식별자의 엔티티 identity 보장
- dirty checking
- 쓰기 지연(write-behind)
- flush 시점 제어

여기서 중요한 동작 차이는 다음이다.

- `flush`: 현재까지 쌓인 변경을 DB SQL로 밀어낸다
- `clear`: 관리 중인 엔티티를 전부 detach한다
- `detach`: 특정 엔티티 하나만 관리 대상에서 뺀다

즉 질문은 "언제 저장되나?"가 아니라, **어떤 시점까지 엔티티를 managed state로 둘 것인가**다.

이 경계를 모르고 개발하면 다음이 흔하다.

- 배치 처리 중 메모리가 끝없이 증가한다
- bulk update 후 조회 결과가 이상하게 stale해 보인다
- 테스트는 통과했는데 실제 커밋 시점에 제약 조건 예외가 난다
- 조회 메서드라고 생각했는데 flush가 섞여 SQL이 튀어나간다

## 깊이 들어가기

### 1. 영속성 컨텍스트는 identity map + unit of work다

같은 트랜잭션 안에서 같은 ID의 엔티티를 두 번 조회하면 보통 같은 Java 객체처럼 다뤄진다.

이건 단순 최적화가 아니라, 영속성 컨텍스트가 **현재 작업 단위의 엔티티 상태를 대표**하기 때문이다.

그래서 managed 엔티티를 바꾸면 즉시 `save()`를 안 불러도 flush 시점에 SQL이 나갈 수 있다.

이 특성이 편리한 동시에 위험하다.

- 수정 의도가 없는 코드도 상태를 바꿔 버릴 수 있다
- 긴 트랜잭션에서는 엔티티가 계속 쌓인다
- 현재 메모리 상태와 실제 DB 상태를 혼동하기 쉽다

### 2. `flush`는 커밋이 아니다

가장 흔한 착각은 `flush()`를 호출하면 트랜잭션이 끝난다고 생각하는 것이다.

그렇지 않다.

`flush`는 현재 변경 사항을 SQL로 보낼 뿐이고, 트랜잭션은 여전히 롤백될 수 있다.

이 차이가 중요한 이유는 다음과 같다.

- 제약 조건 오류를 커밋 전에 일찍 드러낼 수 있다
- 다른 SQL 실행 전에 DB 상태를 맞춰야 할 수 있다
- 테스트에서 "진짜 DB 제약"을 확인하려면 flush가 필요할 수 있다

즉 `flush`는 확정이 아니라 **동기화 시점 조정**이다.

### 3. `clear`와 `detach`는 managed state를 끊는다

`clear()`는 현재 영속성 컨텍스트가 관리하던 엔티티를 전부 떼어 낸다.

`detach(entity)`는 특정 엔티티 하나만 떼어 낸다.

이게 필요한 대표 상황은 아래와 같다.

- 대량 배치 처리 중 메모리 사용량 제한
- bulk update 이후 stale entity 제거
- 의도치 않은 dirty checking 차단
- lazy loading이 더 이상 일어나면 안 되는 경계 명시

하지만 detach된 엔티티는 더 이상 자동 추적되지 않는다.

- 수정해도 SQL이 안 나간다
- lazy association 접근이 실패할 수 있다
- merge/reload 전략이 필요할 수 있다

즉 clear/detach는 "문제를 없애는 마법"이 아니라, **관리 책임을 개발자에게 돌리는 선택**이다.

### 4. bulk update와 native query는 영속성 컨텍스트를 우회할 수 있다

JPQL bulk update나 native query는 현재 managed 엔티티 상태와 엇갈리기 쉽다.

예를 들어 DB는 이미 바뀌었는데, 영속성 컨텍스트 안의 엔티티는 예전 값을 들고 있을 수 있다.

이때 자주 보이는 증상은 다음이다.

- update count는 맞는데 곧바로 읽으면 이전 값처럼 보인다
- 테스트에서는 같은 엔티티 인스턴스를 재사용해 stale state를 못 알아챈다

이런 작업 뒤에는 보통 다음 중 하나를 고려한다.

- `clear()`
- 필요한 엔티티만 `refresh()` 또는 재조회
- Spring Data JPA의 `@Modifying(clearAutomatically = true, flushAutomatically = true)` 활용

핵심은 bulk/native 경로를 "빠른 SQL"이 아니라, **영속성 컨텍스트 바깥 경로**로 인식하는 것이다.

### 5. 긴 트랜잭션과 배치는 flush/clear 전략이 필요하다

대량 insert/update에서 managed 엔티티를 계속 붙잡고 있으면 다음 문제가 생긴다.

- 메모리 증가
- dirty checking 비용 증가
- flush 시점 지연으로 SQL 폭탄

그래서 배치성 작업에서는 일정 단위마다 flush/clear하는 패턴이 자주 쓰인다.

```java
for (int i = 0; i < orders.size(); i++) {
    entityManager.persist(orders.get(i));

    if (i % 1000 == 0) {
        entityManager.flush();
        entityManager.clear();
    }
}
```

이 패턴은 단순 성능 팁이 아니라, **영속성 컨텍스트 크기 관리 전략**이다.

### 6. 테스트와 운영은 flush 감각이 달라 보일 수 있다

테스트에서 같은 트랜잭션 안에서 엔티티를 다시 읽으면 이미 메모리에 있는 managed state가 반환될 수 있다.

그래서 다음 문제가 생긴다.

- DB에 실제 SQL이 안 나갔는데도 값이 바뀐 것처럼 보임
- 제약 조건 위반이 commit 직전까지 안 드러남
- bulk update 후 stale 상태를 테스트가 놓침

운영 문제를 테스트에서 더 빨리 드러내려면 필요한 순간에 flush/clear를 의도적으로 넣어 보는 것이 도움이 된다.

## 실전 시나리오

### 시나리오 1: 배치 import가 갈수록 느려지고 메모리가 오른다

영속성 컨텍스트에 수만 개 엔티티가 계속 남아 있을 가능성이 높다.

이 경우는 단순 튜닝보다 flush/clear 주기를 먼저 점검해야 한다.

### 시나리오 2: bulk update를 했는데 곧바로 조회한 결과가 옛값 같다

DB가 안 바뀐 것이 아니라, 현재 persistence context가 stale 상태일 수 있다.

이때는 재조회 전에 clear나 refresh가 필요할 수 있다.

### 시나리오 3: 조회 메서드인데 update SQL이 튀어나온다

이미 managed 상태의 엔티티를 다른 코드가 바꿨고, flush 시점에 그 변경이 반영됐을 수 있다.

이건 [Spring Transaction Isolation / ReadOnly Pitfalls](./spring-transaction-isolation-readonly-pitfalls.md)와 직접 연결된다.

### 시나리오 4: 테스트는 통과하는데 운영에서만 제약 조건 예외가 난다

테스트에서 commit 직전 flush가 늦게 일어나 숨었을 수 있다.

중요한 경로라면 테스트 중간에 flush를 넣어 실제 SQL 시점을 앞당겨 보는 게 좋다.

## 코드로 보기

### batch write에서 주기적 flush / clear

```java
@Transactional
public void importOrders(List<Order> orders) {
    for (int i = 0; i < orders.size(); i++) {
        entityManager.persist(orders.get(i));

        if ((i + 1) % 500 == 0) {
            entityManager.flush();
            entityManager.clear();
        }
    }
}
```

### bulk update 뒤 stale state 정리

```java
@Transactional
public void expireCoupons(LocalDate today) {
    couponRepository.bulkExpire(today);
    entityManager.clear();
}
```

### 특정 엔티티만 detach

```java
Order order = entityManager.find(Order.class, orderId);
entityManager.detach(order);
```

### 테스트에서 제약 조건을 일찍 드러내기

```java
orderRepository.save(order);
entityManager.flush();
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 긴 managed 상태 유지 | 코드가 단순하다 | 메모리 증가, stale state, 숨은 flush 위험 | 작은 유스케이스 |
| 주기적 flush / clear | 메모리와 dirty checking 비용을 줄인다 | 재조회/merge 전략이 필요하다 | 배치, 대량 처리 |
| detach 활용 | 의도치 않은 변경 추적을 끊는다 | lazy loading과 자동 저장이 사라진다 | 읽기 전용 전달 객체화, 경계 분리 |
| bulk update 사용 | 빠르고 SQL 효율이 좋다 | persistence context와 쉽게 어긋난다 | 대량 상태 전환 |

핵심은 영속성 컨텍스트를 "편한 자동 저장기"가 아니라, **크기와 생명주기를 통제해야 하는 상태 기계**로 보는 것이다.

## 꼬리질문

> Q: `flush()`와 commit의 차이는 무엇인가?
> 의도: 동기화와 확정 구분 확인
> 핵심: flush는 SQL 동기화이고, commit은 트랜잭션 확정이다.

> Q: bulk update 뒤에 stale state가 생기는 이유는 무엇인가?
> 의도: 영속성 컨텍스트 우회 이해 확인
> 핵심: bulk SQL이 현재 managed 엔티티 상태를 자동으로 갱신하지 않기 때문이다.

> Q: 배치 처리에서 `clear()`가 왜 중요한가?
> 의도: persistence context 크기 관리 이해 확인
> 핵심: 쌓인 managed 엔티티를 떼어 내 메모리와 dirty checking 비용을 줄인다.

> Q: 테스트에서 `flush()`를 명시적으로 넣는 이유는 무엇인가?
> 의도: 숨은 SQL 시점 인식 확인
> 핵심: 제약 조건이나 실제 DB 동작을 더 이른 시점에 드러내기 위해서다.

## 한 줄 정리

영속성 컨텍스트의 진짜 경계는 트랜잭션 시작/종료만이 아니라, 언제 flush하고 언제 clear/detach할지로 결정된다.
