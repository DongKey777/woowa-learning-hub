---
schema_version: 3
title: Spring Resilience4j Retry CircuitBreaker Bulkhead
concept_id: spring/resilience4j-retry-circuit-breaker-bulkhead
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- resilience4j-retry-circuit
- breaker-bulkhead
- retry-storm
- circuit-breaker-fallback
aliases:
- Resilience4j retry circuit breaker bulkhead
- Spring retry storm
- circuit breaker fallback
- bulkhead resource isolation
- timeout retry backoff
- external API resilience
intents:
- deep_dive
- design
- troubleshooting
linked_paths:
- contents/spring/spring-webclient-vs-resttemplate.md
- contents/spring/spring-observability-micrometer-tracing.md
- contents/spring/spring-webclient-connection-pool-timeout-tuning.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/system-design/circuit-breaker-basics.md
- contents/language/java/executor-sizing-queue-rejection-policy.md
symptoms:
- 외부 API 장애 때 retry가 몰려 latency와 thread 사용량이 더 폭증한다.
- circuit breaker가 열렸는데 fallback이 원인 은폐나 데이터 불일치를 만든다.
- bulkhead 없이 느린 의존성이 전체 request pool을 고갈시킨다.
expected_queries:
- Resilience4j retry circuit breaker bulkhead를 어떤 순서로 설계해야 해?
- Retry storm을 막으려면 timeout backoff circuit breaker를 어떻게 같이 봐야 해?
- Bulkhead는 thread pool이나 semaphore로 어떤 자원을 격리하는 거야?
- Spring 외부 호출 장애에서 fallback은 언제 위험해?
contextual_chunk_prefix: |
  이 문서는 Resilience4j를 단순 재시도 도구가 아니라 timeout, retry, circuit breaker,
  bulkhead, fallback, observability를 함께 설계하는 장애 전파 차단 playbook으로 설명한다.
  retry storm과 resource exhaustion 방지를 중심에 둔다.
---
# Spring Resilience4j: Retry, CircuitBreaker, Bulkhead

> 한 줄 요약: Resilience4j는 외부 호출 실패를 "운 좋게 한 번 더 시도"하는 도구가 아니라, retry storm과 자원 고갈을 막기 위해 timeout, circuit breaker, bulkhead, fallback, observability를 같이 설계하는 방어선이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
> - [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Executor Sizing, Queue, Rejection Policy](../language/java/executor-sizing-queue-rejection-policy.md)
> - [Rate Limiter 설계](../system-design/rate-limiter-design.md)

retrieval-anchor-keywords: Resilience4j, Retry, CircuitBreaker, Bulkhead, TimeLimiter, fallback, Spring Boot

## 핵심 개념

Resilience4j는 장애를 "없던 일"로 만드는 라이브러리가 아니다.

실제로는 다음 질문에 답하는 방어 패턴 묶음이다.

- 외부 API가 느릴 때 얼마나 기다릴 것인가
- 일시적 실패를 몇 번까지 다시 보낼 것인가
- 실패가 계속되면 언제 호출을 멈출 것인가
- 한 의존성의 장애가 전체 스레드를 잡아먹지 않게 어떻게 격리할 것인가
- 최종 실패 시 어떤 fallback으로 degrade할 것인가

핵심은 개별 기능이 아니라 **조합의 순서**다.

- timeout이 먼저 있어야 실패를 감지할 수 있다.
- retry는 멱등성과 backoff가 전제여야 한다.
- circuit breaker는 retry storm을 멈추는 브레이크다.
- bulkhead는 한 의존성의 실패가 전체 자원을 소모하는 것을 막는다.
- fallback은 마지막 안전망이지, 장애를 숨기는 마법이 아니다.

## 깊이 들어가기

### 1. Retry는 회복이 아니라 부하 증폭이 될 수 있다

retry는 일시적 네트워크 오류를 흡수하는 데 유용하다.
하지만 timeout 없이 retry만 넣으면, 실패한 upstream을 더 세게 두드리는 코드가 된다.

특히 다음 상황에서 위험하다.

- 서버가 이미 과부하 상태다
- 호출이 멱등하지 않다
- retry 횟수와 backoff가 없다
- 여러 계층이 동시에 retry한다

이때는 애플리케이션 한 곳의 retry가 아니라, 클라이언트, 프록시, gateway, SDK가 모두 retry하면서 요청 수가 기하급수적으로 늘 수 있다.
이 문맥은 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)과 같이 봐야 한다.

### 2. CircuitBreaker는 실패율만이 아니라 "느려짐"도 본다

Resilience4j CircuitBreaker는 단순히 에러가 몇 번 났는지만 보는 장치가 아니다.
실무에서는 timeout 증가와 latency 악화를 함께 봐야 한다.

왜냐하면 "응답은 오지만 너무 느린 상태"도 사실상 장애이기 때문이다.

상태 전이는 대체로 이렇게 이해하면 된다.

- Closed: 요청을 보낸다
- Open: 실패가 누적되어 호출을 차단한다
- Half-Open: 일부 요청만 흘려보내 복구 여부를 확인한다

이 장치는 장애 난 downstream을 계속 호출해서 전체 스레드와 커넥션을 잠그는 상황을 줄여준다.
이 관점은 [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)와 연결된다.

### 3. Bulkhead는 "같은 JVM 안에서의 분리"다

Bulkhead는 이름이 거창하지만 본질은 간단하다.

- 하나의 의존성에 쓰는 스레드와 큐를 분리한다
- 하나의 호출 경로가 다른 경로를 잡아먹지 못하게 한다

예를 들어 결제 API와 검색 API가 같은 thread pool을 공유하면, 검색 지연이 결제까지 전염될 수 있다.
그래서 bulkhead는 종종 다음 두 형태로 쓴다.

- semaphore bulkhead: 동시 호출 수만 제한
- thread pool bulkhead: 별도 스레드 풀과 큐로 격리

thread pool bulkhead는 격리가 강하지만, 큐가 길어지면 지연이 숨어 버릴 수 있다.
이 부분은 [Executor Sizing, Queue, Rejection Policy](../language/java/executor-sizing-queue-rejection-policy.md)와 같이 봐야 한다.

### 4. TimeLimiter는 "기다림의 상한"을 강제한다

외부 호출은 코드 상으로는 단순해 보여도, 실제로는 DNS, connect, TLS, read, write가 섞여 있다.
TimeLimiter를 붙이지 않으면 요청이 어디서 막혔는지 보이지 않고, 스레드만 오래 잡힌다.

중요한 점은 다음이다.

- TimeLimiter는 timeout policy를 명시한다
- Future나 async 경계에서 특히 의미가 크다
- 느린 upstream을 빨리 포기해야 전체 시스템이 산다

### 5. Fallback은 "대체 응답"이지 "정답"이 아니다

fallback은 장애 시에도 사용자가 완전히 깨진 응답을 보지 않게 해준다.
하지만 fallback을 과하게 믿으면, 실제 장애를 정상처럼 착각하게 된다.

좋은 fallback:

- 캐시된 값 반환
- 부분 데이터 제공
- 최소 기능만 유지

위험한 fallback:

- 실패를 성공처럼 숨김
- 빈 값으로 조용히 대체
- 원인 로깅 없이 무조건 대체

fallback은 반드시 관측성과 함께 써야 한다.

### 6. Spring Boot에서는 설정 실수가 가장 흔한 사고 원인이다

Resilience4j는 편하지만, 기본값만 믿으면 위험하다.

자주 터지는 미스컨피그는 다음과 같다.

- retry 횟수가 너무 많다
- wait duration이 너무 짧다
- circuit breaker sliding window가 너무 작다
- failure threshold를 너무 공격적으로 잡았다
- bulkhead queue가 너무 길다
- fallback이 모든 예외를 삼켜 버린다

즉, 라이브러리 도입보다 중요한 것은 **운영 파라미터를 서비스 특성에 맞게 조정하는 것**이다.

### 7. 관측성 없이는 튜닝할 수 없다

Resilience4j는 "잘 막고 있는지"를 숫자로 봐야 한다.

최소한 다음은 봐야 한다.

- retry count
- retry success vs failure
- circuit breaker state
- bulkhead rejected calls
- timeout count
- fallback 발생 횟수

이 지점은 [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)과 같이 봐야 한다.
관측성이 없으면 retry storm이 발생해도 "그냥 느렸다"로만 보인다.

## 실전 시나리오

### 시나리오 1: 외부 결제 API가 간헐적으로 503을 반환한다

대응은 단순 재시도가 아니다.

1. 짧은 timeout을 건다
2. 멱등 키가 있는 요청만 retry한다
3. exponential backoff와 jitter를 넣는다
4. 실패율이 높아지면 circuit breaker를 연다
5. fallback으로 결제 상태 조회 또는 보류 상태를 반환한다

이때 fallback이 결제를 "성공"으로 보이게 하면 안 된다.

### 시나리오 2: 추천 API가 느려져서 전체 요청이 밀린다

문제는 추천 API 자체보다, 그 API를 기다리느라 전체 스레드가 묶이는 것이다.

해결:

- bulkhead로 추천 호출을 분리한다
- thread pool bulkhead를 쓰면 큐 길이를 짧게 둔다
- bulkhead rejected를 에러로 보고한다
- fallback으로 추천을 비워도 메인 흐름은 진행한다

### 시나리오 3: retry를 여러 계층에서 중복으로 건다

예를 들어 API Gateway, WebClient wrapper, service layer가 모두 retry를 가지고 있으면:

- 원래 1요청이 9요청 이상으로 불어날 수 있다
- 장애가 난 서버에 트래픽이 집중된다
- 정상 서버까지 밀린다

이 경우는 "retry를 더 세게"가 아니라 "retry 주체를 하나로" 정리해야 한다.

### 시나리오 4: fallback이 조용해서 장애를 못 찾는다

겉으로는 200 OK가 나가는데 실제로는 대체 데이터만 내려가면 운영자는 장애를 놓치기 쉽다.

해결:

- fallback metric을 따로 남긴다
- trace에 fallback 이벤트를 기록한다
- 로그에 원인 exception과 dependency 이름을 남긴다

## 코드로 보기

### 1. Spring Boot YAML 설정

```yaml
resilience4j:
  retry:
    instances:
      paymentApi:
        max-attempts: 3
        wait-duration: 200ms
        enable-exponential-backoff: true
        exponential-backoff-multiplier: 2
        retry-exceptions:
          - java.io.IOException
          - java.net.SocketTimeoutException
  circuitbreaker:
    instances:
      paymentApi:
        sliding-window-type: COUNT_BASED
        sliding-window-size: 20
        minimum-number-of-calls: 10
        failure-rate-threshold: 50
        slow-call-duration-threshold: 2s
        slow-call-rate-threshold: 50
        wait-duration-in-open-state: 10s
  bulkhead:
    instances:
      paymentApi:
        max-concurrent-calls: 20
        max-wait-duration: 0
  timelimiter:
    instances:
      paymentApi:
        timeout-duration: 1500ms
```

이 설정에서 주의할 점은 숫자 자체보다 조합이다.

- retry가 3번이면 downstream 부하는 최대 3배 가까이 늘 수 있다
- slow call threshold가 너무 짧으면 정상 호출도 open 상태를 유발할 수 있다
- bulkhead queue를 길게 두면 실패 대신 지연이 쌓인다

### 2. Java 서비스 예시

```java
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.github.resilience4j.bulkhead.annotation.Bulkhead;
import io.github.resilience4j.bulkhead.Bulkhead.Type;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
public class PaymentClientService {

    @Retry(name = "paymentApi", fallbackMethod = "fallbackPayment")
    @CircuitBreaker(name = "paymentApi", fallbackMethod = "fallbackPayment")
    @Bulkhead(name = "paymentApi", type = Type.THREADPOOL)
    @TimeLimiter(name = "paymentApi")
    public CompletableFuture<PaymentResponse> callPayment(PaymentRequest request) {
        return CompletableFuture.supplyAsync(() -> {
            // external HTTP call
            return invokeRemotePayment(request);
        });
    }

    private CompletableFuture<PaymentResponse> fallbackPayment(
            PaymentRequest request, Throwable t) {
        return CompletableFuture.completedFuture(
                PaymentResponse.degraded("PAYMENT_PENDING"));
    }

    private PaymentResponse invokeRemotePayment(PaymentRequest request) {
        throw new UnsupportedOperationException("demo");
    }
}
```

실무에서는 `supplyAsync()`를 아무 executor 없이 쓰지 않는 편이 좋다.
별도 executor와 bulkhead 스레드 풀을 분리해야 thread pool isolation이 유지된다.

### 3. WebClient에 timeout과 retry를 붙일 때

```java
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

public class OrderApiClient {
    private final WebClient webClient;

    public OrderApiClient(WebClient webClient) {
        this.webClient = webClient;
    }

    public Mono<OrderDto> getOrder(String orderId) {
        return webClient.get()
            .uri("/orders/{id}", orderId)
            .retrieve()
            .bodyToMono(OrderDto.class)
            .timeout(Duration.ofSeconds(2))
            .retry(2);
    }
}
```

이 코드는 단순하지만, 운영 관점에서는 아직 부족하다.

- retry 대상 예외를 좁혀야 한다
- backoff가 필요하다
- circuit breaker와 bulkhead가 없다
- 관측성 태그가 없다

즉, 코드 한 줄보다 운영 규칙이 중요하다.

### 4. Micrometer와 연결한 관측 예시

```java
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Counter;
import org.springframework.stereotype.Component;

@Component
public class ResilienceMetrics {
    private final Counter fallbackCounter;

    public ResilienceMetrics(MeterRegistry meterRegistry) {
        this.fallbackCounter = Counter.builder("resilience.fallback.count")
            .tag("dependency", "paymentApi")
            .register(meterRegistry);
    }

    public void markFallback() {
        fallbackCounter.increment();
    }
}
```

Resilience4j의 상태와 fallback 빈도를 남겨야 retry storm이나 bulkhead saturation을 나중에 추적할 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Retry 중심 | 일시 장애를 흡수한다 | storm을 만들 수 있다 | 멱등 요청, 짧은 네트워크 흔들림 |
| CircuitBreaker 중심 | 장애 확산을 멈춘다 | 너무 민감하면 정상 트래픽도 막는다 | 느린 downstream, 반복 실패 |
| Bulkhead 중심 | 자원 격리가 된다 | 설정을 잘못하면 큐잉이 숨어든다 | 중요한 의존성 분리 |
| TimeLimiter 중심 | 무한 대기를 막는다 | timeout이 과하면 오탐이 늘어난다 | 외부 API, async 경계 |
| Fallback 중심 | 사용자 체감을 지킨다 | 장애를 숨기기 쉽다 | degrade 가능한 기능 |

실무 답은 보통 하나가 아니라 조합이다.

1. timeout으로 오래 붙잡지 않는다
2. retry는 제한적으로만 쓴다
3. circuit breaker로 실패 확산을 멈춘다
4. bulkhead로 자원을 분리한다
5. fallback으로 최소 기능을 유지한다
6. observability로 실제 효과를 확인한다

## 꼬리질문

> Q: retry와 circuit breaker는 왜 같이 써야 하나요?
> 의도: 실패 흡수와 실패 차단의 차이를 아는지 확인
> 핵심: retry는 일시 장애를 재시도하고, circuit breaker는 계속 실패하면 호출 자체를 멈춘다.

> Q: bulkhead를 쓰면 왜 thread pool isolation이 중요하나요?
> 의도: 격리의 의미가 스레드 수만이 아님을 아는지 확인
> 핵심: 같은 executor를 공유하면 한 의존성의 지연이 다른 흐름으로 전염된다.

> Q: retry storm은 왜 생기나요?
> 의도: 재시도가 항상 선의가 아니라는 점을 이해하는지 확인
> 핵심: 여러 계층의 retry가 겹치거나 backoff가 없으면 실패가 트래픽 증폭기로 바뀐다.

> Q: fallback이 있으면 장애 대응이 끝난 건가요?
> 의도: 대체 응답과 해결의 차이를 구분하는지 확인
> 핵심: fallback은 사용자 영향 완화일 뿐이고, 원인 파악과 복구는 관측성 없이는 불가능하다.

> Q: TimeLimiter와 timeout은 같은 말인가요?
> 의도: 개념을 단순 단어 수준이 아니라 실행 모델까지 이해하는지 확인
> 핵심: 둘 다 상한을 둔다는 점은 같지만, async 경계와 호출 형태에 따라 적용 방식이 다르다.

## 한 줄 정리

Resilience4j는 retry, circuit breaker, bulkhead, TimeLimiter, fallback을 하나의 방어 체계로 묶어 retry storm과 자원 고갈을 막는 Spring Boot 운영 도구다.
