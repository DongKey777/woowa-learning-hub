# Spring Framework (스프링 프레임워크)

> 작성자 : [이동훈](https://github.com/idonghun)

<details>
<summary>Table of Contents</summary>

- [IoC 컨테이너와 DI](#ioc-컨테이너와-di)
- [Bean 생명주기와 스코프 함정](#bean-생명주기와-스코프-함정)
- [AOP와 프록시 메커니즘](#aop와-프록시-메커니즘)
- [@Transactional 깊이 파기](#transactional-깊이-파기)
- [Spring MVC 요청 생명주기](#spring-mvc-요청-생명주기)
- [Spring MVC vs WebFlux](#spring-mvc-vs-webflux)
- [Spring Boot 자동 구성](#spring-boot-자동-구성)
- [Spring Security 아키텍처](#spring-security-아키텍처)
- [Spring OAuth2 + JWT 통합](#spring-oauth2--jwt-통합)
- [Spring Test Slices와 Context Caching](#spring-test-slices와-context-caching)
- [Spring Cache 추상화 함정](#spring-cache-추상화-함정)
- [Spring Transaction Debugging Playbook](#spring-transaction-debugging-playbook)
- [Spring Scheduler와 Async 경계](#spring-scheduler와-async-경계)
- [Spring Batch chunk, retry, skip](#spring-batch-chunk-retry-skip)
- [Spring Observability, Micrometer, Tracing](#spring-observability-micrometer-tracing)
- [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](#spring-resilience4j-retry-circuitbreaker-bulkhead)
- [Spring WebClient vs RestTemplate](#spring-webclient-vs-resttemplate)
- [Spring EventListener, TransactionalEventListener, Outbox](#spring-eventlistener-transactionaleventlistener-outbox)

</details>

---

## IoC 컨테이너와 DI

> Bean 생명주기, 스코프, singleton 함정까지 — Spring이 객체를 관리하는 진짜 방식

- [IoC 컨테이너와 DI](./ioc-di-container.md)

## Bean 생명주기와 스코프 함정

> singleton/prototype/request/session 스코프와 프록시 타이밍이 만드는 실전 함정

- [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)

## AOP와 프록시 메커니즘

> JDK Dynamic Proxy vs CGLIB, self-invocation 문제의 근본 원인

- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)

## @Transactional 깊이 파기

> 전파 수준, 롤백 규칙, readOnly의 진짜 의미까지

- [@Transactional 깊이 파기](./transactional-deep-dive.md)

## Spring MVC 요청 생명주기

> DispatcherServlet부터 응답까지 전체 파이프라인

- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)

## Spring MVC vs WebFlux

> thread-per-request 모델과 event-loop + backpressure 모델의 차이, 그리고 언제 reactive가 득이 되는지

- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)

## Spring Boot 자동 구성

> @Conditional의 동작 원리와 커스텀 스타터 만들기

- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)

## Spring Security 아키텍처

> 필터 체인, 인증 아키텍처, OAuth2/JWT 통합

- [Spring Security 아키텍처](./spring-security-architecture.md)

## Spring OAuth2 + JWT 통합

> OAuth2 로그인 결과를 애플리케이션 JWT로 안전하게 바꾸는 경계 설계

- [Spring OAuth2 + JWT 통합](./spring-oauth2-jwt-integration.md)

## Spring Test Slices와 Context Caching

> `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest`와 컨텍스트 캐시를 설계 관점으로 해석한다

- [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)

## Spring Cache 추상화 함정

> `@Cacheable`이 숨기는 key, invalidation, self-invocation 함정까지

- [Spring Cache 추상화 함정](./spring-cache-abstraction-traps.md)

## Spring Transaction Debugging Playbook

> `@Transactional`이 왜 안 먹는지, 어디서부터 추적할지 정리한 실전 디버깅 절차

- [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)

## Spring Scheduler와 Async 경계

- [Spring Scheduler와 Async 경계](./spring-scheduler-async-boundaries.md)

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

## Spring WebClient vs RestTemplate

- [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)

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
