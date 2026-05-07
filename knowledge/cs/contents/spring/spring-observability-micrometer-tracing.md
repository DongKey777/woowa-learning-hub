---
schema_version: 3
title: Spring Observability with Micrometer Tracing
concept_id: spring/observability-micrometer-tracing
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- observability-micrometer-tracing
- observability
- micrometer-tracing
- observation-api
aliases:
- Spring observability
- Micrometer tracing
- Observation API
- trace log metric correlation
- MDC trace context
- tag cardinality
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-async-mvc-streaming-observability-playbook.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
- contents/spring/spring-security-architecture.md
- contents/spring/spring-transaction-debugging-playbook.md
- contents/software-engineering/cache-message-observability.md
- contents/network/timeout-retry-backoff-practical.md
- contents/spring/spring-micrometer-tag-cardinality-pitfalls.md
symptoms:
- 로그에는 에러가 있는데 어느 HTTP 요청과 연결되는지 찾기 어렵다.
- p99 latency가 튀지만 DB, 외부 API, servlet write 중 어느 구간인지 분리되지 않는다.
- 사용자 id나 path variable을 tag로 넣어 metrics cardinality가 폭증한다.
expected_queries:
- Spring에서 Micrometer tracing으로 metric trace log를 어떻게 연결해?
- Observation API와 MDC trace context는 어떻게 다른 역할이야?
- p99 latency 장애를 trace와 metric으로 어디서부터 봐야 해?
- Micrometer tag cardinality가 높은 값 때문에 문제가 생기는 이유는?
contextual_chunk_prefix: |
  이 문서는 Spring 관측성을 로그 추가가 아니라 metrics, traces, logs를 같은 사건으로
  연결하는 운영 playbook으로 설명한다. Micrometer, Observation API, tracing context,
  MDC, tag cardinality, timeout/retry 관찰 지점을 다룬다.
---
# Spring Observability with Micrometer Tracing

> 한 줄 요약: 관측성은 로그 몇 개 더 찍는 일이 아니라, 메트릭, 트레이스, 로그를 같은 사건으로 묶어 장애를 빨리 찾는 설계다.

**난이도: 🔴 Advanced**

관련 문서:

- [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
- [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
- [Spring Security 아키텍처](./spring-security-architecture.md)
- [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
- [캐시, 메시징, 관측성](../software-engineering/cache-message-observability.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)

retrieval-anchor-keywords: spring observability, micrometer tracing, metrics traces logs correlation, trace context propagation, mdc vs trace context, high cardinality tag trap, p99 latency trace debugging, observability 뭐예요, tracing 처음, opentelemetry spring

## 핵심 개념

Spring 관측성의 핵심은 세 가지다.

- Metrics: 숫자로 보는 지표
- Tracing: 요청 경로를 따라가는 흐름
- Logging: 사건의 문맥

Micrometer는 메트릭과 관측성의 진입점이고, Tracing은 분산 트랜잭션이 아니라 요청 흐름을 추적하는 도구다.

중요한 점은 모든 데이터를 다 남기면 안 된다는 것이다.

- 태그 cardinality가 너무 높으면 메트릭 저장소가 망가진다.
- trace를 모든 요청에 다 붙이면 비용이 커진다.
- 로그에 민감 정보가 섞이면 보안 사고가 된다.

## 깊이 들어가기

### 1. Observation은 공통 인터페이스다

Spring 6/Boot 3 계열에서는 Observation API를 중심으로 metrics와 tracing을 엮는다.

관측성의 핵심은 "같은 요청을 같은 식별자로 묶는 것"이다.

### 2. Micrometer는 tag 전략이 절반이다

좋은 메트릭:

- 엔드포인트별 p95/p99
- DB 쿼리 수
- 외부 API 실패율
- thread pool saturation

나쁜 메트릭:

- userId, orderId 같은 고카디널리티 태그
- 요청마다 바뀌는 문자열 전체

### 3. trace는 timeout과 retry를 해석하게 만든다

외부 API timeout이 났을 때 trace가 있으면 다음을 본다.

- 어디서 지연이 시작됐는지
- retry가 몇 번 붙었는지
- load balancer나 proxy에서 끊긴 건 아닌지

이 관점은 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)과 연결된다.

### 4. MDC와 trace context는 같지 않다

로그에 traceId를 넣고 싶다고 해서 MDC만 붙이면 끝이 아니다.

- MDC는 로그 문맥
- Trace context는 분산 추적 문맥

이 둘은 동기/비동기 경계에서 따로 사라질 수 있다.

## 실전 시나리오

### 시나리오 1: p99이 튀는데 원인을 모른다

메트릭만 있으면 "느리다"까지만 안다.
트레이스가 있으면 DB인지 외부 API인지 구분할 수 있다.

### 시나리오 2: 특정 사용자만 느리다

고카디널리티 tag를 무작정 붙이지 말고, trace로 좁히고, 샘플링 전략을 둔다.

### 시나리오 3: healthcheck는 살아 있는데 실제 트래픽은 죽는다

로드밸런서 healthcheck와 애플리케이션 지표를 같이 봐야 한다.

이 주제는 [Load Balancer Healthcheck Failure Patterns](../network/load-balancer-healthcheck-failure-patterns.md)와 같이 본다.

## 코드로 보기

### observation 등록

```java
@Configuration
public class ObservabilityConfig {

    @Bean
    public ObservationHandler<Observation.Context> loggingHandler() {
        return new DefaultTracingObservationHandler();
    }
}
```

### 커스텀 관측

```java
@Service
public class PaymentService {
    private final ObservationRegistry registry;

    public PaymentService(ObservationRegistry registry) {
        this.registry = registry;
    }

    public void pay(Long orderId) {
        Observation.createNotStarted("payment.process", registry)
            .lowCardinalityKeyValue("type", "card")
            .observe(() -> {
                // work
            });
    }
}
```

### Micrometer meter

```java
Counter counter = Counter.builder("payment.failures")
    .tag("channel", "card")
    .register(meterRegistry);

counter.increment();
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Metrics 중심 | 가볍고 저렴하다 | 원인 추적이 어렵다 | 운영 대시보드 |
| Tracing 중심 | 원인 경로를 잘 본다 | 비용과 샘플링이 중요하다 | 분산 호출 디버깅 |
| Logging 중심 | 상세 문맥이 많다 | 검색과 보관 비용이 커진다 | 장애 분석 |
| All-in-one | 상호 보완이 된다 | 설계가 없다면 비용만 커진다 | 성숙한 운영 체계 |

## 꼬리질문

> Q: 고카디널리티 tag가 왜 문제인가?
> 의도: 메트릭 저장 비용 이해 확인
> 핵심: 저장소와 쿼리 비용이 폭증한다.

> Q: trace와 log의 차이는 무엇인가?
> 의도: 관측성 구성요소 이해 확인
> 핵심: trace는 경로, log는 사건의 상세 문맥이다.

> Q: 샘플링은 왜 필요한가?
> 의도: 비용과 가시성 균형 이해 확인
> 핵심: 모든 요청을 다 추적하는 것은 비싸다.

## 한 줄 정리

Micrometer tracing은 장애를 더 많이 기록하는 기능이 아니라, metrics, trace, log를 연결해 원인을 빨리 찾게 하는 기능이다.
