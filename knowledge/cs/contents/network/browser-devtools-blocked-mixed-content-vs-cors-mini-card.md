---
schema_version: 3
title: "Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드"
concept_id: network/browser-devtools-blocked-mixed-content-vs-cors-mini-card
canonical: true
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 87
mission_ids: []
review_feedback_tags:
- mixed-content-vs-cors
- browser-policy-block
- preflight-actual-disambiguation
aliases:
- blocked mixed content vs cors
- mixed content blocked
- cors blocked policy
- browser blocked console clue
- https page http resource
- preflight blocked clue
symptoms:
- DevTools blocked를 전부 CORS로 읽고 mixed content나 extension block을 놓친다
- HTTPS 페이지에서 HTTP API를 부르는 문제를 서버 장애나 CORS 설정 문제로 오해한다
- CORS 콘솔 에러가 보이면 actual request가 서버까지 가지 않았다고 단정한다
- OPTIONS preflight 실패와 actual request 실패를 같은 장면으로 묶는다
intents:
- troubleshooting
- symptom
- comparison
prerequisites:
- network/browser-devtools-blocked-canceled-failed-primer
- network/http-https-basics
next_docs:
- network/browser-devtools-options-preflight-vs-actual-failure-mini-card
- network/cross-origin-cookie-credentials-cors-primer
- security/cors-samesite-preflight
- security/preflight-debug-checklist
linked_paths:
- contents/network/browser-devtools-blocked-canceled-failed-primer.md
- contents/network/browser-devtools-options-preflight-vs-actual-failure-mini-card.md
- contents/network/cross-origin-cookie-credentials-cors-primer.md
- contents/network/http-https-basics.md
- contents/network/browser-devtools-first-checklist-1minute-card.md
- contents/security/cors-samesite-preflight.md
confusable_with:
- network/browser-devtools-blocked-canceled-failed-primer
- network/browser-devtools-options-preflight-vs-actual-failure-mini-card
- network/cross-origin-cookie-credentials-cors-primer
- network/http-https-basics
- security/cors-samesite-preflight
forbidden_neighbors: []
expected_queries:
- "DevTools blocked가 mixed content인지 CORS인지 콘솔 문구로 어떻게 구분해?"
- "HTTPS 페이지에서 HTTP API를 호출하면 왜 브라우저가 막아?"
- "CORS blocked가 보이면 actual request가 서버까지 안 갔다고 봐도 돼?"
- "OPTIONS preflight blocked와 actual request failure를 Network 탭에서 나누는 법을 알려줘"
- "blocked by CORS policy와 Mixed Content 문구를 초급 기준으로 비교해줘"
contextual_chunk_prefix: |
  이 문서는 DevTools (blocked) row를 Console message 기준으로 mixed content,
  CORS response read policy, preflight failure, extension block으로 나누고
  HTTPS page -> HTTP resource와 cross-origin response read 문제를 분리하는
  beginner symptom router다.
---
# Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드

> 한 줄 요약: DevTools `Status`가 `(blocked)`일 때 초급자는 먼저 "브라우저가 왜 막았나"를 콘솔 문구로 나눠 읽어야 하고, mixed content는 `HTTPS 페이지 -> HTTP 자원` 차단, CORS는 `cross-origin 응답 읽기 정책` 차단으로 분리하면 첫 오해가 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)
- [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md)
- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- [HTTP와 HTTPS 기초](./http-https-basics.md)
- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: browser blocked mixed content vs cors, devtools blocked console clue, mixed content blocked 뭐예요, cors blocked by cors policy, request was blocked clue, blocked loading mixed active content, preflight blocked beginner, why devtools says blocked, console mixed content vs cors, https page http api blocked, cross origin request blocked, beginner blocked cause

## 핵심 개념

`(blocked)`는 보통 "서버가 `403`을 줬다"보다 **브라우저가 정책상 멈췄다**에 가깝다.
초급자가 특히 자주 보는 갈래는 둘이다.

- mixed content: `https://` 페이지가 `http://` 자원을 불러서 브라우저가 막음
- CORS: origin이 다른 응답을 브라우저 자바스크립트가 읽지 못하게 막음

둘 다 콘솔에는 "blocked" 비슷한 말이 보일 수 있지만, 질문이 다르다.

- mixed content는 "애초에 HTTP 자원을 HTTPS 페이지에서 불러도 되나?"
- CORS는 "요청/응답이 있었더라도 이 cross-origin 응답을 JS가 읽어도 되나?"

한 줄 멘탈 모델:

```text
mixed content = https 페이지에서 http 자원 자체를 막음
cors = cross-origin 응답 읽기 규칙을 막음
```

## 한눈에 보기

| 콘솔/증상 단서 | 초급자 첫 해석 | 요청이 서버까지 갔을 수 있나 | 먼저 볼 다음 곳 |
|---|---|---|---|
| `Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure resource 'http://...'` | HTTPS 페이지가 HTTP 자원을 불렀다 | 아예 안 갔을 수 있다 | 요청 URL 스킴, `http://` 여부 |
| `Access to fetch at ... from origin ... has been blocked by CORS policy` | cross-origin 응답 읽기가 정책에 막혔다 | 갔을 수도 있다 | `Origin`, preflight, CORS 응답 헤더 |
| `Response to preflight request doesn't pass access control check` | 본 요청 전 `OPTIONS` 확인 단계에서 막혔다 | actual 요청은 안 갔을 수 있다 | [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md), `OPTIONS` row, allow-method/header |
| 광고 차단 확장 프로그램 관련 문구 | 브라우저 확장/보안 툴이 막았다 | 안 갔을 수 있다 | 확장 프로그램 끄기, 다른 브라우저 |

짧게 외우면:

```text
https 페이지 -> http 자원 = mixed content
cross-origin 응답 읽기 문제 = cors
```

## 콘솔 문구로 먼저 가른다

`(blocked)`를 보면 Network row만 보지 말고 `Console`의 첫 문장을 같이 읽는다. 초급자에게 가장 빠른 분기점이기 때문이다.

### mixed content 문구

아래처럼 `Mixed Content`와 `insecure resource 'http://...'`가 보이면 mixed content 갈래다.

- 페이지는 `https://`
- 요청 자원은 `http://`
- 브라우저가 "보안이 섞였다"고 막는다

이 경우 첫 메모는 "CORS 헤더 부족"이 아니라 **URL 스킴이 섞였다**가 더 정확하다.

### CORS 문구

아래처럼 `blocked by CORS policy`가 보이면 CORS 갈래다.

- origin이 다르다
- 브라우저 JS가 응답을 읽는 규칙이 맞지 않는다
- preflight(`OPTIONS`)에서 막힐 수도 있다

이 경우 첫 메모는 "무조건 서버가 죽었다"가 아니라 **브라우저의 cross-origin 읽기 규칙이 안 맞는다**가 더 안전하다.

## 흔한 오해와 함정

- `(blocked)`면 전부 CORS라고 생각한다. mixed content와 확장 프로그램 차단도 많다.
- CORS 에러면 요청이 서버에 절대 안 갔다고 단정한다. actual request가 갔는데 JS만 응답을 못 읽는 경우도 있다.
- mixed content를 `http` 서버 장애로 읽는다. 서버 상태보다 `https -> http` 섞임이 핵심이다.
- `OPTIONS` 실패를 app 비즈니스 로직 실패로 읽는다. preflight는 본 요청 전 브라우저 확인 단계다.
- `https://app...`에서 `http://api...`를 호출하면서 "`localhost`라 괜찮겠지"라고 생각한다. 브라우저는 스킴 차이를 그대로 본다.

헷갈릴 때는 문장을 이렇게 고치면 된다.

- "서버가 거절했어요" 대신 "브라우저 정책이 먼저 막았을 수 있어요"
- "CORS니까 요청이 안 갔어요" 대신 "응답 읽기만 막혔는지도 봐야 해요"
- "API가 다운됐어요" 대신 "HTTPS 페이지가 HTTP 자원을 부른 건 아닌지 먼저 볼게요"

## 실무에서 쓰는 모습

### 장면 1. mixed content

페이지는 `https://app.example.com`인데 프런트 코드가 `http://api.example.com/me`를 호출했다고 하자.

이때 초급자 첫 해석은 이렇게 잡으면 된다.

- DevTools `Status`: `(blocked)`
- Console: `Mixed Content ... requested an insecure resource 'http://...'`
- 첫 결론: CORS보다 먼저 `http://` 호출 자체를 `https://`로 고쳐야 한다

### 장면 2. CORS

페이지는 `https://app.example.com`, API는 `https://api.example.com`인데 콘솔이 아래처럼 말한다고 하자.

`Access to fetch at 'https://api.example.com/me' from origin 'https://app.example.com' has been blocked by CORS policy`

이때 첫 해석은 아래가 안전하다.

- 스킴은 둘 다 `https://`라 mixed content는 아니다
- 대신 origin이 달라 CORS 갈래다
- preflight row가 있는지, `Access-Control-Allow-Origin` 같은 응답 헤더가 맞는지 본다

즉 둘 다 `(blocked)`여도 **mixed content는 URL 스킴 문제**, **CORS는 cross-origin 읽기 문제**다.

## 더 깊이 가려면

- `(blocked)` 전체 묶음을 먼저 익히려면 [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)
- `OPTIONS` preflight와 actual request failure를 DevTools row 기준으로 바로 가르고 싶다면 [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md)
- cookie, `credentials`, CORS를 한 표로 더 붙여 보려면 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- `http`와 `https` 차이 자체가 아직 낯설면 [HTTP와 HTTPS 기초](./http-https-basics.md)
- 첫 판독 순서를 1분 카드로 고정하려면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- preflight와 CORS 에러 문구를 더 자세히 보려면 [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)

## 한 줄 정리

DevTools `(blocked)`에서 mixed content는 `HTTPS 페이지가 HTTP 자원을 부른 장면`, CORS는 `cross-origin 응답 읽기 정책 장면`으로 먼저 나누면 초급자의 첫 오분류가 크게 줄어든다.
