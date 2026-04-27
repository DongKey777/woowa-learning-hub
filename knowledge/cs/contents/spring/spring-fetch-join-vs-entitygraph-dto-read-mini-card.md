# Fetch Join vs `@EntityGraph` Mini Card for DTO Reads

> 한 줄 요약: 초급자는 "DTO에 필요한 연관을 이번 조회에서 미리 읽는다"를 먼저 잡고, 쿼리를 직접 설명해야 하면 fetch join, Repository 메서드에 선언적으로 붙이고 싶으면 `@EntityGraph`를 기본값으로 고르면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [DTO Projection vs Entity Loading Mini Card for Read-Only Responses](./spring-dto-projection-vs-entity-loading-readonly-response-mini-card.md)
- [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)
- [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
- [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: fetch join vs entitygraph beginner, dto read mini card, fetch join entitygraph decision card, jpa dto read fetch plan, entitygraph 언제 쓰나, fetch join 언제 쓰나, dto 조회 연관 로딩, lazy loading dto fetch join entitygraph, spring jpa beginner fetch plan, repository entitygraph primer

## 먼저 mental model 한 줄

둘 다 "이번 조회에서 lazy 연관을 미리 읽겠다"는 도구다.

초급자는 먼저 이렇게 기억하면 된다.

- fetch join: JPQL 쿼리 문장에 직접 적는다.
- `@EntityGraph`: Repository 메서드에 "이 연관도 같이 읽어"라고 선언적으로 붙인다.
- 목적은 같다. DTO 변환 전에 필요한 데이터를 transaction 안에서 준비하는 것이다.

## 30초 결정 카드

| 지금 상황 | 먼저 고를 기본값 | 이유 |
|---|---|---|
| 기존 `findById`, `findAll` 같은 Repository 메서드에 연관 하나둘만 추가 로딩 | `@EntityGraph` | 메서드 이름과 함께 fetch plan을 짧게 붙이기 쉽다 |
| 조회 조건, 조인 조건, 정렬을 JPQL로 이미 세밀하게 쓰고 있다 | fetch join | 쿼리 의미와 로딩 계획을 한 문장에 같이 둔다 |
| DTO 읽기에서 `@ManyToOne` 하나를 같이 읽고 싶다 | 둘 다 가능 | 팀이 더 읽기 쉬운 쪽을 고르면 된다 |
| `@OneToMany` 컬렉션 + pagination | 둘 다 피한다 | 둘 다 컬렉션 fetch 제약이 같아서 메모리 페이징/N+1 대안을 먼저 봐야 한다 |

핵심은 "누가 더 강력하냐"보다 **어디에 의도를 적는 편이 지금 코드에서 더 읽기 쉬우냐**다.

단, "엔티티 자체를 읽을지, DTO projection으로 바로 읽을지"가 먼저 헷갈리면 [DTO Projection vs Entity Loading Mini Card for Read-Only Responses](./spring-dto-projection-vs-entity-loading-readonly-response-mini-card.md)를 먼저 보는 편이 순서상 더 쉽다.

## 가장 단순한 예시

주문 DTO를 만들 때 회원 이름이 꼭 필요하다고 하자.

### 1. fetch join으로 직접 적기

```java
@Query("""
    select o
    from Order o
    join fetch o.member
    where o.id = :id
    """)
Optional<Order> findDetailById(Long id);
```

- 장점: SQL/JPQL을 읽는 사람에게 의도가 바로 보인다.
- 잘 맞는 경우: 이미 커스텀 JPQL이 있는 조회.

### 2. `@EntityGraph`로 선언적으로 붙이기

```java
@EntityGraph(attributePaths = "member")
Optional<Order> findById(Long id);
```

- 장점: 메서드 시그니처를 크게 바꾸지 않고 fetch plan만 붙일 수 있다.
- 잘 맞는 경우: Spring Data JPA 기본 메서드나 짧은 파생 쿼리.

## DTO 읽기 기준 초급자 선택 규칙

| 질문 | 예/아니오에 따른 선택 |
|---|---|
| "이미 JPQL을 커스텀으로 쓰고 있나?" | 예면 fetch join이 자연스럽다 |
| "기본 Repository 메서드에 연관 하나만 더 읽으면 되나?" | 예면 `@EntityGraph`가 더 짧다 |
| "응답 DTO에 필요한 연관이 컬렉션인가?" | 예면 pagination 여부를 먼저 확인한다 |
| "팀이 쿼리 문장보다 Repository 선언 스타일을 더 선호하나?" | 예면 `@EntityGraph` 쪽이 유지보수에 유리할 수 있다 |

초급자 기본값을 한 줄로 줄이면 이렇다.

- 기본 메서드에 연관만 보강: `@EntityGraph`
- 커스텀 JPQL이 이미 있음: fetch join

## 자주 하는 오해 4개

- "fetch join이 더 빠르고 `@EntityGraph`는 덜 강력하다"로 외우지 않는다. 초급자 레벨에서는 둘 다 fetch plan을 명시하는 도구로 먼저 보면 된다.
- "`@EntityGraph`면 pagination 문제가 사라진다"가 아니다. 컬렉션 fetch 제약은 비슷하게 남는다.
- "DTO 조회니까 무조건 fetch join"이 아니다. 목적은 DTO에 필요한 연관을 미리 읽는 것이지, JPQL을 억지로 늘리는 것이 아니다.
- "`EAGER`로 바꾸면 둘 다 필요 없다"가 아니다. 전역 fetch 변경보다 조회별 fetch plan 명시가 더 안전하다.

## 같이 기억할 경계 하나

`@ManyToOne` 하나를 DTO에 붙이는 읽기라면 둘 다 편하게 쓸 수 있다.

하지만 아래 상황이면 "fetch join vs `@EntityGraph`" 비교보다 다른 처방을 먼저 봐야 한다.

- 컬렉션 `@OneToMany`를 페이지 조회에서 같이 읽어야 한다
- 컬렉션이 여러 개라 row 수가 불어날 수 있다
- N+1을 테스트로 먼저 고정하지 않았다

이 경우는 [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)를 바로 보는 편이 안전하다.

## 한 줄 정리

DTO 읽기에서 fetch join과 `@EntityGraph`는 둘 다 "이번 조회에서 필요한 연관을 미리 읽는다"는 같은 목적의 도구다. 초급자는 "기본 Repository 메서드 보강이면 `@EntityGraph`, 이미 JPQL을 쓰는 조회면 fetch join"을 기본 카드로 들고 가면 된다.
