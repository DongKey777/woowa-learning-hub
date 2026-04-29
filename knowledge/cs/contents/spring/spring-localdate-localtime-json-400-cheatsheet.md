# Spring `LocalDate`/`LocalTime` JSON 파싱 `400` 자주 나는 형식 모음

> 한 줄 요약: `@RequestBody` DTO에서 `LocalDate`, `LocalTime` 필드는 "비슷해 보이는 문자열"도 꽤 많이 거절하므로, 보이는 증상 문장별로 허용 형식과 틀린 형식을 한 장 표로 먼저 외워 두는 편이 빠르다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)
- [Java `Instant` / `LocalDateTime` 경계](../language/java/java-time-instant-localdatetime-boundaries.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: localdate 400 spring, localtime 400 spring, requestbody date parse error, requestbody time parse error, localdate json format beginner, localtime json format beginner, 2026/05/01 400 spring, 18시 400 spring, cannot deserialize localdate, cannot deserialize localtime, datetime sent to localdate, date only sent to localtime, requestbody datetime cheat sheet, spring date time parsing 처음, localdate localtime format mismatch

## 이 라우트에서 보는 위치

- 현재 문서: 2.5단계 형식 오류 follow-up. `@Valid` 전에 멈춘 `LocalDate`/`LocalTime` 변환 실패를 따로 잡는다.
- 이전 문서: [2단계 `@Valid` primer](./spring-valid-400-vs-message-conversion-400-primer.md)
- 다음 문서: [3단계 `BindingResult` primer](./spring-bindingresult-local-validation-400-primer.md)
- README 복귀: [Spring MVC 바인딩/400 follow-up 지도](./README.md#spring-mvc-바인딩400-follow-up-지도)
- README 바인딩 follow-up 증상표 순서: "`2026/05/01` 보냈는데 `400`이 나요?", "`18시`, `오후 6시`, `6pm` 보내면 왜 안 되죠?", "`LocalDate`인데 `2026-05-01T18:00:00` 보내도 되나요?"면 이 문서를 먼저 보고, "`아직 validation까지 갔나?`"가 다음 질문이면 `@Valid` primer로 넘긴다.

## 질문 그대로 먼저 답하기

README 바인딩 follow-up 증상표와 같은 검색 문장 세트에 바로 답하려는 문서다. 이 문서는 "`validation 규칙이 틀렸나?`"보다 먼저 "`date/time 문자열 모양이 타입과 맞나?`"를 고정한다.

| 학습자가 보통 이렇게 말해요 | 먼저 붙잡을 질문 | 더 가까운 원인 |
|---|---|---|
| "`2026/05/01` 보냈는데 `400`이 나요?" | DTO의 `date` 필드가 `LocalDate`인데 slash(`/`) 형식이 들어간 건가? | `LocalDate` 기본 형식 mismatch |
| "`18시`, `오후 6시`, `6pm` 보내면 왜 안 되죠?" | DTO의 `time` 필드가 `LocalTime`인데 자연어/ampm 문자열이 들어간 건가? | `LocalTime` 기본 형식 mismatch |
| "`LocalDate`인데 `2026-05-01T18:00:00` 보내도 되나요?" | 날짜 칸에 datetime 전체 문자열을 넣은 건가? | 타입보다 더 긴 datetime 입력 |

## 핵심 개념

처음에는 이렇게 잡으면 된다.

- `LocalDate`는 "날짜만" 받는다.
- `LocalTime`는 "시간만" 받는다.
- 둘 다 사람이 보기엔 비슷한 문자열이어도 **기본 형식이 아니면** `@RequestBody` 변환 단계에서 바로 `400`이 날 수 있다.

즉 `2026/05/01`, `2026-05-01T18:00:00`, `18시`, `6pm`은 "의미는 알 것 같아 보이는 문자열"이지만, Spring이 DTO를 만들 때는 그대로 거절할 수 있다.

초급자 기준 핵심은 "날짜/시간 개념"보다 먼저 **DTO 필드 타입이 기대하는 문자열 모양**을 맞추는 것이다.

## 한눈에 보기

| DTO 필드 타입 | 기본으로 가장 안전한 입력 | 자주 틀리는 입력 | 왜 자주 `400`이 나나 |
|---|---|---|---|
| `LocalDate` | `"2026-05-01"` | `"2026/05/01"`, `"05-01-2026"`, `"tomorrow"` | 날짜 구분자, 순서, 자연어 표현이 다르다 |
| `LocalTime` | `"18:00"` | `"18시"`, `"6pm"`, `"1800"` | 시간 표기 방식이 다르다 |
| `LocalDate`에 datetime 문자열 전송 | 없음 | `"2026-05-01T18:00:00"` | 날짜만 받는 칸에 시간까지 같이 들어왔다 |
| `LocalTime`에 date 문자열 전송 | 없음 | `"2026-05-01"` | 시간만 받는 칸에 날짜가 들어왔다 |

짧게 외우면 이렇다.

- `LocalDate` 기본값: `yyyy-MM-dd`
- `LocalTime` 기본값: `HH:mm` 중심으로 생각
- 날짜와 시간을 한 문자열로 보내고 싶으면 애초에 필드 타입이 다른지 같이 의심한다

## `LocalDate`에서 자주 깨지는 증상

<a id="symptom-slash-date"></a>

### 1. "`2026/05/01` 보냈는데 `400`이 나요"

이건 가장 흔한 `LocalDate` 형식 mismatch다.

| 보내는 값 | 필드 타입 | 결과 |
|---|---|---|
| `"2026-05-01"` | `LocalDate` | 보통 정상 |
| `"2026/05/01"` | `LocalDate` | 자주 `400` |

초급자 감각으로는 둘 다 "날짜처럼 보이지만", 기본 파싱은 slash(`/`)가 아니라 hyphen(`-`) 기준으로 생각하는 편이 안전하다.

즉 `LocalDate` 초급 기본값은 아래처럼 외우면 된다.

```text
yyyy-MM-dd
```

<a id="symptom-natural-language-date"></a>

### 2. "`tomorrow`, `next friday` 같은 말도 이해할 줄 알았어요"

사람은 이해해도 `LocalDate` 기본 JSON 파싱은 자연어 날짜를 알아듣지 않는다.

| 보내는 값 | 필드 타입 | 결과 |
|---|---|---|
| `"2026-05-01"` | `LocalDate` | 보통 정상 |
| `"tomorrow"` | `LocalDate` | 자주 `400` |
| `"next friday"` | `LocalDate` | 자주 `400` |

이때 초급자가 자주 하는 오해는 "`JSON 문자열이니까 일단 들어오고 서비스에서 해석하겠지`"다. 실제로는 **컨트롤러 전에 DTO 생성 단계에서 멈출 수 있다.**

<a id="symptom-datetime-to-date"></a>

### 3. "`LocalDate`인데 `2026-05-01T18:00:00` 보내면 더 자세해서 좋은 것 아닌가요?"

아니다. `LocalDate`는 날짜 칸이라서, 시간까지 붙이면 오히려 더 잘 깨진다.

| 보내는 값 | 필드 타입 | 결과 |
|---|---|---|
| `"2026-05-01"` | `LocalDate` | 보통 정상 |
| `"2026-05-01T18:00:00"` | `LocalDate` | 자주 `400` |

이 증상은 보통 두 경우를 뜻한다.

- 프론트가 date picker 값 대신 datetime 전체 문자열을 보냈다
- DTO 설계가 `LocalDate`가 아니라 `LocalDateTime` 쪽이어야 했는데 타입을 좁게 잡았다

즉 "`더 많은 정보`"가 아니라 "**다른 타입의 문자열**"일 수 있다.

## `LocalTime`에서 자주 깨지는 증상

<a id="symptom-korean-time"></a>

### 4. "`18시`, `오후 6시`, `6pm` 보내면 왜 안 되죠?"

`LocalTime`도 사람이 읽기 쉬운 표현과 기본 파싱 형식이 다를 수 있다.

| 보내는 값 | 필드 타입 | 결과 |
|---|---|---|
| `"18:00"` | `LocalTime` | 보통 정상 |
| `"18시"` | `LocalTime` | 자주 `400` |
| `"오후 6시"` | `LocalTime` | 자주 `400` |
| `"6pm"` | `LocalTime` | 자주 `400` |

초급자 기준으로는 `LocalTime`을 아래처럼 생각하면 덜 헷갈린다.

```text
18:00
09:30
```

즉 "한글 시간 표현", "am/pm 축약", "공백 섞인 자연어"는 기본 입력으로 기대하지 않는 편이 안전하다.

<a id="symptom-compact-time"></a>

### 5. "`1800`처럼 숫자만 보내면 안 되나요?"

이것도 자주 보는 실수다.

| 보내는 값 | 필드 타입 | 결과 |
|---|---|---|
| `"18:00"` | `LocalTime` | 보통 정상 |
| `"1800"` | `LocalTime` | 자주 `400` |
| `"18-00"` | `LocalTime` | 자주 `400` |

초급자에게는 "`시간 네 자리 숫자`"보다 "`콜론 있는 문자열`"로 고정해 두는 편이 안전하다.

<a id="symptom-date-to-time"></a>

### 6. "`LocalTime`인데 날짜 문자열을 보내도 일부만 읽지 않나요?"

보통 그렇게 기대하면 안 된다.

| 보내는 값 | 필드 타입 | 결과 |
|---|---|---|
| `"18:00"` | `LocalTime` | 보통 정상 |
| `"2026-05-01"` | `LocalTime` | 자주 `400` |
| `"2026-05-01T18:00:00"` | `LocalTime` | 자주 `400` |

`LocalTime`은 "시간만" 받는 칸이다. 날짜가 앞에 붙은 순간 "비슷한 값"이 아니라 **다른 종류의 값**으로 보는 편이 맞다.

## 상세 분해

### 1. 먼저 타입을 본다

가장 먼저 확인할 것은 JSON 값보다 DTO 필드 선언이다.

```java
public record CreateReservationRequest(
        LocalDate date,
        LocalTime time
) {
}
```

이 선언이면 초급자 기본 규칙은 단순하다.

- `date`에는 `"2026-05-01"`처럼 날짜만
- `time`에는 `"18:00"`처럼 시간만

문자열이 더 자세하거나, 더 친절해 보이거나, 더 자연어 같아도 오히려 타입과 어긋날 수 있다.

### 2. 그다음 문자열 모양을 본다

초급자 디버깅은 "의미가 비슷한가?"보다 "모양이 맞는가?"가 더 중요하다.

| 질문 | `LocalDate` | `LocalTime` |
|---|---|---|
| 구분자가 맞나 | `-` 중심 | `:` 중심 |
| 날짜/시간만 들어왔나 | 날짜만 | 시간만 |
| 자연어가 섞였나 | `tomorrow`면 위험 | `6pm`, `18시`면 위험 |

즉 date/time `400`은 고급 timezone 이슈보다 먼저 **문자열 모양 mismatch**로 보는 편이 초급자에게 훨씬 맞다.

### 3. `@Valid`보다 먼저 막힐 수 있다

이 장면은 validation과 자주 섞인다.

- `date = "2026/05/01"`이면 보통 변환 단계에서 먼저 실패
- `partySize = 0`이면 DTO 생성 후 `@Valid`가 실패할 수 있음

그래서 date/time 형식 오류는 "`@NotNull`이 왜 안 먹지?`"보다 "`아직 validation까지 못 갔나?`"를 먼저 묻는 편이 빠르다.

## 흔한 오해와 함정

- "`2026/05/01`도 날짜니까 알아서 바꿔 줄 것이다"
  아니다. 기본 형식과 다르면 `400`이 날 수 있다.

- "`2026-05-01T18:00:00`은 더 자세한 날짜라서 `LocalDate`도 받을 수 있다"
  아니다. 날짜 칸에 datetime 문자열을 넣은 것이다.

- "`18시`, `6pm`은 사람 눈에 시간인데 왜 안 되지?"
  기본 파싱 형식과 자연어 표현은 다를 수 있다.

- "`@Valid`를 붙였으니 날짜 형식 오류도 validation 메시지로 올 것이다"
  아니다. date/time 파싱 실패는 validation 전에 끝날 수 있다.

## 실무에서 쓰는 모습

RoomEscape 예약 생성 DTO처럼 `date`, `time`이 따로 있는 API라면 아래처럼 맞추는 편이 가장 덜 헷갈린다.

```json
{
  "date": "2026-05-01",
  "time": "18:00"
}
```

반대로 아래 입력은 beginner 단계에서 자주 `400` 후보로 본다.

```json
{
  "date": "2026/05/01",
  "time": "18시"
}
```

짧은 점검 순서는 이렇다.

1. DTO가 `LocalDate`, `LocalTime`인지 본다.
2. `date` 값이 `yyyy-MM-dd` 모양인지 본다.
3. `time` 값이 `HH:mm` 모양인지 본다.
4. 날짜 칸에 datetime, 시간 칸에 날짜를 넣지 않았는지 본다.
5. 그래도 아니면 그다음에 `@JsonFormat` 같은 커스텀 규칙 유무를 본다.

## 더 깊이 가려면

- `400`이 왜 컨트롤러 전에 끝나는지 전체 그림부터 다시 잡고 싶으면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)를 먼저 본다.
- date/time 파싱 실패와 validation 실패를 로그 기준으로 더 잘 가르고 싶으면 [Spring `@Valid`는 언제 타고 언제 못 타는가: `400` 첫 분기 primer](./spring-valid-400-vs-message-conversion-400-primer.md)를 본다.
- binding과 validation 순서를 더 자세히 보고 싶으면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)로 이어간다.
- Java 쪽에서 `LocalDateTime`과 "로컬 날짜/시간" 경계를 먼저 다시 보고 싶으면 [Java `Instant` / `LocalDateTime` 경계](../language/java/java-time-instant-localdatetime-boundaries.md)를 같이 본다.

## 면접/시니어 질문 미리보기

**Q. `LocalDate` 필드에 `2026-05-01T18:00:00`을 보내면 왜 깨질 수 있나요?**  
`LocalDate`는 날짜만 받는 타입이라서, datetime 문자열은 "더 자세한 같은 값"이 아니라 다른 타입의 입력으로 볼 수 있다.

**Q. date/time 형식 오류와 `@Valid` 오류는 왜 디버깅 출발점이 다른가요?**  
date/time 형식 오류는 DTO 생성 단계에서 먼저 실패할 수 있지만, `@Valid`는 DTO 생성이 끝난 뒤에만 탈 수 있기 때문이다.

**Q. 초급자 기준으로 가장 안전한 기본 입력 형식은 무엇인가요?**  
`LocalDate`는 `yyyy-MM-dd`, `LocalTime`는 `HH:mm` 기준으로 먼저 맞추는 편이 가장 안전하다.

## 한 줄 정리

`LocalDate`와 `LocalTime`의 `400`은 대부분 "의미가 비슷한 문자열"이 아니라 "타입이 기대한 정확한 모양의 문자열"을 보내지 못해서 생기므로, date는 `yyyy-MM-dd`, time은 `HH:mm`부터 먼저 맞춰 보는 게 가장 빠르다.
