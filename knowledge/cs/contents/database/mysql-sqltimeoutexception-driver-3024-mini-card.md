---
schema_version: 3
title: MySQL SQLTimeoutException vs Driver Timeout vs 3024 Mini Card
concept_id: database/mysql-sqltimeoutexception-driver-3024-mini-card
canonical: true
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- timeout
- jdbc
- mysql-3024
- exception-mapping
aliases:
- mysql sqltimeoutexception 3024
- driver timeout vs mysql timeout
- mysql query execution interrupted 3024
- sqltimeoutexception what is
- jdbc query timeout vs socket timeout
- mysql max execution time exceeded
- timeout surface signal primer
- MySQL timeout 뭐예요
- SQLTimeoutException은 3024인가요
- driver socketTimeout mysql
symptoms:
- java.sql.SQLTimeoutException 표면 예외만 보고 MySQL 서버 timeout인지 driver socket timeout인지 단정하고 있어
- MySQL errno 3024와 JDBC query timeout, network socket timeout의 ownership을 구분해야 해
- timeout을 retry 문제로 볼지 slow query plan 문제로 볼지 root cause vendor code와 메시지로 내려가야 해
intents:
- troubleshooting
- definition
prerequisites:
- database/timeout-errorcode-mapping-mini-card
- database/statement-timeout-vs-lock-timeout-card
next_docs:
- database/query-tuning-checklist
- database/hikari-connection-pool-tuning
- database/transaction-timeout-vs-lock-timeout
linked_paths:
- contents/database/timeout-errorcode-mapping-mini-card.md
- contents/database/statement-timeout-vs-lock-timeout-card.md
- contents/database/hikari-connection-pool-tuning.md
- contents/language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md
- contents/database/query-tuning-checklist.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/transaction-timeout-vs-lock-timeout.md
confusable_with:
- database/statement-timeout-vs-lock-timeout-card
- database/timeout-errorcode-mapping-mini-card
- database/hikari-connection-pool-tuning
forbidden_neighbors: []
expected_queries:
- SQLTimeoutException이 보이면 항상 MySQL 3024 서버 timeout으로 봐도 돼?
- driver socketTimeout과 MySQL errno 3024를 로그에서 어떻게 구분해?
- JDBC query timeout, network timeout, server max execution time을 ownership 기준으로 설명해줘
- MySQL 3024가 lock timeout이 아니라 slow query signal에 가까운 이유가 뭐야?
- timeout 예외를 보면 root cause, vendor code, query plan 중 무엇부터 확인해야 해?
contextual_chunk_prefix: |
  이 문서는 java.sql.SQLTimeoutException, JDBC driver socket timeout, MySQL errno 3024 query execution timeout을 ownership 기준으로 분리하는 beginner symptom router다.
  SQLTimeoutException은 3024인가요, driver timeout vs mysql timeout, MySQL timeout 뭐예요 질문이 본 문서에 매핑된다.
---
# MySQL `SQLTimeoutException` vs Driver Timeout vs `3024` 미니카드

> 한 줄 요약: `SQLTimeoutException`은 자바 표면 이름이고, driver timeout은 클라이언트 쪽 끊김이며, MySQL `3024`는 서버가 실행 시간을 넘겨 직접 끊은 신호다.

**난이도: 🟢 Beginner**

관련 문서:

- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- [HikariCP 튜닝](./hikari-connection-pool-tuning.md)
- [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](../language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: mysql sqltimeoutexception 3024, driver timeout vs mysql timeout, mysql query execution interrupted 3024, sqltimeoutexception what is, mysql statement timeout beginner, jdbc query timeout vs socket timeout, driver socket timeout mysql, mysql max execution time exceeded, timeout surface signal primer, mysql timeout 뭐예요, mysql sqltimeoutexception driver 3024 mini card basics, mysql sqltimeoutexception driver 3024 mini card beginner, mysql sqltimeoutexception driver 3024 mini card intro, database basics, beginner database

## 먼저 멘탈모델

초보자는 timeout 이름이 아니라 "누가 끊었는가"부터 보면 덜 헷갈린다.

- `SQLTimeoutException`: 자바/JDBC가 바깥으로 보여 준 표면 이름
- driver timeout: JDBC 드라이버나 소켓이 클라이언트 쪽에서 먼저 끊음
- MySQL `3024`: MySQL 서버가 "이 쿼리 너무 오래 걸렸다"며 직접 끊음

짧게 외우면:

- 자바 이름 -> `SQLTimeoutException`
- 클라이언트가 끊음 -> driver timeout
- 서버가 끊음 -> MySQL `3024`

## 30초 비교표

| 먼저 보이는 것 | 어디서 끊겼나 | 초보자 해석 | 첫 확인 포인트 |
|---|---|---|---|
| `java.sql.SQLTimeoutException` | 자바 표면 예외 | 아직 원인 확정 전 | root cause 메시지와 vendor code 확인 |
| driver `socketTimeout` / network timeout | JDBC 드라이버/소켓 | 서버 결과를 받기 전에 클라이언트가 포기 | 드라이버 설정, 네트워크, 서버 쿼리 지속 여부 |
| MySQL errno `3024` | MySQL 서버 | 서버가 실행 시간 예산 초과로 중단 | max execution time, 느린 SQL, 넓은 scan |

핵심은 `SQLTimeoutException` 하나만 보고 바로 "MySQL이 3024를 냈다"라고 단정하지 않는 것이다.

## 세 신호를 이렇게 분리한다

### `SQLTimeoutException`

이건 **원인 이름이 아니라 포장지**에 가깝다. 아래 둘이 모두 이 이름으로 보일 수 있다.

- 서버가 query timeout을 걸어 끊은 경우
- 드라이버가 응답 대기 중 먼저 포기한 경우

그래서 초보자는 예외 클래스만 보지 말고 `SQLException#getErrorCode()`, 메시지, root cause를 같이 봐야 한다.

### driver timeout

이건 **클라이언트 쪽 시계**가 먼저 끝난 경우다.

- `socketTimeout`
- network timeout
- driver read timeout

이 경우 MySQL 서버는 아직 실행 중이었을 수도 있다. 즉 "느린 SQL"일 수는 있어도, **서버가 timeout을 선언한 것과는 다르다**.

### MySQL `3024`

이건 보통 **서버 쪽 statement execution time limit 초과**로 읽으면 된다.

- MySQL이 직접 실행을 중단했다
- 초급자 3버킷으로는 `query-too-slow`에 둔다
- 첫 대응은 retry보다 쿼리 범위와 실행 계획 확인이다

## 작은 예시

| 로그 조각 | 먼저 읽는 법 | 왜 이렇게 보나 |
|---|---|---|
| `SQLTimeoutException` + errno 없음 + `socketTimeout` 언급 | driver timeout 쪽 의심 | 서버 코드보다 드라이버 설정이 먼저 보인다 |
| `SQLTimeoutException` + MySQL errno `3024` | 서버 query timeout | 자바 예외 아래에 MySQL vendor code가 드러난다 |
| Spring `QueryTimeoutException` + root cause `3024` | `query-too-slow` | Spring 이름보다 root MySQL code가 더 직접적이다 |

실무에서는 "표면 예외 이름 -> root cause -> DB code" 순서로 내려가면 된다.

## 자주 헷갈리는 포인트

- `SQLTimeoutException` = 항상 MySQL `3024` -> 아니다. driver timeout도 같은 표면 이름으로 보일 수 있다.
- driver timeout = 무조건 네트워크 장애 -> 아니다. 느린 쿼리 때문에 응답을 오래 못 받아도 난다.
- MySQL `3024` = lock timeout -> 아니다. 보통 lock 경합보다 `query-too-slow` 쪽 신호다.
- `3024`가 보이면 일단 timeout만 늘리면 된다 -> 아니다. 먼저 scan 범위, 인덱스, 정렬, 실행 계획을 본다.

## 다음에 어디로 이어 볼까

- 예외 이름을 `busy` / `retryable` / `query-too-slow`로 먼저 고정하려면 [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- 느린 SQL과 lock wait를 먼저 떼어내려면 [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- JDBC/driver/network timeout ownership을 더 자세히 보려면 [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](../language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)

## 한 줄 정리

`SQLTimeoutException`은 표면 이름, driver timeout은 클라이언트 쪽 포기, MySQL `3024`는 서버가 느린 쿼리를 직접 끊은 신호로 분리해서 읽자.
