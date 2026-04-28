# Absolute Redirect URL Behind Load Balancer Guide

> 한 줄 요약: load balancer 뒤의 앱이 바깥 주소가 아니라 내부 주소로 absolute URL을 만들면, 로그인 후 redirect나 OAuth callback URL이 `app.example.com`에서 `app-internal:8080` 같은 wrong origin으로 바뀐다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 관련 문서:
> - [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)
> - [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
> - [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./wrong-scheme-vs-wrong-origin-redirect-shortcut.md)
> - [Password Reset, Magic Link, Public Origin Guide](./password-reset-magic-link-public-origin-guide.md)
> - [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
> - [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)
> - [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)

retrieval-anchor-keywords: absolute redirect url behind load balancer, absolute redirect behind proxy, x-forwarded-host redirect, x-forwarded-host callback, host preservation load balancer, preserve host header, wrong origin callback, post-login redirect wrong origin, post-login redirect wrong host, oauth callback wrong origin, oauth redirect_uri mismatch behind proxy, redirect_uri built from internal host, 왜 내부 host로 가요, 처음 배우는데 wrong origin, return to browser session troubleshooting path

## 이 문서 다음에 보면 좋은 문서

- Spring deep dive 전에 login-loop 기준점을 다시 맞추려면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) 순서로 먼저 복귀한다.
- `Location` host는 맞는데 `http://`로만 내려오거나 `Secure` cookie가 안 붙으면 [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)로 넘어간다.
- 브라우저 redirect는 정상인데 이메일 reset link나 magic link host만 틀리면 [Password Reset, Magic Link, Public Origin Guide](./password-reset-magic-link-public-origin-guide.md)에서 configured public origin 기준을 먼저 본다.
- `X-Forwarded-*`를 어디까지 믿어야 하는지 불안하면 [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md)로 trusted proxy 경계를 먼저 고정한다.
- `next=https://evil.example`처럼 사용자 입력 redirect가 그대로 반사되면 [Open Redirect Hardening](./open-redirect-hardening.md)을 먼저 본다.
- browser login loop인데 `Location` host/scheme은 정상이라면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)나 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 분기한다.
- 다시 전체 경로를 고르고 싶으면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가면 된다.

## 이 문서의 한 걸음 복귀 경로

이 문서는 `wrong-origin` detour를 끝내는 자리이지, category map을 대체하는 문서는 아니다.

| 여기까지 읽고 난 뒤 상태 | 바로 돌아갈 자리 |
|---|---|
| host/origin 문제라는 건 알겠는데 다음 symptom branch를 다시 골라야 한다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| primer부터 다시 읽어야 할 만큼 browser/session 문장이 다시 섞였다 | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) |

`Wrong-Scheme vs Wrong-Origin Redirect Shortcut`에서 `https://...`인데 host만 틀린 갈래로 들어왔다면, beginner one-step return path도 고정이다. wrong-origin 원인을 한 장만 확인한 뒤에는 absolute URL 세부 설정을 더 파기 전에 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 바로 돌아간다.

## 이 문서를 먼저 읽는 이유

초보자가 자주 보는 장면은 이렇다.

- 로컬에서는 로그인 후 `/dashboard`로 잘 간다
- 운영에서는 login은 성공한 것 같은데 `Location`이 이상한 host로 내려온다
- OAuth/OIDC provider가 `redirect_uri mismatch`를 낸다
- callback URL이 `https://app.example.com/...`이 아니라 `http://app-internal:8080/...`처럼 만들어진다
- staging에서 로그인했는데 production 도메인으로 튀거나, 반대로 production에서 staging 도메인으로 튄다

이 문제는 "redirect 대상 검증"만의 문제가 아니다.
앱이 **바깥 사용자가 접속한 origin**을 모르고, **내부 proxy hop 주소**를 자기 주소라고 착각해서 생기는 경우가 많다.

---

## 초보자 5분 점검 순서

복잡한 설정을 보기 전에 아래 순서로 좁히면 대부분 빠르게 분기된다.

1. login 응답 `Location`이 public origin인지 먼저 본다.
2. OAuth라면 authorization request의 `redirect_uri`가 등록값과 exact match인지 본다.
3. app이 본 `Host`/`X-Forwarded-Host`/`X-Forwarded-Proto`를 같은 로그 라인에서 묶어 본다.
4. absolute URL 생성 소스가 request 값인지, 설정된 public base URL인지 확인한다.
5. relative redirect(`/dashboard`)는 되는데 absolute callback만 깨지면 host 복원/고정 URL 축부터 본다.

| 1차 관찰 | 먼저 의심할 축 | 다음 문서 |
|---|---|---|
| `Location` host만 internal/staging으로 틀림 | host 복원 실패 (`Host`/`X-Forwarded-Host`) | [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md) |
| `Location`이 `http://`로 내려옴 | scheme 복원 실패 (`X-Forwarded-Proto`) | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| 상대 redirect는 정상, OAuth/email link만 틀림 | absolute URL source of truth 오류 | 이 문서의 `absolute URL은 무엇을 기준으로 만들어야 하나` 섹션 |

## 20초 혼동 분리표: 비슷해 보이지만 다른 문제

| 겉증상 | 실제 중심 원인 | 먼저 볼 문서 |
|---|---|---|
| 로그인 후 다른 host로 튐 | public origin 복원 실패 또는 absolute URL builder 기준 오류 | 이 문서 |
| 같은 host인데 `http://`로 내려오고 `Secure` cookie가 안 붙음 | scheme 복원 실패 (`X-Forwarded-Proto`) | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `next=https://evil.example`처럼 사용자 입력 URL로 튐 | user-supplied redirect validation 부족 | [Open Redirect Hardening](./open-redirect-hardening.md) |

## detour에서 복귀하는 browser/session primer ladder

absolute redirect detour에서 원인을 확인했다면, Spring/프록시 설정 상세로 내려가기 전에 아래 사다리로 다시 공통 symptom 기준을 맞춘다.

| 단계 | 왜 이 단계로 복귀하나 | 링크 |
|---|---|---|
| 1. `primer` | login redirect와 `SavedRequest`가 남기는 상태를 다시 고정 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| 2. `primer bridge` | `401`/`302`/login HTML fallback을 한 표에서 같은 기준으로 분기 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| 3. `catalog` | 다음 symptom 갈래를 category navigator에서 안전하게 재선택 | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## 가장 단순한 mental model

앱 앞에 load balancer나 reverse proxy가 있으면, 같은 요청을 세 주체가 다르게 본다.

| 주체 | 보는 주소 | 이 값으로 무엇을 결정하나 |
|---|---|---|
| 브라우저 | `https://app.example.com` | 사용자가 실제로 머무는 origin |
| load balancer / proxy | 바깥 HTTPS 요청과 내부 app 주소 | TLS 종료, host 전달, forwarded header 작성 |
| 앱 | `http://app-internal:8080`처럼 보일 수 있음 | `Location`, callback URL, email link 같은 absolute URL 생성 |

핵심은 이것이다.

- **브라우저 origin**은 사용자가 보는 공개 주소다.
- **앱 내부 주소**는 proxy가 앱에 전달할 때 쓰는 사설 주소일 수 있다.
- 앱이 absolute URL을 만들 때 내부 주소를 쓰면, 사용자는 wrong origin으로 튄다.

여기서 origin은 `scheme + host + port`다.

| URL | origin |
|---|---|
| `https://app.example.com/dashboard` | `https://app.example.com` |
| `http://app.example.com/dashboard` | `http://app.example.com` |
| `https://app-internal:8080/dashboard` | `https://app-internal:8080` |
| `https://staging.example.com/dashboard` | `https://staging.example.com` |

path가 같아도 scheme, host, port 중 하나가 바뀌면 다른 origin이다.

---

## 한 요청에서 주소가 네 번 보일 수 있다

초보자가 가장 헷갈리는 지점은 "도대체 어느 주소가 진짜냐"다.
proxy 뒤에서는 한 요청에 아래 값들이 동시에 등장할 수 있다.

| 이름 | 예시 | 누가 들고 있나 | 언제 써야 하나 |
|---|---|---|---|
| public origin | `https://app.example.com` | 브라우저, 사용자, OAuth provider 등록값 | 사용자가 실제로 돌아와야 하는 주소 |
| raw app host | `app-internal:8080` | 앱이 proxy 뒤에서 직접 본 내부 요청 | 내부 라우팅 확인용일 뿐, public URL 생성 기준으로 쓰면 위험 |
| forwarded host/proto | `app.example.com`, `https` | trusted proxy가 앱에 전달한 값 | 현재 요청의 public origin을 복원할 때 |
| configured public base URL | `https://app.example.com` | 앱 설정, 환경변수, tenant/domain allowlist | email link, reset link, 고정 callback처럼 보안 민감한 absolute URL 생성 시 |

핵심은 "값이 많다"가 아니라 "용도가 다르다"다.

- 내부 hop을 설명하는 값과, 사용자가 실제로 보는 값은 다를 수 있다.
- absolute URL builder가 raw app host를 집으면 wrong origin이 된다.
- absolute URL builder가 trusted forwarded 값이나 configured public base URL을 집어야 public origin으로 돌아간다.

---

## 왜 absolute URL에서 더 잘 터지나

redirect에는 크게 두 모양이 있다.

| 응답 | 브라우저가 해석하는 방식 | 장점 / 위험 |
|---|---|---|
| `Location: /dashboard` | 현재 origin을 유지하고 path만 이동 | 내부 화면 이동에는 단순하고 안전한 편 |
| `Location: https://app.example.com/dashboard` | 응답에 적힌 origin으로 이동 | host/scheme이 틀리면 바로 wrong origin으로 감 |

일반 post-login redirect는 상대 경로만으로 충분한 경우가 많다.
하지만 아래 장면에서는 absolute URL이 자주 필요하다.

- OAuth/OIDC `redirect_uri`
- 외부 provider에 등록할 callback URL
- email magic link / password reset link
- webhook callback URL
- 다른 service나 browser에 전달하는 canonical app URL

이때 앱이 request의 `Host`만 보고 URL을 만들면, proxy 설정에 따라 공개 host가 아니라 내부 host가 들어갈 수 있다.

---

## 정상 흐름

정상 흐름에서는 proxy가 "바깥에서 실제로 어떤 주소로 들어왔는지"를 앱에 전달한다.

```text
Browser
  GET https://app.example.com/login
        |
        v
Trusted load balancer
  GET http://app-internal:8080/login
  Host: app-internal:8080
  X-Forwarded-Proto: https
  X-Forwarded-Host: app.example.com
        |
        v
App
  "바깥 origin은 https://app.example.com 이구나"
  Location: https://app.example.com/dashboard
```

다른 방식도 가능하다.
proxy가 내부 요청의 `Host` 자체를 `app.example.com`으로 보존할 수도 있다.

```http
Host: app.example.com
X-Forwarded-Proto: https
```

중요한 것은 방식이 하나로 맞아야 한다는 점이다.

- proxy가 original host를 보존하거나
- proxy가 `X-Forwarded-Host`를 정확히 써 주고
- 앱이 그 값을 trusted proxy에서 온 경우에만 해석해야 한다

---

## 어디서 깨지나

### 1. host 보존이 안 되어 내부 주소로 redirect됨

```text
Browser
  POST https://app.example.com/login
        |
        v
Proxy
  POST http://app-internal:8080/login
  Host: app-internal:8080
  X-Forwarded-Proto: https
  X-Forwarded-Host: (없음)
        |
        v
App
  Location: https://app-internal:8080/dashboard
```

브라우저는 앱이 준 `Location`을 그대로 따른다.
그래서 사용자는 내부 host, staging host, 잘못된 tenant host로 이동할 수 있다.

### 2. scheme은 맞는데 host만 틀림

`X-Forwarded-Proto: https`만 맞으면 끝이라고 생각하기 쉽다.
하지만 absolute URL에는 host도 들어간다.

| 앱이 알고 있는 값 | 만들어지는 URL | 결과 |
|---|---|---|
| proto=`https`, host=`app.example.com` | `https://app.example.com/callback` | 정상 |
| proto=`https`, host=`app-internal:8080` | `https://app-internal:8080/callback` | wrong host |
| proto=`http`, host=`app.example.com` | `http://app.example.com/callback` | wrong scheme, `Secure` cookie도 빠질 수 있음 |

`Secure` cookie 문제는 주로 scheme mismatch에서 두드러진다.
이 문서는 그중에서도 **host/origin이 잘못 잡혀 absolute URL이 뒤집히는 문제**를 본다.

### 3. OAuth callback URL이 잘못 만들어짐

OAuth login 시작 시 앱이 provider에 아래 값을 보낸다고 해 보자.

```text
redirect_uri=http://app-internal:8080/login/oauth2/code/google
```

provider 입장에서는 이 값이 사전 등록된 값과 다르다.
그래서 보통 둘 중 하나가 된다.

- `redirect_uri mismatch`로 login 시작이 실패한다
- 느슨하게 허용된 환경에서는 callback이 잘못된 host로 돌아간다

정상 값은 보통 이런 식이어야 한다.

```text
redirect_uri=https://app.example.com/login/oauth2/code/google
```

OAuth에서 `redirect_uri`는 보안 경계다.
"대충 같은 서비스"가 아니라, 등록된 scheme/host/path와 정확히 맞아야 한다.

### 4. 공격자가 host를 주장할 수도 있음

## 어디서 깨지나 (계속 2)

`X-Forwarded-Host`는 유용하지만, 아무 요청에서나 믿으면 위험하다.
클라이언트도 같은 이름의 header를 직접 보낼 수 있기 때문이다.

```http
GET /login HTTP/1.1
Host: app.example.com
X-Forwarded-Host: evil.example
X-Forwarded-Proto: https
```

앱이 이 값을 무조건 믿고 absolute URL을 만들면:

- password reset link가 공격자 host로 만들어질 수 있다
- post-login redirect가 이상한 host로 갈 수 있다
- host 기반 tenant 선택이 흔들릴 수 있다

그래서 `X-Forwarded-Host`는 [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md)처럼 known proxy가 strip/overwrite한 값일 때만 믿어야 한다.

---

## `Host` 보존과 `X-Forwarded-Host` 비교

둘 중 하나가 항상 정답은 아니다.
운영 환경과 framework가 같은 모델을 공유하는지가 중요하다.

| 방식 | 의미 | 흔한 장점 | 주의점 |
|---|---|---|---|
| `Host` 보존 | proxy가 앱으로 넘길 때도 공개 host를 유지 | 앱 코드가 단순해질 수 있음 | internal routing이 Host에 의존하면 proxy 설정이 더 중요해짐 |
| `X-Forwarded-Host` | proxy가 original host를 별도 header로 전달 | 내부 host와 외부 host를 분리 가능 | trusted proxy에서 온 값만 해석해야 함 |
| `X-Forwarded-Proto` | original scheme 전달 | `https` redirect와 secure request 판단에 필요 | host 문제는 따로 해결해야 함 |
| `X-Forwarded-Port` | original port 전달 | `:8443` 같은 non-standard port에 필요 | port까지 origin 일부라는 점을 잊기 쉬움 |
| `Forwarded` | `proto`, `host`, `for`를 표준 문법으로 표현 | 표준화된 형식 | 표준 header여도 출처 검증은 여전히 필요 |

초보자용 규칙은 이렇다.

1. 공개 origin을 먼저 정한다.
2. proxy가 그 origin의 scheme/host/port를 앱에 전달한다.
3. 앱은 known proxy에서 온 forwarded 정보만 사용한다.
4. security-sensitive absolute URL은 가능하면 설정된 public base URL이나 등록된 allowlist를 기준으로 만든다.

---

## absolute URL은 무엇을 기준으로 만들어야 하나

모든 absolute URL을 request `Host` 하나로 만들려고 하면 자주 깨진다.
용도에 따라 source of truth를 나누면 훨씬 덜 흔들린다.

| 장면 | 우선 기준 | 왜 이 기준이 낫나 |
|---|---|---|
| login 후 같은 사이트 내부 화면으로 이동 | relative redirect (`/dashboard`) | 현재 browser origin을 그대로 유지하므로 host 재구성이 필요 없다 |
| 지금 들어온 요청의 tenant/domain 기준 callback URL 생성 | trusted proxy가 준 `Host` 보존 또는 `X-Forwarded-Host` + `X-Forwarded-Proto` | 현재 요청의 public origin을 복원해야 하기 때문 |
| OAuth provider에 등록된 고정 callback | 설정된 public callback URL 또는 environment별 allowlist | provider exact match가 필요하고, raw request host에 흔들리면 안 된다 |
| password reset / magic link / email link | 설정된 public base URL 또는 검증된 tenant 도메인 설정 | out-of-band 링크는 현재 request host보다 설정값이 더 안전하다 |

짧게 기억하면 이렇다.

- **같은 브라우저 안에서 바로 이동**이면 relative redirect를 먼저 생각한다.
- **현재 요청의 공개 도메인을 복원**해야 하면 trusted forwarded 정보를 본다.
- **메일, 외부 provider, 고정 callback**처럼 보안 민감한 absolute URL이면 configured public base URL이나 allowlist를 먼저 본다.

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 더 가까운 원인 | 먼저 확인할 것 |
|---|---|---|
| login 후 `Location`이 `app-internal`, `localhost`, staging host로 내려옴 | 앱의 absolute URL builder가 내부 host를 봄 | 응답 `Location`, app raw `Host`, `X-Forwarded-Host` |
| OAuth provider가 `redirect_uri mismatch`를 냄 | 앱이 provider에 보낸 callback URL이 공개 등록값과 다름 | 실제 authorization request의 `redirect_uri` |
| `http://app.example.com`으로만 바뀜 | scheme mismatch가 더 큼 | `X-Forwarded-Proto`, [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| host가 요청마다 이상하게 바뀜 | `Host` / `X-Forwarded-Host`를 외부 입력처럼 받고 있을 수 있음 | edge가 incoming forwarded header를 strip/overwrite하는지 |
| `Location: /dashboard`는 괜찮은데 absolute callback만 깨짐 | 상대 redirect는 현재 origin을 보존하지만 absolute URL builder가 틀림 | callback/base URL 생성 로직 |

---

## 60초 분기: 이 문서가 맞는 문제인지 먼저 가르기

| 지금 보이는 장면 | 더 가능성 높은 원인 | 먼저 볼 문서 |
|---|---|---|
| login 응답 `Location`의 host 자체가 틀리다 | public origin 복원/absolute URL builder 문제 | 이 문서를 계속 본다 |
| `Location` host는 맞는데 user 입력 `next`로 외부 도메인 이동 | redirect destination 검증 누락 | [Open Redirect Hardening](./open-redirect-hardening.md) |
| `Location` host/scheme은 정상인데 로그인 직후 다시 anonymous | cookie scope/session 복원 문제 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| external IdP callback 구간에서만 깨진다 | cross-site cookie 또는 proxy scheme 인식 문제 | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md), [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |

## 초보자 실수 패턴 3개와 즉시 수정 포인트

| 자주 하는 실수 | 왜 깨지나 | 바로 고칠 포인트 |
|---|---|---|
| absolute URL을 매번 request `Host`에서 조립 | proxy 뒤 내부 host가 들어와 wrong origin이 된다 | 내부 이동은 relative redirect를 우선하고, 외부 callback/link는 configured public URL 기준으로 만든다 |
| `X-Forwarded-Proto`만 보고 host는 안 본다 | `https`는 맞아도 host가 내부값이면 여전히 실패한다 | `X-Forwarded-Proto`와 `X-Forwarded-Host`를 한 세트로 검증한다 |
| forwarded header를 모든 요청에서 신뢰 | client가 헤더를 주장하면 spoofing으로 이어질 수 있다 | edge에서 strip/overwrite하고 앱은 trusted proxy에서 온 값만 해석한다 |

---

## 30초 concrete example: 왜 로컬은 되는데 운영에서 깨질까

같은 코드라도 "앱이 어느 host를 자기 주소로 읽었는지"에 따라 결과가 달라진다.

| 환경 | 앱이 읽은 값 | 앱이 만든 `Location` | 결과 |
|---|---|---|---|
| 로컬 단일 서버 | `http://localhost:8080` | `http://localhost:8080/dashboard` | 정상처럼 보임 |
| 운영 + LB (host 보존/forwarded 해석 누락) | `http://app-internal:8080` | `http://app-internal:8080/dashboard` | 브라우저가 wrong origin으로 이동 |
| 운영 + LB (public origin 복원 정상) | `https://app.example.com` | `https://app.example.com/dashboard` | 정상 |

그래서 "로컬에서는 되는데 운영만 깨진다"는 증상 자체가 proxy 경계에서 public origin 복원 실패 신호인 경우가 많다.

---

## 무엇을 확인하면 되나

### 1. 브라우저 Network 탭

login 직후 응답에서 본다.

- `Location`이 공개 origin인지
- 다음 요청 URL이 공개 origin인지
- OAuth login 시작 요청의 `redirect_uri` query parameter가 공개 callback인지

예를 들어 운영 public origin이 `https://app.example.com`이면 아래는 이상 신호다.

```text
Location: http://app-internal:8080/dashboard
Location: https://staging.example.com/dashboard
redirect_uri=http://localhost:8080/login/oauth2/code/google
```

### 2. proxy / load balancer

proxy가 아래 중 어떤 모델을 쓰는지 확인한다.

- original `Host`를 그대로 보존하는가
- 아니면 내부 `Host`로 바꾸고 `X-Forwarded-Host`를 따로 쓰는가
- 외부 client가 보낸 `X-Forwarded-*`를 지우고 다시 쓰는가
- `X-Forwarded-Proto: https`와 host/port가 같이 맞는가

### 3. 앱 / framework

앱은 아래를 알아야 한다.

- 어떤 proxy/range를 trusted proxy로 볼 것인가
- forwarded header를 request scheme/host에 반영하는가
- absolute URL builder가 raw internal request를 쓰는가, public base URL을 쓰는가
- OAuth callback, email link, magic link는 등록된 public origin allowlist에서만 만들어지는가

프레임워크 설정 이름은 다르지만 개념은 같다.

- "proxy가 알려 준 original host/proto를 request에 반영한다"
- "하지만 known proxy에서 온 경우에만 반영한다"

---

## 안전한 설계 습관

| 습관 | 이유 |
|---|---|
| 내부 화면 이동은 가능하면 relative redirect를 쓴다 | 현재 browser origin을 유지하므로 host 재구성이 필요 없다 |
| OAuth `redirect_uri`는 등록된 public callback만 쓴다 | provider exact match와 보안 경계를 유지한다 |
| email / magic link / reset link는 설정된 public base URL에서 만든다 | request `Host` injection 영향을 줄인다 |
| edge proxy에서 incoming `X-Forwarded-*`를 strip/overwrite한다 | client가 주장한 host/proto를 앱이 믿지 않게 한다 |
| 앱은 trusted proxy에서 온 forwarded header만 해석한다 | direct exposure나 spoofing을 줄인다 |
| 로그에 raw `Host`, forwarded host/proto, 최종 `Location`을 함께 남긴다 | wrong origin 문제를 빠르게 좁힐 수 있다 |

---

## 초보자가 자주 헷갈리는 지점

### 1. "`X-Forwarded-Proto`를 맞췄으니 redirect 문제는 끝 아닌가요?"

아니다.
absolute URL은 scheme뿐 아니라 host와 port도 필요하다.
`https`는 맞아도 host가 `app-internal`이면 여전히 wrong origin이다.

### 2. "`Host`와 `Origin`은 같은 말인가요?"

아니다.

- `Host`는 HTTP request가 향하는 host header다.
- browser origin은 `scheme + host + port` 조합이다.
- `Origin` header는 CORS/CSRF 같은 문맥에서 브라우저가 보내는 별도 header다.

이 문서에서 말하는 "wrong origin"은 주로 앱이 만든 URL의 scheme/host/port가 사용자가 기대한 공개 origin과 달라지는 문제다.

### 3. "CORS 설정을 고치면 되나요?"

대개 아니다.
브라우저 navigation redirect와 CORS는 다른 문제다.
`Location`이 wrong host로 내려오는 문제는 서버가 URL을 어떻게 만들었는지부터 봐야 한다.

### 4. "Open redirect와 같은 문제인가요?"

겹치지만 완전히 같지는 않다.

- 이 문서: 앱이 자기 public origin을 잘못 알아서 URL을 잘못 만든다.
- [Open Redirect Hardening](./open-redirect-hardening.md): 사용자가 준 redirect destination을 서버가 그대로 반사해서 외부로 보내는 문제다.

둘 다 redirect 보안에 영향을 주므로 함께 봐야 한다.

### 5. "`trust proxy` 옵션만 켜면 끝인가요?"

아니다.
앱 설정과 proxy 설정이 한 쌍으로 맞아야 한다.

- proxy가 incoming forwarded header를 지우고 다시 쓰는가
- 앱이 어떤 proxy를 신뢰할지 제한하는가
- direct app port가 외부에 노출되어 있지 않은가
- public base URL이 환경별로 정확한가

### 6. "`PUBLIC_BASE_URL` 하나면 멀티테넌트도 충분한가요?"

대개 아니다.
tenant별 도메인을 쓰는 서비스라면 "요청 tenant와 허용 도메인 매핑"을 검증해 URL을 생성해야 한다.
고정 base URL 하나를 재사용하면 tenant 간 wrong origin 이동이나 callback mismatch가 생길 수 있다.

---

## 이 문서와 다른 원인의 경계

| 이런 장면이면 | 먼저 볼 문서 |
|---|---|
| wrong host보다 `http://`로 바뀌며 `Secure` cookie가 빠짐 | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `X-Forwarded-*` 자체를 믿어도 되는지, client IP/rate limit까지 같이 흔들림 | [Forwarded Header Trust Boundary Primer](./forwarded-header-trust-boundary-primer.md) |
| 사용자가 준 `next=https://evil.example` 같은 값이 그대로 반사됨 | [Open Redirect Hardening](./open-redirect-hardening.md) |
| OAuth flow, `state`, PKCE, code exchange가 전체적으로 헷갈림 | [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) |
| `Application > Cookies`에는 값이 있는데 request `Cookie` header가 비어 있음 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| page redirect와 API raw `401` 계약이 섞임 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |

---

## 면접/시니어 질문 미리보기

> Q: load balancer 뒤에서 OAuth `redirect_uri`가 내부 host로 만들어지는 이유는 무엇인가요?
> 핵심: 앱이 바깥 public origin이 아니라 proxy가 전달한 내부 `Host`/scheme을 기준으로 absolute URL을 만들기 때문이다.

> Q: `X-Forwarded-Host`를 언제 믿어도 되나요?
> 핵심: 요청이 known proxy에서 왔고, 그 proxy가 외부 입력을 strip/overwrite한 뒤 쓴 값일 때만 믿는다.

> Q: post-login redirect는 왜 relative path를 쓰는 편이 안전한가요?
> 핵심: `/dashboard` 같은 relative redirect는 현재 browser origin을 유지하므로 앱이 host를 재구성하다 wrong origin을 만들 가능성이 줄어든다.

## 한 줄 정리

load balancer 뒤 absolute redirect 문제의 핵심은 "앱이 자기 public origin을 잘못 배웠다"는 것이다. `Location`, OAuth `redirect_uri`, email link가 wrong host로 바뀌면 `X-Forwarded-Host`, host preservation, public base URL, trusted proxy 설정을 한 묶음으로 확인한다.
