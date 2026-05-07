---
schema_version: 3
title: Session Quarantine / Partial Lockdown Patterns
concept_id: security/session-quarantine-partial-lockdown-patterns
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- session quarantine
- partial lockdown
- suspicious session
- step-up recovery
aliases:
- session quarantine
- partial lockdown
- suspicious session
- step-up recovery
- compromised session containment
- session downgrade
- restricted session
- auth quarantine
- risk-based lockdown
- refresh freeze
- read-only session
- Session Quarantine / Partial Lockdown Patterns
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/token-misuse-detection-replay-containment.md
- contents/security/step-up-session-coherence-auth-assurance.md
- contents/security/session-revocation-at-scale.md
- contents/security/mfa-step-up-auth-design.md
- contents/security/oidc-backchannel-logout-session-coherence.md
- contents/security/auth-observability-sli-slo-alerting.md
- contents/security/bff-session-store-outage-degradation-recovery.md
- contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
- contents/system-design/session-store-design-at-scale.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Session Quarantine / Partial Lockdown Patterns 핵심 개념을 설명해줘
- session quarantine가 왜 필요한지 알려줘
- Session Quarantine / Partial Lockdown Patterns 실무 설계 포인트는 뭐야?
- session quarantine에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Session Quarantine / Partial Lockdown Patterns를 다루는 deep_dive 문서다. 보안 이상 신호가 생겼다고 항상 즉시 전세션 revoke를 할 필요는 없으며, session quarantine은 기본 접근은 줄이고 민감 작업은 step-up으로 승격시키는 중간 상태를 운영하는 패턴이다. 검색 질의가 session quarantine, partial lockdown, suspicious session, step-up recovery처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Session Quarantine / Partial Lockdown Patterns

> 한 줄 요약: 보안 이상 신호가 생겼다고 항상 즉시 전세션 revoke를 할 필요는 없으며, session quarantine은 기본 접근은 줄이고 민감 작업은 step-up으로 승격시키는 중간 상태를 운영하는 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md)
> - [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
> - [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
> - [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

retrieval-anchor-keywords: session quarantine, partial lockdown, suspicious session, step-up recovery, compromised session containment, session downgrade, restricted session, auth quarantine, risk-based lockdown, refresh freeze, read-only session

---

## 핵심 개념

계정 이상 징후가 잡혔을 때 선택지는 보통 둘로 생각되기 쉽다.

- 그냥 계속 허용
- 모든 세션 즉시 끊기

하지만 실무에서는 그 사이 상태가 유용하다.  
그것이 session quarantine이다.

session quarantine은 보통 다음을 의미한다.

- 민감 write 차단
- refresh 또는 장기 세션 연장 중지
- 일부 route는 read-only 유지
- 고위험 작업은 step-up 또는 재인증 요구
- support와 사용자 recovery 경로 제공

즉 quarantine은 "애매하면 다 끊자"가 아니라, 의심 세션을 더 좁은 권한 영역으로 즉시 격리하는 운영 패턴이다.

---

## 깊이 들어가기

### 1. quarantine은 revoke보다 목적이 다르다

revoke는 세션을 무효화한다.  
quarantine은 세션을 살아 있게 두되 위험한 능력을 줄인다.

이게 필요한 이유:

- weak signal만으로 전계정 logout은 오탐 비용이 크다
- support/admin acting-on-behalf-of 도구는 즉시 중단보다 추가 확인이 더 적합할 수 있다
- 사용자가 읽기 기능은 계속 써야 하지만 송금/변경은 막아야 할 수 있다

### 2. quarantine은 route class와 capability를 기준으로 설계해야 한다

좋은 quarantine 정책은 단순 플래그가 아니다.

- read-only 허용 여부
- profile update 차단 여부
- payment/admin/security settings 차단 여부
- refresh token rotation 허용 여부
- API key 발급, MFA reset 같은 고위험 기능 차단 여부

즉 "quarantined=true"보다 capability matrix가 중요하다.

### 3. base session과 elevated grant를 함께 봐야 한다

이미 높은 assurance를 가진 세션이라도 risk signal이 생기면 더 이상 신뢰하면 안 될 수 있다.

예:

- step-up 직후 device fingerprint가 크게 달라짐
- impossible travel과 refresh reuse가 동시에 발생

이 경우:

- 기존 elevated grant 즉시 폐기
- base session만 quarantine 상태로 유지
- 새 step-up 후에만 민감 작업 재허용

즉 quarantine은 elevated state를 먼저 깎는 방향으로 설계하는 편이 안전하다.

### 4. refresh freeze는 강력한 중간 제어 수단이다

세션을 바로 끊지 않더라도 아래는 가능하다.

- 현재 access token은 짧게 만료되도록 둔다
- refresh 재발급은 중단한다
- 새 기기/새 탭 확장은 막는다

이렇게 하면 공격자가 장기 세션을 유지하기 어려워지고, 사용자에게도 회복 여지를 남긴다.

### 5. quarantine 해제는 명시적 recovery action이어야 한다

자동 해제만 두면 위험하다.

가능한 recovery:

- step-up auth 재성공
- 비밀번호 재확인
- trusted device 확인
- support 검토 및 승인

즉 quarantine은 timeout만으로 풀리는 flag라기보다, 추가 검증을 통해 상태를 재평가하는 워크플로우다.

### 6. multi-device와 session family를 같이 봐야 한다

의심 신호가 하나의 세션에 국한되는지, 계정 전체 compromise인지 구분해야 한다.

- 한 device session만 quarantine
- 같은 refresh family 전체 quarantine
- 계정 전체 login 차단

이 범위를 잘못 잡으면:

- 공격자는 다른 세션으로 옮겨 간다
- 반대로 정상 사용자의 모든 기기가 과도하게 막힌다

### 7. audit와 UX가 같이 설계돼야 한다

사용자에게는 단순 "오류"가 아니라 의미가 전달돼야 한다.

- 왜 민감 작업이 막혔는가
- 어떤 추가 인증이 필요한가
- support에 무엇을 전달해야 하는가

내부 audit에는 필요하다.

- quarantine reason
- applied restrictions
- release action
- released by user or operator

### 8. quarantine는 영구 상태가 아니라 incident control plane의 일부다

즉흥적 예외가 아니라 아래가 있어야 한다.

- 상태 전이: active -> quarantined -> recovered or revoked
- TTL
- control owner
- metrics
- kill switch

그래야 운영 중에 누가 왜 세션을 제한했는지 남고, 장기 유령 상태가 쌓이지 않는다.

---

## 실전 시나리오

### 시나리오 1: refresh reuse가 의심되지만 오탐 가능성이 있어 전세션 revoke가 부담스럽다

문제:

- compromise와 네트워크 race를 아직 구분 못 한다

대응:

- family를 quarantine 상태로 전환한다
- refresh 연장을 막고 민감 write를 차단한다
- 다음 민감 작업은 step-up을 요구한다

### 시나리오 2: support operator acting-on-behalf-of 세션에서 이상 신호가 발생한다

문제:

- 업무 중단과 보안 통제가 충돌한다

대응:

- read-only quarantine으로 전환한다
- destructive admin action만 차단한다
- operator reauth와 approval 후 해제한다

### 시나리오 3: federated logout는 됐는데 local app에서는 일부 민감 기능만 계속 열려 있다

문제:

- elevated grant와 quarantine/revoke 경계가 분리돼 있다

대응:

- logout fan-out이 elevated grant와 quarantine state도 함께 정리하도록 맞춘다
- session state transition을 한 저장소에서 관리한다

---

## 코드로 보기

### 1. session state 전이 예시

```java
public enum SessionState {
    ACTIVE,
    QUARANTINED,
    REVOKED
}
```

### 2. capability matrix 예시

```java
public boolean canPerform(SessionState state, RouteClass routeClass) {
    return switch (state) {
        case ACTIVE -> true;
        case QUARANTINED -> routeClass == RouteClass.READ_ONLY;
        case REVOKED -> false;
    };
}
```

### 3. 운영 체크리스트

```text
1. quarantine가 revoke와 별도 상태로 정의돼 있는가
2. read/write/admin/security route별 제한이 명확한가
3. elevated grant와 refresh family를 같이 제어하는가
4. quarantine 해제가 명시적 recovery action으로 설계돼 있는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 즉시 전세션 revoke | 가장 단순하고 강하다 | 오탐 시 UX 피해가 크다 | 강한 compromise 신호 |
| session quarantine | 단계적 대응이 가능하다 | 상태 모델과 UX가 복잡하다 | 회색 신호, 단계적 containment |
| read-only quarantine | 사용자 피해를 줄인다 | 일부 정보 노출은 계속될 수 있다 | consumer app, support workflow |
| refresh freeze only | 구현이 단순하다 | 현재 세션 활동은 일부 계속된다 | 장기 세션 연장만 먼저 막고 싶을 때 |

판단 기준은 이렇다.

- 신호 강도가 revoke까지 갈 만큼 강한가
- 사용자가 읽기 기능을 계속 써야 하는가
- support/admin workflow가 즉시 중단되면 피해가 큰가
- elevated grant와 refresh family를 같이 통제할 수 있는가

---

## 꼬리질문

> Q: session quarantine은 revoke와 무엇이 다른가요?
> 의도: 무효화와 제한적 격리를 구분하는지 확인
> 핵심: revoke는 세션 종료, quarantine은 세션을 제한 상태로 유지하며 민감 능력을 줄이는 것이다.

> Q: 왜 elevated grant를 먼저 끊는 편이 안전한가요?
> 의도: 높은 assurance 상태의 위험을 이해하는지 확인
> 핵심: 의심 세션이 높은 권한 상태를 유지하면 가장 위험한 작업이 계속 열리기 때문이다.

> Q: quarantine 해제를 자동 timeout만으로 해도 되나요?
> 의도: recovery action의 필요를 아는지 확인
> 핵심: 보통은 아니다. step-up, 비밀번호 재확인, support 검토 같은 명시적 복구가 더 안전하다.

> Q: read-only quarantine은 왜 유용한가요?
> 의도: 보안과 UX 균형을 보는지 확인
> 핵심: 전체 중단 없이 민감 write만 빠르게 막을 수 있기 때문이다.

## 한 줄 정리

Session quarantine의 핵심은 오탐 비용과 보안 위험 사이에서 revoke 전 단계의 제한 상태를 만들어, step-up과 recovery workflow로 세션을 다시 신뢰 가능한 상태로 되돌리는 것이다.
