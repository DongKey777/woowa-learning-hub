# HTTP 버전 비교 입문: HTTP/1.1, HTTP/2, HTTP/3

> 한 줄 요약: HTTP/1.1은 요청 하나씩 처리하고, HTTP/2는 한 연결에서 여러 요청을 동시에 처리하며, HTTP/3는 UDP 기반 QUIC으로 연결 오버헤드를 줄였다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [TCP와 UDP 기초](./tcp-udp-basics.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: http version comparison beginner, http 1.1 vs http 2, http 3 quic 입문, http 버전 차이 뭔가요, 멀티플렉싱이 뭔가요, http2 장점, http3 왜 빨라요, 연결 하나에 여러 요청, http 버전 기초, beginner http versions

## 핵심 개념

HTTP는 버전이 올라갈수록 같은 네트워크 연결을 더 효율적으로 쓰는 방향으로 발전했다. 입문자가 헷갈리는 지점은 "버전마다 URL도 바뀌고 코드도 다 바꿔야 하냐"는 오해다. HTTP/2, HTTP/3를 써도 애플리케이션 코드는 거의 그대로다. 버전 협상은 브라우저와 서버 사이에서 자동으로 이뤄진다.

## 한눈에 보기

| 항목 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| 전송 단위 | 텍스트 | 바이너리 프레임 | 바이너리 프레임 |
| 동시 요청 | 연결당 1개 (파이프라이닝은 제한적) | 단일 연결 멀티플렉싱 | 단일 연결 멀티플렉싱 |
| 기반 프로토콜 | TCP | TCP | UDP (QUIC) |
| 헤더 압축 | 없음 | HPACK | QPACK |
| 연결 수립 | TCP + TLS | TCP + TLS | QUIC (1-RTT/0-RTT) |

## 상세 분해

### HTTP/1.1 — 요청 하나씩

HTTP/1.1은 기본적으로 요청 하나를 보내고 응답을 받은 뒤 다음 요청을 보낸다. 여러 요청을 동시에 처리하려면 브라우저가 도메인당 여러 TCP 연결을 열어야 했다. 헤더를 매 요청마다 텍스트로 전송해서 중복이 많다. 가장 오래됐지만 아직도 많은 곳에서 동작한다.

### HTTP/2 — 멀티플렉싱

하나의 TCP 연결에서 여러 요청/응답이 동시에 오가는 **멀티플렉싱**이 핵심이다. 요청마다 번호가 붙은 프레임 단위로 전송되므로, 순서를 기다리지 않아도 된다. 헤더를 HPACK으로 압축해 중복을 줄인다. 단, TCP 수준에서 패킷이 유실되면 그 뒤 패킷 전체가 기다리는 HOL blocking 문제가 있다.

### HTTP/3 — UDP 기반 QUIC

TCP 대신 UDP 위에서 QUIC 프로토콜을 쓴다. TCP handshake + TLS handshake를 QUIC이 하나로 통합해 연결 수립 속도가 빠르다. 패킷 유실이 발생해도 다른 스트림에 영향을 주지 않아 TCP의 HOL blocking을 피한다. 아직 서버·클라이언트 양쪽이 지원해야 하고, 방화벽 등에서 UDP를 막는 환경이 있어 HTTP/2로 자동 폴백되는 경우도 있다.

## 흔한 오해와 함정

- HTTP/2, HTTP/3를 쓰면 코드를 다시 짜야 한다고 오해하는 경우가 있다. 실제로는 서버 설정(Nginx, Spring Boot) 변경이 주이고, 애플리케이션 코드는 거의 바뀌지 않는다.
- "HTTP/2가 항상 HTTP/1.1보다 빠르다"는 것도 오해다. 요청 수가 적거나 네트워크 상태가 좋으면 차이가 미미하거나 HTTP/1.1이 더 나을 수도 있다.
- HTTP/3는 현재 대부분의 주요 브라우저에서 지원하지만, 기업 내부 방화벽 환경에서는 UDP가 막혀 있어 HTTP/2로 자동 다운그레이드된다.

## 실무에서 쓰는 모습

Spring Boot 단독으로는 기본 HTTP/1.1이다. Nginx 앞단을 두고 `http2` 지시어를 켜면 브라우저-Nginx 구간은 HTTP/2가 되고, Nginx-Spring Boot 내부 구간은 HTTP/1.1이나 HTTP/2를 선택할 수 있다. 대규모 서비스에서는 CDN(CloudFront, Cloudflare)이 자동으로 HTTP/3을 협상해주는 경우도 많다.

## 더 깊이 가려면

- [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) — HTTP/2의 멀티플렉싱 동작 원리와 병목 지점 상세
- [network 카테고리 인덱스](./README.md) — 다음 단계 주제 탐색

## 면접/시니어 질문 미리보기

**Q. HTTP/1.1과 HTTP/2의 핵심 차이는?**
HTTP/2는 멀티플렉싱을 지원해서 하나의 TCP 연결로 여러 요청/응답을 동시에 처리한다. HTTP/1.1은 요청 하나씩 처리하거나 도메인당 여러 연결을 열어야 했다.

**Q. HTTP/3는 왜 UDP를 쓰나요?**
TCP의 HOL blocking 문제를 근본적으로 해결하기 위해서다. UDP 위의 QUIC은 스트림 단위로 패킷 유실을 독립적으로 처리해서 다른 요청이 영향을 받지 않는다.

**Q. 멀티플렉싱이 없으면 어떤 문제가 생기나요?**
여러 리소스(JS, CSS, 이미지)를 요청할 때 순서를 기다려야 하거나, 브라우저가 도메인당 여러 TCP 연결을 열어야 한다. 연결 생성 비용과 서버 부하가 증가한다.

## 한 줄 정리

HTTP는 1.1 → 2 → 3로 가면서 단일 연결에서 더 많은 요청을 효율적으로 처리하는 방향으로 발전했다.
