# Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드: 폼/query 바인딩과 JSON body를 한 장으로 분리하기

> 한 줄 요약: `@ModelAttribute`는 query string이나 form 필드를 객체에 묶는 쪽이고, `@RequestBody`는 JSON body를 DTO로 바꾸는 쪽이라서 둘을 섞어 보면 `400` 원인도 같이 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유: JSON, 타입, `Content-Type` 첫 분리](./spring-requestbody-400-before-controller-primer.md)
- [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
- [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
- [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: modelattribute vs requestbody beginner, @modelattribute 뭐예요, @requestbody 뭐예요, spring mvc binding difference, spring 400 원인 헷갈려요, get은 되는데 post는 400 spring, modelattribute requestbody 차이, 폼 바인딩 json 바인딩 차이, get admin reservations query vs post admin reservations json, roomescape admin binding primer, controller 전에 415, json인데 unsupported media type, post json unsupported media type spring, requestbody 415 before controller, content-type application json beginner

## 핵심 개념

처음에는 이렇게만 잡으면 된다.

- `@ModelAttribute`는 URL query string이나 form 필드를 꺼내서 객체 필드에 채운다.
- `@RequestBody`는 HTTP body를 읽어서 JSON 같은 본문 전체를 DTO로 바꾼다.
- 둘 다 "컨트롤러 파라미터를 준비한다"는 점은 같지만, **어디서 값을 읽는지**가 다르다.

그래서 RoomEscape 관리자 화면에서 검색 조건을 받는 `GET /admin/reservations?date=2026-05-01&name=neo` 같은 요청은 `@ModelAttribute` 쪽 감각이 더 잘 맞고, 예약 생성처럼 JSON 본문을 보내는 `POST /admin/reservations`는 `@RequestBody` 쪽 감각이 맞다.

초급자가 자주 헷갈리는 이유는 둘 다 "DTO를 받는 코드"처럼 보이기 때문이다. 하지만 query/form 바인딩과 JSON body 바인딩은 출발점부터 다르다.

검색 문장으로는 보통 아래처럼 들어온다.

- "`GET`은 되는데 `POST`는 왜 바로 `400`이에요?"
- "검색 query는 되는데 JSON 생성 요청은 왜 안 돼요?"
- "`@ModelAttribute`랑 `@RequestBody` 중 뭘 써야 해요?"
- "JSON인데 왜 `Unsupported Media Type`이에요?"
- "컨트롤러 전에 `415`가 나요. `@RequestBody` 문제예요?"

## 한눈에 보기

| 항목 | `@ModelAttribute` | `@RequestBody` |
|---|---|---|
| 값이 오는 곳 | query string, form field, 일부 path/query 조합 | HTTP body 전체 |
| 자주 보는 요청 예시 | `GET /admin/reservations?date=2026-05-01` | `POST /admin/reservations` + JSON |
| 대표 `Content-Type` | query string, `application/x-www-form-urlencoded`, `multipart/form-data` | 보통 `application/json` |
| Spring이 하는 일 | 문자열 필드를 객체 프로퍼티에 채운다 | body를 읽고 JSON을 DTO로 변환한다 |
| 초급자 첫 오해 | "JSON도 DTO니까 이것도 되겠지?" | "query 값도 body처럼 읽겠지?" |
| 자주 보이는 실패 | 필수 query 누락, 숫자/날짜 문자열 변환 실패 | JSON 문법 오류, DTO 타입 불일치, `Content-Type` 불일치 |
| `400`을 볼 때 첫 확인 | 파라미터 이름, 문자열 -> 타입 변환 | JSON 모양, 필드 타입, `Content-Type` |

짧게 말하면 `@ModelAttribute`는 "칸마다 적힌 폼을 읽는 쪽", `@RequestBody`는 "봉투 안 JSON 문서를 통째로 읽는 쪽"이다.

## 언제 무엇을 쓰는가

### `@ModelAttribute`가 잘 맞는 경우

검색 조건, 페이지 번호, 정렬 조건처럼 URL이나 form 필드로 잘 표현되는 입력에 잘 맞는다.

```java
@GetMapping("/admin/reservations")
public List<ReservationResponse> find(@ModelAttribute ReservationSearchRequest request) {
    return reservationService.find(request);
}
```

```text
GET /admin/reservations?date=2026-05-01&page=1
```

이 경우 Spring은 query string의 `date`, `page` 값을 꺼내 `ReservationSearchRequest` 필드에 채운다.

### `@RequestBody`가 잘 맞는 경우

생성/수정 API처럼 JSON 구조 자체가 중요한 입력에 잘 맞는다.

```java
@PostMapping("/admin/reservations")
public ReservationResponse create(@RequestBody CreateReservationRequest request) {
    return reservationService.create(request);
}
```

```json
{
  "roomId": 1,
  "date": "2026-05-01",
  "time": "18:00",
  "name": "neo"
}
```

이 경우 Spring은 body를 읽고 JSON 전체를 `CreateReservationRequest`로 바꾼 뒤에야 컨트롤러를 호출한다.

## 같은 기능을 두 요청으로 붙여 외우기

초급자에게는 "`GET /admin/reservations` 검색"과 "`POST /admin/reservations` 생성"을 한 쌍으로 묶어 외우는 편이 가장 빠르다.

| 장면 | `GET /admin/reservations` 검색 | `POST /admin/reservations` 생성 |
|---|---|---|
| 화면에서 하는 일 | 검색창에 날짜, 이름, 페이지 조건을 적는다 | 예약 생성 폼을 제출해 새 데이터를 만든다 |
| HTTP에서 값이 놓이는 자리 | URL query string | HTTP body(JSON) |
| Spring 파라미터 감각 | `@ModelAttribute ReservationSearchRequest` | `@RequestBody CreateReservationRequest` |
| 값 읽는 느낌 | "검색 조건 칸을 하나씩 꺼내 채운다" | "예약 문서 한 장을 통째로 읽는다" |
| 처음 실패를 볼 자리 | query key 이름, 문자열 -> 날짜/숫자 변환 | JSON 문법, DTO 타입, `Content-Type` |

같은 `/admin/reservations`라도 "`목록을 좁히는 요청`인지", "`새 예약을 만드는 요청`인지"를 먼저 보면 바인딩 감각이 훨씬 덜 섞인다.

```text
GET  /admin/reservations?date=2026-05-01&name=neo&page=1
-> 검색 조건 칸이 URL에 드러난다
-> @ModelAttribute

POST /admin/reservations
Content-Type: application/json
{
  "roomId": 1,
  "date": "2026-05-01",
  "time": "18:00",
  "name": "neo"
}
-> 생성 데이터 문서가 body에 들어간다
-> @RequestBody
```

외울 때는 길게 생각하지 말고 이렇게 끊으면 된다.

- 검색 조건을 URL에 붙여 다시 호출하고 싶다 -> `@ModelAttribute`
- 생성 데이터를 JSON 한 덩어리로 보낸다 -> `@RequestBody`
- 둘 다 DTO처럼 보여도 "값이 놓인 자리"가 다르면 바인딩 경로도 달라진다

## 왜 `400` 원인을 자꾸 섞어 보게 되는가

겉으로는 둘 다 "`400 Bad Request`"처럼 보여도 출발점이 다르다.

| 보이는 현상 | 먼저 의심할 쪽 | 이유 |
|---|---|---|
| `GET /admin/reservations?date=tomorrow`에서 바로 `400` | `@ModelAttribute` 쪽 문자열 변환 | query 값 `"tomorrow"`를 `LocalDate`로 바꾸지 못할 수 있다 |
| 검색 조건 일부가 비어 들어온다 | `@ModelAttribute` 쪽 파라미터 이름 | query key 이름과 DTO 필드명이 안 맞을 수 있다 |
| `POST` JSON 요청에서 컨트롤러 로그가 안 찍힌다 | `@RequestBody` 쪽 message conversion | JSON 문법이나 DTO 타입이 먼저 깨졌을 수 있다 |
| `POST` JSON 요청인데 컨트롤러 전에 `415`가 난다 | `@RequestBody` + `Content-Type` 계약 | JSON처럼 보여도 Spring은 먼저 body 형식 계약부터 확인한다 |
| "JSON인데 `Unsupported Media Type`"가 뜬다 | `@RequestBody` + media type 선택 | body 내용보다 `Content-Type`, `consumes` 불일치를 먼저 의심해야 한다 |
| `415 Unsupported Media Type` | `@RequestBody` + `Content-Type` 계약 | JSON body를 보냈는데 `application/json`이 아니거나 `consumes`와 안 맞을 수 있다 |

초급자에게 가장 중요한 분리 기준은 이것이다.

- URL 뒤 `?key=value`나 form 칸에서 온 값이면 `@ModelAttribute`부터 본다.
- raw JSON 본문이 핵심이면 `@RequestBody`부터 본다.

즉 "DTO를 받는다"가 아니라 "어디서 값을 읽느냐"를 먼저 보면 `400` 원인을 훨씬 빨리 좁힐 수 있다.

한 줄로 다시 자르면 이렇다.

- query/form이 먼저 떠오르면 `@ModelAttribute`
- JSON body가 먼저 떠오르면 `@RequestBody`
- "같은 `/admin/reservations`인데 GET은 되고 POST만 깨진다"면 두 요청의 입력 위치를 따로 봐야 한다
- "POST JSON인데 controller 전에 `415`"면 JSON 값보다 `Content-Type`과 media type 계약을 먼저 본다

## 흔한 오해와 함정

- "`@ModelAttribute`도 객체니까 JSON body를 넣어도 되겠지"
  아니다. 초급자 기준 기본 감각은 query/form 쪽 바인딩이다.

- "`@RequestBody`면 query string도 같이 자동으로 다 읽는다"
  아니다. 핵심 입력 출처는 body다. query 값은 별도 파라미터나 다른 바인딩 경로로 생각하는 편이 안전하다.

- "`400`이면 둘 다 같은 원인이다"
  아니다. `@ModelAttribute`는 파라미터 이름/문자열 변환을 먼저 보고, `@RequestBody`는 JSON 문법/DTO 타입/`Content-Type`을 먼저 본다.

- "`GET`에도 무조건 `@RequestBody`를 붙이면 더 명확하다"
  실무의 초급 기본값으로는 검색 조건처럼 URL에 잘 드러나는 입력은 `@ModelAttribute`나 `@RequestParam`이 더 읽기 쉽다.

## 실무에서 쓰는 모습

RoomEscape 관리자 기능을 단순화하면 두 장면으로 나눠 보면 된다.

1. 예약 목록 필터링
   `GET /admin/reservations?date=2026-05-01&name=neo`
   이건 "검색 조건 칸"에 가깝기 때문에 `@ModelAttribute ReservationSearchRequest`로 받는 쪽이 자연스럽다.
2. 예약 생성
   `POST /admin/reservations` + JSON body
   이건 "새 예약 데이터를 담은 문서"에 가깝기 때문에 `@RequestBody CreateReservationRequest`가 자연스럽다.

초급자 첫 점검 순서도 다르게 가져가면 좋다.

- 목록 검색이 이상하면 query key 이름, 필드 타입, 기본값을 먼저 본다.
- 생성 API가 바로 `400`이면 JSON 문법, 날짜/시간 타입, `Content-Type`을 먼저 본다.
- 같은 `/admin/reservations`인데도 GET 검색은 "`URL 칸 채우기`", POST 생성은 "`JSON 문서 읽기`"라고 떠올리면 recall이 오래 간다.

## 더 깊이 가려면

- 요청 전체 흐름 안에서 이 둘이 어느 단계에서 준비되는지 보고 싶으면 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)로 이어간다.
- `@RequestBody` 쪽 `400`을 JSON 문법, DTO 타입, `Content-Type`으로 더 잘게 쪼개 보고 싶으면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)를 본다.
- "`json인데 unsupported media type`처럼 `415` 증상으로 들어왔다"면 [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)에서 `Content-Type`과 `consumes` 축을 바로 확인한다.
- 바인딩 실패와 validation 실패 순서를 더 엄밀하게 보고 싶으면 [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)로 내려간다.
- HTTP 메서드와 body/query 역할을 먼저 정리하고 싶으면 [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)을 같이 보면 연결이 잘 된다.

## 면접/시니어 질문 미리보기

**Q. `@ModelAttribute`와 `@RequestBody`의 가장 큰 차이는 무엇인가요?**  
값을 읽는 출처가 다르다. `@ModelAttribute`는 주로 query/form 필드, `@RequestBody`는 body 전체를 DTO로 변환한다.

**Q. 왜 둘 다 `400`이 날 수 있는데 원인 분리가 중요한가요?**  
겉 응답은 비슷해도 `@ModelAttribute`는 문자열 변환과 파라미터 이름을 먼저 보고, `@RequestBody`는 JSON 문법과 message conversion을 먼저 봐야 해서 디버깅 출발점이 다르다.

**Q. 검색 API와 생성 API에서 보통 무엇을 고르나요?**  
검색 조건은 `@ModelAttribute`나 `@RequestParam`, 생성/수정 JSON API는 `@RequestBody`가 초급 기본값으로 가장 읽기 쉽다.

## 한 줄 정리

`@ModelAttribute`는 query/form 입력을 객체에 채우는 바인딩이고 `@RequestBody`는 JSON body를 DTO로 바꾸는 바인딩이라서, 두 어노테이션을 값의 출처 기준으로 나눠 보면 `400` 원인 혼동이 크게 줄어든다.
