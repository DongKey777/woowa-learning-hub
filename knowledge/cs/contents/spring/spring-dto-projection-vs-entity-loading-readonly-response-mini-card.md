---
schema_version: 3
title: DTO Projection vs Entity Loading Mini Card for Read-Only Responses
concept_id: spring/dto-projection-vs-entity-loading-readonly-response-mini-card
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 86
review_feedback_tags:
- dto-projection-vs
- entity-loading-readonly
- response
- entity-loading
aliases:
- DTO projection vs entity loading
- JPQL DTO projection
- Querydsl DTO projection
- read only response projection
- entity loading vs projection JPA
- select new DTO projection
- response DTO no entity loading
intents:
- comparison
- definition
linked_paths:
- contents/spring/spring-fetch-join-vs-entitygraph-dto-read-mini-card.md
- contents/spring/spring-lazy-loading-dto-mapping-checklist.md
- contents/spring/spring-open-session-in-view-tradeoffs.md
- contents/spring/spring-data-jpa-basics.md
- contents/database/n-plus-one-query-detection-solutions.md
expected_queries:
- 읽기 전용 응답에서는 DTO projection과 entity loading 중 무엇을 골라야 해?
- JPQL select new DTO projection은 언제 자연스러워?
- 조회 뒤 엔티티 규칙을 쓸 일이 있으면 projection이 맞지 않은 이유는?
- DTO projection이 lazy loading과 N+1을 줄이는 데 어떻게 도움이 돼?
contextual_chunk_prefix: |
  이 문서는 read-only response에서 DTO projection과 entity loading을 비교하는
  beginner mini card다. JPQL select new, Querydsl constructor projection,
  필요한 컬럼만 읽기, lazy loading/N+1 회피, 조회 뒤 엔티티 규칙이나 상태 변경이
  필요한 경우 entity loading을 고르는 기준을 설명한다.
---
# DTO Projection vs Entity Loading Mini Card for Read-Only Responses

> 한 줄 요약: 응답이 읽기 전용이고 필요한 값이 몇 개 안 되면 JPQL/Querydsl DTO projection을 먼저 떠올리고, 조회 뒤에 엔티티 규칙을 쓰거나 상태 변경 가능성이 있으면 엔티티 로딩을 고른다.

**난이도: 🟢 Beginner**

관련 문서:

- [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)
- [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
- [Spring Data JPA 기초: Repository로 DB를 다루는 방법](./spring-data-jpa-basics.md)
- [N+1 Query Detection and Solutions](../database/n-plus-one-query-detection-solutions.md)

retrieval-anchor-keywords: dto projection vs entity loading, jpql dto projection beginner, querydsl dto projection beginner, read only response dto projection, entity loading vs projection jpa, select new dto projection, querydsl constructor projection, spring jpa read model beginner, response dto no entity loading, projection 언제 쓰나, 엔티티 로딩 언제 쓰나, 읽기 전용 응답 projection, jpa dto projection primer, spring dto projection vs entity loading readonly response mini card basics, spring dto projection vs entity loading readonly response mini card beginner

## 먼저 mental model 한 줄

초급자는 먼저 이렇게 나누면 된다.

- 엔티티 로딩: "객체 자체를 가져와서 연관과 상태를 다룬다"
- DTO projection: "응답에 필요한 값만 바로 뽑아 담는다"

핵심 질문은 하나다.

**이번 조회 뒤에 엔티티를 계속 다룰 일도 없고, 응답만 만들면 끝나는가?**

- 예: DTO projection 쪽이 자연스럽다
- 아니오: 엔티티 로딩 쪽이 더 안전하다

## 30초 결정 카드

| 지금 상황 | 먼저 고를 기본값 | 이유 |
|---|---|---|
| 목록/상세 응답을 읽기 전용 DTO로 바로 내려준다 | DTO projection | 필요한 컬럼만 바로 읽어 lazy loading, 불필요한 엔티티 보관을 줄인다 |
| 조회 후 엔티티 메서드 호출, 검증, 상태 변경 가능성이 있다 | 엔티티 로딩 | managed 엔티티가 있어야 흐름이 자연스럽다 |
| 응답에 필드 3~5개 정도만 필요하다 | DTO projection | "엔티티 전체"보다 의도가 더 직접적이다 |
| 응답에 연관 여러 개와 도메인 규칙 판단이 섞여 있다 | 엔티티 로딩 후 DTO 변환 | projection보다 서비스 코드가 읽기 쉬울 수 있다 |
| 이미 fetch join/`@EntityGraph`로 필요한 연관을 잘 제어하고 있다 | 엔티티 로딩 유지 가능 | 억지로 projection으로 바꿀 이유는 없다 |

초급자 기본값을 더 짧게 줄이면 이렇다.

- 읽기 전용 응답이고 값 몇 개만 필요함: projection
- 읽은 뒤 엔티티를 더 다룸: entity

## 가장 단순한 비교 예시

주문 목록 화면에 아래 값만 필요하다고 하자.

- 주문 id
- 주문자 이름
- 총액

### 1. 엔티티를 읽고 DTO로 바꾸는 방식

```java
@Transactional(readOnly = true)
public List<OrderSummaryResponse> findOrders() {
    return orderRepository.findAllWithMember().stream()
        .map(order -> new OrderSummaryResponse(
            order.getId(),
            order.getMember().getName(),
            order.getTotalPrice()
        ))
        .toList();
}
```

이 방식은 아래 때 잘 맞는다.

- 이미 엔티티 기반 조회가 있다
- 서비스에서 엔티티 규칙을 같이 본다
- 연관 로딩 계획을 fetch join/`@EntityGraph`로 관리하고 있다

### 2. DTO projection으로 바로 읽는 방식

```java
@Query("""
    select new com.example.api.OrderSummaryResponse(
        o.id,
        m.name,
        o.totalPrice
    )
    from Order o
    join o.member m
    order by o.id desc
    """)
List<OrderSummaryResponse> findOrderSummaries();
```

이 방식은 아래 때 잘 맞는다.

- 응답 DTO 모양이 명확하다
- 조회 결과를 수정하지 않는다
- 엔티티 전체를 들고 있을 이유가 없다

Querydsl을 쓰는 팀이라면 같은 판단 기준으로 projection을 고르면 된다.
문법만 다르고, "응답에 필요한 값만 바로 담는다"는 목적은 같다.

## 왜 projection이 초급자에게 실용적인가

| 초급자 고민 | projection이 주는 효과 |
|---|---|
| "controller/serializer에서 lazy loading 터질까?" | 응답 DTO가 이미 완성돼 있어 경계가 더 분명해진다 |
| "필요 없는 연관까지 읽는 것 아닌가?" | 필요한 값만 선택적으로 고르기 쉽다 |
| "읽기 API인데 엔티티를 꼭 들고 있어야 하나?" | 꼭 그렇지 않다는 선택지를 보여 준다 |

단, projection이 "항상 더 좋은 최적화"는 아니다.
응답이 단순할 때 특히 잘 맞는 도구라고 보는 편이 정확하다.

## 엔티티 로딩이 더 나은 경우도 많다

아래 중 하나라도 크면 엔티티 로딩 쪽이 더 자연스럽다.

- 조회 후 비즈니스 규칙을 엔티티 메서드나 도메인 로직으로 판단한다
- 같은 트랜잭션에서 상태 변경까지 이어질 수 있다
- 응답을 만들기 전에 연관을 따라 여러 판단을 해야 한다
- projection 쿼리보다 "엔티티 조회 후 변환"이 팀에 더 읽기 쉽다

이때는 "엔티티를 읽지 말자"가 아니라, **필요한 연관만 미리 읽고 service 안에서 DTO로 닫자**가 더 실용적인 기본값이다.

## 자주 하는 오해 5개

- "읽기 API는 무조건 projection이 정답"이 아니다. 서비스 로직이 엔티티를 필요로 하면 엔티티 로딩이 더 낫다.
- "projection이면 성능이 무조건 훨씬 좋다"로 외우지 않는다. 이 카드는 먼저 의도와 경계 명확화에 초점을 둔다.
- "엔티티 로딩은 곧 나쁜 코드"가 아니다. 읽은 뒤 엔티티를 다루면 자연스러운 선택이다.
- "projection을 쓰면 fetch join/`@EntityGraph`를 몰라도 된다"가 아니다. 엔티티 기반 조회를 유지할 때는 여전히 중요하다.
- "projection은 JPQL에서만 된다"가 아니다. Querydsl로도 같은 목적을 달성할 수 있다.

## 초급자용 선택 질문 3개

1. 이 조회는 응답 DTO만 만들고 끝나는가?
2. 응답에 필요한 값이 엔티티 전체보다 훨씬 적은가?
3. 조회 뒤에 엔티티 상태 변경이나 도메인 규칙 판단이 없는가?

세 질문에 대부분 "예"라면 DTO projection을 먼저 검토할 만하다.

## 같이 보면 좋은 다음 카드

- 엔티티는 유지하되 어떤 연관을 미리 읽을지 헷갈리면 [Fetch Join vs `@EntityGraph` Mini Card for DTO Reads](./spring-fetch-join-vs-entitygraph-dto-read-mini-card.md)를 본다.
- controller나 serializer 시점 lazy loading이 왜 위험한지 다시 묶고 싶다면 [Lazy Loading to DTO Mapping Checklist](./spring-lazy-loading-dto-mapping-checklist.md)를 본다.

## 한 줄 정리

읽기 전용 응답에서 "필요한 값만 바로 내려주면 끝"이라면 JPQL/Querydsl DTO projection이 좋은 기본값이고, 조회 뒤에 엔티티를 더 다루거나 상태 변경 가능성이 있으면 엔티티 로딩 후 service 안에서 DTO로 닫는 쪽이 더 안전하다.
