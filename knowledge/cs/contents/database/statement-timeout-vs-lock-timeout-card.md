# Statement Timeout vs Lock Timeout 비교 카드

> 한 줄 요약: `statement timeout`이 보여도 먼저 **락을 기다린 시간인지**, **SQL 실행 자체가 느린 시간인지**부터 분리해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md)
- [EXPLAIN 첫 판독 미니카드](./explain-first-read-timeout-mini-card.md)
- [Pool-Timeout 용어 짝맞춤 카드](./pool-timeout-term-matching-card.md)
- [Timeout 로그 타임라인 체크리스트 카드](./timeout-log-timeline-first-failure-checklist-card.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [Spring 트랜잭션 기본](../spring/spring-transactional-basics.md)
- [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: statement timeout vs lock timeout, statement timeout first check, statement timeout lock wait or slow query, query timeout vs lock wait timeout, sql timeout vs row lock wait, postgres 57014 55p03 timeline, mysql statement timeout lock wait timeout, beginner timeout card, 실행 지연 vs 락 대기 지연, statement timeout 먼저 무엇을 보나, statement timeout 뭐예요, 57014 55p03 same request, 느린 sql vs 막힌 sql, lock wait vs slow query, lock timeout basics

## 먼저 멘탈모델

초보자는 `statement timeout`이라는 이름만 보면 바로 "느린 쿼리다"로 닫기 쉽다.
하지만 첫 분류는 이름이 아니라 **시간이 어디서 쓰였는가**다.

- lock 대기 시간: **앞 트랜잭션이 비켜 주길 기다린 시간**
- 실행 시간: **내 SQL이 row를 읽고 정렬하고 갱신하느라 쓴 시간**

짧게 외우면:

- `statement timeout` = 실행 시간 예산 초과
- `lock timeout` = 락 대기 지연

## 10초 그림

| 상황 | 머릿속 그림 | 먼저 떠올릴 질문 |
|---|---|---|
| `statement timeout` | "내 쿼리가 혼자 달리는데 너무 오래 간다" | 왜 이렇게 많은 row를 읽거나 정렬하지? |
| `lock timeout` | "내 쿼리가 앞차가 비키길 기다리다가 멈춘다" | 누가 같은 row/key를 오래 잡고 있지? |

## 1분 우선 점검 카드

`statement timeout`이 먼저 보였을 때도 아래 3줄부터 확인하면 초보자가 덜 헤맨다.

| 먼저 확인할 것 | `lock wait` 쪽에 더 가까운 신호 | `slow query` 쪽에 더 가까운 신호 |
|---|---|---|
| 평소 속도 | 평소 10~20ms인데 특정 경쟁 때만 느려진다 | 혼자 실행해도 자주 느리다 |
| 로그 앞줄 | `55P03`, `lock wait timeout`, `could not obtain lock`가 먼저 보인다 | lock 신호 없이 `57014`, `query canceled`, 큰 scan/sort 로그가 보인다 |
| 첫 액션 | blocker 트랜잭션, 같은 key 반복, 긴 트랜잭션부터 본다 | `EXPLAIN`, 읽는 row 수, 정렬/임시 테이블부터 본다 |

핵심 질문은 하나다.

> "이 시간은 남을 기다린 시간인가, 내가 실행하느라 쓴 시간인가?"

## 1페이지 비교표

| 항목 | `statement timeout` | `lock timeout` |
|---|---|---|
| 초보자 첫 해석 | "이 요청의 statement 예산이 다 닳았다" | "다른 트랜잭션이 길을 막고 있다" |
| 먼저 던질 질문 | "혼자 돌려도 느린가?" | "누가 같은 key를 오래 잡고 있나?" |
| 주된 지연 원인 | 넓은 scan, 정렬, 큰 UPDATE, 느린 실행 계획 | hot row, 긴 트랜잭션, 락 순서 충돌, blocker 미종료 |
| 시간이 쓰인 곳 | SQL 실행 시간 | 락 해제 대기 시간 |
| 무엇을 기다리나 | SQL 1개가 끝나기만 기다림 | 필요한 row/range 락이 풀리길 기다림 |
| 로그 힌트 | `57014`, `query canceled`, scan/sort 흔적 | `55P03`, `lock wait timeout`, `could not obtain lock` |
| 먼저 볼 것 | `EXPLAIN`, 읽는 row 수, 정렬/임시 테이블 | blocker 트랜잭션, 같은 key 반복 경합, lock wait 로그 |
| 초보자용 3버킷 | `query-too-slow` | `busy` |

## 같은 예시로 둘을 나눠 보기

같은 SQL 하나로도 두 갈래가 나온다.

```sql
UPDATE seats
SET status = 'HELD'
WHERE concert_id = 7 AND seat_no = 'A-10';
```

| 같은 SQL인데 다른 상황 | 더 가까운 분류 | 초보자 첫 질문 |
|---|---|---|
| 혼자 실행해도 여러 row를 훑거나 정렬 때문에 5초 넘게 돈다 | `statement timeout` | "이 SQL이 왜 이렇게 오래 실행되지?" |
| 평소엔 20ms인데 다른 트랜잭션이 같은 좌석 row를 잡고 있어 기다리다 끝난다 | `lock timeout` | "누가 이 row를 먼저 잡고 있지?" |

핵심은 SQL 문장이 아니라 **시간이 어디서 소모됐는지**다.

## 작은 예시

위 `UPDATE seats ...`를 같은 화면에서 눌렀다고 가정하자.

| 상황 | 로그/관찰 | 읽는 법 |
|---|---|---|
| 인덱스가 맞지 않아 좌석 row를 찾는 데 오래 걸린다 | `statement timeout`, `query canceled` | 쿼리 자체가 느리다. `EXPLAIN`과 읽는 row 수를 먼저 본다 |
| 운영자가 같은 좌석을 수정 중이라 row lock이 안 풀린다 | `lock wait timeout exceeded`, `could not obtain lock` | 다른 트랜잭션을 기다린다. blocker와 긴 트랜잭션을 먼저 본다 |

공유 예시로 기억하면 쉽다.

- 같은 SQL이어도 `혼자 달려도 느리면` `statement timeout`
- 같은 SQL이어도 `남이 비켜야 끝나면` `lock timeout`

## 같은 요청에서 `57014`와 `55P03`가 같이 보일 때

초보자가 가장 많이 헷갈리는 장면은 "한 요청 안에서 둘 다 보였다"는 로그다. 이때는 에러 이름을 섞지 말고, **한 줄씩 시간축에 다시 놓는다**.

```text
10:00:00.000 INFO  tx-17  UPDATE seats ...
10:00:02.000 WARN  tx-17  SQLSTATE 55P03 lock not available
10:00:05.000 ERROR tx-17  SQLSTATE 57014 canceling statement due to statement timeout
```

| 시각 | 초보자 해석 | 분리해서 읽는 법 |
|---|---|---|
| `10:00:02` | 먼저 lock을 못 얻었다 | 이 시점의 지연 성격은 `lock timeout` 축이다 |
| `10:00:05` | 기다리거나 실행하던 statement 전체 예산도 넘겼다 | 나중에 `statement timeout`이 덮여 보여도 첫 막힘은 lock 쪽일 수 있다 |

타임라인으로 풀면 보통 두 경우다.

- `55P03 -> 57014`: 처음엔 락 줄에서 막혔고, 기다리다 statement 전체 예산까지 소진했다.
- `57014`만 단독: 락보다 SQL 실행 자체가 느린 경우가 많다.

즉 `57014`가 마지막에 보였다고 바로 "느린 쿼리만의 문제"로 닫으면 안 된다.
같은 요청에 `55P03`가 앞에 있으면, 초보자 첫 질문은 "`EXPLAIN`부터 볼까?"가 아니라 "**먼저 누가 lock을 쥐고 있었나?**"가 더 맞다.

## 자주 헷갈리는 포인트

- "`statement timeout`이면 무조건 락 문제다" -> 아니다. 락이 없어도 느린 SQL이면 난다.
- "`lock timeout`이면 SQL이 원래 느리다는 뜻이다" -> 아니다. 원래 빠른 SQL도 blocker 때문에 오래 기다릴 수 있다.
- "마지막에 `57014`가 찍혔으니 원인은 항상 느린 SQL이다" -> 아니다. 앞줄에 `55P03`가 먼저 있으면 락 대기가 시작점일 수 있다.
- "둘 다 결국 오래 걸린 거니까 같은 튜닝이다" -> 아니다. 하나는 실행 계획/범위 문제, 다른 하나는 동시성/경합 문제다.
- "`statement timeout`이 나면 일단 retry하면 된다" -> 보통 아니다. 느린 SQL을 그대로 다시 보내면 또 느릴 가능성이 높다.
- "`lock timeout`이 나면 인덱스만 보면 된다" -> 보통 아니다. 같은 key 경합이나 긴 트랜잭션을 먼저 봐야 한다.
- "`lock timeout`이면 이미 다른 요청이 성공한 것이다" -> 아니다. 누가 막고 있는지는 맞지만, 그 작업이 최종 성공했는지는 별도 확인이 필요하다.

## 30초 분류 질문

1. 이 SQL이 혼자 실행돼도 원래 오래 걸릴 것 같은가?
2. 아니면 특정 row/key를 잡은 선행 트랜잭션 때문에 여기서만 기다리는가?
3. `statement timeout` 직전 로그에 `55P03`/`lock wait timeout` 같은 lock 신호가 있었는가?

빠른 기준:

- 혼자 돌려도 오래 걸릴 것 같으면 `statement timeout` 쪽
- 특정 key 경쟁 때만 오래 걸리면 `lock timeout` 쪽
- `statement timeout`만 봤더라도 앞줄 lock 신호가 있으면 먼저 `lock wait` 축을 의심

## 초보자 대응 시작점

| 지금 먼저 보인 것 | 첫 대응 |
|---|---|
| `statement timeout` + 앞줄 lock 신호 없음 | SQL 범위, 인덱스, 정렬, `EXPLAIN`부터 본다 |
| `statement timeout` + 앞줄 lock 신호 있음 | blocker 트랜잭션과 같은 key 경합부터 본다 |
| `lock timeout` | blocker 트랜잭션, hot row, 트랜잭션 길이부터 본다 |

필요하면 다음 문서로 이어 본다.

- `statement timeout` 쪽이면 [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- `lock timeout` 쪽이면 [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md), [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md), [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)

## 한 줄 정리

`statement timeout`은 **SQL 실행이 너무 오래 걸린 신호**, `lock timeout`은 **락 줄에서 너무 오래 기다린 신호**다. 둘 다 "느리다"로 묶지 말고, **실행 지연인지 락 대기 지연인지** 먼저 분리해서 읽자.
