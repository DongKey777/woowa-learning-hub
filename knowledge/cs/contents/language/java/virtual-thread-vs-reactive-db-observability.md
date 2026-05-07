---
schema_version: 3
title: Virtual Thread vs Reactive DB Observability
concept_id: language/virtual-thread-reactive-db
canonical: true
category: language
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 92
mission_ids:
- missions/payment
review_feedback_tags:
- virtual-thread
- reactive
- database-observability
aliases:
- Virtual Thread vs Reactive DB Observability
- JDBC vs R2DBC observability
- virtual thread JDBC vs reactive DB
- Loom vs WebFlux database troubleshooting
- thread timeline vs signal timeline
- virtual thread reactive DB 관측 비교
symptoms:
- virtual thread JDBC와 reactive DB stack의 병목 신호를 모두 thread dump만으로 해석하려 해 reactive signal age와 demand를 놓쳐
- reactive timeout이나 cancel signal을 DB query가 실제 중단됐다는 증거로 바로 해석해 driver cleanup과 server-side cancel 확인을 빠뜨려
- Hikari pending acquire, R2DBC pending acquire, operator backlog, lock wait를 같은 이름의 latency로 뭉개 원인 분리를 못 해
intents:
- comparison
- troubleshooting
- deep_dive
prerequisites:
- language/virtual-threads-project-loom
- language/jdbc-observability-under-virtual-threads
- spring/webflux-vs-mvc
next_docs:
- language/virtual-thread-jdbc-cancel-semantics
- spring/reactive-blocking-bridge-boundedelastic-block-traps
- system-design/backpressure-and-load-shedding-design
linked_paths:
- contents/language/java/virtual-threads-project-loom.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/language/java/jdbc-observability-under-virtual-threads.md
- contents/language/java/virtual-thread-jdbc-cancel-semantics.md
- contents/language/java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md
- contents/spring/spring-webflux-vs-mvc.md
- contents/spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md
- contents/database/transaction-timeout-vs-lock-timeout.md
- contents/system-design/backpressure-and-load-shedding-design.md
confusable_with:
- language/jdbc-observability-under-virtual-threads
- spring/webflux-vs-mvc
- spring/reactive-blocking-bridge-boundedelastic-block-traps
forbidden_neighbors: []
expected_queries:
- virtual thread JDBC와 reactive R2DBC의 DB 장애 관측은 thread timeline과 signal timeline에서 어떻게 달라?
- Hikari pending acquire와 R2DBC pending acquire를 각각 어떤 증거로 해석해야 해?
- reactive timeout cancel signal이 나도 DB query가 계속 돌 수 있는 이유를 설명해줘
- Loom vs WebFlux에서 database bottleneck을 thread dump, publisher age, demand, pool metric으로 어떻게 비교해?
- virtual thread와 reactive 중 어떤 스택이 DB lock wait나 backpressure 원인을 더 빨리 드러내?
contextual_chunk_prefix: |
  이 문서는 virtual thread + JDBC와 reactive DB stack을 observability 관점에서 고르는 advanced chooser다.
  JDBC vs R2DBC, Loom vs WebFlux, thread timeline, signal timeline, pending acquire, reactive cancel, backpressure 질문이 본 문서에 매핑된다.
---
# Virtual Thread vs Reactive DB Observability

> 한 줄 요약: virtual thread + JDBC는 대기를 thread/pool 타임라인으로 드러내고, reactive DB stack은 대기를 signal/demand 타임라인으로 드러낸다. 둘 다 결국 pool과 DB lock, timeout을 봐야 하지만, virtual thread는 "누가 어디서 block 중인가", reactive는 "어느 publisher가 왜 신호를 못 내보내는가"라는 렌즈가 먼저다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)
> - [Virtual-Thread JDBC Cancel Semantics](./virtual-thread-jdbc-cancel-semantics.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Spring WebFlux vs MVC](../../spring/spring-webflux-vs-mvc.md)
> - [Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps](../../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
> - [Spring Request Lifecycle, Timeout, Disconnect, and Cancellation Bridges](../../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Transaction Timeout vs Lock Timeout](../../database/transaction-timeout-vs-lock-timeout.md)
> - [Backpressure and Load Shedding Design](../../system-design/backpressure-and-load-shedding-design.md)

> retrieval-anchor-keywords: virtual thread vs reactive DB observability, JDBC vs R2DBC diagnostics, virtual thread JDBC wait signal, reactive database wait signal, connection pool pending acquire, Hikari pending threads, R2DBC pending acquire, blocking thread dump vs signal timeline, reactive streams demand, backpressure vs queueing, JDBC statement timeout, reactive timeout cancel, reactive DB cancellation, pool wait vs operator backlog, loom vs webflux database troubleshooting, virtual thread thread dump, reactive scheduler queue latency

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [같은 장애를 서로 다르게 보여주는 이유](#같은-장애를-서로-다르게-보여주는-이유)
- [wait 신호 비교](#wait-신호-비교)
- [backpressure 신호 비교](#backpressure-신호-비교)
- [timeout과 cancel 신호 비교](#timeout과-cancel-신호-비교)
- [진단 렌즈 선택표](#진단-렌즈-선택표)
- [실전 시나리오](#실전-시나리오)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

둘 다 "DB가 느리다"는 같은 사용자 증상을 만들 수 있다.  
하지만 운영자가 처음 보는 증거는 꽤 다르다.

- virtual thread + JDBC는 request 코드가 blocking 흐름을 유지하므로, wait가 thread dump, JFR, pool pending, connection hold time에 잘 드러난다.
- reactive DB stack은 thread를 적게 쓰고 signal로 진행하므로, wait가 "멈춰 있는 thread"보다 in-flight publisher age, pending acquire, operator backlog, cancellation signal로 드러난다.
- 따라서 virtual thread 환경에서는 **thread timeline**, reactive 환경에서는 **signal timeline**이 기본 진단 렌즈다.

핵심 질문도 달라진다.

1. virtual thread + JDBC에서는 지금 어느 구간이 block 중인가  
   `getConnection()`인가, `execute()`인가, `commit()`인가, 아니면 transaction 안의 non-SQL 코드인가
2. reactive DB stack에서는 어느 publisher가 terminal signal을 못 내고 있는가  
   connection acquire publisher인가, result consumption인가, `flatMap` 내부 체인인가, cancel propagation인가
3. timeout이 났다면 "호출자가 포기한 것"과 "DB가 실제로 멈춘 것"을 어떻게 구분할 것인가

즉 선택의 핵심은 기술 선호가 아니라 **어떤 증거면 병목이 더 빨리 좁혀지는가**다.

## 같은 장애를 서로 다르게 보여주는 이유

| 축 | virtual thread + JDBC | reactive DB stack | 공통 해석 |
|---|---|---|---|
| wait | parked virtual thread, `Socket Read`, `getConnection()` 대기, hold time 증가로 보인다 | 적은 수의 event-loop/scheduler thread는 멀쩡해 보이는데 publisher completion이 늦다 | 실제 scarcity는 pool, DB CPU, lock wait, 느린 downstream일 수 있다 |
| backpressure | pool, executor, semaphore, request queue 같은 외부 정책으로 표현된다 | Reactive Streams demand, operator buffer, prefetch, concurrency limit로 표현된다 | admission control이 없으면 둘 다 latency debt를 숨길 수 있다 |
| timeout | caller thread에서 acquire timeout, statement timeout, request timeout 예외가 바로 보인다 | `onError`, `cancel`, `doFinally`로 보이거나 upstream이 조용히 취소된다 | 애플리케이션 timeout이 DB cancel까지 성공했다는 뜻은 아니다 |
| 1차 관측 수단 | thread dump, JFR, datasource metric, request trace | operator trace, scheduler queue, pool metric, subscriber age, cancel/error hook | DB wait/lock 관측은 둘 다 필요하다 |

표의 핵심은 "DB 병목의 본질"보다 "운영자가 처음 만나는 신호의 표면"이 다르다는 점이다.

## wait 신호 비교

### 1. virtual thread + JDBC는 wait가 thread 상태와 구간 시간으로 보인다

virtual thread 모델에서는 request마다 straight-line call stack이 유지된다.  
그래서 다음 구간이 직접 보인다.

- `dataSource.getConnection()`에서 오래 기다리는 acquire wait
- `executeQuery()`나 `commit()` 안에서 길어지는 SQL/lock wait
- transaction 안에서 외부 HTTP, serialization, retry가 길어져 늘어나는 connection hold time

이때 가장 유용한 1차 자료는 보통 이 조합이다.

- thread dump에서 `getConnection()` 근처 park/wait stack
- JFR의 `Thread Park`, `Socket Read`, `VirtualThreadPinned`
- datasource active/idle/pending acquire
- request trace의 acquireMs, holdMs, sqlMs, commitMs

즉 virtual thread 쪽 wait는 "누가 block 중인가"를 먼저 보는 편이 빠르다.

### 2. reactive DB stack은 wait가 "신호가 안 온다"로 보인다

reactive DB stack에서는 thread가 많은 정보를 주지 못할 때가 많다.

- event-loop thread 수는 원래 적다
- thread dump가 깨끗해도 connection acquire publisher가 오래 안 끝날 수 있다
- `flatMap` 안 체인이 오래된 in-flight 상태로 남아 있어도 `WAITING` thread 더미는 보이지 않을 수 있다

그래서 reactive wait는 보통 다음처럼 읽는다.

- subscription 이후 first row까지 얼마나 걸리는가
- terminal signal(`onComplete`/`onError`)까지 age가 얼마나 쌓이는가
- pool pending acquire가 올라가는가
- scheduler queue latency나 operator buffer가 커지는가
- downstream demand가 줄어 row delivery가 지연되는가

즉 reactive 쪽 wait는 "어느 publisher가 얼마나 오래 신호를 못 내고 있는가"를 먼저 봐야 한다.

### 3. thread dump의 역할이 비대칭이다

이 차이를 실전에서 자주 헷갈린다.

- virtual thread + JDBC에서는 thread dump가 1급 증거다
- reactive DB stack에서는 thread dump가 "event-loop가 block됐는지"를 확인하는 2차 증거에 가깝다

reactive에서 thread dump가 조용하다는 사실은, 단지 병목이 thread state가 아니라 signal pipeline에 숨어 있다는 뜻일 수 있다.

## backpressure 신호 비교

### 1. JDBC on virtual threads는 backpressure를 자동으로 주지 않는다

blocking JDBC 호출은 caller를 기다리게 만들 수는 있어도, 그것만으로 좋은 backpressure가 되지는 않는다.

- virtual thread가 cheap해지면 더 많은 요청이 조용히 대기열로 들어간다
- thread 수가 많아도 reject나 shed가 없다면 단지 waiters가 늘어날 뿐이다
- 진짜 backpressure는 pool acquire timeout, bounded executor, semaphore, request queue limit처럼 별도 정책으로 만들어야 한다

즉 virtual thread + JDBC에서 `WAITING` virtual thread가 많다고 해서 "backpressure가 잘 작동한다"는 뜻은 아니다.  
오히려 **admission control 없이 latency debt가 쌓이고 있다**는 신호일 수 있다.

### 2. reactive DB stack은 demand가 1급 신호다

reactive에서는 backpressure가 프로토콜 일부다.

- downstream이 `request(n)`을 줄이면 upstream emission도 줄어든다
- `flatMap(concurrency)`, prefetch, operator buffer 크기가 실제 처리 창구를 만든다
- `onBackpressureBuffer`, dropped signal, discard hook이 부하 조절 실패를 드러낸다

이 점 때문에 reactive observability는 thread보다 다음을 더 중요하게 본다.

- operator별 in-flight 개수
- prefetch/buffer 사용량
- downstream demand 부족 여부
- scheduler queue 적체
- blocking bridge 때문에 `boundedElastic` 같은 격리 구간이 포화되는지

다만 중요한 제한도 있다.  
reactive backpressure가 있다고 해서 DB lock wait나 느린 query 자체가 사라지지는 않는다.

- query 제출 이후 DB 안에서 이미 lock wait가 걸리면 reactive도 결국 completion 지연으로 보인다
- driver가 row fetch를 chunk로 나눠도, 이미 실행 중인 query의 cost 자체를 없애 주는 것은 아니다
- pool과 DB가 병목이면 reactive에서도 pending acquire와 timeout이 그대로 보인다

즉 reactive의 backpressure는 **앱 내부 buffering과 소비 속도 문제를 더 명시적으로 드러내는 것**이지, DB scarcity를 마법처럼 없애는 기능은 아니다.

## timeout과 cancel 신호 비교

### 1. virtual thread + JDBC는 timeout 계층이 예외로 드러난다

JDBC 계층에서는 timeout이 보통 이렇게 나뉜다.

- connection acquire timeout
- statement/query timeout
- transaction timeout
- request/gateway timeout
- network/socket timeout

이들은 대개 caller thread의 예외나 로그로 보인다.

- pool timeout 예외
- `SQLTimeoutException`
- request timeout 이후 interrupt 또는 cleanup path
- cancel 실패 뒤 connection abort

그래서 virtual thread 진단은 "어느 thread가 어느 timeout에 걸렸는가"를 따라가기 쉽다.  
대신 request timeout이 query cancel을 자동으로 뜻하지 않는다는 점은 따로 확인해야 한다.

### 2. reactive timeout은 stream termination과 cancel propagation으로 읽는다

reactive에서는 timeout이 보통 이런 형태로 드러난다.

- `timeout()` operator가 `onError`를 낸다
- subscriber가 취소되어 upstream에 cancel signal이 간다
- `doFinally`, `doOnCancel`, `doOnError`에서 종료 이유가 기록된다

이때 중요한 구분은 두 가지다.

- reactive chain이 종료된 것과 DB statement가 실제로 취소된 것은 다를 수 있다
- timeout이 pool acquire 전에 났는지, query 제출 후에 났는지에 따라 해석이 달라진다

예를 들면 다음이 가능하다.

- acquire 단계에서 timeout -> DB에는 query가 아예 안 갔을 수 있다
- query 제출 뒤 `timeout()` -> subscriber는 끝났지만 DB는 cancel/close가 성공하기 전까지 계속 돌 수 있다

즉 reactive timeout에서는 "terminal signal이 언제 났는가"와 "driver/DB cancel이 실제로 먹었는가"를 분리해서 봐야 한다.

### 3. cancel 증거의 위치도 다르다

virtual thread + JDBC에서는 cancel 증거가 보통 여기 있다.

- `Statement.cancel()`
- statement timeout 예외
- connection close/abort
- DB lock wait 해제 또는 server-side cancel 흔적

reactive에서는 여기에 더해 다음이 추가된다.

- `cancel` signal 발생 시점
- upstream publisher cleanup 훅 실행 여부
- connection pool 반환/폐기 타이밍
- driver가 cancel을 server-side protocol로 번역했는지

즉 virtual thread는 thread/statement ownership을, reactive는 **signal ownership과 resource cleanup ownership**을 함께 봐야 한다.

## 진단 렌즈 선택표

| 증상 | 먼저 고를 렌즈 | 이유 | 바로 볼 것 |
|---|---|---|---|
| thread dump에 `getConnection()` 근처 virtual thread가 대량으로 걸린다 | virtual thread + JDBC | wait가 caller thread에 직접 실려 있다 | pending acquire, active connection, hold time, DB lock wait |
| thread 수는 안정적인데 p99와 in-flight request age만 오른다 | reactive DB | 병목이 signal pipeline이나 pool acquire publisher에 숨어 있을 가능성이 크다 | pending acquire, subscriber age, `flatMap` concurrency, scheduler queue |
| `SQLTimeoutException`이나 pool acquire timeout이 서비스 로그에 바로 보인다 | virtual thread + JDBC | timeout 계층이 caller 예외로 표면화됐다 | statement timeout, request timeout, cancel 성공 여부 |
| `TimeoutException`, `cancel`, `doFinally`는 보이는데 DB 세션은 계속 산다 | reactive DB 우선, DB 관측 병행 | stream termination과 DB cancel이 분리됐을 수 있다 | cancel propagation, driver cleanup, DB-side cancel evidence |
| dropped signal, buffer growth, `onBackpressureBuffer` 경고가 오른다 | reactive DB | backpressure 계약이 직접 드러났다 | demand, prefetch, buffer 정책, blocking bridge |
| rejected execution, semaphore saturation, pool pending만 오른다 | virtual thread + JDBC | backpressure가 protocol이 아니라 admission policy에서 나타난다 | queue depth, reject policy, pool budget, transaction hold |

정리하면 이렇다.

- **thread가 증거를 많이 준다** -> virtual thread + JDBC 렌즈가 빠르다
- **signal age와 demand가 증거를 많이 준다** -> reactive 렌즈가 빠르다
- **DB lock wait가 의심된다** -> 두 경우 모두 DB 관측을 바로 붙인다

## 실전 시나리오

### 시나리오 1: virtual thread 전환 뒤 Hikari pending이 올랐다

thread dump에는 수많은 virtual thread가 `getConnection()` 근처에서 기다린다.  
이건 reactive backpressure가 아니라, 보통 다음 중 하나다.

- connection hold time 증가
- transaction 안 non-SQL work 증가
- DB lock wait로 active connection이 늦게 돌아옴

즉 이 경우 첫 렌즈는 `thread dump + pool + hold time`이다.

### 시나리오 2: WebFlux + reactive DB 서비스는 thread가 조용한데 p99가 치솟는다

event-loop thread는 몇 개 안 되고 CPU도 낮다.  
하지만 pool pending acquire와 오래된 in-flight publisher가 늘고, `flatMap` 내부 체인이 계속 남아 있다.

이 경우 thread dump는 큰 도움을 주지 못한다.  
첫 렌즈는 `subscriber age + pool pending + operator concurrency`다.

### 시나리오 3: timeout은 났는데 DB query가 계속 돈다

두 모델 모두 이 함정이 있다.

- virtual thread + JDBC에서는 request timeout이 statement cancel까지 자동으로 연결되지 않을 수 있다
- reactive에서는 stream timeout/cancel이 subscriber만 끝내고 DB query는 남길 수 있다

즉 timeout 자체보다 **cancel ownership과 DB-side evidence**를 확인해야 한다.

## 트레이드오프

| 렌즈 | 장점 | 놓치기 쉬운 것 |
|---|---|---|
| thread-centric 진단 | straight-line stack과 wait 구간이 직관적이다 | reactive operator backlog, demand 부족, hidden buffering |
| signal-centric 진단 | backpressure, cancellation, queueing을 더 세밀하게 읽을 수 있다 | 단순한 connection hold 문제를 과하게 추상화할 수 있다 |
| DB-centric 진단 | lock wait, blocker/waiter, slow query를 직접 잡는다 | 앱 레벨 admission control, scheduler backlog, cleanup 누락 |

좋은 운영은 세 렌즈 중 하나만 고집하지 않는다.  
다만 **어느 렌즈를 먼저 꺼내야 시간을 덜 버리는지**는 실행 모델마다 달라진다.

## 꼬리질문

> Q: virtual thread가 많으면 그 자체로 backpressure가 걸린 건가요?
> 핵심: 아니다. cheap thread 위에 waiters가 쌓인 것일 수 있고, reject/shed 정책이 없으면 오히려 latency debt가 커질 수 있다.

> Q: reactive에서 thread dump가 깨끗하면 DB 경로도 건강한가요?
> 핵심: 아니다. wait가 thread state가 아니라 publisher age, pending acquire, operator backlog로 드러날 수 있다.

> Q: `timeout()`이 났으면 query도 취소된 건가요?
> 핵심: 아니다. stream termination과 DB cancel은 분리될 수 있으니 driver/DB 측 증거를 따로 확인해야 한다.

> Q: reactive는 backpressure가 있으니 pool wait 문제도 덜한가요?
> 핵심: 아니다. pool과 DB 처리량 한계는 그대로고, reactive는 그 신호를 demand/publisher 관점으로 더 일찍 드러낼 뿐이다.

## 한 줄 정리

virtual thread + JDBC는 wait를 thread/pool 타임라인으로 읽고, reactive DB stack은 wait를 signal/demand 타임라인으로 읽는다. 따라서 같은 DB 병목이라도 virtual thread에서는 `누가 block 중인가`, reactive에서는 `어느 publisher가 왜 completion을 못 내는가`를 먼저 봐야 진단이 빨라진다.
