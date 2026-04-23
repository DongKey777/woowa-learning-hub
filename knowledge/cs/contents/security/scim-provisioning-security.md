# SCIM Provisioning Security

> 한 줄 요약: SCIM은 계정과 그룹을 자동으로 동기화하는 표준이지만, provisioning 권한이 넓으면 대량 계정 생성과 권한 오염으로 바로 이어질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OIDC, ID Token, UserInfo](./oidc-id-token-userinfo-boundaries.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
> - [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Idor / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)

retrieval-anchor-keywords: SCIM, provisioning, deprovisioning, identity sync, groups, entitlements, lifecycle management, IdP, JIT provisioning, SCIM token, user lifecycle, deprovision session revoke

---

## 핵심 개념

SCIM(System for Cross-domain Identity Management)은 IdP와 SaaS 간 사용자/그룹/계정 상태를 동기화하는 표준이다.

주요 기능:

- user create
- user update
- user deactivate
- group membership sync
- entitlement mapping

위험은 provisioning이 자동화된 만큼 범위도 넓어질 수 있다는 점이다.

- 잘못된 그룹이 대량으로 들어온다
- deprovisioning이 늦으면 퇴사자가 남는다
- tenant mapping이 틀리면 cross-tenant 권한이 생긴다

즉 SCIM은 편의 기능이 아니라 identity lifecycle control plane이다.

---

## 깊이 들어가기

### 1. provisioning과 authentication은 다르다

SCIM은 로그인 프로토콜이 아니다.

- 누가 로그인할지는 OIDC/OAuth가 다룬다
- 누가 어떤 계정을 가지는지는 SCIM이 다룬다

이 경계를 섞으면 외부 IdP 정보만으로 내부 권한이 자동 부여된다.

### 2. deprovisioning이 가장 중요하다

계정 생성보다 계정 제거가 더 중요할 때가 많다.

- 퇴사자
- 계약 종료
- tenant 탈퇴
- group 제거

이 이벤트가 늦으면 기존 access가 계속 살아 있다.

### 3. group sync는 매우 조심해야 한다

그룹이 곧 권한이면 대사 문제가 생긴다.

- IdP 그룹과 내부 role이 1:1이 아닐 수 있다
- 그룹명만 보고 권한을 주면 위험하다
- 그룹 변화가 곧 정책 변화다

### 4. SCIM token도 secret이다

SCIM API는 보통 bearer token이나 client credential을 쓴다.

- 이 token이 유출되면 provisioning 자체가 악용된다
- 대량 계정 생성이나 삭제가 가능하다
- tenant 전체를 뒤흔들 수 있다

### 5. JIT와 SCIM을 구분해야 한다

- JIT provisioning: 로그인 시 계정을 즉석 생성
- SCIM provisioning: IdP가 미리 상태를 밀어 넣음

둘은 함께 쓰일 수 있지만, source of truth를 명확히 해야 한다.

---

## 실전 시나리오

### 시나리오 1: IdP에서 그룹이 잘못 동기화됨

대응:

- 내부 role 매핑을 allowlist로 제한한다
- 대량 변경에 대한 alert를 둔다
- provisioning diff를 감사 로그로 남긴다

### 시나리오 2: 퇴사자가 계정에서 안 빠짐

대응:

- deprovisioning SLA를 정한다
- session revocation과 refresh revoke를 같이 수행한다
- disabled user를 즉시 차단한다

### 시나리오 3: SCIM endpoint가 오남용됨

대응:

- SCIM token을 rotate한다
- rate limit과 audit log를 넣는다
- tenant별 provisioning scope를 분리한다

---

## 코드로 보기

### 1. SCIM create 개념

```java
public void provisionUser(ScimUser scimUser) {
    Tenant tenant = tenantRepository.findByExternalId(scimUser.tenantExternalId());
    userService.createOrUpdateMappedUser(tenant.id(), scimUser.externalId(), scimUser.email());
}
```

### 2. deprovisioning 개념

```java
public void deprovisionUser(String externalId) {
    UserAccount user = userRepository.findByExternalId(externalId);
    user.disable();
    sessionService.revokeAll(user.id());
}
```

### 3. group mapping 개념

```text
1. 외부 group을 내부 role에 직접 1:1로 매핑하지 않는다
2. allowlist mapping만 허용한다
3. 대량 변경은 alert를 발생시킨다
4. deprovisioning을 생성보다 더 강하게 관리한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| JIT provisioning | 단순하다 | 로그인 시점에 늦게 반영된다 | 소규모 |
| SCIM provisioning | lifecycle 자동화가 된다 | 범위 오염 위험이 크다 | SaaS/enterprise |
| manual admin | 통제가 쉽다 | 운영 부담이 크다 | 예외 처리 |

판단 기준은 이렇다.

- deprovisioning SLA가 필요한가
- group sync가 권한에 직접 연결되는가
- tenant별 scope를 분리할 수 있는가
- provisioning token을 안전하게 관리할 수 있는가

---

## 꼬리질문

> Q: SCIM은 무엇을 위한 표준인가요?
> 의도: 계정 lifecycle 관리 표준을 아는지 확인
> 핵심: 사용자, 그룹, provisioning/deprovisioning 동기화다.

> Q: deprovisioning이 왜 중요하나요?
> 의도: 퇴사자/계약 종료 계정 리스크를 아는지 확인
> 핵심: 접근 권한을 즉시 끊어야 하기 때문이다.

> Q: SCIM group sync가 왜 위험할 수 있나요?
> 의도: group-to-role 오염을 아는지 확인
> 핵심: 외부 그룹이 내부 권한으로 그대로 번역되면 안 되기 때문이다.

> Q: SCIM token도 secret인가요?
> 의도: provisioning control plane 보안 이해를 확인
> 핵심: 그렇다. 유출되면 대량 계정 변경이 가능하다.

## 한 줄 정리

SCIM은 계정 lifecycle 자동화 표준이지만, deprovisioning과 group-to-role 매핑을 엄격히 통제해야 안전하다.
