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

retrieval-anchor-keywords: content negotiation pitfalls, spring 415 unsupported media type, @requestbody 415 beginner, content-type application json why, accept vs content-type difference, httpmessageconverter media type, produces consumes mismatch, requestbody media type mismatch, controller 전에 415, spring beginner negotiation, json body not supported, what is content negotiation, spring mvc lifecycle basics binding 단계, binding 단계에서 415 왜, requestbody 400 vs 415 first hit, content-type 415 왜 나요, 처음 content negotiation 헷갈려요

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
3. "`json인데 unsupported media type`" 같은 증상 문장 그대로 빠르게 정리하고 싶으면 먼저 [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)를 본다.
4. 그다음 "`JSON 내용` 문제가 아니라 `Content-Type` 계약 문제구나"가 보이면 이 문서로 돌아와 `Accept`와 `Content-Type`, `consumes`를 같이 본다.

`Spring MVC 요청 생명주기 기초`에서 보던 큰 흐름으로 다시 붙이면, 이 문서는 그중 4번 `argument binding / message conversion` 칸을 확대해서 보는 카드다. 즉 "컨트롤러 전에 왜 막혔지?"까지는 lifecycle basics로 판단하고, "그중에서도 왜 `415`였지?"는 여기서 `Content-Type`, `Accept`, converter 선택으로 더 잘게 나누면 된다.

초급자 기준으로는 여기서 원인을 좁힌 뒤 다시 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)의 4번 `argument binding / message conversion` 칸으로 돌아가 "이 실패가 binding 쪽인지, validation 쪽인지, 아니면 controller 이후 문제인지"를 한 번 더 확인하면 흐름이 덜 끊긴다. `415`는 그 binding 칸 안에서도 `Content-Type` 계약과 converter 선택이 어긋난 경우라고 붙여 두면 기억하기 쉽다.

증상 문장 기준으로 더 짧게 자르면 아래 route가 먼저다.

| 처음 검색하거나 말한 문장 | first hit | 왜 이 순서가 안전한가 |
|---|---|---|
| "`json`인데 `415 Unsupported Media Type`" | [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md) | body 값보다 `Content-Type`/`consumes` 계약부터 확인하게 한다 |
| "`@RequestBody`인데 controller 전에 `400`", "`JSON parse error`" | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md) | `Content-Type`은 맞는 편인데 DTO 변환이나 validation 전 경계에서 실패했는지 먼저 자른다 |
| "`Accept`랑 `Content-Type`이 왜 달라요?`", "`produces`/`consumes`가 왜 필요해요?`" | 이 문서 계속 | 이제는 초급 첫 분기보다 negotiation 계약 전체를 볼 단계다 |

짧게 외우면 이렇다.

- `400`: `Content-Type`은 맞는 편인데 JSON 문법, DTO 타입, validation 쪽을 먼저 의심한다.
- `415`: `Content-Type`, `consumes`, message converter 선택을 먼저 의심한다.
- `406`: 응답 쪽 `Accept` 계약을 먼저 의심한다.

즉 lifecycle basics 한 장에서는 "4번 binding 단계에서 막혔다"까지 찾고, 이 문서에서는 그 binding 단계를 다시 "`400`인지 `415`인지", "`요청 body 해석` 문제인지 "`응답 형식 협상` 문제인지"로 세분화한다고 생각하면 된다.

## 깊이 들어가기

### 1. `Accept`는 응답 형식을 고른다

클라이언트가 JSON을 원하면 JSON converter가, HTML을 원하면 view resolver가 개입한다.

### 2. `Content-Type`은 요청 바디 해석을 고른다

요청이 JSON인데 form으로 해석하려 하면 실패한다.

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
