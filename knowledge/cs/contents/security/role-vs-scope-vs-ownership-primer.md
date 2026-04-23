# Role vs Scope vs Ownership Primer

> 한 줄 요약: `role check`, OAuth `scope check`, `ownership check`는 모두 인가에 속하지만 서로 다른 질문에 답한다. 셋을 분리해야 `scope=orders.read`를 "모든 주문 읽기"로 오해하거나, role만 보고 IDOR를 놓치는 실수를 줄일 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
> - [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Security README: 기본 primer](./README.md#기본-primer)
> - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: role vs scope vs ownership primer, role check vs scope check vs ownership check, oauth scope vs role, scope is not ownership, role is not ownership, resource ownership check primer, object ownership primer, object-level authorization beginner, role scope ownership difference, orders.read does not mean every order, support role but not every ticket, beginner authz primer, oauth scope primer, scope vs audience vs permission, audience is not scope, ownership check before IDOR, object access rule basics

## 이 문서 다음에 보면 좋은 문서

- authn / authz / principal / session 자체가 아직 섞이면 [인증과 인가의 차이](./authentication-vs-authorization.md)로 먼저 돌아가면 된다.
- `roles`, `scope`, `ROLE_`, `hasRole`, `hasAuthority` 같은 문자열 층위가 더 헷갈리면 [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)로 이어 가면 된다.
- OAuth에서 scope가 왜 생기고 누가 주는지 흐름 자체를 다시 잡고 싶으면 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)를 보면 된다.
- OAuth `scope`, token `audience`, 내부 app permission이 모두 같은 "권한"처럼 들리면 [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)으로 이어 가면 된다.
- "남의 주문 ID를 넣었을 때 왜 ownership check가 핵심인가?"를 바로 이어서 보려면 [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)로 내려가면 된다.
- 바깥 응답을 `403`으로 줄지 concealment `404`로 줄지까지 같이 정리하려면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)를 이어 보면 된다.

---

## 먼저 15초 구분표

| 무엇을 보는가 | 이 검사가 답하는 질문 | 주로 어디서 오나 | 이것만으로는 부족한 이유 |
|---|---|---|---|
| Role check | `이 주체가 이 기능 영역에 들어올 자격이 있나?` | 우리 앱의 role / authority / permission bundle | 특정 리소스가 본인 것인지, 같은 tenant인지까지는 모른다 |
| OAuth scope check | `이 토큰이 이 API 범위를 호출하도록 위임됐나?` | authorization server가 넣은 `scope` claim | 토큰이 `orders.read`를 가져도 어떤 주문까지 읽는지는 모른다 |
| Ownership check | `이 주체가 지금 이 객체에 접근해도 되나?` | 서비스 DB, authz graph, resource metadata | 기본 action 자격이나 delegated scope가 없으면 owner여도 바로 허용되면 안 된다 |

핵심은 한 줄이다.

- role은 `기능 묶음`
- scope는 `위임된 API 범위`
- ownership은 `특정 객체와의 관계`

셋은 같은 단어가 아니라, 보통 한 요청 안에서 같이 써야 하는 서로 다른 축이다.

---

## 안전한 읽기 순서

초보자는 아래 순서로 보면 거의 안 헷갈린다.

1. 먼저 `누구인지` 확인한다.
2. 그다음 이 기능 영역에 들어올 `role/permission`이 있는지 본다.
3. OAuth token 기반 호출이면 이 action을 위한 `scope`가 있는지 본다.
4. 마지막으로 지금 만지는 `resource`가 본인 것인지, 같은 tenant인지, 특별 관계가 있는지 본다.

즉 아래처럼 생각하면 된다.

```text
authenticated
AND coarse role/permission gate
AND delegated scope gate(if token-based delegation exists)
AND resource ownership or tenant/context rule
```

어느 하나를 다른 하나로 대체하면 오해가 생긴다.

- role이 있다고 ownership이 자동 통과되지는 않는다.
- scope가 있다고 모든 객체를 읽을 수 있는 것은 아니다.
- owner라고 해서 role/scope 없이 민감 action이 열리면 안 된다.

---

## 예시 1: `scope=orders.read`인데 왜 모든 주문을 읽으면 안 되나

주문 상세 API를 생각해 보자.

- 사용자는 로그인했다.
- token에는 `scope=orders.read`가 있다.
- 앱 role도 일반 사용자용 read path에는 들어갈 수 있다.

그래도 `/orders/123`을 읽을 수 있는지는 별도다.

- 그 주문이 본인 주문인가
- 같은 tenant 주문인가
- support delegated session이면 해당 case에 묶인 범위 안인가

즉 `orders.read`는 보통 `주문 읽기 API를 호출할 수 있는 범위`이지,
`모든 주문 객체를 읽어도 된다`는 뜻이 아니다.

이 ownership / relation check가 빠지면 바로 IDOR/BOLA 쪽 사고로 이어진다.

---

## 예시 2: `ROLE_SUPPORT`가 있어도 모든 티켓을 보면 안 되는 이유

support operator API라고 해서 role만 보면 위험하다.

- `ROLE_SUPPORT`는 support 기능군 진입 자격일 수 있다.
- `scope=tickets.read`는 support tool token이 ticket read API를 호출할 수 있다는 뜻일 수 있다.
- 하지만 특정 ticket이 `이 운영자가 지금 봐도 되는 티켓인가`는 또 다른 질문이다.

실서비스에서는 보통 아래가 더 붙는다.

- 같은 tenant인가
- 현재 acting-on-behalf-of 세션인가
- 이 케이스에 실제로 배정됐는가
- break-glass approval이 살아 있는가

즉 support role과 scope는 entry gate에 가깝고,
특정 ticket 접근 허용은 ownership 또는 relationship policy가 마무리한다.

---

## 예시 3: owner라고 해서 항상 허용되지는 않는다

ownership check를 "최종 만능 키"처럼 생각해도 틀린다.

예를 들어:

- 본인 글 수정은 owner check가 핵심일 수 있다.
- 하지만 `refund.approve`, `tenant.user.invite`, `admin.report.read` 같은 action은 owner 개념만으로 결정되지 않는다.
- OAuth delegated client라면 owner라도 필요한 scope가 없으면 막혀야 한다.

즉 ownership은 주로 `이 객체가 누구 것인가`를 묻고,
role/scope는 `이 종류의 행동 자체가 허용되는가`를 묻는다.

---

## 자주 하는 오해 4개

### 1. role이 있으면 그 role 관련 객체는 전부 볼 수 있다

아니다. role은 보통 기능 묶음이나 coarse entry gate다. 객체별 허용은 ownership, tenant, state rule이 따로 붙는다.

### 2. OAuth scope가 있으면 앱 내부 permission도 끝난다

아니다. scope는 authorization server가 준 위임 범위일 뿐이고, 앱 내부 객체 정책까지 자동으로 설명하지 못한다.

### 3. owner면 role이나 scope는 볼 필요가 없다

아니다. owner check는 객체 관계를 설명할 뿐, 민감 action 자격이나 delegated token 범위를 대체하지 못한다.

### 4. 셋 중 하나만 통과하면 된다

대부분의 실서비스는 반대다. `역할에 맞는 주체인가`, `이 토큰이 이 API를 부를 수 있나`, `이 객체가 정말 이 주체의 범위 안인가`를 함께 봐야 한다.

---

## 10초 기억법

- role: `어떤 종류의 사용자/운영자/서비스인가`
- scope: `이 토큰에 어떤 API 범위를 위임했는가`
- ownership: `이 특정 리소스가 이 주체의 범위 안에 있는가`

이 셋을 분리하면 `scope가 있는데 왜 403/404지?`, `role이 있는데 왜 남의 주문은 못 보지?`, `owner인데 왜 더 높은 권한이 필요하지?` 같은 질문을 훨씬 안전하게 해석할 수 있다.

## 한 줄 정리

role check는 기능 진입 자격, OAuth scope check는 토큰 위임 범위, ownership check는 특정 객체와의 관계를 본다. 같은 요청에서 셋이 모두 필요할 수 있으며, 특히 ownership check를 빼면 IDOR/BOLA가 시작된다.
