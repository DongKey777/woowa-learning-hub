---
schema_version: 3
title: "Service Mesh Local Reply, Timeout, Reset Attribution"
concept_id: network/service-mesh-local-reply-timeout-reset-attribution
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- service-mesh
- local-reply
- timeout-attribution
aliases:
- mesh local reply
- sidecar timeout
- Envoy local reply
- service mesh reset
- route timeout
- circuit breaking
- mTLS failure
- sidecar overload
symptoms:
- mesh sidecar local reply를 app이 반환한 status로 오해한다
- app timeout보다 짧은 route timeout 때문에 sidecar가 먼저 포기한 상황을 놓친다
- gRPC UNAVAILABLE/CANCELLED를 app grpc-status로만 보고 sidecar reset이나 mTLS failure를 보지 않는다
- sidecar overload나 adaptive concurrency rejection을 upstream app 장애로 blame한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/service-mesh-sidecar-proxy
- network/proxy-local-reply-vs-upstream-error-attribution
next_docs:
- network/adaptive-concurrency-limiter-latency-signal-gateway-mesh
- network/grpc-status-trailers-transport-error-mapping
- network/mesh-adaptive-concurrency-local-reply-metrics-tuning
- network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb
linked_paths:
- contents/network/service-mesh-sidecar-proxy.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/network/adaptive-concurrency-limiter-latency-signal-gateway-mesh.md
- contents/network/grpc-status-trailers-transport-error-mapping.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/network/mesh-adaptive-concurrency-local-reply-metrics-tuning.md
- contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md
confusable_with:
- network/proxy-local-reply-vs-upstream-error-attribution
- network/mesh-adaptive-concurrency-local-reply-metrics-tuning
- network/grpc-status-trailers-transport-error-mapping
- network/mtls-handshake-failure-diagnosis
forbidden_neighbors: []
expected_queries:
- "service mesh local reply가 app 응답인지 sidecar 응답인지 어떻게 구분해?"
- "route timeout이 app timeout보다 짧을 때 어떤 attribution 문제가 생겨?"
- "gRPC UNAVAILABLE이 sidecar reset이나 mTLS failure로 번역될 수 있는 이유는?"
- "mesh adaptive concurrency local reject와 no healthy upstream을 어떻게 나눠?"
- "Envoy sidecar local reply reason taxonomy를 어떤 metric으로 봐야 해?"
contextual_chunk_prefix: |
  이 문서는 service mesh sidecar local reply, route timeout, reset,
  circuit breaking, mTLS failure, adaptive concurrency reject와 app/upstream
  attribution을 다루는 advanced playbook이다.
---
# Service Mesh Local Reply, Timeout, Reset Attribution

> 한 줄 요약: mesh 환경의 local reply는 단순히 "프록시가 대신 응답했다"를 넘어서 route timeout, retry policy, circuit breaking, mTLS failure, sidecar overload가 어떤 표면 증상으로 번역되는지까지 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh](./adaptive-concurrency-limiter-latency-signal-gateway-mesh.md)
> - [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Mesh Adaptive Concurrency, Local Reply, Metrics Tuning](./mesh-adaptive-concurrency-local-reply-metrics-tuning.md)
> - [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

retrieval-anchor-keywords: mesh local reply, sidecar timeout, envoy local reply, service mesh reset, route timeout, circuit breaking, mTLS failure, sidecar overload, local origin failure, downstream translated error, local reply reason taxonomy, adaptive concurrency local reject, vendor symptom mapping, no healthy upstream

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

mesh sidecar는 upstream app과 caller 사이에서 독자적으로 결정을 내릴 수 있다.

- route timeout으로 local timeout reply
- circuit breaking / outlier detection으로 local reject
- adaptive concurrency나 local rate limit으로 shedding
- mTLS handshake failure로 transport-level abort

그래서 mesh 환경에서는 "app이 무엇을 반환했는가"뿐 아니라 **sidecar가 무엇을 대신 결정했는가**를 함께 봐야 한다.

### Retrieval Anchors

- `mesh local reply`
- `sidecar timeout`
- `envoy local reply`
- `service mesh reset`
- `route timeout`
- `circuit breaking`
- `mTLS failure`
- `sidecar overload`
- `local reply reason taxonomy`
- `vendor symptom mapping`

## 깊이 들어가기

### 1. mesh local reply는 gateway local reply보다 더 자주 숨어 있다

gateway는 팀이 인식하기 쉽다.  
하지만 sidecar는 앱 옆에 붙어 있어 "앱 일부"처럼 착각하기 쉽다.

그래서 이런 오판이 잦다.

- app 503으로 보였지만 sidecar local reply
- server `UNAVAILABLE`처럼 보였지만 실제론 mTLS/reset
- app timeout처럼 보였지만 route timeout이 더 짧았다

### 2. route timeout과 app timeout이 다르면 blame이 어긋난다

예:

- app 내부 timeout 1500ms
- mesh route timeout 800ms
- caller는 504/UNAVAILABLE
- app은 1.1초 후 완료 로그

이 경우 app은 "성공"했고 sidecar가 "포기"했다.

### 3. mesh의 reset은 app status를 지워 버릴 수 있다

sidecar가 stream을 reset하거나 connection을 끊으면:

- app의 trailer/status가 전달되지 않을 수 있다
- client는 transport-ish error를 본다
- observability는 sidecar와 app 로그를 함께 봐야 한다

특히 gRPC에서 이 차이가 크게 난다.

### 4. mTLS / identity 문제도 local origin failure처럼 보일 수 있다

mesh는 앱 대신 TLS를 많이 처리한다.

- SPIFFE/SAN mismatch
- expired cert
- trust bundle skew
- SDS/secret distribution lag

이 경우 app 코드는 멀쩡한데도 request는 app에 못 도달할 수 있다.

### 5. sidecar overload 자체가 또 다른 local reply 원인이다

mesh는 보호 계층이지만 리소스도 쓴다.

- sidecar CPU saturation
- queue growth
- buffer pressure
- connection pool pressure

이때 일부 요청은 app이 아니라 sidecar에서 먼저 잘릴 수 있다.

### 6. vendor symptom translation을 따로 알아야 한다

같은 사건도 표면이 다르다.

- HTTP: 503/504/local reset
- gRPC: UNAVAILABLE/CANCELLED/deadline-ish status
- metrics: upstream_rq_timeout, local_origin_fail, no_healthy_upstream 같은 카운터

즉 mesh local reply 해석은 vendor와 protocol 표면을 같이 알아야 한다.

### 7. local reply reason taxonomy를 유지해야 blame이 맞는다

`503`, `504`, `UNAVAILABLE`만으로는 부족하다. 최소한 아래 bucket은 분리해야 한다.

- route timeout local reply
- adaptive concurrency / local rate limit
- no healthy upstream / draining gap
- local origin transport fail (`mTLS`, connect, reset)
- downstream disconnect after partial response

이 taxonomy가 있어야 "app에 도달하지 않았는가", "app은 돌았지만 결과가 버려졌는가", "mesh가 다른 표면으로 번역했는가"를 나눌 수 있다.

### 8. 핵심 질문은 app이 안 돌았는가, 돌고도 결과가 버려졌는가, 결과가 번역됐는가다

| failure shape | app 로그 | sidecar evidence | caller surface | 읽는 법 |
|---------------|----------|------------------|----------------|---------|
| app 미도달 | 없음 | upstream connect 전 local reply, health/mTLS fail | 503/502/`UNAVAILABLE` | app bug보다 policy/transport 문제를 먼저 본다 |
| app은 완료했지만 sidecar가 먼저 timeout | 성공 로그 존재 | route timeout, deadline budget mismatch | 504/`UNAVAILABLE` | budget mismatch를 본다 |
| app가 응답했지만 trailers/body가 reset으로 유실 | 부분 로그 또는 성공 로그 가능 | reset reason, truncated stream | 502/`CANCELLED`/`UNAVAILABLE` | transport/reset 단계 문제다 |
| app 응답이 mesh overload 정책으로 대체 | app 로그가 없거나 일부만 존재 | overload/local reject counters | 503/429 | adaptive concurrency와 local rate limit을 구분한다 |

이 표를 머리에 두면 "app 로그가 있으니 app 책임" 또는 "503이니 무조건 capacity 부족" 같은 단정이 줄어든다.

### 9. translation layer가 늘수록 vendor symptom mapping을 같이 봐야 한다

sidecar -> ingress -> edge 순으로 갈수록 original reason이 평탄화된다.

- sidecar에선 local reply reason과 reset detail이 보인다
- ingress에선 502/503/504와 짧은 error text 정도로 축약된다
- edge/LB에선 target health, timeout, connection error 표면만 남는다

그래서 mesh local reply를 설명할 때는 [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)처럼 vendor별 surface와 같이 읽어야 한다.

## 실전 시나리오

### 시나리오 1: app은 건강한데 mesh 도입 후 503이 생긴다

route timeout, circuit breaking, local shedding을 먼저 의심할 만하다.

### 시나리오 2: gRPC status가 갑자기 transport error처럼 바뀐다

sidecar reset이 trailer 전달 전에 끼어든 패턴일 수 있다.

### 시나리오 3: 인증서 회전 직후 일부 서비스끼리만 통신이 끊긴다

app 버그보다 mTLS identity mismatch가 원인일 수 있다.

### 시나리오 4: scale-in 시 app 로그는 조용한데 sidecar가 응답을 자른다

drain 정책이 app와 sidecar에서 엇갈린 패턴일 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- response source: sidecar local reply or upstream app
- route timeout vs app timeout
- mTLS handshake / cert validation failures
- sidecar queue / CPU / buffer pressure
- gRPC trailers seen or lost before reset
- app이 안 돌았는지, 돌고도 결과가 사라졌는지
```

### 현장 질문

```text
- request가 app container까지 도달했는가
- app status가 caller까지 전달됐는가
- sidecar가 local policy로 먼저 끊은 것은 아닌가
- protocol 표면이 HTTP인지 gRPC인지에 따라 번역이 달라졌는가
- ingress/edge를 지나며 원래 reason bucket이 평탄화되지는 않았는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| mesh policy 적극 사용 | 보호와 일관성이 좋다 | blame과 디버깅이 더 어려워진다 | 대규모 mesh |
| app 중심 정책 | 책임 경계가 단순하다 | 중복 구현과 일관성 문제가 생긴다 | 작은 시스템 |
| rich sidecar observability | local reply 해석이 쉬워진다 | 수집과 운영 비용이 든다 | 운영 성숙 팀 |
| app-only dashboards | 단순하다 | sidecar가 만든 실패를 거의 못 본다 | 초기 단계만 적합 |

핵심은 mesh 환경의 실패를 app result 하나로 해석하지 않고 **sidecar policy, identity, reset, timeout의 합성 결과**로 보는 것이다.

## 꼬리질문

> Q: mesh local reply는 gateway local reply와 어떻게 다른가요?
> 핵심: 원리는 비슷하지만 sidecar는 앱 옆에 있어 더 숨기 쉽고, mTLS/route policy/stream reset 같은 mesh 고유 원인이 많다.

> Q: app이 성공 로그를 남겼는데 client는 실패할 수 있나요?
> 핵심: 가능하다. sidecar timeout/reset이 app 결과 전달 전에 끼어들 수 있다.

> Q: mesh 장애에서 왜 app 로그만 보면 안 되나요?
> 핵심: request가 app에 도달하지 않았거나, app 결과가 sidecar에서 번역/절단되었을 수 있기 때문이다.

## 한 줄 정리

mesh local reply를 제대로 해석하려면 app status와 sidecar policy를 분리해 보고, timeout/reset/mTLS failure가 caller 표면에 어떻게 번역됐는지까지 추적해야 한다.
