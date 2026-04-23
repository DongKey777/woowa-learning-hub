# HTTP/2, HTTP/3 Connection Reuse, Coalescing

> 한 줄 요약: HTTP/2와 HTTP/3는 연결을 아끼기 위해 재사용과 coalescing을 적극적으로 쓰지만, 그 이득은 인증서, DNS, 라우팅, 손실 특성까지 맞아야 나온다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)

retrieval-anchor-keywords: connection reuse, coalescing, HTTP/2 origin coalescing, HTTP/3 connection reuse, multiplexing, authority, certificate SAN, shared connection, pooled connection

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

HTTP/2와 HTTP/3는 연결을 더 적게 만들고 더 많이 재사용하려고 설계됐다.

- 하나의 연결에 여러 요청을 태운다
- origin이 같거나 안전하게 묶일 수 있으면 connection coalescing을 시도한다
- 연결 수를 줄여 handshake 비용을 낮춘다

하지만 연결을 아끼는 만큼, **잘못 묶으면 잘못된 서버로 연결을 재사용할 위험**도 생긴다.

### Retrieval Anchors

- `connection reuse`
- `coalescing`
- `HTTP/2 origin coalescing`
- `HTTP/3 connection reuse`
- `multiplexing`
- `authority`
- `certificate SAN`
- `shared connection`
- `pooled connection`

## 깊이 들어가기

### 1. connection reuse가 왜 중요한가

새 연결을 만들 때마다 비용이 든다.

- TCP handshake
- TLS handshake
- 혼잡 제어 초기화
- 커널과 FD 비용

reuse는 이 비용을 줄여 준다.  
특히 짧은 요청이 많은 서비스에서 효과가 크다.

### 2. coalescing은 무엇인가

coalescing은 서로 다른 hostname처럼 보여도, 같은 연결을 안전하게 공유하는 것이다.

HTTP/2에서 이런 일이 가능하려면 보통 다음이 맞아야 한다.

- 인증서 SAN이 여러 origin을 커버한다
- DNS가 같은 엔드포인트로 간다
- 서버가 같은 권한 범위를 받아들인다
- 라우팅이 혼동되지 않는다

즉, "도메인이 다르다"와 "연결을 못 공유한다"는 같은 말이 아니다.  
조건이 맞으면 하나의 연결을 더 똑똑하게 쓸 수 있다.

### 3. HTTP/2의 재사용은 왜 조심해야 하나

HTTP/2는 하나의 TCP 연결 위에 많은 stream을 올린다.

- 연결 수는 줄어든다
- 하지만 손실이 생기면 같은 연결 위의 스트림이 같이 영향을 받는다
- coalescing을 과하게 하면 장애 반경이 커질 수 있다

이 부분은 [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)와 연결된다.

### 4. HTTP/3에서도 비슷한 고민이 남는다

HTTP/3는 QUIC 위에서 동작하므로 TCP HOL blocking은 덜하지만, 연결 재사용 자체의 운영 고민은 남는다.

- connection ID와 migration 고려
- QUIC path validation
- 손실/재시도 특성
- 로드밸런서와 미들박스 호환성

즉, HTTP/3가 "연결 관리가 없다"는 뜻은 아니다.

### 5. 왜 coalescing이 운영에서 더 까다로운가

coalescing은 이득이 크지만, 잘못되면 분석이 어려워진다.

- 한 origin의 문제처럼 보이는데 실제로는 shared connection의 문제일 수 있다
- 인증서 갱신 후 갑자기 coalescing hit rate가 바뀔 수 있다
- DNS/anycast/LB 변경이 연결 재사용 패턴에 영향을 준다

## 실전 시나리오

### 시나리오 1: 연결 수는 줄었는데 느려졌다

가능한 원인:

- 하나의 shared connection에 많은 요청이 몰렸다
- packet loss가 같은 연결 전체에 영향을 줬다
- HOL blocking이 체감됐다

### 시나리오 2: 특정 서브도메인에서만 성능이 들쭉날쭉하다

SAN과 routing이 coalescing 조건을 바꾸었을 수 있다.

- 인증서가 여러 host를 커버한다
- 하지만 backend는 다른 origin처럼 다뤄야 한다
- 연결 재사용이 오히려 혼선을 만든다

### 시나리오 3: HTTP/3 전환 후 연결은 적어졌는데 장애 분석이 어려워졌다

connection reuse가 더 공격적으로 보일수록, tracing과 metrics가 더 중요해진다.

- 어느 origin의 요청이 같은 연결을 썼는지
- 재사용 비율이 얼마나 되는지
- 손실이 어떤 path에 있었는지

## 코드로 보기

### curl에서 HTTP 버전과 재사용 감각 보기

```bash
curl -w 'proto=%{http_version} connect=%{time_connect} appconnect=%{time_appconnect}\n' \
  -o /dev/null -s https://api.example.com
```

### HTTP/2 연결 확인

```bash
nghttp -nv https://api.example.com
```

### TLS 인증서와 origin 매칭 보기

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts
```

### 관찰 포인트

```text
- connection pool hit ratio
- reused stream count
- handshake frequency
- p95 / p99 under loss
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 적극적 connection reuse | handshake 비용이 줄어든다 | shared connection failure domain이 커진다 | 짧은 요청이 많을 때 |
| origin coalescing | 연결 수를 더 줄인다 | 라우팅과 인증서 조건이 복잡하다 | 멀티호스트 운영 |
| 연결을 덜 공유한다 | 장애 반경이 작아진다 | handshake 비용이 늘어난다 | 격리 우선 |

핵심은 연결을 얼마나 적게 쓰느냐가 아니라 **어느 경계까지 공유해도 안전한가**다.

## 꼬리질문

> Q: coalescing은 왜 필요한가요?
> 핵심: 연결 수와 handshake 비용을 줄이기 위해서다.

> Q: 왜 coalescing이 항상 좋은 건가요?
> 핵심: shared connection의 장애 반경이 커지고 분석이 어려워질 수 있다.

> Q: HTTP/3에서도 connection reuse 고민이 남나요?
> 핵심: 남는다. 전송 계층은 바뀌어도 연결 관리와 라우팅 문제는 계속 있다.

## 한 줄 정리

HTTP/2와 HTTP/3의 connection reuse와 coalescing은 비용을 줄이는 강력한 도구지만, 인증서와 라우팅 조건이 맞을 때만 안전하게 이득이 난다.
