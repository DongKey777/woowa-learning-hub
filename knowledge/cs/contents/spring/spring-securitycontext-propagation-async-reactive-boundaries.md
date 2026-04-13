# Spring SecurityContext Propagation Across Async and Reactive Boundaries

> 한 줄 요약: `SecurityContext`는 스레드와 리액티브 컨텍스트 사이에서 자동으로 보존되지 않으므로, async와 reactive boundary를 넘을 때는 별도 전파 전략이 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
> - [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)
> - [Spring Security Method Security Deep Dive](./spring-security-method-security-deep-dive.md)

retrieval-anchor-keywords: SecurityContext propagation, DelegatingSecurityContextAsyncTaskExecutor, ReactiveSecurityContextHolder, context propagation, thread local security, reactive context, async boundary, reactor context

## 핵심 개념

Spring Security의 인증 정보는 기본적으로 현재 실행 컨텍스트에 붙는다.

- MVC/서블릿: thread-local 기반 SecurityContextHolder
- Reactive: Reactor context 기반 ReactiveSecurityContextHolder
- Async: executor thread로 넘어가며 별도 전파가 필요

즉, SecurityContext는 "전역 상태"가 아니라 **실행 모델에 따라 다른 컨텍스트 계약**이다.

## 깊이 들어가기

### 1. 서블릿 모델은 thread-local에 익숙하다

MVC에서는 요청당 스레드가 일정해서 `SecurityContextHolder`가 자연스럽다.

하지만 `@Async`를 쓰면 다른 스레드에서 실행되므로 자동 전파가 깨질 수 있다.

### 2. reactive 모델은 Reactor context를 쓴다

WebFlux에서는 인증 정보가 리액티브 체인에 붙는다.

```java
ReactiveSecurityContextHolder.getContext()
```

이건 thread-local이 아니라 context propagation 기반이다.

### 3. async 경계에서는 데코레이터나 래퍼가 필요하다

```java
@Bean
public AsyncTaskExecutor applicationTaskExecutor() {
    return new DelegatingSecurityContextAsyncTaskExecutor(new ThreadPoolTaskExecutor());
}
```

이런 래퍼가 있어야 SecurityContext가 새 스레드로 복사된다.

### 4. reactive와 blocking을 섞으면 더 복잡해진다

WebFlux 안에서 blocking code를 호출하거나, MVC에서 reactive chain을 잘못 block하면 컨텍스트 전파와 스레드 경계가 꼬인다.

이 문맥은 [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)와 같이 봐야 한다.

### 5. method security도 같은 문제를 공유한다

보안 메서드 수준 검증은 proxy와 context에 의존한다.

이건 [Spring Security Method Security Deep Dive](./spring-security-method-security-deep-dive.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: `@Async` 안에서 인증 정보가 사라진다

원인은 실행 스레드가 바뀌었기 때문이다.

### 시나리오 2: WebFlux에서 인증이 어떤 연산에서는 보이고 어떤 연산에서는 안 보인다

Reactor context가 체인에 제대로 전달되지 않았을 수 있다.

### 시나리오 3: 배경 작업에서 사용자 권한이 필요하다

요청 시점의 SecurityContext를 명시적으로 복사하거나, 아예 필요한 사용자 정보를 파라미터로 전달해야 한다.

### 시나리오 4: thread-local 기반 코드를 reactive 경로에 그대로 옮겼다

이건 보안 정보뿐 아니라 MDC, request scope, transaction context까지 연쇄적으로 깨질 수 있다.

## 코드로 보기

### async executor wrapper

```java
@Bean
public AsyncTaskExecutor asyncTaskExecutor() {
    ThreadPoolTaskExecutor delegate = new ThreadPoolTaskExecutor();
    delegate.initialize();
    return new DelegatingSecurityContextAsyncTaskExecutor(delegate);
}
```

### reactive context access

```java
Mono<String> currentUser = ReactiveSecurityContextHolder.getContext()
    .map(context -> context.getAuthentication().getName());
```

### manual propagation idea

```java
Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| thread-local holder | 단순하다 | async/reactive에 약하다 | MVC |
| async security wrapper | 편리하다 | 래퍼 구성이 필요하다 | background task |
| Reactor context | reactive에 맞다 | 학습 비용이 있다 | WebFlux |
| 명시적 파라미터 전달 | 가장 분명하다 | 호출 체인이 길어진다 | 중요한 작업 |

핵심은 SecurityContext를 "자동으로 따라오는 것"으로 보지 말고, **실행 모델마다 다른 전파 규칙이 있는 상태**로 보는 것이다.

## 꼬리질문

> Q: `SecurityContextHolder`와 `ReactiveSecurityContextHolder`의 차이는 무엇인가?
> 의도: 서블릿/리액티브 컨텍스트 구분 확인
> 핵심: 전자는 thread-local, 후자는 Reactor context다.

> Q: `@Async`에서 SecurityContext가 사라지는 이유는 무엇인가?
> 의도: thread boundary 이해 확인
> 핵심: 다른 스레드에서 실행되기 때문이다.

> Q: WebFlux에서 인증 정보를 읽을 때 무엇을 써야 하는가?
> 의도: reactive security 이해 확인
> 핵심: `ReactiveSecurityContextHolder`를 쓴다.

> Q: security context를 명시적으로 전달하는 것이 언제 더 나은가?
> 의도: boundary 설계 이해 확인
> 핵심: 중요한 배경 작업이나 복잡한 경로에서는 명시 전달이 안전하다.

## 한 줄 정리

SecurityContext는 async와 reactive boundary를 넘으며 자동 전파되지 않으므로, 실행 모델에 맞는 전파 전략을 명시해야 한다.
