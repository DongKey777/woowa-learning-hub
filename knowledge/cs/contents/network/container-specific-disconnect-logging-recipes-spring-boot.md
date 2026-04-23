# Container-Specific Disconnect Logging Recipes for Spring Boot

> 한 줄 요약: Spring Boot에서 client abort 노이즈를 줄이려면 root logger를 내리지 말고, 공통 app-side disconnect category 하나와 container별 narrow logger category 하나만 다뤄야 한다. Tomcat은 `DisconnectedClientHelper` + `org.apache.coyote` guardrail, Jetty는 `org.eclipse.jetty.io` vs `org.eclipse.jetty.server`, Undertow는 `io.undertow.request.io` vs `io.undertow.request` 분리가 핵심이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md)
> - [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
> - [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [Spring Servlet Container Disconnect Exception Mapping](../spring/spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](../spring/spring-problemdetail-before-after-commit-matrix.md)

retrieval-anchor-keywords: spring boot disconnect logging, container-specific disconnect logging recipe, client abort logging category, late write regression guardrail, disconnectedclienthelper, disconnectedclienthelper code example, mvc download disconnect breadcrumb, sse disconnect breadcrumb, async late write breadcrumb, tomcat clientabortexception logging, tomcat coyote logging, org.apache.coyote late write, jetty quietexception logging, org.eclipse.jetty.io eofexception, org.eclipse.jetty.server late write, undertow request io logger, io.undertow.request.io, io.undertow.request, loggingexceptionhandler undertow, asyncrequestnotusableexception logging, access log disconnect recipe, access log correlation recipe, tomcat jetty undertow access log, bytes sent duration disconnect bucket, broken pipe logging recipe

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

client abort를 조용히 만들고 싶다고 해서 container namespace 전체를 내리면 안 된다.  
실무에서는 아래 세 축을 분리해야 late-write regression을 안 놓친다.

- access log: status, bytes, duration으로 "실제로 얼마나 나갔는가"를 남긴다
- app-side disconnect category: Spring의 `DisconnectedClientHelper`로 expected disconnect를 한 줄 DEBUG/TRACE bucket으로 보낸다
- container request/protocol category: commit 후 write failure, protocol finish error, error-page generation 실패 같은 진짜 회귀 신호를 남긴다

| 축 | 권장 역할 | 왜 따로 둬야 하나 |
|---|---|---|
| `app.http.disconnect` 같은 전용 category | expected client abort를 한 줄 breadcrumb로 축소 | Tomcat `ClientAbortException`, Jetty `EofException`, Spring `AsyncRequestNotUsableException`, `broken pipe`/`connection reset` 메시지를 한 bucket으로 묶기 쉽다 |
| container의 quiet I/O category | request-read abort, quiet EOF, channel close noise만 분리 | quiet path만 낮추고 request/protocol logger는 살릴 수 있다 |
| container request/protocol category | late write, response finish, parse/commit 회귀를 계속 보이게 유지 | blanket suppression보다 회귀 탐지가 훨씬 안전하다 |

### Retrieval Anchors

- `spring boot disconnect logging`
- `client abort logging category`
- `late write regression guardrail`
- `disconnectedclienthelper`
- `tomcat coyote logging`
- `jetty quietexception logging`
- `undertow request io logger`
- `asyncrequestnotusableexception logging`

## 깊이 들어가기

### 1. 공통 baseline은 app-side disconnect category부터 깔아야 한다

Spring 6.1+의 `DisconnectedClientHelper`는 disconnected client로 보이는 예외를 감지해:

- DEBUG에서는 한 줄로만 남기고
- TRACE에서만 full stacktrace를 남긴다

이 helper는 `ClientAbortException`, `EOFException`, `EofException`, `AsyncRequestNotUsableException`, `broken pipe`, `connection reset by peer` 같은 shape를 같이 본다.  
즉 container별 예외 이름 차이를 app-side에서 1차 정규화할 수 있다.

공통 baseline은 대체로 아래 형태가 안전하다.

```yaml
logging:
  level:
    app.http.disconnect: DEBUG
    org.springframework.web.context.request.async: INFO
```

- `app.http.disconnect=DEBUG`
  `DisconnectedClientHelper` breadcrumb를 한 줄로 남기고 싶을 때
- `app.http.disconnect=INFO`
  access log와 metrics만으로 충분해 per-request breadcrumb도 끄고 싶을 때
- `org.springframework.web.context.request.async`
  `AsyncRequestNotUsableException` 같은 2차 late-write signal을 아예 묻지 않기 위한 guardrail

여기서 핵심은 **노이즈 감축을 helper category로 먼저 처리하고, container category는 좁게 만지는 것**이다.

예시에서는 package-level logger를 기본값으로 쓴다.  
internal class logger는 major version마다 이름이나 경로가 바뀔 수 있으므로, `org.apache.coyote.http11.Http11Processor` 같은 class-level category는 **일시 drilldown**에만 쓰고 상시 baseline은 package 단위로 두는 편이 안전하다.

Spring 6.1 미만이라 `DisconnectedClientHelper`가 없다면, 같은 `app.http.disconnect` category를 유지한 채 filter / `@ControllerAdvice` / streaming callback에서 예외 이름과 message를 직접 분류하는 방식으로 대체하면 된다.

### 2. Tomcat recipe: `org.apache.coyote`는 guardrail로 남기고, 소음 감축은 app-side에서 한다

Tomcat 쪽 함정은 `ClientAbortException`이 connector buffer에서 throw되지만, request/response finish 쪽 진짜 회귀 신호는 `org.apache.coyote` 경로에 남는다는 점이다.

- `ClientAbortException` 자체는 `org.apache.catalina.connector` dialect다
- request/response finish 문제는 `org.apache.coyote.http11.Http11Processor` / `AbstractProcessor` 쪽 log로 이어질 수 있다
- 그래서 `org.apache.coyote`를 통째로 `ERROR`/`OFF`로 낮추면 late-write 회귀를 같이 가린다

Tomcat에선 Undertow처럼 "이 category만 낮추면 quiet I/O만 빠진다"는 공식 split가 약하다.  
그래서 실전 recipe는 다음 순서가 안전하다.

| 목적 | 권장 category | 해석 |
|---|---|---|
| expected disconnect breadcrumb | `app.http.disconnect` | `DisconnectedClientHelper`로 `ClientAbortException`과 `broken pipe`를 한 줄 DEBUG로 축소 |
| protocol / finish guardrail | `org.apache.coyote` | request finish, response finish, protocol-level 회귀는 계속 보이게 둔다 |
| 일시 drilldown | `org.apache.catalina.connector`, `org.apache.coyote.http11` | upload/read path나 finish path를 볼 때만 좁게 DEBUG로 올린다 |

```yaml
logging:
  level:
    app.http.disconnect: DEBUG
    org.apache.coyote: WARN
    org.apache.catalina.connector: INFO
server:
  tomcat:
    accesslog:
      enabled: true
```

Tomcat에서는 "noise suppression"보다 "guardrail 유지"가 더 중요하다.  
과하게 줄이고 싶으면 `org.apache.catalina` 전체를 내리지 말고, app-side category만 `INFO`로 올려 breadcrumb를 끄는 편이 안전하다.

### 3. Jetty recipe: `org.eclipse.jetty.io`를 noise bucket으로, `org.eclipse.jetty.server`를 regression bucket으로 본다

Jetty의 `EofException`은 `EOFException` 하위 타입이면서 `QuietException`을 구현한다.  
Jetty 문서도 이 예외가 **connection EOF를 구분하기 위한 전용 타입이고, 덜 장황하게 로그하기 위한 목적**이라고 명시한다.

그래서 Jetty에선 다음 분리가 자연스럽다.

| 목적 | 권장 category | 해석 |
|---|---|---|
| quiet EOF / disconnect noise | `org.eclipse.jetty.io` | `EofException` 계열 bucket |
| handler/commit/write 회귀 | `org.eclipse.jetty.server` | server-side failure와 lifecycle 문제 guardrail |
| 일시 drilldown | `org.eclipse.jetty.io`만 DEBUG | whole `org.eclipse.jetty.server`를 DEBUG로 올리면 noise가 너무 커진다 |

```yaml
logging:
  level:
    app.http.disconnect: DEBUG
    org.eclipse.jetty.io: WARN
    org.eclipse.jetty.server: WARN
server:
  jetty:
    accesslog:
      enabled: true
```

Jetty에서 가장 흔한 실수는 `org.eclipse.jetty.server=ERROR` 또는 `OFF`로 내리면서 `EofException` noise를 잡았다고 착각하는 것이다.  
그러면 quiet EOF뿐 아니라 response lifecycle regression까지 같이 사라진다.  
Jetty는 **`org.eclipse.jetty.io`만 손대고 `org.eclipse.jetty.server`는 guardrail로 남기는 방식**이 더 안전하다.

### 4. Undertow recipe: 공식 `REQUEST_IO_LOGGER` split를 그대로 활용한다

Undertow는 세 container 중 logging split가 가장 명확하다.

- `io.undertow.request.io`
  `UndertowLogger.REQUEST_IO_LOGGER`
- `io.undertow.request`
  `UndertowLogger.REQUEST_LOGGER`

그리고 기본 `LoggingExceptionHandler`는:

- `IOException`은 `REQUEST_IO_LOGGER` debug로 낮춰 로그하고
- 그 외 request exception은 `REQUEST_LOGGER`로 보낸다

즉 Undertow는 아예 공식적으로 "malicious or noisy remote client가 I/O exception으로 로그를 채우기 쉬우니 lower level로 둔다"는 설계를 갖고 있다.

| 목적 | 권장 category | 해석 |
|---|---|---|
| request-read abort / quiet channel close noise | `io.undertow.request.io` | Undertow가 공식적으로 분리한 quiet I/O bucket |
| error page / request handling / late write 회귀 | `io.undertow.request` | quiet I/O와 분리된 request failure bucket |
| 일시 drilldown | `io.undertow.request.io`만 DEBUG | read-side disconnect만 보고 싶을 때 가장 좁다 |

```yaml
logging:
  level:
    app.http.disconnect: DEBUG
    io.undertow.request.io: WARN
    io.undertow.request: WARN
server:
  undertow:
    accesslog:
      enabled: true
```

Undertow에서 `io.undertow.request`까지 같이 낮추면 `UT010029`, error-page generation failure, request handling failure 같은 회귀 신호를 잃기 쉽다.  
따라서 Undertow는 **`request.io`만 noise bucket, `request`는 guardrail**로 기억하면 된다.

### 5. late-write regression을 가리지 않으려면 아래 4개는 남겨야 한다

| 남겨야 하는 것 | 이유 |
|---|---|
| access log | `200`처럼 보여도 bytes가 덜 나갔는지, `499`와 같이 움직였는지 확인할 수 있다 |
| `org.springframework.web.context.request.async` | `AsyncRequestNotUsableException`은 commit 후 2차 write 시도를 알려 주는 Spring-side signal이다 |
| Tomcat의 `org.apache.coyote` / Jetty의 `org.eclipse.jetty.server` / Undertow의 `io.undertow.request` | request/protocol/commit regression bucket이다 |
| route별 disconnect ratio + latency | single exception count는 정상 취소와 회귀를 구분하지 못한다 |

운영 판단은 보통 아래처럼 해야 한다.

- `app.http.disconnect`만 늘고 latency/TTFB가 안정적
  정상 취소나 reconnect noise 후보
- `app.http.disconnect`와 access log cancel이 같이 늘지만 container guardrail category는 잠잠
  benign client abort 가능성 높음
- container guardrail category와 `AsyncRequestNotUsableException`, latency, bytes-sent anomaly가 같이 증가
  late-write regression 또는 response commit 이후 낭비 work 의심

## 실전 시나리오

### 시나리오 1: Tomcat download API에서 `ClientAbortException` stacktrace가 너무 많다

Tomcat은 exception 이름이 선명해서 오히려 app logger에 full stacktrace가 쉽게 남는다.

- `DisconnectedClientHelper`를 `app.http.disconnect`에 붙여 한 줄 DEBUG breadcrumb로 축소한다
- `org.apache.coyote`는 내리지 않는다
- access log의 bytes/duration과 같이 봐서 실제 late-write 회귀가 아닌지 확인한다

### 시나리오 2: Jetty SSE에서 `EofException: Closed`가 noisy하다

Jetty는 quiet EOF를 위한 전용 타입이 있으므로:

- `org.eclipse.jetty.io`만 조정한다
- `org.eclipse.jetty.server`는 guardrail로 남긴다
- proxy idle-timeout과 reconnect 주기를 같이 본다

### 시나리오 3: Undertow에서 `IOException`과 `UT010029`가 함께 보여 분류가 안 된다

Undertow에선 둘을 한 bucket에 넣으면 안 된다.

- `io.undertow.request.io`
  request-read abort, quiet I/O noise
- `io.undertow.request`
  request handling / late-write regression guardrail

즉 logger category 분리가 곧 incident phase 분리다.

## 코드로 보기

### 공통 application.yml baseline

```yaml
logging:
  level:
    app.http.disconnect: DEBUG
    org.springframework.web.context.request.async: INFO
```

### container별 category baseline

```yaml
# Tomcat
logging.level.org.apache.coyote=WARN
logging.level.org.apache.catalina.connector=INFO
server.tomcat.accesslog.enabled=true

# Jetty
logging.level.org.eclipse.jetty.io=WARN
logging.level.org.eclipse.jetty.server=WARN
server.jetty.accesslog.enabled=true

# Undertow
logging.level.io.undertow.request.io=WARN
logging.level.io.undertow.request=WARN
server.undertow.accesslog.enabled=true
```

### log review checklist

```text
1. access log에서 status, bytes, duration, cancel ratio를 먼저 본다
2. app.http.disconnect가 한 줄 breadcrumb로만 늘었는지 확인한다
3. container guardrail category(org.apache.coyote / org.eclipse.jetty.server / io.undertow.request)가 같이 늘었는지 본다
4. AsyncRequestNotUsableException, first-byte delay, partial flush failure가 같이 붙는지 본다
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| app-side disconnect category만 도입 | container 차이를 한 bucket으로 줄이기 쉽다 | per-container drilldown은 약하다 | 대부분의 Spring Boot 서비스 baseline |
| container quiet category까지 분리 | read-side noise와 request/protocol regression을 더 잘 가른다 | category 설계와 운영 문서화가 더 필요하다 | SSE/download/upload incident가 잦은 서비스 |
| whole container namespace suppression | 당장 로그가 조용해진다 | late-write regression, protocol finish error까지 가린다 | 권장하지 않음 |
| access log + metrics만 남기고 breadcrumb 제거 | 로그량이 가장 적다 | 단건 forensic breadcrumb가 약해진다 | 정상 reconnect/noise가 매우 많은 대규모 stream 서비스 |

## 꼬리질문

> Q: Tomcat도 Undertow처럼 "이 logger만 내리면 된다"는 category가 있나요?
> 핵심: Undertow만큼 명확하진 않다. Tomcat은 app-side `DisconnectedClientHelper`와 `org.apache.coyote` guardrail 분리로 접근하는 편이 안전하다.

> Q: Jetty에서 왜 `org.eclipse.jetty.server`를 내리면 안 되나요?
> 핵심: quiet EOF뿐 아니라 request lifecycle과 commit/write 회귀 신호까지 같이 사라질 수 있기 때문이다.

> Q: Undertow에서 `io.undertow.request.io`와 `io.undertow.request`를 왜 따로 보나요?
> 핵심: Undertow가 공식적으로 quiet I/O와 일반 request exception을 다른 logger로 분리하기 때문이다.

> Q: `AsyncRequestNotUsableException`은 전부 noise로 봐도 되나요?
> 핵심: 아니다. expected disconnect의 2차 signal일 수도 있지만, commit 후 late write regression이 드러난 것일 수도 있어서 access log와 container guardrail category를 같이 봐야 한다.

## 한 줄 정리

Spring Boot disconnect logging은 "container namespace를 조용히 만드는 일"이 아니라, **app-side disconnect bucket과 container별 regression guardrail을 분리해서 expected abort만 줄이는 일**이다.
