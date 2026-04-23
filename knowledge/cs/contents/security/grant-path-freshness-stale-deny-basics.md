# Grant Path Freshness and Stale Deny Basics

> 한 줄 요약: 권한을 방금 부여해 source of truth에서는 allow가 맞아도, 현재 요청이 보는 session/JWT claim과 deny cache가 아직 옛 상태면 `403`이 계속 나올 수 있으므로 `grant -> claim refresh -> cache invalidation -> 재평가`가 한 경로로 맞물려야 한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
> - [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
> - [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
> - [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [Security README: 기본 primer](./README.md#기본-primer)
> - [Security README: Session Coherence / Assurance deep dive catalog](./README.md#session-coherence--assurance-deep-dive-catalog)
> - [Security README: AuthZ / Tenant / Response Contracts deep dive catalog](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: grant path freshness, stale deny basics, permission granted still 403, newly granted permission still forbidden, new role still 403, grant but still denied, stale deny after grant, fresh grant stale deny, 403 until claim refresh, 403 until cache invalidation, claim refresh after grant, permission grant propagation, authz grant propagation, grant path cache invalidation, deny cache invalidation after grant, session claim stale after grant, jwt stale after role grant, support role granted still 403, tenant membership granted still 403, re-login after permission grant, forced refresh after grant, grant convergence, grant path convergence, stale authorities after grant

## 이 문서 다음에 보면 좋은 문서

- role/permission 변경과 session freshness의 큰 그림을 먼저 잡고 싶으면 [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)로 바로 이어 가면 된다.
- 새 tenant membership이나 workspace access를 받은 뒤에도 `403`이 남는 쪽이 더 가깝다면 [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)를 같이 보면 된다.
- claim, role, authority, permission이라는 단어가 섞여 있으면 [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)를 먼저 붙이는 편이 읽기 쉽다.
- `authz_version`, `session_version`, `tenant_version`을 어떻게 나눠 bump할지 궁금하면 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)로 이어 가면 된다.
- stale deny와 negative cache를 실제 운영 문제로 더 깊게 보고 싶으면 [Authorization Caching / Staleness](./authorization-caching-staleness.md), [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)를 바로 이어 보면 된다.
- self-contained JWT라서 즉시 반영이 어려운지, introspection이라 다음 요청에 더 빨리 반영 가능한지 비교하려면 [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)를 붙이면 된다.

---

## 먼저 20초 그림

| 이미 바뀐 것 | 아직 낡은 것 | 사용자에게 보이는 모습 | 안전한 다음 단계 |
|---|---|---|---|
| admin console이나 DB에서 role/permission grant 완료 | session/JWT claim | 계속 `403`, 재로그인 뒤 해결되는 것처럼 보임 | claim/session refresh 또는 새 token 재발급 |
| claim은 새로 받아 옴 | deny/decision cache | 일부 pod, 일부 tenant, 일부 route만 계속 `403` | grant event로 negative/decision cache 무효화 |
| membership grant 완료 | active tenant/workspace context | UI에는 새 workspace가 보이는데 API는 `403` | backend active context refresh 후 재평가 |
| coarse role grant 완료 | step-up, ownership, extra policy precondition | 목록은 보이는데 민감 POST만 `403` | 최근 인증, ownership 확인, policy 재평가 |

이 문서의 핵심은 두 줄이다.

- `grant가 저장됐다`와 `요청이 새 allow를 본다`는 같은 이벤트가 아니다.
- 새 권한이 열리려면 `fresh claim/context`와 `stale deny cleanup`이 둘 다 끝나야 한다.

---

## grant path freshness란 무엇인가

이 문서에서 말하는 `grant path`는 아래 전체 경로를 뜻한다.

```text
관리자/SCIM/정책 변경으로 grant 발생
-> source of truth 반영
-> session 또는 token claim refresh
-> deny/decision/graph cache invalidation
-> 다음 요청의 재평가
-> 최종 allow
```

여기서 freshness는 단순히 `세션 만료가 안 됐다`가 아니다.

- 현재 요청이 최신 grant를 보고 있는가
- old deny가 아직 남아 있지 않은가
- active tenant나 workspace 문맥이 최신인가

즉 grant path freshness는 `새 권한이 실제 요청 경로까지 도달했는가`를 묻는 말이다.

---

## 왜 grant 직후에도 `403`이 가능한가

### 1. source of truth update와 현재 session update는 다른 단계다

권한 부여는 대개 DB, policy store, membership graph 같은 source of truth에서 먼저 끝난다.
하지만 현재 요청은 종종 그 값을 직접 보지 않는다.

- server session이 로그인 시점 role snapshot을 들고 있다
- self-contained JWT가 예전 claim을 들고 있다
- gateway가 old authority set을 메모리에 들고 있다

그래서 `관리자 화면에서는 grant 완료`인데도, 사용자의 현재 요청은 여전히 old claim으로 authorize할 수 있다.

### 2. stale deny cache가 남아 있을 수 있다

grant 전에는 정상적으로 deny였고, 그 deny를 캐시했을 수 있다.

- negative cache
- PDP decision cache
- relationship path cache
- tenant-scoped membership cache

이 값이 grant 뒤에도 남아 있으면, claim을 새로 받아도 old deny가 재사용된다.
즉 `fresh claim + stale cache` 조합에서도 `403`이 계속 가능하다.

### 3. selected tenant나 workspace는 hint일 뿐이다

새 tenant membership을 받았다고 해서 browser selector가 곧바로 authorization 근거가 되지는 않는다.

- UI는 새 workspace를 노출했다
- 그러나 backend session의 `activeTenantId`는 old 값이다
- membership cache도 아직 갱신되지 않았다

이 경우 사용자는 "workspace는 보이는데 왜 들어가면 `403`이지?"를 겪는다.

### 4. grant와 정책 전제조건은 다른 질문이다

권한이 생겨도 아래 조건은 여전히 별도일 수 있다.

- 최근 step-up이 있었는가
- 현재 resource ownership이 맞는가
- delegated support session이 열린 상태인가
- route가 더 강한 assurance level을 요구하는가

그래서 grant가 보인 뒤에도 일부 high-risk action은 계속 `403`일 수 있다.

---

## 둘 중 하나만 끝나도 아직 막힌다

초보자가 가장 자주 놓치는 포인트는 `claim refresh`와 `cache invalidation`이 서로 대체재가 아니라는 점이다.

| 현재 상태 | 결과 |
|---|---|
| claim만 refresh되고 deny cache는 그대로 | 일부 요청은 계속 `403` |
| cache는 비웠는데 session/JWT claim은 old snapshot | 여전히 `403` |
| UI tenant selector만 바뀌고 backend context는 old 값 | 새 workspace 진입 시 `403` 또는 concealment `404` |
| role grant는 반영됐지만 step-up은 안 함 | read는 열려도 approve/write는 `403` |

즉 `로그아웃 후 다시 로그인하면 된다`가 임시 증상 가리기일 수는 있어도,
근본적으로는 grant path 전체가 수렴해야 한다.

---

## 안전한 grant path timeline

권한 부여 뒤 allow가 열리는 안전한 순서는 보통 이렇다.

1. source of truth에서 membership, role, permission, relationship grant를 기록한다.
2. `authz_version`, `tenant_version`, `membership_version` 같은 freshness 축을 올리거나 동등한 grant event를 발행한다.
3. 현재 session/JWT claim을 refresh하거나, old snapshot을 빠르게 retirement한다.
4. negative cache, decision cache, graph/path cache를 grant 범위에 맞게 무효화한다.
5. 다음 요청은 새 claim과 새 cache miss로 다시 authorize한다.
6. 그 뒤에만 `403`이 `allow`로 바뀌어야 한다.

여기서 중요한 설계 포인트는 이것이다.

- revoke path는 `old allow를 빨리 없애는 것`이 우선이다.
- grant path는 `old deny를 안전하게 치우고 새 권한을 노출하는 것`이 우선이다.
- 둘 다 version, refresh, invalidation 계약이 없으면 운영에서 증상이 뒤엉킨다.

---

## 초보자용 예시 3개

### 1. support role을 방금 부여했는데 계속 `403`이 나온다

가능한 원인:

- 현재 session principal에 `ROLE_SUPPORT`가 아직 없다
- gateway의 deny cache가 예전 결정을 재사용한다
- 민감 support action이라 step-up이 추가로 필요하다

안전한 대응:

- session/claim refresh를 먼저 유도한다
- grant event로 관련 deny cache를 비운다
- high-risk route면 recent-auth requirement를 따로 확인한다

### 2. 새 tenant membership을 받았는데 workspace에 들어가면 `403`이다

가능한 원인:

- tenant picker만 바뀌고 backend `activeTenantId`는 old 값이다
- membership cache key에 tenant version이 빠졌다
- old deny가 concealment `404`나 `403`으로 남아 있다

안전한 대응:

- backend active context를 refresh한다
- tenant-scoped membership cache와 decision cache를 같이 무효화한다
- 다음 요청에서 최신 membership으로 재평가한다

### 3. 문서 공유 grant를 줬는데 일부 인스턴스만 계속 deny한다

가능한 원인:

- 일부 pod만 invalidation event를 못 받았다
- relationship path cache가 region별로 다르게 남아 있다
- claim은 새로워졌지만 graph snapshot은 old 버전이다

안전한 대응:

- scoped purge나 direct recompute로 hot path를 임시 우회한다
- cache provenance와 snapshot version을 비교한다
- 부분 invalidation tail이 끝났는지 본다

---

## 설계할 때의 기본값

- grant 이벤트에서는 source-of-truth update만 하지 말고 claim freshness와 cache invalidation까지 한 계약으로 묶는다.
- deny cache TTL은 allow cache보다 더 짧게 두거나, grant가 잦은 hot path에서는 아예 보수적으로 운영한다.
- 내부 reason code를 `stale_claim`, `negative_cache_hit`, `tenant_context_stale`, `step_up_required`처럼 분리해 둔다.
- self-contained JWT를 쓰면 `권한 부여 직후 즉시 반영`이 어려울 수 있으므로 refresh/re-login UX를 명시한다.
- `403`이 거슬린다고 authorize를 우회하지 말고, refresh와 invalidation 경로를 더 짧고 관측 가능하게 만든다.

---

## 한 줄 정리

새 grant가 실제 allow로 보이려면 DB 반영만으로는 부족하고, 그 grant를 보는 claim/session과 그 grant를 가리던 stale deny cache가 함께 최신 상태로 수렴해야 한다.
