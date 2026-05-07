---
schema_version: 3
title: Backend Browser Session Auth Mission Bridge
concept_id: security/backend-browser-session-auth-mission-bridge
canonical: false
category: security
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 78
mission_ids:
- missions/spring-roomescape
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- browser-session
- cookie
- cors
- auth-failure
aliases:
- backend browser session auth bridge
- cookie cors auth mission bridge
- browser session login loop bridge
- Spring session auth debug bridge
- 쿠키 CORS 인증 브리지
symptoms:
- 로그인은 성공한 것 같은데 다음 API가 401, 403, login HTML 200으로 보인다
- cookie가 저장됐는지 전송됐는지 서버가 복원했는지 한 번에 섞어 디버깅한다
- CORS 설정을 바꾸면 인증 문제가 해결될 것처럼 보고 principal/session 경계를 놓친다
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- security/authentication-authorization-session-foundations
- security/cookie-failure-three-way-splitter
next_docs:
- security/backend-cookie-cors-auth-debug-drill
- network/api-gateway-auth-failure-surface-map
- network/application-tab-vs-request-cookie-header-mini-card
linked_paths:
- contents/security/authentication-authorization-session-foundations.md
- contents/security/cookie-failure-three-way-splitter.md
- contents/security/backend-cookie-cors-auth-debug-drill.md
- contents/security/cors-basics.md
- contents/network/api-gateway-auth-failure-surface-map.md
- contents/network/application-tab-vs-request-cookie-header-mini-card.md
confusable_with:
- security/cookie-failure-three-way-splitter
- security/cors-basics
- network/api-gateway-auth-failure-surface-map
forbidden_neighbors:
- contents/security/jwt-deep-dive.md
expected_queries:
- backend 미션에서 login은 됐는데 다음 API가 401 403이면 어떻게 봐야 해?
- cookie CORS session principal을 mission bridge로 연결해줘
- Application에는 cookie가 있는데 서버는 anonymous인 문제를 어떻게 설명해?
- API가 login HTML 200을 받는 auth failure surface를 학습자용으로 풀어줘
- spring-roomescape 인증 디버깅을 browser session 관점으로 정리해줘
contextual_chunk_prefix: |
  이 문서는 backend browser session auth mission_bridge다. login success,
  next API 401/403, login HTML 200, Set-Cookie, request Cookie header,
  server anonymous, CORS preflight 같은 미션 리뷰 문장을 browser session
  auth debugging 개념으로 매핑한다.
---
# Backend Browser Session Auth Mission Bridge

> 한 줄 요약: 브라우저 기반 인증 문제는 "로그인 성공" 한 문장으로 끝나지 않고, cookie 저장, request 전송, 서버 principal 복원, 권한 판정까지 네 칸으로 나눠야 한다.

**난이도: Beginner**

## 미션 진입 증상

| 브라우저 관찰 | 먼저 볼 경계 |
|---|---|
| Set-Cookie는 내려왔는데 저장 안 됨 | cookie 저장 차단 |
| Application에는 cookie가 있는데 요청 header가 비어 있음 | cookie 전송 조건 |
| Cookie header는 있는데 서버가 anonymous | session/principal 복원 |
| JSON API 대신 login HTML 200 | gateway/app auth failure surface |
| login은 됐는데 특정 API만 403 | authorization/role/ownership |

## 리뷰 신호

- "CORS 설정 바꿨는데도 로그인 유지가 안 돼요"는 cookie 저장/전송과 CORS 응답 읽기를 분리하라는 신호다.
- "200인데 API가 아닌 HTML이 와요"는 redirect를 따라간 최종 응답만 보고 있는지 보라는 뜻이다.
- "JWT/session은 valid인데 403이에요"는 인증과 인가를 분리하라는 말이다.
- "Application 탭에 쿠키가 있어요"는 아직 request에 전송됐다는 증거가 아니다.

## 판단 순서

1. Network 응답의 `Set-Cookie` blocked reason을 확인한다.
2. Application 저장 상태와 실제 request `Cookie` header를 비교한다.
3. 서버가 session/principal을 복원했는지 로그나 응답 표면으로 확인한다.
4. principal은 있는데 403이면 role, scope, ownership, cache freshness로 넘어간다.

이 순서가 잡히면 spring-roomescape나 shopping-cart의 로그인/관리자 API 리뷰가 CORS 설정 암기 대신 증거 기반 디버깅으로 바뀐다.
