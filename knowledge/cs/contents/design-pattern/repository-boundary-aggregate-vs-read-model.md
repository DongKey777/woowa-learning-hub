---
schema_version: 3
title: Repository Boundary: Aggregate Persistence vs Read Model
concept_id: design-pattern/repository-boundary-aggregate-vs-read-model
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- repository-boundary
- aggregate-persistence
- read-model-separation
aliases:
- repository boundary
- aggregate persistence boundary
- read model boundary
- cross aggregate query
- repository remote call anti pattern
- application orchestration
- read repository
- query service boundary
- aggregate 저장소 경계
- 조회 모델 분리
symptoms:
- aggregate repository가 화면 DTO, 원격 결제 상태, 배송 추적까지 조합해 persistence와 orchestration 책임이 섞인다
- 읽기 요구가 복잡해졌다는 이유로 repository 메서드가 dashboard/search/report 형태로 폭증한다
- command side aggregate persistence와 read model/query service 계약을 같은 repository에 모두 밀어 넣는다
intents:
- comparison
- troubleshooting
- design
prerequisites:
- design-pattern/repository-pattern-vs-antipattern
- design-pattern/aggregate-root-vs-unit-of-work
- design-pattern/aggregate-reference-by-id
next_docs:
- design-pattern/cqrs-command-query-separation-pattern-language
- design-pattern/read-model-staleness-read-your-writes
- design-pattern/specification-vs-query-service-boundary
linked_paths:
- contents/design-pattern/repository-pattern-vs-antipattern.md
- contents/design-pattern/aggregate-root-vs-unit-of-work.md
- contents/design-pattern/aggregate-reference-by-id.md
- contents/design-pattern/cqrs-command-query-separation-pattern-language.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/design-pattern/specification-vs-query-service-boundary.md
- contents/design-pattern/query-object-search-criteria-pattern.md
confusable_with:
- design-pattern/repository-pattern-vs-antipattern
- design-pattern/specification-vs-query-service-boundary
- design-pattern/cqrs-command-query-separation-pattern-language
- design-pattern/query-object-search-criteria-pattern
forbidden_neighbors: []
expected_queries:
- Repository boundary는 aggregate persistence와 read model/query service를 어떻게 나눠야 해?
- OrderRepository가 화면 DTO와 결제 배송 원격 조회까지 맡으면 왜 anti-pattern이 돼?
- 같은 DB를 써도 command repository와 read repository를 계약상 분리할 수 있는 이유가 뭐야?
- 복잡한 검색 조건이 늘어나면 repository를 키우지 말고 query service로 빼야 하는 신호는 뭐야?
- aggregate repository에서 join을 전혀 하지 말라는 뜻이 아니라 계약 의도가 중요하다는 말은 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Repository Boundary chooser로, command side repository는 aggregate
  persistence와 restore/save 계약에 집중하고 화면 조합, 검색, 집계, remote orchestration은
  read model, query service, application orchestration으로 분리하는 기준을 설명한다.
---
# Repository Boundary: Aggregate Persistence vs Read Model

> 한 줄 요약: Repository boundary를 aggregate persistence에 맞춰 두면 도메인 경계가 선명해지고, 검색/조인/원격 조회는 query model이나 application orchestration으로 분리할 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md)
> - [Aggregate Root vs Unit of Work](./aggregate-root-vs-unit-of-work.md)
> - [Reference Other Aggregates by ID](./aggregate-reference-by-id.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Specification vs Query Service Boundary](./specification-vs-query-service-boundary.md)
> - [Query Object and Search Criteria Pattern](./query-object-search-criteria-pattern.md)
> - [Transaction Script vs Rich Domain Model](./transaction-script-vs-rich-domain-model.md)
> - [Database: Transaction Boundary, Isolation, and Locking Decision Framework](../database/transaction-boundary-isolation-locking-decision-framework.md)
> - [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)

---

## 핵심 개념

Repository를 쓰기 시작하면 많은 팀이 곧 이런 질문으로 간다.

- 여기서 다른 aggregate까지 join해서 읽어도 되나
- 외부 서비스 조회도 repository 안에 넣어도 되나
- 화면용 DTO를 repository가 바로 만들어도 되나

이 질문의 핵심은 "Repository가 무엇을 저장하는가"가 아니라 **Repository가 어디까지 책임지는가**다.

DDD 기준에서 repository의 기본 경계는 보통 다음에 가깝다.

- aggregate를 로드한다
- aggregate를 저장한다
- aggregate 식별자와 도메인 언어를 중심으로 말한다

반대로 다음은 repository 바깥 책임인 경우가 많다.

- 복잡한 검색과 화면 조합
- 다른 bounded context의 원격 조회
- cross-aggregate orchestration

### Retrieval Anchors

- `repository boundary`
- `aggregate persistence boundary`
- `read model boundary`
- `cross aggregate query`
- `repository remote call anti pattern`
- `application orchestration`
- `read your writes`
- `projection lag`
- `specification vs query service`

---

## 깊이 들어가기

### 1. Repository는 aggregate 경계를 반영해야 한다

Repository가 aggregate보다 더 넓게 생각되면 곧 경계가 흐려진다.

- `OrderRepository`가 주문뿐 아니라 결제, 회원, 배송 join을 모두 떠안는다
- `MemberRepository`가 추천 점수, CRM 상태, 외부 등급 API까지 섞어 읽는다

이런 구조에서는 "무엇이 한 번에 일관되게 바뀌는가"보다 "어떤 화면에 뭐가 필요한가"가 저장 모델을 끌고 가기 시작한다.

Repository는 보통 aggregate root 단위로 생각하는 편이 안전하다.

### 2. 읽기 최적화는 Repository boundary를 넓히라는 뜻이 아니다

실무에서 가장 흔한 혼동은 이거다.

- 읽기 요구가 복잡해짐
- repository 메서드가 급격히 늘어남
- 결국 저장소가 화면 조립기처럼 변함

하지만 읽기 요구가 복잡해졌다는 건 보통 두 가능성 중 하나다.

- query model이 필요하다
- application service가 여러 소스를 조율해야 한다

즉 읽기 복잡도는 CQRS/read model 분리 신호이지, repository 비대화 허가증이 아니다.

### 3. 원격 호출을 repository에 넣으면 persistence와 orchestration이 섞인다

`OrderRepository.loadRichOrder()`가 DB 조회 후 원격 결제 상태와 물류 상태를 합쳐 반환한다면 겉보기에는 편해 보일 수 있다.

하지만 실제로는 다음 문제가 생긴다.

- repository 실패 원인이 DB인지 네트워크인지 불명확하다
- transaction boundary와 원격 호출 boundary가 섞인다
- 테스트에서 repository 더블이 지나치게 복잡해진다

Repository는 persistence abstraction이고, 원격 연동은 port/adapter나 application service orchestration에 더 가깝다.

### 4. 저장용 repository와 조회용 read repository를 구분하면 말이 선명해진다

보통 다음 식의 구분이 도움이 된다.

- `OrderRepository`: aggregate 저장/복원
- `OrderReadRepository` 또는 `OrderQueryService`: 검색/목록/집계/화면 조합

이 구분은 구현 기술이 달라도 유지할 수 있다.

- 같은 DB를 써도 된다
- 같은 스키마를 조회해도 된다
- 중요한 건 계약과 책임 분리다

### 5. repository 메서드가 business sentence를 잃기 시작하면 경계를 다시 봐야 한다

경계가 흐려지는 신호는 보통 이름에서 먼저 드러난다.

- `findDashboardDataByPeriodAndStatusAndTeam`
- `loadOrderWithPaymentShippingCouponMember`
- `findSomethingAndTransformToResponse`

이쯤 되면 repository가 aggregate persistence보다 query/report/orchestration 쪽 책임을 빨아들이고 있을 가능성이 크다.

---

## 실전 시나리오

### 시나리오 1: 주문 상세 화면

화면에는 주문, 결제, 배송, 쿠폰 정보가 모두 필요할 수 있다.  
그렇다고 `OrderRepository`가 모든 join과 외부 조회를 떠안는 건 좋은 기본값이 아니다.

더 안전한 선택지는 다음 중 하나다.

- `OrderQueryService`가 여러 read source를 조합
- projection/read model을 미리 구성

### 시나리오 2: 주문 취소 유스케이스

취소 command는 보통 `Order` aggregate만 로드하면 된다.  
환불 가능 여부 판단에 추가 정보가 필요하면 application service가 별도 port를 통해 조회하거나 policy 입력으로 전달한다.

### 시나리오 3: 관리자 검색

관리자 검색은 상태, 기간, 회원 등급, 결제 수단별로 필터링될 수 있다.  
이건 aggregate repository보다 검색 전용 read repository가 더 자연스럽다.

---

## 코드로 보기

### aggregate repository

```java
public interface OrderRepository {
    Optional<Order> findById(OrderId orderId);
    void save(Order order);
}
```

### read model repository

```java
public interface OrderReadRepository {
    List<OrderDetailView> search(OrderSearchCondition condition);
}
```

### application orchestration

```java
@Transactional
public void cancel(CancelOrderCommand command) {
    Order order = orderRepository.findById(command.orderId()).orElseThrow();
    PaymentSnapshot payment = paymentQueryPort.findByOrderId(command.orderId());

    order.cancel(command.reason(), refundPolicy.forPayment(payment));
    orderRepository.save(order);
}
```

### boundary smell

```java
public interface OrderRepository {
    OrderScreenResponse loadOrderScreen(Long orderId);
    PaymentProviderStatus fetchRemotePayment(Long orderId);
    ShippingTrackingResponse trackShipment(Long orderId);
}
```

이건 persistence abstraction보다 화면 조립과 원격 orchestration에 가깝다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Aggregate repository | 도메인 경계가 선명하다 | 복잡한 조회는 별도 구조가 필요하다 | command side 저장/복원 |
| Repository에 조회까지 몰기 | 처음엔 빠르다 | 경계가 흐려지고 메서드가 폭증한다 | 짧은 수명 프로토타입 정도 |
| Read repository / query service 분리 | 화면/검색 요구를 잘 수용한다 | 구조가 늘어난다 | 조회 조건과 조합이 복잡할 때 |

판단 기준은 다음과 같다.

- aggregate를 복원/저장하는 책임이면 repository
- 화면 조합, 검색, 집계가 중심이면 read model
- 원격 조회가 섞이면 repository boundary를 다시 본다

---

## 꼬리질문

> Q: 같은 DB를 쓰면 repository와 read repository를 굳이 나눠야 하나요?
> 의도: 물리 저장소와 책임 경계를 구분하는지 본다.
> 핵심: 나눌 수 있다. 핵심은 DB 개수가 아니라 계약의 의도다.

> Q: aggregate 조회 시 join을 전혀 하면 안 되나요?
> 의도: 구현 디테일과 설계 경계를 교조적으로 보지 않는지 확인한다.
> 핵심: 구현상 join은 가능하지만, 계약이 aggregate persistence인지 화면 조립인지가 더 중요하다.

> Q: repository 안에서 외부 API를 부르면 왜 안 좋나요?
> 의도: persistence와 orchestration 혼합 문제를 이해하는지 본다.
> 핵심: 실패 원인, 트랜잭션 경계, 테스트 복잡도가 한 번에 섞이기 때문이다.

## 한 줄 정리

Repository boundary를 aggregate persistence에 고정하면 저장 모델과 조회 모델, 원격 orchestration을 더 건강하게 분리할 수 있다.
