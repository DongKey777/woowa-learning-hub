---
schema_version: 3
title: Architectural Governance Operating Model
concept_id: software-engineering/architectural-governance
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- architectural-governance
- decision-rights
- operating-model
aliases:
- Architectural Governance Operating Model
- architecture governance operating model
- federated governance
- architecture stewardship
- decision rights review portfolio
- 아키텍처 거버넌스 운영 모델
symptoms:
- architectural governance를 중앙 리뷰 회의 하나로만 설계해 standards, decisions, controls, learning 흐름이 한 곳에 몰려 병목이 생겨
- 모든 결정을 중앙 승인으로 끌어올리거나 반대로 domain-local 판단을 아무 escalation rule 없이 방치해 기준 편차가 커져
- incident, repeated exception, policy bypass가 decision revalidation과 standards update로 돌아오지 않아 구조적 학습 loop가 닫히지 않아
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/rfc-vs-adr-decision-flow
- software-engineering/architecture-review-anti-patterns
next_docs:
- software-engineering/architecture-council-cadence
- software-engineering/architecture-exception-process
- software-engineering/policy-as-code
linked_paths:
- contents/software-engineering/architecture-review-anti-patterns.md
- contents/software-engineering/rfc-vs-adr-decision-flow.md
- contents/software-engineering/architecture-exception-process.md
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/decision-revalidation-supersession-lifecycle.md
- contents/software-engineering/architecture-council-domain-stewardship-cadence.md
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/team-apis-interaction-modes-architecture.md
confusable_with:
- software-engineering/architecture-council-cadence
- software-engineering/architecture-exception-process
- software-engineering/rfc-vs-adr-decision-flow
forbidden_neighbors: []
expected_queries:
- architectural governance를 standards decisions controls learning 네 층으로 나누는 이유가 뭐야?
- 중앙 architecture review와 federated domain stewardship 사이에서 decision rights를 어떻게 나눠?
- governance operating model에서 repeated exception과 incident를 decision revalidation으로 연결하는 흐름을 설명해줘
- architecture steward는 승인자가 아니라 어떤 흐름을 연결하는 역할이야?
- governance 성공을 통제량이 아니라 drift 회수 속도와 policy update latency로 보는 이유는 뭐야?
contextual_chunk_prefix: |
  이 문서는 architectural governance를 단일 리뷰 회의가 아니라 standards, decisions, controls, learning, decision rights, federated stewardship으로 나누는 advanced operating model playbook이다.
---
# Architectural Governance Operating Model

> 한 줄 요약: architectural governance는 리뷰 회의 하나가 아니라, standards, decision flow, exception, portfolio review, and feedback loop를 역할별로 나눠 운영하는 operating model이어야 지속 가능하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Architectural Governance Operating Model](./README.md#architectural-governance-operating-model)
> - [Architecture Review Anti-Patterns](./architecture-review-anti-patterns.md)
> - [RFC vs ADR Decision Flow](./rfc-vs-adr-decision-flow.md)
> - [Architecture Exception Process](./architecture-exception-process.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)

> retrieval-anchor-keywords:
> - architectural governance
> - governance operating model
> - architecture council
> - federated governance
> - architecture stewardship
> - decision rights
> - review portfolio
> - governance loop

## 핵심 개념

아키텍처 governance를 "중요한 변경은 리뷰받는다" 정도로만 정의하면 금방 병목이 된다.
실제 운영에서는 여러 종류의 판단이 동시에 일어난다.

예:

- 표준 기술을 무엇으로 둘 것인가
- 어떤 변경은 review가 필요한가
- 어떤 규칙은 CI로 강제할 것인가
- 어떤 예외를 언제까지 허용할 것인가
- 어떤 결정은 다시 검토해야 하는가

즉 governance는 단일 회의가 아니라 **여러 판단 경로를 묶는 운영 모델**이다.

---

## 깊이 들어가기

### 1. governance는 네 층으로 나누는 편이 안정적이다

보통 다음 층으로 나눠 보면 운영이 쉬워진다.

- standards: radar, paved road, policy, template
- decisions: RFC, ADR, architecture review
- controls: PRR, rollout gate, exception workflow
- learning: incident review, decision revalidation, scorecard

이걸 한 회의에서 다 처리하려 하면 언제나 과부하가 걸린다.

### 2. 중앙집권과 연방형(federated) 사이의 균형이 필요하다

작은 조직은 중앙에서 많이 결정해도 된다.
하지만 서비스와 팀이 늘어나면 domain-local decision을 중앙에서 다 보려 하면 throughput이 급락한다.

좋은 분배 예:

- central governance: 공통 표준, 고위험 예외, cross-domain 결정
- local stewardship: 도메인 내부 경계, rollout 세부 전략, low-risk 설계

즉 governance의 핵심은 "모두 중앙 승인"이 아니라 **어떤 결정을 어디까지 위임할지 명시하는 것**이다.

### 3. architecture steward 역할이 필요하다

운영 모델이 작동하려면 문서를 쓰는 사람 말고 흐름을 연결하는 steward가 있어야 한다.

역할 예:

- RFC와 ADR 기준 정리
- policy와 review 간 중복 제거
- exception 만료 추적
- repeated incident와 decision revalidation 연결
- portfolio-level debt와 risk 가시화

governance는 승인자만 있어서는 잘 안 굴러간다.

### 4. governance는 socio-technical design을 반영해야 한다

조직 구조와 책임 흐름을 무시한 governance는 오래 못 간다.

증상:

- review는 중앙인데 운영 책임은 도메인 팀에 있음
- 플랫폼 정책은 강한데 예외 판단은 제품 팀이 함
- incident에서 배운 것이 decision flow로 돌아가지 않음

좋은 operating model은 팀 경계, stewardship, on-call, product cadence를 함께 본다.

### 5. governance의 성공은 통제량이 아니라 drift 회수 능력으로 봐야 한다

규칙이 많다고 governance가 좋은 것은 아니다.
정말 중요한 건 drift를 얼마나 빨리 잡고 수정하느냐다.

봐야 할 신호:

- repeated exception count
- review lead time
- policy bypass ratio
- superseded decision age
- incident-to-policy update latency

즉 governance는 규정집이 아니라 **조직의 구조적 학습 속도**를 높이는 장치다.

---

## 실전 시나리오

### 시나리오 1: architecture review가 병목이 된다

모든 구조 변경을 중앙 리뷰에 올리면 도메인 팀이 느려진다.
low-risk 영역은 local steward와 policy gate로 내리고, cross-domain 문제만 중앙으로 올려야 한다.

### 시나리오 2: 예외가 계속 반복된다

이건 예외 프로세스만의 문제가 아니라, standards가 현실과 어긋나거나 migration이 안 끝난 신호일 수 있다.
governance operating model은 이 신호를 radar, ADR revalidation, funding discussion으로 연결해야 한다.

### 시나리오 3: incident에서 같은 문제가 재발한다

review도 있었고 ADR도 있는데 같은 문제가 반복된다면, learning layer가 decision/control layer로 닫히지 않은 것이다.

---

## 코드로 보기

```yaml
architecture_governance:
  standards:
    owners: [platform_architecture]
  decisions:
    paths: [rfc, adr, local_steward_review]
  controls:
    gates: [policy_as_code, prr, exception_workflow]
  learning:
    inputs: [incident_review, scorecard, decision_revalidation]
```

좋은 operating model은 회의 이름보다 판단 경로와 owner가 먼저 보인다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 중앙 review 중심 | 통제가 쉽다 | 병목이 생긴다 | 조직이 작고 위험이 클 때 |
| federated governance | throughput이 높다 | 기준 편차가 생길 수 있다 | 여러 도메인 팀이 있을 때 |
| layered operating model | 확장성이 좋다 | 설계와 stewardship이 필요하다 | 성숙한 조직 |

architectural governance operating model의 목적은 더 많이 승인하는 것이 아니라, **어떤 구조적 판단을 어디서 어떻게 반복 가능하게 할지 설계하는 것**이다.

---

## 꼬리질문

- 어떤 결정은 중앙 governance가 보고, 어떤 결정은 local steward에게 위임할 것인가?
- incident와 repeated exception이 governance 변경으로 얼마나 빨리 연결되는가?
- governance lead time이 delivery 자체를 막고 있지는 않은가?
- standards, decisions, controls, learning 층이 실제로 분리되어 있는가?

## 한 줄 정리

Architectural governance operating model은 리뷰, 표준, 예외, 정책, 학습을 역할별로 분리해 아키텍처 판단을 병목 없이 지속 가능하게 운영하는 구조다.
