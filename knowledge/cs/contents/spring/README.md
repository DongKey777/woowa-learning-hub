# Spring Framework (스프링 프레임워크)

**난이도: 🔴 Advanced**

> 작성자 : [이동훈](https://github.com/idonghun)

<details>
<summary>Table of Contents</summary>

- [Spring Bean과 DI 기초](#spring-bean과-di-기초)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](#spring-primary-vs-qualifier-vs-컬렉션-주입-결정-가이드)
- [Spring Bean 이름 규칙과 rename 함정 입문](#spring-bean-이름-규칙과-rename-함정-입문)
- [커스텀 `@Qualifier` 입문](#커스텀-qualifier-입문)
- [Spring 런타임 전략 선택과 `@Qualifier` 경계](#spring-런타임-전략-선택과-qualifier-경계)
- [Spring Configuration vs Auto-configuration 입문](#spring-configuration-vs-auto-configuration-입문)
- [Spring Component Scan 실패 패턴](#spring-component-scan-실패-패턴)
- [Spring `scanBasePackages` vs `@Import` 선택 기준](#spring-scanbasepackages-vs-import-선택-기준)
- [Spring JPA Scan Boundary 함정](#spring-jpa-scan-boundary-함정)
- [DI 예외 빠른 판별](#di-예외-빠른-판별)
- [IoC 컨테이너와 DI](#ioc-컨테이너와-di)
- [Bean 생명주기와 스코프 함정](#bean-생명주기와-스코프-함정)
- [AOP와 프록시 메커니즘](#aop와-프록시-메커니즘)
- [Spring Self-Invocation / Proxy Annotation Matrix](#spring-self-invocation--proxy-annotation-matrix)
- [Spring Early Bean Reference와 Circular Proxy Traps](#spring-early-bean-reference와-circular-proxy-traps)
- [Spring FactoryBean / SmartInitializingSingleton](#spring-factorybean--smartinitializingsingleton)
- [@Transactional 깊이 파기](#transactional-깊이-파기)
- [Spring TransactionTemplate과 Programmatic Transaction](#spring-transactiontemplate과-programmatic-transaction)
- [Spring UnexpectedRollback / Rollback-Only](#spring-unexpectedrollback--rollback-only)
- [DB Lock Wait / Deadlock vs Spring Proxy / Rollback](#db-lock-wait--deadlock-vs-spring-proxy--rollback)
- [Spring TransactionSynchronization Ordering / Suspend / Resume](#spring-transactionsynchronization-ordering--suspend--resume)
- [Spring Propagation Edge Cases: MANDATORY / SUPPORTS / NOT_SUPPORTED](#spring-propagation-edge-cases-mandatory--supports--not_supported)
- [Spring Service-Layer Transaction Boundary Patterns](#spring-service-layer-transaction-boundary-patterns)
- [Spring MVC 요청 생명주기](#spring-mvc-요청-생명주기)
- [Spring HandlerMethodReturnValueHandler Chain](#spring-handlermethodreturnvaluehandler-chain)
- [Spring ResponseBodyAdvice on Streaming Types](#spring-responsebodyadvice-on-streaming-types)
- [Spring ProblemDetail Before-After Commit Matrix](#spring-problemdetail-before-after-commit-matrix)
- [Spring HttpMessageNotWritableException Failure Taxonomy](#spring-httpmessagenotwritableexception-failure-taxonomy)
- [Spring ProblemDetail vs /error Handoff Matrix](#spring-problemdetail-vs-error-handoff-matrix)
- [Spring MVC vs WebFlux](#spring-mvc-vs-webflux)
- [Spring MVC Async Dispatch](#spring-mvc-async-dispatch)
- [Spring OncePerRequestFilter Async / Error Dispatch](#spring-onceperrequestfilter-async--error-dispatch)
- [Spring BasicErrorController / ErrorAttributes](#spring-basicerrorcontroller--errorattributes)
- [Spring Reactive-Blocking Bridge](#spring-reactive-blocking-bridge)
- [Spring Request Lifecycle Timeout / Disconnect Bridge](#spring-bridge-request-lifecycle-timeout-disconnect)
- [Spring Async Timeout vs Disconnect Decision Tree](#spring-async-timeout-vs-disconnect-decision-tree)
- [Spring Servlet Container Disconnect Exception Mapping](#spring-servlet-container-disconnect-exception-mapping)
- [Spring Partial-Response Access Log Interpretation](#spring-partial-response-access-log-interpretation)
- [Spring HTTP/2 Reset Attribution](#spring-http2-reset-attribution)
- [Spring StreamingResponseBody / SSE Commit Lifecycle](#spring-streamingresponsebody--sse-commit-lifecycle)
- [Spring Async MVC Streaming Observability](#spring-async-mvc-streaming-observability)
- [Spring SSE Disconnect Observability Patterns](#spring-sse-disconnect-observability-patterns)
- [Spring ResponseBodyEmitter Media-Type Boundaries](#spring-responsebodyemitter-media-type-boundaries)
- [Spring MVC Flux JSON vs NDJSON and SSE Adaptation](#spring-mvc-flux-json-vs-ndjson-and-sse-adaptation)
- [Spring Streaming Client Parsing Matrix](#spring-streaming-client-parsing-matrix)
- [Spring SSE Proxy Idle-Timeout Matrix](#spring-sse-proxy-idle-timeout-matrix)
- [Spring MVC SseEmitter vs WebFlux SSE Timeout Behavior](#spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior)
- [Spring SseEmitter Timeout Callback Race Matrix](#spring-sseemitter-timeout-callback-race-matrix)
- [Spring SSE Buffering / Compression Checklist](#spring-sse-buffering--compression-checklist)
- [Spring SSE Replay Buffer / Last-Event-ID Recovery](#spring-sse-replay-buffer--last-event-id-recovery)
- [Spring Boot 자동 구성](#spring-boot-자동-구성)
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ](#spring-starter-넣었는데-bean이-안-뜰-때-faq)
- [Spring Startup Hooks와 Readiness Warmup](#spring-startup-hooks와-readiness-warmup)
- [Spring Startup / Bean Graph Debugging](#spring-startup--bean-graph-debugging)
- [Spring Security 아키텍처](#spring-security-아키텍처)
- [Spring Security 예외 번역과 세션 경계](#spring-bridge-security-session-boundary)
- [Spring Logout Handler / Success Flow](#spring-logout-handler--success-flow)
- [Spring RequestCache / SavedRequest](#spring-bridge-requestcache-savedrequest)
- [Spring OAuth2 + JWT 통합](#spring-oauth2--jwt-통합)
- [Spring Test Slices와 Context Caching](#spring-test-slices와-context-caching)
- [Spring Test Slice Scan Boundary 오해](#spring-test-slice-scan-boundary-오해)
- [Spring Test Slice Boundary Leaks](#spring-test-slice-boundary-leaks)
- [Spring JsonTest / RestClientTest Slice Boundaries](#spring-jsontest--restclienttest-slice-boundaries)
- [Spring Cache 추상화 함정](#spring-cache-추상화-함정)
- [Spring Transaction Debugging Playbook](#spring-transaction-debugging-playbook)
- [Spring Persistence Context Flush / Clear / Detach](#spring-persistence-context-flush--clear--detach)
- [Spring Routing DataSource와 JDBC Exception Translation](#spring-routing-datasource와-jdbc-exception-translation)
- [Spring Scheduler와 Async 경계](#spring-scheduler와-async-경계)
- [Spring TaskExecutor / TaskScheduler Overload Semantics](#spring-taskexecutor--taskscheduler-overload-semantics)
- [Spring Distributed Scheduling / Cron Drift / Leader Election](#spring-distributed-scheduling--cron-drift--leader-election)
- [Spring RequestContextHolder / ThreadLocal Leakage](#spring-requestcontextholder--threadlocal-leakage)
- [Spring `@Transactional`과 `@Async` 조합 함정](#spring-transactional과-async-조합-함정)
- [Spring Batch chunk, retry, skip](#spring-batch-chunk-retry-skip)
- [Spring Observability, Micrometer, Tracing](#spring-observability-micrometer-tracing)
- [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](#spring-resilience4j-retry-circuitbreaker-bulkhead)
- [Spring WebClient vs RestTemplate](#spring-webclient-vs-resttemplate)
- [Spring EventListener, TransactionalEventListener, Outbox](#spring-eventlistener-transactionaleventlistener-outbox)

</details>

retrieval-anchor-keywords: spring readme, spring navigator, spring primer, spring deep dive, spring playbook, spring troubleshooting, spring framework, spring boot, configuration vs autoconfiguration, @Configuration @Bean difference, proxyBeanMethods beginner, full configuration vs lite configuration, method parameter injection bean, inter-bean reference, lite mode @Bean, auto-configuration mental model, spring boot config primer, condition evaluation report beginner, condition report first debug checklist, --debug first checklist, debug=true, actuator conditions endpoint, conditions endpoint beginner, @ConditionalOnMissingBean miss, boot default bean skipped, existing bean found, @Primary vs @Qualifier, @Primary vs @Qualifier vs collection injection, collection injection, list injection, map injection, bean candidate selection, single default bean, explicit bean pick, custom qualifier, custom @Qualifier, qualifier annotation, bean name string qualifier, bean naming rule, default bean name, component bean name, @Component name, @Bean name, bean alias, bean rename pitfall, method rename bean name, class rename bean name, parameter name bean match, semantic qualifier, qualifier meta annotation, spring qualifier beginner, runtime strategy selection, router pattern, Map<String, Bean> router, runtime dispatch vs qualifier, payment router, notification router, per request strategy selection, NoSuchBeanDefinitionException, NoUniqueBeanDefinitionException, DI exception quick triage, missing bean vs ambiguous bean, bean not found vs duplicate bean, scanBasePackages vs @Import, scanBasePackageClasses vs @Import, spring shared module registration, Boot starter decision, EntityScan, EnableJpaRepositories, JPA scan boundary, component scan vs entity scan, component scan vs repository scan, Not a managed type, repository bean not found, scanBasePackages no effect entity scan, ObjectProvider, scoped proxy, provider vs proxy, prototype lookup timing, request lookup timing, prototype scope, request scope, transactional, database spring transaction bridge, transaction isolation to @Transactional, why transactional not applied, rollback not working route, REQUIRES_NEW beginner route, rollback-only beginner route, readOnly beginner route, readOnly routing confusion, inner readOnly writer pool, partial commit beginner, self invocation route, mvc lifecycle, async dispatch, deferredresult, security filter chain, exception translation, session creation policy, LogoutFilter, LogoutHandler, LogoutSuccessHandler, logout success redirect, cookie clearing, RP-initiated logout, OIDC logout, oauth2Login, login success handler, SavedRequestAwareAuthenticationSuccessHandler, sid mapping, back-channel logout, post-login session persistence, BFF token cache cleanup, readiness warmup, bean graph debugging, save persist merge, transactional event listener fallbackExecution, datajpatest flush clear, transactiontemplate, unexpectedrollbackexception, rollback-only, transaction synchronization ordering, suspend resume, propagation mandatory supports not_supported, HandlerMethodReturnValueHandler, ResponseEntity chain, response commit timing, RequestBodyAdvice, ResponseBodyAdvice, beforeBodyWrite, ProblemDetail, ErrorResponse, ResponseEntityExceptionHandler, DefaultHandlerExceptionResolver, response committed, commit boundary matrix, /error handoff, servlet error dispatch, ErrorPageFilter, ErrorPageCustomizer, unresolved MVC exception, HttpMessageNotWritableException, no converter for return value, preset Content-Type, converter selection failure, Could not write JSON, serialization failure, first flush, partial write, partial response, truncated JSON, partial response access log, truncated download, bytes sent interpretation, range response truncation, RequestCache, SavedRequest, savedrequest beginner route, login redirect, 401 302 bounce starter, hidden session mismatch, hidden JSESSIONID route, cookie session jwt bridge, beginner auth bridge, session basics to spring security, distributed scheduling, cron drift, leader election, misfire policy, checkpoint, catch-up semantics, request timeout, AsyncRequestTimeoutException, client disconnect, broken pipe, connection reset, proxy timeout, client abort, 499, cancellation bridge, onceperrequestfilter, basicerrorcontroller, errorattributes, whitelabel, jsontest, restclienttest, factorybean, smartinitializingsingleton, routing datasource, jdbctemplate, persistence context, flush clear detach, transactional async, taskexecutor, taskscheduler, requestcontextholder, threadlocal leak, self invocation matrix, boundedElastic, block, reactive blocking bridge, test slice leak, early bean reference, circular dependency, read replica, spring network bridge, spring + network route, spring + security route, webclient timeout, request timing decomposition, grpc deadline, connection pool wait, StreamingResponseBody, ResponseBodyEmitter, SseEmitter, application/x-ndjson, application/jsonl, text/plain streaming, JSON array streaming, document framing, text/event-stream, fetch stream parser, browser fetch ndjson, TextDecoderStream, response.body getReader, response.json not streaming, EventSource parser contract, CLI line reader NDJSON, SSE line reader mismatch, text/event-stream, SSE heartbeat, heartbeat cadence, heartbeat gap, first byte commit, first-byte latency, flush cadence, last flush, last successful flush, completion cause, async mvc streaming observability, stream completion cause, AsyncRequestNotUsableException, ClientAbortException, EofException, ClosedChannelException, DisconnectedClientHelper, ALB idle timeout, nginx proxy_read_timeout, CDN streaming timeout, EventSource retry, Last-Event-ID, SSE replay buffer, SSE replay window, recovery fence, high water mark, event ordering fence, replay then subscribe gap, multi-instance SSE recovery, sticky session failover, proxy buffering, SSE buffering checklist, SSE compression checklist, X-Accel-Buffering, Cache-Control no-transform, Content-Encoding gzip, brotli off, response transform, event stream coalescing, reconnect storm, reconnect noise, reconnect pressure, disconnect ratio, SSE disconnect observability, SSE alerting, HTTP/2 reset attribution, RST_STREAM, GOAWAY, Tomcat CloseNowException, Jetty EofException reset, Undertow ClosedChannelException, stream reset, connection drain, auth session troubleshooting, browser bff session, session revocation, session store, logout propagation, login loop, WebFlux SSE, Flux<ServerSentEvent>, reactive SSE cancel, doOnCancel, SignalType.CANCEL, SseEmitter timeout vs heartbeat, Flux timeout SSE, Flux application/json, Flux NDJSON, Flux SSE, ReactiveTypeHandler, ResponseBodyEmitterReturnValueHandler, DeferredResult<List<?>>, collect Flux to List, SseEmitter onTimeout, SseEmitter onError, SseEmitter onCompletion, completeWithError, emitter replacement race, compare and remove registry

---

## 빠른 탐색

이 `README`는 Spring primer와 운영형 deep dive가 함께 있는 **navigator 문서**다.
mixed catalog에서 `[playbook]` 라벨은 debugging / observability 순서를 먼저 따라가야 하는 step-oriented 문서라는 뜻이고, 라벨이 없는 항목은 경계/원리 중심 `deep dive`다.

- **🟢 Beginner 입문 5편** (Spring 5단계 시작점):
  - [`IoC와 DI 기초`](./spring-ioc-di-basics.md) — 제어 역전과 의존성 주입이 왜 필요한지
  - [`Spring Bean 생명주기 기초`](./spring-bean-lifecycle-basics.md) — `@PostConstruct`, `@PreDestroy`, singleton 공유 주의
  - [`Spring MVC 컨트롤러 기초`](./spring-mvc-controller-basics.md) — `DispatcherServlet` 흐름, `@RestController`, `@RequestMapping`
  - [`@Transactional 기초`](./spring-transactional-basics.md) — 프록시 트랜잭션, rollback 규칙, 내부 호출 함정
  - [`Spring Security 기초`](./spring-security-basics.md) — 인증 vs 인가, 401 vs 403, `HttpSecurity` 설정

- **🟢 Beginner 입문 5편 (Cycle 2)** — AOP·부트 자동구성·JPA·테스트·예외처리:
  - [`AOP 기초`](./spring-aop-basics.md) — 횡단 관심사, Advice 종류, 프록시 self-invocation 주의
  - [`Spring Boot 자동 구성 기초`](./spring-boot-autoconfiguration-basics.md) — starter, `@ConditionalOnMissingBean`, 자동 Bean 오버라이드
  - [`Spring Data JPA 기초`](./spring-data-jpa-basics.md) — `JpaRepository`, 쿼리 메서드, Dirty Checking 입문
  - [`Spring 테스트 기초`](./spring-testing-basics.md) — `@SpringBootTest` vs 슬라이스 테스트, `MockMvc`, `@MockBean`
  - [`Spring 예외 처리 기초`](./spring-exception-handling-basics.md) — `@ExceptionHandler`, `@RestControllerAdvice`, 오류 응답 통일

- 기본 primer부터 읽고 싶다면:
  - `Spring Bean과 DI 기초`
  - `Spring @Primary vs @Qualifier vs 컬렉션 주입 결정 가이드`
  - `Spring Bean 이름 규칙과 rename 함정 입문`
  - `커스텀 @Qualifier 입문`
  - `Spring 런타임 전략 선택과 @Qualifier 경계`
  - `Spring Configuration vs Auto-configuration 입문`
  - `Spring Component Scan 실패 패턴`
  - `Spring scanBasePackages vs @Import 선택 기준`
  - `Spring JPA Scan Boundary 함정`
  - `DI 예외 빠른 판별`
  - `IoC 컨테이너와 DI`
  - `AOP와 프록시 메커니즘`
  - `Spring MVC 요청 생명주기`
  - `Spring Boot 자동 구성`
  - `Spring Boot Condition Evaluation Report 첫 디버그 체크리스트`
  - `Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ`
  - `Spring Security 아키텍처`
  - `cookie`, `session`, `JWT` 개념에서 올라오는 beginner route라면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md) -> `Spring Security 아키텍처` 순으로 먼저 맞춘다.
- 트랜잭션 / persistence cluster로 바로 들어가려면:
  - `@Transactional 깊이 파기`
  - `DB Lock Wait / Deadlock vs Spring Proxy / Rollback`
  - `[playbook] Spring Transaction Debugging Playbook`
  - `Spring Persistence Context Flush / Clear / Detach`
  - `dirty read`, `write skew`, `phantom`, `왜 @Transactional이 안 먹지`, `왜 안 롤백되지`가 같이 섞이면 처음부터 `REQUIRES_NEW`, rollback-only, readOnly, routing-datasource까지 한 번에 열지 말고 core ladder를 `Transaction Isolation and Locking` -> `Database to Spring Transaction Master Note` -> `@Transactional 깊이 파기` -> `Spring Service-Layer Transaction Boundary Patterns` 순으로 먼저 맞춘다.
  - core ladder 뒤 follow-up beginner branch는 증상별로 고른다.
    - `audit는 남고 본 작업은 롤백`, `REQUIRES_NEW`, `partial commit`이면 `Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies` -> `Spring TransactionSynchronization Ordering / Suspend / Resume`
    - `UnexpectedRollbackException`, `transaction marked rollback-only`, `catch 했는데 마지막에 터짐`이면 `Spring UnexpectedRollback / Rollback-Only` -> `[playbook] Spring Transaction Debugging Playbook`
    - `readOnly면 안전한가`, `dirty checking`, `flush mode`가 헷갈리면 `Spring Transaction Isolation / ReadOnly Pitfalls`
    - `inner readOnly인데 writer pool`, `reader route가 안 탄다`, `read/write split`이면 `Spring Routing DataSource와 JDBC Exception Translation`
  - `lock wait`, `deadlock`, `UnexpectedRollbackException`, `self invocation`이 한 문장에 같이 섞이면 `DB Lock Wait / Deadlock vs Spring Proxy / Rollback`부터 보고 DB branch와 Spring branch를 먼저 가른다
- 요청 처리 / 운영 cluster로 바로 들어가려면:
  - `Spring MVC 요청 생명주기`
  - `Spring MVC Async Dispatch`
  - `Spring ProblemDetail Before-After Commit Matrix`
  - `Spring HttpMessageNotWritableException Failure Taxonomy`
  - `Spring ProblemDetail vs /error Handoff Matrix`
  - `Spring Request Lifecycle Timeout / Disconnect Bridge`
  - `Spring Async Timeout vs Disconnect Decision Tree`
  - `Spring Servlet Container Disconnect Exception Mapping`
  - `Spring Partial-Response Access Log Interpretation`
  - `Spring HTTP/2 Reset Attribution`
  - `Spring StreamingResponseBody / SSE Commit Lifecycle`
  - `Spring ResponseBodyAdvice on Streaming Types`
  - `[playbook] Spring Async MVC Streaming Observability Playbook`
  - `Spring SSE Disconnect Observability Patterns`
  - `Spring ResponseBodyEmitter Media-Type Boundaries`
  - `Spring MVC Flux JSON vs NDJSON and SSE Adaptation`
  - `Spring Streaming Client Parsing Matrix`
  - `Spring SSE Proxy Idle-Timeout Matrix`
  - `Spring MVC SseEmitter vs WebFlux SSE Timeout Behavior`
  - `Spring SseEmitter Timeout Callback Race Matrix`
  - `Spring SSE Buffering / Compression Checklist`
  - `Spring SSE Replay Buffer / Last-Event-ID Recovery`
  - `Spring Observability, Micrometer, Tracing`
  - `499`, `broken pipe`, `client disconnect`, `connection reset`, `proxy timeout`처럼 disconnect symptom이 먼저 보이면 [Spring Request Lifecycle Timeout / Disconnect Bridge](#spring-bridge-request-lifecycle-timeout-disconnect) -> [Spring Async Timeout vs Disconnect Decision Tree](#spring-async-timeout-vs-disconnect-decision-tree) -> [Spring Servlet Container Disconnect Exception Mapping](#spring-servlet-container-disconnect-exception-mapping) -> [Network: Request Lifecycle Upload Disconnect](../network/README.md#network-bridge-request-lifecycle-upload-disconnect)
- [Spring + Network](../../rag/cross-domain-bridge-map.md#spring--network) route로 바로 들어가려면:
  - [Spring Request Lifecycle Timeout / Disconnect Bridge](#spring-bridge-request-lifecycle-timeout-disconnect)
  - [Spring Async Timeout vs Disconnect Decision Tree](#spring-async-timeout-vs-disconnect-decision-tree)
  - [Spring Partial-Response Access Log Interpretation](#spring-partial-response-access-log-interpretation)
  - [Network: Request Lifecycle Upload Disconnect](../network/README.md#network-bridge-request-lifecycle-upload-disconnect)
  - [Network: Edge Status Timeout Control Plane](../network/README.md#network-bridge-edge-status-timeout-control-plane)
- [Spring + Security](../../rag/cross-domain-bridge-map.md#spring--security) route로 바로 들어가려면:
  - `cookie`, `session`, `JWT`는 아는데 `SecurityContextRepository`, `SavedRequest`, `hidden JSESSIONID`가 갑자기 등장하면 [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) route를 먼저 탄다.
  - `SavedRequest`, `401 -> 302` bounce, `hidden session mismatch`가 먼저 보이면 [Spring RequestCache / SavedRequest](#spring-bridge-requestcache-savedrequest)와 [Spring Security 예외 번역과 세션 경계](#spring-bridge-security-session-boundary) anchor부터 확인한다.
  - [Spring Security 예외 번역과 세션 경계](#spring-bridge-security-session-boundary)
  - [Spring RequestCache / SavedRequest](#spring-bridge-requestcache-savedrequest)
  - [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
  - [Security: Session / Boundary / Replay](../security/README.md#session--boundary--replay)
- 운영 디버깅 절차가 먼저 필요하면:
  - `[playbook] Spring Transaction Debugging Playbook`
  - `[playbook] Spring Async MVC Streaming Observability Playbook`
  - `[playbook] Spring Startup Bean Graph Debugging Playbook`
- 문서 역할이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)
  - [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)

## Spring Bean과 DI 기초

> Bean 등록, 생성자 주입, component scan, `@Bean`, 프록시 감각, `@Primary`/`@Qualifier` 후보 선택까지 한 번에 잡는 입문용 primer

- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)

## Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드

> 같은 타입 bean이 여러 개일 때 "기본 하나", "이번엔 이 bean", "전부 모으기"를 한 표와 짧은 예제로 바로 나눈다

- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)

## Spring Bean 이름 규칙과 rename 함정 입문

> 이름 없는 `@Component`/`@Bean`의 기본 이름 규칙, alias, 문자열 `@Qualifier`가 bean 이름과 엮이는 방식, rename 때 깨지는 지점을 beginner 기준으로 정리한다

- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)

## 커스텀 `@Qualifier` 입문

> bean 이름 문자열로 후보를 찍는 단계에서, 같은 선택 규칙이 반복될 때 역할 annotation 계약으로 올리는 기준을 작은 예제로 정리한다

- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)

## Spring 런타임 전략 선택과 `@Qualifier` 경계

> `@Qualifier`가 bean wiring을 고정하는 문제인지, `Map<String, Bean>`/router가 요청마다 전략을 고르는 문제인지 결제·알림 예제로 분리한다

- [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)

## Spring Configuration vs Auto-configuration 입문

> `@Configuration`, `@Bean`, Boot auto-configuration, `proxyBeanMethods`를 "내 설명서 + Boot 기본 설명서 + 안전 스위치"라는 한 장의 mental model로 연결한다

- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-call, 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
- [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)

## Spring Component Scan 실패 패턴

> `@SpringBootApplication` package 위치, custom scan 축소, multi-module package mismatch, stereotype annotation 누락으로 생기는 missing bean 문제를 빠르게 분류한다

- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- `[playbook]` [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)

## Spring `scanBasePackages` vs `@Import` 선택 기준

> shared module을 붙일 때 scan 범위를 넓혀도 되는지, 아니면 명시적 `@Import`나 Boot auto-configuration으로 계약을 세워야 하는지 가른다

- [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)

## Spring JPA Scan Boundary 함정

> `@SpringBootApplication(scanBasePackages = ...)`를 건드렸다고 entity/repository discovery까지 같이 바뀐다고 착각하기 쉬운 지점을 beginner 기준으로 분리한다

- [Spring JPA Scan Boundary 함정: `@EntityScan`, `@EnableJpaRepositories`, Component Scan은 서로 다르다](./spring-jpa-entityscan-enablejparepositories-boundaries.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)

## DI 예외 빠른 판별

> `NoSuchBeanDefinitionException`를 scan 누락 vs `@Profile`/conditional 탈락으로 먼저 가르고, `NoUniqueBeanDefinitionException` 후보 중복까지 이어서 분기하는 beginner troubleshooting note

- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)

## IoC 컨테이너와 DI

> Bean 생명주기, 스코프, singleton 함정까지 — Spring이 객체를 관리하는 진짜 방식

- [IoC 컨테이너와 DI](./ioc-di-container.md)

## Bean 생명주기와 스코프 함정

> singleton/prototype/request/session 스코프와 프록시 타이밍, `ObjectProvider` vs scoped proxy 조회 시점 차이까지 이어서 본다

- [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
- [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)

## AOP와 프록시 메커니즘

> JDK Dynamic Proxy vs CGLIB, self-invocation 문제의 근본 원인

- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)

## Spring Self-Invocation / Proxy Annotation Matrix

> `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`가 왜 같은 self-invocation 구조 함정을 공유하는지 한 번에 본다

- [Spring Self-Invocation Proxy Trap Matrix: `@Transactional`, `@Async`, `@Cacheable`, `@Validated`, `@PreAuthorize`](./spring-self-invocation-proxy-annotation-matrix.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)

## Spring Early Bean Reference와 Circular Proxy Traps

> 순환 의존성과 early reference가 raw target 누출, 프록시 누락, 애매한 startup 오류로 이어지는 경로를 본다

- [Spring Early Bean References and Circular Proxy Traps](./spring-early-bean-reference-circular-proxy-traps.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)

## Spring FactoryBean / SmartInitializingSingleton

> 제품 객체 생성과 singleton 전체 초기화 후 훅을 각각 어디에 써야 하는지 본다

- [Spring `FactoryBean` and `SmartInitializingSingleton` Extension Points](./spring-factorybean-smartinitializingsingleton-extension-points.md)
- [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)

## @Transactional 깊이 파기

> 전파 수준, 롤백 규칙, readOnly의 진짜 의미까지

- [@Transactional 깊이 파기](./transactional-deep-dive.md)
- [Database to Spring Transaction Master Note](../../master-notes/database-to-spring-transaction-master-note.md)
- [트랜잭션 격리수준과 락](../database/transaction-isolation-locking.md)

## Spring TransactionTemplate과 Programmatic Transaction

> 메서드 경계보다 더 잘게 트랜잭션을 자를 때 `TransactionTemplate`을 어떻게 쓰는지 정리한다

- [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)

## Spring UnexpectedRollback / Rollback-Only

> 이미 rollback-only가 찍힌 트랜잭션을 왜 바깥에서 뒤늦게 커밋하려다 실패하는지 정리한다

- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
- `[playbook]` [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

## DB Lock Wait / Deadlock vs Spring Proxy / Rollback

> `lock wait`, `deadlock`, `왜 안 롤백되지`, `왜 @Transactional이 안 먹지`가 섞였을 때 DB wait 증거와 Spring proxy/rollback 착시를 먼저 가른다

- [DB Lock Wait / Deadlock vs Spring Proxy / Rollback 빠른 분기표](./spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../database/lock-wait-deadlock-latch-triage-playbook.md)
- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)

## Spring TransactionSynchronization Ordering / Suspend / Resume

> `TransactionSynchronization`를 afterCommit 편의 기능이 아니라 resource binding, ordering, suspend/resume lifecycle로 본다

- [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
- [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)

## Spring Propagation Edge Cases: MANDATORY / SUPPORTS / NOT_SUPPORTED

> 드물어 보이지만 transaction ownership, request lifecycle, non-tx intent를 함께 읽어야 하는 전파 수준을 정리한다

- [Spring Transaction Propagation: `MANDATORY` / `SUPPORTS` / `NOT_SUPPORTED` Boundaries](./spring-transaction-propagation-mandatory-supports-not-supported-boundaries.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

## Spring Service-Layer Transaction Boundary Patterns

> `@Transactional`을 application service 유스케이스 경계에 두고, controller/repository/internal call 오배치를 피하는 기준

- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)

## Spring MVC 요청 생명주기

> DispatcherServlet부터 응답까지 전체 파이프라인

- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

## Spring HandlerMethodReturnValueHandler Chain

> 컨트롤러 반환값이 view name, body, `ResponseEntity`, async/streaming 응답으로 어떻게 해석되고, body write에서 response commit과 disconnect가 어디서 갈리는지 정리한다

- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
- [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

## Spring ResponseBodyAdvice on Streaming Types

> global JSON envelope를 `ResponseBodyAdvice`로 통일하려 할 때 `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`가 왜 별도 handler ownership과 wire contract 때문에 같은 규칙을 따를 수 없는지 정리한다

- [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
- [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)

## Spring ProblemDetail Before-After Commit Matrix

> 어떤 MVC 실패가 아직 `ProblemDetail`로 번역될 수 있고, 어떤 실패가 response commit 이후 socket/write 오류로 접히는지를 commit 경계 기준으로 정리한다

- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
- [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
- [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## Spring HttpMessageNotWritableException Failure Taxonomy

> `HttpMessageNotWritableException`를 converter-selection, serialization, first-flush, partial-write로 나눠 pre-commit 문제와 post-commit partial response 문제를 빠르게 구분한다

- [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
- [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)

## Spring ProblemDetail vs /error Handoff Matrix

> unresolved MVC exception이 언제 Boot `/error` fallback으로 handoff되고, 언제 committed response 때문에 그 handoff가 끊기는지 ownership 관점에서 정리한다

- [Spring `HttpMessageNotWritableException` Failure Taxonomy](./spring-httpmessagenotwritableexception-failure-taxonomy.md)
- [Spring `ProblemDetail` vs `/error` Handoff Matrix](./spring-problemdetail-vs-error-handoff-matrix.md)
- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)

## Spring MVC vs WebFlux

> thread-per-request 모델과 event-loop + backpressure 모델의 차이, 그리고 언제 reactive가 득이 되는지

- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
- [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)

## Spring MVC Async Dispatch

> `Callable`, `DeferredResult`, `WebAsyncTask`가 Servlet async와 redispatch 위에서 어떻게 동작하는지, filter/interceptor/thread-local이 왜 흔들리는지 본다

- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
- [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)
- [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)
- [gRPC Deadlines, Cancellation Propagation](../network/grpc-deadlines-cancellation-propagation.md)

## Spring OncePerRequestFilter Async / Error Dispatch

> `OncePerRequestFilter`가 async redispatch와 error dispatch에서 왜 다르게 보이는지, 어떤 필터는 왜 다시 타면 안 되는지 정리한다

- [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)

## Spring BasicErrorController / ErrorAttributes

> MVC advice 밖 실패가 `/error`, `BasicErrorController`, `ErrorAttributes` 경로로 어떻게 fallback되는지 본다

- [Spring `BasicErrorController`, `ErrorAttributes`, and Whitelabel Error Boundaries](./spring-basicerrorcontroller-errorattributes-whitelabel-boundaries.md)
- [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)

## Spring Reactive-Blocking Bridge

> WebFlux/WebClient를 쓰면서 어디서 `block()`하고 어디를 `boundedElastic`로 격리할지 경계를 명시한다

- [Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps](./spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
- [Spring WebFlux vs MVC](./spring-webflux-vs-mvc.md)

<a id="spring-bridge-request-lifecycle-timeout-disconnect"></a>
## Spring Request Lifecycle Timeout / Disconnect Bridge

> Spring MVC lifecycle과 timeout budget, `499`, `client disconnect`, `broken pipe`, `connection reset`, `proxy timeout`, cancellation을 함께 본다

- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)

## Spring Async Timeout vs Disconnect Decision Tree

> `AsyncRequestTimeoutException`, `AsyncRequestNotUsableException`, disconnected-client 신호가 `DeferredResult`, `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`에서 어느 순간 resolver path와 transport path로 갈라지는지 decision tree로 정리한다

- [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)

## Spring Servlet Container Disconnect Exception Mapping

> Tomcat/Jetty/Undertow가 `broken pipe`, `connection reset`, disconnected-client style abort를 어떤 예외 shape로 surface하는지와, 이를 로그/알림에서 어떻게 정규화할지 정리한다

- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## Spring Partial-Response Access Log Interpretation

> download와 streaming response가 중간에 잘렸을 때 access log의 status/bytes/duration과 app log disconnect 예외를 한 타임라인으로 묶어 읽는 기준을 정리한다

- [Spring Partial-Response Access Log Interpretation](./spring-partial-response-access-log-interpretation.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## Spring HTTP/2 Reset Attribution

> HTTP/2 `RST_STREAM`, `GOAWAY`, browser cancel이 Tomcat/Jetty/Undertow에서 classic broken pipe와 어떻게 다르게 surface되는지와, Spring MVC에서 어떤 bucket으로 태깅해야 하는지 정리한다

- [Spring HTTP/2 Reset Attribution in Spring MVC](./spring-http2-reset-attribution-spring-mvc.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

## Spring StreamingResponseBody / SSE Commit Lifecycle

> `StreamingResponseBody`, `ResponseBodyEmitter`, `SseEmitter`의 first-byte commit, flush cadence, async timeout, disconnect surface를 타입별로 분리해 본다

- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)

## Spring Async MVC Streaming Observability

> first-byte latency, 마지막 성공 flush, completion cause, `AsyncRequestNotUsableException` attribution을 분리해 streaming endpoint를 운영형 메트릭과 로그로 읽는 기준을 정리한다

- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring Observability, Micrometer, Tracing](./spring-observability-micrometer-tracing.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)

## Spring SSE Disconnect Observability Patterns

> heartbeat cadence, reconnect pressure, container 예외 shape, proxy idle timeout을 한 타임라인으로 묶어 SSE alert noise와 실제 incident를 분리하는 운영 기준을 정리한다

- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- `[playbook]` [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring HTTP/2 Reset Attribution in Spring MVC](./spring-http2-reset-attribution-spring-mvc.md)

## Spring ResponseBodyEmitter Media-Type Boundaries

> `ResponseBodyEmitter`의 flush cadence와 `application/x-ndjson`, `text/plain`, `application/json` 계약 경계를 분리해, client가 flush를 곧바로 메시지 경계로 착각하지 않게 한다

- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE](./spring-mvc-flux-json-vs-ndjson-sse-adaptation.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)

## Spring MVC Flux JSON vs NDJSON and SSE Adaptation

> 같은 `Flux<?>`라도 Spring MVC는 media type이 item framing을 제공하는지에 따라 `application/json`은 `DeferredResult<List<?>>`로 모으고, NDJSON/SSE는 emitter로 흘려 보낸다

- [Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE](./spring-mvc-flux-json-vs-ndjson-sse-adaptation.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
- [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)

## Spring Streaming Client Parsing Matrix

> browser `fetch`, `EventSource`, CLI line reader가 각각 bytes, SSE event block, newline line을 어떻게 parse하는지 기준으로 NDJSON, plain text, SSE endpoint 계약을 맞춘다

- [Spring Streaming Client Parsing Matrix: `fetch`, `EventSource`, CLI Line Readers](./spring-streaming-client-parsing-matrix.md)
- [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
- [Spring MVC `Flux` Adaptation: `application/json` vs NDJSON and SSE](./spring-mvc-flux-json-vs-ndjson-sse-adaptation.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)

## Spring SSE Proxy Idle-Timeout Matrix

> ALB, Nginx, CDN, 브라우저 reconnect가 서로 다른 타이머를 갖는 체인에서 `SseEmitter` heartbeat와 `Last-Event-ID` recovery를 어떻게 맞출지 정리한다

- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)

## Spring MVC SseEmitter vs WebFlux SSE Timeout Behavior

> 같은 SSE라도 MVC `SseEmitter`는 async request lifetime 중심, WebFlux SSE는 publisher lifetime과 cancellation 중심으로 읽어야 하며, heartbeat와 reconnect는 두 스택 모두 별도 계약으로 분리해야 한다

- [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)

## Spring SseEmitter Timeout Callback Race Matrix

> `onTimeout`, `onError`, `onCompletion`, `completeWithError(...)`를 proxy idle timeout, reconnect replacement, scheduler cleanup ownership과 함께 읽어 old emitter cleanup이 new emitter를 지우는 race를 피한다

- [Spring `SseEmitter` Timeout Callback Race Matrix](./spring-sseemitter-timeout-callback-race-matrix.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)

## Spring SSE Buffering / Compression Checklist

> Nginx/CDN buffering, gzip/brotli, body transform이 `text/event-stream`의 즉시 전달과 heartbeat 관측을 어떻게 망가뜨리는지 점검 순서로 정리한다

- [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
- [Cache-Control 실전](../network/cache-control-practical.md)

## Spring SSE Replay Buffer / Last-Event-ID Recovery

> `Last-Event-ID`를 reconnect header로만 보지 않고, replay window 크기, event ordering fence, stale cursor reset, multi-instance failover 복구 계약까지 함께 정리한다

- [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
- [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
- [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
- [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

## Spring Boot 자동 구성

> @Conditional의 동작 원리와 커스텀 스타터 만들기

- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)

## Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ

> starter를 추가했는데 기대한 bean이 안 보일 때 classpath 조건, property, existing bean back-off, scan/import boundary를 한 번에 분기한다

- [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)

## Spring Startup Hooks와 Readiness Warmup

> startup code를 `@PostConstruct`, runner, `SmartLifecycle`, `ApplicationReadyEvent` 중 어디에 둘지와 readiness/liveness 기준을 같이 본다

- [Spring Startup Hooks: `CommandLineRunner`, `ApplicationRunner`, `SmartLifecycle`, and Readiness Warmup](./spring-startup-runner-smartlifecycle-readiness-warmup.md)
- [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)
- [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)

## Spring Startup / Bean Graph Debugging

> Bean 생성 실패, 조건부 자동 구성 누락, 순환 참조, 설정 바인딩 실패를 어디서부터 좁힐지 정리한다

- `[playbook]` [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)
- [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
- [Spring Early Bean References and Circular Proxy Traps](./spring-early-bean-reference-circular-proxy-traps.md)

## Spring Security 아키텍처

> 필터 체인, 인증 아키텍처, OAuth2/JWT 통합

- [Spring Security 아키텍처](./spring-security-architecture.md)

<a id="spring-bridge-security-session-boundary"></a>
## Spring Security 예외 번역과 세션 경계

> 401/403이 어디서 결정되는지, stateless와 session 기반 인증이 어떤 저장 경계를 가지는지 정리한다

- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)
- [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
- [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
- [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

## Spring Logout Handler / Success Flow

> logout handler가 local cleanup을 어디까지 담당하고, logout success가 언제 redirect/IdP hop만 끝낸 채 full revoke와 분리되는지 정리한다

- [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](./spring-security-logout-handler-success-boundaries.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
- [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)
- [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)

<a id="spring-bridge-requestcache-savedrequest"></a>
## Spring RequestCache / SavedRequest

> 로그인 전 요청 저장과 로그인 후 원래 URL 복귀 흐름이 API/stateless 경계와 어떻게 충돌하는지, 그리고 왜 이 정보가 OIDC revoke lookup과는 다른지 정리한다

- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Network: HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)
- [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
- [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
- [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

## Spring OAuth2 + JWT 통합

> OAuth2 로그인 결과를 애플리케이션 JWT로 안전하게 바꾸면서 `SavedRequest`, post-login persistence, OIDC back-channel logout mapping을 어디서 분리할지 정리한다

- [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](./spring-security-logout-handler-success-boundaries.md)
- [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md)

## Spring Test Slices와 Context Caching

> `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest`와 컨텍스트 캐시를 설계 관점으로 해석한다

- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)

## Spring Test Slice Scan Boundary 오해

> `@WebMvcTest`, `@DataJpaTest`, custom test config가 full `@SpringBootTest`와 다른 탐색 경계를 어떻게 만드는지 beginner 기준으로 정리한다

- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
- [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)

## Spring Test Slice Boundary Leaks

> `@Import`, `@TestConfiguration`, custom security/filter 설정이 slice 경계를 어떻게 조용히 넓히는지 정리한다

- [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)
- [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
- [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)

## Spring JsonTest / RestClientTest Slice Boundaries

> Jackson 직렬화 계약과 outbound HTTP client 계약을 각각 어떤 slice로 좁게 검증할지 정리한다

- [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)
- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)

## Spring Cache 추상화 함정

> `@Cacheable`이 숨기는 key, invalidation, self-invocation 함정까지

- [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)

## Spring Transaction Debugging Playbook

> `@Transactional`이 왜 안 먹는지, 어디서부터 추적할지 정리한 실전 디버깅 절차

- `[playbook]` [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
- [Database to Spring Transaction Master Note](../../master-notes/database-to-spring-transaction-master-note.md)

## Spring Persistence Context Flush / Clear / Detach

> dirty checking, bulk update, batch 처리에서 영속성 컨텍스트를 언제 비우고 동기화할지 다룬다

- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md)
- [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

## Spring Routing DataSource와 JDBC Exception Translation

> read/write 분리에서 커넥션 획득 시점과 replica consistency를 어떻게 볼지, JDBC 예외를 어떻게 의미 기반으로 번역할지 함께 본다

- [Spring Routing DataSource Read/Write Transaction Boundaries](./spring-routing-datasource-read-write-transaction-boundaries.md)
- [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
- [Spring `JdbcTemplate` and `SQLException` Translation](./spring-jdbctemplate-sqlexception-translation.md)
- [Spring Transaction Isolation / ReadOnly Pitfalls](./spring-transaction-isolation-readonly-pitfalls.md)

## Spring Scheduler와 Async 경계

- [Spring Scheduler와 Async 경계](./spring-scheduler-async-boundaries.md)

## Spring TaskExecutor / TaskScheduler Overload Semantics

> executor queue, rejection policy, fixedRate/fixedDelay, scheduler overlap이 실제 운영 장애 모델을 어떻게 바꾸는지 본다

- [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](./spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)
- [Spring Scheduler와 Async 경계](./spring-scheduler-async-boundaries.md)

## Spring Distributed Scheduling / Cron Drift / Leader Election

> 멀티 인스턴스에서 `@Scheduled`를 어떻게 바라봐야 하는지, duplicate execution, leader handoff, checkpoint, catch-up policy까지 포함해 정리한다

- [Spring Distributed Scheduling, Cron Drift, and Leader-Election Patterns](./spring-distributed-scheduling-cron-drift-leader-election-patterns.md)
- [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](./spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)
- [Spring Batch Chunk / Retry / Skip](./spring-batch-chunk-retry-skip.md)

## Spring RequestContextHolder / ThreadLocal Leakage

> request context가 async pool에서 단순히 사라지는 것이 아니라 다른 요청에 섞여 남을 수 있는 문제를 본다

- [Spring `RequestContextHolder`, `ThreadLocal`, and Request Context Leakage Across Async Pools](./spring-requestcontextholder-threadlocal-leakage-async-pools.md)
- [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)

## Spring `@Transactional`과 `@Async` 조합 함정

> caller transaction과 worker thread가 언제 갈라지고, 커밋 이후 비동기 후속 처리를 어떻게 분리할지 정리한다

- [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)
- [Spring EventListener, TransactionalEventListener, Outbox](./spring-eventlistener-transaction-phase-outbox.md)

## Spring Batch chunk, retry, skip

- [Spring Batch chunk, retry, skip](./spring-batch-chunk-retry-skip.md)

## Spring Observability, Micrometer, Tracing

- [Spring Observability, Micrometer, Tracing](./spring-observability-micrometer-tracing.md)

## Spring Resilience4j: Retry, CircuitBreaker, Bulkhead

> retry storm, timeout, circuit breaker, bulkhead, fallback를 Spring Boot 운영 관점에서 함께 본다

- [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](./spring-resilience4j-retry-circuit-breaker-bulkhead.md)

## Spring EventListener, TransactionalEventListener, Outbox

> `@EventListener`, `@TransactionalEventListener`, Outbox를 트랜잭션 phase와 정합성 경계 기준으로 비교한다

- [Spring EventListener, TransactionalEventListener, Outbox](./spring-eventlistener-transaction-phase-outbox.md)
- [Spring `@EventListener` Ordering and Async Traps](./spring-eventlistener-ordering-async-traps.md)
- [Spring ApplicationEventMulticaster Internals](./spring-applicationeventmulticaster-internals.md)
- [Spring `@TransactionalEventListener` Outside Transactions and `fallbackExecution`](./spring-transactionaleventlistener-fallbackexecution-no-transaction-boundaries.md)

## Spring WebClient vs RestTemplate

- [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
- [Spring RestClient vs WebClient Lifecycle Boundaries](./spring-restclient-vs-webclient-lifecycle-boundaries.md)
- [Spring WebClient Connection Pool and Timeout Tuning](./spring-webclient-connection-pool-timeout-tuning.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)

---

## 질의응답

_질문에 대한 답을 말해보며 공부한 내용을 점검할 수 있으며, 클릭하면 답변 내용을 확인할 수 있습니다._

<details>
<summary>Spring의 IoC 컨테이너가 Bean을 관리하는 방식과, 개발자가 직접 new로 객체를 생성하는 것의 차이를 설명해주세요.</summary>
<p>

IoC 컨테이너는 BeanDefinition을 기반으로 객체의 생성, 의존성 주입, 초기화, 소멸까지 전체 생명주기를 관리합니다.
개발자가 new로 직접 생성하면 의존 객체를 직접 조립해야 하고, AOP 프록시가 적용되지 않으며, 생명주기 콜백(@PostConstruct 등)도 호출되지 않습니다.
핵심 차이는 "제어의 주체"가 개발자에서 컨테이너로 역전된다는 점입니다.

</p>
</details>

<details>
<summary>@Transactional이 같은 클래스 내부 메서드 호출 시 동작하지 않는 이유를 프록시 관점에서 설명해주세요.</summary>
<p>

Spring AOP는 프록시 기반으로 동작합니다. 외부에서 호출할 때는 프록시 객체를 통해 메서드가 호출되므로 @Transactional 어드바이스가 적용됩니다.
하지만 같은 클래스 내부에서 this.method()로 호출하면, 프록시를 거치지 않고 실제 타깃 객체의 메서드를 직접 호출하게 됩니다.
따라서 트랜잭션 인터셉터가 끼어들 기회가 없어 @Transactional이 무시됩니다.
해결 방법으로는 AopContext.currentProxy(), 별도 빈으로 분리, AspectJ 위빙 등이 있습니다.

</p>
</details>

<details>
<summary>Spring Boot의 자동 구성(Auto-configuration)이 동작하는 원리를 설명해주세요.</summary>
<p>

@SpringBootApplication 안에 포함된 @EnableAutoConfiguration이 핵심입니다.
이 어노테이션은 AutoConfigurationImportSelector를 통해 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 파일에 나열된 모든 자동 구성 클래스를 후보로 로딩합니다.
각 클래스에는 @ConditionalOnClass, @ConditionalOnMissingBean 등의 조건이 붙어 있어, 조건을 만족하는 것만 실제로 빈으로 등록됩니다.
개발자가 직접 같은 타입의 빈을 등록하면 @ConditionalOnMissingBean에 의해 자동 구성이 비활성화되어 커스터마이징이 가능합니다.

</p>
</details>

<details>
<summary>Spring Security의 필터 체인이 요청을 처리하는 흐름을 설명해주세요.</summary>
<p>

HTTP 요청이 들어오면 DelegatingFilterProxy가 Spring 컨텍스트의 FilterChainProxy에게 위임합니다.
FilterChainProxy는 요청 URL 패턴에 맞는 SecurityFilterChain을 선택하고, 그 안에 등록된 필터들(UsernamePasswordAuthenticationFilter, BearerTokenAuthenticationFilter 등)을 순서대로 실행합니다.
인증 필터는 Authentication 객체를 생성해 AuthenticationManager에게 인증을 위임하고, 성공 시 SecurityContextHolder에 저장합니다.
이후 AuthorizationFilter에서 권한 검사를 수행하고, 통과하면 DispatcherServlet으로 요청이 전달됩니다.

</p>
</details>
