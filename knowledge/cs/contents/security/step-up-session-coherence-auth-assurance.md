# Step-Up Session Coherence / Auth Assurance

> 한 줄 요약: step-up auth의 핵심은 MFA를 한 번 더 붙이는 것이 아니라, 기본 세션과 상승된 보증 수준 세션을 구분하고 `auth_time`, assurance level, 만료, revoke 범위를 일관되게 운영하는 것이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md)
> - [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
> - [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
> - [Password Reset Threat Modeling](./password-reset-threat-modeling.md)
> - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
> - [Session Store Design at Scale](../system-design/session-store-design-at-scale.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: step-up session, auth assurance, reauthentication, elevated session, auth_time, acr, amr, session age, step-up TTL, sensitive action reauth, assurance level, session coherence, session quarantine

## 이 문서 다음에 보면 좋은 문서

- step-up 상태를 사용자와 operator 화면에서 어떤 revoke scope로 보여 줄지는 [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)로 이어진다.

---

## 핵심 개념

step-up auth를 도입한 시스템에서 흔한 실수는 "추가 인증을 한 번 더 받았으니 이제 세션이 강해졌다"로 끝내는 것이다.

실제로는 질문이 더 많다.

- 어떤 세션이 기본 세션인가
- 어떤 작업부터 높은 assurance를 요구하는가
- step-up 결과를 얼마나 오래 믿을 것인가
- 로그아웃, 비밀번호 변경, device mismatch 때 elevated state를 어떻게 끊을 것인가

즉 step-up의 본질은 MFA 수단보다 세션 coherence다.

---

## 깊이 들어가기

### 1. 로그인 세션과 elevated 세션은 같은 것이 아니다

보통 사용자에게는 "로그인됨"이라는 하나의 상태만 보이지만, 시스템은 더 세밀하게 봐야 한다.

- base session: 일반 페이지와 저위험 API 접근용
- elevated session or grant: 송금, 비밀번호 변경, 관리자 작업용

이 둘을 구분하지 않으면 문제가 생긴다.

- 한번 step-up 후 모든 기능이 영구적으로 높은 보증 수준이 된다
- 반대로 고위험 작업마다 불필요하게 계속 재인증하게 된다

### 2. assurance는 role이 아니라 최근성(freshness)까지 포함한다

민감 작업에 필요한 건 "이 사용자가 관리자다"만이 아니다.

- 정말 최근에 강한 인증을 했는가
- 어떤 수단으로 인증했는가
- 현재 device/session가 그 인증과 이어지는가

그래서 보통 step-up 판단에는 이런 정보가 필요하다.

- `auth_time`
- `acr` 또는 내부 assurance level
- `amr` 또는 사용한 인증 수단
- session age
- 최근 risk signal

즉 step-up은 "누구인가"와 "얼마나 최근에 얼마나 강하게 확인했는가"를 같이 본다.

### 3. elevated 상태는 별도 artifact로 두는 편이 안전하다

좋지 않은 패턴:

- 기존 세션 플래그 하나를 `mfa=true`로 영구 수정

더 나은 패턴:

- base session은 그대로 유지
- 별도의 step-up grant를 발급
- grant에 scope, issued_at, expires_at, reason을 둔다

예:

- `payments.transfer`
- `admin.user.disable`
- `settings.password.change`

이렇게 해야 고위험 작업 범위를 제한하고, 만료와 revoke도 명확해진다.

### 4. TTL은 risk tier별로 달라야 한다

모든 step-up 결과를 같은 시간 동안 신뢰할 필요는 없다.

- 비밀번호 변경: 매우 짧게
- 대량 송금: 한 번의 작업에만
- 관리자 읽기 전용 콘솔: 조금 더 길게

step-up TTL이 너무 길면 세션 탈취 피해가 커지고, 너무 짧으면 UX가 무너진다.

핵심은 작업 클래스를 나누는 것이다.

### 5. browser/BFF 구조에서는 step-up 상태도 서버 측 세션으로 보는 편이 낫다

브라우저에 elevated claim을 오래 노출하면 곤란하다.

- 탭 복제
- XSS 후 elevated token 재사용
- logout 시 일부 탭만 상태가 남음

그래서 BFF 구조라면 보통:

- browser는 step-up challenge 결과 자체를 오래 들지 않음
- BFF/session store가 elevated grant를 관리
- downstream에는 필요한 순간에만 좁은 elevated context를 보냄

### 6. federated login에서는 IdP assurance와 local assurance를 혼동하면 안 된다

외부 IdP가 강한 인증을 했더라도, 우리 앱에서 어떤 작업까지 허용할지는 별도 정책일 수 있다.

예를 들어:

- IdP에서 MFA 완료
- 하지만 우리 앱은 관리자 기능 전용 local reauth를 요구

즉 external `acr`을 그대로 내부 최종 권한으로 쓰기보다, local assurance mapping이 필요하다.

### 7. misuse containment와 step-up은 연결돼야 한다

위험 신호가 올라왔다고 바로 global logout만 할 필요는 없다.

중간 대응으로 step-up이 유용하다.

- ASN/UA 급변
- device binding mismatch
- 약한 replay signal
- support admin acting-on-behalf-of 작업

이 경우:

- read는 허용
- write는 elevated grant 요구
- refresh는 잠시 quarantine

같은 단계적 정책이 가능하다.

### 8. revoke 범위를 정의하지 않으면 elevated state가 남는다

반드시 정해야 할 것:

- base session logout 시 elevated grant도 같이 끊는가
- 비밀번호 변경 시 모든 elevated grant를 끊는가
- account lockout 시 device별 grant를 어떻게 fan-out하는가
- federated logout가 local elevated grant도 종료하는가

elevated state는 세션의 일부이므로 revoke 모델에 포함되어야 한다.

---

## 실전 시나리오

### 시나리오 1: 한번 MFA 후 관리자 위험 작업이 하루 종일 열린다

문제:

- step-up 결과를 base session에 영구 플래그로 덮어썼다

대응:

- 별도 elevated grant로 분리한다
- action scope와 짧은 TTL을 둔다
- base session과 revoke를 연결한다

### 시나리오 2: 사용자는 방금 로그인했는데도 비밀번호 변경 때마다 계속 MFA를 요구받는다

문제:

- 어떤 assurance level이면 충분한지 정책이 없다

대응:

- 작업별 required assurance와 freshness window를 문서화한다
- 최근 strong auth면 재사용 가능한 짧은 grant를 둔다

### 시나리오 3: federated logout 후에도 민감 작업이 계속 가능하다

문제:

- local elevated grant가 별도 revoke되지 않는다

대응:

- logout fan-out에 elevated grant store를 포함한다
- issuer/sub/sid와 local elevated grant mapping을 둔다

---

## 코드로 보기

### 1. elevated grant 개념

```java
public record StepUpGrant(
        String sessionId,
        String subject,
        String scope,
        String assuranceLevel,
        Instant issuedAt,
        Instant expiresAt
) {
}
```

### 2. 작업별 assurance 검사 예시

```java
public void requireAssurance(UserSession session, String action) {
    StepUpPolicy policy = policyRepository.findByAction(action);
    StepUpGrant grant = grantRepository.findActiveGrant(session.id(), action);

    if (grant == null || grant.expiresAt().isBefore(Instant.now())) {
        throw new ReauthenticationRequiredException(policy.requiredLevel());
    }
}
```

### 3. 운영 체크리스트

```text
1. base session과 elevated grant가 분리되어 있는가
2. action class별 required assurance와 freshness가 정의돼 있는가
3. logout, password change, account disable이 elevated state도 함께 revoke하는가
4. external IdP assurance와 local assurance mapping이 구분되는가
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| base session에 MFA 플래그만 둠 | 구현이 단순하다 | scope, TTL, revoke가 흐려진다 | 가능하면 피한다 |
| action-scoped elevated grant | 세밀한 control이 가능하다 | session mapping이 복잡하다 | 민감 작업이 많은 서비스 |
| 긴 step-up TTL | UX가 좋다 | 탈취 피해 창이 길다 | 낮은 위험 읽기 위주 |
| 짧은 one-shot step-up | 가장 보수적이다 | UX 부담이 크다 | 송금, 권한 변경, 관리자 파괴 작업 |

판단 기준은 이렇다.

- 어떤 작업이 높은 assurance를 요구하는가
- 재인증 UX를 어느 정도 감당할 수 있는가
- BFF/session store에서 elevated state를 운영할 수 있는가
- federated logout와 local revoke를 같이 맞출 수 있는가

---

## 꼬리질문

> Q: step-up auth는 MFA를 한 번 더 붙이는 것과 같은가요?
> 의도: 수단과 세션 모델을 구분하는지 확인
> 핵심: 아니다. step-up은 특정 작업에 더 높은 assurance를 요구하는 세션 정책이다.

> Q: 왜 elevated 상태를 base session과 분리하나요?
> 의도: scope와 revoke의 필요를 이해하는지 확인
> 핵심: 어떤 작업에만, 얼마나 오래, 어떤 조건에서 높은 보증을 인정할지 제어하기 위해서다.

> Q: 외부 IdP가 MFA를 했으면 우리 앱도 무조건 높은 assurance로 봐도 되나요?
> 의도: external assurance와 local policy를 구분하는지 확인
> 핵심: 아니다. 내부 민감 작업 정책은 별도 mapping과 freshness 기준이 필요할 수 있다.

> Q: logout 시 elevated grant도 같이 끊어야 하나요?
> 의도: session coherence 범위를 이해하는지 확인
> 핵심: 그렇다. elevated state가 남으면 민감 작업만 계속 열려 있는 비일관성이 생긴다.

## 한 줄 정리

Step-up auth를 운영 가능하게 만드는 핵심은 MFA 수단보다 base session과 elevated grant의 분리, assurance freshness, revoke 일관성을 세션 모델 안에 넣는 것이다.
