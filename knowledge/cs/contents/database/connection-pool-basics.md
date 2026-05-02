---
schema_version: 3
title: "커넥션 풀 기초 (Connection Pool Basics)"
concept_id: "database/connection-pool"
canonical: true
category: "database"
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 92
aliases:
  - connection pool
  - 커넥션 풀
  - 커넥션 풀이란
  - DB 커넥션 재사용
  - hikari cp
  - hikaricp
  - HikariCP
  - hikaricp가 뭐야
  - jdbc connection pool
  - 스프링 커넥션 풀
  - pool size
  - maxpoolsize
  - 커넥션 고갈
  - connection close returns pool
intents:
  - definition
  - design
prerequisites: []
next_docs:
  - database/connection-pool-transaction-propagation
  - database/connection-timeout-vs-lock-timeout
linked_paths:
  - contents/database/connection-pool-transaction-propagation-bulk-write.md
  - contents/database/connection-timeout-vs-lock-timeout-card.md
  - contents/database/transaction-locking-connection-pool-primer.md
  - contents/database/jdbc-jpa-mybatis.md
  - contents/spring/spring-transactional-basics.md
confusable_with:
  - operating-system/thread-pool
forbidden_neighbors:
  - contents/database/hikari-connection-pool-tuning.md
  - contents/database/connection-pool-transaction-propagation-bulk-write.md
expected_queries:
  - Connection pool이 뭐야?
  - DB 연결을 미리 만들어두고 빌려쓴다는 게 무슨 의미야?
  - HikariCP가 뭐야?
  - 커넥션 풀이 너무 작으면 어떻게 돼?
  - 처음 배우는데 커넥션 풀
contextual_chunk_prefix: |
  이 문서는 Spring 또는 JDBC를 처음 배우는 학습자가 "DB 연결을 매 요청마다 새로
  만드는 게 왜 비효율인가"라는 감각을 잡을 때 참고하는 primer다. 본 문서의 chunk는
  연결 비용 / 풀 크기 결정 / 풀 고갈 / 반환 흐름 중 일부를 설명한다. tuning 심화는
  hikari-connection-pool-tuning에서 다룬다 (본 primer는 큰 그림만).
---

# 커넥션 풀 기초 (Connection Pool Basics)

> 한 줄 요약: 커넥션 풀은 DB 연결을 미리 만들어 재사용하는 캐시이고, 풀 크기가 너무 작으면 대기가, 너무 크면 DB 과부하가 생긴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [트랜잭션·락·커넥션 풀 첫 그림](./transaction-locking-connection-pool-primer.md)
- [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)
- [database 카테고리 인덱스](./README.md)
- [Spring @Transactional 기초](../spring/spring-transactional-basics.md)

## 핵심 개념

커넥션 풀(connection pool)은 **미리 여러 개의 DB 연결(connection)을 만들어두고, 요청이 올 때 빌려주었다가 반환받아 재사용하는 연결 캐시**다.

DB 연결은 TCP 핸드셰이크, 인증, 세션 초기화를 거쳐야 해서 매번 새로 만들면 수십~수백 ms가 소비된다. 트래픽이 높은 서비스에서 요청마다 새 연결을 만들면 응답 시간이 크게 늘어난다. 커넥션 풀은 이 연결 생성 비용을 요청 경로에서 제거한다.

## 30초 멘탈모델

커넥션 풀을 "좌석이 제한된 카페"로 보면 이해가 쉽다.

- 좌석 수 = `maximumPoolSize`
- 손님 = 요청 스레드
- 착석 시간 = 트랜잭션/쿼리 수행 시간

좌석이 모자라면 대기줄이 생기고(`threads awaiting connection`), 너무 많은 좌석을 억지로 늘리면 카페 주방(DB)가 버티지 못한다.

입문자가 자주 헷갈리는 지점:

- 커넥션 풀은 "더 많이 = 더 좋다"가 아니다. DB는 연결 하나마다 메모리·스레드 자원을 쓰므로 풀이 너무 크면 오히려 DB가 과부하된다.
- 커넥션을 빌리고 반환하지 않으면 **커넥션 고갈(pool exhaustion)**이 발생해 이후 요청이 모두 대기 상태에 빠진다.

## 한눈에 보기

- 스레드가 요청 -> 풀에서 유휴 커넥션 빌림 -> SQL 실행 -> 반환
- 풀에 여유 커넥션이 없으면 `connectionTimeout`까지 대기
- 타임아웃 초과 시 예외 발생

```text
Thread A -> borrow conn -> run SQL -> return conn
Thread B -> borrow conn -> run SQL -> return conn
Thread C -> wait (if pool exhausted)
```

## 작은 수치 예시

`maximumPoolSize=10`, 평균 쿼리 시간 100ms라고 가정하면 이론상 동시에 처리 가능한 DB 작업은 대략 10개다.

- 요청이 한순간에 30개 들어오면 10개는 실행, 20개는 대기
- 느린 쿼리로 평균 점유 시간이 500ms로 늘면 같은 풀 크기에서도 대기열이 급격히 늘어난다

즉 풀 고갈은 "트래픽이 많아서"만이 아니라 "커넥션 점유 시간이 길어서"도 발생한다.

## 상세 분해

**풀 크기 (pool size)**

- `maximumPoolSize`: 최대로 유지할 커넥션 수
- `minimumIdle`: 유휴 상태에서도 유지할 최소 커넥션 수

시작점은 작은 값에서 시작해 부하 테스트로 조정하는 것이다. 공식(예: 코어 수 기반)은 출발점일 뿐 정답이 아니다.

**대기 타임아웃 (connectionTimeout)**

- 풀에 여유 커넥션이 없을 때 스레드가 기다리는 최대 시간
- 초과하면 예외가 발생한다

기본값 30초를 그대로 두면 장애가 늦게 드러나서 상위 타임아웃을 같이 무너뜨릴 수 있다. 서비스 SLO에 맞춰 더 짧게 잡는 편이 보통 안전하다.

**반환 (close / return)**

- JDBC에서 `connection.close()`를 호출하면 풀에 반환된다(물리 연결 종료가 아니다)
- try-with-resources나 Spring 트랜잭션 관리가 자동 반환을 도와준다

**HikariCP**

- Spring Boot의 기본 커넥션 풀
- `spring.datasource.hikari.maximum-pool-size`, `spring.datasource.hikari.connection-timeout` 등으로 제어

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "풀 크기를 크게 잡으면 안전하다" | DB는 연결마다 자원을 소비하므로 과도한 풀은 DB 장애를 유발할 수 있다 | DB 스펙과 실제 부하를 측정해서 적정 크기를 결정한다 |
| "커넥션을 오래 잡고 있어도 괜찮다" | 트랜잭션 안에서 외부 API 호출이나 긴 작업을 하면 그 시간만큼 커넥션을 독점한다 | 트랜잭션 범위를 짧게 유지하고, 외부 I/O는 트랜잭션 밖으로 꺼낸다 |
| "`close()`를 호출하면 DB 연결이 끊긴다" | 풀 환경에서는 대부분 반환(return) 동작이다 | `close()` 의미를 "반환"으로 이해하고 누수 여부를 점검한다 |
| "스레드풀 200이면 DB 커넥션도 200이 맞다" | 스레드 동시성 수와 DB 적정 동시 실행 수는 다르다 | 스레드풀과 커넥션 풀을 분리해 튜닝한다 |

## 증상 -> 첫 조치

| 관찰된 증상 | 가장 먼저 볼 것 | 다음 확인 |
|---|---|---|
| `Connection is not available` timeout | `active >= maximumPoolSize`인지 | 느린 쿼리, 긴 트랜잭션 |
| p95/p99가 갑자기 상승 | connection wait time 증가 여부 | 최근 배포에서 트랜잭션 범위 증가 여부 |
| DB CPU는 낮은데 앱은 느림 | 커넥션 대기열 | 애플리케이션 스레드풀/리트라이 폭증 |

## `Connection is not available` 로그 읽기

같은 `Connection is not available`라도 바로 앞 로그가 다르면 해석이 달라진다.

```text
[12:00:01.120] HikariPool-1 - Connection is not available, request timed out after 3000ms.
```

| 바로 앞 타임라인 | 초보자용 해석 | 첫 확인 포인트 |
|---|---|---|
| 같은 시각대에 `lock wait timeout`, deadlock, blocker SQL 로그가 없다 | **pool exhaustion 단독**일 가능성이 크다. 보통 긴 트랜잭션, 외부 I/O, 누수 때문에 커넥션 반환이 늦다 | 요청 하나가 커넥션을 얼마나 오래 쥐는지, 외부 API 호출이 트랜잭션 안에 있는지 |
| 1~2초 전에 `Lock wait timeout exceeded`, `55P03`, blocker session 로그가 이미 있었다 | **lock 경합이 먼저**였고, 그 여파로 뒤 요청들이 커넥션을 못 받아 pool timeout까지 번진 것일 수 있다 | 어느 row/key에서 막혔는지, blocker 트랜잭션이 왜 오래 잡혔는지 |

핵심은 `Connection is not available`를 "무조건 풀 크기 문제"로 읽지 않는 것이다. 먼저 앞선 로그에 **DB lock 대기 신호가 있었는지**를 보고, 없으면 점유 시간 문제를, 있으면 lock 경합 전파를 의심하면 된다.

## 더 깊이 가려면

- 커넥션 풀과 트랜잭션 전파, 벌크 쓰기 패턴 -> [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- `connection timeout`과 `lock timeout`을 한 표로 다시 분리하기 -> [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- 트랜잭션 길이 증가가 왜 pool exhaustion으로 번지는지 보기 -> [트랜잭션·락·커넥션 풀 첫 그림](./transaction-locking-connection-pool-primer.md)
- JDBC·JPA·MyBatis에서 커넥션 풀이 어떻게 사용되는지 -> [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)
- `@Transactional` 경계에서 커넥션 점유 시간이 길어지는 이유 -> [Spring @Transactional 기초](../spring/spring-transactional-basics.md)

## 면접/시니어 질문 미리보기

> Q: 커넥션 풀이 없으면 어떤 문제가 생기나요?
> 의도: 연결 생성 비용과 재사용의 필요성을 이해하는지 확인
> 핵심: 요청마다 새 DB 연결을 만들면 TCP 핸드셰이크·인증 비용이 매번 발생해 응답 시간이 느려지고, 동시 요청이 많으면 DB가 과부하된다.

> Q: 커넥션 풀 크기를 어떻게 결정하나요?
> 의도: "크면 클수록 좋다"는 오해를 극복했는지 확인
> 핵심: DB가 연결마다 자원을 소비하므로 서버 코어 수·DB 스펙·실제 쿼리 지연을 측정해 결정하고, 부하 테스트로 검증한다.

## 한 줄 정리

커넥션 풀은 "요청 스레드가 제한된 DB 좌석을 빌려 쓰는 구조"다. 크기는 크게만 잡는 게 아니라 대기 시간과 DB 부담을 함께 보며 맞춰야 한다.
