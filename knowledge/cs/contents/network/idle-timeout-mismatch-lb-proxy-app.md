# Idle Timeout 불일치: LB, Proxy, App

> 한 줄 요약: 같은 연결을 여러 홉이 공유하는데 idle timeout이 서로 다르면, 한쪽은 살아 있다고 믿는 소켓을 다른 쪽은 이미 죽였을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [WebSocket Heartbeat, Backpressure, Reconnect](./websocket-heartbeat-backpressure-reconnect.md)
> - [SSE, WebSocket, Polling](./sse-websocket-polling.md)

retrieval-anchor-keywords: idle timeout, keep-alive timeout, connection pool, stale socket, connection draining, proxy timeout, load balancer timeout, reconnect storm, heartbeat interval

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`idle timeout`은 "연결이 얼마나 오래 아무 일 없이 있으면 닫을 것인가"를 정하는 값이다.  
문제는 이 값이 LB, reverse proxy, app server, client pool 각각에 따로 존재한다는 점이다.

- LB는 downstream connection을 관리한다
- proxy는 client-facing connection과 upstream connection을 둘 다 관리한다
- app server는 자기 keep-alive와 worker lifetime을 관리한다

이 값들이 서로 엇갈리면, 한 홉에서 끊은 연결을 다른 홉이 아직 살아 있다고 믿고 재사용하는 일이 생긴다.

### Retrieval Anchors

- `idle timeout`
- `keep-alive timeout`
- `connection pool`
- `stale socket`
- `connection draining`
- `proxy timeout`
- `load balancer timeout`
- `heartbeat interval`

## 깊이 들어가기

### 1. idle timeout은 request timeout이 아니다

자주 섞이지만 다르다.

- request timeout은 "이번 요청 전체를 얼마나 기다릴 것인가"
- idle timeout은 "아무 데이터도 없을 때 얼마나 유지할 것인가"

즉, long-polling, streaming, WebSocket 같은 연결에서는 request timeout보다 idle timeout이 더 먼저 문제를 만든다.

### 2. 왜 불일치가 생기나

각 계층이 서로 다른 이유로 타이머를 둔다.

- LB는 자원 보호와 연결 회수를 본다
- proxy는 재사용 효율과 backend 보호를 본다
- app server는 worker와 fd를 본다
- client는 사용자 체감을 본다

문제는 이 타이머들이 서로를 모른다는 점이다.  
그래서 한 홉이 먼저 닫히면 다른 홉의 연결 풀에는 이미 죽은 소켓이 남을 수 있다.

### 3. 가장 흔한 실패 패턴

#### 패턴 A: proxy upstream pool이 너무 길다

proxy가 backend로의 idle connection을 오래 들고 있다가, backend나 LB가 먼저 닫아 버린다.

- 다음 요청에서 stale socket reuse
- `ECONNRESET`
- retry 증가

#### 패턴 B: LB가 proxy보다 더 짧다

client는 proxy와 계속 통신한다고 생각하지만, 중간 LB가 이미 연결을 끊었다.

- 간헐적 502/504
- keep-alive 재사용 시점에만 실패

#### 패턴 C: app server가 너무 빨리 idle close 한다

proxy 입장에서는 backend connection을 재사용하고 싶은데, backend가 자주 닫는다.

- handshake가 늘어난다
- tail latency가 흔들린다
- connection churn이 증가한다

#### 패턴 D: long-lived connection에 heartbeat가 없다

WebSocket, SSE, HTTP/2 streaming처럼 연결이 길게 유지될수록, 중간 장비는 "살아 있다"는 신호를 못 받으면 idle로 판단한다.

### 4. 타이머를 어떻게 맞춰야 하나

정답은 고정 공식이 아니라 **의도적인 hierarchy**다.

좋은 방향:

- 자주 재사용하는 쪽이 오래된 소켓을 믿지 않도록 한다
- 중간 장비가 끊기기 전에 owner가 먼저 정리할 수 있게 여유를 둔다
- heartbeat나 graceful drain을 넣어 아무 일도 안 일어나는 구간을 줄인다

실무에서는 보통 다음을 함께 본다.

- client keep-alive
- proxy client-side idle timeout
- proxy upstream idle timeout
- LB idle timeout
- app server keep-alive
- app shutdown/drain window

핵심은 숫자 하나가 아니라 **연결이 어느 순간 누가 소유하는지**다.

### 5. connection draining이 왜 필요한가

배포나 스케일 인/아웃 때 기존 연결을 즉시 끊으면 불필요한 오류가 난다.

- 새 요청은 새 인스턴스로 보낸다
- 기존 연결은 잠깐 더 살려서 마무리한다
- 그 뒤에 정리한다

draining이 없으면, 타임아웃 불일치가 배포 순간에 갑자기 장애처럼 보일 수 있다.

## 실전 시나리오

### 시나리오 1: 가끔만 `ECONNRESET`이 난다

원인이 서버 코드가 아니라 idle timeout mismatch일 수 있다.

- 평소엔 괜찮다
- idle 뒤 첫 요청만 실패한다
- retry하면 된다

이 패턴은 stale socket reuse의 전형이다.

### 시나리오 2: WebSocket은 잘 되는데 가끔 끊긴다

heartbeat가 없거나 너무 느리면 중간 LB가 idle로 판단할 수 있다.

이 경우는 [WebSocket Heartbeat, Backpressure, Reconnect](./websocket-heartbeat-backpressure-reconnect.md)와 같이 봐야 한다.

### 시나리오 3: 배포 때만 502/504가 튄다

배포 중 app은 내려가는데 proxy/LB의 pool은 아직 그 connection을 믿는다.

- drain이 부족하다
- idle timeout이 너무 길다
- health check는 통과하지만 기존 연결은 죽어 있다

### 시나리오 4: retry가 장애를 키운다

죽은 연결을 재사용한 뒤 retry가 붙으면:

- 새 connection 생성
- 더 많은 TCP handshake
- 더 많은 타임아웃
- 더 많은 stale socket

이건 [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)와 [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md) 문제를 한 번에 키운다.

## 코드로 보기

### Nginx에서 keep-alive와 idle timeout 감각

```nginx
upstream app_backend {
    server app:8080;
    keepalive 64;
}

server {
    listen 443 ssl;

    keepalive_timeout 60s;
    proxy_connect_timeout 2s;
    proxy_read_timeout 30s;
    proxy_send_timeout 30s;
}
```

포인트는 "값을 크게 잡는 것"이 아니라, **연결을 재사용하는 쪽이 peer보다 오래 믿지 않도록** 구성하는 것이다.

### Spring/Java에서 connection pool을 볼 때

```java
HttpClient httpClient = HttpClient.create()
    .keepAlive(true)
    .responseTimeout(Duration.ofSeconds(3));
```

```text
체크 포인트:
- pool idle timeout
- max idle connections
- validation on borrow
- stale connection eviction
```

### long-lived connection heartbeat

```text
heartbeat interval < middleware idle timeout
```

heartbeat는 너무 잦으면 비용이 되고, 너무 느리면 중간 장비를 못 속인다.  
즉, "없으면 안 되고, 과하면 손해"다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 짧은 idle timeout | 자원을 빨리 회수한다 | 재연결과 handshake가 늘어난다 | 연결이 드물고 짧을 때 |
| 긴 idle timeout | 재사용이 좋다 | stale socket이 남는다 | 연결이 자주 재사용될 때 |
| heartbeat 추가 | 중간 장비가 끊지 않는다 | 추가 트래픽이 생긴다 | WebSocket, SSE, 장시간 스트리밍 |

핵심은 idle timeout을 없애는 게 아니라 **각 홉이 같은 현실을 보게 만드는 것**이다.

## 꼬리질문

> Q: idle timeout과 request timeout은 왜 다르게 관리해야 하나요?
> 핵심: 한 요청의 최대 대기와, 아무 데이터도 없는 연결의 유지 여부는 다른 문제다.

> Q: stale socket reuse는 왜 생기나요?
> 핵심: 한 홉이 먼저 닫은 연결을 다른 홉의 pool이 아직 살아 있다고 믿기 때문이다.

> Q: WebSocket은 왜 heartbeat가 필요한가요?
> 핵심: 중간 장비가 아무 트래픽이 없으면 죽은 연결로 판단할 수 있기 때문이다.

## 한 줄 정리

idle timeout은 각 계층이 따로 갖는 숨은 종료 조건이므로, LB와 proxy, app의 타이머를 맞추지 않으면 살아 있다고 믿은 연결이 이미 죽어 있을 수 있다.
