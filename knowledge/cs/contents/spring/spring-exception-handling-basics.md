# Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기

> 한 줄 요약: 처음에는 "`@ExceptionHandler`는 한 컨트롤러 안에서 급한 불을 끄는 도구, `@RestControllerAdvice`는 여러 API의 실패 응답을 한 정책으로 맞추는 도구"로 잡으면 `400`/`404`/`409`가 왜 갈리는지 훨씬 빨리 보인다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나: 컨트롤러 로컬 처리 초급 카드](./spring-bindingresult-local-validation-400-primer.md)
- [Spring RoomEscape validation `400` vs business conflict `409` 분리 primer](./spring-roomescape-validation-400-vs-business-conflict-409-primer.md)
- [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [Spring `404` / `405` vs Bean Wiring Confusion Card](./spring-404-405-vs-bean-wiring-confusion-card.md)
- [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring exception handling basics, spring exceptionhandler vs restcontrolleradvice, 스프링 예외 처리 처음, exceptionhandler 입문, restcontrolleradvice 뭐예요, responseentityexceptionhandler beginner, responseentityexceptionhandler vs restcontrolleradvice, spring 400 404 409 응답, requestbody 400 왜 나요, binding failure vs business exception, validation 400 vs conflict 409, not found 404 spring api, global error response beginner, roomescape admin api error handling, bindingresult local vs global validation handling

## 핵심 개념

컨트롤러마다 try-catch를 넣기 시작하면 같은 실패 응답이 여러 파일에 복사된다. 초급자 기준으로는 예외 처리도 먼저 두 칸으로만 나누면 된다.

- `@ExceptionHandler`: 한 컨트롤러 안에서 "이 예외가 나면 이렇게 응답하자"를 적는 로컬 규칙
- `@RestControllerAdvice`: 여러 컨트롤러에 공통으로 적용되는 전역 규칙

RoomEscape 관리자 API를 떠올리면 감이 쉽다. 이 문서는 lifecycle primer와 같은 칸으로 실패를 읽는다.

- binding / message conversion 단계에서 JSON 형식, 날짜 타입 변환이 깨지면 주로 `400 Bad Request`
- validation 단계에서 `@Valid` 제약을 못 넘으면 주로 `400 Bad Request`
- controller / service 단계에서 없는 예약 id를 찾으면 `404 Not Found`
- controller / service 단계에서 이미 예약된 시간 충돌을 발견하면 `409 Conflict`

핵심은 "예외를 어디서 잡는가"보다 "어떤 실패를 어떤 HTTP 의미로 번역할 것인가"다.

validation `400`만 놓고 보면 handoff는 더 단순하다.

- `BindingResult`가 없으면: validation 실패가 `MethodArgumentNotValidException`으로 번져 전역 예외 처리 쪽으로 온다
- `BindingResult`가 있으면: 같은 validation 실패라도 컨트롤러가 먼저 받아 로컬 분기할 수 있다

그래서 이 문서는 "전역으로 넘어온 뒤 어떻게 번역할까"에 더 가깝고, "`왜 전역으로 안 넘어오고 메서드 안에서 멈췄지?`"는 [Spring `BindingResult` primer](./spring-bindingresult-local-validation-400-primer.md)가 담당한다.

## 한눈에 보기

```text
HTTP 요청
  -> argument binding / message conversion
  -> @Valid validation
  -> Controller / Service
  -> 예외면 @ExceptionHandler or @RestControllerAdvice
  -> HTTP 응답
```

| 상황 | 먼저 쓰기 쉬운 도구 | 왜 그렇게 보나 |
|---|---|---|
| 한 컨트롤러만 특별한 에러 응답이 필요하다 | `@ExceptionHandler` | 범위가 작고 바로 옆에서 읽힌다 |
| 여러 API가 같은 JSON 에러 형식을 써야 한다 | `@RestControllerAdvice` | 전역 규칙을 한 곳에 모은다 |
| MVC 기본 예외의 기본 처리 메서드를 조금만 바꾸고 싶다 | `@RestControllerAdvice` + `ResponseEntityExceptionHandler` 상속 | Spring이 이미 나눠 둔 `handle...` 메서드를 재사용할 수 있다 |
| `@RequestBody` 변환 실패처럼 MVC 기본 예외도 함께 다뤄야 한다 | `@RestControllerAdvice` 쪽 공통 정책 | `400` 계열 응답 형식을 통일하기 쉽다 |
| HTML 뷰가 아니라 JSON API 서버다 | `@RestControllerAdvice` | 리턴값이 응답 본문으로 바로 직렬화된다 |

| 실패 칸 | 컨트롤러 진입 전/후 | 대표 예시 | 대표 상태 코드 |
|---|---|---|---|
| binding / message conversion failure | 전 | JSON 문법 오류, `LocalDate` 변환 실패 | `400` |
| validation failure | 보통 전, `BindingResult`가 있으면 로컬 분기 가능 | `@NotBlank`, `@Positive` 제약 위반 | `400` |
| business exception | 후 | 없는 예약 조회, 중복 예약 슬롯 충돌 | `404`, `409` |

| validation `400` 안에서 다시 묻는 질문 | 로컬 처리 | 전역 처리 |
|---|---|---|
| 어떤 도구가 먼저 잡나 | `BindingResult` | `MethodArgumentNotValidException` + `@RestControllerAdvice` / `ResponseEntityExceptionHandler` |
| 컨트롤러 메서드가 호출되나 | 호출된다 | 보통 호출되지 않는다 |
| 잘 맞는 장면 | 폼 재표시, 엔드포인트별 커스텀 `400` | API 전체 공통 에러 계약, 공통 로깅/모니터링 |
| 입문용 연결 문서 | [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나](./spring-bindingresult-local-validation-400-primer.md) | 이 문서 계속 |

이 표를 먼저 잡아 두면 "`400`이니까 다 같은 입력 오류"와 "`business exception`도 그냥 `400` 아닌가?"를 덜 섞는다.

## 로컬 vs 전역 처리

### 1. `@ExceptionHandler`는 "이 컨트롤러만 예외적으로"에 가깝다

같은 컨트롤러 안에서만 다른 응답이 필요하면 가장 읽기 쉽다. 예를 들어 관리자 화면 컨트롤러만 임시로 다른 메시지를 내려야 할 때 쓸 수 있다.

```java
@RestController
@RequestMapping("/admin/reservations")
public class AdminReservationController {

    @ExceptionHandler(ReservationNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(ReservationNotFoundException ex) {
        return new ErrorResponse("RESERVATION_NOT_FOUND", ex.getMessage());
    }
}
```

다만 컨트롤러가 늘어날수록 같은 코드가 복제되기 쉽다.

### 2. `@RestControllerAdvice`는 "여러 API가 같은 계약을 쓴다"에 가깝다

RoomEscape처럼 관리자 API가 여러 개 생기면 `404`, `409`, `400` 포맷을 한 곳에서 맞추는 편이 낫다.

```java
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ReservationNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(ReservationNotFoundException ex) {
        return new ErrorResponse("RESERVATION_NOT_FOUND", ex.getMessage());
    }

    @ExceptionHandler(ReservationConflictException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse handleConflict(ReservationConflictException ex) {
        return new ErrorResponse("RESERVATION_CONFLICT", ex.getMessage());
    }
}
```

`@RestControllerAdvice`는 `@ControllerAdvice`에 `@ResponseBody` 감각이 합쳐진 형태라서 JSON API에 더 자연스럽다.

validation `400` 관점에서는 여기가 "`BindingResult`가 없을 때 주로 도착하는 다음 정류장`"이다. 즉 `@Valid` 실패가 `MethodArgumentNotValidException`으로 번졌다면, 초급자는 이 문단과 [Spring `BindingResult` primer](./spring-bindingresult-local-validation-400-primer.md)를 한 세트로 읽으면 된다.

## `ResponseEntityExceptionHandler` 브리지

`ResponseEntityExceptionHandler`는 "`@RestControllerAdvice`를 버리는 것"이 아니라 "기본 MVC 예외용 뼈대를 빌리는 것"에 가깝다.

처음 보면 `ResponseEntityExceptionHandler`가 별도 전략처럼 보이지만, 초급자 기준으로는 "`@RestControllerAdvice` 안에서 Spring 기본 예외 처리 메서드를 편하게 override하는 부모 클래스"로 이해하면 충분하다.

```java
@RestControllerAdvice
public class ApiExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(ReservationConflictException.class)
    public ResponseEntity<ErrorResponse> handleConflict(ReservationConflictException ex) {
        return ResponseEntity.status(HttpStatus.CONFLICT)
            .body(new ErrorResponse("RESERVATION_CONFLICT", ex.getMessage()));
    }

    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("INVALID_INPUT", "입력 형식을 다시 확인해 주세요."));
    }
}
```

여기서 판단 기준은 단순하다.

| 질문 | 먼저 떠올릴 선택 |
|---|---|
| 도메인 예외 몇 개만 공통 JSON으로 묶으면 충분한가 | plain `@RestControllerAdvice` + `@ExceptionHandler` |
| `MethodArgumentNotValidException`, `HttpMessageNotReadableException`처럼 Spring MVC 기본 예외도 팀 표준 바디로 맞추고 싶은가 | `ResponseEntityExceptionHandler` 상속 고려 |
| Spring이 이미 준비한 기본 처리 메서드 이름을 따라가며 수정하고 싶은가 | `ResponseEntityExceptionHandler` 상속 고려 |

즉, `ResponseEntityExceptionHandler`는 "전역 예외 처리의 대체재"가 아니라 "전역 예외 처리 안에서 MVC 기본 예외를 덜 반복해서 다루는 보조 도구"에 가깝다.

## 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 감각

초급자 첫 단계에서는 아래처럼 팀 전용 DTO를 쓰는 경우가 많다.

```java
public record ErrorResponse(String code, String message) {
}
```

이건 좋은 출발점이다. `404`, `409` 같은 도메인 예외를 빠르게 읽고 테스트하기 쉽기 때문이다.

다만 아래 질문이 생기기 시작하면 `ProblemDetail`을 볼 타이밍이다.

- JSON 파싱 실패, validation 실패도 같은 error body로 맞추고 싶은가
- `code/message`만으로는 상태 코드 의미를 설명하기 부족한가
- 여러 컨트롤러와 여러 실패 타입을 하나의 표준 응답 계약으로 묶고 싶은가

짧게 말하면 이렇다.

| 지금 목표 | 더 자연스러운 선택 |
|---|---|
| 도메인 예외 몇 개를 읽기 쉬운 JSON으로 통일 | 커스텀 Error DTO |
| Spring 기본 MVC 예외까지 포함한 공통 오류 계약 | `ProblemDetail` + `ResponseEntityExceptionHandler` 고려 |

이 감각을 RoomEscape 예시와 함께 한 장으로 보고 싶으면 [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](./spring-custom-error-dto-to-problemdetail-handoff-primer.md)를 바로 이어서 보면 된다.

## 상태 코드 감각

### 1. `400`과 `404`와 `409`는 실패 의미가 다르다

같은 4xx라도 질문이 다르다.

- `400`: 요청 형식이나 값이 처음부터 잘못됐나
- `404`: 찾으려는 대상이 없나
- `409`: 대상은 이해했지만 현재 상태와 충돌하나

초급자는 상태 코드를 외우기보다, "요청이 틀렸나 / 대상이 없나 / 상태가 부딪히나" 세 질문으로 먼저 나누는 편이 안전하다.

### 2. `@RequestBody` `400`은 컨트롤러 전에 끝날 수 있다

여기서 자주 헷갈린다. 모든 `400`이 서비스 예외는 아니다.

- JSON 문법 오류
- DTO 타입 변환 실패
- `@Valid` 제약 위반

이런 경우는 컨트롤러 비즈니스 로직보다 앞단에서 이미 실패할 수 있다. 그래서 `400`은 "예외 처리 정책"뿐 아니라 lifecycle primer에서 본 `binding / message conversion`과 `validation` 칸도 같이 봐야 한다.

### 3. binding failure와 business exception은 수정 위치가 다르다

처음 헷갈리는 지점은 둘 다 "실패"처럼 보인다는 점이다. 하지만 초급자 디버깅에서는 "어느 칸에서 실패했나"를 먼저 고정해야 한다.

| 비교 질문 | binding / validation failure | business exception |
|---|---|---|
| lifecycle primer 기준 위치 | argument binding / message conversion, `@Valid` | controller / service |
| 컨트롤러 메서드 진입 | 못 할 수 있다. `BindingResult`가 있으면 validation만 로컬 분기 가능 | 이미 진입한 뒤 서비스 호출 중 발생 |
| 대표 예시 | JSON 문법 오류, 숫자/날짜 변환 실패, `@NotBlank` 위반 | 없는 예약 id, 이미 존재하는 예약 슬롯 |
| 초급자 첫 수정 위치 | request DTO, 요청 body, validation 제약, message conversion 설정 | service 비즈니스 규칙, repository 조회 조건, 예외 매핑 |
| 왜 같은 표로 묶지 않나 | 요청 한 장만 보고도 실패를 알 수 있다 | 현재 저장 상태나 도메인 규칙을 함께 봐야 한다 |

짧게 외우면 이렇다.

- binding failure: "요청을 읽는 단계에서 이미 막혔다"
- business exception: "요청은 읽었고, controller/service가 도메인 규칙을 적용하다가 막혔다"
- `BindingResult`: validation 실패를 예외 대신 컨트롤러 로컬 분기로 바꿀 수 있지만, JSON 파싱 실패까지 다 끌어오지는 못한다

## 흔한 오해와 함정

- "`400`이면 다 같은 입력 오류다"
  아니다. JSON 파싱 실패, validation 실패, 도메인 정책 위반은 모두 다른 층에서 날 수 있다.

- "`404`도 그냥 `IllegalArgumentException`으로 보내고 `400`으로 통일하자"
  그러면 클라이언트는 "형식이 틀린 요청"과 "없는 리소스 조회"를 구분하기 어려워진다.

- "`@ControllerAdvice`만 붙이면 JSON 응답이 된다"
  뷰가 아닌 API 서버라면 `@RestControllerAdvice`가 더 직관적이다.

- "모든 컨트롤러마다 `@ExceptionHandler`를 넣는 게 명시적이라 더 좋다"
  범위가 작을 때는 좋지만, 공통 계약이 생기면 중복이 빠르게 늘어난다.

- "`ResponseEntityExceptionHandler`를 쓰면 `@ExceptionHandler`는 못 쓴다"
  아니다. 보통은 `@RestControllerAdvice`에 `@ExceptionHandler`와 override 메서드를 같이 둔다. 도메인 예외는 직접 잡고, MVC 기본 예외는 부모 클래스 메서드를 재정의하는 식이다.

- "이미 예약된 시간은 서버가 못 처리했으니 `500`이다"
  서버 장애보다 비즈니스 상태 충돌에 가까우면 `409`가 더 의미를 전달한다.

- "`BindingResult`가 있으면 business exception도 컨트롤러에서 다 처리된다"
  아니다. `BindingResult`는 validation 실패의 로컬 분기 도구에 가깝고, 서비스 단계 business exception 경계까지 없애지는 않는다.

## 실무에서 쓰는 모습

RoomEscape 관리자 예약 API를 예로 들면 보통 이렇게 나눈다.

1. `POST /admin/reservations`에서 날짜 형식이 깨졌으면 `400`
2. `GET /admin/reservations/{id}`에서 없는 id면 `404`
3. 이미 예약된 시간에 다시 생성하면 `409`

컨트롤러와 서비스는 예외를 "던지는 쪽"에 가깝고, `@RestControllerAdvice`는 그 예외를 "API 계약으로 번역하는 쪽"에 가깝다.

그래서 초반 설계도 아래처럼 잡으면 충분하다.

- 입력 형식 문제: `400`
- 리소스 부재: `404`
- 상태 충돌: `409`
- 나머지 예상 못 한 실패: `500`

중요한 건 상태 코드 숫자 자체보다, 프론트엔드와 테스트가 읽을 수 있는 일관된 에러 바디를 같이 유지하는 것이다.

초급자 첫 선택으로는 보통 이 순서가 안전하다.

1. 도메인 예외 몇 개를 `@RestControllerAdvice` + `@ExceptionHandler`로 먼저 정리한다.
2. 그다음 validation, JSON 파싱 실패까지 같은 바디로 맞추고 싶어질 때 `ResponseEntityExceptionHandler` 상속을 붙인다.

이렇게 가면 처음부터 너무 큰 resolver 체인을 머릿속에 넣지 않아도 된다.

## 더 깊이 가려면

- `400`이 컨트롤러 전에 끝나는 흐름을 더 자세히 보려면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)를 먼저 본다.
- RoomEscape 예약 생성처럼 validation `400`과 business conflict `409`를 실전 예시로 분리하고 싶으면 [Spring RoomEscape validation `400` vs business conflict `409` 분리 primer](./spring-roomescape-validation-400-vs-business-conflict-409-primer.md)를 먼저 본다.
- validation 실패가 `BindingResult` 때문에 언제 로컬 처리로 바뀌는지 보려면 [Spring `BindingResult`가 있으면 `400` 흐름이 어떻게 달라지나](./spring-bindingresult-local-validation-400-primer.md)를 함께 본다.
- 반대로 `BindingResult`가 빠졌을 때 validation 실패가 왜 `MethodArgumentNotValidException`으로 전역 처리되는지 다시 확인하고 싶으면 같은 primer의 handoff 표를 같이 본다.
- `ResponseEntityExceptionHandler`가 resolver chain 안에서 어디쯤 서는지 궁금하면 [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)로 이어간다.
- `DispatcherServlet`과 exception resolver가 어디서 예외를 넘기는지 보려면 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md) 다음에 [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)로 이어간다.
- `404`와 `405`를 매핑 문제로 먼저 가르는 감각은 [Spring `404` / `405` vs Bean Wiring Confusion Card](./spring-404-405-vs-bean-wiring-confusion-card.md)에서 보강한다.
- 도메인 예외 계층 설계와 에러 응답 계약은 [software-engineering API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)를 참고한다.

## 면접/시니어 질문 미리보기

> Q: `@ExceptionHandler`와 `@RestControllerAdvice`를 언제 갈라 쓰나요?
> 의도: 로컬 처리와 전역 처리 구분 확인
> 핵심: 한 컨트롤러 전용 정책이면 `@ExceptionHandler`, 여러 API 공통 계약이면 `@RestControllerAdvice`가 보통 더 낫다.

> Q: `400`, `404`, `409`를 감각적으로 어떻게 구분하나요?
> 의도: 상태 코드 의미 이해 확인
> 핵심: 요청이 틀렸나(`400`), 대상이 없나(`404`), 현재 상태와 충돌하나(`409`)로 먼저 나눈다.

> Q: 왜 `@RequestBody` 문제와 도메인 예외를 같은 `400`으로 뭉치면 아쉬운가요?
> 의도: 실패 원인 분리 이해
> 핵심: 클라이언트와 테스트가 "입력 형식 실패"와 "업무 규칙 실패"를 구분하기 어려워진다.

## 한 줄 정리

처음에는 "`@ExceptionHandler`는 로컬 예외 대응, `@RestControllerAdvice`는 공통 API 실패 계약"으로 잡고 `400`/`404`/`409`를 요청 오류, 리소스 부재, 상태 충돌로 나눠 기억하면 된다.
