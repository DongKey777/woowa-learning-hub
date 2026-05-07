---
schema_version: 3
title: Architecture Council and Domain Stewardship Cadence
concept_id: software-engineering/architecture-council-cadence
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- architecture-council
- domain-stewardship
- escalation
aliases:
- Architecture Council and Domain Stewardship Cadence
- architecture council cadence
- domain stewardship forum
- federated governance cadence
- decision traffic routing
- architecture escalation forum
symptoms:
- architecture council 하나에 모든 local boundary, exception, cross-domain, standard 안건을 올려 중앙 forum이 병목이 돼
- domain stewardship forum을 두었지만 escalation 조건이 없어 cross-domain impact나 repeated exception이 늦게 올라와
- 과거 ADR, 예외 만료, incident-linked revalidation을 agenda에 넣지 않아 forum이 신규 승인 회의로만 굴러가
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/architectural-governance
- software-engineering/rfc-vs-adr-decision-flow
next_docs:
- software-engineering/shadow-forum-escalation-rules
- software-engineering/team-apis-interaction-modes
- software-engineering/platform-product-capability-boundaries
linked_paths:
- contents/software-engineering/architectural-governance-operating-model.md
- contents/software-engineering/architecture-review-anti-patterns.md
- contents/software-engineering/rfc-vs-adr-decision-flow.md
- contents/software-engineering/decision-revalidation-supersession-lifecycle.md
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/team-apis-interaction-modes-architecture.md
- contents/software-engineering/shadow-forum-escalation-rules.md
confusable_with:
- software-engineering/architectural-governance
- software-engineering/shadow-forum-escalation-rules
- software-engineering/team-apis-interaction-modes
forbidden_neighbors: []
expected_queries:
- architecture council과 domain stewardship forum은 어떤 안건을 각각 봐야 해?
- federated governance에서 cross-domain impact나 repeated exception은 언제 중앙 council로 escalation해야 해?
- governance cadence를 weekly domain stewardship biweekly council monthly portfolio review로 나누는 기준이 뭐야?
- architecture forum agenda에 신규 RFC뿐 아니라 예외 만료와 decision revalidation을 넣어야 하는 이유는 뭐야?
- governance cadence 품질을 forum lead time, escalation rate, stale exception count로 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 architecture council과 domain stewardship forum의 cadence, scope, escalation rule, decision backlog, exception expiry, revalidation loop를 설계하는 advanced governance playbook이다.
---
# Architecture Council and Domain Stewardship Cadence

> 한 줄 요약: governance operating model이 문서로만 남지 않으려면, 중앙 architecture council과 도메인 stewardship forum이 어떤 cadence로 어떤 결정을 보고, 언제 escalation하는지까지 운영 리듬으로 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Architecture Council and Domain Stewardship Cadence](./README.md#architecture-council-and-domain-stewardship-cadence)
> - [Architectural Governance Operating Model](./architectural-governance-operating-model.md)
> - [Architecture Review Anti-Patterns](./architecture-review-anti-patterns.md)
> - [RFC vs ADR Decision Flow](./rfc-vs-adr-decision-flow.md)
> - [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)
> - [Shadow Forum Escalation Rules](./shadow-forum-escalation-rules.md)

> retrieval-anchor-keywords:
> - architecture council
> - domain stewardship
> - governance cadence
> - review forum
> - federated governance
> - escalation forum
> - stewardship cadence
> - governance rhythm
> - shadow forum escalation

## 핵심 개념

architecture governance가 실패하는 흔한 이유는 기준이 없어서가 아니라, **언제 어디서 어떤 결정을 다루는지 리듬이 없기 때문**이다.

중앙 forum 하나에 모든 안건을 모으면 병목이 생기고,
각 팀이 알아서만 하게 두면 cross-domain 문제가 늦게 터진다.

그래서 보통 두 종류의 forum이 필요하다.

- architecture council: cross-domain, high-risk, standard-level 판단
- domain stewardship forum: 로컬 경계, 반복 이슈, low/medium-risk 설계 판단

즉 governance cadence는 회의 일정표가 아니라 **decision traffic routing**이다.

---

## 깊이 들어가기

### 1. council과 stewardship forum은 목적이 달라야 한다

중앙 council이 보는 것:

- 기술 표준 변경
- cross-domain contract 변화
- 장기 예외 누적
- portfolio-level risk

도메인 stewardship forum이 보는 것:

- 로컬 boundary drift
- repeated local exception
- rollout/operability 설계
- local decision revalidation

둘의 목적을 분리하지 않으면 하나는 과부하, 다른 하나는 형식주의가 된다.

### 2. cadence는 변화 속도와 risk에 맞춰야 한다

모든 forum을 매주 열 필요는 없다.
핵심은 안건 흐름과 맞는지다.

예:

- weekly domain stewardship: 빠른 로컬 설계/예외 판단
- biweekly architecture council: cross-domain 안건 정리
- monthly portfolio governance review: repeated issue, standards drift, lifecycle debt 검토

cadence가 너무 촘촘하면 의사결정 비용이 커지고,
너무 느슨하면 drift가 governance보다 빨리 쌓인다.

### 3. escalation path가 없으면 federated governance가 무너진다

도메인 팀이 local decision을 하다가도 다음 상황에서는 중앙 escalation이 필요하다.

예:

- 두 도메인 이상에 영향
- shared platform policy 변경 필요
- high-blast-radius migration
- repeated exception이 2회 이상 누적

즉 local autonomy는 독립국가가 아니라 **상위 escalation이 있는 위임 구조**다.
특히 shadow catalog처럼 `blocked_duration`, `impacted_domains`, `affected_teams`, shared control plane change가 바로 escalation threshold가 되는 영역은 [Shadow Forum Escalation Rules](./shadow-forum-escalation-rules.md)처럼 forum handoff 조건을 별도 문서로 고정해 두는 편이 drift를 줄인다.

### 4. forum은 decision backlog와 feedback loop를 같이 봐야 한다

많은 조직이 새 안건만 보고, 과거 결정의 상태는 안 본다.
그러면 ADR은 쌓이고 revalidation은 안 된다.

좋은 agenda 예:

- 신규 RFC / ADR 후보
- 예외 만료 예정
- recent incident-linked revalidation
- standards drift / shadow path 증가
- portfolio cleanup 후보

즉 governance forum은 승인 회의보다 **decision portfolio review**에 가깝다.

### 5. forum 성숙도는 throughput과 correction speed로 봐야 한다

좋은 forum은 많은 안건을 처리하는 것이 아니라,
중요한 안건은 빨리 올리고 잘못된 결정은 빨리 교정한다.

봐야 할 지표:

- forum lead time
- escalation rate
- decision-to-policy update time
- stale exception count
- repeated incident after review

governance cadence의 품질은 회의 수가 아니라 **판단 품질과 교정 속도**다.

---

## 실전 시나리오

### 시나리오 1: 중앙 review가 항상 밀린다

로컬 stewardship forum이 약해서 모든 안건이 council로 올라가는 구조일 수 있다.
local lane을 강화하고 escalation 기준만 중앙화해야 한다.

### 시나리오 2: 도메인별 기준이 너무 달라진다

federated governance는 좋지만, 공통 review packet과 escalation rule이 없으면 policy drift가 커진다.

### 시나리오 3: 예외가 여러 달 닫히지 않는다

이는 individual team failure라기보다 forum cadence가 만료/재검토를 회수하지 못하는 신호일 수 있다.

---

## 코드로 보기

```yaml
governance_cadence:
  domain_stewardship:
    every: weekly
    scope: local_boundary_and_exception
  architecture_council:
    every: biweekly
    scope: cross_domain_and_standard_change
  escalation_if:
    - cross_domain_impact
    - repeated_exception >= 2
    - blast_radius == high
```

좋은 cadence 모델은 회의 이름보다 escalation rule과 scope가 먼저 보인다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 중앙 council 중심 | 기준이 단순하다 | 병목이 생긴다 | 조직이 작을 때 |
| domain stewardship 중심 | throughput이 높다 | 기준 편차가 생길 수 있다 | 여러 도메인 팀이 있을 때 |
| layered cadence + escalation | 균형이 좋다 | 운영 discipline이 필요하다 | 성장 조직 |

architecture council and domain stewardship cadence의 목적은 회의를 늘리는 것이 아니라, **올바른 안건이 올바른 높이에서 제때 판단되게 만드는 것**이다.

---

## 꼬리질문

- 어떤 안건은 local stewardship에서 끝나고 어떤 안건은 council로 올라가야 하는가?
- repeated exception과 incident는 어떤 cadence에서 회수되는가?
- governance forum의 lead time이 delivery를 막고 있지는 않은가?
- forum agenda에 신규 안건뿐 아니라 재검토 안건도 포함되는가?

## 한 줄 정리

Architecture council and domain stewardship cadence는 중앙과 로컬 governance forum의 역할과 주기와 escalation 기준을 명확히 해 판단 병목과 기준 drift를 함께 줄이는 운영 리듬 설계다.
