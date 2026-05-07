---
schema_version: 3
title: Reference Other Aggregates by ID
concept_id: design-pattern/aggregate-reference-by-id
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- aggregate-id-reference
- object-graph-leakage
- orm-association-boundary
aliases:
- reference other aggregates by id
- aggregate id reference
- foreign aggregate reference
- cross aggregate navigation
- object graph leakage
- lazy loading trap
- aggregate snapshot
- 다른 aggregate id 참조
- 애그리거트 ID 참조
symptoms:
- Order가 Member나 Product aggregate 객체를 직접 필드로 가져 object graph 탐색과 일관성 경계가 함께 커진다
- JPA 연관관계가 곧 aggregate boundary라고 생각해 cascade와 lazy loading이 도메인 규칙처럼 번진다
- 주문 시점 상품명이나 가격처럼 과거 시점 의미가 필요한 값을 live reference로 매번 따라간다
intents:
- troubleshooting
- design
- comparison
prerequisites:
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/aggregate-root-vs-unit-of-work
- design-pattern/repository-boundary-aggregate-vs-read-model
next_docs:
- design-pattern/aggregate-invariant-guard-pattern
- design-pattern/repository-pattern-vs-antipattern
- design-pattern/cqrs-command-query-separation-pattern-language
linked_paths:
- contents/design-pattern/aggregate-boundary-vs-transaction-boundary.md
- contents/design-pattern/aggregate-root-vs-unit-of-work.md
- contents/design-pattern/aggregate-invariant-guard-pattern.md
- contents/design-pattern/repository-boundary-aggregate-vs-read-model.md
- contents/design-pattern/repository-pattern-vs-antipattern.md
confusable_with:
- design-pattern/repository-boundary-aggregate-vs-read-model
- design-pattern/aggregate-root-vs-unit-of-work
- design-pattern/aggregate-boundary-vs-transaction-boundary
- design-pattern/cqrs-command-query-separation-pattern-language
forbidden_neighbors: []
expected_queries:
- 다른 aggregate는 객체 참조보다 ID로 참조하라는 DDD 기본값은 왜 필요해?
- JPA 연관관계와 aggregate boundary를 같은 것으로 보면 어떤 lazy loading 문제가 생겨?
- Order가 Product 전체가 아니라 productId와 주문 시점 snapshot을 저장하는 이유가 뭐야?
- aggregate 간 객체 graph 탐색이 편해 보여도 일관성 경계가 흐려지는 이유가 뭐야?
- 다른 aggregate 정보가 필요할 때 application service 조회와 snapshot 중 무엇을 선택해?
contextual_chunk_prefix: |
  이 문서는 Reference Other Aggregates by ID playbook으로, 다른 aggregate를
  live object graph로 붙이지 않고 ID와 필요한 snapshot으로 참조해 consistency
  boundary, loading cost, ORM association leakage를 통제하는 기준을 설명한다.
---
# Reference Other Aggregates by ID

> 한 줄 요약: 다른 aggregate를 직접 객체 참조로 물고 가지 말고 ID나 snapshot으로 참조하면, 일관성 경계와 로딩 비용이 함께 커지는 일을 막을 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Boundary vs Transaction Boundary](./aggregate-boundary-vs-transaction-boundary.md)
> - [Aggregate Root vs Unit of Work](./aggregate-root-vs-unit-of-work.md)
> - [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md)
> - [Transaction Script vs Rich Domain Model](./transaction-script-vs-rich-domain-model.md)

---

## 핵심 개념

DDD에서 aggregate는 즉시 일관성의 최소 경계다.  
그래서 다른 aggregate를 직접 객체로 물고 들어가면 경계가 흐려지기 쉽다.

- `Order`가 `Member` 엔티티 객체를 직접 가진다
- `Payment`가 `Order` 전체를 필드로 가진다
- ORM 연관관계가 곧 도메인 경계라고 착각한다

이때 흔히 생기는 문제는 두 가지다.

- 변경 범위가 커지며 aggregate 경계가 실질적으로 합쳐진다
- lazy loading과 object graph 탐색이 유스케이스 경계를 흐린다

그래서 DDD 실무에서는 보통 **다른 aggregate는 ID로 참조한다**는 기본값을 둔다.

### Retrieval Anchors

- `reference other aggregates by id`
- `aggregate id reference`
- `foreign aggregate reference`
- `cross aggregate navigation`
- `object graph leakage`
- `lazy loading trap`
- `repository boundary`

---

## 깊이 들어가기

### 1. 객체 참조는 모델을 편하게 보이게 하지만 경계를 숨긴다

`Order.member.grade()`처럼 탐색이 자연스러워 보이면 설계가 좋아진 것 같지만, 실제로는 경계가 감춰질 수 있다.

- 어느 시점에 로딩이 일어나는지 불명확하다
- 다른 aggregate의 상태에 무심코 의존하게 된다
- 트랜잭션이 길어질수록 object graph가 커진다

즉 "탐색하기 쉽다"가 "경계가 맞다"를 보장하지 않는다.

### 2. ID 참조는 일관성의 소유권을 분명하게 만든다

다른 aggregate를 ID로만 들고 있으면 다음이 선명해진다.

- 지금 aggregate가 어떤 규칙까지 책임지는가
- 다른 aggregate 조회가 정말 필요한가
- 유스케이스가 두 aggregate를 함께 조율하는가

이건 단순한 스타일 취향이 아니라 **도메인 소유권을 드러내는 신호**다.

### 3. 다른 aggregate 정보가 필요하면 두 가지로 푼다

보통 선택지는 다음 둘이다.

- application service가 다른 aggregate를 별도 조회해 둘을 조율한다
- 필요한 정보만 snapshot/value object 형태로 복사해 둔다

예를 들어 주문 시점의 상품명과 가격은 `Product` aggregate를 매번 따라가기보다 `OrderLine`에 snapshot으로 고정하는 편이 더 자연스럽다.

### 4. ORM 연관관계는 persistence 편의이지 도메인 규칙이 아니다

JPA 같은 ORM은 연관관계를 쉽게 만든다.  
하지만 다음을 자동으로 보장해주지 않는다.

- aggregate boundary
- transaction boundary
- consistency ownership

오히려 cascade, bidirectional association, lazy loading이 합쳐지면 "어디까지 한 번에 저장되는가"가 흐려지기 쉽다.

### 5. 예외가 없는 원칙은 아니지만, 예외는 비싼 선택이다

다음 경우에는 예외를 검토할 수 있다.

- 같은 shared kernel 안에서 매우 작은 값 객체를 공유한다
- read model이나 projection에서는 탐색형 graph가 더 자연스럽다
- 강한 동시 일관성이 정말 하나의 경계여야 한다

하지만 이때도 먼저 질문해야 한다.

- 이게 진짜 aggregate 하나인가
- 아니면 ORM 편의 때문에 객체 참조를 붙이는가

---

## 실전 시나리오

### 시나리오 1: 주문과 회원

`Order`는 `Member` 객체 전체보다 `MemberId`를 가지는 편이 안전하다.  
회원 등급이 필요하면 주문 시점 snapshot을 저장하거나 application service가 별도로 조회해 정책 판단에 사용한다.

### 시나리오 2: 결제와 주문

`Payment`가 `Order` aggregate를 직접 참조하면 상태 전이 책임이 섞인다.  
보통은 `orderId`만 저장하고, 승인/취소 흐름은 이벤트나 command로 연결한다.

### 시나리오 3: 상품 정보 표시

주문 상세에 상품명이 필요하다고 해서 `OrderLine -> Product` live reference를 두면 안 된다.  
주문 시점 이름, 가격, 옵션을 snapshot으로 보존하는 편이 더 도메인 친화적이다.

---

## 코드로 보기

### 경계를 흐리는 객체 참조

```java
public class Order {
    private Member member;
    private final List<Product> products = new ArrayList<>();
}
```

이 구조는 주문 aggregate가 회원과 상품의 현재 상태에 쉽게 의존하게 만든다.

### ID와 snapshot을 쓰는 방식

```java
public class Order {
    private MemberId memberId;
    private final List<OrderLine> lines = new ArrayList<>();

    public void addLine(ProductId productId, String productName, Money price, int quantity) {
        lines.add(new OrderLine(productId, productName, price, quantity));
    }
}
```

### Application service가 조율

```java
@Transactional
public void placeOrder(PlaceOrderCommand command) {
    Member member = memberRepository.findById(command.memberId()).orElseThrow();
    Product product = productRepository.findById(command.productId()).orElseThrow();

    Order order = Order.place(member.id());
    order.addLine(product.id(), product.name(), product.currentPrice(), command.quantity());
    orderRepository.save(order);
}
```

Aggregate는 자기 경계를 지키고, 여러 aggregate를 함께 읽는 책임은 application layer가 맡는다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 객체 참조로 직접 연결 | 코드 탐색이 편해 보인다 | 경계가 흐려지고 lazy loading 문제가 생긴다 | 보통 aggregate 간에는 피한다 |
| ID 참조 | 경계와 소유권이 선명하다 | 조율 코드가 application layer에 필요하다 | aggregate 간 기본값 |
| ID + snapshot | 기록 시점 의미가 선명하다 | snapshot 갱신 전략을 설계해야 한다 | 주문 가격, 상품명처럼 시점 정보가 중요할 때 |

판단 기준은 다음과 같다.

- 다른 aggregate의 "현재 값"이 아니라 "식별자"를 기본값으로 가진다
- 과거 시점 의미가 중요하면 snapshot을 둔다
- 객체 그래프 탐색이 편하다는 이유만으로 aggregate 경계를 넓히지 않는다

---

## 꼬리질문

> Q: JPA 연관관계가 있는데 왜 ID로 다시 들고 가나요?
> 의도: ORM 편의와 도메인 경계를 구분하는지 본다.
> 핵심: 연관관계는 persistence 편의일 뿐이고, aggregate 경계는 도메인 규칙으로 결정해야 한다.

> Q: 다른 aggregate 정보를 쓰려면 매번 조회해야 하나요?
> 의도: application service 조율과 snapshot 전략을 아는지 본다.
> 핵심: 필요하면 조회하고, 자주 필요한 과거 시점 정보는 snapshot으로 저장한다.

> Q: 객체 참조가 절대 금지인가요?
> 의도: 규칙을 교조적으로 이해하지 않는지 본다.
> 핵심: 아니다. 하지만 예외는 비싸고, 기본값은 ID 참조가 더 안전하다.

## 한 줄 정리

다른 aggregate는 객체 그래프로 붙이기보다 ID와 snapshot으로 참조하는 편이 경계, 일관성, 로딩 비용을 함께 통제하기 쉽다.
