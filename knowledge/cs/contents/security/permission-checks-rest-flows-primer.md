---
schema_version: 3
title: Permission Checks In REST Flows
concept_id: security/permission-checks-rest-flows-primer
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
review_feedback_tags:
- permission checks in rest flows
- rest authorization primer
- rest object authorization beginner
- valid token is not enough
aliases:
- permission checks in rest flows
- rest authorization primer
- rest object authorization beginner
- valid token is not enough
- valid login is not enough
- login success but 403
- token valid but 403
- object-level authorization primer
- object level authorization rest api
- rest endpoint permission check order
- role scope ownership tenant rest
- role vs scope vs ownership vs tenant
symptoms:
- 로그인은 됐는데 특정 API만 403이 나오면 role, scope, ownership 중 무엇을 봐야 할지 모르겠다
- 유효한 토큰이면 특정 주문이나 예약 resource도 열려야 한다고 생각한다
- REST endpoint에서 action permission과 resource ownership 확인 순서를 코드로 설명하지 못한다
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
- contents/security/authentication-vs-authorization.md
- contents/security/permission-model-bridge-authn-to-role-scope-ownership.md
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/security/auth-failure-response-401-403-404.md
- contents/security/idor-bola-patterns-and-fixes.md
- contents/security/tenant-membership-change-session-scope-basics.md
- contents/security/delegated-admin-tenant-rbac.md
- contents/security/tenant-isolation-authz-testing.md
- contents/security/pdp-pep-boundaries-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Permission Checks In REST Flows 핵심 개념을 설명해줘
- permission checks in rest flows가 왜 필요한지 알려줘
- Permission Checks In REST Flows 실무 설계 포인트는 뭐야?
- permission checks in rest flows에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Permission Checks In REST Flows를 다루는 primer 문서다. REST API에서 `로그인 성공`과 `토큰 유효`는 출발점일 뿐이고, 실제 허용은 `action permission`, `scope`, `ownership`, `tenant`를 요청 패턴에 맞게 따로 확인해야 끝난다. 검색 질의가 permission checks in rest flows, rest authorization primer, rest object authorization beginner, valid token is not enough처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Permission Checks In REST Flows

> 한 줄 요약: REST API에서 `로그인 성공`과 `토큰 유효`는 출발점일 뿐이고, 실제 허용은 `action permission`, `scope`, `ownership`, `tenant`를 요청 패턴에 맞게 따로 확인해야 끝난다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| 미션 장면 | 이 문서에서 먼저 잡을 질문 |
|---|---|
| 일반 회원이 admin API를 호출한다 | 기능 권한이 있는가 |
| 로그인한 사용자가 남의 주문 ID를 넣는다 | resource ownership이 맞는가 |
| token은 유효한데 `403`이 나온다 | scope, role, ownership 중 어느 gate인가 |


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 문서 역할: 이 문서는 security 카테고리의 beginner `primer`다. `로그인 됐으니 호출 가능하다`, `유효한 토큰이면 객체도 열려야 한다` 같은 혼동을 REST endpoint 흐름 기준으로 자르는 entrypoint다.

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)
> - [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
> - [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Security README: 기본 primer](./README.md#기본-primer)

retrieval-anchor-keywords: permission checks in rest flows, rest authorization primer, rest object authorization beginner, valid token is not enough, valid login is not enough, login success but 403, token valid but 403, object-level authorization primer, object level authorization rest api, rest endpoint permission check order, role scope ownership tenant rest, role vs scope vs ownership vs tenant, rest flow authz ladder, endpoint authz ladder, object-level authorization beginner

## 먼저 잡는 한 문장

`로그인 성공`은 `누구인지 확인됨`이고, `인가 허용`은 `이 요청을 이 객체에 대해 지금 해도 됨`까지 확인된 상태다.

즉 아래 둘은 같은 말이 아니다.

- `이 사용자는 인증되었다`
- `이 요청은 허용된다`

---

## 15초 mental model: REST에서는 질문이 두 겹이다

REST 요청은 보통 두 질문을 같이 푼다.

1. `이 action을 할 자격이 있나?`
2. `이 특정 resource에 해도 되나?`

초보자가 자주 놓치는 건 2번이다.

| 먼저 보는 축 | 서버가 묻는 질문 | 예시 |
|---|---|---|
| action permission / role | `이 기능 종류를 해도 되나?` | 주문 조회 기능 진입, 관리자 기능 진입 |
| scope | `이 토큰이 이 API 호출을 위임받았나?` | `orders.read`, `tickets.write` |
| ownership | `이 객체가 내 범위 안인가?` | 내 주문인가, 내가 만든 문서인가 |
| tenant / context | `지금 이 tenant/workspace 문맥이 맞나?` | 같은 회사 데이터인가, 현재 workspace 것인가 |

짧게 외우면 이렇게 된다.

- role/permission: `무슨 종류의 일을 해도 되나`
- scope: `이 토큰으로 그 API를 불러도 되나`
- ownership: `이 객체가 내 범위 안인가`
- tenant: `그 범위가 지금 이 workspace 안에서 맞나`

---

## 가장 흔한 오해: 유효한 토큰이면 객체도 열려야 한다

아니다. 보통 순서는 아래처럼 나뉜다.

```text
token/session valid
AND endpoint action allowed
AND token scope allowed (if delegated token model exists)
AND resource ownership allowed
AND tenant/context allowed
```

그래서 아래 문장들은 모순이 아니라 정상적인 증상이다.

- `유효한 토큰인데 403`
- `scope 있는데 남의 주문은 안 됨`
- `내 문서인데 다른 workspace에서는 안 열림`

---

## endpoint 패턴별로 무엇을 확인하나

같은 `/orders` 계열 API여도 endpoint 패턴에 따라 체크 포인트가 달라진다.

| endpoint 패턴 | 흔한 예시 | 최소한 확인할 것 | 초보자가 자주 빠뜨리는 것 |
|---|---|---|---|
| collection list | `GET /orders` | list 권한, tenant 범위, 목록 필터 | `조회 권한만 있으면 전체 tenant 목록을 다 보여 줌` |
| single object read | `GET /orders/{id}` | read 권한, scope, ownership, tenant | `id만 맞으면 조회` |
| create | `POST /orders` | create 권한, 대상 tenant 허용, body 안의 owner/tenant 무시 또는 검증 | `클라이언트가 보낸 ownerId를 그대로 신뢰` |
| update | `PATCH /orders/{id}` | update 권한, 기존 객체 ownership, tenant, 변경 가능한 필드 정책 | `수정 전에 기존 객체 권한을 안 봄` |
| delete | `DELETE /orders/{id}` | delete 권한, ownership 또는 admin rule, tenant | `읽기 권한만 확인하고 삭제까지 허용` |

핵심은 이렇다.

- list는 `무엇을 몇 개까지 보여 줄지`
- object read는 `이 id 하나가 내 범위인지`
- create는 `누구 이름으로 만들 수 있는지`
- update/delete는 `기존 객체에 손대도 되는지`

---

## 바로 써먹는 REST flow 4개

### 1. `GET /orders`

이 endpoint는 "주문 조회 가능"만으로 끝나지 않는다.

- 주문 목록을 볼 기본 권한이 있는가
- 현재 tenant가 맞는가
- 자기 주문만 보는 사용자라면 owner filter가 붙는가
- support/operator라면 delegated 범위만 보이는가

안전한 질문:

- `이 사용자가 orders list를 볼 수 있나?`
- `보여 주는 row들이 이 사용자 범위로 이미 잘 필터링됐나?`

위험한 구현:

- `hasRole(USER)`만 보고 tenant 필터 없이 전체 목록 조회
- `scope=orders.read`만 보고 모든 주문 반환

### 2. `GET /orders/{orderId}`

여기서는 object-level authorization이 핵심이다.

- 이 사용자가 주문 상세를 볼 수 있는가
- 그중에서도 `orderId`가 내 주문인가
- 같은 tenant 주문인가

초보자용 한 줄:

`read API 권한 있음`과 `이 orderId 읽어도 됨`은 같은 말이 아니다.

### 3. `POST /orders`

생성 API는 "없는 객체니까 ownership이 아직 없다"는 이유로 방심하기 쉽다.

그래도 봐야 할 것이 있다.

- 이 tenant에 주문을 만들 권한이 있는가
- body의 `tenantId`, `ownerId`, `createdBy`를 서버가 다시 정하는가
- 다른 tenant 이름으로 생성하지 못하게 막는가

초보자가 자주 놓치는 포인트:

- `ownerId`를 request body에서 받아 그대로 저장
- 현재 로그인 사용자가 아닌 다른 tenant로 생성 허용

### 4. `PATCH /orders/{orderId}` / `DELETE /orders/{orderId}`

수정/삭제는 read보다 더 강한 action permission이 필요할 수 있다.

- `볼 수 있다`와 `바꿀 수 있다`는 다르다
- owner라도 취소는 가능하지만 환불 승인까지 가능한 것은 아닐 수 있다
- support role도 조회만 되고 삭제는 안 될 수 있다

즉 update/delete는 보통 아래 둘을 같이 본다.

- action permission: `수정/삭제 자체를 해도 되나`
- object rule: `이 객체에 대해 해도 되나`

---

## 비교표: role vs scope vs ownership vs tenant

| 축 | 답하는 질문 | 통과해도 아직 모르는 것 | 예시 |
|---|---|---|---|
| role / permission | `이 기능 종류를 써도 되나?` | 어떤 객체 id까지 허용인지 | `ROLE_SUPPORT`, `order.cancel` |
| scope | `이 토큰으로 이 API를 호출해도 되나?` | 그 API가 다루는 모든 객체가 허용인지 | `orders.read` |
| ownership | `이 객체가 내 것인가?` | 현재 tenant 문맥까지 맞는지 | `order.ownerId == me` |
| tenant / context | `이 요청이 지금 이 workspace 범위 안인가?` | action 자체 권한이 있는지 | `order.tenantId == activeTenantId` |

한 줄 정리:

- scope는 보통 `API 범위`
- ownership은 보통 `객체 관계`
- tenant는 보통 `데이터 경계`

셋은 서로 대체재가 아니다.

---

## 같은 token인데 어떤 ID는 되고 어떤 ID는 왜 안 되나

초보자가 많이 묻는 질문을 그대로 풀면 이렇다.

| 관찰 | 실제 뜻 |
|---|---|
| 같은 token으로 `/orders/101`은 되는데 `/orders/202`는 안 됨 | token은 유효하지만 object rule이 다르다 |
| 같은 사용자여도 workspace A에서는 되고 B에서는 안 됨 | tenant/context rule이 다르다 |
| `orders.read`는 있는데 수정은 안 됨 | read와 update action permission이 다르다 |
| owner인데 admin endpoint는 안 됨 | ownership만으로 민감 action까지 열리면 안 된다 |

즉 같은 token이더라도 대상 객체와 tenant가 달라지면 결과도 달라지는 것이 정상이다.

---

## beginner checklist: REST endpoint를 볼 때 최소 질문 6개

새 endpoint를 보거나 리뷰할 때 아래 6개만 먼저 물어도 큰 사고를 많이 줄일 수 있다.

1. 이 요청은 먼저 `누구인지`를 확인했나?
2. 이 action 자체를 할 role/permission이 있나?
3. delegated token 모델이면 필요한 scope가 있나?
4. path의 `{id}` 또는 body의 대상 객체가 내 범위인지 확인하나?
5. 같은 사용자라도 다른 tenant/workspace면 막히나?
6. body 안의 `ownerId`, `tenantId`, `role` 같은 민감 필드를 클라이언트 입력 그대로 믿지 않나?

특히 4번과 5번이 object-level authorization의 핵심이다.

---

## 흔한 실수 5개

1. `로그인 성공`만 보고 상세 조회를 허용한다.
2. `scope=read`만 보고 모든 객체 read를 허용한다.
3. list API에 tenant/ownership 필터를 빼먹는다.
4. create API에서 `ownerId`와 `tenantId`를 body 값 그대로 저장한다.
5. update/delete에서 `read 가능`과 `변경 가능`을 같은 권한으로 취급한다.

이 실수들은 대부분 `유효한 사용자`와 `허용된 객체 작업`을 같은 말로 착각할 때 생긴다.

---

## 30초 예시: 주문 API를 한 번에 읽는 법

주문 시스템이 아래 endpoint를 가진다고 해 보자.

- `GET /orders`
- `GET /orders/{id}`
- `POST /orders`
- `PATCH /orders/{id}`

초보자는 이렇게 읽으면 된다.

| endpoint | 먼저 보는 질문 | 그다음 보는 질문 |
|---|---|---|
| `GET /orders` | 목록 조회 권한이 있나 | 어떤 tenant/order만 보여 줘야 하나 |
| `GET /orders/{id}` | 상세 조회 권한이 있나 | 이 `id`가 내 주문인가, 같은 tenant인가 |
| `POST /orders` | 생성 권한이 있나 | 누구 tenant로 생성되는가, owner를 누가 정하는가 |
| `PATCH /orders/{id}` | 수정 권한이 있나 | 이 객체를 수정해도 되는가, 어떤 필드까지 가능한가 |

이 표를 한 줄로 줄이면:

`endpoint permission`을 먼저 보고, 바로 이어서 `object/tenant permission`을 본다.

---

## 언제 403이고 언제 404인가

이 문서의 중심은 permission check지만, 결과 응답은 초보자가 같이 헷갈린다.

- 인증 자체가 실패하면 보통 `401`
- 인증은 됐지만 action/object rule에서 막히면 보통 `403`
- 남의 private resource 존재를 숨기고 싶으면 concealment `404`를 쓸 수 있음

응답 코드까지 같이 정리하려면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)를 이어서 보면 된다.

---

## 이 문서 다음에 어디로 가면 좋은가

- role/scope/ownership 차이를 더 또렷하게 보고 싶으면 [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- authn 다음에 authz가 어떤 순서로 붙는지 한 장으로 다시 보고 싶으면 [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)
- 남의 주문/문서 ID를 넣는 취약점으로 바로 연결해서 보고 싶으면 [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
- tenant가 섞이는 beginner 증상이 더 강하면 [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- 분기를 다시 고르고 싶으면 [Security README: 기본 primer](./README.md#기본-primer)

## 한 줄 정리

REST 인가의 핵심은 `로그인했는가`가 아니라 `이 action을 이 객체에 대해 이 tenant 문맥에서 해도 되는가`를 끝까지 따로 확인하는 것이다.
