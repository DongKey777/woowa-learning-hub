# Spring `@RequestBody` `415 Unsupported Media Type` 초급 primer: "`json`인데 `415 Unsupported Media Type`가 떠요", "`Content-Type: application/json` 안 붙였는데 `415`예요"

> 한 줄 요약: "`json`인데 `415 Unsupported Media Type`가 떠요", "`Content-Type: application/json` 안 붙였는데 `415`예요" 같은 질문은 JSON 값보다 먼저 "`이 요청 body가 JSON이라고 선언됐나?`"를 확인하면 가장 빨리 풀린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드: 폼/query 바인딩과 JSON body를 한 장으로 분리하기](./spring-modelattribute-vs-requestbody-binding-primer.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
- [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring requestbody 415 primer, @requestbody 415 unsupported media type, json인데 unsupported media type, content-type application json 안 붙였는데 415, content-type application json 왜, 컨트롤러 전에 415 spring, postman 415 spring beginner, consumes application json mismatch, requestbody media type 처음, requestbody 400 vs 415 차이, 왜 415가 나와요, what is unsupported media type, beginner content-type basics, spring json body not supported, 처음 requestbody 헷갈려요

## 핵심 개념

처음에는 이렇게만 잡으면 된다.

- `@RequestBody`는 body 내용만 보는 기능이 아니라, 먼저 `Content-Type`을 보고 어떤 형식인지 판단한다.
- 그래서 body가 JSON처럼 보여도 헤더가 `application/json`이 아니면 Spring은 JSON으로 읽지 않을 수 있다.
- 이때 자주 보이는 응답이 `415 Unsupported Media Type`이다.

즉 "`JSON 문법이 틀렸나?`"보다 "`이 요청이 JSON이라고 제대로 선언됐나?`"를 먼저 묻는 문서다. 초급자 기준으로 `415`는 보통 "값 해석 실패"보다 "body 형식 계약 실패"에 가깝다.

## 질문 그대로 먼저 답하기

이 문서는 아래처럼 검색하는 초급자를 바로 받기 위한 entrypoint다.

- "`json`인데 `415 Unsupported Media Type`가 떠요" -> JSON 모양보다 `Content-Type` 선언을 먼저 본다.
- "`Content-Type: application/json` 안 붙였는데 `415`예요" -> 거의 바로 `Content-Type: application/json` 누락을 먼저 확인하면 된다.
- "컨트롤러 전에 `415 Unsupported Media Type`가 나요" -> 컨트롤러 로직보다 message converter가 요청 형식을 고르기 전에 막힌 장면일 수 있다.

짧게 말해 "`JSON처럼 생겼다`"와 "`JSON이라고 선언했다`"는 다른 질문이다.

## 한눈에 보기

| 지금 보이는 말 | 먼저 붙잡을 질문 | 더 가까운 원인 |
|---|---|---|
| "`415 Unsupported Media Type`" | 요청 헤더에 `Content-Type`이 무엇으로 찍혔나 | media type 계약 |
| "body는 JSON처럼 생겼어요" | JSON 모양과 JSON 선언이 둘 다 맞나 | `Content-Type` 누락/불일치 |
| "`application/json`인데도 415예요" | 컨트롤러 `consumes`와 실제 헤더가 같은가 | `consumes` mismatch |
| "컨트롤러 로그가 안 찍혀요" | binding 전에 막힌 것인가 | message converter 선택 전 단계 |

짧게 외우면 이렇다.

- `400`은 내용 해석 실패에 가깝다.
- `415`는 형식 선언 실패에 가깝다.
- "`json`인데 `415 Unsupported Media Type`가 떠요"면 body 값보다 헤더 계약을 먼저 본다.

## 상세 분해

### 1. body가 JSON처럼 보여도 헤더가 틀리면 `415`가 날 수 있다

```http
POST /admin/reservations
Content-Type: text/plain

{"roomId":1,"date":"2026-05-01"}
```

이 요청은 body만 보면 JSON 같지만, 서버에는 "`나는 text/plain이야`"라고 말하고 있다. Spring은 그 선언을 먼저 보고 판단하므로 `415`가 날 수 있다.

### 2. 가장 먼저 볼 것은 `Content-Type: application/json`

초급자 첫 체크는 복잡하지 않다.

1. 요청 헤더에 `Content-Type: application/json`이 있는가
2. Postman, fetch, RestClient가 실제로 그 헤더를 보냈는가
3. 프록시나 테스트 코드가 다른 형식으로 덮어쓰지 않았는가

body 예쁘게 정리하기보다 이 세 줄을 먼저 보는 편이 빠르다.

### 2-1. "`Content-Type: application/json` 안 붙였는데 `415`예요"면 거의 여기서 끝난다

아래처럼 보내면 body 내용이 JSON이어도 Spring은 JSON 요청으로 읽지 못할 수 있다.

```http
POST /admin/reservations

{"roomId":1,"date":"2026-05-01"}
```

이 경우 초급자 첫 수정은 body를 바꾸는 게 아니라 헤더를 붙이는 것이다.

```http
POST /admin/reservations
Content-Type: application/json

{"roomId":1,"date":"2026-05-01"}
```

### 3. 헤더가 맞아 보여도 `consumes`가 다르면 또 `415`가 난다

```java
@PostMapping(value = "/admin/reservations", consumes = "application/json")
public void create(@RequestBody CreateReservationRequest request) {
}
```

컨트롤러가 이렇게 선언돼 있으면, 요청도 그 계약과 맞아야 한다. 초급자에게는 "`헤더도 계약의 일부`"라고 기억시키는 편이 가장 안전하다.

## 흔한 오해와 함정

- "JSON 모양이면 Spring이 알아서 JSON으로 읽어 주겠지"
  아니다. `Content-Type` 선언이 먼저 맞아야 한다.

- "`415`도 그냥 `400` 비슷한 거 아닌가요?"
  아니다. 초급 첫 분기로는 `400 = 값 해석`, `415 = 형식 계약`으로 나누는 편이 좋다.

- "`@RequestBody`면 query/form도 같이 보겠지"
  아니다. 이 문서의 축은 JSON body와 media type 계약이다. query/form 바인딩과는 입구가 다르다.

- "`application/json`인데도 안 돼요"
  이때는 실제 전송 헤더와 컨트롤러 `consumes`를 같이 봐야 한다.

- "`json`인데 `415 Unsupported Media Type`가 떠요?"
  아니다. 그 문장은 오히려 `400`보다 `415` 쪽에 가깝다. JSON 문법보다 media type 계약부터 본다.

## 실무에서 쓰는 모습

RoomEscape 관리자 예약 생성 요청을 예로 들면 이렇게 본다.

| 장면 | 요청 모습 | 먼저 볼 것 |
|---|---|---|
| 정상 | `Content-Type: application/json` + JSON body | 다음 단계로 DTO 변환 진행 |
| `415` | `Content-Type` 누락 또는 `text/plain` | 헤더 선언 수정 |
| 그래도 `415` | 헤더는 맞아 보이지만 `consumes` 불일치 | 컨트롤러 계약과 클라이언트 설정 비교 |

초급자 디버그 순서는 보통 이쪽이 가장 안전하다.

1. 브라우저/도구의 실제 요청 헤더 확인
2. 컨트롤러 `@PostMapping(consumes = ...)` 확인
3. 그다음에야 JSON 문법이나 DTO 타입 문제를 본다

## 더 깊이 가려면

- `415`와 `400`을 한 번에 가르고 싶으면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)를 먼저 본다.
- query/form 바인딩과 JSON body 바인딩이 섞였으면 [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드](./spring-modelattribute-vs-requestbody-binding-primer.md)로 먼저 돌아간다.
- `Accept`, `Content-Type`, `produces`, `consumes`를 더 넓게 보려면 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)로 이어간다.
- HTTP 헤더 감각 자체가 약하면 [HTTP 요청·응답 헤더 기초](../network/http-request-response-headers-basics.md)를 먼저 붙인다.

## 면접/시니어 질문 미리보기

**Q. body가 JSON처럼 보여도 왜 `415`가 날 수 있나요?**  
Spring은 body 내용보다 먼저 `Content-Type`으로 요청 형식을 판단하기 때문이다.

**Q. `415`와 `400`의 첫 차이는 무엇인가요?**  
초급 기준으로 `415`는 media type 계약 문제, `400`은 JSON parse/type 문제로 먼저 나눈다.

**Q. `application/json`인데도 `415`면 무엇을 보나요?**  
실제 전송 헤더와 컨트롤러 `consumes` 계약이 정말 같은지 확인한다.

## 한 줄 정리

`@RequestBody 415`는 "JSON 값이 틀렸다"보다 "`이 body를 JSON으로 읽어도 된다고 서버와 약속했는가`"를 먼저 확인해야 푸는 문제다.
