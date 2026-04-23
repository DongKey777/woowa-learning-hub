# Spring `RequestContextHolder`, `ThreadLocal`, and Request Context Leakage Across Async Pools

> 한 줄 요약: 요청 컨텍스트는 요청 스레드에 붙어 있다는 가정 위에서 안전한데, thread pool과 async 경계를 넘기며 `ThreadLocal`이나 `RequestContextHolder`를 잘못 복사하면 "사라짐"보다 더 위험한 "다른 요청 정보가 남아 있음" 문제가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring SecurityContext Propagation Across Async and Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](./spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)

retrieval-anchor-keywords: RequestContextHolder, RequestAttributes, ThreadLocal leak, inheritable thread local, request context leakage, async pool contamination, stale request context, request-scoped data leak

## 핵심 개념

요청 컨텍스트를 다룰 때 많은 문서는 "async로 넘기면 사라진다"까지는 말해 준다.

하지만 운영에서 더 위험한 문제는 반대다.

- 사라지는 것보다
- 이전 요청의 컨텍스트가 남아 있는 것

즉 request context 문제의 핵심은 단순 null이 아니라, **thread pool 재사용으로 다른 요청의 `ThreadLocal` 상태가 새 요청에 섞이는 오염**이다.

이 문맥에서 중요한 것은 다음이다.

- `RequestContextHolder`
- custom `ThreadLocal`
- `LocaleContextHolder`
- MDC
- SecurityContext

이들은 모두 "현재 실행 컨텍스트"를 가정하지만, thread pool은 그 가정을 쉽게 깨뜨린다.

## 깊이 들어가기

### 1. `ThreadLocal`은 요청 수명 주기가 아니라 스레드 수명 주기를 따른다

이게 출발점이다.

웹 요청은 짧지만, pool thread는 오래 산다.

그래서 `ThreadLocal` 값을 넣고 확실히 비우지 않으면 다음이 가능하다.

- 요청 A가 thread-1에서 실행
- `ThreadLocal` 값 설정
- cleanup 누락
- 나중에 요청 B도 thread-1 재사용
- 요청 A의 컨텍스트가 요청 B에 보임

즉 leak는 메모리 누수만이 아니라, **논리적 데이터 오염**이다.

### 2. `RequestContextHolder`도 안전지대가 아니다

Spring은 request 처리 중 `RequestContextHolder`에 현재 request attributes를 묶는다.

이걸 직접 읽거나 복사해서 async로 넘기기 시작하면 위험해진다.

- lifecycle이 끝난 request를 나중에 참조할 수 있다
- 잘못 복사된 attributes가 다른 작업에 남을 수 있다
- pool thread 재사용으로 stale context가 보일 수 있다

즉 "request context를 async에서도 계속 쓰고 싶다"는 생각 자체가 종종 잘못된 설계 신호다.

### 3. `InheritableThreadLocal`은 새 thread엔 편해 보여도 pool과는 잘 안 맞는다

가끔 `InheritableThreadLocal`로 해결하려는 시도가 있다.

하지만 thread pool 환경에선 새로 thread를 매번 만들지 않으므로 직관과 다르게 동작하기 쉽다.

- 한 번 상속된 값이 오래 남을 수 있다
- pool 재사용과 섞이면 누가 누구 값을 물려받았는지 추적이 어렵다

즉 request context 전파를 위해 `InheritableThreadLocal`을 기본 해법으로 택하는 건 보통 위험하다.

### 4. 복사보다 "필요한 값만 명시적으로 추출"하는 편이 안전하다

요청 컨텍스트 전체를 들고 가려 하지 말고,
정말 필요한 데이터만 추출해서 immutable 값으로 넘기는 편이 좋다.

예:

- request ID
- user ID
- locale code
- tenant ID

이 방식의 장점:

- 요청 수명 주기와 분리된다
- stale request reference를 막기 쉽다
- 테스트와 디버깅이 쉬워진다

핵심은 context object 전파보다, **업무에 필요한 최소 식별자만 명시적으로 전달**하는 것이다.

### 5. 복사가 필요하다면 반드시 try/finally cleanup이 있어야 한다

MDC나 SecurityContext처럼 복사가 필요한 경우도 있다.

그럴 때는 다음이 중요하다.

- 실행 전 설정
- 실행 후 무조건 clear
- nested task일 때 restore 기준 명확화

즉 context propagation의 본질은 복사가 아니라, **설정과 정리를 쌍으로 갖는 것**이다.

### 6. request-scoped bean을 background 작업에 직접 넘기면 더 빨리 꼬인다

request-scoped proxy를 async 작업에 넘기면 다음 문제가 생긴다.

- 현재 request가 끝난 뒤 접근 실패
- proxy 뒤 실제 request object가 이미 사라짐
- 디버깅 시 proxy class만 보여 더 헷갈림

이 경우는 전파 기술이 부족한 것이 아니라, **요청 전용 상태를 요청 밖으로 가져간 설계** 자체가 문제일 가능성이 높다.

## 실전 시나리오

### 시나리오 1: 간헐적으로 다른 사용자의 request ID가 로그에 찍힌다

MDC/ThreadLocal cleanup 누락을 의심해야 한다.

이건 null보다 훨씬 위험한 오염 신호다.

### 시나리오 2: async 작업에서 RequestContextHolder가 어떤 때는 보이고 어떤 때는 null이다

worker thread 재사용 시점과 복사/cleanup 누락 여부가 섞였을 수 있다.

### 시나리오 3: request-scoped bean을 비동기 알림 작업에 넘겼다

요청이 끝난 뒤 접근하거나, stale proxy reference 때문에 예측하기 어려운 오류가 날 수 있다.

### 시나리오 4: `InheritableThreadLocal`로 해결했더니 더 재현이 어려워졌다

pool thread 재사용과 상속 시점이 섞이면서 문제를 더 은폐했을 수 있다.

## 코드로 보기

### 위험한 custom ThreadLocal

```java
public final class RequestTenantHolder {
    private static final ThreadLocal<String> TENANT = new ThreadLocal<>();

    public static void set(String tenantId) {
        TENANT.set(tenantId);
    }

    public static String get() {
        return TENANT.get();
    }

    public static void clear() {
        TENANT.remove();
    }
}
```

### 최소 값만 추출해서 넘기기

```java
String requestId = request.getHeader("X-Request-Id");
Long userId = currentUser.id();
executor.execute(() -> notificationService.send(userId, requestId));
```

### 복사 + 정리 패턴

```java
Map<String, String> contextMap = MDC.getCopyOfContextMap();
executor.execute(() -> {
    try {
        if (contextMap != null) {
            MDC.setContextMap(contextMap);
        }
        task.run();
    } finally {
        MDC.clear();
    }
});
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| request context 직접 참조 | 구현이 편해 보인다 | async/pool 경계에서 쉽게 깨진다 | 요청 스레드 안에서만 |
| context 전체 복사 | 일부 연속성은 유지된다 | cleanup 누락 시 오염 위험이 크다 | MDC/Security 등 제한적 컨텍스트 |
| 최소 값 명시 전달 | 가장 안전하고 명확하다 | 코드가 조금 더 길어진다 | background/async 작업 |
| `InheritableThreadLocal` | 새 thread엔 편해 보인다 | pool 환경에선 매우 헷갈린다 | 가급적 피함 |

핵심은 request context를 "계속 유지할 상태"가 아니라, **요청 스레드 안에서만 유효한 임시 상태**로 보는 것이다.

## 꼬리질문

> Q: request context 문제에서 null보다 더 위험한 것은 무엇인가?
> 의도: stale context 오염 인식 확인
> 핵심: 이전 요청의 컨텍스트가 남아 다른 요청에 섞이는 것이다.

> Q: `ThreadLocal` cleanup 누락이 왜 thread pool에서 특히 위험한가?
> 의도: 스레드 수명 주기 이해 확인
> 핵심: pool thread가 재사용되기 때문에 오래된 값이 다음 요청으로 넘어갈 수 있기 때문이다.

> Q: `InheritableThreadLocal`이 왜 request context 전파의 기본 해법이 아닌가?
> 의도: pool과 상속 모델 차이 확인
> 핵심: thread pool 재사용 환경에서는 직관과 다르게 stale 값이 남기 쉽기 때문이다.

> Q: 가장 안전한 전파 방식은 무엇인가?
> 의도: 설계 원칙 확인
> 핵심: context object 전체가 아니라 필요한 최소 식별자만 명시적으로 전달하는 것이다.

## 한 줄 정리

요청 컨텍스트 문제의 본질은 "async에서 사라진다"보다, thread pool 재사용 속에서 예전 요청 정보가 남아 새 요청에 섞일 수 있다는 데 있다.
