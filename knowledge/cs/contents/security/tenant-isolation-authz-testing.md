---
schema_version: 3
title: Tenant Isolation / AuthZ Testing
concept_id: security/tenant-isolation-authz-testing
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- tenant isolation
- authz testing
- owner mismatch
- tenant mismatch
aliases:
- tenant isolation
- authz testing
- owner mismatch
- tenant mismatch
- controller test
- service test
- integration test
- cross-tenant access
- ownership
- tenant boundary
- negative test
- 로그인 됐는데 왜 403
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/permission-checks-rest-flows-primer.md
- contents/security/role-vs-scope-vs-ownership-primer.md
- contents/security/idor-bola-patterns-and-fixes.md
- contents/security/delegated-admin-tenant-rbac.md
- contents/security/pdp-pep-boundaries-design.md
- contents/security/permission-model-drift-authz-graph-design.md
- contents/security/authorization-caching-staleness.md
- contents/security/authorization-graph-caching.md
- contents/security/audit-logging-auth-authz-traceability.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Tenant Isolation / AuthZ Testing 핵심 개념을 설명해줘
- tenant isolation가 왜 필요한지 알려줘
- Tenant Isolation / AuthZ Testing 실무 설계 포인트는 뭐야?
- tenant isolation에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Tenant Isolation / AuthZ Testing를 다루는 deep_dive 문서다. tenant isolation 테스트는 "한 테넌트의 권한이 다른 테넌트로 새지 않는가"를 시스템적으로 검증하는 보안 테스트다. 검색 질의가 tenant isolation, authz testing, owner mismatch, tenant mismatch처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Tenant Isolation / AuthZ Testing

> 한 줄 요약: tenant isolation 테스트는 "한 테넌트의 권한이 다른 테넌트로 새지 않는가"를 시스템적으로 검증하는 보안 테스트다.

**난이도: 🔴 Advanced**

관련 문서:

- [Permission Checks In REST Flows](./permission-checks-rest-flows-primer.md)
- [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
- [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
- [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
- [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
- [Authorization Caching / Staleness](./authorization-caching-staleness.md)
- [Authorization Graph Caching](./authorization-graph-caching.md)
- [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
- [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge)

retrieval-anchor-keywords: tenant isolation, authz testing, owner mismatch, tenant mismatch, controller test, service test, integration test, cross-tenant access, ownership, tenant boundary, negative test, 로그인 됐는데 왜 403, 같은 테넌트인데 남의 주문, 다른 테넌트 주문 차단, 처음 배우는 tenant test

---

## 핵심 개념

tenant isolation은 multi-tenant 시스템에서 가장 중요한 보안 경계 중 하나다.
authz testing은 이 경계가 코드, API, cache, BFF, admin tooling에서 모두 지켜지는지 검증한다.

핵심 목표:

- 다른 tenant의 데이터가 보이지 않는가
- 다른 tenant의 객체를 수정할 수 없는가
- delegated admin이 범위를 넘지 않는가
- cache가 tenant를 섞지 않는가

즉 테스트는 기능 확인이 아니라 경계 붕괴를 잡아내는 도구다.

초보자 기준으로는 먼저 둘을 나눠 기억하면 된다.

- `owner mismatch`: 같은 tenant 안이지만 `내 객체가 아닌데` 접근하는 경우
- `tenant mismatch`: 객체 자체가 아예 `다른 tenant 것`인 경우

`owner mismatch`는 object-level 권한 누락을 잡는 테스트고, `tenant mismatch`는 tenant boundary 붕괴를 잡는 테스트다.

---

## 30초 구분표: deny test 3종

한 번에 다 외우려 하지 말고, 아래 표로 "어느 층에서 무엇을 막는지"만 먼저 고정하면 된다.

| test 층 | 무엇을 빠르게 확인하나 | `owner mismatch` 예시 | `tenant mismatch` 예시 | 보통 보는 응답/예외 |
|---|---|---|---|---|
| controller | route에서 잘못된 id 요청이 바로 거부되는가 | `GET /orders/{id}`에서 같은 tenant 남의 주문 조회 | header의 active tenant는 A인데 주문은 tenant B 것 | `403` 또는 concealment 정책이면 `404` |
| service | 핵심 비즈니스 규칙이 HTTP 밖에서도 유지되는가 | `cancelOrder(actor, orderId)`에서 actor가 owner가 아님 | actor membership는 tenant A인데 order는 tenant B 소속 | `AccessDeniedException` 같은 도메인 예외 |
| integration | filter, repo, cache, 메시지 흐름까지 tenant 경계가 안 새는가 | list/search가 남의 row를 섞어 줌 | async export나 cache key가 tenant B 데이터를 포함 | API deny, 빈 목록, output 검증 실패 |

표를 짧게 읽는 법:

- controller test는 `입구에서 거부되는가`
- service test는 `핵심 규칙이 직접 호출에도 버티는가`
- integration test는 `저장소, cache, 비동기 경로까지 안 새는가`

## 자주 헷갈리는 지점

### 1. `owner mismatch`와 `tenant mismatch`는 대체재가 아니다

둘 다 deny여도 실패 이유가 다르다.

- `owner mismatch`: 같은 tenant 안에서 object rule이 틀림
- `tenant mismatch`: tenant selection, membership, query scope 자체가 틀림

예를 들어 tenant A의 support user가 tenant A 주문은 보되 자기 담당 고객 주문만 수정 가능하다면:

- 남의 담당 주문 수정 실패는 `owner mismatch`
- tenant B 주문 조회 시도 실패는 `tenant mismatch`

### 2. positive test보다 negative test가 중요하다

보안 테스트는 "되는가"보다 "안 되는가"를 먼저 본다.

- 다른 tenant resource 접근이 거부되는가
- 같은 tenant라도 남의 객체 수정이 거부되는가
- cross-tenant list가 비어 있는가
- delegated admin이 tenant scope를 넘지 않는가

### 3. same user, different tenant를 따로 만들어야 한다

같은 사용자라도 tenant가 바뀌면 권한이 달라질 수 있다.

- membership
- role
- delegated access
- policy version

---

## 실전 시나리오

### 시나리오 1: order API가 다른 tenant 데이터를 반환함

대응:

- tenant-specific test fixture를 만든다
- owner와 tenant 둘 다 검증한다
- list/detail/update/delete 모두 테스트한다

### 시나리오 2: export job이 cross-tenant 데이터를 포함함

대응:

- async job에도 tenant context를 전달한다
- output artifact를 검사한다
- queue message에 tenant id를 명시한다

### 시나리오 3: cache 때문에 이전 tenant 권한이 남음

대응:

- policy version을 바꾸는 negative test를 넣는다
- cache invalidation 후 거부되는지 본다
- delegated admin revoke나 tenant ownership move 뒤 graph invalidation 전후를 모두 검증한다
- stale decision을 metric으로 잡는다

relationship-based authz를 쓰면 cache test는 decision TTL 확인으로 끝나지 않는다.
tenant ownership edge나 delegated admin scope가 바뀐 뒤 PDP snapshot과 각 PEP cache가 함께 수렴하는지까지 봐야 한다.
이 운영 경계는 [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)과 [Authorization Graph Caching](./authorization-graph-caching.md) 문맥이다.

---

## 코드로 보기

### 1. controller: tenant mismatch deny

```java
@Test
void getOrder_rejectsTenantMismatch() throws Exception {
    mockMvc.perform(get("/orders/{id}", tenantBOrderId)
            .header("X-Tenant-Id", TENANT_A)
            .with(user(tenantAUser)))
        .andExpect(status().isForbidden());
}
```

### 2. service: owner mismatch deny

```java
@Test
void cancelOrder_rejectsOwnerMismatch() {
    assertThatThrownBy(() -> orderService.cancelOrder(tenantAUser, sameTenantOtherOwnerOrderId))
        .isInstanceOf(AccessDeniedException.class);
}
```

### 3. integration: tenant filter 누락 방지

```java
@Test
void listOrders_returnsOnlyActiveTenantRows() {
    List<Order> orders = orderQueryService.listOrders(tenantAUser, TENANT_A);

    assertThat(orders)
        .extracting(Order::tenantId)
        .containsOnly(TENANT_A);
    assertThat(orders)
        .extracting(Order::id)
        .doesNotContain(tenantBOrderId);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| unit-only authz test | 빠르다 | 경계 누락을 놓칠 수 있다 | 보조 수단 |
| integration authz test | 현실적이다 | 느리다 | 핵심 경계 |
| end-to-end tenant test | 가장 믿음직하다 | 유지비가 높다 | 중요한 경로 |
| negative-only suite | 보안 경계에 강하다 | 기능 coverage가 부족할 수 있다 | 보안 우선 |

판단 기준은 이렇다.

- tenant boundary가 중요한가
- cache와 async path가 포함되는가
- BFF나 admin tool이 섞이는가
- negative test를 자동화할 수 있는가

---

## 꼬리질문

> Q: tenant isolation 테스트에서 가장 중요한 것은 무엇인가요?
> 의도: 경계 붕괴를 검증하는 관점을 아는지 확인
> 핵심: 다른 tenant 데이터가 새지 않는지 보는 것이다.

> Q: negative test가 왜 중요한가요?
> 의도: 보안 테스트의 특성을 아는지 확인
> 핵심: 안 되는 요청이 실제로 거부되는지 확인해야 하기 때문이다.

> Q: cache와 async job도 왜 테스트해야 하나요?
> 의도: hidden path를 아는지 확인
> 핵심: 경계가 그 경로에서 깨질 수 있기 때문이다.

> Q: same user, different tenant를 왜 따로 보나요?
> 의도: 멤버십과 권한 분리 이해 확인
> 핵심: 같은 사람이라도 tenant마다 권한이 다를 수 있기 때문이다.

## 한 줄 정리

tenant isolation authz testing은 cross-tenant access가 코드와 비동기 경로에서 모두 차단되는지 검증하는 보안 테스트다.
