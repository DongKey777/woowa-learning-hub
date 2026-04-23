# JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads

> 한 줄 요약: JDBC `Connection.setNetworkTimeout(...)`은 checked-out connection의 I/O fail-safe이고, driver `socketTimeout`/`readTimeout`은 physical connection에 걸리는 driver-specific read ceiling이며, pool timeout/eviction은 borrow wait와 lifecycle 관리다. virtual thread 환경에서는 셋 다 "timeout"처럼 보이지만, 시작 시점과 정리 단위가 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Virtual-Thread JDBC Cancel Semantics](./virtual-thread-jdbc-cancel-semantics.md)
> - [Spring JDBC Timeout Propagation Boundaries](./spring-jdbc-timeout-propagation-boundaries.md)
> - [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)
> - [Connection Budget Alignment After Loom](./connection-budget-alignment-after-loom.md)
> - [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./servlet-async-timeout-downstream-deadline-propagation.md)
> - [HikariCP 튜닝](../../database/hikari-connection-pool-tuning.md)

> retrieval-anchor-keywords: JDBC network timeout vs driver socket timeout, pool socket timeout misconception, `Connection.setNetworkTimeout`, JDBC network timeout pooled connection, driver `socketTimeout`, driver `readTimeout`, JDBC timeout ownership, Hikari `connectionTimeout` vs socket timeout, Hikari `maxLifetime` active connection eviction, Hikari `idleTimeout`, Hikari `keepaliveTime`, Hikari `validationTimeout`, pool borrow timeout vs query timeout, pool eviction cannot cancel active query, virtual threads JDBC timeout ladder, virtual thread JDBC socket hang, checked-out connection timeout leakage, request spike pool wait socket read, broken connection discard after timeout, statement timeout vs network timeout vs pool timeout

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [timeout ownership 지도](#timeout-ownership-지도)
- [깊이 들어가기](#깊이-들어가기)
- [virtual thread 부하에서 읽는 법](#virtual-thread-부하에서-읽는-법)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [운영 체크리스트](#운영-체크리스트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

virtual thread는 기다리는 request를 싸게 만든다.  
하지만 JDBC timeout의 ownership 자체를 바꾸지는 않는다.

이 주제에서 가장 먼저 바로잡아야 할 오해는 "`pool socket timeout`"이라는 표현이다.  
대부분의 connection pool은 **애플리케이션이 이미 빌려 간 connection의 query socket read**를 직접 소유하지 않는다.

pool이 주로 소유하는 것은 다음이다.

- connection을 얼마나 오래 빌리기 전 대기할 수 있는지
- idle connection을 언제 정리할지
- 오래된 connection을 언제 retire할지
- validation ping을 얼마나 오래 기다릴지

반대로 in-flight query의 network wait를 직접 끊는 쪽은 보통 다음 둘이다.

- driver-specific `socketTimeout`/`readTimeout`
- JDBC `Connection.setNetworkTimeout(...)`

그래서 virtual thread 환경에서는 timeout을 네 시계로 나눠 읽어야 한다.

1. pool acquire timeout: 아직 connection도 못 빌린 상태의 대기 한도
2. statement/query timeout: 정상 query deadline
3. driver socket/read timeout 또는 JDBC network timeout: I/O hang fail-safe
4. pool eviction/lifetime: connection lifecycle rotation

이 네 시계를 섞으면, 요청은 virtual thread 위에서 조용히 늘어나는데 원인은 전혀 다른 곳에 있게 된다.

## timeout ownership 지도

| knob | owner | timer가 재는 것 | 보통 깨지는 단위 | 해결하지 못하는 것 |
|---|---|---|---|---|
| pool `connectionTimeout` | pool | `getConnection()` 대기 시간 | borrow 시도 하나 | 이미 실행 중인 query의 socket hang |
| statement/query/transaction timeout | app + Spring + JDBC | statement deadline 또는 남은 tx TTL | statement 하나 | hung socket을 강제로 정리하는 fail-safe |
| driver `socketTimeout` / `readTimeout` | JDBC driver | physical connection의 read/write 대기 | 보통 connection 또는 current operation | pool borrow queue, idle retire |
| `Connection.setNetworkTimeout(...)` | JDBC API on checked-out connection | 해당 connection에서 JDBC call이 network 응답을 기다리는 시간 | 보통 checked-out connection 전체 | pool saturation 자체, idle eviction |
| pool `maxLifetime` / `idleTimeout` / `keepaliveTime` / `validationTimeout` | pool | idle/liveness/rotation 시간 | idle or returning connection | active query를 mid-flight로 취소하는 것 |

표의 핵심은 "timeout이 터졌을 때 무엇을 버리느냐"다.

- borrow timeout은 요청 하나를 포기한다
- statement timeout은 statement 하나를 포기하려고 시도한다
- driver socket timeout과 network timeout은 connection 자체를 broken으로 만들 수 있다
- pool eviction은 보통 idle 또는 return 시점의 connection lifecycle을 조정한다

즉 이름이 비슷해도 **정리 단위**가 다르다.

## 깊이 들어가기

### 1. "`pool socket timeout`"은 보통 잘못 붙인 이름이다

운영에서 자주 듣는 질문은 이렇다.

- "`Hikari timeout`을 줄였는데 왜 socket hang이 안 끊기죠?"

여기서 말하는 `Hikari timeout`은 대개 `connectionTimeout`이거나 `maxLifetime`이다.  
둘 다 query socket read를 직접 자르지 않는다.

- `connectionTimeout`: pool에서 connection을 빌리기까지 기다리는 시간
- `maxLifetime`: 오래된 connection을 retire 대상으로 표시하는 시간
- `idleTimeout`: idle connection 정리 시간
- `keepaliveTime`: idle connection에 대한 keepalive ping 주기
- `validationTimeout`: validation / `isValid()` 같은 liveness probe 대기 시간

즉 pool timeout을 줄였는데 hung query가 그대로라면 이상한 일이 아니다.  
pool은 이미 빌려 나간 active connection 안쪽의 read wait를 소유하지 않기 때문이다.

### 2. driver `socketTimeout`과 JDBC `setNetworkTimeout(...)`은 같은 층이 아니다

둘 다 "네트워크 오래 기다리면 끊는다"는 점에서는 비슷해 보인다.  
하지만 ownership과 적용 범위가 다르다.

driver `socketTimeout`/`readTimeout`은 보통 datasource URL이나 driver property로 고정된다.

- 대개 physical connection 생성 시점부터 driver가 참고한다
- query별로 다른 값을 주기보다는 connection 전체에 일괄 적용되는 경우가 많다
- 정확한 예외 형태와 적용 범위는 driver마다 다르다

반면 `Connection.setNetworkTimeout(...)`은 JDBC API다.

- checked-out connection에 대해 코드가 직접 설정할 수 있다
- request별 남은 budget에 맞춰 더 짧거나 긴 값을 줄 수 있다
- timeout이 나면 connection이 계속 안전하게 재사용되는지보다, **broken으로 보고 버려야 하는지**를 먼저 생각하는 편이 안전하다

실무에서는 둘을 같이 켜 둘 수 있다.  
하지만 그 경우에도 semantics가 합쳐져 "더 똑똑한 timeout"이 되는 것은 아니다.

- 더 먼저 터지는 I/O timeout이 실제 효과를 낼 가능성이 크다
- 어떤 예외로 surface되는지는 driver/pool 조합에 따라 달라질 수 있다
- 따라서 둘 다 설정하더라도 primary fail-safe 하나를 정하고 나머지는 그보다 바깥에 두는 편이 읽기 쉽다

### 3. pool eviction은 active hung connection을 바로 구해 주지 못한다

virtual thread 환경에서 가장 위험한 착시는 이것이다.

- "active connection 몇 개가 socket read에 걸렸어도 `maxLifetime`이 지나면 pool이 치워 주겠지"

보통 그렇게 기대하면 안 된다.

- pool retirement는 대개 idle connection이나 return 시점에 관측된다
- active query를 수행 중인 checked-out connection은 먼저 caller 쪽에서 빠져나와야 pool이 후속 정리를 할 수 있다
- keepalive도 idle connection을 대상으로 하는 경우가 일반적이므로, 이미 사용자 query를 수행 중인 connection을 구하지 못한다

즉 다음 상황에서는 pool eviction보다 borrow timeout이 먼저 전면에 나온다.

1. active connection 몇 개가 DB/네트워크 hang으로 늦게 돌아온다
2. virtual thread 수천 개가 `getConnection()` 근처에서 조용히 park된다
3. 새 요청은 `connectionTimeout`으로 실패한다
4. 운영자는 pool timeout만 보며 "왜 eviction이 안 먹지?"라고 느낀다

실제 원인은 대개 active connection 안쪽의 I/O hang이다.

### 4. virtual thread 부하에서는 잘못 정렬한 timeout이 더 조용히 쌓인다

platform thread 시절에는 worker 부족이 먼저 소리 내서 터졌다.  
virtual thread에서는 기다림 자체가 싸지므로, backlog가 pool과 DB 쪽으로 더 쉽게 밀린다.

그래서 timeout ordering이 더 중요해진다.

- driver socket/read timeout이 statement timeout보다 짧으면, 정상적으로는 statement deadline으로 끝낼 query도 connection broken으로 더 거칠게 끝날 수 있다
- network timeout이 request별 budget보다 너무 짧으면, 약간 느린 구간마다 connection discard와 재연결 churn이 늘 수 있다
- `maxLifetime`를 request SLA처럼 짧게 잡으면, 진짜 문제를 풀기보다 reconnect wave만 만든다

핵심은 이렇다.

- logical deadline은 statement/query timeout으로 먼저 건다
- I/O hang fail-safe는 driver socket timeout 또는 network timeout으로 바깥에 둔다
- pool lifetime/eviction은 per-request deadline이 아니라 lifecycle hygiene로 다룬다

### 5. checked-out connection state는 다음 borrower에게 새어 나가지 않게 봐야 한다

`setNetworkTimeout(...)`은 connection 객체 상태를 바꾼다.  
pool을 쓰는 순간 이 connection은 다음 request에 다시 빌려 갈 수 있다.

그래서 per-request로 network timeout을 바꿀 때는 다음 둘 중 하나가 필요하다.

- `finally`에서 원래 값으로 복구한다
- 현재 pool/driver 조합이 return 시점에 해당 상태를 reset하는지 검증한다

여기서 중요한 것은 "무조건 수동 복구해야 한다"가 아니다.  
정확한 reset 책임은 pool 구현에 따라 다를 수 있으므로, **가정하지 말고 검증**해야 한다는 뜻이다.

잘못되면 이런 현상이 나온다.

- A 요청이 공격적으로 500ms network timeout을 건다
- connection이 pool로 돌아간다
- B 요청이 같은 connection을 받아 예상보다 훨씬 짧은 I/O timeout으로 실패한다

virtual thread 환경에서는 이런 false timeout이 짧은 시간에 많이 번질 수 있다.

## virtual thread 부하에서 읽는 법

| 관측 신호 | 먼저 의심할 것 | 보통 맞는 해석 | 바로 다음 질문 |
|---|---|---|---|
| 많은 virtual thread가 `getConnection()` 근처에서 park + pending acquire 상승 | pool borrow wait | active connection이 늦게 돌아오거나 pool budget이 작다 | 왜 active connection이 늦게 반환되는가 |
| `SQLTimeoutException` 위주로 보이고 broken connection discard는 많지 않다 | statement/query timeout | logical deadline이 먼저 정상 발화 중이다 | transaction 안 non-SQL work가 남아 있지 않은가 |
| I/O 예외와 broken connection discard가 같이 늘고 신규 physical connection 생성이 튄다 | driver socket timeout 또는 `setNetworkTimeout` | fail-safe가 connection abort 쪽으로 발화했다 | 값이 너무 공격적이거나 network hang이 실제로 있는가 |
| `maxLifetime`/keepalive 관련 로그는 많은데 query latency는 그대로다 | pool lifecycle churn | lifetime 튜닝이 원인 대신 증상만 건드리고 있다 | active query wait와 분리해서 보고 있는가 |

virtual thread에서 중요한 점은 "기다림이 싸다"는 사실이다.  
그래서 backlog가 thread 부족 대신 pool pending, socket wait, connection churn으로 옮겨 다닌다.

## 실전 시나리오

### 시나리오 1: active connection 10개가 socket read에 걸리자 borrow timeout만 폭증한다

request는 모두 virtual thread라서 애플리케이션 thread 수는 크게 문제 없어 보인다.  
하지만 active connection 10개가 DB 응답을 못 받고 있으면, 뒤 request는 조용히 `getConnection()`에서 대기하다 `connectionTimeout`으로 죽는다.

이때 해석은 다음이 맞다.

- borrow timeout은 1차 증상이다
- 원인은 active connection 안쪽의 driver/network wait일 수 있다
- `maxLifetime`나 `idleTimeout`만으로는 현재 막힌 10개를 직접 회수하지 못한다

### 시나리오 2: driver `socketTimeout`을 statement timeout보다 짧게 뒀더니 connection churn이 시작된다

원래 의도는 "느린 query를 빨리 끊자"였지만 실제 결과는 더 거칠 수 있다.

- statement timeout이 query 단위로 끝낼 수 있는 일도
- driver socket timeout이 먼저 터지면
- query 실패와 함께 connection discard/reconnect가 늘어난다

즉 logical deadline과 transport fail-safe의 순서를 뒤집은 셈이다.

### 시나리오 3: request별 `setNetworkTimeout(...)`을 낮췄는데 다른 요청까지 false timeout이 난다

이건 pooled connection state hygiene 문제일 가능성이 높다.

- borrowed connection에 건 network timeout이 복구되지 않거나
- pool reset을 검증하지 않은 채 가정했거나
- next borrower가 이전 요청의 공격적인 값을 이어받았을 수 있다

이 경우 원인은 DB 느림이 아니라 timeout state leakage다.

## 코드로 보기

### 1. statement deadline과 network fail-safe를 분리해 건다

```java
Executor networkTimeoutExecutor = sharedNetworkTimeoutExecutor;

try (Connection connection = dataSource.getConnection()) {
    int previousNetworkTimeout = connection.getNetworkTimeout();
    try {
        connection.setNetworkTimeout(networkTimeoutExecutor, 2_500);

        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setQueryTimeout(2); // logical statement deadline
            try (ResultSet rs = ps.executeQuery()) {
                consume(rs);
            }
        }
    } finally {
        connection.setNetworkTimeout(networkTimeoutExecutor, previousNetworkTimeout);
    }
}
```

이 코드의 포인트는 다음 셋이다.

- statement timeout은 정상 deadline이다
- network timeout은 그보다 바깥의 fail-safe다
- pooled connection state를 바꿨다면 restore 또는 pool reset 검증이 필요하다

driver/property 쪽 socket timeout을 주로 쓴다면, 같은 connection에 request마다 다른 값이 필요한지부터 먼저 따져 보는 편이 낫다.  
request별 budget이 중요하면 JDBC network timeout이 더 직접적인 도구일 수 있다.

### 2. 관측 필드는 서로 분리해 남긴다

```text
jdbc.pool.acquire.timeout
jdbc.statement.timeout
jdbc.network.timeout
jdbc.driver.socket.timeout
jdbc.connection.discarded
jdbc.pool.pending
```

이 필드를 하나의 "DB timeout"으로 합치면, virtual thread 환경에서 어디서 queue가 생겼는지 읽기 어려워진다.

## 운영 체크리스트

- pool `connectionTimeout`은 borrow wait 한도지 query socket timeout이 아니라는 점을 팀 공통 용어로 맞춘다.
- statement/query timeout을 정상 deadline의 단일 출처로 두고, driver socket timeout 또는 JDBC network timeout은 fail-safe로 바깥에 둔다.
- `maxLifetime`, `idleTimeout`, `keepaliveTime`을 request SLA 제어 장치처럼 쓰지 않는다.
- virtual thread 환경에서는 pending acquire, active connection, broken connection discard, physical connection recreate를 같이 본다.
- request별 `setNetworkTimeout(...)`을 쓴다면 return 후 reset 책임을 검증한다.
- 짧은 socket/network timeout을 내리기 전에 false timeout이 reconnect churn으로 바뀌지 않는지 본다.

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 맞는가 |
|---|---|---|---|
| 공격적인 driver `socketTimeout` | hung I/O를 빨리 드러낸다 | healthy-but-slow query도 connection abort로 끝날 수 있다 | network hang이 잦고 connection churn 비용을 감당할 수 있을 때 |
| request별 `setNetworkTimeout(...)` | 남은 budget에 맞춘 fail-safe가 가능하다 | pooled connection state hygiene와 driver 지원 여부를 검증해야 한다 | request deadline 편차가 크고 per-call 제어가 필요할 때 |
| 짧은 pool `connectionTimeout` | pool saturation을 빨리 surface한다 | 짧은 burst에도 실패가 빨리 난다 | admission을 명확히 하고 싶은 서비스 |
| 짧은 `maxLifetime` | 오래된 connection을 빨리 회전시킨다 | reconnect churn만 늘고 active hang은 못 푼다 | infra 요구로 stale connection rotation이 필요할 때 |

## 꼬리질문

> Q: `maxLifetime`을 짧게 두면 hung query도 빨리 회수되나요?
> 핵심: 보통 아니다. pool lifecycle은 active checked-out connection의 mid-flight query cancel을 대신하지 못한다.

> Q: driver `socketTimeout`과 `setNetworkTimeout(...)`을 둘 다 쓰면 더 안전한가요?
> 핵심: primary fail-safe 하나를 정하고 ordering을 맞추는 편이 낫다. 둘 다 켜도 semantics가 자동으로 합쳐지지 않는다.

> Q: virtual thread면 기다림이 싸니 `connectionTimeout`을 길게 둬도 되나요?
> 핵심: 기다림의 CPU 비용과 SLA 보호는 다르다. 길게 두면 pool pending이 더 조용히 쌓일 수 있다.

## 한 줄 정리

virtual thread 시대의 JDBC timeout 문제는 "어느 timeout이 먼저 터지느냐"보다 "누가 무엇을 끊을 권한이 있느냐"를 구분하는 데서 풀린다. borrow wait는 pool, 정상 deadline은 statement, I/O fail-safe는 driver/network timeout, lifecycle rotation은 pool eviction이다.
