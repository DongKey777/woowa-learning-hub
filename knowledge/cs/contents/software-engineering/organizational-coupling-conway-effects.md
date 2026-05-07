---
schema_version: 3
title: Organizational Coupling and Conway Effects
concept_id: software-engineering/organizational-coupling-conway-effects
canonical: true
category: software-engineering
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- conway-law
- organization
- ownership
- team-topology
aliases:
- Organizational Coupling and Conway Effects
- Conway effect
- architecture mirrors org
- team topology boundary alignment
- organizational coupling
- 조직 결합 콘웨이 효과
symptoms:
- 팀 소통 경로와 승인 경로가 복잡해 한 변경에 여러 팀이 계속 묶이고 서비스/API 경계도 그 구조를 닮아 중복과 책임 전가가 생겨
- 조직은 바뀌었지만 service ownership, catalog, on-call, API boundary가 갱신되지 않아 stale ownership과 migration 지연이 쌓여
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- software-engineering/platform-product-capability-boundaries
- software-engineering/service-ownership-catalog-boundaries
next_docs:
- software-engineering/team-cognitive-load-boundary-design
- software-engineering/team-apis-interaction-modes
- software-engineering/domain-capability-heatmap
linked_paths:
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/brownfield-strangler-org-model.md
- contents/software-engineering/brownfield-modularization-strategy.md
- contents/software-engineering/architectural-fitness-functions.md
- contents/software-engineering/team-cognitive-load-boundary-design.md
- contents/software-engineering/team-apis-interaction-modes-architecture.md
- contents/software-engineering/domain-capability-heatmap.md
confusable_with:
- software-engineering/platform-product-capability-boundaries
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/team-cognitive-load-boundary-design
forbidden_neighbors: []
expected_queries:
- Conway effect와 organizational coupling이 서비스 경계, API, ownership, release flow에 어떻게 나타나는지 설명해줘
- 팀 구조와 도메인 경계가 맞지 않으면 중복 API와 ownership fragmentation이 생기는 이유가 뭐야?
- capability 기반 팀 구조와 service catalog가 architecture boundary alignment에 왜 중요한지 알려줘
- 조직 개편 후 stale ownership과 duplicated responsibility를 줄이려면 어떤 문서를 갱신해야 해?
- Conway's Law를 없애는 것이 아니라 좋은 형태로 유도한다는 의미는 뭐야?
contextual_chunk_prefix: |
  이 문서는 Conway effects를 팀 소통 경로, service boundary, API ownership, on-call, catalog가 서로 닮아가는 organizational coupling 문제로 설명하는 advanced bridge이다.
---
# Organizational Coupling and Conway Effects

> 한 줄 요약: organizational coupling은 조직 구조가 소프트웨어 구조에 새겨지는 현상이고, Conway effects는 그 결합이 경계와 API, 운영 책임에까지 번지는 결과다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Brownfield Strangler Org Model](./brownfield-strangler-org-model.md)
> - [Brownfield Modularization Strategy](./brownfield-modularization-strategy.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Team Cognitive Load and Boundary Design](./team-cognitive-load-boundary-design.md)
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)

> retrieval-anchor-keywords:
> - Conway effect
> - organizational coupling
> - team topology
> - communication path
> - architecture mirrors org
> - boundary alignment
> - ownership fragmentation
> - delivery structure

## 핵심 개념

Conway's Law는 "조직이 소프트웨어 구조를 닮는다"는 관찰이다.

이건 단순 비유가 아니라, 실제로 팀 구조가 서비스 경계, API, 데이터 책임, 릴리스 흐름에 스며든다는 뜻이다.

조직이 잘못 나뉘면:

- 같은 경계가 여러 서비스에 중복된다
- 서비스가 팀 경계에 맞춰 쪼개진다
- 책임 전가가 잦아진다

즉 organizational coupling은 기술이 아니라 **조직 설계가 남긴 구조적 흔적**이다.

---

## 깊이 들어가기

### 1. coupling은 코드가 아니라 소통 경로에서 시작한다

팀 간 소통 경로가 복잡해질수록 시스템도 복잡해진다.

예:

- 한 변경에 여러 팀 승인 필요
- 배포 일정이 서로 묶임
- API ownership이 분산됨

이런 구조는 서비스 경계에도 반영된다.

### 2. boundary alignment가 중요하다

좋은 구조는 팀 경계와 도메인 경계가 대체로 맞는다.

그러면:

- 결정이 빨라지고
- 장애 대응이 명확해지고
- ownership이 선명해진다

### 3. org coupling은 의도적으로 줄일 수 있다

방법:

- capability 기반 팀 구성
- 명확한 service catalog
- ADR로 책임 기록
- on-call과 ownership 일치
- cognitive load review

### 4. 잘못된 조직 구조는 기술 부채가 된다

조직이 자주 바뀌는데 서비스 경계는 그대로면:

- stale ownership
- duplicated responsibilities
- migration 지연

이 생긴다.

### 5. Conway effect는 완전히 제거할 수 없다

중요한 건 없애는 것이 아니라 **좋은 형태로 유도하는 것**이다.

즉 조직을 경계 설계의 일부로 다뤄야 한다.

---

## 실전 시나리오

### 시나리오 1: 팀별로 같은 API를 다시 만든다

팀 경계가 기능 경계와 맞지 않으면 중복 API가 늘어난다.

### 시나리오 2: 서비스가 팀보다 더 잘 쪼개져 있다

경계는 있는데 소유권이 없다면 운영이 꼬인다.

### 시나리오 3: 전환 프로젝트가 지연된다

조직이 legacy 유지 중심이면 migration이 밀린다.
이때 brownfield strangler org model이 필요하다.

---

## 코드로 보기

```yaml
team_topology:
  commerce:
    owns: [order, checkout]
  platform:
    owns: [deployment, observability, catalog]
```

조직 구조는 문서가 아니라, 실제 시스템 경계를 설계하는 입력이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 기능별 팀 분리 | 빠르다 | 경계가 흐려질 수 있다 | 작은 조직 |
| capability 기반 분리 | 정렬이 좋다 | 설계가 필요하다 | 성장하는 조직 |
| 플랫폼/제품 분리 | 책임이 명확하다 | 조율 비용이 있다 | 큰 시스템 |

organizational coupling은 조직이 기술에 미치는 압력이고, Conway effects는 그 압력이 구조로 굳는 현상이다.

---

## 꼬리질문

- 우리 팀 구조는 서비스 경계와 맞는가?
- 소통 경로가 많아질수록 서비스도 복잡해지는가?
- ownership fragmentation은 어디서 생기는가?
- Conway effect를 줄이기 위해 조직을 어떻게 바꿀 것인가?

## 한 줄 정리

Organizational coupling and Conway effects는 조직 구조가 소프트웨어 구조에 새겨지는 현상을 다루며, 팀 토폴로지를 경계 설계의 일부로 봐야 한다는 점을 보여준다.
