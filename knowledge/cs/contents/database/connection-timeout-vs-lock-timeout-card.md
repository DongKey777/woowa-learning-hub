# Connection Timeout vs Lock Timeout 비교 카드

> 한 줄 요약: `connection timeout`은 **앱의 커넥션 풀 입구 대기 실패**, `lock timeout`은 **DB 내부 락 대기 실패**다.

**난이도: 🟢 Beginner**

관련 문서:

- [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md)
- [Timeout 로그 타임라인 체크리스트 카드](./timeout-log-timeline-first-failure-checklist-card.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [Pool-Timeout 용어 짝맞춤 카드](./pool-timeout-term-matching-card.md)
- [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md)
- [커넥션 풀 기초](./connection-pool-basics.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: connection timeout vs lock timeout, pool timeout vs db lock timeout, borrow timeout vs lock wait timeout, connection is not available lock wait timeout exceeded, connection timeout 뭐예요, lock timeout 뭐예요, timeout timeline first failure, 어떤 timeout이 먼저였는지, first failure timeout order, busy pool wait vs lock wait, busy 원인 분류, insert-if-absent busy lock timeout, transaction boundary long transaction external io hot key, 긴 트랜잭션 외부 io hot key 왜 busy, service busy classifier pool lock

## 먼저 멘탈모델

초보자는 timeout 이름보다 "어느 줄에서 기다리다 실패했는지"를 먼저 보면 된다.

- `connection timeout`: **앱 풀 대기줄**에서 커넥션을 못 빌림
- `lock timeout`: **DB 락 대기줄**에서 row/next-key 락을 못 얻음

둘 다 "대기 실패"지만, 대기하는 장소가 다르다.

## 1페이지 비교표

| 항목 | `connection timeout` (pool) | `lock timeout` (DB) |
|---|---|---|
| 실패 위치 | 애플리케이션 커넥션 풀 | DB 엔진 내부 락 매니저 |
| 대표 신호 | `Connection is not available` | `Lock wait timeout exceeded` |
| 무엇을 기다리나 | 반환된 커넥션 1개 | 잠긴 row/범위의 락 해제 |
| 초보자 첫 해석 | "좌석(커넥션)이 안 돌아온다" | "선행 트랜잭션이 락을 쥐고 있다" |
| 첫 점검 포인트 | 긴 트랜잭션, 트랜잭션 내부 외부 I/O, 풀 크기 대비 동시성 | 핫키 경쟁, 락 순서 불일치, 장기 트랜잭션 |

## 30초 선후관계 타임라인

둘 다 보이면 "무슨 timeout이 더 무서운가"보다 **어느 로그가 먼저 찍혔는가**로 먼저 자른다.

| 먼저 찍힌 로그 | 30초 해석 | pool timeout 의미 | 첫 확인 포인트 |
|---|---|---|---|
| `Connection is not available` -> 나중에 `lock wait timeout` | 시작점이 풀 입구 대기일 가능성이 크다 | **원인 후보**일 수 있다 | 긴 트랜잭션, 외부 I/O, 누수, 과도한 동시성 |
| `lock wait timeout` / `55P03` -> 나중에 `Connection is not available` | 시작점이 DB 락 경합일 가능성이 크다 | **2차 증상**일 수 있다 | blocker 트랜잭션, 같은 row/key 경쟁, hot row |

### 예시 A. pool timeout이 먼저인 경우

```text
10:00:01.100 HikariPool-1 - Pool stats (active=30, idle=0, waiting=12)
10:00:04.102 HikariPool-1 - Connection is not available, request timed out after 3000ms
10:00:04.500 order-service - external coupon API call finished after 2800ms
10:00:06.300 mysql - Lock wait timeout exceeded; try restarting transaction
```

읽는 법:

1. `10:00:04.102`에 이미 pool borrow 실패가 먼저 났다.
2. 앞쪽 힌트가 `active=30`, 외부 API 2.8초 지연이라서 커넥션 장기 점유 축이 더 가깝다.
3. 뒤에 나온 `lock wait timeout`은 별도 후행 사건일 수 있지만, 이 타임라인만 보면 pool timeout이 먼저 무너졌다.

### 예시 B. lock contention이 먼저이고 pool timeout은 2차 증상인 경우

```text
10:00:01.100 mysql - Lock wait timeout exceeded; try restarting transaction /* sku_id=44551 */
10:00:01.120 app - tx holding connection longer than usual for sku_id=44551
10:00:02.200 HikariPool-1 - Pool stats (active=30, idle=0, waiting=9)
10:00:04.205 HikariPool-1 - Connection is not available, request timed out after 3000ms
```

읽는 법:

## 30초 선후관계 타임라인 (계속 2)

1. `10:00:01.100`의 `lock wait timeout`이 먼저라서 시작점은 DB 안쪽 줄이다.
2. 그 뒤 커넥션 반환이 늦어져 `waiting=9`가 생기고, 마지막에 pool timeout이 따라왔다.
3. 이 경우 `connection timeout`은 원인이라기보다 **락 경합이 바깥으로 번진 결과**로 읽는 편이 맞다.

## `busy`로 번역됐을 때 30초 재분류

서비스가 같은 `busy`를 돌려줘도, 초보자는 아래처럼 **어디에서 막혔는지** 한 번 더 나누면 된다.

| 서비스 결과 | 실제 원인 신호 | 어디에서 기다렸나 | 첫 후속 문서 |
|---|---|---|---|
| `busy` | `Connection is not available`, `threads awaiting connection` | 앱 커넥션 풀 입구 | [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md) |
| `busy` | `Lock wait timeout exceeded`, `55P03`, MySQL `1205` | DB 내부 row/key 락 줄 | [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md) |

`insert-if-absent` 문맥에서는 이렇게 바로 연결하면 된다.

- `busy`인데 pool 신호가 먼저 보이면: "아직 DB winner를 본 것도 아니고, 커넥션부터 못 빌렸다"
- `busy`인데 lock timeout이 먼저 보이면: "DB 안까지는 들어갔지만 same key/row 경쟁에서 오래 막혔다"
- `duplicate key`와 다르게 둘 다 winner 확정 신호는 아니다. 분류 기준이 필요하면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)로 바로 이어서 본다.
- `lock timeout`인데 "그러면 blocker는 어디서 보지?"가 바로 궁금하면 [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md)로 이어서 본다.

## `busy` 뒤에 바로 보는 원인 카드

초보자가 가장 자주 헷갈리는 세 가지는 `긴 트랜잭션`, `트랜잭션 안의 외부 I/O`, `hot key`다.
셋을 따로 외우기보다 "`busy`가 transaction boundary를 오래 붙잡았나, 같은 key 줄을 길게 세웠나"로 같이 보면 분류가 빨라진다.

| 바로 보인 신호 | 초보자 원인 카드 | 왜 transaction boundary와 연결되나 | 첫 확인 포인트 |
|---|---|---|---|
| `Connection is not available`, `active=max`, `waiting>0` | 긴 트랜잭션 | 트랜잭션이 늦게 끝나면 커넥션 반환도 늦어진다 | 한 요청이 커넥션을 몇 초 잡는지 |
| pool timeout 직전 외부 API/파일 I/O 로그가 길다 | 트랜잭션 안의 외부 I/O | DB 작업이 끝났어도 commit 전까지 커넥션과 락을 같이 붙잡을 수 있다 | 외부 호출을 트랜잭션 밖으로 뺄 수 있는지 |
| `Lock wait timeout exceeded`, `55P03`, 같은 `sku_id`/`seat_id` 반복 | hot key | 같은 row/key에 요청이 몰리면 뒤 트랜잭션이 같은 지점을 계속 기다린다 | 어떤 key가 가장 자주 막히는지 |

짧게 연결하면 이렇게 읽으면 된다.

- pool 쪽 `busy`면: "트랜잭션 boundary가 너무 길어서 입구가 막혔나?"
- lock 쪽 `busy`면: "같은 key 줄이 길어졌나, 아니면 blocker가 오래 안 끝났나?"
- 외부 I/O는 둘 다 악화시킬 수 있다. 트랜잭션 안에 있으면 커넥션 반환도 늦추고, 이미 잡은 락도 더 오래 유지할 수 있다.

엔진과 프레임워크에 따라 락 이름이나 timeout 표시는 다를 수 있지만, 초보자 첫 분류는 대체로 같다.
`MySQL/InnoDB`, PostgreSQL, Spring/JPA 모두에서 **짧게 끝나야 할 transaction boundary가 길어졌는지**를 먼저 보면 큰 방향은 잘 맞는다.

## 자주 헷갈리는 포인트

- "`connection timeout` = DB lock 문제" -> 항상 아니다. 앱에서 커넥션을 오래 잡아도 발생한다.
- "`lock timeout`이면 풀 설정만 조정하면 된다" -> 보통 아니다. 락 경쟁 쿼리/순서를 먼저 봐야 한다.
- "`lock timeout`이면 이미 다른 요청이 성공했겠지" -> 아니다. 이 오해는 [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)처럼 먼저 `busy`로 고정해 두면 줄어든다.
- "둘 다 timeout이니 같은 튜닝" -> 다르다. 하나는 풀 운영, 하나는 동시성 제어 문제다.

## 30초 분류 체크

1. 로그에서 어떤 timeout이 먼저 나왔는지 시각 순서로 나눈다.
2. `connection timeout`이 선행이면 커넥션 점유 시간과 풀 지표를 먼저 본다.
3. `lock timeout`이 선행이면 pool timeout을 바로 원인으로 단정하지 말고, 블로커 트랜잭션과 경쟁 SQL을 먼저 본다.

로그 타임라인 자체를 더 자세히 나눠 봐야 하면 [Timeout 로그 타임라인 체크리스트 카드](./timeout-log-timeline-first-failure-checklist-card.md)로 이어서 본다.

## 한 줄 정리

`connection timeout`은 **풀 좌석 대기 실패**, `lock timeout`은 **DB 락 줄 대기 실패**다. 같은 timeout으로 묶지 말고 실패 위치를 먼저 분리하자.
