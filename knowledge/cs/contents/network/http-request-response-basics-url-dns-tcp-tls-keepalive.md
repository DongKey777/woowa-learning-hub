# HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive

> 한 줄 요약: 브라우저는 URL을 해석하고 DNS로 주소를 찾고 TCP/TLS로 통신 길을 만든 뒤 HTTP 요청을 보내며, 응답의 상태 코드와 `Set-Cookie`를 보고 redirect, 쿠키 저장, 연결 재사용 같은 다음 행동을 결정한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README: HTTP 요청-응답 기본 흐름](./README.md#http-요청-응답-기본-흐름)
- [Junior Backend Roadmap: 2단계 운영체제와 네트워크 기초](../../JUNIOR-BACKEND-ROADMAP.md#2단계-운영체제와-네트워크-기초)
- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- [DNS 기초](./dns-basics.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [프록시와 리버스 프록시 기초](./proxy-reverse-proxy-basics.md)
- [Spring MVC 컨트롤러 기초](../spring/spring-mvc-controller-basics.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)
- [Database First-Step Bridge](../database/database-first-step-bridge.md)
- [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)
- [SQL 읽기와 관계형 모델링 기초](../database/sql-reading-relational-modeling-primer.md)

retrieval-anchor-keywords: browser request lifecycle basics, browser to server basics, url dns tcp tls http flow, url 입력 후 무슨 일이, 브라우저 요청 응답 처음, dns lookup basics, tcp tls handshake basics, http request response basics, cookie session basics, reverse proxy basics, keep-alive basics, network to spring basics, browser to spring to database beginner ladder, spring 다음 database 뭐부터, 처음 save sql 어디서 봐요

## 핵심 개념

웹 요청은 "브라우저가 서버에 한 줄을 보낸다"로 끝나지 않는다. 초급자가 먼저 잡아야 할 그림은 `주소 해석 -> 연결 준비 -> HTTP 대화 -> 브라우저 후속 동작`이다. 여기서 쿠키는 브라우저 쪽 저장/전송 규칙이고, 세션은 서버 쪽 상태 저장 방식이며, 프록시는 그 사이에서 요청을 대신 받고 넘기는 중간 계층이다. 이 축을 분리하면 Spring 앱을 만들기 전에도 DevTools의 네트워크 탭을 읽을 수 있다.

가장 단순한 역할 분리는 아래처럼 잡으면 된다.

- 브라우저: URL 해석, DNS 조회 시작, 쿠키 저장/전송, redirect 따라가기, 화면 렌더링
- 서버/프록시: 요청 해석, 상태 코드 결정, `Set-Cookie`/`Location` 같은 응답 헤더 반환
- 네트워크 계층: TCP 연결과 TLS 암호화 같은 "통신 길" 제공

## beginner-safe 다음 사다리

이 문서를 읽은 뒤 "`브라우저 -> controller -> database` 전체 흐름이 처음이에요", "`spring 다음에 database는 뭐부터 봐요?`", "`save()`는 보이는데 SQL은 어디서 보죠?`"가 바로 붙으면 deep dive로 건너뛰지 말고 아래 3칸만 이동한다.

| 지금 막힌 말 | 다음 한 칸 | 왜 이 순서가 안전한가 |
|---|---|---|
| "`HTTP 요청이 Spring 코드로 어떻게 넘어가요?`" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | network와 MVC/DI를 한 장면으로 다시 묶어 준다 |
| "`controller` 다음 `service`/`repository`는 보이는데 DB 문서는 어디서 시작해요?" | [Database First-Step Bridge](../database/database-first-step-bridge.md) | `lock`, `failover`, `playbook`보다 먼저 `트랜잭션 -> 접근 기술 -> 인덱스` 순서를 고정한다 |
| "`save()`만 보여서 SQL이 안 보여요" | [Database First-Step Bridge](../database/database-first-step-bridge.md) -> [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | JPA/MyBatis/JDBC를 먼저 구분해야 SQL 위치를 덜 헷갈린다 |

## 한눈에 보기

| 단계 | 브라우저 쪽 행동 | 서버/프록시 쪽 행동 | 개발자가 읽어야 할 핵심 |
|---|---|---|---|
| URL 해석 | scheme, host, path, query를 나눈다 | 아직 HTTP 요청을 받지 않았다 | `https`, `shop.example.com`, `/orders/42` |
| DNS | host에 대한 IP를 찾는다 | DNS 서버가 이름 해석을 돕는다 | DNS가 느리면 요청 시작 자체가 늦다 |
| TCP/TLS | 연결을 만들고 HTTPS면 암호화를 붙인다 | 서버가 연결과 인증서를 받아준다 | `connect`, `ssl` 지연이 여기다 |
| HTTP 요청 | 메서드, 헤더, 바디를 보낸다 | 프록시/앱이 요청을 읽는다 | `GET/POST`, `Host`, `Cookie`, `Content-Type` |
| HTTP 응답 | 상태 코드, 헤더, 바디를 받는다 | 프록시/앱이 결과를 돌려준다 | `302`, `401`, `502`, `504`, `Set-Cookie` |
| 다음 행동 | 쿠키 저장, redirect, 연결 재사용, 렌더링 | 필요하면 같은 연결에서 다음 요청 대기 | 쿠키 전송과 keep-alive는 다른 개념이다 |

간단히 그리면 아래 순서다.

```text
브라우저
  -> URL 해석
  -> DNS 조회
  -> TCP 연결
  -> TLS handshake(HTTPS)
  -> HTTP request
  -> CDN / LB / reverse proxy
  -> app server
  -> HTTP response
  -> 쿠키 저장 / redirect / 화면 렌더링 / 연결 재사용
```

## URL과 DNS

URL은 "어디에 어떤 방식으로 요청할지"를 적은 주소다. 예를 들어 `https://shop.example.com/orders/42?view=summary#reviews`에서 `https`는 프로토콜, `shop.example.com`은 host, `/orders/42`는 path, `?view=summary`는 query다. `#reviews` 같은 fragment는 브라우저 내부 이동용이라 보통 서버로 가지 않는다.

브라우저는 host 이름만으로 바로 연결할 수 없으므로 먼저 DNS로 IP 주소를 찾는다. 이 단계는 HTTP보다 앞선다. 그래서 "서버가 느리다"고 느껴도 실제로는 DNS가 늦을 수 있다. DevTools에서 `dns`나 `domain lookup` 구간이 길면 애플리케이션 코드보다 앞단 문제부터 의심해야 한다.

입문자용으로 아주 짧게 자르면:

- URL: "어디로 갈지" 적는 주소
- DNS: "그 이름이 실제 어느 IP인지" 찾는 전화번호부
- HTTP: "찾아간 뒤 무슨 말을 주고받을지" 정하는 규칙

## TCP, TLS, HTTP request/response

DNS로 IP를 찾으면 브라우저는 서버와 TCP 연결을 만든다. TCP는 데이터를 순서대로 전달하려고 하고, 유실되면 재전송한다. HTTPS라면 그 위에 TLS handshake가 한 번 더 올라가서 암호화와 서버 인증서를 처리한다. 정리하면 `TCP는 길`, `TLS는 자물쇠`, `HTTP는 대화 규칙`이다.

HTTP 요청과 응답은 보통 아래처럼 읽는다.

```http
GET /orders/42 HTTP/1.1
Host: shop.example.com
Accept: text/html
Cookie: JSESSIONID=abc123
```

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Set-Cookie: recent_order=42; Path=/; HttpOnly; Secure
Cache-Control: no-cache
```

요청에서는 메서드, path, header를 보고 "무엇을 달라는지"를 읽고, 응답에서는 상태 코드, header, body를 보고 "어떻게 처리됐는지"를 읽는다. `Cookie`는 브라우저가 보내는 값이고, `Set-Cookie`는 서버가 브라우저에 저장하라고 지시하는 값이다.

처음 읽을 때는 "request가 질문, response가 답"이라고 두고 시작하면 된다.

| 구분 | request | response |
|---|---|---|
| 누가 만드나 | 브라우저/클라이언트 | 서버 또는 프록시 |
| 첫 줄에 무엇이 있나 | `GET /orders/42 HTTP/1.1` | `HTTP/1.1 200 OK` |
| 초보자가 먼저 볼 것 | 메서드, path, `Host`, `Cookie` | 상태 코드, `Set-Cookie`, `Location`, `Content-Type` |

`request`를 보고는 "무엇을 달라고 했나", `response`를 보고는 "그래서 어떻게 됐나"를 먼저 말할 수 있으면 충분하다.

## 쿠키와 세션

쿠키와 세션은 같은 말이 아니다.

| 개념 | 어디에 있나 | 역할 |
|---|---|---|
| cookie | 브라우저 | 다음 요청에 자동으로 실어 보낼 수 있는 작은 데이터 |
| session | 서버 | 로그인 사용자 상태를 저장하는 공간 |
| session id | 보통 cookie 값 | 서버의 session을 찾기 위한 열쇠 |

흔한 로그인 흐름은 이렇다. 서버가 로그인 성공 후 `Set-Cookie: JSESSIONID=...`를 응답하면 브라우저가 이를 저장한다. 이후 같은 사이트에 다시 요청할 때 브라우저는 `Cookie: JSESSIONID=...`를 자동으로 붙인다. 서버는 그 값을 보고 세션 저장소에서 사용자 상태를 찾는다. 즉 쿠키는 운반 수단이고, 세션은 서버 상태다.

## 프록시, 상태 코드, Keep-Alive

브라우저가 항상 Spring 앱에 직접 붙는다고 생각하면 실무 트래픽을 읽기 어렵다. 실제 경로는 자주 `브라우저 -> CDN/LB/reverse proxy -> app server`다. 이 중간 프록시는 TLS를 대신 끝내고, path나 host로 라우팅하고, 필요하면 자기 판단으로 응답을 돌려준다.

상태 코드는 "현재 hop이 바깥에 내보낸 결과"다. `200/201/204`는 성공, `301/302/304`는 이동이나 캐시 재사용, `400/401/403/404`는 요청 측 문제, `500/502/503/504`는 서버 측 문제다. 특히 `502 Bad Gateway`, `504 Gateway Timeout`은 프록시가 upstream 앱을 대신해 낸 응답일 수 있다.

브라우저에서 자주 먼저 읽는 상태 코드는 아래 정도다.

| 코드 | 초급자용 한 줄 의미 | 첫 확인 포인트 |
|---|---|---|
| `200 OK` | 요청이 정상 처리됐다 | 응답 body, 화면 반영 |
| `302 Found` | 다른 URL로 한 번 더 가라 | `Location`, 로그인 redirect |
| `303 See Other` | `POST` 결과 화면은 다른 URL의 `GET`으로 다시 봐라 | `Location`, PRG, 새로고침 대상 |
| `401 Unauthorized` | 인증이 없거나 실패했다 | 로그인 상태, 토큰, 쿠키 |
| `403 Forbidden` | 누군지는 알지만 허용되지 않는다 | 권한, 역할 |
| `404 Not Found` | 경로나 자원이 없다 | path, id |
| `502 Bad Gateway` | 프록시가 upstream 응답을 정상 처리하지 못했다 | 프록시, upstream 연결 |
| `504 Gateway Timeout` | 프록시가 upstream을 기다리다 timeout 났다 | timeout, 느린 서버 |

`keep-alive`는 로그인 상태 유지가 아니라 연결 재사용이다. 한 요청이 끝난 뒤 같은 TCP 연결을 다시 써서 다음 요청 비용을 줄이는 개념이다. 쿠키는 사용자 상태 전달, 세션은 서버 상태 저장, keep-alive는 네트워크 연결 재사용이므로 서로 다른 층이다. 이 셋이 자꾸 섞이면 [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)부터 먼저 보면 된다.

특히 아래 둘을 섞지 않는 것이 중요하다.

| 용어 | 뜻 | 초급자용 기억법 |
|---|---|---|
| HTTP keep-alive | 요청이 끝난 뒤 같은 연결을 다음 HTTP 요청에도 재사용 | "다음 주문도 같은 창구에서 처리" |
| TCP keepalive | 아주 한가한 연결이 아직 살아 있는지 OS 수준에서 확인 | "창구가 아직 열려 있는지 생존 확인" |

초급 문맥에서 "브라우저 keep-alive"라고 하면 대부분 HTTP 연결 재사용을 말한다. 로그인 유지나 세션 timeout을 뜻하지 않는다.

## redirect와 auth failure 첫 구분

redirect와 auth failure를 한 표로 고정해 두면 DevTools를 볼 때 덜 섞인다.

| 장면 | 브라우저가 주로 하는 다음 행동 | 초급자용 첫 해석 |
|---|---|---|
| `302 Found` + `Location: /login` | 다른 URL로 이동한다 | page navigation redirect일 가능성이 크다 |
| `303 See Other` + `Location: /orders/42` | `POST` 뒤 결과 화면 `GET`으로 이동한다 | PRG 흐름이다 |
| raw `401 Unauthorized` | 자동 이동 없이 실패를 surface한다 | API나 보호 자원 인증 실패부터 본다 |
| raw `403 Forbidden` | 자동 이동 없이 거절한다 | 인증은 됐지만 권한이 부족하다 |

## 흔한 오해와 함정

- `https`는 HTTP와 별개 새 프로토콜이 아니라 `HTTP over TLS`다.
- `#fragment`는 같은 URL 문자열에 보여도 보통 서버로 전송되지 않는다.
- 쿠키가 있다고 로그인 상태가 자동으로 이해되는 것은 아니다. 서버가 그 값을 어떻게 해석하는지가 핵심이다.
- `401`은 인증이 없거나 실패한 상태이고, `403`은 인증과 별개로 금지된 상태다.
- `502`나 `504`를 보면 앱 코드만 볼 것이 아니라 프록시와 upstream 연결도 같이 봐야 한다.
- keep-alive와 session timeout은 다른 문제다. 하나는 연결 수명이고, 다른 하나는 로그인 상태 수명이다.
- HTTP keep-alive와 TCP keepalive도 다른 말이다. 초급 문서에서 keep-alive가 나오면 먼저 "연결 재사용"인지 확인한다.

## 실무에서 쓰는 모습

브라우저 네트워크 탭에서 아래 흐름을 읽을 수 있으면 입문 단계 목표는 거의 달성한 것이다.

```http
POST /login HTTP/1.1
Host: shop.example.com
Content-Type: application/json

{"username":"neo","password":"secret"}
```

```http
HTTP/1.1 302 Found
Location: /orders
Set-Cookie: JSESSIONID=abc123; Path=/; HttpOnly; Secure
```

```http
GET /orders HTTP/1.1
Host: shop.example.com
Cookie: JSESSIONID=abc123
```

여기서 읽을 포인트는 세 가지다. 첫째, 로그인 응답이 `302`면 브라우저가 곧바로 다음 URL로 이동한다. 둘째, `Set-Cookie`가 있으면 브라우저가 저장하고 다음 요청에서 `Cookie`로 되돌려 보낸다. 셋째, `/orders` 요청이 `504`로 끝났다면 Spring 컨트롤러 로직만이 아니라 앞단 프록시 timeout도 같이 봐야 한다. 이 습관이 잡히면 이후 Spring MVC 요청 생명주기 문서를 읽을 때도 네트워크와 프레임워크 경계가 분리된다.

폼 제출 뒤 결과 화면을 보여 주는 브라우저 흐름은 PRG로 보면 더 깔끔하다.

```http
POST /orders HTTP/1.1
Content-Type: application/x-www-form-urlencoded

item=cola&qty=2
```

```http
HTTP/1.1 303 See Other
Location: /orders/42
```

```http
GET /orders/42 HTTP/1.1
Cookie: JSESSIONID=abc123
```

이 장면에서 읽을 포인트는 네 가지다.

1. 상태를 바꾸는 요청은 `POST /orders`다.
2. `303`은 "결과 화면은 다른 URL의 `GET`으로 다시 봐라"라는 뜻이다.
3. 그래서 새로고침 대상이 `POST`가 아니라 `GET /orders/42`가 된다.
4. 로그인 여부가 없으면 같은 흐름에서도 raw `401`, login page redirect `302`, 권한 거절 `403`이 각각 다르게 나타날 수 있다.

## 초급자용 다음 한 걸음

처음 백엔드로 넘어갈 때는 바로 deep dive로 가지 말고 `network -> spring -> database` 순서로 한 칸씩만 이동하는 편이 안전하다.

| 지금 막힌 말 | 먼저 갈 primer | 그다음 한 걸음 | deep dive는 나중에 |
|---|---|---|---|
| "브라우저 요청이 Spring 코드 어디로 들어가요?" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Spring MVC 컨트롤러 기초](../spring/spring-mvc-controller-basics.md) | [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md) |
| "컨트롤러 다음에 DB 저장은 어디서 일어나요?" | [Spring MVC 컨트롤러 기초](../spring/spring-mvc-controller-basics.md) | [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | JPA flush, mapper XML, SQL 튜닝 |
| "`save()`가 보이는데 commit은 어디서 결정돼요?" | [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | [트랜잭션 기초](../database/transaction-basics.md) | isolation / locking / propagation |

초급자가 "`브라우저 -> controller -> database`가 한 번에 안 그려져요", "`save()`는 보이는데 그 전에 뭐가 와요?"라고 묻는다면 아래 3칸만 먼저 고정하면 된다.

`HTTP 요청-응답 기본 흐름 -> Spring 요청 파이프라인과 Bean Container 기초 -> Database First-Step Bridge`

## 더 깊이 가려면

- 학습 흐름으로 돌아가려면 [Network README: HTTP 요청-응답 기본 흐름](./README.md#http-요청-응답-기본-흐름), [Junior Backend Roadmap: 2단계 운영체제와 네트워크 기초](../../JUNIOR-BACKEND-ROADMAP.md#2단계-운영체제와-네트워크-기초)를 먼저 본다.
- 브라우저 waterfall에서 `dns`/`connect`/`ssl`/`waiting`을 바로 읽고 싶다면 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- 쿠키와 세션을 브라우저 기준으로 더 보고 싶다면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- 프록시가 어디서 응답을 만들어내는지 더 보고 싶다면 [프록시와 리버스 프록시 기초](./proxy-reverse-proxy-basics.md), [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
- 상태 코드와 request/response를 더 잘 읽고 싶다면 [HTTP 상태 코드 기초](./http-status-codes-basics.md), [HTTP 요청/응답 헤더 기초](./http-request-response-headers-basics.md)
- 브라우저 form submit과 redirect 후 `GET` 흐름을 더 보고 싶다면 [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- Spring 코드로 처음 이어 가려면 [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) -> [Spring MVC 컨트롤러 기초](../spring/spring-mvc-controller-basics.md) 순으로 간다.
- `DispatcherServlet`, binding, 예외 처리 전체 흐름까지 펼치려면 그다음에 [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)로 간다.
- Spring 다음에 DB 코드 독해를 처음 붙일 때는 [Database First-Step Bridge](../database/database-first-step-bridge.md)로 넘어가 `트랜잭션 -> 접근 기술 -> 인덱스` 순서만 먼저 잡는다.
- DB 조회 문서가 왜 그런 SQL 모양이 되는지 미리 잡으려면 [SQL 읽기와 관계형 모델링 기초](../database/sql-reading-relational-modeling-primer.md)를 먼저 본다.

## 면접/시니어 질문 미리보기

**Q. 브라우저 주소창에 URL을 입력하면 HTTP 요청이 바로 나가나요?**
아니다. URL 해석과 DNS 조회가 먼저 오고, 그다음 TCP 연결과 HTTPS라면 TLS handshake가 끝난 뒤에 HTTP 요청이 전송된다.

**Q. 쿠키와 세션의 차이를 설명해 주세요.**
쿠키는 브라우저가 저장하고 전송하는 데이터고, 세션은 서버가 사용자 상태를 저장하는 방식이다. 보통 세션 ID가 쿠키에 담겨 전달된다.

**Q. `502`와 `504`는 언제 자주 보나요?**
브라우저와 앱 서버 사이에 프록시나 게이트웨이가 있을 때 자주 보인다. 프록시가 upstream 연결 실패나 timeout을 바깥에 표현할 때 쓰는 대표 코드다.

## 한 줄 정리

웹 요청은 `URL -> DNS -> TCP/TLS -> HTTP -> 쿠키/세션/프록시 해석 -> 다음 요청 준비`의 흐름으로 읽어야 하고, 이 축이 서면 Spring 앱을 만들기 전에도 브라우저 트래픽을 단계별로 설명할 수 있다.
