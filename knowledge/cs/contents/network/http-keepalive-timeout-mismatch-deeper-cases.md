# HTTP Keep-Alive Timeout Mismatch, Deeper Cases

> 한 줄 요약: HTTP keep-alive timeout은 클라이언트, 프록시, LB, origin이 서로 다르게 잡으면 재사용 시점에만 고장 나는 소켓을 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
> - [LB Connection Draining, Deployment Safe Close](./lb-connection-draining-deployment-safe-close.md)
> - [TCP Reset Storms, Idle Reuse, Stale Sockets](./tcp-reset-storms-idle-reuse-stale-sockets.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)

retrieval-anchor-keywords: HTTP keep-alive, connection pool, idle timeout, upstream timeout, stale socket, proxy timeout, origin keepalive, validation on borrow

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

HTTP keep-alive는 연결 재사용의 기본이다.  
문제는 계층마다 timeout이 다르면, 재사용 시점에만 실패하는 오래된 소켓이 생긴다는 점이다.

- client pool timeout
- proxy downstream keepalive
- proxy upstream keepalive
- origin server keepalive

### Retrieval Anchors

- `HTTP keep-alive`
- `connection pool`
- `idle timeout`
- `upstream timeout`
- `stale socket`
- `proxy timeout`
- `origin keepalive`
- `validation on borrow`

## 깊이 들어가기

### 1. 더 깊은 mismatch 패턴

단순히 "proxy와 app timeout이 다르다"보다 더 복잡한 패턴이 있다.

- client pool은 너무 오래 유지한다
- proxy는 더 빨리 닫는다
- origin은 그 중간 값이다
- 결과적으로 중간 계층이 죽은 소켓을 재사용한다

### 2. 왜 첫 요청만 실패하나

idle 이후 첫 reuse가 가장 위험하다.

- 소켓은 열려 있는 것처럼 보인다
- 실제 peer는 이미 close 했다
- `ECONNRESET` 또는 `broken pipe`가 바로 나온다

### 3. validation on borrow가 필요한 이유

pool에서 꺼낼 때 소켓이 살아 있는지 확인해야 한다.

- stale socket을 줄인다
- timeout mismatch를 빨리 드러낸다
- 하지만 약간의 비용이 든다

### 4. keep-alive가 길면 좋은가

항상 그렇지 않다.

- 너무 길면 stale connection이 쌓인다
- 너무 짧으면 handshake 비용이 늘어난다
- 서비스 특성에 맞는 균형이 필요하다

### 5. 배포와 같이 보면

draining 없이 서버를 내리면 keep-alive mismatch가 더 크게 보인다.

## 실전 시나리오

### 시나리오 1: 거의 항상 괜찮다가 가끔 첫 호출만 깨진다

keep-alive reuse와 timeout mismatch를 의심한다.

### 시나리오 2: 프록시만 바꾸자 reset이 늘었다

proxy upstream/downstream timeout 차이가 벌어졌을 수 있다.

### 시나리오 3: pool이 큰데 성능은 오히려 나쁘다

stale socket과 retry가 섞여 있을 수 있다.

## 코드로 보기

### 관찰

```bash
ss -tan state established
ss -tan state close-wait
```

### 정책 감각

```text
- client pool eviction
- proxy idle timeout
- origin keepalive
- borrow-time validation
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 긴 keep-alive | 재사용 효율이 좋다 | stale socket 위험이 크다 | 안정된 경로 |
| 짧은 keep-alive | mismatch를 줄인다 | handshake 비용이 늘어난다 | 변동성 큰 경로 |
| 검증 포함 reuse | 안전하다 | 구현 비용이 있다 | 운영 안정성 중요 |

핵심은 timeout 숫자보다 **재사용 순간의 검사 여부**다.

## 꼬리질문

> Q: HTTP keep-alive mismatch는 왜 재사용 시점에만 보이나요?
> 핵심: 연결은 살아 보이지만 peer는 이미 닫았을 수 있기 때문이다.

> Q: validation on borrow가 왜 필요한가요?
> 핵심: pool에서 꺼낼 때 stale socket을 걸러내기 위해서다.

> Q: keep-alive를 길게 두면 항상 좋나요?
> 핵심: 아니다. stale connection과 reset이 늘 수 있다.

## 한 줄 정리

HTTP keep-alive timeout mismatch는 연결이 열린 것처럼 보이는 stale socket을 만들기 쉬워서, reuse 직전에 검증을 넣는 것이 중요하다.
