# 웹소켓 기초 (WebSocket Basics)

> 한 줄 요약: 웹소켓은 HTTP로 연결을 업그레이드한 뒤 양방향 통신 채널을 유지하고, 서버가 먼저 데이터를 보낼 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [WebSocket heartbeat, backpressure, reconnect](./websocket-heartbeat-backpressure-reconnect.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP 무상태성과 상태 유지 전략 입문](./http-stateless-state-management-basics.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC Controller 기초](../spring/spring-mvc-controller-basics.md)

retrieval-anchor-keywords: websocket basics, 웹소켓이 뭔가요, http vs websocket, websocket 양방향 통신, 서버 push 입문, ws wss 차이, websocket upgrade 헤더, 실시간 통신 기초, 채팅 구현 방법, beginner websocket

## 핵심 개념

HTTP는 클라이언트가 요청하면 서버가 응답하고 연결이 끝나는 구조다. 서버가 먼저 데이터를 보낼 수 없다. 채팅, 주식 시세, 게임처럼 **서버가 먼저 데이터를 밀어줘야 하는 상황**에 HTTP만으로는 한계가 있다. 웹소켓은 이 문제를 해결하는 프로토콜이다.

입문자가 헷갈리는 지점은 "웹소켓은 HTTP와 다른 프로토콜이냐"는 것이다. 연결은 HTTP로 시작하지만, Upgrade 과정을 거쳐 웹소켓 프로토콜로 전환된다. 이후부터는 HTTP가 아니라 웹소켓 프레임으로 데이터를 주고받는다.

## 한눈에 보기

| 항목 | HTTP (일반 요청) | WebSocket |
|---|---|---|
| 통신 방향 | 단방향 (클라이언트 → 서버 → 클라이언트) | 양방향 |
| 서버 Push | 불가 (polling 필요) | 가능 |
| 연결 유지 | 응답 후 종료 (keep-alive로 재사용은 가능) | 명시적으로 닫을 때까지 유지 |
| 오버헤드 | 매 요청마다 헤더 전송 | 초기 handshake 1회, 이후 프레임 단위 |
| 프로토콜 | `http://` / `https://` | `ws://` / `wss://` |

## 상세 분해

### WebSocket Upgrade 과정

1. 클라이언트가 HTTP 요청을 보낼 때 `Upgrade: websocket` 헤더를 포함한다.
2. 서버가 `101 Switching Protocols` 응답을 돌려준다.
3. 이후부터 같은 TCP 연결에서 웹소켓 프레임으로 데이터를 교환한다.

```
클라이언트 → 서버: GET /chat HTTP/1.1
                   Upgrade: websocket
                   Connection: Upgrade
                   ...
서버 → 클라이언트: HTTP/1.1 101 Switching Protocols
                   Upgrade: websocket
                   ...
[이후 웹소켓 프레임으로 양방향 통신]
```

### ws와 wss

`ws://`는 암호화 없는 웹소켓, `wss://`는 TLS 위에서 동작하는 웹소켓이다. HTTPS 환경에서는 `wss://`를 사용해야 혼합 콘텐츠 오류가 발생하지 않는다.

### 언제 쓰나

실시간 채팅, 알림 서비스, 주식·코인 시세, 온라인 게임, 협업 편집기처럼 서버가 데이터를 능동적으로 보내야 할 때 적합하다. 단순 CRUD API에는 HTTP가 더 적합하다.

## 흔한 오해와 함정

- "웹소켓 연결을 열면 서버 자원을 계속 소비한다"는 말은 맞다. 연결을 유지하므로 서버 메모리와 파일 디스크립터를 점유한다. 수만 명이 동시에 접속하는 서비스에서는 스케일아웃 전략이 중요하다.
- HTTP polling(주기적으로 요청)으로 실시간 효과를 내는 경우도 있다. polling이 단순하고 인프라 설정이 적지만, 불필요한 요청이 많고 지연이 생긴다.
- 웹소켓은 로드밸런서 설정에서 별도 주의가 필요하다. TCP 연결을 오래 유지하므로 idle timeout 설정이 짧으면 연결이 끊긴다.

## 실무에서 쓰는 모습

Spring Boot에서는 `spring-boot-starter-websocket` 의존성을 추가하고 `@EnableWebSocket` 설정으로 웹소켓 엔드포인트를 노출한다. 채팅 기능 구현 시 클라이언트는 브라우저 `WebSocket` 객체로 연결하고, 서버는 연결된 세션 목록을 관리해서 메시지를 원하는 클라이언트에게 브로드캐스트한다.

## 더 깊이 가려면

- [WebSocket heartbeat, backpressure, reconnect](./websocket-heartbeat-backpressure-reconnect.md) — 운영 중 발생하는 연결 유지, 배압, 재연결 전략
- [network 카테고리 인덱스](./README.md) — 다음 단계 주제 탐색

## 면접/시니어 질문 미리보기

**Q. HTTP와 WebSocket의 차이를 설명해 주세요.**
HTTP는 클라이언트가 요청하면 서버가 응답하는 단방향 구조이고, WebSocket은 HTTP Upgrade로 연결을 전환해 양방향 통신 채널을 유지한다. 서버가 먼저 메시지를 보낼 수 있다.

**Q. 웹소켓 대신 Long Polling을 쓰면 안 되나요?**
Long Polling은 서버가 응답을 의도적으로 늦게 보내 실시간 효과를 내는 기법이다. 간단하지만 요청마다 HTTP 오버헤드가 있고, 서버가 스레드를 오래 점유한다. 실시간성이 중요하면 웹소켓이 적합하다.

**Q. 웹소켓 연결이 많아지면 서버에서 어떻게 관리하나요?**
연결 수가 많아지면 파일 디스크립터와 메모리를 많이 쓴다. 비동기/논블로킹 서버(WebFlux, Node.js)가 이 상황에서 유리하고, 다수 서버 인스턴스 간에는 메시지 브로커(Redis pub/sub 등)를 써서 메시지를 공유한다.

## 한 줄 정리

웹소켓은 HTTP로 시작해 101로 업그레이드한 뒤 서버-클라이언트 양방향 채널을 유지하는 프로토콜이다.
