# SameSite=None Cross-Site Login Primer

> 한 줄 요약: external IdP callback, partner portal iframe, embedded login처럼 브라우저가 **cross-site 맥락**에서 cookie를 다시 보내야 하는 흐름은 `SameSite=None; Secure` 축으로 봐야 하고, proxy 뒤에서 app이 HTTPS를 HTTP로 오해하는 문제는 `X-Forwarded-Proto` 축으로 따로 봐야 한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: SameSite None cross-site login primer, samesite none secure login primer, SameSite=None external IdP cookie, SameSite=None iframe login cookie, external IdP callback cookie missing, partner portal iframe login loop, embedded login cookie blocked, social login cookie blocked SameSite, cross-site login cookie not sent, cross-site callback state cookie missing, SameSite None vs X-Forwarded-Proto, samesite vs x-forwarded-proto, external IdP vs proxy cookie mismatch, iframe login vs proxy mismatch, Secure cookie proxy mismatch vs SameSite, browser cross-site cookie send rule, partner iframe session cookie beginner, federated login cookie not sent beginner, security readme browser session troubleshooting

## 이 문서를 먼저 읽는 이유

초보자에게는 아래 장면이 전부 비슷하게 보인다.

- social login은 시작되는데 callback 뒤 다시 로그인 화면으로 튄다
- partner portal iframe 안에서만 로그인 유지가 안 된다
- proxy/LB 뒤에서만 cookie가 안 남는 것처럼 보인다
- 팀 안에서는 모두 "cookie 문제"라고 부른다

하지만 실제로는 질문이 둘이다.

1. 브라우저가 **cross-site 맥락에서도 이 cookie를 보내도 되나?**
2. app이 **원래 요청이 HTTPS였다는 사실을 알고 있나?**

첫 질문은 `SameSite` 축이고, 둘째 질문은 `X-Forwarded-Proto` 축이다.

---

## 가장 중요한 mental model

| 질문 | 누가 판단하나 | 여기서 틀리면 생기는 일 |
|---|---|---|
| 이 cookie를 cross-site 요청에도 보내도 되나? | 브라우저가 `SameSite`로 판단 | external IdP, iframe, partner domain 흐름에서 cookie가 안 붙는다 |
| 원래 사용자는 HTTPS로 들어왔나? | proxy와 app이 `X-Forwarded-Proto` 같은 forwarded header로 판단 | login 응답이 `http://...`로 나가고 `Secure` cookie가 다음 요청에 빠진다 |

핵심은 이것이다.

- `SameSite`는 **브라우저의 cookie 전송 규칙**이다.
- `X-Forwarded-Proto`는 **app의 scheme 이해**다.

둘 다 실패하면 겉으로는 "login cookie가 안 남는다"처럼 보이지만, 관찰 포인트는 다르다.

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 더 가까운 원인 | 먼저 볼 것 |
|---|---|---|
| external IdP, partner portal, iframe 경로에서만 깨지고 직접 `app.example.com`으로 열면 된다 | `SameSite=None; Secure`가 필요한 cross-site cookie 전송 문제일 수 있다 | 실패 요청이 여전히 `https://...`인지, cookie가 어떤 `SameSite`로 발급됐는지 |
| 로컬은 되는데 ALB/Nginx/ingress 뒤에서만 깨지고 login 직후 `Location`이 `http://...`로 바뀐다 | proxy `X-Forwarded-Proto` mismatch일 수 있다 | login 응답의 `Location`, 다음 요청 URL, trusted proxy 설정 |
| `auth.example.com`에서는 되는데 `app.example.com`이나 `api.example.com`으로 가면 풀린다 | `SameSite`보다 `Domain`/host-only/`Path` 문제일 수 있다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |

이 표에서 가장 실용적인 한 줄은 이것이다.

- **redirect가 계속 HTTPS인데 external/iframe 경로에서만 cookie가 안 붙으면 `SameSite` 쪽**
- **redirect가 HTTP로 꺾이면 proxy 쪽**

---

## 장면 1: external IdP나 iframe에서만 깨지는 경우

이 축은 브라우저가 "지금은 cross-site 맥락이네"라고 보는 순간 생긴다.

대표적인 장면은 이렇다.

- 외부 IdP callback이 기존 login transaction cookie를 다시 필요로 한다
- partner site 안 iframe으로 앱을 연다
- embedded login completion이 top-level page가 아니라 frame 안에서 일어난다

이때 브라우저는 cookie를 저장했더라도, `SameSite=Lax`나 `Strict`라면 **그 cross-site 요청에는 안 보낼 수 있다.**

### 간단한 예시

로그인 시작 시 app이 state/session cookie를 이렇게 만들었다고 하자.

```http
Set-Cookie: login_state=xyz; Path=/auth; HttpOnly; Secure; SameSite=Lax
```

이 설정은 같은 site 안에서 잘 동작할 수 있다.
하지만 아래 장면에서는 부족할 수 있다.

- external IdP가 돌아오는 callback에서 기존 cookie를 다시 읽어야 한다
- partner portal iframe 안에서 app API를 호출한다

이 경우 필요한 cookie라면 보통 아래처럼 cross-site 전송을 허용해야 한다.

```http
Set-Cookie: login_state=xyz; Path=/auth; HttpOnly; Secure; SameSite=None
```

중요한 점은 "`None`이 더 강한 설정"이 아니라, **cross-site에서도 보내도 된다는 허용**이라는 점이다.
그래서 정말 필요한 cookie에만 제한적으로 써야 한다.

---

## 장면 2: proxy 뒤에서만 깨지는 경우

이 축은 브라우저보다 app이 헷갈릴 때 생긴다.

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
  Location: http://app.example.com/home
```

이후 브라우저는 `http://...`로 이동한다.
그러면 `Secure` cookie는 다음 요청에 붙지 않는다.

즉 이 경우 문제는:

- `SameSite=None`이 없어서가 아니라
- app이 원래 HTTPS였다는 사실을 몰라서 `http://` redirect를 만든 것

이다.

이 장면은 특히 아래 특징을 가진다.

- local에서는 잘 된다
- reverse proxy/LB/ingress 뒤에서만 깨진다
- login 응답의 `Location`이 `http://...`로 보이거나, next request URL이 HTTP다

---

## 같은 "cookie 문제"처럼 보여도 증거는 다르다

| 관찰 포인트 | `SameSite=None; Secure` 쪽 | `X-Forwarded-Proto` 쪽 |
|---|---|---|
| 언제 자주 깨지나 | external IdP, iframe, partner domain, embedded login | ALB, ingress, reverse proxy 뒤 배포 환경 |
| login 응답의 `Location` | 대개 `https://...`이거나 relative URL | `http://...`로 내려가는 경우가 많다 |
| 실패 요청 URL | 여전히 HTTPS일 수 있다 | HTTP로 바뀌는 경우가 많다 |
| request `Cookie` header가 비는 이유 | 브라우저가 cross-site 전송을 막음 | 브라우저가 HTTP 요청에는 `Secure` cookie를 안 보냄 |
| 첫 수정 포인트 | 필요한 cookie만 `SameSite=None; Secure`로 조정 | forwarded header 신뢰, `X-Forwarded-Proto`, redirect scheme 수정 |

---

## 초보자가 가장 자주 섞는 오해

### 1. "`auth.example.com`에서 `app.example.com`으로 가면 cross-site 아닌가요?"

보통은 아니다.

- same-origin은 아닐 수 있다
- 하지만 same-site인 경우가 많다

그래서 sibling subdomain 문제는 먼저 `SameSite=None`보다:

- host-only cookie인가
- `Domain`이 너무 좁은가
- `Path`가 callback에만 묶였는가

를 본다.

이 분해는 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 이어 간다.

### 2. "`SameSite=None`만 주면 끝나나요?"

아니다.

- `None`이면 `Secure`가 같이 필요하다
- cross-site cookie가 열리면 CSRF 방어도 같이 봐야 한다

즉 `SameSite=None; Secure`는 login 성공 버튼이 아니라, **cross-site 허용과 보안 부담을 함께 여는 설정**이다.

### 3. "`Secure` cookie가 안 붙으니 무조건 proxy 문제 아닌가요?"

아니다.

`Secure`는 단지 HTTPS에서만 전송된다는 뜻이다.

- 실패 요청이 여전히 HTTPS인데 external IdP/iframe 경로에서만 cookie가 안 붙으면 `SameSite` 쪽일 수 있다
- 실패 요청이 HTTP로 바뀌면 proxy 쪽일 가능성이 크다

즉 `Secure`는 두 문제에 모두 등장할 수 있지만, **원인 분류는 요청 맥락과 URL scheme으로 한다.**

---

## 무엇을 먼저 확인하면 되나

### 1. Network 탭에서 `Location`과 다음 요청 URL을 본다

- login 응답 `Location`이 `http://...`인가?
- 다음 요청이 실제로 HTTP로 가는가?

여기서 HTTP가 보이면 proxy `X-Forwarded-Proto` 쪽을 먼저 본다.

### 2. 실패가 언제만 재현되는지 본다

- external IdP callback에서만 그런가?
- partner portal iframe 안에서만 그런가?
- 직접 app URL을 열면 괜찮은가?

이렇다면 `SameSite` 축이 더 가깝다.

### 3. `Set-Cookie` 속성을 본다

- `SameSite=Lax` 또는 `Strict`인가?
- 정말 cross-site 전송이 필요한 cookie인가?
- `SameSite=None`이라면 `Secure`도 같이 있는가?

### 4. sibling subdomain 문제를 먼저 빼고 본다

`auth.example.com` -> `app.example.com` 이동이면 `SameSite`보다 `Domain`/host-only가 더 흔하다.
이 경우 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 먼저 간다.

---

## 이 문서와 다른 원인의 경계

| 이런 장면이면 | 먼저 볼 문서 |
|---|---|
| `auth.example.com`에는 cookie가 보이는데 `app.example.com` 요청에는 안 붙는다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| login 직후 `Location`이 `http://...`로 바뀌거나 proxy/LB 뒤에서만 깨진다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `fetch credentials`, CORS credential 응답, cookie scope가 한 문제처럼 섞인다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |
| cross-site cookie를 열었더니 callback 뒤 첫 POST의 CSRF 경계가 헷갈린다 | [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md) |
| external IdP callback hardening과 session regeneration까지 같이 보고 싶다 | [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md), [Session Fixation in Federated Login](./session-fixation-in-federated-login.md) |

---

## 한 줄 정리

external IdP/iframe login failure는 먼저 "브라우저가 cross-site라서 cookie를 안 보내는가"를 보고, proxy/LB 뒤 login failure는 먼저 "app이 HTTPS를 HTTP로 오해했는가"를 본다. `SameSite=None; Secure`와 `X-Forwarded-Proto`는 비슷해 보이지만 완전히 다른 질문이다.
