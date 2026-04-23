# HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교

**난이도: 🔴 Advanced**

> connection reuse, multiplexing, HOL blocking, browser/server 변화만 먼저 잡고 싶은 학습자를 위한 HTTP 버전 비교 primer

> 관련 문서:
> - [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/2, HTTP/3 Connection Reuse, Coalescing](./http2-http3-connection-reuse-coalescing.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)

retrieval-anchor-keywords: HTTP/1.1 vs HTTP/2 vs HTTP/3, beginner HTTP version comparison, HTTP keep-alive, connection reuse, multiplexing basics, HOL blocking, browser protocol negotiation, server protocol support, QUIC basics, TCP HOL vs QUIC streams, HTTP version differences

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [한 번에 보는 큰 그림](#한-번에-보는-큰-그림)
- [연결 재사용은 어떻게 달라지나](#연결-재사용은-어떻게-달라지나)
- [멀티플렉싱과 HOL blocking은 어떻게 달라지나](#멀티플렉싱과-hol-blocking은-어떻게-달라지나)
- [브라우저 입장에서는 무엇이 달라지나](#브라우저-입장에서는-무엇이-달라지나)
- [서버와 인프라 입장에서는 무엇이 달라지나](#서버와-인프라-입장에서는-무엇이-달라지나)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

HTTP 버전 비교는 "무엇이 더 최신인가"보다 **브라우저가 연결을 어떻게 아끼고, 요청을 어떻게 동시에 보내며, 손실이 났을 때 어디서 막히는가**를 구분하는 문제다.

특히 입문 단계에서는 아래 네 가지를 같이 이해하면 된다.

- 연결을 한 번 맺고 계속 재사용하는가
- 한 연결에서 여러 요청을 동시에 섞어 보낼 수 있는가
- 앞의 지연이 뒤 요청까지 막는가
- 브라우저와 서버가 지원해야 하는 것이 무엇인가

### Retrieval Anchors

- `HTTP/1.1 vs HTTP/2 vs HTTP/3`
- `HTTP keep-alive`
- `connection reuse`
- `multiplexing basics`
- `HOL blocking`
- `browser protocol negotiation`
- `server protocol support`
- `QUIC basics`

---

## 한 번에 보는 큰 그림

세 버전을 가장 짧게 비교하면 아래와 같다.

| 비교 항목 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| 전송 계층 | TCP | TCP | QUIC over UDP |
| 연결 재사용 | `keep-alive`로 재사용, 그래도 여러 TCP 연결을 자주 연다 | 한 TCP 연결을 더 적극적으로 재사용한다 | 한 QUIC 연결을 더 적극적으로 재사용한다 |
| 멀티플렉싱 | 사실상 없음 | stream multiplexing | QUIC stream multiplexing |
| HOL blocking 핵심 | 한 연결 안에서 요청/응답 순서가 발목을 잡기 쉽다 | HTTP 레벨 HOL은 줄지만 TCP HOL은 남는다 | TCP HOL을 피한다. 한 stream 손실이 다른 stream을 덜 막는다 |
| 브라우저 동작 | 병렬성을 위해 여러 연결을 연다 | 적은 연결에 많은 요청을 싣는다 | 가능하면 QUIC/H3를 쓰고 안 되면 H2로 fallback한다 |
| 서버 변화 | 소켓 수와 연결 관리 비용이 크다 | stream 수, flow control, H2 지원이 중요하다 | UDP 443, QUIC, fallback 운영이 중요하다 |

핵심만 말하면:

- HTTP/1.1은 "연결을 재사용하되 병렬성은 연결 수로 확보"한다
- HTTP/2는 "한 TCP 연결에 여러 요청을 같이 싣는다"
- HTTP/3는 "그 멀티플렉싱을 QUIC 위로 옮겨 TCP HOL 문제를 줄인다"

---

## 연결 재사용은 어떻게 달라지나

### HTTP/1.1

HTTP/1.1도 이미 `keep-alive`로 연결 재사용을 한다.  
다만 한 연결에서 요청을 마음 편하게 동시에 섞어 보내기 어렵기 때문에, 브라우저는 보통 같은 origin에 TCP 연결을 여러 개 연다.

즉 감각은 이렇다.

- 재사용은 한다
- 하지만 병렬성 확보를 위해 연결 수를 늘린다
- 그래서 socket, handshake, TLS 비용이 늘기 쉽다

### HTTP/2

HTTP/2는 한 TCP 연결 위에 여러 stream을 올려서 **연결을 더 오래, 더 공격적으로 재사용**한다.

- 브라우저는 같은 origin에 새 TCP 연결을 여러 개 열 필요가 줄어든다
- 작은 CSS, JS, API 요청을 한 연결에 같이 실을 수 있다
- 연결 수는 줄지만, 한 연결이 더 중요한 자원이 된다

### HTTP/3

HTTP/3도 연결 재사용을 매우 중요하게 본다.  
차이는 그 연결이 TCP가 아니라 QUIC이라는 점이다.

- 브라우저는 QUIC 연결 하나에 여러 stream을 올린다
- 네트워크가 바뀌어도 QUIC이 연결을 이어갈 여지가 있다
- 단, H3를 못 쓰는 경로가 있으면 브라우저는 H2/H1로 내려간다

입문 감각으로 정리하면:

- HTTP/1.1: "재사용은 하지만 여러 연결이 필요"
- HTTP/2: "한 연결 재사용을 적극화"
- HTTP/3: "한 연결 재사용을 유지하면서 transport 한계도 보완"

---

## 멀티플렉싱과 HOL blocking은 어떻게 달라지나

### HTTP/1.1: 연결 안에서는 순차성이 강하다

HTTP/1.1에서는 한 연결에서 요청 하나가 오래 걸리면 뒤 요청이 기다리기 쉽다.  
그래서 브라우저는 아예 연결을 여러 개 열어 우회한다.

즉 HTTP/1.1의 병렬성은 "프로토콜이 잘 섞어준다"기보다 **연결을 여러 개 만들어서 분산한다**에 가깝다.

### HTTP/2: HTTP 레벨 HOL은 줄지만 TCP HOL은 남는다

HTTP/2의 핵심은 stream multiplexing이다.

- 요청 A, B, C를 한 연결에서 동시에 보낼 수 있다
- 큰 응답 하나 때문에 작은 응답이 HTTP 메시지 순서상 완전히 막히지는 않는다

하지만 TCP 위라는 사실은 그대로다.

- 패킷 하나가 유실되면
- 그 TCP 연결 위의 뒤 패킷들은 재전송이 끝날 때까지 대기할 수 있고
- 결국 같은 연결의 여러 stream이 함께 느려질 수 있다

즉 HTTP/2는 **HTTP 레벨 HOL blocking은 줄였지만 TCP 레벨 HOL blocking은 남긴다.**

### HTTP/3: QUIC stream으로 TCP HOL 문제를 줄인다

HTTP/3는 QUIC 위에서 각 stream을 다룬다.

- 어떤 stream에서 손실이 나도
- 다른 stream 데이터까지 같은 방식으로 멈출 필요가 줄어든다

그래서 손실이 있거나 모바일처럼 경로가 불안정한 환경에서 HTTP/3의 이점이 체감되기 쉽다.

단, 이것이 "절대 안 느려진다"는 뜻은 아니다.

- UDP 차단
- QUIC 미지원 middlebox
- fallback 경로

같은 다른 운영 이슈가 남는다.

### 아주 짧은 비유

- HTTP/1.1: 차선을 여러 개 늘려서 차를 분산한다
- HTTP/2: 차선을 하나로 합치고 차 안에서 줄을 잘 세운다
- HTTP/3: 차선 하나를 유지하되, 앞차 사고가 옆차까지 모두 멈추게 하지는 않으려 한다

---

## 브라우저 입장에서는 무엇이 달라지나

브라우저가 하는 큰 일은 세 버전 모두 비슷하다.

- 서버에 연결한다
- request를 보낸다
- response를 받아 렌더링한다

달라지는 것은 **어떤 연결을 몇 개 쓰고, 어떤 프로토콜을 협상하며, 실패 시 어디로 fallback하느냐**다.

### HTTP/1.1 브라우저 감각

- 병렬 다운로드를 위해 연결을 여러 개 연다
- `keep-alive`로 재사용하지만 연결 수가 많아지기 쉽다
- 텍스트 기반이라 디버깅 감각은 비교적 단순하다

### HTTP/2 브라우저 감각

- TLS 단계에서 보통 ALPN으로 `h2`를 협상한다
- 연결 수는 줄이고 한 연결에 많은 요청을 태운다
- 한 연결 상태가 나빠지면 많은 리소스 요청이 같이 흔들릴 수 있다

### HTTP/3 브라우저 감각

- 가능하면 `h3`를 시도하고, 안 되면 H2로 fallback한다
- QUIC/UDP가 가능한 경로에서 성능 이득을 본다
- 네트워크 이동이나 손실이 있는 환경에서 더 유리할 수 있다

입문자가 기억할 핵심은 이것이다.

- 브라우저 코드를 따로 짜지 않아도 대부분 자동 협상한다
- 하지만 브라우저는 "지원되는 가장 좋은 버전"을 쓰려 할 뿐이다
- 서버와 인프라가 준비되지 않으면 결국 H1/H2로 내려간다

---

## 서버와 인프라 입장에서는 무엇이 달라지나

애플리케이션 입장에서는 세 버전 모두 결국 request/response를 처리한다는 점은 비슷하다.  
정말 크게 달라지는 곳은 보통 **웹 서버, 프록시, CDN, 로드밸런서, 관측 체계**다.

### HTTP/1.1 서버 감각

- 연결 수가 많아질 수 있다
- keep-alive timeout과 idle socket 관리가 중요하다
- reverse proxy와 app server가 오래전부터 잘 지원한다

### HTTP/2 서버 감각

- H2 termination을 지원해야 한다
- `MAX_CONCURRENT_STREAMS`, flow control, header compression 같은 개념이 추가된다
- 연결 수는 줄지만 한 연결에 더 많은 요청이 몰린다

### HTTP/3 서버 감각

- TCP 443만이 아니라 UDP 443도 열어야 한다
- QUIC과 TLS 1.3 통합 스택이 필요하다
- `Alt-Svc`, fallback, UDP 차단 대응을 같이 운영해야 한다
- packet capture와 장애 해석이 H1/H2보다 어렵다

즉 서버 쪽에서 느끼는 변화는:

- H1.1: 연결 수 관리
- H2: stream과 공유 연결 관리
- H3: UDP/QUIC 운영과 fallback 관리

---

## 자주 헷갈리는 포인트

### HTTP/2가 있으면 HTTP/1.1은 완전히 쓸모없나

아니다.

- 여전히 호환성이 가장 넓다
- 중간 장비와 오래된 클라이언트가 단순하게 지원한다
- 일부 환경에서는 H2/H3보다 디버깅과 운영이 쉽다

### HTTP/2는 항상 HTTP/1.1보다 빠른가

아니다.

- 요청이 많고 손실이 적은 환경에서는 유리하다
- 하지만 손실이 있는 네트워크에서는 TCP HOL 때문에 기대만큼 이득이 안 날 수 있다

### HTTP/3는 HTTP/2의 완전한 상위호환인가

개념적으로는 더 진화한 쪽이지만, 운영 현실은 다르다.

- QUIC/UDP를 못 쓰는 경로가 있다
- 그래서 대부분 H3만 단독으로 두지 않고 H2 fallback을 같이 둔다

### 브라우저와 서버 코드가 완전히 바뀌나

보통 애플리케이션 business logic은 크게 안 바뀐다.  
대신 protocol termination, proxy 설정, TLS/ALPN, 관측 포인트가 달라진다.

---

## 면접에서 자주 나오는 질문

> Q: HTTP/1.1과 HTTP/2의 가장 큰 차이는 무엇인가요?
> 핵심: 연결 재사용 방식보다도, 한 연결에서 여러 요청을 동시에 섞어 보내는 multiplexing 지원 여부가 가장 크다.

> Q: HTTP/2에도 HOL blocking이 남는 이유는 무엇인가요?
> 핵심: HTTP/2는 TCP 위에 있으므로 패킷 손실 시 TCP 레벨 HOL blocking이 같은 연결의 여러 stream에 영향을 줄 수 있다.

> Q: HTTP/3는 무엇을 바꾸나요?
> 핵심: HTTP 의미 자체보다 transport를 QUIC으로 바꿔 TCP HOL 문제를 줄이고, 손실/이동성 환경에서 더 유리하게 만든다.

> Q: 브라우저와 서버 입장에서 실무적으로 가장 큰 차이는 무엇인가요?
> 핵심: 브라우저는 자동 협상과 fallback이 중요하고, 서버는 H2/H3 termination, stream/UDP 운영, 관측 체계 준비가 중요하다.

## 한 줄 정리

HTTP/1.1은 여러 연결로 병렬성을 확보하고, HTTP/2는 한 TCP 연결 재사용과 multiplexing으로 효율을 높이며, HTTP/3는 그 구조를 QUIC으로 옮겨 TCP HOL blocking을 줄이되 운영 복잡도는 더 가져온다.
