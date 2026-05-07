---
schema_version: 3
title: Brownfield Strangler Org Model
concept_id: software-engineering/brownfield-strangler-org
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- brownfield
- strangler-fig
- ownership-model
aliases:
- Brownfield Strangler Org Model
- strangler org model
- brownfield transformation team
- dual operating model
- migration squad
- legacy ownership split
symptoms:
- Strangler 전환을 코드 cutover 문제로만 보고 legacy 유지, new service 개발, migration, operations 책임을 나누지 않아
- transition squad가 일시 조직인지 product/platform으로 ownership을 넘길 종료 조건이 있는지 정하지 않아 전환팀이 영구화돼
- legacy bug, new contract failure, rollback 판단, cutover ownership이 회색지대로 남아 전환 속도가 느려져
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/brownfield-modularization
- software-engineering/strangler-fig-migration-contract-cutover
next_docs:
- software-engineering/strangler-verification-shadow-traffic-metrics
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/platform-product-capability-boundaries
linked_paths:
- contents/software-engineering/brownfield-modularization-strategy.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/strangler-verification-shadow-traffic-metrics.md
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
confusable_with:
- software-engineering/brownfield-modularization
- software-engineering/strangler-fig-migration-contract-cutover
- software-engineering/platform-product-capability-boundaries
forbidden_neighbors: []
expected_queries:
- brownfield strangler migration에서 legacy team, migration squad, product team 책임을 어떻게 나눠야 해?
- Strangler 전환이 코드보다 조직 ownership 때문에 실패하는 경우를 설명해줘
- transition squad는 어떤 역할을 하고 언제 소멸하거나 ownership을 넘겨야 해?
- legacy bug, new contract failure, rollback 판단은 전환 중 누가 책임져야 해?
- legacy call ratio, shadow diff rate, migrated consumer count 같은 migration KPI를 org model에 어떻게 붙여?
contextual_chunk_prefix: |
  이 문서는 brownfield Strangler Fig migration을 legacy team, migration squad, product/platform owner, dual operating model, cutover ownership 관점에서 설계하는 advanced playbook이다.
---
# Brownfield Strangler Org Model

> 한 줄 요약: brownfield strangler는 코드 전환만이 아니라, 레거시와 신규를 동시에 운영할 조직 구조와 책임 분리를 함께 바꿔야 성공한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Strangler Verification, Shadow Traffic Metrics](./strangler-verification-shadow-traffic-metrics.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)

> retrieval-anchor-keywords:
> - strangler org model
> - brownfield transformation
> - transition team
> - legacy ownership
> - dual operating model
> - migration squad
> - responsibility split
> - change agent

## 핵심 개념

Strangler 전환이 실패하는 이유는 코드보다 조직이 더 자주 원인인 경우가 많다.

새 시스템을 만드는 팀과 레거시를 유지하는 팀이 분리되어 있으면,
누가 전환의 끝을 책임지는지 모호해질 수 있다.

그래서 brownfield strangler org model은:

- 레거시 유지 책임
- 신규 서비스 개발 책임
- migration 책임
- 운영 책임

을 어떻게 나눌지 설계한다.

---

## 깊이 들어가기

### 1. dual operating model이 필요하다

전환 기간에는 레거시와 신규가 동시에 존재한다.

따라서 조직도 같이 이중 구조가 필요하다.

- legacy team: 안정성 유지, 문제 대응
- migration team: cutover, contracts, observability
- product team: 기능 우선순위

이 구조가 없으면 모두가 전환을 "남의 일"로 본다.

### 2. transition squad는 일시적이어야 한다

전환 전담팀은 영구 조직이 되면 안 된다.

역할:

- 경계 추출
- 데이터 이전
- shadow compare
- consumer migration
- 마지막 cutover

전환이 끝나면 소멸하거나 다른 책임으로 재배치해야 한다.

### 3. ownership split이 명확해야 한다

전환 중 가장 위험한 것은 회색지대다.

예:

- 레거시 버그는 누가 고치는가?
- 신규 contract 실패는 누가 처리하는가?
- rollback 판단은 누가 하는가?

이 질문에 답이 없으면 운영이 멈춘다.

### 4. migration metric이 있어야 한다

조직 모델은 숫자와 연결되어야 한다.

예:

- 전환한 소비자 수
- shadow diff rate
- legacy call ratio
- deprecated path usage
- rollback count

### 5. brownfield 전환은 소유권 이전과 함께 간다

전환이 진척될수록 레거시 소유권은 줄고, 신규 소유권은 늘어야 한다.

이 변화가 없으면 조직은 오래된 시스템을 계속 붙든다.

---

## 실전 시나리오

### 시나리오 1: 레거시와 신규가 서로 책임을 떠넘긴다

전환 전담팀이 없으면 문제가 누구 책임인지 흐려진다.
전환팀이 있어야 migration 책임을 중앙에서 볼 수 있다.

### 시나리오 2: cutover가 자꾸 미뤄진다

조직이 레거시 안정성에만 맞춰져 있으면 신규 전환이 밀린다.
전환 KPI를 넣어야 한다.

### 시나리오 3: 전환 후에도 전담팀이 남아 있다

전환팀이 계속 존재하면 조직이 전환을 끝내지 못한다.
이 경우 ownership을 제품/플랫폼 팀으로 다시 넘겨야 한다.

---

## 코드로 보기

```yaml
org_model:
  legacy_team: maintain
  migration_squad: transition
  product_team: own_future_state
```

조직 모델은 문서보다 책임 흐름이 중요하다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 레거시/신규 단일 팀 | 일관성이 좋다 | 전환 속도가 느리다 | 작은 시스템 |
| 전환 전담팀 | 집중도가 높다 | 소멸 관리가 필요하다 | 큰 brownfield 전환 |
| 제품/플랫폼 분리 | 책임이 명확하다 | 경계 조율이 필요하다 | 전환 후 운영 |

brownfield strangler org model은 코드 전환을 지원하는 **책임 전환 구조**다.

---

## 꼬리질문

- 전환 책임은 누가 진짜 지는가?
- 전환팀은 언제 종료되는가?
- legacy team과 migration squad의 경계는 어디인가?
- 전환 KPI는 무엇인가?

## 한 줄 정리

Brownfield strangler org model은 레거시와 신규를 동시에 다루는 전환 기간 동안 책임과 운영 권한을 분리해 cutover를 실제로 완성시키는 조직 설계다.
