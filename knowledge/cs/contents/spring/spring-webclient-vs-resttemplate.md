# Spring WebClient vs RestTemplate

> 한 줄 요약: RestTemplate은 단순한 블로킹 클라이언트이고, WebClient는 reactive 체인과 backpressure까지 고려하는 비동기 클라이언트다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [Timeout types: connect/read/write](../network/timeout-types-connect-read-write.md)
> - [gRPC vs REST](../network/grpc-vs-rest.md)
> - [HTTP/2 Multiplexing과 HOL Blocking](../network/http2-multiplexing-hol-blocking.md)

## 핵심 개념

둘의 차이는 단순히 "새 것 vs 옛 것"이 아니다.

- RestTemplate: 호출 스레드를 블로킹한다.
- WebClient: 비동기와 reactive 체인을 지원한다.

즉, RestTemplate은 단순성이 장점이고, WebClient는 확장성과 조합성이 장점이다.

중요한 점은 WebClient를 써도 `block()`을 남발하면 장점이 사라진다는 것이다.

## 깊이 들어가기

### 1. RestTemplate은 이해하기 쉽다

- 코드가 직선적이다.
- 디버깅이 쉽다.
- 동기 서비스와 잘 맞는다.

하지만 요청이 몰리면 스레드가 많이 묶인다.

### 2. WebClient는 체인 기반이다

WebClient는 reactive 스트림 위에서 동작한다.

- timeout, retry, filter를 체인으로 붙이기 쉽다.
- 대량 fan-out 호출에서 유리하다.
- WebFlux와 같이 쓰면 비동기 흐름이 자연스럽다.

### 3. timeout과 retry 전략을 같이 봐야 한다

클라이언트 선택보다 더 중요한 건 timeout 구성이다.

- connect timeout
- read timeout
- write timeout

이 구분이 없으면 네트워크 장애가 생겨도 어디서 멈췄는지 알기 어렵다.

### 4. observability가 중요해진다

WebClient는 filter로 trace, metric, log를 붙이기 좋다.

이 문맥은 [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)과 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 레거시 동기 서비스에서 외부 API 한두 개만 호출한다

RestTemplate이 충분할 수 있다.

### 시나리오 2: 알림/피드/집계처럼 fan-out 호출이 많다

WebClient가 더 자연스럽다.

### 시나리오 3: WebClient를 썼는데도 느리다

대부분 다음 중 하나다.

- 내부에서 `block()`을 호출했다
- timeout이 없다
- retry가 너무 공격적이다
- 외부 API가 느린데 backpressure 전략이 없다

## 코드로 보기

### RestTemplate

```java
@Service
public class LegacyProfileClient {
    private final RestTemplate restTemplate;

    public LegacyProfileClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public Profile get(Long id) {
        return restTemplate.getForObject("/profiles/" + id, Profile.class);
    }
}
```

### WebClient

```java
@Service
public class ReactiveProfileClient {
    private final WebClient webClient;

    public ReactiveProfileClient(WebClient webClient) {
        this.webClient = webClient;
    }

    public Mono<Profile> get(Long id) {
        return webClient.get()
            .uri("/profiles/{id}", id)
            .retrieve()
            .bodyToMono(Profile.class);
    }
}
```

### retry + timeout

```java
webClient.get()
    .uri("/feed")
    .retrieve()
    .bodyToMono(String.class)
    .timeout(Duration.ofSeconds(2))
    .retry(2);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| RestTemplate | 단순하다 | 블로킹이다 | 레거시, 소규모 호출 |
| WebClient | 확장성 좋다 | 학습/디버깅 비용이 있다 | fan-out, reactive stack |
| WebClient + block() | 기존 코드에 붙이기 쉽다 | 장점이 많이 사라진다 | 전환기 |

## 꼬리질문

> Q: WebClient를 썼는데 왜 빨라지지 않는가?
> 의도: 비동기 모델 이해 확인
> 핵심: 내부 블로킹이나 잘못된 timeout/retry가 있으면 느리다.

> Q: RestTemplate은 언제 충분한가?
> 의도: 기술 선택 기준 확인
> 핵심: 단순 동기 호출과 레거시 통합에는 충분할 수 있다.

> Q: WebClient와 WebFlux는 같은 것인가?
> 의도: 클라이언트/서버 스택 구분 확인
> 핵심: WebClient는 클라이언트, WebFlux는 서버/reactive 스택이다.

## 한 줄 정리

RestTemplate은 단순한 블로킹 클라이언트이고, WebClient는 reactive 체인과 운영 전략까지 같이 설계해야 하는 클라이언트다.
