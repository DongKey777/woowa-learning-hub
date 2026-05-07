---
schema_version: 3
title: Contract Drift Detection and Rollout Governance
concept_id: software-engineering/contract-drift-governance
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- contract-drift
- rollout-governance
- runtime-compatibility
aliases:
- Contract Drift Detection and Rollout Governance
- contract drift detection
- producer consumer drift
- runtime compatibility drift
- semantic drift rollout pause
- contract rollout governance
symptoms:
- contract drift를 schema diff로만 보고 producer 선언, 실제 payload, consumer parser/fallback/business rule이 어긋나는 semantic drift를 놓쳐
- additive change, field removal, enum emission, semantic reinterpretation을 같은 rollout 경로로 처리해 consumer tolerance 배포 순서와 pause 기준이 흐려져
- runtime parse error, unknown enum fallback, semantic diff, version skew 신호가 registry와 owner/pause authority에 연결되지 않아
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- software-engineering/backward-compatibility-gates
- software-engineering/contract-registry-governance
next_docs:
- software-engineering/consumer-migration-playbook
- software-engineering/compatibility-waiver-governance
- software-engineering/strangler-verification-shadow-traffic-metrics
linked_paths:
- contents/software-engineering/backward-compatibility-test-gates.md
- contents/software-engineering/contract-registry-governance.md
- contents/software-engineering/consumer-migration-playbook-contract-adoption.md
- contents/software-engineering/rollout-approval-workflow.md
- contents/software-engineering/strangler-verification-shadow-traffic-metrics.md
- contents/software-engineering/backward-compatibility-waiver-consumer-exception-governance.md
confusable_with:
- software-engineering/backward-compatibility-gates
- software-engineering/contract-registry-governance
- software-engineering/consumer-migration-playbook
forbidden_neighbors: []
expected_queries:
- contract drift detection은 schema diff가 아니라 producer declared contract, produced behavior, consumed behavior 차이를 보는 거야?
- 새 enum emission이나 optional field가 parser는 통과해도 silent misclassification을 만들 수 있는 이유를 설명해줘
- additive change, field removal, semantic reinterpretation은 producer/consumer rollout 순서를 어떻게 달리해야 해?
- runtime unknown enum fallback rate, semantic diff rate, version skew를 rollout pause 기준에 어떻게 연결해?
- contract registry와 telemetry가 닫힌 루프를 만들어야 drift governance가 작동하는 이유는 뭐야?
contextual_chunk_prefix: |
  이 문서는 contract drift를 declared contract, produced payload, consumed behavior 사이의 semantic/runtime mismatch로 보고 rollout pause, registry update, consumer impact governance로 연결하는 advanced playbook이다.
---
# Contract Drift Detection and Rollout Governance

> 한 줄 요약: contract drift detection은 schema diff를 찾는 기능이 아니라, producer 선언과 consumer 기대, runtime 실제 사용이 어긋나는 순간을 잡아 rollout 순서와 중단 기준으로 연결하는 운영 체계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Backward Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Contract Registry Governance](./contract-registry-governance.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Rollout Approval Workflow](./rollout-approval-workflow.md)
> - [Strangler Verification, Shadow Traffic Metrics](./strangler-verification-shadow-traffic-metrics.md)
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)

> retrieval-anchor-keywords:
> - contract drift detection
> - producer consumer drift
> - rollout governance
> - runtime compatibility
> - semantic drift
> - shadow compare
> - version skew
> - rollout pause

## 핵심 개념

계약이 깨지는 순간은 항상 "breaking change를 배포한 순간"과 같지 않다.
실무에서는 producer가 안전하다고 생각한 변경이 consumer별 parser, fallback, business rule 차이 때문에 뒤늦게 문제를 만든다.

그래서 drift는 단순 schema diff보다 더 넓게 봐야 한다.

- declared contract: 문서, schema, version policy, deprecation rule
- produced behavior: 실제 payload, enum emission, default 값, 순서, null 처리
- consumed behavior: consumer parser, unknown field tolerance, fallback logic, business invariant

이 세 축이 벌어지기 시작하면 contract drift가 생긴다.

중요한 것은 drift를 "테스트 실패"로만 다루지 않는 것이다.
좋은 운영 체계는 drift를 다음 흐름으로 연결한다.

- 조기 탐지
- 영향 consumer 식별
- rollout 단계 조정
- pause/rollback 결정
- 사후 학습과 registry 갱신

즉 contract drift detection은 호환성 검사의 한 종류가 아니라, **producer와 consumer가 다른 속도로 바뀌는 상황을 통제하는 governance loop**다.

---

## 깊이 들어가기

### 1. drift는 breaking change보다 먼저 시작된다

drift는 보통 배포 실패보다 먼저 나타난다.

예:

- producer는 새 enum 값을 내보내기 시작했지만, 일부 consumer는 unknown value를 fallback 처리하고 있어 장애가 아니라 silent misclassification이 난다
- 문서에는 optional field라고 적혀 있지만, 실제 consumer는 그 필드가 없으면 다른 API를 연쇄 호출해 latency와 비용이 급증한다
- schema는 유지됐지만 의미가 바뀌어 settlement, analytics, notification이 서로 다른 해석을 하게 된다

즉 drift는 "파싱 가능/불가능"보다 **동일한 계약을 같은 의미로 쓰고 있는가**를 묻는 문제다.

### 2. drift detection은 정적 검사, 사전 검증, runtime 신호를 같이 써야 한다

하나의 레이어만 보면 늦거나, 너무 많은 false positive가 나온다.

보통은 세 층으로 본다.

1. design-time detection
   - schema diff
   - breaking change lint
   - registry metadata check
   - deprecation window policy 확인
2. pre-release detection
   - provider verification
   - consumer contract matrix
   - replay/backfill compatibility
   - shadow compare in staging or canary
3. runtime detection
   - parse error rate
   - unknown field or enum fallback rate
   - contract version skew
   - semantic diff rate
   - consumer별 retry, timeout, compensation 증가

정적 검사는 빠르지만 semantic drift를 놓치기 쉽다.
runtime 신호는 강하지만 너무 늦을 수 있다.
그래서 둘을 합쳐서 drift를 **조기 신호와 확정 신호**로 나눠 보는 것이 좋다.

### 3. rollout governance는 drift 유형에 따라 producer/consumer 순서를 달리해야 한다

모든 계약 변경을 같은 rollout 경로로 보내면 안 된다.

대표적인 판단은 다음과 같다.

- additive change:
  consumer tolerance를 먼저 배포하고, producer emission은 나중에 연다
- semantic reinterpretation:
  contract test만으로 부족하므로 shadow compare와 business metric 검증이 먼저 와야 한다
- field removal:
  producer가 끊기 전에 consumer adoption, replay safety, hidden dependency 제거를 먼저 증명해야 한다
- new version introduction:
  producer와 consumer를 동시에 올리기보다 dual-read, dual-parse, canary 순서를 분리해야 한다

즉 rollout governance는 "누가 먼저 배포하나"보다 **어떤 drift를 감지할 때 다음 단계를 멈출 것인가**를 정의해야 한다.

### 4. drift signal은 approval과 pause 권한에 직접 연결돼야 한다

신호가 있어도 의사결정 권한이 불명확하면 운영 체계가 작동하지 않는다.

명확해야 할 것:

- producer rollout을 누가 pause하는가
- consumer lagging exception을 누가 승인하는가
- deprecation deadline을 누가 연장할 수 있는가
- semantic mismatch가 보일 때 누가 "계속 진행 가능"을 판단하는가

이때 producer owner 혼자 안전하다고 말하는 구조는 위험하다.
상위 몇 개 consumer owner, on-call, contract steward가 함께 보는 형태가 현실적이다.

좋은 rule 예:

- parse error는 자동 pause
- semantic diff는 human review gate
- unregistered consumer 탐지 시 full rollout 금지
- deprecation deadline 도달 전 adoption coverage가 기준 미달이면 removal 금지

### 5. registry와 telemetry가 닫힌 루프를 만들어야 한다

drift detection은 지표만 있어서는 반쪽이다.
그 지표가 어떤 계약, 어떤 producer release, 어떤 consumer 버전과 연결되는지 알아야 한다.

그래서 registry에는 최소한 다음이 연결돼야 한다.

- contract id
- owner/steward
- known consumers
- supported version range
- rollout stage
- next review date

telemetry에는 보통 다음이 필요하다.

- consumer별 contract version distribution
- unknown field/enum 처리량
- fallback path activation
- replay or backfill failure rate
- semantic diff sample

이 연결이 있어야 "무슨 계약이 위험한가"를 넘어서 **어느 rollout 단계에서 누구를 멈춰야 하는가**까지 판단할 수 있다.

---

## 실전 시나리오

### 시나리오 1: 새 enum 값을 producer가 먼저 내보낸다

주문 상태에 `PARTIALLY_CONFIRMED`를 추가했다.
schema registry는 통과했고 provider test도 통과했지만, 일부 consumer는 switch 문 default를 `FAILED`로 처리하고 있었다.

이 경우 필요한 대응:

- unknown enum fallback rate 계측
- high-traffic consumer canary 먼저 확인
- producer emission flag는 off 상태 유지
- adoption coverage가 기준 이상일 때만 full emission

문제는 enum 추가 자체보다, **consumer fallback 의미가 팀마다 다르다**는 점이다.

### 시나리오 2: consumer가 새 필드를 required처럼 사용하기 시작한다

producer는 `promotionId`를 optional 필드로 추가했다.
그런데 특정 consumer가 이를 전제로 캐시 키를 만들면, field 미존재 구간에서 hit ratio와 latency가 크게 흔들릴 수 있다.

이 경우 drift는 producer 변경이 아니라 consumer adoption 방식에서 시작된다.

필요한 것:

- consumer contract matrix에 required/optional 기대 반영
- dual-parse 또는 null-safe fallback 검증
- consumer rollout canary와 KPI 관측

즉 drift는 producer가 만들고 consumer가 당하는 일만이 아니다.
consumer가 계약을 더 강하게 해석해도 drift가 생긴다.

### 시나리오 3: field removal은 usage 0이 아니라 dependency 0을 증명해야 한다

producer가 `legacyDeliveryCode` 제거를 원한다.
registry상 active consumer는 0명처럼 보이지만, replay job과 ad-hoc export가 여전히 그 필드를 읽고 있을 수 있다.

그래서 removal gate에는 보통 다음이 들어간다.

- registered consumer adoption 100%
- shadow/replay verification
- hidden consumer 탐지
- rollback window 내 재활성화 가능 여부

삭제 rollout은 "아무도 안 쓴다"는 선언이 아니라, **다시 켜야 할 때도 안전한가**를 확인하는 문제다.

---

## 코드로 보기

```yaml
contract_rollout_policy:
  contract_id: order-status-v4
  producer:
    emit_strategy: feature_flag
    canary_percent: 5
  consumer_requirements:
    adoption_coverage: ">= 95%"
    strict_parsers_allowed: false
  drift_signals:
    parse_error_rate: "== 0"
    unknown_enum_fallback_rate: "< 0.1%"
    semantic_diff_rate: "< 0.05%"
    unregistered_consumer_detected: false
  pause_rules:
    - parse_error_rate_breach
    - semantic_diff_rate_breach
    - hidden_consumer_detected
  approvers:
    - producer_owner
    - contract_steward
    - top_consumer_owner
    - oncall
```

핵심은 policy가 "배포한다/안 한다"만 말하지 않고, 어떤 drift signal이 어느 rollout 단계의 중단 조건인지 명시하는 것이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| schema diff 중심 | 빠르고 싸다 | semantic drift를 놓친다 | 소비자 수가 적고 변화가 단순할 때 |
| contract test + consumer matrix | 현실성이 높다 | 운영 메타데이터 유지가 필요하다 | producer/consumer 팀이 여러 개일 때 |
| runtime drift detection + rollout governance | 장애를 미리 줄인다 | 관측과 승인 체계가 복잡하다 | blast radius가 크고 소비자 다양성이 클 때 |

가장 큰 비용은 검출 체계 자체보다, drift를 모른 채 full rollout한 뒤 복구하는 비용이다.

---

## 꼬리질문

- 지금 보고 있는 변화는 schema drift인가, semantic drift인가, usage drift인가?
- producer와 consumer 중 누가 먼저 배포돼야 하는가?
- 어떤 drift signal은 자동 pause하고, 어떤 signal은 사람이 판단해야 하는가?
- registry에 없는 hidden consumer를 어떻게 찾을 것인가?
- deprecation deadline과 actual adoption coverage가 충돌하면 무엇을 우선할 것인가?

## 한 줄 정리

Contract drift detection and rollout governance는 producer 선언, consumer 기대, runtime 실제 사용의 어긋남을 조기에 감지하고, 그 신호를 rollout 단계와 중단 규칙에 연결해 계약 변경을 안전하게 운영하는 체계다.
