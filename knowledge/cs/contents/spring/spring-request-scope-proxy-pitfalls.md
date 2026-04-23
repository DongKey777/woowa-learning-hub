# Spring Request Scope Proxy Pitfalls

> 한 줄 요약: request scope는 웹 요청과 함께 살아가는 상태를 담는 도구지만, proxy와 thread boundary를 잘못 이해하면 가장 안전해야 할 컨텍스트가 가장 빨리 사라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Spring `RequestContextHolder`, `ThreadLocal`, and Request Context Leakage Across Async Pools](./spring-requestcontextholder-threadlocal-leakage-async-pools.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)

retrieval-anchor-keywords: request scope, scoped proxy, proxyMode, thread boundary, request attribute, WebApplicationContext, ObjectProvider, scope proxy, async request scope, RequestContextHolder, ThreadLocal leak

## 핵심 개념

`request` scope는 HTTP 요청마다 새로운 객체를 만든다.

이 scope는 유용하지만, 직접 주입하면 언제 생성되는지 오해하기 쉽다.

- 요청마다 새 객체다
- 그러나 singleton에 바로 넣으면 주입 시점이 문제다
- thread boundary를 넘기면 사라질 수 있다

즉, request scope는 "요청과 함께 살아가는 상태"를 담는 것이지, 아무 데나 넣는 컨텍스트가 아니다.

## 깊이 들어가기

### 1. request scope는 servlet request에 묶인다

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_REQUEST, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestUserContext {
}
```

이 객체는 요청이 올 때 생성되고, 요청이 끝나면 사라진다.

### 2. scoped proxy가 싱글톤 주입을 가능하게 한다

singleton 서비스에 request scope 객체를 넣고 싶으면 proxy가 대신 들어간다.

```java
@Service
public class AuditService {

    private final RequestUserContext requestUserContext;

    public AuditService(RequestUserContext requestUserContext) {
        this.requestUserContext = requestUserContext;
    }
}
```

이때 실제 객체는 proxy 뒤에서 요청마다 달라진다.

### 3. proxy를 잘못 이해하면 디버깅이 어렵다

- `getClass()`가 예상과 다르다
- 실제 request object가 아니라 proxy만 보인다
- 초기화 시점과 요청 시점이 다르다

### 4. async/thread pool 경계에서 request scope는 깨진다

`@Async`나 별도 executor로 넘기면 request context가 사라질 수 있다.

이 문맥은 [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)와 같다.

### 5. request scope는 상태를 보관하지, 소유권을 바꾸지 않는다

request scope는 편리하지만, 요청 외부로 전달될 대상은 아니다.

- 배치
- 비동기 작업
- 메시지 큐

이런 곳에 넘기면 구조가 꼬인다.

## 실전 시나리오

### 시나리오 1: request scope를 singleton에 주입했더니 에러가 난다

대개 scoped proxy가 없거나, bean 정의가 잘못된 경우다.

### 시나리오 2: request scope 값을 async 작업에서 읽으려 했다

thread boundary를 넘어갔기 때문에 사라질 수 있다.

### 시나리오 3: 요청 로깅용 context를 request scope에 넣었다

이건 자연스럽지만, 너무 많은 정보를 넣으면 HTTP 요청과 service 로직이 강하게 결합된다.

### 시나리오 4: request scope와 session scope를 혼동했다

request는 한 번의 요청, session은 여러 요청에 걸친 저장이다.

## 코드로 보기

### request scope bean

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_REQUEST, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestContextHolder {
    private String requestId;
}
```

### singleton 서비스에서 사용

```java
@Service
public class LoggingService {
    private final RequestContextHolder requestContextHolder;

    public LoggingService(RequestContextHolder requestContextHolder) {
        this.requestContextHolder = requestContextHolder;
    }
}
```

### 안전한 명시적 조회

```java
@Service
public class SafeService {
    private final ObjectProvider<RequestContextHolder> provider;

    public SafeService(ObjectProvider<RequestContextHolder> provider) {
        this.provider = provider;
    }

    public void handle() {
        RequestContextHolder context = provider.getObject();
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| request scope + proxy | 주입이 편하다 | 실제 객체가 숨는다 | 웹 요청별 컨텍스트 |
| ObjectProvider 조회 | 의도가 명확하다 | 코드가 길어진다 | scope 객체를 명시적으로 가져올 때 |
| ThreadLocal | 접근이 쉽다 | thread boundary에 약하다 | 매우 제한적 컨텍스트 |
| 파라미터 전달 | 가장 명시적이다 | 호출 체인이 길어질 수 있다 | 핵심 context 전달 |

핵심은 request scope를 쓰는 것이 아니라, **요청 상태를 어디까지 허용할지**다.

## 꼬리질문

> Q: request scope와 singleton 주입을 같이 쓰려면 무엇이 필요한가?
> 의도: scoped proxy 이해 확인
> 핵심: proxyMode나 ObjectProvider가 필요하다.

> Q: request scope가 async 작업에서 깨질 수 있는 이유는 무엇인가?
> 의도: thread boundary 이해 확인
> 핵심: 요청 스레드와 실행 스레드가 다르기 때문이다.

> Q: request scope와 session scope의 차이는 무엇인가?
> 의도: 웹 상태 범위 이해 확인
> 핵심: request는 한 번의 요청, session은 세션 수명이다.

> Q: scoped proxy가 디버깅을 어렵게 만드는 이유는 무엇인가?
> 의도: proxy visibility 이해 확인
> 핵심: 실제 객체 대신 proxy가 보이기 때문이다.

## 한 줄 정리

Request scope는 요청별 상태를 안전하게 분리하는 도구지만, proxy와 thread boundary를 모르고 쓰면 가장 빨리 사라지는 컨텍스트가 된다.
