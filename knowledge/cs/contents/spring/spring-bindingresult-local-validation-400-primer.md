# Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드

> 한 줄 요약: "`BindingResult` 있으면 뭐가 달라져요?", "왜 `MethodArgumentNotValidException` 안 나요?", "`@Valid` 실패인데 컨트롤러 안으로 왜 들어와요?", "`BindingResult` 붙였는데 왜 어떤 `400`은 여전히 컨트롤러 전에 끝나요?" 같은 첫 질문은 `@Valid` 옆 `BindingResult`가 validation 실패를 전역 `400` 예외 대신 컨트롤러 로컬 분기로 바꾸는지부터 보면 풀린다.

**난이도: 🟢 Beginner**

이 문서를 바로 찾는 질문:

- "왜 `MethodArgumentNotValidException` 안 나요?"
- "`@Valid` 실패인데 컨트롤러 안으로 왜 들어와요?"
- "`BindingResult` 있으면 뭐가 달라져요?"
- "`BindingResult` 붙였는데 왜 어떤 `400`은 여전히 컨트롤러 전에 끝나요?"

관련 문서:

- [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring `MethodArgumentNotValidException` vs `HandlerMethodValidationException` 초급 브리지: `@Valid` request body와 method validation `400`를 한 표로 잇기](./spring-methodargumentnotvalidexception-vs-handlermethodvalidationexception-beginner-bridge.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)
- [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)
- [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)
- [spring 카테고리 인덱스](./README.md)

## 이 라우트에서 보는 위치

- 현재 문서: 3단계. validation 실패가 전역 예외로 가는지, 컨트롤러 로컬 분기로 들어오는지 가른다.
- 이전 문서: [2단계 `@Valid` primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- 다음 문서: [4단계 `ProblemDetail` handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md)
- README 복귀: [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)

retrieval-anchor-keywords: bindingresult 400 flow, spring bindingresult beginner, bindingresult 있으면 뭐가 달라져요, methodargumentnotvalidexception vs bindingresult, 왜 methodargumentnotvalidexception 안 나요, @valid 실패인데 컨트롤러는 타요, 왜 @valid 실패인데 controller 들어와요, bindingresult 붙였는데 왜 400 먼저 나요, controller local validation handling, validation error local response spring, @valid bindingresult order, requestbody bindingresult 400 spring, controller advice 대신 bindingresult, dto 변환 실패는 왜 before controller, problemdetail validation 400

## 핵심 개념

처음에는 `BindingResult`를 "`검증 실패를 메서드 안으로 들여오는 바구니`"라고 이해하면 된다.

핵심 비교 기준은 하나다. `BindingResult`는 **DTO를 이미 만든 뒤의 validation 실패**에 끼어들고, JSON 문법 오류나 타입 불일치 같은 **DTO 변환 실패**는 여전히 컨트롤러 전에 끝난다.

> 먼저 못 박기: `LocalDate`에 `"tomorrow"`를 넣거나 JSON parse 자체가 깨진 경우는 `BindingResult` 차례가 오기 전에 요청이 종료된다. 이 문서는 그 반대편인 "`DTO는 만들었고, 그다음 validation이 실패한 경우`"를 설명한다.

기본 흐름은 이렇다.

1. Spring이 요청 값을 DTO로 바인딩한다.
2. `@Valid`가 제약을 검사한다.
3. 실패하면 보통 `MethodArgumentNotValidException` 같은 예외로 바뀌고 `400`으로 끝난다.

그런데 `@Valid` 대상 파라미터 바로 뒤에 `BindingResult`를 두면 validation 실패가 예외로 바로 번지지 않고, 컨트롤러 메서드가 호출된 뒤 `bindingResult.hasErrors()`로 로컬 분기할 수 있다.

즉 핵심 차이는 "`검증 실패 = 즉시 전역 400`"이 아니라 "`검증 실패 = 컨트롤러 로컬 분기 가능`"으로 바뀐다는 점이다. 반대로 "`DTO 변환 실패 = `BindingResult`로 받는다`"는 틀린 기억이다. 그 경우는 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)에서 다루는 앞단 문제다.

초급자 질문으로 바꾸면 이 문서가 맡는 증상은 README 바인딩 follow-up 증상표와 같은 아래 네 줄이다.

- "`BindingResult` 있으면 뭐가 달라져요?"
- "왜 `MethodArgumentNotValidException`이 안 나요?"
- "`@Valid` 실패인데 컨트롤러 안으로 왜 들어와요?"
- "`BindingResult` 붙였는데 왜 어떤 `400`은 여전히 컨트롤러 전에 끝나요?"

읽는 순서를 짧게 고정하면 이렇다.

1. 먼저 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)에서 "`이건 validation 실패가 맞다`"를 확인한다.
2. 그다음 이 문서에서 "`validation 실패가 전역 예외로 가는가, 로컬 `BindingResult`로 들어오는가`"를 본다.
3. 마지막에 팀 공통 `400` 응답 모양이 필요하면 [Spring 예외 처리 기초](./spring-exception-handling-basics.md)나 [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md)로 이어간다.

## 한눈에 보기

```text
요청 -> 바인딩 성공 -> @Valid 검사
    -> BindingResult 없음: 예외 발생 -> ControllerAdvice/기본 400
    -> BindingResult 있음: controller 진입 -> if (bindingResult.hasErrors()) 분기
```

| 경우 | DTO는 만들어졌나 | `BindingResult` 개입 가능? | 전역 vs 로컬 |
|---|---|---|---|
| `@Valid` 뒤에 `BindingResult` 없음 | 예 | 아니오 | 전역 예외 `400`으로 간다 |
| `@Valid` 뒤에 `BindingResult` 있음 | 예 | 예 | 컨트롤러 로컬 분기가 가능하다 |
| JSON parse, 타입 변환 같은 앞단 실패 | 아니오 | 아니오 | 컨트롤러 전에 전역 `400`으로 끝난다 |

단, 이것은 **validation 실패** 이야기다. `LocalDate`에 `"tomorrow"`를 넣거나 JSON 중괄호가 깨진 경우처럼 DTO를 아예 못 만든 message conversion/parse 실패는 여전히 컨트롤러 전에 끝난다.

여기서 handoff를 한 문장으로 잡으면 더 덜 헷갈린다.

- `BindingResult`가 없으면: validation 실패가 `MethodArgumentNotValidException`으로 넘어가서 전역 `400` 처리로 이어진다
- `BindingResult`가 있으면: 같은 validation 실패가 먼저 컨트롤러 안으로 들어와서 로컬 처리 여부를 네가 결정한다
- `LocalDate`/JSON parse 같은 message conversion 실패면: 둘 다 못 일어나고 컨트롤러 진입 전에 끝난다

즉 이 문서는 "`왜 이번 요청은 예외 처리 primer 쪽으로 갔고, 왜 이번 요청은 컨트롤러 안에서 멈췄지?`"를 가르는 입구 카드다.

## 상세 분해

### 1. 기본값은 "예외로 400"이다

초급자가 많이 보는 기본 코드는 이쪽이다.

```java
@PostMapping("/members")
public ResponseEntity<Void> create(@Valid @RequestBody CreateMemberRequest request) {
    memberService.create(request);
    return ResponseEntity.ok().build();
}
```

이 상태에서 `name`이 비었거나 `age`가 음수면 보통 validation 실패가 예외로 번진다.

- `MethodArgumentNotValidException`
- 전역 `@RestControllerAdvice`
- 기본 `400 Bad Request`

즉 컨트롤러는 "`실패 데이터를 보고 결정`"하기보다, **실패를 예외 처리 계층에 넘기는 쪽**에 가깝다.

### 2. `BindingResult`를 붙이면 "예외 전에 메서드 안으로" 들어온다

```java
@PostMapping("/members")
public ResponseEntity<?> create(
        @Valid @RequestBody CreateMemberRequest request,
        BindingResult bindingResult
) {
    if (bindingResult.hasErrors()) {
        return ResponseEntity.badRequest().body(bindingResult.getFieldErrors());
    }

    memberService.create(request);
    return ResponseEntity.ok().build();
}
```

이제 validation 실패는 곧바로 전역 예외로 가지 않고, 먼저 `bindingResult.hasErrors()`로 확인할 기회를 준다.

초급자 감각으로 바꾸면 이렇다.

- 없으면: "Spring이 대신 `400`을 만든다"
- 있으면: "내가 이 메서드에서 `400`을 어떻게 만들지 먼저 정한다"

## 배치와 handoff

### 3. `BindingResult`는 바로 뒤에 둬야 한다

초급자가 자주 놓치는 포인트다.

- `@Valid` 대상 파라미터 바로 다음에 둔다
- 다른 파라미터 사이에 떨어뜨리지 않는 편이 안전하다

즉 "`BindingResult`를 선언만 하면 된다"가 아니라, **어느 파라미터의 에러를 받을지 붙여서 쓴다**는 감각이 중요하다.

### 4. 로컬 처리에서 전역 처리로 넘어가는 handoff

초급자가 많이 헷갈리는 지점은 "`BindingResult`를 쓰면 예외 처리를 안 배우는 건가?`"다. 아니다. 둘은 경쟁 관계보다 **분기 순서**에 가깝다.

| 지금 장면 | 먼저 서는 문 | 다음 문서 |
|---|---|---|
| `BindingResult` 없이 `@Valid`가 실패했다 | `MethodArgumentNotValidException` -> 전역 예외 처리 | [Spring 예외 처리 기초](./spring-exception-handling-basics.md) |
| `BindingResult`가 있고 `hasErrors()`가 `true`다 | 현재 컨트롤러 메서드의 로컬 분기 | 이 문서 |
| 로컬로 잡았지만 응답 모양은 팀 공통 계약을 따르고 싶다 | 컨트롤러에서 공통 에러 DTO/매퍼를 호출 | [Spring 예외 처리 기초](./spring-exception-handling-basics.md) |
| validation까지 못 가고 JSON/타입 변환에서 먼저 실패했다 | `BindingResult`보다 앞선 binding/message conversion 문제 | [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md) |

핵심은 "`BindingResult`가 전역 예외 처리를 없앤다"가 아니라, **validation 실패를 전역으로 넘기기 전에 한 번 로컬에서 붙잡을 기회를 준다**는 점이다.

## `ProblemDetail` 계약과 연결해서 보기

팀이 validation `400`을 `ProblemDetail` 같은 공통 error contract로 맞추고 있다면, 여기서 beginner가 한 번 더 헷갈린다. "`전역 advice에서 `ProblemDetail`을 만들면 끝 아닌가?`" 싶지만, `BindingResult`를 쓰는 메서드는 그 전역 경로로 자동 handoff되지 않을 수 있다.

| 비교 질문 | `BindingResult` 로컬 처리 | `MethodArgumentNotValidException` 전역 처리 |
|---|---|---|
| validation 실패를 어디서 처음 잡나 | 현재 컨트롤러 메서드 | `@RestControllerAdvice` / `ResponseEntityExceptionHandler` |
| 공통 `ProblemDetail` 적용 방식 | 메서드 안에서 직접 맞추거나 공통 매퍼 호출 | 전역 advice 한 곳에서 공통 생성 |
| 초급자가 보기 쉬운 증상 | `bindingResult.hasErrors()` 분기 | `MethodArgumentNotValidException` 로그/handler override |
| 장점 | 화면 재표시, 엔드포인트별 예외 응답 분기 | API 전체 `400` contract 통일이 쉽다 |
| 주의점 | 메서드마다 계약이 조금씩 달라질 수 있다 | 로컬 폼 처리처럼 세밀한 분기는 덜 직접적이다 |

즉 `BindingResult`를 쓴다고 `ProblemDetail`을 못 쓰는 것은 아니다. 다만 **전역에서 자동으로 만들어 주던 `400` body를 로컬 메서드도 같은 약속으로 직접 맞춰야 한다**는 점이 달라진다.

## 바뀌지 않는 경계

`BindingResult`가 있다고 해서 모든 `400`이 메서드 안으로 들어오는 것은 아니다.

- JSON 문법이 깨졌다
- `"age": "old"`처럼 숫자 변환이 안 된다
- `LocalDate`에 `"tomorrow"`가 들어온다
- `LocalDate`에 `"2026/05/01"`처럼 slash 형식이 들어온다

이 경우는 DTO 생성 자체가 실패할 수 있다. 그러면 `@Valid` 단계까지 가지 못하므로, `BindingResult` 로컬 처리보다 먼저 message conversion 쪽에서 끝날 수 있다.

특히 beginner가 제일 많이 착각하는 문장을 그대로 적으면 이렇다.

- "`BindingResult`를 붙였는데 왜 `LocalDate` 에러를 못 잡아요?"

답은 간단하다. `BindingResult`는 "`만들어진 DTO의 validation 오류 바구니`"이고, `LocalDate` parse 실패는 "`DTO를 만들다가 멈춘 오류`"라서 같은 바구니에 담기지 않는다.

즉 "`BindingResult`가 있는데 왜 컨트롤러가 안 탔지?`"라고 느껴지면 validation이 아니라 **바인딩/변환 실패**를 먼저 의심하는 편이 빠르다.

## 흔한 오해와 함정

- "`BindingResult`가 있으면 모든 `400`을 내가 처리한다"
  아니다. validation 실패에는 개입할 수 있지만, DTO를 못 만든 바인딩 실패는 여전히 컨트롤러 전에 끝날 수 있다.

- "`BindingResult`가 있으면 `400`이 자동으로 안 나간다"
  자동 `400` 대신 직접 분기할 기회를 얻는 것이다. 하지만 `hasErrors()`를 보고 직접 `400`을 반환하는 경우가 여전히 많다.

- "`BindingResult`는 API에서 무조건 더 좋다"
  아니다. API 전체가 같은 에러 포맷을 써야 하면 전역 예외 처리 쪽이 더 단순할 수 있다.

- "`BindingResult`만 넣으면 서비스가 안전하다"
  아니다. validation 에러를 잡는 것과 서비스/도메인 규칙을 보장하는 것은 다른 문제다.

## 실무에서 쓰는 모습

초급자 기준으로는 장면을 두 개로 나누면 이해가 빠르다.

| 장면 | 왜 `BindingResult`가 어울리나 | 흔한 처리 |
|---|---|---|
| 서버 렌더링 폼 제출 | 같은 화면으로 에러 메시지를 다시 보여주기 쉽다 | 입력 폼 반환, 필드별 메시지 노출 |
| 특정 엔드포인트만 응답 모양이 다름 | 전역 `ControllerAdvice` 규칙을 깨지 않고 로컬 예외 케이스를 분기할 수 있다 | 현재 메서드에서 커스텀 `400` JSON 반환 |

예를 들어 폼 기반 회원가입에서는 "name 필드 아래에 바로 에러 문구 다시 보여주기"가 중요할 수 있다. 이때는 `BindingResult`가 직관적이다.

반대로 JSON API 전체가 아래처럼 같은 에러 계약을 써야 하면 전역 예외 처리가 더 단순하다.

- 모든 `400`을 같은 `code/message/errors` 구조로 통일
- 모든 validation 실패를 같은 로거/모니터링 규칙으로 모으기

즉 `BindingResult`는 "`전역 예외 처리의 반대편`"이라기보다, **일부 요청에서 컨트롤러 로컬 의사결정이 필요할 때 쓰는 분기점**에 가깝다.

## 더 깊이 가려면

- 같은 `400`이라도 "`@Valid`를 탔나, 못 탔나"를 먼저 가르고 싶으면 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)를 먼저 본다.
- `BindingResult`가 있어도 왜 어떤 요청은 컨트롤러 전에 끝나는지 보려면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)로 이어간다.
- 로컬 처리와 전역 예외 처리 선택을 더 넓게 보고 싶으면 [Spring 예외 처리 기초](./spring-exception-handling-basics.md)를 본다.
- 로컬 `BindingResult` 처리와 전역 `MethodArgumentNotValidException` 처리를 `ProblemDetail` error contract 쪽과 같이 보고 싶으면 [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md)로 이어간다.
- 특히 "`BindingResult`가 없을 때 왜 `MethodArgumentNotValidException`으로 전역 `400`이 되는가`"를 이어서 보려면 [Spring 예외 처리 기초](./spring-exception-handling-basics.md)의 validation `400` 표를 바로 이어 읽는다.
- 순서와 내부 메커니즘을 더 자세히 보고 싶으면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)를 본다. 여기까지 이해됐고 "Spring이 실제로 어느 지점에서 `BindingResult`와 예외를 가르는지"가 궁금해졌을 때 넘어가면 된다.

## 면접/시니어 질문 미리보기

**Q. `BindingResult`가 있으면 validation 실패 흐름이 왜 달라지나요?**  
기본적으로는 validation 실패가 예외로 번져 전역 `400` 처리로 가지만, `BindingResult`가 있으면 그 에러를 컨트롤러 메서드 안에서 직접 확인하고 응답을 분기할 수 있다.

**Q. `BindingResult`가 있어도 컨트롤러가 안 타는 경우는 왜 생기나요?**  
validation 이전의 바인딩이나 message conversion 단계에서 DTO 생성이 실패하면, `BindingResult` 로컬 처리 전에 요청이 끝날 수 있다.

**Q. API에서는 `BindingResult`와 전역 예외 처리 중 무엇을 더 자주 쓰나요?**  
공통 에러 계약이 강하면 전역 예외 처리가 더 단순하고, 엔드포인트별 예외 응답이나 폼 재표시가 필요하면 `BindingResult`가 더 직접적이다.

## 한 줄 정리

`BindingResult`는 validation 실패를 "즉시 전역 `400` 예외"에서 "컨트롤러 안에서 직접 분기 가능한 로컬 처리"로 바꾸지만, DTO 생성 자체가 실패하는 바인딩 오류까지 모두 끌고 오지는 못한다.
