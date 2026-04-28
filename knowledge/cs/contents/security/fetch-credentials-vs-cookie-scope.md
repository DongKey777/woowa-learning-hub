# Fetch Credentials vs Cookie Scope

> 한 줄 요약: `credentials: "include"`는 "브라우저가 credential을 실어도 된다"는 요청 옵션일 뿐이다. 실제 cookie가 붙으려면 cookie scope도 맞아야 하고, JavaScript가 응답을 읽으려면 서버 CORS credential 정책도 따로 맞아야 한다.

**난이도: 🟢 Beginner**

> 먼저 15초 체크:
> `Application > Cookies`에 보이는가? -> 같은 실패 요청의 `Network > Request Headers > Cookie`가 비는가? -> 그다음에야 CORS 응답 읽기 문서로 간다.
> 이 순서는 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md#application-vs-network-15초-미니-체크)의 `Application vs Network` 미니 체크와 같은 습관이다.

> `origin` vs `site` 감각부터 흐리면 먼저 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md#먼저-origin과-site를-구분하자)에서 1분 mental model을 맞춘 뒤 다시 이 문서로 돌아온다.

관련 문서:
- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)
- [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)
- [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- [CORS 기초](./cors-basics.md)
- [Preflight Debug Checklist](./preflight-debug-checklist.md)
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder)
- [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: fetch credentials vs cookie scope, same-origin vs same-site fetch, origin vs site basics, credentials include cookie missing, request cookie header empty, cookie stored but not sent, cors response blocked, cookie scope vs cors chooser, application vs network cookie check, application cookie present but request header empty, application 탭에는 cookie가 보이는데 요청 헤더는 없음, cookie 있는데 다시 로그인, beginner fetch cookie primer, browser session troubleshooting return path, fetch credentials vs cookie scope beginner

## Application vs Network 15초 미니 체크

cross-origin `fetch`에서도 초보자용 첫 습관은 같다.
`Application`은 "저장돼 있는가", `Network`는 "이번 요청에 실제로 실렸는가"를 보여 준다.

| 2-pane 체크 | DevTools에서 보는 곳 | 15초 질문 | 바로 내리는 뜻 |
|---|---|---|---|
| `Application` pane | `Application > Cookies` | session cookie가 저장돼 있는가? | 안 보이면 아직 저장 단계 문제다 |
| `Network` pane | 같은 실패 요청의 `Request Headers > Cookie` | 방금 본 cookie가 이번 요청에 실제로 실렸는가? | 비어 있으면 `credentials` 또는 cookie scope를 먼저 본다 |
| `Network`의 응답 해석 | 같은 요청의 `Status` + console CORS 메시지 | cookie는 실렸는데 JS만 응답을 못 읽는가? | 그때부터 CORS 응답 읽기 문서로 간다 |

짧게 외우면:

- `Application`에 보인다는 사실만으로 전송 성공 결론을 내리지 않는다.
- 같은 실패 요청의 `Network > Request Headers > Cookie`를 보기 전에는 CORS deep dive로 바로 뛰지 않는다.
- request `Cookie`가 실린 뒤에만 CORS와 server-side auth 복원 갈래를 고른다.

## 10초 chooser: cookie scope vs CORS

이 문서는 "cookie가 왜 안 붙는지"를 자르는 primer bridge다. 아래 표에서 가운데 줄이면 이 문서가 맞다.

| 지금 DevTools에서 먼저 보이는 장면 | 먼저 좁힐 축 | 바로 갈 문서 |
|---|---|---|
| `OPTIONS`만 실패하고 actual `GET`/`POST`가 안 보인다 | preflight / CORS 출발 여부 | [Preflight Debug Checklist](./preflight-debug-checklist.md) |
| actual request는 있는데 request `Cookie` header가 비어 있다 | `fetch credentials` 또는 cookie scope | 이 문서의 [Application vs Network 15초 미니 체크](#application-vs-network-15초-미니-체크) -> [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| request `Cookie`는 실렸는데 콘솔이 CORS 에러를 말한다 | CORS 응답 읽기 정책 | [CORS 기초](./cors-basics.md) |
| request `Cookie`도 실렸고 CORS도 아닌데 다시 `/login`이나 anonymous다 | server-side session/auth 복원 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |

짧게 외우면 `Cookie`가 비면 이 문서, `Cookie`는 있는데 JS만 막히면 CORS 문서다. 갈래를 잃으면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아간다.

## 먼저 같은 실패 요청에서 `Application` vs `Network`를 나눈다

초보자는 `credentials: "include"`와 CORS를 먼저 건드리기 쉽지만, 더 안전한 첫 질문은 아래 둘이다.

1. `Application > Cookies`에 session cookie가 저장돼 있는가?
2. 같은 실패 요청의 `Network > Request Headers > Cookie`에 그 cookie가 실제로 실렸는가?

필드 이름이 아직 낯설면 [Cookie DevTools Field Checklist Primer](./cookie-devtools-field-checklist-primer.md)에서 `Set-Cookie` / `Application row` / request `Cookie`를 같은 cookie 이름으로 맞추는 1분 표부터 먼저 본다.

이 두 칸을 먼저 나누면 `stored but not sent`와 `sent but CORS/read failure`를 섞지 않게 된다.
cross-origin reader도 같은 실패 요청의 `Application`과 `Network`를 한 쌍으로 보지 않으면 transport verification을 건너뛰고 CORS만 만지기 쉽다.

request `Cookie` header가 비었다고 해서 곧바로 `SameSite`나 CORS로 뛰지는 않는다.
초보자용 handoff는 아래 세 칸이면 충분하다.

| request `Cookie`가 비는 이유를 가르는 첫 질문 | 먼저 보는 것 | 다음 한 걸음 |
|---|---|---|
| actual request 자체가 있었나? | `OPTIONS`만 있고 actual `GET`/`POST`가 없는지 | actual request가 없으면 [Preflight Debug Checklist](./preflight-debug-checklist.md) |
| actual request가 있었다면 cross-origin `fetch`에 `credentials: "include"`가 있었나? | 호출 코드 또는 request mode | 빠졌으면 이 문서의 `credentials` 구간을 먼저 본다 |
| `credentials: "include"`도 있었는데 여전히 비나? | cookie `Domain`/`Path`/`SameSite`와 request URL | 그러면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 내려간다 |

한 줄 규칙:

- `Access-Control-Allow-Credentials: true`는 request에 cookie를 붙이는 스위치가 아니다.
- request `Cookie`가 비면 CORS 응답 읽기보다 request option과 cookie scope를 먼저 자른다.

## 거울 예시: `Application`에는 있는데 request `Cookie`는 비는 경우

아래 장면은 [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](../network/application-tab-vs-request-cookie-header-mini-card.md)와 같은 말을 cross-origin `fetch`에 그대로 옮긴 예시다.

| 같은 턴에 보는 칸 | 실제로 보이는 것 | 초급자 해석 |
|---|---|---|
| `Application > Cookies > https://api.example.com` | `SID` cookie row가 있다 | 브라우저에 저장된 사실은 맞다 |
| `Network > Headers > Request Headers > Cookie` | 비어 있다 | 이번 요청 전송 판정에서 탈락했다 |
| 프런트 코드 | `fetch("https://api.example.com/me")` | cross-origin인데 `credentials: "include"`가 빠졌다 |

이때 첫 해석은 "cookie 저장 실패"가 아니라 "이번 요청이 credential을 싣지 못했다"다.
즉 `Application` row는 과거 저장 사실이고, request `Cookie` header는 이번 요청 판정 결과다.

바로 이어서 볼 것은 두 가지뿐이다.

1. `fetch`에 `credentials: "include"`가 빠졌는가
2. 넣어도 비어 있다면 `Domain`/`Path`/`SameSite`/`Secure`가 맞는가

이 거울 예시를 먼저 고정하면 "`Application`에는 보이는데 왜 익명이지?"를 CORS 응답 읽기 문제와 덜 섞게 된다.

## 첫 증거로 갈래를 정한다

| 먼저 본 증거 | 1차 해석 | 바로 갈 문서 | 읽고 난 뒤 복귀 |
|---|---|---|---|
| `Application > Cookies`에도 안 보인다 | 아직 저장 단계일 수 있다 | [Cookie Failure Three-Way Splitter](./cookie-failure-three-way-splitter.md) -> [Cookie Rejection Reason Primer](./cookie-rejection-reason-primer.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `Application > Cookies`에는 보이는데 같은 실패 요청의 `Cookie` header가 비어 있다 | `credentials` 또는 cookie scope를 먼저 봐야 한다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| request `Cookie`는 실렸는데 콘솔이 CORS 에러를 말한다 | cookie 전송은 됐다. 응답 읽기 정책을 본다 | [CORS 기초](./cors-basics.md) -> [CORS, SameSite, Preflight](./cors-samesite-preflight.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| request `Cookie`도 실렸고 CORS도 아닌데 다시 anonymous나 `/login`이다 | 이제 server-side auth/session 복원 갈래다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

한 줄 규칙:

- `Application`에 보인다는 사실만으로 전송 성공 결론을 내리지 않는다.
- request `Cookie` header가 비면 CORS deep dive보다 cookie 전송 갈래를 먼저 본다.
- CORS 문서는 request `Cookie`가 실제로 실린 뒤에 읽어도 늦지 않다.

## 이 문서의 자리부터 잡기

이 문서는 "CORS를 공부하는 문서"도 아니고 "cookie 속성만 파는 문서"도 아니다.
초보자가 아래 세 문장을 같은 뜻으로 읽기 시작할 때 끼워 넣는 bridge다.

- "`credentials: \"include\"`를 넣었는데 cookie가 안 간다"
- "`Access-Control-Allow-Credentials: true`도 켰는데 왜 안 되지?"
- "`Application > Cookies`에는 값이 보이는데 브라우저만 익명처럼 보인다"

먼저 어디서 들어왔는지에 따라 읽는 순서를 짧게 고르면 된다.

> 한 줄 chooser: "request `Cookie`가 왜 비는지"를 고르는 문서가 필요하면 이 문서를, "cookie는 갔는데 CORS가 왜 응답을 막는지"만 빠르게 다시 잡고 싶으면 [CORS 기초](./cors-basics.md)를, 갈래를 다시 고르고 싶으면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)를 본다.

| 지금 상태 | 이 문서를 읽기 전/후 다음 한 걸음 |
|---|---|
| Network에 `OPTIONS`가 먼저 `401`/`403`/`405`로 실패하고 actual `GET`/`POST`가 보이지 않는다 | 먼저 [Preflight Debug Checklist](./preflight-debug-checklist.md)로 가서 preflight failure와 actual auth failure를 분리한 뒤, actual request가 보일 때만 이 문서로 돌아온다 |
| `origin`, `site`, `fetch credentials` 용어부터 낯설다 | 먼저 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)으로 용어를 맞춘 뒤 이 문서로 돌아온다 |
| `credentials: "include"`와 cookie `Domain`/`Path`/`SameSite`가 한 덩어리로 섞여 있다 | 이 문서에서 request option, cookie scope, CORS response 읽기를 세 칸으로 나눈다 |
| 문서를 읽다가 갈래를 잃었다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 symptom 기준으로 다시 고른다 |

## detour에서 복귀하는 login-loop primer ladder

`fetch`/CORS/cookie scope를 분리했다면, beginner route는 아래 사다리로 같은 자리로 복귀한다.

| 단계 | 왜 이 단계로 복귀하나 | 링크 |
|---|---|---|
| 1. `primer` | login redirect와 `SavedRequest` 복귀 흐름을 baseline으로 다시 고정 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| 2. `primer bridge` | `401`/`302`, login HTML fallback, cookie 누락 증상을 한 표로 다시 분기 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| 3. `catalog` | 다음 symptom 갈래를 category navigator에서 다시 선택 | [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## 막히면 여기로 돌아온다

이 문서를 읽다가 branch가 너무 많아졌다면, 초보자는 아래 한 줄만 다시 잡으면 된다.

| 내가 확인한 증거 | 다음 한 걸음 | 돌아오는 자리 |
|---|---|---|
| actual request 자체가 없다 | [Preflight Debug Checklist](./preflight-debug-checklist.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| actual request는 있는데 `Cookie` header가 비어 있다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| request `Cookie`는 실렸는데 JS가 응답을 못 읽는다 | [CORS 기초](./cors-basics.md) -> [CORS, SameSite, Preflight](./cors-samesite-preflight.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| `401`/`302`, login HTML fallback, hidden session 갈래로 다시 묶고 싶다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

## request `Cookie` header를 본 뒤 같은 return path

이 문서는 branch를 늘리기 위한 문서가 아니라, request `Cookie` header 확인 뒤에 초보자가 같은 자리로 복귀하게 만드는 splitter다.

| request `Cookie` header 체크 결과 | 다음 한 걸음 | 같은 복귀 anchor |
|---|---|---|
| actual request가 없다 | [Preflight Debug Checklist](./preflight-debug-checklist.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| actual request는 있는데 `Cookie` header가 비어 있다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| request `Cookie`는 실렸는데 JS가 CORS 에러로 응답을 못 읽는다 | [CORS 기초](./cors-basics.md) -> [CORS, SameSite, Preflight](./cors-samesite-preflight.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| request `Cookie`는 실렸는데 login HTML fallback, `302 -> /login`, anonymous가 남는다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

한 줄 규칙:

- request `Cookie`를 보기 전에는 `session persistence` 결론을 서두르지 않는다.
- request `Cookie`를 본 뒤에는 branch를 읽고 다시 같은 troubleshooting anchor로 돌아온다.

## 먼저 잡을 mental model

브라우저 인증 디버깅에서는 "쿠키를 보낸다"라는 말을 세 단계로 나눠야 한다.

1. JavaScript 요청이 credential을 포함해도 되는가?
2. 그 cookie가 이 URL에 붙을 수 있는 scope인가?
3. 서버 응답을 JavaScript가 읽어도 되는 CORS 정책인가?

세 질문은 서로 대신해 주지 않는다.

| 관문 | 묻는 질문 | 주로 보는 것 | 실패하면 보이는 장면 |
|---|---|---|---|
| `fetch` credential mode | 이 요청이 브라우저 credential을 포함해도 되나? | `credentials: "omit" / "same-origin" / "include"` | cross-origin 요청의 `Cookie` header가 비어 있다 |
| cookie scope | 이 cookie가 이 host/path/site에 붙을 수 있나? | `Domain`, `Path`, `SameSite`, `Secure`, host-only 여부 | `Application`에는 보이지만 실패 요청에는 안 붙는다 |
| CORS credential policy | credential이 섞인 cross-origin 응답을 JS가 읽어도 되나? | `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, `Vary: Origin` | 요청은 갔는데 콘솔에는 CORS 에러가 난다 |

즉 `credentials: "include"`를 넣었다고 CORS가 해결되지 않고, CORS를 열었다고 cookie scope가 자동으로 넓어지지 않는다.

## 먼저 20초 분기표: CORS vs cookie scope

아래는 beginner가 가장 덜 헷갈리는 첫 분기다.

| 실패 요청에서 먼저 보이는 증거 | 먼저 좁힐 축 | 바로 갈 문서 | 읽고 난 뒤 복귀 |
|---|---|---|---|
| `OPTIONS`만 `401`/`403`/`405`로 실패하고 actual `GET`/`POST`가 아예 없다 | preflight/CORS lane | [Preflight Debug Checklist](./preflight-debug-checklist.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| actual 요청은 보이는데 request `Cookie` header가 비어 있다 | cookie 전송/scope lane | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| request `Cookie`는 실렸는데 콘솔이 CORS 에러로 응답 읽기를 막는다 | CORS response 읽기 lane | [CORS 기초](./cors-basics.md) -> [CORS, SameSite, Preflight](./cors-samesite-preflight.md) | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |

한 줄 규칙:

- actual 요청이 없으면 auth/session 결론을 내리지 않는다.
- actual 요청에 cookie가 없으면 CORS보다 cookie scope를 먼저 본다.
- cookie는 실렸는데 JS가 못 읽으면 CORS response policy를 먼저 본다.

## 30초 DevTools Network reading box

이 문서도 [Preflight Debug Checklist](./preflight-debug-checklist.md)의 같은 읽기 순서를 그대로 쓴다.
초보자는 `status` 숫자보다 아래 3칸을 같은 순서로 보면 덜 헷갈린다.

> 30초 mental model:
> `요청 method` -> `actual request 존재 여부` -> actual request의 `Cookie` header / `status` 순서로 읽는다.

| 장면 | 요청 method | actual request 존재 여부 | actual request의 `Cookie` header | 지금 읽는 status | 1차 결론 |
|---|---|---|---|---|---|
| 예시 A | `OPTIONS` | 같은 path의 actual `GET`/`POST`가 없음 | 볼 actual request 자체가 없음 | `OPTIONS`의 `401`/`403`/`405` | 아직 cookie/auth 결론을 내리지 않는다. 먼저 preflight/CORS lane이다 |
| 예시 B | `OPTIONS` 다음 actual `GET`/`POST` | actual request가 실제로 보임 | 비어 있음 | actual request의 `401` 또는 login HTML | `credentials` 또는 cookie scope를 먼저 본다. CORS 응답 읽기보다 앞 단계다 |
| 예시 C | `OPTIONS` 다음 actual `GET`/`POST` | actual request가 실제로 보임 | `session=...`가 실려 있음 | actual request는 `200`/`401`, 콘솔은 CORS 에러 | cookie는 이미 갔다. 이제 CORS response 읽기 또는 server-side auth 복원을 본다 |

초보자용 한 줄 해석:

- `OPTIONS`만 실패하면 아직 "`cookie가 안 갔다`"고도 말하지 않는다.
- actual request가 보이면 그때 request `Cookie` header부터 본다.
- request `Cookie`가 비면 cookie scope/`credentials` lane, request `Cookie`가 있으면 CORS/auth lane으로 넘긴다.

---

## `credentials` 옵션은 무엇을 바꾸나

`fetch`의 `credentials`는 브라우저가 자동으로 관리하는 credential, 특히 cookie를 요청에 포함할지 결정한다. 이 문서에서는 cookie 디버깅에 집중한다.

| 값 | beginner 감각 | 주의할 점 |
|---|---|---|
| `omit` | cookie 같은 브라우저 credential을 보내지 않는다 | login API처럼 cookie가 필요한 호출에 쓰면 인증 상태가 안 간다 |
| `same-origin` | 기본값이다. 정확히 같은 origin일 때만 보낸다 | sibling subdomain은 same-site일 수 있어도 same-origin은 아니다 |
| `include` | cross-origin 요청에도 credential을 포함할 수 있게 한다 | cookie scope와 CORS 응답 정책이 맞아야 실제로 성공한다 |

응답이 `Set-Cookie`를 내려주는 흐름도 같이 봐야 한다.
cross-origin `fetch`에서 cookie 저장을 기대한다면 credential mode, CORS credential 응답, cookie 속성(`Secure`, `SameSite`, `Domain`, `Path`)이 모두 맞아야 한다.
DevTools에 cookie rejection reason이 보이면 그 메시지를 먼저 따른다.

예를 들어 프론트가 `https://app.example.com`, API가 `https://api.example.com`이면 origin이 다르다.

```js
fetch("https://api.example.com/me")
```

이 기본 요청은 cross-origin cookie 전송을 기대하기 어렵다. cookie 기반 인증 API라면 보통 아래처럼 명시한다.

```js
fetch("https://api.example.com/me", {
  credentials: "include"
})
```

하지만 여기까지는 첫 번째 관문만 지난 것이다.

---

## CORS credential 정책은 무엇을 바꾸나

서버는 credential이 포함된 cross-origin 응답을 브라우저 JavaScript가 읽어도 된다고 명시해야 한다.

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
```

여기서 중요한 점은 두 가지다.

- `Access-Control-Allow-Origin: *`는 credential 응답과 같이 쓰면 안 된다.
- `Access-Control-Allow-Credentials: true`는 cookie를 "붙여 주는" 헤더가 아니다. 이미 credential이 포함된 요청/응답을 JS에 노출해도 된다고 허용하는 쪽에 가깝다.

그래서 이런 혼란이 생긴다.

| 관찰 | 가능한 해석 |
|---|---|
| 서버 로그에는 `/me`가 `200`으로 찍힘 | 네트워크 요청 자체는 도착했을 수 있다 |
| 브라우저 콘솔에는 CORS 에러 | JS가 응답을 읽는 단계에서 막혔을 수 있다 |
| request `Cookie` header가 비어 있음 | CORS보다 앞 단계인 `fetch credentials` 또는 cookie scope 문제일 수 있다 |

CORS는 "응답 읽기"의 문제이고, cookie scope는 "요청에 cookie가 붙는가"의 문제다.

---

## cookie scope는 무엇을 바꾸나

cookie가 브라우저에 저장돼 있어도 모든 요청에 붙는 것은 아니다.
브라우저는 매 요청마다 `Domain`, `Path`, `SameSite`, `Secure`를 보고 전송 여부를 다시 판단한다.

예를 들어 login이 아래처럼 끝났다고 하자.

```http
Set-Cookie: session=abc123; Path=/; HttpOnly; Secure
```

`Domain`이 없으면 보통 이 cookie는 응답을 준 정확한 host에 묶이는 host-only cookie다.
`https://auth.example.com/login`에서 받은 host-only cookie는 `https://api.example.com/me`에 붙지 않는다.

반대로 subdomain 사이에서 공유하려면 의도적으로 scope를 맞춰야 한다.

```http
Set-Cookie: session=abc123; Domain=example.com; Path=/; HttpOnly; Secure; SameSite=Lax
```

이 설정도 만능은 아니다.

- `Path=/auth`면 `/api/me`에는 안 붙는다.
- cross-site iframe이나 partner domain 호출이면 `SameSite=None; Secure`가 필요할 수 있다.
- `Secure` cookie는 HTTPS 요청에만 붙는다.

즉 `credentials: "include"`는 cookie scope를 무시하는 버튼이 아니다.

---

## 한 장면으로 보는 디버깅

### 장면 1: `credentials: "include"`가 빠진 경우

| 항목 | 관찰 |
|---|---|
| 프론트 | `https://app.example.com` |
| API | `https://api.example.com/me` |
| `Application > Cookies` | `https://api.example.com` 아래 `session=abc123`가 보임 |
| 요청 코드 | `fetch("https://api.example.com/me")` |
| 실패 요청 | `Cookie` header가 비어 있음 |

먼저 의심할 것은 default `same-origin`이다.
`app.example.com`과 `api.example.com`은 같은 site일 수 있어도 origin은 다르다.

후보 수정:

```js
fetch("https://api.example.com/me", {
  credentials: "include"
})
```

그다음 서버 CORS와 cookie scope를 이어 확인한다.

### 장면 2: CORS credential 정책이 빠진 경우

| 항목 | 관찰 |
|---|---|
| 실패 요청 | `Cookie: session=abc123`가 실제로 실림 |
| 서버 로그 | `/me`가 `200` 또는 `401`로 찍힘 |
| 브라우저 콘솔 | CORS 에러로 JS가 응답을 못 읽음 |

이때는 cookie 전송보다 응답 노출 정책이 더 의심된다.

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
```

허용 origin은 `*`가 아니라 실제 프론트 origin이어야 한다.

### 장면 3: cookie scope가 틀린 경우

| 항목 | 관찰 |
|---|---|
| 요청 코드 | `credentials: "include"` 있음 |
| CORS 응답 | exact origin + credentials 허용 |
| DevTools `Application` | cookie가 `auth.example.com` 아래 보임 |
| 실패 요청 | `https://api.example.com/me`에 `Cookie` header가 없음 |

이때는 `fetch`나 CORS보다 cookie scope를 먼저 본다.

- host-only cookie인가?
- `Domain=example.com`이 필요한 구조인가?
- `Path`가 `/auth`처럼 너무 좁지 않은가?
- cross-site 맥락인데 `SameSite=Lax`/`Strict`로 막히지 않았나?

이 분해는 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에서 더 자세히 본다.

---

## 가장 흔한 혼동

### 1. "`Access-Control-Allow-Credentials: true`면 cookie가 자동으로 가나요?"

아니다.

이 헤더는 서버가 브라우저에게 credentialed response를 허용한다고 말하는 쪽이다.
request에 cookie를 붙일지는 `fetch` credential mode와 cookie scope가 먼저 결정한다.

### 2. "`credentials: include`를 넣었는데 왜 아직 CORS 에러가 나나요?"

`credentials: "include"`는 요청 옵션이다.
서버 응답에는 여전히 exact `Access-Control-Allow-Origin`과 `Access-Control-Allow-Credentials: true`가 필요하다.

### 3. "`SameSite`와 `same-origin`은 같은 말인가요?"

아니다.

| 비교 | 예시 | 뜻 |
|---|---|---|
| same-origin | `https://app.example.com` -> `https://app.example.com` | scheme, host, port가 모두 같다 |
| same-site | `https://app.example.com` -> `https://api.example.com` | 보통 같은 registrable domain 묶음이다 |

### 4. "Network에 `401`이 보이는데 이게 cookie 누락인가요, CORS인가요?"

숫자 하나만으로는 모른다.

먼저 아래 순서로 다시 읽는다.

1. `401`이 `OPTIONS`에 붙었는지 actual `GET`/`POST`에 붙었는지 본다.
2. actual request가 있으면 그 request의 `Cookie` header가 비었는지 본다.
3. `Cookie`가 비면 cookie scope/`credentials`, `Cookie`가 있으면 CORS response 읽기나 서버 auth 복원을 본다.

## 다음 단계 한 칸 + category 복귀

- `OPTIONS`만 실패하고 actual request가 없으면: [Preflight Debug Checklist](./preflight-debug-checklist.md)
- actual request는 있는데 `Cookie` header가 비면: [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
- request `Cookie`는 실렸는데 콘솔이 CORS 에러를 내면: [CORS 기초](./cors-basics.md) -> [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
- login loop 전체 맥락으로 다시 묶고 싶으면: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- 갈래를 잃으면: [Security README: Browser / Session Beginner Ladder](./README.md#browser--session-beginner-ladder) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

`fetch` default인 `same-origin`은 sibling subdomain을 같은 origin으로 보지 않는다.
반면 cookie `SameSite`는 origin이 아니라 site 맥락을 본다.

### 4. "Postman에서는 되는데 브라우저만 안 돼요"

Postman은 브라우저 CORS 정책과 cookie scope 자동 판단을 똑같이 적용하지 않는다.
브라우저 auth 문제는 반드시 DevTools `Network`에서 실제 request `Cookie` header와 CORS 응답 헤더를 같이 봐야 한다.

---

## 실전 확인 순서

1. 호출 URL이 같은 origin인지, sibling subdomain인지, 완전히 다른 site인지 적는다.
2. `fetch`에 `credentials: "include"`가 필요한 cross-origin 호출인지 본다.
3. 실패한 요청의 raw request header에 `Cookie`가 실제로 있는지 확인한다.
4. `Cookie`가 없으면 `Application > Cookies`의 `Domain`, `Path`, `SameSite`, `Secure`를 요청 URL과 비교한다.
5. `Cookie`가 있는데 JS가 응답을 못 읽으면 `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, `Vary: Origin`을 본다.
6. 서버가 새 cookie를 내려줘야 하는 흐름이면 응답의 `Set-Cookie`와 브라우저의 cookie rejection reason도 같이 확인한다.
7. cookie가 실제로 실렸고 응답도 읽히는데 여전히 익명이면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 넘긴 뒤, 다시 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 다음 branch를 고른다.

이 순서의 핵심은 "CORS부터 고치자"가 아니라, request 전송과 response 읽기와 cookie scope를 따로 관찰하는 것이다.

---

## 읽고 나서 바로 어디로 가나

| 지금 확인한 사실 | 다음 문서 |
|---|---|
| request `Cookie` header가 비어 있고 `Domain`/`Path`/`SameSite`가 의심된다 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md) |
| request에는 cookie가 실렸는데 브라우저 콘솔이 CORS 에러를 말한다 | [CORS 기초](./cors-basics.md)부터 다시 보고, 운영 세부까지 필요하면 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)로 내려간다 |
| cookie도 실리고 CORS도 읽히는데 login HTML fallback이나 `302 -> /login`이 남는다 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| `hidden session mismatch`라고 부르지만 실제로는 cookie 전송 실패인지 session 조회 실패인지 구분이 안 된다 | 먼저 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 `cookie-not-sent` vs `server-mapping-missing`를 분리하고, 전송 실패면 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 이어 간다 |
| side path 분리는 끝났고 login-loop baseline으로 돌아가고 싶다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path) |
| 여전히 어느 갈래인지 모르겠다 | [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아가 symptom 기준으로 다시 고른다 |

---

## 다음 단계

- side path 분리를 끝냈으면 같은 login-loop 복귀 사다리로 돌아간다: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path).
- cookie가 저장됐지만 특정 host/path/site 요청에 안 붙는 문제는 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)로 이어 간다.
- preflight, `SameSite=None`, `Vary: Origin`, CORS allowlist 운영까지 더 깊게 보려면 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)를 본다.
- credentialed CORS allowlist 설계 자체는 [CORS Credential Pitfalls / Allowlist Design](./cors-credential-pitfalls-allowlist.md)로 내려간다.
- cookie가 붙는데도 `302 -> /login`이나 login HTML fallback이 보이면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)를 본다.
- browser/session symptom 자체를 다시 분류하고 싶으면 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아간다.

## 한 줄 정리

브라우저 cookie auth 디버깅은 `fetch`가 credential을 허용했는지, cookie scope가 요청 URL에 맞는지, 서버 CORS credential 정책이 응답 읽기를 허용했는지를 세 칸으로 나누면 빠르게 좁혀진다.
