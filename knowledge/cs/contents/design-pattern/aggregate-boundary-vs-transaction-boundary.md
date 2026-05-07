---
schema_version: 3
title: Aggregate Boundary vs Transaction Boundary
concept_id: design-pattern/aggregate-boundary-vs-transaction-boundary
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- aggregate-boundary
- transaction-boundary
- ddd-consistency-boundary
aliases:
- aggregate boundary vs transaction boundary
- aggregate boundary
- transaction boundary
- one aggregate per transaction
- cross aggregate invariant
- immediate consistency boundary
- saga local transaction
- aggregate와 transaction 경계
- 애그리거트 경계 트랜잭션 경계
symptoms:
- 한 번에 commit해야 한다는 이유만으로 여러 도메인 객체를 거대 aggregate로 합친다
- aggregate boundary와 DB transaction boundary를 같은 개념으로 설명해 외부 API 호출까지 transaction 안에 넣는다
- cross-aggregate invariant를 saga, reservation, outbox 같은 프로세스 설계 없이 rollback으로만 해결하려 한다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- design-pattern/aggregate-root-vs-unit-of-work
- design-pattern/unit-of-work-pattern
- design-pattern/domain-events-vs-integration-events
next_docs:
- design-pattern/aggregate-invariant-guard-pattern
- design-pattern/aggregate-reference-by-id
- design-pattern/saga-coordinator-pattern-language
linked_paths:
- contents/design-pattern/aggregate-root-vs-unit-of-work.md
- contents/design-pattern/unit-of-work-pattern.md
- contents/design-pattern/aggregate-invariant-guard-pattern.md
- contents/design-pattern/aggregate-reference-by-id.md
- contents/design-pattern/domain-events-vs-integration-events.md
- contents/design-pattern/saga-coordinator-pattern-language.md
confusable_with:
- design-pattern/aggregate-root-vs-unit-of-work
- design-pattern/unit-of-work-pattern
- design-pattern/saga-coordinator-pattern-language
- design-pattern/domain-events-vs-integration-events
forbidden_neighbors: []
expected_queries:
- Aggregate boundary와 transaction boundary는 즉시 일관성과 atomic commit 관점에서 어떻게 달라?
- 한 command가 한 aggregate를 한 local transaction으로 바꾸는 건 규칙이야 기본값이야?
- 같은 DB transaction에 outbox와 audit log가 들어가도 같은 aggregate가 아닌 이유가 뭐야?
- cross-aggregate invariant를 거대 aggregate나 긴 transaction 대신 saga로 풀어야 하는 경우는 언제야?
- 외부 결제 API 호출을 DB transaction 안에 넣으면 aggregate 설계가 왜 위험해져?
contextual_chunk_prefix: |
  이 문서는 Aggregate Boundary vs Transaction Boundary chooser로, aggregate는
  즉시 일관성을 지키는 도메인 경계이고 transaction은 이번 실행의 commit/rollback
  경계라는 차이를 설명하며, mega aggregate와 giant transaction을 피하는 기준을 다룬다.
---
# Aggregate Boundary vs Transaction Boundary

> 한 줄 요약: Aggregate boundary는 즉시 일관성을 지켜야 하는 도메인 경계이고, transaction boundary는 한 유스케이스에서 함께 commit/rollback할 작업 경계다. 둘을 같은 것으로 취급하면 거대 aggregate와 과도한 트랜잭션이 동시에 생긴다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Root vs Unit of Work](./aggregate-root-vs-unit-of-work.md)
> - [Unit of Work Pattern: 트랜잭션 경계 안에서 변경을 모으기](./unit-of-work-pattern.md)
> - [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)
> - [Reference Other Aggregates by ID](./aggregate-reference-by-id.md)
> - [Reservation, Hold, and Expiry as a Consistency Seam](./reservation-hold-expiry-consistency-seam.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)
> - [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)

---

## 핵심 개념

실무에서 Aggregate와 transaction은 자주 같은 문맥에 등장한다.  
그래서 많은 팀이 둘을 거의 같은 말처럼 쓰기 시작한다.

하지만 두 경계는 설계 이유부터 다르다.

- Aggregate boundary: 어떤 상태가 **항상 함께 유효해야 하는가**
- Transaction boundary: 어떤 작업이 **이번 실행에서 함께 반영되거나 함께 실패해야 하는가**

이 둘은 종종 정렬될 수 있다.  
예를 들어 "한 command가 한 aggregate를 수정하고 한 번 commit한다"는 설계는 매우 흔하다.

중요한 건 **자주 같이 움직인다는 사실과 개념적으로 동일하다는 주장은 다르다**는 점이다.

### Retrieval Anchors

- `aggregate boundary`
- `transaction boundary`
- `immediate consistency`
- `cross aggregate invariant`
- `aggregate invariant guard`
- `one aggregate per transaction`
- `saga local transaction`
- `domain event integration event`
- `reservation pattern`
- `consistency seam`

---

## 깊이 들어가기

### 1. Aggregate boundary는 불변식에서 나온다

Aggregate boundary는 persistence 편의가 아니라 **도메인 불변식의 최소 보호 범위**에서 결정된다.

- 어떤 메서드가 끝난 직후에도 반드시 참이어야 하는가
- 동시 수정이 들어와도 한 번에 검증해야 하는 규칙은 무엇인가
- 외부가 내부 객체를 직접 건드리지 못하게 막아야 하는 이유는 무엇인가

예를 들어 `Order` aggregate 안에서 다음 규칙은 즉시 일관성이 필요하다.

- 주문 총액은 주문 항목 합계와 일치해야 한다
- 이미 취소된 주문은 다시 결제 대기 상태로 갈 수 없다
- 배송 시작 후에는 주소 변경 규칙이 제한된다

이건 "한 DB transaction으로 처리하기 쉬운가"와는 별개다.  
aggregate는 **도메인 모델의 경계**다.

### 2. Transaction boundary는 실행 단위에서 나온다

Transaction boundary는 application service나 command handler가 정하는 **실행/실패 단위**다.

- 어떤 저장 작업을 함께 commit할 것인가
- 어떤 예외가 나면 전체를 rollback할 것인가
- 어떤 부수 효과를 outbox나 별도 단계로 밀어낼 것인가

같은 aggregate라도 use case마다 transaction 경계는 달라질 수 있다.

- 명령 처리: 읽고 바꾸고 저장하는 write transaction
- 조회 처리: read-only transaction
- 배치 처리: 여러 건을 chunk 단위 transaction으로 나눔

즉 transaction boundary는 **유스케이스와 운영 특성에 따라 흔들릴 수 있는 경계**다.  
반면 aggregate boundary는 도메인 규칙이 바뀌지 않는 한 더 안정적이다.

### 3. 둘을 conflation하면 왜 설계가 무너질까

가장 흔한 오해는 두 방향으로 나타난다.

#### 오해 A: "한 번에 commit해야 하니 한 aggregate로 묶자"

이 생각은 거대 aggregate를 만든다.

- 주문, 결제, 쿠폰, 포인트를 한 root에 집어넣는다
- 라이프사이클이 다른 객체가 한 잠금 경계를 공유한다
- 사소한 변경에도 전체를 로드하고 optimistic lock 충돌을 겪는다

결국 aggregate가 불변식을 보호하는 모델이 아니라 **트랜잭션을 억지로 담는 컨테이너**가 된다.

#### 오해 B: "다른 aggregate라도 무조건 한 transaction으로 묶어야 안전하다"

이 생각은 과도한 transaction을 만든다.

- 서비스 메서드 하나에서 여러 aggregate를 직접 변경한다
- 외부 API 호출까지 DB transaction 안에 넣는다
- 실패 보상 문제를 rollback으로 덮으려 한다

이 구조는 겉으로는 "안전해 보이지만" 실제로는 잠금 시간, 재시도 복잡도, 결합도를 함께 키운다.

### 4. Senior 관점의 기준은 질문이 다르다는 점이다

Aggregate boundary를 정할 때는 이렇게 묻는다.

- 이 규칙은 반드시 즉시 지켜져야 하는가
- 같은 root 안에서만 보호 가능한가
- 다른 aggregate와 eventual consistency로 풀면 안 되는가

Transaction boundary를 정할 때는 이렇게 묻는다.

- 이번 command에서 어디까지를 atomic하게 반영할 것인가
- 외부 연동은 local transaction 바깥으로 빼야 하는가
- outbox, idempotency key, audit log를 같은 commit에 넣어야 하는가

질문이 다르기 때문에 답도 다르다.  
그래서 한쪽 답을 다른 쪽에 복사하면 설계가 흐려진다.

### 5. "보통 한 transaction에 한 aggregate"는 규칙이 아니라 디폴트다

DDD 실무에서 자주 쓰는 안전한 기본값은 다음과 같다.

- 한 command는 보통 한 aggregate의 불변식을 바꾼다
- 그 변경은 하나의 local transaction으로 commit한다
- 다른 aggregate나 외부 시스템은 이벤트, 정책, saga로 잇는다

이 기본값이 좋은 이유는 **개념을 동일시해서가 아니라 충돌 면적을 줄이기 때문**이다.

다만 다음까지 같은 뜻은 아니다.

- 한 transaction에 들어간 모든 레코드가 같은 aggregate 소속이다
- 한 aggregate를 바꾸려면 항상 하나의 transaction만 존재한다
- 같은 DB에 있으면 같은 aggregate로 보는 게 맞다

예를 들어 한 transaction 안에 다음이 같이 들어갈 수 있다.

- `Order` aggregate 저장
- outbox 이벤트 저장
- idempotency key 기록
- 감사 로그 저장

이 보조 레코드들은 같은 commit 경계에 있을 수 있지만, 같은 aggregate는 아니다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성과 결제 승인

주문 생성과 결제 승인은 비즈니스상 밀접하지만 보통 같은 aggregate가 아니다.

- `Order`는 주문 상태와 주문 항목 불변식을 지킨다
- `Payment`는 승인/실패/취소 흐름과 정산 규칙을 지킨다

둘을 하나로 합치면 주문 모델이 결제 모델의 라이프사이클까지 떠안는다.  
둘을 한 transaction으로만 묶으려 하면 외부 PG 호출이 transaction 안으로 들어오게 된다.

더 안전한 구조는 다음에 가깝다.

- `Order`를 생성하고 `OrderPlaced`를 outbox와 함께 commit
- 결제는 다음 local transaction에서 승인 시도
- 실패 시 `Order` 상태를 보상 흐름으로 전환

### 시나리오 2: 재고 차감과 주문 확정

"재고까지 한 번에 줄어야 안전하지 않나?"라는 질문이 자주 나온다.

여기서 먼저 봐야 하는 것은 transaction이 아니라 **어떤 불변식이 정말 즉시 일관성을 요구하는가**다.

- 상품별 가용 재고는 `Inventory` aggregate의 규칙일 수 있다
- 주문의 상태 전이는 `Order` aggregate의 규칙일 수 있다

둘이 다른 이유가 분명하다면, 같은 DB를 쓴다는 이유만으로 같은 aggregate가 되지 않는다.
필요하면 예약, 만료, 보상, 재시도 전략을 설계해야 한다.

### 시나리오 3: 쿠폰 사용과 포인트 적립

한 checkout 흐름에서 쿠폰 차감과 포인트 적립이 같이 일어나더라도 둘의 일관성 요구 수준은 다를 수 있다.

- 쿠폰 중복 사용 방지는 즉시 일관성이 필요할 수 있다
- 포인트 적립은 짧은 지연 허용이 가능할 수 있다

모든 후속 작업을 한 transaction에 우겨 넣으면 checkout latency와 실패 면적만 커진다.

---

## 코드로 보기

### 경계를 혼동한 예시

```java
@Transactional
public void checkout(CheckoutCommand command) {
    Order order = orderRepository.findById(command.orderId()).orElseThrow();
    Coupon coupon = couponRepository.findById(command.couponId()).orElseThrow();

    order.applyCoupon(coupon);
    coupon.markUsedBy(order.getMemberId());

    paymentGateway.approve(command.paymentRequest());

    order.confirm();
}
```

문제는 세 가지다.

- 서로 다른 aggregate를 한 transaction에 강하게 묶는다
- 외부 결제 호출이 DB transaction 안에 들어간다
- 실패 모델이 rollback 의존적으로 바뀐다

### 경계를 분리한 예시

```java
@Transactional
public void placeOrder(CheckoutCommand command) {
    Order order = Order.place(command.lines(), command.memberId());
    order.applyCoupon(command.couponCode());

    orderRepository.save(order);
    outboxRepository.save(OrderPlacedEvent.from(order));
}
```

```java
@Transactional
public void confirmPayment(PaymentApproved event) {
    Order order = orderRepository.findById(event.orderId()).orElseThrow();
    order.markPaid(event.paymentId());
}
```

첫 transaction은 `Order` aggregate의 즉시 일관성을 지킨다.  
결제와 후속 처리는 별도 local transaction으로 연결한다.

### Aggregate 안에서 지켜야 할 것

```java
public class Order {
    private OrderStatus status;
    private Money totalAmount;

    public void applyCoupon(String couponCode) {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("pending order only");
        }
        // totalAmount recalculation
    }

    public void markPaid(String paymentId) {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("already finalized");
        }
        status = OrderStatus.PAID;
    }
}
```

Aggregate는 자기 불변식을 지키고, transaction orchestration은 바깥에서 조립하는 편이 안전하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Aggregate와 transaction을 동일시 | 설계가 단순해 보인다 | 거대 root, 긴 transaction, 외부 호출 결합이 생긴다 | 초기 실험 코드에서만 잠깐 |
| 한 command당 한 aggregate + 한 local transaction | 모델과 실행 단위가 명확하다 | 후속 흐름 분리가 필요하다 | 기본 선택지 |
| 여러 aggregate를 saga로 연결 | 경계가 선명하고 확장성이 좋다 | 보상/재시도 설계가 필요하다 | 강한 결합 없이 프로세스를 이어야 할 때 |

판단 기준은 다음과 같다.

- 즉시 일관성 질문은 aggregate로 푼다
- atomic commit 질문은 transaction으로 푼다
- 둘이 어긋나면 큰 transaction보다 process design을 먼저 본다

---

## 꼬리질문

> Q: 같은 DB transaction에 저장되면 같은 aggregate 아닌가요?
> 의도: commit 경계와 도메인 경계를 혼동하는지 확인한다.
> 핵심: 아니다. outbox, audit log, idempotency record는 같은 transaction에 들어가도 aggregate가 아니다.

> Q: 그럼 항상 aggregate 하나만 transaction에서 바꿔야 하나요?
> 의도: 실무 기본값과 절대 규칙을 구분하는지 확인한다.
> 핵심: 기본값으로는 좋지만 절대 법칙은 아니다. 다만 예외는 명확한 이유와 비용 인지가 필요하다.

> Q: cross-aggregate invariant가 있으면 어떻게 해야 하나요?
> 의도: 모든 문제를 mega-aggregate나 giant transaction으로 푸는지 확인한다.
> 핵심: 즉시 일관성이 정말 필요한지 다시 묻고, 필요하면 aggregate 재설계, 아니면 saga/policy/reservation 전략을 고려한다.

## 한 줄 정리

Aggregate boundary는 "무엇이 항상 함께 맞아야 하는가"를, transaction boundary는 "이번 실행에서 무엇을 함께 commit할 것인가"를 다룬다. 둘이 자주 정렬되더라도 같은 개념으로 취급하면 설계가 빠르게 비대해진다.
