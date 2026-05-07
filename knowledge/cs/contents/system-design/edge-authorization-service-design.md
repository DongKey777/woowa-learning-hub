---
schema_version: 3
title: Edge Authorization Service 설계
concept_id: system-design/edge-authorization-service-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- edge authorization
- authz service
- policy decision point
- policy enforcement point
aliases:
- edge authorization
- authz service
- policy decision point
- policy enforcement point
- tenant scope
- resource ownership
- cached authorization
- OPA
- JWT claims
- authorization caching
- Edge Authorization Service 설계
- edge authorization service design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/authentication-vs-authorization.md
- contents/system-design/api-gateway-control-plane-design.md
- contents/system-design/session-store-design-at-scale.md
- contents/system-design/edge-verifier-claim-skew-fallback-design.md
- contents/system-design/entitlement-quota-design.md
- contents/security/audit-logging-auth-authz-traceability.md
- contents/security/authorization-caching-staleness.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Edge Authorization Service 설계 설계 핵심을 설명해줘
- edge authorization가 왜 필요한지 알려줘
- Edge Authorization Service 설계 실무 트레이드오프는 뭐야?
- edge authorization 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Edge Authorization Service 설계를 다루는 deep_dive 문서다. edge authorization service는 요청이 백엔드까지 도달하기 전에 신원, 권한, 자원 범위를 빠르게 판단하는 엣지 정책 집행 계층이다. 검색 질의가 edge authorization, authz service, policy decision point, policy enforcement point처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Edge Authorization Service 설계

> 한 줄 요약: edge authorization service는 요청이 백엔드까지 도달하기 전에 신원, 권한, 자원 범위를 빠르게 판단하는 엣지 정책 집행 계층이다.

retrieval-anchor-keywords: edge authorization, authz service, policy decision point, policy enforcement point, tenant scope, resource ownership, cached authorization, OPA, JWT claims, authorization caching

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](../security/authentication-vs-authorization.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)
> - [Entitlement / Quota 설계](./entitlement-quota-design.md)
> - [Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)
> - [Authorization Caching / Staleness](../security/authorization-caching-staleness.md)

## 핵심 개념

Edge authorization은 "로그인했는가"를 보는 문제가 아니다.  
실전에서는 다음을 함께 판단해야 한다.

- 이 사용자가 누구인지
- 어떤 tenant에 속하는지
- 어떤 resource를 볼 수 있는지
- 어떤 action을 할 수 있는지
- 정책이 얼마나 최신인지
- 거부/허용 결과를 얼마나 빨리 내려야 하는지

즉, edge authz는 인증 결과를 바탕으로 요청의 허용 여부를 바로 내리는 정책 엔진이다.

## 깊이 들어가기

### 1. authn과 authz는 다른 문제다

인증은 신원 확인이고, 인가는 허용 범위 판단이다.  
엣지에서 authorization만 잘 해도 백엔드 공격면을 크게 줄일 수 있다.

- 인증: JWT, session, mTLS, external IdP
- 인가: role, permission, ownership, policy, tenant scope

### 2. Capacity Estimation

예:

- 초당 50만 edge request
- 요청당 1~3개의 authz check
- p95 5ms 이하 요구

그럼 policy lookup은 거의 항상 cache hit이어야 한다.  
원격 호출이 많은 설계는 edge의 의미가 없다.

봐야 할 숫자:

- authz QPS
- cache hit ratio
- policy propagation delay
- deny rate
- fallback rate

### 3. PDP와 PEP를 분리한다

```text
Client
  -> Gateway / PEP
  -> Edge Authorization Service / PDP
  -> Policy Store
  -> Deny or Allow
```

- PEP: policy enforcement point, 실제로 요청을 막는 지점
- PDP: policy decision point, 허용/거부를 계산하는 지점

이 분리를 해야 policy engine을 여러 enforcement point에 재사용할 수 있다.

### 4. 정책 모델

권장하는 정책 축:

- principal: user, service, api client
- resource: document, order, tenant, project
- action: read, write, approve, delete
- context: region, time, device, risk score

대부분의 실무는 RBAC만으로는 부족하고 ABAC 또는 RBAC+ownership이 필요하다.

### 5. 최신성 문제

인가 캐시가 stale하면 큰 사고가 난다.

- 권한 회수 후에도 access 유지
- tenant 탈퇴 후 resource 접근
- role 변경 후 반영 지연

완화책:

- 짧은 TTL
- versioned policy snapshot
- revoke event fan-out
- critical action은 synchronous check

이 부분은 [Authorization Caching / Staleness](../security/authorization-caching-staleness.md)와 연결된다.

### 6. edge에서 판단할 수 있는 것과 없는 것

엣지에서 좋은 판단:

- JWT claim 기반 role check
- tenant membership
- resource ownership prefix
- 간단한 quota/rate policy

엣지에서 무거운 판단:

- 복잡한 graph traversal
- 외부 데이터베이스 join
- 고비용 risk scoring

무거운 판단이 필요하면 정책을 edge-friendly하게 전처리해야 한다.

### 7. 감사와 설명 가능성

거부는 설명 가능해야 한다.

- 어떤 policy version이었는가
- 어떤 rule이 매칭됐는가
- deny reason code는 무엇인가

이런 기록은 [Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)와 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 관리자 화면 보호

문제:

- 일반 사용자가 admin endpoint를 호출한다

해결:

- edge에서 role + tenant scope를 확인
- deny reason code를 남김

### 시나리오 2: 권한 회수 직후

문제:

- 운영자가 사용자를 정지했는데 오래된 토큰이 살아 있다

해결:

- session version 또는 token introspection과 연동
- critical endpoint는 synchronous policy check

### 시나리오 3: 멀티 테넌트 자원 접근

문제:

- 같은 path라도 tenant마다 접근 범위가 다르다

해결:

- tenant-aware policy key
- resource ownership check

## 코드로 보기

```pseudo
function authorize(request):
  ctx = buildContext(request)
  policy = policyCache.get(ctx.tenant, ctx.route, ctx.version)
  decision = policy.evaluate(ctx)
  if decision.deny:
    return 403
  return allow()
```

```java
public AuthorizationDecision decide(AuthContext ctx) {
    PolicySnapshot snapshot = snapshotCache.current(ctx.tenantId());
    return policyEngine.evaluate(snapshot, ctx);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Gateway-local rules | 빠르다 | 표현력이 약하다 | 단순 edge policy |
| Remote PDP | 정책이 유연하다 | latency가 늘어난다 | 복잡한 권한 |
| Cached policy snapshot | 빠르고 현실적이다 | stale risk | 대부분의 서비스 |
| Synchronous introspection | 최신성이 좋다 | auth server 의존 | 민감 경로 |
| RBAC only | 구현이 쉽다 | 세밀한 제어가 약하다 | 단순 관리자 기능 |

핵심은 edge authorization이 단순 필터가 아니라 **엣지에서 실행되는 정책 결정 시스템**이라는 점이다.

## 꼬리질문

> Q: 인증과 인가를 왜 분리하나요?
> 의도: 신원 확인과 권한 판단의 차이를 아는지 확인
> 핵심: 둘은 다른 실패 모델과 저장 구조를 가진다.

> Q: edge에서 모든 권한을 판단할 수 있나요?
> 의도: edge-friendly policy의 한계를 아는지 확인
> 핵심: 단순 정책은 가능하지만 복잡한 그래프 판단은 무겁다.

> Q: policy cache가 stale하면 어떻게 하나요?
> 의도: 최신성과 성능 trade-off를 아는지 확인
> 핵심: versioned snapshot과 revoke fan-out이 필요하다.

> Q: deny reason을 왜 남기나요?
> 의도: 운영성과 감사 가능성을 아는지 확인
> 핵심: 사고 조사와 사용자 설명에 필요하다.

## 한 줄 정리

Edge authorization service는 요청이 백엔드에 도달하기 전에 권한, 자원 소유권, tenant scope를 빠르게 판단하는 엣지 정책 엔진이다.
