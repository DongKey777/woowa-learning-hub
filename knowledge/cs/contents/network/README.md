---
schema_version: 3
title: Network 네트워크 라우팅 인덱스
concept_id: network/network-routing-index
canonical: true
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 94
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- network-first-router
- http-browser-entrypoint
- beginner-navigation
aliases:
- network readme
- 네트워크 처음 라우터
- HTTP 요청 흐름 뭐부터
- browser request lifecycle basics
- status redirect cache cookie route
- 302 303 304 401 basics
- network category entrypoint
symptoms:
- 네트워크를 처음 볼 때 request lifecycle, status code, redirect, PRG, cache, cookie/session 중 어디서 시작할지 모르겠다
- 302, 303, 304, 401이 한 덩어리로 보이고 이동, cache, 인증을 다음 행동 기준으로 자르지 못한다
- HTTP 질문에서 갑자기 Spring, Security, proxy, Alt-Svc 같은 운영형 갈래로 내려가며 beginner entrypoint를 잃는다
intents:
- troubleshooting
- definition
- comparison
prerequisites: []
next_docs:
- network/http-request-response-basics-url-dns-tcp-tls-keepalive
- network/http-status-codes-basics
- network/redirect-vs-forward-vs-spa-navigation-basics
- network/post-redirect-get-prg-beginner-primer
- network/http-caching-conditional-request-basics
- network/cookie-session-jwt-browser-flow-primer
linked_paths:
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
- contents/network/http-status-codes-basics.md
- contents/network/redirect-vs-forward-vs-spa-navigation-basics.md
- contents/network/post-redirect-get-prg-beginner-primer.md
- contents/network/http-caching-conditional-request-basics.md
- contents/network/cookie-session-jwt-browser-flow-primer.md
- contents/security/session-cookie-jwt-basics.md
confusable_with:
- network/http-status-codes-basics
- network/redirect-vs-forward-vs-spa-navigation-basics
- network/http-caching-conditional-request-basics
- network/cookie-session-jwt-browser-flow-primer
- security/session-cookie-jwt-basics
forbidden_neighbors: []
expected_queries:
- 네트워크 처음 공부할 때 요청 흐름 상태 코드 redirect cache cookie 중 어디서 시작해야 해?
- 302 303 304 401이 헷갈릴 때 network beginner route를 잡아줘
- 브라우저 request lifecycle에서 URL DNS TCP TLS HTTP status Keep-Alive 순서를 먼저 보고 싶어
- POST 다음 GET이 보이면 PRG인지 redirect인지 cache인지 어떻게 나눠?
- HTTP 다음 Spring이나 Security로 넘어가기 전에 Network 입구 문서로 정리해줘
contextual_chunk_prefix: |
  이 문서는 network category의 beginner routing index다. request lifecycle, HTTP status,
  redirect/PRG, cache, cookie/session을 첫 갈래로 나누고, Spring/Security/proxy/Alt-Svc
  운영형 갈래로 내려가기 전의 복귀 지점을 제공한다.
---
# Network (네트워크)

> 한 줄 요약: 이 README는 네트워크 카테고리의 입구로, 처음 보는 사람이 `요청 흐름`, `상태 코드`, `redirect/PRG`, `cookie/session`, `cache` 중 어디서 시작할지 증상 질문 기준으로 빠르게 고르게 돕는다.
**난이도: 🟢 Beginner**

관련 문서:

- [Network 처음 읽는 5장: beginner entrypoint](#처음-읽는-5장)
- [Network primer 되돌아가기: 길을 잃었을 때 복귀 지점](#network-primer-되돌아가기)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Spring 카테고리 README: HTTP에서 MVC/DI/트랜잭션으로 넘어가는 첫 10분](../spring/README.md#처음-10분-라우트)
- [Security: Session / Cookie / JWT basics](../security/session-cookie-jwt-basics.md)
- [Security README: `401`/`403`/login loop를 다시 자르는 browser/session 라우트](../security/README.md#browser--session-beginner-ladder)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [CS 루트 README: 카테고리 전체 Quick Routes](../../README.md#quick-routes)

retrieval-anchor-keywords: network readme basics, network beginner, network 뭐부터 읽지, network 처음 헷갈려요, browser request lifecycle basics, http status basics, redirect basics, prg basics, cookie session basics, cache basics, 302 303 304 401 basics, beginner network route, network category return path, what is network basics, http 다음 spring 뭐부터
> 작성자 : [권혁진](https://github.com/KimKwon), [서그림](https://github.com/Seogeurim), [윤가영](https://github.com/yoongoing)

## 이번 바퀴는 여기까지만

이 README는 beginner가 network 전체 catalog를 다 훑으라고 만든 문서가 아니다. 처음이면 아래 5개 entry만 먼저 고르고, `421`, `Alt-Svc`, gateway timeout, proxy incident, mesh tuning 같은 운영형 갈래는 관련 문서 링크로만 넘긴다.

| 지금 막힌 첫 질문 | 먼저 읽을 entry | 여기서 멈춰도 되는 이유 |
|---|---|---|
| "`url` 입력 뒤 뭐가 먼저 일어나요?" | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) | request lifecycle 큰 그림이 먼저 서야 뒤 문서가 덜 섞인다 |
| "`302` `303` `304` `401`이 왜 다르게 보여요?" | [HTTP 상태 코드 기초](./http-status-codes-basics.md) | 상태 코드를 `다음 행동` 기준으로 먼저 자른다 |
| "화면은 바뀌었는데 누가 이동시켰죠?" | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) | redirect, forward, SPA 이동 주체를 먼저 분리한다 |
| "`POST` 다음 `GET`이 보여요" | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | 폼 제출 마무리를 `POST -> redirect -> GET`으로 읽는다 |
| "같은 URL인데 `304`나 `from disk cache`가 보여요" | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) | body 재사용과 재검증을 먼저 구분한다 |

beginner return path는 이 한 줄이면 충분하다.

`request lifecycle -> status -> redirect/PRG -> cache -> cookie/session`

## 이 README를 쓰는 법

처음 읽을 때는 `처음 1분 라우트`, `빠른 탐색 메모`, `처음 읽는 5장`만 먼저 쓰면 된다. `421`, `alt-svc`, proxy timeout, mesh local reply처럼 운영형 키워드는 첫 바퀴에서 바로 내려가지 말고, 필요한 경우에만 아래 목차에서 찾아간다.

- beginner 첫 클릭은 `request lifecycle`, `status`, `redirect/PRG`, `cache`, `cookie/session` 다섯 갈래 중 하나만 고른다.
- spring 용어가 먼저 튀어나오면 [`Spring 카테고리 README`](../spring/README.md#처음-10분-라우트)로 한 칸만 넘기고, 다시 이 README로 돌아와도 된다.
- browser 저장/전송 관찰이 먼저 필요하면 cookie/session/cache 라인부터, transport나 timeout 책임이 궁금하면 network deep dive로 늦게 내려간다.

## category-local 목차

- beginner 입구: [`처음 1분 라우트`](#처음-1분-라우트), [`처음 읽는 5장`](#처음-읽는-5장), [`network primer 되돌아가기`](#network-primer-되돌아가기)
- browser 관찰 축: [`http 요청-응답 기본 흐름`](#http-요청-응답-기본-흐름), [`http 상태 코드 기초`](#http-상태-코드-기초), [`redirect vs forward vs spa router navigation 입문`](#redirect-vs-forward-vs-spa-navigation-입문), [`cookie / session / jwt 브라우저 흐름 입문`](#cookie--session--jwt-브라우저-흐름-입문), [`http 캐싱과 조건부 요청 기초`](#http-캐싱과-조건부-요청-기초)
- transport 심화: `http/2`, `http/3`, `grpc`, `alt-svc`, `connection coalescing`, `flow control`
- 운영 심화: `proxy`, `gateway`, `timeout`, `retry`, `disconnect`, `load balancer`, `service mesh`
- cross-category handoff: [`spring 카테고리 README`](../spring/README.md#처음-10분-라우트), [`security README`](../security/README.md#browser--session-beginner-ladder), [`cs 루트 quick routes`](../../README.md#quick-routes)

---

## 빠른 탐색

이 `README`는 network category 입구다. 처음이면 아래 `처음 읽는 5장`, `상태 코드 / redirect / PRG로 바로 가기`, `브라우저 / 쿠키 / 캐시에서 막히면 여기서 시작`까지만 따라가면 된다. `421`, proxy incident, timeout blame, H3 discovery, runbook 같은 운영형 가지는 beginner 첫 바퀴에서 중심으로 읽지 않는다.

browser beginner 3단계:
`request lifecycle` -> `status/redirect` -> `cookie/session/cache`

## 처음 1분 라우트

처음엔 topic 이름보다 "`지금 뭐가 바뀌었나`"를 먼저 보면 entry 선택이 빨라진다.

| 지금 보인 변화 | 먼저 읽을 문서 | 한 줄 이유 |
|---|---|---|
| 요청 자체가 어디서 시작되는지 흐리다 | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) | request lifecycle부터 잡아야 뒤 문서가 덜 헷갈린다 |
| `302`, `303`, `304`, `401`이 한 덩어리로 보인다 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) | 이동, cache, 인증을 질문 축으로 먼저 자른다 |
| URL이 바뀌었거나 화면 이동 주체가 헷갈린다 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) | 누가 이동을 결정했는지 먼저 분리한다 |
| `POST` 다음 `GET`이 보여 새로고침이 불안하다 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | 폼 제출 마무리를 `POST -> redirect -> GET`으로 읽는다 |
| 같은 URL인데 `304`, `from memory cache`가 보인다 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) | body 재사용과 서버 재검증을 먼저 가른다 |
| API 호출인데 JSON 대신 HTML이나 정체불명 JSON 에러가 온다 | [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md) | `Status`/`Content-Type`/preview 3칸으로 app JSON, gateway JSON, login HTML을 먼저 가른다 |
| `404 problem+json`인데 `No static resource`가 보여 controller가 만든 건지 헷갈린다 | [Spring `404` `ProblemDetail`: framework `No static resource` vs domain not found bridge](./spring-404-problemdetail-framework-vs-domain-bridge.md) | framework 기본 `404`와 app domain `404`를 먼저 가른다 |

짧은 추천 순서는 이렇다.

`request lifecycle -> status -> redirect/PRG -> cache`

## 빠른 탐색 메모

- 길을 잃으면 여기로 돌아오기: [`빠른 탐색`](#빠른-탐색)에서 증상축을 고르고, Spring 요청 처리 질문이면 [`Spring 카테고리 README`](../spring/README.md)로 건너간다.
- beginner return path: "`302`/`304`/`401`이 왜 헷갈려요?", "`cookie는 저장됐는데 왜 안 붙어요?`", "`HTTP 다음에 Spring은 어디 봐요?`"는 아래 5개 primer 중 하나로 시작하고 막히면 다시 이 섹션으로 복귀한다.
- beginner scope guard: "`왜 H3로 갔지?`", "`proxy timeout은 누구 책임이지?`", "`JWT/CSRF/BFF까지 지금 같이 봐야 하나?`"가 붙어도 이번 턴에서는 먼저 `request lifecycle`, `status`, `cookie 전송`, `cache 재사용` 중 하나만 고른다. 더 깊은 갈래는 아래 follow-up 문서로 뒤로 미룬다.
- 버전/브라우저 cache 실험이 커질 때: [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)
- 로그인 복귀 URL과 저장 흐름이 같이 헷갈릴 때: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- cross-site cookie와 `fetch credentials`까지 커질 때: [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- auth 증상으로 넘어가면: `401`, `403`, `login loop`, `cookie 있는데 다시 로그인`은 [Security README: Browser / Session Beginner Ladder](../security/README.md#browser--session-beginner-ladder)에서 다시 자른다.
- cross-category bridge: "`HTTP 다음에 Spring은 뭐부터 봐요?`"라면 [`Network -> Spring handoff`](#network---spring-handoff)에서 [`Spring 처음 10분 라우트`](../spring/README.md#처음-10분-라우트)로 한 칸만 넘어가고, Spring 용어가 갑자기 많아지면 다시 [`Network primer 되돌아가기`](#network-primer-되돌아가기)로 돌아온다.
- category navigator return: network 안에서도 길을 잃으면 [`처음 읽는 5장`](#처음-읽는-5장)으로 복귀하고, 카테고리 자체를 다시 고르고 싶으면 [`CS 루트 Quick Routes`](../../README.md#quick-routes)로 바로 돌아간다.

## 처음 읽는 사람 규칙

- `302`, `303`, `304`, cookie, request lifecycle가 아직 헷갈리면 `421`, `Alt-Svc`, gateway timeout, proxy 운영 문서로 내려가지 않는다.

## 30초 출발점

처음 보는 사람이 "`어디서부터 읽지?`"를 빨리 끊으려면 status 숫자보다 먼저 `url`, `method`, `body` 중 뭐가 바뀌었는지만 본다.

| 지금 먼저 보인 변화 | 먼저 갈 entry 문서 | 여기서 답하려는 질문 |
|---|---|---|
| url이 바뀌었다 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) | 누가 이동을 결정했는가 |
| `post` 뒤 `get`이 붙었다 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | 왜 결과 화면을 `get`으로 다시 여는가 |
| 같은 url인데 `304`가 보인다 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) | 이동이 아니라 body 재사용 질문인가 |
| `/login`이나 `401`에서 멈춘다 | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) | 인증이 빠졌나, 세션이 끊겼나 |
| 요청 자체가 어디서 시작되는지 흐리다 | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) | 브라우저 요청 lifecycle이 어떻게 이어지는가 |

한 줄로 줄이면 이렇다.

- url 변화는 redirect 질문이다.
- `post -> get` 변화는 prg 질문이다.
- 같은 url의 body 재사용은 cache 질문이다.
- `/login`, `401`은 cookie/session 질문이다.

헷갈리면 이 짧은 loop로만 움직여도 된다.

`request lifecycle -> status -> redirect/PRG -> cache -> cookie/session`

## 한 번에 보는 example pass cycle

처음에는 `request lifecycle`, `status`, `redirect/PRG`, `cache`가 각각 다른 문서 이름으로만 보여서 어디서 끊어 읽어야 할지 헷갈리기 쉽다. 아래 한 사이클만 잡으면 beginner가 가장 자주 묻는 "`왜 `POST` 다음에 `GET`이 보여요?`", "`왜 그다음엔 `304`예요?`"를 한 장면에서 분리할 수 있다.

| 순서 | trace에서 보이는 것 | 지금 먼저 붙일 질문 | 먼저 갈 문서 |
|---|---|---|---|
| 1 | URL 입력 뒤 `DNS`, `Connect`, `SSL` | 요청이 어디서부터 출발했는가 | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) |
| 2 | `POST /orders -> 303 See Other` | 왜 결과 화면 주소를 따로 알려 주는가 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| 3 | `GET /orders/42 -> 200 OK` | 브라우저가 결과 화면을 정상 도착했는가 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |
| 4 | 새로고침 뒤 `GET /orders/42 -> 304 Not Modified` | 같은 URL body를 다시 받아야 하나 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |

짧게 고정하면 이렇다.

- `303`은 이동과 `POST -> GET` 마무리 질문이다.
- `200`은 최종 도착 장면이다.
- `304`는 같은 URL body 재사용 질문이다.
- 그래서 `303 -> 200 -> 304`는 서로 모순이 아니라 한 브라우저 흐름의 다른 장면이다.

## beginner 자주 하는 한 문장 질문

처음엔 용어보다 질문 문장으로 entry를 고르는 편이 빠르다.

| learner 질문 | 먼저 갈 문서 | 왜 여기서 시작하나 |
|---|---|---|
| "`새로고침했는데 왜 js는 304고 로그인은 그대로예요?`" | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) | cache 재사용과 login 유지가 다른 축임을 한 번에 자른다 |
| "`hard reload`하니 200인데 평소엔 304예요. 뭐가 진짜예요?`" | [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md) | 실험 스위치와 평소 cache 정책을 분리한다 |
| "`Application`에 cookie는 있는데 왜 다시 로그인해요?`" | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) | 저장, 전송, 인증 성공을 다른 체크로 분리한다 |
| "`from memory cache`랑 `304`가 왜 달라요?`" | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) | body 재사용과 서버 재검증을 나눠 읽게 만든다 |

짧은 route:

`reload 차이` -> `cache trace` -> `cookie/session` 순서가 아니라, 먼저 **지금 질문이 body 재사용인지 login 상태인지**를 고른다.

헷갈리면 더 짧게 아래 한 줄만 기억하면 된다.

- `304`/`from memory cache` = body 재사용
- `Cookie`/`Set-Cookie` = 브라우저 저장과 전송
- `/me -> 200/401/302` = 로그인 복원 결과

## beginner 멈춤선

이 README는 catalog도 같이 품고 있어서 처음 보는 사람은 아래 선에서 한 번 멈추는 편이 안전하다.

| 지금 상태 | 여기서 멈춰도 되는 이유 | 다음 문서 |
|---|---|---|
| "`요청이 어떻게 흘러가는지` 자체가 아직 흐릿하다" | request lifecycle이 안 잡히면 상태 코드와 cache 해석도 같이 흔들린다 | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) |
| "`302` `304` `401`이 한 장면에서 같이 보여요" | redirect, cache, 인증을 먼저 세 갈래로 나눠야 한다 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |
| "`cookie`, `session`, `cache`가 다 같은 상태처럼 들려요" | browser 저장, server 복원, body 재사용을 먼저 분리해야 한다 | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |
| "DevTools 실험값인지 실제 사용자 흐름인지 모르겠어요" | `hard reload`, `Disable cache`는 관찰 조건을 흔든다 | [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md) |

아래 catalog에서 `421`, `Alt-Svc`, proxy, retry, timeout 문서를 보고 싶어도 위 4칸 중 하나가 아직 비면 먼저 primer로 돌아온다. 이 README의 beginner 라우팅은 "운영 사고 원인 찾기"보다 "지금 본 장면을 어느 질문 축으로 읽을지"를 먼저 정하는 데 목적이 있다.

## beginner 먼저 보는 5갈래

| 지금 막힌 말 | 먼저 볼 문서 | 여기서 답하려는 질문 |
|---|---|---|
| "`URL` 넣고 나서 DNS, TCP, TLS가 뭐부터인지 모르겠어요" | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) | 브라우저 요청이 어디서부터 시작되는가 |
| "`302` `303` `304` `401`이 헷갈려요" | [HTTP 상태 코드 기초](./http-status-codes-basics.md) | 지금 본 숫자가 이동, cache, 인증 중 무엇인가 |
| "화면이 바뀌었는데 redirect예요? forward예요?" | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) | 누가 이동을 결정했는가 |
| "왜 `POST` 다음에 `GET`이 보여요?" | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | 왜 결과 화면을 `GET`으로 분리하는가 |
| "`304`, `from memory cache`, `Disable cache`가 같이 보여요" | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) | body를 다시 받는지, 그냥 재사용하는지, 실험값이 섞였는지 |

처음에는 위 다섯 문서 중 하나만 고르고, 답이 안 나오면 다음 칸으로 넘어간다. request lifecycle이 아직 흐리면 status/redirect/PRG를 바로 깊게 읽지 말고, `304`와 `from memory cache`가 섞이면 redirect보다 cache 문서로 먼저 가는 편이 안전하다.

## beginner 한 장면 판독 순서

처음 보는 Network trace를 glossary처럼 외우지 말고 아래 순서로 자르면 beginner가 가장 자주 막히는 `status`, `redirect`, `PRG`, `cache`를 한 장면에서 분리할 수 있다.

| 먼저 볼 변화 | 먼저 붙일 질문 | 먼저 볼 문서 |
|---|---|---|
| URL이 바뀌었는가 | redirect인가 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) |
| `POST` 뒤 `GET`이 붙었는가 | PRG인가 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| 같은 URL인데 body를 다시 안 받았는가 | cache 재사용인가 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| 그 자리에서 `401`이나 `/login`으로 멈췄는가 | 인증 문제인가 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |

한 줄로 줄이면 이렇다.

- URL 변화는 redirect 축이다.
- `POST -> GET` 변화는 PRG 축이다.
- 같은 URL body 재사용은 cache 축이다.
- 인증 부재는 상태 코드와 cookie/session 축이다.

`뭐부터 봐야 하지?`가 다시 생기면 아래 짧은 route만 기억해도 된다.

`request lifecycle -> status -> redirect/PRG -> cache -> cookie/session`

## 브라우저 / 쿠키 / 캐시 입구 3갈래

`Application`, `Cookie`, `304`, `hard reload`가 한 번에 보여 scope가 커질 때는 아래 셋 중 한 갈래만 먼저 고른다.

| 지금 보인 말 | 먼저 볼 문서 | 여기서 끊는 이유 |
|---|---|---|
| "`Set-Cookie`는 왔는데 다음 요청 `Cookie`가 없어요" | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) | 저장과 전송을 먼저 분리한다 |
| "`304`, `from memory cache`가 보여요" | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) | body 재사용 질문부터 자른다 |
| "`hard reload`하니 결과가 달라져요" | [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md) | 실험 스위치와 실제 정책을 분리한다 |

이 단계에서는 "`왜 H3로 갔는가`", "`왜 proxy timeout이 났는가`"보다 "`지금 본 차이가 저장, 재사용, 실험 중 무엇인가`"만 먼저 답하면 된다.

범위가 다시 커지면 아래처럼 한 칸만 더 내려간다.

- cookie는 저장됐는데 로그인 복귀나 원래 URL 이동까지 같이 헷갈리면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- same-site, cross-site, `fetch credentials`까지 붙으면 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- DevTools cache 실험이 H3, `Alt-Svc`, DNS cache 질문으로 커지면 [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)

즉 beginner 첫 바퀴에서는 아래 순서로만 좁힌다.

1. 저장소 문제인가
2. 로그인 복원 문제인가
3. body 재사용 문제인가
4. 그다음에만 H3/proxy/운영 문서로 간다

<a id="상태-코드--redirect--prg로-바로-가기"></a>
## 상태 코드 / redirect / PRG를 한 번에 자르는 1분 분기표

세 주제가 같이 보이면 glossary처럼 읽기 쉽다. 처음에는 숫자 뜻보다 "무엇이 바뀌었는가"만 먼저 자른다.

| 지금 먼저 볼 변화 | 이 변화가 뜻하는 질문 | 먼저 볼 문서 |
|---|---|---|
| URL이 바뀌었다 | 다른 목적지로 이동했는가 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) |
| `POST` 뒤 `GET`이 보인다 | 결과 화면을 `GET`으로 다시 열었는가 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| 같은 URL인데 `304`가 보인다 | body를 다시 받지 않고 재사용했는가 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| `/login`으로 가거나 `401`이 뜬다 | 이동 문제가 아니라 인증 부재인가 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |

위 표에서 막히지 않았다면 그때만 아래 catalog의 deep dive로 내려간다. beginner 첫 독해에서는 `421`, `H3`, timeout incident를 같은 단계에서 섞지 않는 편이 안전하다.

## `POST -> 303 -> GET -> 304` 예시를 한 번에 읽기

처음엔 숫자 이름을 다 외우지 말고 한 브라우저 pass cycle에서 무엇이 바뀌는지만 보면 된다.

| 순서 | 보이는 것 | 지금 답해야 하는 질문 | 먼저 볼 문서 |
|---|---|---|---|
| 1 | `POST /orders -> 303 See Other` | 결과 화면 주소를 따로 열라는 뜻인가 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| 2 | `GET /orders/42 -> 200 OK` | 브라우저가 redirect를 따라 새 결과 화면을 열었는가 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) |
| 3 | 새로고침 뒤 `GET /orders/42 -> 304 Not Modified` | 같은 URL body를 다시 받지 않고 재사용했는가 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |

한 줄로 자르면 이렇다.

- `303`은 "`POST` 결과를 다른 URL의 `GET`으로 다시 열라"는 흐름이다.
- `200`은 결과 화면이 실제로 열렸다는 뜻이다.
- `304`는 그 결과 화면을 다시 열 때 body를 재사용했다는 뜻이다.
- 같은 장면에 함께 보여도 redirect와 cache를 같은 뜻으로 읽으면 안 된다.

## beginner 공통 오해 4줄 컷

상태 코드, redirect, PRG, cache가 한 화면에서 같이 보이면 아래 네 문장이 가장 자주 섞인다.

| 헷갈리는 문장 | 빠른 정정 | 먼저 볼 문서 |
|---|---|---|
| "`302`도 보였는데 결국 성공했으니 같은 뜻 아닌가요?" | 아니다. `302`는 중간 이동 안내이고 최종 성공은 이어진 응답이 말한다 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |
| "`POST` 다음 `GET`이 보이니 중복 제출된 거죠?" | 꼭 아니다. 먼저 PRG인지 확인한다 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| "`303` 다음 `304`가 보이니 redirect가 두 번 난 건가요?" | 아니다. `303`은 이동, `304`는 같은 URL body 재사용이다 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| "`304`가 떴으니 로그인도 유지됐죠?" | 아니다. `304`는 body 재사용 신호이고 로그인 유지 여부는 `/me`, `401`, `302 /login`으로 본다 | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |

처음엔 이 네 문장만 분리해도 `status`, `redirect/PRG`, `cache`, `cookie/session`이 서로 다른 질문이라는 감각이 빨리 잡힌다.

## 처음엔 이 4칸만 분리

browser 관련 초급 질문은 아래 4칸만 먼저 자르면 glossary처럼 읽지 않아도 된다.

| 지금 구분할 축 | 한 줄 질문 | DevTools에서 먼저 볼 자리 | 먼저 볼 문서 |
|---|---|---|---|
| 저장 | "브라우저가 값을 저장했나?" | `Application > Cookies` | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |
| 전송 | "이번 요청에 실제로 실렸나?" | `Network > Request Headers > Cookie` | [Application 탭 vs Request Cookie 헤더 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md) |
| 인증/복원 | "서버가 로그인 상태로 인정했나?" | `/me` 같은 API의 `200/401/302` | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |
| body 재사용 | "이 응답 body를 다시 받았나?" | `304`, `from memory cache`, `from disk cache` | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |

한 줄 메모:

- `cookie가 저장됨`과 `request에 전송됨`은 같은 체크가 아니다.
- `304`와 `from memory cache`는 로그인 유지 신호가 아니라 body 재사용 신호다.
- `hard reload`는 평소 사용자 흐름이 아니라 실험 결과일 수 있다.

## beginner 예시 한 사이클

처음에는 숫자 뜻을 다 외우기보다 한 번의 browser pass cycle에서 "무슨 질문이 바뀌는가"만 자르면 된다.

| 순서 | DevTools에서 보이는 장면 | 먼저 붙일 질문 | 먼저 갈 문서 |
|---|---|---|---|
| 1 | `POST /login -> 200 + Set-Cookie` | 브라우저가 무엇을 저장했나 | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |
| 2 | `GET /me -> Cookie -> 200` | 서버가 로그인 상태를 복원했나 | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |
| 3 | `GET /app.js -> 304` 또는 `from memory cache` | 같은 body를 다시 받았나 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |

한 줄 메모:

- `Set-Cookie`는 저장 신호다.
- `/me -> 200/401/302`는 인증/복원 신호다.
- `304`, `from memory cache`는 body 재사용 신호다.

## 브라우저 / 쿠키 / 캐시에서 막히면 여기서 시작

`cookie`, `session`, `304`, `memory cache`는 모두 "이전 상태 재사용"처럼 들리지만 질문이 다르다. 아래 표에서 지금 보인 증상 한 줄만 먼저 고르면 된다.

| 지금 보인 장면 | 먼저 볼 문서 | 왜 이 문서부터인가 | 다음 한 걸음 |
|---|---|---|---|
| "`Set-Cookie`는 왔는데 다음 요청 `Cookie`가 비어요" | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) | 저장과 자동 전송을 먼저 분리한다 | [Application 탭 vs Request Cookie 헤더 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md) |
| "`cookie`는 있는데 왜 다시 로그인해요?" | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) | cookie 전달, session 복원, cache 재사용을 다른 질문으로 자른다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| "`sessionStorage`, `JSESSIONID`, 서버 session이 다 뭐가 달라요?" | [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md) | 탭 저장소, 브라우저 cookie, 서버 session을 먼저 다른 상자로 자른다 | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |
| "`Application`에 cookie, localStorage, cache storage가 다 보여서 뭐부터 봐야 할지 모르겠어요" | [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md) | 저장소별 질문을 `자동 전송`, `JS 직접 사용`, `SW cache`로 먼저 가른다 | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |

특히 아래 두 문장은 다른 질문이다.

- "`js가 304라서 로그인도 유지됐죠?`"는 빠르다. `304`는 body 재사용 신호다.
- "`hard reload`했더니 200이라 로그아웃된 거죠?`"도 빠르다. reload는 먼저 cache 실험 질문이고, login 유지 여부는 `/me`, `401`, `302 /login`으로 따로 본다.
## Cache와 Cookie를 같이 읽을 때

`304`, `from memory cache`, `Application` 탭 cookie는 같이 보여도 서로 다른 질문이다.

| 지금 보인 장면 | 먼저 볼 문서 | 왜 이 문서부터인가 | 다음 한 걸음 |
|---|---|---|---|
| "`304`랑 `from memory cache`가 왜 달라요?" | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) | body 출처와 재검증을 나눠 준다 | [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md) |
| "`Application`에 cookie는 있는데 `304`도 떠서 헷갈려요" | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) | 저장, 전송, 인증, body 재사용을 4칸으로 끊는다 | [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md) |
| "`Cache Storage`에도 있고 `304`도 떠요. 같은 cache예요?" | [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md) | Service Worker용 저장소와 브라우저 HTTP cache를 먼저 분리한다 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |
| "`X-Cache`나 `Age`가 보여요. 이건 app 응답이에요, CDN 응답이에요?" | [Browser DevTools `X-Cache` / `Age` 1분 헤더 카드](./browser-devtools-x-cache-age-ownership-1minute-card.md) | cache 관련 헤더를 edge/cache ownership 후보로 먼저 읽게 만든다 | [CDN Vendor Header Crosswalk Mini Card: CloudFront / Cloudflare 단서 읽기](./cdn-vendor-header-crosswalk-cloudfront-cloudflare-mini-card.md) |

## 새로고침과 상태 코드가 헷갈릴 때

`302`, `304`, `401`, `hard reload`는 모두 새로고침 장면에서 한 번에 보일 수 있지만, redirect/auth/cache/실험 스위치라는 서로 다른 질문이다.

| 지금 보인 장면 | 먼저 볼 문서 | 왜 이 문서부터인가 | 다음 한 걸음 |
|---|---|---|---|
| "`302`인지 `304`인지 `401`인지`부터 헷갈려요" | [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md) | redirect, cache, unauthenticated를 같은 새로고침 장면에서 끊어 준다 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |
| "`hard reload`하니 `200`인데 평소엔 `304`예요. 뭐가 진짜예요?" | [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md) | 실험 스위치와 실제 cache 정책을 같은 뜻으로 묶지 않게 해 준다 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |

<a id="network---spring-handoff"></a>
## Network -> Spring handoff

browser 증상이 먼저면 [`HTTP 상태 코드 기초`](./http-status-codes-basics.md), [`Cookie / Session / JWT 브라우저 흐름 입문`](./cookie-session-jwt-browser-flow-primer.md), [`HTTP 캐싱과 조건부 요청 기초`](./http-caching-conditional-request-basics.md)로 한 칸 되돌아간다. `request -> controller -> database flow`가 처음이면 [`HTTP 요청-응답 기본 흐름`](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [`Spring 요청 파이프라인과 Bean Container 기초`](../spring/spring-request-pipeline-bean-container-foundations-primer.md) -> [`Database First-Step Bridge`](../database/database-first-step-bridge.md)만 먼저 유지한다.

`json` 요청인데 controller 전에 `415`가 보이면 database로 내려가지 않고 [`Browser DevTools \`Accept\` vs Response \`Content-Type\` 미니 카드`](./browser-devtools-accept-vs-content-type-mini-card.md) -> [`Spring @RequestBody 415 Unsupported Media Type 초급 primer`](../spring/spring-requestbody-415-unsupported-media-type-primer.md) 순서로 한 칸만 더 간다.

짧게는 `network primer -> spring bridge -> database bridge`만 기억한다. Spring으로 넘어간 뒤에도 category 입구가 필요하면 [`Spring 처음 10분 라우트`](../spring/README.md#처음-10분-라우트)에서 다시 시작하면 되고, Spring 용어가 갑자기 빨라지면 [`Spring primer 되돌아가기`](../spring/README.md#spring-primer-되돌아가기) 또는 [`처음 읽는 5장`](#처음-읽는-5장)으로 한 칸 복귀한다. 다시 category 단위로 고르고 싶으면 [`역할별 라우팅 요약`](#역할별-라우팅-요약)이나 [`CS 루트 Quick Routes`](../../README.md#quick-routes)까지 바로 돌아간다.

<a id="network---spring-handoff-예시"></a>
## Network -> Spring handoff 예시

| 지금 막힌 beginner 문장 | primer | follow-up 한 칸 | deep dive는 나중에 |
|---|---|---|---|
| "`HTTP 다음에 Spring은 뭐부터 봐요?`" | [HTTP 요청-응답 기본 흐름](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | filter ordering, async timeout |
| "`controller`는 보이는데 `save()` 뒤 SQL이 안 보여요" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Database First-Step Bridge](../database/database-first-step-bridge.md) -> [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | deadlock, failover, replay |
| "`302`/`304`/`cookie`가 아직 헷갈려서 Spring으로 못 넘어가겠어요" | [HTTP 상태 코드 기초](./http-status-codes-basics.md), [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) | [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md) | Spring Security session deep dive |
| "Spring primer까지 갔는데 다시 category 입구가 필요해요" | [Spring primer 되돌아가기](../spring/README.md#spring-primer-되돌아가기) | [Network primer 되돌아가기](#network-primer-되돌아가기) 또는 [CS 루트 Quick Routes](../../README.md#quick-routes) | Security, transaction, H3 incident docs |

`처음`, `뭐예요`, `헷갈려` 검색에서는 이 사다리가 먼저 잡혀야 한다.

<a id="network-primer-되돌아가기"></a>
## Network primer 되돌아가기

primer를 읽다가 "`지금은 너무 운영 쪽이다`", "`아직 browser 쪽부터 다시 잡아야겠다`" 싶으면 여기서 다시 한 칸만 고른다.

| 지금 다시 막힌 말 | README에서 되돌아갈 곳 | 왜 이 복귀점이 안전한가 |
|---|---|---|
| "`302`, `303`, `304`, `401`이 한 화면에 같이 보여서 뭐부터 읽을지 모르겠어요" | [`상태 코드 / redirect / PRG로 바로 가기`](#상태-코드--redirect--prg로-바로-가기) | 새로고침, redirect, auth, PRG를 beginner 기준으로 다시 나눠 준다 |
| "`HTTP 다음에 Spring은 어디로 넘어가요?`" | [`Network -> Spring handoff`](#network---spring-handoff), [`Spring 처음 10분 라우트`](../spring/README.md#처음-10분-라우트) | category handoff와 Spring primer 입구를 한 번에 고정한다 |
| "`controller` 뒤 SQL이나 트랜잭션이 궁금한데 아직 DB 문서가 낯설어요" | [`Network -> Spring handoff 예시`](#network---spring-handoff-예시) | Spring bridge 다음에 DB bridge로 넘어가는 최소 경로만 다시 보여 준다 |
| "문서가 많아서 network 카테고리나 전체 CS에서 다시 고르고 싶어요" | [`처음 읽는 5장`](#처음-읽는-5장), [`CS 루트 Quick Routes`](../../README.md#quick-routes) | network primer 입구와 전체 네비게이터를 같이 보여 줘서 안전하게 복귀할 수 있다 |

## 되돌아가기와 다음 한 걸음

| 지금 막힌 beginner 문장 | 여기서 바로 갈 곳 | 왜 이 링크가 안전한가 |
|---|---|---|
| "`421`, `Alt-Svc` 문서까지 봤는데 너무 빨라요" | [`처음 읽는 5장`](#처음-읽는-5장) | 운영형 deep dive를 끊고 primer 5장으로 되돌아가게 해 준다 |
| "`HTTP 다음에 Spring은 어디로 넘어가요?`" | [`Network -> Spring handoff`](#network---spring-handoff), [`Spring 처음 10분 라우트`](../spring/README.md#처음-10분-라우트) | category handoff와 Spring primer 입구를 한 번에 보여 준다 |
| "문서가 많아서 다시 category 단위로 고르고 싶어요" | [`역할별 라우팅 요약`](#역할별-라우팅-요약), [`CS 루트 Quick Routes`](../../README.md#quick-routes) | network 내부 라우팅과 전체 카테고리 네비게이터 둘 다 안전한 복귀점이다 |
| "primer 한 장은 읽었는데 다음에 뭘 눌러야 할지 모르겠어요" | [`Network primer 되돌아가기`](#network-primer-되돌아가기), [`Network -> Spring handoff`](#network---spring-handoff) | 같은 beginner 질문 축에서 다음 한 칸만 고르게 하고, 필요하면 Spring bridge까지 자연스럽게 연결한다 |

<a id="처음-읽는-5장"></a>
## 처음 읽는 5장

- 처음 읽는다면 이 5개부터:
  - [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) — 브라우저 주소 입력 뒤 request lifecycle 전체와 `request vs response`, `HTTP keep-alive vs TCP keepalive`를 먼저 구분하는 첫 문서
  - [HTTP 상태 코드 기초](./http-status-codes-basics.md) — `302`/`303`/`304`/`401`/`403`/`404`를 "누가 다음 행동을 해야 하는가" 기준으로 읽는 상태 코드 입문
  - [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) — "`화면이 바뀌었다`"를 redirect, server-side forward, SPA 라우터 이동으로 나눠 읽는 primer
  - [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) — `Set-Cookie` 저장, `Cookie` 자동 전송, 서버 세션/JWT 검증을 한 표로 구분하는 브라우저 상태 entry
  - [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) — `from disk cache`와 `304`를 먼저 갈라 cache mental model을 세우는 follow-up

이 5장 중 하나를 읽고 나면 바로 deep dive로 내려가기보다 [`Network primer 되돌아가기`](#network-primer-되돌아가기)에서 다음 질문 축을 다시 고르거나 [`Spring 처음 10분 라우트`](../spring/README.md#처음-10분-라우트)로 한 칸만 넘어가는 편이 junior reader에게 안전하다.

- next step bridge: "`HTTP 다음에 Spring은 어디서 받아요?`", "`controller`부터 보고 싶어요"가 바로 나오면 [`Network -> Spring handoff`](#network---spring-handoff)에서 [`Spring 처음 10분 라우트`](../spring/README.md#처음-10분-라우트)로 한 칸만 넘어간다.
- safe return path: primer를 읽다가 "`다시 network 카테고리에서 고를래요`"가 되면 [`Network primer 되돌아가기`](#network-primer-되돌아가기)로, 카테고리 자체를 다시 고르려면 [`CS 루트 Quick Routes`](../../README.md#quick-routes)로 복귀한다.

## 처음이면 여기서 멈춰도 된다

처음 배우는데 "`Alt-Svc`가 뭐예요?", "`421`까지 지금 알아야 하나요?", "`runbook`도 같이 읽어야 하나요?"가 바로 붙으면 아래 기준으로 범위를 자른다.

| 지금 질문 | 여기서 먼저 멈출 문서 | 더 깊은 follow-up은 나중에 |
|---|---|---|
| "`302` `303` `304` `401`이 헷갈려요" | [HTTP 상태 코드 기초](./http-status-codes-basics.md) | `421`, coalescing, H3 recovery는 나중에 |
| "`POST` 다음에 왜 `GET`이 보여요?" | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | 로그인 redirect 세부와 `SavedRequest`는 나중에 |
| "`304`랑 `from disk cache`가 왜 달라요?" | [HTTP 캐싱과 조건부 요청 기초](./http-caching-conditional-request-basics.md) | H2/H3 fallback, CDN edge case는 나중에 |
| "`URL` 입력 뒤 무슨 일이 일어나요?" | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) | timeout/abort/runbook 계열은 나중에 |

## 상태 코드 / redirect / PRG로 바로 가기

| learner query shape | 먼저 볼 문서 | 다음 한 걸음 |
|---|---|---|
| "`302` `303` `304` `401`이 왜 다 다르게 읽혀요?", "상태 코드 처음인데 뭐부터 봐요?" | [HTTP 상태 코드 기초](./http-status-codes-basics.md) | [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md) |
| "로그인 뒤 화면이 바뀌었는데 redirect예요? forward예요?", "왜 URL은 안 바뀌는데 화면만 바뀌죠?" | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) | [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) |
| "새로고침하면 다시 제출돼요", "왜 `POST` 다음에 `GET`이 보여요?" | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| "`POST -> 303 -> GET`까지는 알겠는데, 새로고침하니 왜 또 `304`가 보여요?", "`303`이랑 `304`가 한 흐름에서 같이 보여도 정상인가요?" | [HTTP 상태 코드 기초](./http-status-codes-basics.md) | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) -> [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md) |
| "`cookie`는 있는데 왜 다시 로그인해요?", "`304`가 떴는데 그럼 로그인 유지된 거 아닌가요?" | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) -> [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |

## beginner 3단계 사다리: 상태 코드 -> 이동 방식 -> 새로고침

`처음`, `헷갈려요`, `왜 POST 다음에 GET`, `왜 302인데 성공처럼 보여요` 같은 질문은 아래 사다리로 읽으면 glossary처럼 튀지 않고 흐름이 이어진다.

| step | learner symptom phrase | 먼저 볼 문서 | 여기서 답하려는 한 질문 |
|---|---|---|---|
| 1 | "`302` `303` `304` `401`이 뭐예요?" | [HTTP 상태 코드 기초](./http-status-codes-basics.md) | 지금 본 숫자가 목적지 이동인지, body 재사용인지, 인증 실패인지 |
| 2 | "화면이 바뀌었는데 redirect예요? forward예요?" | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) | 누가 이동을 결정했는지 |
| 3 | "왜 `POST` 다음에 `GET`이 보여요?", "새로고침하면 다시 제출돼요?" | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | 왜 결과 화면을 `GET`으로 분리하는지 |

이 세 문서를 다 읽은 뒤에도 `304`, `from memory cache`, `Disable cache`가 다시 꼬이면 cache 질문으로 축이 바뀐 것이므로 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)로 이동한다.

한 줄로 요약하면 `숫자 읽기 -> 이동 주체 읽기 -> form submit 마무리 읽기` 순서다. 이 순서를 지키면 beginner가 `302`, `303`, `304`, `401`을 한 장면에서 같은 뜻으로 묶는 실수를 줄일 수 있고, 운영형 deep dive를 너무 일찍 여는 것도 막을 수 있다.

## 초보자용 한 번에 묶는 trace

| trace에서 보이는 순서 | 초보자용 한 줄 해석 | 먼저 읽을 문서 |
|---|---|---|
| `POST /orders -> 303 See Other` | 서버가 "결과 화면은 다른 URL의 `GET`으로 다시 열어라"라고 말했다 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| `GET /orders/42 -> 200 OK` | 브라우저가 redirect를 따라가 결과 화면을 열었다 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) |
| 새로고침 뒤 `GET /orders/42 -> 304 Not Modified` | 실패가 아니라 같은 URL 결과를 cache 재검증 뒤 재사용했다 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |

이 trace는 beginner가 가장 자주 묻는 "`왜 POST 다음에 GET이 보이고, 또 새로고침하면 304가 떠요?`"를 한 번에 묶어 읽는 최소 예시다. 핵심은 `303`이 **다음 목적지 URL**을 바꾸고, `304`가 **같은 URL의 body 재사용 여부**를 말한다는 점이다.

같은 묶음에서 "`그럼 `307`은 왜 달라요?`"가 바로 붙으면 PRG 문서의 `302`/`303`/`307` 비교표로 내려가면 된다. beginner 기준으로는 "`결과 화면을 `GET`으로 다시 열어라`"면 `303`, "`방금 보낸 `POST`를 그대로 다시 보내라`"면 `307`로 먼저 끊는 편이 가장 덜 헷갈린다.

## 브라우저 저장소와 cache를 같이 헷갈릴 때

`cookie`, `session`, `localStorage`, `304`, `from memory cache`는 모두 "이전 상태가 남아 있다"처럼 들리지만 실제 질문은 다르다. 아래 두 문서를 붙여 읽으면 beginner가 가장 자주 섞는 저장/전송/인증/body 재사용을 빨리 분리할 수 있다.

| 지금 막힌 문장 | 먼저 볼 문서 | 한 줄 이유 | 다음 한 칸 |
|---|---|---|---|
| "`Application`에 값은 있는데 요청엔 왜 안 보여요?" | [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md) | 저장소별 질문을 `자동 전송` vs `JS 직접 사용` vs `SW cache`로 자른다 | [Application 탭 vs Request Cookie 헤더 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md) |
| "`저장된 것`, `실제로 전송된 것`, `cache 재사용된 것`이 자꾸 섞여요" | [Browser DevTools 저장됨 vs 전송됨 vs 재사용됨 판독 드릴 3문제](./browser-devtools-stored-sent-reused-tracing-drill.md) | `Application`, request header, `304`/cache 신호를 3문제로 끊어 Intermediate bridge를 만든다 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |
| "`cookie`는 있는데 왜 다시 로그인해요?" | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) | cookie 전달, session 복원, cache 재사용을 다른 축으로 분리한다 | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |

## `session` 이름이 겹쳐서 헷갈릴 때

`sessionStorage`, session cookie, server session은 이름만 비슷하고 보는 층이 다르다. 로그인 지속과 body cache 재사용을 섞지 않으려면 아래 표처럼 끊는 편이 빠르다.

| 지금 막힌 문장 | 먼저 볼 문서 | 한 줄 이유 | 다음 한 칸 |
|---|---|---|---|
| "`sessionStorage`가 있는데 왜 로그인은 안 돼요?", "`session`이 세 군데서 보여요" | [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md) | `sessionStorage`, session cookie, server session을 같은 뜻으로 읽지 않게 끊어 준다 | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) |
| "`304`나 `from memory cache`가 보이면 로그인도 유지된 건가요?" | [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) | `304`와 cache hit는 body 재사용 신호일 뿐 인증 신호가 아님을 끊어 준다 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |

## 빠른 탐색 (계속 1)

- 아래부터는 primer 추가 묶음이다. beginner 첫 질문이 상태 코드, redirect, PRG라면 위 섹션까지만 읽고 멈춰도 된다.

- 전체 흐름 `survey`가 먼저 필요하면:
  - [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey)
  - [루트 README](../../README.md)
- 🟢 Beginner 입문 문서 (신규 추가):
  - [OSI 7계층 기초](./osi-7-layer-basics.md) — OSI 모델 개념과 계층별 역할
  - [TCP와 UDP 기초](./tcp-udp-basics.md) — 연결/신뢰성 차이와 사용 시나리오
  - [DNS 기초](./dns-basics.md) — 도메인 → IP 조회 흐름과 TTL 기초, HTTPS RR/SVCB를 H3 discovery bridge로 넘기는 입문
  - [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md) — GET/POST/PUT/DELETE와 멱등성
  - [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) — 새로고침 시 같은 `POST`가 다시 가는 이유와 `POST -> redirect -> GET` 흐름, 그리고 왜 이것만으로 서버 중복 방지가 끝나지 않는지 설명하는 beginner bridge
  - [HTTP semantics와 caching 첫 원리](./http-semantics-caching-first-principles.md) — safe/idempotent 의미, browser cache vs shared cache, validator와 `304`를 한 번에 묶는 primer
  - [HTTP 무상태성과 상태 유지 전략 입문](./http-stateless-state-management-basics.md) — stateless와 쿠키/세션/토큰
  - [TCP 3-way handshake 기초](./tcp-three-way-handshake-basics.md) — SYN/SYN-ACK/ACK 순서와 왜 3번인지
  - [HTTP와 HTTPS 기초](./http-https-basics.md) — TLS 역할, 암호화·인증·무결성 입문
  - [IP 주소와 포트 기초](./ip-address-port-basics.md) — IP, 포트, 소켓 개념과 well-known port
  - [HTTP 버전 비교 시작 가이드 (3분 브리지)](./http-versions-beginner-overview.md) — 3분 방향 잡기 후 메인 엔트리(`http1-http2-http3-beginner-comparison.md`)로 연결
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) — protocol 신호와 cache 신호 경계를 정리한 primer

## 빠른 탐색 (계속 2)

- 아래 `계속 2`부터 `계속 4`는 H3 discovery, `421`, coalescing 같은 follow-up 묶음이다.
- beginner 첫 질문이 `302/303/304/401`, cache, redirect, PRG라면 이 블록을 건너뛰고 위 `처음 읽는 5장` 또는 `상태 코드 / redirect / PRG로 바로 가기`에서 멈추는 편이 안전하다.

- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md) — DevTools 기준 `cold/warm/stale` 5단계 체크리스트와 `Protocol`/`Connection ID`/`Remote Address` 예시 캡처 1장, `304`는 HTTP cache 재검증일 뿐 Alt-Svc lifecycle 판독과 별개라는 경고, 문서 말미 3문항 self-check로 `warm인데 h2 유지`와 stale fallback 오판을 줄여 주는 entry primer
  - [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md) — `ma`는 hint TTL이고 cache scope는 origin 단위이며 `421`은 alternative-service reuse 범위를 다시 좁히는 신호라는 follow-up (초급자 질문별 빠른 라우팅 포함)
  - [Alt-Svc Endpoint Migration Rollout Symptom Bridge](./alt-svc-endpoint-migration-rollout-symptom-bridge.md) — H3 `Alt-Svc` endpoint를 옮긴 직후 일부 repeat visitor에서만 `421 -> 재시도 성공`, `h3 -> h2` 같은 transient symptom이 왜 보이는지, rollout 수렴 구간 관점에서 짧게 읽는 beginner bridge
  - [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md) — stale `Alt-Svc`/예전 endpoint authority로 `421` 후 fresh path에서 회복되는 H3 beginner 패턴에 더해 DevTools `같은 URL 두 줄 -> 새 connection 먼저 -> status` 첫 확인 순서 박스와 `중복 호출 vs 브라우저 recovery`, `421 -> 403/404` 미니 FAQ를 함께 묶은 primer

## 빠른 탐색 (계속 2-1)

  - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md) — 상단 `먼저 보는 FAQ`에서 `HTTPS RR이 있으면 항상 첫 요청 H3인가?`, `Alt-Svc를 봤으면 바로 재사용 허가인가?`, `421이면 discovery 실패인가?`를 먼저 자른 뒤 `Discovery vs Reuse Guardrail` 박스와 `HTTP header vs DNS record`, `DevTools vs DNS trace` 표로 `421`을 앱 권한/리소스 오류가 아닌 connection reuse 경계로 읽게 돕는 bridge
  - [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md) — 문서 상단 용어 고정 박스와 `첫 요청`/`다음 새 연결(재요청)`/`fallback` 표기를 먼저 맞춘 뒤, DevTools -> `dig` -> `curl` 고정 복붙 블록, `HTTPS RR 없음` vs `HTTPS RR 있음` `dig` 출력 2종, `curl --http3` 미지원 환경과 실제 H3 연결 실패를 가르는 1차 분기까지 묶어 Alt-Svc driven/HTTPS RR driven 첫 판독을 더 빨리 하게 돕는 입문

## 빠른 탐색 (계속 3)

- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md) — 여러 origin이 언제 같은 H2/H3 연결을 공유할 수 있는지
  - [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md) — wildcard cert가 넓어도 CDN/LB 경계 때문에 일부 host만 같은 connection을 써야 하는 이유
  - [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md) — ORIGIN으로 재사용 범위를 좁히고 `421`로 잘못된 공유를 되돌리는 후속 primer
  - [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) — README 미니표와 함께 DevTools, curl, proxy log에서 `421` wrong-connection 신호를 `403/404`와 구분하는 실전 입문
  - [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md) — wildcard cert는 맞지만 routing boundary가 달라 `admin` 요청이 `www` connection에서 `421`을 받는 장면을 DevTools, `curl`, proxy log 3면으로 짧게 따라가는 초급 실습 카드
  - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) — H3에서 ORIGIN frame 없이 certificate, Alt-Svc endpoint authority, `421`로 재사용 경계를 잡는 후속 primer
  - [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) — 문서 초입 `discovery vs reuse guardrail` 2x2 첫 분기표로 `H3를 못 찾은 문제`와 `찾은 뒤 shared connection 경계에서 막힌 문제`를 먼저 가르고, `421 -> 200`과 `421 -> 403` 캡처를 한 표에 붙여 비교해 초급자가 recovery 성공과 recovery 뒤 auth 거절을 덜 섞게 한 beginner 입문

## 빠른 탐색 (계속 4)

- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md) — 같은 URL 두 줄이 `421 recovery`인지 `304 revalidation`인지 먼저 가르는 비교 표를 추가해 Network 탭 초독해에서 cache 재검증과 wrong-connection retry를 섞지 않게 돕는 H2/H3 follow-up
  - [HTTP 상태 코드 기초](./http-status-codes-basics.md) — 2xx/3xx/4xx/5xx 첫 구분 위에 `421 vs 403/404` 오해를 먼저 끊는 beginner entry
  - [웹소켓 기초](./websocket-basics.md) — HTTP Upgrade, 양방향 통신, ws vs wss
- network `primer`부터 읽고 싶다면:
  - [레거시 primer](#레거시-primer)
  - [OSI 7 계층](#osi-7-계층)
  - [TCP 3-way-handshake & 4-way-handshake](#tcp-3-way-handshake--4-way-handshake)
  - [TCP 와 UDP](#tcp-와-udp)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) - URL 입력 뒤 DNS/TCP/TLS/HTTP와 cookie-session, reverse proxy, `502/504`, `HTTP keep-alive` vs `TCP keepalive`까지 한 번에 잡는 browser-to-server primer
- [HTTP semantics와 caching 첫 원리](./http-semantics-caching-first-principles.md) - safe/idempotent 메서드 의미, browser cache/shared cache, validator/`304`를 한 장으로 연결하는 follow-up primer
- [REST, WebSocket, SSE, gRPC, HTTP/2, HTTP/3 선택 입문](./rest-websocket-sse-grpc-http2-http3-choice-primer.md) - "대화 방식"과 "전송 길"을 먼저 분리해 transport choice를 고르는 beginner entrypoint
- [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) - HTTP 버전 학습의 메인 beginner 엔트리(연결 수, 멀티플렉싱, 손실 전파)

## 빠른 탐색 (계속 5)

- `HTTP 버전 route`: [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) -> [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) -> [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md)
  - `DevTools reused connection first-check route`: [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md) -> [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md) -> [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
  - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) - ALPN/`Alt-Svc`/`fallback`에 더해 `첫 요청` vs `다음 새 연결(재요청)`과 protocol 신호 vs cache 신호 경계를 빠른 판단표로 읽는 beginner primer
  - [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md) - 1분 체크리스트 다음 단계로, `Protocol`/`Remote Address`/`Connection ID`를 묶어 reused connection 단서를 읽는 compact primer
  - [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md) - DevTools `cold/warm/stale` 5단계 체크리스트와 `Protocol`/`Connection ID`/`Remote Address` 예시 캡처, 문서 말미 3문항 self-check로 repeat visit과 existing connection reuse, stale fallback 오판을 함께 줄이는 follow-up primer
  - [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md) - `ma`의 의미, origin별 cache scope, `421`이 reuse 결정을 어떻게 바꾸는지 묶어 보고, 같은 라우팅 문장으로 reuse/discovery primer에 이어 주는 초급 follow-up

## 빠른 탐색 (계속 6)

- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md) - stale `Alt-Svc`/예전 endpoint authority로 `421` 후 fresh path recovery가 보이는 H3 beginner 패턴에 더해 DevTools `같은 URL 두 줄 -> 새 connection 먼저 -> status` 첫 확인 순서와 `중복 호출 vs 브라우저 recovery`, `421 -> 403/404` 첫 판독을 함께 묶은 primer
  - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md) - `HTTP header vs DNS record`, `DevTools vs DNS trace` 1표와 Alt-Svc driven/HTTPS RR driven 4줄 타임라인으로 discovery와 reuse guardrail 질문을 분리하는 bridge primer
  - [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md) - `HTTPS RR 없음` vs `HTTPS RR 있음` `dig` 예시를 DevTools 첫 줄과 바로 붙여 읽게 해서 `h3=원인확정`, `dig 없음=H3불가` 같은 초급 오판을 더 빨리 교정하는 관측 primer
  - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
  - [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
  - [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
  - [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
  - [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md) - wildcard cert는 맞는데 `421`이 왜 edge에서 나는지 DevTools, `curl`, proxy log 신호를 한 줄 incident 메모까지 이어 읽는 mini-lab
  - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)

## 빠른 탐색 (계속 7)

- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) - `421 -> 200`과 `421 -> 403`를 한 장 비교표로 읽어 recovery 성공과 recovery 뒤 app 거절을 분리하는 초급 trace primer
  - [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
  - [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) — `저장됨`/`전송됨`/`인증됨`을 분리해 cookie, session, JWT를 같은 말로 읽지 않게 돕는 browser-state primer
  - [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
  - [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
  - [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
  - [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) — 브라우저가 body를 바로 재사용하는 경우와 validator를 들고 재확인하는 경우를 나눠 보는 cache entry
- [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md) - Cache Storage와 브라우저 HTTP cache를 같은 상자로 읽지 않도록, DevTools 첫 화면에서 "누가 body를 건넸는가" 기준으로 Service Worker 경로와 memory/disk/304를 먼저 가르고, cookie와 `sessionStorage`/`localStorage`를 자동 전송 상태인지 JS 앱 상태인지까지 함께 분리하는 초급 분기표
  - [Strong vs Weak ETag: validator 정밀도와 cache correctness](./strong-vs-weak-etag-validator-precision-cache-correctness.md)

## 빠른 탐색 (계속 8)

- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) - 문서 상단의 4단계 `첫 방문/반복 방문` 판독 체크리스트와 같은 URL 2분 실험에 더해, 같은 URL 재방문에서 `304`와 `from memory cache`를 `서버에 다시 물어봤는가` 기준으로 먼저 가르고 waterfall의 `waiting`/`content download` 같은 타이밍 신호와 섞지 않게 하는 1분 브리지까지 붙인 cache trace primer
- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md) - HTTP 요청-응답 기본 흐름 다음에 바로 붙는 follow-up으로, waterfall의 `dns`/`connect`/`ssl`/`request sent`/`waiting`/`content download`를 "연결 준비 vs 첫 바이트 대기 vs body 다운로드"와 `304`/`memory cache`/`disk cache` 같은 cache 신호와 분리해 읽게 하고, 같은 origin의 첫 요청과 반복 요청 waterfall을 나란히 비교해 재사용 keep-alive 연결에서 `dns/connect/ssl`이 사라지는 장면을 브라우저 이상이 아닌 connection reuse 단서로 먼저 읽게 하는 초급 primer
- [Browser DevTools `Request Sent` vs `Waiting` 미니 카드](./browser-devtools-request-sent-vs-waiting-mini-card.md) - waterfall에서 `request sent`가 길 때를 `server response가 느리다`로 오해하지 않도록, 큰 request body upload와 느린 first byte 대기를 가장 작은 분기로 먼저 가르는 beginner timing card
- [Browser DevTools `Waiting` vs `Content Download` 미니 카드](./browser-devtools-waiting-vs-content-download-mini-card.md) - waterfall에서 두 막대가 둘 다 길어 보여도 `waiting`은 첫 바이트 전 대기, `content download`는 body 다운로드라는 가장 작은 분기를 먼저 고정해 `504`/slow API/큰 payload를 같은 종류의 느림으로 뭉개지 않게 하는 초급 timing card

## 빠른 탐색 (계속 8-0)

- [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md) - 같은 URL에서 `normal reload`, `hard reload`, `empty cache and hard reload`, `Disable cache` 영향을 한 beginner 표로 분리해, 실험 스위치와 진짜 cache 정책을 섞지 않게 만드는 초급 entry primer

## 빠른 탐색 (계속 8-1)

- [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md) - 같은 URL 기준 3단계 실험에 before/after 2행 표를 더해, `Disable cache` ON 때문에 cache 관찰 결과가 왜 틀어지는지 바로 구분하게 돕는 초급 카드
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md) - `Status`/`Content-Type`/response preview 세 칸만으로 app JSON, gateway JSON, login HTML, CDN 에러 HTML, gateway 기본 페이지를 먼저 갈라 "`왜 JSON 대신 HTML이 와요?`", "`gateway가 JSON도 줄 수 있나요?`" 질문의 시작점을 바로 잡게 돕는 beginner checklist
- [CDN Error HTML vs App Error JSON Decision Card](./cdn-error-html-vs-app-json-decision-card.md) - `Generated by cloudfront (CloudFront)`, `The request could not be satisfied.`, `Attention Required! | Cloudflare`, `Sorry, you have been blocked` 같은 branded first-line clue를 `status`/`content-type`와 함께 읽어 app JSON이 아닌 CDN branded HTML 후보를 30초 안에 분리하게 돕는 tiny beginner card
- [CDN Vendor Header Crosswalk Mini Card: CloudFront / Cloudflare 단서 읽기](./cdn-vendor-header-crosswalk-cloudfront-cloudflare-mini-card.md) - `Server: CloudFront`, `X-Cache`, `CF-Cache-Status`, `CF-Ray`, `Via` 같은 vendor 헤더를 "범인 확정" 대신 `edge/CDN 경유`, `edge cache 재사용`, `owner 보류` 같은 안전한 초급 언어로 번역하게 돕는 follow-up 카드
- [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)
- [보조 primer](#보조-primer)

## 빠른 탐색 (계속 9)

- cookie / session / JWT 기본에서 auth/security/spring 경계로 올라가려면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md) -> [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md) -> [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md) -> [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> [Browser Session Spring Auth](#network-bridge-browser-session-auth) anchor와 [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) route를 함께 탄다.

## 빠른 탐색 (계속 10)

- `cookie 있는데 다시 로그인`, `saved request bounce`, `SavedRequest`, `401 -> 302` bounce, `hidden session mismatch`는 같은 beginner ladder로 묶는다. 핸드오프 cue는 `기억/전송/복원`이며, 초보자 표기는 `SavedRequest`(기억) -> `cookie-missing`(전송) -> `server-anonymous`(복원) 3칸으로 고정한다. 기존 `server-mapping-missing`은 retrieval 별칭으로만 남긴다. 이 README의 고정 사다리는 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) -> (follow-up) [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) -> (troubleshooting catalog) [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) 순서다.

## 빠른 탐색 (계속 10-1)

- `새로고침하면 다시 제출돼요`, `등록 완료 후 F5가 무서워요`, `form resubmission warning`, `주문이 두 번 생성돼요`처럼 browser form submit 중복이 먼저 보이면 [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)으로 가서 `POST -> redirect -> GET` 흐름을 먼저 고정한다. 다만 더블클릭, timeout retry, 모바일 재전송까지 같이 의심되면 같은 문서의 `PRG와 idempotency key는 왜 같이 나오나` 섹션을 먼저 보고, 서버 dedup 쪽은 [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)로 넘긴다. redirect 자체가 헷갈리면 [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)으로 이어 읽는다.
- 운영형 `deep dive catalog`에서 bucket을 먼저 고르려면:
  - [현대 topic catalog](#현대-topic-catalog)
  - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) - 입문 비교 문서에서 넘어온 독자를 위해 문서 상단 bridge box(멘탈 모델/혼동 포인트)를 추가한 HOL deep dive
  - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
  - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
  - [WebSocket heartbeat, backpressure, reconnect](./websocket-heartbeat-backpressure-reconnect.md)
  - [Forwarded / X-Forwarded-For / X-Real-IP 신뢰 경계](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
- 운영 복구 순서가 먼저 필요한 `playbook` / `runbook`으로 가려면:
  - `[playbook]` [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)

## 빠른 탐색 (계속 11)

- `[runbook]` [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md)
- upload `401/413/499` symptom `deep dive`로 바로 들어가려면:
  - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
  - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
  - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
  - cross-category upload / cleanup / Spring lifecycle bundle은 [Request Lifecycle Upload Disconnect](#network-bridge-request-lifecycle-upload-disconnect) anchor에서 이어 본다.
- disconnect / cancel symptom `deep dive`로 바로 들어가려면:
  - `499`, `broken pipe`, `client disconnect`, `connection reset`, `proxy timeout`처럼 같은 incident가 여러 hop에서 다른 surface로 보이면 아래 문서들을 한 묶음으로 본다.
  - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
  - [WebFlux Cancel-Lag Tuning](./webflux-cancel-lag-tuning.md)
  - [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md)
  - [SSE Last-Event-ID Replay Window](./sse-last-event-id-replay-window.md)
  - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

## 빠른 탐색 (계속 12)

- Spring lifecycle / container logging / abort surface bundle은 [Request Lifecycle Upload Disconnect](#network-bridge-request-lifecycle-upload-disconnect) anchor에서 이어 본다.
- edge `502/504` symptom `deep dive`로 바로 들어가려면:
  - `502`, `504`, `bad gateway`, `gateway timeout`, `local reply`, `upstream reset`처럼 edge status owner가 헷갈리면 아래 문서들을 한 묶음으로 본다.
  - edge owner / vendor translation / mesh local reply bundle은 [Edge Status Timeout Control Plane](#network-bridge-edge-status-timeout-control-plane) anchor에서 이어 본다.
- timeout-mismatch symptom `deep dive`로 바로 들어가려면:
  - `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`, `gateway는 504인데 app은 200`처럼 hop별 종료 순서가 흔들리면 아래 문서들을 한 묶음으로 본다.
  - timeout / Spring surface / lifecycle handoff bundle은 [Edge Status Timeout Control Plane](#network-bridge-edge-status-timeout-control-plane) anchor에서 이어 본다.
- [Spring + Network](../../rag/cross-domain-bridge-map.md#spring--network) route로 확장하려면:
  - [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)
  - 같은 기준으로 문맥을 넘기려면 아래 handoff 표를 먼저 보고, 각 row의 `primer -> follow-up`만 밟는다.
  - request lifecycle / Spring handoff는 [Request Lifecycle Upload Disconnect](#network-bridge-request-lifecycle-upload-disconnect) anchor에서 시작한다.
  - edge / timeout / control-plane handoff는 [Edge Status Timeout Control Plane](#network-bridge-edge-status-timeout-control-plane) anchor에서 시작한다.

## 빠른 탐색 (계속 13)

| 전환 구간 | 먼저 붙잡을 질문 | primer | follow-up |
|---|---|---|---|
| HTTP -> MVC | "이 HTTP 요청이 Spring 코드에서 어디서 처음 handler/controller로 넘어가나?" | [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md) -> [Spring MVC 컨트롤러 기초](../spring/spring-mvc-controller-basics.md) | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) |
| Spring -> DB | "`controller` 다음 `save()`와 SQL은 어디서 봐요?", "`처음`이라 browser -> controller -> database가 한 장면으로 헷갈려요" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) -> [Database First-Step Bridge](../database/database-first-step-bridge.md) | [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) -> [트랜잭션 기초](../database/transaction-basics.md) |
| JDBC -> DI/AOP | "이 JDBC 호출이 왜 service/bean/proxy 문맥으로 감싸져 보이나?" | [JDBC / JPA / MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) -> [IoC와 DI 기초](../spring/spring-ioc-di-basics.md) | [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md) -> [AOP 기초](../spring/spring-aop-basics.md) |

- 문서 역할이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)
  - [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)

## 역할별 라우팅 요약

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| network 전체 흐름과 추천 순서 | `survey` | [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey), [루트 README](../../README.md) |
| TCP / HTTP / DNS 기본 축 복습 | `primer` | [레거시 primer](#레거시-primer), [보조 primer](#보조-primer) |
| URL 입력부터 DNS, request/response, cookie/session, proxy, status code까지 한 번에 복습 | `primer` | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) |
| `304`, keep-alive, login session을 같은 말처럼 섞고 있어 먼저 경계부터 정리하고 싶다 | `primer / confusion cleanup` | [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md), [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md), [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |

## 역할별 라우팅 요약 (계속 1)

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| HTTP 버전 문서가 2개라 어디서 시작할지 헷갈릴 때 3분 안에 역할부터 정리 | `bridge primer` | [HTTP 버전 비교 시작 가이드 (3분 브리지)](./http-versions-beginner-overview.md) |
| HTTP/1.1, HTTP/2, HTTP/3 차이를 connection reuse와 HOL blocking 중심으로 빠르게 비교하고, 첫 읽기에서 흔한 오해 5개를 빨리 걸러내고 싶다 | `primer` | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) |
| HTTP/2에서 느려졌을 때 `HOL blocking`과 `flow-control stall`을 1페이지 표로 먼저 구분하고 싶다 | `bridge primer / quick decision table` | [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md) |

## 역할별 라우팅 요약 (계속 2)

| 브라우저가 왜 첫 요청은 H2인데 다음엔 H3를 쓸 수 있는지, 그리고 DevTools에서 `cold/warm/stale`를 5단계로 바로 판독하고 싶은지 이해 | `primer / Alt-Svc cache lifecycle` | [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md), [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md), [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md), [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md), [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md) |
| `ma`가 hint TTL인지, Alt-Svc cache scope가 왜 origin 단위인지, `421`이 alternative-service reuse를 어떻게 다시 좁히는지 함께 이해 | `follow-up primer / alt-svc scope and 421` | [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md), [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md), [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) |
| stale `Alt-Svc`나 예전 endpoint authority 때문에 첫 H3 요청은 `421`인데 fresh path에서는 바로 성공하는 패턴과 `중복 호출 vs 브라우저 recovery`, `421 -> 403/404` 첫 판독을 함께 이해 | `bridge primer / stale Alt-Svc recovery` | [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md), [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md), [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) |

## 역할별 라우팅 요약 (계속 3)

| 같은 URL에서 `421`이 한 번 나온 뒤 바로 성공(`200/204`)하는 증상에서 무엇부터 확인할지 가장 빠른 첫 읽기 순서가 필요 | `beginner first-check route / 421 then success` | [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md) -> [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md) -> [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) |
| 브라우저가 H3 endpoint를 응답의 `Alt-Svc`로 배우는지, DNS의 HTTPS RR/SVCB로 먼저 아는지, 그리고 `첫 clean request -> Alt-Svc 학습 -> 다음 새 connection` 10초 구분표까지 포함해 `HTTP header vs DNS record`, `DevTools vs DNS trace`를 한 번에 구분하고 싶다 | `bridge primer / discovery mental model / first request h3 faq` | [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md), [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md), [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md) |
| DevTools -> `dig` -> `curl` 3단계로 H3 discovery(`Alt-Svc` vs HTTPS RR)와 reuse guardrail(`421`/reuse) 질문을 빠르게 분리해 확인 | `primer / discovery observability` | [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md), [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md), [DNS 기초](./dns-basics.md) |

## 역할별 라우팅 요약 (계속 4)

| 서로 다른 origin이 왜 하나의 H2/H3 connection을 공유할 수 있고, 언제 `421`로 끊어야 하는지 이해 | `primer / connection reuse boundary` | [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md), [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) |
| wildcard cert가 여러 host를 덮더라도 왜 CDN/LB 경계 때문에 일부 origin만 같은 connection을 써야 하는지 concrete example로 이해 | `primer / wildcard cert boundary example` | [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md), [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md), [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) |
| wildcard cert는 맞는데 `admin` 요청만 `421`을 받아서 DevTools, `curl`, proxy log를 어떤 순서로 읽어야 할지 빠른 실습이 필요 | `primer / wildcard cert 421 trace / devtools curl proxy log` | [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md), [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md), [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) |

## 역할별 라우팅 요약 (계속 5)

| `ORIGIN` frame이 coalescing 범위를 어떻게 좁히고 `421`이 wrong-connection retry를 어떻게 유도하는지 이해 | `follow-up primer / connection reuse guardrail` | [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md), [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md) |
| DevTools, curl, proxy log에서 `421`이 `403/404`와 어떻게 다르게 보이는지 README 미니표부터 빠르게 판독 | `primer / troubleshooting entry / first-check mini table` | [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md), [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md), [HTTP 상태 코드 기초](./http-status-codes-basics.md) |
| H3에서 `ORIGIN` frame 없이 certificate scope, `Alt-Svc` endpoint authority, `421` recovery로 cross-origin reuse를 지키는 흐름을 이해 | `follow-up primer / H3 reuse guardrail` | [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md), [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md), [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md) |

## 역할별 라우팅 요약 (계속 6)

| Browser DevTools와 edge log에서 H3 `421`이 coalescing recovery인지, `421 -> 200`인지 `421 -> 403/404`인지, 아니면 같은 URL 2줄이 그냥 프런트 중복호출인지 30초 안에 구분하고 Safari처럼 `Connection ID`가 약한 화면에서는 `IP/Remote Address + 시간순서 + edge log` 대체 카드로 이어 읽기 | `primer / H3 421 observability / duplicate call vs recovery / 421 200 vs 421 403 comparison / status protocol connection id remote address checklist / safari connection id 없음` | [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md), [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md), [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) |
| wrong-connection reuse가 브라우저에서 같은 URL의 `421 -> 새 connection retry`로 어떻게 보이는지 H2/H3 예시로 이해 | `follow-up primer / browser-facing retry flow` | [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md), [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md), [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) |
| 브라우저가 cookie를 저장/전송하고 session/JWT가 request에 어디 실리는지 이해 | `primer -> primer bridge route` | [Browser Session Spring Auth](#network-bridge-browser-session-auth), [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) |

## 역할별 라우팅 요약 (계속 7)

| `401`, `403`, `302`를 page login redirect와 API auth failure 계약으로 자꾸 섞어서 먼저 decision table이 필요 | `beginner auth failure primer` | [HTTP 상태 코드 기초](./http-status-codes-basics.md), [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `남의 주문인데 왜 404`, `없는 것도 아닌데 404`, concealment policy 같은 말을 듣고 `403`과 `404` 의미를 헷갈림 | `beginner authz concealment bridge` | [`403` vs `404` Concealment: 존재를 숨길 때 초보자가 읽는 법](./http-403-vs-404-concealment-beginner-bridge.md), [HTTP 상태 코드 기초](./http-status-codes-basics.md), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md) |
| 브라우저 login redirect, `302`, 숨은 `JSESSIONID`, `SavedRequest` 복귀를 Spring deep dive 전에 묶어서 이해 | `primer bridge -> deep dive handoff` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md), [Browser Session Spring Auth](#network-bridge-browser-session-auth) |

## 역할별 라우팅 요약 (계속 7-a)

| `SameSite`, `HttpOnly`, `Secure`, `Domain`, `Path`가 브라우저 동작과 CSRF 노출을 각각 어떻게 바꾸는지 이해 | `primer / cookie security boundary` | [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md), [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md), [CSRF in SPA + BFF Architecture](../security/csrf-in-spa-bff-architecture.md) |
| 브라우저 토큰을 `cookie`와 `localStorage` 중 어디에 둘지, 자동 전송과 XSS/CSRF 경계를 먼저 비교하고 싶다 | `beginner choice card / browser token storage` | [Cookie vs `localStorage` 토큰 저장 선택 카드](./cookie-vs-localstorage-token-storage-choice-card.md), [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md), [XSS와 CSRF 기초](../security/xss-csrf-basics.md) |

## 역할별 라우팅 요약 (계속 7-1)

| same-origin, same-site, `fetch credentials`, CORS가 왜 서로 다른 답을 내는지 이해 | `primer / browser boundary` | [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md), [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md), [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md) |
| 브라우저 캐시 재사용과 `304` 재검증 흐름을 입문 수준에서 이해 | `primer` | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |

## 역할별 라우팅 요약 (계속 8)

| DevTools 첫 화면에서 `from ServiceWorker`와 `memory cache`/`disk cache`/`304`를 섞지 않고 1분 안에 갈라 읽고 싶다 | `primer / troubleshooting entry` | [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md), [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |
| weak/strong ETag 차이, `If-Match` vs `If-None-Match`, range resume 안전성을 같이 이해 | `deep dive` | [Strong vs Weak ETag: validator 정밀도와 cache correctness](./strong-vs-weak-etag-validator-precision-cache-correctness.md), [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| DevTools에서 `memory cache`, `disk cache`, `304`를 실제 trace로 구분하고 `첫 방문/반복 방문` 체크리스트까지 바로 보고 싶다 | `primer / troubleshooting entry / first visit vs repeat visit checklist` | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md), [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md), [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) |

## 역할별 라우팅 요약 (계속 8-1)

| Waterfall에서 두 번째 요청부터 `dns/connect/ssl`이 안 보여서 HTTPS나 계측이 깨졌다고 느껴질 때, connection reuse 단서부터 짧게 잡고 싶다 | `beginner bridge / waterfall reuse clue` | [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md), [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md), [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md) |
| DevTools waterfall에서 `waiting`과 `content download`가 둘 다 느림처럼 보여 같은 문제로 읽힐 때, first byte 대기와 body 다운로드를 1분 안에 갈라 잡고 싶다 | `mini card / waterfall waiting vs content download / first byte vs body` | [Browser DevTools `Waiting` vs `Content Download` 미니 카드](./browser-devtools-waiting-vs-content-download-mini-card.md), [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md), [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md) |

## 역할별 라우팅 요약 (계속 9)

| cache trace를 읽기 전에 `normal reload`, `hard reload`, `empty cache and hard reload`, `Disable cache` 차이를 같은 URL 기준으로 먼저 분리하고 싶다 | `entry primer / reload vs hard reload vs disable cache / true cache policy boundary` | [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md), [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md), [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md) |
| DevTools `Protocol` 열에서 `h1`/`http/1.1`/`h2`/`h3`가 섞여 보여도 같은 뜻끼리 먼저 묶고, `Remote Address`/`Connection ID`를 함께 붙여 H2/H3 incident에서 connection reuse 단서를 빠르게 읽고 싶다 | `beginner helper note / protocol remote address connection reuse / protocol 304 alt-svc boundary` | [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md), [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md), [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) |

## 역할별 라우팅 요약 (계속 10)

| 같은 URL로 `Disable cache` OFF/ON 차이를 3단계로 재현해 cache hit와 강제 bypass를 헷갈리지 않고 싶다 | `primer / experiment card / disable cache vs Alt-Svc confusion` | [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md), [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md), [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) |
| DevTools 첫 화면에서 뭘 먼저 봐야 할지 막막해서 `Status`/`Protocol`/`Remote Address`/`Connection ID` 4개로 1분 안에 첫 판독 순서를 잡고, `421`/H3 장면에서만 `Response Alt-Svc` 한 칸을 작게 덧붙여 보고 싶다 | `primer / first-check mini card / devtools first minute / response alt-svc quick check` | [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md), [Browser DevTools `Protocol` 열 표기 차이 보조노트](./browser-devtools-protocol-column-labels-primer.md), [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) |

## 역할별 라우팅 요약 (계속 10-1)

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| DevTools 빨간 row에 response headers가 거의 없어서 `(blocked)` / `canceled` / `(failed)`를 서버 `404`/`500`처럼 읽고 있다면, browser-side 메모부터 짧게 분리하고 싶다 | `primer / devtools status without response headers / blocked canceled failed` | [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md), [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md), [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md) |
| 검색 자동완성에서 `a -> ab -> abc`처럼 요청이 연달아 뜨고 앞줄이 `canceled`, 마지막만 `200`이라서 백엔드 버그인지 헷갈린다면, `AbortController` 기반 의도된 취소 trace를 먼저 확인하고 싶다 | `intermediate trace card / abortcontroller autocomplete canceled / stale request abort` | [AbortController 검색 자동완성 `canceled` trace 카드](./abortcontroller-search-autocomplete-canceled-trace-card.md), [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md), [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md) |
| DevTools `(blocked)`인데 콘솔에 `Mixed Content`와 `blocked by CORS policy`가 번갈아 보여 왜가 헷갈린다면, 초급자가 실제로 보는 두 원인을 먼저 가르고 싶다 | `mini card / blocked mixed content vs cors / console clue` | [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md), [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md), [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md) |

## 역할별 라우팅 요약 (계속 10-1a)

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| DevTools에 `OPTIONS`가 실패해서 보이는데 이것이 preflight 차단인지, actual `POST`/`GET` 실패인지 처음부터 헷갈린다면 같은 path의 actual row 존재 여부로 먼저 자르고 싶다 | `mini card / preflight vs actual failure / options only vs actual request` | [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md), [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md), [Preflight Debug Checklist](../security/preflight-debug-checklist.md) |
| Network에는 actual `401`/`403` row가 있는데 콘솔은 계속 CORS만 말해 "`요청이 안 간 건지`, `권한이 없는 건지`"가 섞인다면, actual auth failure와 error-path CORS masking을 한 번 더 분리하고 싶다 | `intermediate bridge / actual request exists + console cors / error-path cors masking` | [Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지](./browser-devtools-error-path-cors-vs-actual-401-403-bridge.md), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](../security/auth-failure-response-401-403-404.md), [Error-Path CORS Primer](../security/error-path-cors-primer.md) |

## 역할별 라우팅 요약 (계속 10-2)

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| 같은 URL의 언어/압축/표현 variant와 `Vary`가 왜 필요한지 입문 수준에서 이해 | `primer` | [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md), [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| 증상 축별로 다음 문서를 고르기 | `catalog / navigator` | [현대 topic catalog](#현대-topic-catalog) 아래 각 섹션 |

## 역할별 라우팅 요약 (계속 11)

| 장애 대응 순서나 메트릭 런북이 먼저 필요함 | `playbook` / `runbook` | [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md), [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md) |
| 역할 라벨이나 검색 alias가 헷갈림 | `taxonomy` / `routing helper` | [Navigation Taxonomy](../../rag/navigation-taxonomy.md), [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md) |

## 추천 학습 흐름 (category-local survey)

아래 흐름은 network 내부에서 `primer -> deep dive -> playbook`을 잇는 category-local survey다.

### 0. Browser Cookie / Auth Primer

[HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md) -> [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md) -> [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)

### 1. TCP / HTTP Version Progression

## 추천 학습 흐름 (category-local survey) (계속 2)

[OSI 7 계층](#osi-7-계층) -> [TCP 와 UDP](#tcp-와-udp) -> [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md) -> [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) -> [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md) -> [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) -> [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md) -> [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md) -> [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md) -> [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md) -> [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md) -> [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md) -> [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md) -> [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)

## 추천 학습 흐름 (category-local survey) (계속 2-1)

[HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md) -> [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) -> [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) -> [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)

## 추천 학습 흐름 (category-local survey) (계속 2) (계속 2)

[421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md) -> [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) -> [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) -> [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md) -> [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) -> [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) -> [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md)

## 추천 학습 흐름 (category-local survey) (계속 3)

### 2. Proxy / Mesh / Trust Boundary

[TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md) -> [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md) -> [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md) -> [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md) -> [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

### 3. Timeout / Queueing / Overload

[Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md) -> [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md) -> [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md) -> `[runbook]` [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md) -> [Mesh Adaptive Concurrency, Local Reply, Metrics Tuning](./mesh-adaptive-concurrency-local-reply-metrics-tuning.md)

### 4. Streaming / Disconnect / Cancellation

## 추천 학습 흐름 (category-local survey) (계속 4)

[HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md) -> [WebSocket heartbeat, backpressure, reconnect](./websocket-heartbeat-backpressure-reconnect.md) -> [SSE, WebSocket, Polling](./sse-websocket-polling.md) -> [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md) -> [WebFlux Cancel-Lag Tuning](./webflux-cancel-lag-tuning.md) -> [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md) -> [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md) -> [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md) -> [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md) -> [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md) -> [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md) -> [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md) -> [SSE Last-Event-ID Replay Window](./sse-last-event-id-replay-window.md)

## 추천 학습 흐름 (category-local survey) (계속 5)

### 5. Cache / DNS / Edge Variation

[DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md) -> [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) -> [Strong vs Weak ETag: validator 정밀도와 cache correctness](./strong-vs-weak-etag-validator-precision-cache-correctness.md) -> [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) -> [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md) -> [Cache-Control 실전](./cache-control-practical.md) -> [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md) -> `[playbook]` [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md) -> [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

## 연결해서 보면 좋은 문서 (cross-category bridge)

빠른 탐색에서는 symptom별 entrypoint만 남기고, 세부 cross-category bundle은 아래 anchor에서만 길게 유지한다.

<a id="network-bridge-browser-session-auth"></a>
### Browser Session Spring Auth

security README의 `Browser / Session Coherence` route와 wording parity를 맞춘 network-side bridge anchor다.
이 섹션에서는 역할 cue를 `primer -> primer bridge -> deep dive`로 고정하고, `hidden session mismatch`는 초보자 기준 `SavedRequest` / `cookie-missing` / `server-anonymous` 3분기로 먼저 자른다. 기존 `cookie-not-sent`, `server-mapping-missing`은 retrieval 별칭으로만 유지한다.

## 연결해서 보면 좋은 문서 (cross-category bridge) (입문 사다리)

| 지금 막힌 말 | primer | follow-up primer bridge | 첫 Spring deep dive |
|---|---|---|---|
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 `redirect / navigation memory` 확정 | [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `Application`에는 cookie가 보이는데 request `Cookie` header가 비어 있음 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 `cookie-header gate` 통과 | Spring으로 안 내려가고 먼저 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md), proxy/LB면 [Secure Cookie Behind Proxy Guide](../security/secure-cookie-behind-proxy-guide.md) |
| request `Cookie` header는 있는데 계속 anonymous, `next request anonymous after login` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)에서 `server-anonymous` 확정 | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) |

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 2)

| beginner split | 한 줄 뜻 | 첫 증거 | 다음 문서 |
|---|---|---|---|
| `SavedRequest` (`기억`) | 로그인 전 원래 URL을 기억했다가 다시 보내는 navigation memory 흐름 | `POST /login -> 302 original URL -> ...` | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md), [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |
| `cookie-missing` (`전송`) | `Application`에는 cookie가 보여도 다음 request `Cookie` header에는 빠진다 | stored cookie는 있는데 request `Cookie` header가 비어 있음 | [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md), [Secure Cookie Behind Proxy Guide](../security/secure-cookie-behind-proxy-guide.md) |
| `server-anonymous` (`복원`) | request `Cookie` header는 왔는데 서버가 session/auth를 복원하지 못해 anonymous로 본다 | app log의 `anonymous`, `session-not-found`, `token-mapping-miss` | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) |

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 3)

- `[primer]` cookie / session / JWT 입문 개념을 Spring auth 설계로 올리려면 [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md) -> [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md) 순으로 먼저 고정한다.
- `[common confusion]` `stateless`, `cookie`, `session`, `cache`가 한 덩어리처럼 들리면 [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)에서 `누가 무엇을 저장하나` 표와 `/login -> /me -> /static/app.js` 예시로 먼저 역할을 분리한 뒤 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md), [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)로 내려간다.
- `[primer bridge]` `SavedRequest`, `login loop`, `401 -> 302`, `hidden session mismatch`가 보이기 시작하면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) -> [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) 순으로 security route와 같은 bridge ladder를 먼저 고정한다.

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 4)

- `[deep dive]` primer bridge 이후에만 [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md) -> [Spring Security 아키텍처](../spring/spring-security-architecture.md) -> [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) -> [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) 순으로 내려간다.

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 5)

- `[primer bridge -> deep dive split]` `Application > Cookies`에는 값이 보이는데 다음 request `Cookie` header가 비거나 `auth`/`app`/`api` subdomain 이동 뒤에만 깨지면, 먼저 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)의 `Application vs Network 15초 미니 체크`로 `stored` vs `sent`를 고정한 뒤 `cookie-missing` branch(`cookie-not-sent` 별칭)로 보고 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)로 간다. redirect `Location`이나 다음 요청 URL이 `http://...`로 꺾이거나 proxy/LB 뒤에서만 재현되면 [Secure Cookie Behind Proxy Guide](../security/secure-cookie-behind-proxy-guide.md)로 먼저 분기한다. request `Cookie` header가 실제로 실리는 것이 확인되면 `server-anonymous` branch(기존 `server-mapping-missing`)로 올려 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)와 [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)로 내려간다.

<a id="network-bridge-request-lifecycle-upload-disconnect"></a>
### Request Lifecycle Upload Disconnect

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 6)

- 애플리케이션 요청 생명주기와 함께 보려면 [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md), [Spring Multipart Exception Translation Matrix](./spring-multipart-exception-translation-matrix.md), [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md), [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md), [WebFlux Request-Body Abort Surface Map](./webflux-request-body-abort-surface-map.md), [Spring MVC Async `onError`

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 6) (계속 2)

`AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md), [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md), [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md), [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md), [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md), [Spring WebClient Connection Pool and Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md), [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)을 이어 보면 좋다.

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 7)

<a id="network-bridge-edge-status-timeout-control-plane"></a>
### Edge Status Timeout Control Plane

- edge `502/504` ownership을 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md), [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md), [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)을 같이 보면 local reply, upstream reset, vendor translation이 한 줄로 잡힌다.
- timeout mismatch를 Spring surface까지 이어 보려면 [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md), [Idle Timeout Mismatch: LB / Proxy / App](./idle-timeout-mismatch-lb-proxy-app.md), [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md), [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)을 같이 본다.
- latency / retry / queueing을 교차 도메인으로 묶으려면 [Latency Debugging Master Note](../../master-notes/latency-debugging-master-note.md), [Retry, Timeout, Idempotency Master Note](../../master-notes/retry-timeout-idempotency-master-note.md), [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)을 같이 보면 좋다.

## 연결해서 보면 좋은 문서 (cross-category bridge) (계속 8)

- control plane / global routing으로 확장하려면 [Service Discovery / Health Routing](../system-design/service-discovery-health-routing-design.md), [Service Mesh Control Plane](../system-design/service-mesh-control-plane-design.md), [Global Traffic Failover Control Plane](../system-design/global-traffic-failover-control-plane-design.md)을 이어 읽으면 network symptom이 orchestration 문제로 번지는 지점을 잡기 쉽다.

## 레거시 primer

아래 구간은 네트워크 입문 설명과 기본 개념 복습용 primer다.

바로 아래 본문은 교재형 설명이 길어서, 초심자는 먼저 아래 짧은 진입표로 시작한 뒤 필요한 구간만 내려가는 편이 덜 흔들린다.

## 레거시 primer (계속 2)

| 지금 필요한 첫 그림 | 먼저 볼 문서 | 다음 한 걸음 | 돌아올 곳 |
|---|---|---|---|
| 브라우저 요청이 서버까지 어떻게 흘러가는지 한 번에 잡고 싶다 | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency-basics.md) | [역할별 라우팅 요약](#역할별-라우팅-요약) |
| `302`, `304`, `401`이 왜 다 다르게 읽혀야 하는지 처음부터 정리하고 싶다 | [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md) | [HTTP 상태 코드 기초](./http-status-codes-basics.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) | [빠른 탐색](#빠른-탐색) |
| 폼 제출 뒤 왜 `POST` 대신 `GET` 화면으로 끝내는지 감이 안 잡힌다 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) -> [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) | [레거시 primer](#레거시-primer) |

## 레거시 primer (계속 2-0)

| 지금 필요한 첫 그림 | 먼저 볼 문서 | 다음 한 걸음 | 돌아올 곳 |
|---|---|---|---|
| `304`, keep-alive, 로그인 유지가 머릿속에서 한 덩어리로 보인다 | [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md) | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) | [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey) |
| `http keep-alive`, `tcp keepalive`, `idle timeout`, `heartbeat`가 전부 같은 말처럼 들린다 | [HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat](./http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md) | [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md) -> [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md) | [레거시 primer](#레거시-primer) |

## 레거시 primer (계속 2-0a)

| 지금 필요한 첫 그림 | 먼저 볼 문서 | 다음 한 걸음 | 돌아올 곳 |
|---|---|---|---|
| keep-alive를 켰는데도 `한참 후 첫 요청만` `connection reset`처럼 실패해 이유가 궁금하다 | [Keep-Alive 켰는데 왜 idle 뒤 첫 요청만 실패할까? (Stale Idle Connection Primer)](./keepalive-reuse-stale-idle-connection-primer.md) | [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md) -> [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md) | [레거시 primer](#레거시-primer) |
| HTTP 요청은 이해했는데 "이제 Spring 코드에서는 어디로 들어가나?"를 바로 잇고 싶다 | [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md) | [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md) -> [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](../spring/spring-ioc-di-basics.md) -> [Database First-Step Bridge](../database/database-first-step-bridge.md) | [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge) |

## 레거시 primer (계속 2-1)

| 지금 필요한 첫 그림 | 먼저 볼 문서 | 다음 한 걸음 | 돌아올 곳 |
|---|---|---|---|
| OSI, TCP, UDP를 외우기보다 "어느 층에서 무슨 문제가 나는가" 감각부터 잡고 싶다 | [OSI 7 계층](#osi-7-계층) -> [TCP 와 UDP](#tcp-와-udp) | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) | [빠른 탐색](#빠른-탐색) |
| HTTP 버전 문서가 많아서 바로 H3/421 deep dive로 떨어질까 걱정된다 | [HTTP 버전 비교 시작 가이드 (3분 브리지)](./http-versions-beginner-overview.md) | [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) | [레거시 primer](#레거시-primer) |
| HTTP 버전은 알겠는데 "왜 H2 다음에 QUIC 이야기가 나오지?"를 한 줄 route로 잡고 싶다 | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) | [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) -> [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md) | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](#http11-vs-http2-vs-http3-입문-비교) |

## 레거시 primer (계속 3)

- `beginner handoff`: HTTP 문서에서 "요청의 의미"까지 잡혔으면 다음은 "누가 그 요청을 받는가", "컨트롤러 안 서비스는 누가 넣는가", "`save()` 뒤 SQL은 어디서 보나"를 붙이면 된다. 안전한 순서는 [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md) -> [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md) -> [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](../spring/spring-ioc-di-basics.md) -> [Database First-Step Bridge](../database/database-first-step-bridge.md)다.

## OSI 7 계층

> 개방형 시스템 상호 연결을 위한 기초 참조 모델(Open Systems Interconnection Reference Model)

OSI 7 계층이란, 국제표준화기구(ISO)에서 개발한 모델로, 컴퓨터 네트워크 프로토콜 디자인과 통신을 계층으로 나누어 설명한 것이다.

쉽게 말하면 **네트워크에서 통신이 일어나는 과정을 7단계로 나눈 것**을 말한다. 계층 모델에 의해 **프로토콜도 계층별로 구성**된다. 현재 네트워크 시스템의 기반이 된 모델이며 다양한 시스템은 이 계층 모델을 기반으로 통신한다. (현재의 인터넷은 각 계층의 역할들이 합쳐지면서 TCP/IP 4 계층 모델(링크 계층, 인터넷 계층, 전송 계층, 응용 계층)을 기반으로 한다.)

> 현재의 인터넷 계층 모델 참조 : [RFC1122 공식 문서 - Internet Protocol Suite](https://tools.ietf.org/html/rfc1122)

OSI 7 계층을 나눈 이유는 **통신이 일어나는 과정을 단계별로 알 수 있고, 7단계 중 특정한 곳에 이상이 생기면 다른 단계와 독립적으로 그 단계만 수정할 수 있기 때문**이다.

OSI 7 계층은 **물리 계층, 데이터 링크 계층, 네트워크 계층, 전송 계층, 세션 계층, 표현 계층, 응용 계층**으로 구성되어 있다.

### 프로토콜이란

위에서 프로토콜이 계층별로 구성된다고 언급하였다. 이 프로토콜이란 메시지를 주고 받는 양식이나 규칙을 의미하는 **통신 규약**이다.

시스템 간 메시지를 주고 받기 위해서는 한쪽에서 보낸 메시지를 반대쪽에서 이해할 수 있어야 한다. 한쪽에서 '안녕' 이라는 메시지를 보냈을 때
인사로 알아듣고 대답으로 '안녕' 이라는 메시지를 보낼 수 있어야 한다는 뜻이다. 통신 모델에서도 메시지를 주고 받으며 통신할 때 그 언어와 대화 방법에
대한 규칙이 있어야 의사소통을 할 수 있을 것이다. 이 규칙을 정의한 것이 프로토콜이고 이 규칙은 계층별로 다르게 존재한다.

### OSI 7 계층의 구조

<img src="img/osi-and-tcp-ip.png" alt="osi-7-layer" width="40%" /> <img src="img/osi-7-layer.png" alt="osi-7-layer" width="59%" />

#### \[7] 응용 계층 (Application Layer) : 데이터 단위 message | 프로토콜 HTTP, SMTP, FTP, SIP 등

- 통신의 최종 목적지로, 응용 프로그램들이 통신으로 활용하는 계층이다.
- 사용자에게 가장 가까운 계층이며 웹 브라우저, 응용 프로그램을 통해 사용자와 직접적으로 상호작용한다.
- 많은 프로토콜이 존재하는 계층으로, 새로운 프로토콜 추가도 굉장히 쉽다.

#### \[6] 표현 계층 (Presentation Layer) : 데이터 단위 message | 프로토콜 ASCII, MPEG 등

## OSI 7 계층 (계속 2)

- 데이터의 암호화, 복호화와 같이 응용 계층에서 교환되는 데이터의 의미를 해석하는 계층이다.
- 응용 프로그램 ⇔ 네트워크 간 정해진 형식대로 데이터를 변환, 즉 표현한다.
- 인터넷의 계층 구조에는 포함되어있지 않으며 필요에 따라 응용 계층에서 지원하거나 어플리케이션 개발자가 직접 개발해야 한다.

#### \[5] 세션 계층 (Session Layer) : 데이터 단위 message | 프로토콜 NetBIOS, TLS 등

- 데이터 교환의 경계와 동기화를 제공하는 계층이다.
- 세션 계층의 프로토콜은 연결이 손실되는 경우 연결 복구를 시도한다. 오랜 시간 연결이 되지 않으면 세션 계층의 프로토콜이 연결을 닫고 다시 연결을 재개한다.
- 데이터를 상대방이 보내고 있을 때 동시에 보낼지에 대한 전이중(동시에 보냄, 전화기), 반이중(동시에 보내지 않음, 무전기) 통신을 결정할 수 있다.
- 인터넷의 계층 구조에는 포함되어있지 않으며 필요에 따라 응용 계층에서 지원하거나 어플리케이션 개발자가 직접 개발해야 한다.

#### \[4] 전송 계층 (Transport Layer) : 데이터 단위 segment | 프로토콜 TCP, UDP, SCTP 등

- 상위 계층의 메시지를 하위 계층으로 전송하는 계층이다.
- 메시지의 오류를 제어하며, 메시지가 클 경우 이를 나눠서(Segmentation) 네트워크 계층으로 전달한다. 그리고 받은 패킷을 재조립해서 상위 계층으로 전달한다.
- 대표적으로 TCP, UDP 프로토콜이 있다. TCP는 연결 지향형 통신을, UDP는 비연결형 통신을 제공한다.

#### \[3] 네트워크 계층 (Network Layer) : 데이터 단위 datagram, packet | 프로토콜 IP, ICMP, ARP, RIP, BGP 등

- 패킷을 한 호스트에서 다른 호스트로 라우팅하는 계층이다. (여러 라우터를 통한 라우팅, 그를 통한 패킷 전달)
- 전송 계층에게 전달 받은 목적지 주소를 이용해서 패킷을 만들고 그 목적지의 전송 계층으로 패킷을 전달한다.
- 인터넷의 경우 IP 프로토콜이 대표적이다.

#### \[2] 데이터 링크 계층 (Data Link Layer) : 데이터 단위 frame | 프로토콜 PPP, Ethernet, Token ring, IEE 802.11(Wifi) 등

- 데이터를 frame 단위로 한 네트워크 요소에서 이웃 네트워크 요소로 전송하는 계층이다. (물리 계층을 이용해 전송)
- 인터넷의 경우 Ethernet 프로토콜이 대표적이다. Ethernet은 MAC 주소를 이용해 Node-to-Node, Point-to-Point로 프레임을 전송한다.
- 이 계층의 장비로 대표적인 것은 스위치, 브릿지이다.

#### \[1] 물리 계층 (Physical Layer) : 데이터 단위 bit | 프로토콜 DSL, ISDN 등

## OSI 7 계층 (계속 3)

- 장치 간 전기적 신호를 전달하는 계층이며, 데이터 프레임 내부의 각 bit를 한 노드에서 다음 노드로 실제로 이동시키는 계층이다.
- 인터넷의 Ethernet 또한 여러가지 물리 계층 프로토콜을 갖고 있다.
- 이 계층의 장비로 대표적인 것은 허브, 리피터이다.

---

## TCP 3-way-handshake & 4-way-handshake

> 참고 : [[Network] TCP 3-way handshaking과 4-way handshaking](https://gmlwjd9405.github.io/2018/09/19/tcp-connection.html)

TCP는 네트워크 계층 중 **전송 계층에서 사용하는 프로토콜** 중 하나로, **신뢰성을 보장하는 연결형 서비스**이다.

TCP의 **3-way-handshake**란 TCP 통신을 시작하기 전에 논리적인 경로 **연결을 수립 (Connection Establish)** 하는 과정이며, **4-way-handshake**는 논리적인 경로 **연결을 해제 (Connection Termination)** 하는 과정이다. 이러한 방식을 Connect Oriented 방식이라 부르기도 한다.

### TCP 3-way-handshake : Connection Establish

3-way-handshake 과정을 통해 양쪽 모두 데이터를 전송할 준비가 되었다는 것을 보장한다.

<img src="img/3-way-handshake.png" alt="3-way-handshake" width="80%" />

#### A 프로세스(Client)가 B 프로세스(Server)에 연결을 요청

1. **A**(CLOSED) **→ B**(LISTEN) **: SYN(a)**
    - 프로세스 A가 연결 요청 메시지 전송 (SYN)
    - 이 때 Sequence Number를 임의의 랜덤 숫자(a)로 지정하고, SYN 플래그 비트를 1로 설정한 segment를 전송한다.
2. **B**(SYN_RCV) **→ A**(CLOSED) **: ACK(a+1), SYN(b)**
    - 연결 요청 메시지를 받은 프로세스 B는 요청을 수락(ACK)했으며, 요청한 A 프로세스도 포트를 열어달라(SYN)는 메시지 전송
    - 받은 메시지에 대한 수락에 대해서는 Acknowledgement Number 필드를 (Sequence Number + 1)로 지정하여 표현한다. 그리고 SYN과 ACK 플래그 비트를 1로 설정한 segment를 전송한다.
3. **A**(ESTABLISHED) **→ B**(SYN_RCV) **: ACK(b+1)**
    - 마지막으로 프로세스 A가 수락 확인을 보내 연결을 맺음 (ACK)
    - 이 때, 전송할 데이터가 있으면 이 단계에서 데이터를 전송할 수 있다.

최종 PORT 상태 : A-ESTABLISHED, B-ESTABLISHED (연결 수립)

### TCP 4-way-handshake : Connection Termination

<img src="img/4-way-handshake.png" alt="4-way-handshake" width="77%" />

#### A 프로세스(Client)가 B 프로세스(Server)에 연결 해제를 요청

## TCP 3-way-handshake & 4-way-handshake (계속 2)

1. **A**(ESTABLISHED) **→ B**(ESTABLISHED) **: FIN**
    - 프로세스 A가 연결을 종료하겠다는 FIN 플래그를 전송
    - 프로세스 B가 FIN 플래그로 응답하기 전까지 연결을 계속 유지
2. **B**(CLOSE_WAIT) **→ A**(FIN_WAIT_1) **: ACK**
    - 프로세스 B는 일단 확인 메시지(ACK)를 보내고 자신의 통신이 끝날 때까지 기다린다.
    - Acknowledgement Number 필드를 (Sequence Number + 1)로 지정하고, ACK 플래그 비트를 1로 설정한 segment를 전송한다.
    - 그리고 자신이 전송할 데이터가 남아있다면 이어서 계속 전송한다. (클라이언트 쪽에서도 아직 서버로부터 받지 못한 데이터가 있을 것을 대비해 일정 시간동안 세션을 남겨놓고 패킷을 기다린다. 이를 TIME_WAIT 상태라고 한다.)
3. **B**(CLOSE_WAIT) **→ A**(FIN_WAIT_2) **: FIN**
    - 프로세스 B의 통신이 끝나면 이제 연결 종료해도 괜찮다는 의미로 프로세스 A에게 FIN 플래그를 전송한다.
4. **A**(TIME_WAIT) **→ B**(LAST_ACK) **: ACK**
    - 프로세스 A는 FIN 메시지를 확인했다는 메시지를 전송 (ACK)
    - 프로세스 A로부터 ACK 메시지를 받은 프로세스 B는 소켓 연결을 해제한다.

최종 PORT 상태 : A-CLOSED, B-CLOSED (연결 해제)

---

## TCP 와 UDP

아래의 자료에서 자세한 설명과 코드를 볼 수 있다.

- 작성자 권혁진 | [TCP 와 UDP](https://nukw0n-dev.tistory.com/10)

## HTTP 요청-응답 기본 흐름

> URL 입력 뒤 DNS, TCP/TLS, HTTP request/response, cookie/session, reverse proxy, 상태 코드, keep-alive를 browser-to-server 흐름으로 묶어 주는 입문 primer

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat](./http-keep-alive-vs-tcp-keepalive-idle-timeout-heartbeat-primer.md)
- [Keep-Alive 켰는데 왜 idle 뒤 첫 요청만 실패할까? (Stale Idle Connection Primer)](./keepalive-reuse-stale-idle-connection-primer.md)

## 현대 topic catalog

아래 구간은 순서대로 읽는 `survey`가 아니라 운영 이슈 중심 `deep dive catalog`다. mixed catalog에서 `[playbook]`, `[runbook]` 라벨은 step-oriented 대응 문서라는 뜻이고, 라벨이 없는 항목은 trade-off / failure-mode 중심 `deep dive`다.

## TCP 혼잡 제어

- [TCP 혼잡 제어](./tcp-congestion-control.md)

## TCP Zero Window, Persist Probe, Receiver Backpressure

> packet loss가 없어도 receiver-side backpressure 때문에 전송이 멈출 수 있다는 점과 `rwnd=0`, persist probe, write stall 해석을 다룬다

- [TCP Zero Window, Persist Probe, Receiver Backpressure](./tcp-zero-window-persist-probe-receiver-backpressure.md)

---

## HTTP 요청 방식 - GET, POST

HTTP의 GET, POST 메서드란 HTTP 프로토콜을 이용해서 서버에 데이터(요청 정보)를 전달할 때 사용하는 방식이다.

### HTTP GET 메서드

GET 메서드는 **정보를 조회**하기 위한 메서드로, 서버에서 어떤 데이터를 가져와서 보여주기 위한 용도의 메서드이다. **"가져오는 것(Select)"**

GET 방식은 요청하는 데이터가 HTTP Request Message의 Header 부분의 url에 담겨서 전송된다. 이는 요청 정보를 url 상에 넣어야 한다는 뜻이다. 요청 정보를 url에 넣는 방법은 요청하려는 url의 끝에 `?`를 붙이고, `(key=value)` 형태로 요청 정보를 담으면 된다. 요청 정보가 여러 개일 경우에는 `&`로 구분한다.

> ex. `www.urladdress.xyz?name1=value1&name2=value2`, `www.google.com/search?q=서그림`

GET 방식은 게시판의 게시글 조회 기능처럼 데이터를 조회할 때 쓰이며 서버의 상태를 바꾸지 않는다. 예외적으로 방문자의 로그 남기기 기능이나 글을 읽은 횟수 증가 기능에도 쓰인다.

GET 방식은 다음과 같은 특징이 있다.

- url에 요청 정보가 이어붙기 때문에 전송할 수 있는 데이터의 크기가 제한적이다. (주솟값 + 파라미터 해서 255자로 제한된다. HTTP/1.1은 2048자)
- HTTP 패킷의 Body는 비어 있는 상태로 전송한다. 즉, Body의 데이터 타입을 표현하는 Content-Type 필드도 HTTP Request Header에 들어가지 않는다.
- 요청 데이터가 그대로 url에 노출되므로 사용자가 쉽게 눈으로 확인할 수 있어 POST 방식보다 보안상 취약하다. 보안이 필요한 데이터는 GET 방식이 적절하지 않다.
- GET 방식은 멱등성(Idempotent, 연산을 여러 번 적용하더라도 결과가 달라지지 않는 성질)이 적용된다.
- GET 방식은 캐싱을 사용할 수 있어, GET 요청과 그에 대한 응답이 브라우저에 의해 캐쉬된다. 따라서 POST 방식보다 빠르다.

> GET 방식의 캐싱 : 서버에 리소스를 요청할 때 웹 캐시가 요청을 가로채 서버로부터 리소스를 다시 다운로드하는 대신 리소스의 복사본을 반환한다. HTTP 헤더에서 cache-control 헤더를 통해 캐시 옵션을 지정할 수 있다.
> _(출처: [\[네트워크\] get 과 post 의 차이](https://noahlogs.tistory.com/35))_

### HTTP POST 메서드

POST 메서드는 서버의 값이나 상태를 바꾸기 위한 용도의 메서드이다. **"수행하는 것(Insert, Update, Delete)"**

POST 방식은 요청하는 데이터가 HTTP Request Message의 Body 부분에 담겨서 전송된다. Request Header의 Content-Type에 해당 데이터 타입이 표현되며, 전송하고자 하는 데이터 타입을 적어주어야 한다.

## HTTP 요청 방식 - GET, POST (계속 2)

- Default : application/octet-stream
- 단순 txt : text/plain
- 파일 : multipart/form-data

POST 방식은 게시판 글쓰기 기능처럼 서버의 데이터를 업데이트할 때 쓰인다.

POST 방식은 다음과 같은 특징이 있다.

- Body 안에 데이터를 담아 전송하기 때문에 대용량의 데이터를 전송하기에 적합하다.
- GET 방식보다 보안상 안전하지만, 암호화를 하지 않는 이상 보안에 취약한 것은 같다.
- 클라이언트 쪽에서 데이터를 인코딩하여 서버로 전송하고, 이를 받은 서버 쪽이 해당 데이터를 디코딩한다.

> **목적에 맞는 기술을 사용해야 한다. - GET 방식의 캐싱과 연관지어 생각해보기**
>
> GET 방식의 요청은 브라우저에서 캐싱을 할 수 있다고 했다. 때문에 POST 방식으로 요청해야 할 것을, 요청 데이터의 크기가 작고 보안적인 문제가 없다는 이유로 GET 방식으로 요청한다면 기존에 캐싱되었던 데이터가 응답될 가능성이 존재한다. 때문에 목적에 맞는 기술을 사용해야 한다.

---

## HTTP 와 HTTPS

아래의 자료에서 자세한 설명과 코드를 볼 수 있다.

- 작성자 권혁진 | [HTTP와 HTTPS](https://nukw0n-dev.tistory.com/11?category=940859)

## HTTP 메서드, REST, 멱등성

- [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)

## Post/Redirect/Get(PRG) 패턴 입문

> 폼 제출이나 form login 성공 뒤 완료 화면을 바로 `POST` 응답으로 끝내지 않고 `POST -> 303 -> GET` mental model로 먼저 고정해, 새로고침 재전송을 줄이는 browser 흐름을 먼저 설명하는 beginner primer. `201 Created`, 서버 중복 방지, 메서드 유지 redirect 같은 follow-up은 관련 문서로 넘긴다.

- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)

## HTTP의 무상태성과 쿠키, 세션, 캐시

> `stateless`, `cookie`, `session`, `cache`가 모두 "상태" 이야기처럼 들릴 때, 브라우저 저장/서버 저장/응답 재사용을 한 표와 `/login -> /me -> /static/app.js` 예시로 먼저 가르는 beginner bridge

- [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)

## Cookie / Session / JWT 브라우저 흐름 입문

> 브라우저가 `Set-Cookie`를 언제 저장하고 `Cookie`를 언제 다시 보내는지, session cookie와 JWT header/cookie 방식이 HTTP 요청에 어떻게 나타나는지 묶어 보는 입문 primer

- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)

## Cookie vs `localStorage` 토큰 저장 선택 카드

> 브라우저 자동 전송 여부, XSS/CSRF 경계, `Application`/`Network` 탭 확인 위치를 한 표로 먼저 끊어서 "토큰을 어디에 둬야 하지?" 질문에 초급자용 첫 판단 기준을 주는 choice card

- [Cookie vs `localStorage` 토큰 저장 선택 카드](./cookie-vs-localstorage-token-storage-choice-card.md)

## Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문

> browser login flow에서 `302`/`303`/`307`, `Location`, redirect 응답의 `Set-Cookie`, 숨은 `JSESSIONID`, 로그인 후 원래 URL 복귀를 Spring deep dive 전에 한 번에 정리하고, `fetch`가 login HTML `200`을 받았을 때 숨은 redirect follow와 missing cookie를 먼저 분리하게 돕는 bridge primer

- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)

## Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드

> `fetch` redirect에서 beginner가 가장 자주 섞는 세 신호를 `follow` 뒤 최종 결과 신호와 `manual` 모드의 제한 신호로 분리해, "`manual`인데 왜 `response.redirected`가 안 맞죠?`", "`response.url`이 원래 요청 URL인가요?`" 같은 질문을 바로 정리하는 tiny follow-up card

- [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md)
- safe next step:
  [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

## Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`

> `fetch('/api/...')`에서 auth failure가 났을 때 raw `401 JSON`, 첫 응답 `302 /login`, redirect를 따라간 뒤 최종으로 보이는 login HTML `200`을 한 decision table로 잘라, "`왜 API가 HTML을 받아요?`", "`200인데 왜 실패처럼 처리해야 하죠?`" 같은 beginner query를 먼저 정리하는 chooser card

- [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md)
- safe next step:
  [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md) -> [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)

## Browser fetch vs page navigation redirect trace card

> 같은 `/api/me -> /login` incident를 page navigation, `fetch`, DevTools waterfall 용어로 나란히 보여 줘 "`왜 주소창 이동과 API login HTML `200`이 같은 일처럼 보이죠?`", "`원인 `302`는 어디서 보고 최종 `200`은 어디서 읽죠?`" 같은 beginner query를 짧게 고정하는 tiny companion card

- [Browser fetch vs page navigation redirect trace card](./browser-fetch-vs-page-navigation-redirect-trace-card.md)
- safe next step:
  [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md) -> [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)

## Fetch `redirect:"error"` tiny card

> `fetch` redirect 세 모드 중 "`redirect: "error"`는 언제 제일 깔끔한가?"를 beginner 기준으로 분리해, JSON/API 계약에서 login HTML `200` 같은 숨은 성공 표면을 막고 싶을 때 왜 `follow`나 `manual`보다 `error`가 더 선명한지 설명하는 tiny choice card

- [Fetch `redirect: "error"` tiny card](./fetch-redirect-error-choice-card.md)
- safe next step:
  [Fetch Auth Failure Chooser: `401 JSON` vs `302 /login` vs 숨은 Login HTML `200`](./fetch-auth-failure-401-json-vs-302-login-vs-hidden-login-html-200-chooser.md) -> [Fetch `response.redirected` vs `response.url` vs `opaqueredirect` 미니 카드](./fetch-redirected-response-url-opaqueredirect-mini-card.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)

## Redirect vs Forward vs SPA Router Navigation 입문

> 로그인 뒤 화면 이동이 모두 같아 보일 때, HTTP redirect, server-side forward, SPA router navigation을 "누가 이동을 결정했는가" 기준으로 먼저 분리하는 beginner bridge

- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)

## SSR 뷰 렌더링 vs JSON API 응답 입문

> 같은 `200 OK`라도 브라우저가 바로 그릴 HTML인지, 프론트 코드가 처리할 JSON인지 먼저 가르게 하고, "진짜 HTML endpoint"와 "`fetch`/XHR에서 숨은 `302 -> /login` 뒤 온 login HTML fallback"을 짧은 chooser로 나눠 주는 beginner bridge

- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)

## Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path

> `SameSite`, `HttpOnly`, `Secure`, `Domain`, `Path`가 browser 자동 전송, JS 접근, scope, CSRF 노출을 각각 어떻게 바꾸는지 속성별로 분리해 설명하는 focused primer

- [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)

## Cross-Origin Cookie, `fetch credentials`, CORS 입문

> `same-origin`, `same-site`, `credentials: "same-origin" | "include"`, `SameSite`, CORS가 cross-origin browser request에서 어떻게 합쳐지는지 beginner flow로 풀어 주고, origin/site basics 뒤에는 request `Cookie` header 체크를 기준으로 hidden redirect follow와 missing cookie를 분리한 다음 `Fetch Credentials vs Cookie Scope` / `Cookie Scope Mismatch Guide` / 같은 Security troubleshooting anchor로 다시 복귀시키는 primer

- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)

## HTTP 캐싱과 조건부 요청 기초

> 브라우저 cache freshness, `Cache-Control`, validator(`ETag`, `Last-Modified`), `304 Not Modified`를 한 request/response 흐름으로 묶고, `from disk cache` vs `304`를 `서버 왕복 여부/validator 유무` 3칸 표로 바로 가르게 한 뒤 같은 browsing session에서도 `304` 재검증과 H2/H3 선택이 독립이라는 예시까지 붙인 입문 primer

- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)

## Strong vs Weak ETag

> weak validator와 strong validator의 차이, `If-None-Match`/`If-Match`/`If-Range`가 요구하는 비교 강도, compressed variant에서 ETag semantics가 왜 cache correctness를 바꾸는지 다루는 follow-up deep dive

- [Strong vs Weak ETag: validator 정밀도와 cache correctness](./strong-vs-weak-etag-validator-precision-cache-correctness.md)

## Browser DevTools Cache Trace Primer

> Chrome/Edge Network 탭에서 `memory cache`, `disk cache`, `revalidation`, `304`를 실제 trace와 header로 구분하고, `Protocol(h2/h3)`이 말하는 전송 경로와 cache가 말하는 body 출처를 따로 읽게 해 H3/DevTools 초급 오분류를 줄이는 실전 primer

- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)

## Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문

> DevTools `Protocol`/`Remote Address`/`Connection ID`를 한 묶음으로 읽어 HTTP/2, HTTP/3 incident 첫 장면에서 "버전 질문인지, 기존 연결 재사용인지, 새 연결 recovery인지"를 초급자 관점으로 먼저 가르는 compact primer

- [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md)

## Browser DevTools 첫 확인 체크리스트 1분판

> DevTools 첫 화면에서 `Status`, `Protocol`, `Remote Address`, `Connection ID` 네 칸으로 시작하고, `421`/H3 trace에서는 `Response Alt-Svc`를 작은 보조 칸으로만 덧붙여 읽게 만드는 초급 미니 카드

- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)

## Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문

> response headers가 거의 없는 빨간 row를 서버 `404`/`500`처럼 읽지 않도록, DevTools `Status`의 `(blocked)` / `canceled` / `(failed)`를 브라우저 메모로 먼저 묶어 정책 차단, 취소, 연결 실패의 초급 1차 분기를 잡아 주는 compact primer

- [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)

## AbortController 검색 자동완성 `canceled` trace 카드

> 검색 자동완성에서 `a -> ab -> abc`처럼 연속 입력할 때 앞 요청이 `canceled`, 마지막 요청만 `200`으로 끝나는 trace를 "백엔드 오류"가 아니라 프론트의 의도된 stale request 정리 패턴으로 읽게 돕는 intermediate trace card

- [AbortController 검색 자동완성 `canceled` trace 카드](./abortcontroller-search-autocomplete-canceled-trace-card.md)

## Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드

> DevTools `(blocked)`에서 초급자가 가장 자주 마주치는 `Mixed Content`와 `blocked by CORS policy`를 콘솔 문구 기준으로 먼저 가르게 해 주는 tiny follow-up card

- [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md)

## Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드

> DevTools에서 `OPTIONS` row가 실패할 때 이를 actual API 실패와 같은 뜻으로 읽지 않게 하고, 같은 path의 actual `GET`/`POST` row 존재 여부로 preflight 차단과 실제 auth/API failure를 먼저 가르게 하는 tiny beginner card

- [Browser DevTools `OPTIONS` Preflight vs Actual Request Failure 미니 카드](./browser-devtools-options-preflight-vs-actual-failure-mini-card.md)

## Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지

> DevTools `Network`에는 actual `GET`/`POST`의 `401`/`403`이 이미 보이는데 콘솔은 계속 CORS만 말하는 장면에서, pure preflight failure와 actual auth failure + error-path CORS masking을 분리해서 읽게 만드는 intermediate bridge

- [Browser DevTools에서 CORS처럼 보이지만 actual `401`/`403`이 있는 경우: Error-Path CORS 브리지](./browser-devtools-error-path-cors-vs-actual-401-403-bridge.md)

## Browser DevTools `502` vs `504` vs App `500` 분기 카드

> 브라우저에서 본 `500`을 app 직접 실패 후보로, `502`/`504`를 proxy나 gateway가 만든 기본 HTML/body/header 패턴 후보로 먼저 나누게 해 주는 compact beginner decision card

- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)

## Browser DevTools `Request Sent` vs `Waiting` 미니 카드

> waterfall에서 `POST`/multipart upload의 slow send time과 실제 server first-byte 대기를 같은 뜻으로 읽지 않게 하고, "`Request Sent`가 길면 서버가 느린 거예요?"라는 beginner 질문을 upload/body send vs response start 2갈래로 먼저 자르는 timing mini card

- [Browser DevTools `Request Sent` vs `Waiting` 미니 카드](./browser-devtools-request-sent-vs-waiting-mini-card.md)

## Browser DevTools 첫 실패 후 두 번째 성공 trace 카드

> 한동안 idle 뒤 같은 URL이 `처음은 실패`하고 `바로 다음은 성공`하는 장면에서, DevTools 두 줄을 나란히 보고 stale idle connection 재사용 실패 후 새 연결 성공 후보를 먼저 읽게 만드는 intermediate observability bridge

- [Browser DevTools 첫 실패 후 두 번째 성공 trace 카드](./browser-devtools-first-fail-second-success-keepalive-card.md)

## Gateway JSON vs App JSON Tiny Card

> "`502`/`504`인데 JSON이 왔어요", "`title/detail` JSON이면 앱 에러예요 gateway 에러예요?`" 같은 질문에서 generic gateway/proxy JSON과 서비스-owned JSON error envelope을 필드 말투 기준으로 먼저 가르게 돕는 tiny beginner card

- [Gateway JSON vs App JSON Tiny Card](./gateway-json-vs-app-json-tiny-card.md)

## Browser DevTools Response Body Ownership 체크리스트

> DevTools `Response` 탭에서 body가 보일 때 `Status`/`Content-Type`/response preview 3칸만 먼저 읽어 app JSON, gateway JSON, login HTML, CDN 에러 HTML, gateway 기본 페이지 owner를 빠르게 가르게 하여 "`API가 왜 HTML을 줘요?`", "`gateway JSON은 app JSON이랑 어떻게 달라요?`" 질문의 첫 분기를 안정시키는 beginner checklist

- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)

## CDN Error HTML vs App Error JSON Decision Card

> "`왜 JSON 대신 브랜드 있는 HTML 에러 페이지가 와요?`", "`이 JSON 에러는 앱이 만든 거예요?`"처럼 CDN branded page와 app-owned JSON을 헷갈릴 때 `status`/`content-type`/body 첫 줄만으로 30초 1차 분기를 잡는 tiny beginner card

- [CDN Error HTML vs App Error JSON Decision Card](./cdn-error-html-vs-app-json-decision-card.md)

## Browser DevTools `Accept` vs Response `Content-Type` 미니 카드

> body preview를 열기 전에도 request `Accept`와 response `Content-Type` 두 칸만 먼저 읽어 "`JSON을 기대했는데 왜 HTML이 와요?`" 질문을 빠르게 가르는 초급 헤더 미니 카드

- [Browser DevTools `Accept` vs Response `Content-Type` 미니 카드](./browser-devtools-accept-vs-content-type-mini-card.md)

## Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge

> `504` 뒤 같은 URL이 다시 보여도 transport 복구, 사용자 새로고침, 비멱등 `POST` 중복 제출을 같은 뜻으로 읽지 않게 하고, "`누가 다시 보냈나`"와 `Method`/`303` 여부부터 보게 만드는 beginner bridge

- [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md)

## Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드

> 응답 헤더 3칸만으로 "브라우저 문제인지, proxy가 대신 응답한 건지, app까지 들어간 건지"를 DevTools 첫 pass에서 빠르게 가르게 돕는 beginner card

- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)

## DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge

> DevTools에서 찾은 `X-Request-Id`를 gateway 로그, app 로그, tracing 화면으로 어떻게 넘겨 읽는지 연결해, "`헤더는 봤는데 이제 어디를 찾아야 하죠?`" 질문의 다음 한 걸음을 고정하는 beginner bridge

- [DevTools 뒤 `X-Request-Id`는 어디로 가나요? Gateway -> App Log -> Trace Beginner Bridge](./x-request-id-gateway-app-log-trace-beginner-bridge.md)

## Browser DevTools `traceparent` vs `tracestate` 초급 미니 카드

> `traceparent`와 `tracestate`가 같이 보일 때 "`둘 다 읽어야 해요?`", "`왜 표준 헤더가 두 개예요?`" 같은 입문 혼선을 줄이기 위해, first pass에서는 `traceparent`를 먼저 보고 `tracestate`는 vendor 메타데이터로 뒤로 미루는 안전한 읽기 순서를 고정하는 beginner card

- [Browser DevTools `traceparent` vs `tracestate` 초급 미니 카드](./browser-devtools-traceparent-vs-tracestate-mini-card.md)

## Browser DevTools `traceId` vs `spanId` 초급 미니 카드

> DevTools 옆 로그와 tracing 화면에서 `traceId`와 `spanId`가 같이 보일 때 "`왜 spanId로 먼저 찾으면 안 나와요?`", "`둘 다 ID인데 뭐가 먼저예요?`" 같은 초급 혼선을 줄이기 위해, `traceId`를 전체 요청 흐름 검색 키로 먼저 잡고 `spanId`는 세부 hop 확대용으로 뒤에 쓰는 읽기 순서를 고정하는 beginner follow-up card

- [Browser DevTools `traceId` vs `spanId` 초급 미니 카드](./browser-devtools-traceid-vs-spanid-mini-card.md)

## Browser DevTools `X-Cache` / `Age` 1분 헤더 카드

> `X-Cache`, `Age`, `CF-Cache-Status` 같은 cache 관련 응답 헤더가 보일 때 초급자가 app ownership을 성급히 확정하지 않고, `304`/`from disk cache` 같은 browser cache 신호와 분리해서 먼저 `edge/CDN cache 재사용 후보`로 번역하게 돕는 adjacent header card

- [Browser DevTools `X-Cache` / `Age` 1분 헤더 카드](./browser-devtools-x-cache-age-ownership-1minute-card.md)

## Browser DevTools Application 탭 저장소 읽기 1분 카드

> `Cookies`, `Local Storage`, `Session Storage`, `Cache Storage`를 같은 "브라우저 저장소"로 뭉개지 않고, 각각이 답하는 질문을 `저장됨`, `JS가 직접 읽음`, `탭 수명`, `Service Worker용 응답 상자`로 끊어 읽게 만드는 초급 Application 탭 entry card. 특히 "`Application`에는 cookie가 있는데 왜 request header는 비어요?"처럼 DevTools-first로 들어온 질문을 `credentials: "include"` 누락 증상까지 한 줄로 바로 연결한다.

- [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md)

## Browser DevTools Application vs Request Cookie Header 미니 카드

> `Application` 탭의 저장 확인과 `Network` 탭의 request `Cookie` 전송 확인을 같은 것으로 읽지 않게 만드는 초급 reverse-link anchor다. "`Application에는 있는데 왜 요청 헤더는 비어요?`" 같은 증상 문장은 여기서 다시 잡는다.

- [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md)
- safe next step:
  [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) -> [Cross-Origin Cookie, `fetch credentials`, CORS 입문](./cross-origin-cookie-credentials-cors-primer.md)
- return path:
  `302`, `304`, `401`, cache 재검증까지 같이 섞여 보이면 [빠른 탐색](#빠른-탐색)으로 돌아가 symptom별 entrypoint를 다시 고른다.

## Browser DevTools 저장됨 vs 전송됨 vs 재사용됨 판독 드릴 3문제

> `Application` 탭의 저장 사실, request header의 실제 전송, `304`/cache signal의 body 재사용을 3문제로 일부러 섞어 내서, beginner 문서를 읽고도 자주 남는 "`저장됐는데 왜 안 갔어요?`", "`token이 있는데 왜 401이에요?`", "`Cache Storage`랑 `304`는 같은 cache예요?`"를 Intermediate bridge로 묶는 practice drill

- [Browser DevTools 저장됨 vs 전송됨 vs 재사용됨 판독 드릴 3문제](./browser-devtools-stored-sent-reused-tracing-drill.md)

## Browser DevTools `Disable cache` ON/OFF 실험 카드

> 같은 URL 하나로 `Disable cache` OFF의 자연 cache 재사용과 ON의 강제 bypass를 3단계로 비교해, beginner가 재현 실험을 섞어 읽지 않게 만드는 초급 실험 카드

- [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)

## Browser DevTools 새로고침 분기표

> cache trace에 들어가기 전에 `normal reload`, `hard reload`, `empty cache and hard reload`, `Disable cache`를 같은 URL 실험표로 먼저 분리해, 실험 스위치와 진짜 cache 정책을 섞지 않게 만드는 초급 entry primer

- [Browser DevTools 새로고침 분기표: normal reload, hard reload, empty cache and hard reload](./browser-devtools-reload-hard-reload-disable-cache-primer.md)

## Browser `302` vs `304` vs `401` 새로고침 분기표

> page reload 뒤 `302` redirect, `304` cache revalidation, raw `401` unauthenticated를 DevTools 첫 4칸(`Status`, `Location`, validator, auth header)으로 바로 가르게 해, "왜 로그인으로 갔는지"와 "왜 기존 body를 다시 썼는지"를 같은 뜻으로 섞지 않게 만드는 초급 bridge primer

- [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md)

## Service Worker 혼선 1분 분기표

> DevTools 첫 화면에서 `from ServiceWorker`와 HTTP cache(`memory cache`, `disk cache`, `304`)를 "누가 body를 건넸는가" 기준으로 먼저 분리하는 초급 entry primer

- [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)

## Vary와 Content Negotiation 기초

> 같은 URL에서 언어, 압축, 표현 형식이 달라질 때 서버가 무엇을 보고 variant를 고르고 cache가 왜 `Vary`를 알아야 하는지 설명하는 입문 primer

- [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)

## gRPC vs REST

- [REST, WebSocket, SSE, gRPC, HTTP/2, HTTP/3 선택 입문](./rest-websocket-sse-grpc-http2-http3-choice-primer.md)
- [브라우저 경계에서 보는 gRPC-Web vs BFF vs REST 브리지](./grpc-web-vs-bff-vs-rest-browser-boundary-bridge.md)
- [gRPC vs REST](./grpc-vs-rest.md)

## gRPC Status, Trailers, Transport Error Mapping

> gRPC 실패를 app-level status, trailers-only 응답, proxy reset, transport close로 나눠 해석하는 방법과 retry 판단 포인트를 정리한다

- [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)

## HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교

> 한 페이지에서 여러 리소스를 가져올 때 브라우저가 연결 수, 멀티플렉싱, 손실 전파를 어떻게 다르게 다루는지 먼저 잡는 beginner primer다. 첫 읽기 이탈을 줄이기 위해 `HTTP/2면 무조건 빠른가`, `HTTP/3면 무조건 써야 하나` 같은 자주 헷갈리는 질문 5줄 판별 카드도 포함한다.

| 지금 막힌 질문 | 한 줄 route |
|---|---|
| 버전 큰그림 -> TCP HOL 한계 -> QUIC 선택 이유를 순서대로 잡고 싶다 | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) -> [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) -> [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md) |

- [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [TCP와 UDP 기초](./tcp-udp-basics.md)
- [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
- [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md)

## 브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문

> 브라우저가 실제로 언제 H1/H2/H3를 고르고, 왜 `첫 요청`과 `다음 새 연결(재요청)`의 protocol이 달라질 수 있는지 설명하면서 ALPN/QUIC 같은 protocol 신호와 `Alt-Svc`/HTTP cache 같은 cache 신호, 그리고 `fallback`을 같은 용어로 분리해 읽게 만드는 beginner primer다. 이번 보강에서는 중간에 `HTTP header vs DNS record` 분기 상자를 넣어 "`어디서 H3 후보를 배웠나`"와 "`실제로 어떤 protocol이 성립했나`"를 먼저 가르게 했고, DevTools에서는 `첫 row의 Alt-Svc 확인 -> 새 connection 확인 -> 다음 row의 h3 확인` 3단계 체크리스트로 `first h2 -> next h3`를 바로 검증하게 했다. 초급 진입은 `primer bridge -> primer -> follow-up primer / deep dive` 순서로 맞췄다.
>
> - `첫 방문은 h2인데 repeat visit은 h3`, `같은 탭 새로고침인데 왜 아직 h2`처럼 **첫 방문/반복 방문 confusion**이 중심이면 바로 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)로 점프한다.

## 브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문 (계속 2)

- `[primer bridge]` 큰 그림부터 잡으려면 [HTTP 버전 비교 시작 가이드 (3분 브리지)](./http-versions-beginner-overview.md)로 먼저 들어간다.
- `[primer]` 첫 학습 엔트리는 [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)다.
- `[follow-up primer]` 브라우저 선택 과정을 바로 보고 싶으면 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)으로 이어간다.
- `[follow-up primer]` `첫 방문 h2 -> 반복 방문 h3` 패턴이 헷갈리면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)로 간다.
- `[primer bridge]` discovery와 reuse guardrail을 함께 묶어 보고 싶으면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)를 본다.
- `[follow-up primer]` DevTools와 DNS 관측 축으로 바로 확인하려면 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)로 간다.
- `[follow-up primer]` 여러 origin의 같은 연결 재사용이 궁금하면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)으로 이어간다.
- `[deep dive]` 협상 실패와 라우팅 mismatch를 추적하려면 [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)를 본다.
- `[deep dive]` H3 미사용 원인을 attribution하려면 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)으로 내려간다.

## Alt-Svc Cache Lifecycle Basics

> `Alt-Svc` cache warming, `ma` expiry, stale hint 때문에 왜 첫 방문은 H2인데 repeat visit은 H3 또는 다시 H2처럼 보일 수 있는지 설명하고, `304`는 HTTP cache 재검증일 뿐 Alt-Svc lifecycle 상태를 직접 말해 주지 않는다는 경고를 함께 붙여 회사망/집망 전환 같은 현실 예시로 이어지게 해 주는 beginner primer다

- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

## Alt-Svc `ma`, Cache Scope, 421 Reuse Primer

> `ma`를 hint TTL로, cache scope를 origin별 메모로, `421`을 alternative-service reuse 교정 신호로 묶어 설명하고, 문서 말미 3문항 셀프체크로 `ma=connection lifetime` 오해를 바로 잡는 beginner follow-up primer다

- [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)

## H3 Stale Alt-Svc 421 Recovery Primer

> stale `Alt-Svc`나 예전 endpoint authority 때문에 첫 H3 시도는 `421`이지만, 새 connection 또는 기본 경로의 fresh path에서는 바로 성공할 수 있는 beginner failure pattern을 회사망/집망 전환 타임라인과 DevTools `같은 URL 두 줄 -> 새 connection 먼저` 첫 확인 순서로 설명한다

- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)

## Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge

> 브라우저가 H3 endpoint를 응답의 `Alt-Svc`로 배우는지, DNS의 HTTPS RR/SVCB로 먼저 아는지를 상단 `Discovery vs Reuse Guardrail` 용어 고정 박스와 `첫 요청`/`다음 새 연결(재요청)`/`fallback` 표기 통일로 먼저 고정하고, `HTTP header vs DNS record`, `DevTools vs DNS trace` 1표와 Alt-Svc driven/HTTPS RR driven 4줄 타임라인으로 discovery가 app 권한/리소스 오류보다 앞단의 coalescing 경계 판단과 이어진다는 점을 설명하는 beginner bridge다

- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

## H3 Discovery Observability Primer

> 상단의 용어 고정 박스에 `첫 요청`/`다음 새 연결(재요청)`/`fallback` 통일 표기까지 묶고, DevTools -> `dig` -> `curl` 3단계 1분 실습 카드와 `Protocol`/`Alt-Svc`/DNS answer 3칸 최소 관측 표로 첫 요청 `h2` -> 다음 새 연결 `h3` 패턴을 beginner가 discovery 질문과 cache/body 출처 질문으로 먼저 분리한 뒤 reuse guardrail까지 자가검증하게 돕는 관측 primer다

- [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [DNS 기초](./dns-basics.md)
- [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

## HTTP/2와 HTTP/3 Connection Coalescing 입문

> 여러 origin이 언제 같은 H2/H3 connection을 공유할 수 있는지, certificate, endpoint, routing, `421 Misdirected Request` 관점으로 먼저 잡는 beginner primer다

- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)
- [SNI Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)

## Wildcard Certificate vs Routing Boundary Primer

> wildcard cert가 여러 host를 덮더라도 왜 CDN/LB 경계 때문에 일부 origin만 같은 connection을 써야 하는지 concrete CDN/LB example로 설명하는 beginner primer다

- [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
- [SNI, Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)

## HTTP/2 ORIGIN Frame와 421 입문

> 브라우저가 cross-origin reuse 후보를 만든 뒤, 서버가 `ORIGIN` frame으로 범위를 미리 좁히고 `421`로 잘못된 재사용을 되돌리는 흐름을 설명하는 beginner follow-up primer다

- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)

## HTTP 421 Troubleshooting Trace Examples

> Browser DevTools, curl, proxy log에서 `421 Misdirected Request`가 `403 Forbidden`, `404 Not Found`와 다르게 보이는 trace 신호를 먼저 잡고, 특히 같은 URL의 `421 -> 403`와 `421 -> 200` mixed trace를 4필드(`Status`/`Protocol`/`Connection ID`/`Remote Address`)로 한눈에 가르게 만든 beginner troubleshooting entrypoint다

| 첫 질문 | `421` 먼저 의심 | `403/404` 먼저 의심 |
|---|---|---|
| 지금 막 틀리기 쉬운 포인트 | "요청이 잘못된 connection/authority 문맥에 실렸나?" | "맞는 서버까지 갔고 권한 또는 리소스에서 막혔나?" |
| 첫 확인 위치 | `Protocol`, `Remote Address`, `Connection ID`, `Host`/`:authority` | auth/session, role/policy, URL path, route, resource id |

- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md) — `403/404`와 `421 wrong-connection`을 가장 먼저 갈라 보는 상태 코드 입문
- [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

## 421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough

> wildcard cert가 같아도 routing boundary가 다르면 왜 `admin` 요청이 기존 `www` connection에서 `421`을 받는지, DevTools `Connection ID`, `curl -v`의 `Host`, proxy log의 local reply 신호를 한 번에 따라가게 만드는 beginner mini-lab이다

- [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md)
- [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md)

## HTTP/3 Cross-Origin Reuse Guardrails Primer

> H3에서 H2의 `ORIGIN` frame 없이 certificate scope, `Alt-Svc` endpoint authority, `421 Misdirected Request`로 cross-origin reuse 경계를 잡는 beginner follow-up primer다. 같은 라우팅 문장으로 `scope` 질문은 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md), `discovery` 질문은 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)로 넘긴다.

- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)

## HTTP/3 421 Observability Primer

> 문서 초입 `discovery vs reuse guardrail` 2x2 분기로 `H3를 못 찾은 문제`와 `찾은 뒤 shared connection 경계에서 막힌 문제`를 먼저 가른 다음, Browser DevTools와 edge log에서 H3 `421`이 wrong-connection recovery인지, recovery 뒤 app-level `403/404`가 이어진 mixed trace인지 분리해서 읽고, 같은 URL `421 -> 200` 최소 4필드(`Status`/`Protocol`/`Connection ID`/`Remote Address`) 스냅샷과 Chrome `Remote Address` vs Safari `IP Address` 대체 캡처 규칙, 그리고 `Connection ID`가 약한 환경에서 `IP/Remote Address + 시간순서 + edge log`로 보완 판독하는 20초 카드까지 바로 따라 읽게 만든 beginner observability primer다

- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)

## 421 Retry After Wrong Coalescing

> wrong-connection reuse가 브라우저에서 같은 URL의 `421` 뒤 새 connection retry로 어떻게 보이는지, 그리고 같은 URL 두 줄 장면을 `304 revalidation`과 어떻게 바로 가를지 비교 표와 `421 -> 200` 3줄 recovery 예시로 먼저 잡아 주는 beginner follow-up primer다

- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)

## h2c, Cleartext Upgrade, Prior Knowledge, Routing

> cleartext 환경에서 `h2c` upgrade와 prior knowledge가 proxy chain에서 어떻게 깨지고 internal gRPC/H2 mismatch를 어떻게 만드는지 다룬다

- [h2c, Cleartext Upgrade, Prior Knowledge, Routing](./h2c-cleartext-upgrade-prior-knowledge-routing.md)

## h2c Operational Traps: Proxy Chain, Dev/Prod Drift

> dev/prod drift, ingress/sidecar cleartext hop, gRPC cleartext mismatch처럼 h2c가 환경별로만 깨지는 운영 함정을 따로 정리한다

- [h2c Operational Traps: Proxy Chain, Dev/Prod Drift](./h2c-operational-traps-proxy-chain-dev-prod.md)

## HTTP/2 멀티플렉싱과 HOL blocking

> `HTTP/1.1 vs HTTP/2 vs HTTP/3` 입문 비교 이후, HTTP 레벨 HOL 완화와 TCP 레벨 HOL 잔존을 구분해 이해하도록 상단 beginner bridge를 포함한 deep dive entry다

- [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md)
- [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)

## HTTP/2 Flow Control, WINDOW_UPDATE, Stall

> 문서 상단 60초 beginner bridge에서 "window=보내도 되는 데이터 예산" 멘탈 모델과 첫 확인 포인트를 먼저 잡고, 그 다음 stream/connection stall과 `WINDOW_UPDATE` 지연을 deep dive 한다

- [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md)
- [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)

## HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation

> 한 connection 안에서 stream slot이 부족할 때 생기는 숨은 queueing과 unary/streaming 혼합 트래픽의 tail latency 악화를 정리한다

- [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)

## HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics

> HTTP/2에서 stream-level reset, connection-level `GOAWAY`, TCP close를 어떻게 구분해야 하는지와 gRPC retry/streaming 취소 해석을 정리한다

- [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)

## TLS, 로드밸런싱, 프록시

- [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)

## TLS Record Sizing, Flush, Streaming Latency

> TLS record와 flush/coalescing 정책이 SSE, WebSocket, chunked/gRPC streaming의 first byte와 chunk cadence에 어떤 영향을 주는지 다룬다

- [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)

## TLS close_notify, FIN/RST, Truncation

> TLS 종료에서 `close_notify`와 TCP `FIN`/`RST`를 어떻게 구분해야 하는지와 truncation, EOF 오해를 설명한다

- [TLS close_notify, FIN/RST, Truncation](./tls-close-notify-fin-rst-truncation.md)

## Service Mesh, Sidecar Proxy

- [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)

## Service Mesh Local Reply, Timeout, Reset Attribution

> sidecar가 만든 local reply, route timeout, reset, mTLS failure가 app 결과와 어떻게 섞여 보이는지와, app 미도달/결과 유실/번역된 실패를 어떻게 가를지 mesh 관점으로 정리한다

- [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)

## API Gateway, Reverse Proxy 운영 포인트

- [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
- [API Gateway Auth Failure Surface Map: `401`/`403`, `302`, Login HTML 구분 입문](./api-gateway-auth-failure-surface-map.md)
> `API got login HTML 200`, `raw 401 JSON`, `왜 api가 html을 받아요`처럼 같은 auth 실패가 브라우저 redirect 표면과 API 계약 표면으로 갈라져 보일 때, 어느 문서로 라우팅해야 하는지 빠르게 잡는 beginner symptom bridge

## HTTP Response Compression, Buffering, Streaming Trade-offs

> gzip/brotli가 throughput에는 유리하지만 streaming 경로의 flush와 chunk cadence를 어떻게 바꿀 수 있는지와 압축 위치별 운영 포인트를 다룬다

- [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)

## Compression, Cache, Vary, Accept-Encoding, Personalization

> `Accept-Encoding`, `Vary`, personalization, CDN key가 섞일 때 압축 variant와 shared cache correctness를 어떻게 맞출지 다룬다

- [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)

## Cache, Vary, Accept-Encoding Edge Case Playbook

> `Vary` 누락, unkeyed input cache poisoning, ETag/304 mismatch, personalized variant mix, compression mismatch를 증상 기준으로 추적하는 운영 플레이북이다

- `[playbook]` [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)

## Expect 100-continue, Proxy Request Buffering

> 대용량 업로드에서 `Expect: 100-continue`, auth/rate limit early reject, proxy request buffering이 어떻게 업로드 낭비와 지연을 바꾸는지 정리한다

- [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)

## HTTP Request Body Drain, Early Reject, Keep-Alive Reuse

> 요청 본문을 끝까지 읽기 전에 early reject할 때 unread body를 drain할지 close할지에 따라 keep-alive 재사용과 파싱 안정성이 어떻게 달라지는지 설명한다

- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)

## HTTP/2 Upload Early Reject, RST_STREAM, Flow-Control Cleanup

> H2 large upload를 early reject할 때 final response, `RST_STREAM`, late DATA discard, connection-level flow control cleanup을 어떻게 함께 해석해야 하는지 정리한다

- [HTTP/2 Upload Early Reject, RST_STREAM, Flow-Control Cleanup](./http2-upload-early-reject-rst-stream-flow-control-cleanup.md)
- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
- [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
- [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
- [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
- [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)

## Gateway Buffering vs Spring Early Reject

> `Expect: 100-continue`, gateway request buffering, Spring Security/filter reject, unread-body cleanup를 한 업로드 path로 묶어 어느 홉이 실제 body 비용을 부담했는지와 무엇을 계측해야 하는지 정리한다

- [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
- [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
- [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [WebFlux Request-Body Abort Surface Map](./webflux-request-body-abort-surface-map.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](../spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)

## Proxy-to-Container Upload Cleanup Matrix

> gateway buffering, `Expect: 100-continue`, Spring reject phase, servlet container unread-body cleanup를 한 매트릭스로 묶어 edge `401/413/499`를 origin behavior로 역추적하는 문서다

- [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
- [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
- [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
- [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

## Multipart Parsing vs Auth Reject Boundary

> `MultipartFilter` 위치, `DispatcherServlet.checkMultipart()`, eager/lazy multipart resolution에 따라 같은 `401/403`도 header-only reject에서 body-consuming reject로 경계가 이동하는 지점을 정리한다

- [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
- [Spring Multipart Exception Translation Matrix](./spring-multipart-exception-translation-matrix.md)
- [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [Spring Multipart Upload Request Pipeline](../spring/spring-multipart-upload-request-pipeline.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](../spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)

## Spring Multipart Exception Translation Matrix

> Spring top-level multipart 예외를 container root cause, 기본 status owner, 관측 필드로 다시 풀어 "`MultipartException`이 보인 뒤 무엇부터 확인할지"를 symptom-first 기준으로 정리한다

- [Spring Multipart Exception Translation Matrix](./spring-multipart-exception-translation-matrix.md)
- [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
- [Proxy-to-Container Upload Cleanup Matrix](./proxy-to-container-upload-cleanup-matrix.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
- [Spring Multipart Upload Request Pipeline](../spring/spring-multipart-upload-request-pipeline.md)
- [Spring Security `ExceptionTranslationFilter`, `AuthenticationEntryPoint`, `AccessDeniedHandler`](../spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md)

## Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains

> `client disconnect`, `499`, `broken pipe`, `connection reset`, `proxy timeout`이 hop마다 다른 번역본으로 보이는 이유와 cancel 신호를 end-to-end로 전파하는 법을 다룬다

- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

## SSE Failure Attribution Across HTTP/1.1 and HTTP/2

> 같은 SSE downstream abort가 downstream H2에서는 `RST_STREAM`, edge에서는 `499`, upstream H1에서는 chunked flush failure, H1 read-side에서는 `EOF`로 갈라져 보일 때 어떤 표면이 같은 incident의 번역본인지 정리한다

- [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md)
- [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
- [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
- [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)

## gRPC Deadlines, Cancellation Propagation

> gRPC의 deadline과 cancellation이 proxy hop, downstream service, async 작업까지 어떻게 전파되어야 하는지 정리한다

- [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)

## Proxy Retry Budget Discipline

> proxy retry와 app retry가 겹쳐 증폭되지 않도록 retry budget을 어디서 끊고 어떻게 관측할지 정리한다

- [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)

## Network, Spring Request Lifecycle, Timeout, Disconnect Bridge

> 네트워크에서 보이는 upload early reject, `499`, `client disconnect`, `client closed request`, `connection reset`, `proxy timeout`, async timeout mismatch, first-byte 지연, commit 후 late write failure를 Spring MVC/WebFlux 요청 생명주기와 이어 설명한다

## Network, Spring Request Lifecycle, Timeout, Disconnect Bridge (계속 2)

- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
- [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md)
- [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
- [WebFlux Request-Body Abort Surface Map](./webflux-request-body-abort-surface-map.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [Spring WebClient Connection Pool and Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)

## Spring MVC Async `onError` to `AsyncRequestNotUsableException` Crosswalk

> container `onError`, committed response, 늦게 깨어난 producer의 2차 write가 서로 다른 시계로 움직일 때 어떤 예외가 1차 transport signal이고 어떤 예외가 Spring guardrail인지 타임라인으로 정리한다

- [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
- [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## Container-Specific Disconnect Logging Recipes for Spring Boot

> Spring Boot에서 client abort noise를 Tomcat, Jetty, Undertow별 좁은 logger category로 줄이면서 access log, `AsyncRequestNotUsableException`, late write regression guardrail을 같이 유지하는 법을 정리한다

- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
- [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
- [Spring Servlet Container Disconnect Exception Mapping](../spring/spring-servlet-container-disconnect-exception-mapping.md)

## Access Log Correlation Recipes: Tomcat, Jetty, Undertow

> Tomcat과 Jetty의 `%X`, Tomcat `%F`, Undertow의 `RESPONSE_TIME`/custom bucket 차이를 이용해 `bytes_sent + duration + disconnect_bucket` 축으로 access log를 정규화하는 방법을 정리한다

- [Access Log Correlation Recipes: Tomcat, Jetty, Undertow](./access-log-correlation-recipes-tomcat-jetty-undertow.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)

## DisconnectedClientHelper Breadcrumb Wiring

> `DisconnectedClientHelper`를 MVC download, `SseEmitter` heartbeat, `AsyncRequestNotUsableException` tail advice에 어떻게 배치해야 expected disconnect breadcrumb만 남기고 non-disconnect는 그대로 올릴 수 있는지 wiring 예제로 정리한다

- [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
- [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)

## SSE/WebFlux Streaming Cancel After First Byte

> SSE/WebFlux stream에서 first byte commit 뒤 downstream disconnect, partial flush failure, cancel lag가 서로 다른 시계로 움직일 때 무엇을 마지막 정상 이벤트로 볼지 정리한다

- [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
- [WebFlux Cancel-Lag Tuning](./webflux-cancel-lag-tuning.md)
- [SSE Last-Event-ID Replay Window](./sse-last-event-id-replay-window.md)
- [SSE, WebSocket, Polling](./sse-websocket-polling.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)
- [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)

## WebFlux Cancel-Lag Tuning

> Reactor Netty/WebFlux stream에서 prefetch, explicit buffer, blocking bridge 선택이 downstream disconnect 이후 post-cancel work를 얼마나 남기는지와 어떤 tuning 순서가 실제 stop latency를 줄이는지 정리한다

- [WebFlux Cancel-Lag Tuning](./webflux-cancel-lag-tuning.md)
- [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
- [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Spring Reactive Blocking Bridge and `boundedElastic` Traps](../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)

## WebFlux Request-Body Abort Surface Map

> Reactor Netty/WebFlux request-read EOF/reset, truncated multipart, pre-handler cancel이 `AbortedException`/`IOException`, `DecodingException`, `ServerWebInputException`/`ContentTooLargeException`으로 어떻게 갈라지고, 시그니처에 따라 handler 전후 경계가 왜 바뀌는지 정리한다

- [WebFlux Request-Body Abort Surface Map](./webflux-request-body-abort-surface-map.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Multipart Parsing vs Auth Reject Boundary](./multipart-parsing-vs-auth-reject-boundary.md)
- [WebFlux Cancel-Lag Tuning](./webflux-cancel-lag-tuning.md)
- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

## SSE Last-Event-ID Replay Window

> SSE reconnect에서 `Last-Event-ID`, replay window, duplicate suppression, gap recovery를 어떻게 한 세트로 설계해야 partial delivery 뒤에도 상태를 복원할 수 있는지 다룬다

- [SSE Last-Event-ID Replay Window](./sse-last-event-id-replay-window.md)
- [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
- [SSE, WebSocket, Polling](./sse-websocket-polling.md)
- [WebSocket heartbeat, backpressure, reconnect](./websocket-heartbeat-backpressure-reconnect.md)
- [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)

## Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow

> request body EOF/reset, multipart parse failure, unread-body cleanup, committed-response late write가 Tomcat, Jetty, Undertow에서 서로 다른 예외와 cleanup 정책으로 surface될 때 Spring의 `MultipartException`/`AsyncRequestNotUsableException`까지 어떻게 다시 번역할지 정리한다

- [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
- [Spring Multipart Exception Translation Matrix](./spring-multipart-exception-translation-matrix.md)
- [WebFlux Request-Body Abort Surface Map](./webflux-request-body-abort-surface-map.md)
- [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
- [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
- [Spring Multipart Upload Request Pipeline](../spring/spring-multipart-upload-request-pipeline.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

## Proxy Local Reply vs Upstream Error Attribution

> 사용자가 본 502/503/504/429가 upstream app 결과인지 proxy/gateway가 local reply로 만든 것인지 구분하는 관측과 blame 포인트를 정리한다

- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)
- [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)

## Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB

> 같은 upstream 문제를 Nginx `499`, Envoy downstream disconnect flag, ALB `401/460`, `proxy timeout`, `connection reset`처럼 서로 다르게 surface할 때, buffered upload reject와 drain-vs-close 관측 축까지 generic failure category로 번역하는 감각을 정리한다

- [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)
- [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
- [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
- [Connection Draining vs FIN, RST, Graceful Close](./connection-draining-vs-fin-rst-graceful-close.md)

## Connection Keep-Alive, Load Balancing, Circuit Breaker

- [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
- [Spring RestClient vs WebClient Lifecycle Boundaries](../spring/spring-restclient-vs-webclient-lifecycle-boundaries.md)
- [Spring WebClient Connection Pool and Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)

## Connection Pool Starvation, Stale Idle Reuse, Debugging

> long-lived stream, stale idle socket, borrow validation 부재, keepalive mismatch가 겹칠 때 connection pool starvation이 어떻게 생기고 어떻게 구분할지 다룬다

- [Connection Pool Starvation, Stale Idle Reuse, Debugging](./connection-pool-starvation-stale-idle-reuse-debugging.md)

## Queue Saturation Attribution, Metrics, Runbook

> worker queue, pending acquire, H2 stream queue, sidecar queue, write backlog를 같은 축의 메트릭으로 묶고, timeout-before-dispatch와 timeout ladder까지 포함해 attribution하는 런북이다

- `[runbook]` [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md)
- [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [Mesh Adaptive Concurrency, Local Reply, Metrics Tuning](./mesh-adaptive-concurrency-local-reply-metrics-tuning.md)

## Upstream Queueing, Connection Pool Wait, Tail Latency

> 실제 네트워크 I/O 시작 전 connection pool과 worker queue에서 생기는 대기 시간이 어떻게 tail latency와 timeout budget을 태우는지 다룬다

- [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)

## gRPC Keepalive, GOAWAY, Max Connection Age

> 장수명 gRPC 연결에서 keepalive ping, `GOAWAY`, max connection age, LB drain이 어떻게 reconnect storm과 맞물리는지 다룬다

- [gRPC Keepalive, GOAWAY, Max Connection Age](./grpc-keepalive-goaway-max-connection-age.md)

## Accept Queue, SYN Backlog, Listen Overflow

> burst traffic에서 half-open queue와 accept queue를 구분하지 못할 때 생기는 `connect timeout`, `SYN retransmission`, health check 착시를 정리한다

- [Accept Queue, SYN Backlog, Listen Overflow](./accept-queue-syn-backlog-listen-overflow.md)

## NAT, Conntrack, Ephemeral Port Exhaustion

- [NAT, Conntrack, Ephemeral Port Exhaustion](./nat-conntrack-ephemeral-port-exhaustion.md)

## Timeout, Retry, Backoff 실전

- [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)

## Timeout 타입: connect, read, write

- [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)

## Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB

> 전체 latency를 DNS, connect, TLS, queue wait, first byte, last byte로 분해해 hop별 병목을 추적하는 방법을 정리한다

- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [Spring RestClient vs WebClient Lifecycle Boundaries](../spring/spring-restclient-vs-webclient-lifecycle-boundaries.md)

## Timeout Budget Propagation Across Proxy, Gateway, Service Hops

> proxy, gateway, service hop chain에서 end-to-end timeout budget을 어떻게 깎아 전달해야 하는지와 hop별 timeout reset이 만드는 504, zombie work, retry 증폭을 다룬다

- [Edge는 `504`인데 App은 `200`? Timeout Budget Mismatch Beginner Bridge](./edge-504-but-app-200-timeout-budget-mismatch-beginner-bridge.md) - 브라우저 timeline 1장과 hop-by-hop 표 1개로 `edge 504`와 app `200`이 함께 보이는 초급자 첫 해석을 고정하는 bridge
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- [Idle Timeout Mismatch: LB / Proxy / App](./idle-timeout-mismatch-lb-proxy-app.md)
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)
- [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

## Load Balancer 헬스체크 실패 패턴

- [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)

## HTTP/3와 QUIC 실전 트레이드오프

- [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md)

## HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block

> H3가 조용히 H2/H1로 downgrade되는 경로를 `Alt-Svc`, UDP 차단, ALPN, edge policy 관점에서 어떻게 추적할지 정리한다

- [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

## CDN 캐시 키와 무효화 전략

- [CDN 캐시 키와 무효화 전략](./cdn-cache-key-invalidation.md)

## Retry Storm Containment, Concurrency Limiter, Load Shedding

> retry budget을 넘어서 concurrency limiter, queue cap, local shedding으로 retry storm를 어떻게 containment할지 운영 관점으로 정리한다

- [Retry Storm Containment, Concurrency Limiter, Load Shedding](./retry-storm-containment-concurrency-limiter-load-shedding.md)

## Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh

> latency와 queue pressure를 early overload signal로 써서 dynamic concurrency limit을 조절하는 adaptive limiter를 gateway/mesh 관점에서 다룬다

- [Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh](./adaptive-concurrency-limiter-latency-signal-gateway-mesh.md)

## Mesh Adaptive Concurrency, Local Reply, Metrics Tuning

> mesh adaptive concurrency에서 inflight limit 추세, local reply reason bucket, vendor symptom crosswalk, route/class별 reject 분포를 어떻게 읽고 튜닝할지 다룬다

- [Mesh Adaptive Concurrency, Local Reply, Metrics Tuning](./mesh-adaptive-concurrency-local-reply-metrics-tuning.md)

## WebSocket heartbeat, backpressure, reconnect

- [WebSocket heartbeat, backpressure, reconnect](./websocket-heartbeat-backpressure-reconnect.md)

## DNS TTL과 캐시 실패 패턴

- [DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md)

## Cache-Control 실전

- [Cache-Control 실전](./cache-control-practical.md)

## SSE, WebSocket, Polling

- [SSE, WebSocket, Polling](./sse-websocket-polling.md)
- [SSE Last-Event-ID Replay Window](./sse-last-event-id-replay-window.md)

## Forwarded / X-Forwarded-For / X-Real-IP 신뢰 경계

> reverse proxy 체인에서 실제 클라이언트 IP를 어디까지 믿을지와 spoofing 위험을 다룬다

- [Forwarded / X-Forwarded-For / X-Real-IP 신뢰 경계](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)

---

## 보조 primer

아래 구간은 최신 운영 catalog보다는 레거시 설명/보조 학습 성격이 강한 primer 문서다.

## DNS round robin 방식

아래의 자료에서 자세한 설명과 코드를 볼 수 있다.

- 작성자 윤가영 | [DNS round robin & network flow](./materials/yoongoing_networkflow.pdf)

---

## 웹 통신의 흐름

최신 primer는 아래 문서로 URL -> DNS -> TCP/TLS -> HTTP -> cookie/session/proxy 흐름을 먼저 잡고, 이 구간은 레거시 보조 설명으로 보면 된다.

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)

#### 웹이란 ?

`WWW (world wide web)` 의 약자이며 인터넷으로 연결된 컴퓨터를 통해 정보를 공유할 수 있는 공간을 뜻한다.

흔히들 웹과 인터넷을 통용하여 사용하는데 엄연히 다른 개념이다.

#### 웹 통신

기본적으로 웹 통신은 `HTTP 프로토콜`을 사용하여 통신한다.

통신의 주체를 크게 `Client`와 `Server`로 나눌 수 있다.

- **Client**: 서버에게 정보를 요청하거나 접속하고자 하는 주체

  - ex) 브라우저

- **Server**: 클라이언트에게 정보 혹은 서비스를 제공하는 컴퓨터 (혹은 시스템)

이러한 클라이언트와 서버가 `Request`와 `Response` 를 주고받으며 통신이 일어난다.

#### 웹 통신 세부과정

`https://www.naver.com/` 주소창에 해당 URL을 입력한 뒤 클라이언트에 화면이 렌더링 되기까지 어떤 과정이 있을까?

그 전에, `IP주소`와 `도메인 이름` 그리고 이 둘의 관계에 대해 알아보자.

- IP주소란, 컴퓨터들의 고유 식별번호로 생각하면 된다. IP주소는 `127.0.0.1`과 같은 형태의 숫자로 나타난다.

  > 현재는 .으로 구분된 각 자리에서 0~255를 나타낼 수 있는 32비트의 IPv4 프로토콜을 사용하나, 인터넷 사용자 수 증가로 IP주소 부족 현상이 일어났고 이는 128비트의 IPv6가 등장하는 배경이 되었다.

- 도메인 이름이란, 사람이 쉽게 외울 수 있도록 IP주소를 어떠한 문자로 표현한 것을 의미한다. 즉, 위 URL에서 `naver.com`이 도메인 이름에 해당한다.

> 터미널을 켠 뒤 `host naver.com`을 입력해보자.
> `naver.com` 도메인이 갖는 IP주소를 알 수 있고, 주소창에 해당 IP주소를 입력하면 도메인을 입력했을 때와 같은 결과를 얻는다.

**즉**, 브라우저에 입력된 도메인 이름을 통해 **해당 도메인의 IP주소를 얻은 뒤** 통신을 시작할 수 있다는 것이다.

이러한 `도메인 이름->IP` 과정에서 필요한 도우미 역할을 하는 것이 `DNS`이다.

_다음의 그림과 함께 살펴보자._

![](http://tcpschool.com/lectures/img_webbasic_10.png)

작동 과정은 다음과 같다.

## 웹 통신의 흐름 (계속 2)

1. 사용자가 **도메인 이름** 입력
2. **DNS**를 통해 도메인 이름과 매핑되는 IP주소 획득
3. **HTTP** 프로토콜을 사용하여 요청 `(=HTTP Request)` 생성
4. **TCP** 프로토콜을 사용하여 **서버의 IP주소 컴퓨터**로 Request 전송
5. 서버가 클라이언트의 **요청**에 대한 **응답** `(=HTTP Response)` 전송
6. 브라우저에 도착한 Response는 **웹페이지를 나타내는 데이터**로 변환되어 브라우저에 나타남.

웹 통신의 물리적인 요소와 관련된 자세한 설명은 아래의 자료에서 볼 수 있다.

- 작성자 윤가영 | [DNS round robin & network flow](./materials/yoongoing_networkflow.pdf)

---

## 질의응답

_질문에 대한 답을 말해보며 공부한 내용을 점검할 수 있으며, 클릭하면 답변 내용을 확인할 수 있습니다._

<details>
<summary>OSI 7계층을 택하면 좋은점이 무엇일까요?</summary>
<p>

1. 네트워크 통신이 일어나는 과정을 단계별로 살필 수 있기 때문에 문제 원인의 범위를 좁힐 수 있어 효율적이다.
2. 장비 간 호환성을 제공하며 네트워크 장치/컴퓨팅 장치를 만들 때의 참조모델 표준이 될 수 있다.

</p>
</details>

<details>
<summary>많은 직장인들이 아웃룩을 이용하여 회사 메일을 관리하고 있습니다. 아웃룩과 관련된 계층과 프로토콜을 말해주세요.</summary>
<p>

- 계층 : 7계층, Application Layer
- 프로토콜 : SMTP, POP3

아웃룩은 메시지 프로토콜을 사용하기 쉽게하는 응용프로그램이다.

</p>
</details>

<details>
<summary>이전에 저희 회사의 서비스를 제공받는 모든 고객의 pc에서 서비스 중단 이 일어났습니다. OSI 7계층의 관점으로 몇번째 계층의 문제임을 예상할 수 있을까요?</summary>
<p>

한명의 고객이 아닌, “모든 고객의 pc”에서 문제가 생겼으므로, `1계층` 혹은 `3계층`에 문제가 있음을 예상할 수 있다.

</p>
</details>

<details>
<summary>서버에 문제가 생겼는데, Ping Test 시 문제는 없었습니다. 그렇다면 어느 계층에서 문제가 있다는 것을 유추할 수 있나요?</summary>
<p>

Ping Test는 3계층(네트워크 레이어)에 속한다. 즉, 4계층 ~ 7계층 사이에서 문제가 발생한 것으로 유추할 수 있다.

</p>
</details>

<details>
<summary>유튜브와 같은 스트리밍 서비스를 제작해보려합니다. 이때 어떤 프로토콜로 구현할 것인지 관련 계층과 연관지어 말해주세요.</summary>
<p>

의도한 답 : 스트리밍에서는 연속성이 중요하기 때문에 신뢰도는 낮지만 빠른 4계층 transport layer의 `UDP 프로토콜`을 사용하여 구현하겠습니다.

</p>
</details>

---

<details>
<summary>http 프로토콜을 사용하여 개발한 경험이 있다면 말씀해주세요.</summary>
<p>
정해진 답 없음.
</p>
</details>

<details>
<summary>http는 연결성일까요, 비 연결성일까요? 근거를 들어 말해주세요.</summary>
<p>

비연결성이다.

`비연결성`이란 클라이언트와 서버가 한 번 연결을 맺은 후, 클라이언트 요청에 대해 서버가 응답을 마치면 맺었던 연결을 끊어 버리는 성질을 말한다.

하지만 다수의 클라이언트와 서버간의 연결상태를 유지하려면 자원이 많이 필요하다. HTTP는 다수의 클라이언트가 웹 서버에 요청하는 방식을 띄므로 연결지속에 필요한 자원을 줄여 더 많은 `Connection` 을 수립하는 것에 중점을 둔다.

</p>
</details>

## 질의응답 (계속 2)

<details>
<summary>비 연결성의 장점은 무엇인가요?</summary>
<p>

서버에서 다수의 클라이언트와 연결을 유지한다면, 그만큼 리소스가 많이 필요하게 된다. 비연결성이면, 이에 따른 리소스를 줄여 더 많은 연결을 할 수 있다.

</p>
</details>

<details>
<summary>비 연결성의 단점은 무엇이고, 해결법은 무엇인가요?</summary>
<p>

서버가 클라이언트를 기억하고 있지 않아 동일한 클라이언트의 요청에 대해 매번 연결 시도/해제의 작업을 해야하므로 오버헤드가 증가한다.

기본적으로 HTTP Header에는 `Keep-Alive` 속성이 있는데, 이를 통해 연결에 대한 타임아웃을 지정할 수 있다.

연결성외에 클라이언트의 상태 정보를 저장하기 위해서는 `Cookie`, `Token`, `Session` 을 사용하기도한다.

</p>
</details>

<details>
<summary>데이터를 조회하기 위한 용도로 POST가 아닌 GET 방식을 사용하는 이유는 무엇인가요?</summary>

1. 설계 원칙에 따라 GET 방식은 서버에게 여러 번 요청을 하더라도 동일한 응답이 돌아와야 한다. (멱등성)
    - GET 방식은 "가져오는 것"으로, 서버의 데이터나 상태를 변경시키지 않아야 한다.
      (ex. 게시판의 리스트, 게시글 보기 기능 | 예외. 방문자의 로그 남기기, 글을 읽은 횟수 증가 기능)
    - POST 방식은 "수행하는 것"으로, 서버의 값이나 상태를 바꾸기 위한 용도이다.
      (ex. 게시판에 글쓰기 기능)
2. 웹에서 모든 리소스는 Link할 수 있는 url을 가지고 있어야 한다.
    - 어떤 웹페이지를 조회할 때 원하는 페이지로 바로 이동하거나 이동시키기 위해서는 해당 링크의 정보가 필요하다.
    - 만일 POST 방식을 사용한다면, 링크의 정보가 Body에 있기 때문에 url만 전달할 수 없으므로 GET 방식을 사용해야 한다. 글을 저장하는 경우에는 URL을 제공할 필요가 없기 때문에 POST 방식을 사용한다.

</details>

<details>
<summary>웹 애플리케이션 제작 시 조회/삭제/수정의 업무를 하려고합니다. 각각을 어떤 방식으로 설계할 것인지 말해주세요.</summary>
<p>

의도한 답 : 조회는 `GET`, 삭제는 `DETELE`, 수정은 `POST`로 설계할 것이다. GET은 조회하기 위한 메서드로 `멱등성`을 만족하기 위해 데이터의 수정이 없어야하며, POST는 서버의 값 혹은 상태를 변경하기 위한 메서드로 수정하기 위해 사용한다. RESTful API에 근거하여 삭제는 DELETE로 설계한다.

</p>
</details>

---

<details>
<summary>TCP의 특성에 대해서 말씀해주세요. </summary>
<p>

## 질의응답 (계속 3)

TCP는 `Transfer Control Protocol`로 4계층 Transport Layer에 속하는 프로토콜이다.
1. `3-way Handshaking`을 통해 논리적인 경로의 연결을 수립하고 `4-way Handshaking`을 통해 논리적인 경로의 연결을 해제하는 `Connect Oriented` 즉, 연결지향성 프로토콜이다.
2. 혼잡제어, 흐름제어 기능을 제공한다.
3. `Reliable Data Transfer(=RDT)` 즉, 신뢰성 있는 전송을 지원한다. RDT1.0 ~ RDT3.0 등으로 발전해왔으며 `Go-Back-N`, `Selective Repeat`, `타이머`를 통한 timeout 등 다양한 방식이 있다.
4. HTTP, E-mail, File Transfer 등에 사용된다.
</p>
</details>

<details>
<summary>UDP의 특성에 대해서 말씀해주세요. </summary>
<p>

UDP는 `User Datagram Protocol`로 TCP와 같이 전송계층에 속해있으나 갖는 특징이 조금 다르다.

1. 비연결형, `Connectionless` 프로토콜이다. TCP와 같은 Handshaking 절차가 존재하지 않는다.
2. TCP에서 지원하는 흐름제어, 혼잡제어, 순서보장, 전송보장 기능을 제공하지 않는다.
3. 최소한의 오류검출을 위해 `checksum` 을 활용한다.
4. TCP에 비해 빠른 속도와 적은 부하를 갖기에 `실시간 스트리밍`, `DNS`에 사용하기 적합하다.

</p>
</details>

---

<!-- 4월 3주차 CS면접 주제 : [Network] HTTP와 HTTPS, DNS, 웹 통신 흐름 -->
<!-- 여기 HTTP & HTTPS -->

<details>
<summary>HTTP또는 암호화 되지 않은 프로토콜의 문제점은 무엇이 있나요?</summary>
<p>

1. 평문 통신이기 때문에 도청이 가능하다.

2. 통신 상대를 확인하지 않기 때문에 위장이 가능하다.

3. 완전성을 증명할 수 없기 때문에 변조가 가능하다.

</p>
</details>

<details>
<summary>이러한 문제를 해결하기 위한 다양한 방안이 존재하는데 대표적으로 HTTPS 가 있습니다. HTTPS에 대해 설명 해주시겠어요?</summary>
<p>

HTTPS는 HTTP에 SSL을 덮어 씌운것 과 같다. 원래 HTTP의 통신하는 소켓 부분을 SSL 또는 TLS라는 프로토콜로 대체하는 것이다. HTTP는 원래 TCP와 직접 통신했다면 HTTPS에서는 HTTP와 SSL이 통신하고 SSL과 TCP가 통신하는 방식이라 할 수 있다. SSL을 이용하는 HTTP는 암호화와 증명서, 안전성 보호를 이용할 수 있게 된다. 등등

</p>
</details>

<details>
<summary>HTTP 와 HTTPS 중 어떤 프로토콜이 더 많이 사용 된다고 생각하는지와 그 이유에 대해서 말씀해주세요.</summary>
<p>

## 질의응답 (계속 4)

HTTPS가 보안적인 면에서 뛰어난 만큼 처리해야할 작업이 많아 속도가 떨어져 중요한 데이터 처리 이외에는 HTTP를 사용할 것이라 생각하겠지만 큰 오산이다. 약 10년전 CPU만해도 이러한 작업을 처리하는데 아무런 문제가 없이 사용될만한 실험적 수치를 보였다. 또한 HTTPS 만을 지원하도록 HTTP/2(사실상 HTTP도 지원하지만 개발팀이 그렇게 개발하지 않음)는 다중화와 우선순위를 이용하여 더빠르게 페이지를 로드하는 구글의 네트워크 프로토콜  SPDY를 기반으로 하고 있다. 그래서 HTTP/2를 지원하는 웹이라면 HTTPS 가 속도 조차 더욱 빠르다. 이러한 이유들로 개인정보와 크게 상관없는 사이트들 조차 선택이 아닌 필수로 HTTPS를 사용하고 있다.

[참고링크](https://tech.ssut.me/https-is-faster-than-http/)

</p>
</details>

---

<!-- DNS -->

<details>
<summary>DNS 서버는 무슨 역할을 하나요?</summary>
<p>

DNS 시스템은 ip주소와 도메인 이름의 매핑을 관리합니다. DNS 서버는 ip 주소와 도메인 간의 변환 작업을 수행하며, 사용자가 도메인 이름을 웹 브라우저에 입력하면 해당 사용자를 어떤 서버에 연결할 것인지를 제어하는 역할을 합니다.

</p>
</details>

<details>
<summary>도메인과 ip 주소에 대해서 설명해보세요.</summary>
<p>

인터넷은 서버들을 유일하게 구분할 수 있는 ip 주소를 기본 체계로 이용합니다. 하지만 ip 주소는 숫자로 이루어진 조합이라 인간이 기억하기엔 무리가 있습니다. 따라서 우리는 기억하기 편한 언어 체계의 도메인 이름을 통해 웹 서버에 접속합니다.

</p>
</details>

<details>
<summary>도메인의 구조에 대해서 설명해주세요.</summary>
<p>

도메인은 .(dot) 또는 루트(root)라고 불리는 도메인 이하에 Inverted tree 구조로 구성되어 있습니다. 1단계부터 차례대로 TLD(Top Level Domain), SLD(Second Level Domain), SubDomain이라고 합니다.

</p>
</details>

<details>
<summary>DNS 서버의 Recursive Query 과정을 설명해주세요.</summary>
<p>

로컬 DNS 서버가 여러 DNS 서버를 차례대로 (루트 → com → naver.com DNS 서버) 질의해서 ip 주소를 찾아가는 과정을 말합니다.

</p>
</details>

<details>
<summary>RoundRobin DNS 에 대해 간략하게 설명 해주시겠어요?</summary>
<p>

클라이언트의 웹서버 IP를 요청하는 쿼리를 받을 때마다 여러대의 웹서버를 번갈아가면서 가르쳐즘으로 부화를 분산시키는 로드밸런싱 방법이다.

</p>
</details>

## 질의응답 (계속 5)

<details>
<summary>Round Robin DNS의 문제점은 무엇이 있을 까요?</summary>
<p>

필요한 서버만큼 공인 IP 주소 필요, 균등하게 분산되지 않을 수 있음(특히 스마트폰의 경우), 서버가 다운되어도 확인 불가 하고, 유저들에게 해당 IP를 제공할 수도 있음.

</p>
</details>

<details>
<summary>이러한 문제점을 해결하기 위한 스케줄링 알고리즘에 대해 설명 해주실 수 있나요?</summary>
<p>

Weighted Round Robin : Round Robin과 같지만 가중치를 더해서 분산비율을 변경한다. 가중치가 큰 서버일 수록 자주 선택되므로 처리능력이 높은 서버를 가중치를 높게 설정한다.

Least Connection : 접속수가 가장 적은 서버를 선택한다.

</p>
</details>

---

<!-- 웹 통신 흐름 -->

<details>
<summary>인터넷에 <code>www.naver.com</code>을 쳤을 때, 브라우저의 렌더링 과정에 대해 설명해주세요.</summary>
<p>

1. 로컬 DNS 서버에게 `www.naver.com`에 해당하는 ip 주소가 있는지 물어본다. 있다면 바로 해당 ip로 받아온다.
2. 없다면, 루트 DNS 서버에 물어본다. 있다면 바로 해당 ip로 받아온다.
3. 없다면, `.com`을 관리하는 DNS 서버에 물어본다. 있다면 바로 해당 ip로 받아온다.
4. 없다면, `naver.com`을 관리하는 DNS 서버에 물어본다. 있다면 바로 해당 ip로 받아온다.
5. 목적지의 ip를 알게 되었다. TCP 통신을 통해 소켓을 개방한다. (웹 브라우저 ⇔ 서버 : TCP 3 way handshaking 방식을 통한 커넥션 생성)
6. HTTP 프로토콜로 요청한다.
7. 라우팅 중 프록시 서버를 만난다면, 웹 캐시에 저장된 정보를 response 받는다.
8. 프록시 서버를 만나지 못해 `www.naver.com`을 서빙하는 서버까지 간다면 서버에서 요청에 맞는 데이터를 response로 전송한다.
9. 브라우저의 loader가 해당 response를 다운로드할지 말지 결정한다.
10. 브라우저의 웹 엔진이 다운로드한 .html 파일을 파싱하여 DOM 트리를 결정한다.
11. .html 파싱 중 script 태그를 만나면 파싱을 중단한다.
12. script 태그에 있는 자원을 다운로드하여 처리가 완료되면 다시 파싱을 재개한다.
13. css parser가 .css 파일을 파싱하여 스타일 규칙을 DOM 트리에 추가하여 렌더 트리를 만든다.
14. 렌더 트리를 기반으로 브라우저의 크기에 따라 각 노드들이 크기를 결정한다.
15. 페인트한다. (렌더링 엔진이 배치를 시작한다.)

</p>
</details>

<details>
<summary>브라우저가 전송한 request 메시지를 웹 서버까지 전송하고 그 응답을 받기까지의 과정을 설명해주세요.</summary>
<p>

## 질의응답 (계속 6)

> 브라우저 → 프로토콜 스택 → LAN 어댑터 → 스위칭 허브 → 라우터 → 인터넷 → 웹 서버 LAN → 웹 서버 → 웹 서버 어플리케이션 → 응답은 왔던 길 그대로 돌아감

1. 운영체제에 내장된 네트워크 제어용 소프트웨어인 프로토콜 스택이 브라우저로부터 메시지를 받습니다.
2. 브라우저로부터 받은 메시지를 패킷 속에 저장하고, 수신처 주소 등의 제어 정보를 덧붙여 패킷을 LAN 어댑터에 넘깁니다.
3. LAN 어댑터는 다음 Hop의 Mac 주소를 붙인 프레임을 전기 신호로 변환시키고 신호를 LAN 케이블에 송출시킵니다.
4. LAN 어댑터가 송신한 프레임은 스위칭 허브를 경유하여 인터넷 접속용 라우터에 도착합니다.
5. 라우터는 패킷을 프로바이더(통신사)에게 전달합니다.
6. 패킷은 인터넷의 입구에 있는 액세스 회선(통신 회선)에 의해 POP(Point Of Presence, 통신사용 라우터)까지 운반됩니다.
7. 패킷은 POP를 거쳐 인터넷의 핵심부로 들어가 목적지를 향해 흘러갑니다.
8. 패킷은 인터넷 핵심부를 통과하여 목적지 웹 서버측의 LAN에 도착합니다.
9. 기다리고 있던 방화벽이 도착한 패킷을 검사합니다. 또한 캐시 서버가 웹 서버까지 갈지 말지를 판단합니다.
10. 패킷이 물리적인 웹 서버에 도착하면 웹 서버의 프로토콜 스택이 패킷을 추출하여 메시지를 복원하고 웹 서버 어플리케이션에 넘깁니다.
11. 메시지를 받은 웹 서버 어플리케이션은 요청 메시지에 따른 데이터를 응답 메시지에 넣어 클라이언트로 회송합니다. 응답 메시지는 왔던 방식 그대로 돌아갑니다.

</p>
</details>

<details>
<summary>프로토콜 스택은 어떤 역할을 하나요?</summary>
<p>

통신 중 오류가 발생했을 때 제어 정보를 사용하여 고쳐보내거나, 각종 상황을 조절하는 등 네트워크 세계의 비서와 같은 역할을 합니다.

</p>
</details>

<details>
<summary>프록시 서버는 어떤 기능을 하나요?</summary>
<p>

프록시 서버는 클라이언트로부터 요청된 내용들을 캐시에 저장하고 다음에 같은 요청이 들어온다면 캐시에 저장된 정보를 제공합니다. 이로써 전송 시간을 줄일 수 있습니다.

</p>
</details>

<details>
<summary>그럼 두 번 이상 요청된 내용은 프록시 서버 캐시로부터 다운로드받게 될텐데 페이지의 값이 바뀐다면 어떻게 처리할 수 있나요?</summary>
<p>

최초 요청 시 실제 서버에서 캐시 만료 기한을 설정해서 프록시 서버로 보내면 됩니다. 프록시 서버로 사용자가 요청을 했을 때 요청한 시각이 만료 기한이 이내라면 프록시 서버에서 다운로드를 하고, 그렇지 않다면 실제 서버로 다시 요청합니다.

</p>
</details>

<details>
<summary>서로 다른 프로토콜을 사용하는 두 네트워크를 연결하기 위한 방법은 무엇이 있을 까요?</summary>
<p>

## 질의응답 (계속 7)

게이트웨이란 현재 사용자가 위치한 네트워크에서 다른 네트워크로 이동하기 위해 반드시 거쳐야하는 거점을 의미한다. 두 컴퓨터 네트워크 상에서 서로 연결되기 위해서는 동일한 통신 프로토콜을 사용해야 한다. 따라서 프로토콜이 다른 네트워크 상의 컴퓨터와 두 프로토콜을 적절히 변환해 주는 변환기가 필요한데, 게이트웨이가 바로 이러한 변환기 역할을 한다.

</p>
</details>

<details>
<summary>CORS 문제가 무엇이고 경험해본적 있는가요?</summary>
<p>

CORS는 Cross Origin Resource Sharing의 약자로 클라이언트가 도메인 및 포트가 다른 서버로  요청했을 때 브라우저가 보안상의 이유로 API를 차단하는 문제이다.  예로 들면 로컬에서 클라이언트는 3000 포트로 서버는 10000 포트로 서버를 띄웠을때 또는 로컬 서버에서 다른 서버로 호출할 때 발생하게 된다.

</p>
</details>

## 한 줄 정리

Network (네트워크)는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
