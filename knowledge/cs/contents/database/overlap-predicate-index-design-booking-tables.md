# Overlap Predicate Index Design for Booking Tables

> 한 줄 요약: booking overlap probe에서 composite index는 "논리 규칙"을 그대로 잠그지 않고, B-tree가 실제로 스캔하는 축을 잠그므로 `(resource_id, start_at)`와 `(resource_id, end_at)`는 같은 쿼리라도 전혀 다른 lock footprint를 만든다.

**난이도: 🔴 Advanced**

관련 문서:

- [인덱스와 실행 계획](./index-and-explain.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Guard-Row Scope Design for Multi-Day Bookings](./guard-row-scope-design-multi-day-bookings.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)

retrieval-anchor-keywords: overlap predicate index design, booking overlap probe, composite index lock footprint, btree scan axis interval predicate, room booking start_at end_at index, mysql overlap locking read, next-key lock overlap probe, interval predicate btree mismatch, booking table overlap index, active booking probe index

## 핵심 개념

booking overlap probe는 보통 이렇게 생긴다.

```sql
SELECT id
FROM room_booking
WHERE room_id = :room_id
  AND status IN ('HELD', 'CONFIRMED')
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;
```

팀이 기대하는 의미는 "겹치는 활성 booking이 있으면 막고, 없으면 insert"다.  
하지만 B-tree와 InnoDB locking read가 실제로 기억하는 것은 **논리적 overlap 집합**이 아니라 **스캔한 index range**다.

즉 질문은 "인덱스가 있느냐"가 아니라 다음 두 가지다.

1. equality prefix 뒤에서 어떤 컬럼이 실제 scan axis가 되는가
2. 그 축을 따라 스캔한 range가 어떤 gap/record를 잠그는가

이 차이 때문에 `(room_id, start_at)`와 `(room_id, end_at)`는 같은 overlap SQL에도 전혀 다른 lock footprint를 만든다.

## 왜 B-tree 축이 interval predicate와 잘 안 맞는가

overlap 조건은 본질적으로 2차원이다.

- `start_at < :requested_end`
- `end_at > :requested_start`

이 조건은 `(start_at, end_at)` 평면에서 직사각형이나 단일 범위가 아니라 **대각선 띠(diagonal band)** 에 가깝다.  
반면 일반 B-tree는 lexicographic order 하나만 가진다.

- `(room_id, start_at, end_at)` 인덱스는 `start_at` 축을 따라 먼저 정렬한다
- `(room_id, end_at, start_at)` 인덱스는 `end_at` 축을 따라 먼저 정렬한다

즉 어느 쪽이든 한 boundary는 range start/stop을 만들 수 있지만, 다른 boundary는 대개 post-filter 또는 ICP 대상이 된다.  
그래서 B-tree는 logical overlap band 전체를 정확히 잠그기보다, **band를 가로지르는 한쪽 축의 긴 띠**를 잠그게 된다.

핵심 오해는 이거다.

- overlap predicate가 2개 있으니 두 조건이 모두 잠금 범위를 정확히 줄여 줄 것이라고 기대한다
- 실제로는 왼쪽 prefix 뒤 첫 range 조건이 scan axis를 거의 결정한다

즉 "복합 인덱스를 더 길게 만들면 논리 overlap을 정확히 잠그겠지"라고 보면 안 된다.

## 인덱스 모양별 lock footprint 비교

아래 표는 `room_id` equality가 먼저 있는 booking table을 가정한다.

| 인덱스 | 실제 scan axis | 나중에 남는 filter | 잠금/대기 표면에서 자주 보이는 현상 |
|---|---|---|---|
| `(room_id, start_at)` | `start_at < :requested_end` 방향으로 같은 room의 과거 구간부터 훑음 | `end_at > :requested_start`, `status` | 이미 오래전에 끝난 예약도 `start_at`만 이르면 많이 스캔해 over-locking 되기 쉽다 |
| `(room_id, end_at)` | `end_at > :requested_start` 방향으로 같은 room의 미래 구간을 훑음 | `start_at < :requested_end`, `status` | 아직 한참 뒤에 시작할 예약도 `end_at`가 늦으면 범위에 들어와 future-side over-locking 이 커진다 |
| `(room_id, status, start_at)` | active status를 먼저 좁히고 `start_at` 축으로 스캔 | `end_at > :requested_start` | inactive history를 덜 만져 footprint가 줄지만 overlap band를 정확히 잠그는 것은 아니다 |
| `(room_id, active_flag, start_at)` | blocking truth를 boolean prefix로 고정한 뒤 `start_at` 축 스캔 | `end_at > :requested_start` | `status IN (...)`보다 경로 일관성이 좋고, active/inactive drift를 줄이기 쉽다 |
| `(room_id, start_at, end_at)` | 여전히 `start_at`가 scan axis | `end_at > :requested_start` 대부분은 후단 평가 | 같은 `start_at` 묶음 안에서는 도움이 될 수 있지만 대각선 band 전체를 range로 만들지는 못한다 |
| `(room_id, end_at, start_at)` | 여전히 `end_at`가 scan axis | `start_at < :requested_end` 대부분은 후단 평가 | start-side 과다 스캔을 줄이는 대신 end-side future rows를 더 많이 건드릴 수 있다 |

핵심은 세 번째 컬럼이 아니라 **equality prefix 다음에 어느 boundary가 오는가**다.

## lock footprint가 왜 index shape에 따라 바뀌는가

InnoDB locking read는 exact `WHERE` 조건을 잠그는 것이 아니라 **statement가 스캔한 index record와 gap**을 기준으로 락을 건다.  
그래서 인덱스 shape가 바뀌면 다음이 함께 바뀐다.

- 어디서 scan이 시작되는가
- 어느 지점까지 next-key/gap lock이 퍼지는가
- 어떤 insert가 wait하고, 어떤 insert는 그냥 통과하는가
- secondary index를 탔을 때 어떤 clustered row까지 같이 잠그는가

예를 들어 같은 SQL이라도:

- `(room_id, start_at)`는 `requested_end` 이전의 오래된 booking pile을 넓게 건드린다
- `(room_id, end_at)`는 `requested_start` 이후의 먼 미래 booking pile을 넓게 건드린다

즉 쿼리 텍스트는 같아도, **어느 쪽에서 false positive scan을 많이 만들지**가 달라지고 그 false positive가 곧 lock footprint가 된다.

인덱스가 더 나쁘면 현상은 더 심해진다.

- active predicate prefix가 없으면 `CANCELLED`, `EXPIRED` history까지 같이 스캔한다
- 적절한 인덱스가 없으면 테이블/클러스터드 인덱스를 넓게 훑어 거의 전체 row를 잠글 수 있다

그래서 overlap probe의 composite index는 단순 성능 문제가 아니라 **동시성 표면 설계**에 가깝다.

## active predicate를 prefix로 올리는 이유

booking table은 status/history row가 빠르게 누적된다.  
이때 overlap probe가 실제로 보고 싶은 것은 "blocking truth"뿐이다.

그래서 아래 차이는 생각보다 크다.

- `(room_id, start_at)`
- `(room_id, status, start_at)`
- `(room_id, active_flag, start_at)`

`status IN ('HELD', 'CONFIRMED')`를 그냥 filter로 두면:

- inactive row도 scan range에 많이 포함된다
- 경로마다 active status 해석이 다르면 lock footprint도 경로마다 달라진다
- `BLACKOUT`, `MAINTENANCE`, `EXPIRED` 추가 시 probe 경로가 자꾸 흔들린다

반면 `active_flag` 같은 generated column이나 materialized blocking key를 두면:

- equality prefix가 짧고 안정적으로 유지된다
- lock footprint를 active set 기준으로 줄이기 쉽다
- overlap check와 cleanup/reconciliation의 active contract를 맞추기 좋다

물론 이것도 만능은 아니다.  
`active_flag`를 넣어도 interval predicate는 여전히 한 boundary만 scan axis가 되므로, exact overlap lock이 되는 것은 아니다.

## booking overlap probe에서 자주 하는 착각

### 1. `(start_at, end_at)`를 같이 넣었으니 두 범위가 모두 index range가 될 것이라는 착각

복합 인덱스는 equality prefix 다음 첫 range가 강하게 작동하고, 뒤쪽 range는 대개 post-filter로 남는다.  
그래서 overlap band 전체가 깔끔한 직사각형처럼 잠기지 않는다.

### 2. 읽기 plan이 좋아 보이면 locking semantics도 안전하다는 착각

`EXPLAIN`이 예뻐도 locking read는 scan path를 따라 gap/record를 잠근다.  
read efficiency와 phantom-safe invariant는 겹치지만 같은 문제가 아니다.

### 3. 인덱스 둘을 만들면 둘의 교집합만 잠길 것이라는 착각

`(room_id, start_at)`와 `(room_id, end_at)`를 둘 다 두어도, statement 하나는 실제 선택된 access path를 따라 잠근다.  
두 B-tree가 합쳐져 logical overlap predicate lock이 되는 것은 아니다.

### 4. `READ COMMITTED`에서도 같은 probe가 빈 구간을 보호할 것이라는 착각

`REPEATABLE READ`에서 보이던 next-key/gap protection은 `READ COMMITTED`에서 약해진다.  
따라서 "없음을 잠갔다"는 착시는 더 빨리 깨진다.

## 어떤 composite index가 상대적으로 낫나

정답은 하나가 아니라 workload에 따라 달라진다.  
다만 booking overlap probe에서는 아래 순서가 현실적이다.

### 1. equality dimension과 active predicate를 먼저 prefix로 고정한다

예:

- `(tenant_id, room_id, active_flag, start_at)`
- `(tenant_id, resource_type, resource_id, active_flag, end_at)`

같은 resource가 아니면 애초에 경쟁 surface를 분리해야 하고, inactive row는 scan 후보에서 빨리 빼야 한다.

### 2. start-side와 end-side 중 false positive가 더 적은 축을 고른다

질문:

- 같은 room의 과거 이력 row가 훨씬 많나
- 미래 예약 queue가 길게 쌓이나
- booking length distribution이 짧은가 긴가

보통:

- 과거 history가 매우 많으면 `end_at` 축이 더 나을 수 있다
- 미래 대기가 길고 과거 정리가 잘 되어 있으면 `start_at` 축이 더 나을 수 있다

즉 "정답 인덱스"가 아니라 **어느 쪽 과다 스캔을 감수할지**를 고르는 문제다.

### 3. probe 전용 index와 write arbitration 전략을 분리해서 생각한다

좋은 composite index는 probe 비용과 lock footprint를 줄여 준다.  
하지만 그 자체로 overlap invariant를 완전히 닫아 주는 도구는 아니다.

phantom-safe가 핵심이면:

- PostgreSQL: exclusion constraint
- MySQL: slotization
- MySQL: guard row / arbitration ledger

같은 별도 surface를 먼저 검토하는 편이 안전하다.

## 실전 시나리오

### 시나리오 1. `(room_id, start_at)`만 두고 오래된 이력이 계속 쌓이는 경우

현상:

- 오늘 1시간짜리 예약 probe인데, 몇 달 전 시작한 장기 row와 오래전에 끝난 row까지 많이 스캔한다
- `REPEATABLE READ` locking read에서 과거 구간 쪽 lock wait가 불필요하게 늘어난다

의미:

- `start_at < :requested_end`는 맞지만 `end_at > :requested_start`를 만족하지 않는 row가 너무 많다
- scan false positive가 곧 lock false positive가 된다

대응:

- active predicate prefix 추가
- history/archive 분리 검토
- `end_at` 축 대안이나 guard row 전환 비교

### 시나리오 2. `(room_id, end_at)`로 뒤집었더니 먼 미래 예약이 같이 묶이는 경우

현상:

- 긴 대여나 장기 blackout이 많아 `end_at > :requested_start` 범위가 넓다
- 당장 겹치지 않는 미래 booking insert도 대기한다

의미:

- start-side false positive를 줄였지만 end-side future pile을 lock surface에 넣은 것이다

대응:

- workload의 skew를 다시 본다
- booking 길이 상한이나 active horizon을 분리한다
- continuous interval 대신 slotization 가능한지 본다

### 시나리오 3. status prefix가 없어 운영툴과 API의 footprint가 달라지는 경우

현상:

- API는 active booking만 본다고 생각하지만 실제 locking read는 cancelled/history row까지 넓게 스캔한다
- 운영툴은 다른 status 조합을 써서 서로 다른 range를 건드린다

의미:

- "같은 규칙"이라고 믿지만 실제 scan surface가 경로마다 다르다

대응:

- `active_flag` 또는 materialized blocking predicate를 prefix에 올린다
- API, 운영툴, cleanup job이 같은 probe contract를 쓰게 맞춘다

## 코드로 보기

```sql
CREATE TABLE room_booking (
  id BIGINT PRIMARY KEY,
  room_id BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL,
  active_flag TINYINT(1) NOT NULL,
  start_at DATETIME NOT NULL,
  end_at DATETIME NOT NULL
);
```

```sql
CREATE INDEX idx_booking_room_start
    ON room_booking (room_id, start_at);

CREATE INDEX idx_booking_room_end
    ON room_booking (room_id, end_at);

CREATE INDEX idx_booking_room_active_start
    ON room_booking (room_id, active_flag, start_at);
```

```sql
SELECT id
FROM room_booking
WHERE room_id = ?
  AND active_flag = 1
  AND start_at < ?
  AND end_at > ?
FOR UPDATE;
```

위 SQL에서 `idx_booking_room_active_start`를 타면 보통:

- equality prefix: `room_id`, `active_flag`
- range axis: `start_at < :requested_end`
- residual filter: `end_at > :requested_start`

가 된다.  
즉 logical overlap 전체를 range로 잠그는 것이 아니라, **active row 중 requested_end 이전에 시작한 긴 띠**를 잠근다.

## 운영 체크리스트

- overlap probe는 read latency뿐 아니라 lock wait 분포로도 평가한다
- equality dimension과 active predicate를 composite index 왼쪽 prefix에 먼저 올린다
- `(start_at)` 축과 `(end_at)` 축 중 어느 쪽 false positive scan이 더 작은지 실제 데이터 분포로 비교한다
- `EXPLAIN`만 보지 말고 lock wait, deadlock, `performance_schema.data_locks` 같은 관측으로 scan surface를 확인한다
- `READ COMMITTED`에서는 empty-result overlap probe가 nonexistence를 보호하지 못한다는 전제를 유지한다
- phantom-safe invariant가 핵심이면 composite index 튜닝만으로 끝내지 말고 slotization/guard row/exclusion constraint를 검토한다

## 꼬리질문

> Q: `(room_id, start_at, end_at)`면 overlap predicate를 정확히 잠그는 건가요?
> 의도: 복합 인덱스와 logical predicate lock을 구분하는지 확인
> 핵심: 아니다. 보통 `start_at`가 scan axis가 되고 `end_at`는 후단 filter로 남는다

> Q: `(room_id, start_at)`와 `(room_id, end_at)` 중 어느 쪽이 정답인가요?
> 의도: 단일 정답보다 false positive scan trade-off를 보는지 확인
> 핵심: workload distribution에 따라 다르며, 어느 쪽 과다 스캔과 lock footprint를 감수할지의 문제다

> Q: composite index를 잘 잡으면 MySQL overlap invariant도 충분히 닫히나요?
> 의도: 성능 튜닝과 arbitration surface를 혼동하지 않는지 확인
> 핵심: 아니다. 인덱스는 probe를 줄여 주지만 exact overlap constraint를 대체하지는 못한다

## 한 줄 정리

booking overlap probe의 composite index는 logical interval 전체를 잠그는 도구가 아니라 B-tree가 실제로 걷는 축을 정하는 도구이고, 그 축이 곧 lock footprint가 된다.
