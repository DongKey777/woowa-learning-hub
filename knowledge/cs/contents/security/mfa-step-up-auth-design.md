# MFA / Step-Up Auth Design

> 한 줄 요약: MFA는 로그인 한 번으로 끝나는 기능이 아니라, 위험도에 따라 추가 검증을 요구하는 step-up 정책으로 설계해야 운영이 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Rate Limiting vs Brute Force Defense](./rate-limiting-vs-brute-force-defense.md)
> - [WebAuthn / Passkeys / Phishing-Resistant Login](./webauthn-passkeys-phishing-resistant-login.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Security README: Browser / Session Coherence](./README.md#browser--session-coherence)

retrieval-anchor-keywords: MFA, step-up auth, risk-based auth, TOTP, WebAuthn, recovery code, reauthentication, sensitive action, account takeover, session age, auth assurance, elevated session, auth_time

---

## 핵심 개념

MFA(Multi-Factor Authentication)는 하나의 계정 보호 수단이 아니라, 인증 보증 수준(assurance level)을 높이는 장치다.  
실무에서는 모든 요청에 항상 MFA를 요구하기보다, 위험한 순간에 추가 인증을 요구하는 step-up 방식이 더 자연스럽다.

핵심 요소:

- `something you know`: 비밀번호, PIN
- `something you have`: 휴대폰, 인증 앱, 하드웨어 키
- `something you are`: 생체인식
- `step-up auth`: 민감 작업 전에 더 강한 인증을 추가로 요구하는 것

즉 MFA는 로그인 한 번의 이벤트가 아니라, 세션 전체의 위험도 관리다.

---

## 깊이 들어가기

### 1. 왜 MFA만으로는 충분하지 않은가

MFA가 있어도 다음 공격은 가능하다.

- 세션 탈취 후 재사용
- 인증 직후 민감 작업 수행
- 복구 경로를 통한 우회
- push fatigue, OTP 피로 공격

그래서 민감 작업에는 step-up이 필요하다.

예:

- 비밀번호 변경
- 출금
- 결제 수단 추가
- API key 발급
- 새 기기 등록
- 관리자 권한 변경

### 2. risk-based auth가 유용하다

항상 같은 수준의 MFA를 요구하면 UX가 무거워진다.

대신 위험 신호를 본다.

- 새 디바이스
- 새 국가/IP
- 세션 나이
- 비정상 실패 횟수
- 고위험 endpoint 접근
- 계정 회수/이메일 변경 직후

위험이 낮으면 평소 세션으로 허용하고, 위험이 높으면 추가 인증을 요구한다.

### 3. 인증 수단마다 운영 특성이 다르다

- `TOTP`: 널리 쓰이지만 피싱과 실시간 릴레이에 약할 수 있다
- `SMS OTP`: 사용성은 좋지만 SIM swap과 delivery 지연 문제가 있다
- `push approval`: 편하지만 fatigue 공격이 생길 수 있다
- `WebAuthn`: 피싱 저항성이 강하다

즉 MFA는 하나를 고르는 문제가 아니라, threat model에 맞는 factor 조합을 고르는 문제다.

### 4. recovery path가 가장 약한 고리다

많은 계정 탈취는 본 인증이 아니라 복구 경로에서 난다.

- 백업 이메일이 너무 약하다
- recovery code가 로그에 남는다
- 고객센터 절차가 느슨하다

그래서 recovery는 MFA보다 더 강하게 설계해야 한다.

### 5. session age와 step-up을 연결해야 한다

세션이 오래됐는데도 출금이나 설정 변경을 허용하면 위험하다.

보통 다음을 함께 본다.

- 마지막 강한 인증 시각
- 세션 생성 시각
- 재인증 후 경과 시간
- 최근 위험 이벤트 여부

---

## 실전 시나리오

### 시나리오 1: 로그인은 성공했지만 결제 수단 추가는 차단해야 함

문제:

- 일반 로그인과 민감 작업의 위험도가 다르다

대응:

- step-up auth를 요구한다
- 비밀번호 재입력 또는 WebAuthn assertion을 요구한다
- 일정 시간 안에만 추가 작업을 허용한다

### 시나리오 2: SMS OTP가 너무 자주 오감

문제:

- 재전송 폭주와 사용성 저하가 생긴다

대응:

- rate limit을 둔다
- 재전송 쿨다운을 둔다
- TOTP나 passkey로 전환을 유도한다

### 시나리오 3: 새 기기 등록이 공격자가 가장 먼저 노리는 지점

문제:

- 세션 탈취 후 새 MFA 수단을 등록하면 계정이 사실상 넘어간다

대응:

- 새 기기 등록은 항상 step-up을 요구한다
- 기존 factor로 알림을 보낸다
- 등록 후 즉시 revoke 가능한 관리 화면을 제공한다

---

## 코드로 보기

### 1. step-up 판단 개념

```java
public void requireStepUp(UserPrincipal user, String action) {
    boolean sensitive = Set.of("withdraw", "change_password", "add_device").contains(action);
    boolean sessionTooOld = Duration.between(user.lastStrongAuthAt(), Instant.now()).toMinutes() > 30;

    if (sensitive || sessionTooOld || riskEngine.isHighRisk(user)) {
        throw new StepUpRequiredException("additional verification required");
    }
}
```

### 2. MFA challenge 수행 예시

```java
public void verifyTotp(String userId, String code) {
    if (!mfaDeviceService.matchesTotp(userId, code)) {
        throw new SecurityException("invalid mfa code");
    }
    authSessionService.markStronglyVerified(userId);
}
```

### 3. 민감 작업 전 재인증

```text
1. 일반 로그인으로 세션을 만든다
2. 위험 점수를 계산한다
3. 민감 작업이면 step-up을 요구한다
4. 성공 시 짧은 시간만 강한 인증 상태를 허용한다
5. 작업 완료 후 감사 로그를 남긴다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| always-on MFA | 단순하다 | UX가 무겁다 | 매우 민감한 시스템 |
| step-up auth | UX와 보안을 균형 있게 잡는다 | 정책 설계가 복잡하다 | 대부분의 실서비스 |
| TOTP | 보편적이다 | 피싱/릴레이에 취약할 수 있다 | 기본 MFA |
| WebAuthn step-up | 강하다 | 호환성/복구 설계가 필요하다 | 높은 보안 요구 |

판단 기준은 이렇다.

- 어떤 작업을 추가 검증 대상으로 볼 것인가
- 재인증 유효 시간을 얼마나 줄 것인가
- recovery path를 어떻게 강하게 유지할 것인가
- MFA 실패 시 계정 잠금이 DoS가 되지 않는가

---

## 꼬리질문

> Q: MFA와 step-up auth는 같은 말인가요?
> 의도: 인증 강도와 정책 시점을 구분하는지 확인
> 핵심: 아니다. MFA는 수단이고 step-up은 정책이다.

> Q: 왜 모든 요청에 MFA를 요구하지 않나요?
> 의도: UX와 위험도 기반 설계를 아는지 확인
> 핵심: 대부분의 요청은 과도하게 무거워지기 때문이다.

> Q: recovery path가 왜 더 위험할 수 있나요?
> 의도: 우회 경로의 중요성을 아는지 확인
> 핵심: 본 인증보다 느슨하면 계정 탈취가 쉬워진다.

> Q: WebAuthn이 MFA에서 좋은 이유는 무엇인가요?
> 의도: 피싱 저항성 이해 확인
> 핵심: origin-bound 공개키 기반이라 피싱에 강하다.

## 한 줄 정리

MFA는 계정에 한 번 거는 스위치가 아니라, 위험한 순간에만 강한 인증을 요구하는 step-up 정책으로 설계해야 한다.
