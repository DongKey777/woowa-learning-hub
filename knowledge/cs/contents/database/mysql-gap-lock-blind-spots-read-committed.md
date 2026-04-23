# MySQL Gap-Lock Blind Spots Under READ COMMITTED

> 한 줄 요약: `REPEATABLE READ`에서 next-key/gap lock에 기대던 MySQL overlap check는 `READ COMMITTED`로 내리면 "비어 있는 범위"를 더 이상 잠그지 못해 phantom insert가 다시 열린다.

**난이도: 🔴 Advanced**

관련 문서:

- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [Read Committed와 Repeatable Read의 이상 현상 비교](./read-committed-vs-repeatable-read-anomalies.md)
- [Write Skew and Phantom Read Case Studies](./write-skew-phantom-read-case-studies.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)
- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)

retrieval-anchor-keywords: mysql read committed gap lock blind spot, overlap check phantom under read committed, next-key lock disabled read committed, locking nonexistence mysql, select for update empty result phantom, booking overlap race mysql, read committed overlap mitigation, overlap probe composite index, booking lock footprint mysql, guard row booking mysql, slotization overlap mysql, serializable retry overlap mysql, duplicate-key foreign-key gap lock exception

## 핵심 개념

MySQL InnoDB에서 어떤 overlap check가 `REPEATABLE READ`에서만 멀쩡해 보였다면, 그건 종종 **논리 규칙이 안전해서가 아니라 next-key/gap lock이 빈 범위를 우연히 막아 줬기 때문**이다.

전형적인 패턴은 이렇다.

1. `SELECT ... FOR UPDATE`로 겹치는 예약이 없는지 확인한다.
2. 결과가 없으면 같은 트랜잭션에서 insert한다.
3. `REPEATABLE READ`에서는 인덱스 range scan이 next-key/gap lock을 잡아 새 insert를 막아 주는 것처럼 보인다.

하지만 `READ COMMITTED`에서는 search/scan에 대한 gap locking이 꺼지므로, 같은 SQL이 **기존 row는 잠가도 아직 없는 row의 삽입은 막지 못한다.**  
그래서 "없음을 잠갔다"고 믿었던 overlap check가 phantom-safe하지 않게 된다.

중요한 예외도 있다.

- duplicate-key check
- foreign-key check

`READ COMMITTED`에서도 이런 경우에는 일부 gap lock이 남을 수 있다.  
하지만 continuous overlap predicate는 보통 unique duplicate나 FK 검사가 아니므로, 이 예외에 기대서는 안 된다.

## 깊이 들어가기

### 1. 왜 `REPEATABLE READ`에서는 안전해 보였나

회의실 예약 overlap check를 예로 들면 흔히 이런 SQL이 있다.

```sql
SELECT id
FROM room_booking
WHERE room_id = :room_id
  AND status IN ('HELD', 'CONFIRMED')
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;
```

여기서 팀이 기대하는 의미는 보통 "겹치는 활성 booking이 없으면 지금 insert해도 된다"다.  
문제는 이 SQL이 **논리적 overlap 전체**를 잠그는 것이 아니라, 실제로 스캔한 인덱스 range를 잠근다는 점이다.

이때 `(room_id, start_at)`를 타는지 `(room_id, end_at)`를 타는지에 따라 어떤 gap과 record를 건드리는지가 달라진다.  
복합 인덱스 shape별 lock footprint 비교는 [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)에서 이어 본다.

그런데 `REPEATABLE READ`에서는 다음 조건이 맞으면 꽤 오래 버틴다.

- locking read를 쓴다
- `room_id, start_at` 같은 적절한 인덱스를 탄다
- 모든 write path가 같은 probe를 먼저 수행한다
- active predicate와 range boundary가 경로마다 같다

이때는 next-key/gap lock이 스캔 범위 안의 새 insert를 막으면서  
"존재하지 않음도 잠근 것 같다"는 착시를 준다.

즉 `REPEATABLE READ`에서의 안전성은 종종 **비즈니스 규칙의 완전한 모델링**이 아니라  
**검색 경로와 락 구현 세부에 묶인 부분적 보호**였다.

### 2. `READ COMMITTED`로 내리면 정확히 무엇이 바뀌나

`READ COMMITTED`에서 InnoDB는 search/scan에 대해 gap lock을 일반적으로 사용하지 않는다.  
locking read가 잡는 중심은 "지금 존재해서 스캔한 index record"다.

그래서 overlap check가 다시 취약해지는 핵심 이유는 세 가지다.

- 결과가 비어 있으면 잠긴 범위도 사실상 비어 버린다
- 이미 있던 row는 잠가도, 그 사이 gap에 들어올 새 row는 막지 못한다
- statement마다 최신 committed view를 보므로, 다음 statement에서 새 row를 관측할 수 있다

즉 `READ COMMITTED`는 "최신성"에는 유리할 수 있지만,  
`REPEATABLE READ`에서 next-key lock이 만들어 주던 **absence serialization**을 잃는다.

### 3. overlap check에서 특히 잘 터지는 blind spot

#### blind spot 1. empty-result probe

가장 위험한 경우다.

1. 트랜잭션 A가 overlap query를 `FOR UPDATE`로 실행한다
2. 결과가 `0 row`라서 안전하다고 판단한다
3. 트랜잭션 B가 같은 resource에 겹치는 row를 insert 후 commit한다
4. 트랜잭션 A도 자기 row를 insert 후 commit한다

`READ COMMITTED`에서는 A가 빈 범위를 잠근 것이 아니므로 둘 다 성공할 수 있다.

#### blind spot 2. existing-row bias

충돌 후보가 이미 존재하면 그 row는 잠글 수 있다.  
하지만 overlap invariant는 "이미 있는 row"만 보호하면 끝나지 않는다.

- 지금은 없지만 조금 뒤 같은 predicate 안으로 들어올 row
- 같은 resource 안의 다른 `start_at` 지점
- 상태 전이가 바뀌며 active predicate 안으로 들어오는 row

이런 미래 row는 record lock만으로는 보호되지 않는다.

#### blind spot 3. predicate와 B-tree 축의 불일치

overlap은 보통 두 경계를 함께 본다.

- `start_at < :requested_end`
- `end_at > :requested_start`

하지만 B-tree scan은 실제로 한 index prefix를 따라 움직인다.  
즉 `REPEATABLE READ`에서도 보호 범위는 "논리적 overlap 연산자"가 아니라 "실제로 스캔한 축"이었다.

그래서 `READ COMMITTED`로 낮추는 순간 드러나는 건 단순히 락이 약해진다는 사실뿐 아니라,  
원래부터 overlap 규칙이 storage/index surface에 과도하게 의존했다는 구조적 약점이다.

#### blind spot 4. mixed write path

한 경로는 `SELECT ... FOR UPDATE`를 하고, 다른 경로는 바로 `INSERT`하거나 다른 인덱스를 타면  
`REPEATABLE READ`에서도 완전하지 않다. `READ COMMITTED`에서는 이 문제가 더 빨리 드러난다.

즉 isolation level 변경은 종종 **숨겨져 있던 경로 불일치**를 폭로하는 계기다.

### 4. 같은 overlap check가 RR과 RC에서 어떻게 달라지는가

예약 요청 두 개가 같은 방, 겹치는 시간대를 노린다고 하자.

#### `REPEATABLE READ`에서 기대한 흐름

1. A: overlap query `FOR UPDATE`
2. A: scanned range에 next-key/gap lock 형성
3. B: 같은 range에 들어오는 insert 시도
4. B: 대기하거나, A 커밋 후 재평가
5. A/B 둘 중 하나만 성공

이건 어디까지나 "같은 probe, 같은 인덱스, 같은 active predicate"를 모두 지킨다는 가정 아래의 이야기다.

#### `READ COMMITTED`에서 실제로 벌어질 수 있는 흐름

1. A: overlap query `FOR UPDATE`
2. A: 기존 row가 없으므로 범위 gap protection 없음
3. B: 겹치는 booking row insert 후 commit
4. A: 여전히 자기 판단을 믿고 row insert
5. 최종적으로 겹치는 booking 두 개가 함께 존재

즉 `READ COMMITTED`에서는 overlap check가 다시  
**"check-then-insert" 안티패턴**으로 돌아가 버린다.

## 실전 시나리오

### 시나리오 1. 회의실 예약

기존 구현:

- `room_id + start_at` 인덱스를 탄 `FOR UPDATE` overlap probe
- 결과가 없으면 `room_booking` insert

`REPEATABLE READ`에서는 얼핏 잘 동작했지만, `READ COMMITTED`로 바꾼 뒤 특정 시간대에서 중복 예약이 발생한다.

원인:

- empty-result overlap probe가 nonexistence를 잠그지 못함
- 운영툴/배치 경로 중 일부가 직접 insert해서 serialization surface를 우회

### 시나리오 2. blackout window와 사용자 예약의 경합

사용자 예약 API와 운영자 blackout 등록이 같은 base table을 공유한다.

- API는 overlap `FOR UPDATE` 후 insert
- 운영툴도 overlap `FOR UPDATE` 후 insert

`READ COMMITTED`에서는 두 쪽 모두 빈 결과를 본 뒤 각자 insert할 수 있다.  
그래서 blackout과 booking이 동시에 active set에 들어간다.

### 시나리오 3. hold 만료 상태 전이

hold row가 만료되어 `EXPIRED`로 바뀌는 worker와 신규 예약 생성이 경합한다.

이때 보호 대상은 단순 insert race만이 아니다.

- 기존 row의 status 변화
- `released_at` 처리 지연
- cleanup lag로 인한 active predicate 흔들림

즉 `READ COMMITTED`에서 overlap check를 유지하려면 락만이 아니라  
**active predicate 자체를 단순한 arbitration surface로 재모델링**해야 한다.

## 대응 전략

### 1. 가장 먼저 할 일: RR 의존 코드를 식별한다

격리수준을 낮추기 전에 아래 패턴을 찾는다.

- `SELECT ... FOR UPDATE` 후 `if none then INSERT`
- 겹침/부재/범위 없음 판단 뒤 쓰기
- 예약, blackout, 정책 window, hold, active claim 같은 active predicate 포함 쿼리

질문은 하나다.

> "이 코드가 정말 규칙을 모델링한 것인가, 아니면 RR next-key lock에 기대고 있었던 것인가?"

### 2. discrete하다면 slotization으로 내린다

시간이 5분, 15분, 1일처럼 business resolution으로 잘릴 수 있으면  
continuous overlap을 slot row로 바꾸는 편이 가장 설명 가능하다.

```sql
CREATE TABLE room_slot_claim (
  room_id BIGINT NOT NULL,
  slot_start DATETIME NOT NULL,
  booking_id BIGINT NOT NULL,
  PRIMARY KEY (room_id, slot_start)
);
```

장점:

- `READ COMMITTED`에서도 unique arbitration이 유지된다
- phantom-safe overlap을 unique 충돌로 번역할 수 있다
- 배치/운영툴/API가 같은 surface를 공유하기 쉽다

### 3. continuous interval이면 guard row를 세운다

bucket이 어색하면 `room_guard(room_id)` 또는 `(room_id, booking_day)` guard row를 둔다.

패턴:

1. guard row를 `FOR UPDATE`로 잠근다
2. overlap을 다시 확인한다
3. insert한다

여기서 serialization point는 gap lock이 아니라 guard row다.  
따라서 `READ COMMITTED`에서도 모든 경로가 같은 guard row를 거치면 안전성을 유지할 수 있다.

### 4. 여러 상태/테이블이 섞이면 arbitration table을 분리한다

`booking`, `blackout`, `hold`, 외부 시스템 상태까지 섞이면  
base table 위에서 overlap을 직접 판정하기보다 별도 ledger/materialized arbitration table을 둔다.

이 접근의 장점:

- active predicate를 한 곳으로 정규화할 수 있다
- `READ COMMITTED`와 `REPEATABLE READ` 차이에 덜 흔들린다
- reconciliation과 drift repair도 같은 기준면에서 할 수 있다

### 5. 재모델링이 어렵다면 `SERIALIZABLE` + retry를 쓴다

정말 query-level predicate 자체를 보호해야 하고  
slotization이나 guard row를 단기간에 넣기 어렵다면 `SERIALIZABLE`과 bounded retry를 검토한다.

다만 이건 마지막 선택지에 가깝다.

- 비용이 크다
- retry/idempotency 설계가 같이 필요하다
- hot range에서는 대기와 rollback이 늘 수 있다

즉 "RR에서 되던 게 RC에서 깨졌으니 그냥 serializable"은 너무 비싼 복구일 수 있다.

## 코드로 보기

```sql
-- 안티패턴: RC에서 empty-result overlap probe를 안전하다고 믿음
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;

SELECT id
FROM room_booking
WHERE room_id = :room_id
  AND status IN ('HELD', 'CONFIRMED')
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;

INSERT INTO room_booking(room_id, start_at, end_at, status)
VALUES (:room_id, :requested_start, :requested_end, 'CONFIRMED');

COMMIT;
```

```sql
-- guard row 패턴: serialization surface를 gap이 아니라 대표 row로 옮김
START TRANSACTION;

SELECT 1
FROM room_guard
WHERE room_id = :room_id
  AND booking_day = :booking_day
FOR UPDATE;

SELECT id
FROM room_booking
WHERE room_id = :room_id
  AND status IN ('HELD', 'CONFIRMED')
  AND start_at < :requested_end
  AND end_at > :requested_start;

INSERT INTO room_booking(room_id, start_at, end_at, status)
VALUES (:room_id, :requested_start, :requested_end, 'CONFIRMED');

COMMIT;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `REPEATABLE READ` 유지 + locking probe | 기존 구현을 빨리 유지할 수 있다 | 인덱스/plan/write-path 가정에 취약하다 | 단기 완충, 레거시 경로 유지 |
| slotization + unique | 가장 설명 가능하고 엔진 차이에 덜 흔들린다 | row 수 증가, bucket 합의 필요 | 시간이 discrete한 예약/점유 |
| guard row | `READ COMMITTED`에서도 직렬화 지점을 명확히 만든다 | hot key 경합, canonical order 필요 | continuous interval, capacity, active set |
| arbitration table / ledger | 여러 상태와 시스템을 한 surface로 모은다 | 모델링 비용이 있다 | blackout, hold, 외부 연동 포함 규칙 |
| `SERIALIZABLE` + retry | 강한 안전망을 준다 | 비용이 크고 retry 설계가 필요하다 | 빠른 재모델링이 불가능한 고정합성 경로 |

## 마이그레이션 체크리스트

- `REPEATABLE READ`에서 `READ COMMITTED`로 바꾸기 전에 `FOR UPDATE` 기반 부재 체크를 grep한다
- 쿼리가 `0 row`를 반환했을 때도 "지금은 안전하다"라고 해석하는 코드를 찾는다
- conflict surface가 unique key, slot row, guard row, ledger 중 무엇으로 표현될지 먼저 정한다
- 운영툴, 배치, API가 모두 같은 arbitration surface를 통과하는지 확인한다
- empty-result race를 재현하는 동시성 테스트를 isolation level별로 만든다

## 꼬리질문

> Q: 왜 `SELECT ... FOR UPDATE`가 `REPEATABLE READ`에서는 버티다가 `READ COMMITTED`에서 깨질 수 있나요?
> 의도: next-key/gap lock 의존성과 absence serialization을 이해하는지 확인
> 핵심: `READ COMMITTED`에서는 search/scan gap lock을 기대할 수 없어 빈 범위가 다시 열리기 때문이다

> Q: overlap 문제는 왜 unique 제약보다 구현이 더 어려운가요?
> 의도: exact key와 predicate/range invariant의 차이를 이해하는지 확인
> 핵심: overlap은 "같은 키"가 아니라 범위 관계를 보호해야 해서 base table locking read만으로는 불안정하다

> Q: `READ COMMITTED`를 꼭 써야 한다면 어디를 먼저 바꿔야 하나요?
> 의도: isolation level 변경보다 arbitration surface 재설계를 우선하는지 확인
> 핵심: slotization, guard row, arbitration table처럼 conflict surface를 저장 시점에 명시해야 한다

## 한 줄 정리

MySQL에서 overlap check가 `REPEATABLE READ`에서만 안전해 보였다면, `READ COMMITTED` 전환 시 가장 먼저 의심해야 할 것은 로직이 아니라 **gap lock에 기대던 부재 잠금 착시**다.
