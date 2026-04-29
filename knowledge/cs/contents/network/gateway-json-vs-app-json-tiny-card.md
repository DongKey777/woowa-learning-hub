# Gateway JSON vs App JSON Tiny Card

> 한 줄 요약: `502`/`504`에서 보이는 `title/detail` 중심 generic JSON은 gateway/proxy local reply 후보로 먼저 읽고, 서비스가 늘 쓰는 `errorCode/message/traceId` 같은 필드는 app-owned error envelope 후보로 먼저 읽으면 "`JSON이면 다 앱 에러인가요?`" 질문의 첫 분기가 빨라진다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](../spring/spring-custom-error-dto-to-problemdetail-handoff-primer.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: gateway json vs app json, 502 json vs app error, 504 json title detail, generic problem json beginner, service error envelope beginner, errorcode message traceid, json이면 다 앱 에러인가요, gateway local reply json, proxy json error what is, devtools title detail why, 처음 gateway json 헷갈려요, app owned json basics

## 핵심 개념

처음에는 필드 뜻을 다 외우려 하지 말고 "이 JSON이 누구 말투인가"만 먼저 가르면 된다.

- gateway/proxy JSON: 앞단이 upstream 문제를 대신 설명하려고 만든 generic 응답 후보
- app-owned JSON: 서비스가 자기 API 계약대로 직접 내려준 에러 envelope 후보

초급자가 가장 자주 틀리는 장면은 `application/json`을 보자마자 "그럼 앱이 만든 에러네요"라고 확정하는 것이다. `502`/`504`에서는 JSON이어도 gateway가 자기 local reply를 내려줄 수 있다.

## 한눈에 보기

| 지금 보인 조합 | 먼저 붙일 라벨 | 왜 이렇게 읽나 |
|---|---|---|
| `502`/`504` + `application/json` + `title/detail/status` | gateway/proxy JSON 후보 | generic timeout/bad gateway 설명이 먼저 보인다 |
| `400`/`404`/`500` + `application/json` + `errorCode/message/traceId` | app-owned JSON 후보 | 서비스 계약 필드와 도메인 문장이 먼저 보인다 |
| `502`/`504` + `application/problem+json` + `Gateway Timeout` | app 확정 보류, gateway 후보 우선 | `problem+json`은 app 전용이 아니라 gateway도 쓴다 |
| `200` + `application/json` + 정상 데이터 shape | 에러 owner 분기보다 정상 응답 후보 | status 자체가 에러가 아니다 |

짧게 외우면 이렇다.

```text
title/detail/status -> generic gateway JSON 후보
errorCode/message/traceId -> service-owned JSON 후보
```

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
| 필드 이름 | `title`, `detail`, `status`, `reason` | `errorCode`, `message`, `traceId`, `fieldErrors` |
| 문장 톤 | generic timeout/connectivity 설명 | 서비스 도메인 규칙, 검증 메시지 |
| header 단서 | `Server`, `Via`, vendor 흔적이 강함 | 서비스 tracing/header 규칙이 더 익숙함 |

처음 메모는 한 줄이면 충분하다.

- "`504` + `title/detail`이라 gateway JSON 후보"
- "`500` + `errorCode`라 app-owned JSON 후보"

## 흔한 오해와 함정

- `application/json`이면 무조건 app이라고 단정한다. `502`/`504` generic JSON은 gateway일 수 있다.
- `problem+json`이면 무조건 Spring 예외라고 단정한다. proxy나 gateway도 같은 형식을 쓴다.
- `500`만 app 에러라고 외우고 `504` JSON도 app 로그부터 찾는다. 먼저 owner를 가르는 편이 빠르다.
- 필드 이름만 보고 끝낸다. `Status`와 `Server`/`Via`도 같이 묶어야 안전하다.
- `message` 필드 하나만 보고 app 계약이라고 착각한다. generic vendor envelope에도 `message`는 있을 수 있다.

## 실무에서 쓰는 모습

DevTools `Preview`에서 아래 둘을 봤다고 하자.

| 장면 | preview 첫 인상 | 초급자 첫 판독 |
|---|---|---|
| A | `{ "title": "Gateway Timeout", "status": 504, "detail": ... }` | gateway/proxy가 upstream timeout을 JSON으로 대신 말한 후보 |
| B | `{ "errorCode": "PAYMENT_DECLINED", "message": "결제를 승인할 수 없습니다.", "traceId": ... }` | 서비스가 자기 에러 계약으로 직접 말한 후보 |

이때 다음 한 걸음도 다르다.

- A면 app business rule보다 gateway/proxy timeout, upstream 연결, header 단서를 먼저 본다.
- B면 서비스 예외 매핑, 공통 에러 DTO, 도메인 규칙을 먼저 본다.

## 더 깊이 가려면

- `502`/`504`와 `500`의 owner 분기를 큰 그림으로 다시 보려면 [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- JSON/HTML/login/CDN까지 body owner를 넓게 가르려면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- header 단서까지 묶어 보고 싶으면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- 서비스 error DTO와 `ProblemDetail` 경계를 app 쪽에서 보고 싶으면 [Spring 커스텀 Error DTO에서 `ProblemDetail`로 넘어가는 초급 handoff primer](../spring/spring-custom-error-dto-to-problemdetail-handoff-primer.md)

## 한 줄 정리

`502`/`504` JSON에서 `title/detail/status`가 먼저 보이면 gateway/proxy generic reply 후보를 먼저 열고, `errorCode/message/traceId`가 먼저 보이면 서비스-owned JSON error envelope 후보를 먼저 열면 된다.
