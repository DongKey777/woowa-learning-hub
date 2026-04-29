# HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문

> 한 줄 요약: `cache reuse`, `connection reuse`, `session persistence`는 모두 "이전 것을 다시 쓴다"처럼 들리지만, 각각 다시 쓰는 대상이 응답 본문, TCP 연결, 로그인 상태로 다르다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- [network 카테고리 인덱스](./README.md)
- [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)

retrieval-anchor-keywords: http cache vs keep-alive vs session, cache reuse vs connection reuse, session persistence basics, keep-alive 로그인 유지 아니에요, 304 vs cookie login state, 브라우저가 뭘 다시 쓰나요, http cache body reuse, connection reuse same tcp socket, session persistence cookie session id, cache랑 keep-alive 차이, session이랑 cache 차이, beginner http confusion

## 핵심 개념

초급자가 가장 많이 섞는 이유는 세 단어가 모두 "전에 있던 걸 다시 쓴다"처럼 들리기 때문이다.

- cache reuse: **이전 응답 본문**을 다시 쓴다
- connection reuse: **이전에 열어 둔 TCP 연결**을 다시 쓴다
- session persistence: **이전 로그인 상태**를 다음 요청에서도 이어 간다

즉 셋은 같은 층위의 기능이 아니다.

- cache는 "body를 다시 받을까"
- keep-alive는 "길을 다시 만들까"
- session persistence는 "이 사용자가 아까 그 사용자 맞나"

이렇게 질문 자체가 다르다고 잡으면 첫 혼동이 많이 줄어든다.

## 한눈에 보기

| 구분 | 다시 쓰는 대상 | 브라우저에서 자주 보이는 단서 | 대표 신호 |
|---|---|---|---|
| cache reuse | 응답 body와 validator | `memory cache`, `disk cache`, `304` | `Cache-Control`, `ETag`, `Last-Modified` |
| connection reuse | 이미 열린 TCP 연결 | 같은 사이트 요청이 새 handshake 없이 이어짐 | `keep-alive`, HTTP/2/H3 연결 재사용 |
| session persistence | 로그인/사용자 상태 | 다음 요청에도 `Cookie`나 token이 실림 | `Set-Cookie`, `Cookie`, session id, `Authorization` |

아주 짧게 기억하면 아래 한 줄이면 된다.

- cache는 **응답 재사용**
- keep-alive는 **연결 재사용**
- session은 **사용자 상태 지속**

## 한 요청 흐름에서 세 가지를 분리해 보기

같은 브라우저 장면에서도 세 가지가 동시에 보일 수 있다.

```text
1. GET /login-page
2. 서버가 HTML과 app.js를 응답
3. 브라우저가 app.js를 cache에 저장
4. 로그인 성공 응답이 Set-Cookie: JSESSIONID=abc 를 보냄
5. 브라우저가 다음 /me 요청에 Cookie: JSESSIONID=abc 를 자동 전송
6. 이 /me 요청이 기존 TCP 연결로 나가면 connection reuse
7. 나중에 app.js를 다시 열었을 때 304 또는 memory cache가 보이면 cache reuse
```

여기서 각각의 질문은 따로 해야 한다.

| 장면 | 먼저 해야 할 질문 | 답이 가리키는 축 |
|---|---|---|
| `304 Not Modified`가 보임 | body를 다시 받지 않았나 | cache reuse |
| 로그인 후 다음 요청에도 `Cookie: JSESSIONID=...`가 보임 | 같은 사용자 상태가 이어지나 | session persistence |
| 두 요청 사이에 새 `connect` 비용이 거의 없음 | 같은 연결을 재사용했나 | connection reuse |

중요한 점은 하나가 참이라고 나머지도 참이 되는 게 아니라는 것이다.

- cache hit가 나도 로그인은 풀릴 수 있다
- 세션이 유지돼도 매 요청이 새 연결일 수 있다
- 같은 연결을 재사용해도 응답 body는 캐시하지 않을 수 있다

## 왜 초급자가 자주 헷갈리나

특히 아래 세 문장이 비슷해 보여서 자주 섞인다.

| 흔한 말 | 실제 뜻 |
|---|---|
| "브라우저가 전에 받은 걸 다시 쓴다" | cache일 수도 있고 cookie/session일 수도 있다. 무엇을 다시 쓰는지 먼저 말해야 한다 |
| "keep-alive라서 로그인 유지된다" | 아니다. keep-alive는 연결을 덜 끊는 것이지 로그인 상태를 저장하지 않는다 |
| "세션이 있으니 304가 뜬다" | 아니다. `304`는 캐시 재검증 결과고, 세션 유무와 직접 같은 개념이 아니다 |

초급자용 비유로 자르면:

- cache reuse: **전에 받아 둔 문서 사본을 다시 꺼내 본다**
- connection reuse: **같은 창구를 계속 쓴다**
- session persistence: **창구 직원이 "아까 그 손님"이라고 알아본다**

## 흔한 오해와 함정

- `keep-alive = 로그인 유지`가 아니다. 로그인 유지 여부는 cookie/session/token 설계가 결정한다.
- `304 = 세션이 살아 있다`가 아니다. `304`는 "기존 body를 계속 써도 된다"는 캐시 신호다.
- `JSESSIONID` cookie가 보인다고 cache가 된 것이 아니다. 그것은 사용자 상태를 이어 가는 단서다.
- `memory cache`가 보인다고 같은 TCP 연결을 썼다고 단정할 수 없다. body 재사용과 연결 재사용은 별도다.
- 세션이 유지돼도 `Cache-Control: no-store` 응답이면 body는 캐시하지 않을 수 있다.

## 실무에서 쓰는 모습

쇼핑몰 페이지를 예로 들면 가장 쉽게 분리된다.

1. 브라우저가 `/products/10`을 열고 `app.js`를 받는다.
2. `app.js`는 다음 새로고침에서 `304`나 `memory cache`로 보일 수 있다.
3. 사용자가 로그인하면 서버는 `Set-Cookie: JSESSIONID=abc...`를 보낸다.
4. 이후 `/me` 요청마다 브라우저는 `Cookie: JSESSIONID=abc...`를 보낸다.
5. 이 요청들이 같은 TCP 연결로 이어지면 keep-alive 덕분에 handshake 비용이 줄어든다.

이 장면을 한 줄씩 해석하면:

- `app.js`의 `304`는 cache 이야기
- `JSESSIONID`는 session persistence 이야기
- 새 `connect`가 없거나 같은 연결이 이어지는 것은 connection reuse 이야기

## 더 깊이 가려면

- `304`, `ETag`, `Cache-Control` 흐름을 더 자세히 보려면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- 브라우저가 `Set-Cookie`를 저장하고 다음 요청에 `Cookie`를 붙이는 흐름은 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- keep-alive를 먼저 기초 수준에서 분리하고 싶다면 [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- 운영형 keepalive 튜닝이나 heartbeat 차이는 그다음에 [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
- session을 서버 저장 방식 관점에서 비교하려면 [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)

## 한 줄 정리

`cache reuse`는 응답, `connection reuse`는 연결, `session persistence`는 사용자 상태를 다시 쓰는 것이므로 같은 "재사용"이라는 말로 묶으면 안 된다.
