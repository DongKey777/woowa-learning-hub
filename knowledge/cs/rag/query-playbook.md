# Query Playbook

> 한 줄 요약: `CS-study`를 검색할 때 질문을 어떻게 쪼개고 어떤 키워드로 재질의할지 정리한 실행 지침이다.
>
> 관련 문서:
> - [Navigation Taxonomy](./navigation-taxonomy.md)
> - [RAG Design](./README.md)
> - [Topic Map](./topic-map.md)
> - [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
> - [Security README](../contents/security/README.md)
> - [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
> - [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md)
> - [Master Notes Index](../master-notes/README.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: query playbook, retrieval query, role routing, keyword expansion, symptom search, alias expansion, master note escalation, cross-domain bridge, topic routing, search reformulation, security label parity, incident recovery trust, browser session troubleshooting path, session boundary replay, identity delegation lifecycle, authz tenant response contracts, stale read, stale-read, read-after-write, projection lag, old data after write, transaction isolation, transaction-isolation, @Transactional, transactional not applied, rollback not working, rollback-only, unexpectedrollbackexception, UnexpectedRollbackException, self invocation, checked exception commit, readOnly isolation confusion, database spring transaction bridge, database + spring route, 499, broken pipe, client disconnect, client-disconnect, client closed request, cancelled request, zombie work, 502, 504, bad gateway, gateway timeout, local reply, local reply vs app error, timeout mismatch, async timeout mismatch, idle timeout mismatch, deadline budget mismatch, auth outage, auth-outage, login loop, 302 login loop, hidden session mismatch, cookie drop, cookie 있는데 다시 로그인, cookie exists but session missing, login-loop canonical beginner entry route, canonical login-loop beginner entry route, canonical beginner entry route login-loop, canonical beginner entry route: login-loop, cookie-not-sent, cookie-not-sent beginner split, server-mapping-missing, session store recovery handoff, 401 302 bounce, 401 -> 302 bounce, 401 redirect loop, API가 login HTML을 받음, browser gets html login page, fetch gets login page instead of 401, api returns 302 login, session store outage, savedrequest, saved request, savedrequest primer bridge, saved request primer bridge, savedrequest before browser 401 302, sid mapping, post-login session persistence, logout token session miss, logout tail, JWKS outage, kid miss, auth verification outage, revoke lag, revocation tail, logout but still works, stale authz cache, stale deny, 403 after revoke, revoked admin still has access, missing-audit-trail, missing audit trail, audit trail missing, auth-signal-gap, auth signal gap, auth telemetry gap, decision log missing, no decision log, observability blind spot, auth observability primer bridge, signal decision audit beginner route, authority transfer, authority bridge first, scim tail bridge first, backfill green access tail, access tail remains, auth shadow divergence, deprovision tail, deprovision tail bridge first, shadow read green auth decision diverges, cleanup evidence, retirement evidence, decision log join key, audit evidence bundle, template method beginner route, template method primer route, template basics first, hook method beginner route, abstract step beginner route, hook은 선택 빈칸, abstract step은 필수 빈칸, 처음 배우는데 hook method, 처음 배우는데 abstract step, 템플릿 메소드 큰 그림, 템플릿 메소드 기초 먼저, 템플릿 메소드 vs 전략 beginner route, 부모가 흐름을 쥔다, 호출자가 전략을 고른다, 시스템 디자인 처음 배우는데, 시스템 디자인 큰 그림, 로드밸런서 캐시 DB 큐 언제 쓰는지, 캐시 언제 쓰는지, 캐시 무효화 기초, 포트와 어댑터 처음 배우는데, hexagonal architecture 큰 그림, query model 언제 쓰는지, dao vs query model 처음 배우는데, lis, longest increasing subsequence, subsequence vs subarray, subsequence vs sliding window, subwindow, contiguous only, skip allowed sequence, meeting rooms ii, minimum meeting rooms, railway platform, hotel booking possible, calendar overlap count, car pooling, sweep line, event sweep, my calendar

## 역할이 헷갈릴 때 먼저 볼 문서

- 질문이 "이 문서가 길찾기용인지 설명용인지"부터 모호하면 [Navigation Taxonomy](./navigation-taxonomy.md)로 문서 역할을 먼저 판별한다.
- 질문이 처음부터 여러 레이어를 함께 건드리면 [Master Notes Index](../master-notes/README.md)와 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)으로 범위를 넓힌 뒤 재질의한다.

## 기본 원칙

질문을 한 번에 던지지 말고 다음 순서로 쪼갠다.

1. 영역을 정한다.
2. 개념어를 2~3개로 압축한다.
3. 장애, 성능, 설계 중 어떤 관점인지 붙인다.
4. 버전/프레임워크/DB 엔진이 있으면 명시한다.

## Query Templates

### 저장소/DB

- `transaction isolation lost update write skew phantom`
- `EXPLAIN` 결과가 느릴 때
- `MySQL index not used`
- `slow query analysis`
- `online schema change chunk copy metadata lock`
- `replica lag read after write`
- `Debezium outbox binlog CDC`
- `offset vs seek pagination`
- `write skew phantom read`
- `redo log undo log checkpoint crash recovery`
- `index condition pushdown filesort using temporary`

### 네트워크

- `gRPC vs REST browser mobile backend`
- `HTTP2 multiplexing HOL blocking`
- `HTTP3 QUIC tradeoff`
- `timeout connect read write difference`
- `service mesh sidecar failure pattern`
- `CDN cache key invalidation`
- `websocket heartbeat reconnect backpressure`
- `DNS TTL stale cache failure`
- `NAT conntrack ephemeral port exhaustion TIME_WAIT`
- `Forwarded X-Forwarded-For X-Real-IP trusted proxy spoofing`

### OS

- `epoll kqueue io_uring compare`
- `zombie orphan process PID 1 container`
- `false sharing cache line`
- `futex mutex semaphore spinlock`
- `run queue load average CPU saturation`
- `page cache dirty writeback fsync`
- `NUMA production debugging`
- `signal supervision graceful shutdown`
- `eBPF perf strace production tracing off-CPU`

### Java

- `G1 vs ZGC latency tradeoff`
- `reflection cost MethodHandle codegen`
- `virtual threads pinning blocking I/O`
- `JIT deoptimization warmup`
- `ClassLoader leak playbook`
- `JFR JMC performance analysis`
- `thread dump RUNNABLE BLOCKED WAITING interpretation`
- `jcmd Thread.print VM.native_memory JFR.start`
- `async-profiler vs JFR flamegraph native stack`
- `records sealed pattern matching`
- `VarHandle Unsafe atomics`
- `jcstress memory model outcome testing`
- `direct buffer off heap native memory RSS NMT`
- `happens-before volatile final publication`
- `equals hashCode comparable contract hashmap treemap`

### Spring

- `bean lifecycle scope trap proxy`
- `transaction debugging self invocation rollback`
- `@Transactional self invocation proxy rollback-only`
- `UnexpectedRollbackException rollback-only checked exception commit`
- `readOnly isolation read replica routing datasource`
- `WebFlux vs MVC backpressure event loop`
- `OAuth2 JWT integration Spring Security`
- `Spring scheduler async boundary`
- `Spring Batch chunk retry skip`
- `Micrometer tracing observability`
- `WebClient vs RestTemplate`
- `Resilience4j retry circuit breaker bulkhead`
- `TransactionalEventListener BEFORE_COMMIT AFTER_COMMIT outbox`

### Security

- `JWT refresh token theft replay`
- `OAuth2 authorization code grant PKCE`
- `XSS CSRF Spring Security`
- `HTTPS HSTS MITM`
- `CORS SameSite preflight`
- `OIDC id token userinfo boundary`
- `secret rotation leak pattern`
- `session fixation clickjacking CSP`
- `service to service auth mTLS JWT SPIFFE SPIRE`
- `API key HMAC signature nonce timestamp replay protection`
- `authority transfer backfill green access tail`
- `auth shadow divergence old allow new deny`
- `deprovision tail session revoke lag claim version`

### System Design

- `distributed cache invalidation consistency`
- `chat system message ordering offline delivery`
- `newsfeed fan out write read`
- `rate limiter token bucket sliding window`
- `distributed lock lease fencing token`
- `search system indexing ranking shard`
- `presigned URL CDN file storage`
- `workflow orchestration saga compensation`
- `multi tenant SaaS isolation shared schema separate database`
- `payment ledger reconciliation idempotency auth capture refund`

### Architecture

- `bounded context failure pattern`
- `monolith to MSA failure pattern`
- `SOLID failure pattern over abstraction`
- `anti corruption layer integration pattern`
- `consumer driven contract testing`
- `modular monolith boundary enforcement`
- `feature flag cleanup expiration`
- `idempotency retry consistency boundary`
- `strangler fig migration shadow traffic contract testing dual write`

### Design Pattern

- `template method basics hook method abstract step`
- `hook method vs abstract step beginner`
- `template method vs strategy beginner`
- `abstract class vs strategy beginner`
- `처음 배우는데 템플릿 메소드`
- `처음 배우는데 hook method`
- `처음 배우는데 abstract step`
- `상속 vs 객체 주입 template method strategy`

### Data Structure / Algorithm

- `HashMap resize treeification load factor`
- `TreeMap vs HashMap vs LinkedHashMap`
- `sliding window pattern`
- `amortized analysis pitfalls`
- `Bloom Filter false positive`
- `skip list compare BTree`
- `segment tree lazy propagation`
- `binary search pattern lower upper bound`
- `network flow intuition max flow min cut`
- `trie prefix search autocomplete top k`

### 알고리즘 재질의: `LIS` / `subsequence` / `subarray` / `subwindow`

- `LIS`, `longest increasing subsequence`, `증가 부분 수열`처럼 원소를 건너뛰는 표현이면 [Longest Increasing Subsequence Patterns](../contents/algorithm/longest-increasing-subsequence-patterns.md)와 [Binary Search Patterns](../contents/algorithm/binary-search-patterns.md)로 먼저 붙인다.
- `subarray`, `substring`, `window`, `subwindow`, `최근 k개`처럼 연속 구간이 핵심이면 [Sliding Window Patterns](../contents/algorithm/sliding-window-patterns.md)와 [Algorithm README](../contents/algorithm/README.md) 쪽으로 먼저 붙인다.
- `subsequence`와 `subarray`가 섞여 들어오면 재질의에서 `skip allowed`와 `contiguous only`를 같이 적어 문제 모양을 먼저 고정한다.

| 헷갈린 표현 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `LIS가 subarray인가요` | `lis`, `subsequence`, `skip allowed` | `lis longest increasing subsequence subsequence vs subarray` | [Longest Increasing Subsequence Patterns](../contents/algorithm/longest-increasing-subsequence-patterns.md) |
| `가장 긴 증가 subwindow` | `subwindow`, `sliding window`, `contiguous` | `sliding window contiguous subarray substring recent k` | [Sliding Window Patterns](../contents/algorithm/sliding-window-patterns.md) |
| `subsequence인지 sliding window인지 모르겠어요` | `subsequence vs subarray`, `contiguous only` | `subsequence vs subarray sliding window contiguous only` | [Algorithm README](../contents/algorithm/README.md) |
| `LIS lower_bound 왜 써요` | `tails`, `binary search`, `subsequence` | `lis tails binary search lower_bound subsequence` | [Binary Search Patterns](../contents/algorithm/binary-search-patterns.md) |

### 알고리즘 재질의: `meeting rooms` / `minimum meeting rooms` / `calendar booking`

- `meeting rooms II`, `minimum meeting rooms`, `railway platform`, `hotel booking possible`, `동시에 몇 개가 겹치나`처럼 자원 수나 최대 동시성을 묻는 표현이면 [Sweep Line Overlap Counting](../contents/algorithm/sweep-line-overlap-counting.md)으로 먼저 붙인다.
- `meeting rooms I`, `can attend all meetings`, `겹침이 있나`처럼 feasibility만 묻는 표현이면 [구간 / Interval Greedy 패턴](../contents/algorithm/interval-greedy-patterns.md)으로 먼저 붙인다.
- `erase overlap intervals`, `activity selection`, `minimum arrows`처럼 남길/버릴 interval 선택이 핵심이면 역시 [구간 / Interval Greedy 패턴](../contents/algorithm/interval-greedy-patterns.md) 쪽이 맞다.
- `my calendar`, `calendar booking`, `insert interval then query`처럼 매 입력마다 질의가 따라오면 [Interval Tree](../contents/data-structure/interval-tree.md)와 [Disjoint Interval Set](../contents/data-structure/disjoint-interval-set.md)을 먼저 붙인다.

| 헷갈린 표현 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `meeting rooms II가 왜 greedy가 아니에요` | `meeting rooms ii`, `minimum meeting rooms`, `max concurrency` | `meeting rooms ii minimum meeting rooms sweep line max concurrency` | [Sweep Line Overlap Counting](../contents/algorithm/sweep-line-overlap-counting.md) |
| `meeting rooms I이랑 II가 뭐가 달라요` | `meeting rooms i vs ii`, `feasibility`, `room count` | `meeting rooms i vs ii interval greedy sweep line` | [Algorithm README](../contents/algorithm/README.md) |
| `hotel booking possible은 뭐로 풀어요` | `hotel booking possible`, `capacity`, `difference array` | `hotel booking possible sweep line difference array capacity` | [Sweep Line Overlap Counting](../contents/algorithm/sweep-line-overlap-counting.md) |
| `my calendar가 meeting rooms랑 같은가요` | `my calendar`, `online insert`, `interval tree` | `my calendar online insert interval tree calendar booking` | [Interval Tree](../contents/data-structure/interval-tree.md) |

## Beginner Primer Routes

처음 배우는데 `hook method`, `abstract step`, `template method vs strategy`처럼 용어가 먼저 들어오면 프레임워크 예시나 smell 문서보다 primer를 먼저 붙인다.
이 cluster는 "큰 그림 -> 기초 비교 -> 예시/심화" 순서가 beginner 회수율이 높다.

초보자 발화형 prompt는 아래 규칙으로 먼저 route한다.

1. `처음 배우는데`, `큰 그림`, `기초`, `언제 쓰는지`가 보이면 deep dive보다 primer/entrypoint를 먼저 붙인다.
2. 질문에 box/component 이름이 여러 개 섞이면 비교 문서보다 foundations/starter pack을 먼저 붙여 역할 축부터 고정한다.
3. `언제 A를 쓰는지` 형태면 implementation pattern보다 선택 기준 entrypoint를 먼저 붙이고, 필요할 때만 deep dive로 내린다.
4. beginner query는 사용자가 쓴 질문형 표현을 유지하고, 옆에 짧은 canonical alias만 덧붙인다.

### 시스템 설계 / 소프트웨어 엔지니어링 beginner 예시

| 실제 beginner prompt | 먼저 붙일 alias | 재질의 예시 | primer-first 연결 순서 |
|---|---|---|---|
| `시스템 디자인 처음 배우는데 큰 그림이 궁금해요` | `system design beginner route`, `system design foundations`, `큰 그림` | `system design foundations beginner 큰 그림 load balancer cache database queue` | [System Design Foundations](../contents/system-design/system-design-foundations.md) -> [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](../contents/system-design/stateless-backend-cache-database-queue-starter-pack.md) |
| `로드밸런서 캐시 DB 큐를 언제 쓰는지 기초부터 알고 싶어요` | `load balancer cache database queue`, `언제 쓰는지`, `starter pack` | `load balancer cache database queue 언제 쓰는지 starter pack beginner` | [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](../contents/system-design/stateless-backend-cache-database-queue-starter-pack.md) -> [System Design Foundations](../contents/system-design/system-design-foundations.md) |
| `캐시는 왜 쓰고 언제 위험해지는지 처음 배우는데 알고 싶어요` | `cache basics`, `cache invalidation primer`, `캐시 언제 쓰는지` | `cache basics beginner cache invalidation primer 언제 쓰는지` | [캐시 기초](../contents/system-design/caching-basics.md) -> [Cache Invalidation Patterns Primer](../contents/system-design/cache-invalidation-patterns-primer.md) |
| `포트와 어댑터가 처음 배우는데 큰 그림에서 뭐예요` | `ports and adapters beginner`, `hexagonal primer`, `큰 그림` | `ports and adapters beginner hexagonal primer 큰 그림 inbound outbound` | [Ports and Adapters Beginner Primer](../contents/software-engineering/ports-and-adapters-beginner-primer.md) -> [Architecture and Layering Fundamentals](../contents/software-engineering/architecture-layering-fundamentals.md) |
| `DAO랑 query model을 언제 나누는지 기초로 보고 싶어요` | `dao vs query model`, `query repository 언제 쓰는지`, `큰 그림 read model` | `dao vs query model beginner query repository 언제 쓰는지 read model 큰 그림` | [DAO vs Query Model Entrypoint](../contents/software-engineering/dao-vs-query-model-entrypoint-primer.md) -> [Query Model Separation for Read-Heavy APIs](../contents/software-engineering/query-model-separation-read-heavy-apis.md) |

### `hook method` / `abstract step` / `template method vs strategy`

- 재질의 키워드: `template method basics hook method abstract step`, `hook method vs abstract step beginner`, `template method vs strategy beginner`, `처음 배우는데 템플릿 메소드`, `부모가 흐름을 쥔다`, `호출자가 전략을 고른다`
- 첫 진입은 [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md)로 잡고, 그다음 [템플릿 메소드 패턴 기초](../contents/design-pattern/template-method-basics.md)로 내린다. `hook`을 `선택 빈칸`, `abstract step`을 `필수 빈칸`으로 먼저 번역해 두면 프레임워크 API 이름에 덜 끌려간다.
- 비교 질문이면 [템플릿 메소드 vs 전략](../contents/design-pattern/template-method-vs-strategy.md)을 바로 붙여 `부모가 흐름을 쥔다 vs 호출자가 전략을 고른다` 한 줄 기준을 먼저 고정한다. beginner first-hit에서는 framework/smell 문서보다 primer chooser가 먼저 와야 한다.
- 프레임워크 예시는 primer 다음에만 [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](../contents/design-pattern/template-method-framework-lifecycle-examples.md)로 넘긴다. `OncePerRequestFilter`, `HttpServlet`, `xUnit` 같은 이름이 먼저 보여도 primer를 건너뛰지 않는다.
- `hook`이 많아져서 냄새를 묻는 질문일 때만 마지막 단계에서 [Template Hook Smells](../contents/design-pattern/template-hook-smells.md)로 올린다.

| 실제 beginner prompt | 먼저 붙일 alias | 재질의 예시 | primer-first 연결 순서 |
|---|---|---|---|
| `hook method가 뭐예요` | `hook method beginner`, `hook은 선택 빈칸`, `template basics first` | `hook method beginner template method basics 선택 빈칸` | [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md) -> [템플릿 메소드 패턴 기초](../contents/design-pattern/template-method-basics.md) |
| `abstract step이 뭐예요` | `abstract step beginner`, `abstract step은 필수 빈칸`, `template basics first` | `abstract step beginner template method basics 필수 빈칸` | [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md) -> [템플릿 메소드 패턴 기초](../contents/design-pattern/template-method-basics.md) |
| `template method vs strategy가 뭐가 달라요` | `template method vs strategy beginner`, `부모가 흐름을 쥔다`, `호출자가 전략을 고른다` | `template method vs strategy beginner parent controls flow caller chooses strategy` | [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md) -> [템플릿 메소드 vs 전략](../contents/design-pattern/template-method-vs-strategy.md) |

## Symptom-First Bridge Routes

증상 문장으로 들어온 질문은 사용자가 이미 말한 표현을 지우지 말고, 그 표현을 유지한 채 bridge path에 맞는 명사열로 압축한다.
아래 route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)과 [Master Notes Index](../master-notes/README.md)를 같이 쓰는 기준이다.

### `transaction isolation` / `transaction-isolation` / `@Transactional` / `rollback not working` / `self invocation`

- 재질의 키워드: `transaction isolation @Transactional transactional not applied rollback not working self invocation checked exception commit rollback-only UnexpectedRollbackException`, `readOnly isolation read replica routing datasource`
- 넓은 질문이면 [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md)와 [Transaction Boundary Master Note](../master-notes/transaction-boundary-master-note.md)로 anomaly vocabulary와 application boundary를 먼저 같이 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#bridge-database-spring-transaction-cluster)의 `Transaction Isolation / @Transactional / Rollback Debugging` section (`database ↔ spring`)을 타고, 본문은 [트랜잭션 격리수준과 락](../contents/database/transaction-isolation-locking.md) → [Isolation Anomaly Cheat Sheet](../contents/database/isolation-anomaly-cheat-sheet.md) → [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md) → [@Transactional 깊이 파기](../contents/spring/transactional-deep-dive.md) → [Spring Service-Layer Transaction Boundary Patterns](../contents/spring/spring-service-layer-transaction-boundary-patterns.md) → [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md) 순으로 붙인다.
- `dirty read`, `lost update`, `write skew`, `phantom` 자체가 먼저 낯설면 DB anomaly ladder부터 타고, `왜 @Transactional이 안 먹지`, `왜 안 롤백되지`, `UnexpectedRollbackException`이 먼저 보이면 Spring surface branch부터 붙인다.

| 실제 증상 문장 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `왜 @Transactional이 안 먹지` | `transactional not applied`, `self invocation`, `proxy boundary` | `@Transactional transactional not applied self invocation proxy boundary private method` | [Spring Self-Invocation Proxy Trap Matrix](../contents/spring/spring-self-invocation-proxy-annotation-matrix.md) -> [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md) |
| `checked exception인데 커밋돼요` | `checked exception commit`, `rollbackFor`, `rollback-only` | `checked exception commit rollbackFor rollback-only UnexpectedRollbackException` | [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](../contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md) |
| `readOnly=true인데도 read replica에서 이상해요` | `transaction isolation`, `readOnly isolation confusion`, `routing datasource` | `transaction isolation readOnly read replica routing datasource` | [Spring Transaction Isolation / ReadOnly Pitfalls](../contents/spring/spring-transaction-isolation-readonly-pitfalls.md) -> [Spring Routing DataSource Read/Write Transaction Boundaries](../contents/spring/spring-routing-datasource-read-write-transaction-boundaries.md) |

### `stale read` / `stale-read` / `read-after-write` / `old data after write` / `방금 썼는데 조회가 옛값`

- 재질의 키워드: `stale read stale-read read-after-write projection lag old data after write`, `summary table stale watermark`, `dual read verification mismatch`
- 넓은 질문이면 [Replica Freshness Master Note](../master-notes/replica-freshness-master-note.md)와 [Consistency Boundary Master Note](../master-notes/consistency-boundary-master-note.md)로 freshness budget과 fallback 경계를 먼저 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Freshness / Stale Read / Read-After-Write` section (`design-pattern/read-model ↔ database/system-design`)을 타고, 본문은 [Read Model Staleness and Read-Your-Writes](../contents/design-pattern/read-model-staleness-read-your-writes.md) → [Incremental Summary Table Refresh and Watermark Discipline](../contents/database/incremental-summary-table-refresh-watermark.md) → [Dual-Read Comparison / Verification Platform 설계](../contents/system-design/dual-read-comparison-verification-platform-design.md) 순으로 붙인다.

### `499` / `broken pipe` / `client disconnect` / `client closed request`

- 재질의 키워드: `499 broken pipe client disconnect client-disconnect client closed request`, `connection reset response commit`, `cancelled request zombie work proxy timeout spring async cancellation`, `proxy timeout인지 spring bug인지`
- 넓은 질문이면 [Network Failure Handling Master Note](../master-notes/network-failure-handling-master-note.md)와 [Retry, Timeout, Idempotency Master Note](../master-notes/retry-timeout-idempotency-master-note.md)로 hop별 종료 지점과 retry 증폭 여부를 먼저 본다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Client Disconnect / 499 / Broken Pipe` section (`spring ↔ network`)을 타고, 본문은 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) → [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md) → [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) 순으로 붙인다.

### `502` / `504` / `bad gateway` / `gateway timeout`

- 재질의 키워드: `502 bad gateway local reply upstream reset`, `504 gateway timeout app logs 200`, `proxy local reply upstream attribution`, `local reply인지 app 에러인지`
- 넓은 질문이면 [Edge Request Lifecycle Master Note](../master-notes/edge-request-lifecycle-master-note.md)와 [Network Failure Handling Master Note](../master-notes/network-failure-handling-master-note.md)로 edge/app ownership을 먼저 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Edge 502 / 504 / Timeout Mismatch` section (`spring ↔ network`)을 타고, 본문은 [Proxy Local Reply vs Upstream Error Attribution](../contents/network/proxy-local-reply-vs-upstream-error-attribution.md) → [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](../contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md) → [Service Mesh Local Reply, Timeout, Reset Attribution](../contents/network/service-mesh-local-reply-timeout-reset-attribution.md) 순으로 붙인다.

### `timeout mismatch` / `async timeout mismatch` / `idle timeout mismatch`

- 재질의 키워드: `timeout mismatch gateway 504 app 200`, `async timeout mismatch deferredresult`, `idle timeout mismatch lb proxy app`, `deadline budget mismatch`
- 넓은 질문이면 [Retry, Timeout, Idempotency Master Note](../master-notes/retry-timeout-idempotency-master-note.md)와 [Edge Request Lifecycle Master Note](../master-notes/edge-request-lifecycle-master-note.md)로 hop budget과 종료 순서를 먼저 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Edge 502 / 504 / Timeout Mismatch` section (`spring ↔ network`)을 타고, 본문은 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) → [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) → [Idle Timeout Mismatch: LB / Proxy / App](../contents/network/idle-timeout-mismatch-lb-proxy-app.md) → [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md) 순으로 붙인다.

## Security Symptom Label Parity

아래 security symptom prompt는 [Topic Map](./topic-map.md)과 같은 label wording으로 시작한다.
질문을 다시 쪼갤 때도 먼저 이 label을 고정한 뒤 alias를 옆에 붙이면, security README catalog와 system-design handoff가 같은 이름으로 이어진다.

| symptom prompt | canonical entrypoint label | parity cue |
|---|---|---|
| `JWKS outage`, `kid miss`, `auth verification outage` | [Incident / Recovery / Trust](../contents/security/README.md#incident--recovery--trust) | trust plane incident, verifier failure, recovery/failover drill |
| `auth-outage`, `login loop`, `hidden session mismatch`, `cookie drop` | `[canonical beginner entry route: login-loop]` -> [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) | browser/BFF/session symptom first, then session boundary or replay fallout |
| `cookie 있는데 다시 로그인`, `401 -> 302 bounce`, `API가 login HTML을 받음` | `[canonical beginner entry route: login-loop]` -> [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) | raw `401`, browser `302`, API HTML fallback을 먼저 갈라 beginner auth bridge로 내린다 |
| `revoke lag`, `logout but still works`, `allowed after revoke` | [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) | browser-visible logout symptom과 revoke/replay tail을 같은 route로 잇는다 |
| `stale authz cache`, `stale deny`, `403 after revoke` | [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) -> [AuthZ / Tenant / Response Contracts deep dive catalog](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog) | session/auth freshness와 deny/tenant contract를 분리해서 읽는다 |
| `authority transfer`, `SCIM deprovision`, `SCIM disable but still access`, `backfill is green but access tail remains`, `deprovision tail`, `decision parity`, `auth shadow divergence` | `[primer]` [Role Change and Session Freshness Basics](../contents/security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](../contents/security/claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../contents/database/README.md#database-bridge-identity-authority) -> `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle) | SCIM/deprovision/access-tail symptom은 primer/primer bridge로 tail mental model을 먼저 고정한 뒤 bridge starter에서 data parity와 runtime authority tail을 분리해 내려간다 |

### `JWKS outage` / `kid miss` / `auth verification outage`

- 먼저 붙일 security label: [Incident / Recovery / Trust](../contents/security/README.md#incident--recovery--trust)
- 재질의 키워드: `jwks outage kid miss auth verification outage`, `unable to find jwk auth failover`, `stale jwks cache key rotation rollback`
- 넓은 질문이면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)로 auth state 큰 그림을 먼저 잡고, trust 경계가 섞이면 [Trust and Identity Master Note](../master-notes/trust-and-identity-master-note.md)를 바로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Auth Incident / JWKS Outage / Auth Verification` section (`security ↔ system-design`)을 타고, 본문은 [Auth Incident Triage / Blast-Radius Recovery Matrix](../contents/security/auth-incident-triage-blast-radius-recovery-matrix.md) → [JWT / JWKS Outage Recovery / Failover Drills](../contents/security/jwt-jwks-outage-recovery-failover-drills.md) → [Service Discovery / Health Routing 설계](../contents/system-design/service-discovery-health-routing-design.md) 순으로 붙인다.
- 장애 범위가 region failover나 session plane까지 번지면 [Global Traffic Failover Control Plane 설계](../contents/system-design/global-traffic-failover-control-plane-design.md)와 [Session Store Design at Scale](../contents/system-design/session-store-design-at-scale.md)를 추가하고, browser-visible session fallout이 보이면 [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) label도 바로 붙인다.

### `auth-outage` / `login loop` / `hidden session mismatch` / `logout token은 오는데 spring 앱 세션을 못 찾는다`

- 먼저 붙일 canonical beginner label: `[canonical beginner entry route: login-loop]`
- 안전한 다음 단계와 return path: `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> `[catalog]` [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay)
- 재질의 키워드: `auth outage auth-outage login loop hidden session mismatch cookie drop`, `cookie 있는데 다시 로그인 cookie exists but session missing hidden JSESSIONID`, `401 302 bounce browser 401 vs 302 login loop SavedRequest`, `API가 login HTML을 받음 fetch gets login page instead of 401 api returns 302 login`, `post-login session persistence`, `logout token은 오는데 spring 앱 세션을 못 찾는다`
- 초보자 mental model은 `SavedRequest = 로그인 후 어디로 돌아갈지 기억하는 navigation memory`, `session cookie / hidden JSESSIONID = 다음 요청에서 서버가 auth/session state를 다시 찾는 손잡이` 두 칸이다. raw `401`, browser `302 -> /login`, API HTML fallback이 한 문장에 섞이면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md)에서 이 두 칸을 먼저 분리한 뒤 [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md)에서 redirect/navigation memory, missing-cookie/session persistence, API filter chain을 갈라 본다.
- 넓은 질문이면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)와 [Browser Auth Frontend Backend Master Note](../master-notes/browser-auth-frontend-backend-master-note.md)로 browser/BFF/session state를 먼저 잡고, federated logout이나 persisted auth 경계가 섞이면 [Trust and Identity Master Note](../master-notes/trust-and-identity-master-note.md)를 보조로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#spring--security)의 `Spring + Security` section (`spring ↔ security`)을 타고, 본문은 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) → [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) → [Spring Security `RequestCache` / `SavedRequest` Boundaries](../contents/spring/spring-security-requestcache-savedrequest-boundaries.md) → [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) → [Browser / BFF Token Boundary / Session Translation](../contents/security/browser-bff-token-boundary-session-translation.md) → [Spring OAuth2 + JWT 통합](../contents/spring/spring-oauth2-jwt-integration.md) → [OIDC Back-Channel Logout / Session Coherence](../contents/security/oidc-backchannel-logout-session-coherence.md) 순으로 붙인다.
- beginner split을 더 빨리 고르려면 `cookie-not-sent`는 `[primer]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) 쪽으로, `server-mapping-missing` / `session store recovery handoff`는 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md) 쪽으로 재질의한다.

| 실제 증상 문장 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `cookie 있는데 다시 로그인` | `cookie exists but session missing`, `hidden session mismatch`, `SecurityContextRepository` | `cookie 있는데 다시 로그인 cookie exists but session missing hidden session mismatch SecurityContextRepository SessionCreationPolicy` | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[safe follow-up]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) / [Secure Cookie Behind Proxy Guide](../contents/security/secure-cookie-behind-proxy-guide.md) -> `[deep dive gate]` request `Cookie` header가 실제로 실리는 것이 확인된 뒤 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |
| `cookie-not-sent` | `cookie exists but not sent`, `cookie stored but not sent`, `request cookie header empty` | `cookie-not-sent cookie exists but not sent cookie stored but not sent request cookie header empty cookie scope mismatch` | `[primer]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[safe follow-up]` [Secure Cookie Behind Proxy Guide](../contents/security/secure-cookie-behind-proxy-guide.md) |
| `401 -> 302 bounce` | `browser 401 vs 302`, `SavedRequest`, `login loop` | `401 302 bounce browser 401 vs 302 login loop SavedRequest request cache` | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[safe follow-up]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) / [Secure Cookie Behind Proxy Guide](../contents/security/secure-cookie-behind-proxy-guide.md) -> `[deep dive gate]` browser/app route 분리가 끝난 뒤 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../contents/spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `API가 login HTML을 받음` | `fetch gets login page instead of 401`, `api returns 302 login`, `browser bff boundary` | `API가 login HTML을 받음 fetch gets login page instead of 401 api returns 302 login browser bff boundary` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> [Browser / BFF Token Boundary / Session Translation](../contents/security/browser-bff-token-boundary-session-translation.md) |
| `session store recovery handoff` | `server-mapping-missing`, `cookie는 있는데 session missing`, `session store outage` | `session store recovery handoff server-mapping-missing cookie는 있는데 session missing session store outage` | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md) |

- 증상이 `cookie 있는데 다시 로그인`처럼 cookie reference는 남았지만 server session이나 token translation이 사라진 쪽으로 기울면 [Session Store Design at Scale](../contents/system-design/session-store-design-at-scale.md)와 `[recovery]` [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md)를 추가해 저장소 계층과 browser-visible fallout을 같이 본다. `API가 login HTML을 받음`처럼 browser login chain이 API route까지 덮인 표현은 위 primer -> guide ladder의 HTML fallback 구간부터 읽고, `SavedRequest`, `logout tail`, `revocation tail`처럼 state cleanup이 남는 표현이면 label wording도 `Session / Boundary / Replay` 쪽으로 바로 좁힌다.

### `revoke lag` / `logout but still works` / `allowed after revoke`

- 먼저 붙일 security label: [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay)
- 재질의 키워드: `revoke lag revocation tail logout tail allowed after revoke`, `revoked admin still has access`, `claim version stale revoke bus lag`
- 넓은 질문이면 [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md)로 revoke 의미와 permission freshness를 먼저 잡고, browser/device logout tail이 강하면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)를 보조로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Revoke Lag / Stale AuthZ Cache / 403 After Revoke` section (`security ↔ system-design`)을 타고, 본문은 [Revocation Propagation Lag / Debugging](../contents/security/revocation-propagation-lag-debugging.md) → [Session Store / Claim-Version Cutover 설계](../contents/system-design/session-store-claim-version-cutover-design.md) → [Revocation Bus Regional Lag Recovery](../contents/system-design/revocation-bus-regional-lag-recovery-design.md) 순으로 붙인다.
- 한 route는 계속 허용되고 다른 route는 이미 거부되면 session/ticket tail과 authz cache tail이 섞인 상태일 수 있으므로, 마지막에 [Authorization Caching / Staleness](../contents/security/authorization-caching-staleness.md)를 붙여 캐시 분기를 같이 본다.

### `stale authz cache` / `stale deny` / `403 after revoke`

- 먼저 붙일 security label: [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) -> [AuthZ / Tenant / Response Contracts deep dive catalog](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)
- 재질의 키워드: `stale authz cache stale deny 403 after revoke`, `grant but still denied tenant-specific 403`, `cached 404 after grant permission cache stale`
- 넓은 질문이면 [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md)로 scope/ownership/tenant boundary를 먼저 잡고, 응답 코드 의미가 흔들리면 [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md)로 deny contract를 바로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Revoke Lag / Stale AuthZ Cache / 403 After Revoke` section (`security ↔ system-design`)을 타고, 본문은 [Authorization Caching / Staleness](../contents/security/authorization-caching-staleness.md) → [AuthZ Cache Inconsistency / Runtime Debugging](../contents/security/authz-cache-inconsistency-runtime-debugging.md) → [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md) 순으로 붙인다.
- `403 after revoke`가 사실상 "권한 변경 후 deny가 남는다"는 뜻이면 negative cache나 concealment drift를 먼저 의심하고, 반대로 "revoke했는데 아직도 허용된다"면 바로 위 revoke-lag route로 갈아탄다.

### `missing-audit-trail` / `auth-signal-gap` / `decision log missing` / `observability blind spot`

- 먼저 붙일 beginner-safe starter: `[primer bridge]` [Auth Observability Primer Bridge](../contents/security/auth-observability-primer-bridge.md) -> `[catalog]` [Security README: 증상별 바로 가기](../contents/security/README.md#증상별-바로-가기)
- 재질의 키워드: `missing-audit-trail auth-signal-gap decision log missing`, `allow deny reason code가 안 보인다`, `401 403 spike인데 reason bucket이 없다`, `observability blind spot auth`
- 초보자 mental model은 `signal = 어디서 깨졌는지`, `decision = 왜 허용/거부됐는지`, `audit = 나중에 무엇을 증명할지` 세 칸이다. 용어보다 이 세 칸을 먼저 고정한 뒤 deep dive로 내려가면 auth observability와 incident evidence를 덜 섞는다.
- bridge route는 security category 안에서 먼저 `[primer bridge]` [Auth Observability Primer Bridge](../contents/security/auth-observability-primer-bridge.md)로 들어간 뒤 `[catalog]` [Security README: 운영 / Incident catalog](../contents/security/README.md#운영--incident-catalog)와 `[catalog]` [Security README: AuthZ / Tenant / Response Contracts deep dive catalog](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)로 분기하고, 그다음 `[deep dive]` [Auth Observability: SLI / SLO / Alerting](../contents/security/auth-observability-sli-slo-alerting.md) -> [AuthZ Decision Logging Design](../contents/security/authz-decision-logging-design.md) -> [Audit Logging for Auth / AuthZ Traceability](../contents/security/audit-logging-auth-authz-traceability.md) -> [Authorization Runtime Signals / Shadow Evaluation](../contents/security/authorization-runtime-signals-shadow-evaluation.md) 순으로 붙인다.

| 실제 증상 문장 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `missing-audit-trail`, `auth-signal-gap` | `decision log missing`, `observability blind spot`, `signal decision audit` | `missing-audit-trail auth-signal-gap decision log missing signal decision audit auth observability` | `[primer bridge]` [Auth Observability Primer Bridge](../contents/security/auth-observability-primer-bridge.md) -> `[safe follow-up]` [Security README: 증상별 바로 가기](../contents/security/README.md#증상별-바로-가기) -> `[deep dive]` [Auth Observability: SLI / SLO / Alerting](../contents/security/auth-observability-sli-slo-alerting.md) / [AuthZ Decision Logging Design](../contents/security/authz-decision-logging-design.md) / [Audit Logging for Auth / AuthZ Traceability](../contents/security/audit-logging-auth-authz-traceability.md) |

### `backfill은 green인데 access tail이 남는다` / `backfill is green but access tail remains` / `SCIM disable but still access` / `deprovision tail` / `auth shadow divergence` / `authority transfer`

- 먼저 붙일 beginner-safe starter: `[primer]` [Role Change and Session Freshness Basics](../contents/security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](../contents/security/claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../contents/database/README.md#database-bridge-identity-authority) -> `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle)
- SCIM/deprovision/access-tail phrasing은 starter를 위 `primer -> primer bridge -> bridge` 4단계로 고정하고, `[system design]`/`[deep dive]`는 그 다음에 붙인다.
- 재질의 키워드: `authority transfer backfill green access tail`, `backfill은 green인데 access tail이 남는다`, `shadow read는 green인데 auth decision이 갈린다`, `shadow read green auth decision diverges`, `SCIM deprovision 뒤에도 권한이 남는다`, `auth shadow divergence old allow new deny`, `deprovision tail session revoke lag claim version`, `cleanup evidence retirement evidence`, `decision log join key audit evidence`
- 초보자 mental model은 한 줄이면 충분하다: `DB row parity가 green`이어도 `security runtime authority tail`은 남을 수 있으니, bridge에서 두 축을 먼저 분리하고 deep dive로 내려간다.
- 넓은 질문으로 확장돼 cutover 승격/조직 owner 경계까지 필요할 때만 `[master note]` [Migration Cutover Master Note](../master-notes/migration-cutover-master-note.md)를 붙이고, allow/deny 의미나 tenant claim drift가 핵심이면 [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md)를 보조로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Authority Transfer / SCIM Deprovision / Decision Parity` section (`database ↔ security ↔ system-design`)을 타고, 먼저 `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../contents/database/README.md#database-bridge-identity-authority) -> `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle) -> `[system design]` [System Design: Database / Security Authority Bridge](../contents/system-design/README.md#system-design-database-security-authority-bridge) -> `[system design]` [System Design: Verification / Shadowing / Authority Bridge](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge) 순으로 label path를 고정한 뒤, `[deep dive]` [Online Backfill Verification, Drift Checks, and Cutover Gates](../contents/database/online-backfill-verification-cutover-gates.md) → [SCIM Drift / Reconciliation](../contents/security/scim-drift-reconciliation.md) → [Authorization Runtime Signals / Shadow Evaluation](../contents/security/authorization-runtime-signals-shadow-evaluation.md) → [SCIM Deprovisioning / Session / AuthZ Consistency](../contents/security/scim-deprovisioning-session-authz-consistency.md) → [Database / Security Identity Bridge Cutover 설계](../contents/system-design/database-security-identity-bridge-cutover-design.md) → [Session Store / Claim-Version Cutover 설계](../contents/system-design/session-store-claim-version-cutover-design.md) → [AuthZ Decision Logging Design](../contents/security/authz-decision-logging-design.md) → [Audit Logging for Auth / AuthZ Traceability](../contents/security/audit-logging-auth-authz-traceability.md) 순으로 붙인다.
- row parity는 green인데 access tail이 남으면 database verification을 통과했다는 사실과 decision/session cleanup이 남았다는 사실을 분리해서 읽는다. lifecycle cleanup 대신 revoke/session tail이 전면에 보이면 [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay)를 보조 label로 붙여 identity cleanup과 session cleanup을 분리한다. cleanup-ready 판단이 필요하면 마지막에 decision log와 audit evidence까지 붙여 `data parity vs decision parity vs retirement evidence` 세 축으로 다시 쪼갠다.

## Re-query Strategy

검색이 빗나가면 키워드를 바꾸지 말고 범위를 바꾼다.

1. `정의`가 안 나오면 `README.md`를 먼저 찾는다.
2. 질문이 넓거나 여러 분야를 동시에 건드리면 `master-notes/`를 먼저 붙인다.
3. `장애/운영`이 안 나오면 `playbook`, `failure pattern`, `debugging`을 붙인다.
4. `코드`가 안 나오면 `example`, `snippet`, `playbook`, `troubleshooting`을 붙인다.
5. `RAG`에서는 긴 문장보다 짧은 명사열이 더 잘 먹힌다.
6. 알고리즘 질문에서 `subsequence`와 `subarray`가 섞이면 `skip allowed` 또는 `contiguous only`를 추가해 문제 형태부터 고정한다.
7. bridge 문구가 이미 구체적이면 `SavedRequest 때문에 login loop가 난다`, `backfill은 green인데 access tail이 남는다` 같은 표현을 지우지 말고 canonical alias만 옆에 덧붙인다.

## Good vs Bad Queries

| 나쁜 질의 | 더 나은 질의 |
|---|---|
| `Spring` | `Spring transaction debugging rollback self invocation` |
| `트랜잭션이 안 먹어요` | `@Transactional transactional not applied self invocation proxy boundary` |
| `cache` | `distributed cache invalidation consistency` |
| `JWT` | `JWT refresh token theft replay` |
| `GC` | `G1 vs ZGC p99 latency` |
| `algorithm` | `sliding window pattern longest substring` |
| `login loop` | `auth outage login loop hidden session mismatch saved request sid mapping` |
| `cookie 있는데 다시 로그인` | `cookie 있는데 다시 로그인 cookie exists but session missing hidden session mismatch SecurityContextRepository` |
| `API가 login HTML을 받음` | `API가 login HTML을 받음 fetch gets login page instead of 401 api returns 302 login browser 401 vs 302` |
| `LIS` | `lis longest increasing subsequence tails binary search` |
| `subwindow` | `sliding window contiguous subarray substring recent k` |
| `subsequence인지 subarray인지 모르겠어요` | `subsequence vs subarray sliding window contiguous only` |
| `backfill은 green인데 access tail이 남아요` | `authority transfer backfill green access tail decision parity auth shadow divergence` |

## Retrieval Order

질문이 들어오면 다음 순서로 검색한다.

1. 카테고리 README
2. 질문이 넓거나 교차 도메인이면 `master-notes/`
3. 기본 개념 문서
4. 실전/장애 문서
5. 트레이드오프 문서
6. 시니어 질문

## When To Prefer Master Notes

아래 질문은 `contents/*`의 개별 문서보다 `master-notes/`를 먼저 붙이는 편이 좋다.

- 원인이 여러 층에 걸친 p95/p99 지연 질문
- retry / timeout / idempotency를 한 번에 묻는 질문
- Spring transaction과 DB lock을 같이 묻는 질문
- 세션 / 쿠키 / JWT / OIDC / BFF를 한 번에 비교하는 질문
- migration / cutover / rollback / shadow traffic를 같이 묻는 질문
- JVM / RSS / native memory / cgroup / page cache를 같이 묻는 질문

## Meta Query Rule

기본 검색에서는 아래 메타 문서를 우선 회수하지 않는다.

- `rag/*`
- `RAG-READY.md`
- 루트 가이드 문서

이 문서들은 아래처럼 **RAG 자체를 묻는 질문**일 때만 다시 포함한다.

- `RAG chunking metadata`
- `retrieval strategy`
- `query playbook`
- `topic map`
- `master notes guide`

## Citation Rule

답변에는 가능한 한 아래 순서를 유지한다.

1. 개념 문서 1개
2. 실전 문서 1개
3. 관련 비교 문서 1개

이렇게 하면 같은 답변 안에서 정의, 실전, 판단 기준이 함께 유지된다.
