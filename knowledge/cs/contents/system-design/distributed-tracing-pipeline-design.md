---
schema_version: 3
title: Distributed Tracing Pipeline 설계
concept_id: system-design/distributed-tracing-pipeline-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- distributed tracing
- spans
- trace context
- head sampling
aliases:
- distributed tracing
- spans
- trace context
- head sampling
- tail sampling
- baggage
- span ingestion
- trace query
- exemplars
- service dependency graph
- high cardinality tags
- canary trace
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/metrics-pipeline-tsdb-design.md
- contents/system-design/trace-attribute-freshness-read-source-bridge.md
- contents/system-design/backpressure-and-load-shedding-design.md
- contents/system-design/api-gateway-control-plane-design.md
- contents/system-design/service-discovery-health-routing-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/multi-region-active-active-design.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/automated-canary-analysis-rollback-platform-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Distributed Tracing Pipeline 설계 설계 핵심을 설명해줘
- distributed tracing가 왜 필요한지 알려줘
- Distributed Tracing Pipeline 설계 실무 트레이드오프는 뭐야?
- distributed tracing 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Distributed Tracing Pipeline 설계를 다루는 deep_dive 문서다. distributed tracing pipeline은 요청이 여러 서비스를 건너갈 때 span과 context를 수집, 샘플링, 저장해 지연과 오류의 인과 경로를 복원하는 관측성 시스템이다. 검색 질의가 distributed tracing, spans, trace context, head sampling처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Distributed Tracing Pipeline 설계

> 한 줄 요약: distributed tracing pipeline은 요청이 여러 서비스를 건너갈 때 span과 context를 수집, 샘플링, 저장해 지연과 오류의 인과 경로를 복원하는 관측성 시스템이다.

retrieval-anchor-keywords: distributed tracing, spans, trace context, head sampling, tail sampling, baggage, span ingestion, trace query, exemplars, service dependency graph, high cardinality tags, canary trace, route cutover, release analysis

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md)
> - [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)

## 핵심 개념

로그가 "무슨 일이 있었는가"를 많이 알려 준다면,
트레이싱은 "어디를 거치며 느려졌는가"를 보여 준다.

실전 tracing 시스템은 다음을 같이 풀어야 한다.

- cross-service context propagation
- 대량 span ingest
- sampling 정책
- 고카디널리티 tag 폭발 제어
- trace query와 서비스 의존성 분석
- 장애 중에도 최소 가시성 유지

즉, tracing은 디버깅 도구가 아니라 **인과 관계를 저장하는 observability data plane**이다.

## 깊이 들어가기

### 1. span model과 context propagation

기본 단위는 span이다.

- trace id: 요청 전체를 묶는 식별자
- span id: 개별 작업 단위 식별자
- parent span id: 호출 관계
- attributes: route, tenant tier, db table 같은 메타데이터

중요한 것은 ID를 만드는 것보다, gateway에서 시작된 context가 queue, async worker, 배치 경계까지 이어지게 하는 것이다.

### 2. Capacity Estimation

예:

- 초당 요청 10만
- 요청당 평균 20 spans
- 1% 기본 샘플링
- incident 시 tail sampling 10%로 상향

이때 보는 숫자:

- accepted spans/sec
- dropped spans ratio
- ingest queue lag
- trace query latency
- storage retention
- tail sampling decision latency

tracing은 full fidelity로 다 저장하면 금방 비용이 폭발한다.

### 3. Head sampling과 tail sampling

샘플링은 trace의 운명을 언제 결정하느냐의 문제다.

- head sampling: 요청 시작 시 확률적으로 선택
- tail sampling: trace가 끝난 뒤 error, latency 조건을 보고 선택

head sampling은 단순하고 싸지만 중요한 trace를 놓칠 수 있다.
tail sampling은 관찰 가치가 높은 trace를 더 잘 남기지만 ingest와 buffering 비용이 높다.

### 4. 인덱스와 query 모델

대부분의 질의는 다음과 같다.

- 특정 trace id 조회
- 특정 서비스의 느린 trace 찾기
- 특정 route와 status 조건으로 최근 오류 trace 탐색
- 두 서비스 사이 호출 dependency 확인

그래서 저장소는 보통 두 층으로 나뉜다.

- raw span store
- query index 또는 service dependency projection

모든 tag를 전부 인덱싱하면 비용이 감당되지 않는다.

### 5. 고카디널리티 tag 제어

트레이싱도 cardinality 폭발에 취약하다.
문제가 되는 예:

- user_id
- request_id
- full SQL text
- unbounded error message

대응:

- 허용된 attribute allowlist
- value truncation
- route normalization
- exemplar만 metrics에 연결

즉, tracing은 자세한 데이터를 담되 무한정 자유롭게 두면 안 된다.

### 6. Metrics, logs와의 연결

트레이싱만으로 운영을 끝낼 수는 없다.

- metric에서 p95 spike를 본다
- exemplar나 trace link로 느린 trace를 찾는다
- 필요하면 관련 structured log를 본다

세 신호를 연결해야 문제의 표면과 원인을 같이 볼 수 있다.
특히 cutover 중에는 primary/candidate route, backend version, shadow/canary 여부를 span attribute로 남겨 diff와 guardrail을 빠르게 좁히는 편이 유용하다.

### 7. 장애 중 tracing 자체를 보호해야 한다

관측성 시스템이 장애 증폭자가 되면 안 된다.

대응:

- local batching
- bounded queue
- overload 시 low-priority span drop
- control plane 장애 시 static sampling fallback

즉, tracing도 [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md) 원칙을 그대로 적용해야 한다.

## 실전 시나리오

### 시나리오 1: API p95 급증 원인 추적

문제:

- metrics는 느려졌다는 사실만 보여 준다

해결:

- gateway span에서 느린 request exemplar를 찾는다
- DB, cache, downstream RPC span을 따라 병목 hop을 확인한다
- 특정 zone이나 endpoint에 편중되는지 service graph로 본다

### 시나리오 2: incident 중 샘플링 상향

문제:

- 평소에는 1% 샘플링이라 재현 trace가 부족하다

해결:

- error status와 특정 route에 대해 tail sampling 비율을 높인다
- 전체 traffic이 아니라 문제 구간만 증량한다
- incident 종료 후 기본 정책으로 복귀한다

### 시나리오 3: 비동기 경계에서 trace 끊김

문제:

- queue를 거치면 parent-child 관계가 사라진다

해결:

- message metadata에 trace context를 담는다
- async consumer는 새로운 span을 만들되 링크 관계를 남긴다
- batch worker는 fan-in/fan-out semantics를 분리해 기록한다

## 코드로 보기

```pseudo
function handleRequest(req):
  ctx = tracer.extract(req.headers)
  span = tracer.startSpan("gateway.request", ctx)
  try:
    res = downstream.call(withTraceHeaders(req, span.context))
    span.tag("status", res.status)
    return res
  finally:
    tracer.finish(span)

function export(spanBatch):
  if overload():
    dropLowPriority(spanBatch)
  collector.send(spanBatch)
```

```java
public ServerResponse intercept(ServerRequest request) {
    TraceContext context = propagator.extract(request.headers());
    Span span = tracer.startSpan("http.request", context);
    return next.handle(request).doFinally(signal -> span.finish());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Full tracing | 디버깅이 쉽다 | 비용이 매우 크다 | 작은 트래픽, 단기 분석 |
| Head sampling | 단순하고 싸다 | 중요한 trace를 놓칠 수 있다 | 기본 운영 |
| Tail sampling | 가치 높은 trace를 남기기 쉽다 | buffering과 결정 지연이 필요하다 | incident 대응, 고가치 서비스 |
| Raw span only | 저장이 단순하다 | 검색이 어렵다 | 초기 시스템 |
| Indexed trace query | 탐색이 쉽다 | 인덱스 비용이 든다 | 다수 서비스 운영 |

핵심은 distributed tracing이 로그의 대체재가 아니라 **요청 경로의 인과 관계를 복원해 주는 관측성 파이프라인**이라는 점이다.

## 꼬리질문

> Q: trace와 log는 어떻게 다른가요?
> 의도: 관측 신호의 역할 구분 확인
> 핵심: trace는 호출 관계와 지연 경로를, log는 개별 사건의 상세 내용을 더 잘 보여 준다.

> Q: tail sampling은 왜 비싼가요?
> 의도: 샘플링 시점의 비용 이해 확인
> 핵심: trace가 끝날 때까지 span을 버퍼링하고 판단해야 하기 때문이다.

> Q: trace tag에 user_id를 넣으면 안 되나요?
> 의도: cardinality 감각 확인
> 핵심: 무한한 식별자는 인덱스와 저장 비용을 폭발시킬 수 있다.

> Q: tracing pipeline이 장애나면 어떻게 해야 하나요?
> 의도: observability 시스템의 자기 보호 이해 확인
> 핵심: bounded queue, fallback sampling, selective drop으로 본 시스템을 우선 보호해야 한다.

## 한 줄 정리

Distributed tracing pipeline은 여러 서비스를 가로지르는 요청의 span과 context를 수집, 샘플링, 질의 가능하게 저장해 지연과 오류의 인과 경로를 복원하는 관측성 시스템이다.
