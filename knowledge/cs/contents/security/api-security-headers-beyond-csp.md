---
schema_version: 3
title: API Security Headers Beyond CSP
concept_id: security/api-security-headers-beyond-csp
canonical: true
category: security
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- browser-hardening-headers
- api-sensitive-response-cache-control
- csp-is-not-enough
aliases:
- API security headers beyond CSP
- security headers beyond csp
- HSTS Referrer-Policy Permissions-Policy
- COOP COEP CORP
- X-Content-Type-Options nosniff
- Cache-Control security header
- 브라우저 보안 헤더 묶음
symptoms:
- CSP만 설정하면 브라우저 보안 헤더가 충분하다고 생각하고 있어
- OAuth callback이나 API 응답의 민감 정보가 referrer나 cache에 남을 수 있다는 감각이 약해
- HSTS, Referrer-Policy, Permissions-Policy, COOP, COEP, CORP가 각각 무엇을 줄이는지 헷갈려
intents:
- deep_dive
- design
prerequisites:
- security/xss-csrf-basics
- security/cors-basics
- security/browser-storage-threat-model-for-tokens
next_docs:
- security/csp-nonces-vs-hashes-script-policy
- security/csp-report-only-rollout-violation-feedback
- security/https-hsts-mitm
- security/cors-credential-pitfalls-allowlist
linked_paths:
- contents/security/csp-nonces-vs-hashes-script-policy.md
- contents/security/csp-report-only-rollout-violation-feedback.md
- contents/security/https-hsts-mitm.md
- contents/security/cors-credential-pitfalls-allowlist.md
- contents/security/session-fixation-clickjacking-csp.md
- contents/network/http-caching-conditional-request-basics.md
confusable_with:
- security/xss-csrf-basics
- security/session-fixation-clickjacking-csp
- security/browser-storage-threat-model-for-tokens
forbidden_neighbors: []
expected_queries:
- CSP 말고 API와 브라우저 경계에서 어떤 보안 헤더를 같이 봐야 해?
- Referrer-Policy는 OAuth callback이나 민감 URL 누출을 어떻게 줄여?
- HSTS와 X-Content-Type-Options, Permissions-Policy는 각각 어떤 공격면을 줄여?
- 민감 API 응답에 Cache-Control no-store를 보안 관점에서 왜 써?
- COOP, COEP, CORP는 CSP와 어떤 역할이 달라?
contextual_chunk_prefix: |
  이 문서는 CSP 이후의 browser/API hardening header deep dive로, HSTS, Referrer-Policy, Permissions-Policy, COOP/COEP/CORP, X-Content-Type-Options, Cache-Control을 공격면별로 묶는다.
  CSP만으로 충분한지, 민감 API no-store, referrer leak, nosniff, cross-origin isolation header 같은 자연어 질문이 본 문서에 매핑된다.
---
# API Security Headers Beyond CSP

> 한 줄 요약: API와 브라우저 경계에서는 CSP만으로 부족하고, HSTS, Referrer-Policy, Permissions-Policy, COOP/COEP/CORP, X-Content-Type-Options 같은 헤더를 목적에 맞게 조합해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CSP Nonces / Hashes / Script Policy](./csp-nonces-vs-hashes-script-policy.md)
> - [CSP Report-Only Rollout / Violation Feedback](./csp-report-only-rollout-violation-feedback.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
> - [CORS Credential Pitfalls / Allowlist Design](./cors-credential-pitfalls-allowlist.md)
> - [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)

retrieval-anchor-keywords: security headers, HSTS, Referrer-Policy, Permissions-Policy, COOP, COEP, CORP, X-Content-Type-Options, cache-control, browser hardening

---

## 핵심 개념

CSP는 중요한 한 조각이지만, 브라우저와 API를 안전하게 하려면 헤더 묶음으로 생각해야 한다.

자주 쓰는 헤더:

- `Strict-Transport-Security`
- `Referrer-Policy`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy`
- `Cross-Origin-Embedder-Policy`
- `Cross-Origin-Resource-Policy`
- `X-Content-Type-Options`
- `Cache-Control`

각 헤더는 다른 공격면을 줄인다.

---

## 깊이 들어가기

### 1. HSTS

HSTS는 HTTPS 강제를 돕는다.

- downgrade를 줄인다
- 첫 요청 이후 HTTPS를 강제한다
- MITM 위험을 낮춘다

### 2. Referrer-Policy

리퍼러에 민감한 URL이 섞이지 않게 한다.

- 토큰이나 code가 query에 있으면 leak 가능
- 외부 링크로 이동할 때 출처 노출을 줄인다

### 3. Permissions-Policy

브라우저 기능 접근을 제한한다.

- camera
- microphone
- geolocation
- payment

필요 없는 기능은 끈다.

### 4. COOP/COEP/CORP

이 세 헤더는 cross-origin isolation과 resource 보호에 도움을 준다.

- window 간 분리
- shared memory 같은 고급 기능 제어
- resource embedding control

### 5. X-Content-Type-Options

`nosniff`를 통해 MIME sniffing을 줄인다.

- script로 잘못 해석되는 위험 감소
- downloadable content 보안 향상

### 6. Cache-Control

민감 응답은 캐시하면 안 된다.

- `no-store`
- `private`
- `max-age` 제한

API response에 token이나 PII가 있으면 특히 중요하다.

---

## 실전 시나리오

### 시나리오 1: OAuth callback URL에 민감 파라미터가 남음

대응:

- Referrer-Policy를 강화한다
- query에 민감 값을 남기지 않는다
- callback 이후 URL을 정리한다

### 시나리오 2: 브라우저 기능이 필요 없는데 열려 있음

대응:

- Permissions-Policy로 제한한다
- 필요한 origin만 allow한다

### 시나리오 3: API response가 캐시에 남음

대응:

- Cache-Control을 `no-store`로 둔다
- 민감 response는 shared cache를 피한다

---

## 코드로 보기

### 1. security header set 개념

```java
public void addSecurityHeaders(HttpServletResponse response) {
    response.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
    response.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
    response.setHeader("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
    response.setHeader("X-Content-Type-Options", "nosniff");
}
```

### 2. API cache control

```java
public void cacheSensitiveResponse(HttpServletResponse response) {
    response.setHeader("Cache-Control", "no-store");
    response.setHeader("Pragma", "no-cache");
}
```

### 3. cross-origin isolation hints

```text
1. CSP만으로 끝내지 않는다
2. HSTS와 Referrer-Policy를 같이 본다
3. Permissions-Policy로 불필요한 기능을 끈다
4. 민감 API는 Cache-Control을 강하게 둔다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| minimal headers | 쉽다 | 방어가 약하다 | 낮은 위험 |
| full browser hardening | 강하다 | 설정과 테스트가 필요하다 | public web app |
| strict cache control | 민감 정보 보호에 좋다 | 성능 캐시 이득이 줄 수 있다 | auth/API 응답 |
| permissive policies | 호환성이 좋다 | 공격면이 넓다 | 피해야 함 |

판단 기준은 이렇다.

- 브라우저에서 민감한 정보를 다루는가
- 외부 origin과 상호작용하는가
- 기능 제한을 걸어도 UX가 유지되는가
- 캐시와 리퍼러 노출을 줄여야 하는가

---

## 꼬리질문

> Q: CSP 외에 어떤 헤더가 중요한가요?
> 의도: 브라우저 하드닝의 폭을 아는지 확인
> 핵심: HSTS, Referrer-Policy, Permissions-Policy, COOP/COEP/CORP, nosniff다.

> Q: Referrer-Policy가 왜 중요한가요?
> 의도: URL 민감 정보 leak를 아는지 확인
> 핵심: query나 path의 민감 값이 외부로 새는 것을 줄인다.

> Q: Cache-Control은 왜 보안 헤더인가요?
> 의도: 캐시가 데이터 노출 면적이 될 수 있음을 아는지 확인
> 핵심: 민감 응답이 남지 않도록 하기 때문이다.

> Q: Permissions-Policy는 무엇을 막나요?
> 의도: 브라우저 기능 접근을 아는지 확인
> 핵심: camera, mic, geo 같은 기능 남용을 막는다.

## 한 줄 정리

API와 브라우저 하드닝은 CSP만이 아니라 HSTS, Referrer-Policy, Permissions-Policy, COOP/COEP/CORP, Cache-Control을 함께 설계해야 한다.
