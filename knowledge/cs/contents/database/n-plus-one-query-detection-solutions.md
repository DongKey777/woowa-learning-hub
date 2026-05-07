---
schema_version: 3
title: N+1 Query Detection and Solutions
concept_id: database/n-plus-one-query-detection-solutions
canonical: true
category: database
difficulty: intermediate
doc_role: playbook
level: intermediate
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- jpa-n-plus-one-fetch-plan
- lazy-loading-query-count
- fetch-join-entitygraph-batchsize
aliases:
- N+1 query
- N plus one problem
- JPA N+1
- lazy loading N+1
- fetch join
- EntityGraph
- BatchSize
- query count test
symptoms:
- repository는 한 번 호출했는데 DTO 변환이나 엔티티 순회 중 SQL이 여러 번 나가는 이유를 못 찾고 있어
- lazy loading을 버그로만 보고 fetch plan을 조회 시점에 명시해야 한다는 점을 놓치고 있어
- fetch join, EntityGraph, BatchSize를 쿼리 수만 줄이는 같은 해결책으로 보고 pagination/컬렉션 제약을 놓치고 있어
intents:
- troubleshooting
- comparison
prerequisites:
- spring/spring-data-jpa-basics
- database/index-and-explain
next_docs:
- spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card
- database/covering-index-composite-ordering
- software-engineering/datasource-proxy-vs-statistics
- software-engineering/jpa-lazy-loading-n-plus-one-boundary-smells
linked_paths:
- contents/spring/spring-persistence-transaction-web-service-repository-primer.md
- contents/spring/spring-data-jpa-basics.md
- contents/spring/spring-data-jpa-save-persist-merge-state-transitions.md
- contents/spring/jpa-dirty-checking-version-strategy.md
- contents/spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md
- contents/database/covering-index-composite-ordering.md
- contents/database/transaction-isolation-locking.md
- contents/software-engineering/datasource-proxy-vs-hibernate-statistics-query-count-batch-primer.md
- contents/software-engineering/jpa-lazy-loading-n-plus-one-boundary-smells.md
confusable_with:
- spring/spring-data-jpa-basics
- spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card
- database/covering-index-composite-ordering
- software-engineering/jpa-lazy-loading-n-plus-one-boundary-smells
forbidden_neighbors: []
expected_queries:
- N+1 query는 왜 repository 호출 한 번인데 SQL이 1+N번 나가는 문제야?
- lazy loading 때문에 DTO 변환 중 SQL이 여러 번 찍힐 때 어디서 fetch plan을 잡아야 해?
- fetch join, EntityGraph, BatchSize는 각각 어떤 제약과 장점이 있어?
- collection fetch join과 pagination을 같이 쓰면 왜 위험해?
- N+1을 query count test로 어떻게 탐지하고 회귀를 막아?
contextual_chunk_prefix: |
  이 문서는 JPA/Hibernate N+1 troubleshooting playbook으로, lazy loading, entity traversal, fetch plan, fetch join, EntityGraph, BatchSize, query count test, pagination with collection fetch join을 다룬다.
  N+1 뭐예요, 조회 한 번인데 SQL 여러 번, lazy loading SQL 폭증, fetch join 언제, EntityGraph, BatchSize 같은 자연어 질문이 본 문서에 매핑된다.
---
# N+1 Query Detection and Solutions

> 한 줄 요약: 이 문서는 `"N+1 뭐예요?"`, `"왜 조회 한 번 했는데 쿼리가 여러 번 나가요?"`, `"lazy loading 때문에 SQL이 갑자기 많이 찍혀요"` 같은 첫 질문에서 먼저 잡히는 primer를 목표로 하며, N+1을 "ORM이 느리다"가 아니라 지연 로딩과 fetch plan 경계가 어긋난 증상으로 설명한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-persistence-transaction-web-service-repository-primer.md)
- [Spring Data JPA 기초](../spring/spring-data-jpa-basics.md)


retrieval-anchor-keywords: n+1 뭐예요, n plus one 뭐예요, 처음 배우는데 n+1, jpa n+1 뭐예요, lazy loading 때문에 쿼리가 여러 번 나가요, 조회 한 번 했는데 sql이 여러 번 나가요, controller dto 만들 때 쿼리가 또 나가요, 엔티티 순회했더니 쿼리 많이 나가요, fetch join 언제 써요, entitygraph 언제 써요, batch fetch size 언제 써요, n+1 탐지 방법, query count test, 지연 로딩 sql 많이 찍힘, spring data jpa n+1 beginner
> 관련 문서:
> - [Spring Data JPA `save`, `persist`, `merge` State Transitions](../spring/spring-data-jpa-save-persist-merge-state-transitions.md)
> - [JPA Dirty Checking, @Version, Cascade Trade-offs](../spring/jpa-dirty-checking-version-strategy.md)
> - [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](../spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)
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

## 이 문서가 먼저 답하는 질문

- "`N+1`이 뭐예요?"
- "왜 repository는 한 번 호출한 것 같은데 SQL은 여러 번 나가요?"
- "lazy loading이랑 N+1이 같은 말인가요?"
- "fetch join, `@EntityGraph`, `@BatchSize` 중 뭘 먼저 골라야 해요?"

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

## 깊이 들어가기 (계속 2)

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

DTO 읽기에서 "fetch join과 `@EntityGraph` 중 무엇을 먼저 고를지"만 빠르게 정리하고 싶다면 [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](../spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)를 먼저 보고 돌아오면 된다.

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
