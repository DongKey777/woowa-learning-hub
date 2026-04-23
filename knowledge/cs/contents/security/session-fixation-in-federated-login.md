# Session Fixation in Federated Login

> 한 줄 요약: federated login은 외부 IdP를 쓰더라도 세션 고정 공격이 사라지지 않는다. callback 이후 세션 재발급과 state 연동을 제대로 해야 login CSRF와 fixation을 같이 막을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Session Revocation at Scale](./session-revocation-at-scale.md)
> - [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)
> - [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)

retrieval-anchor-keywords: session fixation, federated login, login CSRF, session regeneration, callback, IdP, state, nonce, session fixation attack, authenticated session, Spring Security, browser session coherence, login hardening path, post-login hardening, browser server boundary catalog, security readme browser server boundary

## 이 문서 다음에 보면 좋은 문서

- 브라우저 login hardening 묶음으로 다시 돌아가려면 [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)에서 redirect, fixation, browser-visible credential 축을 한 번에 다시 고를 수 있다.
- callback 이전 redirect 검증 축은 [Open Redirect Hardening](./open-redirect-hardening.md)으로 이어진다.
- callback 이후 frame/script hardening까지 붙여 보려면 [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)로 이어진다.

---

## 핵심 개념

session fixation은 공격자가 피해자의 세션 식별자를 먼저 정해두고, 피해자가 로그인한 뒤 그 세션을 이어 쓰게 만드는 공격이다.  
federated login에서도 이 문제는 그대로 남는다.

핵심은 다음이다.

- 외부 IdP 로그인 성공만으로 기존 세션을 계속 쓰면 안 된다
- callback 시점에 세션을 재발급해야 한다
- state와 callback 연동이 깨지면 login CSRF가 된다
- login 완료 후 privileged session으로 전환해야 한다

즉 federated login은 "외부에서 인증했다"가 끝이 아니라, "우리 세션을 새로 만들어야 한다"가 핵심이다.

---

## 깊이 들어가기

### 1. 왜 세션 재발급이 필요한가

공격자가 미리 심어둔 세션 ID를 로그인 후에도 그대로 쓰면 fixation이 된다.

- 사용자는 정상 로그인했다고 생각한다
- 공격자는 같은 세션을 재사용한다
- 브라우저 cookie가 그대로 살아 있으면 위험하다

### 2. callback에서 해야 할 일

OAuth/OIDC callback에서는 다음이 필요하다.

- state 검증
- external identity 검증
- 기존 세션 폐기 또는 교체
- 새 session id 발급
- 권한 재평가

### 3. same-session continuation을 피해야 한다

로그인 전 익명 세션과 로그인 후 인증 세션은 같은 객체처럼 보이면 안 된다.

- 익명 cart 세션과 인증 세션은 구분될 수 있다
- 반면 session fixation 방어를 위해 session id는 재발급해야 한다
- 내부 속성만 옮기고 식별자는 바꿔야 한다

### 4. federated login에서 흔한 실수

- callback 후 redirect만 하고 세션을 바꾸지 않는다
- external provider 결과를 곧바로 privileged session으로 본다
- state를 검증하지 않고 code만 교환한다
- login 성공 후 쿠키 scope를 넓게 둔다

### 5. step-up과 연결할 수 있다

민감한 작업은 federated login 이후에도 step-up이 필요할 수 있다.

- password change
- payment
- device registration
- admin action

즉 한번 IdP로 로그인했다고 고위험 권한까지 끝난 것은 아니다.

---

## 실전 시나리오

### 시나리오 1: IdP 로그인 후 세션이 그대로 남음

대응:

- callback에서 새 세션을 발급한다
- 이전 세션은 폐기한다
- 권한과 CSRF token을 재초기화한다

### 시나리오 2: login CSRF와 fixation이 같이 의심됨

대응:

- state 검증을 강화한다
- callback 도메인과 redirect를 엄격히 분리한다
- login 후 session regeneration을 강제한다

### 시나리오 3: SSO 후 privileged cookie가 유지됨

대응:

- 일반 세션과 관리자 세션을 분리한다
- 관리자 세션은 별도 step-up을 요구한다
- session revocation과 audit log를 남긴다

---

## 코드로 보기

### 1. session regeneration 개념

```java
public void onOAuthLoginSuccess(HttpServletRequest request, UserAccount account) {
    request.changeSessionId();
    HttpSession session = request.getSession(true);
    session.setAttribute("userId", account.getId());
}
```

### 2. state와 session 연동

```java
public void validateCallback(String state, HttpServletRequest request) {
    if (!stateService.matches(request.getSession().getId(), state)) {
        throw new SecurityException("state mismatch");
    }
}
```

### 3. privileged session 분리

```text
1. 로그인 전 익명 세션과 로그인 후 인증 세션을 분리한다
2. callback에서 session id를 바꾼다
3. 민감 작업은 별도 step-up 세션을 둔다
4. logout 시 모든 세션을 revoke한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| session regeneration | fixation을 줄인다 | 구현을 빼먹기 쉽다 | 거의 항상 |
| same session reuse | 구현이 쉽다 | fixation 위험이 크다 | 비권장 |
| separate privileged session | 민감 작업에 강하다 | UX가 늘어난다 | 관리자/결제 |
| stateless JWT only | 수평 확장이 쉽다 | fixation 자체는 세션보다 덜하지만 다른 재사용 문제가 있다 | API 중심 |

판단 기준은 이렇다.

- callback 후 세션 식별자를 바꾸는가
- state를 세션과 함께 검증하는가
- privileged action에 별도 재인증이 필요한가
- logout 시 기존 세션을 모두 끊는가

---

## 꼬리질문

> Q: federated login에서 왜 session fixation을 걱정하나요?
> 의도: IdP 사용과 세션 방어를 분리하는지 확인
> 핵심: 외부 인증이 있어도 우리 세션은 여전히 고정 공격에 노출되기 때문이다.

> Q: callback에서 가장 먼저 해야 할 일은 무엇인가요?
> 의도: state와 세션 재발급의 순서를 아는지 확인
> 핵심: state 검증과 session regeneration이다.

> Q: 왜 privileged session을 따로 둘 수 있나요?
> 의도: 민감 작업 분리 설계를 이해하는지 확인
> 핵심: 일반 로그인과 고위험 작업의 보안 수준이 다르기 때문이다.

> Q: session fixation과 login CSRF는 같은 문제인가요?
> 의도: 서로 다른지만 연결된 공격을 아는지 확인
> 핵심: 다르지만 callback과 세션 처리에서 함께 터질 수 있다.

## 한 줄 정리

federated login에서는 IdP 인증 이후에도 우리 세션을 새로 발급하고 state를 묶어 fixation과 login CSRF를 같이 막아야 한다.
