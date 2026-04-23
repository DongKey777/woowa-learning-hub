# Delivery Surface Policy for Support Access Alerts

> 한 줄 요약: support access alert는 security timeline을 canonical evidence로 고정한 뒤 email, in-app inbox, alternate verified channel을 mailbox trust와 actionability 기준으로 선택해야 하며, mailbox compromise가 의심되면 primary email은 즉시 인지 수단의 기본값에서 내려야 한다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **support AOBO / break-glass alert를 email, in-app inbox, security timeline, alternate verified channel 중 어디에 실을지 정하는 delivery surface policy**를 설명하는 focused deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
> - [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)
> - [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)
> - [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Email Magic-Link Threat Model](./email-magic-link-threat-model.md)
> - [Password Reset Threat Modeling](./password-reset-threat-modeling.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: delivery surface policy for support access alerts, support access delivery surface, support access alert channel policy, support access email vs inbox vs timeline, support access alternate verified channel, compromised mailbox support access alert, mailbox compromise notification routing, primary email suppression policy, verified alternate channel, verified secondary email, tenant security contact fallback, recovery center inbox, next login blocking banner, support access timeline canonical surface, support access immediate plus timeline, aobo delivery policy, break glass delivery policy, support alert mailbox trust, support alert in app inbox, support alert security timeline, support alert verified phone fallback, customer traceability vs immediate notification

## 이 문서 다음에 보면 좋은 문서

- privacy-safe copy spine과 channel wording은 [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)로 이어진다.
- affected user, tenant admin, security contact를 먼저 어떻게 고를지는 [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)에서 본다.
- `delivery_class`, `retention_class`, `access_group_id`를 canonical event에 어떻게 싣는지는 [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)로 이어진다.
- start/end lifecycle을 같은 audience와 surface에 어떻게 닫을지는 [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)에서 같이 보면 좋다.
- operator step-up, scope, TTL 제약은 [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)로 이어진다.
- mailbox compromise와 recovery channel 자체의 위협 모델은 [Email Magic-Link Threat Model](./email-magic-link-threat-model.md), [Password Reset Threat Modeling](./password-reset-threat-modeling.md)과 연결해서 보면 좋다.

---

## 핵심 개념

support access alert에서 먼저 고정해야 하는 것은 "어디로 보내나"가 아니라 **무엇이 canonical truth인가**다.

권장 순서는 세 단계다.

1. audience를 고른다
2. security timeline에 canonical event를 남긴다
3. 즉시 인지가 필요할 때만 email, in-app inbox, alternate verified channel을 추가한다

여기서 가장 흔한 실패는 mailbox가 이미 공격자 손에 있을 수 있는데도 primary email을 기본 channel로 계속 쓰는 것이다.

핵심 원칙:

- security timeline은 customer-visible support access의 canonical evidence다
- in-app inbox는 unread 관리와 timeline deep link용이다
- email은 out-of-band awareness용이지만 mailbox trust가 충분할 때만 쓴다
- alternate verified channel은 mailbox trust가 깨졌을 때 쓰는 예외 channel이지, 임시로 적어 넣은 새 연락처가 아니다

즉 delivery surface policy의 본질은 notification UX가 아니라 **trust가 깨진 channel을 자동으로 격하시킬 수 있는 보안 정책**이다.

---

## 깊이 들어가기

### 1. security timeline은 항상 canonical surface여야 한다

support AOBO와 break-glass는 channel마다 따로 진실이 생기면 안 된다.

- security timeline: start/end, reason category, scope, `case_ref`, status를 다시 확인하는 canonical evidence
- in-app inbox: unread state와 deep link를 제공하는 accelerator
- email: 현재 세션 밖에서도 눈에 띄게 만드는 out-of-band alert
- alternate verified channel: primary mailbox가 신뢰되지 않을 때의 fallback

좋은 설계:

- 모든 customer-visible support access lifecycle은 security timeline row를 가진다
- inbox/email/alternate channel은 같은 canonical event를 압축해서 보여 준다
- 종료 이벤트도 같은 `access_group_id`와 visible reference로 닫힌다

나쁜 설계:

- email만 보내고 timeline row는 없다
- inbox에는 `진행 중`인데 timeline에는 `종료됨`으로 어긋난다
- mailbox compromise 케이스에서도 primary email을 유일한 즉시 channel로 쓴다

### 2. surface 결정 전에 mailbox trust 상태를 먼저 분류해야 한다

support access event는 내용보다 channel 신뢰도가 먼저다.

| mailbox trust | 의미 | 허용 기본값 | 추가 규칙 |
|---|---|---|---|
| `trusted` | verified primary email이 정상이고 recent recovery/mailbox takeover 신호가 없다 | timeline + inbox/email policy 사용 가능 | email을 immediate surface로 사용할 수 있다 |
| `degraded` | recent email change, bounce, forwarding anomaly, recovery 진행 중, mailbox ownership 불확실성이 있다 | timeline 필수, inbox 우선, primary email 단독 사용 금지 | action-required alert는 alternate verified channel을 같이 본다 |
| `compromised` | mailbox takeover가 확인됐거나 그 mailbox를 기반으로 credential/recovery state가 흔들린다 | timeline 필수, primary email 억제, alternate verified channel 또는 next-login interrupt 우선 | primary email은 forensic copy 수준으로만 남기거나 완전히 생략한다 |

`degraded`와 `compromised`를 나누는 이유:

- `degraded`는 primary email이 틀렸을 가능성이 커졌다는 뜻이다
- `compromised`는 primary email이 공격자에게 signal을 보내는 channel일 수 있다는 뜻이다

즉 mailbox trust가 떨어지면 email은 "추가 channel"이 아니라 "금지 또는 격하 대상"이 된다.

### 3. event class별 default surface baseline을 따로 둬야 한다

| event class | trusted mailbox 기본값 | degraded mailbox 기본값 | compromised mailbox 기본값 | 이유 |
|---|---|---|---|---|
| read-only AOBO, user-scoped inspection | timeline, 필요 시 inbox | timeline, 필요 시 inbox | timeline | read-only는 기본적으로 evidence 중심이고, mailbox risk 때문에 email을 강제할 이유가 약하다 |
| write AOBO, user security/profile change | timeline + inbox + email | timeline + inbox + alternate verified channel | timeline + alternate verified channel + next-login blocking banner | 상태 변경이 일어났으므로 immediate notice가 필요하지만, mailbox 신뢰가 낮으면 email을 대체해야 한다 |
| user-scoped break-glass | timeline + inbox + email | timeline + inbox + alternate verified channel | timeline + alternate verified channel + next-login blocking banner | incident-grade event라 immediate notice가 필요하다 |
| tenant/workspace-scoped read-only AOBO | tenant admin/security timeline, 필요 시 admin inbox | tenant admin/security timeline, inbox 우선 | tenant admin/security timeline | shared surface inspection은 accountability audience가 먼저고, email은 필수는 아니다 |
| tenant/workspace-scoped write AOBO 또는 break-glass | admin/security timeline + inbox + email | admin/security timeline + inbox + alternate verified org channel | admin/security timeline + alternate verified org channel | tenant 책임면은 유지하되, 같은 mailbox domain이 의심되면 org alternate channel로 우회해야 한다 |

핵심:

- read-only AOBO는 `timeline-first`
- write AOBO와 break-glass는 `immediate + timeline`
- mailbox trust가 흔들리면 `email`보다 `alternate verified channel`과 `next-login interrupt`가 우선한다

### 4. email은 `always-on`이 아니라 trust-gated out-of-band channel이다

email이 맞는 경우:

- mailbox trust가 `trusted`다
- 사용자가 현재 세션 밖에 있어도 알아야 한다
- write AOBO나 break-glass처럼 later dispute보다 immediate awareness가 중요하다
- message가 privacy-safe copy로 충분히 압축 가능하다

email을 기본값에서 내려야 하는 경우:

- primary email이 최근 변경됐다
- email/recovery/MFA/password 자체가 이번 support access scope에 포함된다
- mailbox compromise가 의심된다
- tenant가 `security contact only` routing을 별도로 설정했다

특히 피해야 할 패턴:

- `MFA` reset이나 primary email change를 그 primary email 주소로만 알린다
- recovery 중 새로 입력된, 아직 검증되지 않은 이메일로 보안 alert를 보낸다
- security timeline 없이 email subject만으로 사건을 설명하려 한다

### 5. in-app inbox는 active session과 next-open session을 잇는 중간 surface다

in-app inbox가 맞는 경우:

- 사용자가 다시 앱에 들어올 가능성이 높다
- unread badge와 deep link가 중요하다
- security center / timeline 진입점이 필요하다
- 같은 access lifecycle의 `진행 중`, `종료됨`, `자동 만료됨`을 compact하게 보여 줘야 한다

in-app inbox만으로 부족한 경우:

- user security state가 바뀌었는데 사용자가 앱 밖에 있다
- break-glass처럼 off-session awareness가 필요하다
- current session이 이미 의심스럽거나 강제 로그아웃될 수 있다

이때는 ordinary inbox만 쓰지 말고:

- email이 신뢰되면 email 추가
- email이 불신이면 next-login blocking banner 또는 recovery center interrupt 추가

즉 inbox는 timeline의 대체재가 아니라, timeline으로 내려가기 전의 queue다.

### 6. alternate verified channel은 "편한 우회"가 아니라 미리 검증된 독립 channel이어야 한다

alternate verified channel로 인정하기 쉬운 예:

- 사고 이전에 검증된 secondary email, 그리고 primary mailbox와 다른 provider/domain
- 사고 이전에 등록된 verified phone/SMS/voice channel
- passkey/2FA-gated recovery center 또는 next-login blocking banner
- B2B tenant가 사전에 등록한 security contact alias, on-call number, verified security webhook endpoint

alternate verified channel로 인정하면 안 되는 예:

- support 티켓 중간에 새로 적어 넣은 미검증 메일 주소
- ordinary chat DM, unverified messenger
- same mailbox domain의 다른 alias인데 domain compromise 가능성을 무시한 경우
- tenant admin이 아닌 일반 distribution list 전체 broadcast

좋은 정책은 alternate channel에도 최소 기준을 둔다.

- incident 이전에 ownership이 검증돼 있어야 한다
- affected mailbox와 failure domain이 가능하면 분리돼 있어야 한다
- audit에 어느 alternate path를 탔는지 남아야 한다
- start/end closure를 같은 alternate channel family에 다시 닫을 수 있어야 한다

### 7. compromised mailbox 케이스는 "primary email 억제"가 먼저다

mailbox compromise가 의심되면 가장 먼저 해야 할 일은 더 많은 channel을 추가하는 것이 아니라, **위험한 channel을 줄이는 것**이다.

권장 decision ladder:

1. security timeline start/end event를 즉시 생성한다
2. primary email을 immediate notification 기본값에서 제거한다
3. next-login blocking banner 또는 recovery center interrupt를 활성화한다
4. pre-verified alternate channel이 있으면 그쪽으로 즉시 보낸다
5. B2B면 tenant admin/security contact의 alternate verified org channel을 추가한다
6. 종료/만료/강제 종료도 같은 reference와 audience에 닫는다

이 패턴이 중요한 이유:

- 공격자가 primary mailbox를 보고 있으면 alert 자체가 탐지를 도와주지 못할 수 있다
- 오히려 복구 절차를 방해하거나 social-engineering 타이밍을 맞춰 줄 수 있다
- 반대로 user가 다시 앱에 들어왔을 때 보이는 blocking banner는 공격자가 mailbox만 장악해서는 가릴 수 없다

### 8. B2B는 mailbox failure domain도 tenant 단위로 본다

B2B에서는 "user mailbox compromise"와 "tenant mail domain issue"를 구분해야 한다.

| 상황 | 권장 surface | 피해야 할 것 |
|---|---|---|
| 특정 end-user mailbox만 의심됨 | affected user timeline + alternate verified channel, tenant admin/security contact는 일반 policy대로 | 같은 user primary email에 write AOBO나 break-glass alert만 보내기 |
| tenant mail domain 전체가 불안정하거나 compromise 의심 | tenant admin/security timeline + alternate verified org channel + in-app/admin console banner | 같은 domain의 admin/security contact 메일에만 의존하기 |
| shared control plane write/break-glass | tenant admin/security contact immediate + timeline, direct impact user만 추가 | 모든 end-user broadcast를 기본값으로 삼기 |

즉 B2B fallback은 "누구에게 보내나"뿐 아니라 "같은 mail domain을 계속 믿어도 되나"를 함께 본다.

### 9. start와 end의 delivery family를 끊으면 trust가 무너진다

support access alert는 열렸다는 사실보다 닫혔다는 사실까지 전달돼야 한다.

좋은 규칙:

- start를 inbox로 보냈으면 end도 inbox에서 같은 thread/status로 닫는다
- start를 alternate verified channel로 보냈으면 end도 같은 verified family에 닫는다
- timeline은 언제나 lifecycle 전체를 유지한다

나쁜 규칙:

- start는 alternate SMS로 보냈는데 end는 primary email만 보낸다
- start는 admin inbox에 있는데 end는 timeline-only라 운영자가 closure를 놓친다
- break-glass 종료를 "ordinary admin activity" 피드에 묻는다

### 10. 정책 코드는 audience decision과 surface decision을 분리하는 편이 안전하다

```java
enum MailboxTrust {
    TRUSTED,
    DEGRADED,
    COMPROMISED
}

enum Surface {
    SECURITY_TIMELINE,
    IN_APP_INBOX,
    PRIMARY_EMAIL,
    ALT_VERIFIED_CHANNEL,
    NEXT_LOGIN_BLOCKING_BANNER
}

Set<Surface> decideSurfaces(SupportAccessEvent event, MailboxTrust mailboxTrust) {
    EnumSet<Surface> surfaces = EnumSet.of(Surface.SECURITY_TIMELINE);

    boolean immediate = event.isWriteLike() || event.isBreakGlass();
    if (event.shouldShowInbox()) {
        surfaces.add(Surface.IN_APP_INBOX);
    }

    if (!immediate) {
        return surfaces;
    }

    switch (mailboxTrust) {
        case TRUSTED -> surfaces.add(Surface.PRIMARY_EMAIL);
        case DEGRADED -> surfaces.add(Surface.ALT_VERIFIED_CHANNEL);
        case COMPROMISED -> {
            surfaces.add(Surface.ALT_VERIFIED_CHANNEL);
            surfaces.add(Surface.NEXT_LOGIN_BLOCKING_BANNER);
        }
    }

    if (event.touchesMailboxOrRecoveryState()) {
        surfaces.remove(Surface.PRIMARY_EMAIL);
        surfaces.add(Surface.ALT_VERIFIED_CHANNEL);
    }

    return surfaces;
}
```

포인트:

- audience routing은 별도 단계에서 먼저 결정한다
- surface decision은 mailbox trust와 event criticality를 본다
- `touchesMailboxOrRecoveryState()`는 primary email 억제 rule을 강제한다

---

## 실전 시나리오

### 시나리오 1: B2C에서 account recovery 도중 support가 `MFA`를 재설정했다

좋은 정책:

- security timeline에 `지원 변경` start/end를 남긴다
- primary mailbox가 recovery 대상이면 ordinary email은 보내지 않는다
- next-login blocking banner와 recovery center inbox를 띄운다
- 사고 이전에 검증된 secondary email 또는 verified phone이 있으면 그쪽으로 즉시 알린다

피해야 할 정책:

- `MFA` reset 사실을 장악 의심 mailbox 한 곳에만 보낸다
- timeline 없이 recovery SMS 한 번으로 끝낸다

### 시나리오 2: B2B에서 support가 billing export 설정을 read-only로 확인했다

좋은 정책:

- tenant admin/security timeline에 evidence를 남긴다
- admin inbox는 opt-in 또는 unread 필요가 있을 때만 쓴다
- read-only inspection이므로 email은 기본값이 아니다

피해야 할 정책:

- 모든 end-user에게 `관리자 접근` 메일을 보낸다
- tenant accountability event를 ordinary user activity feed에 섞는다

### 시나리오 3: B2B tenant outage 중 tenant-wide break-glass가 발급됐고 mail domain도 불안정하다

좋은 정책:

- tenant admin/security timeline에 start/end pair를 남긴다
- primary domain email 대신 사전 등록된 alternate security contact endpoint로 즉시 보낸다
- admin console 또는 security center banner를 함께 띄운다
- direct user state change가 생긴 계정만 별도 affected user alert를 받는다

피해야 할 정책:

- same domain admin/security contact 메일만 믿고 보낸다
- start만 alternate channel로 보내고 종료는 timeline-only로 남긴다

---

## 운영 체크리스트

```text
1. audience routing과 delivery surface decision이 분리돼 있는가
2. 모든 customer-visible support access lifecycle에 security timeline row가 있는가
3. mailbox trust가 degraded/compromised일 때 primary email 억제 규칙이 있는가
4. alternate verified channel이 incident 이전에 검증된 독립 channel인가
5. email/inbox/banner가 모두 같은 case_ref와 status를 가리키는가
6. write AOBO와 break-glass의 종료/만료/강제 종료가 같은 delivery family에 닫히는가
7. tenant mail domain compromise 시 org-level alternate channel fallback이 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| timeline-only 기본값 | canonical evidence가 단순하다 | immediate awareness가 약하다 | read-only AOBO, low-risk inspection |
| email + inbox + timeline 기본값 | 인지가 빠르다 | mailbox compromise에 취약하고 noise가 크다 | trusted mailbox의 write AOBO, break-glass |
| alternate verified channel + banner + timeline | compromise 상황에 강하다 | alternate channel enrollment와 운영 복잡도가 필요하다 | mailbox degraded/compromised, recovery-heavy 제품 |
| 모든 channel에 무조건 중복 발송 | 누락이 적어 보인다 | 공포, over-notification, 공격자 노출 위험이 커진다 | 가능하면 피한다 |

판단 기준:

- event가 read인지 write인지
- mailbox/recovery state 자체가 scope에 포함되는지
- mailbox trust가 trusted인지 degraded/compromised인지
- B2B에서 같은 mail domain failure를 함께 의심해야 하는지

---

## 꼬리질문

> Q: security timeline이 있는데 왜 inbox나 email이 더 필요한가요?
> 의도: canonical surface와 immediate surface를 구분하는지 확인
> 핵심: timeline은 증거고, inbox/email은 발견성을 높이는 delivery accelerator다.

> Q: compromised mailbox인데 email도 참고용으로 보내면 안 되나요?
> 의도: mailbox trust가 깨졌을 때의 보수적 원칙을 이해하는지 확인
> 핵심: immediate alert로는 부적절하다. 공격자에게 signal을 줄 수 있어 기본값은 억제다.

> Q: alternate verified channel은 왜 incident 중에 새로 받으면 안 되나요?
> 의도: fallback channel 검증 시점을 이해하는지 확인
> 핵심: 공격자나 confused deputy가 끼어들 수 있으므로, 사전 검증된 독립 channel이 아니면 fallback으로 신뢰할 수 없다.

> Q: B2B tenant-wide break-glass를 왜 모든 end-user에게 보내지 않나요?
> 의도: accountability audience와 blast-radius communication을 구분하는지 확인
> 핵심: 기본 audience는 tenant admin/security contact이고, end-user broadcast는 실제 행동 요구가 있을 때만 별도 incident comms로 다룬다.

## 한 줄 정리

Support access delivery surface policy의 핵심은 security timeline을 항상 남긴 뒤, trusted mailbox에서는 email/inbox를 쓰고, mailbox trust가 흔들리면 primary email을 격하시켜 alternate verified channel과 next-login interrupt로 옮기는 것이다.
