---
schema_version: 3
title: XSS와 CSRF 기초
concept_id: security/xss-csrf-basics
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- xss-csrf-threat-separation
- script-execution-vs-forged-request
- csrf-token-samesite-basics
aliases:
- xss csrf basics
- XSS와 CSRF 기초
- xss csrf 차이
- xss가 뭔가요
- csrf란 무엇인가
- cross site scripting beginner
- cross site request forgery beginner
- csrf token 왜 써요
- HttpOnly cookie xss csrf
- Spring Security CSRF 403
- social login first post 403
symptoms:
- XSS와 CSRF를 둘 다 웹 보안 공격이라고만 알고 원인과 방어 방향을 섞어 이해하고 있어
- 쿠키 기반 인증에서 왜 CSRF token이나 SameSite가 필요한지 모르겠어
- Spring Security에서 POST가 403으로 막힐 때 CSRF 방어를 먼저 봐야 하는지 궁금해
intents:
- definition
- comparison
prerequisites:
- network/http-https-basics
- security/session-cookie-jwt-basics
next_docs:
- security/xss-csrf-spring-security
- security/csrf-in-spa-bff-architecture
- security/browser-storage-threat-model-for-tokens
- security/cors-samesite-preflight
linked_paths:
- contents/security/xss-csrf-spring-security.md
- contents/security/session-cookie-jwt-basics.md
- contents/security/oauth2-basics.md
- contents/security/oauth2-authorization-code-grant.md
- contents/security/csrf-in-spa-bff-architecture.md
- contents/security/browser-storage-threat-model-for-tokens.md
- contents/security/cors-samesite-preflight.md
- contents/spring/spring-mvc-request-lifecycle.md
confusable_with:
- security/browser-storage-threat-model-for-tokens
- security/csrf-in-spa-bff-architecture
- security/cors-samesite-preflight
- security/xss-csrf-spring-security
forbidden_neighbors: []
expected_queries:
- XSS와 CSRF 차이를 스크립트 실행과 인증 상태 도용 요청 기준으로 설명해줘
- XSS는 출력 이스케이프와 CSP로, CSRF는 token과 SameSite로 막는 이유가 뭐야?
- HttpOnly cookie는 XSS token 탈취를 줄이지만 왜 CSRF는 따로 봐야 해?
- Spring Security에서 CSRF 때문에 POST가 403이 나는 흐름을 초급자 관점으로 설명해줘
- social login callback 뒤 첫 POST가 403이면 OAuth와 CSRF 중 무엇을 이어 봐야 해?
contextual_chunk_prefix: |
  이 문서는 XSS를 malicious script execution 문제로, CSRF를 authenticated browser가 forged state-changing request를 보내는 문제로 분리해 설명하는 beginner primer다.
  XSS vs CSRF, output escaping, CSP, CSRF token, SameSite cookie, Spring Security CSRF 403, social login first POST 403 같은 자연어 질문이 본 문서에 매핑된다.
---
# XSS와 CSRF 기초

> 한 줄 요약: XSS는 "내 사이트에서 공격자 스크립트가 실행되는 문제"이고, CSRF는 "사용자의 인증 상태를 몰래 이용해 요청을 보내는 문제"다. 원인도 방어 방향도 다르다.

**난이도: 🟢 Beginner**

관련 문서:

- [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [OAuth2 기초](./oauth2-basics.md)
- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
- [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [[survey] Security README: 기본 primer](./README.md#기본-primer)
- [[catalog] Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)

retrieval-anchor-keywords: xss csrf basics, xss가 뭔가요, csrf란 무엇인가, xss csrf 차이, cross-site scripting beginner, cross-site request forgery beginner, 스크립트 삽입 공격, csrf token 왜 써요, xss 방어 방법, social login first post 403, callback 이후 csrf, bff login completion csrf, security readme xss csrf primer, security beginner route, return to security readme

## 이 문서 다음에 보면 좋은 문서

- `[return]` 다른 beginner primer를 다시 고르고 싶으면 [[survey] Security README: 기본 primer](./README.md#기본-primer)로 돌아간다.
- `[return]` 증상표에서 다음 갈래를 다시 고르고 싶으면 [[catalog] Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)로 돌아간다.
- `[next step]` `social login callback은 성공했는데 첫 POST가 403`이라면 [OAuth2 기초](./oauth2-basics.md) -> [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) -> [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md) 순서로 callback/login completion 흐름을 이어 본다.
- `[next step]` Spring Security 필터와 header 설정까지 이어 보려면 [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)를 본다.

## 핵심 개념

### XSS (Cross-Site Scripting)

XSS는 공격자가 웹 페이지에 **악의적인 스크립트를 삽입**하고, 다른 사용자의 브라우저에서 그 스크립트가 실행되도록 하는 공격이다.

핵심 문제: 서버가 사용자 입력을 그대로 HTML에 출력하면, 입력 안에 `<script>` 태그가 있을 때 브라우저가 그것을 코드로 실행한다.

### CSRF (Cross-Site Request Forgery)

CSRF는 로그인된 사용자가 악의적인 사이트를 방문했을 때, 그 사이트가 **사용자 모르게 사용자의 인증 쿠키를 이용해 API를 호출**하는 공격이다.

핵심 문제: 브라우저는 동일 도메인 쿠키를 요청마다 자동으로 첨부한다. 공격자 사이트가 `bank.com/transfer`로 요청을 보내도 쿠키가 따라간다.

## 한눈에 보기

| 구분 | XSS | CSRF |
|---|---|---|
| 무엇이 문제인가 | 공격 스크립트가 브라우저에서 실행됨 | 인증 쿠키를 몰래 사용해 요청이 전송됨 |
| 공격자가 원하는 것 | 세션 탈취, 키로깅, 피싱 | 사용자 대신 상태 변경 (송금, 삭제 등) |
| 피해 발생 위치 | 피해자의 브라우저 | 피해자의 계정/데이터 |
| 핵심 방어 | 출력 이스케이프, CSP | CSRF 토큰, SameSite 쿠키 |

## 상세 분해

### XSS의 두 가지 주요 유형

**저장형(Stored) XSS**: 공격자가 게시판 댓글 등에 `<script>악성코드</script>`를 저장하면, 다른 사용자가 그 페이지를 볼 때 스크립트가 실행된다.

**반사형(Reflected) XSS**: URL 파라미터의 값을 페이지에 그대로 출력할 때 발생한다. 공격 링크를 클릭한 사람만 피해를 입는다.

XSS로 탈취 가능한 것: HttpOnly가 없는 쿠키, localStorage 토큰, 화면에 보이는 민감 정보

### CSRF 공격 흐름

1. 사용자가 `bank.com`에 로그인한 상태다.
2. 공격자가 만든 `evil.com` 페이지를 방문한다.
3. `evil.com` 페이지가 브라우저에서 `bank.com/transfer?to=attacker&amount=100`을 자동 요청한다.
4. 브라우저가 `bank.com` 쿠키를 자동으로 첨부해 요청이 완성된다.

## 흔한 오해와 함정

### "HTTPS를 쓰면 XSS/CSRF가 막힌다"

HTTPS는 전송 암호화다. 브라우저 내에서 스크립트가 실행되거나 쿠키가 요청에 첨부되는 것은 HTTPS와 무관하다.

### "XSS는 입력할 때 막으면 된다"

입력 검증도 필요하지만 더 중요한 것은 **출력 시 이스케이프**다. HTML을 출력할 때 `<`를 `&lt;`로 변환하면 스크립트가 실행되지 않는다. 타임리프, JSP EL 등은 기본 이스케이프를 제공한다.

### "CSRF는 JSON API에서는 안 일어난다"

`Content-Type: application/json`은 단순 요청(simple request)이 아니므로 CORS preflight를 거치지만, `Content-Type: application/x-www-form-urlencoded`로 보내는 폼 요청은 CORS를 타지 않아 여전히 위험할 수 있다.

## 실무에서 쓰는 모습

Spring Security는 기본적으로 CSRF 방어가 활성화돼 있다. `POST` 요청에 CSRF 토큰이 없으면 거부한다.

- 브라우저 세션 방식: Thymeleaf 폼에 `_csrf` hidden 필드 자동 삽입
- REST API + JWT 방식: CSRF 방어를 끄는 경우가 많지만, 쿠키로 JWT를 전달한다면 `SameSite=Strict` 또는 `SameSite=Lax`와 함께 사용하는 것이 좋다.

XSS 방어는 템플릿 엔진의 기본 이스케이프를 신뢰하되, 직접 HTML을 concat 하는 코드는 피한다.

## 더 깊이 가려면

- Spring Security CSRF 필터와 XSS 헤더 심화: [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
- 세션과 쿠키가 왜 CSRF의 표적인지: [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)

## 면접/시니어 질문 미리보기

> Q: XSS와 CSRF의 차이를 설명해 보세요.
> 의도: 두 공격의 원리를 구분하는지 확인
> 핵심: XSS는 스크립트 실행, CSRF는 인증 상태 도용 요청. 방어 방향도 다르다.

> Q: Spring Security의 CSRF 방어는 어떻게 동작하나요?
> 의도: 토큰 기반 방어 원리를 이해하는지 확인
> 핵심: 서버가 발급한 토큰을 폼 또는 헤더로 함께 보내야 한다. 공격자는 이 토큰을 미리 알 수 없다.

## 한 줄 정리

XSS는 출력 이스케이프로, CSRF는 토큰·SameSite 쿠키로 막는다. 둘은 원인이 다르므로 방어 방향도 따로 챙겨야 한다.
