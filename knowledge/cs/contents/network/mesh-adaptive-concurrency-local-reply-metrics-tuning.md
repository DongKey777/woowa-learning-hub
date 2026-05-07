---
schema_version: 3
title: "Mesh Adaptive Concurrency, Local Reply, Metrics Tuning"
concept_id: network/mesh-adaptive-concurrency-local-reply-metrics-tuning
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- adaptive-concurrency
- service-mesh
- local-reply
aliases:
- mesh adaptive concurrency
- sidecar local reply metrics
- inflight limit tuning
- route-level limiter
- adaptive concurrency metrics
- local reply reason
- latency sample window
symptoms:
- sidecar가 가끔 503을 만든다고만 보고 inflight limit과 local reply reason을 보지 않는다
- adaptive concurrency sample window가 너무 짧아 limiter가 요동치는 문제를 놓친다
- route class를 분리하지 않아 streaming이나 admin traffic이 핵심 unary route와 같이 잘린다
- app service time과 sidecar local reply metric을 같은 timeline에 놓지 않는다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/adaptive-concurrency-limiter-latency-signal-gateway-mesh
- network/service-mesh-local-reply-timeout-reset-attribution
next_docs:
- network/queue-saturation-attribution-metrics-runbook
- network/proxy-local-reply-vs-upstream-error-attribution
- network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb
- network/retry-storm-containment-concurrency-limiter-load-shedding
linked_paths:
- contents/network/adaptive-concurrency-limiter-latency-signal-gateway-mesh.md
- contents/network/service-mesh-local-reply-timeout-reset-attribution.md
- contents/network/service-mesh-sidecar-proxy.md
- contents/network/queue-saturation-attribution-metrics-runbook.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md
confusable_with:
- network/adaptive-concurrency-limiter-latency-signal-gateway-mesh
- network/service-mesh-local-reply-timeout-reset-attribution
- network/proxy-local-reply-vs-upstream-error-attribution
- network/queue-saturation-attribution-metrics-runbook
forbidden_neighbors: []
expected_queries:
- "mesh adaptive concurrency local reply metric을 어떻게 읽어야 해?"
- "sidecar 503이 adaptive concurrency limit 때문인지 upstream 오류인지 구분하는 법은?"
- "latency sample window가 짧으면 limiter가 왜 요동쳐?"
- "route class isolation 없이 adaptive concurrency를 켜면 어떤 문제가 생겨?"
- "inflight limit, local reply reason, app service time을 같이 보는 방법은?"
contextual_chunk_prefix: |
  이 문서는 service mesh adaptive concurrency의 inflight limit, latency sample
  window, sidecar local reply reason, route class isolation, metric tuning을
  다루는 advanced playbook이다.
---
# Mesh Adaptive Concurrency, Local Reply, Metrics Tuning

> 한 줄 요약: mesh adaptive concurrency는 켜는 것보다 읽는 게 더 어렵다. inflight limit, latency sample, local reply reason, route class를 함께 보지 않으면 "sidecar가 가끔 503을 만든다" 정도로만 보인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh](./adaptive-concurrency-limiter-latency-signal-gateway-mesh.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
> - [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

retrieval-anchor-keywords: mesh adaptive concurrency, sidecar local reply metrics, inflight limit tuning, route-level limiter, mesh 503 tuning, adaptive concurrency metrics, local reply reason, latency sample window, route class isolation, sidecar overload tuning, adaptive concurrency local reply, route timeout vs overload, no healthy upstream, vendor symptom mapping, envoy overload symptom

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

mesh adaptive concurrency 튜닝은 세 가지를 함께 본다.

- limit이 어떻게 바뀌는가
- 어떤 신호가 그 변화를 유도했는가
- local reply가 어떤 route/class에서 얼마만큼 나오는가

즉 "adaptive concurrency enabled"는 시작점일 뿐이고, 실제 운영은 **metric interpretation 문제**다.

### Retrieval Anchors

- `mesh adaptive concurrency`
- `sidecar local reply metrics`
- `inflight limit tuning`
- `route-level limiter`
- `adaptive concurrency metrics`
- `local reply reason`
- `latency sample window`
- `route class isolation`
- `adaptive concurrency local reply`
- `no healthy upstream`
- `vendor symptom mapping`

## 깊이 들어가기

### 1. inflight limit 자체보다 변경 추세가 중요하다

고정 숫자보다 중요한 것은:

- limit이 언제 올라가고 내려가는가
- route별 차이가 있는가
- deployment, retry spike, downstream slowdown과 상관있는가

limit의 절대값만 보면 튜닝 포인트를 놓친다.

### 2. sample window가 너무 짧으면 limiter가 요동친다

adaptive limiter는 관측된 latency를 본다.

- 샘플이 너무 짧으면 noise에 민감
- 너무 길면 overload를 늦게 봄

그래서 tuning은 흔히:

- route 성격
- batch vs unary
- mobile spike vs steady traffic

에 따라 다르게 가져가야 한다.

### 3. local reply reason은 route-level로 봐야 한다

전체 503만 보면 오해한다.

- 어떤 route가 잘리는가
- control plane / health / admin traffic도 같이 잘리는가
- streaming route가 unary route를 잡아먹는가

adaptive concurrency는 class-aware하지 않으면 중요한 경로를 같이 희생시킬 수 있다.

### 4. sidecar metric과 app metric을 같은 축에 놓아야 한다

유용한 조합:

- sidecar inflight / limit
- sidecar local reply reason
- app service time
- queue wait
- downstream pool saturation

이렇게 봐야 limiter가:

- 실제 app slowdown에 반응한 것인지
- sidecar own overload에 반응한 것인지

를 알 수 있다.

### 5. false positive shedding도 문제다

adaptive concurrency는 보호 장치지만 과민하면:

- healthy request까지 잘림
- cacheable/public route도 unnecessary 503
- user 체감은 악화

그래서 성공률과 p99를 같이 봐야 한다.

### 6. tuning 목표는 "에러 0"이 아니라 "healthy path 유지"다

중요한 건 일부 rejection이 아니라:

- 핵심 route latency가 유지되는가
- collapse를 막았는가
- queue가 무한히 늘지 않는가

즉 일부 503 증가는 의도된 보호일 수 있다.

### 7. 숫자를 올리기 전에 traffic class를 먼저 분리해야 한다

adaptive concurrency가 global하게 붙어 있으면 tuning 숫자보다 분리 전략이 먼저다.

- health, admin, control plane은 가능하면 별도 budget이나 bypass
- unary user API와 batch/streaming route는 limiter를 분리
- retry-heavy caller와 bulk traffic도 class를 나눈다

이 분리가 없으면 "limit을 조금 올렸더니 핵심 API만 다시 무너진다" 같은 현상이 반복된다.

### 8. local reply는 reason bucket으로 먼저 재분류해야 한다

`503` 하나로 묶지 말고 reason bucket을 먼저 만든다.

| reason bucket | 실제 의미 | 먼저 비교할 축 | tuning 포인트 |
|---------------|-----------|----------------|---------------|
| adaptive concurrency shedding | latency signal이 queue collapse를 막으려고 locally reject | current limit 추세, inflight usage, app service time, retry burst | limit 숫자보다 sample window와 route class 분리부터 본다 |
| local rate limit | quota/policy ceiling 초과 | principal/route별 token depletion, auth/rate-limit policy | concurrency tuning과 별개로 quota 설계를 본다 |
| route timeout local reply | app이 늦어서라기보다 mesh budget이 먼저 소진 | route timeout, upstream service time, timeout propagation | timeout budget 정렬이 우선이다 |
| no healthy upstream / drain gap | endpoint health/readiness/drain 문제가 먼저 | rollout timing, health check, endpoint membership | limit 상향보다 readiness/drain 수정이 우선이다 |
| local origin transport failure | mTLS, pool, connect/reset 등 transport 계층 문제 | handshake/reset reason, connection error, pool pressure | adaptive concurrency 원인으로 오인하지 않도록 분리한다 |

이렇게 나누면 "503이 늘었다"를 "어떤 보호 계층이 왜 개입했는가"로 바꿔 읽게 된다.

### 9. vendor symptom mapping은 source와 phase를 보존해야 한다

mesh 내부에선 reason을 알고 있어도, 바깥으로 나가면 vendor surface가 달라진다.

| generic cause | Envoy/mesh에서 먼저 보이는 것 | Nginx/ingress에서 흔한 표면 | ALB/front door에서 흔한 표면 | 흔한 오판 |
|---------------|------------------------------|------------------------------|------------------------------|-----------|
| adaptive concurrency shedding | local reply, overload 계열 카운터, limit drop, upstream time 거의 0 | ingress 503/429, upstream time이 매우 짧음 | edge 503/5xx, app target은 비교적 건강 | app capacity 503으로 단정 |
| route timeout before app reply | route timeout 증가, app 완료 로그는 뒤늦게 남음 | `504`와 timeout 문구 | `504` 또는 target timeout 계열 | app handler만 blame |
| no healthy upstream / drain gap | cluster membership 감소, health/readiness 흔들림 | rollout 중 502/503 | unhealthy target / 503 성격 | adaptive limit을 올리려 함 |
| local origin transport failure | handshake/reset/connect failure detail | 502/bad gateway 계열 | 502/connection error 계열 | app bug로 오해 |

같은 사건을 sidecar, ingress, edge에서 각각 다르게 보더라도, `source=local reply인가`, `phase=upstream connect 전인가 후인가`를 보존하면 blame이 덜 틀어진다.

### 10. tuning loop는 reject 수보다 protected path를 기준으로 닫는다

좋은 tuning loop는 다음 순서를 반복한다.

1. 핵심 route와 비핵심 route를 분리해 baseline을 만든다.
2. local reply를 reason bucket으로 재분류한다.
3. route/class별 success rate, p95/p99, reject ratio를 같이 본다.
4. sample window나 update cadence를 조정한 뒤 vendor surface에서 같은 사건이 어떻게 보이는지 재검증한다.
5. rejection만 줄고 핵심 path latency가 무너지면 rollback한다.

즉 목표는 reject zero가 아니라 **핵심 경로 latency와 availability를 지키는 것**이다.

## 실전 시나리오

### 시나리오 1: rollout 뒤 sidecar 503이 늘어 app 팀이 패닉한다

adaptive concurrency가 overload를 드러낸 것일 수 있으므로, limit trend와 local reply reason을 먼저 봐야 한다.

### 시나리오 2: batch route 시작 뒤 user API만 느려진다

route class 분리가 부족하거나 limiter가 global하게 적용된 패턴일 수 있다.

### 시나리오 3: limiter를 켰는데 p99는 좋아졌지만 에러율이 올랐다

의도된 trade-off인지, false positive shedding인지 local reply 분포와 business-critical route를 같이 봐야 한다.

### 시나리오 4: same traffic인데 어떤 cluster만 adaptive limit이 요동친다

latency sample window, sidecar resource pressure, downstream path variability 차이를 의심할 수 있다.

### 시나리오 5: sidecar에서는 overload로 보이는데 ingress 대시보드에는 generic 503만 찍힌다

vendor symptom mapping과 source tag가 빠져 있어 같은 사건이 팀마다 다른 장애로 보이는 패턴일 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- current inflight limit
- inflight usage vs limit
- local reply reason bucket vs raw 503 count
- route/class별 reject ratio
- app service time vs sidecar queue time
- sample window / update cadence
- ingress/edge surface와 sidecar reason의 crosswalk
```

### 운영 감각

```text
limit oscillates?
  sample too noisy or workload mix too wide
rejections on critical route?
  split route/class
local reply grows but app is healthy?
  distinguish overload from timeout/drain/transport first
edge shows only generic 503?
  preserve source and phase across vendor surfaces
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| fast-reacting limiter | overload를 빨리 감지한다 | jitter/noise에 민감하다 | 짧은 burst 방어 |
| slow-reacting limiter | 안정적이다 | collapse 직전 반응이 늦을 수 있다 | steady workload |
| global mesh limit | 단순하다 | route interference가 크다 | 작은 mesh |
| route/class-aware tuning | 핵심 경로 보호가 좋다 | 운영 복잡도가 늘어난다 | 대규모 mixed traffic |

핵심은 adaptive concurrency를 "켜면 끝"이 아니라 **limit 추세, reject 이유, route class별 영향**을 함께 읽는 운영 기능으로 보는 것이다.

## 꼬리질문

> Q: mesh adaptive concurrency 튜닝에서 가장 중요한 지표는 무엇인가요?
> 핵심: current limit, inflight usage, local reply reason, route/class별 reject 분포를 함께 보는 것이다.

> Q: 에러율이 조금 늘었는데 p99가 좋아졌으면 실패인가요?
> 핵심: 아니다. healthy path 보호 목적의 의도된 trade-off일 수 있다.

> Q: 왜 route class 분리가 필요한가요?
> 핵심: global limiter는 batch/streaming 경로가 latency-sensitive unary route를 같이 해칠 수 있기 때문이다.

## 한 줄 정리

mesh adaptive concurrency는 단순한 limiter가 아니라 sidecar local reply와 latency signal을 함께 읽어야 하는 운영 기능이라서, route별 reject 이유와 inflight 추세를 같이 보는 순간 제대로 튜닝할 수 있다.
