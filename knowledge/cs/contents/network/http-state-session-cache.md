# HTTP의 무상태성과 쿠키, 세션, 캐시

> 한 줄 요약: `stateless`, `cookie`, `session`, `cache`는 모두 "상태"와 관련 있지만 같은 층위의 개념은 아니다. 이 문서는 브라우저 저장, 서버 저장, 응답 재사용을 한 번에 분리해 보는 beginner primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README](./README.md#http의-무상태성과-쿠키-세션-캐시)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)

retrieval-anchor-keywords: http stateless, cookie, session, jwt, http cache, set-cookie, cookie header, session id, browser state, browser cookie storage flow, jwt header vs cookie, personalization cache, login state, beginner auth bridge, why login state is kept

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
- cache는 로그인 상태 저장소가 아니다. 개인화된 `/me` 응답과 정적 `app.js` 응답은 캐시 판단 기준이 다르다.
- `304 Not Modified`는 인증 성공 신호가 아니다. 기존 캐시 body를 계속 써도 된다는 뜻이다.

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
