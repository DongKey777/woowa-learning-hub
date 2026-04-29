# Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer

> 한 줄 요약: `@Valid`는 DTO 바인딩이 끝난 뒤에만 탈 수 있으므로, 같은 `400 Bad Request`라도 먼저 DTO를 못 만든 **DTO 변환 실패**인지 DTO를 만든 뒤 규칙을 어긴 **validation 실패**인지부터 갈라야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)
- [Spring `MethodArgumentNotValidException` vs `HandlerMethodValidationException` 초급 브리지: `@Valid` request body와 method validation `400`를 한 표로 잇기](./spring-methodargumentnotvalidexception-vs-handlermethodvalidationexception-beginner-bridge.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring RoomEscape validation `400` vs business conflict `409` 분리 primer](./spring-roomescape-validation-400-vs-business-conflict-409-primer.md)
- [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)
- [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)
- [spring 카테고리 인덱스](./README.md)

## 이 라우트에서 보는 위치

- 현재 문서: 2단계. DTO 변환 실패와 validation 실패를 가른다.
- 이전 문서: [1단계 `@RequestBody` 400 primer](./spring-requestbody-400-before-controller-primer.md)
- 다음 문서: [3단계 `BindingResult` primer](./spring-bindingresult-local-validation-400-primer.md)
- README 복귀: [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)

## 먼저 되돌아갈지 10초 체크

아래 증상이 먼저 보이면 이 문서보다 [1단계 `@RequestBody` 400 primer](./spring-requestbody-400-before-controller-primer.md)로 바로 되돌아가는 편이 빠르다.

| 지금 보이는 단서 | 먼저 갈 곳 |
|---|---|
| "`컨트롤러 로그가 아예 안 찍혀요`" | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md) |
| "`JSON parse error`", "`Cannot deserialize`", "`HttpMessageNotReadableException`" | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md) |
| "`date` 형식이 틀렸어요", "`enum`/숫자 변환이 안 돼요" | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md) |
| "`DTO는 만들어진 것 같은데 `@NotBlank`/`@Positive`에서 막혀요`" | 이 문서 계속 읽기 |

retrieval-anchor-keywords: 왜 @valid 안 타요, @valid 언제 타요, @notblank 왜 안 먹어요, spring binding failure vs validation failure, spring 400 first branch beginner, methodargumentnotvalidexception beginner, httpmessagenotreadableexception beginner, 같은 400인데 뭐가 다른가요, dto 변환 실패 vs validation 실패, binding 실패면 @valid 안 타요, validation message not blank beginner, json parse error 400 spring, 날짜 형식 틀리면 @valid 안 타요, requestbody 400 primer reverse link, roomescape admin 400 primer

## 이 문서가 바로 맞는 질문

README 바인딩 증상표 기준으로는 아래 검색 문장 세트에 바로 답하려는 문서다.

- "`왜 `@Valid` 안 타요?`"
- "`같은 `400`인데 뭐가 다른가요?`"
- "`@NotBlank`가 왜 안 먹어요?`"

처음 분기는 하나만 잡으면 된다.

- JSON/body를 DTO로 못 만들었으면 `@Valid` 전에 멈춘다.
- DTO를 만든 뒤 규칙을 어겼으면 그때 `@Valid`를 탄다.

## 핵심 개념

처음에는 `@Valid`를 "항상 실행되는 검사"로 생각하지 않는 게 중요하다.

`@Valid`는 **아무 때나 타는 게 아니라**, Spring이 먼저 요청 body를 DTO로 만들어야만 탈 수 있다.

즉 순서는 이렇다.

1. JSON body를 읽고 DTO로 바인딩한다.
2. 바인딩이 성공하면 `@Valid`가 돈다.
3. `@Valid`도 통과하면 컨트롤러/서비스 로직으로 간다.

그래서 같은 `400`이어도 질문이 먼저 갈린다.

- "DTO를 아예 못 만들었나?"
- "DTO는 만들었는데 제약을 어겼나?"

RoomEscape 관리자 예약 생성 API를 예로 들면, `POST /admin/reservations` 요청에서 `date`가 `"tomorrow"`면 DTO 생성 단계에서 막힐 수 있고, `name`이 빈 문자열이면 DTO 생성은 됐지만 `@NotBlank` 검증에서 막힐 수 있다.

## 한눈에 보기

먼저 검색 문장을 분기표로 바로 바꾸면 이렇다.

| 내가 지금 하는 말 | 첫 판단 |
|---|---|
| "`왜 `@Valid` 안 타요`" | DTO 생성 전에 막혔는지부터 본다 |
| "`같은 `400`인데 뭐가 달라요`" | DTO 변환 실패 `400`인지 validation `400`인지 먼저 가른다 |
| "`@NotBlank`가 왜 안 먹어요`" | 제약이 고장난 게 아니라 `@Valid`까지 못 갔는지 먼저 본다 |

```text
HTTP 요청
  -> JSON body를 DTO로 바인딩
     -> 실패: @Valid 못 탐, DTO 변환 실패 400
     -> 성공: @Valid 검사
         -> 실패: validation 400
         -> 성공: controller/service 로직 실행
```

| 지금 실패한 곳 | DTO는 만들어졌나 | `@Valid` 가능? | `BindingResult` 개입 가능? | 대표 예시 |
|---|---|---|---|---|
| JSON/body를 DTO로 바꾸는 바인딩·message conversion 단계 | 아니오 | 아니오 | 아니오 | `"date": "tomorrow"`, JSON parse 오류 |
| DTO 생성 후 제약 검사 단계 | 예 | 예 | `BindingResult` 없으면 아니오, 있으면 예 | `"name": ""`, `"partySize": 0` |

핵심은 "`400`이 났다"보다 먼저 "`@Valid`까지 갔나?`"를 묻는 것이다.

초급자 질문 흐름은 두 갈래만 먼저 고정하면 된다.

1. "`DTO를 아예 못 만들었다`"면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md) 쪽 질문이다.
2. "`DTO는 만들었고 그다음 규칙에서 막혔다`"면 `BindingResult` 없이는 전역 예외 `400`, 있으면 컨트롤러 로컬 분기다. 자세한 비교는 [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나](./spring-bindingresult-local-validation-400-primer.md), 예외 이름 비교는 [Spring `MethodArgumentNotValidException` vs `HandlerMethodValidationException` 초급 브리지](./spring-methodargumentnotvalidexception-vs-handlermethodvalidationexception-beginner-bridge.md)로 이어 본다.

즉 `BindingResult`는 이 둘 중 **DTO를 만든 뒤의 validation `400`에서만** 손을 댈 수 있다. `LocalDate` parse 실패, JSON parse 실패처럼 DTO 생성 전 단계에서 멈춘 `400`에는 끼어들지 못한다. `@RequestBody 400` primer와 같은 기준으로 말하면, `BindingResult`는 "`DTO는 만들어졌나?`가 예일 때만 개입 가능한 handoff"다.

## 상세 분해

초급자 검색 문장으로 바꾸면 이 문서가 맡는 증상은 README 바인딩 증상표와 같은 아래 세 줄이다.

- "왜 `@Valid` 안 타요?"
- "같은 `400`인데 뭐가 다른가요?"
- "`@NotBlank`가 왜 안 먹어요?"

그리고 이 둘은 결국 같은 질문이다.

- "`@Valid` 안 타요" = DTO 생성 전에 멈췄는지 묻는 질문
- "`같은 `400`인데 뭐가 다른가요`" = DTO 생성 실패 `400`과 validation `400`을 갈라 달라는 질문

### 1. 바인딩이 실패하면 `@Valid`는 못 탄다

초급자 관점에서는 이 한 줄을 먼저 기억하면 된다.

- JSON 문법이 깨졌다
- 문자열을 `LocalDate`, `LocalTime`, `Long`, `enum`으로 못 바꿨다
- `HttpMessageConverter`가 DTO를 끝까지 만들지 못했다

이때는 `@NotBlank`, `@Positive`가 붙어 있어도 아직 볼 차례가 오지 않는다.

즉 "`제약 애너테이션이 왜 반응이 없지?`"가 아니라, **그 제약 검사까지 도달하지 못했을 수 있다**.

### 2. 바인딩이 성공해야 `@Valid`가 돈다

DTO가 만들어지면 그다음은 Bean Validation 차례다.

예를 들어 DTO가 아래와 같다고 하자.

```java
public record CreateReservationRequest(
        @NotBlank String name,
        @Positive Long roomId,
        @Positive int partySize
) {
}
```

이때 JSON 문법도 맞고 타입도 맞다면 `@Valid`는 탈 수 있다.

그 뒤에 이런 규칙 위반을 검사한다.

- `name`이 빈 문자열이다
- `roomId`가 `0` 이하이다
- `partySize`가 `0` 이하이다

즉 "`빈 문자열`", "`길이 제한`", "`최소/최대값`"은 보통 `@Valid`가 탄 뒤에야 드러난다.

### 3. `400` 디버깅 첫 분기는 "형식이냐 규칙이냐"다

초급자 디버깅은 길게 시작할 필요가 없다. 아래 두 질문이면 충분하다.

| 먼저 던질 질문 | 그렇다면 어디부터 보나 |
|---|---|
| JSON이나 타입을 DTO로 만들 수 있었나 | 아니오라면 DTO 변환 실패부터 본다 |
| DTO는 만들어졌고 그다음 규칙 위반이 났나 | 예라면 `@Valid` 제약부터 본다 |

짧게 바꾸면 이렇다.

- 형식 문제면 `@Valid` 전에 막힌다.
- 규칙 문제면 `@Valid`를 탄 뒤에 막힌다.

### 4. "`@NotBlank`를 붙였는데 왜 안 먹어요?"라고 느껴질 때

이 증상은 초급자가 validation과 변환 실패를 가장 자주 섞는 지점이다.

- `name = ""`처럼 문자열 제약을 어긴 경우라면 `@Valid`가 탈 가능성이 크다
- `date = "tomorrow"`나 `time = "six"`처럼 타입 변환이 먼저 깨지면 `@Valid` 자체를 못 탈 수 있다

즉 제약 애너테이션이 "고장난 것"보다, **그 제약까지 도달할 DTO 생성이 끝났는지**를 먼저 확인하는 편이 빠르다.

## 로그와 응답 메시지로 빠르게 가르는 법

### 1. DTO 변환 실패는 "읽다가 못 만들었다"는 표현이 많다

이쪽은 JSON이나 타입 변환이 깨졌을 때 보인다.

- `JSON parse error`
- `Cannot deserialize value`
- `Cannot construct instance`
- `HttpMessageNotReadableException`

초급자 감각으로는 "`DTO 안 필드 규칙`"보다 "`JSON body 자체를 못 읽었다`"에 가깝다. 이 경우는 `@Valid`를 탔다고 보기 어렵다.

예를 들어 이런 요청이다.

```json
{
  "roomId": 1,
  "date": "tomorrow",
  "time": "18:00",
  "partySize": 2
}
```

`date`가 `LocalDate`인데 `"tomorrow"`가 들어오면, validation까지 가기 전에 변환 단계에서 멈출 수 있다. 즉 `@Valid`는 못 탄다.

### 2. `@Valid` validation 실패는 "만들긴 만들었는데 규칙 위반" 표현이 많다

이쪽은 DTO가 이미 만들어졌다는 뜻이다. 그래서 메시지가 필드 규칙 중심으로 보인다.

- `must not be blank`
- `must be greater than 0`
- `size must be between ...`
- `MethodArgumentNotValidException`
- `Field error in object ...`

예를 들어 DTO가 아래처럼 생겼다고 하자.

```java
public record CreateReservationRequest(
        @NotBlank String name,
        @Positive Long roomId,
        @Positive int partySize
) {
}
```

이때 이런 요청은 validation 쪽에 더 가깝다.

```json
{
  "name": "",
  "roomId": 1,
  "partySize": 0
}
```

JSON 문법은 맞고 타입도 맞는다. 대신 제약 조건을 어겨서 `@Valid` `400`이 난다.

### 3. 응답 본문이 단순 `400`이어도 로그 힌트는 남을 수 있다

팀의 `@RestControllerAdvice`가 모든 `400`을 같은 JSON 모양으로 감쌀 수도 있다. 그러면 응답만 봐서는 둘이 비슷해 보인다.

그래도 초급자 첫 분리 기준은 남는다.

- 응답/로그에 field validation 문구가 보이면 `@Valid` 쪽
- 응답/로그에 JSON parse, deserialize, read message 문구가 보이면 message conversion 쪽

즉 **커스텀 에러 응답이 같아도 내부 예외 이름이나 로그 키워드는 다를 수 있다.**

## 30초 분기표

`400`을 봤을 때 초급자가 제일 먼저 자를 분기는 아래 한 표면 충분하다.

| 보이는 증상 | 첫 판단 | 바로 볼 것 |
|---|---|---|
| `JSON parse error`, `Cannot deserialize`, `HttpMessageNotReadableException` | DTO 변환 실패로 `@Valid` 전에 멈췄을 가능성 큼 | 요청 JSON, 날짜/시간/enum/숫자 타입 |
| `must not be blank`, `must be greater than 0`, `Field error` | `@Valid`를 탄 뒤 실패했을 가능성 큼 | DTO 제약 애너테이션, 입력값 |
| `@Valid` 실패인데 컨트롤러 안으로 들어왔다 | `BindingResult`가 validation 실패를 로컬로 받은 경우일 수 있음 | `@Valid` 바로 뒤 `BindingResult` 유무 |
| 컨트롤러 첫 줄 로그가 안 찍힘 | 둘 다 가능 | 로그 키워드로 DTO 변환 실패인지 validation 실패인지 추가 분기 |
| `@NotBlank`를 붙였는데 메시지가 안 보임 | DTO 변환에서 먼저 실패했을 수 있음 | DTO 생성 자체가 됐는지 확인 |

## RoomEscape 예시로 분리하기

| 요청 예시 | 먼저 실패할 가능성이 큰 곳 | 이유 |
|---|---|---|
| `"date": "next friday"` | DTO 변환 실패 | `LocalDate`로 바꿀 수 없다 |
| `"time": "six"` | DTO 변환 실패 | `LocalTime` 형식이 아니다 |
| `"name": ""` | `@Valid` | 빈 문자열 금지 제약을 어긴다 |
| `"partySize": 0` | `@Valid` | 양수 제약을 어긴다 |
| JSON 마지막 중괄호 누락 | DTO 변환 실패 | JSON 문법 자체가 깨졌다 |

RoomEscape 관리자 API에서 초급자가 가장 많이 보는 오해는 이것이다.

- 날짜 형식이 틀렸는데 "`@NotNull`이 안 먹었다"라고 본다
- 사실은 `@NotNull` 전에 DTO 생성이 실패해서 validation까지 못 갔을 수 있다

그래서 "`제약 애너테이션이 왜 반응이 없지?`"라는 느낌이 들면, 먼저 DTO 생성 실패 가능성을 의심하는 편이 빠르다. 초급자 디버깅 첫 분기는 "`@Valid`를 탔나, 못 탔나`"다.

## 흔한 오해와 함정

- "`400`이면 무조건 `@Valid`다"
  아니다. JSON 파싱이나 타입 변환 실패면 `@Valid` 전에 끝난다.

- "컨트롤러 로그가 안 찍히면 validation은 아니다"
  둘 다 컨트롤러 호출 전에 끝날 수 있어서, 로그 유무만으로는 완전히 구분되지 않는다. 메시지 내용을 같이 봐야 한다.

- "`@NotBlank`가 붙어 있으니 날짜 문자열 오류도 validation으로 잡힌다"
  아니다. 날짜 문자열을 `LocalDate`로 못 바꾸면 validation 단계까지 가지 못할 수 있다. 즉 `@Valid`를 못 탄다.

- "응답 JSON 모양이 같으면 같은 종류의 실패다"
  아니다. 팀이 공통 에러 포맷으로 감쌌을 수 있다. 내부 예외 이름과 메시지를 같이 봐야 한다.

## 실무에서 쓰는 모습

초급자 점검 순서를 짧게 정리하면 이렇다.

1. 응답이나 서버 로그에 `must not`, `field error`, `MethodArgumentNotValidException`이 보이면 "`@Valid`를 탔다"라고 보고 제약부터 본다.
2. `JSON parse`, `deserialize`, `HttpMessageNotReadableException`이 보이면 "`@Valid`를 못 탔다"라고 보고 DTO 변환 실패부터 본다.
3. 날짜, 시간, enum, 숫자 타입이 있으면 DTO 변환 실패 가능성을 먼저 높게 둔다.
4. 빈 문자열, 길이 제한, 최소값/최대값 규칙이면 `@Valid` 가능성을 먼저 본다.

RoomEscape 기준으로는 "예약 시간 형식이 이상하다"는 변환 문제일 때가 많고, "이름이 비었다"나 "인원 수가 0이다"는 validation 문제일 때가 많다.

## 더 깊이 가려면

- `@RequestBody`가 왜 컨트롤러 전에 끝나는지부터 다시 잡고 싶으면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)를 먼저 본다.
- binding과 validation의 순서를 더 자세히 보고 싶으면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)로 이어간다.
- 같은 예약 생성 API에서 validation `400`과 서비스 business conflict `409`를 한 번 더 가르고 싶으면 [Spring RoomEscape validation `400` vs business conflict `409` 분리 primer](./spring-roomescape-validation-400-vs-business-conflict-409-primer.md)를 본다.
- 예외를 `@RestControllerAdvice`에서 어떻게 한 응답 형식으로 모으는지 보고 싶으면 [Spring 예외 처리 기초](./spring-exception-handling-basics.md)를 본다.
- `Content-Type`과 `415`를 같이 정리하고 싶으면 [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)를 함께 본다.

## 면접/시니어 질문 미리보기

**Q. 같은 `400`인데 message conversion과 `@Valid` 실패를 왜 나눠 봐야 하나요?**  
실패 지점이 달라서 디버깅 시작점이 달라진다. 전자는 DTO 생성 문제, 후자는 DTO 생성 후 규칙 검사 문제다.

**Q. `MethodArgumentNotValidException`과 `HttpMessageNotReadableException`은 감각적으로 어떻게 다른가요?**  
앞은 "필드 규칙을 어겼다"에 가깝고, 뒤는 "JSON body를 DTO로 읽지 못했다"에 가깝다.

**Q. 컨트롤러 로그가 안 찍히면 무조건 message conversion인가요?**  
그렇게 단정하면 안 된다. `@Valid`도 컨트롤러 메서드 본문 전에 끝날 수 있어서, 예외 이름과 메시지 힌트를 같이 봐야 한다.

## 한 줄 정리

같은 `400`이라도 바인딩에 실패하면 `@Valid`를 못 타고, DTO 생성 뒤 규칙을 어기면 그때 `@Valid`가 타므로 "`형식 실패냐, 규칙 실패냐`"를 첫 분기로 잡아야 한다.
