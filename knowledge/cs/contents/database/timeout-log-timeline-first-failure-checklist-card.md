# Timeout 로그 타임라인 체크리스트 카드

> 한 줄 요약: timeout 사건에서는 "무슨 에러가 있었나"보다 먼저 **어느 줄이 먼저 막혔는지**를 시간순으로 나눠 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md)
- [Pool-Timeout 용어 짝맞춤 카드](./pool-timeout-term-matching-card.md)
- [타임아웃 튜닝 순서 체크리스트 카드](./timeout-tuning-order-checklist-card.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: timeout log timeline checklist, first failure timeout timeline, which timeout happened first, connection timeout lock timeout order, statement timeout timeline card, lock wait timeout first check, timeout incident timeline checklist, beginner timeout incident card, 타임아웃 로그 타임라인 체크리스트, 무엇이 먼저 터졌는지, 어떤 timeout이 먼저였는지, 로그 시간순 판별, connection timeout lock timeout 순서, statement timeout 먼저 확인, 락웨이트 타임아웃 선행, timeout 사건 초보자 체크리스트

## 먼저 멘탈모델

초보자는 timeout 사건을 보면 에러 이름부터 모으기 쉽다.
하지만 복구 시작점은 "이름 목록"보다 **막힘의 시작 시각**이다.

- `connection timeout`: 앱 **입구 줄**에서 못 들어감
- `lock wait timeout`: DB **안쪽 줄**에서 못 지나감
- `statement timeout`: 이미 실행 중인 SQL이 **예산 시간**을 넘김

핵심 질문은 하나다.

> "맨 처음 느려진 곳이 어디인가?"

## 30초 판단 표

| 먼저 찍힌 신호 | 초보자 첫 해석 | 다음으로 볼 것 |
|---|---|---|
| `threads awaiting connection`, `Connection is not available` | 풀 입구가 먼저 막혔다 | 긴 트랜잭션, 외부 I/O, 커넥션 장기 점유 |
| `Lock wait timeout exceeded` | DB 안 락 줄이 먼저 막혔다 | blocker 트랜잭션, 같은 key 반복, hot row |
| `statement timeout`, query cancel | SQL 자체가 오래 달리거나 오래 붙잡혔다 | `EXPLAIN`, scan/sort, 락 대기 동반 여부 |

## 로그 타임라인 5단계 체크리스트

### 1. 로그를 한 줄로 섞지 말고 시각 순서로 다시 적는다

- 앱 로그, pool 로그, DB 에러 로그를 같은 시각축에 놓는다.
- 초 단위만 있으면 밀릴 수 있으니 가능하면 밀리초까지 본다.

질문:

- 첫 `WARN/ERROR`가 어디서 나왔나?
- 그 직전에 `active/idle/waiting` 숫자가 어떻게 변했나?

### 2. "증상"과 "원인 후보"를 분리한다

- `threads awaiting connection`은 보통 **입구에서 보이는 증상**이다.
- `lock wait timeout`은 보통 **DB 내부 경합의 직접 신호**다.
- `statement timeout`은 **느린 실행** 또는 **락 대기로 길어진 실행** 둘 다 가능하다.

짧게 기억:

- pool 로그 = 바깥 증상
- lock 로그 = 안쪽 원인 후보
- statement 로그 = 느림 축 추가 확인 필요

### 3. 가장 먼저 등장한 timeout 종류를 고정한다

| 먼저 나온 로그 | 1차 분류 | 초보자 첫 액션 |
|---|---|---|
| `Connection is not available` | 풀 선행 | 커넥션 점유 시간이 왜 길어졌는지 본다 |
| `Lock wait timeout exceeded` | 락 선행 | 같은 row/key blocker를 찾는다 |
| `statement timeout` | 실행 지연 선행 | 느린 SQL인지 락 대기 동반인지 분리한다 |

주의:

- 나중에 더 큰 에러가 보여도, **먼저 나온 신호**를 지우면 안 된다.
- 마지막에 터진 에러가 가장 근본 원인이라는 보장은 없다.

### 4. "연쇄"인지 "별도 사건"인지 본다

대표 연쇄 패턴:

1. `lock wait timeout` 선행
2. 트랜잭션이 길어짐
3. 커넥션 반환 지연
4. `threads awaiting connection`
5. `connection timeout`

이 패턴이면 pool timeout은 2차 결과일 수 있다.

반대 패턴:

1. 외부 API 지연 또는 긴 트랜잭션 선행
2. `active` 고정, `waiting` 증가
3. `connection timeout`
4. DB lock 에러는 거의 없음

이 패턴이면 시작점은 pool/점유 시간 축일 가능성이 높다.

### 5. 첫 신호 기준으로 다음 문서를 고른다

| 첫 신호 | 다음 문서 | 이유 |
|---|---|---|
| pool timeout 선행 | [타임아웃 튜닝 순서 체크리스트 카드](./timeout-tuning-order-checklist-card.md) | 긴 트랜잭션, 외부 I/O, 풀 설정 순서를 바로 따라갈 수 있다 |
| lock timeout 선행 | [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md) | pool 결과와 lock 시작점을 한 번 더 분리해 준다 |
| statement timeout 선행 | [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md) | 느린 SQL과 락 대기를 다시 나눌 수 있다 |

## 작은 예시

```text
14:02:13.104 WARN  HikariPool-1 - Pool stats (active=20, idle=0, waiting=7)
14:02:24.227 ERROR HikariPool-1 - Connection is not available, request timed out after 10000ms
14:02:24.231 ERROR mysql - Lock wait timeout exceeded; try restarting transaction
14:02:24.233 WARN  HikariPool-1 - Pool stats (active=20, idle=0, waiting=19)
```

### 이 예시를 초보자 기준으로 읽으면

| 시각 | 보이는 것 | 해석 |
|---|---|---|
| `14:02:13.104` | `waiting=7` | 이미 풀 입구 대기가 시작됐다 |
| `14:02:24.227` | `connection timeout` | 일부 요청이 입구에서 먼저 실패했다 |
| `14:02:24.231` | `lock wait timeout` | 다른 요청은 DB 안에서 락 줄에 막혀 있었다 |
| `14:02:24.233` | `waiting=19` | 내부 막힘 때문에 입구 대기가 더 커졌다 |

첫 결론:

- "맨 마지막 에러"는 `lock wait timeout`이지만
- "먼저 실패한 요청"은 `connection timeout`이었다

그래서 이 사건의 첫 질문은 둘 중 하나를 고르는 것이다.

- "입구에서 먼저 죽은 요청을 줄일까?"
- "안쪽 락 경합을 줄여 전체 대기를 꺼낼까?"

실무에서는 둘 다 보지만, **타임라인상 먼저 무너진 지점**을 고정해야 대응 순서가 덜 흔들린다.

## 자주 헷갈리는 포인트

- "`lock wait timeout`이 더 근본적이니 무조건 첫 사건이다" -> 아닐 수 있다. 먼저 실패한 요청은 pool timeout일 수 있다.
- "`connection timeout`이 먼저 찍혔으니 DB는 무관하다" -> 아닐 수 있다. 내부 락 경합이 뒤에서 커넥션 반환을 늦췄을 수 있다.
- "`statement timeout`이면 항상 느린 쿼리다" -> 아니다. 락 대기로 statement 예산을 먼저 써 버릴 수도 있다.
- "같은 초에 찍혔으면 아무거나 먼저 봐도 된다" -> 가능하면 밀리초, thread, SQL 키까지 붙여 다시 본다.

## 초보자용 한 줄 절차

1. 로그를 시각순으로 다시 적는다.
2. 첫 timeout 종류를 고정한다.
3. 그 timeout이 pool, lock, statement 중 어디 줄인지 분류한다.
4. 연쇄 패턴인지 확인한다.
5. 그다음에만 timeout 값 조정을 고민한다.

## 한 줄 정리

timeout 사건에서 중요한 것은 "무슨 이름의 에러가 있었는가"보다 **어느 대기줄이 먼저 무너졌는가**다. 로그 타임라인을 먼저 고정하면 대응 순서가 흔들리지 않는다.
