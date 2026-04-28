# HTTP의 무상태성과 쿠키, 세션, 캐시

> 한 줄 요약: `stateless`, `cookie`, `session`, `cache`는 모두 "상태"와 관련 있지만 같은 층위의 개념은 아니다. 이 문서는 브라우저 저장, 서버 저장, 응답 재사용을 한 번에 분리해 보는 beginner primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README](./README.md#http의-무상태성과-쿠키-세션-캐시)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)

retrieval-anchor-keywords: http stateless, cookie, session, jwt, http cache, set-cookie, cookie header, session id, browser state, 304 why, cookie 왜 다시 로그인, stateless 뭐예요, cache basics, session basics, 처음 헷갈려요

## 왜 중요한가

입문 단계에서는 아래 네 단어가 자주 한 덩어리로 들린다.

- `stateless`: HTTP가 이전 요청을 자동으로 기억하지 않는 성질
- `cookie`: 브라우저가 저장하고 다음 요청에 실어 보내는 값
- `session`: 서버가 사용자 상태를 보관하는 방식
- `cache`: 이전 응답을 다시 쓰는 방식

핵심은 "누가 무엇을 저장하나"를 먼저 나누는 것이다. cookie는 브라우저 저장, session은 서버 저장, cache는 응답 재사용이고, stateless는 그 전체 배경 규칙이다.

## 한눈에 보는 역할 구분

| 개념 | 누가 들고 있나 | 주로 무엇을 위해 쓰나 | 첫 질문 |
|---|---|---|---|
| HTTP stateless | 프로토콜 성질 | 요청 사이 자동 기억 없음 | 서버가 이전 요청을 저절로 기억하나? |
| cookie | 브라우저 | 다음 요청에 값 전달 | 브라우저가 무엇을 저장하고 보내나? |
| session | 서버 | 로그인 상태 복원 | 서버가 어떤 사용자로 볼지 어디서 찾나? |
| cache | 브라우저/중간 캐시 | 같은 응답 재사용 | 이 body를 다시 받아야 하나? |

이 표만 먼저 잡아도 `cookie=session`, `cache=로그인 유지`, `stateless면 쿠키를 못 쓴다` 같은 첫 오해를 많이 줄일 수 있다.

## 처음엔 이 4칸 메모부터 본다

처음 읽을 때는 정의를 길게 외우기보다 "`지금 보인 현상은 저장, 전송, 인증, body 재사용 중 무엇인가?`"만 먼저 고르면 된다.

| 4칸 메모 | 지금 답하려는 질문 | DevTools에서 먼저 볼 자리 | 흔한 오해 |
|---|---|---|---|
| 저장 | 브라우저가 cookie를 저장했나 | `Application > Cookies` | 저장됐으면 자동으로 인증도 된다고 생각함 |
| 전송 | 이번 요청에 `Cookie`가 실제로 실렸나 | `Network > Request Headers` | 저장됨과 전송됨을 같은 체크로 봄 |
| 인증/복원 | 서버가 그 값으로 사용자를 찾았나 | `/me`, `200/401/302` | `Cookie`만 있으면 로그인 유지라고 생각함 |
| body 재사용 | 응답 body를 다시 받았나 | `304`, `from memory cache`, `from disk cache` | cache hit를 session 복원과 같은 뜻으로 읽음 |

한 줄로 줄이면:

- cookie는 주로 저장/전송 질문이다.
- session은 서버 복원 질문이다.
- cache는 body 재사용 질문이다.

## 처음엔 이 3문장으로 자른다

초급자에게는 정의보다 "지금 내가 본 현상이 어느 질문인가"를 먼저 고르는 편이 안전하다.

| 지금 보인 장면 | 먼저 답할 질문 | 이 문서에서 붙일 이름 | 바로 이어서 볼 문서 |
|---|---|---|---|
| `Application > Cookies`에는 보이는데 request `Cookie` 헤더가 없다 | 브라우저가 저장한 값을 이번 요청에 보냈나 | cookie 전송 문제 | [Application 탭 vs Request Cookie 헤더 미니 카드](./application-tab-vs-request-cookie-header-mini-card.md) |
| request `Cookie`는 있는데 다시 로그인된다 | 서버가 그 값으로 사용자 상태를 복원했나 | session 복원 문제 | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |
| `304` 또는 `from memory cache`가 보인다 | 같은 body를 다시 받았나 | cache 재사용 문제 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |

한 줄로 줄이면:

- cookie는 `저장됐나`와 `보내졌나`를 따로 본다
- session은 `보내진 값`으로 서버가 누구인지 복원했는지 본다
- cache는 로그인과 별개로 `응답 body`를 다시 썼는지 본다

## 증상으로 먼저 고르는 1표

처음에는 개념 정의보다 "지금 보이는 현상이 어느 축 문제인가"를 먼저 고르는 편이 덜 헷갈린다.

| 지금 보이는 증상 | 먼저 의심할 축 | 왜 그렇게 보나 | 바로 이어서 볼 문서 |
|---|---|---|---|
| "`Set-Cookie`는 봤는데 다음 요청에 `Cookie`가 없어요" | cookie 전송 | 브라우저 저장과 전송 규칙이 깨졌을 수 있다 | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |
| "cookie는 있는데 왜 다시 로그인해요?" | session 복원 | 브라우저 전달은 됐지만 서버 session 복원이 실패했을 수 있다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| "`304`가 떴으니 로그인도 유지된 거죠?" | cache 재검증 오해 | `304`는 body 재사용 신호이지 사용자 인증 신호가 아니다 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| "DevTools에 `from memory cache`가 보이는데 서버가 나를 기억한 건가요?" | browser cache | 브라우저가 응답 body를 재사용한 것이지 사용자 세션을 복원한 것은 아니다 | [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md) |

## DevTools에서 어디를 먼저 볼까

입문자가 가장 많이 섞는 장면은 "`Application`에 cookie가 있고 `304`도 보이는데, 그래서 로그인 유지가 된 건가요?"다. 이때는 저장 위치와 질문을 분리해서 보면 된다.

| 지금 보는 곳 | 이 화면이 답하는 질문 | 여기서 바로 단정하면 안 되는 것 | 바로 다음 확인 |
|---|---|---|---|
| `Application > Cookies` | 브라우저가 cookie를 저장했나 | 이번 요청에 실제로 전송됐나 | 같은 요청의 `Request Headers > Cookie` |
| `Network > Request Headers` | 이번 요청에 cookie나 token이 실렸나 | 서버가 로그인 상태로 인정했나 | 응답 status, `/me` 응답 body |
| `Network > Status 304` | 같은 body를 다시 받아야 했나 | 로그인 상태도 유지됐나 | 인증 요청(`/me`)과 정적 파일 요청을 분리 |
| `Network > from memory cache`/`from disk cache` | 브라우저가 body를 재사용했나 | 서버 세션도 복원됐나 | session/API 요청 row를 따로 확인 |

짧게 외우면 아래 순서다.

1. `Cookies`는 저장 확인이다.
2. `Request Headers`는 전송 확인이다.
3. `200/401`은 인증 결과다.
4. `304`와 `memory cache`는 body 재사용 결과다.

## 한 번에 읽는 예시

아래 세 장면을 같은 브라우저에서 연달아 본다고 생각하면 쉽다.

```http
POST /login HTTP/1.1
Host: shop.example.com

HTTP/1.1 200 OK
Set-Cookie: JSESSIONID=abc123; Path=/; HttpOnly; Secure
```

```http
GET /me HTTP/1.1
Host: shop.example.com
Cookie: JSESSIONID=abc123
```

```http
GET /static/app.js HTTP/1.1
Host: shop.example.com

HTTP/1.1 200 OK
Cache-Control: max-age=600
ETag: "app-js-v8"
```

여기서 읽는 포인트는 세 가지다.

- 로그인 응답의 `Set-Cookie`는 브라우저 저장 규칙이다
- 다음 `/me` 요청의 `Cookie`는 서버가 session을 찾기 위한 전달 수단이다
- `app.js`의 `Cache-Control`과 `ETag`는 로그인 상태가 아니라 응답 재사용 규칙이다

즉 `/me`는 "누가 로그인했는가" 질문이고, `app.js`는 "이 파일을 다시 내려받아야 하는가" 질문이다.

## 헷갈리는 장면 한 번에 끊기

초보자가 자주 보는 장면을 한 줄로 다시 붙이면 아래와 같다.

```text
POST /login -> 200 + Set-Cookie
GET /me -> Cookie 전송 -> 200
F5 on /static/app.js -> 304 Not Modified
```

여기서 세 번째 줄 때문에 "`304`가 떴으니 로그인 상태를 서버가 기억했다"라고 읽기 쉽지만, 실제로는 질문이 둘이다.

| 장면 | 진짜 질문 | 보는 단서 |
|---|---|---|
| `Set-Cookie`가 왔다 | 브라우저가 무엇을 저장했나 | response header |
| `/me`에 `Cookie`가 붙었다 | 서버가 누구 요청인지 찾을 단서를 받았나 | request header |
| `304 Not Modified`가 떴다 | 같은 body를 다시 받아야 하나 | validator, cache header |

즉 login state와 cache reuse는 같은 "상태"처럼 들려도 서로 다른 질문에 답한다.

## 자주 하는 오해를 한 번 더 끊기

| 헷갈리는 말 | 실제로는 | 왜 초급자가 섞기 쉬운가 |
|---|---|---|
| "`cookie`가 있으니 로그인 유지죠?" | cookie는 전달 단서일 뿐, 서버 session 복원은 별도다 | 저장과 인증 성공을 한 단계로 묶어 생각하기 쉽다 |
| "`304`가 떴으니 서버가 나를 기억했죠?" | `304`는 body 재사용 신호다 | 둘 다 "이전 것을 다시 쓴다"처럼 들린다 |
| "`from memory cache`면 session도 메모리에서 유지됐죠?" | 브라우저 cache와 서버 session은 다른 층이다 | 둘 다 DevTools에 보이는 "state"라 같은 상자로 느껴진다 |
| "`stateless`면 로그인 기능을 못 만들죠?" | HTTP가 자동 기억을 안 할 뿐, cookie/session/token으로 보완한다 | stateless를 "상태 금지"로 오해하기 쉽다 |

## HTTP는 왜 Stateless인가

HTTP는 기본적으로 각 요청을 독립적으로 본다. 같은 사용자가 1초 전에 로그인했더라도, 다음 요청에 아무 단서가 없으면 서버는 그 사용자를 자동으로 알아보지 못한다.

그래서 로그인 같은 기능에는 "이 요청이 누구의 것인지 알려 주는 단서"가 따로 필요하다. 가장 흔한 단서가 cookie 안의 session id다. stateless라는 말은 "상태를 절대 못 가진다"가 아니라 "프로토콜이 자동으로 이어 주지 않는다"에 가깝다.

## 쿠키와 세션은 어떻게 이어지나

가장 흔한 session 로그인 흐름은 아래와 같다.

1. 서버가 로그인 성공 후 session store에 사용자 상태를 만든다.
2. 서버가 그 상태를 찾을 수 있는 session id를 `Set-Cookie`로 보낸다.
3. 브라우저가 다음 요청에 `Cookie` 헤더로 session id를 자동 전송한다.
4. 서버가 session id로 사용자 상태를 다시 찾는다.

즉 cookie는 운반 수단이고, session은 서버 조회 방식이다. 둘은 자주 같이 등장하지만 같은 개념은 아니다.

JWT를 쓰면 서버가 session store 대신 토큰 자체를 검증할 수 있다. 다만 JWT도 `Authorization` 헤더에 넣을 수도 있고 cookie에 넣을 수도 있으므로, "JWT냐 cookie냐"보다 "무엇을 어떤 transport에 실었나"가 더 정확한 질문이다.

## 캐시는 왜 별도 축인가

cache는 인증 상태를 보관하는 장치가 아니라 "이전 응답 body를 다시 쓸 수 있는가"를 다루는 축이다.

| 장면 | 중심 헤더/단서 | 답하는 질문 |
|---|---|---|
| session 복원 | `Cookie: JSESSIONID=...` | 이 요청이 누구 것인가 |
| JWT 검증 | `Authorization` 또는 cookie 속 JWT | 이 요청을 믿어도 되는가 |
| HTTP cache 재사용 | `Cache-Control`, `ETag`, `Last-Modified` | 이 응답 body를 다시 받아야 하는가 |

예를 들어 로그인 유지가 잘 되어도 `app.js`는 cache miss가 날 수 있고, 반대로 정적 파일이 disk cache에서 잘 재사용돼도 `/me` 요청은 session 만료로 `401`이 날 수 있다. 서로 다른 질문이기 때문이다.

## 자주 헷갈리는 포인트

- `stateless`는 cookie 금지가 아니다. HTTP가 자동 기억을 안 할 뿐, 브라우저와 서버가 추가 단서를 주고받을 수 있다.
- cookie가 있다고 곧 session은 아니다. cookie에는 session id도, JWT도, 단순 설정값도 들어갈 수 있다.
- session cookie라는 말은 "세션 인증"이 아니라 브라우저 종료 전까지만 유지되는 cookie 수명을 뜻할 때도 있다.
- `Application > Cookies`에 보이는 것과 request `Cookie` 헤더에 실제로 실린 것은 같은 체크가 아니다.
- cache는 로그인 상태 저장소가 아니다. 개인화된 `/me` 응답과 정적 `app.js` 응답은 캐시 판단 기준이 다르다.
- `304 Not Modified`는 인증 성공 신호가 아니다. 기존 캐시 body를 계속 써도 된다는 뜻이다.
- `from memory cache`나 `from disk cache`가 보여도 "서버가 나를 기억했다"는 뜻은 아니다. 그건 body 출처 신호다.

## 다음 단계 브리지

- browser가 `Set-Cookie`를 저장하고 `Cookie`를 언제 다시 보내는지부터 보고 싶으면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- `304`, `ETag`, `from disk cache`가 더 헷갈리면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- `cache 재사용`, `연결 재사용`, `로그인 유지`가 한 덩어리면 [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- login redirect, 숨은 `JSESSIONID`, 원래 URL 복귀가 섞이면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- Spring/security 쪽으로 더 깊게 가려면 [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)

## 면접에서 자주 나오는 질문

### Q. HTTP가 stateless라는 것은 무엇인가요?

이전 요청 상태를 프로토콜이 자동으로 이어 주지 않는다는 뜻이다. 그래서 로그인 상태 같은 것은 cookie, session, token 같은 별도 단서가 필요하다.

### Q. cookie와 session의 차이는 무엇인가요?

cookie는 브라우저 저장/전송 수단이고, session은 서버 상태 저장 방식이다. 보통 session id를 cookie로 전달한다.

### Q. cache는 cookie나 session과 무엇이 다른가요?

cache는 "응답 body를 다시 받을지"를 다루고, cookie/session은 "이 요청이 누구 것인지"를 다룬다. 즉 질문 자체가 다르다.

## 한 줄 정리

HTTP의 stateless는 "자동 기억 없음"이고, cookie는 브라우저 전달 수단, session은 서버 상태 저장, cache는 응답 재사용 규칙이다. 먼저 "누가 무엇을 저장하나"를 분리하면 이후 Spring auth와 browser cache 문서를 훨씬 덜 헷갈리고 읽을 수 있다.
