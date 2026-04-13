# Write Skew and Phantom Read Case Studies

> 한 줄 요약: 격리수준과 락의 차이는 정의보다 사례에서 드러난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
> - [트랜잭션 실전 시나리오](./transaction-case-studies.md)
> - [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)

## 핵심 개념

`Phantom Read`와 `Write Skew`는 둘 다 동시성 문제지만 원인이 다르다.

- Phantom Read: 범위 조회 결과가 바뀜
- Write Skew: 서로 다른 row를 보고 각각 업데이트해서 불변식이 깨짐

## 깊이 들어가기

### 1. Phantom Read 사례

```sql
-- 첫 번째 조회
SELECT COUNT(*) FROM booking WHERE room_id = 10 AND date = '2026-04-08';

-- 다른 트랜잭션이 insert
INSERT INTO booking(room_id, date) VALUES (10, '2026-04-08');

-- 두 번째 조회 결과가 달라짐
```

범위 조건이 있는 조회에서 새 row가 끼어들면 phantom이 생긴다.

### 2. Write Skew 사례

의사 스케줄링 예시:

- 의사 A와 B가 둘 다 “오늘 당직 의사가 최소 1명은 남아야 한다”는 규칙을 본다
- 둘 다 자신의 row만 비활성화한다
- 결과적으로 아무도 당직이 남지 않는다

서로 다른 row를 업데이트했지만 전체 불변식이 깨지는 게 write skew다.

### 3. 왜 격리수준만으로 안 끝나는가

읽기/쓰기 패턴에 따라 다음이 필요하다.

- row lock
- gap lock
- unique constraint
- application-level invariant check

DB 격리수준만 믿고 비즈니스 불변식을 맡기면 사고가 난다.

## 실전 시나리오

### 시나리오 1: 좌석 예약

좌석 예약은 phantom과 write skew가 모두 문제다.

- 같은 좌석을 두 번 잡는 문제
- 같은 시간대에 허용 가능 수를 넘기는 문제

### 시나리오 2: 재고 차감

재고는 음수가 되면 안 된다.

이 규칙은 DB row 하나가 아니라 전체 주문 흐름의 불변식이다.

## 코드로 보기

```sql
-- 불변식이 중요하면 unique key/constraint를 같이 둔다
ALTER TABLE booking
ADD CONSTRAINT uq_room_date UNIQUE(room_id, date);
```

## 트레이드오프

| 대응 | 장점 | 단점 | 사용 시점 |
|---|---|---|---|
| 높은 격리수준 | 단순하다 | 성능 비용 | 매우 중요한 정합성 |
| 비관적 락 | 안전하다 | 경합이 커진다 | 충돌이 잦을 때 |
| 제약조건 | 강하다 | 모델링이 필요 | 불변식이 명확할 때 |
| 애플리케이션 재검증 | 유연하다 | 구현 복잡 | 분산 워크플로우 |

## 꼬리질문

> Q: Phantom Read와 Write Skew는 같은 문제인가요?
> 의도: 격리 이상 현상 구분 여부 확인
> 핵심: phantom은 범위 결과 변화, write skew는 불변식 파괴다.

> Q: Serializable만 쓰면 해결되나요?
> 의도: 안전성과 성능 trade-off 이해 확인
> 핵심: 가장 강하지만 비용이 크고, 모델링으로 해결 가능한 부분은 constraint가 더 낫다.

## 한 줄 정리

Phantom Read는 범위가 흔들리는 문제이고, Write Skew는 서로 다른 row를 보고도 전체 규칙이 깨지는 문제다.
