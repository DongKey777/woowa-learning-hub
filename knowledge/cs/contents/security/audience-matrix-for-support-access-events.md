# Audience Matrix for Support Access Events

> 한 줄 요약: support AOBO와 break-glass 알림은 "이벤트가 있었는가"보다 "그 blast radius를 누가 설명하고 책임져야 하는가"를 기준으로 affected user, tenant admin, security contact에 다르게 라우팅해야 하며, B2C는 개인 traceability 중심, B2B는 tenant accountability escalation이 추가된다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **support access event의 audience routing matrix를 B2C/B2B tenancy, scope, severity별로 정의하는 focused deep dive**다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Support Access Alert Router Primer](./support-access-alert-router-primer.md)
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
> - [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)
> - [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)
> - [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md)
> - [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md)
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: audience matrix for support access events, support access audience matrix, support audience routing, AOBO audience routing, break glass audience routing, affected user notification, tenant admin notification, security contact notification, b2b support access alert, b2c support access alert, privileged support change alert, emergency access routing, support access escalation matrix, tenant security contact escalation, tenant policy schema for privileged support alerts, privileged support alert policy, managed identity escalation, security contact opt in, compliance-sensitive support event, support access delivery surface, support access alternate verified channel, compromised mailbox support access alert, tenant security contact fallback, canonical security timeline event schema, aobo start end event contract, support access end audience closure, access group id, case ref, support timeline schema, browser session coherence, session boundary bridge, ordinary session inventory vs support timeline

## 이 문서 다음에 보면 좋은 문서

- support access 알림을 처음 보는 단계라면 [Support Access Alert Router Primer](./support-access-alert-router-primer.md)의 `10초 라우터`에서 `read / write / break-glass / tenant / mailbox trust` 중 한 줄을 먼저 고르고 다시 내려오면 된다.

- customer-facing copy와 security timeline surface 자체는 [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)로 이어진다.
- `case_ref`, `access_group_id`, start/end pair를 어떤 shared schema로 고정할지는 [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)로 이어진다.
- start를 받은 audience가 같은 lifecycle의 end도 어떻게 닫아 받아야 하는지는 [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)에서 같이 보면 좋다.
- 이 matrix를 tenant-level opt-in, managed-identity escalation, compliance-sensitive override로 어떻게 materialize할지는 [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md)로 이어진다.
- audience를 정한 뒤 email, inbox, timeline, alternate verified channel 중 무엇을 쓸지는 [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md)에서 이어서 본다.
- operator identity, subject identity, step-up, TTL 제어는 [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)로 이어진다.
- break-glass actor/scope/duration 통제와 cleanup은 [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md), [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)로 이어진다.
- B2B에서 tenant owner 역할 자체를 어떻게 모델링할지는 [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)와 같이 보면 좋다.
- ordinary session inventory와 support access timeline을 같은 security center에서 어떻게 분리할지는 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)으로 되돌아가서 같이 보면 좋다.

---

## 핵심 개념

support access event에는 보통 세 audience가 엮인다.

- affected user: 직접 조회되거나 변경된 계정의 주체
- tenant admin: workspace, billing, directory, org security policy를 설명해야 하는 운영 책임자
- security contact: incident-grade override나 privileged access를 받아야 하는 보안 escalation 창구

여기서 중요한 점은 **event taxonomy와 audience policy를 분리하는 것**이다.

- event taxonomy: `aobo_read`, `aobo_write`, `break_glass_started`, `break_glass_ended`
- audience policy: affected user, tenant admin, security contact 중 누가 어떤 surface에서 받아야 하는가

같은 `aobo_write`라도 B2C 개인 계정이면 affected user만 받으면 충분할 수 있고, B2B에서 `SSO`/`MFA`/role에 닿는 작업이면 tenant admin과 security contact까지 올라가야 할 수 있다.

---

## 깊이 들어가기

### 1. audience routing은 "누가 touched 되었는가"보다 "누가 설명 책임을 지는가"를 기준으로 정한다

다음 네 입력이 routing 기준이다.

- tenancy: `B2C`인지 `B2B`인지
- mode: read-only AOBO인지, write AOBO인지, break-glass인지
- scope owner: 개인 계정인지, admin-managed identity/security surface인지, tenant-wide shared surface인지
- reason family: 고객 요청 처리인지, 서비스 복구인지, 보안 대응인지

잘못된 패턴:

- 모든 support access를 affected user에게만 보낸다
- tenant-wide break-glass를 모든 end-user에게 broadcast한다
- security contact를 모든 read-only AOBO에 참조한다

좋은 기준은 이렇다.

- 직접 계정/credential/security state가 바뀌면 affected user가 본다
- workspace나 shared control plane에 닿으면 tenant admin이 본다
- incident-grade, privileged write, security/compliance surface면 security contact가 본다

### 2. surface 강도도 matrix에 포함해야 한다

같은 audience라도 같은 강도로 보내면 안 된다.

- `타임라인`: security center / support access timeline에 기록만 남긴다
- `즉시 + 타임라인`: email/inbox 등 즉시 인지 수단과 timeline을 함께 쓴다
- `직접 영향 시만`: 전체 audience broadcast는 하지 않고, 실제로 바뀐 사람만 받게 한다
- `정책 opt-in`: tenant 설정, 요금제, 규제 프로필에 따라 켜진 경우에만 보낸다

원칙:

- break-glass와 write AOBO는 대체로 `즉시 + 타임라인`
- read-only AOBO는 기본값이 `타임라인`
- 시작 알림을 즉시 보냈다면 종료/cleanup도 같은 audience에 닫아 줘야 한다

### 3. B2C matrix는 affected user 중심으로 단순해야 한다

B2C에서는 tenant admin과 security contact를 억지로 만들지 않는 편이 낫다.

| 케이스 | affected user | tenant admin | security contact | 이유 |
|---|---|---|---|---|
| user-requested read-only AOBO, account-scoped inspection | 타임라인 | 기본값 없음 | 기본값 없음 | 설명 책임이 개인 계정 소유자에게만 있다 |
| write AOBO, account security/profile change (`MFA` reset, email/phone change, recovery) | 즉시 + 타임라인 | 기본값 없음 | 기본값 없음 | 직접 security state가 바뀌므로 ordinary support note보다 강하게 보여야 한다 |
| account-scoped break-glass, recovery/service/security response | 즉시 + 타임라인 | 기본값 없음 | 기본값 없음 | 긴급 access 시작과 종료를 둘 다 증명해야 한다 |

보완 규칙:

- primary email이 공격자에게 장악됐을 수 있으면 ordinary email 대신 verified alternate channel, next-login blocking banner, recovery center inbox를 우선한다.
- B2C에서 break-glass라고 해서 모든 과거 기기나 모든 주소로 동시에 보내는 것은 오탐과 혼란을 키울 수 있다.

### 4. B2B matrix는 "누가 tenant를 대신 설명할 것인가"를 추가로 본다

B2B에서는 affected user만 알면 끝나지 않는다.
tenant admin과 security contact는 서로 다른 책임을 가진다.

| 케이스 | affected user | tenant admin | security contact | 이유 |
|---|---|---|---|---|
| user-scoped read-only AOBO, end-user ticket 처리 | 타임라인 | 정책 opt-in 또는 admin-managed surface일 때 타임라인 | 기본값 없음 | 개인 이슈지만 directory/security 관리형 계정이면 tenant owner가 나중에 설명해야 할 수 있다 |
| user-scoped write AOBO, managed identity/security state 변경 | 즉시 + 타임라인 | 즉시 + 타임라인 | privileged support change alert를 켠 tenant만 즉시 + 타임라인 | user와 tenant policy owner가 모두 영향을 받는다 |
| tenant/workspace-scoped read-only AOBO, shared config/billing/export inspection | 직접 영향 시만 | 타임라인 | security/compliance export면 정책 opt-in | shared surface는 tenant owner가 accountable이고, 일반 end-user 전체 공지는 과하다 |
| tenant/workspace-scoped write AOBO, org policy/config/billing change | 직접 영향 시만 | 즉시 + 타임라인 | security/billing/compliance surface면 즉시 + 타임라인 | shared control plane 변경은 tenant 차원의 change로 다뤄야 한다 |
| user-scoped break-glass, suspected compromise or urgent recovery | 즉시 + 타임라인 | 즉시 + 타임라인 | 즉시 + 타임라인 | narrow scope라도 incident-grade event이므로 보안 escalation이 필요하다 |
| tenant-wide or cross-user break-glass | 직접 영향 시만 | 즉시 + 타임라인 | 즉시 + 타임라인 | blast radius owner는 tenant admin/security contact이며, 모든 end-user broadcast는 기본값이 아니다 |

핵심 해석:

- tenant admin은 **운영 책임자**다. admin-managed identity, shared config, billing, tenant-wide recovery를 본다.
- security contact는 **incident/security escalation 창구**다. break-glass, security-response AOBO, compliance-grade privileged write를 본다.
- affected user는 **직접 영향 원칙**으로 본다. tenant-wide break-glass라고 해서 모든 end-user가 기본 audience가 되지는 않는다.

### 5. tenant admin과 security contact를 같은 메일링 리스트로 취급하면 안 된다

둘을 구분해야 하는 이유:

- tenant admin은 daily 운영과 사용자 설명 책임이 있다
- security contact는 incident, audit, compliance escalation 책임이 있다
- 같은 사람일 수도 있지만, policy 모델은 분리해 두는 편이 안전하다

따라서 권장 기본값:

- read-only AOBO: security contact 제외
- write AOBO: tenant-managed security surface일 때만 security contact opt-in
- break-glass: security contact 포함을 기본값으로

### 6. 시작 알림과 종료 알림의 audience를 끊어 먹지 말아야 한다

support access에서 흔한 문제는 `시작됨`만 보내고 `종료됨`은 남기지 않는 것이다.

특히 아래는 start/end pair가 중요하다.

- write AOBO
- user-scoped break-glass
- tenant-wide break-glass

좋은 contract:

- 같은 `grant_id` 또는 `case_ref`를 start/end event에 재사용
- start를 받은 audience는 end도 같은 surface에서 받는다
- read-only AOBO라도 장시간 열린 경우 timeline에서 `진행 중 -> 종료됨` 상태가 닫혀야 한다

### 7. "모든 affected user에게 다 알림"은 B2B에서 자주 틀린 기본값이다

tenant-wide break-glass나 shared config inspection은 영향을 받는 end-user 수가 많을 수 있다.
하지만 그 사실만으로 모든 user를 직접 audience에 넣으면:

- noise가 너무 커지고
- 실제 의사결정권이 없는 사람에게 incident detail이 뿌려지고
- security contact와 tenant admin이 받아야 할 책임형 알림이 end-user flood에 묻힌다

그래서 B2B 기본값은 이렇다.

- shared surface: tenant admin / security contact 중심
- direct account/security state change: 해당 affected user 추가
- all-user broadcast: 실제 사용자 행동 요구가 있을 때만 별도 incident comms 채널로

---

## 실전 시나리오

### 시나리오 1: B2C에서 support가 결제 문제 재현을 위해 account 설정을 read-only로 확인했다

좋은 라우팅:

- affected user security timeline에 `지원 조회` event 기록
- tenant admin/security contact는 없음
- ordinary login alert는 사용하지 않음

피해야 할 라우팅:

- `새 로그인 감지` 템플릿 발송
- support 조회를 `긴급 접근`처럼 과장

### 시나리오 2: B2B에서 support가 사원 계정의 `MFA`를 재설정했다

좋은 라우팅:

- affected user에게 즉시 알림 + timeline
- tenant admin에게 즉시 알림 + timeline
- tenant가 privileged support change alert를 켰다면 security contact에도 즉시 알림

피해야 할 라우팅:

- affected user에게만 보내고 tenant admin은 모르게 둠
- read-only AOBO와 같은 저강도 copy 사용

### 시나리오 3: B2B tenant outage 중 workspace 전체에 break-glass가 발급됐다

좋은 라우팅:

- tenant admin과 security contact에 `시작` / `종료` 쌍을 즉시 발송
- affected user는 실제 계정 상태가 바뀐 사람만 별도 안내
- security timeline에서는 같은 `grant_id`로 start/end를 연결

피해야 할 라우팅:

- 모든 end-user에게 tenant-wide emergency access를 일괄 발송
- start event만 보내고 cleanup 완료를 닫지 않음

---

## 코드로 보기

### 1. audience routing decision 예시

```java
enum Delivery {
    NONE,
    TIMELINE,
    IMMEDIATE
}

public record AudienceRoute(
        Delivery affectedUser,
        Delivery tenantAdmin,
        Delivery securityContact,
        boolean sendEndEvent
) {
}

public AudienceRoute route(SupportAccessEvent event, TenantPolicy policy) {
    boolean b2b = event.tenantId() != null;
    boolean writeLike = event.type() == EventType.AOBO_WRITE || event.type() == EventType.BREAK_GLASS;
    boolean touchesManagedIdentity = event.scope().touchesManagedIdentity();
    boolean touchesSharedTenantSurface = event.scope().isTenantWide() || event.scope().touchesSharedPolicy();
    boolean securityEscalation = event.type() == EventType.BREAK_GLASS
            || event.reasonFamily() == ReasonFamily.SECURITY_RESPONSE;

    Delivery affectedUser = writeLike || event.scope().touchesUserSecurityState()
            ? Delivery.IMMEDIATE
            : Delivery.TIMELINE;

    Delivery tenantAdmin = !b2b
            ? Delivery.NONE
            : (touchesManagedIdentity || touchesSharedTenantSurface)
            ? Delivery.IMMEDIATE
            : policy.notifyAdminsOnUserScopedRead() ? Delivery.TIMELINE : Delivery.NONE;

    Delivery securityContact = !b2b
            ? Delivery.NONE
            : (securityEscalation
            || (writeLike && event.scope().touchesSecurityControlPlane() && policy.notifySecurityContacts()))
            ? Delivery.IMMEDIATE
            : Delivery.NONE;

    return new AudienceRoute(affectedUser, tenantAdmin, securityContact, writeLike || securityEscalation);
}
```

### 2. 운영 체크리스트

```text
1. event taxonomy(aobo_read/write, break_glass)와 audience matrix가 분리돼 있는가
2. B2B에서 user-scoped와 tenant-scoped event를 다른 audience로 라우팅하는가
3. security contact가 모든 read-only AOBO를 받지 않도록 제한돼 있는가
4. write AOBO와 break-glass는 시작/종료가 같은 audience에 닫히는가
5. compromised mailbox 같은 경우 alternate verified channel 규칙이 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| affected user만 항상 알림 | 단순하다 | B2B tenant accountability가 사라진다 | B2C 중심 서비스 |
| 모든 end-user와 admin에 전부 알림 | 설명 누락이 적어 보인다 | noise, 공포, 정보 과노출이 크다 | 가능하면 피한다 |
| affected user + tenant admin 조건부 matrix | 책임과 noise 균형이 맞다 | tenant metadata와 policy 설정이 필요하다 | 일반적인 B2B SaaS |
| security contact 별도 escalation | incident 대응이 선명하다 | 연락처 hygiene와 opt-in 모델이 필요하다 | regulated, enterprise, support-heavy 환경 |

판단 기준은 이렇다.

- direct account/security change인지, shared tenant surface change인지
- tenant가 admin-managed identity를 쓰는지
- incident-grade break-glass인지, 일반 support AOBO인지
- start/end pair를 어떤 audience에게 닫아 줘야 dispute가 줄어드는지

---

## 꼬리질문

> Q: B2B tenant-wide break-glass를 왜 모든 end-user에게 기본 발송하지 않나요?
> 의도: direct impact와 accountability audience를 구분하는지 확인
> 핵심: 책임 있는 audience는 tenant admin/security contact이고, end-user broadcast는 실제 사용자 행동 요구가 있을 때만 별도 comms로 다루는 편이 낫다.

> Q: security contact는 언제 AOBO도 받아야 하나요?
> 의도: break-glass와 privileged support write를 구분하는지 확인
> 핵심: 모든 AOBO가 아니라, security/compliance surface를 건드리는 privileged write나 security-response case에서만 받는 편이 좋다.

> Q: 왜 start와 end를 같은 audience에 보내야 하나요?
> 의도: closure 증명의 중요성을 이해하는지 확인
> 핵심: support access는 열렸다는 사실보다 닫혔다는 사실까지 보여 줘야 trust와 audit가 완성되기 때문이다.

> Q: B2C에서도 tenant admin/security contact 개념을 억지로 넣어야 하나요?
> 의도: tenancy model 차이를 이해하는지 확인
> 핵심: 아니다. B2C는 affected user 중심으로 단순하게 유지하는 편이 오히려 정확하다.

## 한 줄 정리

Support access audience matrix의 핵심은 AOBO와 break-glass를 같은 copy로 보내는 것이 아니라, tenancy, scope, severity를 기준으로 affected user, tenant admin, security contact의 책임면을 분리해 B2C는 간결하게, B2B는 accountable하게 라우팅하는 것이다.
