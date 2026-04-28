# MySQL EXPLAIN for Range Locking Primer

> 한 줄 요약: exact-key locking read에서 `EXPLAIN`으로 "거의 한 칸만 보나"를 확인했다면, range/overlap query에서는 반대로 "`EXPLAIN`이 어디까지 넓게 훑는가"를 먼저 확인해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [MySQL Overlap Fallback Beginner Bridge](./mysql-overlap-fallback-beginner-bridge.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md)
- [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)
- [인덱스와 실행 계획](./index-and-explain.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: mysql explain range locking primer, explain overlap query beginner, explain range locking read, explain for update range scan, mysql overlap explain primer, beginner explain gap lock, explain rows type range for update, exact key vs range explain, overlap query explain checklist, mysql explain wider access path, range lock beginner, 왜 for update인데 넓게 막혀요, explain overlap what is basics, 처음 range lock explain

## 핵심 개념

먼저 exact-key와 range를 이렇게 나눠서 보면 된다.

- exact-key 읽기: "정말 한 칸만 찌르나?"
- range/overlap 읽기: "몇 칸까지 길게 훑나?"

`FOR UPDATE`가 붙었다고 해서 `WHERE` 문장 전체가 잠기는 것은 아니다.
입문자 기준으로는 아래 한 줄을 기억하면 충분하다.

> range locking read는 `WHERE` 절보다 **`EXPLAIN`이 보여 주는 access path 폭**을 먼저 믿어야 한다.

즉 beginner 확인 순서는 이렇다.

1. 어떤 인덱스를 탔는가
2. 접근 타입이 exact lookup인가, `range`인가
3. `rows`가 작은가, 이미 넓은가
4. 이 넓은 scan이 곧 넓은 lock footprint 후보인가

## 이런 질문으로 들어왔으면 이 문서가 맞다

아래처럼 말하고 있다면 exact-key 문서보다 이 문서가 먼저다.

- "`FOR UPDATE`인데 왜 생각보다 넓게 막혀요?"
- "겹치는 row만 잠그는 것 아닌가요?"
- "`EXPLAIN rows`가 큰데 lock wait도 같이 커질 수 있나요?"
- "처음 overlap query를 보는데 `type=range`가 뭐예요?"

반대로 질문이 "`정말 같은 key 한 칸만 보나?`"에 더 가깝다면 [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)부터 보는 편이 빠르다.

## exact-key에서 range로 넘어갈 때 달라지는 질문

| 장면 | exact-key에서 묻는 질문 | range/overlap에서 묻는 질문 |
|---|---|---|
| `key` | intended `UNIQUE`를 탔나 | 어느 축의 인덱스를 탔나 |
| `type` | `const`/`ref`처럼 좁은가 | `range`라면 어느 범위를 읽기 시작하나 |
| `rows` | 거의 `1`인가 | 이미 넓은 읽기인가 |
| 초보자 결론 | 같은 key queue 보조 가능성 확인 | 넓은 scan이면 넓은 대기 가능성부터 의심 |

exact-key 문서에서는 "`rows=1` 근처인가"가 핵심이었다.
이 문서에서는 반대로 "`rows`가 벌써 크면 락도 business 문장보다 넓게 퍼질 수 있다"가 핵심이다.

## 가장 단순한 mental model

range locking read를 책장으로 비유하면 쉽다.

- exact-key: 책 한 권 자리를 찌르는 것
- range: 특정 선반 구간을 훑는 것

InnoDB는 대개 "내가 훑은 선반 구간" 기준으로 gap/next-key 영향을 남긴다.
그래서 overlap query에서 중요한 것은 "`겹침`이라는 한국어 문장"보다 "`실제로 어느 선반부터 어디까지 읽었나`"다.

## 30초 확인표

| 먼저 볼 것 | 보이면 어떻게 읽나 | 초보자 다음 행동 |
|---|---|---|
| `type = range` | 한 칸 lookup이 아니라 구간 scan이다 | "잠금도 넓어질 수 있다"를 먼저 적는다 |
| `rows`가 생각보다 큼 | overlap 후보 말고도 많이 훑을 수 있다 | 인덱스 축과 active predicate를 다시 본다 |
| `key`가 `(resource_id, start_at)` 같은 축 | `start_at` 방향 scan일 가능성이 크다 | "`overlap 전체 잠금`이라고 말하지 않는다" |
| `Extra`에 `Using where` | 인덱스가 잡아 준 뒤에도 후단 필터가 남는다 | logical overlap 전체가 index range로 줄지 않았다고 본다 |

이 표는 정밀한 optimizer 해석표가 아니다.
beginner가 "지금 이 query를 exact-key처럼 말하면 안 되겠구나"를 빠르게 감지하는 용도다.

## 예시 1. exact-key처럼 보이는 좋은 장면

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR SHARE;
```

```sql
UNIQUE KEY uq_coupon_member (coupon_id, member_id)
```

| 항목 | 기대 해석 |
|---|---|
| `key = uq_coupon_member` | intended unique path |
| `type = ref` 또는 비슷한 좁은 lookup | 거의 한 칸 probe |
| `rows = 1` 근처 | 넓은 range scan이 아니다 |

이 장면은 "같은 key 앞에서 줄이 생길 수 있는지"를 보기 좋은 exact-key 검증이다.

## 예시 2. overlap query에서 바로 시선이 바뀌는 장면

```sql
SELECT id
FROM booking
WHERE resource_id = :resource_id
  AND active_flag = 1
  AND start_at < :requested_end
  AND end_at > :requested_start
FOR UPDATE;
```

```sql
KEY idx_booking_resource_active_start (resource_id, active_flag, start_at)
```

여기서 beginner가 먼저 볼 것은 "`FOR UPDATE`니까 강하겠지"가 아니다.

| 항목 | 초보자 해석 |
|---|---|
| `key = idx_booking_resource_active_start` | `start_at` 축을 따라 읽을 가능성이 크다 |
| `type = range` | exact-key가 아니라 구간 scan이다 |
| `rows`가 20, 200처럼 커질 수 있음 | 실제 overlap row보다 더 많이 만질 수 있다 |
| `Extra = Using where` | `end_at > :requested_start`는 후단 필터일 수 있다 |

핵심 해석:

- 이 query는 overlap 규칙 전체를 그대로 잠근다고 말하기 어렵다
- 우선 `start_at` 축으로 읽고, 그다음 `end_at` 조건으로 걸러낼 수 있다
- 그래서 lock footprint도 logical overlap 집합보다 넓거나 비뚤어질 수 있다

## 왜 `Using where`가 beginner에게 중요한가

입문자는 `Extra`를 다 외울 필요는 없다.
여기서는 한 가지만 보면 된다.

- `Using where`가 보인다
  - 인덱스가 잡아 온 후보를 SQL이 한 번 더 걸러내고 있을 수 있다

overlap query에서는 이 한 줄만으로도 도움이 된다.

> "인덱스가 overlap 전체를 정확히 표현한 게 아니라, 후보를 넓게 가져와서 나중에 거르고 있을 수 있구나."

그래서 `Using where`가 강하게 보이면 beginner는 이렇게 적어 두면 된다.

- overlap predicate 전체가 exact range로 잠긴다고 설명하지 않는다
- chosen index axis와 post-filter를 분리해서 본다

## 자주 나오는 good / suspicious 비교

| 보이는 모양 | good에 가까운 해석 | suspicious 해석 |
|---|---|---|
| `key`가 intended composite index | 적어도 원하는 축으로 읽으려 한다 | 다른 인덱스면 lock surface 설명이 바로 흔들린다 |
| `type = range` | range query에서는 자연스러울 수 있다 | exact-key처럼 말하면 안 된다 |
| `rows`가 아주 작다 | 비교적 좁은 range일 수 있다 | 그래도 exact-key 보장으로 과장하지 않는다 |
| `rows`가 크다 | 넓은 scan 가능성 | 넓은 lock wait, false positive 대기부터 의심 |
| `Using where`가 남는다 | 후단 필터가 있다 | logical overlap 전체가 index에 안 담겼을 수 있다 |

초보자 메모:

- `rows`가 크다고 "문제 확정"은 아니다
- 대신 "`겹치는 것만 잠근다`고 말하면 위험" 신호로 읽는 편이 맞다

## beginner 검증 순서

### 1. exact-key 문장인지 range 문장인지 먼저 분류한다

- equality full key면 exact-key 쪽 문서로 본다
- `<`, `>`, `BETWEEN`, overlap 조건이 있으면 range 쪽으로 본다

이 첫 분류를 놓치면 `FOR UPDATE`를 exact-key처럼 설명하기 쉽다.

### 2. `EXPLAIN`의 `key`로 "어느 축을 읽는지" 적는다

예:

- `(resource_id, active_flag, start_at)`면 `start_at` 축
- `(resource_id, active_flag, end_at)`면 `end_at` 축

입문자 기억법:

> overlap query는 "겹침 전체"보다 "어느 시간 축으로 먼저 읽는가"를 먼저 적는다.

### 3. `type = range`면 보호 범위를 과장하지 않는다

`range` 자체가 나쁘다는 뜻은 아니다.
다만 이때는 exact-key 직관을 멈춰야 한다.

- same-key 한 칸 보호가 아니다
- 읽는 구간이 넓어질 수 있다
- false positive scan이 곧 false positive lock wait 후보가 된다

### 4. `rows`를 보고 "얼마나 넓게 읽나"를 묻는다

`rows`는 정확한 실측이 아니라도 beginner 판단에는 충분하다.

- `rows`가 작다
  - 비교적 좁을 수 있다
- `rows`가 크다
  - overlap 후보 말고도 많은 row를 훑는다는 뜻일 수 있다

이때 초보자 결론은 단순하다.

- `rows`가 크면 "`겹치는 것만 잠근다`"는 설명을 멈춘다

### 5. active predicate가 index prefix에 있는지 본다

예약/홀드 테이블은 inactive history가 많이 쌓인다.
그래서 아래 차이가 크다.

- `(resource_id, start_at)`
- `(resource_id, active_flag, start_at)`

`active_flag` 같은 prefix가 없으면,

- 끝난 row까지 많이 읽을 수 있고
- lock footprint도 필요 이상으로 넓어질 수 있다

즉 beginner가 range query에서 보는 추가 질문은 이것이다.

> "내가 보고 싶은 active 집합이 index 앞쪽에 있나?"

## 자주 틀리는 말

- "`FOR UPDATE`니까 overlap 전체가 잠긴다"
  - 아니다. chosen index path를 따라 넓게 읽고 잠글 수 있을 뿐이다.
- "`rows`가 조금 크지만 어차피 겹치는 row만 막겠죠?"
  - 아니다. scan이 넓으면 대기도 넓어질 수 있다.
- "`Using where`는 성능 얘기일 뿐이죠?"
  - overlap 검증에서는 후단 필터 존재를 보여 주는 beginner 경보등이기도 하다.
- "`type = range`면 실패한 plan이네요"
  - 아니다. overlap/range query에서는 자연스러울 수 있다. 다만 exact-key처럼 설명하면 안 된다.

## 그다음 결정

`EXPLAIN`을 보고 아래처럼 나누면 beginner가 덜 흔들린다.

| 상황 | 다음 판단 |
|---|---|
| full unique equality + `rows=1` 근처 | exact-key queue 보조 검증 흐름으로 간다 |
| overlap/range + `type=range` + `Using where` | chosen axis 기반 넓은 scan으로 읽는다 |
| `rows`가 커서 lock wait가 걱정됨 | index 축 재검토 또는 slot/guard row 쪽으로 이동 검토 |
| active/history가 섞여 scan이 커 보임 | `active_flag` prefix, active table split, 다른 arbitration surface를 검토 |

처음 읽는다면 위 표에서 자기 query를 한 줄로 분류한 뒤, `EXPLAIN key/type/rows`만 코드 리뷰 메모에 남기는 것부터 시작하면 된다.

## 다음에 어디로 가면 좋은가

- exact-key 검증 흐름부터 다시 보고 싶으면 [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- overlap을 MySQL locking read로 오래 붙잡지 말아야 하는 이유를 beginner 톤으로 보고 싶으면 [MySQL Overlap Fallback Beginner Bridge](./mysql-overlap-fallback-beginner-bridge.md)
- gap/next-key를 더 정확히 배우고 싶으면 [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- RR에서 range lock 가정이 실제로 언제 깨지는지 더 엄밀하게 보고 싶으면 [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md)
- booking overlap에서 `(start_at)` 축과 `(end_at)` 축이 왜 다른 footprint를 만드는지 보고 싶으면 [Overlap Predicate Index Design for Booking Tables](./overlap-predicate-index-design-booking-tables.md)

## 한 줄 정리

exact-key에서 `EXPLAIN`이 "한 칸 lookup인지"를 확인하는 도구였다면, range/overlap에서는 `EXPLAIN`이 "얼마나 넓게 훑고 얼마나 넓게 잠글 수 있는지"를 가늠하는 첫 검증 도구다.
