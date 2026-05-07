---
schema_version: 3
title: PDP / PEP Boundaries Design
concept_id: security/pdp-pep-boundaries-design
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- PDP
- PEP
- policy decision point
- policy enforcement point
aliases:
- PDP
- PEP
- policy decision point
- policy enforcement point
- authorization architecture
- decision latency
- enforcement
- policy engine
- sidecar
- gateway
- split policy
- relationship-based authz
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/authz-decision-logging-design.md
- contents/security/authorization-caching-staleness.md
- contents/security/authorization-graph-caching.md
- contents/security/permission-model-drift-authz-graph-design.md
- contents/security/delegated-admin-tenant-rbac.md
- contents/security/tenant-isolation-authz-testing.md
- contents/security/audit-logging-auth-authz-traceability.md
- contents/security/idor-bola-patterns-and-fixes.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- PDP / PEP Boundaries Design 핵심 개념을 설명해줘
- PDP가 왜 필요한지 알려줘
- PDP / PEP Boundaries Design 실무 설계 포인트는 뭐야?
- PDP에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 PDP / PEP Boundaries Design를 다루는 deep_dive 문서다. PDP는 정책 결정을 내리고 PEP는 그 결정을 실행한다. 경계를 분리해야 캐시, 로깅, fallback, audit가 관리 가능해진다. 검색 질의가 PDP, PEP, policy decision point, policy enforcement point처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# PDP / PEP Boundaries Design

> 한 줄 요약: PDP는 정책 결정을 내리고 PEP는 그 결정을 실행한다. 경계를 분리해야 캐시, 로깅, fallback, audit가 관리 가능해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Authorization Graph Caching](./authorization-graph-caching.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)

retrieval-anchor-keywords: PDP, PEP, policy decision point, policy enforcement point, authorization architecture, decision latency, enforcement, policy engine, sidecar, gateway, split policy, relationship-based authz, graph snapshot version, tenant-scoped invalidation, tenant graph cache

---

## 핵심 개념

PDP(Policy Decision Point)는 "허용할지 말지"를 결정하는 곳이고,  
PEP(Policy Enforcement Point)는 그 결정을 실제로 막거나 통과시키는 곳이다.

둘을 분리하는 이유:

- 정책 엔진과 실행 지점을 분리할 수 있다
- 캐시와 fallback을 따로 설계할 수 있다
- audit와 decision log를 분리할 수 있다

즉 PDP는 머리, PEP는 손이다.

---

## 깊이 들어가기

### 1. PDP가 무엇을 보나

PDP는 일반적으로:

- user or actor
- resource
- action
- context
- policy version

을 보고 결정을 만든다.

### 2. PEP가 무엇을 하냐

PEP는 다음 위치에 있을 수 있다.

- API gateway
- sidecar proxy
- application filter
- middleware

PEP는 PDP의 결정을 집행하고, 필요하면 요청을 차단한다.

### 3. 분리의 장점

분리하면 다음이 쉬워진다.

- policy engine 교체
- enforcement 위치 변경
- cache 적용
- deny reason 로깅

### 4. 분리의 위험

분리 자체가 보안을 자동으로 주지는 않는다.

- PDP와 PEP가 다른 policy version을 보면 안 된다
- network failure 시 fail-open/fail-closed를 정해야 한다
- cache stale이 있으면 잘못된 결정이 나온다

relationship-based authz를 쓰면 mismatch 대상은 `policy version` 하나로 끝나지 않는다.  
PDP는 graph snapshot/version을 판단 근거로 들고, PEP는 tenant-scoped invalidation token이나 cache bust가 실제 enforcement tier까지 전파됐는지 확인해야 한다.  
delegated admin scope 변경이나 tenant ownership 이동처럼 edge가 바뀌는 순간은 [Authorization Graph Caching](./authorization-graph-caching.md), [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md), [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)을 같이 봐야 한다.

### 5. inline authorization와 중앙 정책의 균형

모든 결정을 중앙으로만 보내면 느려질 수 있다.  
모든 결정을 앱 코드에 넣으면 drift가 생긴다.

그래서 보통:

- coarse control은 PEP
- fine-grained decision은 PDP
- 민감 경로는 app-level recheck

---

## 실전 시나리오

### 시나리오 1: gateway에서 먼저 차단하고 싶다

대응:

- PEP를 gateway에 둔다
- PDP는 중앙 정책 서비스에 둔다
- 앱은 민감 작업을 다시 확인한다

### 시나리오 2: PDP가 죽으면 전체 인증이 멈춤

대응:

- fallback policy를 정한다
- 중요 경로는 fail-closed
- 덜 민감한 경로만 제한적 완화

### 시나리오 3: policy version이 서로 다름

대응:

- PDP와 PEP가 같은 version을 보도록 배포한다
- version mismatch를 metric으로 본다
- cache invalidation을 붙인다

---

## 코드로 보기

### 1. PDP 결정 개념

```java
public AuthorizationDecision decide(Subject subject, Resource resource, Action action) {
    return policyEngine.evaluate(subject, resource, action);
}
```

### 2. PEP enforcement 개념

```java
public void enforce(AuthorizationDecision decision) {
    if (!decision.allowed()) {
        throw new AccessDeniedException(decision.reasonCode());
    }
}
```

### 3. gateway + app double check

```text
1. gateway PEP가 coarse deny를 한다
2. PDP가 policy version으로 결정을 준다
3. 앱이 민감 작업을 다시 recheck한다
4. decision log와 audit log를 남긴다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| centralized PDP | 정책 관리가 쉽다 | latency와 dependency가 생긴다 | 대규모 플랫폼 |
| embedded PEP | 빠르다 | 정책 drift가 생기기 쉽다 | edge enforcement |
| app-only authz | 단순하다 | 일관성이 약하다 | 작은 서비스 |
| PDP + PEP split | 유연하다 | 설계가 복잡하다 | 대부분의 중대형 시스템 |

판단 기준은 이렇다.

- 정책이 자주 바뀌는가
- enforcement 지점이 여러 개인가
- audit와 decision log를 분리할 수 있는가
- fail-open/closed를 제어할 수 있는가

---

## 꼬리질문

> Q: PDP와 PEP의 차이는 무엇인가요?
> 의도: 결정과 집행을 구분하는지 확인
> 핵심: PDP는 판단, PEP는 enforcement다.

> Q: 왜 분리하나요?
> 의도: 정책 관리와 실행 경계의 장점을 아는지 확인
> 핵심: 캐시, 로그, 교체, fallback을 나눠 설계할 수 있기 때문이다.

> Q: 분리하면 자동으로 안전해지나요?
> 의도: version mismatch와 stale cache를 아는지 확인
> 핵심: 아니다. version과 fallback을 같이 관리해야 한다.

> Q: PEP는 어디에 있을 수 있나요?
> 의도: enforcement 위치를 이해하는지 확인
> 핵심: gateway, sidecar, filter, middleware다.

## 한 줄 정리

PDP는 정책을 결정하고 PEP는 집행하며, 둘의 경계를 분리해야 authorization 아키텍처가 운영 가능해진다.
