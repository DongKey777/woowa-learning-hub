# Saga Reservation Consistency와 예약 상태 전이

> 한 줄 요약: 예약은 확정이 아니라 홀드이며, Saga에서는 그 홀드를 언제 잡고 언제 풀지까지 정합성의 일부다.

**난이도: 🔴 Advanced**

관련 문서: [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md), [트랜잭션 실전 시나리오](./transaction-case-studies.md), [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
retrieval-anchor-keywords: saga reservation, inventory hold, seat booking, compensation, reservation ttl

## 핵심 개념

예약형 Saga는 하나의 큰 작업을 여러 단계로 쪼개고, 각 단계가 실패하면 보상 작업으로 되돌리는 모델이다.  
예약은 그중에서도 가장 자주 깨지는 단계다.

왜 중요한가:

- 좌석, 재고, 쿠폰, 방 배정은 “미리 잡고 나중에 확정”하는 흐름이 많다
- 예약과 확정 사이에 시간차가 있으면 중간 실패를 처리해야 한다
- 예약이 풀리지 않거나 중복 해제되면 정합성이 깨진다

예약은 실제 확정이 아니라 **임시 소유권**이다.

## 깊이 들어가기

### 1. reservation이 필요한 이유

동시 경쟁이 있는 자원은 바로 확정하면 충돌이 잦다.

- 좌석 1개에 두 명이 몰린다
- 재고가 적고 결제가 외부 시스템을 거친다
- 쿠폰은 선착순이라 경쟁이 심하다

이때 먼저 reservation을 잡고, 이후 결제/검증이 끝나면 confirm한다.

### 2. 예약 상태 전이

대표적인 상태는 다음과 같다.

- `HOLD`
- `CONFIRMED`
- `CANCELLED`
- `EXPIRED`

중요한 점은 상태 전이가 단방향이어야 한다는 것이다.  
이미 expired된 예약이 다시 confirmed 되면 안 된다.

### 3. 보상 작업의 함정

Saga의 보상은 단순한 rollback이 아니다.

- 결제 취소는 실제 환불이 될 수 있다
- 재고 해제는 이미 다른 요청이 잡았을 수 있다
- 좌석 해제는 타임아웃과 경합할 수 있다

그래서 보상은 “반대 동작”이지, 이전 상태의 완전 복원은 아니다.

### 4. TTL과 만료 처리

예약은 영원히 잡아두면 안 된다.

- 사용자가 결제를 중단할 수 있다
- 클라이언트가 죽을 수 있다
- 외부 승인 대기가 길어질 수 있다

TTL 기반 만료와 배경 정리 작업이 필요하다.

## 실전 시나리오

### 시나리오 1: 좌석 예약 후 결제 실패

예약은 잡혔지만 결제가 실패했다면, reservation을 풀어야 한다.  
이 과정이 누락되면 좌석이 유령처럼 사라진다.

### 시나리오 2: 재시도 때문에 예약이 두 번 생성됨

같은 요청이 재시도되면 reservation row가 중복될 수 있다.  
멱등성 키로 예약 선점을 막아야 한다.

### 시나리오 3: 만료 직후 confirm이 도착함

TTL이 만료된 뒤 confirm이 늦게 오면, 시스템은 이를 거절하거나 재검증해야 한다.

## 코드로 보기

```sql
CREATE TABLE reservations (
  reservation_id VARCHAR(80) PRIMARY KEY,
  resource_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  expires_at DATETIME NOT NULL,
  UNIQUE KEY uk_resource_active (resource_id, status)
);

-- 예약 선점
INSERT INTO reservations (reservation_id, resource_id, status, expires_at)
VALUES ('r-1001', 42, 'HOLD', NOW() + INTERVAL 5 MINUTE);
```

```java
// saga step
reserve();
try {
    pay();
    confirm();
} catch (Exception e) {
    cancelReservation();
    throw e;
}
```

예약은 성공/실패를 넘어, **언제까지 잡고 언제 풀지**가 같이 설계돼야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 즉시 확정 | 단순하다 | 경합과 실패가 많다 | 경쟁이 거의 없을 때 |
| HOLD 후 CONFIRM | 충돌을 줄인다 | TTL과 보상 로직이 필요하다 | 예약/좌석/재고 |
| optimistic recheck | 구현이 가볍다 | 경쟁이 심하면 실패가 늘어난다 | 중간 규모 |
| hold + idempotent retry | 안정적이다 | 설계가 복잡하다 | 분산 워크플로우 |

## 꼬리질문

> Q: 예약과 확정의 차이는 무엇인가요?
> 의도: 임시 소유권과 최종 커밋을 구분하는지 확인
> 핵심: 예약은 홀드이고 확정은 최종 상태다

> Q: Saga의 보상이 왜 rollback과 다른가요?
> 의도: 외부 부작용이 있는 작업의 되돌림을 아는지 확인
> 핵심: 보상은 반대 업무이지 시간 역행이 아니다

> Q: 예약 TTL이 왜 필요한가요?
> 의도: 유실된 세션과 유령 홀드 문제를 아는지 확인
> 핵심: 실패한 사용자의 홀드가 영원히 남지 않게 하기 위해서다

## 한 줄 정리

Saga의 예약은 임시 소유권이며, HOLD-CONFIRM-CANCEL 전이를 멱등하고 만료 가능하게 설계해야 정합성이 유지된다.
