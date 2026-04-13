# Delegated Admin / Tenant RBAC

> 한 줄 요약: delegated admin은 "권한을 준다"가 아니라 "어떤 tenant와 어떤 범위까지 대신 관리할 수 있는가"를 명시하는 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [Authorization Caching / Staleness](./authorization-caching-staleness.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)

retrieval-anchor-keywords: delegated admin, tenant RBAC, scoped admin, tenant admin, sub-admin, cross-tenant, least privilege, admin delegation, role hierarchy, tenant isolation

---

## 핵심 개념

delegated admin은 상위 관리자가 다른 사용자나 팀에게 제한된 관리 권한을 위임하는 모델이다.  
multi-tenant SaaS에서는 tenant RBAC와 결합되면서 매우 복잡해진다.

핵심 질문:

- 누구의 tenant를 관리하는가
- 어떤 action만 가능한가
- 어떤 resource 범위까지 가능한가
- 위임이 언제 만료되는가
- 위임된 권한을 누가 회수하는가

즉 delegated admin은 단순 role 추가가 아니라, scope와 tenant boundary를 함께 정의하는 문제다.

---

## 깊이 들어가기

### 1. tenant RBAC의 기본

tenant별로 역할이 달라진다.

- 같은 `ADMIN`이라도 tenant A와 tenant B에서 범위가 다를 수 있다
- global admin과 tenant admin을 분리해야 한다
- support role은 읽기 전용일 수 있다

### 2. delegated admin은 상속만으로 해결되지 않는다

role hierarchy만 두면 문제가 생긴다.

- 너무 많은 예외 role이 생긴다
- 범위가 섞인다
- tenant 경계가 흐려진다

그래서 권한은 `role + scope + tenant`로 본다.

### 3. scoped admin은 최소 권한으로 만든다

예:

- billing admin
- user admin
- content moderator
- support read-only

중요한 건 role 이름보다 어떤 action과 resource에 적용되는가다.

### 4. delegation에는 만료와 감사가 필요하다

위임된 권한은 영구적이면 안 된다.

- 만료 시각
- 재승인 흐름
- 위임자와 수임자
- 변경 감사 로그

이게 없으면 비정상 권한이 오래 남는다.

### 5. tenant isolation이 기본이다

tenant admin이 다른 tenant에 닿으면 안 된다.

- list endpoint
- export endpoint
- impersonation 기능
- delegated support access

모두 tenant boundary를 명시적으로 확인해야 한다.

---

## 실전 시나리오

### 시나리오 1: 고객사 운영자가 일부 사용자만 관리해야 함

대응:

- tenant admin보다 더 좁은 scoped role을 만든다
- 특정 resource type만 허용한다
- 위임 만료를 둔다

### 시나리오 2: support가 고객을 대신해 설정을 바꿔야 함

대응:

- delegated access를 별도 권한으로 분리한다
- audit log에 actor와 acting-on-behalf-of를 둘 다 남긴다
- 민감한 작업은 step-up auth를 요구한다

### 시나리오 3: cross-tenant 접근이 발생함

대응:

- tenant id를 모든 정책에 포함한다
- IDOR/BOLA 검사를 더한다
- cache key에 tenant를 넣는다

---

## 코드로 보기

### 1. scoped admin 체크

```java
public void manageUser(UserPrincipal actor, Long tenantId, Long targetUserId) {
    if (!actor.hasRole("TENANT_ADMIN", tenantId)) {
        throw new AccessDeniedException("not tenant admin");
    }
    if (!actor.canManageResource("USER", tenantId)) {
        throw new AccessDeniedException("scope mismatch");
    }
}
```

### 2. delegation with expiry

```java
public boolean isDelegationValid(Delegation delegation) {
    return delegation.expiresAt().isAfter(Instant.now())
        && delegation.status() == DelegationStatus.ACTIVE;
}
```

### 3. audit-friendly delegation

```text
1. who granted the role
2. who received it
3. which tenant it applies to
4. what scope it covers
5. when it expires
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| flat admin role | 단순하다 | 범위가 너무 넓다 | 작은 조직 |
| tenant admin | 현실적이다 | cross-tenant 오염 위험 | multi-tenant SaaS |
| delegated scoped admin | 안전하다 | 설계가 복잡하다 | support/ops 중심 |
| role hierarchy only | 관리가 쉬워 보인다 | drift와 예외가 늘어난다 | 피해야 할 때가 많다 |

판단 기준은 이렇다.

- 위임 권한이 tenant를 넘나드는가
- support가 고객 대신 행동해야 하는가
- 만료와 회수가 필요한가
- 감사 추적이 필요한가

---

## 꼬리질문

> Q: delegated admin이 왜 복잡한가요?
> 의도: scope와 tenant 경계의 복잡성을 아는지 확인
> 핵심: 누가 누구의 어떤 tenant를 얼마나 관리하는지 모두 따져야 하기 때문이다.

> Q: tenant admin과 global admin은 왜 분리하나요?
> 의도: 권한 경계와 blast radius를 아는지 확인
> 핵심: 같은 관리 권한이라도 영향 범위가 다르기 때문이다.

> Q: delegation에 만료가 왜 필요한가요?
> 의도: 일시 위임과 영구 권한의 차이를 아는지 확인
> 핵심: 오래 남은 위임 권한은 위험하기 때문이다.

> Q: support impersonation은 어떻게 다뤄야 하나요?
> 의도: 대리 액션과 감사 추적을 아는지 확인
> 핵심: acting-on-behalf-of와 step-up auth가 필요하다.

## 한 줄 정리

delegated admin은 단순 role이 아니라 tenant와 scope를 함께 묶어 위임 범위를 정확히 제한하는 권한 설계다.
