---
schema_version: 3
title: Specification vs Query Service Boundary
concept_id: design-pattern/specification-vs-query-service-boundary
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- specification-query-boundary
- read-contract-boundary
- repository-query-leakage
aliases:
- specification vs query service
- domain condition boundary
- read contract boundary
- repository query leakage
- screen model query
- search vs domain rule
- query object
- domain specification vs jpa specification
- 화면 검색 조건 vs 도메인 조건
- query service boundary
symptoms:
- 관리자 화면 검색 조건과 탭/정렬/페이징 요구를 모두 Domain Specification으로 올려 도메인 언어가 화면 요구에 끌려간다
- Query Service 대신 repository method와 specification 조합만 늘려 read contract와 aggregate persistence boundary가 흐려진다
- JPA Specification이라는 구현 도구를 도메인 Specification과 동일시해 command side 규칙과 query side 최적화를 섞는다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- design-pattern/specification-pattern
- design-pattern/query-object-search-criteria-pattern
- design-pattern/repository-boundary-aggregate-vs-read-model
next_docs:
- design-pattern/search-normalization-query-pattern
- design-pattern/cqrs-command-query-separation-pattern-language
- design-pattern/read-model-staleness-read-your-writes
linked_paths:
- contents/design-pattern/specification-pattern.md
- contents/design-pattern/query-object-search-criteria-pattern.md
- contents/design-pattern/repository-boundary-aggregate-vs-read-model.md
- contents/design-pattern/repository-pattern-vs-antipattern.md
- contents/design-pattern/cqrs-command-query-separation-pattern-language.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/design-pattern/search-normalization-query-pattern.md
confusable_with:
- design-pattern/specification-pattern
- design-pattern/query-object-search-criteria-pattern
- design-pattern/repository-boundary-aggregate-vs-read-model
- design-pattern/cqrs-command-query-separation-pattern-language
forbidden_neighbors: []
expected_queries:
- Specification과 Query Service는 조건을 다루지만 도메인 조건과 화면 조회 계약이 어떻게 달라?
- 관리자 검색 조건을 Domain Specification으로 모두 올리면 repository boundary가 흐려지는 이유가 뭐야?
- JPA Specification을 Query Service 내부 구현으로 쓸 수는 있지만 공개 계약 의도는 왜 별도로 봐야 해?
- 취소 가능한 주문인지 판단하는 조건은 Specification이고 관리자 주문 목록 조회는 Query Service에 가까운 이유가 뭐야?
- screen query leakage를 막으려면 Query Object, Read Repository, Domain Specification 책임을 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 Specification vs Query Service Boundary chooser로, 도메인 언어를 가진
  boolean condition은 Specification 후보이고, 화면/검색/집계/페이징/정렬을 만족하는 read
  contract는 Query Service와 Query Object 후보라는 경계를 repository boundary와 함께 설명한다.
---
# Specification vs Query Service Boundary

> 한 줄 요약: Specification은 도메인 조건의 의미를 조합하는 데 강하고, Query Service는 화면/검색/집계 요구를 만족하는 조회 계약을 조직하는 데 강하므로 둘의 경계를 섞지 않는 편이 repository boundary를 지키기 쉽다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Specification Pattern](./specification-pattern.md)
> - [Query Object and Search Criteria Pattern](./query-object-search-criteria-pattern.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)

---

## 핵심 개념

Specification을 도입하면 곧 이런 유혹이 생긴다.

- 모든 검색 조건을 Specification으로 만들자
- Query Service 대신 Specification만 조합하면 되지 않나
- 화면 조회도 결국 조건이니 domain spec으로 처리하자

하지만 여기에는 중요한 경계가 있다.

- Specification: 도메인 조건의 의미를 표현
- Query Service: 조회 목적에 맞는 read contract를 제공

이 둘을 섞기 시작하면 domain condition과 screen query가 같은 추상화 위에 올라가면서 repository boundary가 다시 흐려질 수 있다.

그래서 "조건식인가"보다 먼저 "이 조건이 도메인 판단에 재사용되는가, 아니면 특정 화면의 read contract인가"를 물어야 한다.

### Retrieval Anchors

- `specification vs query service`
- `domain condition boundary`
- `read contract boundary`
- `repository query leakage`
- `screen model query`
- `search vs domain rule`
- `query object`

---

## 깊이 들어가기

### 1. Specification은 "이 조건을 만족하는가"에 가깝다

명세는 보통 이런 질문에 맞는다.

- 이 회원은 쿠폰 대상자인가
- 이 주문은 취소 가능한가
- 이 신청은 승인 조건을 만족하는가

즉 조건 자체가 도메인 언어를 가진다.

### 2. Query Service는 "무엇을 보여줘야 하는가"에 가깝다

조회 서비스는 다음 요구를 다룬다.

- 관리자 검색 화면
- 정렬/페이징/필터 조합
- 여러 소스 조합한 대시보드
- 응답 DTO/View 모델 생성

이건 참/거짓보다 **표현과 조회 목적**이 중심이다.

### 3. 모든 검색을 Specification으로 몰면 도메인 언어가 화면 요구에 끌려간다

예를 들면 이런 smell이 생긴다.

- `RecentCardPaymentOrderSpecification`
- `DashboardHighlightedSellerSpecification`
- `AdminTabVisibleSpecification`

이런 이름은 도메인 규칙이라기보다 화면 요구나 운영 검색 요구에 가깝다.

즉 Specification이 domain boundary보다 screen query leakage를 흡수하는 통로가 될 수 있다.

### 4. repository 안의 specification 사용과 query service 경계는 별개다

Repository가 내부적으로 Specification을 쓸 수는 있다.  
하지만 그게 곧 모든 조회 계약을 repository로 끌어들이라는 뜻은 아니다.

- command side repository 내부 검색 조건 최적화
- query side read repository/query service의 검색 API

둘은 구현 도구가 겹칠 수 있어도 책임은 다르다.

### 5. 좋은 질문은 "이 조건이 도메인 언어로 재사용되는가"다

다음 질문이 도움이 된다.

- 이 조건이 여러 command 판단에 재사용되는가
- aggregate/policy/domain service에서 의미가 있는가
- 아니면 특정 화면/탭/검색 UX에만 필요한가

전자는 Specification 후보고, 후자는 Query Service 후보일 가능성이 크다.

---

## 실전 시나리오

### 시나리오 1: 쿠폰 발급 대상자

활성 회원, 등급, 최근 활동 같은 조건은 domain rule로 재사용될 수 있다.  
이런 건 Specification이 자연스럽다.

### 시나리오 2: 관리자 주문 검색

다중 정렬, 탭별 필터, 페이징, 카드 결제만 보기, 취소 제외는 Query Service가 더 자연스럽다.  
이걸 모두 domain specification으로 올리면 도메인 언어가 화면에 끌려간다.

### 시나리오 3: 승인 가능 여부 판단 + 목록 조회

승인 가능 여부는 Specification, 승인 대기 목록 조회는 Query Service가 각각 더 잘 맞을 수 있다.  
같은 조건 일부를 공유하더라도 책임은 분리할 수 있다.

---

## 코드로 보기

### domain specification

```java
public interface Specification<T> {
    boolean isSatisfiedBy(T candidate);
}

public class CancellableOrderSpecification implements Specification<Order> {
    @Override
    public boolean isSatisfiedBy(Order order) {
        return order.status() == OrderStatus.PAID && !order.hasShipmentStarted();
    }
}
```

### query service

```java
public class OrderQueryService {
    public List<OrderSearchView> search(OrderSearchCondition condition) {
        return orderReadRepository.search(condition);
    }
}
```

### 경계 원칙

```java
// "취소 가능한가?"는 specification 쪽에 더 가깝고,
// "관리자 탭에서 어떤 주문 목록을 보여줄까?"는 query service 쪽에 더 가깝다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Specification 중심 | 도메인 조건 재사용이 좋다 | 화면 조회 요구까지 빨아들이면 경계가 흐려진다 | 승인/대상자/자격 조건 |
| Query Service 중심 | 표현과 검색 최적화에 강하다 | 도메인 규칙 판단에는 약할 수 있다 | 관리자 검색, 대시보드, 목록 응답 |
| 혼합 | 각자 잘하는 일을 맡긴다 | 공유 조건을 어디에 둘지 판단이 필요하다 | 대부분의 실무 시스템 |

판단 기준은 다음과 같다.

- 참/거짓 도메인 의미가 핵심이면 Specification
- 페이징/정렬/표현 계약이 핵심이면 Query Service
- repository 경계를 지키려면 screen query를 domain spec으로 올리지 않는다

---

## 꼬리질문

> Q: 검색 조건도 결국 조건식인데 왜 Specification이 아니죠?
> 의도: 조건 일반과 도메인 조건의 차이를 보는 질문이다.
> 핵심: 검색 조건 중 상당수는 화면 표현 요구라서 Query Service가 더 자연스럽다.

> Q: Query Service에서도 Specification을 내부적으로 써도 되나요?
> 의도: 책임 경계와 구현 도구를 구분하는지 본다.
> 핵심: 된다. 중요한 건 공개 계약의 의도다.

> Q: domain specification과 JPA specification은 같은 건가요?
> 의도: 도메인 의미와 ORM 도구를 동일시하지 않는지 본다.
> 핵심: 아니다. 겹칠 수 있지만 한쪽은 도메인 언어, 다른 쪽은 구현 도구다.

## 한 줄 정리

Specification과 Query Service를 구분하면 도메인 조건과 화면 조회 계약이 서로를 잠식하지 않게 되고, repository boundary도 더 오래 건강하게 유지된다.
