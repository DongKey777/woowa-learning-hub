---
schema_version: 3
title: HTTPS / HSTS / MITM
concept_id: security/https-hsts-mitm
canonical: false
category: security
difficulty: intermediate
doc_role: deep_dive
level: intermediate
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- https
- hsts
- mitm
- certificate validation
aliases:
- https
- hsts
- mitm
- certificate validation
- tls termination
- downgrade attack
- mixed content
- secure cookie
- x-forwarded-proto
- certificate pinning
- trust store
- browser hardening
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
- contents/security/authentication-vs-authorization.md
- contents/security/xss-csrf-spring-security.md
- contents/security/cors-credential-pitfalls-allowlist.md
- contents/security/csp-nonces-vs-hashes-script-policy.md
- contents/security/csp-report-only-rollout-violation-feedback.md
- contents/security/open-redirect-hardening.md
- contents/security/signed-cookies-server-sessions-jwt-tradeoffs.md
- contents/security/browser-storage-threat-model-for-tokens.md
- contents/security/oauth2-authorization-code-grant.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- HTTPS / HSTS / MITM 핵심 개념을 설명해줘
- https가 왜 필요한지 알려줘
- HTTPS / HSTS / MITM 실무 설계 포인트는 뭐야?
- https에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 HTTPS / HSTS / MITM를 다루는 deep_dive 문서다. HTTPS는 전송 구간의 기밀성과 무결성을 지키지만, 인증서 검증이 깨지면 MITM은 여전히 가능하다. HSTS는 다운그레이드와 습관적 HTTP 접속을 줄이는 방어선이다. 검색 질의가 https, hsts, mitm, certificate validation처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# HTTPS / HSTS / MITM

> 한 줄 요약: HTTPS는 전송 구간의 기밀성과 무결성을 지키지만, 인증서 검증이 깨지면 MITM은 여전히 가능하다. HSTS는 다운그레이드와 습관적 HTTP 접속을 줄이는 방어선이다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 관련 문서:
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [CORS Credential Pitfalls / Allowlist Design](./cors-credential-pitfalls-allowlist.md)
> - [CSP Nonces / Hashes / Script Policy](./csp-nonces-vs-hashes-script-policy.md)
> - [CSP Report-Only Rollout / Violation Feedback](./csp-report-only-rollout-violation-feedback.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](./signed-cookies-server-sessions-jwt-tradeoffs.md)
> - [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [HTTPS와 TLS 기초](./https-tls-beginner.md)
> - [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: https, hsts, mitm, certificate validation, tls termination, downgrade attack, mixed content, secure cookie, x-forwarded-proto, certificate pinning, trust store, browser hardening, https beginner primer, hsts beginner handoff, return to security readme

---

## 처음 읽는다면

- HTTPS/TLS 자체가 아직 낯설면 이 문서보다 먼저 [HTTPS와 TLS 기초](./https-tls-beginner.md)에서 "암호화된 전송"과 "인증서 검증" mental model을 잡는 편이 안전하다.
- 다른 입문 문서로 돌아가고 싶으면 [Security README 기본 primer 묶음](./README.md#기본-primer)으로 복귀하면 된다.

---

## 핵심 개념

HTTPS는 HTTP 위에 TLS를 얹은 것이다.
주요 목표는 다음 세 가지다.

- 기밀성: 중간에서 내용을 읽지 못하게 한다
- 무결성: 중간에서 내용을 바꾸지 못하게 한다
- 인증: 상대 서버가 진짜 그 도메인 소유자인지 확인한다

하지만 HTTPS가 있다고 해서 자동으로 완벽해지는 것은 아니다.

- 인증서 검증을 무시하면 MITM이 가능하다
- 다운그레이드 공격이 가능하다
- mixed content나 잘못된 proxy 설정이 사고를 만든다

운영에서 더 자주 터지는 문제는 이것이다.

- 프록시 뒤에서 앱이 HTTPS를 HTTP로 오해한다
- secure cookie가 누락된다
- mixed content 때문에 일부 브라우저만 깨진다
- 테스트 환경에서 permissive TLS 예외가 운영에 남는다
- `http://` 링크나 캐시된 링크가 습관처럼 돌아다닌다

---

## 깊이 들어가기

### 1. MITM이 가능한 경로

대표적인 경로:

- 루트 CA를 잘못 신뢰함
- self-signed certificate를 검증 없이 허용함
- 프록시/앱에서 인증서 검증을 끔
- 공용 Wi-Fi, 악성 AP, DNS 변조

### 2. HSTS

HSTS는 브라우저에게 "이 도메인은 무조건 HTTPS로만 접근하라"고 알려주는 정책이다.

효과:

- 첫 접속 이후 HTTP 다운그레이드를 막는다
- 습관적 `http://` 접근을 줄인다
- cookie `Secure` 정책과 함께 쓰면 안전성이 올라간다

운영 팁:

- preload는 강력하지만 되돌리기 어렵다
- 서브도메인까지 포함할지 먼저 결정한다
- staging과 production을 같은 정책으로 묶지 않는다
- HSTS를 켠 뒤에도 certificate renewal 경보를 둔다

### 3. TLS termination

로드밸런서나 reverse proxy에서 TLS를 종료하는 경우가 많다.
이때는 내부 구간도 믿는지, 끝까지 암호화할지 판단해야 한다.

- 외부 노출 구간은 HTTPS
- 내부 마이크로서비스 구간은 mTLS를 검토
- `X-Forwarded-Proto`를 잘못 다루면 secure cookie/redirect가 꼬인다

이 구간에서 생기는 사고:

- 로그인 callback이 `http`로 리다이렉트된다
- `Secure` cookie가 전송되지 않는다
- Origin/Referer 검증이 어긋난다
- CORS와 CSRF 정책이 꼬인다

프록시 뒤 HTTPS 인식은 [CORS Credential Pitfalls / Allowlist Design](./cors-credential-pitfalls-allowlist.md)와 [Signed Cookies / Server Sessions / JWT Tradeoffs](./signed-cookies-server-sessions-jwt-tradeoffs.md)에서도 연결해서 보면 좋다.

### 4. certificate pinning

핀닝은 특정 인증서/공개키를 더 강하게 신뢰하는 방식이다.

- 장점: MITM 방어가 강해진다
- 단점: 인증서 교체/회전이 까다롭다

운영 복잡도가 올라가므로 모든 서비스에 무조건 넣는 건 아니다.

모바일/고위험 클라이언트에서는 고려할 수 있지만, 웹 서비스는 보통 HSTS와 신뢰할 수 있는 CA 체인, 그리고 엄격한 cert validation으로 충분한지 먼저 본다.

### 5. mixed content와 referer leak

HTTPS 페이지 안에서 HTTP 리소스를 불러오면 mixed content가 된다.

- active mixed content는 특히 위험하다
- redirect 후 URL에 민감 값이 남으면 Referer로 새어 나갈 수 있다
- 인증 code나 reset token이 query에 남지 않게 해야 한다

그래서 [Open Redirect Hardening](./open-redirect-hardening.md)과 같이 보면 더 낫다.

## 깊이 들어가기 (계속 2)

---

## 실전 시나리오

### 시나리오 1: HTTP 링크를 눌러 로그인 페이지로 들어감

다운그레이드된 HTTP로 가면 초기 요청이 노출될 수 있다.
HSTS는 이런 습관적 HTTP 접근을 줄이는 데 유용하다.

### 시나리오 2: 프록시 뒤에서 secure cookie가 누락됨

원인:

- TLS는 LB에서 종료됐는데 앱이 요청을 HTTP로 오해한다
- `X-Forwarded-Proto` 설정이 누락됐다

결과:

- redirect loop
- secure cookie 미전달
- 로그인 세션 불안정

### 시나리오 3: self-signed cert를 운영 환경에서 허용함

개발 편의를 위해 예외를 넣었다가 운영에 남는 경우가 있다.
이건 사실상 MITM 방어를 포기하는 것이다.

### 시나리오 4: 브라우저는 HTTPS인데 내부 API는 평문

외부는 안전해 보여도 내부망 트래픽이 평문이면 전체 위협 모델이 약해진다.
최소한 민감 경로는 내부도 암호화를 고려해야 한다.

---

## 코드로 보기

### 1. Spring Security에서 HTTPS 강제

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .requiresChannel(channel -> channel.anyRequest().requiresSecure())
            .headers(headers -> headers
                .httpStrictTransportSecurity(hsts -> hsts
                    .includeSubDomains(true)
                    .preload(true)
                )
            )
            .build();
    }
}
```

### 2. 운영에서 자주 보는 헤더

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### 3. 프록시 뒤의 HTTPS 인식

```properties
server.forward-headers-strategy=framework
```

이 설정이 없으면 secure redirect나 cookie 판단이 꼬일 수 있다.

### 4. mixed content / redirect hygiene

```text
1. HTTP 링크를 HTTPS로 강제한다
2. 인증 code, reset token, session token을 URL에 넣지 않는다
3. referrer policy를 보수적으로 둔다
4. open redirect를 제거한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| HTTPS only | 기본 전송 보안이 확보된다 | 인증서 운영이 필요하다 | 거의 항상 |
| HSTS | 다운그레이드 방어가 된다 | 잘못 걸면 복구가 번거롭다 | 운영 도메인 |
| certificate pinning | MITM 방어가 강하다 | 인증서 교체가 어렵다 | 모바일 앱 등 일부 환경 |
| TLS termination at LB | 운영이 단순해진다 | 내부 구간 신뢰 모델을 따로 봐야 한다 | 일반적인 서비스 |
| end-to-end TLS | 내부까지 더 강하게 보호된다 | 운영이 복잡해진다 | 민감 데이터 경로 |

핵심 판단 기준은 다음이다.

- 중간자 공격을 어느 지점까지 막아야 하는가
- 인증서와 프록시 운영 부담을 감당할 수 있는가
- 브라우저/모바일/서버 중 어디가 주 고객인지
- HSTS preload를 운영할 준비가 되었는가
- mixed content와 referrer leak을 함께 막고 있는가

---

## 꼬리질문

> Q: HTTPS만 있으면 MITM이 완전히 불가능한가?
> 의도: 인증서 검증과 경로 신뢰를 분리해서 보는지 확인
> 핵심: 인증서 검증이 깨지면 MITM은 가능하다.

> Q: HSTS와 redirect to HTTPS는 뭐가 다른가?
> 의도: 브라우저 정책과 서버 리다이렉트의 차이를 이해하는지 확인
> 핵심: HSTS는 브라우저에 HTTPS 강제 정책을 기억시킨다.

> Q: TLS termination을 LB에서 할 때 조심할 점은?
> 의도: 프록시 뒤 secure cookie와 scheme 인식 문제를 아는지 확인
> 핵심: `X-Forwarded-Proto`, secure cookie, 내부 구간 신뢰 모델이다.

## 한 줄 정리

HTTPS는 전송 보안의 기본이고, HSTS는 다운그레이드를 막는 추가 방어선이며, 프록시와 인증서 검증이 틀리면 MITM은 여전히 가능하다.
