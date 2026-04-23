# Secure Cookie Behind Proxy Guide

> 한 줄 요약: 브라우저는 HTTPS로 접속했는데 앱은 proxy 뒤 HTTP 요청으로 착각하면 `Secure` cookie, login redirect, session 복원이 서로 어긋나서 login cookie가 "안 남는 것처럼" 보일 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
> - [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)
> - [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md)
> - [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)
> - [HTTPS와 TLS 기초](./https-tls-beginner.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
> - [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: secure cookie behind proxy, secure cookie proxy guide, secure cookie login loop, tls termination cookie issue, tls termination login cookie missing, X-Forwarded-Proto mismatch, x-forwarded-proto login loop, reverse proxy secure cookie, load balancer https http mismatch, browser sees https app sees http, app thinks request is http, request.isSecure false, secure cookie not persisting, secure cookie not sent after redirect, https login redirects to http, X-Forwarded-Host redirect, host preservation load balancer, wrong origin callback, proxy trust headers, ingress secure cookie issue, ALB secure cookie loop, nginx x-forwarded-proto cookie, spring forward headers secure cookie, express trust proxy secure cookie, secure session cookie behind proxy, login works locally but fails behind proxy, secure cookie dropped after http redirect, browser session troubleshooting return path, proxy cookie return path, 401 302 proxy branch
retrieval-anchor-keywords: SameSite None vs X-Forwarded-Proto, external IdP iframe vs proxy mismatch, redirect becomes http after login, proxy cookie mismatch beginner

## 이 문서를 먼저 읽는 이유

초보자가 자주 보는 장면은 이렇다.

- 로컬에서는 로그인 유지가 잘 된다
- 그런데 ALB, Nginx, ingress, reverse proxy 뒤에 올리면 login loop가 난다
- `Domain`, `Path`, `SameSite`는 멀쩡해 보인다
- `Application > Cookies`에는 session cookie가 보이기도 한다

이때 핵심 원인은 종종 이것이다.

- **브라우저는 "나는 HTTPS였다"고 생각한다**
- **앱은 "아니, HTTP 요청이 왔다"고 생각한다**

즉 cookie 자체보다 먼저, **원래 요청이 HTTPS였다는 사실이 proxy를 지나 앱까지 제대로 전달됐는지**를 봐야 한다.

---

## 가장 중요한 mental model

같은 login 요청을 세 주체가 다르게 본다고 생각하면 쉽다.

| 주체 | 무엇을 보나 | 여기서 틀리면 생기는 문제 |
|---|---|---|
| 브라우저 | 사용자가 실제로 접속한 URL과 scheme (`http` / `https`) | `Secure` cookie를 언제 보낼지 결정한다 |
| TLS 종료 proxy | 바깥 HTTPS를 내부 HTTP로 바꿔 앱에 전달한다 | 원래 scheme 정보를 앱에 넘겨줘야 한다 |
| 앱 | "이 요청이 secure한가?"를 보고 cookie/redirect를 만든다 | `http://` redirect, 잘못된 session cookie 정책이 나온다 |

핵심 세 문장만 기억하면 된다.

- `Secure` cookie를 **보낼지 말지**는 브라우저가 판단한다.
- login 뒤 **어디로 redirect할지**는 앱이 판단한다.
- proxy는 "원래 HTTPS였다"는 사실을 `X-Forwarded-Proto` 같은 헤더로 앱에 전달한다.

그래서 browser/proxy/app 셋 중 하나라도 scheme을 다르게 이해하면 login이 꼬인다.

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 보통 뜻하는 것 | 먼저 볼 것 |
|---|---|---|
| 로컬에서는 되는데 proxy/LB 뒤에서만 login loop | cookie scope보다 proxy scheme 전달 문제일 수 있다 | login 응답의 `Location`, `Set-Cookie`, 다음 요청 URL |
| HTTPS login 직후 redirect가 `http://...`로 내려온다 | 앱이 요청을 insecure로 읽고 있다 | `X-Forwarded-Proto`, app의 proxy header 신뢰 설정 |
| `Application` 탭에는 cookie가 있는데 redirect 뒤 다음 요청에는 cookie가 안 실린다 | `Secure` cookie가 `http` 요청에는 안 붙는다 | 다음 요청 URL이 `https`인지 `http`인지 |
| `Domain` / `Path` / `SameSite`는 맞아 보이는데 staging/prod에서만 깨진다 | TLS termination 경계가 더 의심된다 | proxy가 original scheme을 넘기는지 |

---

## 정상 흐름은 어떻게 생기나

브라우저 login 요청이 proxy를 거쳐 앱으로 갈 때, 내부 hop이 HTTP여도 괜찮다.
중요한 것은 앱이 **원래 바깥 요청이 HTTPS였다**는 사실을 아는 것이다.

```text
Browser
  POST https://app.example.com/login
        |
        v
TLS termination proxy
  POST http://app-internal/login
  X-Forwarded-Proto: https
        |
        v
App
  "원래 요청은 HTTPS였구나"라고 이해
  Set-Cookie: SESSION=abc; Secure; HttpOnly
  Location: https://app.example.com/dashboard
```

이 흐름이면 브라우저는 다음 요청도 HTTPS로 보내고, `Secure` cookie도 함께 보낸다.

---

## 어디서 깨지나

문제는 TLS termination 뒤에 **scheme 번역**이 틀어질 때 생긴다.

```text
Browser
  POST https://app.example.com/login
        |
        v
TLS termination proxy
  POST http://app-internal/login
  X-Forwarded-Proto: (없음 또는 http)
        |
        v
App
  "HTTP 요청이네"라고 착각
  Set-Cookie: SESSION=abc; Secure; HttpOnly
  Location: http://app.example.com/dashboard
```

그다음 브라우저는 이렇게 행동한다.

1. login 응답을 받아 cookie를 저장할 수 있다
2. 하지만 redirect target이 `http://...`라면 다음 요청은 HTTP가 된다
3. `Secure` cookie는 HTTP 요청에 보내지지 않는다
4. 서버는 session cookie를 못 보고 다시 `/login`으로 보낸다

겉으로는 "cookie가 안 남는다"처럼 보이지만, 실제로는:

- cookie가 저장은 됐지만
- **다음 요청이 `http`가 되어 `Secure` cookie가 빠진 것**일 수 있다

---

## `X-Forwarded-Proto`가 왜 필요한가

TLS termination proxy는 바깥의 HTTPS를 내부 HTTP로 바꾸는 경우가 많다.
그러면 앱 입장에서는 raw TCP 연결만 보면 "HTTP 요청이 왔네?"처럼 보인다.

이때 proxy가 보통 알려 주는 힌트가:

```http
X-Forwarded-Proto: https
```

의미는 단순하다.

- "지금 내가 너에게 HTTP로 전달하긴 했지만"
- "원래 사용자는 HTTPS로 들어왔다"

앱이 이 힌트를 신뢰하고 해석해야:

- absolute redirect URL을 `https://...`로 만들고
- secure request 정책을 올바르게 적용하고
- session cookie 관련 보안 설정도 기대와 맞출 수 있다

반대로 header가 없거나, 값이 틀리거나, 앱이 그 header를 무시하면 문제가 난다.

---

## 왜 `Secure` cookie가 특히 잘 깨지나

`Secure` 속성 자체는 단순하다.

- **HTTPS 요청에서만 cookie를 보낸다**

이 규칙은 보안상 맞는 동작이다.
문제는 login 직후 app이 잘못된 `http://` redirect를 만들거나, request를 insecure로 오해할 때다.

| 장면 | 브라우저 동작 | 결과 |
|---|---|---|
| login 후 다음 요청도 `https://...` | `Secure` cookie 전송 | 정상적으로 session 복원 가능 |
| login 후 redirect가 `http://...` | `Secure` cookie 미전송 | 서버는 익명으로 보고 login loop |
| 바깥은 HTTPS인데 app만 HTTP로 인식 | cookie/redirect 정책이 엇갈림 | prod에서만 재현되는 login failure |

즉 `Secure` cookie는 문제의 원인이라기보다, **scheme mismatch를 드러내는 경보 장치**에 가깝다.

---

## 초보자가 자주 헷갈리는 지점

### 1. "proxy가 TLS를 끝내면 app은 HTTP만 보니까 `Secure` cookie는 원래 못 쓰는 것 아닌가요?"

아니다.

브라우저가 보는 바깥 연결이 HTTPS라면 `Secure` cookie는 정상적으로 쓸 수 있다.
내부 proxy -> app hop이 HTTP인 것 자체는 흔한 구조다.
중요한 것은 app이 forwarded header를 통해 **original scheme을 올바르게 이해하는 것**이다.

### 2. "`Application > Cookies`에 값이 있으면 proxy 문제는 아닌 것 아닌가요?"

아니다.

cookie가 저장됐더라도, 다음 redirect가 `http://...`로 나가면 그 다음 요청에는 `Secure` cookie가 빠질 수 있다.
즉 `cookie stored`와 `cookie sent`는 다른 단계다.

### 3. "`X-Forwarded-Proto`는 브라우저가 보내는 헤더인가요?"

아니다.

보통은 reverse proxy나 load balancer가 앱 쪽으로 추가하는 헤더다.
그래서 app은 이 헤더를 **신뢰 가능한 proxy에서 온 경우에만** 해석해야 한다.

---

## 한 장면으로 보는 실패 예시

아래는 실제로 많이 보는 패턴이다.

| 단계 | 보이는 것 | 실제 의미 |
|---|---|---|
| 1. 사용자가 `https://app.example.com/login`에 로그인 | 브라우저는 HTTPS라고 인식 | 바깥 연결은 안전하다 |
| 2. proxy가 TLS를 종료하고 app에 HTTP로 전달 | app raw request는 HTTP처럼 보일 수 있다 | forwarded header가 필요하다 |
| 3. app이 `X-Forwarded-Proto`를 못 읽는다 | app은 insecure request라고 착각 | redirect/cookie policy가 틀어질 수 있다 |
| 4. app이 `Location: http://app.example.com/home`를 응답 | 브라우저는 다음 이동을 HTTP로 한다 | `Secure` cookie는 이 요청에 안 붙는다 |
| 5. 서버가 session cookie를 못 본다 | 다시 `/login` 또는 익명 응답 | login cookie가 안 남는 것처럼 보인다 |

이 장면은 `Domain`, `Path`, `SameSite`가 모두 맞아도 생길 수 있다.
반대로 redirect와 다음 요청 URL이 계속 `https://...`인데 external IdP callback, partner portal iframe, embedded login 경로에서만 cookie가 안 붙으면 이 문서보다 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) 쪽이 더 가깝다.

---

## 무엇을 확인하면 되나

### 1. 브라우저에서 확인

Network 탭에서 login 직후 두 가지만 본다.

- login 응답의 `Location`이 `https://...`인지
- 다음 요청 URL이 정말 `https://...`인지

그리고 한 단계 더 보면 좋다.

- login 응답에 `Set-Cookie`가 있는지
- 그 다음 요청의 `Cookie` header에 session cookie가 실렸는지

### 2. proxy에서 확인

proxy/LB/ingress가 아래 역할을 하는지 본다.

- TLS termination을 수행하는지
- original scheme을 `X-Forwarded-Proto: https`로 넘기는지
- app이 absolute URL을 만들 때 필요한 host 정보도 보존하는지

### 3. 앱에서 확인

앱이 아래를 제대로 하고 있는지 본다.

- trusted proxy의 forwarded header를 읽는지
- forwarded `https`를 secure request로 해석하는지
- login 후 redirect를 `https://...`로 만드는지
- absolute URL을 만들 때 공개 host를 보존하거나 `X-Forwarded-Host`를 해석하는지

프레임워크마다 설정 이름은 다르지만, 개념은 같다.

- "proxy header를 신뢰할 것"
- "원래 scheme이 HTTPS였다는 사실을 request에 반영할 것"

---

## 이 문서와 다른 원인의 경계

| 이런 장면이면 | 먼저 볼 문서 |
|---|---|
| `auth.example.com`에는 cookie가 보이는데 `app.example.com` 요청에는 안 붙음 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| external IdP, social login callback, partner portal iframe 경로에서만 깨지고 redirect는 계속 HTTPS다 | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) |
| redirect scheme은 HTTPS인데 host가 `app-internal`, `localhost`, staging host로 바뀌거나 OAuth `redirect_uri`가 wrong origin이다 | [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md) |
| redirect는 모두 HTTPS고 request `Cookie` header도 실리는데 서버가 여전히 익명처럼 봄 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| HTTPS, HSTS, MITM, TLS termination 전반을 더 넓게 이해하고 싶음 | [HTTPS / HSTS / MITM](./https-hsts-mitm.md) |

즉 이 문서는:

- `Domain` / `Path` / `SameSite` mismatch 문서가 아니라
- **HTTPS edge와 app 내부 인식이 어긋나는 문제**를 먼저 분리하는 entrypoint다

---

## 다음 단계

- login redirect와 `302 -> /login` 자체를 먼저 다시 읽고 싶으면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 돌아가 `401` 의미와 browser UX redirect를 다시 분리한다.
- request `Cookie` header 자체가 비고 `auth`/`app`/`api` subdomain, `Domain`, `Path`, `SameSite`가 더 의심되면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 옮겨 간다.
- `http://`로 꺾이는 것보다 `Location`이나 OAuth `redirect_uri`의 host가 wrong origin으로 바뀌는 것이 핵심이면 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)에서 host preservation과 `X-Forwarded-Host`를 이어 본다.
- redirect와 다음 요청 URL이 계속 `https://...`인데 external IdP callback, iframe, partner portal 경로에서만 깨지면 [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)로 분기한다.
- redirect는 정상 HTTPS이고 request `Cookie` header도 실리는데 서버가 계속 anonymous로 보면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 server session/BFF mapping 갈래로 다시 타거나 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 다음 갈래를 고른다.

## 한 줄 정리

`Secure` cookie behind proxy 문제의 핵심은 "브라우저는 HTTPS라고 보는데 앱은 HTTP라고 본다"는 불일치다. login cookie가 안 남는 것처럼 보이면 cookie 값만 보지 말고, TLS termination 뒤 `X-Forwarded-Proto`, login redirect scheme, 다음 요청의 실제 URL까지 같이 확인한다.
