# Transaction Script vs Rich Domain Model

> 한 줄 요약: Transaction Script는 유스케이스 흐름을 절차적으로 조립하는 데 강하고, Rich Domain Model은 복잡한 상태 전이와 불변식을 모델 안에 가둬 둘 때 강하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Boundary vs Transaction Boundary](./aggregate-boundary-vs-transaction-boundary.md)
> - [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)
> - [Invariant-Preserving Command Model](./invariant-preserving-command-model.md)
> - [Domain Service vs Pattern Abuse](./domain-service-vs-pattern-abuse.md)
> - [Policy Object Pattern](./policy-object-pattern.md)
> - [Layered Validation Pattern](./layered-validation-pattern.md)

---

## 핵심 개념

실무에서 많은 팀이 DDD를 도입한다고 말하지만, 실제 코드베이스를 보면 두 스타일이 섞여 있다.

- Transaction Script: 서비스 메서드가 조회, 검증, 계산, 저장을 순서대로 진행한다
- Rich Domain Model: 엔티티와 값 객체가 상태 전이와 도메인 규칙을 스스로 보호한다

문제는 어느 한쪽이 "항상 더 좋다"가 아니라는 점이다.  
복잡하지 않은 CRUD를 억지로 rich model로 만들면 ceremony만 늘고, 반대로 복잡한 주문/결제/정산 흐름을 transaction script로만 밀어붙이면 규칙이 서비스 계층으로 새어 나온다.

### Retrieval Anchors

- `transaction script`
- `rich domain model`
- `anemic domain model`
- `behavior rich aggregate`
- `service layer orchestration`
- `domain complexity threshold`
- `patch vs command model`

---

## 깊이 들어가기

### 1. Transaction Script는 흐름이 중심이다

Transaction Script는 "이번 요청에서 어떤 순서로 무엇을 할 것인가"가 중심이다.

- 입력 검증
- 엔티티 조회
- 계산
- 저장
- 외부 호출

장점은 단순함이다.  
도메인 복잡도가 낮고 상태 전이가 거의 없으면 이 방식이 가장 읽기 쉽다.

하지만 규칙이 늘기 시작하면 서비스 메서드가 빠르게 비대해진다.

- 같은 검증이 여러 메서드에 중복된다
- 상태 전이 규칙이 `if` 문으로 흩어진다
- "어디가 진짜 규칙의 소유자인가"가 흐려진다

### 2. Rich Domain Model은 불변식이 중심이다

Rich Domain Model은 객체가 자기 상태를 바꾸는 규칙을 내부에 가진다.

- 어떤 상태에서 어떤 전이가 가능한가
- 총합, 한도, 수량 같은 규칙을 누가 보장하는가
- 외부가 내부 컬렉션을 직접 건드릴 수 있는가

이 스타일은 특히 다음에서 강하다.

- 상태 전이가 많다
- 잘못된 중간 상태가 위험하다
- 같은 규칙을 여러 유스케이스가 공유한다

즉 "절차"보다 "도메인 규칙"이 오래 남는 문제에서 가치가 커진다.

### 3. Rich Model을 만든다고 서비스가 사라지는 건 아니다

많은 팀이 여기서 극단으로 간다.

- Transaction Script에 지쳐 모든 로직을 엔티티에 넣는다
- 그 결과 엔티티가 저장소 조회, 외부 API 호출까지 떠안는다

하지만 rich model의 핵심은 "모든 로직을 객체에 넣는다"가 아니다.

- 도메인 규칙은 aggregate, value object, policy에 둔다
- 유스케이스 흐름 조립은 application service가 맡는다
- 저장과 외부 연동은 repository와 adapter가 맡는다

즉 서비스가 줄어드는 건 맞지만, 사라지는 건 아니다.

### 4. 둘 중 하나만 선택해야 하는 것도 아니다

실제 시스템은 스타일이 섞이는 경우가 많다.

- 관리자 설정 화면, 코드 테이블 관리: transaction script가 충분하다
- 주문, 결제, 환불, 정산: rich model이 더 안전하다
- 조회 모델, 리포트, 배치 정산 집계: read model 중심 절차형이 더 낫다

Senior 판단은 "DDD를 썼는가"보다 **어디에 불변식과 변경 비용이 집중되는가**를 보는 데 있다.

### 5. 전환 시점은 도메인 복잡도가 알려준다

다음 신호가 보이면 transaction script를 계속 유지하는 비용이 커진다.

- 같은 상태 검증이 여러 서비스 메서드에 반복된다
- 한 상태 변경에 연쇄 검증이 붙는다
- 잘못된 업데이트를 막기 위한 서비스 단 테스트가 폭증한다
- 서비스가 엔티티 내부 필드를 직접 조작한다

반대로 다음 신호면 rich model이 과할 수 있다.

- 대부분이 단순 CRUD다
- 상태 전이가 거의 없다
- 규칙 변화보다 화면/입출력 변화가 더 잦다
- 객체를 풍성하게 만들어도 행동이 거의 없다

---

## 실전 시나리오

### 시나리오 1: 관리자 공지 관리

공지 작성, 수정, 노출 여부 변경 정도라면 transaction script가 자연스럽다.  
복잡한 aggregate를 만들 필요가 없다.

### 시나리오 2: 주문 취소와 환불

취소 가능 상태, 환불 수수료, 부분 취소, 배송 시작 이후 제한이 붙기 시작하면 rich domain model이 유리하다.  
같은 규칙을 여러 서비스가 반복 검증하면 금방 누수가 생긴다.

### 시나리오 3: 정산 마감 배치

정산 대상 집계, 파일 생성, 전송, 마감 기록은 절차형 흐름이 더 읽기 쉽다.  
모든 배치 단계를 aggregate 행동으로 모델링하려 들면 오히려 복잡해진다.

---

## 코드로 보기

### Transaction Script 스타일

```java
@Transactional
public void cancelOrder(Long orderId, CancelReason reason) {
    Order order = orderRepository.findById(orderId).orElseThrow();

    if (order.getStatus() == OrderStatus.SHIPPED) {
        throw new IllegalStateException("already shipped");
    }
    if (order.getStatus() == OrderStatus.CANCELLED) {
        throw new IllegalStateException("already cancelled");
    }

    order.setStatus(OrderStatus.CANCELLED);
    refundPort.refund(order.getPaymentId(), reason);
}
```

흐름은 단순하지만 규칙이 서비스 계층에 있다.

### Rich Domain Model 스타일

```java
@Transactional
public void cancelOrder(Long orderId, CancelReason reason) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.cancel(reason, refundPolicy);
    refundPort.refund(order.paymentId(), reason);
}
```

```java
public class Order {
    private OrderStatus status;

    public void cancel(CancelReason reason, RefundPolicy refundPolicy) {
        if (status == OrderStatus.SHIPPED) {
            throw new IllegalStateException("already shipped");
        }
        if (status == OrderStatus.CANCELLED) {
            throw new IllegalStateException("already cancelled");
        }
        refundPolicy.validate(this, reason);
        status = OrderStatus.CANCELLED;
    }
}
```

상태 전이 규칙이 aggregate 안으로 모인다.

### 혼합 전략

```java
// Command side는 rich domain model,
// query/report/batch side는 transaction script에 가까운 절차형으로 가져가는 경우가 많다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Transaction Script | 읽기 쉽고 빠르게 만든다 | 규칙이 흩어지기 쉽다 | CRUD, 낮은 상태 복잡도 |
| Rich Domain Model | 불변식과 상태 전이를 보호한다 | 설계와 학습 비용이 크다 | 주문/결제/정산처럼 규칙이 복잡할 때 |
| 혼합 전략 | 복잡도에 맞게 투자한다 | 스타일 일관성 관리가 필요하다 | 시스템 안에 단순/복잡 도메인이 함께 있을 때 |

판단 기준은 다음과 같다.

- 상태 전이와 규칙 재사용이 많으면 rich model
- 화면 조립과 데이터 이동이 대부분이면 transaction script
- 전체 시스템에 하나의 스타일을 강요하지 않는다

---

## 꼬리질문

> Q: Transaction Script를 쓰면 무조건 Anemic Domain Model인가요?
> 의도: 구현 스타일과 모델 품질을 기계적으로 동일시하지 않는지 본다.
> 핵심: 아니다. 다만 복잡한 규칙이 서비스 계층으로 과도하게 새면 anemic smell이 강해진다.

> Q: Rich Domain Model이면 서비스 계층이 필요 없나요?
> 의도: 규칙과 유스케이스 조립을 구분하는지 본다.
> 핵심: 아니다. 흐름 조립, 트랜잭션, 외부 연동은 여전히 서비스가 맡는다.

> Q: 언제 전환을 고려해야 하나요?
> 의도: 도입 시점에 대한 감각을 보는 질문이다.
> 핵심: 검증 중복, 상태 전이 폭증, 서비스 비대화가 반복되면 전환 신호다.

## 한 줄 정리

Transaction Script는 절차가 단순한 문제에 강하고, Rich Domain Model은 상태 전이와 불변식이 핵심인 문제에서 더 오래 버틴다.
