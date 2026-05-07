---
schema_version: 3
title: JDBC Observability Under Virtual Threads
concept_id: language/jdbc-observability-under-virtual-threads
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 92
mission_ids:
- missions/payment
- missions/racingcar
review_feedback_tags:
- jdbc-observability
- virtual-thread
- connection-pool
aliases:
- JDBC Observability Under Virtual Threads
- virtual thread JDBC diagnostics
- Hikari pending acquire virtual thread
- connection hold time long transaction
- DB lock wait after Loom
- virtual thread 데이터베이스 병목 관측
symptoms:
- virtual thread가 많이 보인다는 사실만 보고 pinning 문제로 결론 내려 datasource acquire wait, connection hold time, DB lock wait를 분리하지 못해
- Hikari pending acquire 증가를 pool size 부족으로만 보고 long transaction이나 transaction 안 외부 HTTP wait를 놓쳐
- JDBC execute/commit socket wait를 네트워크 문제로만 해석해 DB lock contention과 blocker chain을 붙여 보지 못해
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/virtual-threads-project-loom
- language/connection-budget-alignment-after-loom
- database/hikari-connection-pool-tuning
next_docs:
- language/jfr-loom-incident-signal-map
- language/jdbc-db-side-cancel-confirmation-playbook
- database/lock-wait-deadlock-latch-triage-playbook
linked_paths:
- contents/language/java/virtual-threads-project-loom.md
- contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/language/java/connection-budget-alignment-after-loom.md
- contents/language/java/virtual-thread-vs-reactive-db-observability.md
- contents/language/java/virtual-thread-jdbc-cancel-semantics.md
- contents/language/java/jdbc-db-side-cancel-confirmation-playbook.md
- contents/language/java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/language/java/jfr-event-interpretation.md
- contents/language/java/jfr-loom-incident-signal-map.md
- contents/language/java/thread-dump-state-interpretation.md
- contents/language/java/jcmd-diagnostic-command-cheatsheet.md
- contents/database/hikari-connection-pool-tuning.md
- contents/database/transaction-boundary-isolation-locking-decision-framework.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
- contents/spring/spring-transaction-debugging-playbook.md
confusable_with:
- language/connection-budget-alignment-after-loom
- language/jfr-loom-incident-signal-map
- database/lock-wait-deadlock-latch-triage-playbook
forbidden_neighbors: []
expected_queries:
- virtual thread 도입 후 JDBC 장애를 datasource acquire wait connection hold time DB lock wait로 어떻게 나눠 봐?
- Hikari pending acquire가 늘 때 pool size부터 키우면 왜 위험할 수 있어?
- transaction duration과 SQL duration 합을 비교해 long transaction을 찾는 방법을 알려줘
- JDBC execute나 commit에서 오래 멈출 때 DB lock wait와 Java monitor contention을 어떻게 구분해?
- Loom 환경에서 connection pool wait와 VirtualThreadPinned 이벤트를 같은 시간창에서 해석하는 순서를 알려줘
contextual_chunk_prefix: |
  이 문서는 virtual thread 환경의 JDBC 관측을 datasource acquire wait, connection hold time, long transaction, DB lock wait, JFR/thread dump 신호로 분해하는 advanced playbook이다.
  virtual thread JDBC diagnostics, Hikari pending, connection hold time, DB lock wait, long transaction 질문이 본 문서에 매핑된다.
---
# JDBC Observability Under Virtual Threads

> 한 줄 요약: virtual thread 도입 뒤 JDBC 장애 해석의 핵심은 "스레드가 많이 보인다"가 아니라 datasource acquire wait, connection hold time, DB lock wait를 분리해서 보는 것이다. virtual thread는 blocking JDBC를 감당하기 쉽게 만들지만, pool wait와 long transaction, lock contention을 숨겨 주지는 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [Connection Budget Alignment After Loom](./connection-budget-alignment-after-loom.md)
> - [Virtual Thread vs Reactive DB Observability](./virtual-thread-vs-reactive-db-observability.md)
> - [Virtual-Thread JDBC Cancel Semantics](./virtual-thread-jdbc-cancel-semantics.md)
> - [DB-Side Cancel Confirmation Playbook](./jdbc-db-side-cancel-confirmation-playbook.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [JFR Event Interpretation](./jfr-event-interpretation.md)
> - [JFR Loom Incident Signal Map](./jfr-loom-incident-signal-map.md)
> - [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)
> - [`jcmd` Diagnostic Command Cheat Sheet](./jcmd-diagnostic-command-cheatsheet.md)
> - [HikariCP 튜닝](../../database/hikari-connection-pool-tuning.md)
> - [Transaction Boundary, Isolation, and Locking Decision Framework](../../database/transaction-boundary-isolation-locking-decision-framework.md)
> - [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../../database/lock-wait-deadlock-latch-triage-playbook.md)
> - [Spring Transaction Debugging Playbook](../../spring/spring-transaction-debugging-playbook.md)

> retrieval-anchor-keywords: JDBC observability under virtual threads, virtual thread JDBC diagnostics, connection pool wait, datasource acquire wait, Hikari pending threads, HikariCP wait, long transaction diagnosis, transaction hold time, connection hold time, JDBC cancel observability, statement timeout, SQLTimeoutException, Statement.cancel, DB lock wait, lock contention after loom, virtual thread database bottleneck, getConnection latency, commit latency, pending acquire threads, pool saturation, row lock wait, monitor contention vs DB lock, JFR Thread Park, VirtualThreadPinned, thread dump parked virtual thread, JDBC execute wait, remote call inside transaction, transaction open too long, virtual thread vs reactive DB observability, JDBC vs R2DBC diagnostics, JFR Loom incident signal map, connection budget alignment after loom, DB concurrency budget, HTTP bulkhead vs pool size

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [관측 지도](#관측-지도)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

virtual thread를 도입하면 request thread scarcity는 줄어들 수 있다.  
하지만 JDBC 경로에서 먼저 드러나는 것은 대개 다음 셋이다.

- connection pool에서 기다리는 시간
- connection을 잡은 뒤 transaction을 오래 여는 시간
- DB 안에서 lock 때문에 막히는 시간

이 셋은 겉으로 보면 모두 "요청이 느리다"는 같은 증상으로 보인다.  
그래서 관측은 thread count가 아니라 **request 시작 -> connection acquire -> SQL 실행 -> commit/release** 타임라인을 기준으로 짜야 한다.

핵심 질문도 세 가지로 줄어든다.

1. 아직 connection을 못 얻어서 기다리는가
2. connection은 얻었는데 application이 너무 오래 쥐고 있는가
3. DB 안에서 lock wait가 생겨 execute/commit이 막히는가

virtual thread 환경에서 이 구분이 더 중요해지는 이유는, 스레드가 싸져서 대기가 "조용히" 늘어나기 쉽기 때문이다.  
예전에는 platform thread 부족이 먼저 터졌다면, 이제는 datasource pending, long transaction, hot row contention이 먼저 전면에 나온다.

## 깊이 들어가기

### 1. virtual thread 이후 첫 병목은 thread가 아니라 downstream일 수 있다

virtual thread는 waiting 동안 carrier를 덜 점유하게 해 준다.  
하지만 다음 자원은 자동으로 늘어나지 않는다.

- datasource max pool size
- DB가 실제로 처리할 수 있는 동시 transaction 수
- hot row/table/index에 대한 lock 경쟁
- transaction 안에 섞여 들어간 외부 HTTP, retry, sleep, batch flush

즉 "virtual thread로 바꿨더니 요청을 더 많이 받는다"와 "JDBC 경로가 그 병렬도를 감당한다"는 별개다.

### 2. connection-pool wait는 acquire 대기와 active saturation을 같이 본다

pool wait의 전형적인 신호는 다음 조합이다.

- datasource pending acquire가 오른다
- active connection 수가 pool 상한에 붙는다
- thread dump/JFR에서 많은 virtual thread가 `getConnection()` 또는 pool borrow 근처에서 park/wait 한다

이때 중요한 해석은 "virtual thread가 막혔다"가 아니라 **connection이 부족하거나 오래 반환되지 않는다**는 것이다.

특히 이렇게 나누면 좋다.

- pending acquire 증가 + active가 상한 근처 + DB CPU/active session은 낮다  
  보통 application이 transaction을 너무 오래 들고 있거나, SQL 사이에 외부 대기가 섞여 있다.
- pending acquire 증가 + active가 상한 근처 + DB도 이미 바쁘다  
  pool 설정보다 DB 처리량/쿼리/lock wait가 먼저 병목일 수 있다.
- pending acquire만 보고 pool size만 키운다  
  long transaction이나 lock wait를 더 넓게 퍼뜨릴 수 있다.

즉 pool wait는 원인이라기보다 "downstream scarcity가 눈에 보이기 시작한 첫 경보"에 가깝다.

### 3. long transaction은 SQL 시간보다 connection hold time으로 읽어야 한다

virtual thread 환경에서 흔한 착시는 "blocking JDBC가 잘 맞으니 transaction 안 대기도 괜찮다"는 생각이다.  
하지만 운영에서 중요한 것은 thread 점유가 아니라 connection hold time이다.

그래서 transaction 관측은 최소한 아래 네 구간으로 쪼개야 한다.

- acquire wait: `getConnection()`부터 connection 확보까지
- connection hold: acquire 후 release까지
- SQL execution: statement execute/query/update/commit에 실제로 쓴 시간
- non-SQL in transaction: HTTP 호출, retry sleep, JSON 직렬화, 대용량 매핑, lock 획득 전 애플리케이션 코드

특히 아래 냄새를 먼저 의심한다.

- transaction duration이 SQL duration 합보다 훨씬 길다
- 같은 trace 안에서 outbound HTTP나 message publish retry가 transaction 사이에 들어간다
- commit 직전까지 business logic/serialization이 길게 이어진다

long transaction은 pool wait의 상류 원인이 되기 쉽다.  
한 connection을 오래 잡으면 뒤 요청들이 virtual thread 위에서 조용히 대기하고, 그 결과 pending acquire가 연쇄적으로 오른다.

### 4. lock contention은 Java monitor와 DB lock을 분리해서 본다

"락 경쟁"이라는 표현은 두 층위를 섞기 쉽다.

- JVM/application 락 경쟁: `synchronized`, `ReentrantLock`, monitor contention
- DB 락 경쟁: row lock, gap lock, metadata lock, commit wait

virtual thread 전환 뒤 pool wait가 늘었다고 해서 모두 pinning이나 Java monitor 문제는 아니다.  
오히려 흔한 패턴은 이쪽이다.

1. 요청이 더 많이 동시에 DB로 들어간다
2. hot row/update path에서 DB lock wait가 생긴다
3. connection이 release되지 못해 active가 오래 찬다
4. 뒤 요청은 pool acquire에서 기다린다

즉 lock contention은 종종 **pool wait의 하류 원인**이다.

관측 힌트는 다음처럼 나뉜다.

- `BLOCKED`/`Java Monitor Blocked`가 많고 JDBC 바깥 임계영역이 길다  
  application lock 문제일 가능성이 크다.
- JDBC execute/commit 호출에서 오래 멈추고 DB 쪽 blocker/waiter가 잡힌다  
  DB lock wait일 가능성이 크다.
- `Thread Park`만 많고 pinning/monitor blocked는 적다  
  pool acquire wait일 가능성이 크다.

### 5. 타임라인 하나로 네 레이어를 묶어야 한다

증상 해석이 흔들리는 이유는 pool, application, JVM, DB를 따로 보기 때문이다.  
실전에서는 같은 60~120초 창에서 네 레이어를 함께 잡는 편이 빠르다.

- pool: active, idle, pending acquire, acquire timeout
- application: request latency, transaction duration, outbound HTTP duration, retry count
- JVM: thread dump, JFR `Thread Park`, `Socket Read`, `Java Monitor Blocked`, `VirtualThreadPinned`
- DB: active transaction, lock wait, blocker/waiter, slow query

이 네 레이어를 같은 trace/request/transaction 기준으로 묶지 못하면 "pool이 작다", "DB가 느리다", "virtual thread가 문제다"가 번갈아가며 나와도 결론이 흐려진다.

## 관측 지도

| 증상 축 | 먼저 볼 수치/사실 | thread dump / JFR에서 보이는 것 | 1차 해석 | 다음 질문 |
|---|---|---|---|---|
| connection-pool wait | pending acquire 증가, active가 상한에 근접 | 많은 virtual thread가 `getConnection()`/pool borrow 근처에서 park | pool saturation 또는 upstream long transaction | 왜 connection이 늦게 돌아오는가 |
| long transaction | hold time 증가, transaction duration이 SQL 합보다 길다 | 같은 요청 흐름에서 JDBC 전후로 HTTP/socket wait나 큰 애플리케이션 처리 구간이 보인다 | transaction boundary가 넓거나 non-SQL work가 transaction 안에 있다 | transaction 안에 꼭 남겨야 할 코드가 무엇인가 |
| DB lock contention | active connection 유지, commit/execute latency 상승, DB lock wait 증가 | JDBC execute/commit stack에서 오래 머무르고 pool pending이 2차로 따라 오른다 | hot row/order/DDL/lock order 문제 | 누가 blocker이고 어떤 순서로 경합하는가 |
| pinning / app lock contention | pool보다 monitor blocked, pinned event가 먼저 튄다 | `Java Monitor Blocked`, `VirtualThreadPinned`, 임계영역 안 blocking I/O | JDBC보다 application lock 구조가 먼저 병목 | lock 안에서 I/O나 외부 호출을 하고 있지 않은가 |

표에서 중요한 점은 순서다.  
pool wait는 최종 증상일 때가 많고, long transaction이나 DB lock wait가 상류 원인인 경우가 흔하다.

## 실전 시나리오

### 시나리오 1: virtual thread 도입 직후 Hikari pending이 급증한다

thread dump에는 수많은 virtual thread가 기다리는 것으로 보이지만, 그것만으로 원인은 정해지지 않는다.  
먼저 active connection이 상한에 붙었는지, transaction hold time이 같이 늘었는지 본다.

- hold time도 같이 늘면 transaction boundary가 넓어진 것이다
- hold time은 비슷한데 DB lock wait가 늘면 hot row contention 쪽이 먼저다
- 둘 다 아니면 burst traffic 대비 pool/DB budget 불일치일 수 있다

### 시나리오 2: transaction 안에서 외부 HTTP retry가 돈다

virtual thread에서는 이 코드가 "자연스럽게" 보일 수 있다.  
하지만 관측상으로는 connection hold time이 길어지고, 그 뒤 pending acquire가 연쇄적으로 오른다.

핵심은 HTTP wait가 느린 것이 아니라 **connection을 쥔 채 느리다**는 점이다.

### 시나리오 3: fan-out이 쉬워지자 update hot row가 잠기기 시작한다

virtual thread로 fan-out이 쉬워지면 같은 aggregate/row에 대한 동시 update가 늘 수 있다.  
이 경우 application 쪽에서는 execute/commit latency와 pool pending만 보일 수 있지만, 실제 원인은 DB blocker chain이다.

즉 "thread가 많아서 느리다"가 아니라 "더 많은 동시성으로 같은 lock을 두드리고 있다"가 맞다.

## 코드로 보기

### 1. acquire wait와 hold time을 따로 기록한다

```java
long acquireStartedAt = System.nanoTime();

try (Connection connection = dataSource.getConnection()) {
    long acquiredAt = System.nanoTime();
    log.info("jdbc acquireMs={} traceId={}",
            millis(acquiredAt - acquireStartedAt),
            traceId());

    connection.setAutoCommit(false);
    try {
        doBusinessSql(connection);
        connection.commit();
    } finally {
        long releasedAt = System.nanoTime();
        log.info("jdbc holdMs={} traceId={}",
                millis(releasedAt - acquiredAt),
                traceId());
    }
}
```

프레임워크를 쓴다면 직접 `Connection`을 감싸기보다 datasource proxy, Micrometer, transaction observation으로 같은 구간을 캡처하는 편이 낫다.  
핵심은 metric 이름이 아니라 `acquire`와 `hold`를 분리하는 것이다.

### 2. 운영 캡처는 thread dump와 JFR을 같은 시간 창에 묶는다

```bash
jcmd <pid> Thread.print
jcmd <pid> JFR.start name=vt-jdbc settings=profile duration=120s filename=/tmp/vt-jdbc.jfr
jcmd <pid> JFR.check
```

같은 시간 창에 pool metric과 DB lock wait 스냅샷을 같이 남겨야 `park`가 pool wait인지, execute/commit wait가 DB lock인지 구분이 빨라진다.

### 3. 해석 메모는 세 줄이면 충분하다

```text
pending acquire 상승 + active=max + DB lock wait 없음 => pool/transaction hold 문제 우선
hold time 상승 + SQL 합은 짧음 => transaction 안 non-SQL work 의심
execute/commit 정체 + DB blocker 확인됨 => lock contention 우선
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| thread 수만 본다 | 빠르게 대시보드 한 장을 읽을 수 있다 | pool wait와 DB lock wait를 쉽게 혼동한다 |
| acquire/hold/SQL 시간을 분리한다 | 병목 위치가 선명해진다 | 계측 포인트와 trace 정합성을 신경 써야 한다 |
| pool size부터 키운다 | 즉시 완화처럼 보일 수 있다 | long transaction과 lock wait를 더 넓게 퍼뜨릴 수 있다 |
| transaction boundary를 줄인다 | connection hold time을 직접 줄일 수 있다 | service 흐름, outbox, retry ownership 재설계가 필요할 수 있다 |

핵심은 virtual thread 시대의 JDBC 관측을 "많이 기다리는 thread"가 아니라 "늦게 돌아오는 connection" 중심으로 다시 읽는 것이다.

## 꼬리질문

> Q: virtual thread가 많이 WAITING이면 pinning 문제인가요?
> 핵심: 아니다. 먼저 pool acquire wait, DB lock wait, app monitor contention 중 무엇인지 분리해야 한다.

> Q: pending acquire가 보이면 pool size만 키우면 되나요?
> 핵심: 보통 아니다. long transaction이나 DB lock wait가 상류 원인인지 먼저 확인해야 한다.

> Q: DB lock wait도 thread dump에서 `BLOCKED`로 보이나요?
> 핵심: 꼭 그렇지 않다. Java monitor 경쟁이 아니라 JDBC execute/commit 호출 정체와 DB blocker chain으로 드러나는 경우가 많다.

> Q: 왜 virtual thread 도입 뒤 이런 증상이 더 잘 보이나요?
> 핵심: thread scarcity가 줄어 숨겨져 있던 datasource와 DB concurrency 한계가 더 빨리 드러나기 때문이다.

## 한 줄 정리

virtual thread 이후 JDBC 장애를 보려면 thread 개수가 아니라 `acquire wait -> connection hold -> execute/commit lock wait` 타임라인으로 읽어야 하고, pool wait와 long transaction, lock contention을 같은 관측 창에서 분리해야 한다.
