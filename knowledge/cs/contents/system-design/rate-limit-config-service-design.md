---
schema_version: 3
title: Rate Limit Config Service 설계
concept_id: system-design/rate-limit-config-service-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- rate limit config
- quota policy
- limit rollout
- token bucket config
aliases:
- rate limit config
- quota policy
- limit rollout
- token bucket config
- tenant limit
- endpoint limit
- dynamic throttling
- policy snapshot
- propagation
- safety guard
- Rate Limit Config Service 설계
- rate limit config service design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/rate-limiter-design.md
- contents/system-design/api-gateway-control-plane-design.md
- contents/system-design/config-distribution-system-design.md
- contents/system-design/entitlement-quota-design.md
- contents/system-design/feature-flag-control-plane-design.md
- contents/system-design/multi-tenant-saas-isolation-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Rate Limit Config Service 설계 설계 핵심을 설명해줘
- rate limit config가 왜 필요한지 알려줘
- Rate Limit Config Service 설계 실무 트레이드오프는 뭐야?
- rate limit config 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Rate Limit Config Service 설계를 다루는 deep_dive 문서다. rate limit config service는 endpoint, tenant, user, key별 제한 정책을 중앙에서 관리하고, edge와 app에 안전하게 배포하는 제어 평면이다. 검색 질의가 rate limit config, quota policy, limit rollout, token bucket config처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Rate Limit Config Service 설계

> 한 줄 요약: rate limit config service는 endpoint, tenant, user, key별 제한 정책을 중앙에서 관리하고, edge와 app에 안전하게 배포하는 제어 평면이다.

retrieval-anchor-keywords: rate limit config, quota policy, limit rollout, token bucket config, tenant limit, endpoint limit, dynamic throttling, policy snapshot, propagation, safety guard

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)
> - [Entitlement / Quota 설계](./entitlement-quota-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)

## 핵심 개념

Rate limit config는 enforcement가 아니다.  
실전에서는 아래를 설계해야 한다.

- 어떤 키로 제한할지
- 어느 계층에서 적용할지
- 언제 변경을 반영할지
- 급한 정책을 어떻게 롤백할지
- tenant별 공정성을 어떻게 보장할지

즉, config service는 limiter 정책을 운영하는 중앙 제어 계층이다.

## 깊이 들어가기

### 1. 정책 모델

정책은 보통 여러 축을 가진다.

- global
- tenant
- user
- IP
- API key
- endpoint

각 축의 우선순위를 명확히 해야 한다.

### 2. Capacity Estimation

예:

- 수천 정책 변경/일
- 초당 수만 검사 요청

정책 읽기는 많고 쓰기는 적다.  
그래서 snapshot 기반 배포가 효율적이다.

봐야 할 숫자:

- policy lookup QPS
- propagation delay
- stale policy rate
- rollback time
- conflict rate

### 3. publish flow

```text
Admin / Automation
  -> Validate
  -> Version
  -> Snapshot
  -> Publish
  -> Edge / App Refresh
```

### 4. guard rails

rate limit 정책은 잘못 바꾸면 장애를 만든다.

- 상한선
- 최소 허용치
- canary rollout
- automatic rollback

### 5. tenant-aware fairness

멀티테넌트 환경에서는 한 tenant가 다른 tenant를 잠식하지 않아야 한다.

- tenant quota
- burst budget
- emergency override

이 부분은 [Entitlement / Quota 설계](./entitlement-quota-design.md)와 연결된다.

### 6. edge sync

정책은 edge와 app에 빠르게 전파돼야 한다.

- push notification
- pull snapshot
- version pinning

이 부분은 [Config Distribution System 설계](./config-distribution-system-design.md)와 같다.

### 7. observability

정책 변경 후를 봐야 한다.

- allow/reject ratio
- error spikes
- latency shifts
- policy version adoption

## 실전 시나리오

### 시나리오 1: 로그인 공격 대응

문제:

- `/login` limit을 빠르게 낮춰야 한다

해결:

- endpoint policy update
- canary rollout
- revert path 확보

### 시나리오 2: 특정 tenant 과다 사용

문제:

- 한 tenant가 API를 과하게 사용한다

해결:

- tenant quota 축소
- user-level carve-out

### 시나리오 3: 잘못된 제한 배포

문제:

- 전역 limit을 너무 낮게 걸어버렸다

해결:

- last-known-good snapshot
- emergency override

## 코드로 보기

```pseudo
function publishLimit(policy):
  validate(policy)
  version = store.save(policy)
  snapshot = buildSnapshot(version)
  distributor.broadcast(snapshot)
```

```java
public LimitPolicy current(String tenantId, String endpoint) {
    return policyCache.load(tenantId, endpoint);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Static config | 단순하다 | 대응이 느리다 | 작은 서비스 |
| Dynamic config service | 반영이 빠르다 | 운영 복잡도 | 실서비스 |
| Snapshot-based rollout | 안정적이다 | propagation 지연 | 대부분의 시스템 |
| Per-tenant override | 유연하다 | 정책 폭증 | SaaS |
| Hard guard rails | 안전하다 | 유연성이 낮다 | 민감한 경로 |

핵심은 rate limit config service가 단순 저장소가 아니라 **방어 정책을 안전하게 배포하는 운영 시스템**이라는 점이다.

## 꼬리질문

> Q: limiter와 config service는 왜 분리하나요?
> 의도: 실행과 정책 관리 분리 이해 확인
> 핵심: 정책 변경과 요청 경로를 분리해야 한다.

> Q: canary rollout은 왜 필요한가요?
> 의도: 정책 변경의 위험 제어 이해 확인
> 핵심: 잘못된 제한은 즉시 장애를 만들 수 있기 때문이다.

> Q: tenant quota와 endpoint limit은 어떻게 다른가요?
> 의도: 정책 축 분리 이해 확인
> 핵심: 공정성과 보호 대상이 다르다.

> Q: 정책 롤백은 어떻게 빠르게 하나요?
> 의도: last-known-good와 version pin 이해 확인
> 핵심: snapshot version을 즉시 되돌린다.

## 한 줄 정리

Rate limit config service는 limiter 정책을 버전, 롤아웃, 롤백, tenant fairness까지 포함해 중앙에서 관리하는 제어 평면이다.

