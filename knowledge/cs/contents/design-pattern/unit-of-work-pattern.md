# Unit of Work Pattern: 트랜잭션 경계 안에서 변경을 모으기

> 한 줄 요약: Unit of Work 패턴은 여러 엔티티의 변경을 한 덩어리로 추적하고 커밋 시점에 한 번에 반영해, 일관된 트랜잭션 경계를 만든다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Unit of Work는 **한 트랜잭션에서 발생한 변경 사항을 추적하고, 커밋 시점에 일괄 반영하는 패턴**이다.  
데이터를 단순히 저장하는 게 아니라, 변경 집합을 관리하는 데 초점이 있다.

backend에서 이 패턴은 ORM, persistence context, dirty checking과 자주 연결된다.

- 어떤 엔티티가 새로 만들어졌는가
- 어떤 엔티티가 수정되었는가
- 어떤 엔티티가 삭제되었는가
- 언제 flush와 commit을 할 것인가

### Retrieval Anchors

- `unit of work pattern`
- `identity map`
- `dirty checking`
- `flush commit`
- `transaction boundary`

---

## 깊이 들어가기

### 1. 변경을 모으는 이유

개별 저장 호출이 많아지면 다음 문제가 생긴다.

- 중간 실패 시 일관성 깨짐
- 저장 순서가 중요해짐
- 같은 객체를 여러 번 조회하게 됨

Unit of Work는 이런 변경을 한 곳에 모아 처리한다.

### 2. Identity Map과 함께 움직인다

같은 트랜잭션 안에서는 같은 객체를 여러 번 조회해도 동일 인스턴스를 재사용하는 편이 유리하다.
이게 Identity Map의 감각이다.

### 3. JPA의 persistence context가 대표적이다

JPA를 사용하면 엔티티 매니저의 persistence context가 사실상 Unit of Work 역할을 한다.

- 더티 체크로 변경 감지
- flush 시점에 SQL 반영
- 트랜잭션 커밋과 함께 일관성 유지

---

## 실전 시나리오

### 시나리오 1: 주문 생성

주문, 주문 항목, 결제 기록이 하나의 트랜잭션 안에서 함께 저장되어야 한다.

### 시나리오 2: 관리자 일괄 수정

여러 엔티티를 수정한 뒤 한번에 커밋하면 저장 순서와 실패 처리를 단순화할 수 있다.

### 시나리오 3: 조회 후 수정 흐름

같은 요청 안에서 읽고 바꾸고 다시 저장하는 경우, 변경 추적이 없으면 코드가 지저분해진다.

---

## 코드로 보기

### 개념적 구현

```java
public class UnitOfWork {
    private final List<Object> newObjects = new ArrayList<>();
    private final List<Object> dirtyObjects = new ArrayList<>();
    private final List<Object> removedObjects = new ArrayList<>();

    public void registerNew(Object entity) {
        newObjects.add(entity);
    }

    public void registerDirty(Object entity) {
        dirtyObjects.add(entity);
    }

    public void registerRemoved(Object entity) {
        removedObjects.add(entity);
    }

    public void commit() {
        // 저장 순서에 맞게 반영
    }
}
```

### JPA 감각

```java
@Transactional
public void placeOrder(PlaceOrderCommand command) {
    Order order = Order.place(command);
    order.addItem(command.itemId());
    orderRepository.save(order);
    // commit 시점에 변경 반영
}
```

JPA에서는 `save()`가 즉시 DB 반영이라는 뜻이 아니라, 변경을 Unit of Work 안에 등록하는 감각에 가깝다.

### Dirty checking

```java
@Transactional
public void changeAddress(Long orderId, String address) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.changeAddress(address);
    // 엔티티 매니저가 변경을 감지
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 저장 | 단순하다 | 중간 실패에 약하다 | 아주 단순한 흐름 |
| Unit of Work | 변경이 일관되게 반영된다 | 트랜잭션 경계 이해가 필요하다 | 여러 엔티티를 함께 다룰 때 |
| 이벤트 소싱 | 변경 이력이 선명하다 | 학습/운영 비용이 크다 | 이력 자체가 핵심일 때 |

판단 기준은 다음과 같다.

- 한 요청에서 여러 엔티티를 함께 바꾸면 Unit of Work가 자연스럽다
- 읽기와 쓰기 경계가 커지면 CQRS와 함께 보자
- 저장 시점 제어가 중요하면 flush와 commit 차이를 이해해야 한다

---

## 꼬리질문

> Q: Unit of Work와 Repository는 어떻게 다른가요?
> 의도: 저장소와 변경 추적의 역할을 구분하는지 확인한다.
> 핵심: Repository는 조회/저장을 추상화하고, Unit of Work는 변경 집합을 관리한다.

> Q: JPA를 쓰면 Unit of Work를 직접 구현해야 하나요?
> 의도: ORM이 제공하는 기능과 직접 구현의 경계를 아는지 확인한다.
> 핵심: 보통은 아니다. 하지만 개념을 이해해야 트랜잭션을 제대로 다룰 수 있다.

> Q: Unit of Work가 없으면 어떤 문제가 생기나요?
> 의도: 변경 추적과 트랜잭션 경계의 중요성을 보는지 확인한다.
> 핵심: 저장 순서, 일관성, 중복 조회 문제가 커진다.

## 한 줄 정리

Unit of Work는 한 트랜잭션 안의 변경을 모아 관리해, 여러 엔티티를 일관된 경계에서 커밋하게 하는 패턴이다.

