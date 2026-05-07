---
schema_version: 3
title: Spring JsonTest and RestClientTest Slice Boundaries
concept_id: spring/jsontest-restclienttest-slice-boundaries
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 80
review_feedback_tags:
- jsontest-restclienttest-slice
- boundaries
- jsontest
- restclienttest
aliases:
- @JsonTest
- @RestClientTest
- Jackson slice test
- MockRestServiceServer
- JsonContent
- outbound HTTP slice test
- serialization contract test
- RestClient.Builder test
intents:
- troubleshooting
- design
symptoms:
- JSON 직렬화 계약만 확인하려는 테스트에 service/security/full app 설정을 기대한다.
- outbound HTTP client 계약을 검증하려다 전체 SpringBootTest로 너무 넓게 올린다.
- slice test에 @Import나 TestConfiguration을 과하게 넣어 무엇을 검증하는지 흐려진다.
linked_paths:
- contents/spring/spring-test-slices-context-caching.md
- contents/spring/spring-test-slice-import-testconfiguration-boundaries.md
- contents/spring/spring-webclient-vs-resttemplate.md
- contents/spring/spring-restclient-vs-webclient-lifecycle-boundaries.md
- contents/spring/spring-async-context-propagation-restclient-http-interface-clients.md
expected_queries:
- @JsonTest와 @RestClientTest는 어떤 계약을 좁게 검증해?
- JSON 직렬화 모양을 controller test와 별도로 고정하려면 무엇을 써?
- RestClient outbound HTTP 요청/응답 계약은 @RestClientTest로 어떻게 검증해?
- slice test 경계를 넘기 시작하면 왜 반쪽 통합 테스트가 돼?
contextual_chunk_prefix: |
  이 문서는 @JsonTest가 Jackson serialization/deserialization contract를,
  @RestClientTest가 RestTemplate/RestClient outbound HTTP client contract를 좁게
  검증한다는 점을 다룬다. MockRestServiceServer, JsonContent, ObjectMapper,
  Test slice boundary leak과 full SpringBootTest 오용을 진단하는 playbook이다.
---
# Spring `@JsonTest` and `@RestClientTest` Slice Boundaries

> 한 줄 요약: `@JsonTest`와 `@RestClientTest`는 각각 직렬화 계약과 outbound HTTP 계약을 빠르게 검증하는 좋은 slice지만, 애플리케이션 전체 설정을 기대하기 시작하면 계약 테스트가 아니라 모호한 반쪽 통합 테스트가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
> - [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)
> - [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
> - [Spring RestClient vs WebClient Lifecycle Boundaries](./spring-restclient-vs-webclient-lifecycle-boundaries.md)
> - [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)

retrieval-anchor-keywords: JsonTest, RestClientTest, Jackson slice test, MockRestServiceServer, JsonContent, outbound http slice test, serialization contract test, RestTemplateBuilder test, RestClient.Builder test

## 핵심 개념

Spring test slice 하면 보통 `@WebMvcTest`와 `@DataJpaTest`부터 떠올리기 쉽다.

하지만 실무에서 자주 중요한 계약은 아래 두 가지다.

- JSON 직렬화/역직렬화 계약
- 외부 HTTP 호출 클라이언트 계약

이때 각각 잘 맞는 slice가 있다.

- `@JsonTest`: Jackson 중심 직렬화 계약
- `@RestClientTest`: `RestTemplate` / `RestClient` 계열 outbound client 계약

핵심은 이 둘을 "작은 통합 테스트"로 보는 것이 아니라, **입출력 계약을 좁게 검증하는 slice**로 보는 것이다.

## 깊이 들어가기

### 1. `@JsonTest`는 JSON 모양을 계약으로 고정하는 데 강하다

많은 서비스에서 실제 버그는 controller 로직보다 JSON contract 변화에서 난다.

- 필드 이름이 바뀜
- 날짜 포맷이 달라짐
- enum 직렬화 정책이 달라짐
- custom serializer/deserializer가 빠짐

`@JsonTest`는 이 부분만 빠르게 검증하는 데 적합하다.

즉 "API 테스트를 다 하자"가 아니라, **Jackson mapping 규칙 자체를 별도로 고정**하는 것이다.

### 2. `@RestClientTest`는 outbound HTTP client를 좁게 검증한다

외부 API client는 보통 다음 계약이 중요하다.

- 어떤 URL을 치는가
- 어떤 헤더를 보내는가
- 응답 JSON을 어떤 DTO로 해석하는가
- 오류 응답을 어떤 예외/결과로 바꾸는가

이걸 전체 `@SpringBootTest`로 돌릴 수도 있지만, 대개 너무 넓다.

`@RestClientTest`는 `MockRestServiceServer`와 함께 이 경계를 빠르게 검증하게 해 준다.

핵심은 "HTTP를 실제로 보내는지"보다, **우리 client 코드가 어떤 요청/응답 계약을 가졌는지**다.

### 3. slice 경계를 넘기 시작하면 오히려 가치가 떨어진다

`@JsonTest`에서 service bean이나 full security config를 기대하기 시작하면 방향이 틀어진다.

`@RestClientTest`에서 앱 전체 configuration, retry, async, 보안 컨텍스트까지 한 번에 보려 하면 역시 경계가 흔들린다.

이때는 테스트가 풍부해지는 것이 아니라, **무엇을 검증하는지 흐려지는 것**이다.

### 4. `@JsonTest`는 controller test를 대체하지 않고 보완한다

`@WebMvcTest`에서도 결국 JSON을 보게 된다.

하지만 `@JsonTest`는 다음처럼 더 좁고 빠르다.

- DTO 단위 직렬화 정책
- custom `ObjectMapper` 설정
- date/time/module 등록

즉 컨트롤러 계약이 아니라, **payload shape 자체를 고정하는 세밀한 테스트**다.

### 5. `@RestClientTest`는 outbound contract를 inward logic와 분리해 준다

서비스 로직 테스트에서 외부 client까지 전부 mock으로 덮어 버리면, 실제 HTTP 매핑 계약이 놓칠 수 있다.

반대로 full integration으로 가면 너무 넓어진다.

`@RestClientTest`는 이 사이에서 유용하다.

- HTTP method
- path/query
- headers
- request body
- response mapping

즉 외부 시스템과의 **클라이언트 어댑터 계층**을 따로 검증하게 해 준다.

### 6. 한계도 분명하다

`@JsonTest`가 약한 것:

- 필터/보안/컨트롤러 매핑
- end-to-end API behavior

`@RestClientTest`가 약한 것:

- 실제 네트워크 timeout
- connection pool behavior
- async context propagation
- retry/backoff 전체 orchestration

즉 slice는 계약을 좁게 잘라 보기에 좋지만, **운영 행태 전체를 대신 검증하지는 않는다**.

## 실전 시나리오

### 시나리오 1: 배포 후 날짜 포맷이 바뀌어 클라이언트가 깨진다

이건 `@WebMvcTest`보다 `@JsonTest`가 더 정확히 잡아낼 수 있는 버그다.

payload shape를 DTO 단위로 고정하면 리팩터링 내성도 높아진다.

### 시나리오 2: 외부 API client가 헤더 하나를 빠뜨려 운영에서만 401이 난다

서비스 레벨 mock 테스트만 있으면 놓치기 쉽다.

`@RestClientTest`로 요청 헤더/경로 계약을 분리해 검증하는 편이 낫다.

### 시나리오 3: slice에 설정을 너무 많이 import해 테스트가 느려진다

이건 `@JsonTest`/`@RestClientTest`도 `@WebMvcTest`처럼 boundary leak가 생긴 것이다.

### 시나리오 4: outbound client 테스트로 timeout/retry까지 다 보려 한다

그건 slice가 아니라 더 넓은 통합 테스트나 전용 client integration 테스트가 맞을 수 있다.

## 코드로 보기

### `@JsonTest`

```java
@JsonTest
class OrderResponseJsonTest {

    @Autowired
    JacksonTester<OrderResponse> json;

    @Test
    void serializesExpectedShape() throws Exception {
        OrderResponse response = new OrderResponse(1L, "PAID");
        assertThat(json.write(response)).extractingJsonPathStringValue("$.status")
            .isEqualTo("PAID");
    }
}
```

### `@RestClientTest`

```java
@RestClientTest(PaymentApiClient.class)
class PaymentApiClientTest {

    @Autowired
    PaymentApiClient client;

    @Autowired
    MockRestServiceServer server;

    @Test
    void callsExpectedEndpoint() {
        server.expect(requestTo("/payments/1"))
            .andRespond(withSuccess("{\"status\":\"DONE\"}", MediaType.APPLICATION_JSON));

        PaymentResponse response = client.find(1L);
        assertThat(response.status()).isEqualTo("DONE");
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@JsonTest` | 빠르고 payload contract가 선명하다 | web/security 흐름은 못 본다 | DTO 직렬화/역직렬화 검증 |
| `@RestClientTest` | outbound HTTP contract를 좁게 본다 | 네트워크/운영 행태는 약하다 | 외부 API client adapter 검증 |
| `@WebMvcTest` | inbound API contract를 본다 | payload 세부 케이스가 무거울 수 있다 | controller 계약 |
| `@SpringBootTest` | 실제와 가깝다 | 느리고 범위가 넓다 | 더 넓은 wiring 검증이 필요할 때 |

핵심은 `@JsonTest`와 `@RestClientTest`를 "작은 앱 기동"으로 보지 말고, **입출력 경계별 계약 테스트**로 쓰는 것이다.

## 꼬리질문

> Q: `@JsonTest`가 `@WebMvcTest`와 다른 가치는 무엇인가?
> 의도: payload contract 분리 이해 확인
> 핵심: controller 없이도 JSON shape와 ObjectMapper 규칙을 좁게 고정할 수 있다.

> Q: `@RestClientTest`가 좋은 이유는 무엇인가?
> 의도: outbound adapter 테스트 가치 확인
> 핵심: 외부 HTTP client의 요청/응답 계약을 서비스 로직과 분리해 빠르게 검증할 수 있다.

> Q: `@RestClientTest`로 timeout/retry까지 다 보면 안 되는가?
> 의도: slice 한계 인식 확인
> 핵심: 실제 네트워크/운영 행태는 더 넓은 테스트 경계가 필요할 수 있다.

> Q: 왜 이 slice들도 boundary leak를 경계해야 하는가?
> 의도: 테스트 설계 일관성 확인
> 핵심: 필요 이상 설정을 끌어오면 계약 테스트가 모호한 반쪽 통합 테스트가 되기 때문이다.

## 한 줄 정리

`@JsonTest`와 `@RestClientTest`의 가치는 Spring을 조금만 띄우는 데 있지 않고, JSON과 outbound HTTP 계약을 각각 독립된 테스트 경계로 고정하는 데 있다.
