# Aggregate Version and Optimistic Concurrency Pattern

> 한 줄 요약: aggregate에 version을 두고 optimistic concurrency를 적용하면 긴 잠금 없이 stale command를 감지할 수 있지만, 충돌 이후 재시도와 사용자 의미를 어디서 처리할지는 별도 패턴으로 설계해야 한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Aggregate Root vs Unit of Work](./aggregate-root-vs-unit-of-work.md)
> - [Aggregate Boundary vs Transaction Boundary](./aggregate-boundary-vs-transaction-boundary.md)
> - [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)
> - [Semantic Lock and Pending State Pattern](./semantic-lock-pending-state-pattern.md)
> - [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md)
> - [Command Handler Pattern](./command-handler-pattern.md)

---

## 핵심 개념

Aggregate를 나눴더라도 동시 수정 문제는 사라지지 않는다.  
여러 사용자가 같은 aggregate를 거의 동시에 바꾸면 다음 질문이 생긴다.

- 마지막 저장만 이기게 둘까
- 누가 먼저 바꿨는지 감지할까
- stale command는 자동 재시도할까, 사용자에게 다시 보여줄까

Optimistic concurrency는 이런 상황에서 **version check로 충돌을 감지하는 기본 패턴**이다.

- aggregate는 version을 가진다
- 로드 시 version을 함께 읽는다
- 저장 시 expected version과 현재 version이 맞는지 확인한다
- 다르면 stale write로 처리한다

### Retrieval Anchors

- `aggregate version`
- `optimistic concurrency`
- `stale command detection`
- `expected version`
- `lost update prevention`
- `optimistic locking aggregate`
- `semantic lock`

---

## 깊이 들어가기

### 1. optimistic concurrency는 lock-free가 아니라 short-lock에 가깝다

많은 팀이 optimistic concurrency를 "락이 없다"로 이해한다.  
실제로는 긴 잠금을 피하는 것이지, 충돌 가능성이 사라지는 건 아니다.

- 읽을 때는 자유롭다
- 쓸 때 version 비교로 충돌을 감지한다
- commit 순간에는 여전히 원자적 비교가 필요하다

즉 본질은 **stale update를 나중에 감지한다**는 점이다.

### 2. version은 persistence 기술보다 aggregate 의도와 연결되어야 한다

ORM이 `@Version`을 제공하더라도 설계 질문은 남는다.

- 어떤 변경이 같은 aggregate version을 올리는가
- 보조 레코드 수정도 충돌로 볼 것인가
- command가 stale이면 같은 재시도가 안전한가

즉 version은 단순 DB 컬럼이 아니라 aggregate 변경 의미와 연결된다.

### 3. 충돌 처리 정책은 유스케이스마다 달라진다

stale write를 감지했다고 해서 답이 하나는 아니다.

- 재고 예약: 즉시 재조회 후 다시 시도 가능
- 주문 수정: 사용자에게 최신 상태를 다시 보여주는 편이 낫다
- 관리자 메모: last-writer-wins도 허용 가능할 수 있다

따라서 optimistic concurrency는 detection 패턴이고, **resolution 패턴은 별도**다.

### 4. automatic retry는 domain safety를 먼저 따져야 한다

충돌이 났다고 무조건 재시도하면 안 된다.

- command가 멱등적인가
- 최신 상태에서 같은 의도가 여전히 유효한가
- 재시도로 side effect가 중복되지 않는가

예를 들어 "금액을 1000원으로 바꿔라"와 "현재 금액에 1000원을 더하라"는 retry 의미가 다르다.

### 5. read model과 UI는 version drift를 드러내는 편이 낫다

사용자 편집 화면에서 오래된 snapshot을 들고 수정했다면, 충돌을 감추기보다 최신 상태와 차이를 보여주는 UX가 더 안전하다.

- 최신 aggregate version 제공
- edit token 또는 etag 사용
- 충돌 시 diff 표시

즉 optimistic concurrency는 backend만의 문제가 아니라 read/write coordination 문제이기도 하다.

---

## 실전 시나리오

### 시나리오 1: 주소 수정과 주문 취소 경합

한 사용자는 주소를 수정하고, 다른 프로세스는 주문을 취소할 수 있다.  
취소 후 주소 수정은 더 이상 유효하지 않으므로 stale command로 거절하는 편이 낫다.

### 시나리오 2: 관리자 태그 편집

충돌해도 큰 의미 차이가 없으면 latest version을 다시 읽고 merge 또는 last-writer-wins를 허용할 수 있다.

### 시나리오 3: 재고 수량 조정

수량 차감은 충돌이 잦고 의미가 민감하므로, stale write 감지 후 최신 상태 기준 재평가가 필요할 수 있다.

---

## 코드로 보기

### aggregate version

```java
public class Order {
    private long version;
    private OrderStatus status;

    public long version() {
        return version;
    }

    public void changeAddress(Address newAddress) {
        if (status == OrderStatus.CANCELLED) {
            throw new IllegalStateException("cancelled order");
        }
        // address update
    }
}
```

### repository save with expected version

```java
public interface OrderRepository {
    Optional<Order> findById(OrderId orderId);
    void save(Order order, long expectedVersion);
}
```

### command handler

```java
public void handle(ChangeAddressCommand command) {
    Order order = orderRepository.findById(command.orderId()).orElseThrow();
    order.changeAddress(command.newAddress());
    orderRepository.save(order, command.expectedVersion());
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| pessimistic locking | 충돌을 일찍 막는다 | 잠금과 대기 비용이 크다 | 충돌 비용이 매우 큰 좁은 구간 |
| optimistic concurrency | 긴 잠금을 줄인다 | stale conflict 처리 정책이 필요하다 | 웹 요청, 일반 aggregate update |
| last-writer-wins | 구현이 단순하다 | lost update 위험이 크다 | 의미 충돌이 작고 운영적으로 허용될 때 |

판단 기준은 다음과 같다.

- 충돌 자체보다 잠금 비용이 크면 optimistic 쪽
- stale command resolution을 유스케이스별로 정한다
- retry는 command 의미와 side effect 안전성을 먼저 본다

---

## 꼬리질문

> Q: `@Version`만 붙이면 설계가 끝난 건가요?
> 의도: ORM 기능과 domain resolution policy를 구분하는지 본다.
> 핵심: 아니다. 충돌 감지는 시작일 뿐이고, 이후 해석과 UX가 더 중요하다.

> Q: 충돌이 나면 무조건 재시도하면 되나요?
> 의도: automatic retry의 위험을 보는 질문이다.
> 핵심: 아니다. command 의미와 side effect 안전성이 다르기 때문이다.

> Q: optimistic concurrency가 aggregate boundary와 왜 연결되나요?
> 의도: version 단위를 domain boundary와 연결해서 보는지 확인한다.
> 핵심: 어떤 상태 변화가 한 version 충돌 단위인지가 aggregate 경계와 연결되기 때문이다.

## 한 줄 정리

Aggregate version과 optimistic concurrency는 stale update를 감지하는 기본 패턴이고, 진짜 설계 포인트는 그 충돌을 유스케이스별로 어떻게 해석하고 풀어낼지에 있다.
