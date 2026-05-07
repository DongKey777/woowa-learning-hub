---
schema_version: 3
title: Policy Snapshot Cache 설계
concept_id: system-design/policy-snapshot-cache-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- policy snapshot
- config cache
- authz cache
- quota cache
aliases:
- policy snapshot
- config cache
- authz cache
- quota cache
- session cache
- versioned snapshot
- stale policy
- fallback
- checksum
- invalidation
- Policy Snapshot Cache 설계
- policy snapshot cache design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/feature-flag-control-plane-design.md
- contents/system-design/config-distribution-system-design.md
- contents/system-design/edge-authorization-service-design.md
- contents/system-design/rate-limit-config-service-design.md
- contents/system-design/session-store-design-at-scale.md
- contents/system-design/distributed-cache-design.md
- contents/system-design/secrets-distribution-system-design.md
- contents/system-design/multi-tenant-saas-isolation-design.md
- contents/system-design/multi-region-active-active-design.md
- contents/system-design/tenant-aware-search-architecture-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Policy Snapshot Cache 설계 설계 핵심을 설명해줘
- policy snapshot가 왜 필요한지 알려줘
- Policy Snapshot Cache 설계 실무 트레이드오프는 뭐야?
- policy snapshot 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Policy Snapshot Cache 설계를 다루는 deep_dive 문서다. policy snapshot cache는 flag, config, quota, authz, session 같은 정책 데이터를 버전화해 빠르게 읽고 안전하게 갱신하는 캐시 계층이다. 검색 질의가 policy snapshot, config cache, authz cache, quota cache처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Policy Snapshot Cache 설계

> 한 줄 요약: policy snapshot cache는 flag, config, quota, authz, session 같은 정책 데이터를 버전화해 빠르게 읽고 안전하게 갱신하는 캐시 계층이다.

retrieval-anchor-keywords: policy snapshot, config cache, authz cache, quota cache, session cache, versioned snapshot, stale policy, fallback, checksum, invalidation

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Edge Authorization Service 설계](./edge-authorization-service-design.md)
> - [Rate Limit Config Service 설계](./rate-limit-config-service-design.md)
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)

## 핵심 개념

정책 데이터는 자주 읽히고, 아주 중요하고, 자주 바뀌지 않는다.  
그래서 snapshot cache와 궁합이 좋다.

- feature flag snapshot
- config snapshot
- authz policy snapshot
- quota snapshot
- session version snapshot

즉, policy snapshot cache는 제어 평면을 데이터 평면에서 빠르게 읽기 위한 저장 계층이다.

## 깊이 들어가기

### 1. 왜 snapshot이어야 하나

정책 데이터는 원본 저장소를 매 요청마다 때리면 느리다.

- flag eval
- authz check
- quota lookup
- session validation

snapshot은 versioned copy를 읽게 해 속도를 확보한다.

### 2. Capacity Estimation

예:

- 초당 수십만 policy read
- 수백 개 버전 동시 유지
- refresh는 분당/초당 단위

쓰기보다 읽기가 훨씬 많다.  
그래서 cache hit ratio와 refresh latency가 핵심이다.

봐야 할 숫자:

- policy read QPS
- snapshot refresh latency
- stale window
- version adoption rate
- fallback hit rate

### 3. snapshot lifecycle

```text
Source of Truth
  -> Build Snapshot
  -> Validate / Checksum
  -> Publish Version
  -> Data Plane Refresh
  -> Fallback to Last Known Good
```

### 4. stale policy management

정책은 stale해지면 위험하다.

- revoke가 늦어짐
- quota가 늦게 반영됨
- 잘못된 flag가 유지됨

그래서 critical path는 짧은 TTL 또는 synchronous verify가 필요하다.

### 5. checksum and integrity

스냅샷은 무결성이 중요하다.

- checksum
- version id
- publish timestamp
- source revision

이 부분은 [Config Distribution System 설계](./config-distribution-system-design.md)와 [Secrets Distribution System 설계](./secrets-distribution-system-design.md)와 연결된다.

### 6. invalidation strategy

모든 스냅샷을 즉시 삭제하는 건 위험하다.

- graceful rollover
- old/new overlap
- emergency revoke
- pinning by critical action

### 7. multi-tenant and multi-region

스냅샷은 tenant와 region 경계를 따라야 한다.

- tenant-specific quota
- region-specific policy
- global default
- local override

이 부분은 [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md), [Multi-Region Active-Active 설계](./multi-region-active-active-design.md), [Tenant-aware Search Architecture 설계](./tenant-aware-search-architecture-design.md)와 잘 맞는다.

## 실전 시나리오

### 시나리오 1: 권한 회수

문제:

- role을 바꿨는데 일부 노드가 옛 권한을 본다

해결:

- versioned snapshot
- short TTL for critical authz
- fallback to sync verify

### 시나리오 2: rate limit 정책 변경

문제:

- 특정 endpoint 제한을 즉시 바꿔야 한다

해결:

- 정책 snapshot publish
- edge refresh

### 시나리오 3: feature flag rollback

문제:

- 잘못된 롤아웃을 빨리 되돌려야 한다

해결:

- last-known-good snapshot
- version pinning

## 코드로 보기

```pseudo
function readPolicy(ctx):
  snapshot = cache.get(ctx.tenant, ctx.kind)
  if snapshot == null:
    snapshot = loadLastKnownGood(ctx)
  if snapshot.version < ctx.requiredVersion:
    refresh()
  return snapshot
```

```java
public PolicySnapshot current(PolicyKey key) {
    return snapshotCache.getOrFallback(key);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Live read from source | 최신성 좋다 | 느리다 | 낮은 QPS |
| Versioned snapshot cache | 빠르고 안정적이다 | stale window 존재 | 대부분의 정책 읽기 |
| Synchronous introspection | revoke가 빠르다 | auth server 의존 | 민감 경로 |
| Per-tenant snapshot | 격리가 좋다 | 버전 관리가 늘어난다 | SaaS |
| Last-known-good fallback | 장애에 강하다 | 오래된 정책 위험 | control plane 장애 |

핵심은 policy snapshot cache가 단순 캐시가 아니라 **제어 평면 정책을 빠르게 읽기 위한 안전한 버전화 계층**이라는 점이다.

## 꼬리질문

> Q: snapshot cache와 일반 cache는 무엇이 다른가요?
> 의도: 정책 스냅샷의 버전성과 안전성을 이해하는지 확인
> 핵심: snapshot은 versioned policy를 안전하게 읽는 데 초점이 있다.

> Q: stale policy를 왜 위험하게 보나요?
> 의도: 권한/quota/flag의 최신성 중요성을 아는지 확인
> 핵심: revoke나 quota 변경이 늦게 반영되면 사고가 난다.

> Q: fallback은 어떻게 정하나요?
> 의도: 장애 시 fail-open/fail-close 판단 이해 확인
> 핵심: 민감 경로는 fail-close, 비핵심 경로는 degraded mode를 쓴다.

> Q: 체크섬은 왜 필요한가요?
> 의도: 배포 무결성 이해 확인
> 핵심: 정책 파일이 손상되거나 잘못 배포되는 것을 막는다.

## 한 줄 정리

Policy snapshot cache는 flag, config, quota, authz 같은 정책 데이터를 버전화해 빠르게 읽고, 장애 시에도 마지막으로 안전한 상태를 유지하게 한다.

