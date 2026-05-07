---
schema_version: 3
title: AuthZ Cache Inconsistency / Runtime Debugging
concept_id: security/authz-cache-inconsistency-runtime-debugging
canonical: false
category: security
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- authz cache inconsistency
- authorization cache debugging
- stale decision cache
- negative cache bug
aliases:
- authz cache inconsistency
- authorization cache debugging
- stale decision cache
- negative cache bug
- policy version drift
- graph snapshot drift
- stale graph snapshot
- authz graph version drift
- authorization graph caching
- cache key omission
- tenant cache mixup
- authz runtime debug
symptoms:
- AuthZ Cache Inconsistency / Runtime Debugging 관련 운영 사고나 보안 이상 징후가 발생해 대응 순서가 필요하다
intents:
- troubleshooting
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/authorization-graph-cache-relationship-cache-primer.md
- contents/security/authorization-caching-staleness.md
- contents/security/authorization-graph-caching.md
- contents/security/authz-negative-cache-failure-case-study.md
- contents/security/auth-failure-response-401-403-404.md
- contents/security/authorization-runtime-signals-shadow-evaluation.md
- contents/security/authz-decision-logging-design.md
- contents/security/delegated-admin-tenant-rbac.md
- contents/security/tenant-isolation-authz-testing.md
- contents/security/auth-observability-sli-slo-alerting.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- AuthZ Cache Inconsistency / Runtime Debugging 장애가 나면 복구 순서는?
- authz cache inconsistency 운영 대응 체크리스트가 뭐야?
- AuthZ Cache Inconsistency / Runtime Debugging에서 blast radius를 어떻게 줄여?
- authz cache inconsistency 사고 후 어떤 증거를 남겨야 해?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 AuthZ Cache Inconsistency / Runtime Debugging를 다루는 playbook 문서다. 인가 캐시 문제는 단순 stale TTL보다, cache key 누락, version drift, negative cache, region skew, partial invalidation으로 나타나는 경우가 많아서 decision reason과 cache provenance를 함께 남겨야 디버깅이 가능하다. 검색 질의가 authz cache inconsistency, authorization cache debugging, stale decision cache, negative cache bug처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# AuthZ Cache Inconsistency / Runtime Debugging

> 한 줄 요약: 인가 캐시 문제는 단순 stale TTL보다, cache key 누락, version drift, negative cache, region skew, partial invalidation으로 나타나는 경우가 많아서 decision reason과 cache provenance를 함께 남겨야 디버깅이 가능하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Authorization Graph Caching](./authorization-graph-caching.md)
> - [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)
> - [Auth Failure Response Contracts: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: authz cache inconsistency, authorization cache debugging, stale decision cache, negative cache bug, policy version drift, graph snapshot drift, stale graph snapshot, authz graph version drift, authorization graph caching, cache key omission, tenant cache mixup, authz runtime debug, cache provenance, negative cache case study, stale deny, grant but still denied, tenant-specific 403, only one tenant 403, cross-tenant 403, tenant-only 404, inconsistent 401 404, 401 404 flip, authn authz drift, concealment drift, cached 404 after grant
retrieval-anchor-keywords: authz cache debug entry cue, advanced authz debugging jump-in, stale deny runtime debugging gate, beginner fallback to grant path primer bridge, runtime debug vs deep dive, authz cache next step, authz cache return path, authz tenant catalog return, runtime debugging beginner safe route

---

## 시작 전에: 이 문서의 역할과 입장 큐

- 이 문서는 `deep dive` 중에서도 runtime `debugging` 중심 문서다. pod/tenant/request pair를 비교하면서 증거를 좁힐 때 읽는다.
- 이 문서는 `primer`가 아니다. `grant했는데 아직 403/404`를 처음 설명하는 단계라면 먼저 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 간다.
- 이 문서는 cache 구조를 처음 배우는 `deep dive 입문`도 아니다. `authorization graph cache`/`relationship cache` 용어부터 정리해야 하면 먼저 `[primer]` [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md), 그다음 `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md)로 간다.
- 이 문서는 `survey`도 아니다. authz cache/tenant 문서 전체에서 다음 갈래를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 돌아간다.
- 이 문서는 `recovery` runbook도 아니다. 실시간 복구 순서보다 "어느 cache layer가 어긋났는지"를 증거로 고정하는 데 초점을 둔다.

### 30초 return path

먼저 외워 둘 기본값은 간단하다.
`grant path`와 `cache 구조`를 먼저 정리했고, 이제 `runtime evidence`를 맞추는 단계일 때 이 문서가 맞다.

| 지금 내 상태 | 먼저 볼 역할 | 먼저 갈 문서 | 이 문서를 바로 열어도 되는가 |
|---|---|---|---|
| `권한 줬는데 아직 403/404`를 처음 설명해야 함 | `primer bridge` | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | 아직 이르다 |
| `graph cache`, `relationship cache`, `negative cache` 용어가 아직 헷갈림 | `primer` -> `deep dive 입문` | [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md) -> [Authorization Caching / Staleness](./authorization-caching-staleness.md) | 대체로 아직 이르다 |
| 이미 pod/tenant/request pair 차이와 cache provenance를 대조 중 | `runtime debugging deep dive` | 이 문서 | 이제 적절하다 |

다음 셋 중 하나라도 "아직 아니다"라면 이 문서보다 앞 문서로 돌아간다.

- 응답 의미를 이미 구분했다: `403`인지 concealment `404`인지 안다.
- stale 위치를 이미 좁혔다: grant path, cache key, negative cache 중 어디가 의심되는지 말할 수 있다.
- 비교 증거가 있다: same actor 다른 pod, same resource 다른 tenant, invalidation 전후 request pair 중 하나를 잡았다.

| 나는 어디서 왔나 | 이 문서에서 먼저 볼 구간 | 다음 문서 |
|---|---|---|
| `[primer bridge]`에서 stale deny를 막 분리했다 | `4. runtime debugging에는 cache provenance가 필요하다` + `7. debugging은 request pair 비교가 유용하다` | `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md) |
| `[primer]`/`[deep dive 입문]`에서 cache key, version drift 개념을 막 정리했다 | `2. cache key omission은 아주 흔한 사고다` + `5. partial invalidation은 조용한 tail을 만든다` | `[deep dive]` [Authorization Graph Caching](./authorization-graph-caching.md) |
| 이미 운영 로그에서 pod/tenant별 allow/deny 차이를 잡았다 | `실전 시나리오 1-3` + `운영 체크리스트` | `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md), `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md) |

- runtime debugging 문서를 읽은 뒤에는 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 돌아가 다음 갈래를 고른다.

## 핵심 개념

인가 캐시는 성능을 위해 붙이지만, 장애는 성능이 아니라 "왜 어떤 요청은 allow고 어떤 요청은 deny인가"로 나타난다.

특히 위험한 경우:

- 동일 사용자/동일 리소스인데 pod마다 결과가 다름
- tenant A 권한이 tenant B에 섞여 보임
- 같은 tenant admin인데 특정 tenant에서만 403이 반복됨
- 권한 회수 후 일부 route만 계속 allow
- old deny / new allow가 특정 region에서만 발생

즉 authz cache incident의 핵심은 TTL이 아니라 decision provenance를 복원하는 것이다.

---

## 깊이 들어가기

### 1. inconsistency는 여러 층에서 생긴다

- role/member lookup cache
- ownership snapshot cache
- PDP decision cache
- edge/gateway authz cache
- negative cache for "not found / denied"

각 층의 drift가 다른 증상을 만든다.
relationship-based authz라면 ownership snapshot cache나 computed decision cache drift를 [Authorization Graph Caching](./authorization-graph-caching.md)의 runtime incident로 같이 봐야 한다.

### 2. cache key omission은 아주 흔한 사고다

빠뜨리기 쉬운 축:

- tenant id
- actor type
- policy version
- route class
- delegated scope

이 중 하나라도 빠지면 cross-tenant 또는 cross-role bleed가 난다.

### 3. negative cache는 특히 조심해야 한다

예:

- 잠깐 deny됐던 결과를 오래 캐시
- resource not found를 404 concealment와 함께 장시간 캐시

그러면 권한이 복구돼도 계속 deny된다.

### 4. runtime debugging에는 cache provenance가 필요하다

최소한 남길 것:

- decision came from cache or recompute
- cache key fingerprint
- policy version
- graph snapshot version
- cached_at
- cache layer name
- invalidation event id

이게 없으면 stale policy인지 graph snapshot drift인지 policy bug인지 구분이 안 된다.

### 5. partial invalidation은 조용한 tail을 만든다

예:

- DB는 바뀜
- 일부 pod만 invalidation 받음
- edge cache는 old value 유지

이때 "대부분 정상"이라 더 찾기 어렵다.

### 6. tenant isolation과 concealment policy가 함께 있으면 디버깅이 더 어려워진다

외부에는 같은 404라도 내부 원인은 다를 수 있다.

- not found
- tenant mismatch
- stale negative cache

그래서 internal reason code가 필수다.
인증 컨텍스트 복원까지 route나 pod마다 흔들리면,
어떤 요청은 anonymous로 해석돼 `401`, 다른 요청은 stale deny concealment로 `404`가 나오는 식의 `401`/`404` flip도 생길 수 있다.

### 7. debugging은 request pair 비교가 유용하다

유용한 비교 축:

- same actor, different pod
- same resource, different region
- same request before/after invalidation

이 비교로 cache layer 문제를 빨리 좁힐 수 있다.

### 8. 복구는 cache purge만이 아니다

가능한 레버:

- scoped purge
- negative cache disable
- direct recompute for hot routes
- old policy evaluator fallback
- cache key hotfix

---

## 실전 시나리오

### 시나리오 1: 권한 회수 후 일부 요청만 계속 allow된다

문제:

- partial invalidation 또는 stale ownership snapshot, 즉 relationship graph snapshot drift

대응:

- decision provenance를 확인한다
- pod/region별 cache hit 차이를 본다
- hot route에 direct recompute를 임시 적용한다

### 시나리오 2: 어떤 tenant에서만 403/404가 급증한다

문제:

- concealment policy 자체가 아니라 tenant key omission 또는 stale membership cache일 수 있다

대응:

- cache key에 tenant id가 포함되는지 본다
- negative cache hit ratio를 본다
- same resource cross-tenant pair를 비교한다
- delegated scope가 key에 포함되는지도 함께 본다

### 시나리오 3: 같은 route가 pod/tenant별로 `401`과 `404` 사이에서 흔들린다

문제:

- 일부 요청은 authn context hydrate에 실패해 anonymous로 보이고, 다른 요청은 stale deny concealment를 재사용한다

대응:

- gateway/app의 auth failure mapping을 같은 request id로 비교한다
- internal deny reason과 external status를 분리해 본다
- authn cache/session cache와 authz negative cache를 따로 purge 또는 bypass한다

---

## 코드로 보기

### 1. decision provenance 예시

```java
public record DecisionProvenance(
        String layer,
        String cacheKeyHash,
        String policyVersion,
        String graphSnapshotVersion,
        Instant cachedAt,
        boolean cacheHit
) {
}
```

### 2. 운영 체크리스트

```text
1. authz decision마다 cache provenance를 복원할 수 있는가
2. tenant/policy version/graph snapshot version/delegated scope가 cache key에 포함되는가
3. negative cache를 별도 layer로 관측하는가
4. hot route에서 scoped purge/direct recompute 레버가 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| aggressive decision cache | 성능이 좋다 | inconsistency blast radius가 커진다 | low-risk read heavy path |
| provenance-rich cache | 디버깅이 쉽다 | 메타데이터 비용이 늘어난다 | authz가 중요한 시스템 |
| negative cache | miss 비용이 줄어든다 | stale deny가 길어진다 | 매우 신중히 |
| direct recompute fallback | 정확성이 강하다 | latency와 DB 비용이 늘어난다 | hot fix, admin/high-risk route |

판단 기준은 이렇다.

- tenant/ownership drift가 보안상 치명적인가
- cache hit율보다 디버깅 가능성이 더 중요한 route가 있는가
- negative cache를 운영할 준비가 되어 있는가
- scoped purge와 recompute fallback을 제공할 수 있는가

---

## 꼬리질문

> Q: authz cache inconsistency에서 가장 흔한 실수는 무엇인가요?
> 의도: TTL보다 cache key omission을 먼저 보는지 확인
> 핵심: tenant, policy version, delegated scope 같은 key 축을 빠뜨리는 것이다.

> Q: negative cache가 왜 위험한가요?
> 의도: stale deny를 이해하는지 확인
> 핵심: 권한이나 존재 상태가 바뀌어도 예전 deny/not-found 결과가 오래 남을 수 있기 때문이다.

> Q: cache provenance가 왜 필요한가요?
> 의도: policy bug와 stale cache를 구분하는지 확인
> 핵심: 어떤 layer의 어떤 cached decision인지 알아야 재현과 복구가 가능하기 때문이다.

> Q: purge만이 항상 답인가요?
> 의도: 다른 복구 레버를 아는지 확인
> 핵심: 아니다. direct recompute, negative cache disable, old evaluator fallback이 더 안전할 수 있다.

## 다음 단계와 복귀 경로

- cache 구조와 trade-off를 다시 정리하고 싶으면 [Authorization Caching / Staleness](./authorization-caching-staleness.md)
- graph/relationship cache 쪽 증거를 더 파고들고 싶으면 [Authorization Graph Caching](./authorization-graph-caching.md)
- negative cache 실전 사례를 이어서 보고 싶으면 [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)
- authz cache 말고 다른 보안 증상 갈래를 다시 고르고 싶으면 [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog), [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)

## 한 줄 정리

AuthZ cache incident를 잘 다루려면 TTL이 아니라 decision provenance, cache key completeness, negative cache behavior를 중심으로 런타임 inconsistency를 디버깅해야 한다.
