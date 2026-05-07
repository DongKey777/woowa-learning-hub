---
schema_version: 3
title: Cookie Rejection Reason Primer
concept_id: security/cookie-rejection-reason-primer
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 70
mission_ids: []
review_feedback_tags:
- cookie rejection reason primer
- devtools set-cookie blocked
- blocked response cookies beginner
- secure cookie blocked http
aliases:
- cookie rejection reason primer
- devtools set-cookie blocked
- blocked response cookies beginner
- secure cookie blocked http
- samesite none without secure
- invalid domain attribute cookie
- cookie path too narrow beginner
- set-cookie 줬는데 저장이 안 됨
- 로그인한 뒤 쿠키가 막힘
- browser session beginner ladder return
- return to browser session troubleshooting path
- cookie rejection next step branch
symptoms: []
intents:
- definition
- deep_dive
prerequisites: []
next_docs: []
linked_paths:
- contents/security/cookie-devtools-field-checklist-primer.md
- contents/security/cookie-prefixes-host-secure-primer.md
- contents/security/secure-cookie-behind-proxy-guide.md
- contents/security/samesite-none-cross-site-login-primer.md
- contents/security/cookie-scope-mismatch-guide.md
- contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
- contents/security/wrong-scheme-vs-wrong-origin-redirect-shortcut.md
- contents/security/browser-401-vs-302-login-redirect-guide.md
- contents/security/fetch-credentials-vs-cookie-scope.md
- contents/security/subdomain-login-callback-boundaries.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Cookie Rejection Reason Primer 핵심 개념을 설명해줘
- cookie rejection reason primer가 왜 필요한지 알려줘
- Cookie Rejection Reason Primer 실무 설계 포인트는 뭐야?
- cookie rejection reason primer에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 security 카테고리에서 Cookie Rejection Reason Primer를 다루는 primer 문서다. DevTools의 `This Set-Cookie was blocked...` 같은 문구는 보통 "쿠키 전체가 신비롭게 망가졌다"는 뜻이 아니라, 브라우저가 `Secure`, `SameSite`, `Domain`, `Path` 중 어느 축에서 멈췄는지 알려 주는 힌트다. 검색 질의가 cookie rejection reason primer, devtools set-cookie blocked, blocked response cookies beginner, secure cookie blocked http처럼 들어오면 인증/인가 보안 설계, 운영 진단, 사고 대응 관점으로 연결한다.
---
# Cookie Rejection Reason Primer

> 한 줄 요약: DevTools의 `This Set-Cookie was blocked...` 같은 문구는 보통 "쿠키 전체가 신비롭게 망가졌다"는 뜻이 아니라, 브라우저가 `Secure`, `SameSite`, `Domain`, `Path` 중 어느 축에서 멈췄는지 알려 주는 힌트다.

**난이도: 🟢 Beginner**

관련 문서:

- `[primer]` [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)
- `[primer detour]` [Cookie Prefixes Primer: `__Host-` vs `__Secure-`](./cookie-prefixes-host-secure-primer.md)
- `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
- `[follow-up]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)
- `[follow-up]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- `[cross-category bridge]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: cookie rejection reason primer, devtools set-cookie blocked, blocked response cookies beginner, secure cookie blocked http, samesite none without secure, invalid domain attribute cookie, cookie path too narrow beginner, set-cookie 줬는데 저장이 안 됨, 로그인한 뒤 쿠키가 막힘, browser session beginner ladder return, return to browser session troubleshooting path, cookie rejection next step branch, cookie rejection reason primer basics, cookie rejection reason primer beginner, cookie rejection reason primer intro
retrieval-anchor-keywords: devtools cookie blocked reason secure, devtools cookie blocked reason samesite, devtools cookie blocked reason domain, devtools cookie blocked reason path, response cookie rejected vs request cookie excluded, cookie stored but not sent path mismatch, blocked response cookies filter, has blocked cookies devtools
retrieval-anchor-keywords: cookie checklist set-cookie issues application cookies, devtools cookie exact columns blocked reason
retrieval-anchor-keywords: samesite vs proxy 15 second check, devtools blocked reason sameSite vs proxy, blocked reason secure vs samesite branch, cookie blocked reason quick branch, devtools blocked cookie 15초 분기
retrieval-anchor-keywords: primer follow-up catalog return ladder, beginner cookie branch return, return to Browser / Session Troubleshooting Path, browser session beginner ladder return, cookie rejection next step branch

## primer -> follow-up -> catalog return ladder

이 문서는 beginner가 blocked reason을 보고 바로 deep dive로 점프하지 않게 만드는 첫 갈림길이다.
읽는 순서는 아래처럼 고정하면 안전하다.

1. `primer`: 이 문서에서 DevTools reason을 `Secure` / `SameSite` / `Domain` / `Path` 축으로 먼저 자른다.
2. `follow-up`: [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md), [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) 중 하나만 고른다.
3. `catalog return`: follow-up을 읽고도 증상이 섞여 보이면 같은 wording인 `return to Browser / Session Troubleshooting Path`로 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) 순서로 돌아간다.

이 문서의 역할은 "원인 확정"이 아니라 "다음 한 문서만 안전하게 고르기"다.
OAuth/OIDC, fetch/CORS, Spring session deep dive는 1차 분기가 끝난 뒤에만 내려간다.

## 이 문서를 먼저 읽는 이유

초보자에게 DevTools의 cookie 경고는 전부 비슷하게 보인다.

- `This Set-Cookie was blocked...`
- `SameSite`가 어쩌고 `Secure`가 어쩌고 나온다
- `Application > Cookies`에는 값이 보이기도 하고 안 보이기도 한다
- 그래서 "도대체 서버가 뭘 잘못한 거지?"가 된다

하지만 beginner 관점에서는 훨씬 단순하게 보면 된다.

- 브라우저가 **이 응답의 cookie를 저장해도 되는가**를 먼저 판단한다
- 저장된 뒤에는 **다음 요청에 이 cookie를 보내도 되는가**를 다시 판단한다

DevTools의 blocked / rejected reason은 이 두 단계 중 어디서 막혔는지 알려 주는 힌트다.

## 먼저 볼 DevTools 칸

blocked reason을 읽기 전에, 초보자는 아래 세 줄이 같은 cookie 이름을 가리키는지 먼저 맞추는 편이 안전하다.

| 먼저 볼 위치 | 정확히 볼 필드 | 왜 먼저 보나 |
|---|---|---|
| `Network > response > Response Headers` | `Set-Cookie` | 서버가 어떤 속성으로 cookie를 내려보냈는지 본다 |
| `Network > response > Issues` | `This Set-Cookie was blocked...` reason | 저장 단계에서 왜 멈췄는지 본다 |
| `Application > Cookies` | 같은 cookie `Name` row가 생겼는지 | blocked reason이 실제 저장 실패로 이어졌는지 본다 |

필드 이름이 익숙하지 않으면 먼저 [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)에서 `Set-Cookie` / `Application row` / request `Cookie` 3칸을 한 번에 보는 표를 보고 돌아오면 된다.

---

## 이 primer가 바로 보내는 다음 세 갈래

이 문서는 beginner가 DevTools 문구를 보고 **다음 한 문서만 고르도록** 만드는 entrypoint다.
먼저 아래 세 갈래 중 하나만 잡고, 더 깊은 문서는 그다음에 내려간다.

| 지금 가장 먼저 보이는 증거 | 여기서 바로 갈 문서 | 왜 이쪽이 첫 걸음인가 |
|---|---|---|
| `Secure`, HTTPS, redirect가 `http://...`로 꺾임, proxy/LB 뒤에서만 재현 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | cookie 속성 자체보다 scheme/proxy 전달이 먼저 틀어졌을 가능성이 크다 |
| `SameSite`, external IdP callback, iframe, partner portal, cross-site 문맥이 먼저 보임 | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) | external site를 거친 cookie 전송 허용 범위를 먼저 정리해야 한다 |
| blocked reason은 약한데 `Application`에는 있고 request `Cookie`는 비거나, `Domain`/`Path`가 더 수상함 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | "저장됨"과 "전송됨"을 분리해서 host/path 범위를 다시 봐야 한다 |

beginner 기준의 안전 장치는 이것이다.

- proxy, `SameSite`, cookie scope 중 **하나만 먼저 고른다**
- OAuth/OIDC, Spring session, BFF deep dive는 이 세 갈래에서 1차 분기가 끝난 뒤에만 내려간다
- 다음 문서를 읽고도 증상이 섞여 보이면 `return to Browser / Session Troubleshooting Path`라는 같은 wording으로 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 다시 고른다

## 다음 한 걸음과 복귀 경로

첫 deep dive handoff를 이미 탔다면, 같은 축을 더 파기 전에 다시 category ladder로 복귀할 cue를 같이 기억하면 덜 헤맨다.

| 방금 읽은 첫 follow-up / deep dive | 바로 이어서 볼 한 문서 | 길을 잃었을 때 복귀할 ladder |
|---|---|---|
| [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | redirect `scheme`까지 같이 틀어졌는지 [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md) | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |
| [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) | iframe / external IdP 증상이면 그 문서의 `15초 체크`만 더 본다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | request `Cookie` header까지 실렸는지 다시 확인한 뒤 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

짧은 규칙:

- 첫 deep dive에서 바로 Spring/BFF로 더 내려가기보다 browser/session ladder anchor로 한 번 되돌아간다.
- `blocked Set-Cookie`가 `stored but not sent`나 `sent but anonymous`로 바뀌면, 현재 문서보다 ladder 재선택이 더 안전하다.

---

## 15초 체크: SameSite vs Proxy

DevTools blocked reason에 `SameSite`와 `Secure`가 같이 보여도, 초보자는 첫 분기를 아래 두 질문으로만 자르면 된다.

| 지금 바로 확인할 것 | 이쪽이면 먼저 갈 문서 | 이유 |
|---|---|---|
| login 응답 `Location`이나 다음 요청 URL이 `http://...`로 꺾였나 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | 브라우저가 `Secure` cookie를 못 보내는 원인이 proxy/scheme mismatch일 가능성이 더 크다 |
| redirect는 계속 `https://...`인데 external IdP callback, iframe, partner portal에서만 막히나 | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md#15초-체크-samesite-vs-proxy) | cross-site cookie 전송 규칙과 proxy 문제를 한 장에서 바로 나눌 수 있다 |

짧은 규칙:

- **redirect가 HTTP로 꺾이면 proxy부터 본다**
- **redirect가 계속 HTTPS인데 external/iframe 경로에서만 깨지면 `SameSite`부터 본다**
- 둘이 섞여 보이면 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md#15초-체크-samesite-vs-proxy)의 분기표로 바로 내려간다

---

## 먼저 잡을 mental model

cookie 문제는 아래 두 질문으로 나누면 덜 헷갈린다.

| 단계 | 브라우저가 묻는 질문 | 여기서 자주 보이는 축 |
|---|---|---|
| 응답 저장 단계 | "이 `Set-Cookie`를 받아들여도 되나?" | `Secure`, `SameSite=None` + `Secure`, invalid `Domain` |
| 다음 요청 전송 단계 | "이 URL에 지금 이 cookie를 붙여도 되나?" | `Domain`, `Path`, `SameSite`, `Secure` |

여기서 beginner가 기억할 한 줄은 이것이다.

- **blocked response cookie**는 저장 자체가 막힌 것
- **stored but not sent**는 저장은 됐지만 다음 요청 scope가 안 맞는 것

`Path`는 특히 두 번째 칸에 자주 나온다.
즉 `Path` 문제는 DevTools의 "blocked response cookie" 문구보다, **다음 요청의 `Cookie` header가 비는 장면**으로 더 자주 보인다.

---

## 먼저 10초 매핑표

DevTools 문구는 브라우저 버전마다 조금 달라질 수 있다.
문장 전체를 외우기보다 **굵은 키워드가 무엇인지** 먼저 본다.

| DevTools에서 먼저 보이는 키워드 | 보통 뜻하는 것 | 가장 먼저 할 수정 |
|---|---|---|
| `Secure` + secure connection / HTTPS 아님 | `Secure` cookie를 HTTP 응답이나 HTTP 요청 흐름에 얹으려 했다 | public URL과 redirect를 `https://`로 유지하고, proxy 뒤라면 `X-Forwarded-Proto`/scheme 인식을 먼저 고친다 |
| `__Secure-` / `__Host-` prefix | cookie 이름 prefix 규칙과 `Secure`/`Domain`/`Path` 조합이 안 맞다 | [Cookie Prefixes Primer: `__Host-` vs `__Secure-`](./cookie-prefixes-host-secure-primer.md)에서 prefix 규칙부터 자른다 |
| `SameSite=None` + `Secure` 없음 | cross-site 전송을 허용하려 했지만 필수 조건인 `Secure`가 빠졌다 | `SameSite=None; Secure`로 같이 보낸다. cross-site가 불필요하면 `None` 자체를 빼고 `Lax`/기본값으로 단순화한다 |
| `SameSite` + cross-site / third-party | 브라우저가 이 흐름을 cross-site로 보고 cookie를 막았다 | external IdP, iframe, partner domain이면 `SameSite=None; Secure`를 검토한다. sibling subdomain만 오간다면 `SameSite`보다 `Domain`을 먼저 의심한다 |
| `Domain` + invalid / current host와 안 맞음 | 이 응답 host가 그 `Domain`을 설정할 자격이 없다 | sibling host를 쓰지 말고 host-only로 두거나, 정말 공유가 필요하면 현재 host의 상위 domain으로 맞춘다 |
| blocked reason은 없는데 callback 다음 API만 익명 | 저장은 됐지만 다음 요청 `Path` 범위가 좁다 | session cookie라면 보통 `Path=/`로 넓히고, callback 전용 cookie면 좁은 `Path`를 유지한다 |

---

## 1. `Secure` reason은 "HTTPS 축"으로 읽는다

### 가장 단순한 해석

DevTools reason이 `Secure`를 강조하면 beginner는 먼저 이렇게 읽으면 된다.

- "이 cookie는 HTTPS 전용인데"
- "브라우저가 지금 흐름을 HTTPS로 보지 않았다"

대표 장면은 둘이다.

1. 서버가 아예 `http://...` 응답에서 `Secure` cookie를 보내고 있다
2. 브라우저는 처음엔 HTTPS였지만, login 직후 redirect가 `http://...`로 꺾였다

### 흔한 예시

```http
Set-Cookie: SESSION=abc123; Path=/; Secure; HttpOnly
```

이 자체는 정상일 수 있다.
문제는 이 헤더가 붙은 응답이나 그 다음 redirect가 HTTP 축으로 보일 때다.

| 장면 | beginner 해석 | 첫 수정 포인트 |
|---|---|---|
| 응답 URL 자체가 `http://app.example.com/login` | insecure 응답에서 `Secure` cookie를 세우려 함 | login 자체를 HTTPS로 고친다 |
| 브라우저에서는 HTTPS로 시작했는데 login 뒤 `Location: http://...` | app/proxy가 scheme을 잘못 이해함 | proxy header, forwarded scheme 신뢰 설정을 본다 |
| localhost만 되는데 staging/prod에서만 깨짐 | proxy/LB 뒤 scheme mismatch 가능성 큼 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)로 간다 |

### 바로 기억할 fix

- public login / callback URL은 끝까지 `https://`여야 한다
- `Secure` cookie가 필요한데 redirect가 `http://...`로 바뀌면 proxy 축을 먼저 본다
- localhost 예외를 prod/staging 기준으로 일반화하면 안 된다

---

## 2. `SameSite` reason은 "cross-site가 정말 필요한가?"부터 묻는다

### 가장 단순한 해석

DevTools가 `SameSite`를 말하면 beginner는 먼저 이렇게 나눈다.

1. 이 흐름이 정말 **cross-site**인가?
2. cross-site라면 `SameSite=None; Secure`가 필요한가?

`SameSite=None`은 "더 강한 보안 옵션"이 아니라,
**cross-site에서도 보내도 된다는 허용**이다.

### 가장 흔한 blocked 조합

```http
Set-Cookie: login_state=xyz; Path=/auth; HttpOnly; SameSite=None
```

이렇게 `SameSite=None`만 주고 `Secure`를 빼면 브라우저가 막을 수 있다.

beginner fix는 보통 이것이다.

```http
Set-Cookie: login_state=xyz; Path=/auth; HttpOnly; SameSite=None; Secure
```

### 같은 `SameSite` 문제처럼 보여도 둘로 나뉜다

| 장면 | 실제로 더 가까운 질문 | 먼저 볼 것 |
|---|---|---|
| external IdP callback, partner iframe, embedded login에서만 실패 | 정말 cross-site cookie 전송이 필요한가 | `SameSite=None; Secure` |
| `auth.example.com` -> `app.example.com` 이동에서만 실패 | same-site sibling subdomain인데 scope가 맞는가 | `Domain`, host-only 여부 |
| cross-origin `fetch`인데 request `Cookie`가 비어 있음 | `SameSite` 전에 `credentials: "include"`가 있는가 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |

### beginner가 자주 놓치는 점

- `auth.example.com`과 `app.example.com`은 origin은 달라도 보통 same-site다
- 그래서 sibling subdomain login loop는 `SameSite`보다 `Domain` 문제인 경우가 더 흔하다
- cross-site가 정말 필요한 cookie에만 `SameSite=None; Secure`를 붙인다

external IdP, social login, iframe 경로에 집중해야 하면 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)로 바로 내려가면 된다.

---

## 3. `Domain` reason은 "이 host가 그 domain을 설정할 수 있나?"로 읽는다

### 가장 단순한 해석

DevTools reason이 `Domain` invalid를 말하면 beginner는 이렇게 보면 된다.

- 응답을 준 host는 자기 자신이나 자기의 상위 domain 쪽만 다룰 수 있다
- **sibling host를 직접 찍어서는 안 된다**

### 흔한 실수 예시

응답 host가 `auth.example.com`인데:

```http
Set-Cookie: SESSION=abc123; Domain=app.example.com; Path=/; Secure; HttpOnly
```

이건 beginner가 보기에는 "앱에서 쓸 거니까 app을 찍자"처럼 보여도,
실제로는 `auth.example.com`이 sibling인 `app.example.com` cookie를 직접 세우려는 셈이라 막힐 수 있다.

보통 fix는 둘 중 하나다.

```http
Set-Cookie: SESSION=abc123; Path=/; Secure; HttpOnly
```

- 현재 host에만 쓸 거면 `Domain`을 아예 빼서 host-only cookie로 둔다

```http
Set-Cookie: SESSION=abc123; Domain=example.com; Path=/; Secure; HttpOnly
```

- sibling subdomain끼리 공유가 목적이면 상위 domain으로 맞춘다

### beginner quick rule

| 의도 | 보통 맞는 선택 |
|---|---|
| `auth.example.com`에서만 쓸 cookie | `Domain` 생략 |
| `auth.example.com`과 `app.example.com`이 함께 쓸 cookie | `Domain=example.com` |
| `auth.example.com` 응답이 `app.example.com`만 콕 집어 주기 | 보통 틀린 방향 |

`auth.example.com/callback` 뒤 `app.example.com` 첫 요청이 anonymous라면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)도 같이 보면 된다.

---

## 4. `Path`는 대개 "blocked reason"보다 "다음 요청 누락"으로 보인다

### 가장 중요한 예외 포인트

이 문서 제목은 rejection reason이지만,
beginner가 `Path`까지 같이 묶어서 이해하려면 이 사실을 알아야 한다.

- `Path`는 보통 cookie 저장 자체를 막는 주범이 아니다
- 대신 **저장된 cookie가 어디까지 전송되나**를 좁힌다

즉 DevTools에 무서운 blocked 문구가 없더라도,
cookie가 `/auth/callback`에서는 살아 있고 `/api/me`에서만 사라지면 `Path` 축을 의심한다.

### 흔한 예시

```http
Set-Cookie: SESSION=abc123; Path=/auth; Secure; HttpOnly
```

이 cookie는 보통 아래처럼 보인다.

| 요청 URL | cookie 전송 여부 |
|---|---|
| `/auth/callback` | 전송됨 |
| `/auth/me` | 전송됨 |
| `/api/me` | 전송 안 됨 |
| `/dashboard` | 전송 안 됨 |

그래서 beginner는 이런 장면을 본다.

1. callback 응답에서 cookie가 저장된다
2. `Application > Cookies`에도 값이 보인다
3. 그런데 다음 `/api/me` 요청 `Cookie` header는 비어 있다
4. 서버는 다시 익명처럼 본다

이때 fix는 보통 단순하다.

- session cookie를 앱 전역에서 쓸 거면 `Path=/`
- callback 전용, CSRF state 전용이라면 좁은 `Path`를 유지

### `Path` 축은 이렇게 기억하면 된다

- `Path`는 "어디서 읽히나"보다 "어느 request path에 붙나"에 가깝다
- "cookie가 저장된 것 같다"와 "지금 이 API에 실렸다"는 다르다
- `Path` 문제는 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 더 자주 보인다

---

## 자주 섞이는 오해

### 1. `auth.example.com` -> `app.example.com`이면 무조건 `SameSite` 문제인가?

아니다.
beginner 환경에서는 대개 먼저 `Domain` 또는 host-only cookie를 본다.

### 2. `SameSite=None`만 넣으면 다 해결되나?

아니다.
`Secure`가 같이 필요하고, 정말 cross-site 전송이 필요한 cookie인지도 다시 봐야 한다.

### 3. `Application > Cookies`에 값이 보이면 저장 성공이니 문제는 서버 쪽인가?

아니다.
그 다음 요청 `Cookie` header가 비면 `Path`, `Domain`, `SameSite`, `Secure` 전송 축일 수 있다.

### 4. `Path`는 보안 경계인가?

아니다.
beginner 관점에서는 "전송 범위를 나누는 스위치" 정도로 이해하면 충분하다.

---

## DevTools에서 이렇게 보면 된다

1. `Network`에서 문제 request를 고른다.
2. `Cookies` 탭에서 response cookie가 blocked 되었는지 본다.
3. reason 문장에서 먼저 `Secure`, `SameSite`, `Domain` 중 무엇이 보이는지 체크한다.
4. response blocked reason이 없는데도 다음 요청이 anonymous면, 바로 다음 request의 `Cookie` header를 보고 `Path`까지 확인한다.

한 줄로 요약하면:

- **문구에 `Secure`가 보이면 HTTPS / proxy**
- **문구에 `SameSite`가 보이면 cross-site 여부**
- **문구에 `Domain`이 보이면 host와 parent domain 관계**
- **문구가 없는데 다음 요청만 비면 `Path`**

---

## follow-up 한 장

표에서 **한 줄만 먼저 고른다.**

| 지금 막힌 지점 | 바로 다음 문서 | 읽고 나서 돌아올 자리 |
|---|---|---|
| HTTPS인데 login 뒤 redirect가 `http://...`로 바뀌거나 proxy 뒤에서만 깨진다 | `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| external IdP callback, iframe, social login에서만 cookie가 안 붙는다 | `[follow-up]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) | `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `Application > Cookies`에는 있는데 request `Cookie`는 비거나 `Domain`/`Path`가 더 수상하다 | `[follow-up]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## follow-up 한 장 (계속 2)

| `auth.example.com/callback` 뒤 첫 요청만 anonymous다 | `[follow-up]` [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) | `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## return to Browser / Session Troubleshooting Path

읽고 나면 복귀 wording은 항상 같게 유지한다.

- `Application`에는 cookie가 있는데 request에 안 붙는 전체 그림이 필요하면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- external IdP, iframe, social login 쪽이면 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)
- HTTPS인데 redirect가 `http://...`로 꺾이거나 proxy 뒤에서만 깨지면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
- `auth.example.com/callback` 뒤 `app.example.com` 첫 요청만 anonymous면 [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
- scope migration 뒤 old cookie cleanup까지 필요하면 [Cookie Scope Migration Cleanup](./cookie-scope-migration-cleanup.md)

막히면 항상 `return to Browser / Session Troubleshooting Path`로 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) 순서로 돌아와
`blocked response cookie인지, stored but not sent인지, sent but anonymous인지`를 다시 고른다.

## 한 줄 정리

이 primer의 beginner-safe 종료 동작은 단순하다. blocked reason으로 첫 follow-up 한 문서만 고르고, 첫 deep dive를 읽은 뒤에는 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)와 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아와 다음 갈래를 다시 고른다.
