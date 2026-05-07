---
schema_version: 3
title: '로그인 후에도 API가 anonymous — Cookie / CORS / SameSite / 서버 세션 분기'
concept_id: security/cookie-cors-auth-anonymous-symptom-router
canonical: false
category: security
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: mixed
source_priority: 86
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
review_feedback_tags:
- cookie-not-sent
- cors-credentials
- server-session-restore
- anonymous-after-login
aliases:
- 로그인 후 anonymous
- cookie cors anonymous
- Set-Cookie 됐는데 API 익명
- 쿠키 있는데 인증 안 됨
- CORS credentials cookie auth
- SameSite cookie login loop
symptoms:
- 로그인 응답에는 Set-Cookie가 보이는데 다음 API 요청에서 서버가 anonymous로 본다
- Application 탭에는 쿠키가 있는데 Request Cookie 헤더에는 값이 없다
- Request Cookie 헤더는 있는데 Spring Security나 서버 세션 복원이 실패한다
intents:
- symptom
- troubleshooting
prerequisites:
- security/cookie-failure-three-way-splitter
- security/session-cookie-jwt-basics
next_docs:
- security/cookie-rejection-reason-primer
- security/fetch-credentials-vs-cookie-scope
- security/cors-samesite-preflight
linked_paths:
- contents/security/cookie-failure-three-way-splitter.md
- contents/security/cookie-rejection-reason-primer.md
- contents/security/fetch-credentials-vs-cookie-scope.md
- contents/security/cors-samesite-preflight.md
- contents/security/session-cookie-jwt-basics.md
- contents/security/auth-failure-response-401-403-404.md
- contents/spring/spring-api-401-vs-browser-302-beginner-bridge.md
- contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md
confusable_with:
- security/cookie-failure-three-way-splitter
- security/fetch-credentials-vs-cookie-scope
- security/cors-samesite-preflight
forbidden_neighbors:
- contents/security/jwt-deep-dive.md
expected_queries:
- 로그인은 성공했는데 API에서는 anonymous로 보이면 어디부터 봐?
- Set-Cookie는 내려왔는데 다음 요청 Cookie 헤더가 비어 있으면 원인이 뭐야?
- 쿠키는 있는데 Spring Security가 인증 사용자를 못 찾는 이유를 분기해줘
- CORS credentials랑 SameSite 때문에 로그인 세션이 안 붙을 때 어떻게 확인해?
contextual_chunk_prefix: |
  이 문서는 로그인 직후 API가 anonymous로 보이는 증상을 cookie 저장,
  cookie 전송, 서버 세션/인증 복원 세 단계로 나누는 security symptom_router다.
  Set-Cookie는 있는데 Request Cookie가 없음, Application에는 쿠키가 있음,
  credentials include 누락, SameSite/Secure 문제, 서버가 anonymous로 봄 같은
  질의를 cookie/CORS/session 경계 진단으로 연결한다.
---
# 로그인 후에도 API가 anonymous — Cookie / CORS / SameSite / 서버 세션 분기

> 한 줄 요약: "로그인은 됐는데 API가 anonymous"는 보통 쿠키가 저장되지 않았거나, 저장됐지만 전송되지 않았거나, 전송됐지만 서버가 세션/인증으로 복원하지 못한 문제다. 이 세 단계를 먼저 분리해야 CORS, SameSite, Spring Security 설정을 헛돌지 않는다.

**난이도: 🟡 Intermediate**

## 1분 분기

### 1. `Set-Cookie`가 브라우저에 저장되지 않는다

증상:

- Network 응답에는 `Set-Cookie`가 보인다.
- DevTools가 blocked reason을 표시한다.
- Application 탭에는 쿠키가 없다.

먼저 볼 것:

- `SameSite=None`이면 `Secure`가 같이 있는가
- domain/path가 현재 origin과 맞는가
- HTTPS가 아닌 로컬 환경에서 `Secure`를 강제하지 않았는가

이 갈래는 [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)로 내려간다.

### 2. 저장은 됐지만 다음 요청에 안 붙는다

증상:

- Application 탭에는 쿠키가 있다.
- API 요청의 `Cookie` 헤더가 비어 있다.
- 프론트 코드가 `fetch`나 axios로 cross-origin 요청을 보낸다.

먼저 볼 것:

- `fetch(..., { credentials: "include" })` 또는 axios `withCredentials`가 있는가
- 서버가 `Access-Control-Allow-Credentials: true`를 보냈는가
- `Access-Control-Allow-Origin: *`와 credentials를 같이 쓰고 있지 않은가
- cookie `SameSite`가 cross-site 전송을 막고 있지 않은가

이 갈래는 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)와 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)로 이어진다.

### 3. 요청에는 붙었지만 서버가 anonymous로 본다

증상:

- Request `Cookie` 헤더에는 세션 쿠키가 있다.
- 서버 로그에서는 anonymous이거나 새 세션으로 보인다.
- 로그인 직후 `302` 루프나 `401/403`이 반복된다.

먼저 볼 것:

- 서버 세션 저장소가 같은 인스턴스/Redis를 보고 있는가
- `SessionCreationPolicy.STATELESS`로 세션 복원을 꺼두지 않았는가
- proxy가 cookie header를 제거하거나 domain/path를 바꾸지 않았는가
- Spring Security filter chain에서 인증 복원 필터가 해당 경로에 적용되는가

이 갈래는 [Session Cookie vs JWT Basics](./session-cookie-jwt-basics.md)와 Spring Security 세션 문서로 내려간다.

## 흔한 오해

`Set-Cookie`가 보이면 인증이 끝났다고 생각하기 쉽다. 하지만 인증 세션은 세 단계가 모두 맞아야 한다.

- 저장
- 전송
- 서버 복원

어느 단계에서 끊겼는지 모르면 CORS만 계속 바꾸거나 JWT 설정을 건드리며 시간을 낭비한다.

## 꼬리질문

> Q: Application 탭에는 쿠키가 있는데 request에 안 붙으면 서버 문제인가요?
> 핵심: 우선 브라우저 전송 조건 문제다. credentials, SameSite, domain/path부터 확인한다.

> Q: Cookie 헤더가 있는데도 anonymous면 어디가 문제인가요?
> 핵심: 서버가 쿠키 값을 세션/인증 객체로 복원하는 단계가 깨졌는지 본다.

## 한 줄 정리

로그인 후 anonymous 문제는 `Set-Cookie 저장 -> 다음 요청 전송 -> 서버 인증 복원` 세 칸으로 자르면 가장 빨리 좁혀진다.
