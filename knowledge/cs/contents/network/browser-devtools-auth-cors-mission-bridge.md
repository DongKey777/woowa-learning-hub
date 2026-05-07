---
schema_version: 3
title: Browser DevTools Auth CORS Mission Bridge
concept_id: network/browser-devtools-auth-cors-mission-bridge
canonical: false
category: network
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 78
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
review_feedback_tags:
- browser-devtools
- cors-vs-auth
- preflight-actual
- mission-debugging
aliases:
- browser devtools auth cors mission bridge
- Network 탭 CORS 인증 bridge
- options actual 401 403 bridge
- roomescape cors login 403 devtools
- shopping-cart cookie empty request header bridge
symptoms:
- Console은 CORS라고 하지만 Network actual request에는 401이나 403이 보인다
- OPTIONS만 보고 실제 GET/POST가 나갔는지 확인하지 않는다
- Application 탭에는 쿠키가 있는데 request header에는 Cookie가 비어 있다
intents:
- mission_bridge
- troubleshooting
- comparison
prerequisites:
- network/browser-devtools-first-checklist-1minute-card
- network/browser-devtools-options-preflight-vs-actual-failure-mini-card
next_docs:
- network/browser-devtools-error-path-cors-vs-actual-401-403-bridge
- security/cookie-cors-auth-anonymous-symptom-router
- security/auth-failure-response-401-403-404
linked_paths:
- contents/network/browser-devtools-first-checklist-1minute-card.md
- contents/network/browser-devtools-options-preflight-vs-actual-failure-mini-card.md
- contents/network/browser-devtools-error-path-cors-vs-actual-401-403-bridge.md
- contents/network/cross-origin-cookie-credentials-cors-primer.md
- contents/security/cookie-cors-auth-anonymous-symptom-router.md
- contents/security/auth-failure-response-401-403-404.md
confusable_with:
- network/browser-devtools-options-preflight-vs-actual-failure-mini-card
- network/browser-devtools-error-path-cors-vs-actual-401-403-bridge
- security/cookie-cors-auth-anonymous-symptom-router
forbidden_neighbors:
- contents/software-engineering/controller-service-domain-responsibility-split-drill.md
expected_queries:
- roomescape에서 CORS처럼 보이는데 Network에는 403이면 어떻게 봐?
- shopping-cart 쿠키가 Application 탭에는 있는데 요청 헤더에는 비어 있으면 어디부터 봐?
- OPTIONS만 있고 actual POST가 없을 때 preflight와 auth 실패를 어떻게 나눠?
- DevTools Network로 401 403 CORS cookie 문제를 미션 문맥에서 설명해줘
contextual_chunk_prefix: |
  이 문서는 browser DevTools auth CORS mission_bridge다. OPTIONS preflight,
  actual GET/POST row, actual 401/403, console CORS, cookie empty request
  header, Application tab cookie visible 같은 미션 디버깅 질문을 Network 탭
  판독 순서로 매핑한다.
---
# Browser DevTools Auth CORS Mission Bridge

> 한 줄 요약: 브라우저에서 CORS처럼 보여도 Network actual row가 있으면 auth 실패를 버리지 말고, actual row가 없으면 preflight부터 본다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "Console은 CORS라고 하는데 Network에는 401이나 403이 보여요" | 방탈출 관리자 로그인, 장바구니 checkout API 실패 | Console 문구보다 actual request row의 status를 먼저 읽는다 |
| "OPTIONS만 보고 실제 요청이 나갔는지 확인하지 않았어요" | preflight와 실제 POST/GET 실패가 섞인 브라우저 디버깅 | actual row 존재 여부로 preflight lane과 auth failure lane을 나눈다 |
| "Application 탭에는 쿠키가 있는데 요청에는 Cookie가 비어 있어요" | 세션 기반 인증 요청이 익명으로 처리되는 장면 | cookie 저장 여부와 request header 전송 여부를 분리한다 |

## CS concept 매핑

| DevTools 장면 | 먼저 붙일 질문 |
|---|---|
| `OPTIONS`만 있고 actual `POST`가 없음 | preflight에서 막혔는가 |
| actual `POST`가 있고 status `401` | 인증 실패인가 |
| actual `GET`이 있고 status `403` | 인가 실패인가 |
| Console은 CORS, Network actual은 `401/403` | error-path CORS가 auth 실패를 가리는가 |
| Application 탭 cookie는 보이지만 request `Cookie` 없음 | credentials / SameSite / domain / secure 조건인가 |

## 리뷰 신호

- "CORS 에러라서 서버 로직은 안 탄 것 같아요"는 actual request row부터 확인해야 하는 신호다.
- "`OPTIONS 401`이니까 로그인 문제죠?"는 actual 요청 존재 여부를 먼저 보라는 뜻이다.
- "쿠키는 있는데 익명으로 처리돼요"는 저장된 cookie와 전송된 request header를 나누라는 말이다.
- "Network에는 403인데 프론트는 CORS라고 해요"는 auth failure와 error response exposure를 같이 봐야 한다.

## 판단 순서

1. same path의 actual `GET/POST/PUT/DELETE` row가 있는지 본다.
2. 없으면 preflight lane으로 보고 CORS method/header/origin을 확인한다.
3. 있으면 actual row의 status를 먼저 읽고 `401/403/404` 의미를 고정한다.
4. cookie가 필요한 요청이면 request header의 `Cookie` 존재를 본다.

이 순서가 잡히면 roomescape admin auth나 shopping-cart checkout 디버깅에서 CORS 설정만 계속 바꾸는 시간을 줄일 수 있다.
