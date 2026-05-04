---
schema_version: 3
title: 'Beginner Guide to Auth Failure Responses: 401 / 403 / 404'
concept_id: security/auth-failure-response-401-403-404
canonical: false
category: security
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
aliases:
- 401 vs 403 vs 404
- auth failure response
- 로그인 됐는데 왜 403
- token valid but forbidden
- 404 concealment
intents:
- comparison
- design
linked_paths:
- contents/security/authentication-vs-authorization.md
- contents/security/permission-model-bridge-authn-to-role-scope-ownership.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/spring/spring-security-filter-chain.md
- contents/security/concealment-404-entry-cues.md
forbidden_neighbors:
- contents/network/redirect-vs-forward-vs-spa-navigation-basics.md
confusable_with:
- security/authentication-vs-authorization
- security/permission-model-bridge-authn-to-role-scope-ownership
expected_queries:
- 401 403 404 차이가 뭐야?
- 로그인 됐는데 왜 403이 나와?
- token valid인데 왜 forbidden이야?
- 남의 주문 조회를 404로 숨기는 건 언제 써?
contextual_chunk_prefix: |
  이 문서는 학습자가 로그인은 됐는데 어떤 작업이 막히면 그게 인증 실패인지
  권한 실패인지 처음 가르는 chooser다. 401(인증 실패) vs 403(권한 실패)
  vs 404(자원 은닉) 분기, token valid인데 forbidden, 로그인은 됐는데 작업
  막힘, 인증 vs 인가 응답 코드 같은 자연어 paraphrase가 본 문서의 세 분기에
  매핑된다.
---

# Beginner Guide to Auth Failure Responses: `401` / `403` / `404`

> 한 줄 요약: `401`은 다시 인증, `403`은 인증은 됐지만 거절, `404`는 진짜 없음 또는 존재 은닉으로 먼저 읽으면 초보자도 흔한 혼동을 줄일 수 있다.

**난이도: 🟢 Beginner**

> 문서 역할: 이 문서는 `401` / `403` / `404`를 처음 구분하는 beginner primer다. 운영 사고, cache stale deny, concealment 설계, 브라우저 redirect 세부는 관련 문서로 넘긴다.

> target query shape: `401 403 404 차이`, `로그인 됐는데 왜 403`, `남의 주문인데 왜 404`, `what is 401 vs 403 vs 404`

관련 문서:
- [인증과 인가의 차이](./authentication-vs-authorization.md)
- [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)
- [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- [Preflight Debug Checklist](./preflight-debug-checklist.md)
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)
- [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
- [Spring `ProblemDetail` Error Response Design](../spring/spring-problemdetail-error-response-design.md)

retrieval-anchor-keywords: 401 403 404 beginner, 401 vs 403 vs 404, auth failure response basics, 로그인 됐는데 왜 403, 남의 주문인데 왜 404, 토큰 valid인데 왜 403, 쿠키는 있는데 왜 다시 로그인, cookie exists but login again, what is 401, when to use 403, 404 concealment basics, actual request vs preflight, browser 401 vs 302, 처음 보는 auth status, why token valid but forbidden

## 처음 볼 때는 이 순서만 기억하면 된다

먼저 `이 요청이 누구인지 확인됐나?`를 본다. 아직 확인되지 않았으면 `401`이다. 그다음 `누구인지는 알겠는데 이 행동을 허용하나?`를 본다. 여기서 막히면 기본값은 `403`이다. 마지막으로 `없는 리소스인가, 아니면 있어도 있다고 말하지 않기로 한 정책인가?`를 본다. 이 단계에서 바깥 응답은 `404`가 될 수 있다.

짧게 외우면 아래 한 줄이면 충분하다.

- `401`: 다시 인증해야 한다.
- `403`: 인증은 됐지만 이 요청은 안 된다.
- `404`: 진짜 없거나, 있다고 알려 주지 않는다.

초보자 mental model은 `AuthN -> AuthZ -> concealment/absence` 순서다.
다만 `404`가 항상 숨김이라는 뜻은 아니다. 진짜 없는 리소스일 수도 있으니 ownership 문맥과 resource ID를 같이 본다.

## 한 장 비교표

| 상태 코드 | 초보자용 의미 | 흔한 예시 | 첫 행동 |
|---|---|---|---|
| `401` | 아직 인증을 믿을 수 없음 | 로그인 안 함, 만료 토큰, 깨진 세션 쿠키 | 재로그인, 토큰 갱신, credential 전달 경로 확인 |
| `403` | 인증은 됐지만 권한이 부족함 | 관리자 권한 없음, scope 부족, ownership 불일치 | role, permission, scope, ownership 확인 |
| `404` | 리소스가 없거나 존재를 숨김 | 잘못된 ID, 남의 주문 조회, concealment 정책 | ID 확인, user-owned 리소스인지 확인 |

같은 URL이어도 항상 같은 코드가 나오지 않는다. `코드 선택 기준은 endpoint 이름이 아니라 현재 요청 상태`다.

## 30초 예시

| 요청 상황 | 왜 이 코드인가 | 바깥 응답 |
|---|---|---|
| `Authorization` 헤더 없이 `GET /api/me` 호출 | principal을 만들 수 없다 | `401` |
| 일반 사용자가 `GET /admin/reports` 호출 | principal은 있지만 필요한 권한이 없다 | `403` |
| 사용자 A가 사용자 B의 주문 `GET /orders/123` 호출, 서비스가 존재를 숨기기로 함 | ownership mismatch를 바깥에 숨긴다 | `404` |
| `GET /orders/999999`인데 진짜 없는 주문 번호 | 리소스가 실제로 없다 | `404` |

`토큰이 유효하다`와 `이 요청이 허용된다`는 같은 말이 아니다. 토큰 검증을 통과해도 role, scope, ownership 단계에서 `403`이나 `404`가 나올 수 있다.

## 자주 헷갈리는 지점

- `로그인 됐는데 왜 403`:
이미 principal은 만들어졌고, 그다음 권한 단계에서 막힌 경우가 많다. 이때는 재로그인보다 role, permission, scope, ownership을 먼저 본다.
- `token valid but 403`:
유효한 토큰은 보통 `401`이 아니라는 뜻일 뿐이다. 허용 여부는 별도의 authz 판단이다.
- `남의 주문인데 왜 404`:
user-owned 또는 multi-tenant 리소스는 존재를 숨기기 위해 `403` 대신 `404`를 쓸 수 있다. 이 문서에서는 여기까지만 기억하고, 자세한 정책은 관련 문서로 넘긴다.
- `OPTIONS 401`만 봤다:
처음 보는 auth status라도 바로 `401` 의미를 해석하지 말고, actual `GET`/`POST`가 있었는지 먼저 본다. preflight 문제일 수 있다.

## 15초 다음 행동표

| 지금 눈앞의 문장 | 바로 할 일 |
|---|---|
| `로그인하라고 다시 보낸다` | `401`로 보고 credential 전달 경로를 먼저 확인한다 |
| `로그인은 됐는데 이 API만 안 된다` | `403`로 보고 role, scope, ownership을 순서대로 본다 |
| `내 건 되는데 남의 것만 404다` | concealment 가능성을 열고 ownership/tenant 문맥을 확인한다 |

## 질문 문장 그대로 자르는 초보자 라우팅

질문이 이미 증상 문장이라면 상태 코드 해석과 다음 문서를 같이 고르는 편이 빠르다.

| 학습자가 자주 던지는 말 | 이 문서에서 먼저 붙일 뜻 | 바로 넘길 다음 문서 |
|---|---|---|
| `토큰 valid인데 왜 403` | 토큰 검증 성공은 authn 통과일 뿐이고, authz gate는 아직 남아 있다 | [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md) |
| `로그인 됐는데 이 API만 403` | 재로그인보다 role, scope, ownership 순서가 먼저다 | [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| `권한을 방금 줬는데도 403` | authz freshness나 stale deny 가능성을 먼저 연다 | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |
| `쿠키는 있는데 왜 다시 로그인` | 바깥 모양은 authz보다 browser/session continuity 문제일 가능성이 더 크다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |

짧게 정리하면:

- `token valid but 403`은 `401`이 아니라 `403` primer에서 시작하는 질문이다.
- `cookie는 있는데 왜 다시 로그인`은 `권한 부족`보다 `redirect / cookie 전송 / server 복원` 축으로 먼저 자르는 질문이다.

## 어디까지가 이 문서 범위인가

이 문서는 beginner primer라서 `응답 코드의 첫 해석`까지만 다룬다. 아래 상황은 이 문서에서 깊게 파지 않는다.

- 브라우저에서 `401` 대신 `302 -> /login`이 보이는 문제
- 권한을 방금 줬는데 `403`이나 `404`가 남는 stale deny 문제
- concealment `404`를 어떤 리소스 클래스에 적용할지 정하는 설계 문제
- 외부 에러 body, `ProblemDetail`, 내부 로그 필드 설계

이런 분기는 아래 문서로 넘기면 된다.

## 다음 단계 라우팅

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `인증`과 `인가` 자체가 아직 헷갈린다 | [인증과 인가의 차이](./authentication-vs-authorization.md) |
| `로그인 됐는데 왜 403`를 더 구조적으로 보고 싶다 | [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md) |
| `scope`와 `ownership` 차이가 헷갈린다 | [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| `토큰 valid인데 왜 403`, `권한을 방금 줬는데도 403` | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |
| Network에 `OPTIONS`만 보인다 | [Preflight Debug Checklist](./preflight-debug-checklist.md) |
| 브라우저에서는 `302 -> /login`이 보인다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| `쿠키는 있는데 왜 다시 로그인`, `Application > Cookies`에는 있는데 request `Cookie`가 헷갈린다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| `남의 주문인데 왜 404`를 더 깊게 보고 싶다 | [Concealment `404` Entry Cues](./concealment-404-entry-cues.md) |
| 권한을 방금 줬는데도 `403`/`404`가 남는다 | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |
| 응답 body를 어떻게 설계할지 궁금하다 | [Spring `ProblemDetail` Error Response Design](../spring/spring-problemdetail-error-response-design.md) |

## 한 줄 정리

처음에는 `401 = 다시 인증`, `403 = 권한 부족`, `404 = 없음 또는 존재 은닉`만 정확히 고정하고, browser redirect나 stale deny 같은 심화 분기는 관련 문서로 넘기면 된다.
