# Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh

> 한 줄 요약: adaptive concurrency는 고정 상한 대신 현재 latency와 queue 압력을 보고 허용 동시성을 조절하는 방식이라서, overload를 늦게 드러내는 정적 큐보다 healthy latency를 더 잘 지킬 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Retry Storm Containment, Concurrency Limiter, Load Shedding](./retry-storm-containment-concurrency-limiter-load-shedding.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Mesh Adaptive Concurrency, Local Reply, Metrics Tuning](./mesh-adaptive-concurrency-local-reply-metrics-tuning.md)

retrieval-anchor-keywords: adaptive concurrency, concurrency limiter, latency signal, queue pressure, gateway overload control, service mesh limiter, sidecar local reply, gradient controller, inflight limit, shed load

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

정적 concurrency limit은 단순하지만 환경 변화에 둔감하다.

- 평상시엔 너무 보수적일 수 있다
- 장애 직전엔 너무 늦게 반응할 수 있다

adaptive concurrency는 현재 상태를 보고 limit을 움직인다.

- inflight 수
- queue wait
- latency 상승
- timeout / local reject 비율

즉 목표는 처리량 최대화가 아니라 **healthy latency를 유지하는 동시성 상한을 동적으로 찾는 것**이다.

### Retrieval Anchors

- `adaptive concurrency`
- `concurrency limiter`
- `latency signal`
- `queue pressure`
- `gateway overload control`
- `service mesh limiter`
- `inflight limit`
- `shed load`

## 깊이 들어가기

### 1. 왜 static limit만으로 부족한가

요청 특성과 backend 상태는 고정되어 있지 않다.

- 어떤 시간엔 request가 가볍다
- 어떤 시간엔 DB lock으로 service time이 늘어난다
- 어떤 route는 streaming 때문에 오래 잡고 있다

이때 static `max inflight`는:

- 너무 높으면 latency 붕괴
- 너무 낮으면 여유 처리량 낭비

를 번갈아 만든다.

### 2. adaptive limiter는 latency를 overload 신호로 본다

보통 overload는 에러가 나기 전에 latency로 먼저 나타난다.

- queue wait 증가
- TTFB 상승
- upstream pending acquire 증가
- timeout 직전의 긴 요청 증가

adaptive limiter는 이런 신호를 이용해 "지금 더 넣으면 안 된다"를 판단한다.

### 3. gateway/mesh에서 특히 유용한 이유

edge나 sidecar는 트래픽 분기점이라 overload가 빨리 모인다.

- 앱보다 먼저 pressure를 본다
- local reply로 빠르게 거절 가능
- route별 policy 적용이 쉽다

즉 gateway/mesh는 adaptive limiter를 붙이기 좋은 위치지만, 동시에 잘못 튜닝하면 모든 서비스에 공통 피해를 줄 수도 있다.

### 4. 어떤 신호를 쓰느냐가 핵심이다

가능한 입력:

- p50/p90 request latency
- queue wait
- timeout ratio
- in-flight requests
- upstream pending stream/connection count

나쁜 입력:

- 이미 너무 늦은 total latency만 사용
- route mix를 무시한 global average만 사용
- long-lived stream과 unary를 한데 섞은 지표

### 5. local reply와 observability가 같이 가야 한다

adaptive limiter는 종종 503/429류 local reply를 만든다.

그래서 운영자가 알아야 한다.

- app이 거절한 것인지
- sidecar/gateway limiter가 거절한 것인지
- 어떤 signal 때문에 줄였는지

이 정보가 없으면 limiter는 "가끔 이유 없이 503을 뱉는 프록시"처럼 보인다.

### 6. limiter는 route/traffic class 분리가 중요하다

하나의 전역 limiter가 모든 트래픽을 같이 자르면 문제다.

- admin / health / control plane
- user-facing latency-sensitive route
- batch / streaming route

가 모두 다르기 때문이다.  
adaptive concurrency는 보통 class-aware해야 실전 가치가 크다.

## 실전 시나리오

### 시나리오 1: static limit을 높이면 p99가 무너지고, 낮추면 처리량이 아쉽다

adaptive limiter 후보 신호가 준비되지 않은 상태일 수 있다.

### 시나리오 2: mesh를 켠 뒤 일부 route만 local 503이 늘었다

route별 latency signal과 inflight pattern이 달라 adaptive limiter가 먼저 작동한 것일 수 있다.

### 시나리오 3: batch job 시작 때 사용자 API가 같이 느려진다

global limiter가 traffic class를 분리하지 않아 shared pressure를 사용자 API에 전파한 패턴일 수 있다.

### 시나리오 4: limiter는 잘 작동하는데 팀이 app 장애로 오해한다

local reply attribution과 limiter reason tagging이 부족한 패턴이다.

## 코드로 보기

### 관찰 포인트

```text
- inflight requests
- queue wait
- local reply reason = adaptive concurrency
- p50/p90/p99 under limiter changes
- route / class별 limit과 reject 분포
```

### 정책 감각

```text
use latency as early overload signal
bound queue before it explodes
tag local rejects with limiter reason
separate long-lived traffic from latency-sensitive unary traffic
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| static concurrency limit | 단순하고 예측 가능하다 | 변화하는 부하에 둔감하다 | 안정적 단일 workload |
| adaptive concurrency | healthy latency를 더 잘 지킨다 | 신호 선택과 튜닝이 어렵다 | gateway, mesh, mixed traffic |
| global limiter | 운영이 단순하다 | route별 특성을 못 살린다 | 작은 시스템 |
| route/class-aware limiter | 보호 품질이 좋다 | 설정과 관측이 복잡하다 | 대규모 edge/mesh |

핵심은 adaptive concurrency를 "더 똑똑한 큐"가 아니라 **latency를 지키기 위해 동시성을 조절하는 보호 계층**으로 보는 것이다.

## 꼬리질문

> Q: adaptive concurrency는 무엇을 기준으로 limit을 조절하나요?
> 핵심: 보통 queue wait나 latency 상승 같은 early overload signal을 본다.

> Q: 왜 gateway/mesh에 잘 맞나요?
> 핵심: 트래픽이 모이는 지점이라 overload를 먼저 보고 local reply로 빠르게 보호할 수 있기 때문이다.

> Q: 왜 route 분리가 중요하나요?
> 핵심: long-lived stream과 짧은 unary request를 같은 limiter로 자르면 중요한 경로까지 함께 피해를 볼 수 있다.

## 한 줄 정리

adaptive concurrency는 queue가 터진 뒤 늦게 반응하는 대신 latency와 pressure를 조기에 보고 동시성을 줄여, gateway/mesh에서 healthy path를 더 잘 보호하게 해 준다.
