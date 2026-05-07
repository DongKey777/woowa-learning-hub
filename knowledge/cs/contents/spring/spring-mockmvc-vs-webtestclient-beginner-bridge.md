---
schema_version: 3
title: Spring MockMvc vs WebTestClient Beginner Bridge
concept_id: spring/mockmvc-vs-webtestclient-beginner-bridge
canonical: true
category: spring
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 86
review_feedback_tags:
- mockmvc-vs-webtestclient
- mockmvc
- webtestclient
- servlet-stack-test
aliases:
- MockMvc vs WebTestClient
- Spring MockMvc beginner
- Spring WebTestClient beginner
- servlet stack test
- WebFlux test
- MVC controller test
- reactive test client
intents:
- comparison
- definition
linked_paths:
- contents/spring/spring-testing-basics.md
- contents/spring/spring-webflux-vs-mvc.md
- contents/spring/spring-webclient-vs-resttemplate.md
- contents/spring/spring-jsontest-restclienttest-slice-boundaries.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
confusable_with:
- spring/spring-testing-basics
- spring/webflux-vs-mvc
- spring/webclient-vs-resttemplate
- software-engineering/testing-strategy-and-test-doubles
expected_queries:
- MockMvc와 WebTestClient는 Spring 테스트에서 어떻게 달라?
- Spring MVC controller test는 MockMvc를 먼저 떠올리면 돼?
- WebFlux endpoint는 왜 WebTestClient가 자연스러워?
- 실제 서버를 띄운 HTTP 호출은 E2E와 app integration test 중 무엇에 가까워?
contextual_chunk_prefix: |
  이 문서는 MockMvc와 WebTestClient를 서버 stack 기준으로 구분하는 beginner bridge다.
  MockMvc는 servlet Spring MVC controller를 mock servlet 환경에서 검증하는 도구이고,
  WebTestClient는 WebFlux/reactive endpoint 또는 실제 서버 호출에 쓰는
  client-shaped test API라는 차이를 설명한다.
---
# Spring beginner bridge: `MockMvc`와 `WebTestClient`를 언제 구분해서 부르나

> 한 줄 요약: `MockMvc`는 servlet stack의 Spring MVC를 서버 쪽에서 검증하는 도구이고, `WebTestClient`는 reactive/WebFlux 쪽에서 많이 쓰는 클라이언트 모양 API라서, 초심자는 먼저 "`지금 내가 테스트하는 서버 stack이 무엇인가`"를 기준으로 둘을 나누면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](./spring-testing-basics.md)
- [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
- [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)
- [Spring `@JsonTest` and `@RestClientTest` Slice Boundaries](./spring-jsontest-restclienttest-slice-boundaries.md)
- [테스트 전략과 테스트 더블](../software-engineering/testing-strategy-and-test-doubles.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: mockmvc vs webtestclient, spring mockmvc beginner, spring webtestclient beginner, servlet stack test basics, webflux test basics, mockmvc 뭐예요, webtestclient 뭐예요, spring test 처음, mockmvc webtestclient 헷갈려, reactive test client basics, mvc controller test what is, webflux controller test what is

## 핵심 개념

처음에는 도구 이름보다 **서버 stack**을 먼저 보면 된다.

- `MockMvc`: Spring MVC, 즉 servlet stack 테스트에서 자주 만난다.
- `WebTestClient`: WebFlux 테스트에서 기본 선택지처럼 등장한다.

입문자가 많이 섞어 부르는 이유는 둘 다 "`HTTP 요청을 흉내 내서 응답을 본다`"는 겉모습이 비슷하기 때문이다. 하지만 mental model은 다르다.

- `MockMvc`는 **Spring MVC 서버 쪽을 mock servlet 환경에서 검증**하는 도구다.
- `WebTestClient`는 **클라이언트처럼 요청을 보내고 응답을 읽는 API**다.

그래서 처음 한 줄로 외우면 된다.

`MockMvc`는 "MVC 서버 테스트 도구", `WebTestClient`는 "WebFlux에서 많이 쓰는 테스트 클라이언트"다.

## 한눈에 보기

| 지금 구분할 축 | `MockMvc` | `WebTestClient` |
|---|---|---|
| 초심자용 첫 인상 | Spring MVC용 서버 테스트 | WebFlux에서 많이 보이는 테스트 클라이언트 |
| 기본 연결 대상 | servlet stack controller | reactive/webflux handler 또는 서버 |
| API 느낌 | server-side test DSL | client request/response DSL |
| 처음 추천되는 질문 | "`내 앱이 MVC인가?`" | "`내 앱이 WebFlux인가?`" |
| 흔한 오해 | "`WebClient`랑 비슷하니 outbound client인가?`" | "`reactive면 MVC에서는 못 쓰나?`" |

초심자 기준 결정표는 더 짧다.

| 내가 테스트하는 것 | 먼저 떠올릴 도구 |
|---|---|
| `@WebMvcTest`, `@Controller`, servlet MVC 요청/응답 | `MockMvc` |
| `@WebFluxTest`, `Mono`, `Flux`, reactive endpoint | `WebTestClient` |
| 실제 서버를 띄운 HTTP 호출 | `WebTestClient` 또는 다른 HTTP client |

- 여기서 중요한 용어 정리는 하나다. **실제 서버를 띄운 HTTP 호출이라고 바로 E2E는 아니다.**
- 테스트 코드가 서버를 직접 호출해 wiring, 직렬화, 보안 경계를 보는 경우는 보통 **앱 통합 테스트(App Integration Test)** 다.
- 브라우저나 실제 사용자 클라이언트가 로그인부터 주문 완료까지 바깥에서 끝까지 검증할 때만 E2E라고 부르는 편이, [Spring 테스트 기초](./spring-testing-basics.md)와 정의가 정확히 맞는다.

## 상세 분해

### 1. `MockMvc`는 MVC 요청 파이프라인을 좁게 검증한다

`MockMvc`는 실제 톰캣을 띄우지 않아도 `DispatcherServlet` 기준의 MVC 요청 흐름을 테스트할 수 있게 도와준다.

그래서 이런 질문과 잘 맞는다.

- URL 매핑이 맞나
- `@RequestBody` 바인딩이 맞나
- validation 실패가 `400`으로 가나
- JSON 응답 모양이 맞나

즉 "`Spring MVC 컨트롤러 계약을 빨리 확인하고 싶다`"면 `MockMvc`가 자연스럽다.

### 2. `WebTestClient`는 WebFlux에서 기본 감각이 더 자연스럽다

`WebTestClient`는 요청을 만들고 응답 상태, 헤더, 바디를 확인하는 **클라이언트 모양 API**다.

그래서 이런 코드와 자주 같이 보인다.

- `Mono<OrderResponse>`
- `Flux<ServerSentEvent<?>>`
- `@WebFluxTest`

즉 "`내 endpoint가 reactive publisher를 반환한다`"는 감각이 먼저 보이면 `WebTestClient` 쪽이 더 자연스럽다.

### 3. 이름이 비슷해 보여도 `WebClient`와 `WebTestClient`는 다르다

여기서 초심자가 한 번 더 헷갈린다.

- `WebClient`: 애플리케이션 코드에서 외부 HTTP를 호출하는 실제 클라이언트
- `WebTestClient`: 테스트 코드에서 서버 응답을 검증하는 테스트용 클라이언트

즉 둘 다 client라는 단어가 들어가지만, 하나는 **운영 코드용**, 다른 하나는 **테스트용**이다.

### 4. `WebTestClient`가 MVC에서 아예 금지되는 것은 아니다

초심자용 첫 분기는 "`MVC면 MockMvc, WebFlux면 WebTestClient`"로 잡는 편이 가장 덜 헷갈린다. 다만 이걸 "`WebTestClient`는 MVC에서 절대 못 쓴다"로 외우면 또 틀린다.

Spring은 `MockMvc`를 뒤에 두고 `WebTestClient` 스타일 API로 MVC를 검증하는 연결 방법도 제공한다. 하지만 beginner 동선에서는 이 확장보다 **기본 stack 구분**을 먼저 잡는 편이 안전하다.

즉 첫 단계에서는 이렇게 정리하면 충분하다.

- 기본 MVC 학습: `MockMvc`
- 기본 WebFlux 학습: `WebTestClient`
- 나중에 필요하면: MVC에서도 `WebTestClient` 스타일 API를 붙일 수 있다

## 흔한 오해와 함정

- "`MockMvc`가 있으니 reactive endpoint도 다 검증하겠지"라고 생각하면 안 된다. 먼저 내가 servlet MVC인지 WebFlux인지 봐야 한다.
- "`WebTestClient`는 `WebClient`랑 비슷해 보이니 외부 API mock 도구인가?`"라고 묶으면 안 된다. 전자는 테스트 도구, 후자는 실제 HTTP client다.
- "`둘 다 요청/응답을 보니까 완전히 같은 것 아닌가요?`"라고 느끼기 쉽지만, 기본적으로 기대하는 서버 실행 모델이 다르다.
- "`처음부터 둘 다 다 외워야 하나요?`"라고 걱정할 필요는 없다. 현재 미션이 Spring MVC 기반이면 `MockMvc`부터 잡아도 충분한 경우가 많다.

## 실무에서 쓰는 모습

MVC 컨트롤러를 테스트할 때는 이런 그림이 가장 흔하다.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;
}
```

이 코드는 "`주문 컨트롤러의 요청 매핑, 검증, JSON 응답을 MVC 기준으로 보겠다`"는 뜻에 가깝다.

WebFlux endpoint를 테스트할 때는 이런 그림이 흔하다.

```java
@WebFluxTest(OrderController.class)
class OrderControllerTest {
    @Autowired WebTestClient webTestClient;
}
```

이 코드는 "`reactive endpoint의 상태 코드와 body를 클라이언트처럼 검증하겠다`"는 뜻에 가깝다.

짧은 결정 예시는 아래처럼 보면 된다.

| 지금 코드에서 먼저 보이는 힌트 | 더 자연스러운 시작점 |
|---|---|
| `@WebMvcTest`, `MockBean`, `DispatcherServlet` | `MockMvc` |
| `@WebFluxTest`, `Mono`, `Flux`, `RouterFunction` | `WebTestClient` |
| 실제 서버를 띄워 HTTP 경계와 bean wiring을 함께 본다 | `WebTestClient` 기반 앱 통합 테스트 |
| 외부 API를 호출하는 운영 코드 `WebClient` | 테스트 도구 선택 질문이 아니라 [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md) 질문 |

## 더 깊이 가려면

- Spring 테스트 전체 큰 그림이 먼저 필요하면 [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](./spring-testing-basics.md)로 돌아간다.
- 왜 MVC와 WebFlux가 아예 다른 실행 모델인지까지 보고 싶다면 [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)로 이어서 본다.
- `WebClient`와 `WebTestClient` 이름 혼동이 계속 나면 [Spring WebClient vs RestTemplate](./spring-webclient-vs-resttemplate.md)로 가서 "운영용 client" 축을 먼저 분리한다.
- 테스트 경계를 더 잘 고르고 싶다면 [테스트 전략과 테스트 더블](../software-engineering/testing-strategy-and-test-doubles.md)이 다음 안전한 한 걸음이다.

## 면접/시니어 질문 미리보기

> Q: `MockMvc`와 `WebTestClient`를 한 줄로 구분하면?
> 의도: servlet MVC와 reactive test 도구의 기본 축 구분 확인
> 핵심: `MockMvc`는 MVC 서버 테스트, `WebTestClient`는 reactive/WebFlux에서 많이 쓰는 테스트 클라이언트다.

> Q: `WebTestClient`는 WebFlux에서만 쓸 수 있나?
> 의도: 기본 분기와 확장 분기를 함께 구분하는지 확인
> 핵심: 기본 학습 분기는 WebFlux 쪽이지만, Spring MVC를 `MockMvc` 뒤에 두고 `WebTestClient` API로 검증하는 연결도 가능하다.

> Q: `WebClient`와 `WebTestClient`는 무엇이 다른가?
> 의도: 운영 코드용 client와 테스트 도구 구분 확인
> 핵심: 전자는 실제 외부 호출용, 후자는 테스트 검증용이다.

## 한 줄 정리

처음에는 "`내 서버가 servlet MVC인가, WebFlux인가`"를 먼저 보고, MVC면 `MockMvc`, reactive endpoint면 `WebTestClient`로 출발하면 `MockMvc`와 client 계열 도구를 섞어 부르는 혼동이 크게 줄어든다.
