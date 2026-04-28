# Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리

> 한 줄 요약: `@RequestBody` 요청이 `400 Bad Request`로 먼저 끝나는 가장 흔한 이유는 Spring이 controller / service 단계에 들어가기 전, binding / message conversion 단계에서 이미 요청 body를 읽지 못해 **DTO 변환 실패**가 났기 때문이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)
- [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드: 폼/query 바인딩과 JSON body를 한 장으로 분리하기](./spring-modelattribute-vs-requestbody-binding-primer.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)
- [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)
- [Spring `LocalDate`/`LocalTime` JSON 파싱 `400` 자주 나는 형식 모음](./spring-localdate-localtime-json-400-cheatsheet.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
- [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: @requestbody 400 왜 바로 나요, @requestbody 400 vs 415 차이, post /admin/reservations requestbody 400, roomescape admin reservations json example, requestbody type mismatch json, wrong content-type 415 spring, unsupported media type why spring, spring content-type application json beginner, 컨트롤러 로그 안 찍힘 requestbody, 컨트롤러 진입 전 400 spring, httpmessageconverter basics, malformed json 400 spring, enum localdate parse 400, spring mvc requestbody 처음 배우는데, dto 변환 실패 400 spring

## 핵심 개념

처음에는 이렇게 기억하면 된다.

- `@RequestBody`는 "컨트롤러가 raw body를 직접 읽는 기능"이 아니다.
- Spring이 먼저 요청 body를 읽고, JSON을 DTO로 바꾸는 데 성공해야 컨트롤러 메서드를 호출한다.
- binding / message conversion 단계에서 실패하면 controller / service 단계는 시작도 못 하고 **DTO 변환 실패 `400`** 같은 오류 응답이 먼저 나간다.
- 이때는 아직 DTO 자체가 없어서 `@Valid`도, `BindingResult`도 개입할 자리가 없다.

즉 "`400`이 났다"와 "내 컨트롤러 코드가 실행됐다"는 같은 말이 아니다. RoomEscape 관리자 API에서 `POST /admin/reservations`를 보낼 때도 JSON 모양이나 타입이 틀리면 `create()` 메서드 첫 줄 로그조차 안 찍힐 수 있다. 이 문서의 초점은 그중에서도 **DTO를 아예 못 만든 경우**이고, DTO를 만든 뒤 제약을 어긴 **validation 실패**는 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)로 이어진다.

초급자 검색 문장으로 바꾸면 이 문서가 직접 받는 질문은 아래와 같다.

- "컨트롤러 로그가 왜 안 찍혀요?"
- "`@RequestBody`인데 왜 컨트롤러 진입 전에 `400`이 나요?"
- "JSON 보냈는데 왜 `@Valid`도 못 타요?"

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

| 보이는 현상 | 첫 분기 | 먼저 볼 것 |
|---|---|---|
| `302`/`401`/`403` | 아직 body 단계 전 | security / filter |
| `415 Unsupported Media Type` | body 형식 선언 실패 | `Content-Type: application/json` |
| `400` + JSON parse / 날짜 / enum / 숫자 단서 | **DTO 변환 실패** | JSON 문법, 필드명, 타입 |
| `400` + `@Valid`/field error 단서 | **validation 실패** | 제약 애너테이션, 입력값 |

짧게 외우면 된다.

- `415`면 body 형식 선언부터 본다.
- `400`인데 parse/type 단서가 보이면 **DTO 변환 실패**부터 본다.
- `400`인데 `@Valid` 단서가 보이면 **validation 실패**까지는 온 것이다.

## `400` parse/type vs `415` media-type

초급자에게 가장 자주 필요한 건 "`400`과 `415`를 한 번에 어떻게 가르지?"다. 그래서 아래 decision table을 먼저 붙잡으면 좋다.

| 비교 축 | `400 Bad Request` parse/type 실패 | `415 Unsupported Media Type` 실패 |
|---|---|---|
| Spring이 먼저 못한 일 | JSON을 읽어 DTO로 바꾸기 | 이 body를 어떤 형식으로 읽을지 결정하기 |
| 보통 이미 맞춰진 것 | `Content-Type: application/json` | body가 JSON처럼 보여도 상관없다. 핵심은 header 계약 |
| 학습자 화면에서 자주 보이는 단서 | `JSON parse error`, `Cannot deserialize`, 날짜/enum/숫자 변환 실패 | `Content-Type 'text/plain' is not supported`, `application/json` 누락 |
| 가장 먼저 확인할 것 | 닫는 괄호, 쉼표, 필드 타입, 날짜/시간 형식 | 요청 헤더의 `Content-Type`, 컨트롤러의 `consumes` 계약 |
| body를 JSON처럼 예쁘게 적어도 해결되나 | 아니오. 값 형식까지 DTO 타입과 맞아야 한다 | 아니오. 헤더가 틀리면 body 모양보다 먼저 막힌다 |
| beginner 한 줄 판단 | "내용은 읽으려 했는데 값 해석에 실패했다" | "애초에 이 형식 body는 받지 않겠다고 판단했다" |

## `BindingResult` 경계 먼저 붙이기

여기서 `BindingResult` 경계까지 같이 붙이면 첫 분기가 더 빨라진다.

| 지금 실패한 곳 | DTO는 만들어졌나 | `@Valid` 가능? | `BindingResult` 개입 가능? | 다음 문서 |
|---|---|---|---|---|
| JSON 문법 / 타입 변환 / `HttpMessageConverter` | 아니오 | 아니오 | 아니오 | 이 문서 계속 |
| validation 실패 + `BindingResult` 없음 | 예 | 예 | 아니오 | [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md) |
| validation 실패 + `BindingResult` 있음 | 예 | 예 | 예 | [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md) |

즉 "`BindingResult`가 있는데도 왜 컨트롤러 전에 끝났지?"라고 느껴지면, 초급자는 먼저 **validation 이전의 message conversion 실패**를 의심하면 된다.

아래 두 문장이 이 문서와 연결 문구의 기준이다.

- 이 문서는 "`DTO 변환 실패라서 `@Valid`도 못 탔다`" 쪽을 설명한다.
- `@Valid` 이후 규칙 위반은 "`validation 실패`"로 따로 부른다.

초급자 handoff 문장으로는 아래 한 줄이 가장 중요하다.

- **message conversion `400`은 `BindingResult`가 받아 줄 수 없고, `BindingResult`는 DTO를 만든 뒤의 validation 실패에서만 힘을 쓴다.**

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

## 왜 controller / service 전에 끝나는가

Spring MVC는 컨트롤러 메서드를 호출하기 전에 파라미터를 다 준비한다. `@RequestBody CreateReservationRequest request`가 있다면 Spring은 대략 아래 순서로 움직인다.

1. 요청의 `Content-Type`을 보고 어떤 converter를 쓸지 고른다.
2. body를 읽어 JSON으로 해석한다.
3. JSON 값을 DTO 필드 타입에 맞게 변환한다.
4. 여기까지 성공해야 `create(request)`를 호출한다.

관리자 API라면 이 순서 앞에 한 칸이 더 있다.

1. Spring Security가 로그인 여부와 `ADMIN` 권한을 먼저 본다.
2. 그다음에야 `Content-Type`과 body를 보고 converter를 고른다.
3. binding / message conversion이 된다.
4. 마지막에 controller / service 단계가 시작된다.

그래서 아래처럼 컨트롤러 첫 줄에 로그를 넣어도, binding / message conversion에서 실패하면 이 로그는 찍히지 않는다.

```java
@PostMapping("/admin/reservations")
public ReservationResponse create(@RequestBody CreateReservationRequest request) {
    log.info("controller entered");
    return reservationService.create(request);
}
```

초급자 기준으로는 "`service 로직이 잘못됐다`"보다 "`binding / message conversion 단계에서 아직 컨트롤러 메서드 인자를 못 만들었다`"가 더 정확한 설명이다. 이번 축 이름으로 부르면 "`controller 전에 DTO 변환 실패가 났다`"에 가깝다.

이 경계 때문에 `@Valid @RequestBody CreateReservationRequest request, BindingResult bindingResult`처럼 선언해 두었더라도, JSON 문법 오류나 `LocalDate` 파싱 실패는 `bindingResult.hasErrors()`까지 데려올 수 없다. `BindingResult`는 "만들어진 DTO의 validation 에러 바구니"이지, "DTO를 못 만든 body 파싱 에러 바구니"는 아니다.

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
- 정상 JSON이라도 그다음엔 validation이나 controller / service 단계에서 다른 오류가 날 수 있다.

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
| "컨트롤러 로그 안 찍힘" | controller 이전 DTO 변환 실패 |
| "`@RequestBody`인데 바로 `400`" | message conversion / JSON 파싱 |
| "`@Valid`가 안 타는 것 같아요" | validation 전 단계에서 DTO 생성 실패 |
| "`415`도 같이 보여요" | `Content-Type` 계약 |

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

### 3. `Content-Type`이 잘못된 경우

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

## 실무에서 쓰는 모습

RoomEscape 관리자 예약 생성 API를 예로 들면 초반 점검 순서는 이쪽이 안전하다.

1. `Content-Type: application/json`이 붙었는지 본다.
2. JSON이 문법적으로 닫혀 있는지 본다.
3. DTO 필드 타입이 `Long`, `LocalDate`, `LocalTime`, `int` 같은 변환 가능한 값인지 본다.
4. 그래도 실패하면 그다음에 `@Valid` 제약이나 `@RestControllerAdvice` 응답 모양을 본다.

초급자에게 가장 실용적인 감각은 이것이다.

- 컨트롤러 로그가 안 찍히면 controller / service보다 binding / message conversion을 먼저 본다.
- 날짜, 시간, enum, 숫자 필드는 "문자열이 비슷해 보여도" 자주 깨진다.
- Postman, 브라우저 fetch, 프론트엔드 axios에서 `Content-Type` 누락이 생각보다 흔하다.

## 더 깊이 가려면

- 요청 전체 흐름에서 지금 위치를 다시 잡고 싶으면 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)를 먼저 본다.
- 관리자 인증과 body binding 실패를 한 요청 파이프라인으로 같이 보고 싶다면 [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)를 먼저 읽는다.
- `400`이 다른 `404`, `409`와 어떻게 다른 응답 의미인지 함께 잡고 싶으면 [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)로 이어간다.
- 바인딩 실패와 validation 실패 순서를 더 자세히 보고 싶으면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)로 이어간다.
- `@Valid` `400`과 message conversion `400`을 로그 문구 기준으로 빠르게 가르는 카드가 필요하면 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)를 본다.
- "`BindingResult`가 왜 어떤 `400`에는 안 먹는지"를 controller 로컬 처리 관점에서 이어 보고 싶으면 [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)를 바로 이어 읽는다.
- `Accept`, `Content-Type`, `415` 경계를 더 분명히 보고 싶으면 [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)와 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)를 같이 본다.

## 면접/시니어 질문 미리보기

**Q. `@RequestBody` 요청에서 컨트롤러 로그가 안 찍히는데 왜 `400`이 날 수 있나요?**  
컨트롤러 호출 전에 `HttpMessageConverter`가 binding / message conversion을 수행하는데, 이 단계에서 JSON 문법 오류나 타입 변환 실패가 나면 controller / service 단계까지 도달하지 못한다.

**Q. JSON 문법 오류와 validation 실패는 어떻게 다른가요?**  
문법 오류는 DTO를 만들기 전 실패고, validation 실패는 DTO 생성 후 `@Valid` 같은 제약 검사에서 실패한다.

**Q. `BindingResult`가 있는데도 왜 JSON parse `400`이 컨트롤러로 안 들어오나요?**  
`BindingResult`는 DTO를 만든 뒤 생긴 validation 에러를 담는 도구다. JSON parse 오류나 타입 변환 실패는 DTO를 만들기 전에 끝나므로 `BindingResult`가 끼어들지 못한다.

**Q. `Content-Type`이 틀리면 왜 `400`이 아니라 `415`가 날 수도 있나요?**  
이 경우는 "본문 값이 틀렸다"보다 "이 형식의 본문은 받지 않겠다"는 media type 계약 위반에 가깝기 때문이다.

## 한 줄 정리

`@RequestBody`의 `400`은 controller / service보다 먼저 binding / message conversion 단계에서 나는 경우가 많으므로, JSON 문법, DTO 타입, `Content-Type`을 먼저 분리해서 봐야 한다.
