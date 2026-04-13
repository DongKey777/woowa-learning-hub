# Query Playbook

> 한 줄 요약: `CS-study`를 검색할 때 질문을 어떻게 쪼개고 어떤 키워드로 재질의할지 정리한 실행 지침이다.

## 기본 원칙

질문을 한 번에 던지지 말고 다음 순서로 쪼갠다.

1. 영역을 정한다.
2. 개념어를 2~3개로 압축한다.
3. 장애, 성능, 설계 중 어떤 관점인지 붙인다.
4. 버전/프레임워크/DB 엔진이 있으면 명시한다.

## Query Templates

### 저장소/DB

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
- `records sealed pattern matching`
- `VarHandle Unsafe atomics`
- `direct buffer off heap native memory RSS NMT`
- `happens-before volatile final publication`
- `equals hashCode comparable contract hashmap treemap`

### Spring

- `bean lifecycle scope trap proxy`
- `transaction debugging self invocation rollback`
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

## Re-query Strategy

검색이 빗나가면 키워드를 바꾸지 말고 범위를 바꾼다.

1. `정의`가 안 나오면 `README.md`를 먼저 찾는다.
2. 질문이 넓거나 여러 분야를 동시에 건드리면 `master-notes/`를 먼저 붙인다.
3. `장애/운영`이 안 나오면 `playbook`, `failure pattern`, `debugging`을 붙인다.
4. `코드`가 안 나오면 `example`, `snippet`, `playbook`, `troubleshooting`을 붙인다.
5. `RAG`에서는 긴 문장보다 짧은 명사열이 더 잘 먹힌다.

## Good vs Bad Queries

| 나쁜 질의 | 더 나은 질의 |
|---|---|
| `Spring` | `Spring transaction debugging rollback self invocation` |
| `cache` | `distributed cache invalidation consistency` |
| `JWT` | `JWT refresh token theft replay` |
| `GC` | `G1 vs ZGC p99 latency` |
| `algorithm` | `sliding window pattern longest substring` |

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
