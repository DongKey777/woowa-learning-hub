# Gateway JSON vs App JSON Tiny Card

> 한 줄 요약: gateway와 Spring app은 둘 다 RFC 7807 계열 `problem+json` 모양을 낼 수 있으므로, "`같은 `title/detail/status`인데 이거 누가 만든 거예요?`"라는 beginner 질문에는 body shape보다 status, header, trace 단서로 owner를 가르는 bridge가 먼저 필요하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](../spring/spring-custom-error-dto-to-problemdetail-handoff-primer.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: gateway problem+json vs spring problemdetail, rfc 7807 gateway vs app, spring problemdetail ownership beginner, same title detail status who made this, 502 problem json vs app error, gateway local reply json, problemdetail 뭐예요 gateway도 쓰나요, json이면 다 앱 에러인가요, devtools problem json why, 처음 gateway json 헷갈려요, app owned json basics, browser response owner clue, what is problem+json owner

## 핵심 개념

처음에는 RFC 번호보다 "`이 JSON이 누구 말투인가`"만 먼저 가르면 된다.

- gateway/proxy JSON: 앞단이 upstream 문제를 대신 설명하려고 만든 generic 응답 후보
- app-owned JSON: 서비스가 자기 API 계약대로 직접 내려준 에러 envelope 후보

초급자가 가장 자주 틀리는 장면은 아래 두 문장을 같은 뜻으로 착각하는 것이다.

- "`application/problem+json`이다"
- "`그러면 Spring `ProblemDetail`이 만들었다"

이 둘은 같은 뜻이 아니다. `problem+json`은 RFC 7807 계열의 **응답 모양**이고, `ProblemDetail`은 Spring 6+/Boot 3+에서 그 모양을 쓰기 쉽게 만든 **app 쪽 도구**다. gateway나 proxy도 같은 RFC 모양을 local reply에 쓸 수 있다.

즉 `problem+json`은 "주인이 누구냐"보다 "오류를 어떤 형식으로 적었냐"에 더 가깝다.

## 왜 같은 모양이 두 군데에서 나오나

초심자 mental model은 이렇게 잡으면 된다.

- RFC 7807 `problem+json`: 오류를 적는 공용 양식
- Spring `ProblemDetail`: app이 그 양식을 쓰는 방법 중 하나
- gateway local reply: app까지 못 가거나 app 앞에서 막았을 때 앞단이 그 양식을 그대로 흉내 내는 장면

비유하면 `problem+json`은 "민원서 양식"이고, gateway와 app은 둘 다 그 양식에 글을 쓸 수 있다. 다만 이 비유는 여기까지만 맞다. 실제 owner 판정은 양식이 아니라 **누가 어떤 상황에서 응답을 끝냈는지**로 정해야 한다.

## 한눈에 보기

| 지금 보인 조합 | 먼저 붙일 라벨 | 왜 이렇게 읽나 |
|---|---|---|
| `502`/`504` + `application/problem+json` + `Gateway Timeout` | gateway/proxy JSON 후보 우선 | RFC 7807 모양이어도 status와 문장이 앞단 timeout 쪽이다 |
| `404`/`409` + `application/problem+json` + 도메인 문장 | app-owned `ProblemDetail` 후보 우선 | Spring app이 자기 예외를 RFC 7807로 번역했을 가능성이 크다 |
| `400`/`404`/`500` + `application/json` + `errorCode/message/traceId` | app-owned JSON 후보 | 서비스 계약 필드와 도메인 문장이 먼저 보인다 |
| `502`/`504` + `application/json` + `title/detail/status` | gateway/proxy JSON 후보 | generic timeout/bad gateway 설명이 먼저 보인다 |
| `200` + `application/json` + 정상 데이터 shape | 에러 owner 분기보다 정상 응답 후보 | status 자체가 에러가 아니다 |

짧게 외우면 이렇다.

```text
problem+json == owner 확정 아님
502/504 + generic title/detail -> gateway 후보 먼저
404/409 + domain sentence -> app ProblemDetail 후보 먼저
```

## owner를 가르는 추가 단서 4개

같은 `title/detail/status`라도 아래 네 칸을 같이 보면 owner가 훨씬 빨리 갈린다.

| 추가 단서 | gateway/proxy 쪽으로 기우는 신호 | app/Spring 쪽으로 기우는 신호 |
|---|---|---|
| `Status` | `502`/`503`/`504`처럼 upstream hop 문제에 가까움 | `400`/`404`/`409`처럼 도메인/입력 오류에 가까움 |
| `title`/`detail` 문장 | `Gateway Timeout`, `Bad Gateway`, `upstream reset`처럼 generic 운영 문장 | `Reservation not found`, `validation failed`처럼 도메인/입력 문장 |
| header | `Server`, `Via`, vendor header가 강함 | 서비스가 늘 붙이던 tracing/header 규칙이 더 익숙함 |
| trace/log 연결 | gateway access log에서만 ID가 잡힘 | app 로그와 예외 매핑에서 같은 request ID/traceId가 이어짐 |

초급자 메모는 이 정도면 충분하다.

- "`504 problem+json`인데 `Server/Via`가 강해서 gateway 후보"
- "`404 problem+json`인데 app 로그 traceId와 이어져서 Spring `ProblemDetail` 후보"

## 필드 말투를 이렇게 자른다

### generic gateway/proxy JSON

이쪽은 "왜 실패했는지"를 운영 관점의 공통 문구로 짧게 설명하는 경우가 많다.

- `status`, `title`, `detail`, `type`
- `error`, `reason`, `request_id`
- `Gateway Timeout`, `Bad Gateway`, `upstream timeout`, `connection reset`

예시:

```json
{
  "title": "Gateway Timeout",
  "status": 504,
  "detail": "Upstream service did not respond in time."
}
```

이런 shape는 서비스 도메인보다 앞단 hop의 실패 설명에 더 가깝다.

주의할 점은, 이 모양만으로는 gateway 확정이 아니라는 것이다. app도 같은 필드 이름을 쓸 수 있으므로 **status와 문장 톤**을 같이 봐야 한다.

### Spring `ProblemDetail` app JSON

Spring 6+/Boot 3+ 계열에서는 `ProblemDetail`을 통해 app도 비슷한 모양을 쉽게 만든다.

- `status`, `title`, `detail`, `type`, `instance`
- validation, not found, conflict 같은 app 예외를 RFC 7807 계열로 번역
- 필요하면 `traceId`, `errors` 같은 확장 필드를 추가하기도 함

예시:

```json
{
  "type": "https://example.com/problems/reservation-conflict",
  "title": "Reservation conflict",
  "status": 409,
  "detail": "이미 예약된 시간입니다.",
  "instance": "/api/reservations/42"
}
```

이 shape는 gateway generic timeout보다 "`우리 서비스가 이 요청을 어떻게 실패로 해석했나`"에 더 가깝다.

### service-owned app JSON

이쪽은 "우리 서비스 계약에서 어떤 실패였는지"를 도메인 언어로 보여 주는 경우가 많다.

- `errorCode`, `message`, `traceId`
- `fieldErrors`, `path`, `timestamp`
- `ORDER_NOT_FOUND`, `RESERVATION_CONFLICT` 같은 도메인 코드

예시:

```json
{
  "errorCode": "ORDER_NOT_FOUND",
  "message": "주문 42를 찾을 수 없습니다.",
  "traceId": "9f1c2a7e"
}
```

이런 shape는 "`gateway가 왜 timeout을 냈나`"보다 "`서비스가 어떤 규칙으로 실패를 표현하나`"에 더 가깝다.

## 30초 결정표

| 내가 먼저 볼 것 | gateway/proxy JSON 쪽 신호 | app-owned JSON 쪽 신호 |
|---|---|---|
| `Status` | `502`/`504`/`503` | `400`/`404`/`409`/`500` |
| 필드 이름 | `title`, `detail`, `status`, `reason` | `errorCode`, `message`, `traceId`, `fieldErrors`, `instance` |
| 문장 톤 | generic timeout/connectivity 설명 | 서비스 도메인 규칙, 검증 메시지, 리소스 경로 |
| header 단서 | `Server`, `Via`, vendor 흔적이 강함 | 서비스 tracing/header 규칙이 더 익숙함 |
| 로그 단서 | gateway access log까지만 잡힘 | app exception log나 advice trace와 연결됨 |

처음 메모는 한 줄이면 충분하다.

- "`504` + `title/detail`이라 gateway JSON 후보"
- "`404 problem+json` + 도메인 문장이라 app `ProblemDetail` 후보"

## 같은 RFC 7807 모양인데 마지막 판정이 갈리는 예시

| 장면 | body만 보면 | 추가 단서를 붙이면 | 최종 first pass |
|---|---|---|---|
| A | `{ \"title\": \"Gateway Timeout\", \"status\": 504, \"detail\": \"Upstream service did not respond in time.\" }` | `Server: envoy`, `Via` 존재, app 로그 없음 | gateway local reply 후보 |
| B | `{ \"title\": \"Reservation conflict\", \"status\": 409, \"detail\": \"이미 예약된 시간입니다.\" }` | app traceId가 이어지고 서비스의 `409` 정책과 맞음 | Spring `ProblemDetail` 후보 |
| C | `{ \"title\": \"Not Found\", \"status\": 404, \"detail\": \"No static resource\" }` | Spring 기본 `/error`나 framework 경로일 수도 있음 | gateway로 단정하지 말고 app/framework 경계 재확인 |

여기서 C 같은 장면이 중요하다. `problem+json` 모양이어도 반드시 "우리 도메인 controller가 만들었다"는 뜻은 아니다. app 내부에서도 framework 기본 경로와 커스텀 advice가 나뉠 수 있다.

## 흔한 오해와 함정

- `application/json`이면 무조건 app이라고 단정한다. `502`/`504` generic JSON은 gateway일 수 있다.
- `problem+json`이면 무조건 Spring 예외라고 단정한다. proxy나 gateway도 같은 형식을 쓴다.
- `title/detail/status`가 같으면 owner도 같다고 생각한다. 그건 body shape가 같을 뿐이다.
- `500`만 app 에러라고 외우고 `504` JSON도 app 로그부터 찾는다. 먼저 owner를 가르는 편이 빠르다.
- 필드 이름만 보고 끝낸다. `Status`와 `Server`/`Via`도 같이 묶어야 안전하다.
- `message` 필드 하나만 보고 app 계약이라고 착각한다. generic vendor envelope에도 `message`는 있을 수 있다.
- Spring `ProblemDetail`을 쓰면 gateway와 절대 안 겹친다고 생각한다. 표준 형식을 공유하면 겹치는 게 오히려 자연스럽다.

## 실무에서 쓰는 모습

DevTools `Preview`에서 아래 둘을 봤다고 하자.

| 장면 | preview 첫 인상 | 초급자 첫 판독 |
|---|---|---|
| A | `{ "title": "Gateway Timeout", "status": 504, "detail": ... }` | gateway/proxy가 upstream timeout을 JSON으로 대신 말한 후보 |
| B | `{ "title": "Reservation conflict", "status": 409, "detail": "이미 예약된 시간입니다." }` | Spring app이 `ProblemDetail`로 직접 말한 후보 |
| C | `{ "errorCode": "PAYMENT_DECLINED", "message": "결제를 승인할 수 없습니다.", "traceId": ... }` | 서비스가 자기 에러 계약으로 직접 말한 후보 |

이때 다음 한 걸음도 다르다.

- A면 app business rule보다 gateway/proxy timeout, upstream 연결, header 단서를 먼저 본다.
- B면 Spring advice, `ProblemDetail`, app trace/log 연결을 먼저 본다.
- C면 서비스 예외 매핑, 공통 에러 DTO, 도메인 규칙을 먼저 본다.

## 더 깊이 가려면

- `502`/`504`와 `500`의 owner 분기를 큰 그림으로 다시 보려면 [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- JSON/HTML/login/CDN까지 body owner를 넓게 가르려면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- header 단서까지 묶어 보고 싶으면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- 서비스 error DTO와 `ProblemDetail` 경계를 app 쪽에서 보고 싶으면 [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](../spring/spring-custom-error-dto-to-problemdetail-handoff-primer.md)
- Spring app 내부에서도 `ProblemDetail`, framework 기본 오류, commit 이후 실패가 어떻게 갈리는지 더 보려면 [Spring `ProblemDetail` Error Response Design](../spring/spring-problemdetail-error-response-design.md)

## 한 줄 정리

같은 RFC 7807 `problem+json` 모양이 보여도 owner는 body shape가 아니라 `Status`, 문장 톤, `Server`/`Via`, trace 연결로 가르며, `502`/`504` generic 문장은 gateway 후보를 먼저, `404`/`409` 도메인 문장은 Spring `ProblemDetail` 후보를 먼저 연다.
