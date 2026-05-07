---
schema_version: 3
title: AuthZ / Session Versioning Patterns
concept_id: security/authz-session-versioning-patterns
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- authz session versioning
- session version pattern
- authz version pattern
- claim version
aliases:
- authz session versioning
- session version pattern
- authz version pattern
- claim version
- claim epoch
- permission version
- token version
- token epoch
- jwt version claim
- stale claim revoke
- stale authority revoke
- role revoked but jwt still works
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/role-change-session-freshness-basics.md
- contents/security/session-revocation-at-scale.md
- contents/security/authorization-caching-staleness.md
- contents/security/authorization-graph-caching.md
- contents/security/token-introspection-vs-self-contained-jwt.md
- contents/security/jwt-deep-dive.md
- contents/security/refresh-token-family-invalidation-at-scale.md
- contents/security/tenant-membership-change-session-scope-basics.md
- contents/security/scim-deprovisioning-session-authz-consistency.md
- contents/security/background-job-auth-context-revalidation.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- AuthZ / Session Versioning Patterns 핵심 개념을 설명해줘
- authz session versioning가 왜 필요한지 알려줘
- AuthZ / Session Versioning Patterns 실무 설계 포인트는 뭐야?
- authz session versioning에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 AuthZ / Session Versioning Patterns를 다루는 deep_dive 문서다. stale claim revoke를 만료 시간에만 맡기지 말고, `session_version`, `authz_version`, `tenant_version`, `policy_version` 같은 축을 분리해 bump해야 server session, JWT, cache를 함께 정합하게 끊을 수 있다. 검색 질의가 authz session versioning, session version pattern, authz version pattern, claim version처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# AuthZ / Session Versioning Patterns

> 한 줄 요약: stale claim revoke를 만료 시간에만 맡기지 말고, `session_version`, `authz_version`, `tenant_version`, `policy_version` 같은 축을 분리해 bump해야 server session, JWT, cache를 함께 정합하게 끊을 수 있다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **claim freshness와 version-bump 설계 패턴**을 설명하는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Authorization Graph Caching](./authorization-graph-caching.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
> - [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
> - [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)
> - [Background Job Auth Context / Revalidation](./background-job-auth-context-revalidation.md)
> - [Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md)
> - [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)
> - [분산 캐시 설계](../system-design/distributed-cache-design.md)
> - [Security README: Session Coherence / Assurance deep dive catalog](./README.md#session-coherence-assurance-deep-dive-catalog)
> - [Security README: AuthZ / Tenant / Response Contracts deep dive catalog](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: authz session versioning, session version pattern, authz version pattern, claim version, claim epoch, permission version, token version, token epoch, jwt version claim, stale claim revoke, stale authority revoke, role revoked but jwt still works, granted role but still 403, permission change active session, authz freshness version, session freshness version, policy version, tenant version, tenant membership version, graph snapshot version, version bump revocation, revocation without blacklist, server session versioning, authz cache version key, authz version mismatch, logout all devices version, forced refresh after role change, stale authorities fix

## 이 문서 다음에 보면 좋은 문서

- role, permission, tenant membership이 바뀌면 왜 old session이 낡는지부터 다시 잡고 싶으면 [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)부터 보면 된다.
- version bump를 실제 revoke plane과 fan-out 관점에서 보고 싶으면 [Session Revocation at Scale](./session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)으로 이어진다.
- version을 cache key에 어떻게 실어야 stale deny와 stale allow를 줄일지 궁금하면 [Authorization Caching / Staleness](./authorization-caching-staleness.md), [Authorization Graph Caching](./authorization-graph-caching.md)을 같이 보면 된다.
- JWT local validation과 introspection을 어떤 조합으로 쓸지 고민 중이면 [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md), [JWT 깊이 파기](./jwt-deep-dive.md)로 이어 읽으면 된다.
- tenant 이동, deprovision, delegated grant 종료처럼 identity lifecycle까지 version bump가 이어지는 경계는 [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md), [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)에서 확장한다.

---

## 핵심 개념

version bump는 "토큰이 만료될 때까지 기다리는 것"의 반대다.

- expiration은 시간 기준이다
- versioning은 상태 변화 기준이다

즉 `exp`가 아직 남아 있어도:

- role이 회수될 수 있다
- tenant membership이 바뀔 수 있다
- policy가 바뀔 수 있다
- authorization graph snapshot이 바뀔 수 있다

이때 old session, old JWT, old decision cache를 같은 방식으로 낡게 만드는 공통 장치가 version이다.

핵심은 `하나의 버전 숫자`가 아니라 `무엇이 바뀌었는지에 맞는 버전 축`을 분리하는 것이다.

---

## 만료와 version mismatch는 다른 질문이다

| 질문 | expiration이 답하는 것 | versioning이 답하는 것 |
|---|---|---|
| 이 credential이 시간상 아직 유효한가 | 맞다 | 일부만 맞다 |
| 이 credential이 최신 권한을 반영하는가 | 직접 답하지 못한다 | 맞다 |
| 언제 필요한가 | 평상시 수명 관리 | role revoke, tenant move, policy deploy, account compromise |

그래서 stale claim 문제를 `access token TTL 5분이면 괜찮다`로만 해결하려 하면 보통 세 가지가 남는다.

- 5분도 너무 긴 privileged tail
- cache는 더 오래 남는 hidden stale state
- server session은 따로 살아 있어서 JWT만 짧아도 해결되지 않음

---

## 어떤 version 축을 분리해야 하나

모든 시스템이 아래 축을 전부 쓰는 것은 아니다. 하지만 무엇을 끊고 싶은지에 따라 축을 나눠야 한다.

| 버전 축 | 주로 무엇이 바뀔 때 bump | 어디에 실리는가 | mismatch 시 기본 동작 |
|---|---|---|---|
| `session_version` | password reset, logout-all, account disable, 의심 세션 격리 | server session row, session cookie payload, access/refresh token claim | 세션 자체를 끊고 재로그인 요구 |
| `authz_version` | role grant/revoke, group membership change, delegated grant 종료 | principal snapshot, access token claim, authz lookup cache key | 권한 snapshot refresh 또는 재평가 |
| `tenant_version` | tenant membership change, active tenant move, tenant별 role 변경 | active tenant context, JWT claim, tenant-scoped cache key | selected tenant refresh, tenant context 재선택 |
| `policy_version` | policy deploy, feature gate / ruleset 변경 | PDP cache key, decision log, rollout metadata | decision cache bust 후 즉시 재평가 |
| `graph_snapshot_version` | ownership graph rebuild, relationship edge invalidate, backfill cutover | graph cache key, decision provenance | graph/path cache 재계산 |
| `refresh_family_version` | device compromise, refresh token reuse, logout device | refresh token store, device/session graph | 새 access 발급 중단, family 재인증 요구 |

실전에서 가장 흔한 실수는 `session_version` 하나로 전부 해결하려는 것이다.  
이렇게 하면 role revoke 때도 무조건 전세션 로그아웃으로 가거나, 반대로 authz cache stale은 못 잡는 일이 생긴다.

---

## practical pattern 1. server session에는 hard gate와 soft refresh를 나눠 둔다

server-side session은 보통 request마다 session row나 principal snapshot을 다시 읽을 수 있으므로 version gate를 가장 세밀하게 걸기 쉽다.

권장 패턴:

- `session_version` mismatch: 즉시 세션 무효화, `401` 또는 재로그인
- `authz_version` mismatch: 세션 자체는 유지 가능하지만 principal/authority snapshot 재구성
- `tenant_version` mismatch: active tenant 선택값을 버리고 다시 선택하게 함

즉 browser session을 계속 유지할지, 권한만 낮출지를 분리할 수 있다.

이 패턴이 유용한 이유:

- role 회수와 password reset의 severity가 다르다
- 같은 계정이라도 tenant context stale은 전계정 로그아웃보다 더 좁게 처리할 수 있다
- cache bust와 session kill을 같은 이벤트에서 다른 강도로 처리할 수 있다

---

## practical pattern 2. JWT에는 low-churn version만 넣고, high-churn version은 server-side에서 본다

self-contained JWT에 version claim을 넣을 때는 무엇을 넣지 말아야 하는지도 중요하다.

보통 잘 맞는 것:

- `session_version`
- `authz_version`
- active tenant가 명시적이면 `tenant_version`

보통 조심해야 하는 것:

- 초단위로 자주 바뀌는 `policy_version`
- graph recompute 때마다 흔들리는 `graph_snapshot_version`

이유는 간단하다.

- JWT에 실린 version은 토큰 재발급 주기와 연결된다
- 너무 자주 바뀌는 version을 토큰에 넣으면 refresh storm가 생긴다

그래서 실무에서는 자주 아래 조합을 쓴다.

1. access JWT는 짧게 유지한다
2. JWT에는 `session_version`과 `authz_version` 정도만 싣는다
3. resource server는 lightweight version store나 introspection cache로 current version을 확인한다
4. `policy_version`, `graph_snapshot_version`은 decision cache나 PDP 쪽에서만 본다

즉 JWT version claim은 `모든 freshness 문제의 정답`이 아니라, 중앙 state check를 줄여 주는 coarse gate다.

---

## practical pattern 3. cache key는 token claim과 같은 축으로 맞추되, 더 세밀해야 한다

stale claim을 막는다고 access token만 확인하면 cache가 따로 낡을 수 있다.

대표적인 cache:

- user principal cache
- role / permission lookup cache
- tenant membership cache
- authorization decision cache
- relationship graph / path cache
- negative deny cache

cache key에는 최소한 해당 decision이 의존하는 version이 들어가야 한다.

예:

- principal cache: `user_id + authz_version`
- tenant membership cache: `user_id + tenant_id + tenant_version`
- decision cache: `subject + tenant + resource + action + authz_version + policy_version`
- graph cache: `tenant_id + graph_snapshot_version + relationship_shape`

특히 deny cache는 allow cache와 다른 축이 아니다.  
grant 이후에도 `403`이 남는 이유는 보통 deny cache key에 version이 빠졌기 때문이다.

---

## practical pattern 4. one-size-fits-all global epoch는 마지막 수단이다

전역 `auth_epoch` 하나를 두면 설명은 쉽다.

- 뭔가 바뀌면 epoch를 올린다
- 모든 세션/JWT/cache가 old epoch면 폐기한다

하지만 비용이 크다.

- 모든 사용자와 tenant가 같이 날아간다
- 대규모 cache stampede가 생긴다
- 사소한 role 변경도 전역 logout처럼 보인다

전역 epoch는 아래 같은 경우에만 마지막 수단으로 두는 편이 좋다.

- signing key compromise
- policy engine의 치명적 계산 버그
- tenant isolation bug로 전체 invalidate가 필요한 경우

평상시에는 `subject`, `tenant`, `policy`, `graph` 축을 분리해야 한다.

---

## practical pattern 5. refresh path version과 access path version을 구분한다

모바일/API 환경에서는 access token과 refresh token의 성격이 다르다.

- access token: 짧고 자주 발급됨
- refresh token: 길고 재발급의 뿌리 역할

그래서 `refresh_family_version`이나 family revoke는 따로 다루는 편이 낫다.

예:

- device compromise: 해당 device의 refresh family만 죽인다
- password reset: 모든 refresh family를 끊고 `session_version`도 올린다
- role revoke: 모든 refresh family를 죽이지 않고 `authz_version`만 올릴 수도 있다

이 구분이 없으면 사소한 권한 조정에도 모바일 모든 기기를 강제로 다시 로그인시키게 된다.

---

## 무엇을 bump해야 하나

| 이벤트 | bump할 version | 같이 해야 하는 것 | 흔한 실수 |
|---|---|---|---|
| 비밀번호 변경 / 계정 탈취 의심 | `session_version`, `refresh_family_version` | active session terminate, remember-me 정리 | `authz_version`만 올리고 세션을 안 끊음 |
| admin role 회수 | `authz_version` | allow/deny cache bust, 민감 API fresh check | 무조건 전세션 로그아웃 또는 아무것도 안 함 |
| support role 부여 | `authz_version` | stale deny cache 제거, 필요하면 step-up 요구 | grant인데도 old deny cache 유지 |
| tenant membership 제거 | `tenant_version`, 필요시 `authz_version` | selected tenant 초기화, tenant-scoped cache purge | `user_id`만 key로 써서 cross-tenant stale 발생 |
| policy deploy | `policy_version` | PDP/decision cache bust, rollout provenance 기록 | user token까지 전부 재발급 |
| relationship graph backfill / cutover | `graph_snapshot_version` | graph/path cache 재생성, shadow compare | graph cache는 그대로 두고 policy만 올림 |
| logout all devices | `session_version`, `refresh_family_version` | device graph fan-out, browser session 제거 | refresh revoke만 하고 server session은 남김 |

---

## mismatch를 어떤 응답으로 연결할까

version mismatch가 났다고 항상 같은 UX로 보내면 운영이 거칠어진다.

| mismatch 종류 | 보통 사용자에게 보이는 결과 | 이유 |
|---|---|---|
| `session_version` | `401`, 재로그인, 세션 재생성 | 인증 상태 자체를 더 못 믿음 |
| `authz_version` | principal refresh 후 재평가, 필요시 `403` | 로그인은 유지되지만 권한 snapshot은 stale |
| `tenant_version` | active tenant 재선택, context refresh | selected tenant 문맥이 stale |
| `policy_version` | request 재평가, 보통 logout 없음 | 정책 계산 결과만 stale |
| `graph_snapshot_version` | cache bust 후 decision recompute | 관계 그래프만 stale |

즉 versioning의 목표는 "무조건 로그아웃"이 아니라 `무엇이 stale인지에 맞는 최소한의 파괴적 동작`을 선택하는 것이다.

---

## 코드로 보기

### 1. authoritative version snapshot

```java
public record AuthVersionSnapshot(
    long sessionVersion,
    long authzVersion,
    long tenantVersion,
    long policyVersion,
    long graphSnapshotVersion
) {}
```

### 2. server session gate

```java
public SessionDecision validate(ServerSession session, AuthVersionSnapshot current) {
    if (session.sessionVersion() != current.sessionVersion()) {
        return SessionDecision.reauthenticate();
    }
    if (session.authzVersion() != current.authzVersion()) {
        return SessionDecision.refreshAuthorities();
    }
    if (session.tenantVersion() != current.tenantVersion()) {
        return SessionDecision.refreshTenantContext();
    }
    return SessionDecision.ok();
}
```

### 3. JWT + cache key 조합

```java
public AuthorizationDecision decide(AccessClaims claims, String resourceId, String action) {
    CurrentVersions current = versionStore.load(claims.subject(), claims.tenantId());

    if (claims.sessionVersion() != current.sessionVersion()) {
        throw new ReauthenticateRequiredException();
    }
    if (claims.authzVersion() != current.authzVersion()) {
        throw new ClaimsRefreshRequiredException();
    }

    String key = String.join(":",
        claims.subject(),
        claims.tenantId(),
        resourceId,
        action,
        String.valueOf(current.authzVersion()),
        String.valueOf(current.policyVersion()),
        String.valueOf(current.graphSnapshotVersion())
    );

    return decisionCache.computeIfAbsent(key, ignored -> evaluateFresh(claims, resourceId, action));
}
```

이 예시의 핵심은 JWT claim에 없는 `policy_version`, `graph_snapshot_version`도 cache key에는 들어간다는 점이다.

---

## 운영 원칙

### 1. version source of truth는 하나여야 한다

`session_version`을 user DB에서 올리고, `authz_version`을 cache에서만 관리하면 eventually inconsistent revoke가 된다.

- authoritative row 또는 document를 정한다
- cache는 projection일 뿐이다
- event는 source of truth를 알리는 fan-out이어야 한다

### 2. timestamp보다 monotonic counter나 opaque epoch가 낫다

region 간 clock skew가 있으면 `updated_at > iat` 비교는 흔들린다.

그래서 보통:

- DB incrementing counter
- monotonic sequence
- compare-only opaque epoch token

같은 값을 쓰는 편이 안전하다.

### 3. version bump는 idempotent하고 관측 가능해야 한다

운영자가 나중에 봐야 하는 질문은 항상 같다.

- 누가 무엇 때문에 version을 올렸나
- 어느 scope를 대상으로 했나
- cache invalidation fan-out이 끝났나
- old decision tail이 아직 남았나

즉 audit log, decision log, propagation status가 같이 따라와야 한다.

### 4. background job도 같은 version contract를 따라야 한다

request path만 freshness를 확인하고 worker가 old claim을 계속 들고 있으면 revoke가 절반만 된다.

장시간 실행 작업, outbox consumer, batch job도:

- job start 시 version snapshot 기록
- 민감 작업 전 revalidation
- mismatch 시 중단 또는 downgrade

를 갖춰야 한다.

---

## 자주 하는 실수

### 1. `exp`만 짧게 두고 stale claim 문제는 끝났다고 생각한다

JWT가 짧아도 server session, cache, background job은 그대로 남을 수 있다.

### 2. role revoke와 password reset을 같은 version 축으로만 다룬다

둘 다 중요하지만, 보통 하나는 authz freshness 문제이고 다른 하나는 authentication compromise 문제다.

### 3. allow cache만 지우고 deny cache는 안 지운다

grant 이후에도 `403`이 남는 가장 흔한 이유다.

### 4. tenant를 cache key에서 빼먹는다

multi-tenant stale allow/deny는 대부분 여기서 시작한다.

### 5. policy churn을 JWT claim으로 직접 들고 다닌다

토큰 재발급 폭풍과 cache stampede를 같이 만든다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 맞는가 |
|---|---|---|---|
| `session_version`만 사용 | 단순하다 | authz/policy/tenant를 거칠게 다룸 | 작은 서비스, coarse revoke |
| `session_version + authz_version` | 로그인 유지와 권한 refresh를 분리 가능 | 검증 로직이 늘어난다 | 대부분의 웹/API 서비스 |
| `+ tenant_version` | tenant stale을 좁게 막는다 | active tenant 관리가 필요하다 | multi-tenant SaaS |
| `+ policy_version + graph_snapshot_version` | cache/policy drift를 정밀하게 제어 | control-plane 복잡도 증가 | PDP/graph 기반 authz |
| introspection 중심 | revoke가 빠르다 | 중앙 의존성 증가 | high-risk 경로 |
| short JWT + version store | latency와 revoke를 절충 | current version lookup이 필요 | 일반 API 경로 |

---

## 꼬리질문

> Q: 왜 `session_version` 하나만으로 부족한가요?
> 의도: authn revoke와 authz freshness를 분리하는지 확인
> 핵심: password reset, role revoke, policy deploy는 같은 강도로 처리할 일이 아니기 때문이다.

> Q: JWT에 `policy_version`까지 넣으면 더 안전하지 않나요?
> 의도: high-churn version을 토큰에 실을 때의 비용을 이해하는지 확인
> 핵심: 안전해질 수는 있지만 refresh storm와 운영 복잡도가 급격히 늘어난다.

> Q: grant 이후 `403`이 남는 이유는 왜 deny cache가 더 자주 문제인가요?
> 의도: stale deny를 인식하는지 확인
> 핵심: cache key에서 `authz_version`이나 `tenant_version`이 빠지면 old deny가 그대로 재사용되기 때문이다.

> Q: mismatch가 났을 때 항상 `401`로 보내야 하나요?
> 의도: authn/session revoke와 authz refresh를 구분하는지 확인
> 핵심: `session_version` mismatch는 재로그인이 맞지만, `authz_version` mismatch는 principal refresh와 재평가가 더 맞는 경우가 많다.

## 한 줄 정리

stale claim revoke의 실전 해법은 `하나의 만능 세션 버전`이 아니라, session/authz/tenant/policy/cache 축을 분리한 version bump를 각 enforcement layer가 같은 계약으로 확인하게 만드는 것이다.
