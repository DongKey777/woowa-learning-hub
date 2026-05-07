---
schema_version: 3
title: "Multipart Parsing vs Auth Reject Boundary"
concept_id: network/multipart-parsing-vs-auth-reject-boundary
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- multipart-auth-reject-boundary
- spring-security-upload-body
- multipart-filter-order
aliases:
- multipart auth reject boundary
- MultipartFilter before Spring Security
- request.getParts auth boundary
- resolveLazily multipart
- header-only reject upload
- body-consuming reject upload
symptoms:
- controller 전에 401/403이 났으니 multipart body를 전혀 읽지 않았다고 단정한다
- MultipartFilter나 request.getParts가 Spring Security 전에 body-consuming boundary를 앞당기는 점을 놓친다
- resolveLazily=true가 multipart parse boundary를 없애는 것이 아니라 뒤로 미루는 것임을 구분하지 못한다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/gateway-buffering-vs-spring-early-reject
- network/http-request-body-drain-early-reject-keepalive-reuse
next_docs:
- network/spring-multipart-exception-translation-matrix
- network/proxy-to-container-upload-cleanup-matrix
- network/webflux-request-body-abort-surface-map
- spring/multipart-upload-request-pipeline
- spring/security-exceptiontranslation-entrypoint-accessdeniedhandler
linked_paths:
- contents/network/expect-100-continue-proxy-request-buffering.md
- contents/network/http-request-body-drain-early-reject-keepalive-reuse.md
- contents/network/gateway-buffering-vs-spring-early-reject.md
- contents/network/proxy-to-container-upload-cleanup-matrix.md
- contents/network/spring-multipart-exception-translation-matrix.md
- contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md
- contents/network/webflux-request-body-abort-surface-map.md
- contents/network/servlet-container-abort-surface-map-tomcat-jetty-undertow.md
- contents/spring/spring-multipart-upload-request-pipeline.md
- contents/spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md
confusable_with:
- network/gateway-buffering-vs-spring-early-reject
- network/http-request-body-drain-early-reject-keepalive-reuse
- network/proxy-to-container-upload-cleanup-matrix
- network/spring-multipart-exception-translation-matrix
- spring/multipart-upload-request-pipeline
forbidden_neighbors: []
expected_queries:
- "multipart upload에서 auth reject가 header-only인지 body-consuming인지 어떻게 가르나?"
- "MultipartFilter를 Spring Security 앞에 두면 왜 인증 전에 request body를 읽을 수 있어?"
- "DispatcherServlet checkMultipart와 request.getParts가 controller 전 multipart parse를 시작하는 흐름을 설명해줘"
- "resolveLazily=true는 multipart parsing 경계를 없애는 게 아니라 언제로 미뤄?"
- "Unauthorized temp file upload를 막으려면 filter order와 multipart resolver를 어떻게 봐?"
contextual_chunk_prefix: |
  이 문서는 Spring multipart/form-data upload에서 MultipartFilter,
  DispatcherServlet.checkMultipart, request.getParts, resolveLazily,
  Spring Security filter chain, header-only reject vs body-consuming reject
  boundary를 다루는 advanced playbook이다.
---
# Multipart Parsing vs Auth Reject Boundary

> 한 줄 요약: `multipart/form-data` 업로드는 "controller 전이냐 후냐"보다 **누가 언제 `request.getParts()` 또는 그에 준하는 multipart resolution을 강제했는가**가 더 중요하다. Spring Security filter chain 앞뒤에 `MultipartFilter`를 어디 두는지, `DispatcherServlet.checkMultipart()`가 eager parse를 하는지, `resolveLazily=true`인지에 따라 같은 `401/403`도 header-only reject에서 body-consuming reject로 경계가 이동한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
> - [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
> - [Spring Multipart Exception Translation Matrix](./spring-multipart-exception-translation-matrix.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [WebFlux Request-Body Abort Surface Map](./webflux-request-body-abort-surface-map.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [Spring Multipart Upload Request Pipeline](../spring/spring-multipart-upload-request-pipeline.md)
> - [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](../spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)

retrieval-anchor-keywords: multipart parsing vs auth reject boundary, multipart auth reject boundary, header-only reject upload, body-consuming reject upload, MultipartFilter before Spring Security, MultipartFilter after Spring Security, StandardServletMultipartResolver resolveLazily, DispatcherServlet checkMultipart, request.getParts auth boundary, multipart csrf body token, unauthorized temp file upload, multipart filter chain early reject, spring security multipart order, multipart resolution before controller

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

multipart 업로드에서 auth reject 경계는 보통 아래 순서로 움직인다.

1. **Spring Security filter chain이 header/cookie/path만 보고 막는 구간**
2. **`MultipartFilter` 또는 custom filter가 multipart/body를 먼저 읽는 구간**
3. **`DispatcherServlet.checkMultipart()`가 `MultipartResolver`를 실행하는 구간**
4. **lazy multipart wrapper가 실제 파일/파라미터 접근 시 parse를 늦게 시작하는 구간**

핵심은 간단하다.

- Spring Security가 filter에서 `401/403`을 만들더라도, 그 전에 아무도 multipart를 풀지 않았다면 app 관점에선 아직 header-only reject다
- 반대로 controller에 안 들어갔더라도 `MultipartFilter`, `request.getParts()`, eager `MultipartResolver`가 이미 돌았다면 그 reject는 이미 body-consuming reject다
- `resolveLazily=true`는 boundary를 없애지 않고 **뒤로 미룰 뿐**이다

### Retrieval Anchors

- `multipart auth reject boundary`
- `MultipartFilter before Spring Security`
- `DispatcherServlet checkMultipart`
- `request.getParts auth boundary`
- `header-only reject upload`
- `body-consuming reject upload`
- `StandardServletMultipartResolver resolveLazily`
- `unauthorized temp file upload`

## 깊이 들어가기

### 1. 경계는 "controller 전"이 아니라 "첫 multipart resolution 전"이다

같은 업로드 요청도 아래처럼 phase를 나눠야 한다.

| phase | 누가 돌고 있는가 | multipart/body 상태 | reject 성격 |
|---|---|---|---|
| filter chain 초반 | gateway / servlet filter / Spring Security | 아직 multipart 미해석 | header-only reject 가능 |
| `MultipartFilter` 실행 시점 | servlet filter | `resolveMultipart()`가 multipart wrapper를 만들며 parse 시작 가능 | body-consuming reject로 이동 |
| `DispatcherServlet.checkMultipart()` | Spring MVC servlet | default resolver면 여기서 `request.getParts()`까지 갈 수 있음 | controller 전이어도 body-consuming |
| lazy wrapper 이후 first access | interceptor / argument resolver / controller | `MultipartFile`, multipart parameter 접근 순간 parse | 그 시점부터 body-consuming |
| 응답 후 cleanup | container / resolver cleanup | temp file 삭제, unread body drain/close | reject는 끝났어도 wire cleanup은 남음 |

즉 upload auth 문제의 실제 질문은 "`401`이 언제 나갔나?"가 아니라 **"`401` 이전에 누가 body를 만졌나?"**다.

### 2. 기본 Spring MVC + Spring Security 조합에선 security reject가 먼저 올 수 있다

Spring Security의 servlet support는 `FilterChainProxy` 안의 filter들로 동작하고, Spring MVC 요청 본체는 `DispatcherServlet`이 처리한다.  
즉 일반적인 순서는:

```text
client
-> servlet filters
-> Spring Security FilterChainProxy
-> DispatcherServlet.doDispatch()
   -> checkMultipart()
   -> handler mapping
   -> interceptor / controller
```

이 기본 순서라면, 아래 조건에서는 security reject가 아직 header-only reject다.

- `MultipartFilter`를 따로 앞에 두지 않았다
- custom filter가 `request.getParts()`나 request body read를 먼저 하지 않았다
- auth / ACL / tenant 검사에 multipart body 값이 필요 없다

그래서 `AuthenticationEntryPoint`나 `AccessDeniedHandler`가 controller 전에 `401/403`을 만들어도, **그 직전까지는 multipart parse가 아직 시작되지 않았을 수 있다**.

다만 wire 관점에선 별도 문제가 남는다.

- client가 `Expect: 100-continue` 없이 body를 이미 밀어 넣고 있을 수 있다
- proxy buffering이 먼저 body를 받아 버릴 수 있다
- reject 후 unread body drain/close 정책은 여전히 필요하다

즉 app 내부 기준으로는 header-only reject여도, 네트워크 전체로는 "이미 body가 흐르는 중인 reject"일 수 있다.

### 3. `MultipartFilter`를 Spring Security 앞에 두면 경계가 filter 단계에서 body-consuming으로 당겨진다

Spring Security 문서에서 multipart body 안의 CSRF token을 읽으려면 `MultipartFilter`를 Spring Security filter보다 앞에 두라고 설명한다.  
이 배치는 효과가 분명하다.

- CSRF token을 body에서 읽을 수 있다
- Security filter가 multipart form field를 볼 수 있다

하지만 비용도 분명하다.

- 인증 전에 multipart resolution이 시작된다
- temp file / part 생성이 먼저 일어날 수 있다
- 그 뒤의 `401/403`은 이미 body-consuming reject다

다만 이 설명은 **filter 단계에서 multipart resolution이 실제로 가능한 구성**이라는 전제가 붙는다.  
Servlet spec 기준 multipart 설정은 본래 servlet 쪽에 붙기 때문에, `MultipartFilter` 경로는 container workaround나 filter용 resolver 구성이 필요한 경우가 있다.  
즉 설정이 성립하면 boundary가 앞당겨지고, 설정이 성립하지 않으면 경계는 다시 `DispatcherServlet` 쪽으로 남는다.

정리하면:

```text
MultipartFilter before security
-> multipart parse or temp spool
-> Spring Security reject
```

이때 "Security가 controller 전에 막았다"는 말은 맞지만, "header만 보고 막았다"는 뜻은 아니다.

### 4. `DispatcherServlet.checkMultipart()`는 controller보다 앞이지만, security보다 뒤다

Spring MVC에서 `DispatcherServlet.doDispatch()`는 handler lookup 전에 `checkMultipart(request)`를 호출한다.  
그리고 `StandardServletMultipartResolver`의 기본값은 eager parse다.

- `resolveMultipart()`는 `StandardMultipartHttpServletRequest(request, false)`를 만든다
- 이 wrapper는 기본값에서 생성 시점에 `parseRequest()`를 호출한다
- `parseRequest()`는 결국 `request.getParts()`를 호출한다

그래서 아래 reject들은 controller 미진입이어도 이미 body-consuming reject일 수 있다.

- `HandlerInterceptor.preHandle()`에서 리턴한 `401/403`
- argument resolver 이전의 custom MVC reject
- multipart parse 실패를 감싼 `MultipartException`
- size limit를 감싼 `MaxUploadSizeExceededException`

즉 "controller가 안 탔다"는 사실만으로 header-only reject라고 결론 내리면 안 된다.  
eager multipart resolver가 있으면 **Spring MVC 진입 직후 이미 multipart body를 읽기 시작했을 수 있다**.

반대로 request가 이미 `MultipartHttpServletRequest`로 감싸진 상태라면, `DispatcherServlet`은 "이미 resolved"된 요청으로 보고 다시 multipart resolution을 시작하지 않는다.  
즉 `MultipartFilter`가 먼저 성공한 구성에서는 boundary가 이미 filter 단계로 이동한 것이다.

### 5. `resolveLazily=true`는 경계를 뒤로 미루지만, body-dependent decision이면 결국 소비된다

`StandardServletMultipartResolver#setResolveLazily(true)`를 켜면 `checkMultipart()` 시점엔 wrapper만 만들고 즉시 parse하지 않는다.  
실제 parse는 multipart 파일이나 파라미터에 처음 접근할 때 시작된다.

이 설정이 주는 변화:

- Spring Security filter reject는 여전히 header-only reject로 남기기 쉽다
- header만 보는 `HandlerInterceptor`라면 body-consuming 이전에 막을 수 있다
- 반대로 `@RequestPart`, `MultipartFile`, multipart parameter 접근이 시작되면 그 시점부터 reject는 body-consuming으로 변한다

따라서 lazy parse에서 중요한 질문은 이것이다.

- reject 로직이 multipart body를 읽기 전에 끝나는가
- 아니면 form field/file metadata 확인이 필요해 결국 parse를 트리거하는가

`resolveLazily=true`는 "항상 header-only reject"가 아니라, **body 접근 전까지 유예하는 장치**다.

### 6. body를 직접 읽는 custom filter는 경계를 가장 먼저 깨뜨린다

Spring 공식 multipart 컴포넌트가 아니어도 아래 코드는 경계를 앞당긴다.

- security 이전 custom filter가 `request.getParts()`를 직접 호출
- logging/inspection filter가 실제 `ServletInputStream`을 읽음
- virus scan / DLP filter가 request body를 먼저 흡수

이 경우 Spring Security가 그 뒤에 `401/403`을 반환하더라도 이미 reject는 body-consuming reject다.  
즉 "누가 multipart resolver를 썼는가"보다 **누가 request body를 최초 소비했는가**를 먼저 봐야 한다.

### 7. 실무에선 `Expect: 100-continue`와 proxy buffering이 app boundary를 덮어쓴다

app 안에서 header-only reject가 가능해도 wire 절약이 자동으로 따라오진 않는다.

- client가 body를 기다리지 않고 바로 보낼 수 있다
- ingress/gateway가 request buffering으로 body를 먼저 받을 수 있다
- reject 후 connection reuse를 위해 unread body를 drain할 수 있다

그래서 upload incident를 해석할 때는 아래 두 축을 분리해야 한다.

- **app boundary**: Spring Security / MultipartFilter / DispatcherServlet 중 누가 body consumption을 시작했는가
- **wire boundary**: gateway와 client 사이에서 실제 몇 바이트가 이미 흘렀는가

app 쪽 header-only reject와 edge 쪽 "이미 2GB 업로드됨"은 동시에 참일 수 있다.

### 8. 가장 유용한 triage 질문은 네 개면 충분하다

1. `MultipartFilter`가 Spring Security 앞에 있는가 뒤에 있는가
2. `DispatcherServlet`의 multipart resolver가 eager인가 lazy인가
3. reject 주체가 security filter인가, interceptor인가, argument binding 이후인가
4. edge/proxy가 이미 body를 buffering했는가, reject 후 drain/close를 했는가

이 네 가지가 고정되면, 같은 `401/403/413`도 header-only reject인지 body-consuming reject인지 거의 바로 분류된다.

## 실전 시나리오

### 시나리오 1: `401`은 5ms인데 unauthorized temp file이 남는다

가장 먼저 의심할 것은 `MultipartFilter`가 security 앞에 있는 구성이다.

- CSRF token을 body에서 읽기 위해 multipart를 먼저 풀었을 수 있다
- app auth latency는 짧아도 reject는 이미 body-consuming이다

### 시나리오 2: controller는 안 탔는데 `MultipartException`과 `403`이 같이 보인다

`DispatcherServlet.checkMultipart()`가 eager parse를 먼저 수행했을 수 있다.

- controller 미진입
- interceptor 또는 exception translation에서 reject/에러 처리
- 하지만 body는 이미 `request.getParts()` 단계에서 읽혔다

### 시나리오 3: 어떤 요청은 header-only reject인데 어떤 요청은 같은 endpoint에서 body-consuming reject다

흔한 원인:

- `resolveLazily=true`
- 어떤 코드 경로는 header만 보고 막음
- 어떤 코드 경로는 multipart parameter/file 접근 후 막음

즉 endpoint가 같아도 **첫 multipart access 여부**에 따라 경계가 달라질 수 있다.

### 시나리오 4: Spring은 security filter에서 `401`, edge는 upload bytes가 크다

app boundary와 wire boundary를 혼동한 경우다.

- app에서는 multipart parse 이전 reject였을 수 있다
- 하지만 gateway buffering이나 client eager send 때문에 network에선 이미 body가 들어왔다
- 이후 drain/close 때문에 request time과 keep-alive reuse가 흔들릴 수 있다

## 코드로 보기

### boundary map

```text
A. Spring Security before multipart
client
-> filters
-> SecurityFilterChain
-> 401/403
== app-level header-only reject 가능

B. MultipartFilter before Spring Security
client
-> MultipartFilter(resolveMultipart)
-> request.getParts()/temp files
-> SecurityFilterChain
-> 401/403
== body-consuming reject

C. DispatcherServlet eager multipart
client
-> SecurityFilterChain 통과
-> DispatcherServlet.checkMultipart()
-> request.getParts()
-> interceptor/controller reject
== controller 전이어도 body-consuming reject

D. DispatcherServlet lazy multipart
client
-> SecurityFilterChain 통과
-> DispatcherServlet.checkMultipart() wrapper only
-> first MultipartFile / multipart parameter access
-> reject
== first access 전까진 header-only 가능
```

### `MultipartFilter`를 security 앞에 두는 구성

```java
@Override
protected void beforeSpringSecurityFilterChain(ServletContext servletContext) {
    insertFilters(servletContext, new MultipartFilter());
}
```

이 구성은 body 안의 CSRF token을 읽을 수 있게 하지만, 인증 전에 multipart temp storage가 생길 수 있다.

### lazy multipart resolver 예시

```java
@Bean
MultipartResolver multipartResolver() {
    StandardServletMultipartResolver resolver = new StandardServletMultipartResolver();
    resolver.setResolveLazily(true);
    return resolver;
}
```

이 설정은 parse 시점을 늦추지만, 이후 `MultipartFile`이나 multipart parameter에 접근하는 순간 boundary가 다시 body-consuming으로 넘어간다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| security filter에서 header-only reject 유지 | unauthorized upload를 body parse 전에 끊기 쉽다 | body 안의 token/form field에 의존한 보안 검사는 어렵다 | auth가 header/cookie/path만으로 끝나는 업로드 API |
| `MultipartFilter`를 security 앞에 둠 | multipart body field를 security에서 읽을 수 있다 | unauthorized temp file과 body-consuming reject를 감수해야 한다 | multipart body 안의 CSRF token을 꼭 읽어야 하는 경우 |
| eager multipart resolver | parse failure와 size 문제를 일찍 surface한다 | interceptor/controller 전 reject도 이미 body-consuming이 된다 | 전형적인 Spring MVC multipart |
| lazy multipart resolver | header-only reject 구간을 더 뒤로 미룬다 | 예외 시점이 늦어지고 code path마다 boundary가 달라진다 | header 기반 reject를 최대한 늦게까지 유지하고 싶은 경우 |

핵심은 "어디서 인증하나"보다 **"어디서 multipart를 최초 해석하나"**를 먼저 고정하는 것이다.

## 꼬리질문

> Q: Spring Security가 controller 전에 `401`을 만들면 항상 header-only reject인가요?
> 핵심: 아니다. 그 전에 `MultipartFilter`나 custom filter가 body를 읽었다면 이미 body-consuming reject다.

> Q: controller에 안 들어갔는데 왜 body-consuming reject가 되나요?
> 핵심: `DispatcherServlet.checkMultipart()`의 eager parse가 handler mapping보다 먼저 `request.getParts()`를 호출할 수 있기 때문이다.

> Q: `resolveLazily=true`면 multipart upload가 항상 body를 안 읽고 막히나요?
> 핵심: 아니다. 첫 multipart 파일/파라미터 접근 전까지만 유예될 뿐이다.

> Q: edge에서 upload bytes가 큰데 app은 security filter reject라면 누가 body를 읽은 건가요?
> 핵심: app boundary에선 아무도 안 읽었을 수 있고, gateway buffering이나 client eager send가 wire boundary를 이미 넘겼을 수 있다.

## 한 줄 정리

multipart upload의 auth reject 경계는 status code가 아니라 **`MultipartFilter`/`request.getParts()`/`checkMultipart()` 중 누가 먼저 body 해석을 시작했는가**로 결정되며, 그 순간부터 같은 `401/403`도 header-only reject가 아니라 body-consuming reject가 된다.
