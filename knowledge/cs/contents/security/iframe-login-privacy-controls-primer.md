# Embedded Login Privacy Primer

> 한 줄 요약: iframe login에서 `SameSite=None; Secure`까지 맞췄는데도 세션이 안 붙으면, 이제 질문은 "cookie 속성이 맞나?"가 아니라 "브라우저가 third-party cookie 자체를 막는 privacy 모드인가?"로 옮겨간다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - `[entrypoint]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)
> - `[primer]` [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
> - `[primer]` [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md)
> - `[follow-up]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md)
> - `[follow-up]` [Embedded Login CSRF Bridge](./embedded-login-csrf-bridge.md)
> - `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - `[catalog]` [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: embedded login privacy primer, iframe login privacy primer, iframe login still fails after SameSite None Secure, third-party cookie privacy controls beginner, embedded login third-party cookie blocked, iframe session blocked by browser privacy, SameSite None Secure but iframe login fails, partner portal iframe login privacy controls, third-party cookie phaseout beginner, browser privacy iframe cookie failure, storage access iframe login beginner, third-party cookie blocked even with SameSite None, safari iframe login cookie blocked, firefox total cookie protection iframe login, chrome block third-party cookies iframe login, embedded auth privacy control mental model, iframe login works in top-level tab only, security readme browser session troubleshooting, privacy controls vs samesite beginner
retrieval-anchor-keywords: top-level login fallback iframe, popup redirect instead of iframe login, embedded auth blocked by browser policy, third-party cookie disabled symptom, privacy sandbox cookie blocking beginner, partitioned cookie mention beginner, chips embedded login follow-up, storage access api follow-up, iframe auth modern browser policy

## 이 문서가 필요한 장면

이 문서는 아래 상황의 follow-up이다.

- iframe login 문제라서 `SameSite=None; Secure`까지 이미 맞췄다
- redirect도 계속 `https://...`다
- 그런데 partner portal iframe, embedded login, in-app webview 같은 장면에서만 계속 실패한다
- 같은 앱을 새 탭이나 top-level page로 열면 로그인 유지가 된다

이제는 "`SameSite`를 더 만지면 되나?"보다,
**브라우저가 third-party cookie 자체를 제한하는가**를 먼저 봐야 한다.

---

## 가장 중요한 mental model

| 질문 | 누가 결정하나 | 실패하면 보이는 장면 |
|---|---|---|
| 이 cookie가 cross-site로 보내져도 되나? | cookie 속성 (`SameSite=None; Secure`) | external IdP/iframe에서 cookie가 기본 규칙 때문에 빠진다 |
| 브라우저가 third-party cookie 자체를 허용하나? | 브라우저 privacy 정책, 사용자 설정, private mode | 속성은 맞아도 iframe 안에서만 계속 빠진다 |

핵심은 이것이다.

- `SameSite=None; Secure`는 필요 조건일 수 있다
- 하지만 modern browser에서는 이것만으로 충분 조건이 아닐 수 있다

즉 "`None`까지 넣었는데 왜 또 안 되죠?"는 이상한 현상이 아니라,
iframe login에서는 꽤 정상적인 다음 질문이다.

---

## 먼저 10초 판별표

| 지금 보이는 현상 | 더 가까운 원인 | 먼저 할 일 |
|---|---|---|
| top-level 새 탭에서는 되는데 partner iframe 안에서만 안 된다 | third-party cookie/privacy control | 이 문서에서 privacy-control 장면부터 본다 |
| iframe이든 아니든 redirect가 `http://...`로 꺾인다 | proxy/scheme mismatch | [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) |
| `auth.example.com`에서는 되는데 `app.example.com`으로만 안 간다 | `Domain`/`Path`/host-only 범위 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| external IdP callback에서 바로 `state mismatch`가 난다 | callback cookie의 `SameSite` 또는 callback flow | [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) |

beginner 기준 한 줄 요약은 아래다.

- 탭에서는 되는데 iframe에서만 안 되면 privacy-control 쪽
- HTTP redirect가 보이면 proxy 쪽
- subdomain 간 handoff만 깨지면 cookie scope 쪽

---

## 왜 `SameSite=None; Secure`만으로 끝나지 않나

예전 질문은 주로 이것이었다.

- "브라우저가 cross-site cookie를 보낼 수 있나?"

지금은 질문이 하나 더 붙는다.

- "브라우저가 third-party cookie 자체를 아예 제한하지는 않나?"

iframe 안의 `app.example.com`은 `partner.com` 입장에서는 third-party처럼 보일 수 있다.
그러면 cookie 속성이 맞아도 브라우저가 privacy 이유로 막을 수 있다.

이때 자주 보이는 장면은 이렇다.

- 개발자 laptop의 한 브라우저에서는 된다
- Safari, Firefox, Chrome private/incognito, "third-party cookies 차단"이 켜진 환경에서만 깨진다
- embedded iframe에서는 안 되는데 popup이나 top-level redirect login은 된다

이 장면은 서버가 "`SameSite=None; Secure`를 안 붙였다"와는 다른 축이다.

---

## 초보자용 비교: 속성 문제 vs privacy-control 문제

| 구분 | 속성 문제 (`SameSite`, `Secure`) | privacy-control 문제 |
|---|---|---|
| top-level 탭에서 재현되나 | 그럴 수 있다 | 보통 iframe보다 덜하다 |
| iframe에서만 유독 심한가 | 그럴 수 있다 | 아주 흔하다 |
| 브라우저/모드별 차이가 큰가 | 상대적으로 작다 | 크다 |
| `SameSite=None; Secure` 추가 후 바로 해결되나 | 자주 해결된다 | 계속 실패할 수 있다 |
| 첫 대응 | cookie 속성 수정 | embedded login 자체를 다시 설계할지 결정 |

여기서 실무적으로 중요한 결론은 하나다.

- privacy-control 문제는 cookie 플래그 하나 더 바꿔서 끝나는 경우가 드물다

---

## 가장 흔한 관찰 패턴

### 1. 새 탭에서는 되고 iframe에서는 안 된다

이 패턴이면 브라우저가 "top-level site 안의 세션"과
"다른 site 안에 embed된 third-party 세션"을 다르게 다루는지 먼저 의심한다.

### 2. 특정 브라우저나 private mode에서만 안 된다

예를 들면 이런 식이다.

- Safari에서만 실패
- Firefox strict privacy 설정에서만 실패
- Chrome incognito 또는 third-party cookie 차단 설정에서만 실패

이 경우는 앱 서버가 랜덤하게 망가진 것이 아니라,
브라우저 정책 차이를 맞닥뜨린 것일 수 있다.

### 3. redirect는 계속 HTTPS다

이 패턴이면 proxy 문제보다 privacy-control 쪽이 더 가깝다.

즉,

- `http://...` redirect가 없다
- `Domain`/`Path`도 얼추 맞아 보인다
- `SameSite=None; Secure`도 이미 붙였다

그런데 iframe만 안 되면, 이제는 third-party cookie 허용 여부를 봐야 한다.

---

## 초보자가 가장 먼저 해야 할 확인

| 확인할 것 | 왜 보나 |
|---|---|
| 같은 플로우를 iframe이 아닌 새 탭으로 열었을 때 되는가 | embedded-only 문제인지 자른다 |
| 실패가 특정 브라우저/모드에 집중되는가 | privacy policy 차이인지 본다 |
| `Set-Cookie`에 `SameSite=None; Secure`가 이미 있는가 | 아직 속성 문제 단계인지, 다음 단계인지 자른다 |
| redirect가 `http://...`로 꺾이지 않는가 | proxy 문제를 먼저 배제한다 |

이 네 줄만 확인해도 "cookie 설정 문제를 더 파야 하는지"와
"embedded login 설계를 다시 봐야 하는지"가 갈린다.

---

## 그다음 선택지는 보통 세 가지다

### 1. iframe 안에서 로그인하지 않고 top-level login으로 뺀다

beginner에게 가장 안전한 해법은 이쪽이다.

- iframe 안에서는 "로그인 필요" 안내만 보여 준다
- 실제 로그인은 새 탭, popup, full-page redirect로 수행한다
- 로그인 완료 뒤 원래 화면으로 돌아오게 한다

이 방식은 modern privacy 정책과 덜 충돌한다.

### 2. embed가 꼭 필요하면 브라우저별 허용 모델을 따로 검토한다

예를 들면 아래 키워드가 등장할 수 있다.

- Storage Access API
- partitioned cookie / CHIPS
- browser-specific third-party cookie exceptions

하지만 이 문서의 범위에서는 구현 디테일보다는,
"이건 이제 단순 SameSite 조정이 아니라 제품/브라우저 정책 설계 문제"라는 점만 잡으면 충분하다.

### 3. 정말 iframe이 필요한지 제품 요구사항을 다시 확인한다

partner portal embed는 기술보다 요구사항이 먼저 흔들리는 경우가 많다.

- 반드시 same-tab embedded login이어야 하는가
- popup 또는 top-level redirect를 허용할 수 없는가
- 로그인 이후의 데이터 표시만 iframe이어도 되는가

이 질문이 정리되면 구현 선택지도 훨씬 단순해진다.

---

## 자주 하는 오해

### 1. "`SameSite=None; Secure`까지 했으니 브라우저가 무조건 보내야 하죠?"

아니다.

그 설정은 cross-site cookie 전송의 기본 문을 여는 것이지,
모든 privacy 정책을 무시하게 만드는 스위치는 아니다.

### 2. "iframe에서 안 되면 서버가 가끔 불안정한 거 아닌가요?"

그럴 수도 있지만, 먼저 브라우저 조건 차이를 본다.

- 같은 서버
- 같은 cookie 속성
- 다른 브라우저/모드

인데 결과가 갈리면 privacy 정책 차이일 가능성이 크다.

### 3. "그럼 cookie를 localStorage로 바꾸면 되나요?"

이 문서 기준의 안전한 첫 답은 아니다.

브라우저 저장 위치를 바꾸는 문제는
XSS, token 노출, BFF 경계까지 같이 열기 쉽다.
이 축은 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)에서 따로 본다.

---

## 어디로 이어서 읽으면 되나

| 지금 남은 질문 | 다음 한 장만 읽기 | 이유 |
|---|---|---|
| 아직 `SameSite`/proxy/cookie scope 분리가 안 끝났다 | `[entrypoint]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) | beginner용 1차 분기를 다시 고정한다 |
| `auth.example.com`과 `app.example.com` handoff가 더 수상하다 | `[follow-up]` [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | iframe privacy보다 subdomain 범위 문제가 더 흔할 수 있다 |
| redirect가 `http://...`로 꺾이는 장면도 있다 | `[follow-up]` [Secure Cookie Behind Proxy Guide](./secure-cookie-behind-proxy-guide.md) | privacy 문제가 아니라 scheme 전달 문제일 수 있다 |
| cookie 대신 다른 browser/server 경계 설계를 고민해야 한다 | `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) | 저장 위치 변경보다 경계 설계를 먼저 본다 |
| cross-site cookie를 연 뒤 CSRF까지 같이 봐야 한다 | `[follow-up]` [Embedded Login CSRF Bridge](./embedded-login-csrf-bridge.md) | cookie 허용 뒤 최소 CSRF 기대치를 먼저 본다 |

## 한 줄 정리

iframe login이 `SameSite=None; Secure` 이후에도 실패하면, 이제 질문은 cookie 속성보다는 브라우저의 third-party cookie/privacy 정책이다. beginner에게 가장 안전한 첫 선택지는 embedded login을 top-level login으로 우회할 수 있는지부터 확인하는 것이다.
