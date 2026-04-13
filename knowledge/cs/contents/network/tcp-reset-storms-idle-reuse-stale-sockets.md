# TCP Reset Storms, Idle Reuse, Stale Sockets

> 한 줄 요약: reset storm은 죽은 연결을 재사용하거나 idle timeout이 엇갈릴 때 쌓이며, 재시도와 keep-alive가 그 폭풍을 더 키울 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)

retrieval-anchor-keywords: TCP reset storm, stale socket, idle reuse, ECONNRESET, connection pool eviction, connection churn, retry amplification, keep-alive reuse, proxy close

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

reset storm은 소켓이 연속으로 `ECONNRESET`을 뿜는 상태를 말한다.

- 오래된 idle connection이 재사용된다
- 중간 proxy나 LB가 이미 닫은 소켓을 앱이 믿는다
- retry가 새 연결을 더 많이 만들며 상황을 악화시킨다

### Retrieval Anchors

- `TCP reset storm`
- `stale socket`
- `idle reuse`
- `ECONNRESET`
- `connection pool eviction`
- `connection churn`
- `retry amplification`
- `keep-alive reuse`
- `proxy close`

## 깊이 들어가기

### 1. reset storm은 왜 생기나

대부분은 "연결을 재사용했는데 이미 죽어 있었다"에서 시작한다.

- LB timeout이 더 짧다
- proxy upstream idle timeout이 더 짧다
- app pool이 너무 오래 된 소켓을 들고 있다

### 2. 왜 폭풍처럼 보이나

한 번 실패하면 retry가 더 붙는다.

- 실패한 요청이 새 connection을 만든다
- 새 connection이 또 stale path를 만날 수 있다
- worker와 pool이 계속 흔들린다

즉 reset storm은 단순 오류가 아니라 **재사용 정책과 retry 정책의 합성 실패**다.

### 3. stale socket은 어떻게 발견하나

많이 보이는 신호:

- 첫 요청만 실패하고 다음은 성공
- idle 뒤 첫 호출만 reset
- 특정 backend에서만 `ECONNRESET`

### 4. 왜 health check와 다르게 보이나

health check는 살아 있는 노드만 본다.

- 이미 붙은 connection reuse는 별개다
- pool 안의 오래된 socket은 별도로 관리해야 한다
- draining과 eviction이 필요하다

### 5. 어디서 먼저 고쳐야 하나

보통 다음 순서가 좋다.

1. pool idle eviction
2. peer timeout 정렬
3. keepalive/heartbeat 추가
4. retry budget 제한
5. stale socket validation

## 실전 시나리오

### 시나리오 1: 특정 시간대에만 reset이 급증한다

idle 후 첫 burst에서 stale socket reuse가 발생할 수 있다.

### 시나리오 2: retry를 늘렸더니 더 많이 실패한다

retry amplification으로 reset storm이 커질 수 있다.

### 시나리오 3: proxy 뒤에서만 `ECONNRESET`이 뜬다

중간 장비의 close 시점과 pool lifetime이 맞지 않을 수 있다.

## 코드로 보기

### 상태 관찰

```bash
ss -tan state established
ss -tan state close-wait
ss -tan state time-wait
```

### 리트라이/에러 로그 감각

```text
ECONNRESET after idle period
retry -> new socket -> reset again
pool -> stale socket retained too long
```

### 운영 포인트

```text
- pool validation on borrow
- idle eviction
- timeout hierarchy
- retry budget
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 오래 재사용 | handshake 비용이 줄어든다 | stale socket 위험이 커진다 | 안정적인 peer |
| 짧게 재사용 | stale reuse를 줄인다 | churn과 handshake가 늘어난다 | 변동성 큰 경로 |
| 검증 후 재사용 | 안정성이 좋다 | 구현이 복잡하다 | 운영 안정성이 중요한 경우 |

핵심은 연결 재사용 자체가 아니라 **죽은 소켓을 얼마나 빨리 버리느냐**다.

## 꼬리질문

> Q: reset storm은 왜 생기나요?
> 핵심: stale socket reuse와 timeout mismatch가 반복되기 때문이다.

> Q: retry가 왜 문제를 키우나요?
> 핵심: 실패한 요청이 새 연결과 더 많은 실패를 낳을 수 있다.

> Q: 어떻게 줄이나요?
> 핵심: pool eviction, timeout 정렬, keepalive, retry budget을 같이 맞춘다.

## 한 줄 정리

TCP reset storm은 오래된 소켓을 다시 믿는 순간 시작되므로, idle reuse를 줄이고 retry amplification을 막아야 한다.
