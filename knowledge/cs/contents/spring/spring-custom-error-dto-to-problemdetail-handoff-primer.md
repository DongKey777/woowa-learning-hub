# Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer

> 한 줄 요약: 처음에는 팀 전용 `ErrorResponse` DTO로도 충분하지만, Spring 기본 예외와 여러 API 실패를 한 계약으로 묶고 싶어지는 순간부터 `ProblemDetail`이 "표준 error body" 후보로 의미를 갖기 시작한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring RoomEscape validation `400` vs business conflict `409` 분리 primer](./spring-roomescape-validation-400-vs-business-conflict-409-primer.md)
- [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
- [Spring `ProblemDetail` Error Response Design](./spring-problemdetail-error-response-design.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
- [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)
- [spring 카테고리 인덱스](./README.md)

## 이 라우트에서 보는 위치

- 현재 문서: 4단계. validation `400` 응답 바디를 팀 DTO로 둘지, `ProblemDetail`로 표준화할지 정한다.
- 이전 문서: [3단계 `BindingResult` primer](./spring-bindingresult-local-validation-400-primer.md)
- 더 깊게: [Spring `ProblemDetail` Error Response Design](./spring-problemdetail-error-response-design.md)
- README 복귀: [Spring MVC 바인딩/400 -> `ProblemDetail` 4단계 라우트](./README.md#validation-400-problemdetail-route)

여기서 앞 단계 문장을 그대로 다시 잡고 시작하면 덜 헷갈린다. `BindingResult`는 DTO 생성 후 validation에서만 개입하므로, 이 4단계 문서는 그 다음 질문인 "`그 validation 400 응답 바디를 어떤 계약으로 보여 줄까?`"를 다룬다.

retrieval-anchor-keywords: spring custom error dto problemdetail handoff, problemdetail beginner primer, errorresponse vs problemdetail, custom error dto 언제 problemdetail, spring 표준 에러 바디 언제 필요해요, roomescape error response beginner, restcontrolleradvice problemdetail 입문, responseentityexceptionhandler problemdetail beginner, spring mvc 기본 예외도 같은 바디로, validation 400 custom dto vs problemdetail, beginner error contract handoff, error body standardization spring, bindingresult vs methodargumentnotvalidexception, validation 400 contract 왜 달라요, problemdetail 배우고 validation pipeline 다시

## 핵심 개념

처음에는 두 질문만 잡으면 된다.

- 지금 필요한 게 "우리 팀이 읽기 쉬운 에러 JSON"인가
- 아니면 "Spring이 만드는 기본 오류까지 같은 규칙으로 묶는 표준 계약"인가

초급자 초반에는 아래 DTO로도 충분한 경우가 많다.

```java
public record ErrorResponse(String code, String message) {
}
```

이 DTO는 읽기 쉽고, `404`, `409` 같은 도메인 예외를 빠르게 붙이기 좋다.

하지만 API 수가 늘어나고 아래 요구가 생기면 `ProblemDetail`이 등장할 타이밍이다.

- `@RequestBody` 변환 실패, validation 실패도 같은 error body로 보이고 싶다
- 팀마다 제각각인 `code/message` 대신 status, title, detail 같은 공통 축이 필요하다
- 문서, 테스트, 프론트엔드가 "이건 Spring 표준 오류 응답이다"라는 감각을 공유하고 싶다

즉 `ProblemDetail`은 "커스텀 DTO가 틀렸다"가 아니라, **오류 계약이 커지면서 표준화 이점이 생기는 시점의 다음 단계**다.

## 한눈에 보기

| 지금 상황 | DTO 생성 | `BindingResult` 개입 | 전역 vs 로컬 | 더 자연스러운 응답 계약 |
|---|---|---|---|---|
| 컨트롤러 몇 개에서 `404`, `409`만 간단히 내려준다 | 이미 비즈니스 로직까지 간 뒤다 | 보통 없음 | 전역 advice | 커스텀 Error DTO도 충분 |
| validation 실패를 컨트롤러 안에서 `bindingResult.hasErrors()`로 직접 본다 | 예 | 예 | 로컬 분기 | 로컬에서 팀 DTO나 공통 helper를 맞추기 쉽다 |
| validation 실패가 `MethodArgumentNotValidException`으로 넘어간다 | 예 | 아니오 | 전역 예외 처리 | 전역 `ProblemDetail` 통일이 쉬워진다 |
| JSON parse, `LocalDate` 형식 오류까지 한 body로 묶고 싶다 | 아니오 | 아니오 | 컨트롤러 전 + 전역 예외 처리 | `ProblemDetail` 쪽이 설명과 통일이 쉽다 |
| Spring 기본 예외와 커스텀 예외를 같이 설명해야 한다 | 경우마다 다름 | 경우마다 다름 | 로컬/전역 경로가 섞인다 | `ProblemDetail` 표준 필드 이점이 커진다 |

짧게 기억하면 이렇다.

- 작은 API, 작은 팀 규칙: 커스텀 DTO도 충분
- 공통 정책 확대, Spring 기본 예외까지 통합: `ProblemDetail` 후보

여기서 beginner가 한 번 더 헷갈리는 갈림길이 있다.

- validation 실패가 곧바로 `MethodArgumentNotValidException`으로 전역 처리되는가
- 아니면 `BindingResult`로 컨트롤러 안에서 먼저 잡히는가

둘 다 결국 "입력 검증 실패"이지만, **에러 계약을 어디서 조립하느냐**가 다르다. 그래서 `ProblemDetail` 학습도 이 갈림길과 같이 묶어 봐야 한다.

## 왜 초반엔 커스텀 DTO가 편한가

초급자에게는 아래 코드가 바로 읽힌다.

```java
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ReservationConflictException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse handleConflict(ReservationConflictException ex) {
        return new ErrorResponse("RESERVATION_CONFLICT", ex.getMessage());
    }
}
```

장점은 단순하다.

- `code`, `message`가 바로 보인다
- 팀 용어를 그대로 담기 쉽다
- RoomEscape 같은 초반 미션에서 `400`/`404`/`409`를 빠르게 나누기 좋다

그래서 beginner 단계에서는 "`에러 응답 통일`을 처음 경험한다"는 목적만으로도 가치가 있다.

## 언제 `ProblemDetail`이 의미를 갖기 시작하나

### 1. 도메인 예외 말고 Spring 기본 예외도 같이 다뤄야 할 때

예를 들어 아래 실패는 서비스 예외가 아니라 MVC 입구 쪽 실패다.

- JSON 파싱 실패
- `@Valid` 검증 실패
- 잘못된 HTTP method

이런 실패까지 같은 응답 철학으로 묶고 싶으면, `ResponseEntityExceptionHandler`와 `ProblemDetail` 쪽이 설명이 쉬워진다.

### 2. "상태 코드 + 본문 의미"를 같이 표준화하고 싶을 때

`ProblemDetail`은 최소한 아래 공통 칸을 준다.

- `status`
- `title`
- `detail`
- `type`
- `instance`

초급자 관점에서는 "`message`만 내려주는 DTO"보다 "이 오류가 HTTP에서 어떤 문제인지 구조적으로 적는 방식"으로 이해하면 충분하다.

### 3. API가 늘어나며 팀 전용 DTO가 조금씩 흔들릴 때

처음에는 모든 에러가 `code/message`로 끝나는 것 같아도, 곧 질문이 생긴다.

- validation 필드 오류 목록은 어디에 둘까
- `404`와 `409`의 의미 차이를 body에서 어떻게 더 드러낼까
- 보안 예외나 framework 예외도 같은 규칙을 쓸까

이때부터는 커스텀 DTO가 나쁜 게 아니라, "표준 필드가 있는 쪽이 합의 비용을 줄여 주는가"를 보면 된다.

## RoomEscape 감각으로 보면

| 실패 장면 | DTO 생성 | `BindingResult` 개입 | 전역 vs 로컬 | 초반 선택 -> 다음 handoff |
|---|---|---|---|---|
| 없는 예약 id 조회 | 이미 서비스 로직까지 감 | 없음 | 전역 advice | `ErrorResponse("RESERVATION_NOT_FOUND", "...")` -> `404`를 `status/title/detail`로 더 공통화하고 싶다 |
| 중복 예약 슬롯 | 이미 서비스 로직까지 감 | 없음 | 전역 advice | `ErrorResponse("RESERVATION_CONFLICT", "...")` -> 다른 `409`도 같은 틀로 설명하고 싶다 |
| JSON 날짜 형식 오류 | 아니오 | 아니오 | 컨트롤러 전 전역 `400` | 별도 `400` 처리 필요 -> Spring 기본 `400`까지 같은 형식으로 맞추고 싶다 |
| validation 실패 | 예 | 있으면 예, 없으면 아니오 | 로컬 또는 전역 `400` | 필드 오류 응답을 따로 붙이기 시작 -> framework 예외와 domain 예외를 같은 contract 아래 두고 싶다 |

핵심은 "`ProblemDetail`은 고급 기능"이 아니라, **도메인 예외 밖의 실패까지 계약에 넣고 싶어질 때 자연스럽게 보이는 다음 단계**라는 점이다.

## validation `400`에서 `ProblemDetail`이 끼어드는 자리

`ProblemDetail`을 beginner가 헷갈리는 이유는 "`validation 실패면 다 전역 advice에서 같은 `400` body가 나오겠지`"라고 생각하기 쉽기 때문이다. 하지만 `BindingResult`가 있으면 같은 validation 실패라도 먼저 컨트롤러가 잡는다.

| 질문 | DTO 생성 | `BindingResult` 개입 | 전역 vs 로컬 | `ProblemDetail`을 어디서 맞추나 |
|---|---|---|---|---|
| `BindingResult` 로컬 처리 | 예 | 예 | 현재 컨트롤러 메서드 | 컨트롤러에서 직접 만들거나 공통 helper를 호출 |
| `MethodArgumentNotValidException` 전역 처리 | 예 | 아니오 | `@RestControllerAdvice` / `ResponseEntityExceptionHandler` | 전역 advice에서 한 번에 만들기 쉽다 |
| JSON parse, 타입 변환 같은 앞단 `400` | 아니오 | 아니오 | 컨트롤러 전 전역 `400` | `handleHttpMessageNotReadable` 같은 전역 경로에서 맞춘다 |

이 표를 같은 축으로 다시 읽으면 더 단순해진다.

- DTO를 못 만들었으면: `BindingResult` 차례가 아니고, 전역 `400` body 정책 쪽 질문이다.
- DTO는 만들었고 `BindingResult`가 끼어들면: 로컬 `400` body도 같은 계약으로 직접 맞춰야 한다.
- DTO는 만들었지만 `BindingResult`가 없으면: `MethodArgumentNotValidException` 전역 경로에서 `ProblemDetail` 통일이 쉽다.

즉 `ProblemDetail`은 "validation이면 무조건 자동 생성"이 아니라, **전역 예외 처리 경로에 올라왔을 때 표준 body로 통일하기 쉬운 도구**에 가깝다. 로컬 `BindingResult` 경로를 택했다면 그 메서드도 같은 계약을 따르도록 직접 맞춰 줘야 한다.

## 커스텀 DTO에서 `ProblemDetail`로 바꾸는 첫 bridge

초급자에게는 "전면 교체"보다 "한 advice 안에서 감각 익히기"가 안전하다.

```java
@RestControllerAdvice
public class ApiExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(ReservationConflictException.class)
    public ResponseEntity<ProblemDetail> handleConflict(ReservationConflictException ex) {
        ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.CONFLICT);
        problem.setTitle("Reservation conflict");
        problem.setDetail("이미 예약된 시간입니다.");
        return ResponseEntity.status(HttpStatus.CONFLICT).body(problem);
    }
}
```

이 코드에서 초급자가 봐야 할 포인트는 세 가지다.

- 여전히 `@RestControllerAdvice`에서 예외를 번역한다
- 달라진 것은 body 타입이 `ErrorResponse`에서 `ProblemDetail`로 바뀐 점이다
- `ResponseEntityExceptionHandler`를 같이 쓰면 Spring 기본 MVC 예외도 같은 방향으로 묶기 쉬워진다

## 흔한 오해와 정리

- "`ProblemDetail`을 쓰면 커스텀 code를 아예 못 넣는다"
  아니다. 표준 필드 위에 추가 속성을 넣을 수 있다. 다만 초반에는 표준 칸을 먼저 읽는 습관이 더 중요하다.

- "커스텀 DTO를 쓰면 틀린 설계다"
  아니다. beginner 단계에선 오히려 더 읽기 쉬울 수 있다. 문제는 규모가 커질 때 표준화 비용이다.

- "`ProblemDetail`은 무조건 advanced API에서만 필요하다"
  아니다. `400`/`404`/`409`가 여러 endpoint에 반복되고 Spring 기본 예외도 같이 정리하고 싶으면 초급 API에서도 충분히 이유가 생긴다.

- "`ProblemDetail`로 바꾸면 예외 처리가 자동으로 다 해결된다"
  아니다. 어떤 예외를 어느 상태 코드로 번역할지는 여전히 advice와 정책 설계 문제다.

## 어떤 순서로 넘어가면 안전한가

1. 먼저 `@RestControllerAdvice`로 `400`/`404`/`409` 의미를 정리한다.
2. 그다음 커스텀 `ErrorResponse` DTO로 도메인 예외 몇 개를 통일한다.
3. validation `400`에서 `BindingResult` 로컬 처리와 `MethodArgumentNotValidException` 전역 처리 중 어느 쪽을 쓸지 먼저 정한다.
4. 이후 JSON 파싱 실패, validation 실패 같은 Spring 기본 예외도 같은 형식으로 맞추고 싶어질 때 `ResponseEntityExceptionHandler` + `ProblemDetail`을 붙인다.

이 순서가 안전한 이유는 초급자가 처음부터 resolver chain 전체를 외우지 않아도 되기 때문이다.

## 공통 전역 `400` 감각을 잡았으면 어디로 돌아가나

이 문서를 읽고 나면 beginner는 보통 "`이제 `400` body를 공통 `ProblemDetail`로 맞추는 이유는 알겠는데, 그 `400`이 Spring 내부에서 어느 갈림길을 타고 여기까지 왔지?`"라는 다음 질문으로 넘어간다.

그때의 return path는 한 칸으로 고정하면 된다.

- "`전역 `400` shape를 왜 맞추는지`"는 이 문서에서 잡는다
- "`그 `400`이 binding 실패인지, validation 실패인지, `BindingResult` 로컬 처리였는지`"는 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)에서 다시 분해한다

즉 handoff 순서는 이렇게 기억하면 된다.

```text
BindingResult / MethodArgumentNotValidException 갈림길 이해
-> 공통 전역 400 shape를 Error DTO / ProblemDetail로 정리
-> 다시 pipeline 문서로 돌아가 "어느 실패가 이 shape로 들어왔는지" 복기
```

특히 "`왜 어떤 `400`은 `ProblemDetail` advice로 갔고, 어떤 `400`은 컨트롤러 로컬 `BindingResult`에서 끝났지?`", "`global 400 shaping`은 알겠는데 validation pipeline은 아직 헷갈려요`" 같은 질문이면 이 문서 다음 한 걸음은 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)이다.

## 더 깊이 가려면

- "`404`, `409`, `400`을 advice에서 어떻게 나누는지"부터 다시 잡고 싶으면 [Spring 예외 처리 기초](./spring-exception-handling-basics.md)를 먼저 본다.
- validation 실패가 왜 어떤 때는 컨트롤러 안으로 들어오고, 어떤 때는 `MethodArgumentNotValidException`으로 전역에 가는지 먼저 가르고 싶으면 [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나](./spring-bindingresult-local-validation-400-primer.md)를 바로 본다.
- `@RequestBody` 변환 실패처럼 컨트롤러 전에 끝나는 `400`을 같이 묶고 싶다면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)를 본다.
- `ProblemDetail` 필드와 설계 trade-off를 더 정확히 보려면 [Spring `ProblemDetail` Error Response Design](./spring-problemdetail-error-response-design.md)로 이어간다.
- 공통 전역 `400` shape를 잡은 뒤 "`그 shape 앞에서 binding / validation / `BindingResult`가 어떻게 갈렸지?`"를 다시 복기하려면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)로 돌아간다.
- resolver chain, `/error`, commit 경계까지 들어가려면 [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)와 [Spring `ProblemDetail` Error Response Design](./spring-problemdetail-error-response-design.md)을 같이 본다.

## 면접/시니어 질문 미리보기

> Q: 초반엔 커스텀 DTO를 쓰다가 왜 나중에 `ProblemDetail`이 등장하나요?
> 의도: 표준화 시점 이해 확인
> 핵심: 도메인 예외뿐 아니라 Spring 기본 예외까지 같은 계약으로 묶고 싶어질 때 표준 필드 이점이 커진다.

> Q: `ProblemDetail`로 바꾸면 `@RestControllerAdvice`가 필요 없나요?
> 의도: 예외 번역 책임 확인
> 핵심: 아니다. `ProblemDetail`은 body 형식이고, 어떤 예외를 어떤 HTTP 의미로 번역할지는 여전히 advice가 맡는다.

> Q: beginner 프로젝트에서도 `ProblemDetail`을 고려할 타이밍이 있나요?
> 의도: 적용 시점 감각 확인
> 핵심: 있다. `400`/`404`/`409`가 늘고 framework 예외까지 같은 형식으로 맞추고 싶을 때다.

## 한 줄 정리

커스텀 `ErrorResponse` DTO는 초반 통일에 좋고, `ProblemDetail`은 Spring 기본 예외까지 포함한 공통 오류 계약이 필요해질 때 자연스럽게 넘어가는 다음 단계다.
