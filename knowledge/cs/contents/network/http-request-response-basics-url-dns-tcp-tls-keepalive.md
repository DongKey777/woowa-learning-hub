# HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive

> 한 줄 요약: 브라우저는 URL을 해석하고 DNS로 주소를 찾고 TCP/TLS로 통신 길을 만든 뒤 HTTP 요청을 보내며, 응답의 상태 코드와 `Set-Cookie`를 보고 다음 요청 동작을 바꾼다. 실제 서비스에서는 이 흐름 사이에 CDN, 로드밸런서, 리버스 프록시가 끼어들 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README: HTTP 요청-응답 기본 흐름](./README.md#http-요청-응답-기본-흐름)
- [Junior Backend Roadmap: 2단계 운영체제와 네트워크 기초](../../JUNIOR-BACKEND-ROADMAP.md#2단계-운영체제와-네트워크-기초)
- [DNS 기초](./dns-basics.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [프록시와 리버스 프록시 기초](./proxy-reverse-proxy-basics.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)
- [SQL 읽기와 관계형 모델링 기초](../database/sql-reading-relational-modeling-primer.md)

retrieval-anchor-keywords: browser request lifecycle basics, browser to server basics, url dns tcp tls http flow, url 입력 후 무슨 일이, dns lookup basics, tcp tls handshake basics, http request response basics, http status code basics, cookie session basics, set-cookie cookie flow, reverse proxy basics, keep-alive basics, 401 vs 403 basics, 502 vs 504 basics, network primer return path, network readme http flow entrypoint, network to spring request pipeline bridge, network to database sql primer bridge, beginner backend lane handoff

## 핵심 개념

웹 요청은 "브라우저가 서버에 한 줄을 보낸다"로 끝나지 않는다. 초급자가 먼저 잡아야 할 그림은 `주소 해석 -> 연결 준비 -> HTTP 대화 -> 브라우저 후속 동작`이다. 여기서 쿠키는 브라우저 쪽 저장/전송 규칙이고, 세션은 서버 쪽 상태 저장 방식이며, 프록시는 그 사이에서 요청을 대신 받고 넘기는 중간 계층이다. 이 축을 분리하면 Spring 앱을 만들기 전에도 DevTools의 네트워크 탭을 읽을 수 있다.

## 한눈에 보기

| 단계 | 브라우저가 하는 일 | 개발자가 읽어야 할 핵심 |
|---|---|---|
| URL 해석 | scheme, host, path, query를 나눈다 | `https`, `shop.example.com`, `/orders/42` |
| DNS | host를 IP로 바꾼다 | DNS가 느리면 요청 시작 자체가 늦다 |
| TCP/TLS | 연결을 만들고 HTTPS면 암호화를 붙인다 | `connect`, `ssl` 지연이 여기다 |
| HTTP 요청 | 메서드, 헤더, 바디를 보낸다 | `GET/POST`, `Host`, `Cookie`, `Content-Type` |
| 프록시/앱 처리 | 프록시가 전달하거나 직접 응답한다 | `302`, `401`, `502`, `504`는 프록시가 낼 수도 있다 |
| HTTP 응답 | 상태 코드, 헤더, 바디를 받는다 | `Set-Cookie`, `Location`, `Cache-Control` |
| 다음 요청 준비 | 쿠키 저장, 리다이렉트, 연결 재사용 | 쿠키 전송과 keep-alive는 다른 개념이다 |

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

`keep-alive`는 로그인 상태 유지가 아니라 연결 재사용이다. 한 요청이 끝난 뒤 같은 TCP 연결을 다시 써서 다음 요청 비용을 줄이는 개념이다. 쿠키는 사용자 상태 전달, 세션은 서버 상태 저장, keep-alive는 네트워크 연결 재사용이므로 서로 다른 층이다.

## 흔한 오해와 함정

- `https`는 HTTP와 별개 새 프로토콜이 아니라 `HTTP over TLS`다.
- `#fragment`는 같은 URL 문자열에 보여도 보통 서버로 전송되지 않는다.
- 쿠키가 있다고 로그인 상태가 자동으로 이해되는 것은 아니다. 서버가 그 값을 어떻게 해석하는지가 핵심이다.
- `401`은 인증이 없거나 실패한 상태이고, `403`은 인증과 별개로 금지된 상태다.
- `502`나 `504`를 보면 앱 코드만 볼 것이 아니라 프록시와 upstream 연결도 같이 봐야 한다.
- keep-alive와 session timeout은 다른 문제다. 하나는 연결 수명이고, 다른 하나는 로그인 상태 수명이다.

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

## 더 깊이 가려면

- 학습 흐름으로 돌아가려면 [Network README: HTTP 요청-응답 기본 흐름](./README.md#http-요청-응답-기본-흐름), [Junior Backend Roadmap: 2단계 운영체제와 네트워크 기초](../../JUNIOR-BACKEND-ROADMAP.md#2단계-운영체제와-네트워크-기초)를 먼저 본다.
- DNS가 느린 첫 요청을 더 보고 싶다면 [DNS 기초](./dns-basics.md), [DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md)
- 쿠키와 세션을 브라우저 기준으로 더 보고 싶다면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- 프록시가 어디서 응답을 만들어내는지 더 보고 싶다면 [프록시와 리버스 프록시 기초](./proxy-reverse-proxy-basics.md), [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
- 상태 코드와 request/response를 더 잘 읽고 싶다면 [HTTP 상태 코드 기초](./http-status-codes-basics.md), [HTTP 요청/응답 헤더 기초](./http-request-response-headers-basics.md)
- Spring 코드로 이어 가려면 [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
- 프레임워크 전체 그림으로 바로 붙이려면 [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)로 간다.
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
