# Queue Saturation Attribution, Metrics, Runbook

> 한 줄 요약: queue saturation은 "upstream이 느리다"와 다른 문제다. 실제 네트워크 I/O 전에 worker queue, pending acquire, stream queue, sidecar dispatch 대기에서 timeout budget이 먼저 타는지를 분리해서 봐야 한다.
>
> 문서 역할: 이 문서는 network 운영 cluster 안에서 **queue wait attribution과 현장 triage 순서**를 맡는 runbook이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Connection Pool Starvation, Stale Idle Reuse, Debugging](./connection-pool-starvation-stale-idle-reuse-debugging.md)
> - [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)
> - [Retry Storm Containment, Concurrency Limiter, Load Shedding](./retry-storm-containment-concurrency-limiter-load-shedding.md)
> - [Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh](./adaptive-concurrency-limiter-latency-signal-gateway-mesh.md)
> - [Mesh Adaptive Concurrency, Local Reply, Metrics Tuning](./mesh-adaptive-concurrency-local-reply-metrics-tuning.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)

retrieval-anchor-keywords: queue saturation, queue wait attribution, pending acquire, worker queue, dispatch latency, backlog, queue depth, timeout before dispatch, connection pool wait, stream queue, local overload, inflight limit, overload runbook

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

queue saturation은 "응답 시간이 길다"는 현상을 **실제 처리 시간 증가**와 **처리 시작 전 대기 증가**로 분리하는 문제다.

- worker queue가 길어져 dispatch가 늦다
- connection pool pending acquire가 길다
- H2/H3 stream slot queue가 쌓인다
- sidecar/gateway inflight limit에 막혀 local reply가 먼저 난다
- socket write backlog나 event loop backlog가 누적된다

중요한 점은 이 현상들이 사용자에게는 전부 비슷하게 보인다는 것이다.

- `connect timeout`
- `504`
- mesh/gateway `503`
- p95/p99 tail latency 급등
- app은 평균 service time이 크게 안 오른 것처럼 보임

그래서 queue saturation runbook의 목표는 "느리다"를 넘어 **어디서 아직 시작도 못 했는지**를 찾는 것이다.

### Retrieval Anchors

- `queue saturation`
- `queue wait attribution`
- `pending acquire`
- `dispatch latency`
- `timeout before dispatch`
- `worker queue backlog`
- `stream queue`
- `local overload`

## 깊이 들어가기

### 1. queue는 한 종류가 아니다

실전에서 자주 섞이는 queue는 다음과 같다.

- app thread pool / worker queue
- client connection pool pending acquire
- HTTP/2 `MAX_CONCURRENT_STREAMS` pending queue
- gateway / sidecar inflight queue
- async executor / event loop task queue
- socket write backlog

runbook 첫 단계는 "queue가 있다"가 아니라 **어느 계층 queue인지 이름을 붙이는 것**이다.

### 2. 봐야 할 메트릭은 depth보다 wait time이 먼저다

queue depth만 보면 오해하기 쉽다.

- depth는 짧아도 대기 시간이 길 수 있다
- burst 순간에는 sampling 주기 때문에 depth가 안 잡힐 수 있다
- autoscale 직후 drain/retry 때문에 depth보다 timeout이 먼저 튈 수 있다

우선순위는 보통 이렇다.

1. queue wait / pending duration
2. timeout-before-dispatch 비율
3. local reject / local reply reason
4. queue depth / inflight
5. downstream service time

즉 "몇 개가 쌓였나"보다 **얼마나 오래 못 나갔나**가 더 직접적인 증거다.

### 3. attribution 순서는 upstream blame보다 앞단 대기부터다

다음 순서로 보면 헷갈림이 줄어든다.

1. 요청이 upstream connect를 시작했는가
2. connect 이전에 pool/worker queue에서 기다렸는가
3. proxy가 local timeout/local reject를 냈는가
4. upstream service time이 실제로 늘었는가

판단 예시:

- queue wait 급등 + upstream connect 수 정체
  - local saturation 가능성이 높다
- pending acquire 급등 + app CPU 평이
  - pool/stream slot 병목 가능성이 높다
- local reply `503` 급등 + app access log 공백
  - gateway/mesh 보호 계층이 먼저 잘랐을 수 있다
- TTFB만 증가하고 queue wait은 안정
  - upstream think time이나 lock/contention 쪽을 더 의심한다

### 4. timeout ladder를 같이 봐야 한다

queue saturation은 timeout budget을 조용히 태운다.

예:

- end-to-end timeout 2s
- gateway timeout 1.5s
- pool acquire timeout 800ms
- upstream connect timeout 300ms

이때 pending acquire에서 900ms를 쓰면:

- connect는 아직 시작도 못 했는데
- gateway 기준으로는 이미 절반 이상을 잃는다
- retry까지 겹치면 사실상 성공 확률이 급락한다

그래서 runbook에는 항상 **timeout-before-dispatch** 관점이 들어가야 한다.

### 5. 증폭기는 queue를 더 오래 숨긴다

queue saturation을 키우는 전형적인 증폭기:

- 무제한 retry
- long-lived stream과 short RPC 공유 pool
- fan-out 경로에서 느린 shard 하나
- stale idle reuse로 borrow 실패 후 재시도
- route class 분리 없는 adaptive limiter

이런 경우 queue 자체보다 **queue를 만드는 구조**를 같이 적어야 한다.

### 6. 현장 triage는 "더 많은 queue를 허용"이 아니라 "어느 queue를 줄일지"다

자주 쓰는 triage 선택지는 다음과 같다.

- fail-fast로 pending queue cap 축소
- hot route와 background route 분리
- long-lived traffic 전용 pool 분리
- retry budget 축소
- inflight limiter / concurrency limiter 조정
- timeout hierarchy 재정렬

핵심은 queue를 키워 숨기는 게 아니라, **중요 경로의 대기 시간을 먼저 끊는 것**이다.

## 실전 시나리오

### 시나리오 1: p99만 급등하고 upstream 평균 latency는 안정적이다

우선 확인:

- pending acquire time
- worker queue wait
- timeout-before-dispatch 비율
- retry count

이 패턴은 service time보다 queue wait가 먼저 무너지는 경우가 많다.

### 시나리오 2: mesh 503이 늘었는데 app 로그는 비어 있다

가능한 해석:

- sidecar local reply
- route-level inflight cap 초과
- adaptive concurrency 과민 반응

이때 app 오류율보다 local reply reason과 queue pressure를 먼저 본다.

### 시나리오 3: `connect timeout`이 늘었는데 실제 connect latency는 평이하다

자주 놓치는 경우:

- request가 connect 호출 전 pool에서 기다렸다
- H2 stream slot을 못 얻어 socket I/O가 늦었다
- event loop backlog로 dispatch가 밀렸다

즉 connect timeout surface가 곧 connect phase 원인이라는 뜻은 아니다.

### 시나리오 4: queue depth는 낮은데 사용자 timeout은 많다

가능한 원인:

- sampling interval이 길다
- 대기 시간이 짧게 폭증했다가 사라진다
- local reject가 queue를 길게 만들기 전에 잘라 버린다

그래서 depth 한 장으로 판단하면 놓친다.

## 코드로 보기

### 메트릭 매핑

```text
queue layer                 primary signal                     supporting signal
worker queue                dispatch wait, queue wait p95      active workers, reject count
connection pool            pending acquire time               active/idle conn, borrow timeout
H2/H3 stream queue         pending stream wait                active streams per conn
gateway/mesh               local reply reason, inflight       route class, upstream selected 여부
retry path                 retry attempt count                timeout ladder, duplicated work
```

### 현장 질문

```text
- 이 요청은 upstream connect를 실제로 시작했는가
- timeout이 dispatch 전에 났는가, upstream 처리 중에 났는가
- pending acquire와 service time 중 무엇이 먼저 올랐는가
- local reply/source tag가 있는가
- queue를 키운 증폭기(retry, long-lived stream, mixed route)가 있는가
```

### 짧은 triage 흐름

```text
1. queue wait / pending duration 확인
2. local reply / reject source 확인
3. upstream connect/TTFB/service time과 비교
4. retry, stream mix, route class 혼합 여부 확인
5. 중요한 경로부터 queue cap / isolation / limiter 조정
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 큰 queue 유지 | burst 흡수력이 있다 | tail latency와 zombie work를 숨긴다 | 짧은 순간 버스트 위주 |
| 작은 queue + fail-fast | overload를 빨리 드러낸다 | 에러율이 더 빨리 보인다 | 보호가 더 중요한 경로 |
| route/pool 분리 | 중요한 경로 격리가 좋다 | 운영 복잡도가 늘어난다 | mixed traffic |
| adaptive limiter | 자동 보호가 가능하다 | 튜닝이 어렵고 false positive가 있다 | mesh/gateway |
| retry 축소 | 증폭을 줄인다 | 순간 성공률이 내려갈 수 있다 | queue 증폭이 심할 때 |

핵심은 queue saturation 대응이 단순 capacity 확장이 아니라 **대기 시간의 위치를 찾고 보호 경계를 다시 그리는 작업**이라는 점이다.

## 꼬리질문

> Q: queue saturation과 upstream slowness는 어떻게 구분하나요?
> 핵심: upstream service time보다 queue wait, pending acquire, local reply source가 먼저 오르면 queue saturation 쪽 증거가 더 강하다.

> Q: 가장 먼저 볼 메트릭은 무엇인가요?
> 핵심: depth보다 wait time과 timeout-before-dispatch가 먼저다.

> Q: 왜 queue를 그냥 크게 두면 안 되나요?
> 핵심: burst 흡수는 되지만 tail latency와 retry 증폭을 더 오래 숨길 수 있다.

> Q: app 로그가 비어 있는데 503이 많으면 무엇을 의심하나요?
> 핵심: gateway/mesh local reply, inflight limiter, queue-based fail-fast를 먼저 본다.

## 한 줄 정리

queue saturation runbook의 핵심은 느린 요청을 "upstream이 늦다"로 뭉개지 않고, 실제 I/O 전에 어디서 얼마를 기다렸는지와 누가 먼저 잘랐는지를 분해해 보는 것이다.
