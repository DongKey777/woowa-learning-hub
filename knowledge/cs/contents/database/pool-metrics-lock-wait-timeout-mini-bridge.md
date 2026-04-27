# Pool 지표 읽기 미니 브리지 (active/idle/awaiting + lock wait timeout)

> 한 줄 요약: `active/idle/awaiting`는 "풀 좌석 상태", `lock wait timeout`은 "DB 내부 줄 막힘" 신호라서 같은 문제처럼 보여도 원인 축이 다르다.

**난이도: 🟢 Beginner**

관련 문서:

- [커넥션 풀 기초](./connection-pool-basics.md)
- [트랜잭션·락·커넥션 풀 첫 그림](./transaction-locking-connection-pool-primer.md)
- [Timeout 로그 타임라인 체크리스트 카드](./timeout-log-timeline-first-failure-checklist-card.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [HikariCP 튜닝](./hikari-connection-pool-tuning.md)
- [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: pool metrics mini bridge, active idle awaiting meaning, threads awaiting connection, hikaricp active idle pending, lock wait timeout pool confusion, pool exhaustion vs lock contention, connection timeout vs lock wait timeout, lock contention entrypoint, hot row identification starter, pool log timeline example, threads awaiting connection log example, lock wait timeout log timeline, lock wait timeout timeline walkthrough, 커넥션 풀 지표 읽기, active idle awaiting 해석, lock wait timeout 오해, 락 경합 시작점 찾기, hot row 식별 입문, DB 좌석 비유, pool 대기 vs 락 대기 구분, 로그 타임라인 해석 예시, threads awaiting connection 로그 읽기, lock wait timeout 로그 읽기, first failure timeline, 무엇이 먼저 터졌는지, timeout 사건 타임라인

## 먼저 멘탈모델

초보자는 용어보다 그림부터 잡는 게 빠르다.

- 커넥션 풀: **식당 입구 좌석 관리** (`active/idle/awaiting`)
- DB 락 대기: **주방 안 조리 순서 충돌** (`lock wait timeout`)

즉, "입구 줄이 길다"와 "주방이 서로 기다려 멈췄다"는 연결될 수는 있지만 같은 원인 이름이 아니다.

## 한 표로 연결해서 읽기

| 지금 보이는 신호 | 어디에서 생긴 신호인가 | 흔한 오해 | 초보자 첫 해석 |
|---|---|---|---|
| `active` 증가 | 앱 커넥션 풀 | "DB CPU가 높다는 뜻" | 커넥션이 많이 점유 중이라는 뜻이다 |
| `idle` 거의 0 | 앱 커넥션 풀 | "무조건 풀 사이즈를 늘리면 해결" | 먼저 점유 시간이 왜 길어졌는지 본다 |
| `awaiting` 증가 (`threads awaiting connection`) | 앱 커넥션 풀 대기열 | "풀 자체 버그" | 빌릴 연결이 없어서 입구에서 기다리는 상태다 |
| `Connection is not available` / borrow timeout | 앱에서 풀 대기 초과 | "DB가 죽었다" | 풀 대기가 임계치를 넘었다는 뜻이다 |
| `lock wait timeout` | DB 내부 row/next-key 락 대기 | "커넥션 풀이 작아서 발생" | 락 경쟁으로 SQL이 진행 못 한 상태다 |

핵심 연결:

- 락 대기가 길어지면 트랜잭션이 길어지고, 그동안 커넥션이 반환되지 않아 `active`가 유지된다.
- 그래서 `awaiting`와 `lock wait timeout`이 **같이 보일 수는 있어도** 시작 원인은 서로 다를 수 있다.

## 30초 증상-원인 브리지

| 증상 묶음 | 더 가능성 높은 시작점 | 먼저 확인할 것 |
|---|---|---|
| `awaiting`만 급증, DB 락 에러는 거의 없음 | 느린 쿼리/긴 트랜잭션/외부 I/O로 커넥션 장기 점유 | 트랜잭션 안 외부 호출, p95 쿼리 시간 |
| `lock wait timeout`이 늘고 동시에 `active`가 높게 고정 | 동일 row/key 경합(락 병목) | 어떤 SQL/키에서 대기 집중되는지 |
| `idle` 충분한데 간헐 `lock wait timeout` | 풀 크기보다 락 순서/경합 문제 | 업데이트 순서, hot row 존재 여부 |

## 락 경합 시작점 1분 라우트 (hot row 입문)

`lock wait timeout + active 고정` 패턴이 보이면, 아래 순서로 시작하면 초보자 시행착오가 줄어든다.

| 지금 상황 | 첫 문서 | 이유 |
|---|---|---|
| 같은 key/row가 반복해서 막히는 것 같음 | [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md) | hot row 판단 기준(같은 key 반복, p99 상승, scale-out 무효)을 초급 눈높이로 먼저 잡아 준다 |
| 이미 장애 대응 중이라 deadlock/latch까지 섞여 보임 | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) | lock wait vs deadlock vs latch를 운영 절차 기준으로 분리해 준다 |

자주 헷갈리는 지점:

- "`lock wait timeout`만 보이면 바로 풀 튜닝부터" -> 먼저 hot row 여부(같은 key 반복)를 확인한다.
- "SQL이 느리니까 무조건 인덱스 문제" -> 락 대기 시간이 길어져 느려 보일 수 있다.
- "앱 인스턴스를 늘리면 자동 해결" -> hot row면 대기열만 더 길어질 수 있다.

## 작은 예시

상황:

- `maximumPoolSize=20`
- 평소 `active=6`, `idle=14`, `awaiting=0`
- 장애 시점 `active=20`, `idle=0`, `awaiting=35`
- 같은 시각 DB 에러 로그에 `lock wait timeout` 다수

초보자용 해석 순서:

1. 풀 고갈은 결과로 확인된다 (`active=20`, `awaiting=35`).
2. 그런데 DB에서 `lock wait timeout`이 함께 증가했으므로, 시작점은 "락 경합" 가능성이 높다.
3. 이때 풀만 20->40으로 키우면 대기열만 뒤로 밀리고 락 경합 자체는 남을 수 있다.

## 실제형 로그 타임라인 1세트

아래는 초보자가 가장 많이 헷갈리는 조합인 `threads awaiting connection` + `lock wait timeout`을 한 번에 읽는 예시다.

```text
2026-04-24 14:02:11.842  INFO [checkout-api] [http-nio-8080-exec-17]
com.zaxxer.hikari.pool.HikariPool : HikariPool-1 - Pool stats (total=20, active=18, idle=2, waiting=0)

2026-04-24 14:02:13.104  WARN [checkout-api] [http-nio-8080-exec-31]
com.zaxxer.hikari.pool.HikariPool : HikariPool-1 - Pool stats (total=20, active=20, idle=0, waiting=7)

2026-04-24 14:02:13.104  WARN [checkout-api] [http-nio-8080-exec-31]
com.example.order.OrderService : threads awaiting connection increased: 7

2026-04-24 14:02:24.227 ERROR [checkout-api] [http-nio-8080-exec-08]
org.springframework.jdbc.CannotGetJdbcConnectionException:
HikariPool-1 - Connection is not available, request timed out after 10000ms.

2026-04-24 14:02:24.231 ERROR [mysql] [trx-778421]
SQLSTATE[HY000]: General error: 1205 Lock wait timeout exceeded; try restarting transaction
/* update inventory set reserved = reserved + 1 where sku_id = 44551 */

2026-04-24 14:02:24.233  WARN [checkout-api] [http-nio-8080-exec-44]
com.zaxxer.hikari.pool.HikariPool : HikariPool-1 - Pool stats (total=20, active=20, idle=0, waiting=19)
```

### 타임라인을 5단계로 읽기

| 시각 | 보이는 로그 | 초보자 해석 |
|---|---|---|
| `14:02:11` | `active=18, idle=2, waiting=0` | 아직 풀은 버티고 있다. 이 시점만 보면 큰 문제처럼 안 보일 수 있다. |
| `14:02:13` | `active=20, idle=0, waiting=7` | 이제 풀 좌석이 모두 찼고, 일부 요청은 입구에서 대기 중이다. |
| `14:02:24.227` | `Connection is not available` | 기다리던 요청 일부가 풀에서 커넥션을 못 빌리고 타임아웃 났다. |
| `14:02:24.231` | `Lock wait timeout exceeded` | 다른 요청은 커넥션은 이미 빌렸지만, DB 안에서 같은 `sku_id=44551` 락을 기다리다 실패했다. |
| `14:02:24.233` | `waiting=19` | 락 대기로 커넥션 반환이 늦어지면서 입구 대기열이 더 커졌다. |

### 이 로그에서 먼저 내려야 할 결론

1. `threads awaiting connection`은 "입구 대기"다.
2. `lock wait timeout`은 "주방 안 락 대기"다.
3. 둘이 같은 시각에 보였지만, 더 시작점에 가까운 신호는 `sku_id=44551`에 몰린 락 경합이다.
4. 따라서 첫 대응은 pool size 확대보다 "왜 같은 키 업데이트가 오래 잡히는가" 확인이다.

같은 사건에서 "`무엇이 먼저 터졌는지`"를 요청 단위로 더 엄밀히 나누고 싶다면 [Timeout 로그 타임라인 체크리스트 카드](./timeout-log-timeline-first-failure-checklist-card.md)를 같이 본다.

### 한 줄씩 왜 그렇게 읽는가

- `active=20, idle=0`:
  풀 숫자만 보면 "좌석이 꽉 찼다"는 사실만 보인다. 원인은 아직 모른다.
- `threads awaiting connection increased`:
  커넥션을 못 빌린 스레드가 생겼다는 뜻이다. 이것도 원인보다 결과에 가깝다.
- `Connection is not available`:
  기다리던 쪽이 먼저 실패하기 시작했다는 뜻이다. 실패 레이어는 앱 풀이다.
- `Lock wait timeout exceeded`:
  이미 커넥션을 점유한 트랜잭션이 DB 내부에서 막혔다는 뜻이다. 실패 레이어는 DB 락이다.
- 같은 `sku_id` 업데이트:
  초보자는 여기서 "같은 row/key로 몰리는 hot row인가?"를 가장 먼저 의심하면 된다.

## 이 예시에서 흔한 오해

- "`Connection is not available`이 먼저 보였으니 pool만 키우면 된다" -> 아니다. 뒤이어 나온 `lock wait timeout`이 더 근본 원인일 수 있다.
- "`lock wait timeout`이 있으니 기다린 요청도 전부 같은 에러를 받는다" -> 아니다. 어떤 요청은 DB까지 못 들어가고 pool timeout으로 끝난다.
- "`waiting` 숫자가 크면 DB는 한가한 상태다" -> 아니다. DB 안 락 대기 때문에 앱 입구까지 막혔을 수 있다.
- "둘 다 timeout이라 retry만 넣으면 된다" -> lock timeout은 경합 완화가 먼저고, pool timeout은 점유 시간 축소가 먼저다.

## 자주 하는 오해 4개

- "`awaiting`이 늘면 항상 풀 설정 문제다" -> 아니다. 락/느린 쿼리/긴 트랜잭션의 2차 증상일 수 있다.
- "`lock wait timeout`은 풀이 작아서 난다" -> 보통은 DB 내부 락 경쟁 신호다.
- "`idle=0`이면 무조건 `maximumPoolSize`를 키워야 한다" -> 먼저 점유 시간을 줄일 수 있는지 본다.
- "둘 다 timeout이니까 같은 튜닝으로 해결된다" -> pool timeout과 lock timeout은 실패 레이어가 다르다.

## 초보자용 3단계 체크

1. 풀 신호 확인: `active/idle/awaiting`, borrow timeout 여부.
2. DB 락 신호 확인: `lock wait timeout`, deadlock, 대기 SQL 키.
3. 순서 결정: 풀 사이즈 조정보다 먼저 "점유 시간 단축"과 "락 경합 완화"를 우선 검토.

## 한 줄 정리

`active/idle/awaiting`는 **커넥션 좌석 상태**, `lock wait timeout`은 **DB 락 경쟁 상태**다. 같이 보여도 같은 원인으로 단정하지 말고, "풀 결과"와 "락 시작점"을 분리해서 읽어야 오해가 줄어든다.
