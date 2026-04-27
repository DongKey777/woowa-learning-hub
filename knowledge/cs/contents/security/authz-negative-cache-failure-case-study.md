# AuthZ Negative Cache Failure Case Study

> 한 줄 요약: 인가 negative cache는 miss 비용을 줄이지만, concealment policy와 tenant/ownership 경계가 섞이면 stale deny가 보안 이슈와 운영 이슈를 동시에 만들 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [Auth Failure Response Contracts: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)

retrieval-anchor-keywords: authz negative cache, stale deny case study, concealment cache bug, tenant negative cache, 404 negative cache, ownership cache miss, authz failure case study, stale deny, grant but still denied, tenant-specific 403, only one tenant 403, inconsistent 401 404, 401 404 flip, concealment drift, cached 404 after grant
retrieval-anchor-keywords: negative cache deep dive entry cue, stale deny beginner bridge handoff, grant path freshness to negative cache case study, negative cache next step, negative cache return path, authz tenant catalog return

---

## 시작 전에: 이 문서의 역할과 입장 큐

- 이 문서는 `deep dive` 사례 분석이다. stale deny와 concealment 혼선을 운영 관점에서 분해한다.
- 이 문서는 `primer`가 아니다. `401`/`403`/`404` 의미가 아직 섞이면 먼저 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)와 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 돌아간다.
- 이 문서는 endpoint별 즉시 조치 runbook이 아니다. 실시간 분기 절차가 필요하면 [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)으로 넘긴다.

| 나는 어디서 왔나 | 이 문서에서 먼저 볼 구간 | 다음 문서 |
|---|---|---|
| primer bridge에서 `grant 후 403`를 stale deny로 분리했다 | `사례: tenant 이동 직후 stale deny` + `대응` | [Authorization Caching / Staleness](./authorization-caching-staleness.md), [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) |
| graph snapshot/relationship cache까지 얽혀 보인다 | `원인` + `대응` | [Authorization Graph Caching](./authorization-graph-caching.md), [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md) |

- 이 사례 문서를 본 뒤에는 [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 돌아가 다음 갈래를 고른다.

## 핵심 개념

negative cache는 "없다" 또는 "deny" 결과를 캐시해 miss 비용을 줄이는 방식이다.
하지만 인가에서는 이 값이 오래 남으면 실제 상태와 다르게 거부가 계속된다.

특히:

- concealment 404
- tenant mismatch
- ownership miss

가 섞일 때 디버깅이 어려워진다.

---

## 깊이 들어가기

### 사례: tenant 이동 직후 stale deny

상황:

1. 사용자는 tenant A에 있었고 리소스 접근이 deny됨
2. 지원 작업으로 tenant B로 이동
3. negative cache가 `user-resource -> deny/not-found`를 유지
4. 실제론 접근 가능해졌는데 계속 404/403

증상:

- 일부 pod만 계속 deny
- 특정 tenant에서만 403이 남거나, 다른 route에서는 404 concealment로 보임
- 외부 응답은 404라 not-found와 구분 안 됨
- support는 데이터가 안 보인다고만 느낌
- authn context도 흔들리면 어떤 경로는 401, 어떤 경로는 404로 보여 원인 분리가 더 어려워진다

원인:

- cache key에 tenant/version 누락
- negative TTL 과다
- invalidate 누락

### 왜 위험한가

- 권한 복구가 늦어 운영 장애가 됨
- concealment policy 때문에 원인 추적이 어려움
- cross-tenant 혼선과 섞여 보안 신호처럼 보일 수 있음

### 대응

- negative cache를 별도 telemetry로 분리
- tenant/policy version을 키에 포함
- concealment 404와 stale deny reason을 내부적으로 구분
- `401`/`404`가 섞이면 authn cache와 negative cache를 분리해서 본다
- hot route에서는 negative cache를 더 짧게 또는 비활성화

## 한 줄 정리

AuthZ negative cache의 진짜 위험은 캐시 그 자체보다, concealment와 tenant/ownership 변화가 겹칠 때 stale deny가 조용히 오래 남는 데 있다.
