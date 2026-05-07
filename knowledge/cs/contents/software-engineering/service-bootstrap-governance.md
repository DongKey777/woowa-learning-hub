---
schema_version: 3
title: Service Bootstrap Governance
concept_id: software-engineering/service-bootstrap-governance
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- service-governance
- bootstrap
- golden-path
- ownership
aliases:
- service bootstrap governance
- service creation checklist
- golden path bootstrap
- service scaffold governance
- service catalog registration at bootstrap
- 서비스 부트스트랩 거버넌스
symptoms:
- 새 서비스를 템플릿 생성으로만 시작해서 owner, on-call, observability, release strategy, catalog registration이 비어 있어
- bootstrap generator에는 기본값이 있지만 PRR, service catalog, policy gate에서 유지 여부를 검증하지 않아 시간이 지나며 누락돼
- 실험 서비스와 운영 서비스의 bootstrap default가 구분되지 않아 운영 전환 때 ownership과 policy 부채가 드러나
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/service-template-tradeoffs
- software-engineering/platform-paved-road
next_docs:
- software-engineering/service-maturity-model
- software-engineering/service-portfolio-lifecycle-governance
- software-engineering/policy-as-code
linked_paths:
- contents/software-engineering/service-template-tradeoffs.md
- contents/software-engineering/platform-paved-road-tradeoffs.md
- contents/software-engineering/golden-path-escape-hatch-policy.md
- contents/software-engineering/service-maturity-model.md
- contents/software-engineering/production-readiness-review.md
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/technology-radar-adoption-governance.md
- contents/software-engineering/configuration-governance-runtime-safety.md
- contents/software-engineering/platform-control-plane-delegation-boundaries.md
- contents/software-engineering/service-portfolio-lifecycle-governance.md
confusable_with:
- software-engineering/service-template-tradeoffs
- software-engineering/platform-paved-road
- software-engineering/service-maturity-model
forbidden_neighbors: []
expected_queries:
- service bootstrap governance에서 새 서비스 생성 순간에 owner, on-call, observability, release strategy를 왜 강제해야 해?
- 서비스 템플릿과 bootstrap governance는 코드 scaffold와 운영 정책 관점에서 어떻게 달라?
- bootstrap 기준을 generator, catalog registration, PRR policy gate에 나눠 심는 이유를 설명해줘
- 실험용 서비스와 운영용 서비스의 bootstrap default를 어떻게 구분해야 해?
- golden path bootstrap에 예외 경로를 둘 때 어떤 metadata와 approval을 남겨야 해?
contextual_chunk_prefix: |
  이 문서는 새 서비스 생성 시 owner, on-call, observability, release, catalog registration 같은 운영 기본값을 강제하는 advanced service governance playbook이다.
---
# Service Bootstrap Governance

> 한 줄 요약: service bootstrap governance는 새 서비스를 빨리 시작하게 하는 일이 아니라, 시작 순간부터 ownership, policy, observability, and lifecycle defaults를 강제로 갖추게 하는 운영 규칙이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Template Trade-offs](./service-template-tradeoffs.md)
> - [Platform Paved Road Trade-offs](./platform-paved-road-tradeoffs.md)
> - [Golden Path Escape Hatch Policy](./golden-path-escape-hatch-policy.md)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Technology Radar and Adoption Governance](./technology-radar-adoption-governance.md)
> - [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)
> - [Platform Control Plane and Delegation Boundaries](./platform-control-plane-delegation-boundaries.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)

> retrieval-anchor-keywords:
> - service bootstrap
> - bootstrap governance
> - service creation checklist
> - bootstrap pipeline
> - default policy
> - service scaffold
> - ownership defaults
> - observability defaults
> - lifecycle defaults
> - golden path bootstrap
> - service catalog registration
> - production readiness bootstrap
> - service initialization

## 핵심 개념

새 서비스를 만드는 순간은 가장 방치되기 쉬운 순간이다.

bootstrap governance는 이 시점에 아래를 자동으로 요구한다.

- owner
- on-call
- metrics/logs/traces
- deployment path
- contract policy
- deprecation plan placeholder

즉 bootstrap은 단순 생성이 아니라 **운영 가능한 시작 상태를 강제하는 절차**다.

---

## Template Insertion Points

bootstrap 기준은 generator 한 군데에만 넣으면 빠르게 빠진다. 보통 다음 네 곳에 나눠 심는 편이 낫다.

- bootstrap command/output: owner, on-call, observability, release strategy 기본값을 생성한다.
- repo-level checklist or ADR placeholder: 템플릿 예외와 선택한 운영 기본값을 기록한다.
- service catalog registration: 팀, criticality, contact, template lineage를 등록한다.
- PRR / policy gate: bootstrap 때 채워야 할 필드가 실제로 유지되는지 검증한다.

즉 bootstrap governance의 삽입 지점은 **생성기, 등록 기록, 검증 게이트** 세 축으로 보는 편이 안전하다.

---

## 깊이 들어가기

### 1. bootstrap은 템플릿보다 넓다

템플릿은 코드 골격이고, bootstrap governance는 그 위에 정책과 책임을 덮는다.

### 2. defaults가 중요하다

무언가를 나중에 채우겠다고 두면, 결국 끝까지 비어 있는 경우가 많다.

필수 defaults:

- logging format
- health endpoint
- alert routing
- ownership metadata
- release strategy
- standard stack choice
- config validation default

### 3. governance는 생성 단계에서 시작해야 한다

서비스가 커진 뒤에 policy를 붙이면 거의 항상 누락이 있다.

그래서 생성 PR이나 bootstrap pipeline에서:

- policy check
- metadata check
- catalog registration
- PRR checklist creation

이 일어나야 한다.

### 4. bootstrap and maturity are connected

bootstrap 기준이 높을수록 새 서비스의 초기 성숙도가 높아진다.

이 문맥은 [Service Maturity Model](./service-maturity-model.md)과 연결된다.

### 5. bootstrap governance는 우회 경로를 줄인다

초기에 규칙이 약하면 각 팀이 자기 방식으로 시작해 나중에 통제하기 어렵다.

---

## 실전 시나리오

### 시나리오 1: 새 API 서비스 생성

owner, contract stage, observability, rollout policy를 자동 설정한다.

### 시나리오 2: 실험용 서비스가 운영으로 넘어간다

bootstrap governance를 통해 실험용과 운영용 defaults를 분리한다.

### 시나리오 3: 여러 팀이 각자 서비스를 만든다

공통 bootstrap guardrail이 없으면 성숙도가 들쭉날쭉해진다.

---

## 코드로 보기

```yaml
bootstrap:
  owner: required
  catalog_registration: required
  dashboards: default
  alerts: default
  prr: required
```

bootstrap은 선택사항이 아니라 운영 출발점이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자유로운 시작 | 빠르다 | 품질이 들쭉날쭉하다 | 작은 팀 |
| bootstrap governance | 일관성이 높다 | 시작 비용이 든다 | 여러 팀이 서비스 만들 때 |
| strict bootstrap | 운영 품질이 좋다 | 유연성이 낮다 | 플랫폼 성숙 조직 |

service bootstrap governance는 시작을 느리게 하기 위한 것이 아니라, **운영 부채를 초기에 만들지 않게 하는 안전장치**다.

---

## 꼬리질문

- 서비스 생성 시 필수 defaults는 무엇인가?
- bootstrap에서 누락되면 안 되는 owner 정보는 무엇인가?
- 실험 서비스와 운영 서비스의 bootstrap을 어떻게 구분할 것인가?
- bootstrap 규칙은 어디서 강제할 것인가?

## 한 줄 정리

Service bootstrap governance는 새 서비스가 생성되는 순간부터 운영·책임·관측 기본값을 강제해 초기 부채를 막는 규칙이다.
