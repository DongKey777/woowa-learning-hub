---
schema_version: 3
title: Email Magic-Link Threat Model
concept_id: security/email-magic-link-threat-model
canonical: false
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- magic link
- email login
- one-time link
- email token
aliases:
- magic link
- email login
- one-time link
- email token
- replay
- referrer leak
- email forwarding
- prefetch
- phishing
- login link
- account recovery
- burn after read
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/security/password-reset-magic-link-public-origin-guide.md
- contents/security/password-reset-threat-modeling.md
- contents/security/oauth2-authorization-code-grant.md
- contents/security/pkce-failure-modes-recovery.md
- contents/security/browser-storage-threat-model-for-tokens.md
- contents/security/one-time-token-consumption-race-burn-after-read.md
- contents/security/open-redirect-hardening.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Email Magic-Link Threat Model 핵심 개념을 설명해줘
- magic link가 왜 필요한지 알려줘
- Email Magic-Link Threat Model 실무 설계 포인트는 뭐야?
- magic link에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Email Magic-Link Threat Model를 다루는 deep_dive 문서다. magic link는 비밀번호 대신 쓰는 편한 로그인 수단이지만, 이메일 계정 탈취, link forwarding, referrer leak, prefetch, replay를 함께 고려해야 한다. 검색 질의가 magic link, email login, one-time link, email token처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Email Magic-Link Threat Model

> 한 줄 요약: magic link는 비밀번호 대신 쓰는 편한 로그인 수단이지만, 이메일 계정 탈취, link forwarding, referrer leak, prefetch, replay를 함께 고려해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Password Reset, Magic Link, Public Origin Guide](./password-reset-magic-link-public-origin-guide.md)
> - [Password Reset Threat Modeling](./password-reset-threat-modeling.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [One-Time Token Consumption Race / Burn-After-Read](./one-time-token-consumption-race-burn-after-read.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)

retrieval-anchor-keywords: magic link, email login, one-time link, email token, replay, referrer leak, email forwarding, prefetch, phishing, login link, account recovery, burn after read, consume race

---

## 핵심 개념

magic link는 이메일로 받은 일회성 링크를 클릭해 로그인하는 방식이다.
비밀번호 입력이 줄어 UX가 좋지만, 링크 자체가 bearer credential처럼 동작할 수 있다.

위험:

- 이메일 계정이 탈취되면 바로 로그인된다
- 링크가 포워딩되거나 스크린샷/로그로 유출될 수 있다
- 브라우저 prefetch나 link scanner가 link를 먼저 방문할 수 있다
- replay되면 다시 로그인될 수 있다

즉 magic link는 로그인 편의 기능이 아니라, 짧은 수명의 일회성 토큰을 이메일로 전달하는 보안 플로우다.

---

## 깊이 들어가기

### 1. magic link는 사실상 로그인 토큰이다

링크 안의 토큰은:

- 짧은 TTL
- one-time use
- 특정 device나 browser context에 묶임

이어야 한다.

### 2. 이메일 계정은 약한 고리다

magic link는 종종 email ownership을 인증 근거로 삼는다.

문제:

- email account takeover
- shared inbox
- forwarding rule 악용
- mailbox compromise

고위험 계정에는 추가 step-up이 필요하다.

### 3. prefetch와 scanner를 고려해야 한다

이메일 클라이언트나 보안 제품이 링크를 미리 열 수 있다.

- 실제 사용자 클릭 전 토큰이 consume될 수 있다
- scanner가 로그인 이벤트를 발생시킬 수 있다

그래서 링크 consume는 브라우저 context와 사용자 interaction을 함께 봐야 한다.

### 4. redirect와 return URL도 위험하다

magic link 이후에 redirect를 허용하면 open redirect 문제가 연결될 수 있다.

- 로그인 후 외부로 튈 수 있다
- code/token leak가 생길 수 있다

### 5. magic link는 reset과 매우 비슷하다

비밀번호 reset과 같은 경계를 가진다.

- 토큰은 짧아야 한다
- 클릭하면 즉시 폐기돼야 한다
- 성공 후 세션을 재평가해야 한다

---

## 실전 시나리오

### 시나리오 1: 이메일 포워딩으로 타인이 로그인함

대응:

- one-time token을 짧게 둔다
- device fingerprint보다는 step-up auth를 검토한다
- 이메일 변경 직후 magic link를 더 엄격하게 본다

### 시나리오 2: security scanner가 링크를 먼저 클릭함

대응:

- prefetch-safe flow를 설계한다
- 실제 사용자 interaction을 요구한다
- token consume을 두 단계로 나눈다

### 시나리오 3: magic link가 외부 redirect와 결합됨

대응:

- redirect destination을 서버에서 결정한다
- exact allowlist를 쓴다
- query에 민감 값을 남기지 않는다

---

## 코드로 보기

### 1. one-time login token

```java
public void sendMagicLink(String email) {
    String token = tokenService.issueOneTimeLoginToken(email);
    mailer.send(email, magicLinkUrl(token));
}
```

### 2. consume on click

```java
public LoginResult consume(String token) {
    MagicLinkLink link = tokenStore.consume(token);
    sessionService.issue(link.userId());
    return LoginResult.success();
}
```

### 3. prefetch-aware defense

```text
1. token은 one-time and short-lived로 만든다
2. 클릭 전에 scanner가 consume하지 않게 설계한다
3. 성공 후 세션과 refresh 상태를 재평가한다
4. redirect는 exact allowlist만 허용한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| magic link only | UX가 좋다 | email compromise에 취약하다 | 낮은 위험 |
| magic link + step-up | 더 안전하다 | 흐름이 복잡하다 | 중간/고위험 |
| password + magic link fallback | 현실적이다 | 공격면이 넓다 | 대중 서비스 |
| scanner-tolerant flow | 운영이 쉽다 | 구현이 필요하다 | enterprise email |

판단 기준은 이렇다.

- email 계정이 충분히 안전한가
- 링크가 prefetch/scanner에 노출되는가
- one-time 사용을 강제할 수 있는가
- login 후 세션 재평가가 필요한가

---

## 꼬리질문

> Q: magic link가 왜 위험할 수 있나요?
> 의도: bearer-style login token의 위험을 이해하는지 확인
> 핵심: 이메일 계정 탈취나 링크 유출로 바로 로그인될 수 있기 때문이다.

> Q: prefetch가 왜 문제인가요?
> 의도: scanner/prefetch consume 위험을 아는지 확인
> 핵심: 사용자보다 먼저 링크가 소비될 수 있기 때문이다.

> Q: magic link와 password reset은 어떻게 다른가요?
> 의도: 두 플로우의 공통 위험을 이해하는지 확인
> 핵심: 둘 다 일회성 bearer token을 쓰는 고위험 플로우다.

> Q: redirect를 왜 조심해야 하나요?
> 의도: login 후 open redirect 연결을 아는지 확인
> 핵심: 민감한 상태 전환 후 외부로 튀는 사고를 막기 위해서다.

## 한 줄 정리

email magic link는 편리한 로그인 수단이지만, 이메일 신뢰와 일회성 토큰 소비를 함께 엄격히 관리해야 한다.
