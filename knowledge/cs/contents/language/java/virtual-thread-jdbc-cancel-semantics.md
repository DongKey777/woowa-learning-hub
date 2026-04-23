# Virtual-Thread JDBC Cancel Semantics

> 한 줄 요약: Spring MVC 요청이 virtual thread 위에서 돈다고 해서 JDBC query cancel이 자동으로 맞물리지는 않는다. `interrupt`는 애플리케이션 취소 의도, statement timeout은 JDBC deadline, driver-specific `cancel()`은 실제 DB 중단 시도이며, 필요하면 `setNetworkTimeout`이나 connection abort까지 계층적으로 설계해야 orphan query를 줄일 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)
> - [DB-Side Cancel Confirmation Playbook](./jdbc-db-side-cancel-confirmation-playbook.md)
> - [JDBC Cursor Cleanup on Download Abort](./jdbc-cursor-cleanup-download-abort.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./servlet-async-timeout-downstream-deadline-propagation.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./servlet-asynclistener-cleanup-patterns.md)
> - [Spring Transaction Debugging Playbook](../../spring/spring-transaction-debugging-playbook.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../../spring/spring-mvc-async-deferredresult-callable-dispatch.md)

> retrieval-anchor-keywords: virtual thread JDBC cancel semantics, Spring MVC virtual thread JDBC cancel, interrupt vs query timeout, interrupt vs Statement.cancel, JDBC cancellation ladder, `Statement.cancel`, `Statement.setQueryTimeout`, `SQLTimeoutException`, query timeout vs network timeout, `Connection.setNetworkTimeout`, request timeout query keeps running, client disconnect long query, Spring transaction timeout to statement timeout, `DataSourceUtils.applyTransactionTimeout`, request deadline to statement timeout, servlet async timeout JDBC propagation, servlet async timeout statement cancel, driver-specific cancel, PostgreSQL cancel request, MySQL `KILL QUERY`, SQL Server attention event, orphan query after request timeout, JDBC cancel registry, DB-side cancel confirmation, cancel propagation evidence, PostgreSQL/MySQL/SQL Server cancel confirmation, download abort JDBC cancel, fetch-size cursor cleanup, streaming export statement cancel

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [취소 레이어 지도](#취소-레이어-지도)
- [깊이 들어가기](#깊이-들어가기)
- [Spring MVC 경계에서 보기](#spring-mvc-경계에서-보기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [운영 체크리스트](#운영-체크리스트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

virtual thread는 "blocking 중인 request thread의 비용"을 바꾼다.  
하지만 이미 날아간 JDBC query를 누가 어떻게 멈출지는 여전히 별도 계약이다.

Spring MVC + JDBC 경로에서 취소는 보통 네 층으로 나뉜다.

- `interrupt`: 현재 request code나 worker loop에 "이제 포기해라"라고 알리는 JVM 신호
- statement timeout: JDBC statement 하나에 적용되는 deadline
- `Statement.cancel()`: 이미 실행 중인 statement에 대해 다른 thread가 보내는 명시적 cancel 시도
- network timeout / connection abort: cancel이 먹지 않거나 socket read가 매달릴 때 connection 자체를 끊는 최후 수단

핵심 오해는 "request가 virtual thread니까 client timeout이나 `Future.cancel(true)`가 query도 같이 멈춘다"는 기대다.  
portable JDBC 관점에서는 그렇지 않다.

- current virtual thread가 interrupt를 받아도 driver가 서버 쿼리를 중단한다는 보장은 없다
- statement timeout이 나도 transaction 밖 non-SQL work까지 같이 멈추는 것은 아니다
- `Statement.cancel()`은 유용하지만 현재 in-flight statement handle을 잡고 있어야 한다

즉 virtual thread 환경의 JDBC 취소는 "한 버튼"이 아니라 계층형이다.

## 취소 레이어 지도

| 신호 | 누가 보낸다 | 보통 멈추는 것 | 보장하지 않는 것 | 실전 용도 |
|---|---|---|---|---|
| `Thread.interrupt()` / `Future.cancel(true)` | app timeout, shutdown, async callback | Java loop, `sleep`, `wait`, 일부 interruptible block | 서버에서 이미 실행 중인 SQL 자체의 중단 | request code와 worker를 빨리 접게 만들기 |
| `Statement.setQueryTimeout(...)` | JDBC / Spring transaction timeout wiring | 해당 statement의 deadline 초과 시 driver의 cancel 시도 + `SQLTimeoutException` | query 밖의 business logic, 이미 detach된 다른 task | 가장 portable한 per-statement 보호막 |
| `Statement.cancel()` | timeout callback, watchdog, admin thread | 현재 실행 중인 statement에 대한 즉시 cancel 시도 | driver 미지원, statement handle 부재, cancel 자체의 성공 보장 | request timeout/abort를 실제 query cancel과 연결하기 |
| `Connection.setNetworkTimeout(...)`, `abort(...)`, `close()` | connection owner, pool, admin thread | DB 응답이 없는 socket read/hang, connection 전체 정리 | 정상 query deadline 제어, statement만 살리는 정밀 취소 | cancel 실패나 network partition의 fail-safe |

표에서 중요한 점은 ownership이다.  
각 레이어는 같은 문제를 풀지 않는다.

## 깊이 들어가기

### 1. virtual thread의 interrupt semantics는 바뀌지 않는다

virtual thread도 `interrupt`는 그대로 협력적 취소 신호다.  
즉 다음에는 잘 동작할 수 있다.

- Java loop의 `isInterrupted()` 체크
- `sleep`, `wait`, `BlockingQueue.take()` 같은 interruptible wait
- app이 직접 작성한 timeout / shutdown wiring

하지만 JDBC query cancel은 별개다.

- driver가 interrupt를 보고 `Statement.cancel()`이나 connection close로 번역해 주는지 portable하게 기대할 수 없다
- 이미 `executeQuery()` 안에서 서버 응답을 기다리는 동안, 실제 종료 조건은 statement timeout이나 driver-specific cancel인 경우가 많다
- 따라서 interrupt만 걸고 끝내면 "request virtual thread는 취소됐는데 DB는 계속 실행 중"인 상태가 남을 수 있다

정리하면 interrupt는 **request-level intent**이고, query cancel은 **driver/DB-level effect**다.

### 2. statement timeout은 가장 portable한 query deadline이다

JDBC `Statement.setQueryTimeout(...)`의 의미는 "시간이 지나면 driver가 현재 statement를 cancel하려고 시도한다"는 쪽에 가깝다.  
성공 시 호출자는 보통 `SQLTimeoutException`을 보게 된다.

virtual thread 환경에서 이 레이어가 특히 중요한 이유는 다음과 같다.

- client abort나 servlet timeout이 현재 request virtual thread에 즉시 반영되지 않을 수 있다
- request thread가 싸져서 "조용히 남아 있는 오래된 query"를 더 많이 만들 수 있다
- statement timeout은 request thread의 상태와 별개로 JDBC statement마다 적용할 수 있다

Spring에서는 transaction timeout이 JDBC statement timeout으로 이어질 수 있다.  
대표적으로 Spring JDBC path에서는 현재 transaction의 남은 시간을 `Statement.setQueryTimeout(...)`으로 적용하는 wiring을 쓸 수 있다.

여기서 주의할 점은 세 가지다.

- statement timeout은 statement 단위다. transaction 안의 JSON 매핑, 외부 HTTP, retry sleep까지 막아 주지 않는다
- Spring-aware 경로를 벗어난 raw JDBC/driver 호출은 직접 timeout을 주지 않으면 비어 있을 수 있다
- timeout을 중복 설정하면 더 긴 값으로 덮어쓰는 실수를 하기 쉽다. transaction timeout과 statement timeout의 단일 출처를 정하는 편이 낫다

### 3. `Statement.cancel()`은 "다른 thread가 보낼 수 있는 query cancel"이다

JDBC는 `Statement.cancel()`을 별도 thread에서 호출해 in-flight query를 중단하려는 용도를 열어 둔다.  
이 점이 Spring MVC timeout callback과 잘 맞는다.

예를 들면 다음 흐름이다.

1. controller나 service가 현재 request의 `Statement`를 registry에 등록한다
2. servlet async timeout, request watchdog, admin stop 버튼이 별도 callback thread에서 발동한다
3. callback이 `statement.cancel()`과 `task.cancel(true)`를 둘 다 호출한다

이 패턴의 장점은 명확하다.

- interrupt만으로는 닿지 않는 query cancel을 명시적으로 보낼 수 있다
- request lifetime 종료와 DB statement lifetime 종료를 더 촘촘히 묶을 수 있다

반대로 비용도 있다.

- current `Statement` handle이 필요하다
- cleanup을 빼먹으면 registry가 stale reference를 남긴다
- cancel이 성공했는지 driver/DB 측 증거를 따로 봐야 한다

즉 `Statement.cancel()`은 강력하지만, "요청마다 현재 query를 추적하는 plumbing"이 필요하다.

### 4. driver-specific cancel이 실제 체감을 결정한다

JDBC 표면은 같아도 query cancel의 실제 메커니즘은 driver마다 다르다.  
virtual thread 문서보다 driver 문서를 먼저 믿어야 하는 이유가 여기 있다.

- PostgreSQL 계열에서는 cancel이 현재 data connection이 아니라 별도 cancel request 경로로 전달되는 형태를 많이 쓴다. 그래서 interrupt보다 explicit cancel/timeout wiring이 더 직접적이고, cancel 경로 자체의 timeout도 별도로 봐야 한다.
- MySQL 계열에서는 query timeout이나 `cancel()`이 별도 제어 connection과 `KILL QUERY` 계열 동작에 기대거나, 설정에 따라 connection 자체를 끊는 쪽으로 더 거칠게 동작할 수 있다. cancel 폭주 시에는 query path 말고 control path 부하도 생긴다.
- SQL Server 계열에서는 query timeout/cancel이 server의 Attention 계열 이벤트와 연결돼 관측될 수 있다. 즉 application timeout만 보지 말고 DB 쪽에서 실제 cancel이 들어왔는지도 같이 봐야 한다.

이 차이 때문에 실전 질문도 달라진다.

- cancel이 query만 죽이고 connection은 계속 쓸 수 있는가
- cancel이 실패하면 connection abort로 승격해야 하는가
- server에서 cancel 흔적을 어떻게 확인할 수 있는가

마지막 질문은 애플리케이션 로그만으로 답하기 어렵다.  
엔진별 server-side 증거는 [DB-Side Cancel Confirmation Playbook](./jdbc-db-side-cancel-confirmation-playbook.md)에서 따로 정리했다.

virtual thread는 이 driver-specific gap을 없애 주지 않는다.

### 5. network timeout은 마지막 safety net이다

`Connection.setNetworkTimeout(...)`은 query timeout과 다른 계층이다.

- query timeout은 statement cancel을 먼저 시도하는 정상 경로에 가깝다
- network timeout은 DB 응답이 아예 돌아오지 않아 socket read가 오래 매달릴 때 connection을 unusable로 만들 수 있는 강한 fail-safe다

그래서 운영 원칙은 대체로 이렇다.

- statement timeout이 먼저 발동하도록 둔다
- network timeout은 그보다 약간 높게 둬서 hung socket을 정리한다
- network timeout이 터졌다면 statement만이 아니라 connection 전체를 버릴 각오를 한다

즉 network timeout은 SLA를 세밀하게 맞추는 knob가 아니라, "cancel/timeout 경로가 실패했을 때도 thread와 connection을 영원히 묶어 두지 않기 위한 장치"다.

## Spring MVC 경계에서 보기

### 1. 동기 controller + virtual thread는 query cancel hook을 자동으로 주지 않는다

`spring.threads.virtual.enabled`로 request-per-virtual-thread를 켜면 controller/service 코드가 virtual thread에서 straight-line으로 돈다.  
하지만 다음은 자동으로 생기지 않는다.

- client disconnect를 즉시 현재 handler virtual thread interrupt로 번역하는 보장
- servlet timeout을 현재 JDBC statement cancel로 이어 주는 브리지
- request 종료 후에도 남아 있는 query를 회수하는 registry

그래서 동기 MVC 경로에서는 흔히 이 순서가 나온다.

1. client나 gateway가 먼저 포기한다
2. app은 아직 `executeQuery()` 안에서 기다린다
3. current virtual thread는 별다른 신호를 못 받거나 늦게 받는다
4. query는 statement timeout이나 explicit cancel이 오기 전까지 계속 돈다

즉 virtual thread request handling은 cancellation gap을 없애지 않는다.

### 2. async MVC나 별도 watchdog가 있으면 `interrupt`와 `cancel()`을 둘 다 연결한다

`DeferredResult`, `WebAsyncTask`, `Callable`, 또는 app-level watchdog가 있으면 timeout callback이 생긴다.  
이때는 두 신호를 같이 보내는 편이 안전하다.

- `task.cancel(true)`로 request-side worker를 접게 한다
- `statement.cancel()`로 이미 날아간 query를 끊으려 시도한다

둘 중 하나만 쓰면 빈틈이 남는다.

- interrupt만 쓰면 DB query가 남을 수 있다
- query cancel만 쓰면 request-side business logic/cleanup loop는 계속 돌 수 있다

### 3. transaction timeout과 request timeout의 ordering을 맞춘다

Spring MVC request budget과 JDBC budget을 대충 맞추면 orphan work가 잘 생긴다.  
대체로 정상 deadline과 fail-safe를 다음처럼 나누면 읽기 쉽다.

```text
JDBC statement timeout 1200ms
-> servlet async timeout or app request timeout 1800ms
-> gateway/client deadline 2000ms

fail-safe: connection network timeout 2500ms
```

의도는 단순하다.

- query가 request보다 약간 먼저 포기해야 cleanup 시간이 남는다
- network timeout은 정상 query timeout보다 나중에 발동해야 connection abort가 과하게 늘지 않는다

여기서 더 중요한 건 transaction 안에 query 밖 대기를 넣지 않는 것이다.  
transaction timeout이 statement timeout으로 잘 매핑돼도, transaction 사이의 외부 HTTP와 retry sleep은 별도 취소 계약이 필요하다.

## 실전 시나리오

### 시나리오 1: gateway는 504인데 PostgreSQL query는 계속 돈다

controller는 virtual thread 위에서 blocking JDBC를 호출 중이다.  
gateway deadline이 먼저 만료됐지만 app은 아직 disconnect를 늦게 보거나 못 보고 있다.

이때 실제 종료 조건은 대개 다음 중 하나다.

- statement timeout이 만료돼 driver가 cancel request를 보낸다
- 별도 callback/watchdog가 `Statement.cancel()`을 보낸다
- 더 나쁘면 network timeout이 connection을 끊는다

즉 "virtual thread인데 왜 DB가 안 멈추지?"가 아니라 "request cancel을 query cancel로 연결하지 않았다"가 핵심이다.

### 시나리오 2: `@Transactional(timeout = 2)`는 걸었는데 transaction hold time은 더 길다

Spring이 statement timeout wiring을 해 줘도, timeout은 SQL 실행 구간에만 강하게 닿는다.  
transaction 안에 다음이 섞여 있으면 여전히 hold time이 길어진다.

- 외부 HTTP
- cache miss 후 원격 조회
- retry/backoff sleep
- 큰 payload mapping

이 경우 query는 2초 안에 멈춰도 connection hold time과 request latency는 더 길 수 있다.

### 시나리오 3: async timeout callback에서 `task.cancel(true)`만 호출한다

worker virtual thread는 취소 신호를 받지만, JDBC driver는 query cancel을 못 받는다.  
그러면 app 로그상으로는 timeout 처리됐는데 DB는 몇 초 더 일하는 이상한 상태가 나온다.

이때는 timeout callback에서 `Statement.cancel()`을 같이 호출해야 blind spot이 줄어든다.

## 코드로 보기

### 1. 현재 request의 in-flight statement를 추적한다

```java
final class InFlightStatements {
    private final ConcurrentMap<String, Statement> statements = new ConcurrentHashMap<>();

    void register(String requestId, Statement statement) {
        statements.put(requestId, statement);
    }

    void clear(String requestId, Statement statement) {
        statements.remove(requestId, statement);
    }

    void cancel(String requestId) {
        Statement statement = statements.get(requestId);
        if (statement == null) {
            return;
        }
        try {
            statement.cancel();
        } catch (SQLException ignored) {
            // cancel is best-effort; caller should still rely on timeout/abort fallback
        }
    }
}
```

일반적인 `Statement`/`Connection` 사용은 thread-safe하지 않다.  
cross-thread 접점은 `cancel()`/`close()` 같은 제한된 동작으로 좁히는 편이 안전하다.

### 2. statement timeout과 registry를 같이 건다

```java
@Service
public class ReportQueryService {
    private final JdbcTemplate jdbcTemplate;
    private final DataSource dataSource;
    private final InFlightStatements inFlightStatements;

    public ReportQueryService(
            JdbcTemplate jdbcTemplate,
            DataSource dataSource,
            InFlightStatements inFlightStatements) {
        this.jdbcTemplate = jdbcTemplate;
        this.dataSource = dataSource;
        this.inFlightStatements = inFlightStatements;
    }

    @Transactional(timeout = 2)
    public ReportResponse load(String requestId, long reportId) {
        return jdbcTemplate.execute((ConnectionCallback<ReportResponse>) connection -> {
            try (PreparedStatement ps = connection.prepareStatement(
                    "select id, status from reports where id = ?")) {
                ps.setLong(1, reportId);

                // Spring transaction timeout을 statement timeout으로 반영한다.
                DataSourceUtils.applyTransactionTimeout(ps, dataSource);

                inFlightStatements.register(requestId, ps);
                try (ResultSet rs = ps.executeQuery()) {
                    return mapReport(rs);
                } finally {
                    inFlightStatements.clear(requestId, ps);
                }
            }
        });
    }
}
```

핵심은 "request timeout"과 "statement timeout"을 같은 값으로 두는 것이 아니라,  
request budget 안에서 statement deadline이 먼저 오도록 정렬하는 것이다.

### 3. timeout callback에서 worker interrupt와 query cancel을 함께 보낸다

```java
@GetMapping("/reports/{id}")
public DeferredResult<ResponseEntity<ReportResponse>> report(@PathVariable long id) {
    String requestId = UUID.randomUUID().toString();
    DeferredResult<ResponseEntity<ReportResponse>> result = new DeferredResult<>(1_800L);

    Future<?> task = applicationExecutor.submit(() -> {
        try {
            ReportResponse response = reportQueryService.load(requestId, id);
            if (!result.isSetOrExpired()) {
                result.setResult(ResponseEntity.ok(response));
            }
        } catch (Exception e) {
            if (Thread.currentThread().isInterrupted()) {
                Thread.currentThread().interrupt();
                return;
            }
            if (!result.isSetOrExpired()) {
                result.setErrorResult(ResponseEntity.internalServerError().build());
            }
        }
    });

    Runnable cancelWork = () -> {
        inFlightStatements.cancel(requestId);
        task.cancel(true);
    };

    result.onTimeout(() -> {
        cancelWork.run();
        if (!result.isSetOrExpired()) {
            result.setErrorResult(ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).build());
        }
    });
    result.onError((ex) -> cancelWork.run());
    result.onCompletion(cancelWork);

    return result;
}
```

동기 controller에는 이런 callback이 기본으로 보이지 않는다.  
그래서 sync MVC 경로에서 caller abort를 query cancel까지 끌고 가려면 container bridge, watchdog, driver timeout을 별도 설계해야 한다.

## 운영 체크리스트

- request timeout, statement timeout, network timeout을 서로 다른 메트릭/로그 필드로 남긴다
- `SQLTimeoutException`과 manual `cancel()` 성공/실패를 분리 집계한다
- DB 측에서 실제 cancel 흔적을 확인한다. app thread interrupt만으로 query stop을 추정하지 않는다
- registry cleanup을 `finally`에서 보장한다. stale statement reference를 남기면 엉뚱한 취소를 유발할 수 있다
- network timeout은 statement timeout보다 높게 두되, OS 기본 TCP timeout 수준까지 길게 방치하지는 않는다
- transaction 안의 외부 I/O, retry, sleep을 줄여 query timeout이 실질적인 보호막이 되게 한다

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| interrupt 중심 취소 | request-side code를 빠르게 접기 쉽다 | DB query가 계속 남을 수 있다 |
| statement timeout 중심 설계 | JDBC 표준에 가장 가깝고 portable하다 | query 밖 non-SQL work와 caller abort를 직접 표현하지 못한다 |
| `Statement.cancel()` registry 추가 | request timeout과 query cancel을 가깝게 묶을 수 있다 | statement 추적, cleanup, driver 차이 흡수가 필요하다 |
| network timeout / abort 의존 | hung socket과 failed cancel에 대한 최후 방어선이 된다 | connection을 버리므로 비용이 크고 정상 흐름 제어용으로는 거칠다 |

핵심은 하나를 고르는 것이 아니라, 어떤 레이어를 기본 보호막으로 두고 어떤 레이어를 fail-safe로 둘지 정렬하는 것이다.

## 꼬리질문

> Q: client disconnect가 나면 현재 virtual thread도 바로 interrupt되나요?
> 핵심: portable하게 기대하면 안 된다. disconnect 감지와 current handler interrupt, JDBC cancel은 서로 다른 경계다.

> Q: `setQueryTimeout()`과 `cancel()`은 같은 건가요?
> 핵심: 종종 내부 메커니즘은 닮아도 ownership이 다르다. 전자는 statement의 사전 deadline, 후자는 외부 callback이 보내는 명시적 중단 시도다.

> Q: virtual thread면 `Future.cancel(true)`만으로도 충분하지 않나요?
> 핵심: 아니다. interrupt는 request-side intent일 뿐이며, 이미 DB에 들어간 query stop은 driver cancel/timeout이 맡는 경우가 많다.

> Q: `setNetworkTimeout()`으로 query timeout을 대체해도 되나요?
> 핵심: 보통 아니다. network timeout은 connection 전체를 unusable로 만들 수 있는 강한 fail-safe라서 더 위에 두면 과도하다.

## 한 줄 정리

virtual thread는 blocking request의 비용을 낮출 뿐이므로, Spring MVC + JDBC 경로에서는 `interrupt -> statement timeout -> explicit cancel -> network abort`를 서로 다른 책임으로 나눠 설계해야 실제 query cancel이 맞물린다.
