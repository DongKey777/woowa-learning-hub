# Beginner Guide to Auth Failure Responses: `401` / `403` / `404`

> 한 줄 요약: 먼저 `인증이 성립했는가?`를 보고, 그다음 `권한이 충분한가?`를 보고, 마지막으로 `존재를 숨길 정책인가?`를 보면 `401`, `403`, `404`를 초보자도 일관되게 구분할 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)
> - [Spring ProblemDetail / Error Response Design](../spring/spring-problemdetail-error-response-design.md)

retrieval-anchor-keywords: 401 403 404 beginner guide, 401 vs 403 vs 404, when to use 401 403 404, login required vs forbidden vs not found, unauthorized forbidden not found, auth failure response, authn authz response guide, expired token 401, missing token 401, missing scope 403, role missing 403, other user's resource 404, conceal existence 404, IDOR concealment, WWW-Authenticate, security response semantics, access denied contract, hide existence, API authorization errors, browser 401 vs 302, login redirect instead of 401, browser login page instead of 401, 401 302 bounce beginner, inconsistent 401 404, 401 404 flip, tenant-specific 403, only one tenant 403, stale deny, cached concealment, cached 404 after grant, 401 response body example, 403 response body example, 404 response body example, safe error body auth failure, auth failure problem detail example, concealment 404 body, auth failure request_id example, auth deny log fields, 401 403 404 internal log fields, recovery hint without information leak

## 이 문서 다음에 보면 좋은 문서

- 아직 `인증`과 `인가`의 차이가 흐리면 [인증과 인가의 차이](./authentication-vs-authorization.md)로 돌아가 `principal`, `session`, `permission model`부터 다시 맞추면 된다.
- raw `401`을 기대했는데 브라우저에서는 `302 -> /login`이나 login HTML이 보여 더 헷갈리면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 가서 browser redirect와 API 계약을 먼저 분리하면 된다.
- "다른 사람 리소스에 왜 `404`를 줄 수 있지?"가 더 궁금하면 [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)에서 객체 단위 concealment를 이어 보면 된다.
- gateway, filter, app이 각각 어디서 `401` / `403` / `404`를 내야 하는지 설계로 보고 싶으면 [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)로 이어진다.
- 권한을 방금 줬는데도 `403`이나 concealment `404`가 남는 운영 문제는 [Authorization Caching / Staleness](./authorization-caching-staleness.md)에서 따로 본다.

---

## 먼저 10초 판별표

| 먼저 확인할 질문 | 대표 예시 | 바깥 응답 | 클라이언트가 보통 해야 할 일 |
|---|---|---|---|
| 인증 정보가 없거나 깨졌나? | 로그인 안 함, 만료 토큰, 잘못된 서명, 깨진 세션 쿠키 | `401 Unauthorized` | 다시 로그인, 토큰 갱신, 인증 정보 재전송 |
| 누구인지는 알겠지만 권한이 부족한가? | 일반 사용자가 관리자 API 호출, scope 부족 | `403 Forbidden` | 권한 요청, role 확인, 요청 자체 중단 |
| 리소스가 없거나 존재를 숨겨야 하나? | 없는 주문 번호, 다른 사람 주문 번호, cross-tenant invoice | `404 Not Found` | ID 확인, concealment 정책인지 확인 |

초보자에게 가장 중요한 한 줄은 이것이다.

- `401`: `누구인지 다시 증명해라`
- `403`: `누구인지는 알겠는데 너는 안 된다`
- `404`: `없거나, 있다고 말해주지 않겠다`

`401 Unauthorized`라는 이름 때문에 `403`과 헷갈리기 쉽지만, 실무에서는 대체로 `인증 실패` 쪽에 쓴다고 기억하면 된다.
브라우저 page 요청에서는 이 `401` 상황이 raw 숫자 대신 `302 -> /login`으로 감싸져 보일 수 있는데, 그 차이는 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 따로 정리한다.

---

## 인증(authn)과 인가(authz)를 HTTP 응답으로 연결하기

[인증과 인가의 차이](./authentication-vs-authorization.md)에서 본 흐름을 다시 가져오면 순서는 이렇다.

1. credential, session, token으로 `인증`을 시도한다.
2. 성공하면 현재 요청의 `principal`이 만들어진다.
3. principal과 resource, action을 가지고 `인가`를 판단한다.
4. 마지막으로 concealment policy가 있으면 외부 응답을 `404`로 바꿀 수 있다.

즉 질문 순서가 중요하다.

- 인증이 아직 안 됐으면 `403`까지 갈 수 없다.
- 인증은 됐는데 권한이 부족하면 `401`이 아니라 `403`에 가깝다.
- 권한 부족이라도 리소스 존재를 숨길 정책이면 외부에는 `404`를 줄 수 있다.

---

## 초보자용 예시 3개

### 1. `401`: 로그인 안 했거나 인증 정보가 깨졌다

예시:

- `Authorization` 헤더 없이 `GET /api/me` 호출
- 만료된 bearer token으로 `GET /api/orders`
- 세션 쿠키가 만료된 상태로 `POST /profile`

왜 `401`인가:

- 서버가 아직 `이 요청이 누구인지` 확정하지 못했다.
- 즉 principal을 만들 수 없거나, 기존 인증 상태를 신뢰할 수 없다.

클라이언트 힌트:

- 다시 로그인하거나 token refresh를 시도한다.
- API라면 `WWW-Authenticate: Bearer ...` 같은 challenge가 같이 갈 수 있다.

### 2. `403`: 로그인은 됐지만 허용되지 않는다

예시:

- `USER` role 계정이 `GET /admin/reports` 호출
- `read:orders`만 있는 token으로 `POST /orders/approve`
- 같은 tenant 사용자는 맞지만 `refund.approve` permission이 없음

왜 `403`인가:

- 서버는 principal을 알고 있다.
- 하지만 role, scope, policy, ownership 조건 중 하나가 허용되지 않았다.

클라이언트 힌트:

- 재로그인만으로 해결되지 않는 경우가 많다.
- 권한 요청, 관리자 승인, 더 높은 assurance step-up이 필요한지 봐야 한다.

### 3. `404`: 진짜 없거나, 있어도 있다고 말하지 않는다

예시:

- `GET /orders/999999`인데 진짜 없는 주문 번호
- 사용자 A가 사용자 B의 주문 `GET /orders/123` 시도
- 다른 tenant의 invoice id를 넣었고, 이 서비스는 객체 존재를 숨기기로 한 상태

왜 `404`인가:

- 진짜 없는 경우일 수도 있다.
- 또는 "있다/없다" 자체가 민감해서 존재를 숨기기로 한 security policy일 수도 있다.

클라이언트 힌트:

- 입력한 ID가 맞는지 먼저 본다.
- user-owned resource나 multi-tenant resource라면 concealment `404`일 가능성도 같이 본다.

---

## 제일 자주 틀리는 판단 순서

### 1. token이나 session이 깨졌는데 `403`을 준다

문제:

- 사실은 인증 실패인데 권한 부족처럼 보인다.

왜 나쁜가:

- 클라이언트가 권한 요청 화면을 띄우거나, 운영자가 role 문제로 잘못 추적한다.

더 나은 기준:

- missing token
- expired token
- invalid signature
- malformed credential

위 네 가지는 보통 `401` bucket에 먼저 넣는다.

### 2. 로그인된 사용자의 권한 부족을 `401`로 준다

문제:

- principal은 이미 확인됐는데, 모든 deny를 `401`로 내려 버린다.

왜 나쁜가:

- 사용자는 계속 다시 로그인하지만 결과가 안 바뀐다.
- 브라우저 앱에서는 login loop처럼 보일 수 있다.

더 나은 기준:

- principal이 있고 policy deny라면 기본값은 `403`으로 본다.

### 3. 다른 사람 리소스 조회에 무조건 `403`을 준다

문제:

- 공격자가 "그 주문 번호는 실제로 존재한다"는 힌트를 얻는다.

더 나은 기준:

- user-owned resource, multi-tenant detail endpoint처럼 존재 노출이 민감하면 `404` concealment를 검토한다.
- 대신 내부 로그에는 실제 이유를 남긴다.

### 4. `404`를 아무 데나 섞어 쓴다

문제:

- 어떤 endpoint는 `403`, 어떤 endpoint는 `404`라서 클라이언트 계약이 흔들린다.

더 나은 기준:

- `404` concealment는 `리소스 클래스 단위 정책`으로 정한다.
- 예를 들어 "사용자 개인 주문 상세는 concealment `404`, 관리자 콘솔 privilege 부족은 `403`"처럼 문서화한다.

### 5. 외부 응답 본문에 너무 많은 정보를 넣는다

문제:

- `order 123 exists but belongs to user 42` 같은 메시지는 정보 노출이다.

더 나은 기준:

- 외부 응답은 짧고 표준화한다.
- 내부 로그에는 실제 deny reason을 남긴다.

### 6. personalized deny를 캐시해 버린다

문제:

- 사용자별 `403` / `404`가 다른 사람에게 재사용될 수 있다.
- stale deny 때문에 권한을 줬는데도 `403`이나 concealment `404`가 계속 남을 수 있다.

더 나은 기준:

- auth-dependent deny 응답은 cache policy를 보수적으로 둔다.
- 이 이슈는 운영 관점에서 [Authorization Caching / Staleness](./authorization-caching-staleness.md)로 이어서 본다.

---

## 실전에서 바로 쓰는 판단 체크리스트

1. credential이나 session이 유효한가?
2. principal이 실제로 만들어졌는가?
3. role, scope, ownership, tenant policy가 허용하는가?
4. 이 리소스 클래스는 존재를 숨기기로 했는가?

이 순서로 보면 대부분 정리된다.

- 1번에서 실패하면 `401`
- 1번은 통과했고 3번에서 실패하면 기본값은 `403`
- 3번에서 실패했더라도 4번 concealment policy가 있으면 외부에는 `404`

초보자는 특히 `1번에서 이미 실패했는데 3번까지 판단하려는 습관`을 끊는 것이 중요하다.

---

## response matrix 예시

| 상황 | 내부 판단 | 외부 응답 |
|---|---|---|
| bearer token 없음 | `MISSING_CREDENTIAL` | `401` |
| bearer token 만료 | `INVALID_CREDENTIAL` | `401` |
| 로그인은 됐지만 관리자 role 없음 | `ADMIN_ROLE_REQUIRED` | `403` |
| 로그인은 됐지만 `write:orders` scope 없음 | `INSUFFICIENT_SCOPE` | `403` |
| 다른 사람 주문 상세 접근, concealment policy 있음 | `OWNERSHIP_MISMATCH` | `404` |
| 요청한 리소스가 진짜 없음 | `RESOURCE_MISSING` | `404` |

핵심은 `외부 상태 코드보다 내부 reason taxonomy를 먼저 고정`하는 것이다.

---

## 안전한 에러 body 예시와 내부 로그 매핑

status code만 맞는다고 계약이 끝나는 것은 아니다.
외부 body는 `다음에 무엇을 해야 하는지`만 알려 주고,
실제 실패 원인 분류는 내부 log와 trace에서만 복원 가능하게 두는 편이 안전하다.

외부 body의 최소 공통 필드는 보통 이 정도면 충분하다.

- `type`: 문서화 가능한 stable problem type
- `title`: 사람이 읽는 짧은 제목
- `status`: HTTP status
- `code`: 클라이언트 계약용 stable application code
- `detail`: 복구 힌트는 주되 내부 판단 근거는 숨긴 짧은 설명
- `request_id`: 지원팀, log, trace와 조인할 키

내부 log는 최소한 아래 세 필드를 외부 body와 맞춰 두는 편이 좋다.

- `request_id`
- `http_status`
- `external_code`

그래야 support, SIEM, trace가 같은 실패를 한 번에 묶을 수 있다.

### 1. `401` 예시: 다시 인증하라는 힌트만 준다

외부 body 예시:

```json
{
  "type": "https://api.example.com/problems/authentication-required",
  "title": "Authentication required",
  "status": 401,
  "code": "AUTHENTICATION_REQUIRED",
  "detail": "Sign in again or refresh your credentials, then retry the request.",
  "request_id": "req_7V1p4rM2"
}
```

같이 갈 수 있는 header 예시:

- `WWW-Authenticate: Bearer realm="api"`

이 body는 복구 방향은 주지만, 아래 정보는 숨긴다.

- token이 만료됐는지
- 서명이 깨졌는지
- issuer가 맞지 않는지
- session cookie가 조작됐는지

matching internal log 예시:

```json
{
  "event": "auth.failure",
  "request_id": "req_7V1p4rM2",
  "trace_id": "8f3a0d7d5fb1a0e2",
  "http_status": 401,
  "external_code": "AUTHENTICATION_REQUIRED",
  "internal_reason": "EXPIRED_TOKEN",
  "credential_kind": "bearer",
  "principal_id": null,
  "issuer": "https://id.example.com",
  "route": "GET /api/orders/{id}",
  "resource_type": "order",
  "resource_lookup_key_hash": "sha256:8bbf2a4b...",
  "client_id": "web-frontend"
}
```

핵심은 `expired`, `invalid signature`, `issuer mismatch`를 외부 body에 직접 쓰지 않고,
내부에서는 failure bucket으로 구분해 alert와 triage에 쓰는 것이다.

### 2. `403` 예시: 권한 부족이라는 사실만 알려 준다

외부 body 예시:

```json
{
  "type": "https://api.example.com/problems/insufficient-permission",
  "title": "Forbidden",
  "status": 403,
  "code": "INSUFFICIENT_PERMISSION",
  "detail": "This account cannot perform this action. Request access if you believe it is required.",
  "request_id": "req_C83mP2Q9"
}
```

이 body는 아래 정보는 감춘다.

- 정확히 어떤 role이 없는지
- 어떤 scope가 빠졌는지
- tenant mismatch인지
- step-up이 필요한지

matching internal log 예시:

```json
{
  "event": "authz.deny",
  "request_id": "req_C83mP2Q9",
  "trace_id": "ae71f0bfe0219c61",
  "http_status": 403,
  "external_code": "INSUFFICIENT_PERMISSION",
  "principal_id": "user_12345",
  "tenant_id": "tenant_a",
  "action": "orders.approve",
  "resource_type": "order",
  "resource_id": "ord_1024",
  "decision": "deny",
  "internal_reason": "SCOPE_MISSING",
  "policy_version": "authz-2026-04-14",
  "auth_assurance_level": "aal1",
  "step_up_required": false,
  "cache_result": "miss"
}
```

여기서 외부 body는 "권한이 없다"까지만 말하고,
내부 log는 실제 remediation에 필요한 `internal_reason`, `policy_version`, `step_up_required`를 따로 남긴다.

### 3. `404` 예시: 진짜 없음과 concealment를 같은 몸체로 보낸다

외부 body 예시:

```json
{
  "type": "https://api.example.com/problems/resource-not-found",
  "title": "Not Found",
  "status": 404,
  "code": "RESOURCE_NOT_FOUND",
  "detail": "The requested resource was not found. Verify the identifier or reopen it from a list you can access.",
  "request_id": "req_N4m8L0T1"
}
```

이 body는 아래 정보를 끝까지 숨긴다.

- 리소스가 실제로 존재하는지
- 존재한다면 누구 소유인지
- cross-tenant mismatch인지
- concealment policy가 발동됐는지

matching internal log 예시:

```json
{
  "event": "resource.lookup",
  "request_id": "req_N4m8L0T1",
  "trace_id": "2b966a9f89d6d834",
  "http_status": 404,
  "external_code": "RESOURCE_NOT_FOUND",
  "principal_id": "user_12345",
  "tenant_id": "tenant_a",
  "action": "orders.read",
  "resource_type": "order",
  "resource_lookup_key_hash": "sha256:5f9df4a1...",
  "lookup_outcome": "FOUND_BUT_CONCEALED",
  "internal_reason": "OWNERSHIP_MISMATCH",
  "concealment_applied": true,
  "policy_version": "authz-2026-04-14"
}
```

중요한 포인트는 진짜 missing이든 concealment deny든 외부 body를 거의 동일하게 유지하는 것이다.
차이는 내부 `lookup_outcome`, `internal_reason`, `concealment_applied`에서만 복원한다.

### body에 넣지 말아야 할 문장 예시

| status | 피해야 할 외부 문장 | 왜 나쁜가 |
|---|---|---|
| `401` | `token expired at 2026-04-14T10:03:11Z`, `kid abc123 not found` | validation surface와 verifier 상태를 너무 자세히 드러낸다 |
| `403` | `requires role=SUPER_ADMIN`, `tenant=finance-prod only` | 내부 권한 모델과 tenant topology를 노출한다 |
| `404` | `order 123 exists but belongs to another user` | concealment policy를 완전히 무너뜨린다 |

복구 힌트는 괜찮다.
하지만 힌트는 `다시 로그인`, `접근 권한 요청`, `ID 확인 후 안전한 목록에서 다시 열기` 정도로 멈추는 편이 좋다.

---

## 코드로 보면 더 쉬운 기준

```java
public HttpStatus toExternalStatus(DenyReason reason, boolean concealExistence) {
    return switch (reason) {
        case MISSING_CREDENTIAL, INVALID_CREDENTIAL -> HttpStatus.UNAUTHORIZED;
        case INSUFFICIENT_SCOPE, ADMIN_ROLE_REQUIRED -> HttpStatus.FORBIDDEN;
        case OWNERSHIP_MISMATCH -> concealExistence
                ? HttpStatus.NOT_FOUND
                : HttpStatus.FORBIDDEN;
        case RESOURCE_MISSING -> HttpStatus.NOT_FOUND;
    };
}
```

이 예시는 한 가지를 보여 준다.

- `ownership mismatch` 같은 내부 reason은 서비스 정책에 따라 `403`도 될 수 있고 `404`도 될 수 있다.
- 반면 `missing credential`은 보통 `401` bucket을 벗어나지 않는다.

---

## 운영에서 놓치지 말아야 할 2가지

### 1. 외부 응답과 내부 로그는 분리한다

외부가 `404`여도 내부에는 남겨야 한다.

- request id
- http status
- external code
- internal reason
- principal id
- resource type
- resource lookup key 또는 hash
- concealment applied 여부
- policy version
- correlation / trace id

그래야 운영자가 `진짜 없음`과 `concealment deny`를 구분할 수 있다.
이 필드 묶음은 [AuthZ Decision Logging Design](./authz-decision-logging-design.md)과 [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)에서 보는 decision log, bucketed metric과도 바로 이어진다.

### 2. gateway와 app이 같은 계약을 써야 한다

예를 들어:

- gateway는 만료 token에 `401`
- 앱은 같은 경로에서 scope 부족에 `403`
- 어떤 bypass route는 예외 매핑 실수로 `500`

이렇게 섞이면 클라이언트는 재로그인해야 하는지, 권한을 요청해야 하는지, 버그인지 알 수 없다.
그래서 `401` / `403` / `404`는 controller 한 군데의 취향이 아니라 edge-to-service contract다.

---

## 꼬리질문

> Q: `401`과 `403`의 가장 큰 차이는 무엇인가요?
> 의도: 인증 실패와 권한 부족을 분리하는지 확인
> 핵심: `401`은 유효한 인증 자격이 없고, `403`은 principal은 알지만 허용되지 않는 경우다.

> Q: 로그인은 했는데 관리자 페이지가 안 열립니다. `401`일까요 `403`일까요?
> 의도: authn 성공 뒤 authz 실패를 구분하는지 확인
> 핵심: 보통 `403`이다. 재로그인보다 권한이 맞는지 먼저 본다.

> Q: 왜 다른 사람 주문 조회에 `404`를 줄 수 있나요?
> 의도: concealment policy를 이해하는지 확인
> 핵심: 존재 자체를 숨겨 enumeration을 어렵게 하려는 선택일 수 있다.

> Q: `401 Unauthorized`라는 이름인데 왜 권한 부족이 아니라 인증 실패 쪽인가요?
> 의도: 상태 코드 이름과 실무 의미를 분리하는지 확인
> 핵심: 이름 때문에 헷갈리지만, 실무에서는 대체로 missing/invalid credential 쪽에 쓴다.

## 한 줄 정리

`401 = 다시 인증`, `403 = 권한 부족`, `404 = 진짜 없음 또는 존재 은닉`으로 먼저 외우고, 실제 구현에서는 `인증 -> 인가 -> concealment policy` 순서로 판단하면 된다.
