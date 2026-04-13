# Password Reset Threat Modeling

> 한 줄 요약: password reset은 계정 복구의 편의 기능이 아니라, 가장 자주 공격받는 계정 탈취 경로이므로 토큰, 이메일, 세션, rate limit을 함께 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md)
> - [Rate Limiting vs Brute Force Defense](./rate-limiting-vs-brute-force-defense.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Secret Management, Rotation, Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)

retrieval-anchor-keywords: password reset, account recovery, reset token, one-time link, email verification, step-up auth, brute force, reset abuse, account takeover, recovery flow

---

## 핵심 개념

password reset은 계정 탈취의 마지막 퍼즐이 되기 쉽다.

- 이메일 계정이 먼저 뚫릴 수 있다
- reset token이 너무 길게 살아 있을 수 있다
- 재설정 후 기존 세션이 남을 수 있다
- rate limit이 없으면 enumeration이 된다

즉 password reset은 "링크 보내기"가 아니라, 계정 신원 복원과 재인증을 포함한 고위험 플로우다.

---

## 깊이 들어가기

### 1. reset token은 장기 bearer credential이 될 수 있다

reset 링크가 탈취되면 계정이 넘어간다.

- 이메일 포워딩
- 브라우저 히스토리
- 로그
- referer leak

그래서 reset token은 짧고 일회성이어야 한다.

### 2. email ownership만으로 충분하지 않다

이메일은 흔한 복구 수단이지만 절대적이지 않다.

- email 계정 자체가 탈취될 수 있다
- shared mailbox가 있을 수 있다
- 기업 환경에서는 alias가 많다

그래서 고위험 계정은 step-up auth를 추가한다.

### 3. reset request와 reset completion을 분리해서 본다

두 단계는 서로 다른 공격면이다.

- request abuse: 대량 발송, enumeration, spam
- completion abuse: token 탈취, replay, password overwrite

각각 다른 rate limit과 telemetry가 필요하다.

### 4. reset 후 revoke가 중요하다

비밀번호를 바꾸면 끝이 아니다.

- 모든 세션 revoke
- refresh token revoke
- trusted device reset
- MFA 재확인 또는 재등록

이걸 안 하면 탈취자가 계속 남아 있을 수 있다.

### 5. UX와 보안의 균형

reset 플로우가 너무 느리면 support가 폭증한다.  
너무 느슨하면 account takeover가 쉬워진다.

그래서 보통:

- 일반 사용자에게는 self-service
- 고위험 계정에는 step-up
- 대량 요청에는 cooling

---

## 실전 시나리오

### 시나리오 1: reset 이메일이 무한정 발송됨

대응:

- per-account, per-IP rate limit
- reset request cooldown
- enumeration 방지를 위한 동일 응답

### 시나리오 2: reset 링크가 유출됨

대응:

- 단기 TTL
- one-time use
- completion 후 token 폐기

### 시나리오 3: 비밀번호를 바꿨는데 세션이 안 끊김

대응:

- session version bump
- refresh revoke
- 모든 device logout 옵션

---

## 코드로 보기

### 1. reset request 개념

```java
public void requestReset(String email) {
    resetRateLimiter.assertAllowed(email);
    tokenService.issueResetToken(email);
    mailer.sendResetLink(email);
}
```

### 2. reset completion 개념

```java
public void completeReset(String token, String newPassword) {
    String email = resetTokenService.consume(token);
    passwordService.changePassword(email, newPassword);
    sessionService.revokeAllByEmail(email);
}
```

### 3. 보안 규칙

```text
1. reset token은 짧고 일회성으로 만든다
2. reset 요청과 완료를 모두 rate limit한다
3. reset 후 모든 세션을 끊는다
4. 고위험 계정은 step-up auth를 요구한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| email-only reset | 단순하다 | email takeover에 취약하다 | 저위험 서비스 |
| email + reset token | 일반적이다 | token leak 관리가 필요하다 | 대부분의 서비스 |
| email + step-up | 강하다 | UX가 늘어난다 | 고위험 계정 |
| support-assisted reset | 통제가 쉽다 | 운영 비용이 크다 | 예외 처리 |

판단 기준은 이렇다.

- reset token이 탈취되면 피해가 큰가
- email 계정 자체가 안전한가
- reset 완료 후 세션을 즉시 끊을 수 있는가
- 고위험 계정을 별도 취급할 수 있는가

---

## 꼬리질문

> Q: password reset이 왜 공격받기 쉬운가요?
> 의도: 복구 플로우가 취약해지기 쉬운 이유를 아는지 확인
> 핵심: 계정 탈취의 마지막 우회로가 되기 쉽기 때문이다.

> Q: reset token은 왜 위험한가요?
> 의도: 일회성 bearer credential로 보는지 확인
> 핵심: 링크만 있으면 계정을 바꿀 수 있기 때문이다.

> Q: reset 후 무엇을 해야 하나요?
> 의도: 세션/refresh revoke를 아는지 확인
> 핵심: 모든 세션과 토큰을 끊어야 한다.

> Q: reset request는 왜 rate limit해야 하나요?
> 의도: spam, enumeration, abuse를 아는지 확인
> 핵심: 대량 발송과 계정 존재 확인을 막기 위해서다.

## 한 줄 정리

password reset은 복구 기능이지만, 실무에서는 계정 탈취 경로로 악용되기 쉬운 고위험 보안 플로우다.
