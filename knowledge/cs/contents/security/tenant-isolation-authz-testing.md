# Tenant Isolation / AuthZ Testing

> 한 줄 요약: tenant isolation 테스트는 "한 테넌트의 권한이 다른 테넌트로 새지 않는가"를 시스템적으로 검증하는 보안 테스트다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Authorization Graph Caching](./authorization-graph-caching.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)

retrieval-anchor-keywords: tenant isolation, authz testing, cross-tenant access, security test, integration test, RBAC, BOLA, ownership, tenant boundary, negative test, relationship-based authz, graph snapshot version, tenant-scoped graph invalidation, delegated admin scope

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

---

## 깊이 들어가기

### 1. tenant isolation이 깨지는 지점

- path parameter
- search/list filters
- cache key
- background job
- admin dashboard
- export/download endpoint

### 2. positive test보다 negative test가 중요하다

보안 테스트는 "되는가"보다 "안 되는가"를 봐야 한다.

- 다른 tenant resource 접근이 거부되는가
- cross-tenant list가 비어 있는가
- admin role이 tenant scope를 넘지 않는가

### 3. same user, different tenant를 테스트해야 한다

같은 사용자라도 tenant가 바뀌면 권한이 달라질 수 있다.

- membership
- role
- delegated access
- policy version

### 4. cache와 async job도 포함해야 한다

테스트가 API layer만 보면 부족하다.

- authorization cache
- search index
- async export
- webhook callback

relationship-based authz를 쓰면 cache test는 decision TTL 확인으로 끝나지 않는다.  
tenant ownership edge나 delegated admin scope가 바뀐 뒤 PDP snapshot과 각 PEP cache가 함께 수렴하는지까지 봐야 한다.  
이 운영 경계는 [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)과 [Authorization Graph Caching](./authorization-graph-caching.md) 문맥이다.

### 5. test data design이 중요하다

테스트는 실제로 구분되는 tenant와 resource를 만들어야 의미가 있다.

- tenant A/B
- user A/B
- owner mismatch
- admin mismatch

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

---

## 코드로 보기

### 1. tenant negative test

```java
@Test
void shouldRejectCrossTenantAccess() {
    assertThatThrownBy(() -> api.getOrder(tenantAUser, tenantBOrderId))
        .isInstanceOf(AccessDeniedException.class);
}
```

### 2. list scope test

```java
@Test
void shouldOnlyReturnOwnTenantResources() {
    List<Order> orders = api.listOrders(tenantAUser);
    assertThat(orders).allMatch(order -> order.tenantId().equals(TENANT_A));
}
```

### 3. async context test

```text
1. tenant context를 포함한 테스트 fixture를 만든다
2. cross-tenant 요청을 거부하는지 본다
3. cache와 background job도 포함한다
4. allow보다 deny를 우선 검증한다
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
