# Spring RoomEscape validation `400` vs business conflict `409` 분리 primer

> 한 줄 요약: RoomEscape 예약 생성에서 `400`은 대개 "요청 값 자체가 규칙을 못 넘었다"는 뜻이고, `409`는 "요청 모양은 맞지만 이미 존재하는 예약 슬롯과 부딪혔다"는 뜻이라서 실패 층과 고칠 위치를 다르게 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring 예외 처리 기초: `@ExceptionHandler` vs `@RestControllerAdvice`로 `400`/`404`/`409` 나누기](./spring-exception-handling-basics.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Validation Boundary Mini Bridge](../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: roomescape validation 400 vs 409, spring business conflict 409 beginner, duplicate reservation slot 409, bean validation 400 spring mvc, reservation conflict vs bad request, 같은 요청인데 400 409 왜 달라요, roomescape 예약 중복 conflict, methodargumentnotvalidexception vs reservationconflictexception, 입력 검증 vs 비즈니스 규칙 처음, spring validation vs domain invariant, duplicate slot validation 아니에요, beginner conflict status code

## 핵심 개념

처음에는 질문을 두 개로만 나누면 된다.

- `400 Bad Request`: 요청이 애플리케이션 입구를 통과할 자격이 없나
- `409 Conflict`: 요청은 이해했지만 현재 서버 상태와 충돌하나

RoomEscape 예약 생성으로 바꾸면 더 쉽다.

- `name`이 빈 문자열이고 `partySize`가 `0`이면 Bean Validation 쪽 `400`
- 날짜와 시간 형식도 맞고 필수값도 다 있는데 이미 같은 방, 같은 시간 예약이 있으면 서비스 계층 business conflict `409`

즉 "`값이 이상하다`"와 "`지금은 못 받는다`"를 분리하는 감각이 핵심이다.

## 한눈에 보기

```text
POST /admin/reservations
  -> JSON/DTO 변환
  -> Bean Validation (@NotBlank, @Positive ...)
     -> 실패: 400
  -> service 비즈니스 검사
     -> 이미 존재하는 예약 슬롯 발견: 409
  -> 저장 성공: 201/200
```

| 질문 | validation `400` | business conflict `409` |
|---|---|---|
| 어디서 먼저 보나 | controller 진입 전후의 DTO 검증 | service 도메인 정책 검사 |
| 대표 의미 | 요청 값이 형식/제약을 못 맞춤 | 요청은 맞지만 현재 상태와 충돌 |
| RoomEscape 예시 | `name=""`, `partySize=0` | 같은 room/date/time 슬롯이 이미 존재 |
| 흔한 예외 힌트 | `MethodArgumentNotValidException` | `ReservationConflictException` 같은 커스텀 예외 |
| 초급자 첫 수정 위치 | request DTO, 제약 애너테이션, 요청 값 | 중복 검사 로직, 서비스 정책, 예외 매핑 |

## 상세 분해

### 1. validation `400`은 "입구 검사"에 가깝다

Bean Validation은 주로 request DTO가 최소 규칙을 만족하는지 본다.

- 비어 있으면 안 되는 값
- 양수여야 하는 값
- 길이 제한

이 단계는 "서비스 로직을 실행해 볼 가치가 있나"를 거르는 느낌에 가깝다.

### 2. business conflict `409`는 "업무 규칙 충돌"에 가깝다

중복 예약 슬롯은 문자열 길이 문제와 다르다. 요청 값 자체는 멀쩡해도, 이미 저장된 예약과 비교했을 때만 충돌 여부를 알 수 있다.

그래서 보통 서비스 계층에서 이런 질문을 한다.

- 같은 방에 같은 날짜와 시간 예약이 이미 있나
- 취소된 예약만 예외로 볼 건가
- 관리자 정책상 겹침 허용 범위가 있나

이건 DTO 제약만으로 결정할 수 없는 정보다.

### 3. 중복 예약을 `@Valid`로 해결하려 하면 경계가 흐려진다

초급자가 자주 하는 오해는 "`중복도 잘못된 입력이니 validation 아닌가?`"다. 하지만 중복 예약은 요청 한 장만 보고 판단할 수 없다. DB나 저장된 상태를 조회해야 하므로 service business rule 쪽이 더 자연스럽다.

정리하면:

- 요청 한 장만 보고 알 수 있는가 -> validation `400` 후보
- 현재 저장 상태를 함께 봐야 하는가 -> business conflict `409` 후보

## 흔한 오해와 함정

- "`400`이 더 익숙하니 중복 예약도 그냥 `400`으로 보내자"
  그러면 클라이언트는 "형식이 틀린 요청"과 "현재 슬롯이 찼다"를 같은 종류의 실패로 오해하기 쉽다.

- "`@NotNull`이나 custom validator로 중복 슬롯도 처리하면 되지 않나"
  기술적으로 가능해 보여도, 저장 상태 조회가 섞이면서 request validation과 business rule 경계가 흐려진다.

- "`409`면 서버 장애에 가깝다"
  아니다. RoomEscape 문맥에서는 대개 "이미 다른 예약이 선점했다"는 상태 충돌에 더 가깝다.

- "중복 검사만 service에 있으면 입력 검증은 service에 안 둬도 된다"
  아니다. 빈 문자열, 음수 인원 수 같은 입구 검사는 DTO 쪽에서 먼저 막는 편이 읽기 쉽다.

## 실무에서 쓰는 모습

RoomEscape 관리자 예약 생성 API를 단순화하면 아래처럼 나뉜다.

1. 요청 JSON을 `CreateReservationRequest`로 받는다.
2. `@NotBlank`, `@Positive`, 날짜/시간 형식 같은 최소 규칙을 먼저 통과시키지 못하면 `400`으로 끝난다.
3. DTO가 정상이라면 서비스가 "이 방의 이 날짜/시간 슬롯이 비었는가"를 확인한다.
4. 이미 존재하면 `ReservationConflictException` 같은 도메인 예외를 던지고 advice가 `409`로 번역한다.
5. 비어 있으면 저장하고 성공 응답을 보낸다.

실무에서 디버깅 시작점도 다르다.

- `400`이면 request body, DTO 제약, `MethodArgumentNotValidException`부터 본다.
- `409`이면 repository 조회 조건, 중복 판단 기준, 트랜잭션 안에서의 충돌 처리부터 본다.

## 더 깊이 가려면

- 같은 `400` 안에서도 validation과 message conversion을 더 쪼개려면 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)를 본다.
- `409`를 `@RestControllerAdvice`에서 어떤 JSON 계약으로 내릴지 보려면 [Spring 예외 처리 기초](./spring-exception-handling-basics.md)로 이어간다.
- 요청이 컨트롤러 전에 어디서 검증되고 어디서 서비스로 넘어가는지 다시 묶고 싶으면 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)를 본다.
- 입력 검증과 도메인 불변식 자체의 경계를 더 일반화해서 보고 싶으면 [Validation Boundary Mini Bridge](../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)를 함께 본다.

## 면접/시니어 질문 미리보기

**Q. 중복 예약도 넓게 보면 invalid input 아닌가요?**  
넓게는 그럴 수 있지만, 초급 설계에서는 "요청 한 장만 보고 판단 가능한가"를 기준으로 나누면 validation과 business rule 경계가 훨씬 덜 섞인다.

**Q. 왜 duplicate reservation slot에 `409`가 잘 맞나요?**  
요청 형식은 맞고 대상도 이해했지만, 현재 서버 상태와 충돌해서 지금은 처리할 수 없기 때문이다.

**Q. Bean Validation에서 DB 조회를 해도 되지 않나요?**  
가능 여부보다 경계가 중요하다. 초급자 기준으로는 request DTO 검증은 입구 규칙, 서비스는 저장 상태를 포함한 비즈니스 규칙으로 두는 편이 유지보수와 설명이 쉽다.

## 한 줄 정리

RoomEscape 예약 생성에서 `400`은 주로 request DTO 자체의 제약 실패이고, `409`는 정상 요청이 기존 예약 상태와 충돌한 것이므로 controller validation과 service business rule을 다른 층으로 읽어야 한다.
