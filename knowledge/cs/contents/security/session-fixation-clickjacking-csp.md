---
schema_version: 3
title: Session Fixation Clickjacking CSP
concept_id: security/session-fixation-clickjacking-csp
canonical: true
category: security
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- login-session-hardening
- clickjacking-frame-policy
- csp-defense-in-depth
aliases:
- session fixation clickjacking csp
- 세션 고정 클릭재킹 CSP
- session id rotate after login
- frame-ancestors clickjacking
- X-Frame-Options
- Content-Security-Policy frame ancestors
- 로그인 후 세션 재발급
symptoms:
- 로그인 성공 뒤 session id가 바뀌지 않아도 괜찮다고 생각하고 있어
- clickjacking을 XSS나 CSRF와 같은 층위로만 설명해서 frame 정책을 놓치고 있어
- CSP를 넣으면 XSS가 완전히 해결된다고 오해하고 있어
intents:
- comparison
- design
- deep_dive
prerequisites:
- security/authentication-vs-authorization
- security/xss-csrf-basics
- security/session-cookie-jwt-basics
next_docs:
- security/session-fixation-in-federated-login
- security/api-security-headers-beyond-csp
- security/open-redirect-hardening
- spring/security-architecture
linked_paths:
- contents/security/authentication-vs-authorization.md
- contents/security/xss-csrf-spring-security.md
- contents/network/http-state-session-cache.md
- contents/security/session-fixation-in-federated-login.md
- contents/security/open-redirect-hardening.md
- contents/security/browser-bff-token-boundary-session-translation.md
- contents/spring/spring-security-architecture.md
- contents/security/api-security-headers-beyond-csp.md
confusable_with:
- security/xss-csrf-basics
- security/api-security-headers-beyond-csp
- security/session-fixation-in-federated-login
forbidden_neighbors: []
expected_queries:
- session fixation과 clickjacking과 CSP는 각각 어떤 공격면을 막아?
- 로그인 성공 후 session id를 왜 rotate 해야 해?
- clickjacking은 X-Frame-Options와 CSP frame-ancestors로 어떻게 막아?
- CSP를 넣으면 XSS가 완전히 없어지는 게 아닌 이유는 뭐야?
- Spring Security에서 session fixation protection과 header policy를 같이 보는 이유는 뭐야?
contextual_chunk_prefix: |
  이 문서는 login hardening bridge로, session fixation은 post-login session id rotation, clickjacking은 frame embedding policy, CSP는 script/resource loading policy라는 서로 다른 방어층을 분리한다.
  session id rotate, frame-ancestors, X-Frame-Options, CSP unsafe-inline, Spring Security header/session 설정 같은 자연어 질문이 본 문서에 매핑된다.
---
# Session Fixation, Clickjacking, CSP

> 한 줄 요약: 세션 고정 공격, 클릭재킹, 콘텐츠 보안 정책은 서로 다른 층의 브라우저 공격을 막는다. 하나만 막아서는 충분하지 않다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [Session Fixation in Federated Login](./session-fixation-in-federated-login.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)

retrieval-anchor-keywords: session fixation, clickjacking, csp, frame ancestors, x-frame-options, login hardening, browser hardening, session regeneration, post-login hardening, login csrf, federated login session fixation, browser server boundary, security headers, frame policy, script policy, browser server boundary catalog, security readme browser server boundary

---

## 핵심 개념

### Session Fixation

세션 고정은 공격자가 미리 세션 ID를 정해두고, 피해자가 그 세션으로 로그인하도록 유도한 뒤 인증된 세션을 가로채는 공격이다.

### Clickjacking

클릭재킹은 투명한 iframe이나 UI 오버레이를 이용해 사용자가 의도하지 않은 클릭을 하게 만드는 공격이다.

### CSP

Content-Security-Policy는 브라우저가 어떤 스크립트/리소스를 허용할지 정하는 정책이다.

이 셋은 각각 다른 계층을 막는다.

- Session fixation: 세션 ID 재사용/승격 문제
- Clickjacking: UI 레이어 공격
- CSP: 스크립트/리소스 주입 제한

로그인 하드닝 관점에서는 이 셋을 따로 보지 않는다. callback 이후 세션 재발급, post-login redirect 검증, frame/script 정책이 이어져야 브라우저 경계가 닫힌다.

---

## 깊이 들어가기

### 1. Session fixation 방어

로그인 전과 후에 세션 ID를 재발급해야 한다.

- 로그인 성공 시 `session id rotate`
- 기존 세션 무효화
- 새 인증 컨텍스트로 재생성

이걸 하지 않으면 공격자가 미리 알고 있던 세션이 인증된 상태로 승격될 수 있다.

### 2. Clickjacking 방어

방어 헤더는 주로 둘이다.

- `X-Frame-Options`
- `Content-Security-Policy: frame-ancestors ...`

`X-Frame-Options`는 단순하고 넓게 지원되지만, CSP `frame-ancestors`가 더 유연하다.

### 3. CSP가 왜 중요한가

CSP는 XSS를 완전히 없애진 않지만, 스크립트 로딩 경로를 제한한다.

예를 들면:

- inline script 차단
- 허용된 CDN만 script 허용
- `object-src 'none'`
- `frame-ancestors 'none'`

`unsafe-inline`을 쉽게 넣으면 CSP의 방어 효과가 크게 떨어진다.

### 4. Spring Security와 연결

Spring Security는 세션 고정 방어, frame 옵션, CSP 헤더를 함께 다룰 수 있다.  
즉 애플리케이션 코드만이 아니라 보안 헤더와 세션 lifecycle까지 포함해야 한다.

---

## 실전 시나리오

### 시나리오 1: 로그인 후 세션 ID가 바뀌지 않음

원인:

- 세션 fixation protection이 꺼져 있음

해결:

- 로그인 시 세션 재발급
- 인증 전/후 세션 분리

### 시나리오 2: 관리자 버튼이 iframe 안에서 눌림

원인:

- clickjacking 방어 헤더가 없음

해결:

- `frame-ancestors`를 설정
- `X-Frame-Options`를 함께 고려

### 시나리오 3: CSP를 넣었는데도 XSS가 난다

원인:

- `unsafe-inline` 사용
- 허용 범위가 너무 넓음

해결:

- nonce 기반 정책
- 외부 스크립트 allowlist

### 시나리오 4: 보안 헤더를 적용했는데 일부 기능이 깨짐

원인:

- 외부 iframe, analytics, legacy inline script와 충돌

해결:

- 리소스별 allowlist
- 단계적 rollout

---

## 코드로 보기

### Spring Security 헤더 설정

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .sessionManagement(session -> session
                .sessionFixation(sessionFixation -> sessionFixation.migrateSession())
            )
            .headers(headers -> headers
                .frameOptions(frame -> frame.deny())
                .contentSecurityPolicy(csp -> csp
                    .policyDirectives("default-src 'self'; script-src 'self'; frame-ancestors 'none'")
                )
            )
            .build();
    }
}
```

### 응답 헤더 예시

```http
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; script-src 'self'; frame-ancestors 'none'
```

### 세션 재발급 의사코드

```text
on login success:
  invalidate old session
  create new session id
  copy authenticated context to new session
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 세션 재발급 | fixation 방어가 확실하다 | 구현을 빼먹기 쉽다 | 로그인 기반 앱 |
| `X-Frame-Options` | 단순하고 널리 지원된다 | 유연성이 낮다 | 기본 차단 |
| CSP `frame-ancestors` | 정교하게 제어할 수 있다 | 정책 설계가 어렵다 | 복잡한 프론트 |
| strict CSP | XSS 완화에 좋다 | 레거시가 깨질 수 있다 | 보안 우선 |
| loose CSP | 적용이 쉽다 | 방어력이 약하다 | 전환기 |

핵심 판단 기준은 **브라우저 공격을 헤더 정책으로 얼마나 강하게 억제할 것인가**다.

---

## 꼬리질문

> Q: session fixation과 CSRF는 같은 문제인가요?
> 의도: 세션 승격과 요청 위조를 구분하는지 본다.
> 핵심: 서로 다른 공격이다.

> Q: clickjacking은 왜 frame 관련 헤더로 막나요?
> 의도: UI 렌더링과 보안 경계를 이해하는지 확인한다.
> 핵심: 공격이 iframe 기반으로 이루어지기 때문이다.

> Q: CSP를 넣으면 XSS가 완전히 사라지나요?
> 의도: 방어층의 한계를 아는지 본다.
> 핵심: 완전 방어가 아니라 피해를 줄이는 정책이다.

## 한 줄 정리

Session fixation은 세션 재발급, clickjacking은 frame 차단, CSP는 스크립트/리소스 정책으로 막는다.
