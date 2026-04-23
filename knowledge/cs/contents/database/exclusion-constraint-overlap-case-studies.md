# Exclusion Constraint Case Studies for Overlap and Range Invariants

> 한 줄 요약: overlap 금지는 "겹치는 row가 없는지 조회"가 아니라 equality dimension, range boundary, active predicate를 DB가 저장 시점에 중재하게 만드는 문제다.

**난이도: 🔴 Advanced**

관련 문서:

- [Range Invariant Enforcement for Write Skew and Phantom Anomalies](./range-invariant-enforcement-write-skew-phantom.md)
- [Engine Fallbacks for Overlap Enforcement](./engine-fallbacks-overlap-enforcement.md)
- [Write Skew와 Phantom Read 사례](./write-skew-phantom-read-case-studies.md)
- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)
- [Write Skew Detection과 Compensation Patterns](./write-skew-detection-compensation-patterns.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md)
- [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
- [Soft Delete, Uniqueness, and Active-Row Lifecycle](./soft-delete-uniqueness-indexing-lifecycle.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)

retrieval-anchor-keywords: exclusion constraint, overlap prevention, range overlap invariant, booking overlap constraint, phantom-safe modeling, write skew constraint, temporal uniqueness, PostgreSQL EXCLUDE USING gist, tstzrange, half-open interval, active booking predicate, blackout window, hold expiration, maintenance buffer, SQLSTATE 23P01, overlap preflight scan, PostgreSQL vs MySQL overlap fallback, exclusion constraint fallback

## 핵심 개념

예약, 점검, 정책 window 같은 문제는 본질적으로 "같은 자원에 겹치는 활성 구간이 동시에 존재하면 안 된다"는 규칙을 가진다.

나쁜 접근:

- 먼저 조회해서 빈 구간인지 확인
- 비어 있으면 insert

좋은 접근:

- 어떤 차원에서 같아야 충돌인지(equality dimension)
- 어떤 구간 표현이 실제 점유인지(range expression)
- 어떤 상태가 실제 점유인지(active predicate)

이 세 가지를 고정한 뒤, 저장 시점에 DB가 겹침을 거부하게 만든다.

exclusion constraint는 그 대표적인 도구지만,  
핵심은 특정 문법보다 **애플리케이션의 부재 기반 판단을 DB arbitration으로 옮기는 사고방식**이다.

## 깊이 들어가기

### 1. overlap 규칙은 "시간 겹침"보다 넓다

실무에서 겹침 대상은 예약끼리만이 아니다.

- 예약 vs 예약
- 예약 vs 운영 blackout
- 대여 vs 점검 buffer
- 프로모션 vs 기본 가격 정책

그래서 overlap을 설계할 때는 "어느 테이블을 조회하느냐"보다  
"어떤 row 조합이 같은 자원을 점유하는가"를 먼저 통일해야 한다.

### 2. 반개구간과 active predicate가 문법보다 먼저다

많은 장애는 constraint 문법이 아니라 경계 정의에서 시작된다.

반드시 먼저 고정할 것:

- 구간은 `[start, end)`인지 `[start, end]`인지
- timezone은 UTC 저장인지 로컬 시각 저장인지
- `HELD`, `CONFIRMED`, `BLACKOUT`, `MAINTENANCE`, `EXPIRED` 중 무엇이 활성 상태인지
- turn-around buffer나 청소 시간이 실제 blocked range에 포함되는지

이 정의가 없으면 constraint를 걸어도 false conflict와 missed conflict가 동시에 나온다.

### 3. lifecycle이 비동기 cleanup에만 의존하면 다시 샌다

예를 들어 hold 만료를 배치 job이 정리한다고 하자.

- 앱 쿼리는 `expires_at > now()` 기준으로 active hold를 본다
- constraint는 `status IN ('HELD', 'CONFIRMED')`만 본다
- cleanup job이 지연되면 앱과 DB가 서로 다른 active set을 보게 된다

이런 상태는 "조회는 비어 있는데 제약은 충돌"하거나 그 반대 상황을 만든다.  
active predicate는 비동기 정리 유무와 무관하게 **읽기와 쓰기 경로에서 동일하게 해석**돼야 한다.

### 4. exclusion constraint는 pairwise overlap에는 강하지만 capacity 규칙의 만능 답은 아니다

exclusion constraint는 "둘이 겹치면 안 된다"에 매우 강하다.  
하지만 다음 문제는 다른 도구가 더 맞는다.

- 같은 슬롯에 최대 3건까지 허용
- 전체 합계가 capacity를 넘지 않아야 함
- 서로 다른 테이블이나 외부 시스템까지 합쳐 한도 관리

이 경우에는 slotization, guard row, reservation ledger가 더 자연스럽다.

### 5. 마이그레이션은 constraint 추가보다 데이터 정리가 먼저다

운영 테이블에 바로 제약을 추가하려고 하면 보통 먼저 막히는 것은 레거시 겹침 데이터다.

현실적 순서는 보통 이렇다.

1. 기존 데이터에서 실제 overlap pair를 먼저 찾는다
2. 경계 정의(`[start, end)`, UTC, active status)를 정리한다
3. 모든 쓰기 경로가 같은 predicate를 쓰는지 맞춘다
4. 충돌 예외를 API/백오피스가 같은 방식으로 번역하게 만든다
5. 그다음에 constraint를 걸고 모니터링을 붙인다

constraint를 나중에 거는 이유는 "느슨하게 시작"하기 위해서가 아니라,  
**이미 어긋난 데이터를 제약이 통과할 수 있는 상태로 먼저 되돌려야 하기 때문**이다.

### 6. 충돌은 실패가 아니라 예상 가능한 경쟁 결과다

exclusion constraint를 도입하면 충돌 요청이 반드시 생긴다.  
이걸 장애로 해석하면 운영이 흔들린다.

구분해야 할 결과:

- `23P01` 같은 exclusion conflict: 사용자가 이미 점유된 구간을 요청함
- `40001` 같은 serialization failure: 강한 격리에서 재시도 후보
- 잘못된 입력: `start_at >= end_at`, timezone 누락, 자원 스코프 누락

즉 overlap 보호는 constraint만 추가하는 작업이 아니라,  
**예외 분류와 bounded retry 정책을 함께 설계하는 작업**이다.

## 실전 시나리오

### 시나리오 1. 회의실 예약과 hold 만료 지연

규칙:

- 같은 `room_id`에 대해 `HELD`, `CONFIRMED`, `BLACKOUT` 구간은 겹치면 안 된다

실무 함정:

- 사용자는 hold가 만료됐다고 생각하지만 cleanup job이 아직 상태를 바꾸지 않았다
- 운영자는 같은 시간대에 `BLACKOUT`을 입력할 수 있다
- 모바일, 백오피스, 배치가 서로 다른 active predicate를 쓰면 판단이 갈라진다

권장 guardrail:

- `tstzrange(start_at, end_at, '[)')`로 반개구간을 통일한다
- hold와 blackout을 모두 같은 conflict surface에 태운다
- cleanup 지연이 있어도 active predicate 정의가 읽기/쓰기에서 같게 유지되도록 한다
- `23P01`은 "이미 점유됨"으로 번역하고, 무한 retry하지 않는다

### 시나리오 2. 장비 대여와 점검 buffer 시간

규칙:

- 같은 `device_id`에 대해 대여 종료 후 점검 buffer까지 포함한 blocked range는 겹치면 안 된다

실무 함정:

- 사용자에게 보이는 `rent_end`와 실제 점유 종료 시각 `rent_end + cleanup_buffer`가 다르다
- 장비 교체나 수리 일정이 별도 테이블에 있으면 overlap surface가 분리된다
- 운영자가 수동 수정할 때 buffer 규칙을 빼먹기 쉽다

권장 guardrail:

- `rent_start`, `rent_end`와 별개로 constraint가 보는 blocked range를 명시한다
- maintenance row와 rental row를 같은 중재 규칙 아래 두거나, 적어도 동일한 derived range를 사용한다
- buffer 정책 변경 시 기존 row 재계산과 overlap 재검증 계획을 같이 세운다
- 장비 ID 재할당 전후 구간이 섞이지 않게 migration 순서를 고정한다

### 시나리오 3. 가격 정책 / 프로모션 window 충돌

규칙:

- 같은 `tenant_id`, `product_id`, `country_code` 조합에서 `ACTIVE` 정책 window는 겹치면 안 된다

실무 함정:

- equality dimension 중 하나가 백오피스나 배치 경로에서 빠지기 쉽다
- `DRAFT`, `PENDING_APPROVAL`, `ACTIVE`, `ARCHIVED` 상태를 각 경로가 다르게 해석한다
- 새 정책 경로와 레거시 경로가 배포 기간에 동시에 쓰면 제약 우회 경로가 생긴다

권장 guardrail:

- equality dimension을 API 입력 검증, 저장 쿼리, constraint에서 모두 동일하게 유지한다
- `ACTIVE` 판정이 애플리케이션과 DB predicate에서 같아야 한다
- 배포 중 이중 쓰기 기간에는 모든 경로가 같은 overlap arbitration을 통과하는지 shadow check로 검증한다
- conflict rate를 tenant/product 차원까지 쪼개서 본다

## 운영 guardrail 체크리스트

- `CHECK (start_at < end_at)` 같은 유효 범위 검증을 먼저 둔다
- 시간대는 UTC 저장을 기본으로 하고, 화면 변환은 읽기 경로에서만 한다
- active predicate와 lifecycle 상태 정의를 코드, DB, 운영 문서에서 같은 표현으로 고정한다
- constraint 추가 전 overlap preflight scan으로 기존 충돌 데이터를 정리한다
- `23P01`과 `40001`에 대한 API 에러 번역과 bounded retry 정책을 분리한다
- hot resource의 conflict rate, hold 만료 지연, cleanup backlog를 함께 모니터링한다
- 엔진이 exclusion 문법을 주지 않으면 slotization이나 guard row가 더 단순한지 먼저 비교한다

## 코드로 보기

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE room_booking
ADD CONSTRAINT room_booking_valid_range
CHECK (start_at < end_at);

ALTER TABLE room_booking
ADD CONSTRAINT room_booking_no_overlap
EXCLUDE USING gist (
  room_id WITH =,
  tstzrange(start_at, end_at, '[)') WITH &&
)
WHERE (status IN ('HELD', 'CONFIRMED', 'BLACKOUT'));
```

```sql
-- 제약 추가 전에 기존 overlap pair를 찾는 preflight scan
SELECT a.id AS left_id,
       b.id AS right_id,
       a.room_id
FROM room_booking a
JOIN room_booking b
  ON a.room_id = b.room_id
 AND a.id < b.id
 AND tstzrange(a.start_at, a.end_at, '[)') && tstzrange(b.start_at, b.end_at, '[)')
WHERE a.status IN ('HELD', 'CONFIRMED', 'BLACKOUT')
  AND b.status IN ('HELD', 'CONFIRMED', 'BLACKOUT');
```

```text
conflict handling
1. insert / update 시도
2. SQLSTATE 23P01 -> 이미 점유된 구간으로 번역
3. SQLSTATE 40001 -> 멱등한 hold 생성 경로에만 제한적 retry
4. 그 외 입력 오류 -> 즉시 검증 실패 반환
```

핵심은 특정 DB 기능을 쓰는 것이 아니라,  
겹침 규칙을 "조회 후 판단"에서 "저장 시 중재"로 옮긴 뒤 예외까지 정상 흐름으로 다루는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| app check + insert | 구현이 빠르다 | phantom/write skew에 취약하고 경로별 규칙이 갈린다 | 낮은 중요도, 임시 내부 툴 |
| exclusion constraint | continuous overlap을 직접 보호한다 | 엔진 지원과 range/lifecycle 모델링이 필요하다 | 예약, blackout, 정책 window 충돌 |
| slot row + unique | 설명 가능하고 테스트하기 쉽다 | row 수가 많이 늘 수 있다 | 시간이 15분, 1일 같은 discrete bucket일 때 |
| guard row / capacity row | count/sum 규칙까지 다루기 쉽다 | binary overlap에는 표현이 덜 직접적이다 | capacity, quota, 최소/최대 인원 |
| post-commit validation + compensation | 분산 경계에서 현실적이다 | 늦게 발견될 수 있다 | 외부 시스템 포함 workflow |

## 꼬리질문

> Q: exclusion constraint를 설계할 때 제일 먼저 정해야 하는 것은 무엇인가요?
> 의도: 문법보다 invariant 경계를 먼저 보는지 확인
> 핵심: equality dimension, range boundary(`[start, end)`), active predicate를 먼저 고정해야 한다

> Q: overlap 문제인데 왜 hold 만료 지연이나 cleanup backlog를 같이 보나요?
> 의도: lifecycle과 active predicate가 제약과 연결된다는 점을 이해하는지 확인
> 핵심: 비동기 정리 지연이 앱과 DB가 보는 active set을 다르게 만들면 다시 샌다

> Q: exclusion constraint가 있으면 capacity 초과 문제도 같이 해결되나요?
> 의도: pairwise overlap과 count/sum 규칙을 구분하는지 확인
> 핵심: 아니다. capacity는 guard row나 ledger 같은 다른 모델이 더 직접적이다

## 한 줄 정리

exclusion-style overlap 보호는 단순 문법 문제가 아니라 equality dimension, range boundary, active predicate, migration precheck, conflict handling을 함께 맞춰서 DB가 저장 시점에 겹침을 중재하게 만드는 설계다.
