---
schema_version: 3
title: Traffic Shadowing / Progressive Cutover 설계
concept_id: system-design/traffic-shadowing-progressive-cutover-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- traffic shadowing
- shadow traffic
- progressive cutover
- canary analysis
aliases:
- traffic shadowing
- shadow traffic
- progressive cutover
- canary analysis
- mirrored requests
- diffing
- dark launch
- route guardrail
- weighted routing
- abort switch
- read-only mirror
- automated rollback
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/api-gateway-control-plane-design.md
- contents/system-design/feature-flag-control-plane-design.md
- contents/system-design/service-discovery-health-routing-design.md
- contents/system-design/distributed-tracing-pipeline-design.md
- contents/system-design/zero-downtime-schema-migration-platform-design.md
- contents/system-design/search-indexing-pipeline-design.md
- contents/system-design/automated-canary-analysis-rollback-platform-design.md
- contents/system-design/dual-read-comparison-verification-platform-design.md
- contents/system-design/database-security-identity-bridge-cutover-design.md
- contents/system-design/dual-write-avoidance-migration-bridge-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Traffic Shadowing / Progressive Cutover 설계 설계 핵심을 설명해줘
- traffic shadowing가 왜 필요한지 알려줘
- Traffic Shadowing / Progressive Cutover 설계 실무 트레이드오프는 뭐야?
- traffic shadowing 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Traffic Shadowing / Progressive Cutover 설계를 다루는 deep_dive 문서다. traffic shadowing과 progressive cutover는 새 경로를 실제 운영 트래픽으로 검증하되, write side effect와 blast radius를 통제하면서 점진적으로 승격하는 라우팅 운영 시스템이다. 검색 질의가 traffic shadowing, shadow traffic, progressive cutover, canary analysis처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Traffic Shadowing / Progressive Cutover 설계

> 한 줄 요약: traffic shadowing과 progressive cutover는 새 경로를 실제 운영 트래픽으로 검증하되, write side effect와 blast radius를 통제하면서 점진적으로 승격하는 라우팅 운영 시스템이다.
>
> 문서 역할: 이 문서는 migration / replay / cutover cluster 안에서 **검증 기반 승격과 blast-radius 제어**를 맡는 deep dive다.

retrieval-anchor-keywords: traffic shadowing, shadow traffic, progressive cutover, canary analysis, mirrored requests, diffing, dark launch, route guardrail, weighted routing, abort switch, read-only mirror, automated rollback, dual read verification, cutover observability, write freeze, rollback window, receiver warmup, migration bridge, database security bridge, auth shadow evaluation, auth plugin parity, authorization decision parity, tenant route auth drift

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Tenant Split-Out with Service Identity Rollout 설계](./tenant-split-out-service-identity-rollout-design.md)
> - [Service Mesh Control Plane 설계](./service-mesh-control-plane-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)

## 이 문서 다음에 보면 좋은 설계

- schema / read-path 호환성 문제는 [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)와 같이 봐야 한다.
- 실제 비교/차이 수집은 [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)로 이어진다.
- 자동 승격과 rollback guardrail은 [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)에서 더 깊게 다룬다.
- stateful receiver handoff의 warmup, freeze, rollback soak은 [Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md), [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)로 이어진다.
- 검증이 끝난 뒤 rollback을 닫는 cleanup 경계는 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)에서 따로 다룬다.
- 라우팅 shadowing이 identity/auth plugin 전환과 같이 움직이면 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md), [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)을 함께 봐야 한다.

## 핵심 개념

새 시스템으로 전환할 때 가장 무서운 순간은 "처음 실제 트래픽을 받는 순간"이다.
이때 바로 100% cutover를 하면 장애 반경이 너무 크다.

실전에서는 보통 세 단계를 구분한다.

- **dark launch**: 새 경로를 띄우지만 사용자 응답에는 사용하지 않는다
- **shadowing**: 실제 요청을 복제해 새 경로에도 보내지만 결과는 참조용으로만 본다
- **progressive cutover**: 일부 사용자나 일부 비율만 새 경로 응답을 실제로 사용한다

즉, 핵심은 새 경로의 정확성과 성능을 점진적으로 증명한 뒤 승격하는 것이다.

## 깊이 들어가기

### 1. shadowing과 canary는 다르다

둘 다 "조금씩 검증"처럼 보이지만 질문이 다르다.

- shadowing: 새 경로가 같은 입력을 받았을 때 비슷한 결과를 내는가
- canary: 새 경로가 실제 응답 경로로 올라와도 SLO와 비즈니스 메트릭을 버티는가

따라서 shadowing은 diff와 정합성이 중심이고,
canary는 latency, error rate, saturation, rollback이 중심이다.

### 2. Capacity Estimation

예:

- 초당 8만 요청
- shadow traffic 비율 20%
- 요청당 평균 payload 4 KB
- candidate path가 CPU 1.8배 더 무겁다

이때 봐야 할 숫자:

- mirrored request QPS
- shadow path CPU/memory headroom
- diff sampling rate
- canary error budget burn
- abort-to-recover 시간

shadowing은 응답에 사용하지 않아도 인프라 비용은 실제로 두 배 가까이 늘 수 있다.

### 3. Routing control plane

보통 구조는 다음과 같다.

```text
Client
  -> Edge / Gateway
  -> Traffic Router
      -> Primary Path
      -> Shadow Path
      -> Candidate Path
  -> Diff Collector / Guardrail Evaluator
```

여기서 control plane이 관리하는 것은 단순 비율이 아니다.

- 어떤 route를 shadow할지
- 어떤 tenant만 canary할지
- 어떤 응답 필드까지 diff할지
- 어떤 지표가 나빠지면 자동 rollback할지

### 4. write traffic은 그대로 shadow하면 안 된다

가장 흔한 사고는 write 요청을 후보 시스템에 그대로 복제하는 것이다.

위험:

- 외부 결제나 이메일이 중복 실행
- side effect가 실제로 반영됨
- 두 경로의 상태가 서로 오염됨

대응:

- read-only endpoint만 shadow
- candidate path는 noop side effect로 실행
- write는 synthetic sink 또는 sandbox dependency 사용
- idempotency namespace를 분리

즉, shadowing은 "실제 입력 재생"이지 "실제 세상에 다시 쓰기"가 아니다.

### 5. Diffing 전략

candidate 응답이 완전히 같아야 하는 것은 아니다.
실전 diff는 다음을 구분해야 한다.

- 허용 가능한 필드 차이
- 정렬 순서 차이
- floating point / score 오차
- freshness 차이
- 정책상 반드시 같아야 하는 invariant

그래서 보통은 raw diff보다 normalized diff를 쓴다.
정합성 비교 규칙을 미리 정의하지 않으면 false positive만 늘어난다.
read-heavy migration에서는 route shadowing만으로 부족할 수 있어, sampled dual-read comparison으로 invariant와 semantic diff를 별도 축적하는 편이 좋다.

### 6. Guardrail과 관측성

progressive cutover에서 봐야 할 것은 단순 5xx 비율이 아니다.

- p95/p99 latency
- timeout / retry amplification
- downstream saturation
- business metric guardrail
- diff mismatch ratio

그리고 이 지표는 route/tenant/version 단위로 잘라 볼 수 있어야 한다.
그래야 "전체 평균은 괜찮지만 특정 tenant만 망가지는" 경우를 빨리 잡는다.
실무에서는 이 계층 위에 automated canary analysis가 올라가 promotion, pause, rollback을 결정하는 편이 많다.
또한 cutover 중 어떤 지점이 rollback boundary 안에 있는지, 어떤 config/schema change가 이미 point-of-no-return을 넘겼는지는 별도 rollback safety envelope로 관리하는 편이 좋다.

### 7. mirrored request 검증과 auth shadow evaluation은 분리해서 봐야 한다

traffic shadowing은 live input과 라우팅 압력을 재현하는 데 강하지만, database/security bridge에서는 이것만으로 충분하지 않다.

- mirrored shadow는 gateway, router, auth plugin, downstream saturation을 본다
- dual-read comparison은 같은 요청이 같은 data/response invariant를 내는지 본다
- auth shadow evaluation은 같은 request context에서 old/new policy가 같은 allow/deny를 내는지 본다

예를 들어 다음은 충분히 가능하다.

- mirrored request는 둘 다 200인데 shadow decision log에서는 `old_deny -> new_allow`가 누적된다
- route shadow는 green인데 dual-read compare에서는 stale projection mismatch가 남는다
- foreground route는 정상이지만 tenant split-out 뒤 background worker principal drift가 shadow traffic 밖에서 남는다

그래서 auth plugin, claim parser, SPIFFE allowlist, tenant route cutover가 함께 움직이면
[Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md),
[Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md),
[Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)을 같은 승격 경로로 묶는 편이 안전하다.

핵심은 traffic shadowing이 verification input capture를 맡고, 의미 비교는 dual-read와 auth shadow evaluation으로 분리된다는 점이다.

### 8. Abort switch와 rollback

cutover는 시작보다 중단이 더 중요하다.
좋은 시스템은 다음을 갖는다.

- 즉시 0%로 되돌리는 abort switch
- sticky session이 있다면 안전한 drain 절차
- rollback 후 shadow mode로 복귀
- incident 동안 sampling 확장과 diff 보존

cutover와 cleanup을 한 번에 하지 말고, rollback 가능한 관찰 기간을 남겨 두는 편이 안전하다.

## 실전 시나리오

### 시나리오 1: 검색 엔진 교체

문제:

- 새 검색 클러스터와 ranking 모델을 실제 쿼리로 검증해야 한다

해결:

- 검색 요청을 shadow path로 복제한다
- 결과 top-k diff와 latency 분포를 비교한다
- 특정 tenant와 내부 사용자부터 progressive cutover를 시작한다

### 시나리오 2: 새 API gateway 도입

문제:

- 라우팅 규칙과 auth plugin이 실제 트래픽을 버틸지 불확실하다

해결:

- read-heavy route부터 shadowing한다
- trace와 metric으로 upstream hop latency를 비교한다
- auth plugin old/new allow/deny divergence를 shadow log로 분리한다
- canary percentage를 점진적으로 올리고 abort switch를 유지한다

### 시나리오 3: 리전별 routing 정책 전환

문제:

- 특정 region을 새 path로 우회하고 싶다

해결:

- region 단위 route override를 control plane에서 버전 관리한다
- same-session stickiness를 유지한다
- regional error budget이 나빠지면 즉시 이전 path로 되돌린다

## 코드로 보기

```pseudo
function handle(request):
  primary = routes.primary(request)
  shadow = routes.shadowCandidate(request)
  if shadow.enabled:
    asyncMirror(request, shadow, mode="NO_SIDE_EFFECT")

  candidate = routes.canaryCandidate(request)
  if candidate.matches(request):
    response = send(request, candidate)
    guardrail.observe(request, response, candidate.version)
    return response

  return send(request, primary)

function asyncMirror(request, target, mode):
  mirrored = sanitizeForShadow(request, mode)
  result = send(mirrored, target)
  diffCollector.compare(request.id, result)
```

```java
public RouteDecision decide(RequestContext ctx) {
    if (cutoverPolicy.shouldCanary(ctx)) {
        return RouteDecision.candidate();
    }
    if (cutoverPolicy.shouldShadow(ctx)) {
        shadowExecutor.mirror(ctx);
    }
    return RouteDecision.primary();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Big bang cutover | 빠르다 | blast radius가 크다 | 작은 내부 시스템 |
| Shadow-only validation | 정합성 검증이 좋다 | 실제 응답 경로 위험은 못 본다 | 초기 검증 단계 |
| Canary cutover | 실제 사용자 영향을 제한한다 | guardrail과 rollback이 필요하다 | 대부분의 실서비스 |
| Full response diffing | 정확성 검증이 좋다 | 비용과 false positive가 높다 | 검색/추천/정책 엔진 |
| Read-only shadow | 안전하다 | write path 검증은 별도로 필요하다 | 외부 side effect가 큰 시스템 |

핵심은 traffic shadowing과 progressive cutover가 라우팅 기능이 아니라 **실제 트래픽으로 새 경로를 검증하고 승격하는 운영 제어 절차**라는 점이다.

## 꼬리질문

> Q: shadowing만 통과하면 바로 cutover해도 되나요?
> 의도: shadow와 canary의 차이 이해 확인
> 핵심: 아니다. shadow는 정합성 확인에 가깝고, 실제 응답 경로의 latency와 failure mode는 canary에서 따로 봐야 한다.

> Q: write 요청도 shadow하면 더 현실적인 검증 아닌가요?
> 의도: side effect 위험 이해 확인
> 핵심: 외부 영향과 상태 오염이 생길 수 있어 noop sink, sandbox, idempotency 분리가 필요하다.

> Q: diff mismatch가 조금 있어도 괜찮을 수 있나요?
> 의도: comparison semantics 이해 확인
> 핵심: 정렬, freshness, score 차이는 허용될 수 있으므로 invariant 중심으로 diff 규칙을 설계해야 한다.

> Q: rollback을 빠르게 하려면 무엇이 가장 중요한가요?
> 의도: cutover 운영 감각 확인
> 핵심: abort switch, sticky drain, clear guardrail, cleanup 지연이 중요하다.

## 한 줄 정리

Traffic shadowing과 progressive cutover는 실제 운영 트래픽으로 새 경로를 검증하면서도 side effect와 blast radius를 통제해 안전하게 승격하는 라우팅 운영 시스템이다.
