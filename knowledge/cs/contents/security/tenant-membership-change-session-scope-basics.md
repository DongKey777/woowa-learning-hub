# Tenant Membership Change vs Session Scope Basics

> 한 줄 요약: org/team/tenant 이동은 단순 UI 선택 변경이 아니라 현재 session이 들고 있는 active tenant, membership snapshot, derived scope를 다시 맞춰야 하는 보안 이벤트다.

**난이도: 🟢 Beginner**

관련 문서:

- [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
- [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
- [Authorization Caching / Staleness](./authorization-caching-staleness.md)
- [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)
- [Spring Security 기초](../spring/spring-security-basics.md)

retrieval-anchor-keywords: tenant membership change, tenant membership move, session scope basics, org move session refresh, active tenant stale, stale tenant session, cross-tenant session bleed, membership version, tenant membership removed still access, old tenant still visible after move, 테넌트 세션 뭐예요, beginner tenant session scope, 처음 배우는 테넌트 권한

## 이 문서 다음에 보면 좋은 문서

- role/permission 변경과 같은 큰 그림을 먼저 잡고 싶으면 [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)부터 보면 된다.
- `role`, `scope`, `ownership`, `tenant`가 각각 다른 질문이라는 점이 아직 헷갈리면 [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)를 먼저 붙이면 된다.
- stale allow/deny가 cache 때문인지, session claim 때문인지 더 직접적으로 보고 싶으면 [Authorization Caching / Staleness](./authorization-caching-staleness.md)와 [Authorization Graph Caching](./authorization-graph-caching.md)으로 내려가면 된다.
- 결국 cross-tenant leak를 막는 마지막 안전망은 [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)이다.
- HR/SCIM 이벤트 뒤 membership tail이 남는 운영 문제까지 이어 보고 싶으면 [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)로 이어진다.

---

## 먼저 15초 그림

| 바뀐 것 | stale session이 잘못 들고 있을 수 있는 것 | 안전한 기본 동작 |
|---|---|---|
| tenant membership 제거 | old `activeTenantId`, old tenant-scoped role | 다음 요청부터 old tenant 접근을 deny하고 session context를 refresh 또는 revoke |
| 팀 이동 | old team path, old list/filter scope | team-derived scope를 다시 계산하고 관련 cache를 무효화 |
| org/tenant 이동 | old org tree, old workspace selector, old ownership 문맥 | active org/tenant를 초기화하고 최신 membership으로 재평가 |
| 새 tenant membership 추가 | session 안에 없는 새 membership | refresh 뒤에만 새 tenant를 노출하고 allow 판단에 포함 |

핵심은 이것이다.

- browser가 들고 있는 `selected tenant`는 힌트일 뿐이다.
- backend는 매 요청에서 그 tenant가 아직 현재 사용자 membership 안에 있는지 확인해야 한다.
- membership이 바뀌었는데 session context를 그대로 두면 stale cross-tenant access가 생길 수 있다.

---

## 왜 role 문자열이 그대로여도 위험한가

초보자는 보통 이렇게 생각한다.

- `ROLE_USER`는 그대로다
- 로그인도 안 끊겼다
- 그러면 계속 비슷하게 접근해도 되지 않나

하지만 multi-tenant 시스템에서는 `어느 tenant/org/team 문맥에서 ROLE_USER인가`가 더 중요할 때가 많다.

예를 들어:

- tenant A의 `ROLE_USER`
- tenant B의 `ROLE_USER`
- 같은 tenant 안에서도 team alpha의 manager
- org 이동으로 ownership tree가 바뀐 사용자

이들은 role 문자열만 보면 비슷해 보여도 실제 데이터 접근 범위는 다르다.

즉 org/team/tenant 이동은 `role change가 없더라도` session freshness와 authz correctness를 동시에 흔든다.

---

## session scope에는 무엇이 숨어 있나

session이나 token에는 보통 아래 정보가 직간접적으로 들어 있다.

- 현재 로그인한 user id
- active tenant id 또는 current workspace id
- membership snapshot이나 coarse role
- team/org path에서 파생한 data scope
- 최근 step-up 시각이나 assurance level

문제는 이 중 일부가 `직접 claim`이 아니어도 이미 서버 로직에 녹아 있을 수 있다는 점이다.

- session store row에 `currentTenantId`가 들어 있음
- gateway cache key가 `userId + tenantId`를 들고 있음
- list query builder가 session의 team path를 그대로 씀
- BFF가 browser의 last-selected workspace를 내부 session에 복사함

그래서 org/team/tenant move 뒤에는 `권한 테이블만 바꾸면 끝`이 아니다.  
기존 session context와 파생 cache까지 같이 정리해야 한다.

---

## 가장 중요한 규칙: selected tenant는 신뢰 anchor가 아니다

가장 흔한 실수는 browser나 mobile app이 보낸 `tenant_id`를 그대로 현재 문맥으로 받아들이는 것이다.

안전한 모델은 이렇다.

1. 클라이언트는 `tenant_id`나 `workspace_id`를 보낼 수 있다.
2. 서버는 이 값을 `힌트`로만 본다.
3. 서버는 최신 membership source of truth 또는 versioned cache로 `이 사용자가 지금도 그 tenant에 속하는가`를 다시 확인한다.
4. 확인이 실패하면 old tenant 문맥으로 계속 진행하지 않고 refresh, deny, tenant-picker reset 중 하나로 끊는다.

즉 `selected tenant`는 UX 상태일 수는 있어도 authorization의 최종 근거가 되어서는 안 된다.

---

## 이동 이벤트가 나면 무엇을 refresh해야 하나

org/team/tenant move가 발생했을 때 같이 봐야 하는 refresh 대상은 보통 네 축이다.

### 1. active session context

- `activeTenantId`
- `activeOrgId`
- `selectedTeamId`
- current workspace pointer

이 값이 old membership을 가리키면 다음 요청부터 틀린 문맥으로 authorize하게 된다.

### 2. derived scope와 claim

- tenant-scoped role
- team-derived filter
- ownership path
- delegated admin scope

문제는 원본 membership이 바뀌어도 파생 allow가 남아 있을 수 있다는 점이다.

### 3. cache와 graph snapshot

- authz decision cache
- negative/positive cache
- relationship graph snapshot
- list/export query cache

membership move는 단순 profile update가 아니라 cache invalidation 이벤트다.

### 4. 장기 세션과 위임 세션

- refresh token family
- remember-me session
- support/operator acting-on-behalf-of session
- background job가 들고 있는 stale tenant context

특히 cross-tenant blast radius가 크면 `base login은 유지`보다 `tenant-scoped session revoke`가 더 안전할 수 있다.

---

## 안전한 요청 흐름은 보통 이렇게 생긴다

```text
1. membership/org/team change 발생
2. membership_version 또는 session_context_version 증가
3. tenant-scoped cache / graph snapshot / delegated scope를 무효화
4. 다음 요청에서 session version과 최신 membership version을 비교
5. mismatch면:
   - session context refresh
   - old tenant는 즉시 deny
   - 필요하면 session/token revoke 또는 tenant selector reset
6. refresh 뒤에만 새 org/team/tenant 문맥으로 다시 authorize
```

여기서 중요한 점:

- `새 tenant 추가`도 refresh 전에는 자동 허용으로 열지 않는다.
- `old tenant 제거`는 refresh를 기다리지 말고 다음 요청부터 막히는 쪽이 우선이다.

즉 grant path보다 revoke path가 더 빠르고 보수적이어야 한다.

---

## 초보자용 예시 3개

### 1. 사용자가 tenant A에서 tenant B로 이동했는데 A 데이터가 계속 보인다

이건 단순 UI 잔상 문제가 아니라 stale session context 문제다.

안전한 동작:

- old `activeTenantId=A`를 더 이상 신뢰하지 않는다
- 다음 요청에서 A membership이 없으면 즉시 deny한다
- session의 workspace selector를 비우거나 B로 refresh한다
- A tenant cache key와 list cache를 같이 정리한다

위험한 동작:

- 로그인 안 끊겼으니 old tenant tab은 계속 보여 줌

### 2. 같은 tenant 안에서 팀만 바뀌었는데 이전 팀 주문이 계속 조회된다

이 경우 cross-tenant leak가 아니어도 authz drift다.

가능한 원인:

- session 안의 team path가 stale하다
- search/list filter cache가 old team scope를 들고 있다
- ownership 재계산 없이 old allow를 재사용한다

안전한 동작:

- team-derived scope를 다시 계산한다
- list/detail 모두 최신 team membership으로 재평가한다
- old team scope cache를 무효화한다

### 3. 새 tenant 멤버십을 방금 받았는데 tenant switch 후에도 `403`이 난다

이건 회수 문제의 반대 방향 stale deny다.

가능한 원인:

- session claim이 아직 새 membership을 모른다
- negative cache가 old deny를 유지한다
- tenant picker는 바뀌었지만 backend session context는 refresh되지 않았다

안전한 동작:

- refresh 뒤에만 새 tenant를 active context로 올린다
- deny cache를 같이 비운다
- 민감 작업이면 step-up 또는 재로그인을 요구한다

---

## 자주 하는 오해

### 1. tenant selector만 바꾸면 session scope도 바뀐다

아니다. selector는 화면 상태일 수 있고, backend authz context는 별도 refresh가 필요하다.

### 2. membership 제거는 다음 로그인 때 반영해도 된다

위험하다. old tenant allow가 살아 있는 시간이 바로 보안 노출 시간이다.

### 3. 같은 사람의 이동이니 cross-tenant 문제가 아니다

아니다. 같은 사람이라도 old tenant 문맥이 남으면 다른 tenant 데이터에 계속 닿을 수 있다.

### 4. role 문자열이 안 바뀌면 cache를 건드릴 필요가 없다

아니다. tenant/team/org 문맥이 바뀌면 tenant-scoped cache key와 graph edge도 같이 흔들린다.

---

## 기억할 기본 원칙 5개

1. org/team/tenant move는 profile 변경이 아니라 authorization context 변경이다.
2. `selected tenant`와 `authorized tenant`는 같은 말이 아니다.
3. membership 제거는 다음 요청부터 old scope를 막는 쪽이 우선이다.
4. membership 추가는 refresh 뒤에만 새 scope를 연다.
5. tenant isolation test는 stale session이 old tenant에 남지 않는지까지 검증해야 의미가 있다.

## 한 줄 정리

org/team/tenant 이동이 생기면 안전한 시스템은 기존 session의 active tenant와 파생 scope를 그대로 믿지 않고, membership version을 기준으로 session context를 refresh 또는 revoke해서 stale cross-tenant access를 차단한다.
