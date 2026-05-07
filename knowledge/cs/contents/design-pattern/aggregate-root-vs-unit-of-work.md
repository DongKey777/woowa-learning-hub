---
schema_version: 3
title: Aggregate Root vs Unit of Work
concept_id: design-pattern/aggregate-root-vs-unit-of-work
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- aggregate-root
- unit-of-work
- domain-vs-persistence-boundary
aliases:
- aggregate root vs unit of work
- aggregate root
- unit of work relation
- domain consistency boundary
- persistence change tracking
- aggregate invariants
- aggregate version
- aggregate와 unit of work
- 도메인 경계와 커밋 경계
symptoms:
- Aggregate Root와 Unit of Work를 둘 다 transaction 관련 개념으로만 보고 도메인 규칙과 변경 추적 책임을 섞는다
- Aggregate 내부에 repository save나 flush 같은 persistence 로직을 넣어 도메인 모델과 저장 메커니즘을 결합한다
- Unit of Work가 있으니 aggregate invariant guard가 필요 없다고 오해한다
intents:
- comparison
- definition
- design
prerequisites:
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/unit-of-work-pattern
- design-pattern/aggregate-invariant-guard-pattern
next_docs:
- design-pattern/aggregate-version-optimistic-concurrency-pattern
- design-pattern/aggregate-reference-by-id
- design-pattern/repository-boundary-aggregate-vs-read-model
linked_paths:
- contents/design-pattern/aggregate-boundary-vs-transaction-boundary.md
- contents/design-pattern/unit-of-work-pattern.md
- contents/design-pattern/aggregate-version-optimistic-concurrency-pattern.md
- contents/design-pattern/aggregate-invariant-guard-pattern.md
- contents/design-pattern/aggregate-reference-by-id.md
- contents/design-pattern/cqrs-command-query-separation-pattern-language.md
confusable_with:
- design-pattern/unit-of-work-pattern
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/repository-boundary-aggregate-vs-read-model
- design-pattern/transaction-script-vs-rich-domain-model
forbidden_neighbors: []
expected_queries:
- Aggregate Root와 Unit of Work는 도메인 일관성 경계와 변경 커밋 경계 관점에서 어떻게 달라?
- Aggregate Root 안에 저장 로직이나 flush를 넣으면 왜 관심사가 섞여?
- Unit of Work가 dirty checking과 commit을 해도 aggregate invariant guard가 필요한 이유가 뭐야?
- 한 command에서 aggregate root를 바꾸고 Unit of Work로 커밋하는 흐름을 설명해줘
- Aggregate boundary와 transaction boundary를 구분할 때 Aggregate Root와 Unit of Work는 각각 어떤 역할이야?
contextual_chunk_prefix: |
  이 문서는 Aggregate Root vs Unit of Work chooser로, Aggregate Root는 domain
  consistency boundary와 invariant 접근 규칙이고 Unit of Work는 transaction 안의
  change tracking, dirty checking, flush/commit 메커니즘이라는 차이를 설명한다.
---
# Aggregate Root vs Unit of Work

> 한 줄 요약: Aggregate Root는 도메인 일관성 경계를 지키고, Unit of Work는 그 경계 안의 변경을 하나의 트랜잭션으로 묶는다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Boundary vs Transaction Boundary](./aggregate-boundary-vs-transaction-boundary.md)
> - [Unit of Work Pattern](./unit-of-work-pattern.md)
> - [Aggregate Version and Optimistic Concurrency Pattern](./aggregate-version-optimistic-concurrency-pattern.md)
> - [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)
> - [Reference Other Aggregates by ID](./aggregate-reference-by-id.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)

---

## 핵심 개념

Aggregate Root와 Unit of Work는 서로 다른 레벨의 개념이지만 backend 설계에서 자주 함께 나온다.

- Aggregate Root: 도메인 일관성의 경계
- Unit of Work: 트랜잭션 단위의 변경 추적

즉 하나는 **무엇이 함께 바뀌어야 하는가**를, 다른 하나는 **그 변경을 언제 반영할 것인가**를 다룬다.

### Retrieval Anchors

- `aggregate root`
- `aggregate boundary`
- `domain consistency boundary`
- `transaction boundary`
- `aggregate vs transaction boundary`
- `unit of work relation`
- `aggregate invariants`
- `aggregate invariant guard`
- `aggregate version`
- `optimistic concurrency`

---

## 깊이 들어가기

### 1. Aggregate Root는 접근 규칙이다

Aggregate는 여러 엔티티를 묶는 도메인 경계이고, Root는 외부가 접점으로 삼는 객체다.

- 외부는 root만 통해서 접근한다
- 내부 엔티티는 root가 보호한다
- 불변식은 경계 안에서 지켜진다

### 2. Unit of Work는 변경 반영 규칙이다

Unit of Work는 여러 변경을 모아 commit한다.

- dirty checking
- flush
- commit

이건 도메인 경계가 아니라 persistence 경계다.

### 3. 둘을 헷갈리면 서비스가 비대해진다

Aggregate 규칙을 Unit of Work에 넣거나, 반대로 저장 규칙을 Aggregate에 넣으면 구조가 흐려진다.

---

## 실전 시나리오

### 시나리오 1: 주문 Aggregate

주문과 주문 항목, 배송 상태는 root를 통해 함께 변경돼야 한다.

### 시나리오 2: 결제 상태 변경

상태 패턴은 Aggregate 내부의 전이 규칙을 표현하고, Unit of Work는 그 변경을 모아 저장한다.

### 시나리오 3: CQRS 명령 처리

명령은 root를 통해 처리되고, 변경은 Unit of Work로 반영된다.

---

## 코드로 보기

### Aggregate Root

```java
public class Order {
    private final List<OrderLine> lines = new ArrayList<>();

    public void addLine(OrderLine line) {
        // invariant checks
        lines.add(line);
    }
}
```

### Unit of Work

```java
@Transactional
public void placeOrder(PlaceOrderCommand command) {
    Order order = new Order();
    order.addLine(new OrderLine(command.itemId()));
    orderRepository.save(order);
}
```

### 관계

```java
// Aggregate Root defines what must stay consistent.
// Unit of Work defines when the change set is committed.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Aggregate만 생각 | 도메인 일관성이 선명하다 | 저장 타이밍은 별도로 필요하다 | 도메인 설계 |
| Unit of Work만 생각 | 트랜잭션이 단순해진다 | 도메인 경계가 흐려진다 | persistence 설계 |
| 둘을 함께 사용 | 경계와 커밋이 분리된다 | 개념을 혼동하기 쉽다 | DDD 스타일 backend |

판단 기준은 다음과 같다.

- 일관성 규칙은 Aggregate Root
- 저장 시점과 변경 추적은 Unit of Work
- 둘을 같은 레이어에 놓지 않는다

---

## 꼬리질문

> Q: Aggregate Root와 Unit of Work를 왜 구분해야 하나요?
> 의도: 도메인 경계와 persistence 경계를 혼동하지 않는지 확인한다.
> 핵심: 하나는 규칙, 다른 하나는 커밋이다.

> Q: Aggregate Root 안에 저장 로직이 들어가면 안 되나요?
> 의도: 관심사 분리를 아는지 확인한다.
> 핵심: 저장은 persistence 계층 책임이다.

> Q: Unit of Work가 없으면 Aggregate가 깨지나요?
> 의도: 트랜잭션 관리의 필요성을 보는지 확인한다.
> 핵심: Aggregate는 남지만 변경 반영이 흩어진다.

## 한 줄 정리

Aggregate Root는 도메인 일관성 경계이고, Unit of Work는 그 변경을 하나의 트랜잭션으로 묶는 메커니즘이다.
