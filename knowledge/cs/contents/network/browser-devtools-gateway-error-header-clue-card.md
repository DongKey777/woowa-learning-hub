---
schema_version: 3
title: "Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드"
concept_id: network/browser-devtools-gateway-error-header-clue-card
canonical: true
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
- devtools-header-attribution
- gateway-vs-app-owner
- request-id-tracing-handoff
aliases:
- server via x-request-id
- devtools response header first pass
- gateway error header clue
- response header owner
- proxy app attribution header
- application problem json owner
symptoms:
- response header가 비어 있는데도 app body와 controller 로그만 찾는다
- Server나 Via가 proxy를 가리키는데 JSON이라는 이유로 app 응답이라고 확정한다
- X-Request-Id와 traceparent의 역할을 섞어 request 추적 키를 놓친다
- 502/504에서 gateway local reply와 app error payload를 header 없이 구분하려 한다
intents:
- troubleshooting
- symptom
- comparison
prerequisites:
- network/browser-devtools-first-checklist-1minute-card
- network/http-request-response-headers-basics
next_docs:
- network/browser-devtools-502-504-app-500-decision-card
- network/browser-devtools-response-body-ownership-checklist
- network/x-request-id-gateway-app-log-trace-beginner-bridge
- network/browser-devtools-traceparent-vs-tracestate-mini-card
- network/proxy-local-reply-vs-upstream-error-attribution
linked_paths:
- contents/network/browser-devtools-blocked-canceled-failed-primer.md
- contents/network/browser-devtools-first-checklist-1minute-card.md
- contents/network/browser-devtools-502-504-app-500-decision-card.md
- contents/network/browser-devtools-traceparent-vs-tracestate-mini-card.md
- contents/network/browser-devtools-response-body-ownership-checklist.md
- contents/network/x-request-id-gateway-app-log-trace-beginner-bridge.md
- contents/network/browser-devtools-x-cache-age-ownership-1minute-card.md
- contents/network/http-request-response-headers-basics.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/spring/spring-mvc-request-lifecycle-basics.md
confusable_with:
- network/browser-devtools-blocked-canceled-failed-primer
- network/browser-devtools-502-504-app-500-decision-card
- network/browser-devtools-response-body-ownership-checklist
- network/browser-devtools-traceparent-vs-tracestate-mini-card
- network/proxy-local-reply-vs-upstream-error-attribution
forbidden_neighbors: []
expected_queries:
- "DevTools 응답 헤더에서 Server Via X-Request-Id를 처음에 어떻게 읽어?"
- "application/problem+json인데 Server가 nginx면 app 응답인지 gateway 응답인지 어떻게 구분해?"
- "response headers가 비어 있으면 browser blocked canceled failed 쪽을 먼저 봐야 해?"
- "X-Request-Id가 있으면 app log와 gateway log 중 어디부터 추적해?"
- "502 504에서 Server Via header로 proxy local reply 가능성을 어떻게 봐?"
contextual_chunk_prefix: |
  이 문서는 DevTools response headers에서 Server, Via, X-Request-Id,
  traceparent를 1분 안에 읽어 browser-side failure, proxy/gateway local
  reply, app까지 도달한 request를 나누는 beginner symptom router다.
---
# Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드

> 한 줄 요약: DevTools 응답 헤더에서 `Server`, `Via`, `X-Request-Id` 세 칸만 먼저 읽어도 "브라우저가 막은 건지, proxy가 대신 응답한 건지, app까지 들어간 건지"를 초급자 1차 분기로 빠르게 가를 수 있고, `application/problem+json`도 곧바로 app JSON으로 오해하지 않게 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)
- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- [Browser DevTools `traceparent` vs `tracestate` 초급 미니 카드](./browser-devtools-traceparent-vs-tracestate-mini-card.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- [Browser DevTools `X-Cache` / `Age` 1분 헤더 카드](./browser-devtools-x-cache-age-ownership-1minute-card.md)
- [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: server via x-request-id, devtools response header first pass, x-request-id 뭐예요, via 헤더 뭐예요, server 헤더 뭐예요, browser proxy app attribution, gateway error first check, response header who made this, 처음 devtools header, proxy 흔적 헤더, what is x-request-id, traceparent only no x-request-id, traceparent 처음, application/problem+json beginner, 처음 에러 헤더 볼 때

## 핵심 개념

처음에는 헤더를 많이 보지 말고, 이 세 개를 **명찰**처럼 읽으면 된다.

- `Server`: 누가 응답을 만든 것처럼 보이는가
- `Via`: 중간 proxy나 gateway를 거쳤는가
- `X-Request-Id`: 이 요청을 로그에서 다시 찾을 실마리가 있는가

초급자 첫 질문은 "정확한 근본 원인"이 아니라 "브라우저 / proxy / app 중 어디부터 봐야 하나"다. 이 세 헤더는 그 1차 분기에 도움을 준다.

## 한눈에 보기

| DevTools에서 먼저 보인 것 | 초급자 첫 해석 | 1차 소유 후보 | 먼저 붙일 다음 질문 |
|---|---|---|---|
| 응답 헤더 자체가 거의 없다 | 브라우저 차단, 취소, 전송 실패처럼 HTTP 응답 전 단계일 수 있다 | browser | `Status`가 `(blocked)`/`canceled`/`(failed)`인가 |
| `Server: nginx` 같은 값이 눈에 띈다 | proxy나 web server가 응답을 만든 장면 후보다 | proxy | body가 gateway 기본 HTML인가 |
| `Via: 1.1 varnish` 같은 값이 있다 | 중간 hop을 거쳤다는 뜻이다 | proxy | 이 응답이 app 원본인지, intermediary가 만든 응답인지 |
| `X-Request-Id`가 있다 | 적어도 추적용 식별자를 남길 만큼 서버 체인을 탔을 가능성이 크다 | app 또는 gateway | app/log/trace에서 같은 ID를 찾을 수 있는가 |
| `traceparent`는 있는데 `X-Request-Id`는 없다 | request ID 누락으로 단정하기보다 trace 중심 추적 구성을 먼저 의심한다 | gateway 또는 app tracing chain | tracing UI나 로그의 `traceId` 필드로 같은 요청을 찾을 수 있는가 |

짧게 외우면 이렇게 보면 된다.

```text
헤더 없음 -> 브라우저/전송 단계 의심
Server/Via 강함 -> proxy 문맥 먼저
X-Request-Id 있음 -> 서버 체인 추적 가능성 먼저
```

처음 보는 사람이 가장 헷갈리는 질문을 한 줄로 바꾸면 이렇다.

- "헤더가 비어 있으면 browser 쪽부터"
- "`Server`/`Via`가 먼저 보이면 proxy 쪽부터"
- "`X-Request-Id`가 있으면 app/gateway 로그 추적부터"
- "`traceparent`만 있으면 request ID 누락 단정보다 traceId 추적부터"

## JSON이어도 헤더가 더 강한 장면

처음에는 "JSON이면 app" 대신 아래처럼 외우면 안전하다.

```text
JSON 모양 -> owner 확정 아님
Server/Via 강함 -> proxy/gateway 후보 먼저 유지
X-Request-Id -> gateway log와 app log 둘 다 대조
```

| DevTools에서 같이 보인 것 | 초급자 첫 해석 | 왜 JSON shape만 보면 위험한가 | 먼저 볼 것 |
|---|---|---|---|
| `application/problem+json` + `502/504` + `Server`/`Via` | RFC 7807 모양이어도 gateway local reply 후보를 같이 연다 | `problem+json`은 app 전용 형식이 아니라 gateway도 잘 쓴다 | `title`, `detail`이 generic한지, app 공통 `errorCode`가 없는지 |
| vendor/common error envelope + `Server: envoy`/`nginx`/CDN 흔적 | JSON이어도 proxy/vendor가 대신 말한 장면일 수 있다 | `{ "status": 504, "message": "upstream timeout" }` 같은 포맷은 app 계약과 다를 수 있다 | vendor header, 짧은 generic 문구, upstream timeout wording |
| app처럼 보이는 JSON인데 `Via`가 강하고 `X-Request-Id`는 gateway 로그에만 있음 | "요청은 체인을 탔지만 app가 직접 답한 건 아닐 수 있다" | JSON body가 있다고 해서 app controller가 생성했다고 단정할 수 없다 | gateway access log와 app log 둘 다 같은 ID가 있는지 |

## 헤더에서 payload 예시로 한 번에 건너뛰기

헤더로 1차 owner를 좁혔다면, 다음 10초는 body 전체를 읽지 말고 payload 말투만 확인하면 된다.

| 헤더 clue | 바로 붙일 payload 질문 | 다음 점프 |
|---|---|---|
| `Server`/`Via`가 강하고 `502`/`504`다 | preview가 `{ "title": "Gateway Timeout", "status": 504, "detail": ... }`처럼 generic `problem+json`인가 | [Response Body Ownership 체크리스트의 `payload 미니 예시 3개`](./browser-devtools-response-body-ownership-checklist.md#payload-미니-예시-3개)에서 gateway generic 예시를 바로 대조 |
| `Server`/`Via`는 보이지만 body가 `{ "error": "...", "reason": "...", "request_id": ... }` 쪽이다 | vendor/gateway envelope인지, app 공통 `errorCode` 계약인지 | 같은 `payload 미니 예시 3개`에서 vendor/gateway envelope 예시와 비교 |
| `X-Request-Id`가 app 로그/trace까지 이어지고 `404`/`409`다 | `{ "errorCode": "...", "message": "...", "traceId": ... }` 또는 도메인 `ProblemDetail` 말투인가 | [Gateway JSON vs App JSON Tiny Card](./gateway-json-vs-app-json-tiny-card.md)에서 app JSON vs gateway JSON 분기로 바로 이동 |

짧게 연결하면 이렇다.

```text
Server/Via 강함 -> payload에서 generic title/detail/status 또는 vendor envelope 확인
X-Request-Id가 app까지 이어짐 -> payload에서 errorCode/message/traceId 또는 domain ProblemDetail 확인
```

## `Server`

`Server`는 응답을 만든 소프트웨어 이름이 보일 때가 많다. 예를 들면 `nginx`, `envoy`, `cloudfront`, `Apache` 같은 값이 보일 수 있다.

초급자 1차 해석은 이 정도면 충분하다.

- proxy나 CDN 이름이 먼저 보이면 "앞단이 대신 말한 장면인가?"를 먼저 본다
- app이 늘 주는 JSON 에러 형식보다 기본 HTML 페이지가 더 강하면 proxy 응답 후보가 커진다
- `application/problem+json`이나 vendor JSON envelope이 보여도 `Server`가 gateway/edge 이름이면 app 확정을 잠깐 보류한다

다만 `Server`는 최종 진실표가 아니다. 보안 정책 때문에 지워지거나, app server 이름과 reverse proxy 이름이 섞여 보일 수도 있다.

## `Via`

`Via`는 "이 응답이 중간 proxy를 거쳤다"는 흔적이다. 예를 들면 CDN, gateway, caching proxy가 응답을 전달하면서 붙일 수 있다.

초급자에게 중요한 해석은 하나다.

- `Via`가 보이면 browser와 app 사이에 intermediary가 있다는 뜻이므로, `502`/`504` 같은 응답을 app 코드만으로 바로 설명하지 않는다
- body가 JSON이어도 `Via`가 강하면 "중간 hop이 이 JSON을 만들었나?"를 먼저 묻는다

즉 `Via`는 "누가 최종 에러를 만들었는가"를 100% 확정해 주지는 않지만, **proxy 문맥을 먼저 열어 주는 스위치**다.

## `X-Request-Id`

`X-Request-Id`는 요청 추적용 식별자다. gateway가 만들 수도 있고, app이 그대로 이어 받을 수도 있다.

초급자 첫 판단은 아래 두 줄이면 된다.

- 값이 있으면 "이 요청을 서버 로그에서 다시 찾을 실마리"가 있다
- 값이 app 로그와 같게 이어지면 "요청이 app까지 들어갔는지"를 확인하기 쉬워진다

그래서 `500`이나 `404`를 볼 때 `X-Request-Id`가 있으면, "브라우저가 혼자 실패했다"보다 "서버 체인 안에서 처리된 요청" 쪽으로 먼저 기운다.

초급자 다음 액션도 같이 붙이면 더 안전하다.

- gateway access log에 같은 ID가 있는지 본다
- app 로그에 같은 ID가 찍히는지 본다
- tracing 화면이 있으면 request ID나 연결된 trace를 찾는다

`traceparent`가 있고 `X-Request-Id`가 없으면 한 줄 분기는 이것이면 충분하다: "`request id`가 빠졌다고 단정하지 말고, 이 서비스는 `traceId`를 주 검색 키로 쓰는지부터 본다."

## 실전 예시 한 장

```http
HTTP/1.1 502 Bad Gateway
Server: nginx
Via: 1.1 varnish
X-Request-Id: 8f2d2b71
Content-Type: application/problem+json
```

이 한 장을 초급자용으로 읽으면 충분하다.

- `Server`와 `Via`가 같이 보이므로 browser 단독 실패보다 proxy/gateway 응답 후보가 강하다
- `X-Request-Id`가 있으므로 "이 요청이 서버 체인을 탔다"는 추적 실마리가 있다
- `application/problem+json`이어도 `502 Bad Gateway`와 `Server`/`Via` 조합이 더 강하므로 app JSON보다 gateway local reply 후보를 먼저 본다

### 세 헤더가 없을 때

이 경우는 오히려 해석이 쉬워질 때가 있다.

- `Status`가 `(blocked)`면 브라우저 정책/확장 프로그램/CORS 같은 browser-side 차단 후보
- `canceled`면 페이지 이동, 새로고침, JS abort 후보
- `(failed)`면 DNS, TLS, 네트워크 실패처럼 HTTP 응답 전에 끊긴 장면 후보

즉 **응답 헤더가 없다는 사실 자체**가 "app 에러 body를 읽는 단계가 아니었다"는 힌트가 될 수 있다.

이 세 status를 헤더 없는 row 기준으로 따로 익히고 싶다면 [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)을 먼저 보면 된다.

## 흔한 오해와 함정

- `Server` 값 하나만 보고 "범인은 nginx다"라고 확정한다. `Server`는 힌트이지 판결문이 아니다.
- `Via`가 없으면 proxy가 없다고 단정한다. 일부 서비스는 `Via`를 숨기거나 다른 헤더만 남긴다.
- `X-Request-Id`가 없으면 app에 절대 도달하지 않았다고 말한다. 추적 헤더를 안 쓰는 서비스도 있다.
- `X-Request-Id`가 있으면 무조건 app이 직접 에러를 만들었다고 생각한다. gateway가 만든 응답에도 request ID는 붙을 수 있다.
- `application/problem+json`이면 app 예외 포맷이라고 단정한다. gateway, CDN, API proxy도 이 형식을 쓸 수 있다.
- JSON field 모양만 보고 owner를 확정한다. 초급자 첫 pass에서는 `Server`/`Via`가 JSON shape보다 더 강한 단서일 때가 많다.
- 브라우저 에러 장면에서 응답 헤더를 찾느라 시간을 쓴다. `(blocked)`·`canceled`·`(failed)`는 헤더보다 `Status` 판독이 먼저다.

## 실무에서 쓰는 모습

아래처럼 3장면만 구분해도 첫 DevTools pass 품질이 좋아진다.

| 장면 | DevTools에서 보이는 것 | 초급자 첫 문장 |
|---|---|---|
| A | `Status: 502`, `Server: nginx`, `Via: 1.1 varnish`, 짧은 HTML | "app JSON 에러보다 proxy/gateway 기본 응답 후보를 먼저 본다" |
| B | `Status: 504`, `Content-Type: application/problem+json`, `Server: envoy`, `Via: 1.1 varnish` | "JSON이어도 `Server`/`Via`가 더 강해서 gateway timeout local reply 후보를 먼저 본다" |
| C | `Status: (blocked)`, 응답 헤더 거의 없음 | "서버 에러보다 브라우저 차단 장면을 먼저 본다" |
| D | `Status: 500`, `Content-Type: application/json`, `X-Request-Id: 8f...` | "요청은 서버 체인으로 들어갔고 app 로그/trace를 먼저 찾는다" |

실무에서 가장 안전한 3단계는 이렇다.

1. `Status`가 숫자인지, `(blocked)` 같은 브라우저 메모인지 먼저 가른다.
2. 숫자 응답이면 `Server`와 `Via`로 proxy 문맥을 본다.
3. `X-Request-Id`가 있으면 그 값을 incident 메모에 적고 로그 탐색 키로 쓴다.

## 더 깊이 가려면

- DevTools 첫 판독 순서 전체가 필요하면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- `500`/`502`/`504`를 첫 분기로 나누려면 [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- JSON body owner를 login HTML, gateway JSON, app JSON으로 더 잘게 나누려면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- 헤더 clue 다음에 payload 예시 3개를 바로 대조하려면 [Browser DevTools Response Body Ownership 체크리스트의 `payload 미니 예시 3개`](./browser-devtools-response-body-ownership-checklist.md#payload-미니-예시-3개)
- cache 관련 응답 헤더가 보일 때 app ownership을 언제 보류해야 하는지 보려면 [Browser DevTools `X-Cache` / `Age` 1분 헤더 카드](./browser-devtools-x-cache-age-ownership-1minute-card.md)
- header 기초가 아직 약하면 [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- local reply인지 upstream 실패 번역인지 더 엄밀하게 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- `X-Request-Id`를 DevTools 다음에 gateway 로그, app 로그, trace로 어떻게 이어 보는지 보려면 [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)
- `X-Request-Id`가 실제 서버 처리 흐름에서 어디에 걸리는지 보려면 [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

## 한 줄 정리

DevTools 첫 pass에서는 `Server`와 `Via`로 proxy 문맥을 먼저 열고, `X-Request-Id`로 서버 추적 가능성을 확인하며, 헤더가 거의 없으면 브라우저/전송 단계 실패를 먼저 의심하면 된다.
