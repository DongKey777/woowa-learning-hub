# HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive

**난이도: 🟢 Beginner**

> 브라우저 주소창에 URL을 입력한 뒤 서버 응답을 받아 화면에 그리기까지의 흐름을 한 번에 잡는 입문용 정리

> 관련 문서:
> - [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
> - [DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [HTTP Keep-Alive Timeout Mismatch, Deeper Cases](./http-keepalive-timeout-mismatch-deeper-cases.md)
> - [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)

retrieval-anchor-keywords: HTTP request response basics, URL DNS TCP TLS flow, browser server basics, browser request lifecycle, HTTP status code basics, keep-alive basics, HTTP request headers, HTTP response headers, HTTPS handshake, URL to response, DNS lookup, TCP handshake, TLS handshake, connection reuse

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [한 번에 보는 전체 흐름](#한-번에-보는-전체-흐름)
- [URL은 무엇을 담고 있나](#url은-무엇을-담고-있나)
- [DNS: 도메인을 IP로 바꾸는 단계](#dns-도메인을-ip로-바꾸는-단계)
- [TCP와 TLS는 각각 무엇을 하나](#tcp와-tls는-각각-무엇을-하나)
- [HTTP Request는 어떻게 생겼나](#http-request는-어떻게-생겼나)
- [HTTP Response는 어떻게 생겼나](#http-response는-어떻게-생겼나)
- [상태 코드는 무엇을 말하나](#상태-코드는-무엇을-말하나)
- [Keep-Alive와 연결 재사용](#keep-alive와-연결-재사용)
- [브라우저와 서버는 각자 무엇을 하나](#브라우저와-서버는-각자-무엇을-하나)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

백엔드 개발자는 "브라우저가 서버에 요청한다"를 넘어서,

- URL에서 무엇을 보고
- DNS가 왜 필요한지
- TCP와 TLS가 각각 무슨 역할인지
- HTTP 요청과 응답이 어떤 모양인지
- 상태 코드와 keep-alive가 무엇을 의미하는지

를 설명할 수 있어야 한다.

이 흐름을 이해하면 브라우저와 서버 사이에서 어떤 단계가 느리거나 실패했는지 더 쉽게 나눠서 볼 수 있다.

### Retrieval Anchors

- `HTTP request response basics`
- `URL DNS TCP TLS flow`
- `browser server basics`
- `HTTP status code basics`
- `keep-alive basics`
- `HTTP request headers`
- `HTTP response headers`
- `connection reuse`

---

## 한 번에 보는 전체 흐름

브라우저에서 `https://shop.example.com/products/42?view=summary`를 입력했을 때의 큰 흐름은 보통 아래와 같다.

```text
1. 브라우저가 URL을 해석한다
2. DNS로 shop.example.com의 IP 주소를 찾는다
3. 서버와 TCP 연결을 맺는다
4. HTTPS라면 TLS handshake로 암호화 채널을 만든다
5. HTTP request를 전송한다
6. 서버가 request를 처리하고 HTTP response를 돌려준다
7. 브라우저가 status, header, body를 해석한다
8. HTML/CSS/JS/이미지 등 추가 요청을 보내고 화면을 렌더링한다
```

핵심은 **HTTP만 있는 것이 아니라, 그 전에 DNS와 TCP/TLS가 먼저 준비되어야 한다**는 점이다.

---

## URL은 무엇을 담고 있나

URL은 브라우저가 "어디에, 어떤 방식으로" 접근할지 알려주는 주소다.

예:

```text
https://shop.example.com:443/products/42?view=summary#reviews
```

각 부분은 보통 이렇게 읽는다.

- `https`
  - 어떤 스킴을 쓸지 정한다
  - `https`면 HTTP를 TLS 위에서 보낸다는 뜻이다
- `shop.example.com`
  - 접속할 호스트 이름이다
  - DNS 조회 대상이 된다
- `443`
  - 포트 번호다
  - HTTPS 기본 포트라 보통 생략된다
- `/products/42`
  - 서버 안에서 원하는 리소스 경로다
- `?view=summary`
  - query string이다
  - 추가 조건이나 옵션을 전달할 때 쓴다
- `#reviews`
  - fragment다
  - 보통 브라우저 내부 이동용이고 서버로 그대로 가지는 않는다

즉 URL은 단순 문자열이 아니라, **어느 서버에 어떤 리소스를 어떤 프로토콜로 요청할지 정하는 정보 묶음**이다.

---

## DNS: 도메인을 IP로 바꾸는 단계

브라우저는 `shop.example.com` 같은 이름을 그대로 네트워크에 보낼 수 없다.  
실제로 접속하려면 해당 이름에 대응하는 IP 주소가 필요하다.

그래서 DNS가 필요하다.

흐름을 단순화하면 보통 이렇다.

1. 브라우저와 OS가 먼저 캐시된 결과가 있는지 본다
2. 없으면 DNS resolver에 질의한다
3. resolver가 최종적으로 IP 주소를 찾아 응답한다
4. 브라우저는 그 IP 주소로 연결을 시도한다

중요한 점:

- DNS는 **HTTP보다 먼저** 일어난다
- DNS가 느리면 HTTP request도 늦어진다
- 도메인 이름은 사람이 읽기 쉽고, IP 주소는 실제 연결에 쓰인다

입문 단계에서는 "도메인을 IP로 바꾸는 전화번호부" 정도로 이해해도 괜찮다.  
운영 관점의 TTL, 캐시 층, 전파 지연은 [DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md)에서 더 깊게 볼 수 있다.

---

## TCP와 TLS는 각각 무엇을 하나

### TCP

TCP는 브라우저와 서버가 **신뢰성 있게 데이터를 주고받도록 연결을 만드는 전송 계층 프로토콜**다.

HTTP/1.1과 HTTP/2는 보통 TCP 위에서 동작한다.

입문 수준에서 기억할 핵심:

- 순서대로 전달하려고 한다
- 중간에 유실되면 재전송한다
- 연결을 맺고 끊는 과정이 있다

즉 HTTP message는 그냥 허공에 날아가는 게 아니라, 보통 TCP 연결 위에서 전달된다.

### TLS

HTTPS에서는 TCP 연결 뒤에 TLS handshake가 추가된다.  
TLS는 통신 내용을 암호화하고, "내가 접속한 서버가 맞는지"를 인증서로 확인하는 계층이다.

쉽게 나누면:

- TCP: 길을 만든다
- TLS: 그 길 위의 대화를 암호화한다
- HTTP: 그 길 위에서 request/response 규칙으로 대화한다

그래서 `HTTPS = HTTP + TLS`라고 이해할 수 있다.

---

## HTTP Request는 어떻게 생겼나

HTTP request는 보통

- 시작줄(start line)
- header
- body

로 생각하면 이해하기 쉽다.

예:

```http
GET /products/42?view=summary HTTP/1.1
Host: shop.example.com
Accept: text/html
Cookie: session=abc123
Connection: keep-alive

```

이 요청이 말하는 바:

- `GET`
  - 조회 목적의 메서드다
- `/products/42?view=summary`
  - 어떤 리소스를 원하는지
- `HTTP/1.1`
  - 어떤 HTTP 버전 규칙을 따르는지
- `Host`
  - 어떤 호스트로 보낸 요청인지
- `Accept`
  - 어떤 응답 형식을 선호하는지
- `Cookie`
  - 브라우저가 저장 중인 상태 정보를 함께 보낼 수 있다
- `Connection: keep-alive`
  - HTTP/1.1에서 연결 재사용 의도를 나타내는 대표적 예다

본문이 필요한 요청은 body가 함께 간다.

```http
POST /orders HTTP/1.1
Host: shop.example.com
Content-Type: application/json
Content-Length: 39

{"productId":42,"quantity":1}
```

즉 request는 "무엇을 원하나?"와 "추가 메타데이터는 무엇인가?"를 담고 있다.

---

## HTTP Response는 어떻게 생겼나

HTTP response도 구조는 비슷하다.

- 상태줄(status line)
- header
- body

예:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 1256
Cache-Control: no-cache
Set-Cookie: session=abc123; HttpOnly; Secure
Connection: keep-alive

<html>...</html>
```

이 응답이 말하는 바:

- `200 OK`
  - 요청이 정상 처리되었다
- `Content-Type`
  - body 형식이 무엇인지 알려준다
- `Content-Length`
  - body 길이를 알려준다
- `Cache-Control`
  - 브라우저나 중간 캐시가 어떻게 다룰지 정한다
- `Set-Cookie`
  - 브라우저에 쿠키 저장을 지시한다

body는 HTML일 수도 있고, JSON일 수도 있고, 이미지 바이트일 수도 있다.

브라우저는 response를 받은 뒤:

- HTML이면 파싱하고
- CSS/JS/이미지 참조를 발견하면 추가 요청을 보내고
- JSON이면 주로 JavaScript 코드가 데이터를 사용한다

---

## 상태 코드는 무엇을 말하나

상태 코드는 "요청이 어떤 결과로 끝났는지"를 숫자로 알려준다.

큰 분류는 다음처럼 이해하면 된다.

| 범위 | 의미 | 대표 예시 |
|---|---|---|
| `1xx` | 추가 진행 중 | `101 Switching Protocols` |
| `2xx` | 성공 | `200 OK`, `201 Created`, `204 No Content` |
| `3xx` | 다른 위치/캐시 재사용 안내 | `301 Moved Permanently`, `302 Found`, `304 Not Modified` |
| `4xx` | 클라이언트 쪽 요청 문제 | `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found` |
| `5xx` | 서버 쪽 처리 문제 | `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout` |

입문 단계에서 자주 보는 코드는 아래 정도는 바로 설명할 수 있으면 좋다.

- `200 OK`
  - 정상 성공
- `201 Created`
  - 새 리소스 생성 성공
- `204 No Content`
  - 성공했지만 body는 없음
- `301` / `302`
  - 다른 위치로 이동
- `304 Not Modified`
  - 캐시 재사용 가능
- `400 Bad Request`
  - 요청 형식이 잘못됨
- `401 Unauthorized`
  - 인증이 필요하거나 인증 정보가 유효하지 않음
- `403 Forbidden`
  - 인증과 별개로 접근이 금지됨
- `404 Not Found`
  - 대상 리소스를 찾지 못함
- `500 Internal Server Error`
  - 서버 내부 오류
- `502` / `504`
  - 프록시/게이트웨이 환경에서 자주 보는 upstream 계열 오류

상태 코드는 "누가 잘못했는가"의 최종 진실이라기보다, **현재 hop이 바깥에 어떻게 표현했는가**를 보여 주는 값이라는 점도 함께 기억하면 좋다.

---

## Keep-Alive와 연결 재사용

keep-alive는 매 요청마다 연결을 새로 만들지 않고 **기존 연결을 재사용**하려는 개념이다.

왜 중요할까?

- TCP 연결을 새로 맺는 비용을 줄인다
- HTTPS라면 TLS handshake 비용도 줄일 수 있다
- 여러 요청을 더 빠르게 처리할 수 있다

입문 관점에서는 아래 정도를 기억하면 충분하다.

- HTTP/1.1에서는 연결 재사용이 기본 동작에 가깝다
- HTTP/2와 HTTP/3도 연결 재사용 자체는 매우 중요하지만, `Connection: keep-alive` 헤더를 같은 방식으로 쓰는 것은 아니다
- 오래 idle 상태였던 연결은 중간 프록시나 서버가 이미 닫았을 수 있다
- 그래서 "가끔 첫 요청만 실패" 같은 현상이 생기기도 한다

중요한 구분:

- `HTTP keep-alive`
  - 요청/응답 연결을 재사용하는 개념
- `TCP keepalive`
  - 오랫동안 조용한 소켓이 살아 있는지 probe를 보내는 OS 레벨 기능

이 둘은 이름이 비슷하지만 같은 것은 아니다.

더 깊은 운영 이슈는 [HTTP Keep-Alive Timeout Mismatch, Deeper Cases](./http-keepalive-timeout-mismatch-deeper-cases.md)와 [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)로 이어서 보면 된다.

---

## 브라우저와 서버는 각자 무엇을 하나

### 브라우저 쪽

브라우저는 보통 다음 일을 한다.

- URL 해석
- DNS 조회
- 연결 생성
- 쿠키/캐시 적용
- HTTP request 전송
- response 해석
- HTML 파싱과 렌더링
- CSS, JS, 이미지에 대한 추가 요청 생성

즉 브라우저는 단순히 "문자열을 보내는 프로그램"이 아니라, 네트워크와 렌더링을 함께 담당하는 클라이언트다.

### 서버 쪽

서버는 보통 다음 일을 한다.

- 포트에서 요청 대기
- TLS 종료 또는 프록시 뒤 요청 수신
- 라우팅
- 인증/인가
- 비즈니스 로직 실행
- DB/캐시 호출
- 상태 코드, header, body를 담아 response 반환

실무에서는 브라우저와 애플리케이션 서버 사이에:

- CDN
- 로드밸런서
- 리버스 프록시
- API Gateway

같은 중간 계층이 들어갈 수 있다.  
그래도 입문적으로는 "브라우저가 요청하고 서버가 응답한다"는 큰 그림부터 잡는 것이 먼저다.

---

## 면접에서 자주 나오는 질문

### Q. 브라우저 주소창에 URL을 입력하면 가장 먼저 무슨 일이 일어나나요?

- 브라우저가 URL을 해석하고, 필요한 경우 DNS로 도메인을 IP로 바꾼 뒤, TCP 연결과 HTTPS라면 TLS handshake를 거쳐 HTTP request를 보낸다고 설명하면 된다.

### Q. HTTP와 HTTPS 차이는 무엇인가요?

- HTTP는 요청/응답 규칙이고, HTTPS는 그 HTTP를 TLS 위에서 암호화해 보내는 방식이라고 설명하면 된다.

### Q. 상태 코드 `401`과 `403` 차이는 무엇인가요?

- `401`은 인증이 필요하거나 인증 정보가 유효하지 않은 경우, `403`은 인증 여부와 별개로 접근 권한이 없는 경우라고 설명하면 된다.

### Q. keep-alive를 왜 쓰나요?

- 매 요청마다 TCP/TLS 연결을 새로 만들지 않고 재사용해 지연과 비용을 줄이기 위해 쓴다고 설명하면 된다.

### Q. HTTP request와 response는 각각 무엇으로 이루어지나요?

- request는 메서드, 경로, 헤더, 필요하면 body로, response는 상태 코드, 헤더, body로 이루어진다고 설명하면 된다.
