# N+1 Query Detection and Solutions

> 한 줄 요약: N+1은 "ORM이 느리다"는 현상이 아니라, 지연 로딩이 "필요할 때 한 건씩" 가져오는 기본 계약 위에서 컬렉션을 순회할 때 필연적으로 터지는 구조적 실패이고, 탐지(로그/테스트)와 처방(fetch join / `@EntityGraph` / batch size)을 나눠 이해해야 자기 코드에서 발견할 수 있다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Spring Data JPA `save`, `persist`, `merge` State Transitions](../spring/spring-data-jpa-save-persist-merge-state-transitions.md)
> - [JPA Dirty Checking, @Version, Cascade Trade-offs](../spring/jpa-dirty-checking-version-strategy.md)
> - [Covering Index Composite Ordering](./covering-index-composite-ordering.md)
> - [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)

### Retrieval Anchors

- `N+1 query`
- `N plus one problem`
- `lazy loading N+1`
- `fetch join`
- `JPQL fetch join`
- `@EntityGraph`
- `@BatchSize`
- `hibernate.default_batch_fetch_size`
- `fetch plan`
- `query count test`
- `SQLStatementCountValidator`
- `N+1 탐지`

## 핵심 개념

N+1은 "쿼리가 1 + N번 발생한다"는 표면적 정의 이상의 의미가 있다.

핵심은 세 가지다.

- **지연 로딩(Lazy)** 은 "필요할 때 가져온다"는 계약이다. 즉 개별 엔티티 1건씩 SELECT하겠다는 뜻이다.
- **컬렉션 순회**가 일어나는 순간, 각 요소마다 지연 연관을 건드리면 그 수만큼 쿼리가 터진다.
- 즉 N+1은 lazy의 버그가 아니라 **lazy가 의도된 대로 돈 결과**다. 원인은 "연관 로딩 계획(fetch plan)을 쿼리 시점이 아니라 도메인 코드 시점에 맡겼다"는 것.

"ORM이 알아서 해주겠지"로 접근하면 반드시 만난다. N+1은 **설계 시점에 fetch plan을 명시**해야 풀린다.

## 깊이 들어가기

### 1. N+1이 실제로 어떻게 생기는가

```java
List<Order> orders = orderRepository.findAll();  // 쿼리 1: SELECT * FROM orders
for (Order o : orders) {
    System.out.println(o.getCustomer().getName());  // 쿼리 N: SELECT * FROM customers WHERE id=?
}
```

`Order.customer`가 `@ManyToOne(fetch = LAZY)`라면, `getCustomer().getName()` 호출마다 프록시 초기화가 일어나고 customer 1건씩 SELECT가 나간다. N=100이면 101번 쿼리가 DB로 간다.

여기서 중요한 건, `findAll()`이 끝난 시점에는 쿼리가 1번만 찍혔기 때문에 **쿼리 로그만 보면 정상처럼 보인다**는 것이다. 문제는 **렌더링/직렬화 시점**에 터진다.

### 2. 탐지: 쿼리 개수를 테스트로 박제한다

N+1이 가장 무서운 건 **조용히 번식한다**는 것이다. 개발 때는 데이터 10건이라 느낌이 없고, 프로덕션에서 10,000건일 때 p99 latency로 터진다. 코드 리뷰로 잡기 어렵다.

해결은 단순하다: **쿼리 개수를 테스트로 고정한다.**

- **`datasource-proxy`** / **`p6spy`**: 런타임에 DataSource 래퍼로 SQL 로그 + 카운트를 수집한다. 슬로우 쿼리, 비정상적 양을 추적하기 좋다
- **`SQLStatementCountValidator` (Hibernate Types)**: 테스트에서 "이 메서드는 정확히 2번의 SELECT만 나와야 한다"고 assert한다. JPA/Hibernate 전용
- **`hibernate.generate_statistics=true`**: `Statistics#getPrepareStatementCount()`로 런타임 카운트 조회

로컬 개발에서는 `show-sql`과 `hibernate.format_sql`을 켜고 **같은 페이지의 같은 요청**에서 쿼리가 몇 번 나가는지 눈으로 확인하는 것도 첫 단추로 유효하다.

### 3. 처방: fetch join / `@EntityGraph` / batch size의 경계

세 가지 해법이 있고, 각자 적용 조건이 다르다.

**Fetch join (JPQL)**

```java
@Query("select o from Order o join fetch o.customer")
List<Order> findAllWithCustomer();
```

- 장점: 한 번의 쿼리로 연관까지 가져온다. fetch plan을 쿼리 수준에서 고정한다
- 한계: **컬렉션 fetch join은 하나만 가능**하다. 두 개 이상 걸면 Cartesian product. Pagination(`LIMIT`)과 섞으면 Hibernate가 메모리에서 페이징해서 경고를 찍는다

**`@EntityGraph`**

```java
@EntityGraph(attributePaths = {"customer", "lines"})
List<Order> findAll();
```

- 장점: Repository 시그니처에 선언적으로 fetch plan을 붙인다. JPQL을 쓸 필요가 없다
- 한계: fetch join의 "컬렉션 하나" 제한은 동일. 경로가 복잡해지면 가독성이 깎인다

**`@BatchSize` / `hibernate.default_batch_fetch_size`**

```java
@BatchSize(size = 100)
@OneToMany(mappedBy = "order", fetch = LAZY)
List<OrderLine> lines;
```

- 장점: **lazy를 유지하면서** N번 쿼리를 `WHERE parent_id IN (?, ?, ?, ...)` 한 덩어리로 묶는다. 즉 N+1을 **1 + ceil(N/size)** 로 줄인다
- 한계: 여전히 2번 이상의 쿼리. 하지만 컬렉션 여러 개를 다룰 때 fetch join보다 안전하다

### 4. 선택 기준 — "몇 개의 연관을 어떻게 쓸 것인가"

- 연관이 **단일 `@ManyToOne` 하나**: fetch join 또는 `@EntityGraph` 둘 다 OK
- 연관이 **단일 `@OneToMany` 하나 + pagination 없음**: fetch join OK
- 연관이 **`@OneToMany` + pagination**: fetch join 금지. `@BatchSize`로 풀어야 한다
- 연관이 **여러 `@OneToMany`**: 반드시 `@BatchSize` (fetch join 하나 + batch로 나머지)

## 실전 시나리오

### 시나리오 1: 리스트 API가 갑자기 느려졌다

1주일 전까진 빠르던 주문 리스트 API가 최근 p99가 5초로 튀었다. 쿼리 로그를 보면 `SELECT customer WHERE id=?`가 페이지당 20번씩 찍힌다.

진단: 최근 PR에서 `Order.customer`에 `fetch = LAZY`를 추가했거나 (이전엔 EAGER였다), 리스트 DTO 변환 로직에 `order.getCustomer().getGrade()` 같은 호출이 추가되었다.

처방: 리스트 조회 메서드에 `@EntityGraph(attributePaths = {"customer"})`를 붙이고, 테스트에 `SQLStatementCountValidator.assertSelectCount(1)`을 추가한다.

### 시나리오 2: fetch join을 했는데 페이징이 이상해진다

`fetch join` + `LIMIT 20`을 썼는데 Hibernate가 `HHH000104: firstResult/maxResults specified with collection fetch; applying in memory!` 경고를 찍고, 실제로 모든 행을 가져와 메모리에서 자른다.

원인: 컬렉션 fetch join은 row duplication을 일으키므로 DB-level `LIMIT`이 의미 없다. Hibernate가 "정확성" 쪽을 택해 메모리 페이징한다.

처방: 두 단계로 쪼갠다.
1. 페이지에 들어갈 **부모 ID**만 정렬+LIMIT로 가져온다 (쿼리 1)
2. 그 ID 목록으로 `where id in (?)` + fetch join (쿼리 2)

또는 `@BatchSize`로 lazy를 유지하면서 2+1 쿼리 패턴을 받아들인다.

### 시나리오 3: "쿼리 수는 줄었는데 더 느려졌다"

fetch join을 여러 컬렉션에 걸면 Cartesian product가 생겨 중간 결과 행 수가 폭발한다. 쿼리 1번이지만 네트워크로 10만 행이 내려온다.

처방: fetch join은 컬렉션 하나만. 나머지는 `@BatchSize` 또는 별도 쿼리로 나눈다.

## 코드로 보기

```java
// 쿼리 개수를 테스트로 고정
@SpringBootTest
@Transactional
class OrderQueryTest {

    @Autowired OrderRepository orders;
    @Autowired EntityManager em;

    @BeforeEach
    void seed() { /* 주문 10건 + 각 고객/라인 */ }

    @Test
    void findAll_executes_a_single_select() {
        em.flush(); em.clear();  // 1차 캐시 비움
        SQLStatementCountValidator.reset();

        List<Order> loaded = orders.findAllWithCustomer();  // @EntityGraph 적용
        loaded.forEach(o -> o.getCustomer().getName());

        SQLStatementCountValidator.assertSelectCount(1);
    }
}
```

중요한 건 `em.clear()`로 1차 캐시를 비우는 것이다. 같은 트랜잭션 안에서 이미 로드된 엔티티는 다시 SELECT되지 않기 때문에, 캐시를 비우지 않으면 N+1이 있는데도 테스트가 통과한다. 이 함정을 모르면 "테스트는 통과했는데 프로덕션이 느리다"는 상황이 나온다.

## 트레이드오프

| 해법 | 적용 상황 | 주의 |
|---|---|---|
| fetch join (JPQL) | ManyToOne, 단일 OneToMany, 페이징 없음 | 컬렉션 둘 이상이면 Cartesian product |
| `@EntityGraph` | Repository 선언적, fetch join과 동일 의미 | 제한도 동일 |
| `@BatchSize` | pagination + 컬렉션 다수 | 쿼리 2+ 번, 여전히 N+1의 "N은 아님" |
| EAGER로 되돌리기 | 쓰지 마라 | 모든 조회에 강제 조인 → N+1보다 더 큰 규모의 문제 |

## 꼬리질문

- 지연 로딩과 fetch join 중 무엇을 기본으로 두어야 하나? 왜?
- `@BatchSize(size=100)`이 걸린 컬렉션에서 데이터 250건을 순회하면 쿼리는 몇 번 나가나?
- fetch join + pagination이 금지되는 이유를 SQL 수준에서 설명할 수 있나?
- N+1이 단위 테스트에서는 안 잡히고 통합 테스트에서는 잡히는 이유는?

## 한 줄 정리

N+1은 lazy의 버그가 아니라 fetch plan을 도메인 코드 시점에 맡긴 결과다. 탐지는 쿼리 카운트를 테스트로 박제해서, 처방은 fetch join / `@EntityGraph` / `@BatchSize`를 경계에 맞춰 나눠서.
