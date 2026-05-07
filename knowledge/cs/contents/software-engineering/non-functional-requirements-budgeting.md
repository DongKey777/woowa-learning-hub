---
schema_version: 3
title: Non-Functional Requirements as Budgets
concept_id: software-engineering/nfr-budgeting
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- nfr
- budget
- slo
- architecture-review
aliases:
- Non-Functional Requirements as Budgets
- NFR budgeting
- latency budget
- availability budget
- cost budget
- operability budget
symptoms:
- 성능이 좋아야 한다, 안정적이어야 한다 같은 추상 NFR만 남기고 latency, availability, cost, operability를 경로별 budget으로 나누지 않아 리뷰에서 판단이 안 돼
- checkout p95, monthly error budget, external dependency latency, cost per request가 팀과 서비스 사이에 할당되지 않아 end-to-end 목표가 조용히 깨져
intents:
- design
- deep_dive
- troubleshooting
prerequisites:
- software-engineering/sla-slo-ownership-model
- software-engineering/architectural-fitness-functions
next_docs:
- software-engineering/nfr-budget-negotiation
- software-engineering/production-readiness-review
- software-engineering/lead-time-change-failure-recovery
linked_paths:
- contents/software-engineering/sla-slo-ownership-model.md
- contents/software-engineering/architectural-fitness-functions.md
- contents/software-engineering/production-readiness-review.md
- contents/software-engineering/architecture-review-anti-patterns.md
- contents/software-engineering/lead-time-change-failure-recovery-loop.md
- contents/software-engineering/cross-service-nfr-budget-negotiation.md
confusable_with:
- software-engineering/nfr-budget-negotiation
- software-engineering/sla-slo-ownership-model
- software-engineering/architectural-fitness-functions
forbidden_neighbors: []
expected_queries:
- non-functional requirement를 latency, availability, cost, operability budget으로 바꿔야 하는 이유가 뭐야?
- checkout p95 300ms 같은 end-to-end 목표를 BFF, service, DB, external dependency로 어떻게 분해해?
- latency를 줄이면 cost나 consistency가 나빠질 수 있는 NFR trade-off를 설명해줘
- NFR budget을 architecture review, PRR, fitness function, release gate와 연결하는 방법은?
- dependency owner와 service owner가 supporting budget을 협상해야 하는 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 non-functional requirement를 latency, availability, consistency, cost, operability budget으로 쪼개 architecture review와 release gate에서 쓰는 advanced playbook이다.
---
# Non-Functional Requirements as Budgets

> 한 줄 요약: non-functional requirement는 막연한 희망사항이 아니라, latency, availability, consistency, cost, operability를 각 경로와 팀에 나눠 할당하는 budget으로 바꿔야 설계와 리뷰에서 실제로 쓸 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Non-Functional Requirements as Budgets](./README.md#non-functional-requirements-as-budgets)
> - [SLA, SLO Ownership Model](./sla-slo-ownership-model.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Architecture Review Anti-Patterns](./architecture-review-anti-patterns.md)
> - [Lead Time, Change Failure, and Recovery Loop](./lead-time-change-failure-recovery-loop.md)
> - [Cross-Service NFR Budget Negotiation](./cross-service-nfr-budget-negotiation.md)

> retrieval-anchor-keywords:
> - non-functional requirements
> - NFR budgeting
> - latency budget
> - availability budget
> - cost budget
> - operability budget
> - reliability budget
> - performance budget
> - dependency budget
> - budget negotiation

## 핵심 개념

많은 설계 문서는 NFR을 "성능이 좋아야 한다", "안정적이어야 한다" 수준으로 적고 끝난다.
이렇게 적으면 구현과 리뷰에서 아무 판단도 못 한다.

NFR은 budget으로 바뀌어야 한다.

예:

- checkout p95 latency 300ms
- 월간 error budget 0.1%
- 요청당 비용 상한
- 수동 복구 없이 15분 내 정상화

즉 NFR은 설명 문장이 아니라 **분배 가능한 제약 조건**이다.

---

## 깊이 들어가기

### 1. budget은 end-to-end 목표를 경로별로 쪼개는 일이다

사용자에게 300ms 응답이 필요하다면, 그 안에서 각 hop이 얼마나 쓸 수 있는지 나눠야 한다.

예:

- edge/BFF: 40ms
- application logic: 80ms
- database: 120ms
- external dependency: 60ms

이런 분배가 없으면 모든 구성요소가 각자 "조금만 느리게" 되다가 전체 목표를 넘긴다.

### 2. latency, availability, cost는 서로 독립이 아니다

한 budget을 좋게 만들면 다른 budget이 나빠질 수 있다.

예:

- 더 많은 replica -> availability 증가, cost 증가
- 더 강한 consistency -> correctness 증가, latency 증가
- aggressive retry -> success 증가, downstream overload 위험

그래서 NFR budgeting은 하나의 숫자를 정하는 일이 아니라 **trade-off를 수치화하는 일**이다.

### 3. budget은 서비스 owner와 dependency owner가 함께 본다

end-to-end 목표는 한 팀만으로 못 지키는 경우가 많다.
하지만 아무도 전체 budget을 owning하지 않으면 경로가 무너진다.

좋은 운영 방식:

- 서비스 owner가 user-facing budget을 갖는다
- 하위 dependency는 supporting budget을 갖는다
- 위반 시 escalation path를 정한다

여기서 실제 운영 문제는 supporting budget을 서로 어떻게 협상하느냐이므로, 이 문맥은 [Cross-Service NFR Budget Negotiation](./cross-service-nfr-budget-negotiation.md)과 직접 연결된다.

### 4. NFR은 review, PRR, fitness function에 연결돼야 한다

budget이 문서에만 있으면 곧 잊힌다.

연결 예:

- architecture review에서 예산 배분 검토
- PRR에서 observability와 rollback readiness 검토
- fitness function에서 latency/error/queue depth 검사
- release gate에서 burn rate와 saturation 반영

즉 NFR은 비기능 요구사항이 아니라 **운영 가능한 설계 계약**이다.

### 5. budget은 제품 변화에 따라 다시 계산해야 한다

초기 예산이 영원히 맞지는 않는다.

예:

- 모바일 사용량 급증
- 새로운 외부 연동 추가
- 멀티 리전 요구 등장
- batch workload 증가

제품과 트래픽이 바뀌면 NFR budget도 다시 분해해야 한다.

---

## 실전 시나리오

### 시나리오 1: checkout latency 목표를 세운다

전체 300ms만 선언하면 부족하다.
BFF, 결제, 재고, 쿠폰 조회가 각각 얼마를 가져갈지 나눠야 한다.

### 시나리오 2: 멀티 리전 가용성 목표를 세운다

가용성을 올리려면 replication, failover, 운영 훈련 비용이 같이 든다.
availability budget은 infra 비용과 분리되지 않는다.

### 시나리오 3: 실시간성이 필요한 배치를 만든다

freshness budget이 없으면 "거의 실시간" 같은 표현만 남고, 운영자도 장애 기준을 모르게 된다.

---

## 코드로 보기

```yaml
nfr_budget:
  user_flow: checkout
  latency_p95_ms:
    total: 300
    bff: 40
    order_service: 80
    payment_service: 90
    external_pg: 60
  availability:
    slo: 99.9
    monthly_error_budget_minutes: 43
  cost_per_1000_requests_usd: 2.5
```

좋은 NFR budget은 추상적인 "빨라야 한다"를 설계 가능한 숫자로 바꾼다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 추상적 NFR | 작성이 쉽다 | 실행이 안 된다 | 초기 메모 수준 |
| budgeted NFR | 설계 판단이 가능하다 | 측정과 조율이 필요하다 | 운영 시스템 |
| budget + automated gate | drift를 줄인다 | 운영 규칙이 복잡해진다 | 고위험 서비스 |

non-functional requirements를 budget으로 다루면, 설계팀은 "좋아야 한다" 대신 **무엇을 얼마나 감당할 수 있는지**로 대화하게 된다.

---

## 꼬리질문

- 이 목표는 end-to-end 기준으로 측정 가능한가?
- 어떤 dependency가 가장 많은 budget을 잡아먹는가?
- latency를 줄이는 대신 cost나 consistency는 얼마나 희생되는가?
- budget 위반이 발생하면 release gate와 incident 대응은 어떻게 연결되는가?

## 한 줄 정리

Non-functional requirements as budgets는 NFR을 추상 원칙이 아니라 latency, availability, cost, operability를 경로별로 할당하는 설계 제약으로 바꾸는 관점이다.
