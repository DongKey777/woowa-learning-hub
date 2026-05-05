---
schema_version: 3
title: Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유 프라이머
concept_id: spring/requestbody-400-before-controller-primer
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/roomescape
- missions/baseball
- missions/blackjack
review_feedback_tags:
- requestbody-pre-controller-400
- message-conversion-first-split
- bindingresult-boundary
aliases:
- spring requestbody pre-controller 400
- requestbody 400 before controller
- controller log missing requestbody 400
- json parse error spring
- requestbody empty body 400 spring
- dto conversion failure 400 spring
- requestbody 400 vs 415 first split
- message conversion failure spring
- httpmessagenotreadableexception requestbody
- pre-validation 400 requestbody
symptoms:
- 컨트롤러 첫 줄 로그가 안 찍히는데 POST 요청이 바로 400으로 끝나요
- '@Valid를 붙였는데도 validation 메시지 대신 JSON parse error만 보여요'
- BindingResult를 붙여도 body 파싱 실패는 왜 못 잡는지 헷갈려요
intents:
- definition
- troubleshooting
prerequisites:
- spring/modelattribute-vs-requestbody-binding-primer
- spring/spring-mvc-request-lifecycle-basics
next_docs:
- spring/valid-400-vs-message-conversion-400-primer
- spring/spring-bindingresult-local-validation-400-primer
- spring/requestbody-415-unsupported-media-type-primer
linked_paths:
- contents/spring/spring-valid-400-vs-message-conversion-400-primer.md
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/spring/spring-requestbody-415-unsupported-media-type-primer.md
- contents/spring/spring-bindingresult-local-validation-400-primer.md
- contents/spring/spring-localdate-localtime-json-400-cheatsheet.md
- contents/spring/spring-mvc-request-lifecycle-basics.md
- contents/spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md
- contents/spring/spring-mvc-controller-basics.md
- contents/spring/spring-validation-binding-error-pipeline.md
- contents/spring/spring-content-negotiation-pitfalls.md
- contents/spring/spring-exception-handling-basics.md
- contents/network/http-request-response-headers-basics.md
confusable_with:
- spring/requestbody-415-unsupported-media-type-primer
- spring/valid-400-vs-message-conversion-400-primer
- spring/spring-bindingresult-local-validation-400-primer
- spring/controller-not-hit-cause-router
- spring/json-request-400-cause-router
forbidden_neighbors: []
expected_queries:
- Spring에서 @RequestBody 요청이 컨트롤러 전에 400이면 어디부터 봐야 해?
- JSON parse error가 보일 때 @Valid가 왜 안 타는지 설명해줘
- BindingResult가 있는데도 body 파싱 실패를 못 잡는 이유가 뭐야?
- requestbody 400과 415를 처음 어떻게 나눠 봐야 해?
- roomescape나 blackjack 미션에서 컨트롤러 로그가 안 찍히는 POST 400은 무슨 단계 문제야?
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 `@RequestBody` 요청에서 컨트롤러 로그가 안
  찍히고 `400`이 먼저 나갈 때, 문제를 service나 validation으로 바로
  오인하지 않도록 message conversion 단계부터 보게 만드는 primer다.
  `JSON parse error`, `@Valid 전에 400`, `BindingResult가 못 잡는다`,
  roomescape/baseball/blackjack 미션의 POST 요청 디버깅 같은 자연어 질문이
  이 문서의 핵심 검색 표면이다.
---
# Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리

> 한 줄 요약: README 첫 증상표의 `컨트롤러 로그 안 찍힘`, `@RequestBody인데 컨트롤러 전에 400이 나요`, `JSON parse error가 보여요`, `body를 안 보냈는데 왜 BindingResult도 못 타요?`는 `Content-Type`보다 먼저 Spring의 body 값 해석 / DTO 변환 단계에서 **DTO 변환 실패**가 났는지부터 보게 하는 entrypoint다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드: 폼/query 바인딩과 JSON body를 한 장으로 분리하기](./spring-modelattribute-vs-requestbody-binding-primer.md)
- [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer: JSON인데 왜 `Content-Type`에서 막히나](./spring-requestbody-415-unsupported-media-type-primer.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)
- [Spring `LocalDate`/`LocalTime` JSON 파싱 `400` 자주 나는 형식 모음](./spring-localdate-localtime-json-400-cheatsheet.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
- [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)
- [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)
- [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)
- [spring 카테고리 인덱스](./README.md)

## 이 라우트에서 보는 위치

- 현재 문서: 1단계. `@RequestBody인데 컨트롤러 전에 400이 나요`를 먼저 가른다.
- README 바인딩 첫 증상표 순서: `컨트롤러 로그 안 찍힘`, `@RequestBody인데 컨트롤러 전에 400이 나요`, `JSON parse error가 보여요`면 이 문서를 먼저 보고, 검색어가 직접 `415`/`Content-Type`을 말하면 바로 415 primer로 옮긴다.
- 다음 문서: [2단계 `@Valid` primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- README 복귀: [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)

retrieval-anchor-keywords: @requestbody 400 왜 바로 나요, 컨트롤러 로그 안 찍힘, @requestbody인데 컨트롤러 전에 400이 나요, json parse error가 보여요, requestbody body 비어있어요, requestbody empty body 400 spring, requestbody missing body spring, json null body bindingresult, malformed json 400 spring, dto 변환 실패 400 spring, requestbody 400 vs 415 first split, @valid 전에 400 나요, @requestbody @valid 언제 타요, 처음 requestbody 400 헷갈려요, httpmessageconverter 뭐예요

## 핵심 개념

처음에는 이렇게 기억하면 된다.

- `@RequestBody`에서 "`왜 `@Valid`가 안 타지?`"가 먼저 떠오르면, 이 문서는 "`DTO도 못 만들어서 validation 전에 끊긴 경우`"를 먼저 가르는 입구다. DTO 생성까지 성공한 뒤의 다음 분기는 바로 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)로 이어 본다.
- `@RequestBody`는 "컨트롤러가 raw body를 직접 읽는 기능"이 아니다.
- Spring이 먼저 요청 body를 읽고, JSON을 DTO로 바꾸는 데 성공해야 컨트롤러 메서드를 호출한다.
- binding / message conversion 단계에서 실패하면 컨트롤러 / 서비스 단계는 시작도 못 하고 **DTO 변환 실패 `400`** 같은 오류 응답이 먼저 나간다.
- 이때는 아직 DTO 자체가 없어서 `@Valid`도, `BindingResult`도 개입할 자리가 없다.
- 그래서 body가 아예 없거나, 비어 있거나, JSON 본문이 `null`인 경우도 보통은 Bean Validation보다 먼저 "`DTO를 지금 만들 수 있나?`" 단계에서 갈린다.

단, 이 문서의 기본 설명은 일반적인 `@RequestBody` JSON DTO + 기본 `required=true` 흐름을 기준으로 한 **보통의 경우**다. `@RequestBody(required = false)`, `Optional`, `JsonNode`, 커스텀 converter 설계에서는 결과가 달라질 수 있다.

즉 "`400`이 났다"와 "내 컨트롤러 코드가 실행됐다"는 같은 말이 아니다. RoomEscape 관리자 API에서 `POST /admin/reservations`를 보낼 때도 JSON 모양이나 타입이 틀리면 `create()` 메서드 첫 줄 로그조차 안 찍힐 수 있다. 이 문서의 초점은 그중에서도 **DTO를 아예 못 만든 경우**이고, DTO를 만든 뒤 제약을 어긴 **validation 실패**는 바로 다음 읽기 경로인 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)로 이어진다.

## 먼저 보는 증상 문장

초급자 검색 진입 문장은 README와 같은 증상 문장 세트로 아래처럼 고정한다.

- `컨트롤러 로그 안 찍힘`
- `@RequestBody인데 컨트롤러 전에 400이 나요`
- `JSON parse error가 보여요`
- `JSON인데 415 Unsupported Media Type가 떠요`
- `Content-Type: application/json 안 붙였는데 415예요`
- `Content-Type 때문에 막힌 것 같아요`

읽는 순서를 한 줄로 고정하면 더 덜 헷갈린다.

1. `400`이 났을 때 먼저 "`DTO를 아예 못 만들었나, 아니면 만든 뒤 `@Valid`에서 막혔나?`"를 이 문서와 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md) 한 쌍으로 자른다.
2. 그다음 `@ModelAttribute`와 `@RequestBody` 중 지금 값이 어디로 들어오는지 확인한다.
3. 여기서 `400`/`415`/`302`/`403` 중 어디서 끊겼는지 가른다.

## 한눈에 보기

요청 생명주기 기준으로 보면 이 문서는 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)의 **"argument binding / message conversion = DTO 변환 실패 축"**만 먼저 떼어 보는 카드다.

```text
HTTP 요청
  -> security / filter
  -> DispatcherServlet
  -> HttpMessageConverter가 body 읽기
  -> binding / message conversion
  -> validation
  -> controller 호출
```

| 학습자가 보통 이렇게 말해요 | 먼저 붙잡을 질문 | 더 가까운 원인 |
|---|---|---|
| `컨트롤러 로그 안 찍힘`, `@RequestBody인데 컨트롤러 전에 400이 나요` | "컨트롤러 전에 DTO를 아예 못 만든 건가?" | **DTO 변환 실패** 후보 |
| "`BindingResult`가 왜 못 받았지?" | "아직 DTO 생성 전이라 `BindingResult`까지 못 간 건가?" | validation 이전 message conversion 실패 가능성 |
| "`로그인했는데도 `/login`으로 가요`", "`권한 없다고 떠요`" | "body 읽기 전에 security에서 막힌 건가?" | security / filter 단계 |
| `JSON인데 415 Unsupported Media Type가 떠요`, `Content-Type 때문에 막힌 것 같아요` | "이 요청을 JSON이라고 제대로 선언했나?" | body 형식 선언 실패 |
| `JSON parse error가 보여요`, `날짜/enum/숫자에서 자꾸 400 나요` | "JSON 문법이나 값 형식이 DTO 타입과 안 맞나?" | **DTO 변환 실패** |
| `@Valid는 붙였는데 field error가 보여요`, `입력값 규칙에서 막힌 것 같아요` | "DTO는 만들었고 그다음 validation에서 막힌 건가?" | **validation 실패** |

짧게 외우면 된다.

- `JSON인데 415 Unsupported Media Type가 떠요`면 body 값보다 body 형식 선언부터 본다.
- `JSON parse error가 보여요`, `날짜/enum/숫자에서 자꾸 400 나요`면 **DTO 변환 실패**부터 본다.
- `@Valid는 붙였는데 field error가 보여요`면 **validation 실패**까지는 온 것이다.

`415`만 따로 빠르게 보고 싶다면 [Spring `@RequestBody 415 Unsupported Media Type` 초급 primer](./spring-requestbody-415-unsupported-media-type-primer.md)로 바로 옮겨도 된다. 이 문서는 `400`과 `415`를 함께 가르는 입구이고, 새 primer는 `Content-Type`과 `consumes` 축만 더 짧게 붙잡는다.

## `400` parse/type vs `415` media-type

초급자에게 가장 자주 필요한 첫 분기도 README와 같은 문장으로 잡으면 된다.
`@RequestBody인데 컨트롤러 전에 400이 나요`, `JSON parse error가 보여요`는 이 표의 왼쪽으로 보고,
`JSON인데 415 Unsupported Media Type가 떠요`, `Content-Type: application/json 안 붙였는데 415예요`, `Content-Type 때문에 막힌 것 같아요`는 오른쪽으로 보면 된다.

| 비교 축 | `@RequestBody인데 컨트롤러 전에 400이 나요` / `JSON parse error가 보여요` | `JSON인데 415 Unsupported Media Type가 떠요` / `Content-Type: application/json 안 붙였는데 415예요` / `Content-Type 때문에 막힌 것 같아요` |
|---|---|---|
| Spring이 먼저 못한 일 | JSON을 읽어 DTO로 바꾸기 | 이 body를 어떤 형식으로 읽을지 결정하기 |
| 학습자에게 먼저 확인시킬 질문 | "JSON 문법이나 값 형식이 DTO 타입과 맞나요?" | "이 요청이 JSON이라고 헤더로 제대로 선언됐나요?" |
| 화면에서 자주 같이 보이는 단서 | `JSON parse error`, `Cannot deserialize`, 날짜/enum/숫자 변환 실패 | `Content-Type 'text/plain' is not supported`, `application/json` 누락, `consumes` mismatch |
| 가장 먼저 손댈 곳 | 닫는 괄호, 쉼표, 필드 타입, 날짜/시간 형식 | 요청 헤더의 `Content-Type`, 컨트롤러의 `consumes` 계약 |
| body를 JSON처럼 예쁘게 적어도 해결되나 | 아니오. 값 형식까지 DTO 타입과 맞아야 한다 | 아니오. 헤더가 틀리면 body 모양보다 먼저 막힌다 |
| beginner 한 줄 판단 | "내용은 읽으려 했는데 값 해석에 실패했다" | "애초에 이 형식 body는 받지 않겠다고 판단했다" |

## `BindingResult` 경계 먼저 붙이기

여기서 `BindingResult` 경계까지 같이 붙이면 첫 분기가 더 빨라진다.

| 지금 실패한 곳 | DTO는 만들어졌나 | `@Valid` 가능? | `BindingResult` 개입 가능? | 다음 문서 |
|---|---|---|---|---|
| JSON 문법 / 타입 변환 / `HttpMessageConverter` | 아니오 | 아니오 | 아니오 | 이 문서 계속 |
| body 없음 / empty body / JSON `null` 때문에 DTO 인자를 못 세움 | 보통 아니오 | 보통 아니오 | 보통 아니오 | 이 문서 계속 |
| validation 실패 + `BindingResult` 없음 | 예 | 예 | 아니오 | [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md) |
| validation 실패 + `BindingResult` 있음 | 예 | 예 | 예 | [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md) |

즉 "`BindingResult`가 있는데도 왜 컨트롤러 전에 끝났지?"라고 느껴지면, 초급자는 먼저 **validation 이전의 message conversion 실패**를 의심하면 된다.

아래 두 문장이 이 문서와 연결 문구의 기준이다.

- 이 문서는 "`DTO 변환 실패라서 `@Valid`도 못 탔다`" 쪽을 설명한다.
- `@Valid` 이후 규칙 위반은 "`validation 실패`"로 따로 부른다.

초급자 handoff 문장으로는 아래 한 줄이 가장 중요하다.

- **message conversion `400`은 `BindingResult`가 받아 줄 수 없고, `BindingResult`는 DTO를 만든 뒤의 validation 실패에서만 힘을 쓴다.**

## `@ModelAttribute`와 헷갈릴 때

`@ModelAttribute`와 헷갈리는 초급자라면 한 번 더 이렇게 끊으면 된다.

| 헷갈리는 지점 | `@ModelAttribute` | `@RequestBody` |
|---|---|---|
| 값이 오는 곳 | query string, form field | JSON body |
| 먼저 볼 실패 | 파라미터 이름, 문자열 -> 타입 변환 | JSON 문법, DTO 타입, `Content-Type` |
| 대표 예시 | `GET /admin/reservations?date=2026-05-01` | `POST /admin/reservations` + JSON |

이 비교만 따로 보고 싶다면 [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드](./spring-modelattribute-vs-requestbody-binding-primer.md)로 바로 이동하면 된다.

단, RoomEscape 관리자 API에서는 그보다 더 앞에서 Spring Security가 막을 수도 있다.
즉 `POST /admin/reservations`가 컨트롤러에 안 들어간다고 해서 곧바로 `@RequestBody`만 의심하면 안 되고, `302 /login`/`401`/`403`인지 `400`/`415`인지부터 갈라야 한다.

## 검색 query와 생성 JSON을 먼저 분리하기

같은 `/admin/reservations` endpoint 계열을 한 쌍으로 묶어 기억하면 더 덜 헷갈린다.

| 장면 | 값이 놓이는 자리 | 먼저 볼 것 | 대표 어노테이션 |
|---|---|---|---|
| `GET /admin/reservations?date=2026-05-01&name=neo` 검색 | URL query string | 파라미터 이름, 문자열 변환 | `@ModelAttribute` |
| `POST /admin/reservations` 예약 생성 | JSON body | JSON 문법, DTO 타입, `Content-Type` | `@RequestBody` |

즉 검색 query에서 막혔는지, 생성 JSON에서 막혔는지를 먼저 가르면 "`둘 다 reservations인데 왜 원인이 다르지?`"라는 혼동을 줄일 수 있다. 그리고 생성 JSON에서 막혔다면 다시 "`DTO 변환 실패냐, validation 실패냐`"로 한 번 더 쪼개면 된다.

## 왜 컨트롤러 / 서비스 전에 끝나는가

Spring MVC는 컨트롤러 메서드를 호출하기 전에 파라미터를 다 준비한다. `@RequestBody CreateReservationRequest request`가 있다면 Spring은 대략 아래 순서로 움직인다.

1. 요청의 `Content-Type`을 보고 어떤 converter를 쓸지 고른다.
2. body를 읽어 JSON으로 해석한다.
3. JSON 값을 DTO 필드 타입에 맞게 변환한다.
4. 여기까지 성공해야 `create(request)`를 호출한다.

관리자 API라면 이 순서 앞에 한 칸이 더 있다.

1. Spring Security가 로그인 여부와 `ADMIN` 권한을 먼저 본다.
2. 그다음에야 `Content-Type`과 body를 보고 converter를 고른다.
3. binding / message conversion이 된다.
4. 마지막에 컨트롤러 / 서비스 단계가 시작된다.

그래서 아래처럼 컨트롤러 첫 줄에 로그를 넣어도, binding / message conversion에서 실패하면 이 로그는 찍히지 않는다.

```java
@PostMapping("/admin/reservations")
public ReservationResponse create(@RequestBody CreateReservationRequest request) {
    log.info("controller entered");
    return reservationService.create(request);
}
```

초급자 기준으로는 "`service 로직이 잘못됐다`"보다 "`binding / message conversion 단계에서 아직 컨트롤러 메서드 인자를 못 만들었다`"가 더 정확한 설명이다. 이번 축 이름으로 부르면 "`컨트롤러 전에 DTO 변환 실패가 났다`"에 가깝다.

이 경계 때문에 `@Valid @RequestBody CreateReservationRequest request, BindingResult bindingResult`처럼 선언해 두었더라도, JSON 문법 오류나 `LocalDate` 파싱 실패는 `bindingResult.hasErrors()`까지 데려올 수 없다. `BindingResult`는 "만들어진 DTO의 validation 에러 바구니"이지, "DTO를 못 만든 body 파싱 에러 바구니"는 아니다.

## missing body, empty body, JSON `null`은 왜 보통 더 앞에서 갈리나

학습자는 아래 세 장면을 자주 "`어차피 body 문제니까 `BindingResult`가 잡아야 하는 것 아닌가요?`"로 묶는다.

| 학습자가 말하는 장면 | 실제 body 상태 | 보통 먼저 갈리는 위치 | `BindingResult`까지 오나 |
|---|---|---|---|
| "`body`를 아예 안 보냈는데 왜 바로 `400`이에요?" | body 자체가 없음 | required body 판단 / message conversion 시작점 | 보통 아니오 |
| "`body`는 보냈는데 빈 문자열인데요" | empty body, 공백 body | 읽을 JSON 값이 없음 | 보통 아니오 |
| "`null`만 보냈는데 왜 field validation이 아니에요?" | JSON 토큰은 있지만 값이 `null` | DTO 인스턴스 생성 가능 여부 또는 non-null body 기대 계약 | 보통 아니오 |

핵심은 세 경우 모두 "`필드 하나하나 검증하기 전에, request body를 컨트롤러 인자로 성립시킬 수 있나?`"를 먼저 묻는다는 점이다.

- missing body: 읽을 본문 자체가 없다.
- empty body: 본문 스트림은 있지만 JSON 값으로 해석할 내용이 없다.
- explicit JSON `null`: JSON 문법은 맞아도, 많은 DTO 시그니처에서는 "`객체`를 기대했는데 `null` 토큰이 왔다"는 쪽에서 먼저 끊긴다.

그래서 초급자에게는 "`null`도 JSON이니까 `@NotBlank`가 잡겠지`"보다 "`필드 validation은 역직렬화가 끝난 뒤 시작된다`"라고 가르치는 편이 덜 위험하다.

물론 예외는 있다.

- `@RequestBody(required = false)`로 바꾸면 missing body를 `null` 파라미터로 받을 수 있다.
- 파라미터 타입이 nullable하게 설계되어 있거나 converter 커스터마이징이 있으면 explicit JSON `null`이 그대로 들어올 수 있다.
- 이런 경우에는 그다음 `@NotNull` 같은 제약이나 애플리케이션 로직이 개입할 수 있다.

하지만 일반적인 beginner JSON DTO 엔드포인트에서는 "`body 없음 / 비어 있음 / `null``"을 **필드 validation 문제보다 앞단 문제**로 분리하는 편이 더 정확하다.

## RoomEscape 관리자 API mini bridge

RoomEscape 미션에서 가장 많이 찾게 되는 장면은 `POST /admin/reservations` 요청 한 장면이다. 초급자 기준으로는 정상 요청, 타입 오류 요청, `Content-Type` 오류 요청을 한 표에 같이 두는 편이 훨씬 덜 헷갈린다.

| 상황 | 요청 예시 | 먼저 볼 포인트 | 이번 분류 이름 |
|---|---|---|---|
| 정상 JSON | `Content-Type: application/json` + `{"roomId":1,"date":"2026-05-01","time":"18:00","partySize":2}` | JSON 문법 OK, DTO 타입 OK | 컨트롤러 진입 후 비즈니스 로직 진행 |
| 타입 오류 JSON | `Content-Type: application/json` + `{"roomId":"vip-room","date":"tomorrow","time":"six","partySize":"two"}` | JSON은 맞지만 `Long`, `LocalDate`, `LocalTime`, `int` 변환 실패 | DTO 변환 실패 `400` |
| 잘못된 `Content-Type` | `Content-Type: text/plain` + JSON처럼 생긴 body | JSON converter를 고를 수 있는지 | `415 Unsupported Media Type` |

여기서 하나만 더 붙이면 축이 깔끔해진다.

- 타입 오류 JSON: DTO 변환 실패
- 타입은 맞지만 `@NotBlank`, `@Positive`를 어김: validation 실패

짧게 기억하면 된다.

- body 내용이 틀리면 binding / message conversion `400` 후보다.
- body 형식 선언이 틀리면 media type 계약 위반인 `415` 후보다.
- 정상 JSON이라도 그다음엔 validation이나 컨트롤러 / 서비스 단계에서 다른 오류가 날 수 있다.

위 표를 더 짧게 접으면 이렇게 된다.

| 내가 본 첫 단서 | 지금 붙일 임시 라벨 | 바로 손댈 곳 |
|---|---|---|
| `Content-Type`이 `application/json`이 아님 | `415 media-type 실패` | 헤더, `consumes`, 클라이언트 설정 |
| `Content-Type`은 맞는데 `Cannot deserialize`, 날짜/숫자 parse 오류 | `400 parse/type 실패` | JSON 값 형식, DTO 필드 타입 |

## JSON, 타입, `Content-Type` 예시로 나눠 보기

### 먼저 증상 문장으로 자르기

검색어가 아래처럼 보이면 이 문서의 주제에 가깝다.

| 학습자 증상 문장 | 이 문서에서 먼저 보는 축 |
|---|---|
| `컨트롤러 로그 안 찍힘` | 컨트롤러 이전 DTO 변환 실패 |
| `@RequestBody인데 바로 400` | message conversion / JSON 파싱 |
| `@Valid가 안 타는 것 같아요` | validation 전 단계에서 DTO 생성 실패 |
| `415도 같이 보여요` | `Content-Type` 계약 |

### 1. JSON 문법이 깨진 경우

```json
{
  "date": "2026-05-01",
  "time": "18:00"
```

닫는 중괄호가 없거나 쉼표 위치가 틀리면 JSON 자체를 읽지 못한다. 이때는 DTO 구조를 보기 전에 **문법 오류**로 끝난다. 컨트롤러는 호출되지 않는다.

### 2. JSON은 맞지만 DTO 타입이 안 맞는 경우

```java
public record CreateReservationRequest(
        Long roomId,
        LocalDate date,
        LocalTime time,
        int partySize
) {
}
```

이 타입 변환 실패와 같이 놓고 보면 missing body, empty body, JSON `null`도 같은 축으로 기억하기 쉽다.

| 요청 장면 | 역직렬화 결과 | 먼저 떠올릴 질문 |
|---|---|---|
| body 없음 | DTO 시작 자체를 못 함 | "required body가 빠졌나?" |
| empty body | 읽을 JSON 값이 없음 | "빈 본문이라 converter가 멈췄나?" |
| body가 `null` | JSON 토큰은 읽었지만 DTO 객체를 못 세움 또는 null body로 판단 | "객체 DTO를 기대했나, nullable body를 허용했나?" |
| body가 `{\"age\":\"old\"}` | 필드 타입 변환 실패 | "문자열을 숫자로 못 바꿨나?" |
| body가 `{\"name\":\"\"}` | DTO 생성 성공 후 field validation 단계 가능 | "이제 `@NotBlank` 같은 제약 차례인가?" |

```json
{
  "roomId": "vip-room",
  "date": "tomorrow",
  "time": "six",
  "partySize": "two"
}
```

이 JSON은 모양은 JSON이지만 DTO 타입과 맞지 않는다.

| 필드 | 기대 타입 | 잘못 들어온 값 | 왜 실패하는가 |
|---|---|---|---|
| `roomId` | `Long` | `"vip-room"` | 숫자로 바꿀 수 없다 |
| `date` | `LocalDate` | `"tomorrow"` | 기본 날짜 형식으로 파싱할 수 없다 |
| `time` | `LocalTime` | `"six"` | 시간 형식이 아니다 |
| `partySize` | `int` | `"two"` | 숫자 변환에 실패한다 |

즉 "JSON이 맞다"와 "DTO로 바꿀 수 있다"는 다른 문제다.

## `Content-Type`이 잘못된 경우

```http
POST /admin/reservations
Content-Type: text/plain
```

body 안에 JSON처럼 생긴 문자열을 넣어도 `Content-Type`이 `application/json`이 아니면 Spring이 JSON converter를 선택하지 못할 수 있다. 이때도 컨트롤러 전에 막힌다.

다만 여기서 초급자가 꼭 같이 기억해야 할 점이 있다.

- JSON 문법/타입 변환 실패는 보통 `400`
- `Content-Type` 자체가 계약과 안 맞으면 종종 `415 Unsupported Media Type`

즉 `Content-Type` 문제도 "컨트롤러 전에 실패"라는 점은 같지만, **항상 400은 아니다**. `400`만 찾다가 `415`를 놓치면 원인 파악이 늦어진다.

같은 endpoint 비교는 바로 위 `RoomEscape 관리자 API mini bridge` 표를 다시 보면 된다.

## 흔한 오해와 함정

- "관리자 API에서 컨트롤러 로그가 안 찍히면 무조건 `@RequestBody` 문제다"
  아니다. 먼저 Spring Security가 `302 /login`, `401`, `403`으로 끝냈을 수도 있다.

- "`400`이면 컨트롤러에서 예외를 던진 것이다"
  아니다. `@RequestBody`의 경우 컨트롤러에 들어오기 전 message conversion에서 끝날 수 있다.

- "필드명이 조금 달라도 null로만 들어갈 것이다"
  경우에 따라 일부 필드는 null이 될 수 있지만, 타입 변환이 필요한 필드나 필수 생성자 파라미터에서는 아예 요청 전체가 실패할 수 있다.

- "`Content-Type`만 맞으면 JSON은 다 읽힌다"
  아니다. `Content-Type`은 입장권이고, 실제 JSON 문법과 DTO 타입 일치는 별도 검사다.

- "`@Valid`와 `@RequestBody 400`은 완전히 같은 문제다"
  아니다. body를 DTO로 못 만들면 변환 실패고, DTO는 만들었지만 제약을 어기면 validation 실패다.

- "`BindingResult`를 붙였으니 이제 모든 `400`을 컨트롤러에서 받을 수 있다"
  아니다. `BindingResult`는 validation 실패의 로컬 분기 도구이고, message conversion `400`은 그보다 앞에서 끝난다.

- "`body`가 비거나 `null`이면 일단 DTO는 만들어졌고 field validation이 돈다"
  보통은 아니다. 일반적인 `@RequestBody` JSON DTO에서는 missing body, empty body, explicit JSON `null`이 필드 validation보다 먼저 갈린다. 단 `required = false`나 nullable 설계면 예외가 생길 수 있다.

## 실무에서 쓰는 모습

RoomEscape 관리자 예약 생성 API를 예로 들면 초반 점검 순서는 이쪽이 안전하다.

1. `Content-Type: application/json`이 붙었는지 본다.
2. JSON이 문법적으로 닫혀 있는지 본다.
3. DTO 필드 타입이 `Long`, `LocalDate`, `LocalTime`, `int` 같은 변환 가능한 값인지 본다.
4. 그래도 실패하면 그다음에 `@Valid` 제약이나 `@RestControllerAdvice` 응답 모양을 본다.

초급자에게 가장 실용적인 감각은 이것이다.

- 컨트롤러 로그가 안 찍히면 컨트롤러 / 서비스보다 binding / message conversion을 먼저 본다.
- 날짜, 시간, enum, 숫자 필드는 "문자열이 비슷해 보여도" 자주 깨진다.
- Postman, 브라우저 fetch, 프론트엔드 axios에서 `Content-Type` 누락이 생각보다 흔하다.

## 더 깊이 가려면

- 요청 전체 흐름에서 지금 위치를 다시 잡고 싶으면 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)를 먼저 본다.
- 관리자 인증과 body binding 실패를 한 요청 파이프라인으로 같이 보고 싶다면 [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)를 먼저 읽는다.
- `400`이 다른 `404`, `409`와 어떻게 다른 응답 의미인지 함께 잡고 싶으면 [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)로 이어간다.
- 바인딩 실패와 validation 실패 순서를 더 자세히 보고 싶으면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)로 이어간다.
- `@Valid` `400`과 message conversion `400`을 로그 문구 기준으로 빠르게 가르는 카드가 필요하면 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)를 본다.
- "`BindingResult`가 왜 어떤 `400`에는 안 먹는지"를 controller 로컬 처리 관점에서 이어 보고 싶으면 [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)를 바로 이어 읽는다.
- `Content-Type` 확인은 끝났고 이제 "`Accept`는 또 뭐예요?", "`produces`는 언제 봐요?"가 헷갈리면 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)로 넘어간다.
- `Accept`, `Content-Type`, `415` 경계를 한 장으로 다시 붙이고 싶으면 [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)와 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)를 같이 본다.

## 면접/시니어 질문 미리보기

**Q. `@RequestBody` 요청에서 컨트롤러 로그가 안 찍히는데 왜 `400`이 날 수 있나요?**
컨트롤러 호출 전에 `HttpMessageConverter`가 binding / message conversion을 수행하는데, 이 단계에서 JSON 문법 오류나 타입 변환 실패가 나면 컨트롤러 / 서비스 단계까지 도달하지 못한다.

**Q. JSON 문법 오류와 validation 실패는 어떻게 다른가요?**
문법 오류는 DTO를 만들기 전 실패고, validation 실패는 DTO 생성 후 `@Valid` 같은 제약 검사에서 실패한다.

**Q. `BindingResult`가 있는데도 왜 JSON parse `400`이 컨트롤러로 안 들어오나요?**
`BindingResult`는 DTO를 만든 뒤 생긴 validation 에러를 담는 도구다. JSON parse 오류나 타입 변환 실패는 DTO를 만들기 전에 끝나므로 `BindingResult`가 끼어들지 못한다.

**Q. body를 안 보냈거나 `null`만 보냈는데 왜 `BindingResult`가 못 잡나요?**
보통은 필드 validation 전에 "`이 body로 DTO 인자를 성립시킬 수 있나?`" 단계에서 먼저 갈리기 때문이다. missing body, empty body, explicit JSON `null`은 일반적인 `@RequestBody` DTO 기준으로 역직렬화/required-body 판단 축에 더 가깝다.

**Q. `Content-Type`이 틀리면 왜 `400`이 아니라 `415`가 날 수도 있나요?**
이 경우는 "본문 값이 틀렸다"보다 "이 형식의 본문은 받지 않겠다"는 media type 계약 위반에 가깝기 때문이다.

## 한 줄 정리

`@RequestBody`의 `400`은 컨트롤러 / 서비스보다 먼저 binding / message conversion 단계에서 나는 경우가 많으므로, JSON 문법, DTO 타입, `Content-Type`을 먼저 분리해서 봐야 한다.
