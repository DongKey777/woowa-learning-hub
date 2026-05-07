---
schema_version: 3
title: Backend Cookie CORS Auth Debug Drill
concept_id: security/backend-cookie-cors-auth-debug-drill
canonical: false
category: security
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/spring-roomescape
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- cookie
- cors
- auth-debug
- devtools-network
aliases:
- backend cookie cors auth debug drill
- cookie cors login loop drill
- DevTools cookie auth drill
- CORS cookie 401 403 drill
- 쿠키 CORS 인증 디버깅 드릴
symptoms:
- cookie가 있는데도 API가 anonymous로 보일 때 저장, 전송, 서버 복원 단계를 나누지 못한다
- CORS 에러와 401/403 auth failure를 같은 문제로 처리한다
- Application 탭 cookie만 보고 request Cookie header를 확인하지 않는다
intents:
- drill
- troubleshooting
- comparison
prerequisites:
- security/cookie-failure-three-way-splitter
- security/cors-basics
next_docs:
- network/application-tab-vs-request-cookie-header-mini-card
- network/api-gateway-auth-failure-surface-map
- security/authentication-authorization-session-foundations
linked_paths:
- contents/security/cookie-failure-three-way-splitter.md
- contents/security/cors-basics.md
- contents/network/application-tab-vs-request-cookie-header-mini-card.md
- contents/network/api-gateway-auth-failure-surface-map.md
- contents/security/authentication-authorization-session-foundations.md
- contents/security/browser-direct-call-vs-server-proxy-decision-tree.md
confusable_with:
- security/cookie-failure-three-way-splitter
- security/cors-basics
- network/api-gateway-auth-failure-surface-map
forbidden_neighbors:
- contents/security/jwt-deep-dive.md
expected_queries:
- cookie CORS auth 문제를 DevTools로 드릴하고 싶어
- Application에는 쿠키가 있는데 요청에는 안 붙는 문제를 연습해줘
- CORS 에러와 401 403을 어떻게 먼저 분리해야 해?
- login loop가 저장 차단인지 전송 누락인지 서버 익명 처리인지 문제로 풀어줘
- spring-roomescape 인증 디버깅을 cookie request header 기준으로 연습하고 싶어
contextual_chunk_prefix: |
  이 문서는 backend cookie CORS auth debug drill이다. Set-Cookie blocked,
  stored not sent, request Cookie header empty, server anonymous, CORS
  preflight, 401/403, login loop 같은 미션 증상을 DevTools 판별 문제로
  매핑한다.
---
# Backend Cookie CORS Auth Debug Drill

> 한 줄 요약: cookie/auth 문제는 `저장됐나 -> 요청에 붙었나 -> 서버가 세션/principal로 복원했나` 세 칸으로 먼저 자른다.

**난이도: Beginner**

## 문제 1

상황:

```text
로그인 응답에는 Set-Cookie가 있지만 Application 탭에는 저장되지 않는다.
```

답:

저장 차단 단계다. SameSite=None+Secure, Domain/Path, blocked reason, HTTPS 여부를 먼저 본다.
아직 request Cookie header나 서버 세션 복원을 볼 단계가 아니다.

## 문제 2

상황:

```text
Application 탭에는 session cookie가 있는데 API 요청의 Cookie header가 비어 있다.
```

답:

저장 후 미전송 단계다. fetch credentials, SameSite, Domain, Path, Secure 조건을 Network 요청 기준으로 확인한다.
cookie가 보인다는 사실만으로 전송됐다고 보면 안 된다.

## 문제 3

상황:

```text
request Cookie header에는 session이 있는데 서버 응답은 401 또는 anonymous다.
```

답:

서버 복원 단계다. session store, principal hydration, gateway/app auth failure surface를 본다.
CORS 설정만 계속 바꾸면 원인이 흐려진다.

## 빠른 체크

| 관찰 | 분기 |
|---|---|
| Set-Cookie blocked | 저장 차단 |
| Application에는 있음, request header 없음 | 저장 후 미전송 |
| request header 있음, 서버는 anonymous | 서버 복원 실패 |
| OPTIONS에서 멈춤 | preflight/CORS 응답 먼저 |
