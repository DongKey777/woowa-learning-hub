---
schema_version: 3
title: Repository Pattern vs Anti-Pattern
concept_id: design-pattern/repository-pattern-vs-antipattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- repository-pattern
- repository-antipattern
- query-leakage
aliases:
- repository pattern
- repository anti pattern
- repository antipattern
- domain collection abstraction
- generic crud repository smell
- repository query leakage
- fat repository
- DAO vs repository
- 저장소 패턴
- 레포지토리 안티패턴
symptoms:
- Repository를 모든 SQL과 DTO 조립과 검증과 캐시 정책을 숨기는 data access god class로 만든다
- 도메인 컬렉션 추상화가 아니라 테이블 중심 DAO처럼 selectAllJoinXAndY 형태의 메서드가 늘어난다
- 복잡한 읽기 요구를 query service나 read model로 분리하지 않고 aggregate repository에 계속 붙인다
intents:
- comparison
- troubleshooting
- design
prerequisites:
- design-pattern/unit-of-work-pattern
- design-pattern/aggregate-root-vs-unit-of-work
- design-pattern/aggregate-reference-by-id
next_docs:
- design-pattern/repository-boundary-aggregate-vs-read-model
- design-pattern/specification-vs-query-service-boundary
- design-pattern/cqrs-command-query-separation-pattern-language
linked_paths:
- contents/design-pattern/unit-of-work-pattern.md
- contents/design-pattern/aggregate-root-vs-unit-of-work.md
- contents/design-pattern/aggregate-reference-by-id.md
- contents/design-pattern/repository-boundary-aggregate-vs-read-model.md
- contents/design-pattern/specification-vs-query-service-boundary.md
- contents/design-pattern/anti-pattern.md
confusable_with:
- design-pattern/repository-boundary-aggregate-vs-read-model
- design-pattern/specification-vs-query-service-boundary
- design-pattern/unit-of-work-pattern
- design-pattern/query-object-search-criteria-pattern
forbidden_neighbors: []
expected_queries:
- Repository Pattern과 DAO는 도메인 컬렉션 추상화와 데이터 접근 객체 관점에서 어떻게 달라?
- Repository가 저장, 조회, 검증, DTO 조립, 캐시까지 맡으면 왜 anti-pattern이 돼?
- findBy 조건이 끝없이 늘어날 때 read model이나 query service로 분리해야 하는 신호는 뭐야?
- aggregate 저장용 repository와 복잡한 검색용 query repository를 나누는 기준을 설명해줘
- generic CRUD repository를 도메인 계층에 그대로 노출하면 어떤 책임 누수가 생겨?
contextual_chunk_prefix: |
  이 문서는 Repository Pattern vs Anti-Pattern chooser로, Repository는 domain
  collection처럼 aggregate를 조회/저장하는 계약이어야 하며, SQL 조립, DTO 변환,
  비즈니스 검증, cache policy가 몰리면 fat repository/data access god class가 되는
  기준을 설명한다.
---
# Repository Pattern vs Anti-Pattern

> 한 줄 요약: Repository는 도메인 컬렉션처럼 동작하는 저장소 추상화지만, 모든 데이터 접근을 한 클래스에 몰면 anti-pattern이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Unit of Work Pattern](./unit-of-work-pattern.md)
> - [Aggregate Root vs Unit of Work](./aggregate-root-vs-unit-of-work.md)
> - [Reference Other Aggregates by ID](./aggregate-reference-by-id.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Specification vs Query Service Boundary](./specification-vs-query-service-boundary.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [안티 패턴](./anti-pattern.md)

retrieval-anchor-keywords: repository pattern, repository antipattern, controller service repository 계층 책임, controller service repository layered responsibility, 계층 책임 분담, layered responsibility controller service repository, repository responsibilities, repository pattern vs antipattern, repository overload anti pattern, domain collection abstraction, repository fat anti pattern, generic crud repository smell

---

## 핵심 개념

Repository는 DDD에서 **도메인 객체를 저장/조회하는 추상화**다.  
중요한 건 "모든 SQL을 숨기는 만능 클래스"가 아니라, 도메인 관점의 컬렉션처럼 행동하는 것이다.

하지만 실무에서는 Repository가 쉽게 anti-pattern이 된다.

- CRUD가 전부 한 곳에 몰린다
- 쿼리와 비즈니스 규칙이 섞인다
- `findBy...`가 끝없이 늘어난다
- 사실상 DAO + Service + Mapper가 된다

### Retrieval Anchors

- `repository pattern`
- `repository anti pattern`
- `domain collection abstraction`
- `query leakage`
- `persistence ignorance`
- `aggregate id reference`
- `repository boundary`
- `read model boundary`
- `repository query leakage`

---

## 깊이 들어가기

### 1. Repository는 도메인 언어를 지켜야 한다

좋은 Repository는 도메인 용어를 사용한다.

- `save(order)`
- `findActiveMembers()`
- `findById()`

나쁜 Repository는 테이블과 쿼리 중심으로 변한다.

- `selectAllJoinXAndY`
- `updateStatusAndMemo`
- `findBySomethingAndSomethingElseAndYetAnotherThing`

### 2. anti-pattern이 되는 순간

Repository가 다음 일을 동시에 하면 문제다.

- 영속화
- 비즈니스 규칙 판단
- 응답 DTO 조립
- 캐시 정책

이건 Repository가 아니라 **data access god class**다.

### 3. Query는 읽기 모델로 빼도 된다

복잡한 조회는 Repository 한 개에 몰지 않아도 된다.

- command side: repository
- query side: read model / query service

이 지점에서 CQRS와 잘 연결된다.

---

## 실전 시나리오

### 시나리오 1: 주문 저장

주문 aggregate를 저장하는 Repository는 root 중심으로 단순하게 유지한다.

### 시나리오 2: 검색 API

복잡한 검색은 Repository가 아니라 query service나 read repository로 분리하는 편이 낫다.

### 시나리오 3: 영속성 혼합 로직

Repository 안에 검증, 계산, 외부 호출이 들어가면 바로 smell이다.

---

## 코드로 보기

### Good Repository

```java
public interface OrderRepository {
    Optional<Order> findById(Long id);
    void save(Order order);
}
```

### Smell

```java
public class OrderRepositoryImpl {
    public List<OrderSummary> findByStatusAndPeriodAndMemberGrade(...) {
        // 너무 많은 조회 규칙
    }

    public void validateAndSave(Order order) {
        // 저장과 도메인 규칙이 섞임
    }
}
```

### Query side 분리

```java
public class OrderQueryService {
    public List<OrderSummary> search(OrderSearchCondition condition) {
        return queryRepository.search(condition);
    }
}
```

Repository는 저장과 조회의 계약만 지키는 쪽이 안전하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Repository | 도메인 친화적이다 | 과하면 비대해진다 | aggregate 저장 |
| DAO | 단순 데이터 접근 | 도메인 언어가 약하다 | 기술 중심 코드 |
| Query Service | 조회를 분리한다 | 저장과 분리가 필요하다 | 검색이 복잡할 때 |

판단 기준은 다음과 같다.

- 저장과 도메인 규칙이 중심이면 Repository
- 복잡한 조회가 중심이면 Query Service
- SQL이 도메인 계층으로 새면 설계를 다시 본다

---

## 꼬리질문

> Q: Repository와 DAO의 차이는 무엇인가요?
> 의도: 도메인 중심과 데이터 중심의 차이를 아는지 확인한다.
> 핵심: Repository는 도메인 컬렉션, DAO는 데이터 접근이다.

> Q: Repository가 anti-pattern이 되는 이유는 무엇인가요?
> 의도: 책임 과밀을 이해하는지 확인한다.
> 핵심: 저장, 조회, 검증, 변환이 한곳에 몰리기 때문이다.

> Q: 읽기 쿼리는 어디로 빼야 하나요?
> 의도: CQRS와 조회 분리를 연결하는지 확인한다.
> 핵심: query service나 read model로 분리하는 편이 좋다.

## 한 줄 정리

Repository는 도메인 저장소 추상화지만, 조회와 규칙이 몰리면 anti-pattern이 된다.
