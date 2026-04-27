# SameSite=None Cross-Site Login Primer

> 한 줄 요약: external IdP callback, partner portal iframe, embedded login처럼 브라우저가 **cross-site 맥락**에서 cookie를 다시 보내야 하는 흐름은 `SameSite=None; Secure` 축으로 봐야 하고, proxy 뒤에서 app이 HTTPS를 HTTP로 오해하는 문제는 `X-Forwarded-Proto` 축으로 따로 봐야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)
- `[entrypoint]` [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
- `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
- `[follow-up]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- `[follow-up]` [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md)
- `[follow-up]` [Embedded Login CSRF Bridge](./embedded-login-csrf-bridge.md)
- `[follow-up]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)
- `[follow-up]` [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md)
- `[follow-up]` [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: samesite none cross-site login primer, samesite none secure login primer, samesite=none external idp cookie, samesite=none iframe login cookie, external idp callback cookie missing, partner portal iframe login loop, embedded login cookie blocked, social login cookie blocked samesite, 처음 배우는데 samesite none, samesite none 뭐예요
retrieval-anchor-keywords: samesite none vs x-forwarded-proto, samesite vs x-forwarded-proto, external idp vs proxy cookie mismatch, iframe login vs proxy mismatch, secure cookie proxy mismatch vs samesite, browser cross-site cookie send rule, partner iframe session cookie beginner, federated login cookie not sent beginner, security readme browser session troubleshooting
retrieval-anchor-keywords: login redirect becomes http after login, secure cookie not sent after http redirect, oauth vs oidc vs cookie confusion, social login cookie behavior confusion, social login mental model return, oidc cookie confusion beginner, iframe login still fails after samesite none secure, third-party cookie privacy controls iframe login, embedded login privacy controls beginner
retrieval-anchor-keywords: primer follow-up catalog return ladder, safe next step before deep dive, browser session beginner ladder return, cross-site login safe next step, proxy vs samesite follow-up, beginner primer bridge ladder, 처음 배우는데 samesite none, samesite none 뭐예요
retrieval-anchor-keywords: samesite vs proxy 15 second check, devtools blocked reason samesite vs proxy, quick branch samesite proxy, secure vs samesite quick split, blocked set-cookie samesite proxy bridge
retrieval-anchor-keywords: external idp iframe sibling subdomain split, callback iframe subdomain next step, same-site handoff not cross-site, beginner return to security readme, cross-site primer return path

## primer -> follow-up -> catalog return ladder

이 문서는 beginner가 바로 deep dive로 뛰지 않게 만드는 bridge다.
읽는 순서는 아래처럼 고정하면 된다.

1. `primer`: [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)에서 `blocked Set-Cookie`인지, 저장은 됐지만 전송이 안 되는지부터 자른다.
2. `follow-up`: 이 문서에서 `cross-site cookie 전송`과 `proxy scheme mismatch`를 분리한다.
3. `follow-up`: 분기 결과에 따라 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md), [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md) 중 하나만 더 읽는다.
4. `catalog return`: 갈래를 다시 잃으면 `return to Browser / Session Troubleshooting Path`라는 같은 wording으로 [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아간다.

이 문서의 job은 `SameSite=None; Secure`가 필요한 장면을 고르는 것이다.
CSRF, CORS, callback hardening은 분기가 끝난 뒤에만 내려간다.

## 먼저 세 장면을 갈라 본다

이 문서는 `external IdP`와 `iframe` 쪽을 맡고, sibling subdomain handoff는 옆 문서로 넘긴다.

| 지금 막힌 장면 | 이 문서에서 바로 다루나 | 다음 한 장 |
|---|---|---|
| `accounts.google.com` 같은 external IdP에서 `auth.example.com/callback`으로 돌아온 뒤 cookie가 안 붙는다 | 그렇다 | 이 문서에서 `SameSite=None; Secure` 후보를 본다 |
| partner portal iframe 안에서만 로그인 유지가 안 된다 | 그렇다 | 이 문서에서 먼저 `SameSite` 축인지 본 뒤, 필요하면 [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md) |
| `auth.example.com/callback`은 성공인데 `app.example.com` 첫 요청이 anonymous다 | 아니다 | [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) |

헷갈리면 먼저 [SameSite Login Callback Primer](./samesite-login-callback-primer.md)로 한 칸 올라가 `same-site`와 `cross-site`를 다시 맞춘 뒤 돌아온다.

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

그리고 질문이 아래처럼 섞여 있다면 이 문서만으로는 부족할 수 있다.

- "OAuth2랑 OIDC도 헷갈리는데 cookie까지 같이 안 잡혀요"
- "`access token`, `id token`, session cookie가 다 로그인 증거처럼 보여요"

그 경우에는 먼저 [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)로 돌아가
"외부 로그인 신원 확인"과 "브라우저 cookie 재전송"을 다른 층으로 분리한 뒤 다시 이 문서로 내려오는 편이 안전하다.

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

## 15초 체크: SameSite vs Proxy

| 지금 보이는 현상 | 더 가까운 원인 | 먼저 볼 것 |
|---|---|---|
| external IdP, partner portal, iframe 경로에서만 깨지고 직접 `app.example.com`으로 열면 된다 | `SameSite=None; Secure`가 필요한 cross-site cookie 전송 문제일 수 있다 | 실패 요청이 여전히 `https://...`인지, cookie가 어떤 `SameSite`로 발급됐는지 |
| 로컬은 되는데 ALB/Nginx/ingress 뒤에서만 깨지고 login 직후 `Location`이 `http://...`로 바뀐다 | proxy `X-Forwarded-Proto` mismatch일 수 있다 | login 응답의 `Location`, 다음 요청 URL, trusted proxy 설정 |
| `auth.example.com`에서는 되는데 `app.example.com`이나 `api.example.com`으로 가면 풀린다 | `SameSite`보다 `Domain`/host-only/`Path` 문제일 수 있다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| social login인데 `OAuth2`, `OIDC`, `access token`, session cookie 역할이 한 문장처럼 섞여 있다 | cookie 문제를 보기 전에 login mental model이 먼저 흔들린 상태일 수 있다 | [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md) |

이 표에서 가장 실용적인 한 줄은 이것이다.

- **redirect가 계속 HTTPS인데 external/iframe 경로에서만 cookie가 안 붙으면 `SameSite` 쪽**
- **redirect가 HTTP로 꺾이면 proxy 쪽**

## 첫 수정 포인트 고르기

같은 "cookie 불량"처럼 보여도 첫 수정 포인트를 섞으면 디버깅이 길어진다.

| 증거 | 먼저 고칠 것 | 지금 하지 말 것 |
|---|---|---|
| login 직후 `Location` 또는 다음 요청 URL이 `http://...` | proxy/app의 `X-Forwarded-Proto` 해석, redirect scheme | `SameSite=None`부터 추가 |
| redirect와 다음 요청이 계속 `https://...`, 실패가 external IdP/iframe 경로에 집중 | 필요한 cookie만 `SameSite=None; Secure` 조정 | proxy 설정부터 의심해 대규모 변경 |
| `auth.example.com`에는 cookie가 있는데 `app.example.com` 요청에는 안 붙음 | `Domain`/host-only/`Path` 점검 | `SameSite=None` 일괄 적용 |

## 막히면 여기로 돌아온다

읽다 막히면 아래 표로 다시 접는다.

| 내가 확인한 증거 | 다음 한 걸음 | 돌아오는 자리 |
|---|---|---|
| login 응답 `Location`이나 다음 요청 URL이 `http://...`다 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| redirect는 계속 HTTPS인데 external IdP/iframe/partner portal에서만 깨진다 | 이 문서에서 `SameSite=None; Secure`가 필요한 cookie만 다시 본다 | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |
| `SameSite=None; Secure`까지 이미 맞췄는데 iframe 안에서만 계속 실패하고 새 탭에서는 된다 | [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| 증상 문장에 "`auth.example.com/callback`은 성공인데 `app.example.com` 첫 요청이 anonymous" 또는 "`auth.example.com` cookie가 `app.example.com`에 안 간다"가 들어 있다 | [Subdomain Callback Handoff Chooser](./subdomain-callback-handoff-chooser.md) | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |
| `fetch credentials`, CORS, cookie scope까지 같이 섞인다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| social login인데 "`구글 로그인` 흐름 설명"과 "브라우저가 cookie를 왜 안 보내는가"가 같이 헷갈린다 | [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md)에서 역할을 먼저 분리한 뒤 다시 내려온다 | [Security README: 기본 primer](./README.md#기본-primer) |

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

### 그런데 `SameSite=None; Secure`까지 했는데 iframe만 계속 안 되면?

이제는 같은 질문을 반복하면 안 된다.

- redirect가 계속 HTTPS다
- `Set-Cookie`에도 `SameSite=None; Secure`가 있다
- 그런데 partner iframe, embedded login, in-app browser 안에서만 세션이 안 붙는다
- 새 탭이나 top-level redirect login은 된다

이 패턴이면 modern browser의 third-party cookie/privacy control을 별도 축으로 봐야 한다.
즉 `SameSite` 설정이 부족해서가 아니라, 브라우저가 **third-party cookie 자체를 더 강하게 제한**하는 장면일 수 있다.

이 경우 beginner follow-up은 [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md)다.
그 문서에서는 "`None`을 더 주는 문제"가 아니라 "`embedded login 자체를 유지할지, top-level login으로 우회할지`"를 먼저 고른다.

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
| cross-site cookie를 열었더니 callback 뒤 첫 POST의 CSRF 경계가 헷갈린다 | [Embedded Login CSRF Bridge](./embedded-login-csrf-bridge.md) |
| external IdP callback hardening과 session regeneration까지 같이 보고 싶다 | [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md), [Session Fixation in Federated Login](./session-fixation-in-federated-login.md) |

---

### 한 줄 정리

external IdP/iframe login failure는 먼저 "브라우저가 cross-site라서 cookie를 안 보내는가"를 보고, proxy/LB 뒤 login failure는 먼저 "app이 HTTPS를 HTTP로 오해했는가"를 본다. `SameSite=None; Secure`와 `X-Forwarded-Proto`는 비슷해 보이지만 완전히 다른 질문이다.

## follow-up 한 장 + return to Browser / Session Troubleshooting Path

| 지금 이 문서를 읽고 남은 질문 | 다음 한 장만 읽기 | 그다음 복귀 |
|---|---|---|
| `Location`/다음 요청이 `http://...`다 | `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | `[catalog]` [Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |
| HTTPS인데 특정 host/path에서만 누락된다 | `[follow-up]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | `[catalog]` [Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |
| `SameSite=None; Secure`인데 iframe 안에서만 실패한다 | `[follow-up]` [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md) | `[catalog]` [Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| "`OAuth2`/`OIDC`/`id token`/session cookie가 섞인다"가 남아 있다 | `[follow-up]` [OAuth2 vs OIDC Social Login Primer](./oauth2-oidc-social-login-primer.md) | `[catalog]` [기본 primer](./README.md#기본-primer) |
| cross-site cookie 뒤 callback POST/CSRF 경계가 헷갈린다 | `[follow-up]` [Embedded Login CSRF Bridge](./embedded-login-csrf-bridge.md) | `[catalog]` [Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| login-loop 기준점부터 다시 잡고 싶다 | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) | `[catalog]` [Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |

한 번에 한 장만 읽고 README route로 복귀한다.

## 한 줄 정리

external IdP/iframe login failure는 먼저 "브라우저가 cross-site라서 cookie를 안 보내는가"를 보고, proxy/LB 뒤 login failure는 먼저 "app이 HTTPS를 HTTP로 오해했는가"를 본다. `SameSite=None; Secure`와 `X-Forwarded-Proto`는 비슷해 보여도 다른 질문이다.
