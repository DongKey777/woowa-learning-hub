---
schema_version: 3
title: Spring API 401 vs browser 302 beginner bridge
concept_id: spring/spring-api-401-vs-browser-302-beginner-bridge
canonical: true
category: spring
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 89
mission_ids:
- missions/baseball
- missions/blackjack
- missions/lotto
- missions/shopping-cart
review_feedback_tags:
- response-contract-split
- api-401-vs-login-redirect-302
- authentication-entrypoint-path-split
aliases:
- spring api 401 vs browser 302
- Spring API는 401 브라우저는 302
- api가 login html을 받아요
- api인데 로그인 html 와요
- fetch 401 대신 302
- api인데 302 /login 보여요
- form login api separation spring
- browser redirect api json
- AuthenticationEntryPoint beginner
- response contract split
- login page redirect vs api error
symptoms:
- 같은 인증 실패인데 브라우저 페이지는 302 /login이고 JSON API는 401이어야 한다는 응답 계약 차이를 구분하지 못해
- API fetch가 401 JSON 대신 login HTML이나 302 redirect를 받아서 Security 설정 문제인지 컨트롤러 문제인지 헷갈려
- 302/401 인증 실패와 이미 로그인한 뒤의 403 권한 실패를 같은 문제로 읽어 오진해
intents:
- troubleshooting
- comparison
prerequisites:
- spring/spring-security-basics
- security/browser-401-vs-302-login-redirect-guide
next_docs:
- spring/securityfilterchain-multiple-entrypoints-primer
- spring/admin-302-login-vs-403-beginner-bridge
- spring/security-exceptiontranslation-entrypoint-accessdeniedhandler
- spring/security-requestcache-savedrequest-boundaries
linked_paths:
- contents/spring/spring-securityfilterchain-multiple-entrypoints-primer.md
- contents/spring/spring-admin-302-login-vs-403-beginner-bridge.md
- contents/spring/spring-security-basics.md
- contents/spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md
- contents/spring/spring-security-requestcache-savedrequest-boundaries.md
- contents/spring/spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md
- contents/spring/spring-admin-session-cookie-flow-primer.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/network/http-state-session-cache.md
confusable_with:
- spring/admin-302-login-vs-403-beginner-bridge
- spring/securityfilterchain-multiple-entrypoints-primer
- spring/security-requestcache-savedrequest-boundaries
- security/browser-401-vs-302-login-redirect-guide
forbidden_neighbors: []
expected_queries:
- Spring에서 브라우저 페이지는 302 /login이고 API는 401 JSON이어야 하는 이유를 설명해줘
- fetch가 401 대신 login HTML을 받으면 SecurityFilterChain이나 AuthenticationEntryPoint를 어떻게 의심해야 해?
- 같은 인증 실패를 page contract와 API contract로 나누는 response-contract-split이 뭐야?
- 302 /login, 401 Unauthorized, 403 Forbidden을 Spring Security 흐름에서 어떻게 구분해?
- /admin/**은 form login redirect, /api/**는 JSON 401로 나누려면 다음에 어떤 문서를 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Spring Security에서 같은 unauthenticated 상태라도 browser page request는 302 /login redirect 계약이 자연스럽고 JSON API request는 401 JSON 계약이 자연스럽다는 response-contract-split을 설명하는 beginner bridge다.
  API login HTML, fetch got 302, AuthenticationEntryPoint, SecurityFilterChain split, 401 vs 302 vs 403 같은 자연어 증상 질문이 본 문서에 매핑된다.
---
# Spring API는 `401` JSON인데 브라우저 페이지는 `302 /login`인 이유: 초급 브리지

> 한 줄 요약: 같은 Spring MVC 앱 안에서도 브라우저 페이지 요청은 로그인 화면으로 보내는 `302 /login` 흐름이 자연스럽고, JSON API 요청은 인증 실패를 `401`로 직접 말하는 흐름이 자연스러워서 둘을 같은 실패로 읽으면 금방 헷갈린다.
>
> 문서 역할: 이 문서는 spring/security 입구에서 "`왜 브라우저는 redirect인데 API는 JSON이지?`"를 먼저 분리하는 beginner bridge다. 쿠키/세션 복원이나 final `403`보다 `응답 계약 분리`가 먼저 의심될 때 이 문서가 맞다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "API fetch가 401 JSON 대신 로그인 HTML을 받아요" | shopping-cart 주문 API를 호출했는데 브라우저용 login page가 response body로 오는 상황 | API contract와 browser page contract를 분리한다 |
| "`/admin`은 302가 맞고 `/api`는 401이 맞나요?" | 관리자 화면과 JSON API를 같은 Security 설정으로 처리하는 코드 | path별 AuthenticationEntryPoint를 다르게 볼 수 있는지 확인한다 |
| "401, 302, 403이 전부 인증 실패처럼 보여요" | 로그인 전 요청, 로그인 화면 redirect, 로그인 후 권한 부족을 한 문제로 디버깅 | unauthenticated와 access denied를 먼저 나눈다 |

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md)
- [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)
- [Spring Security 기초: 인증과 인가의 흐름 잡기](./spring-security-basics.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)
- [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)
- [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring api 401 vs browser 302, spring login redirect vs json api, api가 login html을 받아요, api인데 로그인 html 와요, fetch 401 대신 302, api인데 302 /login 보여요, spring mixed mvc app auth failure, authenticationentrypoint beginner, response contract split, exceptiontranslationfilter 처음, form login api separation spring, 처음 배우는데 401 302 차이, spring browser redirect api json, login page redirect vs api error, 왜 api가 login으로 가요

## 핵심 개념

처음에는 "누가 이 응답을 읽는가"만 먼저 보면 된다.

- 브라우저 페이지 요청은 다음 화면으로 이동시켜 주는 것이 중요하다.
- JSON API 요청은 프론트엔드 코드나 다른 클라이언트가 상태 코드를 읽는 것이 중요하다.

그래서 같은 "아직 로그인 안 됨" 상황이어도 결과가 갈린다.

- 브라우저 페이지: `302 /login`
- JSON API: `401 Unauthorized`

입문자가 자주 헷갈리는 이유는 둘 다 결국 "인증 실패"인데, 하나는 이동이고 하나는 데이터 응답이라 모양이 완전히 다르게 보이기 때문이다.

## 이 문서가 바로 맞는 질문

아래처럼 질문이 "`왜 응답 모양이 둘로 갈리지?`"에 있으면 이 문서가 먼저다.

| 지금 입에서 나온 문장 | 먼저 붙일 라벨 | 여기서 먼저 답하는 것 |
|---|---|---|
| "`브라우저는 302인데 API는 401이에요`" | `response-contract-split` | 같은 인증 실패가 왜 서로 다른 응답 계약으로 보이는가 |
| "`api인데 login html 와요`" | `response-contract-split` | API가 브라우저용 entry point를 잘못 탔는가 |
| "`cookie 있는데 다시 로그인`" | `server persistence / session mapping` | 아니다. 이 문서보다 세션 복원 primer가 먼저다 |
| "`로그인 성공 후 원래 URL 복귀 403`" | `login-success-final-403` | 아니다. 이 문서보다 final `403` primer가 먼저다 |

짧게 말하면 이 문서는 `브라우저 vs API 응답 계약`을 자르는 입구고, 로그인 유지 실패나 마지막 권한 실패를 끝까지 파는 문서는 아니다.

## 첫 분기 고정 라벨

이 문서는 Spring Security beginner 사다리에서 `response-contract-split` 라벨을 맡는다.
즉 "`아직 인증 안 됨`인데 왜 브라우저는 `302`, API는 `401`처럼 보이지?"를 먼저 본다.

| 검색하거나 바로 말하는 증상 | 먼저 붙일 고정 라벨 | 지금 바로 던질 질문 | safe next doc |
|---|---|---|---|
| "`브라우저는 302인데 API는 401이에요`", "`브라우저랑 API가 다르게 보여요`" | `response-contract-split` | "누가 이 응답을 읽는가: 페이지 이동인가, JSON 계약인가?" | 이 문서 계속 |
| "`/admin`이 바로 `302 /login`으로 가요" | `pre-login-302` | "아직 비로그인이라 로그인 전 `주소 메모`를 남기는 갈래인가?" | [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md) |
| "`api인데 로그인 html 와요`", "`fetch(\"/api/me\")`가 `401` 대신 login HTML이나 `302`를 받아요" | `response-contract-split` | "API가 브라우저용 redirect 계약을 잘못 탔나?" | 이 문서 계속 -> [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md) |
| "`로그인 성공 후 원래 URL 복귀 403`", "`복귀는 됐는데 권한 없음`" | `login-success-final-403` | "원래 URL 복귀는 끝났고 마지막 권한 검사만 남았나?" | [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md) |
| "`cookie 있는데 다시 로그인`", "`next request anonymous after login`" | `server persistence / session mapping` | "응답 계약보다 다음 요청 로그인 복원이 먼저 깨졌나?" | [Spring 관리자 인증에서 쿠키와 세션이 어떻게 이어지는가: 초급 primer](./spring-admin-session-cookie-flow-primer.md) |

짧게 고정하면 이렇게 읽으면 된다.

- `response-contract-split`: 아직 인증 안 됨인데 브라우저와 API가 서로 다른 계약으로 보인다.
- `pre-login-302`: 브라우저 쪽 로그인 진입이 먼저 보인다.
- `login-success-final-403`: 복귀는 성공했고 마지막 권한 실패가 남았다.

## 한눈에 보기

```text
브라우저가 /admin 페이지 요청
-> 로그인 안 됨
-> login page로 이동시키는 쪽이 편함
-> 302 /login

브라우저 JS 또는 API client가 /api/me 요청
-> 로그인 안 됨
-> redirect보다 상태 코드가 더 중요함
-> 401 JSON
```

| 요청 종류 | 클라이언트가 기대하는 것 | 인증 실패 시 흔한 응답 | 초급자 질문 |
|---|---|---|---|
| 브라우저 페이지 이동 | 다음에 어디로 갈지 | `302 /login` | "로그인 화면으로 보내는 게 자연스러운가?" |
| JSON API 호출 | 상태 코드와 JSON body | `401` | "프론트 코드가 이 실패를 직접 읽어야 하나?" |
| 이미 로그인했지만 권한 부족 | 권한 거부 사실 | `403` | "이건 로그인 문제가 아니라 권한 문제인가?" |

핵심은 `302`와 `401`이 서로 경쟁하는 답이 아니라, **같은 인증 실패를 다른 계약으로 표현한 결과**일 수 있다는 점이다.

이 차이를 실제 설정에서 안전하게 유지하려면 `/admin/**`와 `/api/**`를 서로 다른 `SecurityFilterChain`으로 분리해 각 경로가 자기 `AuthenticationEntryPoint`를 타게 하는 구성이 흔하다.

## entry point / denied handler 재진입 지도

이 문서를 읽다 보면 결국 "`그래서 지금은 entry point 얘기예요, denied handler 얘기예요?`"에서 다시 헷갈리기 쉽다.

처음 재진입은 아래 표처럼 잡으면 된다.

| 지금 보이는 장면 | 먼저 붙일 고정 라벨 | 내부 책임 키워드 | 바로 이어서 볼 문서 | 왜 그 문서로 재진입하나 |
|---|---|---|---|---|
| 브라우저 페이지가 `/login`으로 튄다 | `pre-login-302` | `authenticationentrypoint` | [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md) | "아직 인증 안 됨"을 누가 `302`나 `401`로 번역하는지 핵심 책임을 다시 잡는다 |
| `api인데 로그인 html 와요`, `fetch("/api/me")`가 `401` 대신 login HTML이나 `302`를 받는다 | `response-contract-split` | `authenticationentrypoint + chain split` | [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md) | API가 브라우저용 entry point를 잘못 타는지 경로 분리 관점으로 바로 내려간다 |
| 이미 로그인했는데 마지막 응답이 `403`이다 | `plain-403` | `accessdeniedhandler` | [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md) | "인증 안 됨"과 "권한 부족"을 먼저 끊은 뒤 denied handler 축으로 재진입한다 |
| 로그인 후 원래 URL로 돌아왔는데 마지막에 `403`이다 | `login-success-final-403` | `savedrequest 다음 denied handler` | [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md) | 복귀 자체와 마지막 권한 실패를 두 단계로 나눠 오진을 줄인다 |

- 이 문서의 라벨은 `response-contract-split`이고, 내부 키워드는 `authenticationentrypoint`다.
- `403`이 전면에 나오면 이 문서를 오래 붙잡기보다 `plain-403` 또는 `login-success-final-403` primer로 먼저 갈아타는 편이 beginner-safe하다.

## 상세 분해

### 1. 브라우저 페이지는 "다음 화면"이 중요하다

비로그인 사용자가 `/admin/reservations` 페이지를 열면, 브라우저는 보통 데이터를 직접 해석하기보다 화면 전환을 따른다.

그래서 Spring Security도 form login 중심 앱에서는 이런 흐름을 자주 만든다.

- 보호된 페이지 접근
- 로그인 안 됨
- `/login`으로 redirect
- 로그인 후 원래 페이지로 복귀할 수도 있음

즉 페이지 요청의 `302 /login`은 "실패를 숨긴다"기보다 "로그인 화면으로 안내한다"에 가깝다.

### 2. JSON API는 "화면 이동"보다 "실패 사실 전달"이 중요하다

반대로 `fetch("/api/me")`나 모바일 앱의 `/api/me` 호출은 redirect된 로그인 HTML보다 실패 정보를 직접 받는 편이 낫다.

이때 보통 기대하는 것은 다음이다.

- 상태 코드: `401`
- 응답 본문: JSON 에러 또는 `ProblemDetail`

그래서 API가 `302 /login`을 돌려주면 프론트엔드는 "로그인이 필요한 상태"를 깔끔하게 처리하기보다, login HTML을 받아 버리거나 redirect를 따라가다 더 헷갈리기 쉽다.

### 3. mixed Spring MVC 앱에서는 두 계약이 함께 존재할 수 있다

초급자가 흔히 보는 장면은 이것이다.

- `/admin/**`는 서버가 렌더링한 페이지 또는 브라우저 화면 흐름
- `/api/**`는 JSON 응답 중심 API

둘 다 같은 Spring 앱 안에 있어도, 인증 실패 응답은 같을 필요가 없다.

오히려 초반 설계 감각은 이렇게 잡는 편이 안전하다.

- 페이지 라우트: login redirect 허용
- API 라우트: `401` JSON 유지

즉 "`앱이 하나니까 인증 실패도 하나로 통일돼야지`"보다 "`클라이언트 계약이 다르니 응답도 갈릴 수 있구나`"가 beginner 기준 더 정확하다.

그리고 이 감각을 실제 Spring Security 설정으로 옮길 때는 `/admin/**`와 `/api/**`를 별도 `SecurityFilterChain`으로 나눠 각 경로가 자기 entry point를 타게 하는 구성이 가장 흔하다.

## `403`이 앞에 보이면 denied handler 문서로 한 번 끊는다

이 문서를 읽는 도중에도 장면이 바뀔 수 있다.

- 처음엔 "`브라우저는 왜 `302`고 API는 왜 `401`이지?`"로 시작했다.
- 그런데 로그나 DevTools를 더 보니 사실 마지막 실패가 `403`이었다.

이때는 `response-contract-split`을 더 파기보다, 라벨을 바로 갈아타야 한다.

- 아직 비로그인인가 -> `pre-login-302` 또는 `response-contract-split`
- 이미 로그인했고 권한이 부족한가 -> `plain-403` 또는 `login-success-final-403`

즉 `403`이 중심이면 이 문서를 계속 읽는 것보다 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)에서 `302 /login`과 `403`을 먼저 분리한 뒤, 필요할 때만 [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)로 다시 올라오는 편이 빠르다.

## redirect 기억과 권한 축 분리

### 4. `302`가 반복되면 redirect 기억과 API 계약이 섞였는지 먼저 본다

로그인 후 원래 URL로 복귀시키는 `RequestCache`와 `SavedRequest`는 브라우저 페이지 UX에는 유용하다.

하지만 API까지 같은 정책을 타면 이런 증상이 나온다.

- `fetch`가 `401` JSON 대신 login page HTML을 받는다
- Postman에서는 `401`을 기대했는데 브라우저에서는 `302 /login`으로 보인다
- stateless API라고 생각했는데 redirect와 세션이 함께 보인다

이때는 권한 규칙보다 먼저 "브라우저용 redirect 정책이 API에도 붙었나?"를 보는 편이 빠르다.

### 5. `403`은 이 문서의 주인공이 아니다

이 문서는 "인증 실패를 `302`로 보여 줄지 `401`로 보여 줄지"를 다룬다.

반면 `403`은 보통 이런 뜻이다.

- 로그인은 됨
- 하지만 권한이 없음

즉 `403`은 "`302`냐 `401`이냐"와 다른 축이다.
초급자는 먼저 "`아직 인증 안 됨` vs `이미 로그인했지만 권한 없음`"을 분리한 뒤, 그다음 "`인증 안 됨`을 page 계약으로 보일지 API 계약으로 보일지"를 보면 된다.

## 다음 문서 분기

이 문서 다음에는 `SavedRequest` deep dive로 바로 점프하기보다, 지금 막힌 질문을 고정 라벨 한 번 더 붙여서 가는 편이 안전하다.

| 지금 가장 막히는 질문 | 먼저 붙일 고정 라벨 | 다음 문서 | 왜 그 문서가 먼저인가 |
|---|---|---|---|
| "`/api/**`는 `401`, `/admin/**`는 `302 /login`으로 실제 설정을 어떻게 나눠요?" | `response-contract-split` | [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md) | 이 문서의 `브라우저 계약 vs API 계약`을 실제 체인 분리 설정으로 옮기는 다음 단계다 |
| "`/admin`이 `302 /login`으로 갔다가 로그인 후 다시 돌아오는데 마지막엔 `403`이 나요" | `login-success-final-403` | [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md) | `원래 URL 복귀`와 `최종 권한 실패`를 먼저 두 단계로 끊어야 `RequestCache` 오진입을 줄일 수 있다 |
| "`왜 로그인 후 원래 주소로 다시 가요?`, `SavedRequest`가 뭐예요?" | `redirect / navigation memory` | [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md) | 여기서부터는 `redirect / navigation memory` 축을 깊게 보는 advanced follow-up이다 |

- 짧게 고정하면 이 순서다: `response-contract-split` -> 필요하면 `login-success-final-403` -> 그다음에만 `redirect / navigation memory` deep dive.
- 특히 "`로그인 성공 후 원래 /admin 으로 복귀했는데 마지막에 403`"처럼 `SavedRequest`와 권한 실패가 한 문장에 같이 보이면 advanced 문서보다 `final 403 primer`를 먼저 보는 편이 beginner-safe하다.

## 흔한 오해와 함정

- "`302 /login`이면 무조건 브라우저 쪽 문제다"라고 생각하기 쉽다.
  실제로는 API 경로에 form login용 entry point가 섞였다는 Spring 설정 문제일 수 있다.

- "`401`이 더 HTTP스럽으니 페이지도 전부 `401`로 통일해야 한다"라고 생각하기 쉽다.
  브라우저 화면 흐름에서는 로그인 페이지 이동 UX가 더 자연스러울 수 있다.

- "`302`와 `401`은 전혀 다른 원인이다"라고 생각하기 쉽다.
  같은 "인증 안 됨"을 서로 다른 클라이언트 계약으로 표현한 결과일 수 있다.

- "`fetch`가 login HTML을 받았으니 컨트롤러가 HTML을 반환했다"라고 생각하기 쉽다.
  실제로는 컨트롤러 전에 Spring Security가 redirect를 만들고, 브라우저가 그 결과를 따라간 것일 수 있다.

## 실무에서 쓰는 모습

가장 흔한 mixed app 장면은 이렇다.

1. 사용자가 브라우저 주소창으로 `/admin` 페이지를 연다.
2. 비로그인 상태면 Spring Security가 `/login`으로 보낸다.
3. 같은 앱의 프론트엔드 코드가 `fetch("/api/me")`를 호출한다.
4. 이 요청은 login HTML이 아니라 `401` JSON을 받는 편이 프론트엔드 상태 처리에 맞다.

설정 감각도 두 갈래로 읽으면 된다.

```java
@Bean
SecurityFilterChain apiChain(HttpSecurity http) throws Exception {
    return http
        .securityMatcher("/api/**")
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .exceptionHandling(ex -> ex.authenticationEntryPoint(new Api401EntryPoint()))
        .build();
}

@Bean
SecurityFilterChain webChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/login", "/css/**").permitAll()
            .anyRequest().authenticated()
        )
        .formLogin(Customizer.withDefaults())
        .build();
}
```

이 코드를 외우기보다, 초급자는 아래 두 문장만 잡으면 충분하다.

- `/api/**`는 실패를 data 계약으로 돌려준다.
- 페이지 요청은 필요하면 login 화면으로 이동시킨다.

## 더 깊이 가려면

- `302 /login`과 `403`을 먼저 갈라야 한다면 [Spring 관리자 요청이 `302 /login`이 될 때와 `403`이 될 때: 초급 브리지](./spring-admin-302-login-vs-403-beginner-bridge.md)를 먼저 본다. 이 경로는 beginner 기준 `accessdeniedhandler` 재진입점으로 생각하면 된다.
- `/admin/**`는 login redirect, `/api/**`는 `401` JSON으로 안전하게 분리하는 실제 설정 감각이 필요하면 [Spring `SecurityFilterChain`을 둘로 나눠 `/admin/**`은 `302 /login`, `/api/**`는 `401` JSON으로 안전하게 다루는 입문 primer](./spring-securityfilterchain-multiple-entrypoints-primer.md)로 이어 간다.
- "결국 누가 `302`와 `401`을 최종 결정하나?"가 궁금해지면 [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](./spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)로 내려간다. 이 경로는 `authenticationentrypoint` 책임을 다시 잡는 재진입점이다.
- 로그인 후 원래 URL 복귀 자체가 궁금하면 [Spring Security `RequestCache`, `SavedRequest`, and Login Redirect Boundaries](./spring-security-requestcache-savedrequest-boundaries.md)를 이어 본다.
- 로그인 후 원래 URL로 돌아왔는데 마지막 `403`이 섞여 보인다면 [Spring 로그인 성공 후 원래 관리자 URL로 돌아왔는데도 마지막에 `403`이 나는 이유: `SavedRequest`와 역할 매핑 초급 primer](./spring-admin-login-success-but-final-403-savedrequest-role-mapping-primer.md)를 먼저 거친다.
- 브라우저 DevTools 기준으로 `401`과 `302` 증상을 먼저 나누고 싶다면 [Security: Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)를 먼저 본다.
- 쿠키와 세션 자체가 아직 흐리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)부터 다시 맞춘다.

## 면접/시니어 질문 미리보기

> Q: 같은 Spring 앱인데 어떤 요청은 `302 /login`, 어떤 요청은 `401`이 되는 이유는 무엇인가?
> 의도: browser page 계약과 JSON API 계약 분리 확인
> 핵심: 둘 다 인증 실패일 수 있지만, 페이지 요청은 redirect UX가 자연스럽고 API 요청은 상태 코드와 JSON 응답이 자연스럽다.

> Q: `fetch("/api/me")`가 `401` JSON 대신 login HTML을 받으면 무엇을 먼저 의심해야 하는가?
> 의도: browser redirect 정책과 API 경계 분리 확인
> 핵심: API 경로에 form login용 entry point나 request cache가 섞였는지 먼저 본다.

> Q: `403`은 왜 `302` vs `401` 이야기와 다른 축인가?
> 의도: authentication failure와 authorization failure 분리 확인
> 핵심: `403`은 로그인 후 권한 부족이고, `302`와 `401`은 보통 아직 인증 안 됐을 때의 표현 방식 차이다.

## 한 줄 정리

같은 Spring MVC 앱에서도 브라우저 페이지는 `302 /login`, JSON API는 `401`이 더 자연스러운 계약일 수 있으므로, mixed app 인증 실패는 "누가 이 응답을 읽는가"부터 나눠서 봐야 한다.
