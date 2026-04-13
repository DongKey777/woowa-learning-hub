# Spring Micrometer Tag Cardinality Pitfalls

> 한 줄 요약: Micrometer 태그는 관측성을 풍부하게 하지만, cardinality가 높은 값을 넣으면 메트릭이 폭발해 오히려 시스템을 흐리게 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)

retrieval-anchor-keywords: Micrometer, tag cardinality, high cardinality, low cardinality, meter explosion, metric label, observability cost, histogram, timer tags

## 핵심 개념

Micrometer의 태그는 메트릭을 쪼개는 label이다.

- endpoint
- status
- method
- exception
- client

문제는 태그 값이 너무 다양해질 때다.

고카디널리티 값이 들어가면 메트릭이 무한히 늘어나며 비용과 탐색성이 나빠진다.

## 깊이 들어가기

### 1. low cardinality와 high cardinality를 구분해야 한다

좋은 태그:

- HTTP method
- status code
- route template
- dependency name

나쁜 태그:

- user id
- order id
- request UUID
- full URL with query string

### 2. tag는 차트보다 비용에 영향을 준다

카디널리티가 높으면 시계열이 폭발한다.

- 저장 비용 증가
- query 비용 증가
- 대시보드 혼란 증가

### 3. endpoint template을 써야 한다

`/users/123` 대신 `/users/{id}` 같은 템플릿을 써야 한다.

### 4. exception tag도 조심해야 한다

에러 타입을 너무 세밀하게 나누면 메트릭이 쪼개진다.

### 5. trace와 metric은 다른 문제다

trace는 세부 사건을, metric은 집계를 본다.

이 문맥은 [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)과 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 메트릭은 늘었는데 대시보드가 쓰기 어렵다

태그 폭발 때문이다.

### 시나리오 2: user id를 태그에 넣었다

유용해 보이지만 거의 항상 잘못된 선택이다.

### 시나리오 3: query string까지 tag에 넣었다

고카디널리티의 대표적 함정이다.

### 시나리오 4: status만 보면 충분한데 exception까지 너무 많이 쪼갠다

집계가 깨진다.

## 코드로 보기

### good tags

```java
Timer.builder("http.server.requests")
    .tag("method", "GET")
    .tag("status", "200")
    .tag("route", "/orders/{id}")
    .register(meterRegistry);
```

### bad tags

```java
Timer.builder("http.server.requests")
    .tag("userId", userId.toString())
    .tag("requestId", requestId)
    .register(meterRegistry);
```

### dependency metric

```java
Timer.builder("http.client.requests")
    .tag("client", "payment-api")
    .register(meterRegistry);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| low-cardinality tags | 집계가 안정적이다 | 세부 추적이 적다 | 기본 메트릭 |
| high-cardinality tags | 상세 식별이 된다 | 비용과 폭발 위험이 크다 | trace로 대체 |
| path template tags | 분석이 쉽다 | route 매핑이 필요하다 | HTTP metrics |

핵심은 메트릭 태그를 "분류 키"로 쓰되, **식별자**로 쓰지 않는 것이다.

## 꼬리질문

> Q: tag cardinality가 왜 문제인가?
> 의도: 메트릭 비용 구조 이해 확인
> 핵심: 시계열 수가 폭증하기 때문이다.

> Q: user id를 metric tag에 넣으면 왜 안 되는가?
> 의도: high-cardinality 위험 이해 확인
> 핵심: 메트릭이 너무 잘게 쪼개진다.

> Q: route template을 쓰는 이유는 무엇인가?
> 의도: 집계 안정성 이해 확인
> 핵심: 동일 엔드포인트를 하나의 시계열로 묶기 위해서다.

> Q: metric과 trace를 어떻게 구분해야 하는가?
> 의도: observability 역할 분리 확인
> 핵심: metric은 집계, trace는 개별 사건이다.

## 한 줄 정리

Micrometer 태그는 low-cardinality로 유지해야 하며, 고유 식별자는 metric이 아니라 trace로 보아야 한다.
