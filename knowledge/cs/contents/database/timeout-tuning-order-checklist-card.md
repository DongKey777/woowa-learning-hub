# 타임아웃 튜닝 순서 체크리스트 카드

> 한 줄 요약: timeout 값을 올리기 전에, 먼저 **왜 기다리는 시간이 길어졌는지**를 5단계로 분리해서 본다.

**난이도: 🟢 Beginner**

관련 문서:

- [EXPLAIN 첫 판독 미니카드](./explain-first-read-timeout-mini-card.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md)
- [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
- [HikariCP 튜닝](./hikari-connection-pool-tuning.md)
- [Spring 트랜잭션 기본](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: timeout tuning order checklist, before increasing timeout checklist, connection timeout tuning order, lock timeout tuning order, timeout value increase before checklist, long transaction external io hot key explain plan pool size, timeout tuning beginner card, timeout basics, timeout 뭐예요, 처음 배우는데 timeout, 타임아웃 튜닝 순서 체크리스트, 타임아웃 값 올리기 전에, connection timeout 먼저 볼 것, 트랜잭션 길이 외부 io 핫키 실행계획 풀 크기, timeout 값 늘리기 전 5단계

## 먼저 멘탈모델

초보자는 timeout을 "더 기다릴 시간"으로만 보기 쉽다.
하지만 대부분의 timeout은 "원인이 해결되지 않은 채 대기만 길어졌다"는 신호다.

그래서 첫 질문은 이것이다.

> "값을 올리면 문제가 사라지나, 아니면 같은 막힘을 더 오래 숨기기만 하나?"

이 카드의 목적은 그 질문을 5단계로 빠르게 확인하는 것이다.

## 5단계 한 장 체크리스트

| 단계 | 먼저 볼 것 | 왜 이 순서인가 | `예`면 먼저 할 일 |
|---|---|---|---|
| 1 | 트랜잭션이 너무 길지 않나 | timeout은 길어진 점유 시간의 결과로 자주 보인다 | commit 단위를 짧게 자를 수 있는지 본다 |
| 2 | 트랜잭션 안에 외부 I/O가 있나 | 네트워크 대기가 커넥션/락 점유 시간으로 번질 수 있다 | HTTP/gRPC/파일 업로드/브로커 발행을 경계 밖으로 뺄 수 있는지 본다 |
| 3 | 같은 row/key에 요청이 몰리나 | hot key면 timeout을 늘려도 줄만 더 길어진다 | 어떤 key가 막히는지 로그와 SQL에서 확인한다 |
| 4 | 실행계획이 비효율적인가 | 느린 scan/sort가 lock 보유 시간과 전체 latency를 늘린다 | `EXPLAIN`과 인덱스 경로를 먼저 점검한다 |
| 5 | 그래도 풀 크기나 timeout 값이 너무 작나 | 앞 4개를 본 뒤에야 설정값 부족인지 판단이 선다 | 실제 동시성, DB max connection, 대기열 수치를 기준으로 조정한다 |

## 체크 순서를 짧게 기억하는 법

`길이 -> 외부 대기 -> 핫키 -> 계획 -> 설정값`

- 길이: 트랜잭션이 오래 열려 있나
- 외부 대기: DB 밖의 느린 호출이 안에 섞였나
- 핫키: 같은 row/key 경합이 반복되나
- 계획: 쿼리가 불필요하게 많은 row를 읽나
- 설정값: 마지막에 timeout/pool 크기를 본다

## 작은 비교표

| 지금 하려는 행동 | 초보자에게 흔한 기대 | 실제로 자주 일어나는 일 |
|---|---|---|
| `connectionTimeout`만 올린다 | 에러가 사라진다 | 커넥션 반환 지연이 그대로면 실패 시점만 늦어진다 |
| `lock timeout`만 올린다 | 결국 선행 작업이 끝나서 해결된다 | hot key나 긴 트랜잭션이면 대기열만 더 길어진다 |
| 실행계획/경계 확인 후 일부만 조정한다 | 번거롭다 | 근본 대기 시간을 줄여 timeout 자체를 덜 보게 된다 |

## 5단계 질문 카드

### 1. 트랜잭션 길이

- 한 트랜잭션 안에서 여러 조회/갱신/후처리가 한 번에 묶여 있지 않나?
- commit 전까지 꼭 필요하지 않은 작업이 같이 들어 있지 않나?

보이는 신호:

- `active`가 오래 높게 유지된다
- 같은 API에서 p95/p99가 트랜잭션 시간과 함께 늘어난다

### 2. 외부 I/O

- `@Transactional` 안에서 HTTP, gRPC, Redis, 파일 업로드, 메시지 발행을 기다리나?
- 외부 시스템 지연이 DB 커넥션 점유 시간으로 번질 구조인가?

보이는 신호:

- 외부 API 지연 시점과 pool 대기 증가 시점이 같이 움직인다
- DB CPU는 높지 않은데 `threads awaiting connection`이 늘어난다

### 3. 핫키

- 같은 `user_id`, `sku_id`, `coupon_id`, `room_id` 같은 key에 경쟁이 몰리나?
- timeout 로그의 SQL이 반복해서 같은 조건으로 보이나?

보이는 신호:

- `lock wait timeout` 또는 deadlock이 특정 key 주변에서 반복된다
- 인스턴스를 늘려도 처리량은 안 늘고 대기만 길어진다

### 4. 실행계획

- 원래 좁게 읽어야 할 쿼리가 넓은 scan이나 filesort를 타고 있나?
- 인덱스 순서가 predicate와 맞지 않아 오래 붙잡히나?

보이는 신호:

- 특정 SQL만 유독 느리다
- `EXPLAIN`에서 rows가 크게 잡히거나 불필요한 정렬/임시 테이블이 보인다

### 5. 풀 크기와 timeout 값

앞의 1~4단계에서 큰 원인이 안 보일 때 마지막으로 본다.

- 현재 `maximumPoolSize`가 실제 동시성보다 너무 작은가?
- DB `max_connections`와 애플리케이션 인스턴스 수를 합치면 안전한 범위인가?
- timeout이 서비스 SLO보다 비정상적으로 짧게 잡혀 있나?

핵심:

- 설정값 조정은 필요할 수 있다
- 하지만 앞단 원인을 안 줄인 채 숫자만 올리면 "조용히 더 오래 기다리는 시스템"이 되기 쉽다

## 작은 예시

상황:

- 주문 API에서 `Connection is not available` 증가
- 운영자는 `connectionTimeout`을 `3s -> 10s`로 올리려 한다

5단계로 읽기:

1. 주문 트랜잭션이 평균 150ms에서 피크 2.8s로 늘었다.
2. 같은 구간에 `paymentClient.authorize()`가 트랜잭션 안에서 2초 넘게 대기한다.
3. 게다가 일부 SKU는 같은 `sku_id` 업데이트가 몰린다.
4. 재고 확인 쿼리 `EXPLAIN`을 보니 넓은 범위를 읽는다.
5. 이 상태에서 timeout만 올리면 입구 대기만 더 길어진다.

초보자용 결론:

- 먼저 경계와 쿼리/경합을 줄인다
- 그래도 짧게 잡힌 값이면 그때 pool/timeout을 조정한다

## 자주 헷갈리는 포인트

- "timeout이 났으니 값이 너무 작은 것" -> 아닐 수 있다. 원인 있는 대기를 드러낸 것일 수 있다.
- "DB CPU가 낮으니 풀만 키우면 된다" -> 외부 I/O나 락 대기로도 풀 고갈은 난다.
- "deadlock/lock timeout이 있으니 무조건 재시도" -> 같은 hot key 혼잡이면 retry가 더 악화시킬 수 있다.
- "`EXPLAIN`은 DBA만 본다" -> 초보자도 rows, index 사용 여부, filesort 정도는 먼저 확인할 수 있다.

## 한 줄 정리

timeout 튜닝의 기본 순서는 **트랜잭션 길이 -> 외부 I/O -> 핫키 -> 실행계획 -> 풀 크기/설정값**이다. 숫자를 키우는 일은 마지막 단계로 남겨 두자.
