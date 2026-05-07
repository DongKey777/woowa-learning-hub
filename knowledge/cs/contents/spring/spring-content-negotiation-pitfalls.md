---
schema_version: 3
title: Spring Content Negotiation Pitfalls
concept_id: spring/spring-content-negotiation-pitfalls
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- accept-vs-content-type
- produces-consumes-mismatch
- converter-selection-debugging
aliases:
- spring content negotiation pitfalls
- spring 415 unsupported media type
- accept vs content-type difference
- httpmessageconverter media type
- produces consumes mismatch
- requestbody media type mismatch
- controller-before-415 unsupported media type
- spring negotiation deep dive
- 406 not acceptable spring
- html response instead of json api
- json html response mismatch
- content negotiation advanced
symptoms:
- JSON 요청인데 415나 406이 번갈아 보여서 어디부터 봐야 할지 모르겠어
- Accept와 Content-Type을 헷갈려서 왜 HTML이 왔는지 설명이 안 돼
- API인 줄 알았는데 login HTML이나 text/html 응답이 와서 negotiation 문제인지 헷갈려
intents:
- definition
- troubleshooting
- deep_dive
prerequisites:
- spring/requestbody-415-unsupported-media-type-primer
- spring/requestbody-400-before-controller-primer
- network/browser-devtools-accept-vs-content-type-mini-card
next_docs:
- spring/handlermethodreturnvaluehandler-chain
- spring/mvc-exception-resolver-chain-contract
- spring/spring-api-401-vs-browser-302-beginner-bridge
linked_paths:
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/spring/spring-requestbody-400-before-controller-primer.md
- contents/spring/spring-requestbody-415-unsupported-media-type-primer.md
- contents/spring/spring-mvc-request-lifecycle-basics.md
- contents/spring/spring-mvc-request-lifecycle.md
- contents/spring/spring-handlermethodreturnvaluehandler-chain.md
- contents/spring/spring-mvc-exception-resolver-chain-contract.md
- contents/spring/spring-conversion-service-formatter-binder-pipeline.md
- contents/spring/spring-validation-binding-error-pipeline.md
- contents/spring/spring-api-401-vs-browser-302-beginner-bridge.md
- contents/network/http-request-response-headers-basics.md
- contents/network/browser-devtools-accept-vs-content-type-mini-card.md
confusable_with:
- spring/requestbody-415-unsupported-media-type-primer
- spring/requestbody-400-before-controller-primer
- spring/spring-api-401-vs-browser-302-beginner-bridge
- spring/handlermethodreturnvaluehandler-chain
forbidden_neighbors: []
expected_queries:
- Spring에서 415 Unsupported Media Type과 406 Not Acceptable을 어떤 기준으로 나눠 봐야 해?
- Accept와 Content-Type이 헷갈릴 때 Spring MVC에서 어떤 순서로 디버깅하면 돼?
- JSON API인데 HTML 응답이 올 때 content negotiation 문제와 login redirect 문제를 어떻게 구분해?
- produces consumes 설정과 HttpMessageConverter 선택이 응답 형식에 어떻게 영향을 주는지 설명해줘
- Spring content negotiation이 request body 파싱 실패와 response format 협상에 어떻게 연결되는지 알고 싶어
contextual_chunk_prefix: |
  이 문서는 Spring MVC에서 `Accept`, request `Content-Type`, response
  `Content-Type`, `produces`, `consumes`, `HttpMessageConverter` 선택이
  400/406/415와 HTML vs JSON 응답 차이로 어떻게 이어지는지 설명하는
  advanced deep dive다. 초급 415 primer와 API redirect 브리지를 더 깊은
  negotiation 관점으로 이어 준다.
---
# Spring Content Negotiation Pitfalls

> 한 줄 요약: Content negotiation은 같은 엔드포인트라도 `Accept`, `Content-Type`, converter 조합에 따라 전혀 다른 응답이 나오게 하므로, API 계약과 렌더링 계약을 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드: 폼/query 바인딩과 JSON body를 한 장으로 분리하기](./spring-modelattribute-vs-requestbody-binding-primer.md)
> - [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
> - [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer: JSON인데 왜 `Content-Type`에서 막히나](./spring-requestbody-415-unsupported-media-type-primer.md)
> - [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring `HandlerMethodReturnValueHandler` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)
> - [Browser DevTools `Accept` vs Response `Content-Type` 미니 카드](../network/browser-devtools-accept-vs-content-type-mini-card.md)

retrieval-anchor-keywords: content negotiation pitfalls, spring 415 unsupported media type, @requestbody 415 beginner, content-type application json why, accept vs content-type difference, httpmessageconverter media type, produces consumes mismatch, requestbody media type mismatch, controller 전에 415 unsupported media type, spring beginner negotiation, json인데 415 unsupported media type가 떠요, content-type: application/json 안 붙였는데 415예요, content-type 때문에 막힌 것 같아요, requestbody 400 vs 415 first hit, content-type 415 왜 나요, accept content-type 헷갈려요, 406이 왜 나와요, 406 not acceptable spring, json 대신 html 와요, produces consumes 뭐예요, 처음 content negotiation 헷갈려요

## 핵심 개념

Content negotiation은 "어떤 형식으로 요청하고 어떤 형식으로 응답할지"를 결정한다.

- `Accept`: 클라이언트가 받고 싶은 형식
- `Content-Type`: 클라이언트가 보낸 형식
- `produces` / `consumes`: 서버가 허용하는 형식
- `HttpMessageConverter`: 실제 직렬화/역직렬화 담당

이게 어긋나면 406, 415, 400 같은 상태 코드가 나온다.

## 초급자 입구: `@RequestBody 415`에서 들어왔을 때

이 문서는 원래 content negotiation 전체를 다루는 심화 카드다. 그런데 초급자는 보통 "`@RequestBody`에서 왜 `415 Unsupported Media Type`이 나요?"라는 증상으로 먼저 들어온다. 그때는 아래 순서로 끊어 읽는 편이 안전하다.

1. JSON body와 query/form 바인딩이 섞여 있으면 [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드](./spring-modelattribute-vs-requestbody-binding-primer.md)부터 본다.
2. `400`인지 `415`인지 먼저 갈라야 하면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)에서 첫 분기를 잡는다.
3. "`JSON인데 415 Unsupported Media Type가 떠요`", "`Content-Type: application/json 안 붙였는데 415예요`", "`Content-Type 때문에 막힌 것 같아요`" 같은 증상 문장 그대로 빠르게 정리하고 싶으면 먼저 [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)를 본다.
4. `415`는 아닌데 "`406이 왜 나와요`", "`406 Not Acceptable`", "`json 대신 html 와요`"처럼 응답 형식이 어긋난 말이 먼저 나오면 README 기준 `1.6단계 handoff`라고 생각하고 이 문서로 바로 들어온다.
5. 그다음 "`JSON 내용` 문제가 아니라 `Content-Type` 또는 `Accept` 계약 문제구나"가 보이면 이 문서에서 `Accept`, request `Content-Type`, response `Content-Type`, `consumes`를 같이 본다.

`Spring MVC 요청 생명주기 기초`에서 보던 큰 흐름으로 다시 붙이면, 이 문서는 그중 4번 `argument binding / message conversion` 칸을 확대해서 보는 카드다. 즉 "컨트롤러 전에 왜 막혔지?"까지는 lifecycle basics로 판단하고, "그중에서도 왜 `415`였지?"는 여기서 `Content-Type`, `Accept`, converter 선택으로 더 잘게 나누면 된다.

초급자 기준으로는 여기서 원인을 좁힌 뒤 다시 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)의 4번 `argument binding / message conversion` 칸으로 돌아가 "이 실패가 binding 쪽인지, validation 쪽인지, 아니면 controller 이후 문제인지"를 한 번 더 확인하면 흐름이 덜 끊긴다. `415`는 그 binding 칸 안에서도 `Content-Type` 계약과 converter 선택이 어긋난 경우라고 붙여 두면 기억하기 쉽다.

증상 문장 기준으로 더 짧게 자르면 아래 route가 먼저다.

| 처음 검색하거나 말한 문장 | first hit | 왜 이 순서가 안전한가 |
|---|---|---|
| "`JSON인데 415 Unsupported Media Type가 떠요`", "`Content-Type: application/json 안 붙였는데 415예요`", "`Content-Type 때문에 막힌 것 같아요`" | [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md) | body 값보다 `Content-Type`/`consumes` 계약부터 확인하게 한다 |
| "`@RequestBody`인데 controller 전에 `400`", "`JSON parse error`" | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md) | `Content-Type`은 맞는 편인데 DTO 변환이나 validation 전 경계에서 실패했는지 먼저 자른다 |
| "`api인데 로그인 html 와요`", "`fetch가 401 대신 login html 받아요`", "`api인데 302 /login 보여요`" | [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md) | negotiation보다 먼저 security/browser redirect 계약이 API에 섞였는지 자르게 한다 |
| "`406이 왜 나와요?`", "`json 대신 html 와요`" | 이 문서 계속 | 이제는 body 파싱보다 응답 형식 협상과 `Accept`/`produces`를 같이 볼 단계다 |
| "`Accept`랑 `Content-Type`이 왜 달라요?`", "`accept/content-type 헷갈려요`" | 이 문서 계속 | 요청 쪽 기대와 실제 응답, 요청 body 선언을 한 번에 분리해야 한다 |
| "`produces`/`consumes`가 왜 필요해요?`" | 이 문서 계속 | 초급 첫 분기를 넘어서 HTTP 계약 전체를 붙여 볼 단계다 |

짧게 외우면 이렇다.

- `400`: `Content-Type`은 맞는 편인데 JSON 문법, DTO 타입, validation 쪽을 먼저 의심한다.
- `415`: `Content-Type`, `consumes`, message converter 선택을 먼저 의심한다.
- `406`: 응답 쪽 `Accept` 계약을 먼저 의심한다.

즉 lifecycle basics 한 장에서는 "4번 binding 단계에서 막혔다"까지 찾고, 이 문서에서는 그 binding 단계를 다시 "`400`인지 `415`인지", "`요청 body 해석` 문제인지 "`응답 형식 협상` 문제인지"로 세분화한다고 생각하면 된다.

## 깊이 들어가기

### 1. `Accept`는 응답 형식을 고른다

클라이언트가 JSON을 원하면 JSON converter가, HTML을 원하면 view resolver가 개입한다.

초급자가 "`406이 왜 나와요?`"라고 물을 때는 이렇게 먼저 끊으면 된다.

- `Accept: application/json`인데 서버가 JSON을 만들 수 없거나 `produces = text/html` 같은 계약만 열려 있으면 `406 Not Acceptable`이 날 수 있다.
- `Accept`가 넓게 `*/*`로 열려 있으면 서버가 HTML이나 다른 기본 응답을 골라도 이상하지 않을 수 있다.
- `406`은 보통 "`요청 body를 못 읽었다`"가 아니라 "`응답 형식을 못 맞췄다`" 쪽 질문이다.

여기서 초급자가 가장 자주 섞는 오진이 "`API가 HTML을 줬으니 무조건 content negotiation 문제겠지`"다. 하지만 아래 단서가 먼저 보이면 `406`이나 `produces`보다 security/browser redirect 축이 먼저다.

| 먼저 보이는 단서 | 더 안전한 첫 해석 | 먼저 갈 문서 |
|---|---|---|
| `Location: /login`, login form HTML, redirect chain 뒤 최종 `200 text/html` | API가 브라우저용 login redirect를 따라가 login page HTML을 받은 것일 수 있다 | [Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지](./spring-api-401-vs-browser-302-beginner-bridge.md) |
| redirect는 없고 response `Content-Type: text/html`, controller/view 계약도 HTML 쪽으로 열려 있음 | negotiation이나 `produces` 계약을 먼저 본다 | 이 문서 계속 |

즉 "`json 대신 html`"은 symptom일 뿐이고, 원인은 둘 중 하나일 수 있다.

- negotiation mismatch: `Accept`, `produces`, view/body 계약이 어긋났다.
- security redirect mix: API가 `401` JSON 대신 `/login` HTML로 흘렀다.

### 2. `Content-Type`은 요청 바디 해석을 고른다

요청이 JSON인데 form으로 해석하려 하면 실패한다.

그래서 "`accept/content-type 헷갈려요`"라는 말이 나오면 질문을 둘로 찢는 편이 빠르다.

| 내가 먼저 확인할 헤더 | 답하는 질문 | 흔한 증상 문장 |
|---|---|---|
| `Content-Type` | "내가 보낸 body를 서버가 어떤 형식으로 읽어야 하나?" | "`JSON인데 415 Unsupported Media Type가 떠요`", "`Content-Type: application/json 안 붙였는데 415예요`", "`@RequestBody`인데 controller 전에 막혀요" |
| `Accept` | "나는 어떤 응답을 받고 싶다고 말했나?" | "`406이 왜 나와요`", "`json 대신 html 와요`" |

이 표는 entrypoint primer의 표현을 이 심화 카드로 다시 이어 붙이는 다리다. 다만 실제 응답이 왜 HTML이 되었는지는 login redirect, 예외 resolver, fallback view처럼 다른 층이 섞일 수 있으므로, `Accept`만 보고 모든 원인을 단정하면 안 된다.

### 3. converter 우선순위가 중요하다

Spring은 등록된 converter 중 맞는 것을 찾아 사용한다.

- Jackson JSON
- String converter
- byte array converter
- XML converter

### 4. `produces`와 `consumes`는 API 계약이다

```java
@PostMapping(value = "/orders", consumes = "application/json", produces = "application/json")
public OrderResponse create(@RequestBody CreateOrderRequest request) {
    ...
}
```

이 계약이 명확해야 잘못된 클라이언트 요청을 일찍 막을 수 있다.

### 5. 406/415/500을 구분해야 한다

- 406: 클라이언트가 원하는 응답 형식을 못 맞춤
- 415: 서버가 요청 형식을 못 받음
- 500: converter나 렌더링 내부 오류

처음에는 아래처럼 기억하면 충분하다.

| 상태 코드 | 초급자 첫 질문 | 먼저 보는 칸 |
|---|---|---|
| `406` | "왜 내가 원하는 JSON이 안 오지?" | `Accept`, `produces`, 실제 response `Content-Type` |
| `415` | "왜 이 body를 JSON으로 안 읽지?" | request `Content-Type`, `consumes` |
| `500` | "계약은 맞았는데 내부에서 무엇이 깨졌지?" | converter 내부 예외, 렌더링 예외 |

## 실전 시나리오

### 시나리오 1: 같은 URL인데 어떤 클라이언트는 JSON, 어떤 클라이언트는 HTML이 나온다

이는 negotiation 결과가 다르기 때문이다.

### 시나리오 2: `@RestController`인데도 HTML 에러가 나온다

예외 resolver나 fallback view resolver가 개입했을 수 있다.

이건 [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)와 같이 본다.

### 시나리오 3: `Accept: */*`가 들어와 예상과 다른 converter가 선택된다

client library 기본값이 문제일 수 있다.

### 시나리오 4: 한 엔드포인트에서 XML과 JSON을 같이 열었다

운영은 편하지만 테스트와 문서화가 어려워진다.

## 코드로 보기

### produces and consumes

```java
@PostMapping(
    value = "/users",
    consumes = MediaType.APPLICATION_JSON_VALUE,
    produces = MediaType.APPLICATION_JSON_VALUE
)
public UserResponse create(@RequestBody CreateUserRequest request) {
    return userService.create(request);
}
```

### explicit response type

```java
@GetMapping(value = "/users/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
public UserResponse get(@PathVariable Long id) {
    return userService.get(id);
}
```

### custom converter registration

```java
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 명시적 `produces/consumes` | 계약이 선명하다 | 선언이 늘어난다 | public API |
| 암묵적 negotiation | 편하다 | 예측이 어렵다 | 내부 도구 |
| 단일 media type | 단순하다 | 유연성이 낮다 | 대부분의 서비스 |
| 다중 media type | 호환성이 좋다 | 테스트가 복잡하다 | 레거시 호환 |

핵심은 content negotiation을 "자동 편의"가 아니라 **HTTP 계약의 일부**로 보는 것이다.

## 꼬리질문

> Q: `Accept`와 `Content-Type`의 차이는 무엇인가?
> 의도: 요청/응답 방향 이해 확인
> 핵심: Accept는 응답, Content-Type은 요청 바디다.

> Q: 406과 415는 각각 언제 발생하는가?
> 의도: negotiation 실패 원인 확인
> 핵심: 406은 응답 형식 미스, 415는 요청 형식 미스다.

> Q: `produces`와 `consumes`는 왜 중요한가?
> 의도: API 계약 이해 확인
> 핵심: 서버가 허용하는 media type을 명시한다.

> Q: converter 우선순위가 왜 문제를 만들 수 있는가?
> 의도: 직렬화/역직렬화 경로 이해 확인
> 핵심: 같은 타입도 다른 converter가 선택될 수 있다.

## 한 줄 정리

Content negotiation은 Accept, Content-Type, converter 선택이 합쳐진 계약이므로, 명시하지 않으면 같은 엔드포인트도 다른 의미로 동작할 수 있다.
