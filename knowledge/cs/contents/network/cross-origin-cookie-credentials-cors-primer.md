# Cross-Origin Cookie, `fetch credentials`, CORS 입문

> 한 줄 요약: cookie가 실제 요청에 붙는지는 cookie 속성, `fetch`의 `credentials` 모드, same-site 판단이 함께 결정하고, 브라우저 자바스크립트가 응답을 읽을 수 있는지는 CORS가 결정한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
> - [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
> - [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
> - [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)
> - [CORS Credential Pitfalls / Allowlist Design](../security/cors-credential-pitfalls-allowlist.md)
> - [CSRF in SPA + BFF Architecture](../security/csrf-in-spa-bff-architecture.md)

retrieval-anchor-keywords: cross-origin cookie primer, fetch credentials mode, credentials same-origin include omit, same-origin vs same-site, cross-origin same-site cookie, cross-site cookie fetch, CORS credentials cookie, Access-Control-Allow-Credentials, Access-Control-Allow-Origin exact origin, Set-Cookie cross-origin fetch, subdomain cookie fetch, app.example.com api.example.com cookie, why cookie not sent on fetch, why Set-Cookie not stored cross origin, same-site not same-origin, cross-site cookie SameSite None Secure, SameSite Lax Strict None matrix, cookie attribute matrix, Domain Path cookie scope

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 `origin`과 `site`를 구분하자](#먼저-origin과-site를-구분하자)
- [`fetch.credentials`는 무엇을 바꾸나](#fetchcredentials는-무엇을-바꾸나)
- [CORS는 무엇을 바꾸나](#cors는-무엇을-바꾸나)
- [한 번에 보는 판단 순서](#한-번에-보는-판단-순서)
- [브라우저 요청 흐름 1: same-origin API 호출](#브라우저-요청-흐름-1-same-origin-api-호출)
- [브라우저 요청 흐름 2: cross-origin 이지만 same-site인 서브도메인 API 호출](#브라우저-요청-흐름-2-cross-origin-이지만-same-site인-서브도메인-api-호출)
- [브라우저 요청 흐름 3: cross-site API 호출](#브라우저-요청-흐름-3-cross-site-api-호출)
- [왜 링크 이동은 되는데 `fetch`는 안 되나](#왜-링크-이동은-되는데-fetch는-안-되나)
- [디버깅 체크리스트](#디버깅-체크리스트)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 문서가 필요한가

입문 단계에서 특히 자주 섞이는 말이 아래 네 개다.

- `same-origin`
- `same-site`
- `fetch(..., { credentials })`
- `CORS`

이 네 개를 한 덩어리로 외우면 금방 막힌다.

- `app.example.com`에서 `api.example.com`으로 `fetch`하면 왜 cookie가 안 붙는가
- `credentials: "include"`를 넣었는데 왜 여전히 cookie가 안 보이는가
- 응답에 `Set-Cookie`가 있는데 왜 브라우저에 저장되지 않는가
- 서버 로그에는 요청이 왔는데 프론트 콘솔에는 CORS 에러만 보이는가

핵심은 각 장치가 서로 다른 질문에 답한다는 점이다.

- cookie 속성: "이 cookie를 이 요청에 붙여도 되는가"
- `credentials`: "브라우저가 이번 요청에서 credential을 보내고, 응답의 `Set-Cookie`를 받아들일 것인가"
- CORS: "브라우저 자바스크립트가 이 cross-origin 응답을 읽어도 되는가"

cookie 속성 자체의 의미가 먼저 헷갈리면 [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)를 먼저 보고 오면 이 문서가 더 빨리 읽힌다.

### Retrieval Anchors

- `cross-origin cookie primer`
- `fetch credentials mode`
- `same-origin vs same-site`
- `why cookie not sent on fetch`
- `Set-Cookie cross-origin fetch`
- `CORS credentials cookie`

---

## 먼저 `origin`과 `site`를 구분하자

이 문서의 절반은 사실 이 구분만 서면 정리된다.

- `origin`: 스킴 + 호스트 + 포트
- `site`: 대략 같은 registrable domain 계열인지 보는 더 넓은 단위

예를 들면:

| 페이지 위치 | 요청 대상 | same-origin? | same-site? |
|---|---|---|---|
| `https://app.example.com` | `https://app.example.com/api/me` | 예 | 예 |
| `https://app.example.com` | `https://api.example.com/me` | 아니오 | 예 |
| `https://app.example.com` | `https://partner.com/me` | 아니오 | 아니오 |
| `https://app.example.com` | `https://app.example.com:8443/me` | 아니오 | 예 |

여기서 beginner가 가장 자주 놓치는 포인트는 이것이다.

- `app.example.com -> api.example.com`은 same-site일 수 있지만 same-origin은 아니다
- 그래서 cookie의 `SameSite` 판단과 CORS 판단이 서로 다른 답을 낼 수 있다

즉:

- `SameSite`는 `site`를 본다
- CORS와 `credentials: "same-origin"`은 `origin`을 본다

---

## `fetch.credentials`는 무엇을 바꾸나

`fetch`의 `credentials`는 브라우저가 브라우저 관리 credential을 어떻게 다룰지 정하는 스위치다.

| 값 | 의미 | 입문 감각 |
|---|---|---|
| `omit` | 보내지도 않고, 응답의 credential도 받지 않음 | cookie를 완전히 끄는 모드 |
| `same-origin` | same-origin일 때만 보냄/받음 | 기본값 |
| `include` | cross-origin에서도 보냄/받을 수 있게 함 | 단, cookie 규칙과 CORS가 따로 맞아야 함 |

핵심은 `include`가 "무조건 cookie를 붙여라"가 아니라는 점이다.

- cookie가 요청 대상 host/domain에 맞아야 한다
- `Path`, `Secure`, 만료 시간이 맞아야 한다
- `SameSite` 규칙을 통과해야 한다

즉 `credentials`는 허가문이고, cookie 속성은 실제 탑승 조건이다.

또 하나 중요한 점:

- cross-origin `fetch`에서 응답에 `Set-Cookie`가 와도
- 요청이 `credentials: "include"`가 아니면
- 브라우저는 그 `Set-Cookie`를 무시할 수 있다

그래서 login API를 cross-origin으로 호출하는 SPA에서 아래 실수가 자주 난다.

```js
await fetch("https://api.example.com/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
```

이 코드는 요청은 성공해도, cross-origin이면 cookie가 저장되지 않아서 다음 요청에서 인증이 풀릴 수 있다.

---

## CORS는 무엇을 바꾸나

CORS는 cookie 전송 규칙 그 자체가 아니다.
CORS는 브라우저 자바스크립트가 cross-origin 응답을 읽을 수 있는지를 다룬다.

그래서 아래를 분리해서 봐야 한다.

- cookie가 요청에 붙었는가
- 응답이 자바스크립트에 노출되었는가

credential이 들어가는 cross-origin 요청이라면 서버는 보통 아래 조건을 맞춰야 한다.

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
```

여기서 중요하다.

- `Access-Control-Allow-Origin: *`와 credential 응답은 같이 쓰면 안 된다
- cross-origin에서 cookie를 주고받으려면 보통 `Allow-Origin`에 정확한 origin이 와야 한다

또 practical하게 기억할 점:

- simple cross-origin 요청은 서버까지 간 뒤, 응답만 JS에서 막힐 수 있다
- preflight가 필요한 요청은 `OPTIONS`가 실패하면 실제 요청이 아예 안 나갈 수 있다

즉 CORS 에러가 보인다고 항상 "서버가 요청을 못 받았다"는 뜻은 아니다.

---

## 한 번에 보는 판단 순서

브라우저가 cross-origin cookie를 붙일지 헷갈리면 아래 순서대로 보면 된다.

1. 요청 대상이 same-origin인가?
2. same-origin이 아니라면 `credentials: "include"`를 썼는가?
3. 보내려는 cookie가 요청 대상 host/domain/path에 맞는가?
4. `Secure`, 만료 시간, `SameSite`를 통과하는가?
5. 프론트 코드가 응답을 읽어야 한다면 서버 CORS 헤더가 맞는가?
6. cross-site라면 브라우저 privacy 정책이나 third-party cookie 제한이 추가로 막지 않는가?

이 순서를 표로 줄이면 아래처럼 볼 수 있다.

| 조건 | 없으면 무슨 일이 생기나 |
|---|---|
| `credentials: "include"` | cross-origin `fetch`에서 cookie 송수신이 안 된다 |
| cookie host/domain/path 일치 | 대상 서버용 cookie가 아니므로 안 붙는다 |
| `SameSite=None; Secure` for cross-site | cross-site `fetch`에 cookie가 안 붙는다 |
| 정확한 `Access-Control-Allow-Origin` | JS가 응답을 읽지 못한다 |
| `Access-Control-Allow-Credentials: true` | credentialed CORS 응답이 브라우저에서 막힌다 |

---

## 브라우저 요청 흐름 1: same-origin API 호출

페이지와 API가 완전히 같은 origin이면 가장 단순하다.

```js
fetch("/api/me");
```

이 경우:

- 기본 `credentials: "same-origin"`만으로도 충분하다
- cookie가 host/path/Secure 등에 맞으면 자동 전송된다
- CORS도 필요 없다

흐름은 보통 아래와 같다.

```text
1. 브라우저가 같은 origin으로 요청한다
2. 저장된 cookie 중 대상에 맞는 cookie를 붙인다
3. 서버가 응답한다
4. 브라우저가 응답을 정상적으로 읽고, Set-Cookie도 반영한다
```

즉 same-origin에서는 `credentials`와 CORS가 거의 의식되지 않는다.

---

## 브라우저 요청 흐름 2: cross-origin 이지만 same-site인 서브도메인 API 호출

가장 많이 헷갈리는 케이스다.

- 페이지: `https://app.example.com`
- API: `https://api.example.com`

이 조합은:

- same-origin: 아니오
- same-site: 예

기본 `fetch`는 이렇게 된다.

```js
fetch("https://api.example.com/me");
```

이때는 기본값이 `credentials: "same-origin"`이라서:

- cross-origin 요청이므로 browser cookie를 보내지 않는다
- 응답의 `Set-Cookie`도 cross-origin에서는 기대대로 반영되지 않을 수 있다
- 게다가 JS가 응답을 읽으려면 CORS도 필요하다

보통 의도한 코드는 아래 쪽이다.

```js
fetch("https://api.example.com/me", {
  credentials: "include",
});
```

그래도 여기서 끝이 아니다.

- cookie가 `api.example.com`용이거나 공유 domain 규칙에 맞아야 한다
- `SameSite`는 same-site 요청이므로 `Lax`/`Strict`라도 통과할 수 있다
- 서버는 여전히 CORS를 열어야 프론트 JS가 응답을 읽는다

즉 이 케이스의 핵심은:

- same-site라서 `SameSite`는 통과할 수 있다
- 하지만 cross-origin이라서 기본 `credentials`로는 cookie가 안 붙는다

이 차이를 헷갈리면 "분명 같은 회사 도메인인데 왜 cookie가 안 가지?"라는 질문이 계속 나온다.

---

## 브라우저 요청 흐름 3: cross-site API 호출

이번에는 페이지와 API가 아예 다른 site라고 보자.

- 페이지: `https://shop.example.com`
- API: `https://auth.partner.com`

이 경우 `credentials: "include"`만으로는 부족하다.

```js
fetch("https://auth.partner.com/session", {
  credentials: "include",
});
```

추가로 아래 조건이 더 필요하다.

- cookie가 `auth.partner.com`에 대해 유효해야 한다
- cookie가 `SameSite=None; Secure`여야 한다
- 서버가 정확한 CORS credential 응답을 보내야 한다

예를 들면:

```http
Set-Cookie: sid=abc123; Path=/; HttpOnly; Secure; SameSite=None
Access-Control-Allow-Origin: https://shop.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
```

왜 이렇게 엄격하냐면:

- cross-site cookie는 CSRF, third-party tracking 같은 민감한 경계와 바로 닿기 때문이다

그래서 cross-site cookie 흐름은 보통:

```text
include를 켠다
-> cookie가 target domain에 맞는지 본다
-> SameSite=None; Secure인지 본다
-> 브라우저 privacy 정책이 허용하는지 본다
-> CORS 응답이 정확한지 본다
```

하나라도 빠지면 "요청은 갔는데 cookie가 없거나", "응답은 왔는데 JS가 못 읽는" 상태가 된다.

---

## 왜 링크 이동은 되는데 `fetch`는 안 되나

`SameSite=Lax` 때문에 자주 생기는 현상이다.

`Lax` cookie는:

- same-site 요청에는 보통 전송된다
- cross-site여도 top-level navigation 같은 일부 안전한 이동에는 전송될 수 있다
- 하지만 cross-site `fetch()`에는 보통 전송되지 않는다

그래서 이런 장면이 나온다.

- 사용자가 링크를 클릭해 `https://partner.com/dashboard`로 이동하면 cookie가 붙는다
- 하지만 `fetch("https://partner.com/api/me", { credentials: "include" })`는 cookie가 안 붙는다

즉 "브라우저 주소창 이동"과 "페이지 내부 JS fetch"는 같은 cross-site처럼 보여도 cookie 규칙이 다르게 작동할 수 있다.

이 차이를 알면:

- "redirect login은 되는데 AJAX 인증 확인은 실패한다"
- "클릭으로 들어가면 로그인돼 있는데 SPA 호출은 401이다"

같은 현상을 더 빨리 설명할 수 있다.

---

## 디버깅 체크리스트

브라우저 DevTools에서 아래 순서로 보면 가장 빠르다.

### 1. Request URL과 `Origin`

- 페이지 origin이 어디인가
- 요청 대상 origin이 어디인가
- same-origin인지, cross-origin인지 먼저 확정한다

### 2. Request Headers의 `Cookie`

- 정말 `Cookie` 헤더가 붙었는가
- 안 붙었다면 `credentials`, domain/path, `SameSite`, `Secure` 쪽 문제다

### 3. Response Headers의 `Set-Cookie`

- login 응답에 `Set-Cookie`가 실제로 왔는가
- `SameSite=None; Secure`가 필요한 케이스인데 빠지지 않았는가

### 4. Response Headers의 CORS

- `Access-Control-Allow-Origin`이 정확한 origin인가
- `Access-Control-Allow-Credentials: true`가 있는가
- `Vary: Origin`이 있는가

### 5. Preflight 여부

- `OPTIONS`가 먼저 나갔는가
- `OPTIONS`가 실패해서 실제 요청이 안 간 것은 아닌가

### 6. Storage/Application 탭

- cookie가 실제 저장되었는가
- 저장됐더라도 대상 domain/path가 요청 URL과 맞는가

---

## 자주 헷갈리는 포인트

### 1. `same-site`면 CORS가 필요 없는가

아니다.

- `app.example.com -> api.example.com`은 same-site일 수 있어도 cross-origin이다
- cross-origin이면 CORS 대상이다

### 2. `credentials: "include"`면 cookie가 무조건 붙는가

아니다.

- cookie 대상 domain/path가 맞아야 한다
- `Secure`, `SameSite`, 만료 시간도 통과해야 한다

### 3. CORS를 열면 cookie도 자동으로 붙는가

아니다.

- CORS는 응답 읽기 규칙이다
- cookie 전송은 cookie 속성과 `credentials`가 먼저 결정한다

### 4. `HttpOnly`면 `fetch`에서 안 보내지는가

아니다.

- `HttpOnly`는 JS 읽기를 막는 옵션이다
- 브라우저 자동 전송은 계속 일어날 수 있다

### 5. login 응답에 `Set-Cookie`가 보이면 저장도 됐다고 보면 되는가

아니다.

- cross-origin이면 `credentials` 모드가 맞아야 한다
- cross-site면 `SameSite=None; Secure`가 필요할 수 있다
- CORS credential 응답도 맞아야 한다

---

## 면접에서 자주 나오는 질문

### Q. `same-origin`과 `same-site`는 왜 구분해야 하나요?

- `same-origin`은 CORS와 `fetch` 기본 credential 동작에 직접 연결된다
- `same-site`는 `SameSite` cookie 전송 규칙에 직접 연결된다
- `app.example.com -> api.example.com` 같은 실무 구조를 설명하려면 둘을 나눠야 한다

### Q. `credentials: "include"`는 정확히 무엇을 하나요?

- cross-origin에서도 browser-managed credential을 보내고 받을 수 있게 한다
- 하지만 cookie 규칙을 무시하고 강제로 보내는 것은 아니다

### Q. cross-origin cookie 요청에 왜 `Access-Control-Allow-Origin: *`를 쓰면 안 되나요?

- credentialed CORS 응답은 wildcard로 열 수 없기 때문이다
- 정확한 origin과 `Access-Control-Allow-Credentials: true`가 필요하다

### Q. 왜 링크 이동은 되는데 `fetch`는 401이 나올 수 있나요?

- `SameSite=Lax`는 일부 top-level navigation에는 cookie를 보내지만
- cross-site `fetch`에는 cookie를 보내지 않기 때문이다

## 한 줄 정리

cross-origin browser request를 이해하려면 `origin`, `site`, `credentials`, CORS를 따로 보고, 마지막에 "cookie가 붙는가"와 "응답을 읽는가"를 합쳐서 판단해야 한다.
