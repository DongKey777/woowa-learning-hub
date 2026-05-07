---
schema_version: 3
title: JDBC Cursor Cleanup on Download Abort
concept_id: language/jdbc-cursor-cleanup-download-abort
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 91
mission_ids:
- missions/payment
- missions/racingcar
review_feedback_tags:
- jdbc-streaming
- download-abort
- cursor-cleanup
aliases:
- JDBC Cursor Cleanup on Download Abort
- servlet download abort JDBC cursor cleanup
- StreamingResponseBody JDBC fetchSize cancel
- large CSV export query cancel
- broken pipe Statement.cancel ResultSet close
- JDBC 다운로드 중단 cursor 정리
symptoms:
- fetchSize를 설정하면 client abort 때 ResultSet과 server-side cursor가 자동으로 안전하게 정리된다고 기대해
- StreamingResponseBody callback 밖에서 ResultSet을 열어 두어 try-with-resources 수명과 실제 writer lifetime이 어긋나
- broken pipe나 async timeout을 JDBC Statement.cancel, ResultSet.close, connection close로 번역하지 못해 orphan query나 connection hold를 만든다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- language/streaming-response-abort-surfaces-servlet-virtual-threads
- language/virtual-thread-jdbc-cancel-semantics
- language/spring-jdbc-timeout-propagation-boundaries
next_docs:
- language/jdbc-db-side-cancel-confirmation-playbook
- language/jdbc-network-timeout-driver-socket-timeout-pool-eviction
- language/jdbc-observability-under-virtual-threads
linked_paths:
- contents/language/java/streaming-response-abort-surfaces-servlet-virtual-threads.md
- contents/language/java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md
- contents/language/java/virtual-thread-jdbc-cancel-semantics.md
- contents/language/java/servlet-async-timeout-downstream-deadline-propagation.md
- contents/language/java/servlet-asynclistener-cleanup-patterns.md
- contents/language/java/spring-jdbc-timeout-propagation-boundaries.md
- contents/language/java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md
- contents/language/java/jdbc-observability-under-virtual-threads.md
- contents/language/java/jdbc-db-side-cancel-confirmation-playbook.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
confusable_with:
- language/streaming-response-abort-surfaces-servlet-virtual-threads
- language/virtual-thread-jdbc-cancel-semantics
- language/jdbc-db-side-cancel-confirmation-playbook
forbidden_neighbors: []
expected_queries:
- 대용량 CSV 다운로드 중 client가 끊겼을 때 JDBC cursor와 Statement를 어떻게 정리해야 해?
- fetchSize를 줬는데도 download abort 후 DB query가 남을 수 있는 이유가 뭐야?
- StreamingResponseBody에서 ResultSet lifetime을 writer callback 안에 묶어야 하는 이유를 설명해줘
- broken pipe를 보면 Statement.cancel과 ResultSet.close를 어떤 순서로 호출해야 해?
- servlet timeout과 JDBC cursor cleanup을 하나의 cancelOnce로 묶는 설계를 알려줘
contextual_chunk_prefix: |
  이 문서는 servlet streaming download abort를 JDBC ResultSet/cursor/Statement cancel/close 수명으로 번역하는 advanced playbook이다.
  JDBC cursor cleanup, fetchSize streaming, broken pipe, Statement.cancel, StreamingResponseBody, large export 질문이 본 문서에 매핑된다.
---
# JDBC Cursor Cleanup on Download Abort

> 한 줄 요약: 대용량 servlet 다운로드에서 `fetchSize`는 메모리 압력을 줄이는 힌트일 뿐이고, 실제 안전성은 "현재 `ResultSet`/cursor/`Statement`가 streaming writer와 같은 수명 안에 묶여 있는가", "client abort나 timeout을 `Statement.cancel()`과 resource close로 바로 번역하는가"에 달려 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./streaming-response-abort-surfaces-servlet-virtual-threads.md)
> - [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./streamingresponsebody-sseemitter-terminal-cleanup-matrix.md)
> - [Virtual-Thread JDBC Cancel Semantics](./virtual-thread-jdbc-cancel-semantics.md)
> - [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./servlet-async-timeout-downstream-deadline-propagation.md)
> - [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./servlet-asynclistener-cleanup-patterns.md)
> - [Spring JDBC Timeout Propagation Boundaries](./spring-jdbc-timeout-propagation-boundaries.md)
> - [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](./jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)
> - [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)
> - [DB-Side Cancel Confirmation Playbook](./jdbc-db-side-cancel-confirmation-playbook.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

> retrieval-anchor-keywords: JDBC cursor cleanup on download abort, servlet download abort JDBC cursor cleanup, large export query cancel, fetch-size streaming servlet download, `PreparedStatement.setFetchSize` streaming export, server-side cursor download cleanup, `ResultSet` lifetime `Statement` lifetime, cursor lifetime vs response lifetime, `StreamingResponseBody` JDBC streaming cleanup, broken pipe query cancel, client abort `Statement.cancel`, download abort `ResultSet.close`, download abort cursor close vs cancel, fetch size batch cleanup latency, large CSV export JDBC streaming, read-only forward-only export cursor, streaming export connection hold time, servlet timeout statement cancel, async listener JDBC cancel bridge, DB cursor orphan query, download abort DB-side cancel confirmation

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [수명 지도](#수명-지도)
- [`fetchSize` streaming의 진짜 의미](#fetchsize-streaming의-진짜-의미)
- [abort에서 cleanup까지](#abort에서-cleanup까지)
- [코드로 보기](#코드로-보기)
- [운영 체크리스트](#운영-체크리스트)
- [실전 시나리오](#실전-시나리오)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

대용량 CSV/NDJSON 다운로드를 JDBC로 직접 streaming할 때는 보통 세 흐름이 겹친다.

- servlet response가 chunk를 내보내는 **HTTP lifetime**
- `StreamingResponseBody`나 async writer가 row를 직렬화하는 **writer lifetime**
- `ResultSet`/cursor가 다음 batch를 fetch하는 **JDBC cursor lifetime**

여기서 `fetchSize`는 세 번째 흐름의 batch 크기에 영향을 주는 힌트다.  
하지만 `fetchSize`만으로 다음이 해결되지는 않는다.

- driver가 실제로 full buffering 대신 점진 fetch를 하는가
- client가 다운로드를 중단했을 때 cursor와 query가 바로 닫히는가
- `Statement`와 connection이 pool로 빨리 돌아가는가

핵심 오해는 두 가지다.

- `fetchSize`를 줬으니 abort 시 cursor도 자동으로 정리된다고 기대하는 것
- servlet write가 실패하면 JDBC query도 이미 멈췄다고 간주하는 것

둘 다 portable하게 기대하면 안 된다.  
실전에서 안전한 설계는 "writer가 종료 신호를 본 순간 현재 in-flight `Statement`에 cancel을 보낼 수 있고, 그 뒤 `ResultSet`/`Statement`/connection close가 같은 coordinator에서 한 번만 실행되는 구조"다.

## 수명 지도

| 레이어 | 보통 시작 시점 | 정상 종료 시점 | abort 시 바로 해야 할 일 | 흔한 실수 |
|---|---|---|---|---|
| HTTP response | controller가 streaming body를 반환하고 first byte를 내보낼 때 | 마지막 chunk flush 후 응답 종료 | 더 이상 body rewrite를 시도하지 않고 stop signal만 남김 | broken pipe를 business error body로 바꾸려 함 |
| writer loop | async writer callback 진입 시 | row loop가 끝나고 마지막 `flush()`가 성공할 때 | `closed`/`stop` flag를 올리고 late write를 억제 | writer 예외를 삼키고 producer를 계속 돌림 |
| `ResultSet` / server cursor | `executeQuery()` 후 첫 row fetch 시 | 모든 row를 읽거나 `ResultSet.close()`가 실행될 때 | row 생산 중단, cursor close | controller 밖에서 먼저 열어 두고 callback later-use를 시도 |
| `Statement` | query 준비 직후 | `ResultSet` 소비가 끝나고 statement close 시 | `Statement.cancel()` 후 close | abort인데 `close()`만 기다려 fetch block을 오래 끌고 감 |
| connection / transaction | datasource에서 borrow 시 | commit/rollback 후 pool return 시 | rollback/close/evict 정책 실행 | 다운로드 속도만큼 transaction을 오래 열어 둠 |

표에서 중요한 점은 ownership이다.

- `ResultSet`은 `Statement`의 일부 수명 안에 있다
- `Statement`는 connection과 transaction 수명 안에 있다
- response abort는 이 아래 레이어를 자동으로 닫지 않는다

즉 다운로드 abort 처리의 본질은 "HTTP lifetime 종료를 JDBC lifetime 종료로 번역하는 브리지"다.

## `fetchSize` streaming의 진짜 의미

### 1. `fetchSize`는 streaming 보장이 아니라 batch 힌트다

`PreparedStatement.setFetchSize(n)` 또는 framework fetch-size 설정은 보통 "다음 row를 몇 개 단위로 가져올지"를 driver에 힌트한다.  
하지만 실제 동작은 driver/DB/transaction mode에 따라 달라진다.

- 어떤 조합에서는 server-side cursor나 incremental fetch처럼 동작한다
- 어떤 조합에서는 여전히 driver가 많은 row를 미리 buffer할 수 있다
- ORM이나 higher-level abstraction이 중간에서 list materialization을 해 버리면 `fetchSize` 의미가 거의 사라질 수 있다

그래서 `fetchSize`를 튜닝할 때의 질문은 "숫자를 몇으로 둘까?"보다 먼저 다음이다.

- heap이 정말 row count에 비례해 치솟지 않는가
- network round trip이 batch 단위로 보이는가
- connection hold time이 다운로드 속도에 지나치게 묶이지 않는가

즉 `fetchSize`는 **메모리-왕복 횟수-취소 반응성**의 균형점이지, cleanup 계약 그 자체가 아니다.

### 2. cursor와 writer는 같은 실행 수명 안에서 열고 닫아야 한다

`StreamingResponseBody` 같은 패턴에서 가장 위험한 구조는 controller 메서드 안에서 `ResultSet`을 먼저 열어 두고, 나중에 실행될 writer callback이 그 핸들을 이어받는 방식이다.

이 구조는 두 방향으로 망가지기 쉽다.

- try-with-resources 범위가 controller 메서드에 묶여 있으면 callback이 돌기 전에 cursor가 닫힌다
- 반대로 자원을 밖으로 탈출시키면 abort/timeout 시 close 지점이 흐려져 leak가 생긴다

안전한 기본형은 단순하다.

1. writer callback이 시작된 뒤 query를 연다
2. row loop와 `write`/`flush`를 같은 scope에서 돌린다
3. `ResultSet`, `Statement`, connection을 그 scope 안에서 닫는다

즉 cursor lifetime은 response 객체의 생성 시점이 아니라 **실제 stream producer가 실행되는 시점**에 맞춰야 한다.

### 3. batch 크기는 cleanup latency와도 연결된다

`fetchSize`가 클수록 보통 왕복 횟수는 줄지만, abort 직후 낭비되는 작업량은 커질 수 있다.

- 이미 driver/DB가 다음 batch를 크게 준비해 둔 상태라면 client가 끊겨도 더 많은 row가 헛되이 fetch된다
- `write`/`flush` 사이 간격이 길어져 broken pipe를 늦게 볼 수 있다
- connection과 transaction이 더 오래 잡혀 pool hold time이 늘 수 있다

반대로 `fetchSize`가 너무 작으면:

- network round trip이 늘고 throughput이 떨어질 수 있다
- DB cursor fetch 호출 자체가 병목처럼 보일 수 있다

그래서 export 경로의 `fetchSize`는 단순 DB 성능 knob이 아니라 **abort 이후 남는 tail work 길이**까지 포함해서 잡아야 한다.

## abort에서 cleanup까지

### 1. abort는 보통 다음 `write`/`flush`에서 보인다

브라우저가 다운로드를 취소하거나 proxy가 먼저 끊어도 서버는 대개 다음 시점에서야 그 사실을 안다.

- `OutputStream.write()` / `flush()`의 `IOException`
- framework async timeout callback
- request completion/error callback

즉 다운로드 중단을 "탭을 닫는 순간"에 감지한다고 생각하면 설계가 틀어진다.  
실제 stop signal은 **다음 write 시도**나 **servlet async lifecycle callback**에서 온다.

### 2. cancel ordering은 보통 `stop -> cancel -> close -> suppress`가 안전하다

abort를 본 뒤에는 다음 순서가 읽기 쉽다.

1. `closed`/`stop` flag를 먼저 올린다
2. 현재 in-flight `Statement`가 있으면 `Statement.cancel()`을 시도한다
3. `ResultSet.close()` -> `Statement.close()` -> rollback/connection close를 실행한다
4. 이후 late write와 late completion을 suppression path로 보낸다

이 순서가 중요한 이유는 다음과 같다.

- stop flag가 먼저 있어야 다른 callback이나 producer loop가 추가 row 생성을 멈춘다
- `cancel()`이 있어야 현재 fetch/query block을 줄일 수 있다
- close만 의존하면 driver가 fetch 반환을 기다리는 동안 connection이 오래 잡힐 수 있다

즉 `close()`는 필수지만, abort 순간에는 종종 **너무 늦은 정리 신호**다.  
`cancel()`은 그 gap을 줄이는 명시적 브리지다.

### 3. timeout/disconnect와 JDBC deadline을 따로 두되 ownership은 하나로 묶는다

다운로드 경로에서 흔한 anti-pattern은 신호 출처마다 cleanup 코드를 따로 두는 것이다.

- broken pipe catch에서만 stop
- async timeout callback에서만 fallback response
- JDBC statement timeout은 별도 설정

이렇게 흩어 놓으면 어느 한 경로가 빠질 때 orphan query가 남는다.  
더 안전한 구조는 timeout, disconnect, normal complete가 모두 같은 `cancelOnce(reason)`를 호출하게 만드는 것이다.

그 위에 레이어별 timeout을 얹는다.

- statement timeout: 정상적인 query deadline
- request/download timeout: 현재 응답을 포기하는 parent deadline
- network timeout / pool eviction: cancel이 안 먹을 때 connection을 버리는 fail-safe

핵심은 timeout 숫자가 여러 개여도 ownership entrypoint는 하나여야 한다는 점이다.

### 4. `Statement.cancel()`이 끝이 아니고, DB 쪽 확인은 별도다

애플리케이션이 `cancel()`을 호출했다고 해서 DB 서버에서 statement가 이미 멈췄다는 뜻은 아니다.

- cancel request dispatch가 늦을 수 있다
- driver가 connection close로 더 거칠게 처리할 수 있다
- rollback/lock cleanup이 남을 수 있다

그래서 운영에서는 다음 둘을 분리해서 본다.

- app이 cancel을 시도했는가
- DB current session에서 원래 statement가 실제로 사라졌는가

후자는 [DB-Side Cancel Confirmation Playbook](./jdbc-db-side-cancel-confirmation-playbook.md)으로 확인하는 편이 안전하다.

## 코드로 보기

### writer lifetime 안에서 cursor를 열고, terminal signal을 같은 handle로 닫기

```java
final class JdbcDownloadSession {
    private final DataSource dataSource;
    private final AtomicBoolean closed = new AtomicBoolean();
    private final AtomicReference<Statement> inFlight = new AtomicReference<>();

    JdbcDownloadSession(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    void streamTo(OutputStream outputStream) throws Exception {
        try (Connection connection = dataSource.getConnection()) {
            connection.setReadOnly(true);

            try (PreparedStatement statement = connection.prepareStatement(
                    """
                    select id, created_at, amount
                    from orders
                    order by id
                    """,
                    ResultSet.TYPE_FORWARD_ONLY,
                    ResultSet.CONCUR_READ_ONLY
            )) {
                statement.setFetchSize(500);
                statement.setQueryTimeout(30);
                inFlight.set(statement);

                try (ResultSet rs = statement.executeQuery();
                     BufferedWriter writer = new BufferedWriter(
                             new OutputStreamWriter(outputStream, StandardCharsets.UTF_8)
                     )) {
                    int emitted = 0;
                    while (!closed.get() && rs.next()) {
                        writer.write(toCsvLine(rs));
                        writer.newLine();
                        emitted++;

                        // flush cadence is also an abort probe.
                        if (emitted % 200 == 0) {
                            writer.flush();
                        }
                    }

                    writer.flush();
                } catch (IOException clientAbort) {
                    cancel("client-abort");
                    throw clientAbort;
                } finally {
                    inFlight.compareAndSet(statement, null);
                }
            }
        } finally {
            closed.set(true);
        }
    }

    void cancel(String reason) {
        if (!closed.compareAndSet(false, true)) {
            return;
        }

        Statement statement = inFlight.getAndSet(null);
        if (statement != null) {
            try {
                statement.cancel();
            } catch (SQLException ignored) {
                // Driver-specific failure is handled by outer close/timeout layers.
            }
        }
    }

    private String toCsvLine(ResultSet rs) throws SQLException {
        return rs.getLong("id") + "," + rs.getTimestamp("created_at") + "," + rs.getBigDecimal("amount");
    }
}
```

controller는 보통 아래처럼 이 session을 writer lifetime에 맞춰 사용한다.

```java
@GetMapping("/exports/orders.csv")
public ResponseEntity<StreamingResponseBody> exportOrders() {
    JdbcDownloadSession session = new JdbcDownloadSession(dataSource);

    StreamingResponseBody body = outputStream -> session.streamTo(outputStream);

    // servlet timeout / onError / onCompletion path도 같은 session.cancel(...)을 호출해야 한다.
    return ResponseEntity.ok().body(body);
}
```

예제의 핵심은 framework API 이름이 아니라 수명 정렬이다.

- query는 writer callback 안에서 시작한다
- `Statement` handle을 외부 cancel bridge가 볼 수 있다
- broken pipe, timeout, request completion이 모두 같은 `cancel(...)`을 쓴다

### 피해야 할 구조

다음 구조는 겉으로는 단순해 보여도 수명이 어긋난다.

- controller 메서드에서 `ResultSet`을 미리 열고 callback이 나중에 소비하게 함
- `fetchSize`만 주고 `Statement.cancel()` 표면을 전혀 만들지 않음
- writer 실패를 log만 남기고 connection/transaction 종료를 framework magic에 맡김

대용량 export는 느린 client 때문에 connection hold time이 길어지기 쉬우므로, 이런 구조는 pool starvation과 orphan query를 같이 만든다.

## 운영 체크리스트

- `response_aborted`, `statement_cancel_requested`, `statement_cancel_failed`, `cursor_closed`, `connection_returned`를 분리 기록한다.
- export마다 `rows_emitted`, `bytes_emitted`, `fetch_size`, `flush_interval`, `hold_ms`를 같이 남긴다.
- DB session correlation key(`pg_backend_pid()`, `connection_id()`, `@@SPID`)를 남겨 cancel 실제 효과를 DB 쪽에서 확인할 수 있게 한다.
- `client-abort`, `server-timeout`, `operator-cancel`을 같은 메트릭으로 뭉개지 않는다.
- active pool이 줄지 않거나 hold time tail이 길면 `cancel()`만 보지 말고 connection close/eviction까지 확인한다.

## 실전 시나리오

### 시나리오 1: 브라우저가 CSV 다운로드를 중간 취소했는데 query는 몇 초 더 돈다

가장 흔한 타임라인은 이렇다.

```text
browser cancels download
-> app is still mapping rows or waiting next fetch batch
-> next write/flush surfaces broken pipe
-> no statement cancel path exists
-> query ends only when statement timeout or full scan finishes
```

핵심 원인은 `fetchSize`가 아니라 **abort와 `Statement.cancel()`이 연결되지 않은 것**이다.

### 시나리오 2: `fetchSize`를 줬는데 heap이 여전히 크게 뛴다

이 경우는 cleanup보다 먼저 "정말 streaming이 되고 있는가"를 의심해야 한다.

- driver가 full buffer에 가깝게 동작할 수 있다
- 중간 mapper가 list를 모아 둘 수 있다
- serializer가 row를 메모리에 오래 붙들 수 있다

즉 `fetchSize` 숫자만 보고 cursor-based streaming이 활성화됐다고 결론 내리면 안 된다.

### 시나리오 3: cancel은 보냈는데 pool active가 오래 안 내려온다

가능성은 보통 셋이다.

- DB 쪽에서 query cancel이 늦게 먹고 있다
- transaction rollback이나 lock cleanup이 남아 있다
- driver가 connection을 더는 재사용하기 어렵게 만들어 pool eviction이 필요하다

이때는 app 로그만으로 "cleanup 완료"라고 말하지 말고 DB-side cancel 확인과 pool return latency를 같이 봐야 한다.

## 트레이드오프

- 작은 `fetchSize`: abort 반응성은 좋지만 round trip과 fetch overhead가 늘 수 있다.
- 큰 `fetchSize`: throughput은 나아질 수 있지만 client가 끊긴 뒤 낭비되는 tail work가 커질 수 있다.
- direct DB-to-client streaming: 추가 저장소 없이 바로 내려줄 수 있지만 connection/transaction이 client 속도에 묶인다.
- pre-materialized export file: DB hold time은 짧아지지만 디스크/object storage와 별도 cleanup 비용이 생긴다.

즉 느린 다운로드가 흔하고 resumable export가 중요하다면, "JDBC cursor를 오래 붙든 direct streaming" 자체가 맞는지 다시 보는 편이 낫다.

## 꼬리질문

- 우리 driver는 `fetchSize`를 실제 server-side cursor/streaming으로 쓰는가, 아니면 여전히 크게 prefetch하는가?
- download abort 후 `Statement.cancel()`과 `ResultSet.close()` 중 무엇이 먼저 실행되고, connection은 몇 ms 안에 pool로 돌아오는가?
- client 속도가 매우 느린 export에서 direct streaming보다 background materialization이 더 안전하지 않은가?

## 한 줄 정리

대용량 다운로드에서 `fetchSize`는 cursor를 "가볍게" 만들 수는 있지만 "자동으로 안전하게" 만들지는 않는다.  
안전성의 핵심은 cursor/`Statement` 수명을 writer와 같이 묶고, abort/timeout을 `Statement.cancel()`과 close/rollback으로 즉시 번역하는 cleanup ownership을 분명히 두는 것이다.
