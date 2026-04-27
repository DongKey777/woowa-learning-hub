# Authorization Caching / Staleness

> 한 줄 요약: authorization cache는 성능을 크게 올릴 수 있지만, 권한 회수와 정책 변경을 늦출 수 있으므로 versioned invalidation과 짧은 TTL이 같이 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)
> - [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)
> - [Auth Failure Response Contracts: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Authorization Graph Caching](./authorization-graph-caching.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [Distributed Cache Design](../system-design/distributed-cache-design.md)
> - [Multi-tenant SaaS Isolation Design](../system-design/multi-tenant-saas-isolation-design.md)
> - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: authorization cache, staleness, permission cache, policy version, authz version, claim version, revocation, TTL, negative cache, cache invalidation, RBAC, ABAC, PDP, PEP, cache inconsistency, negative cache bug, stale deny, stale deny case study, grant but still denied, tenant-specific 403, only one tenant 403, cross-tenant 403, inconsistent 401 404, 401 404 flip, concealment cache, cached 404 after grant, authorization graph cache, authorization graph caching, graph snapshot, graph snapshot cache, graph snapshot version, relationship cache, relationship edge cache, graph invalidation, tenant-scoped graph invalidation
retrieval-anchor-keywords: authorization cache entry cue, stale deny beginner handoff, grant path primer bridge to authz cache deep dive, authz cache advanced jump-in cue, cache staleness deep dive entrypoint

---

## 시작 전에: 이 문서의 역할과 입장 큐

- 이 문서는 `deep dive`다. cache 구조, invalidation, negative cache 트레이드오프를 설계/운영 관점으로 다룬다.
- 이 문서는 `primer`나 `primer bridge`가 아니다. 개념 축이 아직 흐리면 먼저 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 돌아간다.
- 이 문서는 `playbook`/`recovery`도 아니다. 실시간 장애 대응 절차가 필요하면 [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) 이후 incident 문서로 간다.

| 나는 어디서 왔나 | 이 문서에서 먼저 볼 구간 | 다음 문서 |
|---|---|---|
| `grant 후 403`를 primer bridge에서 막 분리했다 | `핵심 개념` + `3. cache invalidation` + `4. negative cache` | [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md) |
| 이미 pod/tenant별 결과 불일치를 디버깅 중이다 | `4. negative cache` + `트레이드오프` | [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) |

## 핵심 개념

인가(authorization)는 "이 사용자가 지금 이 자원에 이 행동을 해도 되는가"를 판단하는 일이다.
이 판단은 보통 DB 조회, 정책 계산, 소유권 확인, tenant 검증을 포함하므로 비싸다.

그래서 캐시를 붙이고 싶어진다.

- 사용자 역할을 캐시한다
- permission set을 캐시한다
- 정책 평가 결과를 캐시한다
- 리소스 소유권 조회를 캐시한다

문제는 인가는 상태 변화에 매우 민감하다는 점이다.

- role이 회수될 수 있다
- tenant membership이 바뀔 수 있다
- 리소스 소유권이 변경될 수 있다
- 정책 자체가 배포로 바뀔 수 있다

즉 authorization cache는 성능 도구이지만, 정확성을 잠식하기 쉽다.

---

## 깊이 들어가기

### 1. 무엇을 캐시할 수 있나

모든 인가 결정을 캐시할 수 있는 것은 아니다.

캐시 후보:

- user role lookup
- tenant membership
- policy document version
- resource ownership snapshot
- relationship edge / graph snapshot
- decision result for a short TTL

캐시하기 어려운 것:

- 매우 자주 바뀌는 admin 권한
- 실시간 결제/정산 같은 고위험 작업
- 컨텍스트에 따라 달라지는 ABAC rule

핵심은 "결정"과 "근거"를 구분하는 것이다.

- 근거는 상대적으로 천천히 바뀐다
- 결정은 근거와 컨텍스트에 따라 매번 달라질 수 있다

relationship-based authz에서 graph edge나 path 자체를 캐시하기 시작하면 일반 decision cache보다 invalidation fan-out이 커진다.
tenant ownership 이동이나 delegated admin revoke처럼 edge fan-out이 큰 케이스는 [Authorization Graph Caching](./authorization-graph-caching.md), [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md), [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)을 같이 봐야 한다.

### 2. stale authorization의 위험

권한 캐시는 stale해지면 보안 사고가 된다.

- 퇴사한 관리자가 여전히 관리자 API를 쓸 수 있다
- tenant 이동 후 이전 tenant 데이터에 접근한다
- 권한 회수 뒤에도 몇 분간 예전 권한이 남는다

이 문제는 JWT에 role을 넣은 경우와 매우 비슷하다.
토큰이든 캐시든, 최신 상태를 늦게 반영하면 인가가 늦어진다.

### 3. cache invalidation을 어떻게 할까

가장 현실적인 방법은 여러 층을 섞는 것이다.

- 짧은 TTL
- 권한 변경 시 version bump
- event-driven invalidation
- 민감 작업은 cache bypass
- deny와 allow를 다르게 취급

특히 version stamp가 유용하다.

- `authz_version` 또는 `permission_version`을 사용자마다 둔다
- role이 바뀌면 version을 올린다
- 캐시 키에 version을 포함한다

그러면 권한이 바뀐 사용자는 자연스럽게 새로운 캐시 미스를 만든다.

server session이나 JWT가 들고 있는 claim freshness까지 한 계약으로 맞추고 싶으면 `session_version`/`authz_version`/`tenant_version`을 함께 나눠 가져가는 편이 낫다.
이 축 분해는 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)에서 이어진다.

graph-based authz라면 `policy_version`만으로 부족할 수 있고, `graph_snapshot_version` 또는 edge epoch를 함께 올려야 한다.
이 점이 빠지면 membership은 바뀌었는데 path cache만 남는 문제가 생긴다.

### 4. negative cache는 더 조심해야 한다

deny 결과를 캐시하면 성능은 좋아질 수 있지만, grant 이후에도 거부가 남는다.

- 권한이 막 방금 생겼는데 계속 거부된다
- tenant membership이 복구됐는데 특정 tenant에서만 403이 남는다
- 사용자는 "왜 아직도 안 되지?"를 겪는다

그래서 negative cache는 더 짧게 잡거나, 아예 특정 경로에서는 쓰지 않는다.
concealment `404`를 함께 쓰는 경로라면 stale deny가 `401`/`404` 계약 흔들림처럼 보일 수 있어서,
외부 상태 코드와 내부 deny reason을 분리해 남기는 편이 안전하다.

### 5. gateway cache와 service cache는 다르다

인가 캐시는 어디에 두느냐도 중요하다.

- gateway cache: 요청 초기에 빠르게 거를 수 있다
- service cache: 도메인 맥락을 더 잘 반영한다
- distributed cache: 여러 인스턴스가 공유할 수 있다

하지만 gateway에서 허용했다고 서비스에서도 무조건 허용하면 안 된다.
중요한 API는 service-level에서 다시 확인해야 한다.
이 split enforcement 경계는 [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)과 직접 이어진다.

---

## 실전 시나리오

### 시나리오 1: 관리자 권한 회수 후에도 몇 분간 접근 가능

문제:

- admin role을 캐시해 두었다
- 권한 회수 이벤트가 바로 반영되지 않았다

대응:

- admin 권한은 짧은 TTL로만 캐시한다
- 권한 변경 시 version을 올린다
- 민감 endpoint는 fresh lookup을 요구한다

### 시나리오 2: tenant 전환 후 데이터가 섞임

문제:

- 같은 사용자라도 tenant A와 tenant B에서 권한이 다르다
- 캐시 키에 tenant 정보가 빠졌다
- 운영에서는 `tenant-specific 403` 또는 일부 route만 막히는 형태로 보일 수 있다

대응:

- cache key에 `tenant_id`를 반드시 넣는다
- cross-tenant role을 별도 정책으로 분리한다
- multi-tenant 시스템에서는 default deny를 유지한다

### 시나리오 3: 새 권한이 생겼는데 계속 거부됨

문제:

- negative cache가 오래 남았다
- concealment 정책이 섞여 있으면 `403` 대신 `404`가 계속 남을 수도 있다

대응:

- grant 이벤트에서 관련 cache를 무효화한다
- deny TTL을 짧게 둔다
- 권한 추가 경로에서는 cache bypass를 고려한다

---

## 코드로 보기

### 1. versioned cache key

```java
public AuthorizationDecision decide(UserPrincipal user, String resourceId, String action) {
    String key = String.join(":",
        user.id().toString(),
        resourceId,
        action,
        String.valueOf(user.permissionVersion())
    );

    return decisionCache.computeIfAbsent(key, ignored -> evaluateFresh(user, resourceId, action));
}
```

### 2. 권한 변경 시 invalidation

```java
public void revokeAdminRole(Long userId) {
    userRoleRepository.removeAdmin(userId);
    userRepository.bumpPermissionVersion(userId);
    authzEventPublisher.publish(new PermissionChangedEvent(userId));
}
```

### 3. 민감 작업은 fresh check

```java
public void transferMoney(UserPrincipal user, TransferCommand command) {
    AuthorizationDecision decision = authorizationService.evaluateFresh(
        user, command.accountId(), "transfer"
    );

    if (!decision.allowed()) {
        throw new AccessDeniedException("forbidden");
    }

    paymentService.transfer(command);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| no cache | 항상 최신이다 | 느리다 | 고위험, 저빈도 경로 |
| short TTL cache | 빠르고 단순하다 | 짧은 stale window가 있다 | 대부분의 일반 API |
| versioned cache | invalidation이 쉽다 | version 관리가 필요하다 | role/tenant 변화가 잦을 때 |
| event-driven invalidation | 반영이 빠르다 | 이벤트 전달 실패를 고려해야 한다 | 대규모 권한 시스템 |
| gateway-only cache | 초기에 싸게 막는다 | 서비스 정책과 어긋날 수 있다 | 트래픽이 큰 공개 API |

판단 기준은 이렇다.

- 권한 회수 후 몇 초까지 허용 가능한가
- 잘못 허용되는 것과 잘못 거부되는 것 중 무엇이 더 치명적인가
- tenant/role/policy가 얼마나 자주 바뀌는가
- fresh lookup 비용을 감당할 수 있는가

---

## 꼬리질문

> Q: authorization cache가 왜 위험할 수 있나요?
> 의도: stale decision이 보안 사고가 되는 이유를 아는지 확인
> 핵심: 권한 회수나 정책 변경이 늦게 반영될 수 있기 때문이다.

> Q: cache key에 permission version을 넣는 이유는 무엇인가요?
> 의도: invalidation 전략 이해 확인
> 핵심: 권한이 바뀌면 새 키가 생겨서 자연스럽게 cache miss가 나기 때문이다.

> Q: deny를 캐시하면 왜 더 조심해야 하나요?
> 의도: negative cache의 부작용 이해 확인
> 핵심: 새로 권한이 생겨도 거부가 남을 수 있다.

> Q: gateway에서 허용되면 service에서도 꼭 허용해야 하나요?
> 의도: 층별 책임 분리를 이해하는지 확인
> 핵심: 아니다. 민감 경로는 서비스가 다시 확인해야 한다.

## 한 줄 정리

인가 캐시는 성능을 주지만, 최신 권한을 늦게 반영하는 순간 보안 사고가 되므로 version과 TTL을 함께 설계해야 한다.
