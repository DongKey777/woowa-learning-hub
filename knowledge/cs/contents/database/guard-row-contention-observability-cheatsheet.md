# Guard-Row Contention Observability Cheatsheet

> 한 줄 요약: guard row 경합은 보통 "같은 key 앞에 줄이 길어지는" 모습으로 먼저 보이고, duplicate-key는 "이미 승자가 있다", deadlock은 "순환 대기에서 희생자가 뽑힌다", generic slow query는 "같은 key가 아니라 SQL 자체가 오래 돈다"로 읽으면 초보자 오분류가 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [Guard-Row Dashboard Starter Card](./guard-row-dashboard-starter-card.md)
- [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- [Pool 지표 읽기 미니 브리지 (active/idle/awaiting + lock wait timeout)](./pool-metrics-lock-wait-timeout-mini-bridge.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: guard row observability cheatsheet, guard-row contention observability, guard row lock wait vs duplicate key, guard row deadlock slow query difference, hot row observability beginner, same key wait metrics, guard row timeout logs, duplicate key vs lock wait metrics, deadlock vs guard row contention logs, slow query vs lock wait starter, room_type_day guard observability, campaign guard hot key signals, guard row same key concentration, lock wait duplicate deadlock slow query one page, hot row observability 입문

## 먼저 멘탈모델

guard row는 초보자 기준으로 **입장 게이트 row**다.

- `room_type_day_guard(room_type_id, stay_day)`
- `campaign_guard(campaign_id)`
- `tenant_quota_guard(tenant_id)`

이 gate에 요청이 몰리면 가장 먼저 보이는 질문은 이것이다.

> "이미 승자가 있는가?"가 아니라, "같은 key 앞에 대기줄이 생겼는가?"

그래서 관측도 아래처럼 나누면 쉽다.

- guard-row lock wait: 같은 key 앞에서 오래 기다림
- duplicate-key conflict: 같은 key의 승자가 이미 확정됨
- deadlock: 서로 다른 잠금 순서가 엇갈려 원형 대기
- generic slow query: 특정 guard key보다 SQL 범위/계획/스캔이 오래 걸림

## 30초 분리표

| 지금 보이는 것 | 가장 먼저 읽을 뜻 | 첫 확인 포인트 |
|---|---|---|
| `lock wait timeout`, 대기 시간 증가, 같은 guard key 반복 | guard-row lock wait 가능성 높음 | 상위 wait key가 한두 개에 몰리는가 |
| `duplicate key`, `23505`, `1062` | 이미 winner row가 있음 | same payload 재전송인지, 다른 payload 충돌인지 |
| `deadlock detected`, `1213`, `40P01` | 단순 대기보다 순환 대기 | 잠금 순서가 path마다 다른가 |
| slow query log 증가, full scan/rows examined 급증 | lock보다 SQL 자체가 오래 감 | 같은 key 반복이 아니라 같은 SQL shape 반복인가 |

짧은 기억법:

- 같은 key 줄서기 -> guard-row lock wait
- 이미 자리 있음 -> duplicate-key
- 서로 맞물려 멈춤 -> deadlock
- 줄보다 쿼리 자체가 김 -> generic slow query

## 처음 볼 지표 4개

초보자는 관측 surface를 크게 만들 필요 없다. 아래 네 칸이면 시작할 수 있다.

| 지표 | guard-row lock wait에서 기대되는 모양 | duplicate-key에서 기대되는 모양 | deadlock에서 기대되는 모양 | generic slow query에서 기대되는 모양 |
|---|---|---|---|---|
| `lock_wait_timeout_total` 또는 lock wait 시간 | 올라감 | 보통 핵심 지표 아님 | 같이 오를 수도 있지만 단독 해석 금지 | 낮거나 불규칙할 수 있음 |
| `duplicate_key_total` | 핵심 지표 아님 | 분명하게 올라감 | 핵심 지표 아님 | 핵심 지표 아님 |
| `deadlock_total` / deadlock victim 수 | 낮거나 0일 수 있음 | 거의 무관 | 분명하게 올라감 | 핵심 지표 아님 |
| top key concentration | 상위 1~2개 guard key에 wait 집중 | unique key 충돌 key는 보여도 wait 집중과는 다름 | 여러 key 조합이 엇갈릴 수 있음 | key 집중보다 SQL fingerprint 집중이 먼저 보임 |

핵심 포인트:

- guard-row 문제는 "오류 개수"보다 **같은 key 집중도**가 더 먼저 설명력을 가진다.
- duplicate-key는 기다림보다 **이미 있는 row 재분류**가 먼저다.
- slow query는 guard key보다 **SQL fingerprint / rows examined / scan 범위**를 먼저 본다.

## 로그 패턴 한 장 비교

| 로그 패턴 | 보통 더 가까운 원인 | 왜 그렇게 읽나 |
|---|---|---|
| `Lock wait timeout exceeded ... where room_type_id=? and stay_day=?` 가 반복 | guard-row lock wait | 같은 gate key가 반복해서 대기열 중심에 선다 |
| `duplicate key value violates unique constraint` 뒤 fresh read로 winner row가 보임 | duplicate-key conflict | 이미 승자가 있고 lock 줄을 오래 선 것이 아니다 |
| `deadlock detected`와 함께 서로 다른 statement 두 개가 교차 등장 | deadlock | 기다림이 아니라 원형 대기다 |
| slow query log에 `rows_examined`가 매우 크고 특정 key 패턴이 약함 | generic slow query | 같은 hot key보다 넓은 스캔/나쁜 계획이 더 의심된다 |

## guard-row lock wait를 먼저 의심할 때 보는 것

### 1. 같은 key가 정말 반복되는가

guard-row 경합은 대개 "문제가 난 요청을 key별로 묶었을 때 상위 1개 key가 유난히 크다"로 시작한다.

```sql
SELECT
  guard_key,
  COUNT(*) AS wait_events,
  ROUND(AVG(wait_ms), 1) AS avg_wait_ms
FROM guard_row_wait_events
WHERE observed_at >= :window_start
GROUP BY guard_key
ORDER BY wait_events DESC
LIMIT 5;
```

| 결과 모양 | 초보자 첫 해석 |
|---|---|
| 상위 1개 `guard_key`가 대부분 차지 | single hot guard row 가능성이 높다 |
| 상위 key가 넓게 퍼짐 | 특정 guard row보다 wider write pressure일 수 있다 |
| wait는 적고 duplicate만 많음 | contention보다 winner-conflict 분류가 먼저다 |

### 2. wait 신호와 business reject 신호를 분리한다

예를 들어 예약 경로라면 아래 둘은 같은 실패처럼 보이지만 뜻이 다르다.

- `SOLD_OUT`, `already exists`, `duplicate key`
- `lock wait timeout`, `threads awaiting connection`, wait ms 증가

첫 줄은 **이미 결론 난 경쟁**이고, 둘째 줄은 **줄이 길어진 경쟁**이다.

정상 sold-out 비율은 비슷한데 wait 시간만 치솟으면, 규칙 위반보다 queue shape가 먼저 문제일 수 있다.

### 3. 앱 풀 지표가 2차 증상인지 본다

guard-row lock wait가 길어지면:

- 트랜잭션이 오래 열린다
- 커넥션이 늦게 반환된다
- `active` 고정, `awaiting` 증가가 따라온다

그래서 `threads awaiting connection`만 보고 pool부터 키우면 오판할 수 있다.
시작점이 guard-row lock wait인지 먼저 봐야 한다.

## duplicate-key와 왜 다르게 읽나

duplicate-key는 보통 **기다린 끝에 진 것**보다 **이미 winner가 있었던 것**에 가깝다.

| 질문 | guard-row lock wait | duplicate-key conflict |
|---|---|---|
| 핵심 뜻 | 아직 gate 앞에서 기다린다 | 이미 누가 먼저 들어갔다 |
| 대표 신호 | `lock wait timeout`, wait ms 증가 | `1062`, `23505`, `DuplicateKeyException` |
| 첫 액션 | hot key와 blocker를 본다 | fresh read로 winner 의미를 분류한다 |
| 초보자 실수 | timeout을 `already exists`처럼 읽는다 | duplicate를 lock contention처럼 retry한다 |

즉 duplicate-key가 많다고 해서 guard-row 경합이 심하다고 단정하면 안 된다.
duplicate는 "이미 자리 있음", guard-row wait는 "같은 gate 줄이 김"이다.

## deadlock과 왜 다르게 읽나

deadlock은 hot key가 아니라 **잠금 순서 충돌**일 수 있다.

| 질문 | guard-row lock wait | deadlock |
|---|---|---|
| 대기 모양 | 한쪽이 오래 잡고 다른 쪽이 기다림 | 서로가 서로를 기다림 |
| 흔한 지표 | wait ms, timeout 수, top hot key | deadlock count, victim count |
| 로그 힌트 | 같은 key가 반복 등장 | 두 statement/path가 교차 등장 |
| 첫 액션 | 같은 guard key 집중도 확인 | canonical ordering 회귀 여부 확인 |

중요한 점:

- guard-row lock wait가 있다고 deadlock이 자동으로 나는 것은 아니다.
- deadlock count가 오르면 timeout 숫자보다 **잠금 순서가 path마다 달라졌는지**를 먼저 본다.

## generic slow query와 왜 다르게 읽나

slow query는 "잠겨서 느리다"가 아니라 "원래 오래 돈다"일 수 있다.

| 질문 | guard-row lock wait | generic slow query |
|---|---|---|
| 느려지는 이유 | 같은 key 앞 대기 시간 | 스캔 범위, 계획, I/O, 정렬 비용 |
| 먼저 볼 숫자 | wait ms, lock timeout, hot key concentration | query latency, rows examined, scan type |
| 로그 특징 | 특정 guard key 반복 | 특정 SQL fingerprint 반복 |
| 첫 액션 | blocker/key 집중 확인 | `EXPLAIN`, 인덱스, 범위 축소 확인 |

초보자용 안전 규칙:

1. `slow query`가 보여도 먼저 wait 시간이 포함된 느림인지 본다.
2. 같은 key 반복이 약하고 `rows_examined`가 크면 쿼리 자체 문제 가능성이 높다.
3. 같은 key 반복이 강하고 lock timeout이 같이 보이면 guard-row 쪽이 먼저다.

## 1분 판별 순서

1. `duplicate key`가 먼저 보이면 winner row 분류 경로로 간다.
2. `deadlock` 코드가 먼저 보이면 lock ordering 경로로 간다.
3. 둘 다 아니고 `lock wait timeout + 같은 guard key 반복`이 보이면 guard-row contention을 먼저 의심한다.
4. key 반복보다 slow SQL fingerprint와 scan 지표가 먼저 커지면 generic slow query를 먼저 의심한다.

## 아주 작은 관측 예시

```text
14:02:24  ERROR Lock wait timeout exceeded
/* update room_type_day_guard
   set reserved = reserved + 1
   where room_type_id = 17 and stay_day = '2026-05-05' */

14:02:24  WARN  top_wait_guard_key=room_type:17:2026-05-05 wait_count=83
14:02:24  INFO  duplicate_key_total=2 deadlock_total=0
```

이 장면의 초보자 해석:

- duplicate보다 wait가 중심이다
- deadlock보다 same-key 집중이 중심이다
- slow query보다 guard key queue가 중심이다

즉 첫 분류는 `room_type_id=17, stay_day=2026-05-05` guard row hot spot이다.

반대로 이런 장면이면 다르게 읽는다.

```text
14:02:24 ERROR duplicate key value violates unique constraint uq_coupon_claim
14:02:24 INFO  duplicate_key_total=91 lock_wait_timeout_total=0 deadlock_total=0
```

이때는 guard-row 관측보다 winner read / idempotency 분류가 먼저다.

## 자주 하는 오해

- `lock wait timeout`이 있으면 이미 winner가 있다는 뜻이다
  - 아니다. 아직 결론을 못 본 대기 실패일 수 있다.
- duplicate-key가 많으면 guard-row hot row다
  - 아니다. unique gate 충돌일 수 있고, wait 없는 winner conflict일 수 있다.
- slow query가 보이면 락 문제는 아니다
  - 아니다. lock wait가 포함된 느린 쿼리일 수 있다.
- deadlock과 lock wait는 timeout 숫자만 보면 구분된다
  - 아니다. deadlock 코드는 별도 bucket으로 봐야 한다.

## 한 줄 정리

guard-row 관측의 첫 질문은 "SQL이 느린가?"보다 **"같은 guard key 앞에 줄이 생겼는가?"**다. 그다음에야 duplicate-key의 winner conflict, deadlock의 lock ordering, generic slow query의 SQL 자체 문제를 분리하면 된다.
