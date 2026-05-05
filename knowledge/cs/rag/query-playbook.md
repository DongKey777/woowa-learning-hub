# Query Playbook

> 한 줄 요약: `CS-study`를 검색할 때 질문을 어떻게 쪼개고 어떤 키워드로 재질의할지 정리한 실행 지침이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Navigation Taxonomy](./navigation-taxonomy.md)
- [RAG Design](./README.md)
- [Topic Map](./topic-map.md)
- [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
- [Security README](../contents/security/README.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md)
- [Master Notes Index](../master-notes/README.md)
- [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

retrieval-anchor-keywords: query playbook, retrieval query, search reformulation, symptom search, alias expansion, topic routing, beginner primer route, release blocker, duplicate enqueue, runaway candidate, same bucket different category, same validation axis, release-stop = stop, no_alias_query_overlap, pilot_50_untouched, concept_id_unique, 왜 같은 후보가 또 생겨요, 언제 새 candidate로 올려요, 처음 배우는데, 뭐예요, why, basics, what is

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

질문을 길게 붙잡지 말고 먼저 "도메인 template"와 "ops/release template" 중 어디인지 고른다.
도메인 지식 질문은 아래 카테고리별 query 예시를, queue health나 release blocker 질문은 뒤쪽 `RAG 운영 / index readiness` 표를 먼저 쓴다.

## Core Domain Templates

도메인 질문은 category별 template를 먼저 고르고, broad한 운영 질문은 뒤쪽 RAG 운영 섹션으로 넘긴다.

## Database Query Templates

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

## Network Query Templates

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

## OS Query Templates

- `epoll kqueue io_uring compare`
- `zombie orphan process PID 1 container`
- `false sharing cache line`
- `futex mutex semaphore spinlock`
- `run queue load average CPU saturation`
- `page cache dirty writeback fsync`
- `NUMA production debugging`
- `signal supervision graceful shutdown`
- `eBPF perf strace production tracing off-CPU`

## Java Query Templates

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

## Spring Query Templates

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

## Beginner Paraphrase Query Shapes

paraphrase cohort가 흔들릴 때는 learner 문장을 억지로 alias 한 단어로 줄이지 말고,
질문 모양을 유지한 채 corpus 쪽 기술어를 덧붙이는 편이 더 안전하다.
특히 객체 조립/생성 책임/생명주기처럼 beginner가 "용어 없이 원리만" 묻는 질문은
`expected_queries`와 `contextual_chunk_prefix`가 같은 learner phrasing을 받아야
`no_alias_query_overlap`을 건드리지 않고도 dense rerank가 붙는다.

| learner query shape | 먼저 붙일 기술어 | 재질의 예시 | safe next step |
|---|---|---|---|
| `객체를 직접 만들지 않고 외부에서 받는 게 뭐야?` | `dependency injection`, `spring bean wiring` | `spring dependency injection bean wiring new 대신 주입` | [Spring Bean과 DI 기초](../contents/spring/spring-bean-di-basics.md), [의존성 주입(DI) 기초](../contents/software-engineering/dependency-injection-basics.md) |
| `Spring이 객체끼리 연결할 때 그냥 필요해라고만 적으면 알아서 채워주는 그게 뭐야?` | `autowiring`, `bean wiring`, `container` | `spring autowiring bean wiring container 가 객체를 연결` | [Spring Bean과 DI 기초](../contents/spring/spring-bean-di-basics.md) |
| `스프링이 객체를 만들고, 의존성 채우고, 다 쓰면 정리하는 시점들이 어떻게 정해져?` | `bean lifecycle`, `postconstruct`, `predestroy` | `spring bean lifecycle create inject postconstruct predestroy` | [Spring Bean 생명주기 기초](../contents/spring/spring-bean-lifecycle-basics.md) |
| `객체를 어떻게 만들지 결정하는 책임을 따로 떼서 한 곳에 두는 패턴이 뭐야?` | `factory pattern`, `creation responsibility` | `factory pattern creation responsibility new 대신 factory` | [팩토리 패턴 기초](../contents/design-pattern/factory-basics.md) |

짧게 기억하면 아래 두 줄이다.

1. learner 문장에 이미 있는 구조를 보존한다. 예: `직접 만들지 않고 외부에서 받는다`, `필요해라고만 적는다`, `만들고-채우고-정리한다`.
2. corpus 기술어는 뒤에 붙인다. 예: `DI`, `autowiring`, `bean lifecycle`, `factory pattern`.

## RAG 운영 / index readiness

운영 질문은 broad 증상을 바로 원인으로 번역하지 말고, index-smoke냐 release-blocker냐 queue-governor냐부터 고른다.

## Index Smoke Query Shapes

- `cs-index-build stale index new doc not found`
- `retrieval readiness smoke helper docs only`
- `rag helper docs dominate no content handoff`
- `citation correct but old explanation retrieved`
- `chunk metadata route seems right but content is stale`
- `migration v3 frontmatter gate aliases expected_queries overlap`
- `linked_paths contents path contract contextual chunk prefix`
- `cs-index-build already_current but migration docs changed`
- `manifest corpus hash differs from current corpus`

index-smoke 질문은 broad하게 들어오기 쉬워서, 먼저 retrieval mismatch인지 release handoff인지부터 가른다.

| learner query shape | 먼저 붙일 alias | 재질의 예시 | safe next step |
|---|---|---|---|
| `cs-index-build 했는데 새 문서가 안 잡혀요` | `stale index`, `new doc not found after build`, `build target missing` | `cs-index-build stale index new doc not found build target missing` | [Chunking and Metadata](./chunking-and-metadata.md) |
| `helper 문서만 나와요`, `README만 잡혀요` | `helper docs only`, `no content handoff`, `readiness smoke` | `retrieval readiness smoke helper docs only no content handoff` | [RAG Design](./README.md) -> [Topic Map](./topic-map.md) |
| `manifest hash랑 corpus hash가 달라요` | `source vs local drift`, `manifest corpus hash mismatch`, `publish window not started` | `manifest corpus hash differs from current corpus source vs local drift publish window not started` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |

## Release Blocker Query Shapes

- `release tag unchanged but corpus docs changed`
- `migration v3 cherry pick or batch release`
- `path normalization batch release linked_paths contents`
- `single doc enum typo cherry pick contextual chunk prefix`
- `strict v3 blocker summary path normalization missing expected_queries`
- `pilot lock drift locked_pilot_paths mismatch release stop`

release blocker를 먼저 묻는 질문이면 검색 품질보다 계약 위반부터 자른다.
즉 `pilot 50 untouched -> aliases ⊥ expected_queries -> linked_paths=contents/... -> concept_id unique -> contextual_chunk_prefix format` 순서로 본다.

| learner query shape | 먼저 붙일 alias | 재질의 예시 | safe next step |
|---|---|---|---|
| `frontmatter는 붙였는데 release gate에서 막혀요` | `aliases expected_queries overlap`, `linked_paths contents path`, `contextual chunk prefix` | `migration v3 frontmatter gate aliases expected_queries overlap linked_paths contents path contextual chunk prefix` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |
| `문서는 바꿨는데 cs-index-build는 already_current예요` | `release tag unchanged`, `runpod rebuild pending`, `publish index release pending` | `cs-index-build already_current release tag unchanged runpod rebuild publish index release pending` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |

## Rebuild Trigger Query Shapes

index rebuild trigger 질문은 "지금 rebuild가 필요한가"와 "release tag를 지금 바꿔야 하나"를
같은 말로 섞지 않는 편이 안전하다. 먼저 source corpus, local artifact, release lock 중
어느 surface를 묻는지 고정한 뒤 query를 짧게 만든다.

| learner/ops 질문 모양 | 먼저 붙일 alias | 재질의 예시 | safe next step |
|---|---|---|---|
| `문서는 바뀌었는데 지금 rebuild를 눌러야 하나요` | `source vs local drift`, `runpod rebuild pending`, `manifest corpus hash mismatch` | `source vs local drift runpod rebuild pending manifest corpus hash mismatch` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |
| `RunPod rebuild는 끝났는데 learner는 아직 예전 결과예요` | `release lock unchanged`, `config rag_models release tag`, `publish pending` | `release lock unchanged config rag_models release tag publish pending` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |
| `artifact는 새로 만들었다는데 import가 꼬인 것 같아요` | `artifact contract drift`, `sidecar corpus hash mismatch`, `verify import pending` | `artifact contract drift sidecar corpus hash mismatch verify import pending` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |

짧게 기억하면 아래 세 줄이다.

1. `knowledge/cs/**` 변경은 source corpus 질문이다.
2. `state/cs_rag/manifest.json` / `r3_lexical_sidecar.json`은 local artifact 질문이다.
3. `config/rag_models.json.release.tag`는 publish/release lock 질문이다.

## Release Cut Query Shapes

release cut 질문은 "같은 bucket을 묶을지"와 "release-stop인지"를 먼저 가른다.

| learner query shape | 먼저 붙일 alias | 재질의 예시 | safe next step |
|---|---|---|---|
| `이건 batch release로 묶어야 하나요` | `same failure bucket`, `path-normalization`, `missing-qrel-seed` | `migration v3 batch release same failure bucket path-normalization missing-qrel-seed` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |
| `한 파일만 cherry-pick 해도 되나요` | `single doc typo`, `isolated prefix fix`, `enum-typo` | `migration v3 cherry pick isolated prefix fix enum-typo` | [Retrieval Failure Modes](./retrieval-failure-modes.md) |
| `pilot lock이나 concept_id 충돌인데 일부만 release해도 되나요` | `pilot lock stop`, `cross category concept_id duplicate`, `release stop` | `migration v3 pilot lock concept_id duplicate release stop` | [Retrieval Failure Modes](./retrieval-failure-modes.md) -> [RAG Design](./README.md) |
| `pilot source 목록이랑 locked_pilot_paths가 안 맞는데요` | `pilot lock drift`, `locked_pilot_paths mismatch`, `release stop` | `migration v3 pilot lock drift locked_pilot_paths mismatch release stop` | [Retrieval Failure Modes](./retrieval-failure-modes.md) -> [RAG Design](./README.md) |
| `strict v3 blocker가 왜 갑자기 늘었어요` | `strict v3 blocker summary`, `path-normalization`, `missing-qrel-seed` | `strict v3 blocker summary path-normalization missing-qrel-seed spring binding design pattern` | [Retrieval Failure Modes](./retrieval-failure-modes.md) -> [RAG Design](./README.md) |

## Cohort Eval / Regression Query Shapes

cohort eval 질문은 broad하게 "`점수가 떨어졌어요`"라고만 말하면 corpus repair와 fixture drift가 쉽게 섞인다.
먼저 어떤 cohort가 흔들렸는지와 baseline, qrels, calibration 중 무엇이 변했는지 같이 붙이는 편이 안전하다.

## Cohort Eval / Regression Matrix

| learner query shape | 먼저 붙일 alias | 재질의 예시 | safe next step |
|---|---|---|---|
| `cohort eval baseline이 왜 94.0 아래로 떨어졌어요` | `cohort eval regression`, `baseline 94.0 below`, `real qrels` | `cohort eval regression baseline 94.0 below real qrels drift or corpus regression` | [Retrieval Failure Modes](./retrieval-failure-modes.md), [RAG Ready Checklist](../RAG-READY.md) |
| `expected_queries를 채웠는데 real qrels 검증이 또 막혀요` | `qrels seed drift`, `alias query overlap`, `canonical path contract` | `real qrels verification qrels seed drift alias query overlap canonical path contract` | [Retrieval Failure Modes](./retrieval-failure-modes.md), [Chunking and Metadata](./chunking-and-metadata.md) |
| `refusal threshold calibration만 바뀌었는데 retrieval regression인가요` | `threshold vs retrieval split`, `downgrade vs hit miss`, `calibration drift` | `refusal threshold calibration drift threshold vs retrieval split downgrade vs hit miss` | [Retrieval Failure Modes](./retrieval-failure-modes.md), [Source Priority and Citation](./source-priority-and-citation.md) |

## Cohort Eval / Regression Matrix: Query-Shape Drift

paraphrase와 symptom cohort는 query wording drift가 retrieval handoff를 깨는 경우가 많아서 따로 본다.

| learner query shape | 먼저 붙일 alias | 재질의 예시 | safe next step |
|---|---|---|---|
| `paraphrase cohort만 흔들려요` | `query reformulation drift`, `alias weakening`, `helper docs only` | `paraphrase cohort regression query reformulation drift alias weakening helper docs only` | [RAG Design](./README.md), [Retrieval Failure Modes](./retrieval-failure-modes.md) |
| `symptom cohort만 흔들려요` | `symptom alias gap`, `retrieval anchor keywords`, `safe next step missing` | `symptom cohort regression retrieval anchor keywords safe next step missing` | [RAG Ready Checklist](../RAG-READY.md), [Retrieval Failure Modes](./retrieval-failure-modes.md) |

## Queue-Governor Query Shapes

2026-05-05 스냅샷처럼 strict v3 blocker 숫자가 커 보이는 날도,
queue-governor query는 파일명 검색보다 `path-normalization`, `missing-qrel-seed` 같은 bucket 이름을 먼저 고정하는 편이 더 잘 붙는다.
snapshot count는 우선순위 감각을 주는 참고치일 뿐이고, 새 candidate 이름을 만드는 기준은 아니다.

queue-governor triage에서는 아래 canonical bucket 이름을 그대로 유지하는 편이 좋다.

| learner/ops 질문 모양 | 바로 쓰는 재질의 | 왜 이 query가 안전한가 |
|---|---|---|
| `이거 새 candidate로 올려야 하나요` | `duplicate enqueue canonical bucket category differentiator` | 파일명 대신 bucket 분기를 먼저 강제한다 |
| `next_candidates가 계속 불어나요` | `runaway candidate next_candidates dedupe canonical bucket` | queue 속도 문제가 품질 debt인지 재등록인지 먼저 자른다 |
| `같은 bucket인데 spring이랑 design-pattern 둘 다 있어요` | `same bucket different category batch release or split` | category 검증 축이 다른지부터 확인하게 만든다 |

## Canonical Queue Buckets

| failure shape | canonical bucket | 언제 이 이름을 쓰나 |
|---|---|---|
| `linked_paths` path contract가 category 안에서 반복된다 | `path-normalization` | 같은 종류의 경로 정규화 이슈를 파일별 candidate로 복제하고 싶지 않을 때 |
| `expected_queries`가 비었거나 빠졌다 | `missing-qrel-seed` | frontmatter migration과 qrel seed repair를 분리해서 검색하고 싶을 때 |
| `aliases`와 `expected_queries`가 같은 문장을 반복한다 | `alias-query-overlap` | alias repair와 qrel seed repair를 같은 broad frontmatter 후보로 다시 합치고 싶지 않을 때 |
| `contextual_chunk_prefix`가 비었거나 질문 모양이 약하다 | `contextual-prefix-format` | prefix 보강만 필요한 문서를 path/enum typo wave와 분리하고 싶을 때 |
| chooser 비교축이 부족하다 | `chooser-compare-gap` | 새 chooser 작성보다 기존 chooser 보강이 맞는지 확인할 때 |
| playbook symptom entry가 부족하다 | `playbook-symptom-gap` | symptom_router handoff를 먼저 복구해야 하는지 볼 때 |
| isolated enum/schema typo 1건이다 | `enum-typo` | cherry-pick 후보를 large batch와 섞지 않으려 할 때 |
| Pilot lock drift, Pilot lock 자체 수정, 또는 cross-category `concept_id` 충돌이다 | `release-stop` | `pilot_50_untouched`나 `concept_id_unique` 판단이 흔들리므로 wave를 계속할지 중단할지 먼저 판단해야 할 때 |

## Queue Candidate Naming Rule

queue wave에서 새 후보를 만들 때는 `bucket + category + differentiator`를 같이 적는다.
예를 들면 `path-normalization + spring + linked_paths contents contract`처럼 적고,
이 세 칸 중 differentiator가 비어 있으면 기존 후보의 설명만 보강하고 새 item은 만들지 않는다.

`aliases`와 `expected_queries`가 겹치면 broad한 frontmatter debt로 뭉개지 말고
`alias-query-overlap`과 `no_alias_query_overlap` gate 이름을 같이 붙이는 편이 안전하다.
그래야 alias 확장 문제와 qrel seed 문제를 같은 wave에 다시 섞지 않는다.

## Merge Or Stop Shortcut

queue-governor query에서 split 여부가 헷갈리면 파일명보다 검증 축부터 고정한다.
짧게 외울 문장은 `same bucket + same validation axis = merge`, `release-stop = stop`이다.

| learner/ops 질문 모양 | 바로 붙일 판단 | 왜 이 판단이 안전한가 |
|---|---|---|
| `같은 bucket인데 category만 달라요. 새 candidate로 쪼개요?` | `same bucket + same validation axis = merge` | category 이름이 달라도 검증 계약이 같으면 duplicate enqueue만 늘기 쉽다 |
| `aliases랑 expected_queries가 또 겹쳐요. 새 frontmatter debt로 빼요?` | `alias-query-overlap + no_alias_query_overlap gate` | overlap은 broad metadata 문제가 아니라 alias/qrel 역할 충돌이라 기존 overlap wave로 묶는 편이 정확하다 |
| `Pilot lock drift나 concept_id 충돌인데 일부만 먼저 처리해요?` | `release-stop = stop` | `pilot_50_untouched`와 `concept_id_unique`는 partial split으로 가리면 baseline과 chunk identity 판단이 더 흐려진다 |

짧게 자르면 아래 순서다.

1. 같은 bucket인지 본다.
2. category별 검증 축이 정말 다른지 본다.
3. 다르지 않으면 merge하고, `release-stop`이면 split하지 않고 멈춘다.

queue-governor query는 파일명을 다시 말하는 것보다 learner-facing failure를 다시 말하는 편이 안전하다.
즉 `duplicate enqueue`를 재질의할 때도 "`이 파일을 또 올릴까`"보다 "`같은 bucket인데 category 검증 축이 다른가`"를 먼저 묻는다.
같은 bucket인데 category가 둘 이상 보일 때의 분기표가 필요하면 [Retrieval Failure Modes](./retrieval-failure-modes.md)의 cross-category split section으로 바로 내려가면 된다.
이 질문에 답을 못 하면 새 후보 추가보다 기존 wave summary 보강이 먼저다.

## Queue Candidate Rewrite Examples

queue-governor에서 가장 흔한 실수는 file/path 표현만 바꿔 같은 후보를 다시 enqueue하는 것이다.
아래처럼 "파일명 질문"을 "bucket 질문"으로 바꿔서 보는 편이 duplicate enqueue를 줄인다.

| before | after | enqueue 판단 |
|---|---|---|
| `spring-admin-session-cookie-flow-primer도 새 candidate로 올릴까요` | `path-normalization + spring + linked_paths contents contract` | 같은 bucket이면 새 item보다 기존 spring repair wave에 합친다 |
| `이 문서도 expected_queries 비었는데 따로 빼야 해요` | `missing-qrel-seed + <category> + qrel seed absent` | category 검증 축이 같으면 separate item보다 기존 qrel-seed wave에 합친다 |
| `prefix가 약한 문서가 두 개 더 보였어요` | `contextual-prefix-format + <category> + learner query handoff weak` | differentiator가 같으면 small batch로 묶고 파일별 후보는 만들지 않는다 |
| `Pilot 문서 하나만 concept_id 겹치는데 따로 처리할까요` | `release-stop + cross-category concept_id duplicate` | split 후보가 아니라 stop 신호라서 새 candidate 대신 release-stop 판단으로 올린다 |

`after` 문장을 한 줄로 못 쓰면 queue를 늘리지 말고 기존 summary를 먼저 고친다.

## Security Query Templates

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

## System Design Query Templates

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

## Architecture Query Templates

- `bounded context failure pattern`
- `monolith to MSA failure pattern`
- `SOLID failure pattern over abstraction`
- `anti corruption layer integration pattern`
- `consumer driven contract testing`
- `modular monolith boundary enforcement`
- `feature flag cleanup expiration`
- `idempotency retry consistency boundary`
- `strangler fig migration shadow traffic contract testing dual write`

## Design Pattern Query Templates

- `template method basics hook method abstract step`
- `hook method vs abstract step beginner`
- `template method vs strategy beginner`
- `abstract class vs strategy beginner`
- `처음 배우는데 템플릿 메소드`
- `처음 배우는데 hook method`
- `처음 배우는데 abstract step`
- `상속 vs 객체 주입 template method strategy`

## Data Structure / Algorithm Query Templates

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

## 알고리즘 재질의: `LIS` / `subsequence` / `subarray` / `subwindow`

- `LIS`, `longest increasing subsequence`, `증가 부분 수열`처럼 원소를 건너뛰는 표현이면 [Longest Increasing Subsequence Patterns](../contents/algorithm/longest-increasing-subsequence-patterns.md)와 [Binary Search Patterns](../contents/algorithm/binary-search-patterns.md)로 먼저 붙인다.
- `subarray`, `substring`, `window`, `subwindow`, `최근 k개`처럼 연속 구간이 핵심이면 [Sliding Window Patterns](../contents/algorithm/sliding-window-patterns.md)와 [Algorithm README](../contents/algorithm/README.md) 쪽으로 먼저 붙인다.
- `subsequence`와 `subarray`가 섞여 들어오면 재질의에서 `skip allowed`와 `contiguous only`를 같이 적어 문제 모양을 먼저 고정한다.

| 헷갈린 표현 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `LIS가 subarray인가요` | `lis`, `subsequence`, `skip allowed` | `lis longest increasing subsequence subsequence vs subarray` | [Longest Increasing Subsequence Patterns](../contents/algorithm/longest-increasing-subsequence-patterns.md) |
| `가장 긴 증가 subwindow` | `subwindow`, `sliding window`, `contiguous` | `sliding window contiguous subarray substring recent k` | [Sliding Window Patterns](../contents/algorithm/sliding-window-patterns.md) |
| `subsequence인지 sliding window인지 모르겠어요` | `subsequence vs subarray`, `contiguous only` | `subsequence vs subarray sliding window contiguous only` | [Algorithm README](../contents/algorithm/README.md) |
| `LIS lower_bound 왜 써요` | `tails`, `binary search`, `subsequence` | `lis tails binary search lower_bound subsequence` | [Binary Search Patterns](../contents/algorithm/binary-search-patterns.md) |

## 알고리즘 재질의: `meeting rooms` / `minimum meeting rooms` / `calendar booking`

- `meeting rooms II`, `minimum meeting rooms`, `railway platform`, `hotel booking possible`, `동시에 몇 개가 겹치나`처럼 자원 수나 최대 동시성을 묻는 표현이면 [Sweep Line Overlap Counting](../contents/algorithm/sweep-line-overlap-counting.md)으로 먼저 붙인다.
- `meeting rooms I`, `can attend all meetings`, `겹침이 있나`처럼 feasibility만 묻는 표현이면 [구간 / Interval Greedy 패턴](../contents/algorithm/interval-greedy-patterns.md)으로 먼저 붙인다.

## 알고리즘 재질의: interval 선택 vs online booking

- `erase overlap intervals`, `activity selection`, `minimum arrows`처럼 남길/버릴 interval 선택이 핵심이면 역시 [구간 / Interval Greedy 패턴](../contents/algorithm/interval-greedy-patterns.md) 쪽이 맞다.
- `my calendar`, `calendar booking`, `insert interval then query`처럼 매 입력마다 질의가 따라오면 [Interval Tree](../contents/data-structure/interval-tree.md)와 [Disjoint Interval Set](../contents/data-structure/disjoint-interval-set.md)을 먼저 붙인다.

## 알고리즘 재질의 예시: `meeting rooms` / `calendar booking`

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

## 시스템 설계 / 소프트웨어 엔지니어링 beginner 예시

| 실제 beginner prompt | 먼저 붙일 alias | 재질의 예시 | primer-first 연결 순서 |
|---|---|---|---|
| `시스템 디자인 처음 배우는데 큰 그림이 궁금해요` | `system design beginner route`, `system design foundations`, `큰 그림` | `system design foundations beginner 큰 그림 load balancer cache database queue` | [System Design Foundations](../contents/system-design/system-design-foundations.md) -> [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](../contents/system-design/stateless-backend-cache-database-queue-starter-pack.md) |
| `로드밸런서 캐시 DB 큐를 언제 쓰는지 기초부터 알고 싶어요` | `load balancer cache database queue`, `언제 쓰는지`, `starter pack` | `load balancer cache database queue 언제 쓰는지 starter pack beginner` | [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](../contents/system-design/stateless-backend-cache-database-queue-starter-pack.md) -> [System Design Foundations](../contents/system-design/system-design-foundations.md) |
| `캐시는 왜 쓰고 언제 위험해지는지 처음 배우는데 알고 싶어요` | `cache basics`, `cache invalidation primer`, `캐시 언제 쓰는지` | `cache basics beginner cache invalidation primer 언제 쓰는지` | [캐시 기초](../contents/system-design/caching-basics.md) -> [Cache Invalidation Patterns Primer](../contents/system-design/cache-invalidation-patterns-primer.md) |

## 소프트웨어 엔지니어링 beginner 예시

| 실제 beginner prompt | 먼저 붙일 alias | 재질의 예시 | primer-first 연결 순서 |
|---|---|---|---|
| `포트와 어댑터가 처음 배우는데 큰 그림에서 뭐예요` | `ports and adapters beginner`, `hexagonal primer`, `큰 그림` | `ports and adapters beginner hexagonal primer 큰 그림 inbound outbound` | [Ports and Adapters Beginner Primer](../contents/software-engineering/ports-and-adapters-beginner-primer.md) -> [Architecture and Layering Fundamentals](../contents/software-engineering/architecture-layering-fundamentals.md) |
| `DAO랑 query model을 언제 나누는지 기초로 보고 싶어요` | `dao vs query model`, `query repository 언제 쓰는지`, `큰 그림 read model` | `dao vs query model beginner query repository 언제 쓰는지 read model 큰 그림` | [DAO vs Query Model Entrypoint](../contents/software-engineering/dao-vs-query-model-entrypoint-primer.md) -> [Query Model Separation for Read-Heavy APIs](../contents/software-engineering/query-model-separation-read-heavy-apis.md) |

## `hook method` / `abstract step` / `template method vs strategy`

- 재질의 키워드: `template method basics hook method abstract step`, `hook method vs abstract step beginner`, `template method vs strategy beginner`, `처음 배우는데 템플릿 메소드`, `부모가 흐름을 쥔다`, `호출자가 전략을 고른다`
- 첫 진입은 [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md)로 잡고, 그다음 [템플릿 메소드 패턴 기초](../contents/design-pattern/template-method-basics.md)로 내린다. `hook`을 `선택 빈칸`, `abstract step`을 `필수 빈칸`으로 먼저 번역해 두면 프레임워크 API 이름에 덜 끌려간다.
- 비교 질문이면 [템플릿 메소드 vs 전략](../contents/design-pattern/template-method-vs-strategy.md)을 바로 붙여 `부모가 흐름을 쥔다 vs 호출자가 전략을 고른다` 한 줄 기준을 먼저 고정한다. beginner first-hit에서는 framework/smell 문서보다 primer chooser가 먼저 와야 한다.
- 프레임워크 예시는 primer 다음에만 [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](../contents/design-pattern/template-method-framework-lifecycle-examples.md)로 넘긴다. `OncePerRequestFilter`, `HttpServlet`, `xUnit` 같은 이름이 먼저 보여도 primer를 건너뛰지 않는다.
- `hook`이 많아져서 냄새를 묻는 질문일 때만 마지막 단계에서 [Template Hook Smells](../contents/design-pattern/template-hook-smells.md)로 올린다.

## `hook method` / `abstract step` / `template method vs strategy` 예시

| 실제 beginner prompt | 먼저 붙일 alias | 재질의 예시 | primer-first 연결 순서 |
|---|---|---|---|
| `hook method가 뭐예요` | `hook method beginner`, `hook은 선택 빈칸`, `template basics first` | `hook method beginner template method basics 선택 빈칸` | [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md) -> [템플릿 메소드 패턴 기초](../contents/design-pattern/template-method-basics.md) |
| `abstract step이 뭐예요` | `abstract step beginner`, `abstract step은 필수 빈칸`, `template basics first` | `abstract step beginner template method basics 필수 빈칸` | [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md) -> [템플릿 메소드 패턴 기초](../contents/design-pattern/template-method-basics.md) |
| `template method vs strategy가 뭐가 달라요` | `template method vs strategy beginner`, `부모가 흐름을 쥔다`, `호출자가 전략을 고른다` | `template method vs strategy beginner parent controls flow caller chooses strategy` | [템플릿 메소드 첫 질문 라우터](../contents/design-pattern/template-method-query-router-beginner.md) -> [템플릿 메소드 vs 전략](../contents/design-pattern/template-method-vs-strategy.md) |

## Symptom-First Bridge Routes

증상 문장으로 들어온 질문은 사용자가 이미 말한 표현을 지우지 말고, 그 표현을 유지한 채 bridge path에 맞는 명사열로 압축한다.
아래 route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)과 [Master Notes Index](../master-notes/README.md)를 같이 쓰는 기준이다.

## `transaction isolation` / `transaction-isolation` / `@Transactional` / `rollback not working` / `self invocation`

- 재질의 키워드: `transaction isolation @Transactional transactional not applied rollback not working self invocation checked exception commit rollback-only UnexpectedRollbackException`, `readOnly isolation read replica routing datasource`
- 넓은 질문이면 [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md)와 [Transaction Boundary Master Note](../master-notes/transaction-boundary-master-note.md)로 anomaly vocabulary와 application boundary를 먼저 같이 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#bridge-database-spring-transaction-cluster)의 `Transaction Isolation / @Transactional / Rollback Debugging` section (`database ↔ spring`)을 타고, 본문은 [트랜잭션 격리수준과 락](../contents/database/transaction-isolation-locking.md) → [Isolation Anomaly Cheat Sheet](../contents/database/isolation-anomaly-cheat-sheet.md) → [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md) → [@Transactional 깊이 파기](../contents/spring/transactional-deep-dive.md) → [Spring Service-Layer Transaction Boundary Patterns](../contents/spring/spring-service-layer-transaction-boundary-patterns.md) → [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md) 순으로 붙인다.
- `dirty read`, `lost update`, `write skew`, `phantom` 자체가 먼저 낯설면 DB anomaly ladder부터 타고, `왜 @Transactional이 안 먹지`, `왜 안 롤백되지`, `UnexpectedRollbackException`이 먼저 보이면 Spring surface branch부터 붙인다.

## Transaction Symptom Examples

위 broad route를 바로 learner symptom으로 내리면 아래 세 갈래가 가장 자주 나온다.

| 실제 증상 문장 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `왜 @Transactional이 안 먹지` | `transactional not applied`, `self invocation`, `proxy boundary` | `@Transactional transactional not applied self invocation proxy boundary private method` | [Spring Self-Invocation Proxy Trap Matrix](../contents/spring/spring-self-invocation-proxy-annotation-matrix.md) -> [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md) |
| `checked exception인데 커밋돼요` | `checked exception commit`, `rollbackFor`, `rollback-only` | `checked exception commit rollbackFor rollback-only UnexpectedRollbackException` | [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](../contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md) |
| `readOnly=true인데도 read replica에서 이상해요` | `transaction isolation`, `readOnly isolation confusion`, `routing datasource` | `transaction isolation readOnly read replica routing datasource` | [Spring Transaction Isolation / ReadOnly Pitfalls](../contents/spring/spring-transaction-isolation-readonly-pitfalls.md) -> [Spring Routing DataSource Read/Write Transaction Boundaries](../contents/spring/spring-routing-datasource-read-write-transaction-boundaries.md) |

## `stale read` / `stale-read` / `read-after-write` / `old data after write` / `방금 썼는데 조회가 옛값`

- 재질의 키워드: `stale read stale-read read-after-write projection lag old data after write`, `summary table stale watermark`, `dual read verification mismatch`
- 넓은 질문이면 [Replica Freshness Master Note](../master-notes/replica-freshness-master-note.md)와 [Consistency Boundary Master Note](../master-notes/consistency-boundary-master-note.md)로 freshness budget과 fallback 경계를 먼저 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Freshness / Stale Read / Read-After-Write` section (`design-pattern/read-model ↔ database/system-design`)을 타고, 본문은 [Read Model Staleness and Read-Your-Writes](../contents/design-pattern/read-model-staleness-read-your-writes.md) → [Incremental Summary Table Refresh and Watermark Discipline](../contents/database/incremental-summary-table-refresh-watermark.md) → [Dual-Read Comparison / Verification Platform 설계](../contents/system-design/dual-read-comparison-verification-platform-design.md) 순으로 붙인다.

## `499` / `broken pipe` / `client disconnect` / `client closed request`

- 재질의 키워드: `499 broken pipe client disconnect client-disconnect client closed request`, `connection reset response commit`, `cancelled request zombie work proxy timeout spring async cancellation`, `proxy timeout인지 spring bug인지`
- 넓은 질문이면 [Network Failure Handling Master Note](../master-notes/network-failure-handling-master-note.md)와 [Retry, Timeout, Idempotency Master Note](../master-notes/retry-timeout-idempotency-master-note.md)로 hop별 종료 지점과 retry 증폭 여부를 먼저 본다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Client Disconnect / 499 / Broken Pipe` section (`spring ↔ network`)을 타고, 본문은 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) → [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md) → [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) 순으로 붙인다.

## `502` / `504` / `bad gateway` / `gateway timeout`

- 재질의 키워드: `502 bad gateway local reply upstream reset`, `504 gateway timeout app logs 200`, `proxy local reply upstream attribution`, `local reply인지 app 에러인지`
- 넓은 질문이면 [Edge Request Lifecycle Master Note](../master-notes/edge-request-lifecycle-master-note.md)와 [Network Failure Handling Master Note](../master-notes/network-failure-handling-master-note.md)로 edge/app ownership을 먼저 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Edge 502 / 504 / Timeout Mismatch` section (`spring ↔ network`)을 타고, 본문은 [Proxy Local Reply vs Upstream Error Attribution](../contents/network/proxy-local-reply-vs-upstream-error-attribution.md) → [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](../contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md) → [Service Mesh Local Reply, Timeout, Reset Attribution](../contents/network/service-mesh-local-reply-timeout-reset-attribution.md) 순으로 붙인다.

## `timeout mismatch` / `async timeout mismatch` / `idle timeout mismatch`

- 재질의 키워드: `timeout mismatch gateway 504 app 200`, `async timeout mismatch deferredresult`, `idle timeout mismatch lb proxy app`, `deadline budget mismatch`
- 넓은 질문이면 [Retry, Timeout, Idempotency Master Note](../master-notes/retry-timeout-idempotency-master-note.md)와 [Edge Request Lifecycle Master Note](../master-notes/edge-request-lifecycle-master-note.md)로 hop budget과 종료 순서를 먼저 잡는다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Edge 502 / 504 / Timeout Mismatch` section (`spring ↔ network`)을 타고, 본문은 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) → [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) → [Idle Timeout Mismatch: LB / Proxy / App](../contents/network/idle-timeout-mismatch-lb-proxy-app.md) → [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md) 순으로 붙인다.

## Security Symptom Label Parity

아래 security symptom prompt는 [Topic Map](./topic-map.md)과 같은 label wording으로 시작한다.
질문을 다시 쪼갤 때도 먼저 이 label을 고정한 뒤 alias를 옆에 붙이면, security README catalog와 system-design handoff가 같은 이름으로 이어진다.

## Security Label Parity Matrix

| symptom prompt | canonical entrypoint label | parity cue |
|---|---|---|
| `JWKS outage`, `kid miss`, `auth verification outage` | [Incident / Recovery / Trust](../contents/security/README.md#incident--recovery--trust) | trust plane incident, verifier failure, recovery/failover drill |
| `auth-outage`, `login loop`, `hidden session mismatch`, `cookie drop` | `[canonical beginner entry route: login-loop]` -> [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) | browser/BFF/session symptom first, then session boundary or replay fallout |
| `cookie 있는데 다시 로그인`, `401 -> 302 bounce`, `API가 login HTML을 받음` | `[canonical beginner entry route: login-loop]` -> [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) | raw `401`, browser `302`, API HTML fallback을 먼저 갈라 beginner auth bridge로 내린다 |
 
## Security Label Parity Matrix: Access Tail and AuthZ

같은 security 카테고리 안에서도 access tail과 authz denial은 다른 route를 타므로 표를 분리해 두는 편이 learner symptom handoff가 더 안정적이다.

| symptom prompt | canonical entrypoint label | parity cue |
|---|---|---|
| `revoke lag`, `logout but still works`, `allowed after revoke` | [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) | browser-visible logout symptom과 revoke/replay tail을 같은 route로 잇는다 |
| `stale authz cache`, `stale deny`, `403 after revoke` | [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) -> [AuthZ / Tenant / Response Contracts deep dive catalog](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog) | session/auth freshness와 deny/tenant contract를 분리해서 읽는다 |

## Security Label Parity Matrix: Authority Transfer Tail

authority transfer 계열은 security 내부 symptom으로 보이지만 database/system-design bridge를 바로 타는 편이 안전해서 따로 뺀다.

| symptom prompt | canonical entrypoint label | parity cue |
|---|---|---|
| `authority transfer`, `SCIM deprovision`, `SCIM disable but still access`, `backfill is green but access tail remains`, `deprovision tail`, `decision parity`, `auth shadow divergence` | `[primer]` [Role Change and Session Freshness Basics](../contents/security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](../contents/security/claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../contents/database/README.md#database-bridge-identity-authority) -> `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle) | SCIM/deprovision/access-tail symptom은 primer/primer bridge로 tail mental model을 먼저 고정한 뒤 bridge starter에서 data parity와 runtime authority tail을 분리해 내려간다 |

## `JWKS outage` / `kid miss` / `auth verification outage`

- 먼저 붙일 security label: [Incident / Recovery / Trust](../contents/security/README.md#incident--recovery--trust)
- 재질의 키워드: `jwks outage kid miss auth verification outage`, `unable to find jwk auth failover`, `stale jwks cache key rotation rollback`
- 넓은 질문이면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)로 auth state 큰 그림을 먼저 잡고, trust 경계가 섞이면 [Trust and Identity Master Note](../master-notes/trust-and-identity-master-note.md)를 바로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Auth Incident / JWKS Outage / Auth Verification` section (`security ↔ system-design`)을 타고, 본문은 [Auth Incident Triage / Blast-Radius Recovery Matrix](../contents/security/auth-incident-triage-blast-radius-recovery-matrix.md) → [JWT / JWKS Outage Recovery / Failover Drills](../contents/security/jwt-jwks-outage-recovery-failover-drills.md) → [Service Discovery / Health Routing 설계](../contents/system-design/service-discovery-health-routing-design.md) 순으로 붙인다.
- 장애 범위가 region failover나 session plane까지 번지면 [Global Traffic Failover Control Plane 설계](../contents/system-design/global-traffic-failover-control-plane-design.md)와 [Session Store Design at Scale](../contents/system-design/session-store-design-at-scale.md)를 추가하고, browser-visible session fallout이 보이면 [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) label도 바로 붙인다.

## `auth-outage` / `login loop` / `hidden session mismatch` / `logout token은 오는데 spring 앱 세션을 못 찾는다`

- 먼저 붙일 canonical beginner label: `[canonical beginner entry route: login-loop]`
- 안전한 다음 단계와 return path: `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> `[catalog]` [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay)
## Login Loop Re-query Anchors
- 재질의 키워드: `auth outage auth-outage login loop hidden session mismatch cookie drop`, `cookie 있는데 다시 로그인 cookie exists but session missing hidden JSESSIONID`, `401 302 bounce browser 401 vs 302 login loop SavedRequest`, `API가 login HTML을 받음 fetch gets login page instead of 401 api returns 302 login`, `post-login session persistence`, `logout token은 오는데 spring 앱 세션을 못 찾는다`
- 초보자 mental model은 `SavedRequest = 로그인 후 어디로 돌아갈지 기억하는 navigation memory`, `session cookie / hidden JSESSIONID = 다음 요청에서 서버가 auth/session state를 다시 찾는 손잡이` 두 칸이다. raw `401`, browser `302 -> /login`, API HTML fallback이 한 문장에 섞이면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md)에서 이 두 칸을 먼저 분리한 뒤 [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md)에서 redirect/navigation memory, missing-cookie/session persistence, API filter chain을 갈라 본다.
## Login Loop Bridge Route
- 넓은 질문이면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)와 [Browser Auth Frontend Backend Master Note](../master-notes/browser-auth-frontend-backend-master-note.md)로 browser/BFF/session state를 먼저 잡고, federated logout이나 persisted auth 경계가 섞이면 [Trust and Identity Master Note](../master-notes/trust-and-identity-master-note.md)를 보조로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#spring--security)의 `Spring + Security` section (`spring ↔ security`)을 타고, 본문은 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) → [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) → [Spring Security `RequestCache` / `SavedRequest` Boundaries](../contents/spring/spring-security-requestcache-savedrequest-boundaries.md) → [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) → [Browser / BFF Token Boundary / Session Translation](../contents/security/browser-bff-token-boundary-session-translation.md) → [Spring OAuth2 + JWT 통합](../contents/spring/spring-oauth2-jwt-integration.md) → [OIDC Back-Channel Logout / Session Coherence](../contents/security/oidc-backchannel-logout-session-coherence.md) 순으로 붙인다.
- beginner split을 더 빨리 고르려면 `cookie-not-sent`는 `[primer]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) 쪽으로, `server-mapping-missing` / `session store recovery handoff`는 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md) 쪽으로 재질의한다.
## Login Loop Symptom Examples

| 실제 증상 문장 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `cookie 있는데 다시 로그인` | `cookie exists but session missing`, `hidden session mismatch`, `SecurityContextRepository` | `cookie 있는데 다시 로그인 cookie exists but session missing hidden session mismatch SecurityContextRepository SessionCreationPolicy` | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[safe follow-up]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) / [Secure Cookie Behind Proxy Guide](../contents/security/secure-cookie-behind-proxy-guide.md) -> `[deep dive gate]` request `Cookie` header가 실제로 실리는 것이 확인된 뒤 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |
| `cookie-not-sent` | `cookie exists but not sent`, `cookie stored but not sent`, `request cookie header empty` | `cookie-not-sent cookie exists but not sent cookie stored but not sent request cookie header empty cookie scope mismatch` | `[primer]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[safe follow-up]` [Secure Cookie Behind Proxy Guide](../contents/security/secure-cookie-behind-proxy-guide.md) |
## Login Loop Symptom Examples: API / Recovery
| `401 -> 302 bounce` | `browser 401 vs 302`, `SavedRequest`, `login loop` | `401 302 bounce browser 401 vs 302 login loop SavedRequest request cache` | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[safe follow-up]` [Cookie Scope Mismatch Guide](../contents/security/cookie-scope-mismatch-guide.md) / [Secure Cookie Behind Proxy Guide](../contents/security/secure-cookie-behind-proxy-guide.md) -> `[deep dive gate]` browser/app route 분리가 끝난 뒤 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../contents/spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `API가 login HTML을 받음` | `fetch gets login page instead of 401`, `api returns 302 login`, `browser bff boundary` | `API가 login HTML을 받음 fetch gets login page instead of 401 api returns 302 login browser bff boundary` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> [Browser / BFF Token Boundary / Session Translation](../contents/security/browser-bff-token-boundary-session-translation.md) |
| `session store recovery handoff` | `server-mapping-missing`, `cookie는 있는데 session missing`, `session store outage` | `session store recovery handoff server-mapping-missing cookie는 있는데 session missing session store outage` | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md) |
## Login Loop Recovery Reading Order

- 증상이 `cookie 있는데 다시 로그인`처럼 cookie reference는 남았지만 server session이나 token translation이 사라진 쪽으로 기울면 [Session Store Design at Scale](../contents/system-design/session-store-design-at-scale.md)와 `[recovery]` [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md)를 추가해 저장소 계층과 browser-visible fallout을 같이 본다. `API가 login HTML을 받음`처럼 browser login chain이 API route까지 덮인 표현은 위 primer -> guide ladder의 HTML fallback 구간부터 읽고, `SavedRequest`, `logout tail`, `revocation tail`처럼 state cleanup이 남는 표현이면 label wording도 `Session / Boundary / Replay` 쪽으로 바로 좁힌다.

## `revoke lag` / `logout but still works` / `allowed after revoke`

- 먼저 붙일 security label: [Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay)
- 재질의 키워드: `revoke lag revocation tail logout tail allowed after revoke`, `revoked admin still has access`, `claim version stale revoke bus lag`
- 넓은 질문이면 [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md)로 revoke 의미와 permission freshness를 먼저 잡고, browser/device logout tail이 강하면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)를 보조로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Revoke Lag / Stale AuthZ Cache / 403 After Revoke` section (`security ↔ system-design`)을 타고, 본문은 [Revocation Propagation Lag / Debugging](../contents/security/revocation-propagation-lag-debugging.md) → [Session Store / Claim-Version Cutover 설계](../contents/system-design/session-store-claim-version-cutover-design.md) → [Revocation Bus Regional Lag Recovery](../contents/system-design/revocation-bus-regional-lag-recovery-design.md) 순으로 붙인다.
- 한 route는 계속 허용되고 다른 route는 이미 거부되면 session/ticket tail과 authz cache tail이 섞인 상태일 수 있으므로, 마지막에 [Authorization Caching / Staleness](../contents/security/authorization-caching-staleness.md)를 붙여 캐시 분기를 같이 본다.

## `stale authz cache` / `stale deny` / `403 after revoke`

- 먼저 붙일 security label: [Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) -> [AuthZ / Tenant / Response Contracts deep dive catalog](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)
- 재질의 키워드: `stale authz cache stale deny 403 after revoke`, `grant but still denied tenant-specific 403`, `cached 404 after grant permission cache stale`
- 넓은 질문이면 [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md)로 scope/ownership/tenant boundary를 먼저 잡고, 응답 코드 의미가 흔들리면 [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md)로 deny contract를 바로 붙인다.
- bridge route는 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Revoke Lag / Stale AuthZ Cache / 403 After Revoke` section (`security ↔ system-design`)을 타고, 본문은 [Authorization Caching / Staleness](../contents/security/authorization-caching-staleness.md) → [AuthZ Cache Inconsistency / Runtime Debugging](../contents/security/authz-cache-inconsistency-runtime-debugging.md) → [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md) 순으로 붙인다.
- `403 after revoke`가 사실상 "권한 변경 후 deny가 남는다"는 뜻이면 negative cache나 concealment drift를 먼저 의심하고, 반대로 "revoke했는데 아직도 허용된다"면 바로 위 revoke-lag route로 갈아탄다.

## `missing-audit-trail` / `auth-signal-gap` / `decision log missing` / `observability blind spot`

- 먼저 붙일 beginner-safe starter: `[primer bridge]` [Auth Observability Primer Bridge](../contents/security/auth-observability-primer-bridge.md) -> `[catalog]` [Security README: 증상별 바로 가기](../contents/security/README.md#증상별-바로-가기)
- 재질의 키워드: `missing-audit-trail auth-signal-gap decision log missing`, `allow deny reason code가 안 보인다`, `401 403 spike인데 reason bucket이 없다`, `observability blind spot auth`
- 초보자 mental model은 `signal = 어디서 깨졌는지`, `decision = 왜 허용/거부됐는지`, `audit = 나중에 무엇을 증명할지` 세 칸이다. 용어보다 이 세 칸을 먼저 고정한 뒤 deep dive로 내려가면 auth observability와 incident evidence를 덜 섞는다.
- bridge route는 security category 안에서 먼저 `[primer bridge]` [Auth Observability Primer Bridge](../contents/security/auth-observability-primer-bridge.md)로 들어간 뒤 `[catalog]` [Security README: 운영 / Incident catalog](../contents/security/README.md#운영--incident-catalog)와 `[catalog]` [Security README: AuthZ / Tenant / Response Contracts deep dive catalog](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)로 분기하고, 그다음 `[deep dive]` [Auth Observability: SLI / SLO / Alerting](../contents/security/auth-observability-sli-slo-alerting.md) -> [AuthZ Decision Logging Design](../contents/security/authz-decision-logging-design.md) -> [Audit Logging for Auth / AuthZ Traceability](../contents/security/audit-logging-auth-authz-traceability.md) -> [Authorization Runtime Signals / Shadow Evaluation](../contents/security/authorization-runtime-signals-shadow-evaluation.md) 순으로 붙인다.

| 실제 증상 문장 | 먼저 붙일 alias | 재질의 예시 | 우선 연결 문서 |
|---|---|---|---|
| `missing-audit-trail`, `auth-signal-gap` | `decision log missing`, `observability blind spot`, `signal decision audit` | `missing-audit-trail auth-signal-gap decision log missing signal decision audit auth observability` | `[primer bridge]` [Auth Observability Primer Bridge](../contents/security/auth-observability-primer-bridge.md) -> `[safe follow-up]` [Security README: 증상별 바로 가기](../contents/security/README.md#증상별-바로-가기) -> `[deep dive]` [Auth Observability: SLI / SLO / Alerting](../contents/security/auth-observability-sli-slo-alerting.md) / [AuthZ Decision Logging Design](../contents/security/authz-decision-logging-design.md) / [Audit Logging for Auth / AuthZ Traceability](../contents/security/audit-logging-auth-authz-traceability.md) |

## `backfill은 green인데 access tail이 남는다` / `backfill is green but access tail remains` / `SCIM disable but still access` / `deprovision tail` / `auth shadow divergence` / `authority transfer`

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

## 한 줄 정리

좋은 재질의는 broad learner 문장을 곧바로 정답으로 바꾸는 게 아니라, query shape를 줄이고 다음 안전한 문서 한 장으로 보내는 일이다.
