---
schema_version: 3
title: Cookie DevTools Field Checklist Primer
concept_id: security/cookie-devtools-field-checklist-primer
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids:
- missions/spring-roomescape
- missions/shopping-cart
review_feedback_tags:
- cookie devtools checklist
- cookie field checklist
- cookie compare set-cookie application request
- cookie blocked reason basics
aliases:
- cookie devtools checklist
- cookie field checklist
- cookie compare set-cookie application request
- cookie blocked reason basics
- cookie scope mismatch basics
- cookie request header compare
- cookie name domain path samesite secure
- browser cookie first minute
- 쿠키가 있는데도 요청에 안 감
- cookie 왜 안 보내요
- cookie 뭐예요 basics
- Cookie DevTools Field Checklist Primer
symptoms:
- Application 탭에는 session cookie가 보이는데 실제 API 요청 Cookie header가 비어 있어 로그인 유지가 안 된다
- Set-Cookie, Application 저장 상태, Network 요청 header를 같은 줄에서 비교하지 못해 cookie 문제 원인을 놓친다
- SameSite, Secure, Domain, Path 중 어느 필드를 먼저 봐야 하는지 몰라 CORS와 session 복원 문제를 섞는다
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/security/cookie-failure-three-way-splitter.md
- contents/security/cookie-rejection-reason-primer.md
- contents/security/cookie-scope-mismatch-guide.md
- contents/security/fetch-credentials-vs-cookie-scope.md
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Cookie DevTools Field Checklist Primer 핵심 개념을 설명해줘
- cookie devtools checklist가 왜 필요한지 알려줘
- Cookie DevTools Field Checklist Primer 실무 설계 포인트는 뭐야?
- cookie devtools checklist에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Cookie DevTools Field Checklist Primer를 다루는 primer 문서다. cookie 디버깅 첫 1분은 "브라우저가 받았나, 저장했나, 보냈나"를 같은 cookie 이름 기준으로 `Set-Cookie` 한 줄, `Application` 한 줄, request `Cookie` 한 줄만 비교하면 된다. 검색 질의가 cookie devtools checklist, cookie field checklist, cookie compare set-cookie application request, cookie blocked reason basics처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Cookie DevTools Field Checklist Primer

> 한 줄 요약: cookie 디버깅 첫 1분은 "브라우저가 받았나, 저장했나, 보냈나"를 같은 cookie 이름 기준으로 `Set-Cookie` 한 줄, `Application` 한 줄, request `Cookie` 한 줄만 비교하면 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)
- [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)
- [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: cookie devtools checklist, cookie field checklist, cookie compare set-cookie application request, cookie blocked reason basics, cookie scope mismatch basics, cookie request header compare, cookie name domain path samesite secure, browser cookie first minute, 쿠키가 있는데도 요청에 안 감, cookie 왜 안 보내요, cookie 뭐예요 basics

## 먼저 잡을 mental model

cookie 디버깅 첫 질문은 복잡하지 않다.

1. 서버가 `Set-Cookie`를 내려보냈나
2. 브라우저가 그 cookie를 저장했나
3. 브라우저가 실패한 요청에 그 cookie를 실제로 보냈나

이 세 칸이 서로 다르다.

- `Response Headers > Set-Cookie`는 "서버가 주려 했는가"
- `Application > Cookies`는 "브라우저가 보관했는가"
- `Request Headers > Cookie`는 "그 요청에 실제로 들고 갔는가"

## DevTools 1분 체크리스트

실패한 요청 하나를 기준으로 아래 칸만 비교한다.

| DevTools 위치 | 정확히 볼 필드/컬럼 | 같은 줄에서 비교할 것 | 초보자용 해석 |
|---|---|---|---|
| `Network > login/callback 응답 > Response Headers` | `Set-Cookie` | cookie `Name`, `Domain`, `Path`, `SameSite`, `Secure`, `HttpOnly`, `Max-Age`/`Expires` | 서버가 어떤 범위와 규칙으로 cookie를 주려 했는지 본다 |
| `Network > login/callback 응답 > Issues` 또는 blocked reason | `This Set-Cookie was blocked...` 같은 reason | `Secure`, `SameSite`, invalid `Domain` 같은 키워드 | 저장 단계에서 막혔는지 먼저 본다 |
| `Application > Cookies` | `Name`, `Domain`, `Path`, `Expires/Max-Age`, `SameSite`, `Secure`, `HttpOnly` | 위 `Set-Cookie`와 같은 cookie 이름인지 | 브라우저가 실제로 어떤 row를 저장했는지 본다 |
| `Network > 실패한 요청 > Headers` | `Request URL` | `Application` row의 `Domain`/`Path`와 맞는지 | "이 URL에 붙을 자격이 있나"를 본다 |
| `Network > 실패한 요청 > Request Headers` | `Cookie` | 같은 cookie `Name`이 실제로 실렸는지 | 여기 비면 server session보다 먼저 cookie scope를 본다 |

한 줄 규칙:

- `Set-Cookie`만 있고 `Application` row가 없으면 저장 실패 가능성이 크다.
- `Application` row는 있는데 request `Cookie`가 비면 전송 범위 문제다.
- request `Cookie`까지 있으면 그다음은 서버 복원 갈래다.

## 초보자용 비교 순서

| 순서 | 비교 질문 | 막히면 다음 문서 |
|---|---|---|
| 1 | `Set-Cookie`가 아예 보이나 | 없으면 app/server가 cookie를 안 내려준 것이다. 이 문서보다 upstream flow를 다시 본다 |
| 2 | `Issues`나 blocked reason이 `Secure`/`SameSite`/`Domain`을 말하나 | [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) |
| 3 | `Application > Cookies`에 같은 `Name` row가 생겼나 | 없으면 저장 단계 문제다. [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md) -> [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) |
| 4 | 실패한 요청의 `Request URL` host/path가 그 row의 `Domain`/`Path`와 맞나 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| 5 | 실패한 요청의 request `Cookie` header에 같은 `Name`이 있나 | 없으면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), 있으면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) 또는 server/session 복원 갈래 |

## 가장 자주 보는 컬럼-대-헤더 비교

| 이 둘을 비교 | 왜 비교하나 | 어긋나면 흔한 해석 |
|---|---|---|
| `Application Domain` vs 실패 요청 `Request URL` host | subdomain handoff가 되는지 본다 | `auth.example.com`에만 저장된 host-only cookie라 `app.example.com`에 안 붙을 수 있다 |
| `Application Path` vs 실패 요청 `Request URL` path | callback 전용 cookie인지 본다 | `Path=/auth`인데 요청이 `/api/me`면 안 붙을 수 있다 |
| `Application SameSite` vs 현재 요청 문맥 | cross-site 흐름인지 본다 | external IdP, iframe, partner portal이면 `SameSite`가 막을 수 있다 |
| `Application Secure` vs 실패 요청 URL scheme | HTTPS 전용인지 본다 | redirect가 `http://...`로 꺾이면 안 붙을 수 있다 |
| response `Set-Cookie Name` vs request `Cookie` header | 같은 cookie가 살아서 갔는지 본다 | 저장은 됐어도 다음 요청에는 빠졌을 수 있다 |

## 아주 작은 예시: 로그인 성공 뒤 `/api/me`에 cookie가 안 붙는 경우

`https://auth.example.com/login` 응답은 성공인데, 바로 이어진 `https://app.example.com/api/me` 요청이 anonymous라고 하자. 초급자는 이 세 줄만 같은 cookie 이름 `SESSION`으로 나란히 본다.

| 어디를 보나 | 실제 관찰 | 바로 내리는 첫 해석 |
|---|---|---|
| `Response Headers > Set-Cookie` | `SESSION=...; Path=/auth; Secure; SameSite=Lax` | 서버는 cookie를 주긴 했다 |
| `Application > Cookies` | `SESSION` row가 저장돼 있다 | 저장 자체는 성공했다 |
| `Request Headers > Cookie` on `/api/me` | `SESSION`이 없다 | 전송 단계에서 scope가 안 맞는다 |

이 장면에서는 "세션이 서버에서 사라졌나?"보다 먼저 `Path=/auth`와 요청 경로 `/api/me`가 어긋났는지 본다. 저장은 됐는데 요청에 안 붙는 전형적인 `stored but not sent` 갈래이기 때문이다.

## 자주 헷갈리는 지점

- `Application > Cookies`에 보인다고 그 요청에 자동 전송된 것은 아니다.
- `HttpOnly`는 "JS에서 못 읽음"이지 "요청에 안 붙음"이 아니다.
- `Path` 문제는 blocked reason보다 request `Cookie` 누락으로 더 자주 보인다.
- `app.example.com`과 `api.example.com`은 same-site일 수 있어도 same-origin은 아니다.
- `credentials: "include"`는 전송 허가문일 뿐이고, `Domain`/`Path`/`SameSite`를 대신하지 않는다.

## 다음 한 걸음과 복귀 경로

| 지금 확인된 장면 | 바로 갈 문서 | 읽고 난 뒤 복귀 |
|---|---|---|
| blocked reason이 먼저 보임 | [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `Application` row는 있는데 request `Cookie`가 비어 있음 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| request `Cookie`는 있는데 브라우저는 still anonymous | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) 또는 server/session 복원 갈래 | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |

이 checklist로도 갈래가 안 서면 먼저 [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)로 돌아가서 `blocked` / `stored but not sent` / `sent but anonymous`를 다시 고른다.

## 한 줄 정리

cookie 디버깅 첫 1분은 "브라우저가 받았나, 저장했나, 보냈나"를 같은 cookie 이름 기준으로 `Set-Cookie` 한 줄, `Application` 한 줄, request `Cookie` 한 줄만 비교하면 된다.
