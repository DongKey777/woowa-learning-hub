# Pool-Timeout 용어 짝맞춤 카드

> 한 줄 요약: `connection timeout`은 **앱 풀 입구 대기**, `transaction timeout`은 **작업 전체 시간 초과**, `statement timeout`은 **SQL 1개 실행 시간 초과**, `lock wait timeout`은 **DB 락 줄 대기 시간 초과**다.

**난이도: 🟢 Beginner**

관련 문서:

- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md)
- [커넥션 풀 기초](./connection-pool-basics.md)
- [HikariCP 튜닝](./hikari-connection-pool-tuning.md)
- [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: pool timeout term matching, timeout terminology card, connection timeout vs transaction timeout vs statement timeout vs lock wait timeout, borrow timeout, jdbc statement timeout, spring transaction timeout, innodb lock wait timeout, timeout confusion beginner, pool timeout 오해, lock wait timeout pool confusion, app wait vs db lock wait, app waiting vs db waiting, hot row timeout misunderstanding, lock wait timeout hot row beginner, 커넥션 타임아웃 트랜잭션 타임아웃 스테이트먼트 타임아웃 락웨이트 타임아웃 차이

## 먼저 멘탈모델

초보자는 timeout 이름보다 "어느 대기줄에서 시간이 끝났는가"를 먼저 잡으면 덜 헷갈린다.

- `connection timeout`: **앱 풀 입구**에서 커넥션을 빌리며 기다린 시간
- `transaction timeout`: **작업 전체**가 끝나기를 기다린 시간
- `statement timeout`: **SQL 1개 실행 구간**에서 걸린 시간
- `lock wait timeout`: **DB 내부 락 대기 줄**에서 기다린 시간

짧게 외우면:

- 앱 입구에서 못 들어감 -> `connection timeout`
- 작업 전체가 너무 김 -> `transaction timeout`
- SQL 1개가 너무 긺 -> `statement timeout`
- DB 안에서 앞 트랜잭션이 안 비킴 -> `lock wait timeout`

즉, 같은 timeout이라도 **시계가 도는 위치**가 다르다.

## 4신호 한 장 비교표

| 용어 | 시간 재는 위치 | 무엇을 기다리거나 실행하나 | 주로 보이는 신호 | 초보자 첫 해석 |
|---|---|---|---|---|
| `connection timeout` | 커넥션 풀에서 `getConnection()` 대기 | 반환된 커넥션 1개 | `Connection is not available`, `threads awaiting connection` | "앱 입구에서 좌석을 못 빌렸다" |
| `transaction timeout` | 트랜잭션/작업 전체 시간 | 비즈니스 작업 전체 종료 | Spring `@Transactional(timeout)`, tx timeout rollback | "일 전체가 예산 안에 안 끝났다" |
| `statement timeout` | SQL 문장 1개 실행 시간 | SQL 1개 완료 | query cancel, `statement timeout`, `SQLTimeoutException` | "이 SQL 1개가 너무 오래 붙잡혔다" |
| `lock wait timeout` | DB row/next-key 락 대기 | 필요한 락 해제 | `Lock wait timeout exceeded`, `55P03` 계열 | "DB 안에서 앞 트랜잭션이 길을 막았다" |

## 먼저 이렇게 나누면 덜 헷갈린다

| 초보자 질문 | 먼저 볼 신호 |
|---|---|
| "아직 DB 안에도 못 들어간 건가?" | `connection timeout` |
| "DB는 들어갔는데 전체 작업이 너무 긴 건가?" | `transaction timeout` |
| "SQL 1개가 자체적으로 너무 긴 건가?" | `statement timeout` |
| "SQL이 락 때문에 앞차를 기다린 건가?" | `lock wait timeout` |

특히 이 카드의 핵심은 아래 둘을 분리하는 것이다.

- `connection timeout` = **앱 대기**
- `lock wait timeout` = **DB lock 대기**

둘이 같은 시각에 보여도 같은 층에서 기다린 것이 아니다.

## 작은 예시: 4신호를 한 흐름에 놓기

주문 API가 아래 순서로 흔들린다고 하자.

1. 요청 A가 같은 `sku_id` row를 오래 잡는다.
2. 요청 B, C는 DB 안에서 그 row 락을 기다리다가 `lock wait timeout`을 본다.
3. 이 요청들이 커넥션을 오래 쥔 채 못 끝나서 뒤 요청 D, E는 풀 입구에서 `connection timeout`을 본다.
4. 어떤 요청은 외부 결제 호출까지 트랜잭션 안에 넣어 전체 작업이 5초를 넘어 `transaction timeout`이 난다.
5. 반대로 락이 없어도 보고서 SQL이 혼자 8초를 써서 `statement timeout`이 날 수 있다.

초보자용 읽는 순서:

1. 앱 입구에서 못 막혔는지 (`connection timeout`)
2. DB 안에서 락 줄에 막혔는지 (`lock wait timeout`)
3. 락이 아니라 SQL 1개가 느린지 (`statement timeout`)
4. 그 위에서 작업 전체 예산까지 넘었는지 (`transaction timeout`)

## 앱 대기와 DB lock 대기만 빠르게 떼어내는 표

| 지금 먼저 보인 것 | 아직 DB 안에 들어갔나 | 어디에서 기다렸나 | 첫 후속 문서 |
|---|---|---|---|
| `Connection is not available` | 아직 아니다 | 앱 커넥션 풀 입구 | [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md) |
| `Lock wait timeout exceeded`, `55P03` | 이미 들어갔다 | DB 내부 row/key 락 줄 | [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md), [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |

hot row 감각이 아직 약하면 [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)로 "같은 key 반복 경합" 그림을 먼저 잡는 편이 빠르다.

## 가장 흔한 오해 5개

- "`connection timeout`이면 곧바로 DB lock 문제다" -> 아니다. 외부 I/O 때문에 커넥션 반환이 늦어져도 난다.
- "`lock wait timeout`이면 풀 크기를 키우면 된다" -> 보통 아니다. 먼저 같은 row/key 경쟁을 본다.
- "`statement timeout`이면 무조건 인덱스 문제다" -> 아니다. 락 대기로 SQL이 오래 붙잡혀도 보일 수 있다.
- "`transaction timeout`과 `statement timeout`은 같다" -> 아니다. 하나는 작업 전체, 하나는 SQL 1개 시간이다.
- "넷 다 timeout이니 한 값만 늘리면 된다" -> 아니다. 실패 위치가 달라서 대응도 달라야 한다.

## 30초 대응 순서

1. `Connection is not available`가 먼저면 풀 점유 시간을 본다.
2. `Lock wait timeout exceeded`가 먼저면 blocker 트랜잭션과 hot key를 본다.
3. `statement timeout`이 먼저면 SQL 범위, 정렬, `EXPLAIN`을 본다.
4. `transaction timeout`이 먼저면 트랜잭션 경계와 외부 I/O 포함 여부를 본다.

로그 타임라인 자체를 먼저 다시 세우고 싶으면 [Timeout 로그 타임라인 체크리스트 카드](./timeout-log-timeline-first-failure-checklist-card.md)로 이어서 보면 된다.

## 한 줄 정리

`connection timeout`은 **앱 풀 입구 대기**, `transaction timeout`은 **작업 전체 시간 초과**, `statement timeout`은 **SQL 실행 구간**, `lock wait timeout`은 **DB 락 대기 줄**이다. 특히 초보자는 `connection timeout`과 `lock wait timeout`을 같은 대기로 보지 말고, **앱 대기인지 DB lock 대기인지**부터 먼저 분리하면 된다.
