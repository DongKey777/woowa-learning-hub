---
schema_version: 3
title: "HTTP Statelessness and State Management Basics"
concept_id: network/http-stateless-state-management-basics
canonical: true
category: network
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- http-stateless
- cookie-session-jwt
- login-state
aliases:
- HTTP stateless
- stateless HTTP
- HTTP 상태 유지
- 쿠키 세션 JWT 차이
- 로그인 상태 유지
- stateless vs stateful
- session id cookie
symptoms:
- HTTP가 무상태라서 로그인 상태를 유지할 수 없다고 생각한다
- 쿠키, 세션, JWT를 모두 같은 저장 방식으로 뭉갠다
- 서버 세션 방식과 JWT 방식의 상태 저장 위치와 무효화 trade-off를 구분하지 못한다
- 브라우저가 매 요청마다 어떤 증거를 실어 보내는지 놓친다
intents:
- definition
- comparison
- deep_dive
prerequisites:
- network/http-request-response-basics-url-dns-tcp-tls-keepalive
next_docs:
- network/http-state-session-cache
- network/cookie-session-jwt-browser-flow-primer
- security/session-cookie-jwt-basics
- spring/mvc-request-lifecycle
linked_paths:
- contents/network/http-state-session-cache.md
- contents/network/cookie-session-jwt-browser-flow-primer.md
- contents/spring/spring-mvc-request-lifecycle.md
- contents/security/session-cookie-jwt-basics.md
confusable_with:
- network/http-state-session-cache
- network/cookie-session-jwt-browser-flow-primer
- security/session-cookie-jwt-basics
forbidden_neighbors: []
expected_queries:
- "HTTP가 stateless라는 뜻과 로그인 상태 유지 방식을 설명해줘"
- "쿠키 세션 JWT는 브라우저와 서버가 각각 무엇을 기억해?"
- "HTTP 무상태성이 수평 확장에 왜 유리해?"
- "세션 방식과 JWT 방식의 trade-off는 무엇이야?"
- "서버가 이전 요청을 기억하지 않는데 /me 요청에서 사용자를 어떻게 복원해?"
contextual_chunk_prefix: |
  이 문서는 HTTP stateless 특성, 로그인 상태 유지, cookie/session/JWT,
  session store, Authorization header, 요청마다 상태를 복원하는 방식을
  설명하는 beginner primer다.
---
# HTTP 무상태성과 상태 유지 전략 입문

> 한 줄 요약: HTTP는 기본적으로 각 요청을 독립적으로 처리하는 무상태 프로토콜이며, 로그인 상태처럼 서버가 사용자를 기억해야 할 때는 쿠키·세션·토큰으로 상태를 별도로 관리한다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: http 무상태성, stateless http, what is stateless http, http stateless 란, http 상태 유지 방법, 로그인 상태 어떻게 유지해요, 쿠키 세션 jwt 차이, 쿠키 세션 왜 필요해요, http 요청 독립, stateless vs stateful, 상태없는 프로토콜, 세션 필요한 이유, 처음 배우는 http 무상태성, http basics login state, beginner network

## 핵심 개념

HTTP는 **무상태(stateless) 프로토콜**이다. 서버는 이전 요청을 기억하지 않는다. 두 번째 요청이 들어왔을 때 서버는 그게 같은 사용자인지 모른다. 입문자가 가장 많이 헷갈리는 부분은 "그러면 로그인 상태는 어떻게 유지되나요?"다. HTTP 자체가 아니라 쿠키, 세션, 토큰 같은 추가 수단이 그 역할을 한다.

## 한눈에 보기

HTTP 자체는 이전 요청을 기억하지 않는다. 쿠키를 이용해 클라이언트가 매 요청마다 자신을 증명한다.

```
요청 1: POST /login  → 서버: 인증 성공, session 생성
                                     ↓ Set-Cookie: JSESSIONID=abc

요청 2: GET /me      → 서버: JSESSIONID 없으면 "누구?", 있으면 세션 조회
                                     ↓ Cookie: JSESSIONID=abc 전달

요청 3: GET /orders  → 서버: 또 JSESSIONID 확인
                                     ↓ Cookie: JSESSIONID=abc 전달
```

서버가 기억하는 게 아니라, 클라이언트가 매 요청마다 "나는 이 사람이에요"를 증명한다.

쿠키·세션·JWT 중 어떤 방식을 쓰든, 상태 전달은 항상 요청 안에 들어 있다.

## 상세 분해

### 왜 무상태인가

HTTP는 처음 설계될 때 단순하고 확장 가능하게 만들기 위해 상태를 서버가 유지하지 않도록 했다. 덕분에 서버를 여러 대로 수평 확장할 때 어느 서버에 요청이 가도 동일하게 처리할 수 있다.

### 상태 유지가 필요한 이유

실무에서는 상태가 필요한 시나리오가 많다.

- 로그인 유지: "이 요청을 보낸 사람이 누구인가"
- 장바구니: "이 사용자가 무엇을 담아뒀는가"
- 권한 확인: "이 사용자가 이 리소스에 접근 가능한가"

이런 정보를 HTTP 자체에서 보관하지 않으므로, 별도 수단이 필요하다.

### 상태 유지 주요 전략 세 가지

처음에는 "무엇을 브라우저가 들고 다니고, 무엇을 서버가 기억하나" 두 질문으로 자르면 덜 헷갈린다.

| 방식 | 브라우저가 보내는 것 | 서버가 기억하는 것 | 초급자용 한 줄 감각 |
|---|---|---|---|
| 쿠키 + 세션 | `JSESSIONID` 같은 세션 ID 쿠키 | 세션 저장소의 사용자 상태 | "브라우저는 번호표만 들고, 진짜 상태는 서버가 본다" |
| JWT 토큰 | `Authorization` 헤더나 쿠키의 토큰 | 보통 토큰 자체를 검증하고 바로 해석 | "브라우저가 증명서 자체를 들고 다닌다" |
| 클라이언트 측 저장 | localStorage/sessionStorage 값 | 서버는 별도 저장 없이 요청마다 다시 받음 | "브라우저가 임시 메모를 들고 다니지만 민감 정보는 조심" |

**1. 쿠키 + 서버 세션**

- 서버가 session store에 사용자 상태를 저장한다.
- 클라이언트는 session id만 쿠키에 갖고 다닌다.
- 매 요청마다 서버가 session id로 상태를 조회한다.

**2. 토큰(JWT 등)**

- 서버가 상태를 저장하지 않는다.
- 사용자 정보가 토큰 안에 들어있고, 서버는 토큰의 서명만 검증한다.
- `Authorization: Bearer <token>` 헤더로 전달한다.

**3. 클라이언트 측 저장**

- localStorage, sessionStorage 같은 브라우저 저장소를 쓰기도 한다.
- 다만 XSS에 취약하므로 민감 정보 저장에는 주의가 필요하다.

## 흔한 오해와 함정

- "HTTP가 무상태이니까 로그인이 불가능하다"가 아니다. 무상태는 프로토콜 특성이고, 로그인 상태 유지는 쿠키/세션/토큰 계층에서 따로 구현한다.
- "세션을 쓰면 stateful, JWT를 쓰면 stateless"라고 단순히 이분하면 안 된다. JWT를 쓰더라도 서버가 토큰을 블랙리스트로 관리하면 서버 상태가 생긴다.
- 쿠키와 세션은 같은 게 아니다. 쿠키는 브라우저 전송 수단이고, 세션은 서버 저장 방식이다.
- "쿠키에 로그인 정보가 다 들어 있다"라고 생각하면 위험하다. 보통은 사용자 정보 전체가 아니라 세션 ID나 토큰이 들어 있고, 서버는 그 값을 근거로 다시 사용자를 복원한다.

## 실무에서 쓰는 모습

Spring Security를 사용하는 서버에서 요청이 들어오면 보통 이 흐름을 거친다.

1. 요청에서 쿠키나 `Authorization` 헤더를 꺼낸다.
2. 세션 ID라면 session store를 조회해 사용자 정보를 복원한다.
3. JWT라면 서명과 만료를 검증해 사용자 정보를 복원한다.
4. 복원된 사용자 정보로 권한을 확인하고 컨트롤러를 실행한다.

즉 HTTP가 무상태여도 애플리케이션 계층이 요청마다 상태를 복원하는 구조다.

예를 들어 브라우저에서 로그인 후 `GET /me`를 호출할 때는 아래처럼 읽으면 된다.

- 세션 방식: 브라우저는 `JSESSIONID=abc`를 보내고, 서버는 세션 저장소에서 `abc -> userId=7`을 찾아 현재 사용자를 복원한다.
- JWT 방식: 브라우저는 `Authorization: Bearer <token>`을 보내고, 서버는 토큰 서명과 만료를 확인한 뒤 토큰 안의 사용자 정보를 해석한다.

처음 헷갈릴 때는 "HTTP가 기억한다"가 아니라 "요청마다 증거를 다시 실어 보낸다"로 읽으면 된다.

## 더 깊이 가려면

- [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) — 세션/쿠키/캐시를 실제 Spring 코드와 연결
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) — 브라우저가 실제로 요청에 무엇을 싣는지

## 면접/시니어 질문 미리보기

**Q. HTTP가 무상태 프로토콜이라는 게 무슨 뜻인가요?**
서버가 이전 요청을 기억하지 않는다는 뜻이다. 각 요청은 독립적으로 처리된다. 상태가 필요하면 쿠키·세션·토큰 등 별도 수단으로 매 요청마다 상태를 전달한다.

**Q. 무상태가 확장성에 어떤 이점을 주나요?**
어느 서버 인스턴스에 요청이 가도 같은 결과를 낼 수 있어 수평 확장이 쉬워진다. 서버가 공유 상태를 갖지 않으므로 서버를 늘리거나 줄이는 데 제약이 적다.

**Q. 세션 방식과 JWT 방식의 trade-off는 무엇인가요?**
세션 방식은 서버에서 즉시 무효화가 가능하지만 session store가 필요하다. JWT는 session store 없이 서버를 확장하기 쉽지만, 토큰 만료 전에 즉시 무효화하려면 추가 구현이 필요하다.

## 한 줄 정리

HTTP는 요청 간 상태를 기억하지 않으며, 로그인 같은 상태 유지는 쿠키·세션·토큰이라는 별도 수단으로 매 요청마다 상태를 복원하는 방식으로 구현한다.
