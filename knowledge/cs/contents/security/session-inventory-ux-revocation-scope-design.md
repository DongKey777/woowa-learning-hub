# Session Inventory UX / Revocation Scope Design

> 한 줄 요약: 세션 관리 화면은 "현재 세션", "현재 기기", "refresh family", "모든 기기" 같은 revoke 범위를 사용자와 운영자가 같은 의미로 이해하게 만들어야 하며, support AOBO와 break-glass도 ordinary session과 섞이지 않게 보여 줘야 한다.
>
> 문서 역할: 이 문서는 security 카테고리 안에서 **세션 목록 UX, revocation scope naming, operator session projection**을 설명하는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Logout Scope Primer](./logout-scope-primer.md)
> - [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
> - [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
> - [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
> - [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
> - [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
> - [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
> - [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
> - [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: session inventory ux, revocation scope design, logout all devices ux, current session vs current device, session management screen, revoke scope naming, session inventory copy, device session list, refresh family revoke, logout propagation copy, session list semantics, operator session inventory, support access timeline, support access notification, acting on behalf session view, break glass session panel, revoke requested, propagation in progress, fully blocked confirmed, revocation status payload

## 이 문서 다음에 보면 좋은 문서

- revoke 대상 모델 자체는 [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)로 이어진다.
- `현재 세션`, `이 기기`, `모든 기기`, `refresh family` 용어를 초보자 눈높이에서 먼저 자르고 싶으면 [Logout Scope Primer](./logout-scope-primer.md)를 먼저 붙이고 내려오면 된다.
- 실제 분산 무효화 메커니즘은 [Session Revocation at Scale](./session-revocation-at-scale.md)로 이어진다.
- revoke 이후 `requested`, `in_progress`, `fully_blocked_confirmed` status payload 의미는 [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)에서 따로 고정한다.
- "로그아웃됨" 표시가 언제 안전한지의 tail 문제는 [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)과 같이 봐야 한다.

---

## 핵심 개념

세션 관리 화면에서 가장 위험한 실수는 UI row와 실제 revoke 단위를 다르게 설계하는 것이다.

예를 들어:

- 화면에는 "이 기기" 하나만 보이는데 실제로는 browser session이 여러 개다
- "모든 세션 종료"라고 쓰지만 실제로는 refresh family만 끊는다
- "로그아웃 완료"라고 쓰지만 access token tail이 아직 남아 있다

즉 session inventory UX의 핵심은 보기 좋은 목록이 아니라, 사용자가 누른 범위와 시스템이 실제로 끊는 범위를 일치시키는 것이다.

---

## 깊이 들어가기

### 1. inventory row는 실제 제어 단위와 1:1에 가깝게 맞춰야 한다

세션 목록 row가 무엇을 뜻하는지 먼저 정해야 한다.

- browser session 1개
- app install 1개
- device 아래의 여러 session 묶음
- refresh family 1개

이 매핑이 흐리면 "이 세션 종료"가 예상과 다르게 동작한다.

### 2. scope 이름은 절단면을 설명해야 한다

권장 질문:

- 현재 탭만 끊는가
- 현재 브라우저 세션 전체를 끊는가
- 현재 기기에서 발급된 session family를 끊는가
- 계정의 모든 기기를 끊는가

UI 문구도 이에 맞춰야 한다.

- `현재 세션 종료`
- `이 기기의 모든 세션 종료`
- `이 기기의 로그인 다시 요구`
- `모든 기기에서 로그아웃`

### 3. "현재 세션"과 "현재 기기"를 섞으면 안 된다

같은 노트북에서도 실제 단위는 다를 수 있다.

- 브라우저 프로필이 다름
- 앱과 웹이 같이 존재함
- 같은 기기에서 step-up grant만 별도로 존재함

그래서 device label만으로는 충분하지 않고, 최근 activity와 client type을 함께 보여 주는 편이 좋다.

### 4. row metadata는 사용자가 범위를 추론할 수 있게 도와야 한다

유용한 정보:

- last active
- auth time
- client type
- location/region
- device nickname
- current session 여부

반대로 너무 공격적인 device fingerprint 세부값을 그대로 노출하면 privacy와 support 비용이 커질 수 있다.

### 5. revoke 진행 상태를 숨기면 support 티켓이 늘어난다

세션이 분산 환경에 퍼져 있다면, 버튼 클릭 직후 곧바로 "완료"라고 쓰기보다 상태를 구분하는 편이 낫다.

- revoke requested
- propagation in progress
- fully blocked confirmed

특히 "모든 기기 로그아웃"은 access token TTL과 region fan-out 때문에 tail이 남을 수 있으므로, 고위험 작업은 즉시 막고 일반 route는 순차 정리된다는 copy가 필요할 수 있다.

### 6. quarantine와 step-up 상태도 inventory에 반영돼야 한다

모든 상태가 active/revoked 둘뿐이라고 가정하면 설명이 무너진다.

- quarantined
- read-only restricted
- step-up required
- elevated grant active

이 상태가 UI에 드러나야 사용자는 왜 일부 기능만 막혔는지 이해할 수 있다.

### 7. operator tooling에서는 self-service보다 더 좁은 기본값이 필요하다

사용자 self-service 화면보다 operator console이 더 위험한 이유는 대리 권한과 광범위 revoke 버튼이 같이 있기 때문이다.

그래서 운영 도구는 보통 아래 기본값을 갖는 편이 안전하다.

- `현재 세션 종료`를 기본 선택으로 둔다
- `이 기기의 모든 세션 종료`는 impact preview 뒤에 노출한다
- `모든 기기 로그아웃`은 strong auth와 reason code를 요구한다
- AOBO와 break-glass에서는 같은 label이라도 별도 approval 규칙을 둔다

즉 같은 session graph를 보더라도 operator tool은 사용자 화면보다 더 강한 friction과 preview가 필요하다.

### 8. acting-on-behalf-of와 break-glass는 ordinary device row와 섞이면 안 된다

support operator가 고객 대신 작업하거나 break-glass grant가 활성화된 경우, 이것을 ordinary session row처럼 보여 주면 audit와 고객 설명이 모두 흐려진다.

구분이 필요한 정보:

- actor type: self / support / break-glass
- operator id
- subject user or tenant
- ticket or approval id
- delegated scope
- expiry or hard timeout

그래서 좋은 설계는 아래 둘 중 하나다.

- 일반 session inventory와 별도 support access timeline 또는 emergency access panel을 둔다
- 같은 화면을 쓰더라도 `support access`, `break-glass` badge와 종료 경로를 분리한다

customer-facing 알림 문구, timeline retention, privacy-safe copy 원칙은 [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)에서 이어서 보는 편이 좋다.

### 9. support tooling과 user-facing UX는 같은 용어를 써야 한다

지원 도구에서 `family revoke`라고 하고 사용자 화면에서는 `이 기기 로그아웃`이라고 쓰면, 대응 중 설명이 어긋난다.

좋은 패턴:

- 사용자 UI label
- 내부 audit action name
- support console action

이 셋이 같은 범위 모델을 공유한다.

### 10. reverse link도 scope 축을 따라 묶는 편이 retrieval에 유리하다

세션 목록 UX 문서를 찾는 사람은 보통 아래 문맥 중 하나를 같이 찾는다.

- device/session graph 모델
- distributed revocation tail
- refresh family invalidation
- session quarantine

그래서 관련 문서 링크도 "세션 그래프", "무효화 전파", "중간 격리 상태" 축으로 묶어 두는 편이 좋다.

---

## 실전 시나리오

### 시나리오 1: 사용자가 "이 기기만 로그아웃"을 눌렀는데 같은 노트북의 다른 브라우저 프로필도 같이 죽는다

문제:

- UI는 device 단위처럼 보였지만 실제 구현은 account-wide family revoke였다

대응:

- row가 가리키는 객체를 다시 정의한다
- button copy를 revoke scope 기준으로 바꾼다
- audit action name과 UI label을 맞춘다

### 시나리오 2: "모든 기기에서 로그아웃" 직후 일부 모바일 API가 잠깐 계속 통과한다

문제:

- propagation lag와 access token tail을 UI에서 전혀 설명하지 않았다

대응:

- high-risk route는 즉시 막는다
- session inventory에는 revoke requested와 completion 상태를 분리한다
- support가 확인할 수 있는 last accepted after revoke evidence를 남긴다

### 시나리오 3: risk signal 때문에 일부 세션만 quarantine됐는데 사용자는 버그로 오해한다

문제:

- active/revoked 외의 중간 상태가 UI에 없다

대응:

- restricted state badge를 노출한다
- 어떤 작업이 막혔는지와 해제 방법을 함께 보여 준다
- step-up 또는 recovery flow로 자연스럽게 이어 준다

### 시나리오 4: support가 고객 대신 MFA reset을 수행했는데 고객 보안 화면에는 새 기기 로그인처럼만 보인다

문제:

- AOBO session과 ordinary user session이 같은 row model을 공유했다

대응:

- support access timeline을 일반 device inventory와 분리한다
- 최소한 `support access`, operator id, reason, ticket id를 함께 노출한다
- 고객-facing copy와 내부 audit action name을 맞춘다

### 시나리오 5: break-glass로 tenant-wide 복구를 했는데 ordinary admin session처럼 묻혀 cleanup이 늦어진다

문제:

- emergency override가 session inventory에서 별도 상태로 보이지 않는다

대응:

- emergency access panel을 분리한다
- hard expiry와 leftover alert를 둔다
- `revoke all devices` 같은 일반 action과 다른 종료 절차를 둔다

---

## 코드로 보기

### 1. inventory row 예시

```json
{
  "row_id": "sess_web_123",
  "scope_kind": "browser_session",
  "device_label": "MacBook Pro / Chrome",
  "last_active_at": "2026-04-14T10:12:00Z",
  "auth_time": "2026-04-14T08:03:00Z",
  "state": "active",
  "actions": [
    "revoke_current_session",
    "revoke_device_sessions"
  ]
}
```

### 2. revoke action naming 예시

```text
revoke_current_session
revoke_current_device
revoke_refresh_family
revoke_all_devices
quarantine_session
```

### 3. 운영 체크리스트

```text
1. 세션 목록 row가 실제 revoke 단위와 맞는가
2. current session / current device / all devices를 명확히 구분하는가
3. revoke requested와 fully blocked confirmed를 분리해 표현하는가
4. quarantine, step-up required 같은 중간 상태가 UI에 드러나는가
5. AOBO와 break-glass가 ordinary session row와 분리돼 보이는가
6. support tooling과 audit action name이 같은 범위 모델을 쓰는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| device만 보여주는 단순 목록 | UI가 단순하다 | 실제 revoke 범위를 오해하기 쉽다 | low-risk, 단순 서비스 |
| session row를 자세히 노출 | 범위 설명이 정확하다 | 목록이 길어질 수 있다 | multi-device, multi-session 서비스 |
| support access timeline을 별도로 둠 | AOBO와 ordinary session 의미가 선명하다 | UI surface가 늘어난다 | support operator가 자주 개입하는 서비스 |
| 즉시 완료 copy | UX가 간단하다 | propagation tail을 숨긴다 | 완전 stateful, 즉시 차단 가능한 구조 |
| 진행 상태를 분리 노출 | support 비용이 줄고 설명이 정확하다 | 상태 모델이 복잡해진다 | 분산 revocation tail이 존재하는 구조 |

판단 기준은 이렇다.

- revoke 절단면을 사용자에게 설명해야 하는가
- 같은 기기에서 여러 session/client가 공존하는가
- propagation lag를 제품적으로 숨길 수 있는가
- support/operator가 세션 상태를 자주 다루는가

---

## 꼬리질문

> Q: 세션 목록 row는 왜 실제 제어 단위와 맞아야 하나요?
> 의도: UX label과 revoke scope의 일치를 보는지 확인
> 핵심: 사용자가 누른 범위와 시스템이 실제로 끊는 범위가 달라지면 보안 오해와 지원 비용이 커지기 때문이다.

> Q: "모든 기기 로그아웃" 직후에도 tail이 남을 수 있는 이유는 무엇인가요?
> 의도: propagation lag와 token TTL을 구분하는지 확인
> 핵심: refresh revoke와 별개로 access token TTL, cache, regional fan-out이 남을 수 있기 때문이다.

> Q: quarantine 상태를 왜 inventory에 보여줘야 하나요?
> 의도: revoke 외 중간 상태 설계를 이해하는지 확인
> 핵심: 일부 기능만 막힌 이유와 recovery 경로를 설명해야 사용자가 버그로 오해하지 않기 때문이다.

> Q: 왜 support access를 일반 세션과 분리해 보여 줘야 하나요?
> 의도: AOBO와 ordinary session의 의미 차이를 이해하는지 확인
> 핵심: 사용자의 직접 로그인과 운영자의 대리 개입을 같은 row로 섞으면 audit와 고객 설명이 모두 흐려지기 때문이다.

## 한 줄 정리

세션 관리 UX의 핵심은 목록을 예쁘게 만드는 것이 아니라, 사용자가 본 revoke 범위와 시스템이 실제로 끊는 범위를 정확히 같게 만들고 support AOBO와 break-glass를 ordinary session과 구분해 보여 주는 것이다.
