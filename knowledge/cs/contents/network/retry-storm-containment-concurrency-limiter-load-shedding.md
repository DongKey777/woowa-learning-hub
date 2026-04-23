# Retry Storm Containment, Concurrency Limiter, Load Shedding

> 한 줄 요약: retry budget만으로는 이미 시작된 폭풍을 다 막지 못한다. overload 구간에서는 concurrency limiter, queue cap, local shedding, fail-fast가 함께 있어야 retry가 healthy path까지 집어삼키지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)
> - [ALB, ELB Retry Amplification, Proxy Chain](./alb-elb-retry-amplification-proxy-chain.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh](./adaptive-concurrency-limiter-latency-signal-gateway-mesh.md)

retrieval-anchor-keywords: retry storm containment, concurrency limiter, load shedding, queue cap, fail-fast, overload control, retry amplification, adaptive concurrency, token bucket, healthy path protection

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

retry storm containment의 목표는 단순히 "재시도를 줄이자"가 아니다.

- healthy path를 보호하고
- 이미 늦은 요청을 빨리 버리며
- overload를 queue 안에 가두지 않고 밖으로 드러내는 것

필요한 장치는 보통 같이 온다.

- retry budget
- concurrency limiter
- pending queue cap
- local rate limit / shed load
- circuit breaker

### Retrieval Anchors

- `retry storm containment`
- `concurrency limiter`
- `load shedding`
- `queue cap`
- `fail-fast`
- `overload control`
- `retry amplification`
- `adaptive concurrency`

## 깊이 들어가기

### 1. retry storm은 "실패가 많다"보다 "늦은 요청이 계속 살아 있다"가 더 큰 문제다

폭풍 구간에서는 다음이 같이 일어난다.

- 원래 요청이 느리다
- retry가 새 요청을 만든다
- queue가 길어진다
- 늦은 요청이 더 오래 살아 있다

그래서 핵심은 retry를 줄이는 것뿐 아니라 **이미 늦어질 요청을 빨리 죽이는 것**이다.

### 2. concurrency limiter는 healthy concurrency 상한을 강제한다

단순 queue는 overload를 저장소처럼 쌓아 둔다.

limiter는 다르다.

- 동시 처리 수를 제한
- 임계점 밖 요청은 빠르게 거절
- 내부 latency가 붕괴하기 전에 보호

즉 limiter는 성공률을 조금 희생해서 tail latency와 시스템 생존성을 지킨다.

### 3. queue cap이 없으면 retry budget도 늦게 작동한다

retry budget이 있어도, 요청이 이미 긴 queue 안에서 오래 기다리면:

- budget은 queue 안에서 타 버리고
- dispatch 시점엔 이미 hopeless request가 된다

그래서 overload control은 retry budget보다 한 단계 더 앞에서:

- queue 길이
- pending acquire
- stream slot 대기

를 잘라야 한다.

### 4. shed load는 실패를 "조기에, 의도적으로" 만든다

과감하게 거절하는 것이 전체론 더 낫다.

- 일부 요청은 429/503으로 빨리 실패
- healthy request와 control traffic은 통과
- DB, pool, worker, connection이 살아남음

이건 사용자 경험상 아프지만, 무제한 queue보다 전체 시스템엔 안전하다.

### 5. source-aware local reply가 중요하다

proxy나 gateway가 shedding할 때는 이유를 구분해야 한다.

- local rate limit
- adaptive concurrency rejection
- no healthy upstream
- upstream timeout

같은 503이라도 retry 정책은 달라야 한다.  
그래서 containment은 observability와 붙어 다닌다.

### 6. containment는 layer ownership이 명확해야 한다

여러 계층이 동시에 각자 limiter와 retry를 들고 있으면 또 다른 혼선이 생긴다.

- edge는 coarse shedding
- gateway는 per-route policy
- app는 business-critical queue 분리

처럼 책임을 나눠야 한다.

## 실전 시나리오

### 시나리오 1: p99가 튄 뒤 healthy 노드까지 같이 느려진다

retry storm이 queue를 통해 healthy path까지 전염된 패턴일 수 있다.

### 시나리오 2: 에러율은 올랐지만 전체 장애는 막았다

load shedding이 일부 요청을 의도적으로 빨리 버리며 cluster collapse를 막은 경우일 수 있다.

### 시나리오 3: queue cap을 없앴더니 성공률은 잠깐 높아 보이지만 결국 전부 망가진다

hopeless request를 오래 살려 두며 자원을 다 태운 패턴일 수 있다.

### 시나리오 4: limiter를 켰더니 특정 route만 계속 503이 난다

global limiter가 route 특성을 충분히 분리하지 못해 중요한 경로와 덜 중요한 경로를 같이 자르는 패턴일 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- retry count
- inflight concurrency
- queue length / pending acquire
- shed load count
- local reply reason
- healthy path latency under overload
```

### 정책 감각

```text
retry budget: bounded
queue cap: bounded
concurrency: bounded
hopeless request: fail fast
local reply reason: observable
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 queue + generous retry | transient spike를 더 흡수한다 | storm 시 collapse가 쉬워진다 | 아주 짧은 burst |
| strict queue cap + shedding | healthy path를 보호한다 | 사용자에게 빠른 실패가 더 드러난다 | overload 민감 경로 |
| adaptive concurrency | 현재 상태에 맞춰 보호가 가능하다 | 튜닝과 관측이 더 어렵다 | 대규모 proxy/gateway |
| static concurrency limit | 단순하고 예측 가능하다 | 부하 변화에 둔감하다 | 안정적 트래픽 패턴 |

핵심은 overload를 queue에 숨기지 않고 **조기에, 의도적으로 밖으로 드러내는 것**이다.

## 꼬리질문

> Q: retry budget만 있으면 storm containment가 충분한가요?
> 핵심: 아니다. 이미 긴 queue 안에 들어간 요청은 budget이 남아도 healthy path를 망칠 수 있어서 concurrency와 queue cap이 함께 필요하다.

> Q: load shedding은 왜 필요한가요?
> 핵심: 일부 요청을 빨리 버려서 나머지 healthy request와 핵심 경로를 보호하기 위해서다.

> Q: 왜 같은 503이라도 retry 정책이 달라야 하나요?
> 핵심: local shedding, no healthy upstream, timeout의 의미가 다르기 때문이다.

## 한 줄 정리

retry storm containment은 재시도 횟수만 줄이는 문제가 아니라, queue와 concurrency를 함께 제한해 늦은 요청이 healthy path를 오염시키기 전에 fail-fast시키는 설계다.
