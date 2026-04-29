# Browser DevTools Application 탭 저장소 읽기 1분 카드

> 한 줄 요약: Application 탭의 `Cookies`, `Local Storage`, `Session Storage`, `Cache Storage`는 모두 "값이 있다"를 보여 주지만, 각각 답하는 질문이 달라서 먼저 "브라우저가 자동 전송하나, JS가 직접 읽나, Service Worker가 꺼내 쓰나"를 갈라 읽어야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README](./README.md#browser-devtools-application-탭-저장소-읽기-1분-카드)
- [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md)
- [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)
- [Cookie vs `localStorage` 토큰 저장 선택 카드](./cookie-vs-localstorage-token-storage-choice-card.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)

retrieval-anchor-keywords: application tab storage quick check, devtools cookies local storage session storage cache storage, application cookies vs request cookie, local storage token but no authorization, session storage tab scoped, cache storage service worker quick check, browser storage map beginner, devtools application tab 뭐 봐요, cookie stored but not sent, sessionstorage vs localstorage basics, cache storage entry not proof, cache storage vs 304, application tab vs network tab cache, beginner devtools storage card, 처음 application 탭 뭐 봐요

## 핵심 개념

Application 탭은 "브라우저 안에 지금 무엇이 저장돼 있나"를 보여 주는 화면이다.  
하지만 초급자가 자주 막히는 지점은 "저장돼 있다"와 "이번 요청에 실제로 쓰였다"를 같은 뜻으로 읽는 것이다.

먼저 저장소를 역할별로 나누면 훨씬 쉽다.

- `Cookies`: 브라우저가 조건이 맞으면 요청에 자동으로 실어 보낼 수 있는 값
- `Local Storage`: 자바스크립트가 직접 읽고 써야 하는 값
- `Session Storage`: 현재 탭 문맥에서만 자바스크립트가 직접 쓰는 값
- `Cache Storage`: Service Worker나 앱 코드가 `Request`-`Response` 쌍을 꺼내 쓸 수 있는 상자

한 줄 멘탈 모델:

```text
Cookies = 자동 전송 후보
Local/Session Storage = JS가 직접 읽는 앱 상태
Cache Storage = Service Worker 경로에서 쓸 수 있는 응답 상자
```

## 한눈에 보기

| Application 탭 위치 | 먼저 답하는 질문 | 여기서 바로 확정 못 하는 것 |
|---|---|---|
| `Storage > Cookies` | 이 origin cookie가 브라우저에 저장돼 있나 | 이번 실패 요청에 실제 `Cookie` 헤더로 실렸나 |
| `Storage > Local Storage` | 브라우저에 남는 앱 값이 있나 | 브라우저가 그 값을 자동으로 `Authorization` 헤더에 넣었나 |
| `Storage > Session Storage` | 현재 탭에서만 쓰는 앱 값이 있나 | 새 탭/새 창에서도 그대로 이어지나 |
| `Storage > Cache Storage` | Service Worker나 앱이 쓸 수 있는 cached response entry가 있나 | 이번 Network row의 `from ServiceWorker`, `from disk cache`, `304` 원인이 이것이라고 바로 확정 |

1분 카드로 압축하면 이 순서다.

1. `Cookies`가 보이면 저장 여부 질문이다.
2. `Local Storage`/`Session Storage`가 보이면 JS가 읽어 쓰는지 질문이다.
3. `Cache Storage`가 보이면 Service Worker 경로와 함께 봐야 하는 질문이다.
4. "이번 요청에 실제로 실렸나/쓰였나"는 반드시 Network 탭으로 내려가 확인한다.

특히 `Application > Cache Storage`는 "상자에 entry가 있나"를, `Network > from disk cache`와 `Network > 304`는 "이번 body를 어디서 썼나"를 말한다. 둘 다 캐시처럼 보여도 같은 종류의 증거가 아니다.

빠른 bridge 한 줄:
`Application > Cookies`에는 값이 보이는데 같은 실패 요청의 request `Cookie` header가 비면, 먼저 cross-origin `fetch`의 `credentials: "include"` 누락인지 자르고, 그다음에야 cookie scope mismatch를 본다.

같은 구조를 `localStorage`에 평행하게 붙이면:
`Application > Local Storage`에는 access token이 있는데 같은 API 요청의 request `Authorization` header가 비면, 토큰 만료보다 먼저 프런트 코드의 헤더 조립 경로를 의심한다.

## 로그인 실패 장면에서 30초 분리

초급자가 많이 묻는 질문은 "`Application`에 값은 있는데 왜 요청이나 로그인 결과가 다르죠?"다. 같은 장면에서도 저장소마다 답하는 질문이 다르다.

| 지금 본 것 | 첫 해석 | 아직 모르는 것 | 다음 한 칸 |
|---|---|---|---|
| `Cookies`에 `JSESSIONID`가 있다 | 브라우저 저장은 됐다 | 이번 요청에 전송됐나 | 같은 row의 `Request Headers > Cookie` |
| `Cookies`에는 있는데 cross-origin API request `Cookie`가 비어 있다 | 저장은 됐지만 전송 조건이 빠졌을 수 있다 | `credentials: "include"` 누락인지, `include`도 있는데 cookie scope 문제인지 | [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md) |
| `Local Storage`에 access token이 있는데 같은 API 요청의 request `Authorization` header가 비어 있다 | 앱이 읽을 값은 저장돼 있지만 이번 요청에는 안 실렸다 | 프런트가 `Authorization`을 붙였나 | 같은 row의 `Request Headers > Authorization` |
| `Session Storage`에 redirect state가 있다 | 현재 탭 state는 남아 있다 | 새 탭에서도 유지되나 | 새 탭 재현 또는 앱 라우팅 확인 |
| `Cache Storage`에 `/app.js`가 있다 | SW/app이 쓸 entry는 있다 | 이번 row가 그 entry를 썼나 | `from ServiceWorker` 또는 cache trace 확인 |
| `304` 또는 `from memory cache`가 보인다 | body 재사용 질문이다 | 로그인/session도 유지됐나 | `/me` 같은 인증 요청 row를 따로 확인 |

한 줄로 줄이면:

- Application 탭은 "저장돼 있나"를 잘 보여 준다.
- Network 탭은 "이번 요청에 실제로 쓰였나"를 보여 준다.
- `304`와 `from memory cache`는 인증이 아니라 body 재사용 신호다.

## Cookies / Cache Storage / HTTP cache 20초 분리표

`Application` 탭과 `Network` 탭을 같이 보다 보면 `Cookies`, `Cache Storage`, `304`, `from memory cache`가 전부 "이전 상태 재사용"처럼 들린다. 하지만 초급자에게는 질문을 먼저 나누는 편이 안전하다.

| 지금 보이는 것 | 이건 어느 층 질문인가 | 지금 바로 말할 수 있는 것 | 아직 말하면 안 되는 것 |
|---|---|---|---|
| `Application > Cookies` | 브라우저 저장/자동 전송 후보 | cookie가 저장돼 있다 | 이번 요청에 실제 전송됐다 |
| `Application > Cache Storage` | Service Worker/app cache 저장소 | SW/app이 쓸 entry가 있다 | 이번 row가 거기서 나왔다 |
| `Network > 304 Not Modified` | HTTP cache 재검증 | 서버가 기존 body를 계속 써도 된다고 답했다 | 로그인 상태도 유지됐다 |
| `Network > from memory cache`/`from disk cache` | 브라우저 HTTP cache 재사용 | body를 브라우저 cache에서 재사용했다 | cookie/session도 같이 복원됐다 |

짧게 외우면 이렇게 자른다.

- `Cookies`는 인증 단서 저장/전송 후보다.
- `Cache Storage`는 Service Worker 경로 후보다.
- `304`와 `memory cache`는 body 재사용 신호다.

## Cookies는 무엇을 확인하나

`Application > Cookies`는 "브라우저가 cookie를 저장했는가"에 답한다.

이 화면으로 빠르게 답할 수 있는 질문:

- "`Set-Cookie` 뒤에 session cookie가 브라우저에 들어갔나?"
- "`Domain`, `Path`, `SameSite`, `Secure` 값이 어떻게 저장됐나?"

이 화면만으로 아직 답 못 하는 질문:

- "왜 다음 요청 `Cookie` header가 비었지?"
- "왜 로그인은 됐는데 이 API 요청에서는 익명처럼 보이지?"

즉 `Cookies`는 **stored?**를 잘 보여 주지만, **sent?**는 Network 탭의 같은 요청 row를 봐야 한다.

## Local Storage / Session Storage는 무엇을 확인하나

`Application > Local Storage`는 "브라우저에 남겨 둔 앱 상태가 있나"를 보여 준다.

빠르게 답할 수 있는 질문:

- "토큰이나 feature flag, user preference가 저장됐나?"
- "새로고침 뒤에도 남아 있어야 하는 값이 남아 있나?"

여기서 바로 확정 못 하는 것:

- "브라우저가 이 값을 자동 전송하나?"
- "프런트 코드가 실제 API 호출 때 `Authorization` 헤더를 붙였나?"

한 줄 규칙:

- `localStorage` 값 존재 = JS가 읽을 수 있음
- `localStorage` 값 존재 != 요청에 자동 전송됨

### `Session Storage`

`Application > Session Storage`는 `localStorage`와 비슷해 보이지만 **탭 단위**라는 점이 핵심이다.

빠르게 답할 수 있는 질문:

- "지금 탭에서만 유지되는 step state, redirect state가 있나?"
- "새 탭에서 사라지는 값이 맞나?"

여기서 자주 하는 오해:

- "`sessionStorage`니까 서버 session이겠지"

아니다. 여기의 `session`은 **브라우저 탭 수명**에 가깝다. 서버 session store와는 다른 층이다.

짧게 비교하면 이렇게 자른다.

| 이름 | 어디에 있나 | 언제 같이 보나 | 지금 바로 뜻하는 것 |
|---|---|---|---|
| `sessionStorage` | 브라우저 탭 저장소 | OAuth redirect state, 현재 탭 wizard step | 이 탭에서만 JS가 읽는 값 |
| session cookie | `Application > Cookies` | `JSESSIONID`, `SID` 같은 로그인 단서 | 브라우저가 자동 전송할 수 있는 값 |
| server session | DevTools에 직접 안 보임 | `/me`, `200/401/302` 결과로 추론 | 서버가 사용자 상태를 복원했는지 |

즉 `sessionStorage`, session cookie, server session은 이름만 비슷할 뿐 서로 다른 층이다. "`session`이란 단어가 보여서 같은 상자겠지"라고 읽으면 로그인 문제와 탭 상태 문제를 쉽게 섞는다.

## Cache Storage는 무엇을 확인하나

`Application > Cache Storage`는 "Service Worker나 앱 코드가 꺼내 쓸 수 있는 response entry가 있나"를 보여 준다.

빠르게 답할 수 있는 질문:

- "offline 대응용 cache 이름과 entry가 있나?"
- "특정 URL이 Cache Storage에 들어가 있나?"

여기서 바로 확정 못 하는 것:

- "이번 Network row가 그 entry에서 바로 나왔나?"
- "HTTP cache(`memory cache`, `disk cache`, `304`)와 같은 경로인가?"

`Cache Storage`는 보통 [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)와 붙여 읽어야 안전하다.

## 흔한 오해와 함정

- `Application > Cookies`에 값이 보여도 같은 실패 요청의 `Cookie` header는 비어 있을 수 있다.
- `Application > Local Storage`에 토큰이 보여도 같은 API 요청의 request `Authorization` header는 비어 있을 수 있다. 브라우저가 그 값을 자동으로 보내지 않기 때문이다.
- `Session Storage`는 서버 session이 아니라 탭 범위 앱 상태다.
- session cookie와 `sessionStorage`는 둘 다 이름에 `session`이 들어가지만, 하나는 cookie 수명/전송 규칙이고 다른 하나는 탭 저장소다.
- `Cache Storage`에 entry가 있어도 이번 응답이 반드시 거기서 나온 것은 아니다.
- Application 탭은 "저장 상태" 중심이고, Network 탭은 "이번 요청/응답에서 실제로 무슨 일이 있었나" 중심이다.
- `304`나 `from memory cache`가 보여도 그건 로그인 유지 증거가 아니다. 인증 요청과 정적 파일 요청을 분리해서 봐야 한다.

증상별 첫 질문을 짧게 붙이면 이렇다.

| 보이는 증상 | 먼저 볼 저장소 | 바로 이어서 볼 곳 |
|---|---|---|
| "cookie는 저장된 것 같은데 요청에 안 실려요" | `Cookies` | 같은 요청의 `Request Headers > Cookie`, 그리고 [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md) |
| "`Application > Local Storage`에는 access token이 있는데 request `Authorization` header가 비어요" | `Local Storage` | 같은 요청의 `Request Headers > Authorization` |
| "새 탭 열었더니 값이 사라졌어요" | `Session Storage` | 탭 단위 state인지, 서버 session인지 |
| "Cache Storage에 있는데 왜 네트워크가 또 가요?" | `Cache Storage` | row의 `from ServiceWorker`, `memory cache`, `304` |

## 한 번에 보는 실제 예시

처음 보는 사람은 아래처럼 `login -> /me -> static` 세 줄만 분리해도 오해가 많이 줄어든다.

```text
POST /login -> 200 + Set-Cookie: JSESSIONID=abc
GET /me -> Cookie: JSESSIONID=abc -> 200
GET /app.js -> 304 Not Modified
```

이때 초급자용 첫 해석은 아래와 같다.

| 줄 | 먼저 답하는 질문 | 어디서 확인하나 |
|---|---|---|
| `POST /login -> Set-Cookie` | 브라우저가 무엇을 저장했나 | `Application > Cookies` |
| `GET /me -> Cookie -> 200` | 이번 요청에 cookie가 실렸고 서버가 사용자를 복원했나 | `Request Headers > Cookie`, 응답 status/body |
| `GET /app.js -> 304` | 정적 파일 body를 다시 받아야 했나 | `Status 304`, validator header |

즉 `/me`의 인증 성공과 `/app.js`의 cache 재사용은 같은 "상태"처럼 보여도 다른 질문이다.

## 실무에서 쓰는 모습

가장 흔한 1분 확인 흐름은 아래처럼 잡으면 된다.

1. 로그인 이슈면 `Cookies`에서 저장 여부를 본다.
2. SPA 토큰 이슈면 `Local Storage` 또는 `Session Storage`에서 값 존재를 본다.
3. 그다음 같은 요청 row에서 `Cookie` 또는 `Authorization` header가 실제로 실렸는지 본다.
4. offline/PWA 이슈면 `Cache Storage`와 `from ServiceWorker`를 같이 본다.
5. cache hit 질문이면 `Cache Storage`보다 먼저 `memory cache`, `disk cache`, `304`를 본다.

짧은 비교 예시:

- `Cookies`에 session id가 있고 request `Cookie`도 있으면 저장/전송 단계는 통과한 것이다.
- `Application > Local Storage`에는 access token이 있는데 같은 API 요청의 request `Authorization` header가 비면 프런트 코드 조립 경로를 먼저 의심한다.
- `Cache Storage`에 `/app.js`가 있어도 row가 `304`라면 지금 본 장면은 HTTP cache 재검증일 수 있다.

## 더 깊이 가려면

- cookie 저장과 전송 차이를 더 보고 싶으면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- `localStorage`와 cookie를 선택하는 질문이면 [Cookie vs `localStorage` 토큰 저장 선택 카드](./cookie-vs-localstorage-token-storage-choice-card.md)
- "`Application > Cookies`에는 보이는데 request `Cookie`는 왜 비지?"를 바로 해결하려면 [Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md)
- `Cache Storage`와 HTTP cache를 섞고 있으면 [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)
- `304`, `memory cache`, `disk cache` trace를 읽고 싶으면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- cookie는 저장됐는데 전송이 안 되면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)

## 면접/시니어 질문 미리보기

### Q. `Application > Cookies`에 값이 보이면 인증 문제는 끝난 건가요?

아니다. 저장은 확인됐지만 전송 여부와 서버 복원 여부는 별도다. 같은 요청의 `Cookie` header와 서버 쪽 session 복원까지 봐야 한다.

### Q. `localStorage`와 `sessionStorage`의 가장 실전적인 차이는 무엇인가요?

둘 다 JS가 직접 읽는 저장소지만, `sessionStorage`는 현재 탭 수명에 묶인다는 점이 가장 실전적인 차이다.

### Q. `Cache Storage`와 HTTP cache의 가장 큰 차이는 무엇인가요?

`Cache Storage`는 Service Worker나 앱 코드가 직접 다루는 저장소이고, HTTP cache는 브라우저가 `Cache-Control`, `ETag`, `304` 규칙으로 자동 관리하는 저장소다.

## 한 줄 정리

Application 탭의 저장소들은 모두 "무언가 저장돼 있음"을 보여 주지만, `Cookies`는 자동 전송 후보, `Local/Session Storage`는 JS 앱 상태, `Cache Storage`는 Service Worker용 응답 상자라는 질문 차이를 먼저 고정해야 DevTools 판독이 빨라진다.
