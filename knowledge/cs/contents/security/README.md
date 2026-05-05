# Security (보안)

**난이도: 🟢 Beginner**

> 한 줄 요약: 인증·인가·세션 증상을 beginner-safe primer에서 분기한 뒤 필요한 deep dive로만 내려가게 돕는 security 카테고리 README다.

> 인증, 인가, 세션, OAuth/OIDC, browser/BFF 경계부터 시작하고, JWT/JWKS 장애나 incident 대응은 follow-up으로만 내려가게 자르는 카테고리

관련 문서:

- [기본 primer: auth/session/OAuth 첫 분기](#기본-primer)
- [Browser / Session Beginner Ladder: `401`/`403`/login loop 입구](#browser--session-beginner-ladder)
- [증상별 바로 가기: cookie/CORS/403 shortcut](#증상별-바로-가기)
- [추천 학습 흐름 (category-local survey): primer 다음 읽기 순서](#추천-학습-흐름-category-local-survey)
- [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [Beginner Guide to Auth Failure Responses: 401 / 403 / 404](./auth-failure-response-401-403-404.md)
- [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- [백엔드 주니어를 위한 웹 보안 스타터 팩](./web-security-starter-pack-backend-juniors.md)
- [Network README: redirect/cookie/session에서 다시 자르기](../network/README.md#network-primer-되돌아가기)
- [CS 루트 README: 카테고리 전체 Quick Routes](../../README.md#quick-routes)

retrieval-anchor-keywords: security readme, security category navigator, auth troubleshooting, browser session troubleshooting path, login loop primer, cross-origin fetch cookie confusion, subdomain cookie scope confusion, why 403 basics, 처음 배우는데 auth basics, security 뭐부터 읽지, security 처음 헷갈려요, what is security basics, auth session cookie jwt 뭐부터, jwt 쿠키 세션 헷갈려요, 로그인 됐는데 왜 403 보안

> 처음 읽는다면 `인증·인가·세션 기초 흐름` / `세션·쿠키·JWT 기초` / `백엔드 주니어를 위한 웹 보안 스타터 팩` 셋 중 하나만 먼저 고르면 충분하다. `JWKS outage`, `runbook`, `incident`, `recovery`, `observability`가 제목에 보이면 beginner 첫 클릭이 아니라 follow-up shelf다.

## 먼저 질문 한 줄로 자르기

이 카테고리에서 처음 막히는 질문은 보통 아래 네 갈래다. 용어를 다 읽기 전에 자기 질문을 어느 칸에 놓을지만 정하면 첫 클릭 실수가 줄어든다.

| 지금 머릿속 문장 | 먼저 볼 문서 | 여기서 아직 미뤄도 되는 것 |
|---|---|---|
| `로그인됐는데 왜 403이지?` | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | JWT/JWKS outage, authority mapping deep dive |
| `쿠키, 세션, JWT가 아직 같은 말처럼 들려요` | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | duplicate cookie, proxy, migration cleanup |
| `인증, 인가, 세션이 한 흐름으로 안 잡혀요` | [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md) | graph cache, revocation at scale |
| `웹 보안 전체를 어디서부터 공부해야 할지 모르겠어요` | [백엔드 주니어를 위한 웹 보안 스타터 팩](./web-security-starter-pack-backend-juniors.md) | incident playbook, observability catalog |

한 줄 기준: `왜 403`이면 auth failure guide, `왜 로그인 유지`면 session/cookie primer, `무슨 순서인지 모르겠다`면 auth/session foundations, `웹 보안 큰 그림`이면 starter pack으로 간다.

## 5초 시작

이 README는 끝까지 정독하는 문서보다 "첫 클릭을 틀리지 않게 고르는 라우터"에 가깝다. 처음이면 아래 5개 중 하나만 먼저 고르면 된다.

| 지금 내 질문 | first click | 바로 다음 한 칸 | category 밖으로 나가는 안전한 bridge |
|---|---|---|---|
| `인증`, `인가`, `세션`이 한 번에 헷갈린다 | [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md) | [인증과 인가의 차이](./authentication-vs-authorization.md) | [Network README: redirect/cookie/session에서 다시 자르기](../network/README.md#network-primer-되돌아가기) |
| `쿠키`, `세션`, `JWT` 차이부터 모르겠다 | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) | [Network README: redirect/cookie/session에서 다시 자르기](../network/README.md#network-primer-되돌아가기) |
| `웹 보안을 뭘 먼저 공부하지?` | [백엔드 주니어를 위한 웹 보안 스타터 팩](./web-security-starter-pack-backend-juniors.md) | [XSS와 CSRF 기초](./xss-csrf-basics.md) | [CS 루트 README: 카테고리 전체 Quick Routes](../../README.md#quick-routes) |
| `로그인됐는데 왜 403이지?` | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md) | [Spring README: `401`/`403` 이후 filter chain과 MVC 경계로 넘기기](../spring/README.md#spring-security-ladder) |
| `쿠키는 있는데 왜 다시 로그인하지?`, `API가 login HTML을 받아요` | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) | [System Design README](../system-design/README.md) |

## beginner scope guard

`runbook`, `playbook`, `recovery`, `outage`, `observability`가 먼저 보이면 beginner primer가 아니라 운영 follow-up shelf일 가능성이 높다. 그 경우에는 아래 [운영 / Incident catalog](#운영--incident-catalog)로 바로 내려가고, 아니라면 이 README에서는 `기본 primer`, `증상별 바로 가기`, `Browser / Session Beginner Ladder`까지만 먼저 쓰는 편이 안전하다.

## Beginner first split: 이 README에서 어디로 첫 클릭할까

security 카테고리에서 처음 막히는 질문은 보통 아래 네 갈래 중 하나다. 첫 클릭을 잘못 고르면 `403`, cookie, CORS, XSS를 한 덩어리로 읽게 된다.

| 지금 머릿속 문장 | first click | 왜 여기서 시작하나 |
|---|---|---|
| `로그인됐는데 왜 403이지?` | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | authn 성공 뒤 authz 실패인지부터 갈라야 한다 |
| `쿠키, 세션, JWT가 아직 같은 말처럼 들려요` | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | 전달 수단과 로그인 상태 복원 방식을 먼저 분리해야 한다 |
| `인증, 인가, 세션이 한 흐름으로 안 잡혀요` | [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md) | principal, session, permission check 순서를 한 장으로 붙여 준다 |
| `웹 보안 전체를 어디서부터 공부해야 할지 모르겠어요` | [백엔드 주니어를 위한 웹 보안 스타터 팩](./web-security-starter-pack-backend-juniors.md) | auth/session 바깥의 HTTPS, XSS, CSRF, CORS, secret 축을 먼저 나눈다 |

한 줄 기준: `왜 403`이면 auth failure guide, `왜 로그인 유지`면 session/cookie primer, `무슨 순서인지 모르겠다`면 auth/session foundations, `웹 보안 큰 그림`이면 starter pack으로 간다.

security category-local 목차는 이렇게만 잡으면 된다.

- beginner 입구: [`beginner entrypoints`](#security-beginner-entrypoints), [`기본 primer`](#기본-primer), [`browser / session beginner ladder`](#browser--session-beginner-ladder)
- 증상 라우팅: [`증상별 바로 가기`](#증상별-바로-가기), [`browser / session troubleshooting path`](#browser--session-troubleshooting-path)
- 운영 심화: `incident`, `recovery`, `trust`, `hardware`, `tenant`, `response contract` catalog
- cross-category handoff: [`network README`](../network/README.md#network-primer-되돌아가기), [`spring README`](../spring/README.md#spring-security-ladder), [`cs 루트 quick routes`](../../README.md#quick-routes)

## related-doc handoff

관련 문서:
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- [Network README: redirect, cookie, session부터 다시 고르기](../network/README.md#network-primer-되돌아가기)
- [Spring README: `401`/`403` 이후 filter chain과 MVC 경계로 넘기기](../spring/README.md#spring-security-ladder)
- [System Design README](../system-design/README.md)
- [CS 루트 README: 카테고리 전체 네비게이터](../../README.md#quick-routes)

<a id="security-beginner-entrypoints"></a>

## Beginner Entrypoints (`primer` / `survey` / incident split)

이 README는 security category `navigator`다. `기본 primer`는 auth / session / OAuth 기초 축을 맞추는 입문 구간이고, `추천 학습 흐름`은 category-local `survey`, `... deep dive catalog` heading은 theme bucket을 고르는 `catalog`, 링크된 개별 `.md`는 실제 `deep dive`다. 즉시 대응이 필요한 운영 상황이 아니라면 incident-heavy 문서까지 한 번에 내려가지 않는 편이 beginner scope에 맞다.
여기서 `[primer]`는 용어와 mental model을 처음 여는 first-step 문서이고, `[primer bridge]`는 primer 하나를 읽은 뒤 symptom을 spring / authz / system-design handoff로 넘기는 2단계 문서다.
heading에 `deep dive catalog`, `Incident / Recovery`, `Trust`, `Cutover`가 보이면 beginner 첫 클릭이 아니라 follow-up shelf로 읽는다. security에서는 `기본 primer` / `Beginner Primer Bridge (첫 분기)` / `증상별 바로 가기`가 entry shelf이고, incident-heavy heading은 운영/복구가 급할 때만 올린다.

처음 보는 학습자라면 이 README를 처음부터 끝까지 읽기보다 아래 4갈래 중 하나만 먼저 고르는 편이 안전하다.

| 질문 모양 | first click | 바로 이어서 볼 다음 한 칸 |
|---|---|---|
| `인증`, `인가`, `세션`이 한 번에 헷갈린다 | [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md) | [인증과 인가의 차이](./authentication-vs-authorization.md) |
| `쿠키`, `세션`, `JWT` 차이부터 모르겠다 | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) |
| `웹 보안` 큰 그림이 먼저 필요하다 | [백엔드 주니어를 위한 웹 보안 스타터 팩](./web-security-starter-pack-backend-juniors.md) | [XSS와 CSRF 기초](./xss-csrf-basics.md) |
| 이미 증상이 `왜 403`, `왜 다시 로그인`처럼 보인다 | [증상별 바로 가기](#증상별-바로-가기) | [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) 또는 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |

## beginner question map

| 내가 지금 묻는 말 | 먼저 열 문서 | 여기서 다음에 이어 볼 문서 |
|---|---|---|
| `인증, 인가, 세션이 한 번에 헷갈려요`, `로그인은 됐는데 왜 403이에요` | [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md) | [인증과 인가의 차이](./authentication-vs-authorization.md), [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| `쿠키, 세션, JWT가 뭐가 달라요`, `왜 로그인이 유지돼요` | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md), [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| `웹 보안을 뭘 먼저 공부해야 해요`, `Spring Security 전에 큰 그림이 필요해요` | [백엔드 주니어를 위한 웹 보안 스타터 팩](./web-security-starter-pack-backend-juniors.md) | [XSS와 CSRF 기초](./xss-csrf-basics.md), [CORS 기초](./cors-basics.md) |
| `JWT 필터를 보는데 claim, audience, revocation이 낯설어요` | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | [JWT 깊이 파기](./jwt-deep-dive.md)는 primer를 끝낸 뒤 follow-up으로 내려간다 |

## beginner role routing

초보자 first-click safety rail은 아래처럼 고정하면 된다.

| 지금 상태 | 먼저 열 역할 | 이 README에서 첫 클릭 | 아직 미루는 것 |
|---|---|---|---|
| `처음`, `로그인은 되는데 왜 403`, `cookie가 뭐가 문제인지 모르겠다` | `primer` | [기본 primer](#기본-primer), [Beginner Primer: Auth / Permission Basics](#security-auth-permission-primer), [Beginner Primer Bridge: Permission / 403](#security-permission-403-bridge) | [운영 / Incident catalog](#운영--incident-catalog), trust/recovery deep dive |
| 증상 문장은 있는데 branch가 안 잘린다 | `primer bridge` / `catalog` | [Beginner Primer Bridge (첫 분기)](#security-first-branch), [증상별 바로 가기](#증상별-바로-가기), [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) | 여러 deep dive 연속 읽기 |
| 학습 순서 전체가 먼저 필요하다 | `survey` | [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey) | symptom-first catalog에 오래 머무르기 |
| live incident, outage, recovery 순서가 급하다 | `playbook` / `runbook` / `recovery` | [운영 / Incident catalog](#운영--incident-catalog) | beginner primer를 incident 대응 문서로 착각하기 |

<a id="security-first-branch"></a>

## Beginner Primer Bridge (첫 분기)

cross-origin browser 증상을 먼저 자르고 싶으면 아래 3칸만 보면 된다.

| 지금 먼저 보이는 장면 | 먼저 갈 문서 | 여기서 다음에 고르는 갈래 |
|---|---|---|
| `OPTIONS`만 실패하고 actual `GET`/`POST`가 안 보인다 | `[primer bridge]` [Preflight Debug Checklist](./preflight-debug-checklist.md) | preflight로 확인되면 `[primer]` [CORS 기초](./cors-basics.md), actual request가 나중에 보이기 시작하면 이 표로 다시 돌아온다 |
| actual request는 있는데 request `Cookie` header가 비어 있다 | `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) | cookie scope / `credentials: "include"` / `Access-Control-Allow-Credentials` 오해를 먼저 자른 뒤 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 한 칸만 더 내려간다 |
| actual request가 있고 그 요청의 `401`/`403` 의미가 먼저 궁금하다 | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | browser redirect나 login loop 문장이 섞이면 `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로, 응답이 브라우저에서만 CORS처럼 가려지면 `[primer]` [Error-Path CORS Primer](./error-path-cors-primer.md)로 넘긴다 |

- 길을 잃으면 이 README의 [증상별 바로 가기](#증상별-바로-가기)나 [기본 primer](#기본-primer)로 돌아와 같은 branch를 다시 고르면 된다.
- browser 저장/전송 단계가 더 먼저 헷갈리면 [Network README: redirect, cookie, session부터 다시 고르기](../network/README.md#network-primer-되돌아가기)로 한 번 물러난 뒤 다시 이 branch로 돌아온다.

- 전체 흐름 `survey`가 먼저 필요하면:
  - 아래 `추천 학습 흐름 (category-local survey)` 구간
  - [CS 루트 README](../../README.md#quick-routes)

<a id="security-auth-permission-primer"></a>

## Beginner Primer: Auth / Permission Basics

- auth / session `primer`부터 읽고 싶다면:
  - [기본 primer](#기본-primer)
  - [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md)
  - browser page, SPA + BFF, bearer API 세 흐름에서 login, session continuity, permission check, logout을 한 장으로 먼저 연결하는 entrypoint primer다.
  - `로그인은 됐는데 왜 403`, `token valid인데 왜 거부`, `cookie는 있는데 왜 다시 로그인`처럼 질문이 이미 증상 문장으로 시작할 때도, 먼저 `인증 -> session continuity -> 인가` 순서를 고정하는 entrypoint로 안전하다.
  - [인증과 인가의 차이](./authentication-vs-authorization.md)
  - authn / authz뿐 아니라 `principal`, `session`, `permission model` 기본축까지 같이 잡고 싶을 때 가장 먼저 본다.
  - `principal`, `session`, `permission model`이 아직 낯설고 "`로그인 성공`과 `권한 허용`이 같은 말인가?"가 헷갈릴 때 적합하다.
  - [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
  - `cookie`, `Authorization` header, server session, JWT를 한 표에서 `무엇을 보내는가`와 `어디서 복원하는가`로 분리하는 beginner primer다. `JWT가 쿠키를 대체하나요`, `session이면 JWT는 안 쓰나요` 같은 흔한 혼동부터 끊고 싶을 때 먼저 붙인다.

<a id="security-permission-403-bridge"></a>

## Beginner Primer Bridge: Permission / 403

  - [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)
  - authn에서 role/scope/ownership으로 넘어갈 때 `로그인은 됐는데 왜 403인지`, `유효한 토큰인데 왜 403인지`, `scope 있는데 왜 거부되는지`, `내 것만 되는데 남의 것은 왜 안 되는지`를 같은 4단계 gate 축으로 짧게 정리하는 beginner primer bridge다.
  - [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
  - `role`, OAuth `scope`, `ownership`가 같은 말처럼 보일 때 읽는 primer다. 시작 부분에 `로그인 됐는데 403`를 10초 안에 `기능 입장권(role) / API 위임 범위(scope) / 객체 관계(ownership)`로 자르는 비교표를 두어 초보자가 질문 문장 그대로 빠르게 분기할 수 있게 했다. `orders.read`가 모든 주문을 뜻하지 않고, `내 것만 되는데 남의 것은 안 됨` 같은 증상이 ownership/tenant 축이라는 점을 먼저 분리한다. 문서 하단의 `ownership 누락을 잡는 최소 테스트 패턴`은 컨트롤러/서비스 레이어에서 `남의 객체 요청 거부`를 어떻게 한 쌍으로 고정할지 바로 보여 준다.
  - [리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant](./resource-level-authz-decision-practice.md)
  - beginner primer 다음 단계의 intermediate bridge다. `같은 token인데 어떤 id만 안 된다`, `same user different tenant`, `support read는 되는데 approve는 안 된다` 같은 문장을 action gate(role/scope)와 resource gate(ownership/tenant)로 나눠 실제 요청 판단 연습으로 넘겨 준다.

<a id="security-jwt-authority-freshness"></a>

## Primer + Follow-Up: JWT / Authority / Freshness

  - [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
  - OAuth `scope`, token `audience`, app `permission`이 다 같은 "권한"처럼 들릴 때 읽는 primer다. gateway audience, service audience, downscoped token, business permission을 한 번에 분리한다.
  - [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
  - `roles`, `scope`, `ROLE_`, `hasRole`, `hasAuthority`, app `permission`이 한 단어처럼 섞일 때 바로 보는 primer다.
  - [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md)
  - JWT는 valid한데 Spring route / method security에서만 `403`이 날 때, `claim은 있는데 authority가 비어 있음`, `ROLE_/SCOPE_ mismatch`, `JwtAuthenticationConverter`, `hasRole`, `hasAuthority` mismatch를 바로 좁히는 debugging deep dive다.
  - [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
  - `권한을 방금 줬는데도 403`, `grant 직후 concealment 404`가 섞일 때 source of truth 변경, claim refresh, deny cache invalidation을 먼저 분리하는 beginner `primer bridge`다. `tenant-specific 403`처럼 tenant 문맥이 앞에 서는 질문은 여기서 바로 deep dive로 내려가지 않고 아래 `증상별 바로 가기`의 tenant row로 먼저 보낸다.

<a id="security-oauth-primer"></a>

## Beginner Primer: OAuth / Social Login

  - [OAuth2 기초](./oauth2-basics.md)
  - 소셜 로그인, access token, scope, resource owner/client 같은 OAuth 용어가 아직 낯설다면 Authorization Code Grant로 내려가기 전에 먼저 읽는 first-step primer다.
  - [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
  - `구글로 로그인` 질문인데 OAuth2, OIDC, `access token`, `id token`, 내부 session이 한 문장처럼 섞이면 Authorization Code Grant나 callback hardening deep dive로 바로 뛰기 전에 이 primer bridge로 역할을 먼저 나눈다. SameSite/proxy cookie primer를 읽다가도 "지금 헷갈리는 게 cookie 속성보다 social login mental model인가?" 싶으면 이 문서로 되돌아오면 된다.

<a id="security-oauth-follow-up"></a>

## Deep-Dive Follow-Up: OAuth

  - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
  - [OAuth2 기초](./oauth2-basics.md)와 [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)까지 읽은 뒤, callback / `state` / PKCE / code exchange 흐름을 실제 login completion 관점에서 복습하는 follow-up 문서다.
  - `401` / `403` / `404` primer와 cookie / session / JWT -> Spring auth handoff는 `[cross-category bridge]` [Session / Boundary / Replay](#session--boundary--replay) anchor에서 이어 본다.
  - network primer의 `cookie` / `session` / `JWT` 설명에서 바로 올라오거나, `login loop` / `SavedRequest` / `hidden session mismatch`(=`cookie-not-sent` 또는 `server-mapping-missing`)가 보이는데 용어가 아직 흐리면 [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) route를 먼저 탄다.
  - 브라우저 없는 기기 login branch point는 `[primer bridge]` [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md)
  - authorization request hardening branch point는 `[primer bridge]` [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
  - server-side code exchange나 BFF 이후 client proof / sender-constrained branch는 `[cross-category bridge]` [Session / Boundary / Replay](#session--boundary--replay) anchor에서 이어 본다.

<a id="security-deep-dive-follow-up-shortcuts"></a>

## Deep-Dive Follow-Up Shortcuts

이 구간은 primer를 이미 끝낸 뒤에만 쓴다. `쿠키/세션/JWT가 아직 한 문장으로 안 갈린다`, `로그인 됐는데 왜 403인지부터 모르겠다` 단계라면 아래 링크를 바로 열지 말고 [기본 primer](#기본-primer)나 [증상별 바로 가기](#증상별-바로-가기)로 먼저 돌아간다.

- session coherence `deep dive` cluster로 바로 들어가려면:
  - `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)
  - `[cross-category bridge]` [Session / Boundary / Replay](#session--boundary--replay)
- authz graph / relationship cache cluster로 바로 들어가려면:
  - `[primer]` [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md)
  - `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog)
  - graph invalidation / stale deny / tenant-scoped authz bundle은 `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle) anchor에서 이어 본다.

## Deep-Dive Observability / Boundary Shortcuts

이 구간도 beginner 첫 분기가 아니다. `audit`, `signal`, `shadow evaluation`, `JWKS`, `authority mapping`처럼 운영/구현 용어가 먼저 보일 때만 사용한다.

- auth observability / evidence `deep dive` cluster로 바로 들어가려면:
  - `[catalog]` [운영 / Incident catalog](#운영--incident-catalog)
  - `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog)
  - `missing-audit-trail`, `auth-signal-gap`, `decision log missing`, `allow/deny reason code가 안 보인다`가 먼저 보이면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)에서 `signal / decision / audit` 3칸을 먼저 고정한 뒤 `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md), `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md), `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md), `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md) 순으로 붙인다.
- boundary `deep dive`로 바로 들어가려면:
  - `[deep dive]` [JWT 깊이 파기](./jwt-deep-dive.md)
  - `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
  - `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle)

## Advanced Incident / Recovery Shortcuts

- 운영 `playbook` / `runbook` / `drill` / `incident matrix` / `[recovery]` route로 바로 들어가려면:
  - `[catalog]` [운영 / Incident catalog](#운영--incident-catalog)
  - `[cross-category bridge]` [Incident / Recovery / Trust](#incident--recovery--trust)
  - `[cross-category bridge]` [Session / Boundary / Replay](#session--boundary--replay)
  - `JWKS outage`, `kid miss`, `unable to find JWK`, `auth verification outage`, `stale JWKS cache`가 먼저 보이면 위 incident bridge에서 시작한다.
- 이 구간은 beginner entry shelf가 아니다. `처음`, `로그인 됐는데 왜 403`, `cookie 있는데 왜 다시 로그인`이면 먼저 [기본 primer](#기본-primer)나 [증상별 바로 가기](#증상별-바로-가기)로 돌아간다.

## 키워드 정규화 가이드 (primer 공통)

초보자용 primer의 `retrieval-anchor-keywords`는 "정답 용어 사전"이 아니라 "학습자가 처음 던지는 말을 놓치지 않게 받는 표지판"이다. 가장 안전한 기본형은 같은 주제를 `증상형`, `행동형`, `객체형` 3갈래로 한 번씩 잡는 것이다.

| 분류 | 먼저 받는 말 | 넣는 방식 | 짧은 예시 |
|---|---|---|---|
| `증상형` | 지금 보이는 현상 | 한국어 질문문이나 실패 문장으로 적는다 | `로그인 됐는데 왜 403`, `권한 줬는데도 403`, `남의 주문인데 왜 404` |
| `행동형` | 사용자가 방금 한 일 | 변화, 시도, 흐름을 짧은 동사구로 적는다 | `권한을 방금 줬는데`, `tenant 이동 후`, `재로그인해도 403` |
| `객체형` | 이미 알고 있는 용어 | 문서의 핵심 명사와 정확한 영문 용어를 적는다 | `role`, `scope`, `ownership`, `permission`, `SameSite`, `JWKS` |

처음 문서를 쓸 때는 "무슨 현상인가 -> 뭘 했는가 -> 어떤 객체 이야기인가" 순서로 1줄씩만 적어도 품질 편차가 크게 줄어든다. 한국어 설명형 alias를 먼저 두고, 로그/스펙/코드에서 그대로 보이는 영문 객체명은 뒤에 붙이는 편이 beginner 검색에 유리하다.

### 작은 예시

| 주제 | 약한 키워드 묶음 | 더 나은 키워드 묶음 |
|---|---|---|
| role / scope / ownership primer | `role`, `scope`, `ownership`, `permission` | `로그인 됐는데 왜 403`, `권한을 방금 줬는데`, `남의 주문인데 왜 404`, `role`, `scope`, `ownership` |

위처럼 객체형만 나열하면 glossary에는 맞아도 초보자의 첫 질문을 잘 못 받는다. 반대로 증상형만 있으면 관련 문서를 서로 묶기 어려워진다. primer는 세 갈래를 같이 두는 것이 기본값이다.

## Primer Keyword Checklist

### 작성 체크리스트

- 새 primer에는 최소한 `증상형 1개 + 행동형 1개 + 객체형 1개`를 넣는다.
- 증상형은 초보자가 실제로 말할 한국어 문장으로 먼저 적고, 너무 추상적인 `인증 문제`, `권한 이슈` 같은 표현은 피한다.
- 행동형은 `변경`, `이동`, `재로그인`, `회전`, `복구`처럼 흐름이 보이는 동사구를 쓴다.
- 객체형은 문서의 핵심 명사만 남기고, 하위 구현 세부 키워드를 과하게 늘리지 않는다.
- 영문 에러 문자열이나 스펙 용어가 중요하면 객체형 뒤쪽에 붙이고, 한국어 증상형을 대체하지는 않는다.
- README와 개별 primer 사이에서는 같은 주제를 같은 이름으로 반복한다. 예: `로그인 됐는데 왜 403` / `남의 주문인데 왜 404` / `권한을 방금 줬는데도 403` / `role vs scope vs ownership`.

### 자주 생기는 혼동

- 객체형만 많이 넣는 경우: 검색은 되더라도 초보자 질문이 README entrypoint로 잘 안 붙는다.
- 증상형만 넣는 경우: 비슷한 문서끼리 cluster가 약해져 후속 deep dive 연결이 흐려진다.
- 운영 장애 alias를 primer에 과하게 넣는 경우: beginner 문서가 incident 문서처럼 읽힌다. 이런 키워드는 [운영 / Incident catalog](#운영--incident-catalog)나 관련 `recovery` 문서로 보내고, primer 본문은 first-step mental model에 집중한다.
- decision rule: alias가 `왜 403인지`, `왜 다시 로그인되는지`처럼 첫 증상 해석을 돕는 말이면 primer에 두고, `outage`, `blast radius`, `failover`, `recovery`, `runbook`처럼 운영 판단이나 복구 순서를 바로 요구하면 incident catalog나 `recovery` 문서로만 보낸다.
- 같은 뜻을 너무 많이 복제하는 경우: alias 수를 늘리기보다 대표 표현 하나와 정확한 객체명 하나를 남기는 편이 유지보수와 retrieval 품질이 더 좋다.

연결 예시는 [기본 primer](#기본-primer), [증상별 바로 가기](#증상별-바로-가기), [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog)에서 바로 확인할 수 있다.

## 역할별 라우팅 요약

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| security 전체 지형과 추천 순서 | `survey` | [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey) |
| auth / session / OAuth 기초 축 | `primer` | [기본 primer](#기본-primer) |
| auth / session / authz primer를 읽은 뒤 symptom을 deep dive로 넘기기 | `primer bridge` | 대표 entrypoint: [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md), [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md), [Preflight Debug Checklist](./preflight-debug-checklist.md), [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md), [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md), [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md) |
| session / browser / authz / SCIM 중 어느 bucket부터 읽을지 먼저 고르기 | `catalog / navigator` | 아래 각 `deep dive catalog` 섹션 |
| 특정 failure mode, boundary, cache, revocation tail 같은 한 축을 바로 깊게 보기 | `deep dive` | [Session Revocation at Scale](./session-revocation-at-scale.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |
| 장애 대응 순서, rotation 운영, rehearsal, blast-radius 분류가 먼저 필요함 | `playbook` / `runbook` / `drill` / `incident matrix` / `recovery` | [운영 / Incident catalog](#운영--incident-catalog) |
| security 바깥 handoff까지 같이 묶어 읽기 | `cross-category bridge` | [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge) |
| 역할 라벨이나 검색 alias가 헷갈림 | `taxonomy` / `routing helper` | [Navigation Taxonomy](../../rag/navigation-taxonomy.md) |

<a id="증상별-바로-가기"></a>
## 증상별 바로 가기 (`primer bridge` / incident split)

증상 문장으로 들어온 질문을 incident badge 문서(`playbook` / `runbook` / `drill` / `incident matrix` / `[recovery]`)나 `deep dive` 본문으로 다시 번역하는 shortcut이다. 첫 진입점과 follow-up 모두에 역할 cue를 명시해서, incident 대응 문서와 개념/원인 `deep dive`, section-level `catalog` / `cross-category bridge`를 같은 row 안에서도 바로 구분할 수 있게 유지한다.
beginner row에서는 `[primer]`를 first-step mental model, `[primer bridge]`를 그다음 handoff 문서로 읽는다.
login-loop 인접 beginner route는 `redirect / cookie / session-persistence` 세 갈래 모두를 `[primer] -> [primer bridge]` 라벨로 맞춘다.
cookie-focused shortcut row도 같은 badge 규칙을 쓴다. `blocked Set-Cookie`처럼 저장 단계가 먼저 보이면 `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) -> `[primer bridge]` [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md), `Application > Cookies`에는 보이는데 request `Cookie`가 비면 먼저 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `cookie-header gate`로 같은 실패 요청을 고정한 뒤 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) -> `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md) 순서로만 먼저 노출하고, 그 뒤에만 deep dive나 recovery를 붙인다.
이 표에서는 1차 질문을 고정한다: `OPTIONS-only인가? actual request가 있는가?`를 먼저 확인하고, 그다음 auth/cookie/session branch로 내려간다.

처음 보는 junior reader라면 이 section도 한 번 더 나눠 읽는 편이 안전하다.

| 지금 보이는 질문 재질 | 이 section에서 먼저 읽을 row 역할 | 아직 첫 클릭으로 올리지 않는 것 |
|---|---|---|
| `처음`, `헷갈려요`, `왜 403`, `cookie 있는데 왜 다시 로그인` | `[primer]`, `[primer bridge]`, `[catalog]` | `[playbook]`, `[runbook]`, `[recovery]` |
| `outage`, `blast radius`, `failover`, `rotation incident`, `복구 순서` | `[playbook]`, `[incident matrix]`, `[recovery]` | beginner primer를 incident 정답 문서처럼 기대하기 |

즉 이 section은 "증상으로 들어오되, 먼저 primer/bridge로 branch를 자를지, incident follow-up으로 바로 갈지"를 가르는 symptom-first `catalog`다.

브라우저 `Network`에서 처음 10초는 `status` 숫자보다 `요청 method`와 `actual request 존재 여부`를 먼저 본다.

이 표는 `survey`가 아니라 symptom-first `catalog`다.

## 증상별 바로 가기: 라벨 읽는 법

초보자는 아래 네 가지만 먼저 고정하면 라벨을 덜 헷갈린다.

| 라벨 | 이 표에서 뜻하는 것 | 초보자에게 안전한 읽는 순서 |
|---|---|---|
| `[catalog]` | 아직 정답 설명이 아니라, 다음 branch를 고르는 entrypoint | `catalog`에서 branch를 고른 뒤 `primer`나 `primer bridge`로 한 칸만 내려간다 |
| `[primer bridge]` | 첫 primer 다음에 symptom 언어를 handoff하는 2단계 문서 | 바로 뒤 한 개의 `[deep dive]`만 붙여 읽는다 |
| `[deep dive]` | 특정 원인, 경계, trade-off를 깊게 파는 본문 | `primer`/`primer bridge` 없이 바로 여러 개를 연속으로 열지 않는다 |
| `[playbook]` / `[recovery]` | 지금 장애 대응 순서나 복구 절차가 먼저 필요한 문서 | live incident가 아니면 먼저 `primer`나 `catalog`에서 symptom 해석을 맞춘다 |

큰 그림이 먼저 필요하면 이 표 안에서 오래 머물지 말고 `[survey]` [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey)로 올라간다.

## 증상별 바로 가기: DevTools 첫 질문

| DevTools mini example | Network에서 실제로 보이는 것 | 1차 질문 답 | 다음 이동 |
|---|---|---|---|
| 예시 A: `OPTIONS`만 실패 | `OPTIONS /api/orders` -> `401`, 같은 path의 actual `POST /api/orders`는 아예 안 생김 | `OPTIONS-only` | auth 해석 전에 `[primer bridge]` [Preflight Debug Checklist](./preflight-debug-checklist.md) |
| 예시 B: actual request가 보임 | `OPTIONS /api/orders` -> `204`, 바로 아래 `POST /api/orders` -> `401` | actual request가 실제로 보임 | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) 또는 `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |

- `OPTIONS 401`만 있으면 브라우저가 본 요청은 preflight failure다. 이 단계에서는 "로그인 실패"라고 아직 말하지 않는다.
- actual `POST`/`GET`이 실제로 보일 때만 그 요청의 `401`/`403`를 auth/cookie/session 의미로 읽는다.
- 아래 `추천 학습 흐름` 표의 AuthZ 쪽 row는 role badge를 inline으로 유지한다. `[primer]`는 첫 mental model, `[primer bridge]`는 안전한 다음 분기, `[deep dive]`는 원인 파고들기, `[survey]`는 category-local map으로 되돌아가기다.

## 증상별 바로 가기: Quick Routes

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `1차 질문(고정)`: Network에서 `OPTIONS`만 실패하고 actual `GET`/`POST`가 없나, 아니면 actual request가 실제로 보이나? | `OPTIONS-only`면 `[primer bridge]` [Preflight Debug Checklist](./preflight-debug-checklist.md#먼저-10초-분기표), actual request가 보이면 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)에서 `401 -> 403 -> 404` 기본 분기를 다시 본다 | `OPTIONS-only`로 확인되면 `[primer]` [CORS 기초](./cors-basics.md), actual request가 보이면 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) 또는 `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |
| "남의 주문인데 왜 `403`이 아니라 `404`가 나오죠?", `없는 줄 알았는데 남의 리소스였다` | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)에서 `404`를 먼저 고정 | `[primer bridge]` [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)의 `beginner 최소 테스트 템플릿`으로 `403`과 의도적 `404` assertion 이름을 먼저 고정 -> `[deep dive]` [IDOR / BOLA Patterns and Fixes: `403` vs 의도적 `404` 30초 분기표](./idor-bola-patterns-and-fixes.md#30초-분기표-idor에서-403-vs-의도적-404) |

## 증상별 바로 가기: Browser Call / Error Contract

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `CORS 때문에 프론트에서 외부 API에 직접 붙이고 싶은데`, `브라우저에 API 키를 넣어도 되나`, `server-side only` 문구를 어떻게 읽어야 하나 | `[primer bridge]` [브라우저 직접 호출 vs 서버 프록시 결정 트리](./browser-direct-call-vs-server-proxy-decision-tree.md) | 서버 시크릿 보관과 대리 호출 예시는 `[primer]` [API 키 기초](./api-key-basics.md), 사용자 외부 자원 접근이면 `[primer]` [OAuth2 기초](./oauth2-basics.md), 브라우저/서버 토큰 경계를 깊게 보면 `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |
| `외부 API가 준 401/403/500 body를 사용자에게 그대로 내려도 되나`, `provider error_description을 그대로 보여 줘도 되나`, `request_id만 남기고 짧게 바꾸는 기준이 뭐지` | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | 문서의 `안전한 에러 body 예시와 내부 로그 매핑`에서 provider 에러 pass-through 금지 예시를 먼저 본다. 구현 디테일은 `[spring]` [Spring ProblemDetail / Error Response Design](../spring/spring-problemdetail-error-response-design.md), 브라우저/서버 경계는 `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 이어진다. |

## 증상별 바로 가기: Verification / Rotation

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `JWKS outage`, `invalid signature`, `kid` miss, `unable to find JWK`, `auth verification outage`, `stale JWKS cache`, JWKS fetch/cache mismatch | `[playbook]` [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md) | `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md), `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md) |
| rotation 직후 일부 인스턴스만 검증 실패하거나 old/new signer가 섞여 보임 | `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md) | `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md), `[runbook]` [Key Rotation Runbook](./key-rotation-runbook.md), `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md) |
## 증상별 바로 가기: Incident / Support / Evidence

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `로그아웃했는데 계속 된다`, `logout still works`, revoke가 늦다, route별 tail이 남고 세션이 곳곳에 남는다 | `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) -> `role/claim` tail이면 `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md), tenant/grant 쪽 tail이면 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) / `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md) -> `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md) -> `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md) -> `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md) -> `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge)에서 branch별 `DevTools 1개 + 로그 1개` 최소 증거 체크리스트를 먼저 맞춘다 -> `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](../system-design/revocation-bus-regional-lag-recovery-design.md) |

## 증상별 바로 가기: Revoke Status / Timeline

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| operator-triggered revoke 이후 `requested`, `in_progress`, `fully_blocked_confirmed`를 언제 내려야 할지 헷갈림 | `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md) | `[deep dive]` [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md), `[deep dive]` [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md). 상태 의미가 event/evidence 용어와 다시 섞이면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)로 한 단계 올라가 `signal / decision / audit` 3칸을 다시 맞추고, category 복귀는 `[survey]` [Security README: 운영 / Incident catalog](./README.md#운영--incident-catalog) |
| AOBO / break-glass revoke에서 `preview_id`, `access_group_id`, `revocation_request_id`를 어떤 event와 timeline row에 실어야 할지 헷갈림 | `[deep dive]` [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md) | `[deep dive]` [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md), `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md). correlation id가 evidence/observability 질문으로 다시 넓어지면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)로 되돌아가고, category 복귀는 `[survey]` [Security README: 운영 / Incident catalog](./README.md#운영--incident-catalog) |

## 증상별 바로 가기: Support / Cleanup

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| support AOBO / break-glass transfer cleanup이 안 닫히고 delegated access/session tail이 남아 `cleanup_confirmed`를 언제 내려야 할지 헷갈림 | `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md) | primer의 `10초 라우터`에서 먼저 `종료·cleanup` 갈래만 고정한 뒤 `[deep dive]` [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md)으로 내려간다. evidence 기준은 `[deep dive]` [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md), refresh/session tail은 `[deep dive]` [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md), incident close hard gate는 `[deep dive]` [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)로 이어 붙인다. cleanup evidence를 metric/event/signal로 다시 나눠야 하면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)로 한 칸 올라가고, category 복귀는 `[survey]` [Security README: Service / Delegation Boundaries deep dive catalog](./README.md#service--delegation-boundaries-deep-dive-catalog) |

## 증상별 바로 가기: Support Lifecycle / Timeline

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| delegated support access에서 start/end event id, lifecycle state, inbox/timeline close, `cleanup_confirmed` 경계를 어떻게 맞춰야 할지 헷갈림 | `[deep dive]` [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md) | `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md). lifecycle/event/evidence 축을 다시 줄여야 하면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)와 `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md) 중 한 장만 다시 보고, category 복귀는 `[survey]` [Security README: 운영 / Incident catalog](./README.md#운영--incident-catalog), `[survey]` [Security README: Service / Delegation Boundaries deep dive catalog](./README.md#service--delegation-boundaries-deep-dive-catalog) |

## 증상별 바로 가기: Support Notifications / Policy

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| support access alert에서 email, in-app inbox, security timeline, alternate verified channel을 언제 써야 할지, mailbox compromise 때 primary email을 계속 믿어도 되는지 헷갈림 | `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md) | primer 안의 `10초 라우터`로 먼저 `read / write / break-glass / mailbox trust` 한 줄을 고른 뒤 `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md), `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Email Magic-Link Threat Model](./email-magic-link-threat-model.md). alert evidence와 timeline/event schema가 다시 섞이면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)로 한 번 되돌아가고, category 복귀는 `[survey]` [Security README: Service / Delegation Boundaries deep dive catalog](./README.md#service--delegation-boundaries-deep-dive-catalog) |

## 증상별 바로 가기: Support Tenant Policy

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| tenant마다 privileged support change alert, security-contact opt-in, managed-identity escalation, compliance-sensitive support event retention을 어떤 schema로 저장하고 평가해야 할지 헷갈림 | `[deep dive]` [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md) | `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md). policy schema가 alert/evidence/retention 질문과 다시 섞이면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)로 한 칸 올라가고, category 복귀는 `[survey]` [Security README: Service / Delegation Boundaries deep dive catalog](./README.md#service--delegation-boundaries-deep-dive-catalog) |

## 증상별 바로 가기: Observability / Secrets / Response

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `missing-audit-trail`, `audit trail이 없다`, `누가 허용/거부했는지 안 남는다`, `decision log missing`, `allow/deny reason code가 없다`, `auth-signal-gap`, `auth telemetry gap`, `401/403 spike인데 reason bucket이 안 보임`, `observability blind spot` | `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md) | `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md), `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md), `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md), `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md). observability/evidence 갈래를 다시 고르려면 `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md)로 돌아가고, category 복귀는 `[survey]` [Security README: 기본 primer](./README.md#기본-primer), `[survey]` [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기), `[survey]` [Security README: 운영 / Incident catalog](./README.md#운영--incident-catalog) |

## 증상별 바로 가기: Secrets / Key Handling

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| 외부 API 연동에서 `브라우저에 API 키를 넣어도 되나`, `이건 사용자 로그인 말고 서버 작업인가`, `server-side only` 문구를 어떻게 읽어야 하나가 먼저 헷갈림 | `[primer]` [API 키 기초](./api-key-basics.md) | 브라우저/서버 배치와 키 노출 첫 대응은 API 키 primer에서 먼저 잡고, 사용자 위임 권한이 필요하면 `[primer]` [OAuth2 기초](./oauth2-basics.md), 장기 고정 키 운영 부담이 크면 `[primer bridge]` [Workload Identity vs Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md)로 간다. 저장 위치, `.env`, secret manager, commit 금지가 더 먼저면 아래 `[primer]` [시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유](./secrets-management-basics.md)로 한 칸 옮긴다. |
| `DB 비밀번호나 API 키를 코드/application.properties/.env에 어디까지 두면 안 되나`, `env와 secret manager 중 어디서 시작하지`, `노출되면 코드 수정 말고 뭘 먼저 해야 하나`가 먼저 헷갈림 | `[primer]` [시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유](./secrets-management-basics.md) | 저장/주입 mental model을 먼저 고정한 뒤, 외부 API 호출 자격 증명 선택이 헷갈리면 `[primer]` [API 키 기초](./api-key-basics.md), 로그/에러에 값이 새는 장면이 걱정되면 `[primer]` [로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나](./log-masking-basics.md), 회전·누출·복구 운영으로 내려가려면 `[deep dive]` [시크릿 관리·로테이션·누출 패턴](./secret-management-rotation-leak-patterns.md)으로 이어 간다. |

## 증상별 바로 가기: Response Codes

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `401` / `403` / `404` 중 무엇을 써야 하는지, login required / forbidden / not found가 섞이고 `Unauthorized`라는 이름 때문에 헷갈림 | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | beginner FAQ와 최소 JSON/body 카드로 `Unauthorized`, concealment `404`, stable code, `WWW-Authenticate`를 먼저 정리한다. browser redirect면 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md), stale `403` / cached `404`면 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md), concealment 설계면 `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md), category 복귀는 `[survey]` [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog) |
## 증상별 바로 가기: Browser / CORS / Cookie

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀`, `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음`, `hidden session`, `hidden JSESSIONID`, `hidden session mismatch`, `cookie-not-sent`, `stored but not sent`, `server-mapping-missing`, `sent but anonymous`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login` | `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) | 먼저 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 `redirect / cookie transfer / session mapping / browser redirect` 네 갈래를 고정한다. redirect면 `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md), request `Cookie` header가 비면 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) 또는 `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md), cookie는 갔는데 anonymous면 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), 원인 축을 더 넓히면 `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge)로 내려간다. |

## 증상별 바로 가기: Cookie State Splitter

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `cookie 문제인지 session 문제인지`부터 헷갈리고, `This Set-Cookie was blocked...`, `Application > Cookies`에는 보이지만 request `Cookie`는 비어 있음, request `Cookie`는 있는데도 anonymous가 한 문장처럼 섞임 | `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) | `[primer bridge]` [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)에서 `blocked Set-Cookie` / `stored but not sent` / `sent but anonymous`를 먼저 고정한다. splitter 뒤 `stored but not sent`는 beginner label로 `cross-origin fetch / subdomain scope confusion`이라고 읽으면 된다. 먼저 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `cookie-header gate`로 같은 실패 요청을 맞춘 뒤 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), duplicate cookie와 proxy `Secure` cookie branch가 헷갈리면 `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md), `sent but anonymous`면 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 한 칸만 더 내려간다. |

## 증상별 바로 가기: CORS / Fetch / Cookie Scope

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| 브라우저 콘솔에는 CORS 에러가 뜨는데 Network에는 `OPTIONS`만 `401`/`403`/`405`로 실패하고 actual `GET`/`POST`가 안 보이거나, preflight 뒤 actual `401`이 맞는지 헷갈림 (위 1차 질문에서 `OPTIONS-only`로 확인된 경우) | `[primer bridge]` [Preflight Debug Checklist](./preflight-debug-checklist.md) | `[primer]` [CORS 기초](./cors-basics.md), `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md), actual request `401`/`403` 의미는 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md), deeper CORS/sameSite는 `[deep dive]` [CORS, SameSite, Preflight](./cors-samesite-preflight.md) |

## 증상별 바로 가기: Cookie Scope / Credentials

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| DevTools `Cookies` 탭에 `This Set-Cookie was blocked...` 같은 reason이 뜨는데 `Secure`, `SameSite`, `Domain`, `Path` 중 어느 축부터 봐야 할지 모르겠음 | `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) | `[primer bridge]` [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md)로 먼저 `blocked`가 여전히 저장 단계인지, 이미 `stored but not sent`로 넘어갔는지 확인한다. 그다음 `Secure -> proxy`, `SameSite -> cross-site`, `Domain/Path -> cookie scope` 중 한 갈래만 고르고, sibling subdomain handoff가 의심될 때만 `[primer bridge]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 한 칸 더 내려간다. |
| `fetch`에 `credentials: "include"`를 넣었는데 cookie가 안 가거나, `Access-Control-Allow-Credentials`를 켰는데도 login API가 익명처럼 보임 | `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) | `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), `[primer]` [CORS 기초](./cors-basics.md), `[deep dive]` [CORS, SameSite, Preflight](./cors-samesite-preflight.md), `[deep dive]` [CORS Credential Pitfalls / Allowlist Design](./cors-credential-pitfalls-allowlist.md) |

## 증상별 바로 가기: Social Login / Callback Cookies

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `same-origin`, `same-site`, `cross-site`가 social login callback, `auth.example.com -> app.example.com`, partner iframe 장면에서 한 문제처럼 섞여 어디부터 봐야 할지 모르겠음 | `[primer bridge]` [SameSite Login Callback Primer](./samesite-login-callback-primer.md) | external IdP/iframe면 `[primer bridge]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md), sibling subdomain handoff면 `[primer bridge]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md), redirect가 `http://...`로 꺾이면 `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), XHR/API credential 질문이면 `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md), 다음 branch 재선택은 [Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| external IdP callback, social login, partner portal iframe 경로에서만 cookie가 안 붙고 redirect는 계속 `https://...`라서 proxy 문제인지 `SameSite=None` 문제인지 헷갈림 | `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) | `[primer bridge]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)로 cross-site cookie 전송 축을 먼저 고정한다. OAuth2/OIDC mental model이 다시 섞이면 `[primer bridge]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md), 이후 follow-up은 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) 또는 `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)다. |

## 증상별 바로 가기: Social Login Mental Model

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| 구글/네이버/카카오 social login 질문인데 OAuth2, OIDC, `access token`, `id token`, 내부 session 역할이 한 문장처럼 섞여 어디서부터 읽어야 할지 모르겠음 | `[primer bridge]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md) | `[primer]` [OAuth2 기초](./oauth2-basics.md), `[deep dive]` [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md), `[deep dive]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md), beginner route를 다시 고르려면 [기본 primer](#기본-primer) |

## 증상별 바로 가기: Callback Handoff / CSRF

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `auth.example.com/callback`은 성공인데 `app.example.com` 첫 요청이 anonymous이고, shared cookie로 넓혀야 하는지 handoff가 필요한지 헷갈림 | `[primer]` [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) | chooser에서 shared cookie 기대면 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff 기대면 `[primer bridge]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 먼저 한 칸만 내려간다. external IdP/iframe 경유에서만 깨지면 `[primer bridge]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md), 이후에만 `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), `[deep dive]` [Session Fixation in Federated Login](./session-fixation-in-federated-login.md)로 이어 간다. |
| social login callback은 성공했는데 첫 POST가 `403`이거나, callback 이후 CSRF 경계가 어디서 다시 시작되는지 헷갈림 | `[primer]` [XSS와 CSRF 기초](./xss-csrf-basics.md) | `[primer]` [OAuth2 기초](./oauth2-basics.md) -> `[primer bridge]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md) -> `[deep dive]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) -> `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md), `[deep dive]` [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), `[deep dive]` [Session Fixation in Federated Login](./session-fixation-in-federated-login.md) |

## 증상별 바로 가기: Redirect / Proxy / Duplicate Cookie

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| session cookie scope를 `/app -> /`나 host-only -> shared domain으로 옮긴 뒤 old cookie가 안 지워져 특정 route만 다시 로그인되고, 어떤 `Set-Cookie` tombstone을 보내야 할지 헷갈림 | `[follow-up primer bridge]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md) | broad entrypoint가 아니라 cleanup 설계용 follow-up이다. 먼저 `저장됨 vs 전송됨` 분리가 안 됐으면 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), duplicate인지 proxy인지도 아직 헷갈리면 `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md)로 한 칸 올라간다. |
| login 후 `Location`이나 OAuth `redirect_uri`가 `app-internal`, `localhost`, staging host처럼 wrong origin으로 바뀌고 `X-Forwarded-Host` / host preservation이 헷갈리거나, relative redirect는 괜찮은데 absolute callback/email link만 깨짐 | `[primer]` [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md) | scheme/cookie 쪽이면 `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), forwarded header 신뢰 경계면 `[primer]` [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md), user-supplied `next` 반사면 `[deep dive]` [Open Redirect Hardening](./open-redirect-hardening.md), OAuth flow 전체는 `[deep dive]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) |

## 증상별 바로 가기: Proxy / Duplicate Cookie

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `X-Forwarded-Proto` / `X-Forwarded-For`를 앱이 믿어도 되는지, proxy 뒤에서 `redirect becomes http`, client IP, rate limit, IP allowlist가 같이 헷갈림 | `[primer]` [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md) | cookie/redirect면 `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), wrong host/origin이면 `[follow-up]` [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md), deeper trust chain은 `[deep dive]` [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md), 복귀는 [Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| duplicate session cookie, same cookie name different path/domain, raw `Cookie` header에 `session=...; session=...`가 보이고 특정 route만 login loop | `[follow-up primer]` [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) | 먼저 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `cookie-header gate`로 저장값과 request `Cookie` header를 맞춘다. raw header 중복이 아직 없으면 `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md)로 먼저 분리하고, 복귀는 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)다. |
## 증상별 바로 가기: AuthZ / Freshness / Tenant

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `권한을 방금 줬는데 still 403`, `new role granted but forbidden`, `grant 직후 concealment 404`, re-login/refresh를 언제 요구해야 하는지 헷갈림 | `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | 문서 앞쪽의 `1분 진단표`에서 `claim stale / cache stale / tenant context stale` 세 갈래를 먼저 고정한 뒤, claim/session 쪽이면 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md), tenant 문맥 쪽이면 `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md), stale deny/cached concealment `404`면 `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md), self-contained JWT 반영 속도 비교는 `[deep dive]` [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md), route를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog) |

## 증상별 바로 가기: Tenant Context Freshness

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `새 tenant membership을 받았는데 403`, `tenant-specific 403`, `workspace switch 뒤 403`, `old workspace가 남음` | `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md) | 먼저 tenant/session 문맥이 최신인지 고정한다. grant 직후 deny인지 tenant picker/context stale인지 헷갈리면 이 bridge의 `20초 route split`부터 읽고, membership/session 쪽이면 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md), concealment `404`가 섞이면 `[primer bridge]` [Concealment \`404\` Entry Cues](./concealment-404-entry-cues.md), tenant-scoped cache나 isolation 확인은 그다음에만 `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> `[deep dive]` [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)로 내려간다. route를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog) |

## 증상별 바로 가기: Graph / Claim / Revoke Tail

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `authorization graph cache`, `graph snapshot`, `relationship cache`, delegated scope revoke 뒤 graph invalidation이 의심됨 | `[primer]` [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md) | beginner 기본값은 graph deep dive를 첫 hop으로 열지 않는 것이다. 먼저 primer에서 `변경` / `전파` / `판정` 세 칸을 고정한 뒤 `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)으로 runtime evidence를 맞춘다. `graph snapshot version`, `relationship edge invalidation` 증거가 명확할 때만 `[deep dive]` [Authorization Graph Caching](./authorization-graph-caching.md), `[deep dive]` [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md), `[deep dive]` [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)로 내려가고, 길을 잃으면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 복귀 |

## 증상별 바로 가기: Claim / Revoke Tail

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `role revoked but still works`, stale authority claim, old authorities가 JWT/session/cache/revocation 중 어디에 남는지 먼저 분해하고 싶음 | `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md) | 배경 mental model을 다시 맞출 때는 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md), 구현 전파를 파고들 때는 `[deep dive]` [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md), `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md), route를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog) |

## 증상별 바로 가기: Authority Transfer / Revoke Lag

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `authority transfer`와 `revoke lag`가 같은 말처럼 들리고, cleanup/parity 질문을 authz-cache incident와 먼저 분리하고 싶다 | `[primer bridge]` [Authority Transfer vs Revoke Lag Primer Bridge](./authority-transfer-vs-revoke-lag-primer-bridge.md) | authority transfer 쪽이면 `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md) -> `[survey]` [Security README: Identity / Delegation / Lifecycle](./README.md#identity--delegation--lifecycle) 순으로 owner/parity/cleanup을 먼저 고정하고, revoke lag 쪽이면 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) -> `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)으로 tail 원인을 본다. authz cache route로 돌아가려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog) |

## 증상별 바로 가기: Audience / Authority / Ownership

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `scope`는 있는데 왜 이 API가 token을 안 받지, `aud`/`scope`/app permission이 같은 말인지 헷갈림 | `[primer]` [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md) | grant flow는 `[primer]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md), browser/server 경계는 `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), claim-to-authority 매핑은 `[primer]` [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md), 위임 위험은 `[deep dive]` [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md) |
| JWT는 valid한데 Spring Security route / method security에서만 `403`이고, `JwtAuthenticationConverter`, `ROLE_` / `SCOPE_`, `hasRole` / `hasAuthority` mismatch가 의심됨 | `[primer]` [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md) | Spring mapping 구현 축은 `[deep dive]` [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md), filter 흐름 축은 `[deep dive]` [Spring Security Filter Chain](../spring/spring-security-filter-chain.md), 응답 코드 축을 다시 맞출 때는 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md), authz route를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog) |

## 증상별 바로 가기: Ownership / Permission Model

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| authn은 이해했는데 `로그인은 됐는데 왜 403인지`, `내 것만 되는데 남의 것은 왜 안 되는지`, role/scope/ownership이 한 문장처럼 섞임 | `[primer bridge]` [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md) | 축 이름을 다시 고정할 때는 `[primer]` [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md), object-level 설계로 내려갈 때는 `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md), 응답 코드 축을 같이 맞출 때는 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md), route를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog) |

## 증상별 바로 가기: Stale Deny / Response Drift

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| stale deny가 남거나 grant 뒤 `cached 404`가 남고, 같은 실패가 `401`/`404` 사이에서 흔들려 응답 의미부터 다시 확인해야 함 | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | response code 의미를 먼저 고정한 뒤 freshness 분기는 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) -> cache 원인은 `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> runtime 증거는 `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) -> negative cache 사례는 `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)로 이어 간다. tenant 문맥이 먼저 의심되면 위 `tenant-specific 403` row로, route를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 복귀 |
## 증상별 바로 가기: Replay / Identity / Cleanup

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| nonce/replay store가 죽어서 중복 요청이 막히지 않거나 정상 요청이 과차단됨 | `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md) | `[deep dive]` [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md), `[deep dive]` [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md) |
| key compromise, emergency revoke, blast radius부터 빨리 판단해야 함 | `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md) | `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md), `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md), `[runbook]` [Key Rotation Runbook](./key-rotation-runbook.md) |

## 증상별 바로 가기: Identity Tail / Support Audience

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `SCIM disable은 끝났는데 account-state/access shutdown 설명이 안 맞음`, deprovision은 끝났는데 runtime access tail이 남음, `backfill is green but access tail remains`, `decision parity`, `auth shadow divergence` | `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md) | lifecycle 의미부터 낯설면 `[primer]`에서 `계정 상태 변경`과 `access tail`을 먼저 분리한다. revoke tail과 섞여 들리면 다음 한 걸음만 `[primer bridge]` [Authority Transfer vs Revoke Lag Primer Bridge](./authority-transfer-vs-revoke-lag-primer-bridge.md)로 붙인다. beginner-safe starter는 database/system-design README와 같은 primer-first 사다리로 고정한다: `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle). 이후에만 `[deep dive]` [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md), `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md), `[deep dive]` [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md), `[system design]` [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge), `[system design]` [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge), `[system design]` [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md)로 확장한다. |
| support AOBO나 break-glass를 누구에게 알려야 할지, email/push/in-app copy를 어떻게 맞출지 헷갈림 | `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md) | primer 안의 `10초 라우터`에서 audience row를 먼저 고르고, wording만 급하면 `Email / Inbox / Timeline wording 치트시트` 한 줄을 먼저 본다. 그다음 `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), `[deep dive]` [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md) |

## 기본 primer

아래 문서들은 security 내부의 broad survey가 아니라, 이후 `deep dive catalog`를 읽기 전에 기초 축을 맞추는 `primer`다.

입문자가 특히 자주 섞는 `입력값 검증` / `SQL 인젝션` / `XSS·CSRF`는 아래 한 줄 질문으로 먼저 갈라 보면 된다.

| 헷갈리는 주제 | 먼저 던질 질문 | 여기서 다루는 핵심 | 바로 다음 한 걸음 |
|---|---|---|---|
| [입력값 검증 기초](./input-validation-basics.md) | `이 입력을 서버가 애초에 받아도 되나?` | 형식 검증, 의미 검증, allowlist, 서버측 검증 책임 | DB 쿼리까지 걱정되면 [SQL 인젝션 기초](./sql-injection-basics.md), 화면 출력/브라우저 요청이 걱정되면 [XSS와 CSRF 기초](./xss-csrf-basics.md) |
| [SQL 인젝션 기초](./sql-injection-basics.md) | `이 입력이 SQL 문장 구조를 바꾸나?` | 문자열 연결, 파라미터 바인딩, PreparedStatement | ORM/native query 함정은 [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md), 다른 primer를 다시 고르려면 이 `기본 primer` 목록으로 돌아온다 |
| [XSS와 CSRF 기초](./xss-csrf-basics.md) | `브라우저가 악성 스크립트를 실행하나, 로그인된 사용자를 대신해 요청을 보내나?` | 출력 이스케이프, CSP, CSRF 토큰, SameSite | Spring filter/cookie 흐름은 [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md), 다른 primer를 다시 고르려면 이 `기본 primer` 목록으로 돌아온다 |

cross-origin login/API 증상은 아래 3칸으로 먼저 자르면 CORS 관련 beginner 문서를 전부 훑지 않아도 된다.

| 지금 먼저 보이는 장면 | 먼저 갈 문서 | 여기서 다음에 고르는 갈래 |
|---|---|---|
| `OPTIONS`만 실패하고 actual `GET`/`POST`가 안 보인다 | `[primer bridge]` [Preflight Debug Checklist](./preflight-debug-checklist.md) | preflight lane으로 확인되면 `[primer]` [CORS 기초](./cors-basics.md), actual request가 나중에 보이기 시작하면 이 `기본 primer` 표로 돌아온다 |
| actual request는 있는데 request `Cookie` header가 비어 있다 | `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) | `credentials: "include"`와 cookie scope를 먼저 자른 뒤 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 한 칸만 더 내려간다 |
| actual request가 있고 그 요청의 `401`/`403` 의미가 먼저 궁금하다 | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | browser redirect/login loop면 `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path), error body가 브라우저에서만 CORS처럼 가려지면 `[primer]` [Error-Path CORS Primer](./error-path-cors-primer.md)로 넘긴다 |

**🟢 Beginner 입문 문서 (security 처음이라면 여기서 시작)**

- [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md): CIA 트라이어드(기밀성·무결성·가용성)와 인증·인가의 최소 개념을 잡는 security 첫 진입 문서다. 백엔드에서 보안이 어디서 등장하는지 흐름을 먼저 본 뒤 다른 primer로 이어가기에 좋다.
- [HTTPS와 TLS 기초](./https-tls-beginner.md): HTTP와 HTTPS의 차이, TLS 핸드셰이크, CA 인증서가 무엇인지를 입문자 관점에서 정리한 primer다. 전송 구간 보안이 왜 필요한지부터 잡고 [HTTPS / HSTS / MITM](./https-hsts-mitm.md) 심화로 이어지기에 좋다.
- `[primer]` [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md): HTTP 무상태성 때문에 로그인 상태를 유지하는 방법(서버 세션 vs JWT)과 쿠키 보안 속성(HttpOnly·Secure·SameSite)을 초보자 관점에서 정리한 primer다. [JWT 깊이 파기](./jwt-deep-dive.md)와 [네트워크 HTTP 상태·세션·캐시](../network/http-state-session-cache.md) 사이를 잇는 bridge 역할을 하면서, login loop reader를 [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 넘기는 beginner entrypoint다.
- `[primer]` [인증·인가·세션 기초 흐름](./authentication-authorization-session-foundations.md): authn / authz, session / cookie / JWT / BFF, login / logout, permission check를 browser page / SPA + BFF / bearer API 세 흐름으로 나눠 한 장에 정리한 beginner entrypoint primer다. 특히 `누구인가 -> 어떻게 전달하나 -> 무엇을 허용하나` 4질문, `인증 성공 신호 vs 인가 성공 신호` 30초 분리표, `30초 레이어 판별표`, `전송 실패 -> 인증 복원 실패 -> 인가 실패` 20초 디버깅 시작점, 한 요청 timeline 예시로 `401/403` 혼동을 빠르게 분리할 때 좋다.
- [비밀번호 저장 기초: 왜 해시를 써야 하나](./password-hashing-basics.md): 평문·가역 암호화·빠른 해시가 왜 부족한지, salt와 bcrypt가 무엇을 다르게 하는지를 입문자 관점에서 설명한다. [비밀번호 저장: bcrypt / scrypt / argon2](./password-storage-bcrypt-scrypt-argon2.md) 심화 전 기초 primer다.
- [XSS와 CSRF 기초](./xss-csrf-basics.md): `입력을 받아도 되나`를 묻는 문서가 아니라, 브라우저가 받은 화면과 로그인된 브라우저 요청이 왜 공격 표면이 되는지를 가르는 primer다. XSS는 `출력된 페이지에서 스크립트가 실행되는 문제`, CSRF는 `브라우저가 인증 쿠키를 자동 전송해 상태 변경 요청이 성립하는 문제`로 먼저 분리한 뒤 [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)로 내려가면 된다.
- [SQL 인젝션 기초](./sql-injection-basics.md): `입력 검증 일반론`이 아니라, 사용자 입력이 SQL 쿼리 문자열에 섞이면서 쿼리 구조 자체를 바꾸는 문제에 집중하는 primer다. `허용할 입력인가`보다 `쿼리 구조와 값을 분리했는가`를 먼저 보게 만들고, 다음 단계는 [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md)다.
- [CORS 기초](./cors-basics.md): 동일 출처 정책(SOP)과 CORS 에러가 왜 브라우저에서만 발생하는지, 그리고 beginner가 가장 자주 섞는 `OPTIONS-only` vs actual request, `request cookie 누락`, `응답은 왔지만 CORS로 JS가 못 읽는 상황`을 앞쪽 카드부터 갈라 주는 primer다. 새 `1분 체크 카드`가 먼저 `같은 path에 actual request가 실제로 보이는가`를 고정해 주고, actual request가 없으면 [Preflight Debug Checklist](./preflight-debug-checklist.md), actual request의 `Cookie` header가 비면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md), 응답 읽기 차단이면 [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md)로 바로 넘긴다.
- [Preflight Debug Checklist](./preflight-debug-checklist.md): browser console의 CORS 에러와 actual API `401`/`403`이 한 문장처럼 섞일 때 읽는 beginner bridge다. auth primer와 동일한 `Symptom-First Branch Table (CORS vs Auth)`로 `OPTIONS-only` vs actual request를 먼저 가르고, preflight lane과 auth lane을 섞지 않게 만든다. 두 문서 공통의 `30초 DevTools Network 미니 예시` 박스는 `예시 A: OPTIONS만 있고 actual request 없음`, `예시 B: actual POST가 실제로 보임`을 나란히 두어 `요청 method` -> `실제 요청 존재 여부` -> actual request의 `status` 순서가 왜 필요한지 바로 보여 준다.
- `[primer bridge]` [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md): `blocked Set-Cookie`, `stored but not sent`, `sent but anonymous`를 첫 15초에 갈라 주는 compact primer bridge다. `cookie 문제`를 한 덩어리로 보지 않게 만들고, 각 갈래마다 먼저 읽을 safe next-step 문서를 하나로 고정한 뒤에만 proxy, SameSite, Spring session, BFF deep dive로 내려가게 한다.
- `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md): beginner가 속성 표로 바로 뛰기 전에 `Application > Cookies`와 실패한 요청의 `Network > Request Headers > Cookie`를 먼저 비교하게 만드는 primer다. 새 `Application vs Network first check` checklist가 `저장됨`과 `전송됨`을 분리해 주고, 다 읽은 뒤에는 [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 바로 복귀하게 잡아 준다.
- `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md): login 뒤 다시 튀는 현상을 `same-name cookie 중복 전송`과 `proxy 뒤 wrong-scheme redirect / Secure cookie 미전송`으로 바로 갈라 주는 beginner handoff primer bridge다. `Application > Cookies` 화면만 보고 duplicate와 proxy를 섞지 않게 만들고, 실패한 요청 raw `Cookie` header와 redirect `Location` 중 무엇이 더 강한 증거인지 먼저 고정한 뒤 [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) 또는 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)로 넘긴다.
- `[primer bridge]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md): `credentials: "include"`, `Access-Control-Allow-Credentials`, cookie `Domain`/`Path`/`SameSite`가 한 문제처럼 섞일 때 읽는 beginner bridge다. 이번 정리로 문서 초반에 `Application > Cookies`와 같은 실패 요청의 `Network > Request Headers > Cookie`를 먼저 대조하는 `Application vs Network` 체크를 넣어, beginner가 request cookie 부재와 CORS 응답 읽기 실패를 같은 문제로 섞지 않게 했다. `origin`/`site`/`fetch credentials` 용어부터 흐리면 먼저 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)으로 들어가고, 여기서는 cross-origin fetch에서 cookie가 안 붙는지, CORS 응답 읽기에서 막힌 건지, cookie scope가 틀린 건지를 세 칸으로 나눈 뒤 같은 login-loop 복귀 사다리(`[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder))로 다시 올리게 만든다.
- [입력값 검증 기초](./input-validation-basics.md): `브라우저가 뭘 실행하나`나 `DB 쿼리가 어떻게 바뀌나`보다 먼저, 서버가 어떤 입력을 애초에 받지 말아야 하는지를 정하는 primer다. "서버는 클라이언트를 신뢰하지 않는다"는 원칙, 형식 검증·의미 검증·allowlist, Bean Validation을 입문자 관점에서 정리하고, 이후 DB query concat이 걱정되면 [SQL 인젝션 기초](./sql-injection-basics.md), 출력/브라우저 요청 흐름이 걱정되면 [XSS와 CSRF 기초](./xss-csrf-basics.md)로 갈라지면 된다.
- [대칭키·비대칭키 암호화 기초](./symmetric-asymmetric-encryption-basics.md): AES(대칭)와 RSA(비대칭)의 차이, 키 배포 문제, 디지털 서명, HTTPS가 두 방식을 결합하는 이유를 입문자 관점에서 정리한 primer다. [봉투 암호화와 KMS 기초](./envelope-encryption-kms-basics.md) 심화 전에 먼저 읽으면 좋다.
- [API 키 기초](./api-key-basics.md): API 키의 역할, 코드 하드코딩 금지와 환경 변수 보관, 키 노출 시 대응, API 키와 OAuth 토큰의 차이를 입문자 관점에서 정리한 primer다. API key vs session cookie vs OAuth token 비교표에 더해 `내 서버의 야간 배치가 외부 정산 API를 호출한다` 같은 `2문장 결정 예시`, `지금 API 키가 맞는가` 15초 선택표, `지금 막힌 문제에서 첫 행동` 20초 분기표, `sandbox/test key도 왜 시크릿처럼 다루나` 실제형 예시, `publishable/public key vs secret/server key` 30초 혼동 정리, provider 문구를 `public`, `publishable`, `client-side`, `server-side only`로 바로 해석하는 미니 가이드와 15초 판별 예시, `도메인/권한/기능` 기준으로 publishable key 허용 범위와 server secret 금지 사례를 한 표로 나눈 구분표, 새 `mini anti-pattern` 경고 박스로 브라우저 번들, DevTools, 로그가 왜 초보자 API 키 누출 경로가 되는지 한눈에 묶어 보여 준다. 이어서 `브라우저 직접 호출 vs 서버 대리 호출` 한 요청 비교, 언어별 `10줄 미만 안전 샘플(서버 대리 호출)` 바로 아래의 `배포 전 5항목 카드(env 주입, 로그 마스킹, 에러 바디 필터링, 타임아웃, 재시도)`와 새 `Node / FastAPI / Spring timeout 기본값 비교표`를 한 흐름으로 읽으면 초보자가 "내 서버 작업"과 "사용자 위임 호출"을 첫 단계에서 덜 섞고, "timeout을 controller에 거나 client에 거나?" 같은 복붙 실수도 줄일 수 있다. 이후 [OAuth2 기초](./oauth2-basics.md), [시크릿 관리·로테이션·누출 패턴](./secret-management-rotation-leak-patterns.md), [Webhook Sender Hardening](./webhook-sender-hardening.md), [Workload Identity vs Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md)로 내려가면 좋다.
- [시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유](./secrets-management-basics.md): `API 키를 고르는 문제`보다 먼저 `왜 코드/Git/application.properties에 넣으면 안 되나`, `env와 secret manager는 언제 갈라지나`를 잡는 beginner primer다. `시크릿은 코드 밖에서 관리하고 실행 시점에 주입한다`는 한 줄 mental model 위에 `.env`, 환경변수, cloud secret manager, Vault를 초보자용 표로 나누고, `private 저장소니까 괜찮다`, `application.properties는 코드가 아니다`, `한 번 유출되면 git history만 지우면 끝이다` 같은 흔한 오해를 먼저 걷어 낸다. 이후 외부 API 호출 자격 증명 선택은 [API 키 기초](./api-key-basics.md), 로그/예외 누출 경계는 [로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나](./log-masking-basics.md), 회전·유출 대응 운영은 [시크릿 관리·로테이션·누출 패턴](./secret-management-rotation-leak-patterns.md)으로 이어 가면 된다.
- [로그 마스킹 기초: Authorization 헤더와 에러 로그는 어디까지 가려야 하나](./log-masking-basics.md): `Authorization` header, 외부 API 에러 로그, 예외 메시지를 어디까지 가려야 하는지 초보자 관점에서 바로 보여 주는 primer다. `원인 파악용 필드`와 `재사용 가능한 비밀`을 분리하는 한 줄 기준 위에 `Authorization 헤더`, `외부 API 에러`, `DB 연결 실패`를 before/after 카드와 작은 비교표로 나란히 보여 주고, `prefix를 조금 남겨도 되나`, `stack trace를 그대로 찍어도 되나` 같은 흔한 혼동도 먼저 정리한다. 이후 [시크릿 관리 기초](./secrets-management-basics.md), [Secret Scanning / Credential Leak Response](./secret-scanning-credential-leak-response.md), [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)로 안전하게 이어진다.
- [브라우저 직접 호출 vs 서버 프록시 결정 트리](./browser-direct-call-vs-server-proxy-decision-tree.md): `CORS 때문에 프론트에서 직접 붙일까?` 같은 초보자 질문을 4단계로 빠르게 가르는 beginner bridge다. `server-side only`/`secret key` 문구, `CORS 때문에`라는 흔한 오판, `사용자 자신의 외부 데이터`인지 여부, `public/publishable + origin 제한`이 실제로 있는지를 순서대로 확인하게 만들어 첫 30초 안에 서버 프록시/BFF, OAuth, 제한된 브라우저 직접 호출 중 어디로 가야 하는지 정하게 돕는다.
- [API 키 vs OAuth vs Client Credentials 한 장 비교](./api-key-vs-oauth-vs-client-credentials-primer.md): `API 키면 되나`, `OAuth인데 사용자 로그인도 없나`, `Client Credentials가 뭐가 다른가`를 초보자 눈높이에서 한 표로 먼저 가르는 primer다. `누구를 대표해서 요청하나`라는 한 질문으로 API 키, 사용자 위임 OAuth, 서버-서버 OAuth를 분리해 주기 때문에 외부 API 첫 선택지가 섞일 때 바로 붙이기 좋다.

- `[primer]` [인증과 인가의 차이](./authentication-vs-authorization.md): authn / authz 경계가 섞일 때 먼저 잡는 primer다. `principal`, `session`, `permission model`의 최소 단위를 같이 정리해 두면 이후 authz / tenant 계열 deep dive로 내려가기 좋다.
- `[primer bridge]` [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md): authn을 이해한 직후 `왜 403인지`를 role/permission, scope, ownership 4단계 gate로 짧게 연결해 주는 beginner primer bridge다. 이번 보강으로 `내 것만 되는데 남의 것은 왜 안 되는지`도 같은 표 안에서 object gate로 붙여, response-code primer와 role/scope/ownership primer 사이를 더 촘촘히 왕복하게 했다.
- `[primer]` [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md): `role check`, OAuth `scope`, 객체 `ownership`이 서로 다른 질문이라는 점을 짧게 분리해 주는 beginner primer다. `scope=orders.read`가 모든 주문을 뜻하지 않고, `내 것만 되는데 남의 것은 안 됨`이 ownership/tenant 축이라는 점을 먼저 정리한 뒤 IDOR / deeper authz로 내려가기에 좋다. 이번 정리로 컨트롤러/서비스 레이어에서 `내 요청 성공`과 `남의 객체 거부`를 같이 묶는 최소 ownership 테스트 패턴, 그리고 multi-tenant에서 `owner 맞음`만으로는 부족하고 `tenant + ownership`을 함께 봐야 한다는 미니 케이스까지 바로 이어서 볼 수 있다.
- `[intermediate bridge]` [리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant](./resource-level-authz-decision-practice.md): primer에서 용어를 분리한 다음, 실제 요청을 `action gate`와 `resource gate`로 나눠 읽는 연습용 bridge다. `같은 token인데 어떤 id만 안 됨`, `same user different tenant`, `support read는 되는데 approve는 안 됨` 같은 문장을 표와 연습 카드로 묶어, junior가 role/scope/ownership/tenant를 실제 decision table로 바꾸게 돕는다.
- `[primer]` [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md): external token의 `aud`, OAuth `scope`, 서비스 내부 permission이 서로 다른 boundary라는 점을 multi-service 관점에서 정리하는 primer다. `scope는 있는데 왜 이 API가 token을 안 받지`, `aud도 맞는데 왜 403이지` 같은 질문을 audience -> scope -> app permission 순서로 끊어 읽게 맞춰 두었다.
- `[primer]` [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md): JWT claim, role, Spring authority, application permission이 서로 다른 층위라는 점을 초보자 관점에서 정리한 primer다. `JWT는 valid한데 Spring 403`, `claim은 있는데 authority가 비어 있음`, `roles/scope/ROLE_/hasRole이 다 섞임` 같은 증상 문장으로 들어올 때 바로 읽으면 좋다.
- `[deep dive]` [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md): JWT는 valid한데 Spring route / method security에서만 `403`이 나는 상황을 디버깅하는 deep dive다. `claim은 있는데 authority가 비어 있음`, `ROLE_/SCOPE_ mismatch`, `JwtAuthenticationConverter`, `hasRole`, `hasAuthority` mismatch를 실제 authority 문자열 기준으로 좁힌다.
- `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md): 로그인된 session이 살아 있어도 role, permission, tenant membership이 바뀌면 old claim이 낡을 수 있다는 점을 초보자 관점에서 정리한 first-step primer다. revoke, grant, tenant 이동 symptom을 처음 분해할 때 여기서 출발한 뒤 필요한 쪽의 `[primer bridge]`로 갈라지면 된다.
- `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md): role/permission change가 source of truth에서 끝난 뒤 JWT claim, server session principal, authz cache, revoke plane으로 각각 어떻게 전파되는지 한 장의 timeline으로 묶어 주는 primer bridge다. `old authority가 왜 아직 남는가`를 층별로 분해한 뒤 `[deep dive]` [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md)로 이어지기 좋다.
- `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md): source of truth에서는 grant가 끝났는데 request path에서는 old claim이나 stale deny cache 때문에 `403`이 남을 수 있다는 점을 beginner/intermediate 관점에서 정리한 primer bridge다. `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)로 기초 축을 먼저 맞춘 뒤 `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)로 handoff하기 좋다.
- `[primer bridge]` [Authority Transfer vs Revoke Lag Primer Bridge](./authority-transfer-vs-revoke-lag-primer-bridge.md): `authority transfer`, `deprovision tail`, `backfill is green but access tail remains`, `revoke lag`, `logout still works`가 beginner 질문에서 한 덩어리로 섞일 때 읽는 splitter다. cleanup/parity 질문은 authority-transfer route로, old session/token/cache acceptance tail은 revocation route로 먼저 갈라서 sibling README와 incident deep dive의 owner를 안전하게 고정한다.
- `[primer bridge]` [Auth Observability Primer Bridge](./auth-observability-primer-bridge.md): `missing-audit-trail`, `decision log missing`, `auth-signal-gap`처럼 observability/evidence symptom이 먼저 보일 때 `signal -> decision -> audit` 3칸 mental model을 먼저 고정하는 beginner bridge다. 이후 `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md), [AuthZ Decision Logging Design](./authz-decision-logging-design.md), [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)로 안전하게 handoff할 수 있다.
- `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md): org/team/tenant 이동이 단순 selector 변경이 아니라 active tenant, membership snapshot, derived scope를 refresh해야 하는 session coherence 문제라는 점을 짧게 정리한 primer다. 문서 안의 beginner 분기표에서 `grant는 끝났는데 403`(grant freshness)와 `old tenant 문맥이 남음`(context freshness)을 먼저 갈라 다음 문서를 고르게 만들고, 마지막에 [security 카테고리 README](./README.md#기본-primer)와 [Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 복귀하도록 연결해 둔다.
- `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md): 이 route의 response-code `[primer]`다. preflight checklist와 동일한 `Symptom-First Branch Table (CORS vs Auth)`로 먼저 `OPTIONS-only`인지 actual request인지 분기한 뒤, `401` / `403` / `404`를 authn failure, authz deny, concealment `404`로 읽게 만든다. 두 문서 공통의 `30초 DevTools Network 미니 예시` 박스는 `예시 A: OPTIONS만 있고 actual request 없음`, `예시 B: actual POST가 실제로 보임`을 나란히 두고 `status` 숫자를 마지막에 읽는 습관을 바로 심어 준다. 이번 정리는 authz primer 쪽의 실제 진입 문장도 맞췄다. `로그인 됐는데 왜 403`, `토큰은 유효한데 403`, `scope 있는데 남의 주문 못 봄`, `내 것만 되는데 남의 것은 안 됨`, `남의 주문 조회하면 왜 404` 같은 한국어 질문을 바로 `401/403/404` 해석과 다음 primer bridge로 연결한다. 이후 `첫 읽기 90초 경로`, `재로그인 vs 권한요청 vs ID 재확인` 15초 결정 흐름, `actual 요청 결과인지 먼저 확인` 20초 선행 확인표에 더해 `4단계 gate 기준 30초 분기표(AuthN -> Role/Permission -> Scope -> Ownership/Tenant)`로 첫 진단 순서를 고정해 오해를 줄인다. browser redirect로 읽히면 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md), 다른 사람 리소스 concealment면 `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md), stale `403` / cached concealment `404`면 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) 순으로 handoff하면 된다.
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md): 브라우저 page redirect와 raw API `401`을 같은 뜻으로 읽지 않도록 돕는 primer bridge다. Spring deep dive로 내려가기 전에 `SavedRequest` redirect memory, missing-cookie/scope, server session/BFF mapping을 작은 증상표로 먼저 갈라 준다. 이번 보강으로 `Application > Cookies`와 같은 실패 요청의 `Network > Request Headers > Cookie`, 그리고 `status`/`Location`을 3단계로 대조하는 `Application vs Network 15초 미니 체크`가 들어가, beginner가 `cookie 있는데 왜 다시 로그인하지`를 `stored but not sent`와 `sent but anonymous`로 더 빨리 나누게 했다. [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)으로 browser 저장/복귀 흐름을 먼저 잡은 뒤, `SavedRequest`, session cookie, login loop를 Spring deep dive로 넘길 때 붙인다.
- [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md): DevTools의 `This Set-Cookie was blocked...` 같은 문구를 beginner 관점에서 `Secure`, `SameSite`, `Domain`, `Path` 네 칸으로 번역해 주는 entrypoint primer다. response cookie rejection과 next-request omission을 분리한 뒤, beginner가 바로 `proxy`, `cross-site`, `cookie scope` 중 한 갈래만 고르고 다시 troubleshooting path로 복귀하도록 handoff를 정리해 둔다.
- [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md): `Application` 저장값과 `Network`의 request `Cookie` header를 같은 실패 요청 기준으로 먼저 대조하게 만드는 beginner primer다. 특히 `auth.example.com`에 저장된 cookie가 `app.example.com` 요청에는 안 붙는 한 줄 subdomain 예시를 함께 두어 "저장됨 vs 전송됨"을 먼저 분리하게 만든다. 그다음 `Domain`, `Path`, `SameSite`, host-only cookie, subdomain mismatch와 server session/BFF mapping 갈래를 안전하게 나누고, 같은 login-loop 복귀 사다리(`[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder))로 되돌아가 다음 갈래를 고르게 만든다.
- `[follow-up primer bridge]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md): session cookie scope를 `/app -> /`나 host-only -> shared domain으로 옮긴 뒤, 이미 `old row가 남았다`는 증거나 duplicate detour가 잡힌 상태에서 여는 cleanup 설계 문서다. broad entrypoint로 바로 열기보다 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)나 [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md) 다음 단계로 두고, old scope마다 exact `Domain`/host-only 방식과 `Path`를 다시 맞춰 tombstone을 보내야 한다는 점을 cleanup matrix로 바로 설명한다.
- [SameSite Login Callback Primer](./samesite-login-callback-primer.md): `same-origin`, `same-site`, `cross-site` 용어가 social login callback, sibling subdomain handoff, partner iframe에서 한 덩어리처럼 섞일 때 읽는 beginner bridge다. 한 login flow 안에 external IdP -> callback의 cross-site 구간과 `auth -> app` handoff의 same-site 구간이 같이 들어올 수 있다는 점을 먼저 분리해 준다.
- [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md): `auth.example.com/callback`은 성공했는데 `app.example.com` 첫 요청이 anonymous일 때, shared-domain cookie scope를 기대한 구조인지 one-time handoff 뒤 app-local session을 만드는 구조인지 먼저 가르는 작은 beginner chooser다. deep dive로 바로 뛰지 않고 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) 또는 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) 중 안전한 다음 문서 하나만 고르게 만든다.
- `[primer bridge]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md): external IdP callback, social login, partner portal iframe, embedded login에서만 cookie가 안 붙는데 proxy `X-Forwarded-Proto` mismatch와 구분이 안 될 때 읽는 beginner bridge다. `redirect가 HTTP로 꺾이는지`를 첫 분기점으로 두고, browser의 cross-site cookie 전송 실패(`SameSite`)와 app/proxy의 HTTPS 인식 실패를 초반에 분리한다. follow-up은 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md) 중 하나만 고른 뒤 [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 복귀하게 맞춰져 있다.
- `[follow-up]` [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md): `SameSite=None; Secure`까지 맞췄는데도 partner iframe, embedded login, in-app browser 안에서만 세션이 계속 빠질 때 읽는 beginner follow-up이다. "cookie 속성이 틀린가"와 "브라우저가 modern third-party cookie/privacy 정책으로 embedded login 자체를 제한하는가"를 분리하고, top-level login 우회가 먼저인지 browser-specific 설계 검토가 먼저인지 고르게 만든다.
- `[primer bridge]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md): `auth.example.com/callback`은 성공인데 `app.example.com` 첫 요청이 anonymous일 때 `Domain`, `SameSite`, session handoff를 세 칸으로 끊어 보는 beginner bridge다. shared parent-domain session과 one-time handoff 패턴을 비교해서 "auth cookie가 안 간다"와 "app session이 안 생겼다"를 덜 섞게 해 준다.
- `[follow-up primer]` [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md): generic login-loop 첫 문서가 아니라, raw `Cookie` header 중복이나 route별 stale cookie detour가 이미 잡힌 뒤 여는 follow-up primer다. 같은 이름의 session cookie가 서로 다른 `Domain`/`Path`로 공존할 수 있고, 특정 route나 subdomain에서 stale cookie가 shadowing하며 login loop를 만든다는 점을 beginner 관점에서 풀어 준다. detour를 끝낸 뒤에는 `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) 순서의 3단계 복귀 사다리도 함께 제공한다.
- `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md): 브라우저는 HTTPS인데 app은 proxy 뒤 HTTP로 착각하는 순간 `Secure` cookie, TLS termination, `X-Forwarded-Proto` mismatch 때문에 왜 login cookie가 안 남는 것처럼 보이는지 초보자 관점에서 정리한 primer다. 문서 맨 위 `20초 chooser`가 먼저 `redirect가 http로 꺾이는 proxy scheme drift`와 `redirect는 HTTPS인데 cookie scope만 어긋나는 경우`를 갈라 주므로, beginner가 wrong-scheme 단서를 놓친 채 `Domain`/`Path` 표만 붙들지 않게 만든다. [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)와 [HTTPS / HSTS / MITM](./https-hsts-mitm.md) 사이를 잇는 bridge이며, detour 뒤에는 `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) 순서로 복귀하게 맞춰져 있다.
- `[primer]` [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md): proxy/LB 뒤에서 앱이 absolute URL을 만들 때 `X-Forwarded-Host`, host preservation, public base URL이 어긋나 post-login `Location`이나 OAuth callback URL이 wrong origin으로 바뀌는 문제를 beginner 관점에서 정리한 primer다. `60초 분기표`, 10초 판별표, `wrong origin vs secure-cookie/scheme 문제 vs open redirect` 20초 혼동 분리표에 더해 `초보자 실수 패턴 3개와 즉시 수정 포인트` 표로 원인 축을 먼저 좁히고 다음 문서를 분기하기 좋으며, detour 뒤 primer 복귀 사다리를 동일하게 제공한다.
- `[primer]` [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md): `X-Forwarded-*`가 "header 값"이 아니라 "known proxy가 관찰해 다시 쓴 값"일 때만 의미 있다는 점을 beginner 관점에서 정리한다. `X-Forwarded-Proto`로 redirect/cookie scheme이 꼬이거나 `X-Forwarded-For`로 client IP, rate limit, audit, IP allowlist가 흔들리는 상황을 한 번에 분리한 뒤, follow-up을 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) 또는 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md) 한 장으로 제한하고 catalog 복귀 경로까지 같이 제공한다.
- `[primer]` [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md): browser/server session 모델과 token 보관 전략의 기본 축을 잡는 primer다. 이후 [Browser / Session Coherence](#browser--session-coherence), session coherence, browser / BFF boundary catalog로 이어진다.
- `[primer]` [OAuth2 기초](./oauth2-basics.md): OAuth2가 "로그인" 자체가 아니라 제한된 권한 위임이라는 점을 먼저 분리하는 beginner primer다. `사용자 캘린더/드라이브 데이터를 읽는다` 같은 `2문장 결정 예시`로 API 키와 OAuth의 첫 분기를 실제 시나리오로 빠르게 고를 수 있고, 이번 정리로 `consent screen 이후 외부 토큰 확인 -> 내부 계정 매핑 -> 우리 서비스 session cookie 발급` 예시가 추가돼 social login에서 외부 토큰과 내부 세션이 어디서 갈라지는지 한 번에 잡을 수 있다. access token, scope, authorization server 용어가 흐리면 이 문서를 먼저 보고 Authorization Code Grant로 내려가면 된다.
- `[primer bridge]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md): `구글로 로그인` 질문에서 OAuth2/OIDC, `access token`/`id token`, 내부 session 역할이 아직 섞일 때 보는 beginner handoff primer다. 이 문서를 거치면 social login 질문이 곧바로 callback hardening deep dive로 튀지 않고, [OAuth2 기초](./oauth2-basics.md), [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md), [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) 중 다음 문서를 고르기 쉬워진다.
- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md): [OAuth2 기초](./oauth2-basics.md)와 [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)까지 읽은 뒤, authorization flow와 token 발급 경로를 실제 login/callback 흐름으로 복습하는 follow-up 문서다. 이후 [Browser / Session Coherence](#browser--session-coherence), browser / BFF, service / delegation boundary deep dive로 이어지고, callback/login-completion failure mode는 [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)와 [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)로 이어서 보면 된다. 다만 질문이 `CLI 로그인`, `TV 코드 입력`, `브라우저 없는 기기 승인`이면 이 문서를 mainline으로 타지 말고 `[primer bridge]` [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md)에서 시작한다. front-channel request hardening은 `[primer bridge]` [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md), server-side token endpoint client proof 선택은 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)로 분기해서 보면 된다.

아래 구간은 설명 본문이 아니라 theme별 `deep dive catalog`다. 순서대로 읽는 `survey`가 아니라, 문제 축에 맞는 개별 문서를 고르는 index로 보면 된다. mixed catalog에서 `[playbook]`, `[runbook]`, `[drill]`, `[incident matrix]`는 서로 다른 incident badge다. 각각 live triage, repeatable operation, rehearsal/validation, blast-radius routing을 뜻하고, 기준은 [Navigation Taxonomy의 Incident Badge Vocabulary](../../rag/navigation-taxonomy.md#incident-badge-vocabulary)를 따른다. `[recovery]` 라벨은 outage/degradation incident를 직접 다루지만 full step runbook은 아닌 incident-oriented recovery deep dive라는 뜻이다. mixed incident catalog에서는 incident badge 문서 옆에 놓인 개념 본문도 bare link로 두지 않고 `[deep dive]` cue를 붙인다. badge가 없는 pure deep-dive-only catalog에서는 필요할 때만 bare link를 유지한다.

<a id="운영--incident-catalog"></a>
## 운영 / Incident catalog (`playbook` / `runbook` / `drill` / `recovery`, follow-up)

이 구간은 incident 대응 순서가 먼저 필요한 `playbook`, repeatable operator 절차인 `runbook`, rehearsal 중심 `drill`, 분류표 역할의 `incident matrix`, 그리고 recovery-oriented `deep dive`를 함께 묶은 incident-first catalog다.
즉, 이 섹션은 security beginner entrypoint가 아니라 follow-up bucket이다. `처음`, `헷갈려요`, `why 403`, `cookie 있는데 왜 다시 로그인` 계열이면 먼저 [기본 primer](#기본-primer)나 [증상별 바로 가기](#증상별-바로-가기)로 돌아간다.

| 지금 먼저 필요한 것 | 여기서 시작해도 되나 | 더 안전한 이전 shelf |
|---|---|---|
| live incident triage, outage containment, key rotation recovery | yes | 없음. 이 섹션이 맞는 first click일 수 있다 |
| broad security basics, `로그인은 됐는데 왜 403`, `cookie 있는데 왜 다시 로그인` | no | [기본 primer](#기본-primer), [증상별 바로 가기](#증상별-바로-가기) |

- `[playbook]` [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
- `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
- `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md)
- `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md)
- `[runbook]` [Key Rotation Runbook](./key-rotation-runbook.md)
- `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
- `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)
- `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
- `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
- `[deep dive]` [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
- `[deep dive]` [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)
- `[deep dive]` [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
- `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
- `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md)
- `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
- `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
- `[deep dive]` [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)

## Hardware Trust / Recovery deep dive catalog

- `[deep dive]` [Hardware-Backed Keys / Attestation](./hardware-backed-keys-attestation.md)
- `[recovery]` [Hardware Attestation Policy / Failure Recovery](./hardware-attestation-policy-failure-recovery.md)
- `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
- `[deep dive]` [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)

## Session Coherence / Assurance deep dive catalog

- beginner route는 먼저 `[primer]` / `[primer bridge]`로 session freshness mental model을 열고, revoke tail 같은 symptom이 남을 때 `[deep dive]`로 내려간다.
- `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
- `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md)
- `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
- `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- `[deep dive]` [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
- `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md)
- `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
- `[deep dive]` [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
- `[deep dive]` [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md)
- `[deep dive]` [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
- `[deep dive]` [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
- `[deep dive]` [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)
- `[deep dive]` [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
- `[deep dive]` [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md)
- `[deep dive]` [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md)
- `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
- `[deep dive]` [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md)
- `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)

<a id="browser--session-coherence"></a>
## Browser / Session Coherence

브라우저 symptom으로 들어온 auth/session 질문의 canonical entrypoint다.
초보자 기준 mental model은 세 칸이면 충분하다. `브라우저가 cookie를 저장/전송했나 -> redirect가 원래 URL로 잘 복귀했나 -> cookie는 갔는데 서버/BFF가 session을 복원했나`.
`302`/login-loop와 revoke tail을 같은 묶음에서 받되, 아래 troubleshooting path에서는 위 세 칸을 기준으로 `saved request / hidden session` 문제와 `revocation propagation` 문제를 먼저 갈라 본다.
redirect 검증, callback 이후 세션 재발급, frame/script 정책, browser-visible credential 축을 한 번에 잡고 싶으면 아래 browser/server boundary catalog와 `Session / Boundary / Replay` bridge bullet을 같이 보면 된다.

<a id="browser--session-beginner-ladder"></a>
### Browser / Session Beginner Ladder

초보자용 safe route는 `primer -> primer bridge -> deep dive` 한 줄로 기억하면 된다. browser/session 표에서 `safe next step`은 primer bridge를 고르는 단계다. primer bridge를 거치기 전에는 Spring deep dive나 system-design recovery로 바로 내려가지 않는다.
첫 클릭 정확도를 높이려면 30초 카드 전에 질문 하나를 먼저 고정한다. login 직후 `Location`이 public `https` origin인가, 아니면 `http://...`/wrong host로 이미 틀어졌는가. `Location`이 틀리면 cookie 표보다 먼저 [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md)으로 가고, 읽은 뒤에는 이 anchor나 [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 돌아온다.
login loop를 막 만났다면 30초짜리 starter card부터 본다. `Status`/`Location`으로 `redirect 기억`, request `Cookie` header로 `cookie 전송`, cookie를 보냈는데도 익명이면 `server 복원`으로 자르는 3-step card는 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md#30초-3-step-체크-카드)에 있다. 그다음 20초 공통 표로 좁힌다. `302 + /login`이면 `기억 / redirect`, `Application`에는 있는데 request `Cookie` header가 비면 `전송 / cookie-not-sent`, request `Cookie` header가 붙었는데도 계속 anonymous면 `조회 / server-anonymous`다. 세 갈래의 canonical mini decision matrix는 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md#20초-트리아지-결정표)와 [Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md#20초-트리아지-결정표)에 같은 wording으로 재사용한다.
logout 계열은 같은 표의 바깥에 따로 둔다. `OIDC logout tail`, `logout tail`, `revoke tail`은 login-loop branch가 아니라 `session-tail / revocation propagation` beginner ladder로 정규화하고, first hop은 항상 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)다.

| 단계 | 지금 맞출 mental model | 먼저 볼 문서 | 다음 안전한 한 걸음 |
|---|---|---|---|
| `primer` | cookie/session/JWT가 어디에 저장되고 redirect 응답이 무엇을 남기는지 | `[primer]` [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md), `[primer]` [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md), `[primer]` [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md), `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md), `[primer]` [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) | social login 문맥이면 `[primer]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md), browser 저장 vs 서버 상태 저장의 비교가 더 필요하면 `[primer]` [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md), flow 복습이 필요하면 `[primer]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) |
| `primer bridge` | raw `401`과 browser `302 -> /login`을 같은 뜻으로 읽지 않기. `Application` 저장값, request `Cookie` header, `status`/`Location`을 3단계로 나눠 본다 | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | 아래 `[deep dive]` 세 갈래 중 하나만 고른다 |
| `deep dive` | 저장/전송, redirect, server persistence 중 어느 층이 깨졌는지 | request `Cookie` header가 비면 `cookie transfer`(`cookie-not-sent`, `stored but not sent`)로 보고 먼저 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `cookie-header gate`로 같은 실패 요청의 `Application` 저장값과 request `Cookie` header를 맞춘 뒤 `[deep dive]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 내려간다. `Secure` 전달이나 proxy 종료 지점이 의심되면 `[deep dive]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), cookie는 실리는데 계속 anonymous면 `server persistence / session mapping`(`server-mapping-missing`, `sent but anonymous`)으로 보고 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) | 갈래를 잃으면 `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 돌아온다 |

자주 섞이는 문장:

- `Application > Cookies`에 값이 보인다 != 다음 request `Cookie` header가 실린다.
- raw API `401` != 브라우저 page redirect `302 -> /login`.
- cookie가 실린다 != 서버 session이나 BFF token translation이 살아 있다.
- `hidden session mismatch`는 원인명이 아니라 묶음 alias다. 첫 분기는 `cookie-not-sent`(전송)인지 `server-mapping-missing`(조회)인지다.

- DevTools `Cookies` 탭이 이미 `This Set-Cookie was blocked...` reason을 보여 주는데 그 문구를 어떻게 읽어야 할지 막히면 [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)에서 `Secure`, `SameSite`, `Domain`, `Path` 네 축으로 먼저 번역한다. response rejection인지, 저장은 됐는데 next request omission인지부터 분리하면 이후 handoff가 훨씬 쉬워진다.
- 같은 이름 cookie가 여러 줄 보이거나 `Cookie: session=...; session=...`처럼 중복 전송되면 `[follow-up primer]` [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)으로 좁힌다. 단, raw header 중복이 아직 확인되지 않았으면 broad 첫 hop은 이 문서가 아니라 `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md)다.
- callback trace에서 one-time 확인용 cookie와 main session cookie가 둘 다 `session`처럼 보여 "같은 이름인데 왜 역할이 다르지?"가 먼저 막히면 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)에서 callback 검증용인지 이후 로그인 유지용인지부터 자른다. 거기서 external IdP callback failure면 [SameSite Login Callback Primer](./samesite-login-callback-primer.md), `auth -> app` handoff 뒤 anonymous면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md), raw `Cookie` header 중복이면 [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)으로 이어 간다.
- session cookie scope를 넓히거나 좁힌 배포 직후에 old cookie가 route별로 남고 어떤 tombstone을 보내야 할지 막히면 `[follow-up primer bridge]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)에서 host-only vs `Domain`, `Path` migration cleanup을 정리한다. broad login-loop 첫 hop으로 바로 열기보다 먼저 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) 또는 `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md)에서 전송/중복 갈래를 고정한다.
- `auth.example.com/callback`은 성공하는데 `app.example.com` 첫 요청이 anonymous이고, shared parent-domain session인지 one-time handoff인지부터 헷갈리면 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)에서 먼저 구조를 한 줄로 고른다. shared cookie 기대면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff 기대면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 내려가고, external IdP 경유에서만 깨지면 `SameSite` 쪽으로 좁힌다.
- cross-origin `fetch`에 `credentials: "include"`를 넣었는데도 cookie가 비거나, `Access-Control-Allow-Credentials`를 cookie 전송 설정처럼 읽고 있다면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)에서 request option, CORS credential policy, cookie scope를 먼저 분리한다.
- external IdP callback, social login, partner portal iframe, embedded login 경로에서만 cookie가 안 붙고 redirect는 계속 `https://...`라면 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)에서 `SameSite=None; Secure`가 필요한 cross-site cookie failure인지, proxy `X-Forwarded-Proto` mismatch인지 먼저 분리한다. `SameSite=None; Secure`까지 맞췄는데도 iframe 안에서만 계속 실패하고 새 탭에서는 되면 [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md)로 이어 가서 modern third-party cookie/privacy control 장면인지 확인한다.
- login은 HTTPS로 시작했는데 proxy/LB 뒤에서만 cookie가 안 남거나 login 직후 `Location`이 `http://...`로 바뀌면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)에서 `Secure` cookie, TLS termination, `X-Forwarded-Proto` mismatch를 먼저 확인한다.
- login 직후 `Location`이나 OAuth `redirect_uri`가 `app-internal`, `localhost`, staging host처럼 wrong origin으로 바뀌면 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)에서 `X-Forwarded-Host`, host preservation, public base URL을 먼저 확인한다.
- `X-Forwarded-Proto`, `X-Forwarded-For`, `Forwarded`가 등장하고 redirect scheme, client IP, rate limit, IP allowlist가 한꺼번에 흔들리면 [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md)에서 "무슨 헤더인가"보다 "어느 known proxy가 썼는가"를 먼저 분리한다.
- front-channel login completion hardening은 `[deep dive]` [Open Redirect Hardening](./open-redirect-hardening.md), `[deep dive]` [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), `[deep dive]` [Session Fixation in Federated Login](./session-fixation-in-federated-login.md), `[deep dive]` [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)를 먼저 묶어 보면 된다.
- browser/server credential translation은 `[deep dive]` [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md), `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 이어 읽으면 된다.

<a id="browser--session-troubleshooting-path"></a>
### Browser / Session Troubleshooting Path

#### Boundary Ladder Summary

긴 bullet을 다 읽기 전에 아래 표에서 한 줄 route만 먼저 고른다. beginner 기본 규칙은 system-design handoff와 같은 `catalog -> primer -> primer bridge -> deep dive -> recovery / system design` 순서다. 여기서 `primer`는 mental model, `primer bridge`는 safe next step, `deep dive`는 원인 축소, `recovery`는 운영 복구, `[system design]`은 control-plane/session-store handoff를 뜻한다.
browser/session naming도 system-design 쪽과 맞춘다. 초보자에게 먼저 보이는 normalized route label은 `SavedRequest`, `cookie-missing`, `server-anonymous`, `session-tail / revocation propagation`이고, 기존 `cookie-not-sent`, `server-mapping-missing`은 retrieval 별칭으로만 남긴다.

redirect mismatch에서는 `cookie`보다 `Location`을 먼저 읽는다. 첫 질문은 "`Location`이 `http://...`로 꺾였는가, 아니면 `https://...`인데 host/origin만 틀렸는가"다. 이 1차 분기에서는 [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md)을 먼저 열고, 다 읽은 뒤에는 이 anchor나 [Browser / Session Beginner Ladder](#browser--session-beginner-ladder)로 돌아온다.

| 초보자 첫 클릭 | 바로 여는 문서 | 복귀 경로 |
|---|---|---|
| login 직후 `Location`이 public `https` origin인지 자신 없다 | [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md) | [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) |
| `Location`은 정상이고 다음 요청부터 다시 anonymous다 | 아래 route 표에서 `cookie-missing` / `server-anonymous` row를 고른다 | 같은 anchor에서 계속 본다 |

| 증상 시작점 | 먼저 여는 `primer` | `primer bridge` / safe next step | `deep dive` | `recovery` | category 복귀 anchor |
|---|---|---|---|---|---|
| `login loop`, `SavedRequest`, `401`/`302`가 섞임 (`SavedRequest` / `redirect / navigation memory`) | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) - 문서 앞쪽 FAQ에서 `왜 브라우저는 /login으로 가고 API는 raw 401인가`를 먼저 정리 | `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) | `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) | `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) |
| `cookie-missing` 또는 `server-anonymous`가 의심됨 (`cookie transfer` / `server persistence / session mapping`) | `[primer]` [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md) | 먼저 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `cookie-header gate`로 같은 실패 요청의 `Application` 저장값과 request `Cookie` header를 맞춘다. request `Cookie` header가 비면 `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md)나 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 좁힌다 | `server-anonymous`가 확인되면 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) | `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) | `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) |
| `SameSite=None; Secure`까지 맞췄는데 iframe/embedded login에서만 계속 anonymous (`cross-site cookie` / `embedded privacy controls`) | `[primer]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) | `[primer bridge]` [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md) - top-level 탭에서는 되는지, 브라우저 privacy mode 차이가 있는지 먼저 확인 | `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md) | 없음 | `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) |
| login 뒤 redirect가 틀리는데 `http://...`인지 wrong host인지 먼저 헷갈림 (`redirect scheme` / `wrong origin`) | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) | `[primer bridge]` [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md) | `[deep dive]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), `[deep dive]` [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md) | `[recovery]` [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md) | `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) |
| `logout still works`, revoke tail, role/claim 반영 지연 (`session-tail / revocation propagation`) | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) | `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md), `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md) | `[recovery]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md), `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](../system-design/revocation-bus-regional-lag-recovery-design.md) | `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) -> `[catalog]` [Session Coherence / Assurance deep dive catalog](#session-coherence--assurance-deep-dive-catalog) |

- `왜 로그인 상태가 유지되는지`부터 다시 잡아야 하면 [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)에서 cookie / session / JWT의 최소 그림을 먼저 맞춘 뒤 여기로 돌아와 symptom triage를 시작한다.
- `cookie`, `session`, `JWT`는 아는데 `SavedRequest`, `hidden JSESSIONID`, `SecurityContextRepository`가 갑자기 등장해 문장이 안 읽히면 먼저 [Browser / Session Beginner Ladder](#browser--session-beginner-ladder)만 따라간다. `primer bridge` 이후에도 server-side persistence 문맥이 비면 `[deep dive]` [Spring Security 아키텍처](../spring/spring-security-architecture.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 내려가 cookie 자동 전송, redirect 응답의 저장/복귀, hidden session 생성, Spring persistence, browser/BFF token translation 축을 맞춘다.
- `SavedRequest`, `saved request bounce`, `원래 URL 복귀`, `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음`, `hidden session`, `hidden JSESSIONID`, `hidden session mismatch`, `cookie-not-sent`, `server-mapping-missing`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login`이 먼저 보이면 [Browser / Session Beginner Ladder](#browser--session-beginner-ladder)의 `primer bridge` row부터 시작한다. beginner-safe rule은 간단하다: **Spring deep dive 전에 safe next doc은 항상 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)** 다. 그 guide에서 redirect/navigation memory 쪽이면 `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)로, request `Cookie` header가 비는 쪽은 normalized label `cookie-missing`으로 보고 먼저 `cookie-header gate`로 같은 실패 요청의 `Application` 저장값과 request `Cookie` header를 묶어 확인한 뒤 beginner label `cross-origin fetch / subdomain scope confusion`으로 읽고 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) -> 필요하면 `[primer]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)로, cookie는 실리는데 서버 세션이나 token translation이 사라졌으면 normalized label `server-anonymous`로 보고 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) -> `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge) 순서로 좁힌다. 기존 `cookie-not-sent`, `server-mapping-missing`은 retrieval alias로만 읽는다. system-design 원인까지 내려가야 하면 그 bridge 안에서도 `[primer]` [System Design: Stateless Sessions Primer](../system-design/stateless-sessions-primer.md) -> `[primer bridge]` [System Design: Browser BFF Session Boundary Primer](../system-design/browser-bff-session-boundary-primer.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) -> `[system design]` [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md) 순서로 role cue를 다시 반복한다.
- `토큰 valid인데 왜 403`, `token valid but 403`, `로그인됐는데 이 API만 403`가 먼저 보이면 browser/session ladder로 바로 가지 않는다. beginner-safe first hop은 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) -> `[primer bridge]` [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)다. 여기서 `role/scope/ownership` 축을 먼저 고정한 뒤에만 stale deny면 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로, tenant/context 문맥이면 `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)로 내려간다.
- raw `Cookie` header에서 `session=...; session=...`처럼 같은 이름이 두 번 보이거나, `Application > Cookies`에 같은 이름이 서로 다른 `Domain`/`Path`로 여러 줄 남아 있으면 `[follow-up primer]` [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)에서 stale cookie shadowing 가능성을 먼저 제거한다. 이 문서는 duplicate detour용이지 broad 첫 hop은 아니다. duplicate를 정리한 뒤 raw `Cookie` header가 아예 비면 먼저 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `cookie-header gate` wording으로 같은 실패 요청을 다시 맞춘 다음 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로, header에는 session 하나가 실리는데도 계속 anonymous면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로, redirect host/scheme이 꺾이면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) 또는 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)로 이어 간다. 갈래를 다시 잃으면 이 anchor로 돌아온다.
- callback flow에서 cookie 이름은 같은데 callback 직후 400/loop와 app 첫 요청 anonymous가 한 문제처럼 섞이면 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)에서 callback 확인용 cookie와 main session cookie를 먼저 분리한다. 역할을 나눈 뒤 external IdP callback failure는 [SameSite Login Callback Primer](./samesite-login-callback-primer.md), `auth -> app` handoff failure는 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md), actual duplicate 전송은 [Duplicate Cookie Name Shadowing](./duplicate-cookie-name-shadowing.md)으로 내려간다.
- scope migration 직후 old cookie가 계속 남아 cleanup header를 어떻게 짜야 할지 막히면 `[follow-up primer bridge]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)에서 old scope별 tombstone을 맞춘다. 이 문서는 `cleanup 설계`가 남았을 때 여는 후속 문서다. host-only old cookie라면 `Domain` 없이, shared-domain old cookie라면 old `Domain` 값과 old `Path`를 그대로 맞춰야 한다.
- DevTools가 `This Set-Cookie was blocked...` reason을 보여 주면 [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)에서 먼저 keyword를 읽는다. `Secure`는 HTTPS/proxy, `SameSite`는 cross-site 여부, invalid `Domain`은 host-parent 관계, reason이 없는데 다음 요청만 비면 `Path` 쪽으로 좁힌다. `SameSite`와 proxy가 같이 섞여 보이면 primer 안의 [15초 체크: SameSite vs Proxy](./cookie-rejection-reason-primer.md#15초-체크-samesite-vs-proxy)로 바로 내려가 beginner 분기를 먼저 고정한다.
- `fetch` 관련 첫 판별 기준은 짧게 하나다: **actual 요청이 실제로 보이는가**. `credentials: "include"`가 있는데도 cookie가 안 붙거나, 서버가 `Access-Control-Allow-Credentials: true`를 보냈는데도 브라우저만 실패하면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)에서 같은 30초 Network 읽기 순서(`요청 method` -> actual request 존재 여부 -> actual request의 `Cookie` header / `status`)로 먼저 본다. actual 요청이 안 보이면 [Preflight Debug Checklist](./preflight-debug-checklist.md)로 먼저 가고, actual 요청이 보일 때만 `fetch` credential mode, cookie scope, CORS response 읽기 정책을 세 단계로 나눠 본다. `origin`/`site`/subdomain 감각부터 흔들리면 그 문서가 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)으로 다시 올려 보내고, 막히면 `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder)로 복귀한 뒤 이 anchor에서 다음 symptom branch를 다시 고른다.
- 브라우저 콘솔은 CORS라고 말하는데 Network를 보면 `OPTIONS`가 먼저 `401`/`403`/`405`로 멈추고 actual `GET`/`POST`가 아예 안 보이거나, 반대로 preflight는 통과했는데 actual `401`이 맞는지 헷갈리면 [Preflight Debug Checklist](./preflight-debug-checklist.md)에서 먼저 `OPTIONS` lane과 actual auth lane을 분리한다. 여기서 actual request가 없다는 것이 확인되면 auth보다는 preflight/CORS 설정을 먼저 보고, actual request가 보일 때만 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)나 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)로 내려간다.
- `Application > Cookies`에는 session cookie가 있는데 login 직후 다시 `/login`으로 튀고, 특히 `auth`/`app`/`api` subdomain 사이를 오갈 때만 깨지면 먼저 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `cookie-header gate` wording으로 같은 실패 요청을 고정한다. 즉 `Application`의 저장 여부와 `Network > Request Headers > Cookie`의 전송 여부를 두 칸으로만 먼저 맞춘다. `Application`에는 보이는데 request `Cookie` header가 비면 그다음 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)의 `Application vs Network first check` checklist로 내려가 `Domain`, host-only cookie, `Path`, `SameSite`를 확인한다. 다만 `/auth/callback` 직후에는 괜찮고 첫 app 요청부터 anonymous인데 callback용 cookie와 main session cookie를 같은 이름으로 읽고 있다면 scope 표를 더 파기 전에 [Callback Cookie Name Splitter](./callback-cookie-name-splitter.md)로 먼저 우회한다. request `Cookie` header까지 실제로 실리는 것이 확인된 뒤에야 server session/BFF mapping 쪽으로 넘어간다.
- `auth.example.com/callback`은 성공했고 browser도 `302`를 따라갔는데 `app.example.com` 첫 요청이 여전히 anonymous면 [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)에서 shared cookie 기대인지 handoff 기대인지 먼저 고른다. chooser 뒤 shared cookie면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)로 한 칸만 내려가 callback response의 `Set-Cookie`/`Location`, app 첫 요청의 `Cookie`, `app_session` 생성 여부를 차례로 본다.
- external IdP callback, social login, partner portal iframe, embedded login 경로에서만 cookie가 안 붙는데 login 응답과 다음 요청 URL은 계속 `https://...`라면 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)에서 browser cross-site cookie 전송 규칙과 proxy `X-Forwarded-Proto` mismatch를 먼저 분리한다. 읽다가 OAuth2/OIDC, `access token`, session cookie 역할이 다시 섞이면 [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)로 한 번 되돌아가 social login mental model을 다시 고정한다. redirect가 `http://...`로 꺾이면 곧바로 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)로 넘어간다. detour 뒤에는 `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder)로 돌아오면 된다.
- `localhost`에서는 되는데 ALB/Nginx/ingress 뒤에서만 login cookie가 안 남고, login 응답 직후 redirect가 `http://...`로 바뀌거나 `Secure` cookie가 다음 요청에서 빠지면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)에서 TLS termination, `X-Forwarded-Proto`, app의 proxy header 신뢰 설정을 먼저 확인한다. 읽다가 "지금 막힌 게 redirect scheme인지, OAuth2/OIDC social login 역할 구분인지"가 흔들리면 [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)로 되돌아가 외부 로그인 신원 확인과 내부 session 발급을 먼저 분리한다. 다 읽고 나면 `[catalog]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) 순서로 돌아와 다음 branch를 고른다.
- login 응답 `Location`이나 OAuth authorization request의 `redirect_uri`가 public origin이 아니라 `app-internal`, `localhost`, staging host로 만들어지면 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)에서 host preservation, `X-Forwarded-Host`, absolute URL builder, relative redirect vs configured public base URL 경계를 먼저 본다.
- login 뒤 redirect mismatch가 보이는데 어느 쪽부터 봐야 할지 모르겠으면 순서를 고정한다. 먼저 [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md)에서 `Location`의 `scheme`과 `host/origin`을 자른다. `http://...`면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), `https://...`인데 host만 틀리면 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)로 간다. 두 follow-up 모두 beginner one-step return path는 이 anchor다. 한 장만 읽고 바로 여기로 돌아온 뒤 `cookie-missing` / `server-anonymous` branch를 다시 고른다.
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)까지 읽었는데도 다음 갈래가 헷갈리면 이 anchor로 다시 돌아와 세 질문만 다시 본다. raw `401`인지 `302 + Location: /login`인지, request `Cookie` header가 비었나(`cookie-missing`, 기존 `cookie-not-sent`), login 직후 redirect `Location`이 `http://...`로 꺾였나, cookie는 실리는데 서버가 계속 anonymous로 보나(`server-anonymous`, 기존 `server-mapping-missing`). `cookie-missing` 쪽은 먼저 guide의 `cookie-header gate`로 같은 실패 요청을 다시 맞춘 뒤 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 내려가고, 나머지 두 갈래는 각각 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) 쪽으로 이어진다.
- `로그아웃했는데 계속 된다`, `logout still works`, `OIDC logout tail`, revoke가 늦다, route/region별 tail이 남으면 먼저 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)에서 "source of truth 변경 -> current request 반영 -> revocation propagation" 세 칸 mental model을 맞춘다. 이 row의 normalized route label은 `session-tail / revocation propagation`이다. role/claim 쪽 tail이면 `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md), tenant/grant 쪽 tail이면 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md), `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)로 handoff한 뒤 `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md), `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)로 기대 guarantee와 status vocabulary를 맞춘다. federated logout mapping은 `[deep dive]` [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md), system-design 쪽 tail은 `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge), `[system design]` [System Design: Session Store / Claim-Version Cutover](../system-design/session-store-claim-version-cutover-design.md), `[system design]` [System Design: Canonical Revocation Plane Across Token Generations](../system-design/canonical-revocation-plane-across-token-generations-design.md), `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](../system-design/revocation-bus-regional-lag-recovery-design.md)로 이어 붙인다.
- redirect hardening, PKCE verifier/state, callback 이후 세션 재발급, browser-visible credential 설계 자체를 보고 싶으면 `[deep dive]` [Open Redirect Hardening](./open-redirect-hardening.md), `[deep dive]` [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), `[deep dive]` [Session Fixation in Federated Login](./session-fixation-in-federated-login.md), `[deep dive]` [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md), `[deep dive]` [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)를 설계 축으로 본다.

## Browser / Server Boundary deep dive catalog

- `[deep dive]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- `[deep dive]` [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)
- `[deep dive]` [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md): login-loop, `cookie 있는데 또 로그인`, hidden `JSESSIONID` 증상으로 들어온 초보자는 먼저 문서 상단의 stop-and-branch box를 따라 `[primer]` Login Redirect / `SavedRequest` -> `[primer bridge]` Browser `401` vs `302` route로 되돌린다.
- `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
- `[deep dive]` [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)
- `[deep dive]` [Open Redirect Hardening](./open-redirect-hardening.md)
- `[deep dive]` [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
- `[deep dive]` [Session Fixation in Federated Login](./session-fixation-in-federated-login.md)
- `[deep dive]` [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)
- `[primer bridge]` [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
- `[primer bridge]` [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md)
- `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
- `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)
- `[deep dive]` [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md)
- `[deep dive]` [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)
- `[deep dive]` [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)

## Replay / Token Misuse / Session Defense deep dive catalog

- `[deep dive]` [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md)
- `[deep dive]` [Webhook Signature Verification / Replay Defense](./webhook-signature-verification-replay-defense.md)
- `[deep dive]` [One-Time Token Consumption Race / Burn-After-Read](./one-time-token-consumption-race-burn-after-read.md)
- `[deep dive]` [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
- `[deep dive]` [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md)
- `[deep dive]` [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md)
- `[deep dive]` [Refresh Token Rotation / Reuse Detection](./refresh-token-rotation-reuse-detection.md)
- `[deep dive]` [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
- `[deep dive]` [Device Binding Caveats](./device-binding-caveats.md)
- `[deep dive]` [Email Magic-Link Threat Model](./email-magic-link-threat-model.md)
- `[deep dive]` [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
- `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
- `[deep dive]` [Abuse Throttling / Runtime Signals](./abuse-throttling-runtime-signals.md)

## Identity Lifecycle / Provisioning Primer

- beginner-safe entrypoint는 `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md)다.
- 이 구간에서 `primer`는 SCIM 용어와 lifecycle mental model을 여는 first-step 문서고, `survey`가 아니다.
- `SCIM disable했는데 still access`, `deprovision은 끝났는데 access tail remains`, `group removal 뒤 tenant access가 남는다`처럼 symptom으로 들어오면 deep dive부터 읽지 말고 먼저 primer에서 `계정 상태 변경`과 `session/authz tail`을 분리한다.
- 그다음 안전한 순서는 `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md) -> `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md) -> 아래 lifecycle `[deep dive]` 또는 `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle)이다.

## Identity Lifecycle / Provisioning deep dive catalog

- 이 구간은 `[catalog]`다. 아래 링크들은 lifecycle symptom을 해결하는 개별 문서를 고르는 목록이지, 첫 설명 본문 자체는 아니다.
- beginner가 `disable됐는데 still access`, `group removal 뒤 계속 403/allow`, `backfill은 green인데 tail이 남음`을 바로 떠올리기 어렵다면 `[deep dive]` 전에 `[primer]` -> `[primer bridge]` 선행이 안전하다.
- 빠른 판별: "왜 access tail이 남는지 한 문장으로 설명할 수 없다"면 먼저 `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md) -> `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md) 순서로 간다.

- `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md)
- `[deep dive]` [SCIM Provisioning Security](./scim-provisioning-security.md)
- `[deep dive]` [SCIM Drift / Reconciliation](./scim-drift-reconciliation.md)
- `[deep dive]` [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)

초심자 진입로: 이 구간의 lifecycle `[deep dive]`들은 "계정/멤버십 상태 변화가 왜 session/authz tail과 연결되는가"를 이미 알고 있다는 전제에 가깝다. 그래서 먼저 `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md)으로 lifecycle mental model을 고정하고, tail 직관이 약하면 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md)를 거친 뒤 내려간다. `aud`/`scope`/internal permission 경계가 먼저 막히면 `[primer]` [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)을 side primer로 붙인다.

역할 구분 치트시트:

- `[primer]`: SCIM/provisioning/deprovisioning 단어와 lifecycle mental model을 처음 여는 첫 문서
- `[primer bridge]`: lifecycle은 이해했지만 `disable/group removal -> session/claim/authz tail` handoff가 아직 흐릴 때 거치는 두 번째 문서
- `[survey]`: security 전체 갈래를 넓게 훑는 README section
- `[deep dive]`: SCIM API, drift, session/authz consistency 같은 구체 축을 파고드는 본문
- `[playbook]` / `[recovery]`: 운영 장애나 복구 절차가 중심일 때만 내려가는 문서

## Service / Delegation Boundaries deep dive catalog

- beginner-safe entry는 먼저 `[primer]` 한 장으로 "이 문장이 scope/audience/permission 혼동인지, support alert 라우팅 혼동인지"를 자른 뒤에만 아래 `[deep dive]` 계약 문서로 내려간다.
- 이 section의 `[deep dive]`는 운영용 `recovery` 절차가 아니라 service trust, delegated access, operator contract를 설계/검증하는 본문이다. 실제 outage 복구가 급하면 [Incident / Recovery / Trust](#security-bridge-incident-recovery-trust)로 먼저 간다.

- `[primer]` [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md): service delegation에서 `scope`, `aud`, app permission이 같은 말처럼 들릴 때 가장 먼저 보는 first-step primer다.
- `[deep dive]` [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md): service credential shape를 이미 골라야 하는 단계에서 trust source와 caller identity 전달 방식을 비교하는 본문이다.
- `[deep dive]` [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md): 둘 다 "cert를 쓴다"로 뭉개지지 않게 client auth와 token binding을 분리하는 protocol deep dive다.
- `[deep dive]` [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md): gateway가 붙인 identity header를 downstream service가 어디까지 믿을지 정하는 trust-boundary 본문이다.
- `[deep dive]` [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md): 이미 trust header 체계를 쓰는 상황에서 우회 징후와 detection signal을 읽는 detection deep dive다.
- `[deep dive]` [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md): delegated token이 생긴 뒤 subject/operator/service 경계가 어디서 흐려지는지 파는 delegation-risk 본문이다.
- `[deep dive]` [Workload Identity / Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md): machine identity를 이미 운영하는 단계에서 key 배포와 federation 경계를 비교하는 platform deep dive다.
- `[deep dive]` [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md): service principal과 end-user context를 언제 같이 들고 가는지 정하는 propagation-boundary 본문이다.
- `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md): support AOBO/break-glass 알림에서 `누가 받는가`와 `어디로 보내는가`를 먼저 자르는 first-step primer다.
- `[primer bridge]` support AOBO / break-glass beginner route는 `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md)로 시작한 뒤 질문을 `알림(copy/audience)` / `권한 행사(actor/duration/evidence)` / `종료·cleanup(transfer cleanup / delegated tail)` 한 갈래로만 줄여서 아래 `[deep dive]`를 고른다. 여기서 `종료·cleanup`은 beginner용 delegated-access closeout alias다. generic revoke-lag incident row와 섞지 말고, support transfer cleanup wording을 먼저 붙인 다음 필요한 경우에만 session/revoke deep dive로 내려간다. route가 다시 넓어지면 이 catalog를 `survey`처럼 붙잡지 말고 [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey)로 복귀하고, 실제 장애 복구가 급하면 `[recovery]` / `[playbook]` 성격의 [Incident / Recovery / Trust](#security-bridge-incident-recovery-trust)로 먼저 간다.
- `[deep dive]` [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md): AOBO actor 권한, duration, evidence를 설계하는 delegated-access control 본문이다.
- `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md): customer-facing copy와 timing policy를 다루는 notification-policy deep dive다.
- `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md): email, inbox, alternate verified channel 선택 기준을 고정하는 delivery-policy 본문이다.
- `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md): support/revoke 사건을 같은 event spine으로 남기는 audit-schema deep dive다.
- `[deep dive]` [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md): AOBO lifecycle open/close 이벤트를 contract로 고정하는 event-boundary 본문이다.
- `[deep dive]` [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md): preview, confirm, revoke status를 audit trail로 잇는 correlation-schema deep dive다.
- `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md): tenant admin, end user, security contact를 언제 갈라 알릴지 정하는 audience-policy 본문이다.
- `[deep dive]` [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md): privileged support alert opt-in과 tenant policy shape를 고정하는 schema deep dive다.
- `[deep dive]` [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md): operator UI state와 confirm friction을 설계하는 tooling-semantics 본문이다.
- `[deep dive]` [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md): break-glass 종료 후 leftover privilege를 어떤 metric으로 추적할지 정하는 cleanup-observability deep dive다.
- `[deep dive]` [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md): revoke 버튼 이후에도 남는 delegated session/refresh/cache tail을 어떻게 닫을지 설명하는 cleanup deep dive다.
- `[deep dive]` [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md): incident close 전에 active override와 cleanup blocker를 어떤 hard gate로 볼지 정하는 closure-policy 본문이다.
- `[deep dive]` [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md): operator가 revoke scope를 고를 때 보게 되는 inventory/preview surface를 설계하는 UX-contract deep dive다.
- `[deep dive]` [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md): revoke 전에 보여 주는 preview payload와 join key를 고정하는 preview-contract 본문이다.
- `[deep dive]` [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md): confirm 시점 drift/expiry/reconfirm 응답을 설계하는 confirm-contract deep dive다.
- `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md): confirm 이후 `requested/in_progress/fully_blocked_confirmed` 보장을 어떻게 표현할지 정하는 status-contract 본문이다.

초심자 진입로: support AOBO / break-glass 알림 문서로 바로 점프하기 전에 `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md)의 `10초 라우터`에서 `read / write / break-glass / tenant / mailbox trust` 중 한 줄을 먼저 고르면 audience matrix, delivery surface, copy policy를 한 문서에 섞어 읽는 실수를 줄일 수 있다.

<a id="authz--tenant--response-contracts-deep-dive-catalog"></a>
## AuthZ / Tenant / Response Contracts deep dive catalog

- beginner-safe stale-deny route는 `[primer]` 응답 코드 구분 -> `[primer bridge]` grant-path freshness 분기 -> `[deep dive]` cache 문서 순서로 고정한다.
- `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) 초반의 `30초 비교표`는 `stale 403`과 `cached concealment 404`를 `응답 의미 -> 다음 문서` 기준으로 먼저 고정해 beginner가 `404 == 진짜 없음`으로 미끄러지지 않게 한다.
- beginner-safe concealment route는 `[primer]` 응답 코드 구분 -> `[primer bridge]` concealment `404` entry cue -> `[deep dive]` object-level concealment 문서 순서로 고정한다.
- `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md)와 `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)에는 각각 "primer bridge에서 들어온 경우"와 "advanced debugging에서 점프한 경우" entry cue가 있으니, 현재 상태에 맞는 큐를 먼저 확인하고 내려간다.
- beginner escalation gate를 명시한다: `graph cache` 용어가 보여도 기본값은 `[deep dive]` runtime-debugging handoff를 먼저 타고, `graph snapshot/version/edge invalidation` 증거가 명확할 때만 graph internals로 승격한다.
- cache/graph/negative-cache 묶음의 기본 진입로는 아래 순서로 고정한다: `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) -> `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) -> `(graph 증거가 명확할 때만)` `[deep dive]` [Authorization Graph Caching](./authorization-graph-caching.md) -> `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md).
- graph/negative-cache deep dive를 읽다가 길을 잃으면 이 anchor([AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog))로 돌아와 다음 갈래를 고른다.

- `[primer]` [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- `[primer]` [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
- `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md): role/scope는 통과했는데 ownership 검증이 빠져 바로 broken object-level authorization로 이어지는 이유를 1분 브리지로 먼저 잡고 내려간다. 문서 초반의 beginner용 `30초 분기표`는 IDOR 상황에서 `403`과 의도적 `404`를 언제 고를지 `협업/공유 자원` vs `private/user-owned 자원` 기준으로 먼저 나눠 준다.
- `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
- `[primer bridge]` [Concealment `404` Entry Cues](./concealment-404-entry-cues.md): 초보자가 `없는 줄 알았는데 남의 리소스였다` 같은 표현으로 들어와도 바로 deep dive 용어에 빠지지 않도록, 문서 앞부분에서 그 문장을 `진짜 없음 / 숨김 404 / stale deny` 세 갈래로 번역해 준다. 이번 정리에서는 `user-owned / shared / tenant-scoped` mini matrix를 추가해 `주문 상세 404`, `tenant 상세 404`, `grant 직후 404`를 한 화면에서 먼저 갈라 본 뒤 `IDOR / BOLA` 또는 stale-deny route로 handoff하게 했다.
- `[primer]` [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
- `[deep dive]` [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md)
- `[deep dive]` [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
- `[deep dive]` [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
- `[deep dive]` [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
- `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
- `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md)
- `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md): beginner가 graph internals로 너무 빨리 내려가지 않도록 `grant path -> runtime evidence -> graph escalation` 순서를 먼저 고정하는 handoff 문서다.
- `[deep dive]` [Authorization Graph Caching](./authorization-graph-caching.md): `graph snapshot version`, `relationship edge`, `tenant-scoped invalidation` 증거가 이미 잡힌 뒤에만 여는 graph internals deep dive다. 초반 `30초 return path`가 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md), `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md), 이 catalog로 되돌아오는 beginner-safe exit를 다시 보여 준다.
- `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)
- `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
- `[deep dive]` [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
- `[deep dive]` [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
- `[deep dive]` [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
- `[deep dive]` [Background Job Auth Context / Revalidation](./background-job-auth-context-revalidation.md)
- `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
- `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)

## 추천 학습 흐름 (category-local survey)

아래 흐름은 security 내부에서 "지금은 기초를 맞추는 구간인가, 이미 원인을 좁히는 구간인가, 아니면 장애 복구 문서로 넘어가는 구간인가"를 바로 보이게 만든 category-local `[survey]`다.

읽는 법:

| role badge | 이 badge를 붙이는 이유 |
|---|---|
| `[primer]` | 아직 mental model을 맞추는 첫 문서다. 여기서 막히면 뒤 `deep dive`로 바로 내려가지 않는다. |
| `[primer bridge]` | beginner route에서 다음 `deep dive`나 branch point로 넘기는 handoff 문서다. symptom language와 boundary 용어를 연결한다. |
| `[deep dive]` | 특정 경계, failure mode, 설계 선택을 본격적으로 좁히는 구간이다. |
| `[recovery]` / `[drill]` / `[playbook]` | 장애 복구, rehearsal, live 대응으로 넘어간다는 뜻이다. 개념 본문과 같은 역할로 읽지 않는다. |

### 1. JWT / Session / Recovery

```text
[primer] Signed Cookies / Server Sessions / JWT Trade-offs → [primer] Role Change and Session Freshness Basics → [primer bridge] Claim Freshness After Permission Changes → [deep dive] AuthZ / Session Versioning Patterns → [deep dive] JWT 깊이 파기 → [deep dive] Refresh Token Rotation / Reuse Detection → [deep dive] JWK Rotation / Cache Invalidation / kid Rollover → [recovery] JWKS Rotation Cutover Failure / Recovery → [drill] JWT / JWKS Outage Recovery / Failover Drills → [playbook] Signing Key Compromise Recovery Playbook → [deep dive] Session Revocation at Scale → [deep dive] Revocation Propagation Lag / Debugging → [deep dive] Revocation Propagation Status Contract
```

### 2. OAuth / Browser / BFF

이 구간의 mainline은 브라우저 redirect/BFF 기준이고, `OAuth PAR / JAR`와 `OAuth Device Code`는 inline exception이 아니라 아래 branch point에서 role badge를 유지한 채 따로 갈라지는 side branch로 읽는다.

#### 2-A. Mainline: Browser Redirect / BFF

```text
[primer] OAuth2 기초 → [primer] OAuth2 vs OIDC Social Login Primer → [primer bridge] OAuth2 Authorization Code Grant → [primer] OAuth Scope vs API Audience vs Application Permission → [deep dive] PKCE Failure Modes / Recovery → [primer] Absolute Redirect URL Behind Load Balancer Guide → [deep dive] Open Redirect Hardening → [deep dive] Session Fixation in Federated Login → [deep dive] Session Fixation, Clickjacking, CSP → [deep dive] Browser Storage Threat Model for Tokens → [deep dive] CSRF in SPA + BFF Architecture → [deep dive] Browser / BFF Token Boundary / Session Translation → [deep dive] OAuth Client Authentication → [recovery] BFF Session Store Outage / Degradation Recovery → [deep dive] Step-Up Session Coherence / Auth Assurance → [deep dive] OIDC Back-Channel Logout / Session Coherence
```

- `구글 로그인은 이해했는데 auth/app subdomain handoff부터 막힌다`처럼 `auth.example.com/callback -> app.example.com` 질문이 시작점이면 mainline을 중간부터 읽지 말고 `[primer]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)에서 역할을 다시 분리한 뒤 `[primer]` [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) -> `[primer bridge]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) 순서로 우회한다. 여기서 shared cookie / handoff / `SameSite` 갈래를 고른 다음 다시 mainline이나 [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 돌아오면 beginner가 callback hardening 문서 한가운데로 떨어지지 않는다.

#### 2-B. Branch Point: Authorization Request Hardening

```text
[primer bridge] OAuth2 Authorization Code Grant → [primer bridge] OAuth PAR / JAR Basics → [deep dive] Open Redirect Hardening
```

`PAR / JAR`는 `Open Redirect Hardening` 앞에 잠깐 끼워 넣는 예외가 아니라, authorization request 자체를 hardening해야 할 때 Authorization Code에서 먼저 갈라지는 branch다. 이 branch를 읽고 나면 mainline의 browser hardening 흐름으로 합류하면 된다.

#### 2-C. Branch Point: Browserless / Cross-Device Login

```text
[primer bridge] OAuth Device Code Flow / Security Model
```

브라우저 callback이 없는 CLI, TV, 콘솔은 Authorization Code mainline의 예외 처리로 넘기지 말고 여기서 별도 시작한다.

짧게 이렇게 고르면 된다.

| 질문 모습 | 먼저 읽을 문서 | 읽지 말아야 할 첫 경로 |
|---|---|---|
| `터미널에서 로그인`, `TV에 코드가 뜸`, `휴대폰에서 승인`, `브라우저 없는 기기` | `[primer bridge]` [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md) | browser redirect, `redirect_uri`, BFF cookie 중심 문서 |
| `callback URL`, `PKCE`, `redirect_uri`, `session cookie`, `BFF` | [Mainline: Browser Redirect / BFF](#2-a-mainline-browser-redirect--bff) | device code branch |

Device Code Flow 문서 안에는 beginner용 `30초 분기표`, 다음 step 링크, category README 복귀 링크를 같이 넣어 두었다. sender-constrained token이나 device-bound hardening까지 같이 보려면 [DPoP / Token Binding Basics](./dpop-token-binding-basics.md), [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md), [Device Binding Caveats](./device-binding-caveats.md)를 이어서 보면 된다. 브라우저 callback hardening이 실제 문제였다면 [Mainline: Browser Redirect / BFF](#2-a-mainline-browser-redirect--bff)로 돌아간다.

### 3. Service Trust / Delegation

초심자용 AOBO / break-glass 브리지는 `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md) -> `[primer bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle)에서 `알림` / `권한 행사` / `종료·cleanup` 중 하나만 고정 -> `[deep dive]` AOBO 계약 문서 순서다. `survey`가 필요하면 위 `[catalog]` [Service / Delegation Boundaries deep dive catalog](#service--delegation-boundaries-deep-dive-catalog)로 올라가고, 복구 절차가 급하면 `[recovery]` / `[playbook]` 성격의 `[cross-category bridge]` [Incident / Recovery / Trust](#security-bridge-incident-recovery-trust)로 먼저 간다.

```text
[deep dive] Service-to-Service Auth: mTLS, JWT, SPIFFE → [deep dive] Gateway Auth Context Headers / Trust Boundary → [deep dive] Trust Boundary Bypass / Detection Signals → [deep dive] Token Exchange / Impersonation Risks → [deep dive] Workload Identity / User Context Propagation Boundaries → [deep dive] Support Operator / Acting-on-Behalf-Of Controls → [deep dive] Canonical Security Timeline Event Schema → [deep dive] AOBO Start / End Event Contract → [deep dive] Customer-Facing Support Access Notifications → [deep dive] Audience Matrix for Support Access Events → [deep dive] Tenant Policy Schema for Privileged Support Alerts → [deep dive] Delivery Surface Policy for Support Access Alerts → [deep dive] Operator Tooling State Semantics / Safety Rails → [deep dive] AuthZ Kill Switch / Break-Glass Governance → [deep dive] Emergency Grant Cleanup Metrics → [deep dive] Delegated Session Tail Cleanup → [deep dive] Incident-Close Break-Glass Gate → [deep dive] Revocation Impact Preview Data Contract → [deep dive] Revocation Preview Drift Response Contract → [deep dive] Revocation Propagation Status Contract → [deep dive] AOBO Revocation Audit Event Schema → [deep dive] Session Inventory UX / Revocation Scope Design
```

### 4. AuthZ / Tenant / Detection

```text
[primer] 인증과 인가의 차이 → [primer bridge] Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기 → [primer] Role vs Scope vs Ownership Primer → [intermediate bridge] 리소스 단위 인가 판단 연습: Role / Scope / Ownership / Tenant → [primer] OAuth Scope vs API Audience vs Application Permission → [primer] JWT Claims vs Roles vs Spring Authorities vs Application Permissions → [deep dive] Spring Authority Mapping Pitfalls → [deep dive] IDOR / BOLA Patterns and Fixes → [primer] Beginner Guide to Auth Failure Responses: `401` / `403` / `404` → [deep dive] PDP / PEP Boundaries Design → [deep dive] Permission Model Drift / AuthZ Graph Design → [deep dive] AuthZ / Session Versioning Patterns → [primer bridge] Grant Path Freshness and Stale Deny Basics → [deep dive] Delegated Admin / Tenant RBAC → [deep dive] Authorization Caching / Staleness → [deep dive] AuthZ Cache Inconsistency / Runtime Debugging → (graph snapshot/version/edge invalidation 증거가 명확할 때) [deep dive] Authorization Graph Caching → [deep dive] Authorization Runtime Signals / Shadow Evaluation → [deep dive] AuthZ Kill Switch / Break-Glass Governance → [deep dive] Tenant Isolation / AuthZ Testing → [deep dive] Token Misuse Detection / Replay Containment → [deep dive] Auth Observability: SLI / SLO / Alerting
```

### 5. Abuse / Replay / PoP

```text
[primer] Rate Limiting vs Brute Force Defense → [deep dive] Abuse Throttling / Runtime Signals → [primer] DPoP / Token Binding Basics → [deep dive] Proof-of-Possession vs Bearer Token Trade-offs → [deep dive] mTLS Client Auth vs Certificate-Bound Access Token → [recovery] Replay Store Outage / Degradation Recovery
```

### 6. SCIM / Lifecycle / Drift

```text
[primer] Identity Lifecycle / Provisioning Primer → [primer] Role Change and Session Freshness Basics → [primer bridge] Claim Freshness After Permission Changes → [deep dive] SCIM Provisioning Security → [deep dive] SCIM Drift / Reconciliation → [deep dive] SCIM Deprovisioning / Session / AuthZ Consistency → [deep dive] Authorization Runtime Signals / Shadow Evaluation → [deep dive] AuthZ Decision Logging Design → [deep dive] Audit Logging for Auth / AuthZ Traceability
```

### 7. Security + System Design

```text
[drill] JWT / JWKS Outage Recovery / Failover Drills → [incident matrix] Auth Incident Triage / Blast-Radius Recovery Matrix → [system design] Service Discovery / Health Routing → [system design] Global Traffic Failover Control Plane → [system design] Session Store Design at Scale
```

### 8. Database + Security + System Design

```text
[deep dive] SCIM Drift / Reconciliation → [deep dive] Database: Online Backfill Verification, Drift Checks, and Cutover Gates → [deep dive] SCIM Deprovisioning / Session / AuthZ Consistency → [deep dive] Authorization Runtime Signals / Shadow Evaluation → [system design] Database / Security Identity Bridge Cutover 설계 → [system design] Session Store / Claim-Version Cutover 설계 → [deep dive] AuthZ Decision Logging Design → [deep dive] Audit Logging for Auth / AuthZ Traceability
```

<a id="연결해서-보면-좋은-문서-cross-category-bridge"></a>
## 연결해서 보면 좋은 문서 (cross-category bridge / 한 줄 정리)

겹치던 bridge bullet을 `incident / session / identity` 3축으로 다시 묶었다. 같은 문서를 여러 묶음에 반복하지 않고, 가장 먼저 던지는 질문 기준으로 한 번만 배치했다.
빠른 시작 구간에는 entrypoint만 남기고, 세부 교차 링크는 아래 세 묶음에서만 길게 유지한다.
bridge bullet에서도 역할 cue를 유지한다. `[cross-category bridge]`는 README subsection entrypoint, `[playbook]` / `[drill]` / `[incident matrix]` / `[recovery]`는 incident 대응 문서, `[deep dive]`는 개념·경계 본문, `[system design]`는 control-plane / cutover 설계 handoff를 뜻한다.
같은 bullet 안에서 security/database `deep dive` -> system-design handoff -> security evidence `deep dive`처럼 역할이 다시 바뀌면 첫 링크 한 번만 표기하지 말고 전환 지점마다 badge를 다시 붙여 handoff boundary를 숨기지 않는다.
이 alias 이름은 [Navigation Taxonomy](../../rag/navigation-taxonomy.md)와 [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)에서 쓰는 `cross-category bridge` / `deep dive route` / `system design handoff` vocabulary를 그대로 따른다.
bullet 첫머리에는 `Identity / Delegation / Lifecycle` 같은 개념명만 두지 않고, 학습자가 실제로 말할 symptom 문장을 먼저 노출해 retrieval entry phrase를 바로 읽히게 유지한다.

### Beginner Role-Confusion Micro-FAQ

security bridge anchor 밑에서 가장 많이 헷갈리는 건 "여기서 끝내도 되나, 더 내려가야 하나"다. beginner 기준의 안전한 기본 규칙은 `primer -> primer bridge -> deep dive/recovery`다.

| 질문 | 여기서 멈춰도 되는 role | 더 내려갈 때의 cue | 다음 문서 |
|---|---|---|---|
| `primer`를 읽고 용어가 풀렸나? | `[primer]` | 아직도 `role/scope/ownership`, `401/403/404`, `cookie/session`처럼 두 축 이상이 한 문장으로 섞임 | 같은 주제의 `[primer bridge]` 1개만 더 읽는다. 예: [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md), [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |
| `primer bridge`까지 읽고 나면 언제 멈추나? | `[primer bridge]` | 원인 축이 한 갈래로 고정됐고, 지금 필요한 일이 `개념 분해`인지 `운영 복구`인지 구분된다 | anchor로 복귀해 branch를 다시 고른다. browser/session이면 [Session / Boundary / Replay](#security-bridge-session-boundary-replay), lifecycle면 [Identity / Delegation / Lifecycle](#security-bridge-identity-delegation-lifecycle) |
| 언제 `deep dive`로 가나? | `[deep dive]` | 이미 symptom이 한 갈래로 좁혀졌고, 구현 경계/캐시/정책/프레임워크 동작을 실제로 파야 함 | `catalog`나 bridge에서 연결된 deep dive로 내려간다. 예: [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog), [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) |
| 언제 `recovery`나 `playbook`이 먼저인가? | `[recovery]`, `[playbook]`, `[runbook]`, `[incident matrix]` | 장애 대응, blast radius, failover, cutover, cleanup SLA처럼 "지금 복구 절차가 필요하다"가 먼저임 | incident 성격이면 [Incident / Recovery / Trust](#security-bridge-incident-recovery-trust), session tail/전파 상태면 [Session / Boundary / Replay](#security-bridge-session-boundary-replay) |
| `survey`, `catalog`, `bridge`는 각각 뭘 하나? | `[survey]`, `[catalog]`, `[cross-category bridge]` | route 자체가 헷갈릴 때만 읽는다. 개별 개념 설명을 기대하고 붙잡고 있으면 오히려 늦다 | 전체 순서가 필요하면 [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey), theme bucket 선택은 `catalog`, cross-category handoff는 현재 구간의 bridge anchor |

- 한 줄 기억법:
  `primer`는 용어를 연다.
  `primer bridge`는 섞인 질문을 한 갈래로 줄인다.
  `deep dive`는 한 갈래로 좁혀진 원인을 판다.
  `recovery/playbook`은 복구 절차를 바로 실행할 때 쓴다.

<a id="security-bridge-incident-recovery-trust"></a>
<a id="incident--recovery--trust"></a>
### Incident / Recovery / Trust

- `JWKS outage`, `kid miss`, `unable to find JWK`, `auth verification outage`, `stale JWKS cache` alias cluster의 security-side entrypoint다.
- 이 subsection은 `survey`가 아니라 `cross-category bridge` entrypoint다. 같은 ladder를 빠르게 재호출할 때는 아래 badge-order 표를 먼저 읽는다.
- beginner/junior first click은 이 묶음이 아니다. `처음`, `헷갈려요`, `what is`에 가까운 질문이면 먼저 [Browser / Session Beginner Ladder](#browser--session-beginner-ladder), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md), [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) 같은 `primer` 계열로 내려가고, 여기의 `playbook` / `drill` / `recovery`는 incident follow-up으로만 읽는다.

| 증상 시작점 | `playbook` | `drill` | `incident matrix` | `recovery` | `system design` |
|---|---|---|---|---|---|
| `JWKS outage`, `kid miss`, `unable to find JWK`, `auth verification outage`, `stale JWKS cache` | `[playbook]` [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md) | `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md) | `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md) | `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md) | `[system design]` [System Design: Service Discovery / Health Routing](../system-design/service-discovery-health-routing-design.md) -> `[system design]` [System Design: Global Traffic Failover Control Plane](../system-design/global-traffic-failover-control-plane-design.md) -> `[system design]` [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md) |

- JWT/JWKS 장애의 response ladder를 빠르게 훑으려면 `[playbook]` [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)에서 시작해 `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md), `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md), `[system design]` [System Design: Service Discovery / Health Routing](../system-design/service-discovery-health-routing-design.md), `[system design]` [System Design: Global Traffic Failover Control Plane](../system-design/global-traffic-failover-control-plane-design.md), `[system design]` [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)를 순서대로 보면 `unable to find JWK` 같은 verify error string과 route-level 복구, state-level 복구가 분리된다.
- rotation cutover 실패나 signer compromise를 trust convergence 문제로 보려면 `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md), `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md), `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md), `[deep dive]` [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)을 함께 보고, hardware root까지 흔들린 상황은 `[deep dive]` [Hardware-Backed Keys / Attestation](./hardware-backed-keys-attestation.md), `[recovery]` [Hardware Attestation Policy / Failure Recovery](./hardware-attestation-policy-failure-recovery.md)로 이어 가면 된다.
- `break-glass는 종료됐는데 access/session tail이 남는다`, `cleanup_confirmed`를 언제 내려야 할지 모르겠다, `incident close가 active override 때문에 막힌다` 같은 incident symptom이면 `[deep dive]` [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md), `[deep dive]` [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md), `[deep dive]` [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md), `[deep dive]` [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md), `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md), `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md), `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)를 같이 보면 detection, evidence, leftover privilege cleanup 판단 기준이 이어진다.

<a id="security-bridge-session-boundary-replay"></a>
<a id="session--boundary--replay"></a>
### Session / Boundary / Replay

- browser/session symptom routing은 `[primer -> primer bridge]` [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) -> `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) 순서로 먼저 모은다. `hidden session mismatch`를 보면 같은 경로 안에서 normalized label `cookie-missing` / `server-anonymous`로 먼저 갈라서 system-design bridge와 naming parity를 맞춘다. 기존 `cookie-not-sent` / `server-mapping-missing`은 retrieval alias다. 아래 bullet들은 거기서 갈라진 뒤 원인별 deep dive를 확장하는 용도다.
- 이 subsection은 `survey`가 아니라 bridge 재진입점이다. beginner 기본 규칙은 `primer -> primer bridge -> deep dive`이고, 복구 문서가 필요할 때만 `recovery`까지 간다.
- session-tail, grant/stale-deny, tenant-membership freshness는 모두 같은 재진입 규칙을 쓴다. `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)로 먼저 mental model을 고정하고, 그다음 증상별 `primer bridge` 한 장만 고른 뒤에만 `deep dive`나 `recovery`로 넘긴다. beginner split은 `allowed after revoke` 같은 allow tail이면 `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md), `stale deny` 같은 deny tail이면 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md), tenant 문맥 tail이면 `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)다.
- 이 구간에서 가장 자주 생기는 오해는 `deep dive` / `recovery` 링크를 먼저 눌러도 된다고 보는 것이다. 여기서는 `증상 문장 -> primer -> primer bridge`로 원인 축을 먼저 자르고, Spring internals, BFF translation, store outage 문서는 그다음 follow-up으로만 연다.

| 증상 시작점 | `primer` | `primer bridge` | `deep dive` | `recovery` |
|---|---|---|---|---|
| `login loop`, `SavedRequest`, `401`/`302`가 섞임 (`기억/전송/복원` cue) | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | `[primer bridge]` [30초 3-step 체크 카드](./browser-401-vs-302-login-redirect-guide.md#30초-3-step-체크-카드)로 `redirect 기억` / `cookie 전송` / `server 복원`을 먼저 자른 뒤 `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) | `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) |
| `cookie-missing` 또는 `server-anonymous`가 의심됨 | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | 먼저 `cookie-header gate`로 같은 실패 요청의 `Application` 저장값과 request `Cookie` header를 맞춘 뒤, request `Cookie` header가 비면 `cookie-missing`으로 보고 `[primer]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), handoff가 헷갈리면 `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./duplicate-cookie-vs-proxy-login-loop-bridge.md) | `server-anonymous`가 확인되면 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) | `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md) |
| `logout still works`, `allowed after revoke`, revoke tail, role/claim 반영 지연 | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) | `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md) | "아직 허용된다"는 allow tail로 먼저 읽고 `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md)로 내려간다. stale deny branch와 섞지 않는다. | `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md), `[system design]` [System Design: Revocation Bus Regional Lag Recovery](../system-design/revocation-bus-regional-lag-recovery-design.md) |
| `grant했는데 still 403`, `stale deny`, `cached 404 after grant`, `권한 줬는데 아직도 403/404` | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) | `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | "아직 거부된다"는 deny tail로 먼저 읽는다. actual `GET`/`POST`의 `403`/`404`인지 먼저 확인한 뒤 stale deny로 읽고, `OPTIONS`만 실패하거나 `/login` `302`/CORS 오진이면 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md), `[primer bridge]` [Preflight Debug Checklist](./preflight-debug-checklist.md), `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 먼저 갈라진다. 그다음 cache 축이면 `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) | 보통 `recovery`까지 바로 가지 않는다. 이 row는 beginner deny-tail primer -> cache/runtime `deep dive`가 기본이고, 문장이 `로그아웃했는데 아직 된다`, `revoke했는데 아직 허용된다`로 바뀌면 윗 row의 revoke route로 옮겨 탄다. |
| `남의 주문인데 왜 404`, `권한은 있는데 왜 404`, `404가 숨김인지 stale인지 헷갈림` | `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) | `[primer bridge]` [Concealment `404` Entry Cues](./concealment-404-entry-cues.md) | `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md), `[deep dive]` [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md) | `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) |
| `tenant 이동/추가/제거` 뒤 old workspace가 남거나 새 tenant에서만 `403` | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) | `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md) | `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md) | 보통 `recovery`보다 tenant/session freshness 정리가 먼저다. session cutover 설계까지 넓히려면 `[system design]` [System Design: Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md)로 넘기고, revoke incident status 문서는 이 tenant row의 기본 follow-up이 아니다. |

초보자가 DevTools에서 `Location`, next request URL, request `Cookie` header 세 칸만으로 바로 primer를 고르고 싶으면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)의 `Tiny DevTools evidence card`를 먼저 본다. 읽은 뒤에는 다시 이 subsection이나 [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 복귀한다.

- beginner safety rule: `tenant-specific 403`와 concealment `404`는 둘 다 category README에서 바로 `deep dive` 이름을 고르기 전에 `[primer bridge]` 한 장으로 먼저 줄인다. `grant 직후`면 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md), `tenant 이동/추가/제거` 문맥이면 [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md), `없는 줄 알았는데 남의 리소스였다` 문장이면 [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)로 먼저 붙인다.
- cookie beginner 질문에서 "`Application`이랑 `Network`에서 정확히 무슨 칸을 비교하지?"가 먼저 나오면 [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)로 들어가 `Set-Cookie` / `Application row` / request `Cookie` 3칸을 고정한 뒤 다시 이 README의 [Browser / Session Beginner Ladder](#browser--session-beginner-ladder)나 [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)로 복귀한다.

- `cookie`, `session`, `JWT` 개념은 아는데 Spring 문서에서 `SavedRequest`, `hidden JSESSIONID`, `SecurityContextRepository`, `SessionCreationPolicy`가 갑자기 등장하면 [Browser / Session Beginner Ladder](#browser--session-beginner-ladder) 하나만 먼저 밟는다. follow-up 이후에도 server-side persistence 문맥이 비면 `[deep dive]` [Spring Security 아키텍처](../spring/spring-security-architecture.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 이어 가면 cookie 자동 전송, redirect 응답의 저장/복귀, hidden session 생성, Spring persistence, browser/BFF translation 경계가 한 줄로 이어진다.
- partner iframe, embedded login, in-app browser에서만 세션이 안 붙고 `SameSite=None; Secure`도 이미 맞췄다면 같은 증상을 `SameSite` 문서 안에서 계속 맴돌지 말고 [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md)로 분기한다. 이 문서는 "cookie 속성 수정"과 "modern privacy 정책 때문에 embedded login 자체를 우회해야 하는가"를 beginner 기준으로 나눠 준다.
- login callback hardening을 redirect 검증부터 post-login session/headers까지 한 번에 보려면 `[primer]` [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md), `[deep dive]` [Open Redirect Hardening](./open-redirect-hardening.md), `[deep dive]` [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), `[deep dive]` [Session Fixation in Federated Login](./session-fixation-in-federated-login.md), `[deep dive]` [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md), `[deep dive]` [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md), `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)를 같이 보면 public origin reconstruction, redirect destination, verifier/state consumption, session regeneration, frame/script policy, browser-visible credential, post-login mutation hardening 축이 한 줄로 이어진다.
- 브라우저에 어떤 credential이 보이는지와 BFF가 그 credential을 어떻게 서버측 세션/token cache로 번역하는지는 `[deep dive]` 묶음인 [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](../spring/spring-security-logout-handler-success-boundaries.md), [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)를 먼저 보고, store outage 대응만 필요할 때 `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)로 내려간다.
- 세션 일관성 자체를 보고 싶으면 `[deep dive]` 묶음인 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), [Session Revocation at Scale](./session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md), [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md), [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md), [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)를 먼저 묶으면 된다.
- device/session graph와 operator action surface를 같이 보려면 `[deep dive]` 묶음인 [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md), [Device Binding Caveats](./device-binding-caveats.md), [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md), [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md), [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md), [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md), [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md), [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md), [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)를 한 번에 보면 revoke scope, preview payload, confirm-time drift contract, propagation status contract, delegated tail cleanup 기준, support tooling semantics가 이어진다.
- sender-constrained token과 replay store failure를 같은 boundary 문제로 보려면 `[deep dive]` 묶음인 [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md), [DPoP / Token Binding Basics](./dpop-token-binding-basics.md), [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md), [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md), [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md)를 먼저 보고, store-side 복구 절차가 필요할 때만 `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)로 넘긴다.
- replay/dedup과 one-time token race를 애플리케이션 boundary 바깥 저장소 문제로 확장하려면 `[deep dive]` [Database: 멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)로 먼저 맞춘 뒤, `[system design]` [System Design: Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md), [System Design: Replay / Repair Orchestration Control Plane](../system-design/replay-repair-orchestration-control-plane-design.md)로 handoff하고, 구현/위협 모델 확인은 `[deep dive]` [Email Magic-Link Threat Model](./email-magic-link-threat-model.md), [Password Reset Threat Modeling](./password-reset-threat-modeling.md), [One-Time Token Consumption Race / Burn-After-Read](./one-time-token-consumption-race-burn-after-read.md)로 이어 간다.

<a id="security-bridge-identity-delegation-lifecycle"></a>
<a id="identity--delegation--lifecycle"></a>
### Identity / Delegation / Lifecycle

- `SCIM disable은 끝났는데 access shutdown 설명이 안 맞는다`, `deprovision은 끝났는데 session/authz tail이 남는다`, `backfill is green but access tail remains`, `decision parity`, `auth shadow divergence` alias cluster를 security README에서 바로 붙일 때 쓰는 bridge다.
- 같은 authority-transfer route를 database README는 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design README는 `Database / Security Authority Bridge` -> `Verification / Shadowing / Authority Bridge`로 부른다. route-name이 달라도 같은 handoff 묶음이라는 점을 여기서 먼저 고정한다.
- beginner-path alias wording으로는 `deprovision tail -> access tail -> decision parity -> cleanup evidence` 중 security가 `access tail`을 대표하는 visible bridge label이다. 즉 database의 row parity 다음에 "old authority/session/cache tail이 runtime에 남는가"를 여기서 먼저 붙인다.
- 초보자용 mental model: "권한 이전"은 사용자를 다른 테이블로 옮기는 일만이 아니라, `누가 요청했는가`와 `허용/거부 결정`의 근거가 새 경로에서도 같고, 남은 session/claim/cache tail을 닫을 수 있는지 확인하는 흐름이다.
- 초보자가 `SCIM disable했는데 아직 접근돼요`, `deprovision 끝났는데 access tail이 남아요`, `계정은 껐는데 세션이 아직 살아 있어요`처럼 물으면 security README는 `old authority/session/cache tail이 runtime에 남는가`를 먼저 자르는 visible bridge다.
- `퇴사 처리했는데 아직 접근됨`, `role을 뺐는데 session은 계속 admin처럼 보임`, `grant했는데 특정 pod만 403`처럼 lifecycle / session freshness / authz cache가 한 문장으로 섞이면 먼저 `[primer bridge]` [Lifecycle vs Session Freshness vs AuthZ Cache 비교 카드](./lifecycle-session-freshness-authz-cache-comparison-card.md)에서 세 갈래를 한 번에 자른다.
- `authority transfer`와 `revoke lag`를 먼저 갈라야 할 때는 `[primer bridge]` [Authority Transfer vs Revoke Lag Primer Bridge](./authority-transfer-vs-revoke-lag-primer-bridge.md)에서 시작한다. 이 bridge는 cleanup/parity 질문을 authz-cache incident와 섞지 않게 entrypoint를 고정한다.
- 이 subsection은 `survey`가 아니라 authority-transfer bridge entrypoint다. 아래 badge-order 표는 database/system-design README와 같은 라더를 그대로 재사용한다.

| 한눈 구분 | 더 가까운 축 | 먼저 볼 문서 |
|---|---|---|
| source of truth의 계정/멤버십 변화가 access shutdown까지 이어졌는지부터 헷갈림 | `lifecycle issue` | `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md) |
| 변화는 끝났는데 현재 session/JWT/tenant 문맥이 old snapshot처럼 보임 | `session freshness issue` | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) |
| 같은 사용자 요청이 pod/tenant/route에 따라 stale `403`/cached `404`로 갈림 | `authz cache issue` | `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |

| handoff stage | 유지할 role badge | 이 stage의 job |
|---|---|---|
| database/security symptom entrypoint | `[cross-category bridge]` | `deprovision tail`과 `access tail` 질문을 sibling README label로 먼저 받는다 |
| cutover 설계 입구 | `[system design]` | `decision parity`가 맞도록 new path rollout, claim/session/store cutover, retirement guard를 설계한다 |
| verification / cleanup gate | `[system design]` | `cleanup evidence`가 되도록 shadow/parity evidence와 reversible cleanup 조건을 설계한다 |
| security evidence hand-back | `[deep dive]` | runtime signal, decision log, audit evidence로 cleanup 근거를 닫는다 |

- 서비스 간 caller identity와 end-user context propagation을 같이 보려면 `[deep dive]` 묶음인 [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md), [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md), [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md), [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)를 같이 보면 trust propagation과 bypass signal이 한 묶음으로 보인다.
- `support AOBO나 break-glass transfer cleanup이 안 닫히고 customer timeline closeout, delegated session cleanup, cleanup_confirmed 판단이 한 문장으로 섞인다`면 먼저 `[primer]` [Support Access Alert Router Primer](./support-access-alert-router-primer.md)에서 `종료·cleanup`을 고정한 뒤 delegated admin/support operator 축의 `[deep dive]` [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md), `[deep dive]` [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md), `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), `[deep dive]` [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md), `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md), `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md), `[deep dive]` [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md), `[deep dive]` [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md), `[deep dive]` [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md), `[deep dive]` [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md) 순으로 본다. cleanup closeout이 delegated session tail을 넘어서 authority-transfer retirement gate로 커지면 이 subsection의 공통 라더를 그대로 따른다: `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle) -> `[system design]` [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge) -> `[system design]` [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge) -> `[deep dive]` cleanup evidence docs. preview/confirm/status/timeline을 잇는 `preview_id`/`access_group_id`/`revocation_request_id` correlation spine은 `[deep dive]` [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)에서 확인한 뒤, generic revoke-lag인지 delegated cleanup closeout인지 다시 헷갈리면 `Session / Boundary / Replay`보다 이 subsection의 cleanup ladder로 먼저 되돌아온다.
- authz runtime inconsistency를 정책/캐시 문제로 보려면 먼저 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)로 응답 코드를 고정하고, 그다음 `[deep dive]` 묶음인 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), [Rate Limiting vs Brute Force Defense](./rate-limiting-vs-brute-force-defense.md), [Abuse Throttling / Runtime Signals](./abuse-throttling-runtime-signals.md), [Authorization Caching / Staleness](./authorization-caching-staleness.md), [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md), [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md), [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md), [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)를 같이 보면 stale deny, tenant-specific `403`, `401`/`404` flip, runtime guardrail이 한 축으로 이어진다.
- beginner가 `cache`, `graph-cache`, `negative-cache`를 같은 말처럼 잡지 않도록 첫 선택용 비교표를 먼저 둔다. 이 표는 "지금 어느 캐시를 의심해야 하나"를 고르는 entrypoint이고, 세 문서를 다 읽으라는 뜻이 아니다. 먼저 symptom language를 고정해야 하면 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 한 칸 올라간다.

| 헷갈리는 이름 | 초보자용 한 줄 구분 | 지금 여는 첫 문서 | 아직 안 가는 편이 좋은 문서 |
|---|---|---|---|
| `cache` | 일반 authz decision/claim/session freshness를 넓게 보는 출발점 | `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) | graph 구조 증거가 아직 없으면 [Authorization Graph Caching](./authorization-graph-caching.md) |
| `graph-cache` | relationship/path/snapshot처럼 graph 기반 권한 계산 캐시 | `[primer]` [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md) | stale deny만 보이는데 graph/version 단서가 없으면 [Authorization Graph Caching](./authorization-graph-caching.md) |
| `negative-cache` | "deny/not-found를 저장해 grant 뒤에도 거부가 남는가"를 보는 갈래 | `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md) | 응답 의미도 아직 안 갈렸으면 먼저 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |

- 길을 잃으면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 돌아와 symptom row를 다시 고른다.
- `authorization graph cache`, `graph snapshot`, `relationship cache`, `relationship-based authz인데 delegated scope revoke 뒤 tenant별로 allow/deny가 갈린다`, `tenant ownership move 뒤 graph invalidation이 어디서 끊겼는지 모르겠다` 같은 symptom이면 먼저 `[primer]` [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md)에서 stale 위치(변경/전파/판정)를 분리한 뒤, `[deep dive]` 묶음인 [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md), [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md), [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md), [Authorization Caching / Staleness](./authorization-caching-staleness.md), [Authorization Graph Caching](./authorization-graph-caching.md), [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md), [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)를 같이 보면 graph source of truth, scope edge, decision/enforcement split, tenant-scoped invalidation, shadow diff, negative regression test가 한 줄로 이어진다.
- `SCIM disable했는데 로그인/권한이 그대로 남는다`, `deprovision은 끝났는데 tenant access tail이 남는다`, `backfill is green but access tail remains` 같은 lifecycle symptom이면 먼저 `[primer]` [Identity Lifecycle / Provisioning Primer](./identity-lifecycle-provisioning-primer.md)에서 "계정 상태 변경"과 "access tail"을 분리하고, 이어서 `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md)로 "권한 변경 이후 tail이 남는 이유"를 두 단계로 나눈다. 그다음 authority-transfer handoff는 database/system-design README와 같은 badge 순서를 유지한다: `[cross-category bridge]` [Database README](../database/README.md) -> `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle) -> `[system design]` [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge) -> `[system design]` [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge) -> `[deep dive]` [SCIM Provisioning Security](./scim-provisioning-security.md), `[deep dive]` [SCIM Drift / Reconciliation](./scim-drift-reconciliation.md), `[deep dive]` [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md), `[deep dive]` [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md), `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md), `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md) 순으로 붙인다. system-design 구현 문서를 바로 펼칠 때는 `[system design]` [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md), `[system design]` [System Design: Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md)를 같은 handoff 단계에서 본다. 이렇게 보면 `decision parity`, `auth shadow divergence`, cleanup/retirement evidence를 badge 순서까지 흔들리지 않게 분리해서 읽을 수 있다.
