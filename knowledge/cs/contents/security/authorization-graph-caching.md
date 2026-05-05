# Authorization Graph Caching

> 한 줄 요약: authorization graph caching은 관계 기반 권한 계산을 빠르게 하지만, 그래프 업데이트와 policy version이 늦으면 잘못된 권한을 계속 허용할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)
> - [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)

retrieval-anchor-keywords: authorization graph cache, authorization graph caching, graph cache, relationship-based access control, relationship cache, relationship edge cache, path cache, edge cache, authz graph, invalidation, policy version, graph snapshot, graph snapshot cache, graph snapshot drift, graph snapshot version mismatch, authz runtime debug, auth shadow divergence, tenant graph, shortest path authz, tenant-scoped graph invalidation, delegated admin invalidation, authorization graph cache deep dive, graph cache beginner handoff, stale deny primer bridge, graph cache next step, graph cache return path, authz tenant catalog return, grant path first graph cache later, runtime debugging before graph internals, graph snapshot evidence gate, relationship cache 다음 문서, tenant별 403 왜 다르죠, cache key version mismatch why

---

## 시작 전에: 이 문서의 역할과 입장 큐

- 이 문서는 `deep dive`다. relationship/path cache, snapshot version, invalidation fan-out을 설계 관점으로 다룬다.
- 이 문서는 `primer`가 아니다. `authorization graph cache`/`relationship cache` 용어가 먼저 막히면 `[primer]` [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md)로 간다.
- 이 문서는 `survey`도 아니다. authz cache/tenant 문서 전체에서 다음 갈래를 다시 고르려면 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 돌아간다.
- `grant 후 403`/`cached 404 after grant`/`tenant-specific 403`를 처음 분해하는 단계라면 먼저 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 간다.
- pod/tenant별 allow/deny 불일치, cache key 누락, version drift를 운영 증거로 좁히는 중이라면 graph internals보다 먼저 `[playbook]` 성격의 `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)으로 간다.
- 이 문서는 대응 절차 중심 `recovery` 문서가 아니다. 장애 복구 순서보다 "graph cache를 설계할 때 왜 깨지는가"를 설명하는 문서다.

### 30초 return path

먼저 외워 둘 기본값은 간단하다.
`grant path`와 `runtime debugging`이 먼저이고, graph cache internals는 나중이다.

| 지금 내 상태 | 먼저 볼 역할 | 먼저 갈 문서 | 이 문서를 바로 열어도 되는가 |
|---|---|---|---|
| `권한 줬는데 아직 403/404`를 처음 설명해야 함 | `primer bridge` | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | 아직 이르다 |
| pod/tenant마다 allow/deny가 다르고 로그 키를 대조 중 | `playbook`에 가까운 runtime debugging | [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) | 대체로 아직 이르다 |
| 이미 `graph snapshot version`, `relationship edge`, `tenant-scoped invalidation`이 증거로 잡힘 | `deep dive` | 이 문서 | 이제 적절하다 |

다음 셋 중 하나라도 "아직 아니다"라면 이 문서보다 앞 문서로 돌아간다.

- 응답 의미를 이미 구분했다: `403`인지 concealment `404`인지 안다.
- stale 위치를 이미 좁혔다: grant path, cache key, version drift 중 어디가 의심되는지 말할 수 있다.
- graph 증거가 있다: `graph snapshot/version/edge invalidation` 같은 단어가 로그나 설계에서 실제로 보인다.

| 나는 어디서 왔나 | 이 문서에서 먼저 볼 구간 | 다음 문서 |
|---|---|---|
| `[primer bridge]`에서 stale deny를 분리한 직후 | `2. path cache는 위험도가 높다` + `3. versioned graph snapshot이 유용하다` | `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md) |
| `[playbook]`에 가까운 runtime debugging에서 graph snapshot/version mismatch가 이미 잡힘 | `3. versioned graph snapshot이 유용하다` + `4. invalidation fan-out` | `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md) |
| delegated revoke/tenant ownership move 뒤 graph invalidation이 의심됨 | `4. invalidation fan-out` + `실전 시나리오 2, 3` | `[deep dive]` [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md), `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md) |

- graph cache 문서를 읽은 뒤에는 `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog)로 돌아가 다음 갈래를 고른다.

## 어떤 질문일 때 이 문서를 열까

이 문서는 `graph cache 내부 설계와 invalidation trade-off`를 묻는 질문에 맞는다.

| query shape | 이 문서가 바로 답하는 것 | 먼저 다른 문서가 더 좋은 경우 |
|---|---|---|
| `graph snapshot version을 왜 로그에 남겨요?` | snapshot/version이 stale incident를 좁히는 이유 | 증상만 있고 version 증거가 없으면 [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) |
| `tenant별로 403이 다르면 cache key를 어떻게 봐요?` | tenant-scoped invalidation, key design, fan-out | `403`과 concealment `404`부터 헷갈리면 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |
| `relationship cache랑 path cache 차이가 뭐죠?` | cache granularity와 stale risk 차이 | 용어 입문이 먼저면 [Authorization Graph Cache / Relationship Cache Primer](./authorization-graph-cache-relationship-cache-primer.md) |

## 핵심 개념

authorization graph는 user, group, tenant, resource, role 사이의 관계를 그래프로 보는 모델이다.
이 그래프를 매번 계산하면 비쌀 수 있으므로 캐시를 둘 수 있다.

하지만 graph cache는 일반 cache보다 더 민감하다.

- edge 하나가 바뀌면 여러 decision이 달라진다
- path가 바뀌면 많은 resource에 영향이 간다
- tenant boundary가 섞이면 사고가 커진다

즉 graph cache는 빠르지만 invalidation이 더 어렵다.

---

## 깊이 들어가기

### 1. 무엇을 캐시하나

캐시 후보:

- relationship cache (user/group/tenant/resource edge cache)
- user -> group edges
- group -> role edges
- tenant -> resource ownership edges
- computed path decisions
- subtree membership

### 2. path cache는 위험도가 높다

경로 자체를 캐시하면 빠르지만, 업데이트가 어렵다.

- 한 edge 변경이 경로 전체를 바꾼다
- stale path가 잘못된 allow를 만든다
- negative cache도 오래 남을 수 있다

### 3. versioned graph snapshot이 유용하다

그래프를 versioned snapshot으로 다루면 좋다.

- snapshot version으로 decision을 묶는다
- version change 시 cache bust
- audit log에 version을 남긴다

이 snapshot version이 런타임 로그에서 빠지면 [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)처럼 stale allow/deny incident가 생겼을 때 원인을 좁히기 어렵다.
정책 rollout 중 divergence를 본다면 [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)처럼 policy version과 graph snapshot version을 분리해 관측해야 한다.

### 4. invalidation fan-out을 고려해야 한다

role 변경 하나가 여러 decision을 무효화할 수 있다.

- user membership
- team membership
- tenant ownership
- delegated admin scope

특히 delegated admin grant/revoke는 tenant-scoped admin edge 여러 개를 동시에 바꿀 수 있어서 [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md) 같은 scope model과 같이 설계해야 한다.
이 invalidation이 빠졌을 때 cross-tenant leak 여부를 확인하는 마지막 안전망은 [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)이다.

### 5. graph cache는 그래프 엔진과 결합해야 한다

단순 key-value cache만으로는 부족할 수 있다.

- adjacency cache
- path cache
- subtree cache
- version token

을 같이 써야 한다.

---

## 실전 시나리오

### 시나리오 1: group membership 변경 후 권한이 늦게 반영됨

대응:

- graph version을 올린다
- edge-based invalidation을 보낸다
- stale decision metric을 본다

### 시나리오 2: tenant ownership 이동 후 예전 권한이 남음

대응:

- ownership edge 캐시를 무효화한다
- tenant scope를 다시 계산한다
- reconciliation job을 돌린다

### 시나리오 3: path cache 때문에 cross-tenant 허용이 발생함

대응:

- tenant id를 cache key에 포함한다
- graph snapshot version을 붙인다
- negative authz test를 넣는다

---

## 코드로 보기

### 1. versioned graph cache

```java
public AuthorizationDecision decide(UserPrincipal user, Resource resource) {
    String key = user.id() + ":" + user.graphVersion() + ":" + resource.id();
    return graphCache.computeIfAbsent(key, ignored -> graphEngine.evaluate(user, resource));
}
```

### 2. edge invalidation

```java
public void onMembershipChanged(Long userId) {
    graphCache.evictByUser(userId);
    graphVersionService.bump(userId);
}
```

### 3. snapshot policy

```text
1. 그래프 버전을 명시한다
2. edge 변경 시 cache를 무효화한다
3. decision log에 version을 남긴다
4. tenant boundary를 cache key에 포함한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| no graph cache | 정확하다 | 느리다 | 작은 시스템 |
| edge cache | 빠르다 | invalidation이 필요하다 | 대부분 |
| path cache | 매우 빠르다 | stale risk가 크다 | 제한적 |
| versioned snapshot cache | 균형이 좋다 | version 관리가 필요하다 | 중대형 시스템 |

판단 기준은 이렇다.

- graph가 자주 바뀌는가
- tenant 경계가 중요한가
- path decision이 비싼가
- versioned invalidation을 운영할 수 있는가

---

## 꼬리질문

> Q: authorization graph cache가 왜 위험할 수 있나요?
> 의도: stale path decision을 아는지 확인
> 핵심: 관계 하나가 바뀌어도 캐시된 경로가 남을 수 있기 때문이다.

> Q: versioned snapshot이 왜 유용한가요?
> 의도: policy version과 graph version의 중요성을 아는지 확인
> 핵심: 어떤 그래프 기준으로 판단했는지 추적할 수 있다.

> Q: path cache와 edge cache의 차이는 무엇인가요?
> 의도: 캐시 granularity를 이해하는지 확인
> 핵심: edge는 관계, path는 계산 결과를 저장한다.

> Q: tenant id를 cache key에 넣어야 하나요?
> 의도: cross-tenant 오염을 아는지 확인
> 핵심: 그렇다. 섞이면 권한 사고가 난다.

## 한 줄 정리

authorization graph caching은 관계 기반 권한 계산을 빠르게 하지만, version과 tenant boundary가 없으면 stale decision을 만든다.
