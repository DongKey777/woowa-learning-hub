---
schema_version: 3
title: Tenant Policy Schema for Privileged Support Alerts
concept_id: security/tenant-policy-schema-for-privileged-support-alerts
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- tenant policy schema for privileged support alerts
- privileged support alert policy
- tenant support alert policy
- support access tenant policy
aliases:
- tenant policy schema for privileged support alerts
- privileged support alert policy
- tenant support alert policy
- support access tenant policy
- support access routing config
- privileged support change alert
- security contact opt in
- tenant admin opt in
- admin notification policy
- security contact notification policy
- managed identity escalation
- managed identity support alert
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/support-access-alert-router-primer.md
- contents/security/audience-matrix-for-support-access-events.md
- contents/security/delivery-surface-policy-for-support-access-alerts.md
- contents/security/canonical-security-timeline-event-schema.md
- contents/security/aobo-start-end-event-contract.md
- contents/security/customer-facing-support-access-notifications.md
- contents/security/support-operator-acting-on-behalf-of-controls.md
- contents/security/delegated-admin-tenant-rbac.md
- contents/security/authz-kill-switch-break-glass-governance.md
- contents/security/audit-logging-auth-authz-traceability.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Tenant Policy Schema for Privileged Support Alerts 핵심 개념을 설명해줘
- tenant policy schema for privileged support alerts가 왜 필요한지 알려줘
- Tenant Policy Schema for Privileged Support Alerts 실무 설계 포인트는 뭐야?
- tenant policy schema for privileged support alerts에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Tenant Policy Schema for Privileged Support Alerts를 다루는 deep_dive 문서다. B2B support AOBO와 break-glass 알림은 audience matrix를 문장으로만 두면 drift가 생기므로, tenant admin / security contact opt-in, managed-identity escalation, compliance-sensitive event retention/export를 하나의 tenant policy schema로 고정해야 routing과 timeline evidence가 재현 가능해진다. 검색 질의가 tenant policy schema for privileged support alerts, privileged support alert policy, tenant support alert policy, support access tenant policy처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Tenant Policy Schema for Privileged Support Alerts

> 한 줄 요약: B2B support AOBO와 break-glass 알림은 audience matrix를 문장으로만 두면 drift가 생기므로, tenant admin / security contact opt-in, managed-identity escalation, compliance-sensitive event retention/export를 하나의 tenant policy schema로 고정해야 routing과 timeline evidence가 재현 가능해진다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **privileged support alert용 tenant-level policy knob, policy snapshot, managed-identity escalation contract**를 설명하는 focused deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Support Access Alert Router Primer](./support-access-alert-router-primer.md)
> - [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)
> - [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md)
> - [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)
> - [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)
> - [Security README: Service / Delegation Boundaries](./README.md#service-delegation-boundaries-deep-dive-catalog)

retrieval-anchor-keywords: tenant policy schema for privileged support alerts, privileged support alert policy, tenant support alert policy, support access tenant policy, support access routing config, privileged support change alert, security contact opt in, tenant admin opt in, admin notification policy, security contact notification policy, managed identity escalation, managed identity support alert, admin-managed identity escalation, compliance-sensitive support event, compliance-sensitive support access, support event retention export, support event policy snapshot, policy snapshot id, audience policy key, support access regulated alert, support access compliance routing, AOBO tenant alert policy, break glass tenant alert policy, tenant security contact verified channel, regulated support export alert

## 이 문서 다음에 보면 좋은 문서

- beginner가 `읽기/쓰기/누가 받나` 수준에서 막혔다면 먼저 [Support Access Alert Router Primer](./support-access-alert-router-primer.md)로 돌아가 `10초 라우터`의 `user-scoped routing`과 `tenant policy knob` 경계를 다시 고정한다.
- B2C/B2B별 audience routing matrix 자체는 [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)에서 먼저 본다.
- email, inbox, alternate verified channel 같은 delivery surface 선택은 [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md)로 이어진다.
- `policy_snapshot_id`, `audience_policy_key`, `retention_class`를 canonical event에 어떻게 싣는지는 [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)와 같이 보면 좋다.
- start/end lifecycle을 어떤 audience set으로 닫아야 하는지는 [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)에서 이어진다.
- AOBO grant, break-glass, delegated scope 자체의 제어면은 [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md), [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)로 이어진다.

---

## 핵심 개념

support access alert에서 자주 놓치는 점은 audience matrix와 tenant policy schema가 같은 것이 아니라는 점이다.

- audience matrix는 "원칙적으로 누가 받아야 하는가"를 설명한다
- tenant policy schema는 "이 tenant에서 어떤 opt-in과 escalation이 실제로 켜져 있는가"를 설명한다
- runtime evaluator는 event classification과 tenant policy를 합쳐 effective routing을 만든다
- canonical timeline event는 그 결과를 `policy_snapshot_id`와 함께 고정한다

이 층을 섞으면 다음 문제가 생긴다.

- 문서에는 "security contact는 privileged write만 받는다"고 적혀 있는데 실제 코드는 `sendSecurityContact=true` 같은 단일 boolean으로 흘러간다
- managed identity를 건드린 user-scoped write인데 tenant admin escalation이 빠진다
- compliance-sensitive event인데 retention/export 규칙이 ordinary support alert와 동일하게 저장된다
- start는 tenant admin에게 갔는데 end는 정책 drift 때문에 customer timeline만 닫히고 관리자 쪽 closure가 사라진다

즉 이 문서의 핵심은 새로운 audience를 만드는 것이 아니라, **이미 정의한 routing 원칙을 tenant-level policy object로 materialize해서 재현 가능하게 만드는 것**이다.

---

## 깊이 들어가기

### 1. tenant policy schema는 "누가 받아야 하나"보다 "무슨 조건에서 올라가나"를 답해야 한다

최소한 아래 질문이 schema에서 바로 읽혀야 한다.

| 질문 | field family | 왜 필요한가 |
|---|---|---|
| user-scoped read-only AOBO를 tenant admin도 받아야 하는가 | `audiences.tenant_admin.user_scoped_read` | B2B에서도 ordinary end-user ticket과 admin-managed identity를 구분해야 한다 |
| user-scoped write가 managed identity를 건드리면 어디까지 escalation되는가 | `managed_identity_escalation.*` | `MFA`, recovery, `SSO`, role binding은 ordinary profile edit와 의미가 다르다 |
| security contact는 어떤 privileged change부터 받는가 | `audiences.security_contact.*` | 모든 support event를 incident-grade처럼 보내면 noise가 커진다 |
| 어떤 event가 compliance-sensitive인가 | `compliance_sensitive_events.event_classes` | retention/export와 audit handoff가 ordinary alert와 달라진다 |
| runtime에서 어떤 policy snapshot을 썼는가 | `versioning.policy_snapshot_id` | 나중에 "왜 이 alert가 이 audience에 갔는가"를 재현하려면 필요하다 |

중요한 점은 template 이름이 아니라 **판단 축**을 schema에 넣는 것이다.

- tenancy baseline: `b2c`, `b2b_standard`, `b2b_regulated`
- scope axis: `user_scoped`, `tenant_scoped`
- access axis: `read_only`, `write`, `break_glass`
- escalation axis: `touches_managed_identity`, `is_compliance_sensitive`

이 축이 없으면 policy는 금방 `if` 문 뭉치로 무너진다.

### 2. admin/security-contact opt-in은 boolean보다 delivery mode enum이 안전하다

`notifyAdmins=true` 같은 boolean은 금방 한계에 부딪힌다.

- timeline만 남길지
- 즉시 + timeline으로 올릴지
- break-glass만 예외적으로 강하게 올릴지
- compliance-sensitive read는 받되 ordinary read는 받지 않을지

를 boolean 하나로 설명할 수 없기 때문이다.

권장 baseline enum:

- `off`
- `timeline_only`
- `immediate_plus_timeline`

권장 최소 필드 예시:

| audience | field | 권장 기본값 | 의미 |
|---|---|---|---|
| tenant admin | `user_scoped_read` | `off` 또는 `timeline_only` | ordinary ticket 처리 read를 tenant 책임면에 올릴지 |
| tenant admin | `user_scoped_write` | `immediate_plus_timeline` | 실제 user security/profile state 변경 시 관리자도 closure를 보게 할지 |
| tenant admin | `tenant_scoped_read` | `timeline_only` | shared config/export inspection을 관리자 timeline에 남길지 |
| tenant admin | `tenant_scoped_write` | `immediate_plus_timeline` | org policy/config/billing 변경을 change event로 다룰지 |
| security contact | `privileged_support_change` | `off` 또는 `immediate_plus_timeline` | managed identity/security control plane write를 보안 escalation에 올릴지 |
| security contact | `break_glass` | `immediate_plus_timeline` | emergency override는 opt-in이 아니라 baseline strong route로 둘지 |
| security contact | `compliance_sensitive_read` | `timeline_only` 또는 `immediate_plus_timeline` | export/legal-hold/regulated case read도 감사 대상에 올릴지 |

핵심은 "on/off"가 아니라 **어느 강도로, 어떤 event family에 대해, 어느 audience에 올리는가**를 field로 분해하는 것이다.

### 3. managed-identity escalation은 free-form note가 아니라 resource class taxonomy여야 한다

tenant 정책에서 가장 많이 빠지는 축이 `touches_managed_identity`다.

같은 user-scoped write라도:

- nickname 수정
- `MFA` factor reset
- recovery email 변경
- `SSO` binding 재연결
- admin role binding 수정

은 tenant 책임과 security meaning이 다르다.

권장 resource class:

| class | 포함 예 | 왜 escalation되는가 |
|---|---|---|
| `directory_identity` | corporate directory account, HR-linked identity, employee master record | tenant owner가 사용자 lifecycle을 설명해야 한다 |
| `mfa_or_recovery` | `MFA` reset, recovery channel change, passwordless recovery assist | credential assurance가 직접 흔들린다 |
| `federation_binding` | `SSO` mapping, IdP claim binding, tenant domain federation | shared trust boundary를 건드린다 |
| `role_or_admin_binding` | tenant role assignment, delegated admin binding | privilege와 tenant blast radius가 커진다 |
| `scim_identity` | `SCIM`-managed account, provisioning ownership override | identity source-of-truth와 drift/reconciliation에 영향이 간다 |

권장 평가 규칙:

1. event가 이 resource class 중 하나라도 건드리면 `touches_managed_identity=true`
2. user-scoped write라도 tenant admin escalation을 기본으로 올린다
3. security contact는 `privileged_support_change` opt-in 또는 compliance/break-glass rule에 따라 추가한다
4. ordinary profile/billing read-only case와 혼합하지 않도록 hidden evidence에 matched class를 남긴다

즉 managed identity는 "조금 더 민감한 user change"가 아니라, **tenant 책임면으로 올라가야 하는 escalation trigger**다.

### 4. compliance-sensitive support event는 copy가 아니라 retention/export까지 바꿔야 한다

regulated tenant에서 자주 틀리는 패턴은 compliance-sensitive support access를 ordinary support alert처럼 같은 retention과 같은 inbox row로 취급하는 것이다.

권장 event class 예시:

| event class | 예시 | 추가 정책 의무 |
|---|---|---|
| `break_glass` | incident recovery, emergency override | security contact strong route, long retention, export 가능 |
| `tenant_export_read` | export bundle inspection, regulated data package access | tenant admin/security accountability, audit handoff |
| `security_policy_write` | org `MFA`, session, allowlist, recovery policy 변경 | change-control 성격, longer timeline retention |
| `legal_hold_access` | legal/compliance case linked support access | case traceability, exportability, review path |

좋은 정책은 이 class가 붙으면 다음을 함께 바꾼다.

- `retention_class`
- `export_required`
- security contact delivery mode
- tenant admin immediate/timeline baseline
- customer/admin/security projection에서 보여 줄 `policy_snapshot_id`

권장 baseline:

- ordinary read-only AOBO: `timeline_standard_90d`
- managed identity write: `timeline_extended_180d`
- compliance-sensitive support event: `timeline_regulated_365d_exportable`

즉 compliance-sensitive는 "문구를 더 조심해서 쓴다"가 아니라, **storage and audit obligation 자체가 달라진다**는 뜻이다.

### 5. runtime evaluation은 baseline -> managed identity -> compliance override 순으로 누적하는 편이 안전하다

좋은 evaluator는 아래 순서를 가진다.

1. event를 `user_scoped/tenant_scoped`, `read/write/break_glass`, `reason_category`로 분류한다.
2. tenant baseline에서 tenant admin / security contact delivery mode를 읽는다.
3. `touches_managed_identity=true`면 managed-identity escalation rule을 적용한다.
4. `is_compliance_sensitive=true`면 retention/export/security-contact override를 적용한다.
5. audience별 delivery mode를 surface policy로 넘긴다.
6. canonical event에 `policy_snapshot_id`, `audience_policy_key`, `retention_class`를 stamp한다.

피해야 할 순서:

- email policy를 먼저 정하고 audience를 나중에 붙인다
- `break_glass`와 `privileged_support_change`를 같은 flag로 처리한다
- managed identity escalation을 template 단계에서만 분기한다
- canonical event에는 baseline만 저장하고 override reason은 버린다

즉 policy evaluation은 한 번의 `if`가 아니라 **누적 override를 가진 작은 policy engine**에 가깝다.

### 6. canonical timeline event에는 policy snapshot이 같이 찍혀야 한다

support alert policy는 런타임 순간의 tenant 설정을 읽고 끝내면 안 된다.
나중에 "왜 그때 security contact가 받았지?"를 설명하려면 canonical event에 정책 snapshot이 남아야 한다.

최소 hidden evidence field:

- `policy_snapshot_id`
- `policy_version`
- `audience_policy_key`
- `matched_managed_identity_classes`
- `compliance_event_class`
- `retention_class`
- `delivery_by_audience`

이 값이 중요한 이유:

- start 시점과 end 시점의 routing 근거를 재현할 수 있다
- tenant가 이후 설정을 바꿔도 과거 alert를 소급해서 다시 설명할 수 있다
- export나 audit handoff에서 "policy가 그때 그렇게 평가됐다"는 근거가 남는다
- audience mismatch가 생겼을 때 template bug인지 policy bug인지 분리하기 쉽다

closure rule도 여기서 중요하다.

- start를 받은 audience는 end도 기본적으로 같은 lifecycle에서 닫혀야 한다
- end event가 stronger route를 추가로 가질 수는 있어도, start audience를 조용히 삭제하면 안 된다
- compliance override가 붙은 terminal event는 `retention_class`와 export 의무를 그대로 이어 받아야 한다

### 7. schema 예시는 audience defaults, escalation rules, compliance overrides, versioning을 함께 담아야 한다

```json
{
  "schema_version": "2026-04-14",
  "policy_id": "sapol_01JRQ4R5M9Q4Y8WZK6",
  "tenant_id": "tnt_123",
  "mode": "b2b_enterprise",
  "audiences": {
    "tenant_admin": {
      "user_scoped_read": "timeline_only",
      "user_scoped_write": "immediate_plus_timeline",
      "tenant_scoped_read": "timeline_only",
      "tenant_scoped_write": "immediate_plus_timeline"
    },
    "security_contact": {
      "privileged_support_change": "immediate_plus_timeline",
      "break_glass": "immediate_plus_timeline",
      "compliance_sensitive_read": "timeline_only",
      "compliance_sensitive_write": "immediate_plus_timeline"
    }
  },
  "managed_identity_escalation": {
    "enabled": true,
    "resource_classes": [
      "directory_identity",
      "mfa_or_recovery",
      "federation_binding",
      "role_or_admin_binding",
      "scim_identity"
    ],
    "tenant_admin_delivery": "immediate_plus_timeline",
    "security_contact_delivery": "inherit_privileged_support_change"
  },
  "compliance_sensitive_events": {
    "enabled": true,
    "event_classes": [
      "break_glass",
      "tenant_export_read",
      "security_policy_write",
      "legal_hold_access"
    ],
    "retention_class": "timeline_regulated_365d_exportable",
    "export_required": true,
    "security_contact_delivery": "immediate_plus_timeline"
  },
  "verified_org_channels": {
    "security_contact_channel_policy": "verified_org_only",
    "allowed_route_types": [
      "security_alias",
      "on_call_phone",
      "security_webhook"
    ]
  },
  "versioning": {
    "policy_version": 12,
    "effective_from": "2026-04-14T00:00:00Z",
    "policy_snapshot_id": "polsnap_01JRQ4SE7X3N2H9C4B"
  }
}
```

좋은 구조의 특징:

- audience별 baseline이 먼저 있고
- managed identity와 compliance-sensitive override가 따로 보이며
- verified org channel 제약이 primary email policy와 분리돼 있고
- versioning 정보가 canonical event join key로 바로 재사용된다

### 8. 평가 코드는 "누가 받을까"와 "어떤 의무가 붙을까"를 같이 반환하는 편이 좋다

```java
enum DeliveryMode {
    OFF,
    TIMELINE_ONLY,
    IMMEDIATE_PLUS_TIMELINE
}

public record EffectiveSupportAlertPolicy(
        DeliveryMode tenantAdmin,
        DeliveryMode securityContact,
        String retentionClass,
        boolean exportRequired,
        String policySnapshotId
) {
}

EffectiveSupportAlertPolicy evaluate(
        SupportAccessEvent event,
        TenantSupportAlertPolicy policy
) {
    DeliveryMode tenantAdmin = policy.baseTenantAdminMode(event.scopeClass(), event.accessKind());
    DeliveryMode securityContact = policy.baseSecurityContactMode(event.accessKind());
    String retentionClass = "timeline_standard_90d";
    boolean exportRequired = false;

    if (event.touchesManagedIdentity(policy.managedIdentityClasses())) {
        tenantAdmin = DeliveryMode.IMMEDIATE_PLUS_TIMELINE;
        securityContact = max(
                securityContact,
                policy.managedIdentitySecurityMode()
        );
        retentionClass = "timeline_extended_180d";
    }

    if (event.isComplianceSensitive(policy.complianceEventClasses())) {
        securityContact = max(
                securityContact,
                policy.complianceSecurityMode()
        );
        retentionClass = "timeline_regulated_365d_exportable";
        exportRequired = true;
    }

    return new EffectiveSupportAlertPolicy(
            tenantAdmin,
            securityContact,
            retentionClass,
            exportRequired,
            policy.policySnapshotId()
    );
}
```

핵심 포인트:

- security contact delivery는 baseline보다 강해질 수는 있어도 보통 약해지지 않는다
- managed identity write는 retention도 ordinary read보다 길어질 수 있다
- compliance-sensitive event는 routing뿐 아니라 export flag를 바꾼다
- policy snapshot id는 evaluation 결과와 함께 반환돼야 canonical event에 그대로 찍을 수 있다

---

## 실전 시나리오

### 시나리오 1: B2B에서 support가 `SCIM`-managed 직원 계정의 `MFA`를 재설정했다

좋은 정책 평가:

- event는 `user_scoped_write`
- matched managed identity class는 `scim_identity`, `mfa_or_recovery`
- affected user는 즉시 + timeline
- tenant admin은 managed-identity escalation 때문에 즉시 + timeline
- security contact는 `privileged_support_change` opt-in이 켜진 tenant만 즉시 + timeline
- retention은 최소 `timeline_extended_180d`

피해야 할 평가:

- ordinary profile edit와 같은 routing으로 처리
- affected user만 받고 tenant admin escalation이 없음
- retention을 ordinary read-only AOBO 수준으로 둠

### 시나리오 2: regulated tenant에서 support가 legal-hold linked export bundle을 조회했다

좋은 정책 평가:

- event class는 `tenant_export_read` 또는 `legal_hold_access`
- end-user 전체 broadcast는 하지 않는다
- tenant admin은 timeline 이상으로 남기고, tenant policy에 따라 즉시 route를 추가한다
- security contact는 compliance-sensitive read policy에 따라 timeline 또는 immediate route를 받는다
- canonical event는 `timeline_regulated_365d_exportable`, `export_required=true`, `policy_snapshot_id`를 함께 가진다

피해야 할 평가:

- ordinary support read처럼 90일 retention만 남김
- security/contact routing 근거가 없어 나중에 audit에서 재현 불가

### 시나리오 3: tenant-wide `SSO` outage 중 break-glass가 열렸다

좋은 정책 평가:

- event는 `break_glass`이며 `federation_binding` 또는 shared tenant surface에 닿는다
- tenant admin과 security contact는 baseline strong route를 받는다
- affected user는 직접 상태 변화가 있는 경우에만 별도 안내한다
- start/end 모두 같은 lifecycle closure를 유지하고 compliance-sensitive retention을 가진다

피해야 할 평가:

- break-glass를 privileged write opt-in과 같은 flag에만 의존
- start는 강하게 보내고 end는 ordinary timeline-only로 약화

---

## 운영 체크리스트

```text
1. tenant admin / security contact opt-in을 boolean이 아니라 delivery mode enum으로 모델링하는가
2. managed identity escalation이 free-form string이 아니라 resource class taxonomy를 갖는가
3. compliance-sensitive event class가 retention/export 의무를 함께 바꾸는가
4. canonical event에 policy_snapshot_id, audience_policy_key, retention_class가 함께 찍히는가
5. start를 받은 audience가 end closure에서 조용히 빠지지 않는가
6. security contact route가 verified org channel policy와 분리돼 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 boolean (`notifyAdmins`, `notifySecurity`) | 구현이 단순하다 | event family, 강도, retention 차이를 설명하지 못한다 | 초기 프로토타입 정도 |
| template별 분기 하드코딩 | 빠르게 동작시킬 수 있다 | drift가 빠르고 policy snapshot이 남지 않는다 | 장기 운영에는 부적합 |
| tenant policy schema + override evaluation | 재현 가능하고 audit에 강하다 | schema 설계와 migration 비용이 든다 | enterprise / regulated / support-heavy B2B |

판단 기준은 이렇다.

- managed identity/security surface를 support가 자주 건드리는가
- security contact를 tenant별로 분리 운영하는가
- retention/export를 ordinary support alert와 다르게 가져가야 하는가
- start/end closure 근거를 나중에 설명해야 하는가

---

## 꼬리질문

> Q: security contact opt-in을 왜 boolean 하나로 두면 안 되나요?
> 의도: routing 강도와 event family를 분리하는지 확인
> 핵심: break-glass, privileged write, compliance-sensitive read의 강도가 모두 다르기 때문이다.

> Q: managed identity escalation이 ordinary user change와 왜 다른가요?
> 의도: tenant 책임면을 이해하는지 확인
> 핵심: `MFA`, `SSO`, role, `SCIM` identity는 개인 설정이 아니라 tenant trust boundary를 건드리기 때문이다.

> Q: compliance-sensitive support event는 왜 retention/export까지 같이 바꿔야 하나요?
> 의도: notification과 audit obligation을 분리하는지 확인
> 핵심: regulated support access는 copy가 아니라 evidence lifecycle 자체가 ordinary alert와 다르기 때문이다.

> Q: policy snapshot id를 왜 canonical event에 남겨야 하나요?
> 의도: 사후 재현 가능성을 이해하는지 확인
> 핵심: 나중에 tenant가 설정을 바꿔도 당시 routing 근거를 다시 설명해야 하기 때문이다.

## 한 줄 정리

Privileged support alert의 tenant policy schema는 audience matrix를 코드와 evidence로 고정하는 장치이며, tenant admin/security-contact opt-in, managed-identity escalation, compliance-sensitive retention/export, policy snapshot을 한 객체로 묶어야 AOBO와 break-glass routing이 drift 없이 재현된다.
