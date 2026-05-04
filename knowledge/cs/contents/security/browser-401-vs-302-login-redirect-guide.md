---
schema_version: 3
title: Browser 401 vs 302 Login Redirect Guide
concept_id: security/browser-401-vs-302-login-redirect-guide
canonical: false
category: security
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
aliases:
- browser 401 vs 302
- login redirect guide
- saved request bounce
- final html 200 is not api success
- 쿠키는 있는데 왜 다시 로그인
intents:
- comparison
- design
linked_paths:
- contents/security/cookie-failure-three-way-splitter.md
- contents/security/cookie-scope-mismatch-guide.md
- contents/security/fetch-credentials-vs-cookie-scope.md
- contents/spring/spring-security-filter-chain.md
- contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
forbidden_neighbors:
- contents/database/read-your-writes-session-pinning.md
confusable_with:
- network/login-redirect-hidden-jsessionid-savedrequest-primer
- security/cookie-failure-three-way-splitter
expected_queries:
- 브라우저에서 401 대신 302 /login이 보이면 뭘 봐야 해?
- fetch가 login HTML 200을 받았는데 API 성공이 아닌 이유가 뭐야?
- 쿠키는 있는데 왜 다시 로그인되는지 3단계로 어떻게 나눠?
- SavedRequest bounce랑 cookie missing을 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 학습자가 SavedRequest 흐름과 그냥 쿠키 누락을 어떻게 가리는지,
  브라우저 fetch가 login HTML 200을 받아도 왜 API 성공이 아닌지 처음
  잡는 chooser다. SavedRequest 흐름 vs 쿠키 누락, 401 대신 302, 쿠키는
  있는데 다시 로그인, login HTML 200을 받았지만 API는 실패 같은 자연어
  paraphrase가 본 문서의 분기 진단에 매핑된다.
---

# Browser `401` vs `302` Login Redirect Guide

> 한 줄 요약: 브라우저 앱에서 보이는 `302 -> /login`은 종종 raw `401`을 브라우저 UX로 감싼 `browser 401 -> 302 /login bounce`이고, `fetch` 최종 login HTML `200`은 API 성공이 아니라 redirect를 따라간 마지막 표면일 수 있으며, 초보자가 말하는 `hidden session`은 대개 cookie reference는 보이지만 서버가 auth/session을 못 복원하는 장면을 뜻한다.

**난이도: 🟢 Beginner**

관련 문서:

- `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
- `[primer bridge]` [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md)
- `[deep dive after this guide]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
- `[deep dive after this guide]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- `[return ladder]` [Spring README: Spring + Security ladder](../spring/README.md#spring-security-ladder)

retrieval-anchor-keywords: browser 401 vs 302, login redirect guide, browser login redirect, login loop beginner guide, saved request bounce, hidden jsessionid, 쿠키는 있는데 왜 다시 로그인, request cookie header empty, application cookie vs request cookie header, cookie header gate, secure cookie behind proxy, server-anonymous branch, browser session troubleshooting path, final html 200 != api success, final html 200 not api success

## Beginner-safe ladder

이 문서는 broad primer가 아니라 `follow-up primer bridge`다.
초보자용 고정 순서는 `Login Redirect, Hidden JSESSIONID, SavedRequest 입문 -> 이 guide -> Spring deep dive 1장`이고, 여기서도 `redirect / navigation memory`, `cookie-missing`, `server-anonymous` 셋 중 하나만 확정한 뒤 다음 문서로 내려간다.

| 지금 확정된 branch | 여기서 바로 가는 다음 1장 |
|---|---|
| `redirect / navigation memory` | [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `cookie-missing` | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) 또는 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `server-anonymous` | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |

## 30초 3-step 체크 카드

login loop 시작점에서 초보자가 먼저 고정할 mental model은 `redirect 기억 -> cookie 전송 -> server 복원`이다.

| step | Network 탭에서 딱 보는 칸 | 30초 질문 | 바로 내리는 분기 | safe next doc |
|---|---|---|---|---|
| 1. `redirect 기억` | `Status` + `Location` | raw `401`인가, `302 + /login`인가, `302 + 원래 URL`인가? | raw `401`이면 API auth failure 해석부터, `302 + /login`이면 browser login UX, `302 + 원래 URL`이면 `SavedRequest` 복귀 branch | `302`가 섞이면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> 이 문서 |
| 2. `cookie 전송` | 같은 실패 요청의 `Request Headers > Cookie` | login 뒤 다음 요청에 session cookie가 실제로 실렸나? | 비어 있으면 `cookie-missing` (`전송`, 기존 `cookie-not-sent`)이다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| 3. `server 복원` | 같은 요청의 `Status` + `Location` + `Cookie` 존재 여부 | cookie는 실렸는데도 raw `401` 또는 `302 -> /login`이 반복되나? | 그렇다면 `server-anonymous` (`복원`, 기존 `server-mapping-missing`) branch다 | [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md) |

짧게 외우면:

- `401/302`가 헷갈려도 request `Cookie` header가 비면 아직 browser 전송 문제다.
- request `Cookie` header가 실렸는데도 anonymous면 그때 session/BFF mapping 쪽으로 내려간다.
- `302 + 원래 URL`은 loop 원인이라기보다 `SavedRequest` 복귀 장면일 수 있다.

## 20초 트리아지 결정표

browser/session bridge 문서에서 공통으로 쓰는 mini decision matrix다. 초보자는 이 표 한 번으로 `기억 -> 전송 -> 조회`를 먼저 자른 뒤 다음 문서 하나만 고르면 된다.

| 지금 먼저 보이는 신호 | 먼저 읽는 뜻 | safe next step |
|---|---|---|
| `302 + Location: /login`, login 직후 원래 URL 복귀가 꼬임, `SavedRequest`가 의심됨 | `기억 / redirect` branch다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> 이 문서 |
| `Application > Cookies`에는 값이 있는데 같은 실패 요청의 request `Cookie` header가 비어 있음 | `전송 / cookie-missing` branch다. `cookie-not-sent`는 retrieval alias다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| request `Cookie` header는 붙어 있는데도 raw `401` 또는 `302 -> /login`이 반복됨 | `조회 / server-anonymous` branch다 | [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md) |

다음 갈래가 다시 헷갈리면 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)로 먼저 돌아가고, 더 넓은 symptom 표가 필요할 때만 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 한 칸 더 내려간다.

## 이 문서가 아닌 질문도 먼저 잘라 둔다

`browser/session` 증상처럼 보이지만 실제로는 다른 primer가 더 맞는 질문도 있다.

| 지금 던진 말 | 여기 문서가 맡는가 | 더 안전한 시작점 |
|---|---|---|
| `쿠키는 있는데 왜 다시 로그인` | 예. `redirect 기억 -> cookie 전송 -> server 복원`으로 먼저 자른다 | 이 문서의 `30초 3-step 체크 카드` |
| `토큰 valid인데 왜 403` | 아니오. cookie/session continuity보다 authz gate 질문이다 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) -> [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md) |
| `권한을 방금 줬는데도 403` | 보통 아니오. browser redirect보다 freshness/stale deny 질문일 가능성이 크다 | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |

한 줄 기준:

- `다시 로그인된다`, `302 -> /login`, `cookie는 보이는데 anonymous`면 이 문서다.
- `token valid`, `scope 있음`, `권한 방금 부여` 같은 말이 앞에 오면 authz primer 쪽이 먼저다.

## Tiny DevTools evidence card

redirect clue와 cookie clue가 한 화면에서 같이 보일 때는 아래 3칸만 이어서 읽으면 된다.

| `Location` | next request URL | request `Cookie` header | 초보자용 뜻 | 바로 갈 primer |
|---|---|---|---|---|
| `/login` | `/login` | 비어 있거나 아직 확인 전 | login page로 보내는 redirect clue가 먼저 보인다. `SavedRequest`와 page redirect 흐름부터 본다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| 원래 보려던 URL (`/orders/42`) | 원래 URL로 다시 감 | 비어 있음 | 복귀 redirect 자체보다 cookie 전송이 먼저 끊겼다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| `/login` 또는 원래 URL | 다음 요청이 보호 URL/API로 감 | 있음 | browser는 cookie를 보냈다. 그다음은 server/session 복원 clue다 | [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md) -> [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md) |

이 카드까지 본 뒤에도 branch가 흔들리면 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)로 돌아가고, 증상 문장을 다시 고르려면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀한다.

## Spring deep dive 전에 먼저 고정할 safe next doc

이 문서는 beginner ladder의 `follow-up`이다.
그래서 `Spring deep dive 전에 safe next doc이 무엇인가`를 묻는 질의는 대부분 여기서 한 번 멈춘 뒤 branch를 고르는 쪽이 맞다.

| 지금 질문 | 여기서 고정할 safe next doc | 그다음에만 여는 Spring deep dive |
|---|---|---|
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | 이 문서에서 `redirect / navigation memory`로 확정 | [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `cookie 있는데 다시 로그인`, `hidden session`, `next request anonymous after login` | 이 문서의 `Application vs Network 15초 미니 체크`로 `cookie-missing`(기존 `cookie-not-sent`) vs `server-anonymous`(기존 `server-mapping-missing`)를 확정 | request `Cookie` header가 비면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), 실리면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |
| `API가 login HTML을 받음`, `browser 401 -> 302 /login bounce` | 이 문서에서 page redirect와 API contract를 먼저 분리 | redirect memory면 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md), persistence면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |

## 이 문서 다음에 보면 좋은 문서

- `cookie 있는데 다시 로그인`, `saved request bounce`, `login loop first step`, `next request anonymous after login`, `hidden session`, `browser 401 -> 302 /login bounce`, `browser page redirect vs api 401`가 같이 보이면 beginner entry route는 같다. 먼저 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)으로 alias를 맞춘 뒤 이 문서로 돌아오고, `safe next step`은 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 primer bridge 하나를 고르는 것이다.
- raw `401`, `403`, concealment `404` 의미 자체가 헷갈리면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)로 먼저 내려가 상태 코드 의미를 고정하는 편이 안전하다.
- `Application > Cookies`에는 cookie가 보이는데 다음 request `Cookie` header가 비어 있거나, `auth`/`app`/`api` subdomain 이동 뒤 login loop가 나면 먼저 이 문서의 [Application vs Network 15초 미니 체크](#application-vs-network-15초-미니-체크)로 내려가 `stored` vs `sent`를 고정하고, 그다음 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 `Domain`, `Path`, `SameSite`, host-only cookie 문제를 분리한다.

## proxy/origin 갈래 다음 문서

- login 응답 직후 `Location`이 `http://...`로 바뀌거나, `localhost`에서는 되는데 ALB/Nginx/ingress 뒤에서만 `Secure` cookie가 빠지면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)에서 TLS termination, `X-Forwarded-Proto`, app의 proxy header 신뢰를 먼저 본다.
- login 응답 직후 `Location`이나 OAuth `redirect_uri`가 `app-internal`, `localhost`, staging host처럼 wrong origin으로 바뀌면 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)에서 `X-Forwarded-Host`, host preservation, absolute URL builder를 먼저 본다.
- cross-origin `fetch`에서 `credentials: "include"`와 CORS credential 헤더, cookie scope가 한꺼번에 섞이면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)에서 request 전송과 response 읽기를 먼저 나눠 본다.

## deep dive 전 정리 문서

- `cookie`, `session`, `JWT`가 아직 한 덩어리처럼 보이면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) 순으로 올라가 상태 저장 위치부터 다시 맞춘다.
- `SavedRequest`, `saved request bounce`, `원래 URL 복귀`가 더 깊게 궁금하면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)을 한 번 거친 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 redirect/navigation memory branch를 다시 고른 다음 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)로 이어 간다.

## server 복원 deep dive 전

- `hidden session`, `cookie exists but session missing`이 더 궁금하면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)을 한 번 거친 뒤 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 server session/BFF mapping branch를 다시 고른 다음 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) 순으로 좁힌다.
- route를 다시 고르려면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가고, beginner entry route 전체를 다시 타려면 [Network README: Browser Session Spring Auth](../network/README.md#network-bridge-browser-session-auth)로 돌아간다.

---

## 먼저 세 표현을 분리한다

| 자주 하는 말 | 먼저 이렇게 읽는다 | 고정 next-step label | 안전한 다음 문서 |
|---|---|---|
| `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음`, `browser page redirect vs api 401` | raw `401` auth failure가 browser redirect UX로 감싸진 장면일 수 있다 | `browser redirect / API contract` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login` | browser에는 cookie/session reference가 보이지만 서버는 그 값으로 auth/session을 아직 또는 더 이상 못 찾는 장면일 수 있다 | `server persistence / session mapping` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | 로그인 상태가 아니라 로그인 전 원래 URL을 기억하는 navigation memory다 | `redirect / navigation memory` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |

## 프라이머 핸드오프 큐: `기억/전송/복원`

앞 문서([Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md))에서 온 독자는 이 3칸만 유지하면 된다.

| cue | 지금 이 문서에서 하는 일 | 다음 갈래 |
|---|---|---|
| `기억` | `SavedRequest`/redirect memory가 보여 주는 현상과 raw `401` 의미를 분리한다 | redirect memory 자체를 깊게 보면 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `전송` | `Application` cookie와 request `Cookie` header를 구분해 cookie 전송 실패를 먼저 가른다 | header가 비면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), proxy면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `복원` | cookie는 왔는데 왜 anonymous인지(server session/BFF mapping) 경계를 분리한다 | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |

`SavedRequest`가 보인다고 바로 Spring `RequestCache` 설정부터 볼 필요는 없다.
먼저 "원래 URL을 기억한 문제"인지, "로그인 뒤 인증 상태가 유지되지 않는 문제"인지 나눈다.

## 로그인 loop 신호별 분기

| 지금 보이는 증상 | 더 가까운 축 / split label | 첫 확인 | 안전한 다음 문서 |
|---|---|---|---|
| 로그인 후 원래 URL로 한 번 돌아가고 `200`으로 끝남 | 정상 redirect memory, `SavedRequest` (`기억`) | `POST /login` 다음 `Location`과 최종 status | 더 깊게 필요할 때만 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| 로그인 후 원래 URL로 갔다가 곧바로 다시 `/login` | `SavedRequest` 뒤에 `cookie-missing` 또는 `server-anonymous`로 갈라질 수 있음 | 원래 URL 재요청에 `Cookie` header가 실렸는지 | cookie가 비면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), cookie가 실리면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |
| `Application > Cookies`에는 보이지만 request `Cookie` header가 비어 있음 | `cookie-missing` (`전송`, `cookie-not-sent` alias) | `Domain`, `Path`, `SameSite`, `Secure`, subdomain 이동 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| `Application`에 `auth.example.com`의 session은 보이는데 `https://app.example.com/api/me` 요청 `Cookie` header는 비어 있음 | `cookie-missing` (`전송`, sibling subdomain scope mismatch) | host-only(`Domain` 없음)인지, `Domain=example.com`이 필요한 구조인지 | 먼저 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 `stored` vs `sent`를 확정하고, 그다음에만 `server-anonymous` 갈래로 내려간다 |

## 로그인 loop 신호별 분기 (계속 2)

| login 직후 redirect `Location`이나 다음 요청 URL이 `http://...`로 내려감 | `cookie-missing` 쪽으로 먼저 보는 proxy/`Secure` cookie branch | `X-Forwarded-Proto`, TLS termination, `Secure` cookie 재전송 여부 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| login 직후 redirect `Location`이나 OAuth `redirect_uri`의 host가 wrong origin으로 내려감 | redirect branch이지만 `SavedRequest`보다 absolute redirect origin 계산을 먼저 확인 | raw `Host`, `X-Forwarded-Host`, host preservation, public base URL | [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md) |
| request `Cookie` header는 있는데 서버가 anonymous로 봄 | `server-anonymous` (`복원`, `server-mapping-missing` alias) | session id lookup, session store, BFF token/session mapping | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 보통 뜻하는 것 | 먼저 확인할 것 |
|---|---|---|
| 보호된 HTML 페이지에 들어가자마자 `302 -> /login` | 브라우저용 로그인 UX일 수 있다. 실질적으로는 "지금 인증 안 됨"에 가깝다 | page 요청인지, API 요청인지 |
| 로그인 성공 후 원래 URL로 다시 `302` | `SavedRequest`가 원래 URL로 복귀시키는 정상 흐름일 수 있다 | 로그인 직후 다음 요청이 `200`으로 끝나는지 |
| cookie가 있는데도 다시 `302 -> /login` | cookie는 남았지만 서버 session/BFF mapping이 사라졌을 수 있다 | cookie가 실제로 전송됐는지, 서버가 그 값을 찾는지 |
| `fetch('/api/me')`가 JSON `401` 대신 login HTML을 받음 | 브라우저 redirect 정책이 API 계약에 섞였을 가능성이 크다 | 응답 `Location`, 최종 `Content-Type`, filter chain 분리 |

초보자에게 가장 중요한 한 줄은 이것이다.

- `401`은 `인증이 안 됨`이라는 HTTP 의미다.
- `302`는 `다른 URL로 가라`는 브라우저 navigation 지시다.
- 브라우저 앱은 종종 `401` 상황을 바로 보여 주지 않고 `302 /login`으로 감싼다.

즉 `302`는 원인 그 자체라기보다, 인증 실패를 사용자 화면 흐름으로 바꿔 보여 주는 껍데기일 때가 많다.

### Network / `Location` 미니 표

초보자는 한 화면에서 `status` 숫자와 `Location` header를 같이 보면 훨씬 덜 헷갈린다.

| Network에서 먼저 보이는 것 | `Location` header | 초보자용 해석 |
|---|---|---|
| raw `401 Unauthorized` | 보통 없음 | 서버가 "지금 인증 안 됨"을 그대로 말했다. API 계약에 더 가깝다 |
| `302 Found` | `/login` 또는 login URL | 서버가 인증 안 됨을 브라우저 이동 UX로 감쌌다. page flow에서 흔하다 |
| `302 Found` 뒤 최종 응답이 login HTML `200` | 첫 `302`에 있음 | API 성공이 아니라, API 요청이 redirect를 따라간 마지막 HTML 표면일 수 있다 |
| `302 Found` | 원래 보려던 URL(`/orders/42` 등) | login 뒤 복귀 redirect일 수 있다. `SavedRequest` 흐름을 같이 본다 |

짧게 외우면 이렇다.

- raw `401`이면 먼저 "서버가 auth failure를 직접 말했구나"라고 읽는다.
- `302 + Location: /login`이면 먼저 "브라우저 이동 UX가 섞였구나"라고 읽는다.
- `302 + Location: /원래URL`이면 먼저 "로그인 후 복귀 단계구나"라고 읽는다.

### Application vs Network 15초 미니 체크

## 먼저 10초 판별표 (계속 2)

초보자 handoff line 하나로 외우면 된다. `Application`에는 cookie가 보이는데 같은 실패 요청의 request `Cookie` header가 비면, 여기서 일단 멈추고 `cookie-header gate`를 통과시킨 뒤에만 `SavedRequest`나 server session 쪽으로 내려간다.

초보자 오진은 대개 `Application > Cookies`에 값이 보이는 순간 "cookie는 정상"이라고 결론내리면서 시작한다. 이 문서에서는 `저장됨`과 `전송됨`과 `서버가 복원함`을 따로 본다.

| 3단계 | DevTools에서 보는 곳 | 15초 질문 | 바로 읽는 뜻 |
|---|---|---|---|
| 1. 저장 | `Application > Cookies` | session cookie가 브라우저에 저장돼 있나? | 안 보이면 `Set-Cookie`가 막혔거나 저장 전에 실패했다 |
| 2. 전송 | 같은 실패 요청의 `Network > Request Headers > Cookie` | 방금 저장된 cookie가 이 요청에 실제로 실렸나? | 비어 있으면 `cookie-missing`이다. scope/proxy 쪽을 먼저 본다 |
| 3. 해석 | 같은 요청의 `status` + `Location` | cookie를 보냈는데도 raw `401` 또는 `302 -> /login`인가? | 이때부터는 `server-anonymous` 가능성이 커진다 |

짧게 외우면:

- `Application`은 "브라우저가 저장했는가"만 보여 준다.
- `Network`의 request `Cookie` header는 "이번 요청에 정말 실렸는가"를 보여 준다.
- `status`와 `Location`은 "서버가 그 cookie로 로그인 상태를 복원했는가"를 보여 주는 힌트다.

### 3단계 미니 체크 예시

## 먼저 10초 판별표 (계속 3)

| 보이는 장면 | 초보자가 내리기 쉬운 오진 | 더 안전한 해석 | 다음 문서 |
|---|---|---|---|
| `Application`에는 `JSESSIONID`가 있음, request `Cookie` header는 비어 있음, 응답은 `302 -> /login` | session store가 죽었다 | 아직 서버까지 cookie가 안 갔다. 먼저 전송 실패다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| `Application`에도 있고 request `Cookie` header에도 있음, 응답은 계속 `302 -> /login` | 브라우저가 cookie를 숨긴다 | cookie는 갔다. 서버가 session/principal을 못 복원할 수 있다 | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |
| `Application`에는 있고 login 직후 `Location`이 `http://...`로 꺾인 뒤 다음 요청 `Cookie` header가 비어 있음 | SameSite 하나만 고치면 된다 | 먼저 wrong-scheme/proxy drift를 의심해야 한다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |

## 초급자 FAQ: 왜 브라우저는 `302`, API는 raw `401`로 보이나

먼저 mental model을 한 줄로 잡으면 쉽다.

- page 요청은 "로그인 화면으로 보내기" UX를 자주 쓴다.
- API 요청은 "인증 안 됨" 사실을 raw `401`로 바로 알려 주는 계약을 자주 쓴다.

| 질문 | 짧은 답 |
|---|---|
| 왜 브라우저에서는 `401` 대신 `/login`으로 이동하나요? | 브라우저 page flow는 사용자를 다음 화면으로 보내는 UX가 필요해서, 서버가 인증 실패를 `302 -> /login`으로 감싸는 경우가 많다. |
| 그런데 API 도구나 `curl`에서는 왜 raw `401`이 보이나요? | API 클라이언트는 HTML login page보다 상태 코드와 JSON error를 기대하므로, redirect 없이 raw `401` 계약을 그대로 받는 경우가 많다. |
| 그러면 `302`는 에러가 아니라 정상인가요? | 보호 페이지를 처음 열었을 때의 `302 -> /login`은 정상일 수 있다. 다만 로그인 후에도 계속 반복되면 cookie 전송, session 복원, redirect 설정을 의심해야 한다. |
| `fetch('/api/me')`가 `401` JSON 대신 login HTML을 받는 건 왜 이상한가요? | API route에 browser용 redirect 정책이 섞였다는 신호다. `fetch`는 보통 data 계약을 기대하는데 login page HTML이 와 버리면 프론트엔드가 상태를 제대로 해석하지 못한다. |
| 초보자는 DevTools에서 무엇부터 보면 되나요? | `status`와 `Location`을 같이 본다. raw `401`이면 API 성격, `302 + /login`이면 browser login UX, `302 + 원래 URL`이면 login 후 복귀 단계로 먼저 읽는다. |

자주 하는 오해는 이것이다.

- `302`를 보면 곧바로 "권한 문제"라고 단정하기 쉽지만, 실제로는 login UX redirect일 수 있다.
- `JSESSIONID`가 보인다고 곧바로 로그인 성공은 아니다. 로그인 전 임시 session이나 request memory일 수도 있다.
- 최종 화면이 login HTML `200`이어도, 그 앞단에는 `302 -> /login`이 있었을 수 있다.
- 즉 final HTML `200`은 API 성공 증거가 아니라 redirect chain의 마지막 표면일 수 있다.

---

## 왜 브라우저는 raw `401` 대신 `302`를 자주 보나

브라우저 페이지 요청은 보통 "보호 페이지에 갔더니 로그인 화면으로 이동"하는 UX를 기대한다.

그래서 서버나 framework는 자주 이렇게 동작한다.

1. 현재 요청이 인증되지 않았다고 판단한다.
2. raw `401`을 그대로 보여 주는 대신 login page로 `302` redirect한다.
3. 로그인 성공 후 원래 가려던 URL로 다시 보낸다.

반면 API 클라이언트나 모바일 SDK는 보통 redirect보다 raw `401` JSON을 기대한다.

즉 같은 "인증 안 됨"이라도 바깥 표현이 달라질 수 있다.

- browser page flow: `302 -> /login`
- API flow: raw `401`

핵심은 `상태 코드 숫자`만 보지 말고, **누가 호출했고 어떤 UX를 기대하는 요청인지**를 먼저 보는 것이다.

---

## `302`가 정상인 경우와 문제인 경우

### 1. 정상인 경우: 보호 페이지로 들어가서 login page로 이동

브라우저 웹앱에서 아래 흐름은 이상하지 않다.

```http
GET /orders/42
< 302 Found
< Location: /login
< Set-Cookie: JSESSIONID=abc123; HttpOnly; Secure
```

이 장면은 대개 "아직 인증 안 됨"을 브라우저 친화적으로 표현한 것이다.

- 사용자는 login page로 간다
- framework는 원래 URL을 어딘가에 기억할 수 있다
- 로그인 후 다시 `/orders/42`로 보내려 한다

여기서 중요한 점은 `JSESSIONID`가 생겼다고 곧바로 "로그인 성공"이 아니라는 점이다.
이 cookie는 로그인 전 navigation memory나 CSRF/session 관리를 위해 먼저 만들어질 수도 있다.

### 2. 정상인 경우: login 뒤 원래 URL로 복귀

```http
POST /login
Cookie: JSESSIONID=abc123
< 302 Found
< Location: /orders/42
```

이 흐름은 `SavedRequest`가 "아까 가려던 URL이 `/orders/42`였지"를 기억했다가 복귀시키는 장면일 수 있다.

즉 `SavedRequest`는 보통:

- 로그인 상태 자체를 저장하는 장치가 아니라
- 원래 가려던 URL을 기억하는 navigation memory다

### 3. 문제인 경우: API가 login HTML을 받아 버림

```http
GET /api/me
< 302 Found
< Location: /login
...
GET /login
< 200 OK
< Content-Type: text/html
```

프론트엔드 `fetch`나 API client는 보통 JSON `401`을 기대한다.
그런데 browser chain이 API route까지 덮으면 redirect를 따라간 뒤 login HTML을 받게 된다.

이 경우 문제의 본질은 대개:

- "권한이 왜 없지?"보다
- "browser용 redirect 정책이 API 계약에 섞였다"에 가깝다
- final HTML `200`을 성공으로 읽지 말고, 원래 API 계약이 raw `401`이어야 했는지부터 다시 본다

---

## `SavedRequest` 예시로 보는 login loop

`SavedRequest`를 초보자 눈높이로 보면 아주 단순하다.

- "로그인 전 원래 가려던 URL 메모"

브라우저 login loop는 자주 아래 순서로 보인다.

1. 사용자가 `/admin/report`에 간다.
2. 서버가 인증되지 않았다고 판단하고 `302 -> /login`을 보낸다.
3. 동시에 "원래 요청은 `/admin/report`"였다는 메모를 남긴다.
4. 사용자가 로그인한다.
5. 서버가 메모를 보고 다시 `/admin/report`로 `302` 보낸다.
6. 그런데 다음 요청에서도 인증이 유지되지 않으면 또 `302 -> /login`으로 돌아간다.

즉 loop의 원인은 `SavedRequest` 자체보다 보통 그 뒤쪽이다.

- session이 저장되지 않았다
- session cookie가 안 실렸다
- 다른 domain/path/subdomain으로 가며 cookie가 빠졌다
- 서버 session store에서 해당 session id를 찾지 못했다

`SavedRequest`는 loop를 눈에 보이게 만들 뿐, 근본 원인은 로그인 상태 유지 실패인 경우가 많다.

---

## session cookie 예시로 보는 "cookie는 있는데 왜 또 로그인하지?"

초보자가 가장 자주 헷갈리는 문장은 이것이다.

`브라우저 개발자도구에 cookie가 있는데 왜 다시 /login으로 가지?`

핵심은 cookie가 "살아 있는 인증 상태 그 자체"가 아니라 **서버가 해석해야 하는 손잡이(reference)** 일 수 있다는 점이다.

예를 들어:

```http
GET /orders/42
Cookie: JSESSIONID=abc123
< 302 Found
< Location: /login
```

브라우저 입장에서는 cookie를 잘 보냈다.
하지만 서버는 아래 이유로 여전히 익명처럼 볼 수 있다.

- `abc123` session이 이미 만료됐다
- session store 재시작/장애로 매핑이 사라졌다
- cookie `Path`/`Domain`/`SameSite`가 기대와 달라 실제 요청에는 안 실렸다
- BFF라면 cookie는 왔지만 서버-side token/session mapping이 사라졌다

그래서 초보자용 규칙은 이렇다.

- `cookie exists` != `authenticated`
- `saved request exists` != `session is healthy`

초보자가 말하는 `hidden session`은 대개 위 장면처럼 "cookie reference는 보이는데 서버는 auth/session 상태를 못 복원한다"를 가리킨다.

둘 다 "주변 단서"일 뿐, 실제 인증 성립은 서버가 principal/session mapping을 복원할 수 있을 때만 된다.

---

## 브라우저 page 요청과 API 요청을 분리해서 봐야 하는 이유

같은 `/login` redirect라도 page 요청과 API 요청은 기대 계약이 다르다.

| 요청 종류 | 기대 계약 | 흔한 실패 모습 |
|---|---|---|
| 브라우저 page navigation | `302 -> /login` 후 로그인 화면 이동 | login loop, 원래 URL 복귀 실패 |
| XHR / `fetch` / REST API | raw `401` 또는 `403` JSON | login HTML 수신, redirect 따라가다 의미 상실 |

그래서 `401 vs 302`를 볼 때는 먼저 이 질문을 던진다.

1. 이 요청은 화면 이동용인가, API용인가?
2. 지금 cookie/session reference가 실제로 서버에서 해석되는가?
3. login 후 원래 URL 복귀 메모인 `SavedRequest`가 끼어 있는가?

이 세 질문이 분리되면 `302`, login loop, hidden session mismatch가 한 덩어리로 보이지 않는다.

---

## 실전 체크리스트

1. 네트워크 탭에서 첫 응답이 raw `401`인지, `302 Location: /login`인지 본다.
2. 그 요청이 page navigation인지 `fetch`/API인지 구분한다.
3. login 전후로 cookie 값이 생기거나 바뀌는지, login 직후 redirect `Location`이 `https://...`인지 `http://...`인지 같이 본다.
4. login 성공 후 원래 URL로 돌아간다면 `SavedRequest` 흐름을 의심한다.
5. request `Cookie` header가 비면 cookie scope 또는 proxy `Secure` cookie 갈래로 먼저 나눈다.
6. request `Cookie` header가 실리는데도 다시 `/login`이면 서버 session/BFF mapping lookup을 의심한다.
7. API가 HTML login page를 받으면 `final HTML 200 != API success`를 먼저 적고, browser용 redirect 정책이 API 체인에 섞였는지 본다.

이 체크리스트만 익혀도 초보자가 `401 문제`, `302 UX`, `session persistence 문제`를 서로 다른 축으로 분리하기 훨씬 쉬워진다.

---

## 다음 단계

| 지금 확인한 첫 관찰 | 다음 한 걸음 |
|---|---|
| Spring deep dive로 내려가기 전에 route를 다시 고르고 싶다 | [Spring README: Spring + Security ladder](../spring/README.md#spring-security-ladder) |
| 로그인 후 원래 URL 복귀나 `SavedRequest` 우선순위를 framework 관점에서 더 보고 싶다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 redirect/navigation memory branch를 다시 고른 뒤 [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| request `Cookie` header가 비어 있고 `Domain`/`Path`/`SameSite`/subdomain 이동이 먼저 의심된다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| login 직후 redirect `Location`이 `http://...`로 내려가거나 proxy/LB 뒤에서만 `Secure` cookie가 빠진다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| cross-origin `fetch`와 `credentials: "include"`, CORS credential 헤더가 한 번에 섞였다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |
| request `Cookie` header는 실리는데 서버가 계속 anonymous로 본다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 server session/BFF mapping branch를 다시 고른 뒤 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |

## 다음 단계 (계속 2)

| route를 다시 고르고 싶다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

Spring deep dive handoff를 한 줄로 고정하면 초보자가 덜 흔들린다.

- `원래 URL 복귀가 먼저 헷갈리면` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)로 간다.
- `cookie는 실리는데 다음 요청이 익명이면` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)로 간다.
- `둘 중 어디로 갈지 다시 헷갈리면` [Spring README: Spring + Security ladder](../spring/README.md#spring-security-ladder)와 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아온다.

이 문서는 beginner용 symptom splitter다.
즉 "redirect/navigation memory 쪽인가", "cookie scope 쪽인가", "proxy `Secure` cookie 쪽인가", "server session/BFF mapping 쪽인가"를 가르는 데까지만 쓰고, 다음 갈래는 위 표로 내려가는 편이 가장 안전하다.

---

## 꼬리질문

> Q: `302 -> /login`이면 항상 문제인가요?
> 의도: browser UX redirect와 실제 장애를 구분하는지 확인
> 핵심: 보호된 page 요청에서는 정상일 수 있다. API라면 계약 불일치일 가능성이 크다.

> Q: `SavedRequest`는 로그인 상태를 저장하나요?
> 의도: navigation memory와 authentication state를 분리하는지 확인
> 핵심: 보통 아니다. 원래 가려던 URL을 기억하는 장치에 가깝다.

> Q: cookie가 보이면 로그인된 것 아닌가요?
> 의도: cookie handle과 서버-side session 해석을 구분하는지 확인
> 핵심: 아니다. cookie는 reference일 뿐이고, 서버가 그 값을 해석하지 못하면 다시 익명처럼 보일 수 있다.

> Q: 왜 브라우저는 `401` 대신 login HTML을 보기도 하나요?
> 의도: browser redirect 체인과 API 계약 차이를 이해하는지 확인
> 핵심: framework가 인증 실패를 브라우저 navigation UX로 감싸면서 redirect를 따라간 결과일 수 있다.

## 한 줄 정리

브라우저에서 보이는 `302 -> /login`은 종종 raw `401`의 browser UX 버전이고, final login HTML `200`은 API 성공이 아니라 redirect chain의 마지막 표면일 수 있으며, `SavedRequest`는 원래 URL 메모, session cookie는 서버가 해석해야 하는 reference라는 점을 분리하면 login loop를 훨씬 빨리 읽을 수 있다.
