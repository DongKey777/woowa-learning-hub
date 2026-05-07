---
schema_version: 3
title: Capability-Based Roadmap Planning
concept_id: software-engineering/capability-roadmap
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- roadmap
- capability-planning
- portfolio
aliases:
- Capability-Based Roadmap Planning
- capability roadmap
- capability maturity planning
- business capability roadmap
- investment sequencing
- capability heatmap planning
symptoms:
- roadmap을 feature backlog 나열로만 잡아 실제 병목인 contract stability, rollback readiness, observability maturity 같은 capability 투자를 놓쳐
- product feature와 platform capability의 우선순위를 value와 risk, debt interest, migration blocker 기준으로 같이 보지 않아
- capability maturity가 scorecard와 heatmap에서 바뀌어도 roadmap sequencing에 반영하지 않아 계획이 정적 문서로 남아
intents:
- design
- deep_dive
- comparison
prerequisites:
- software-engineering/domain-capability-heatmap
- software-engineering/platform-product-capability-boundaries
next_docs:
- software-engineering/service-maturity-model
- software-engineering/migration-scorecards
- software-engineering/architecture-runway
linked_paths:
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/organizational-coupling-conway-effects.md
- contents/software-engineering/service-maturity-model.md
- contents/software-engineering/migration-scorecards.md
- contents/software-engineering/architecture-runway-refactoring-window.md
- contents/software-engineering/domain-capability-heatmap.md
confusable_with:
- software-engineering/domain-capability-heatmap
- software-engineering/service-maturity-model
- software-engineering/migration-scorecards
forbidden_neighbors: []
expected_queries:
- capability-based roadmap planning은 feature roadmap과 어떻게 다르고 어떤 능력을 먼저 성숙시킬지 정하는 방식이야?
- 결제 재시도, 관측성, 계약 안정성, rollback readiness 같은 capability를 roadmap에 넣는 기준을 알려줘
- capability 병목과 migration blocker를 value risk debt interest 기준으로 어떻게 우선순위화해?
- capability heatmap과 service maturity scorecard가 roadmap sequencing에 어떻게 반영돼?
- platform 투자와 product feature 사이의 균형을 capability roadmap으로 어떻게 설명해?
contextual_chunk_prefix: |
  이 문서는 feature list가 아니라 business capability maturity, bottleneck, risk, debt interest, migration readiness를 기준으로 investment sequencing을 잡는 advanced roadmap playbook이다.
---
# Capability-Based Roadmap Planning

> 한 줄 요약: capability-based roadmap planning은 기능 목록이 아니라 business capability의 성숙도와 병목을 기준으로 언제 무엇을 먼저 바꿀지 정하는 전략이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Organizational Coupling and Conway Effects](./organizational-coupling-conway-effects.md)
> - [Service Maturity Model](./service-maturity-model.md)
> - [Migration Scorecards](./migration-scorecards.md)
> - [Architecture Runway and Refactoring Window](./architecture-runway-refactoring-window.md)

> retrieval-anchor-keywords:
> - capability-based roadmap
> - capability maturity
> - roadmap sequencing
> - business capability
> - portfolio planning
> - dependency bottleneck
> - capability heat
> - investment sequencing

## 핵심 개념

로드맵을 기능 단위로만 잡으면, 실제로는 사용자 가치보다 내부 의존성과 우연한 우선순위에 끌려간다.

capability-based roadmap planning은 다음을 기준으로 순서를 잡는다.

- 어떤 capability가 가장 중요한가
- 어디가 가장 병목인가
- 어떤 capability가 다른 capability를 막고 있는가
- 어느 정도 성숙도가 부족한가

즉 roadmap은 백로그의 나열이 아니라 **capability 투자 순서**다.

---

## 깊이 들어가기

### 1. feature roadmap과 capability roadmap은 다르다

feature roadmap은 "무엇을 만들지"에 가깝다.
capability roadmap은 "어떤 능력을 먼저 성숙시킬지"에 가깝다.

예:

- feature: 새 결제 화면
- capability: 결제 재시도, 관측성, 계약 안정성, rollback readiness

### 2. capability는 시스템 경계와 연결돼야 한다

capability가 어디에서 구현되는지 알아야 한다.

그래서 다음과 함께 본다.

- service ownership
- domain boundary
- platform responsibility
- contract lifecycle

### 3. roadmap은 가치와 위험을 같이 본다

우선순위 기준:

- 사용자 가치
- 운영 리스크 감소
- 전환/마이그레이션 효과
- 기술 부채 이자 감소

### 4. roadmap planning은 정적인 문서가 아니다

capability maturity가 바뀌면 roadmap도 바뀌어야 한다.

그래서 scorecard, heatmap, readiness review와 같이 봐야 한다.

### 5. capability roadmap은 팀 토폴로지와 충돌을 줄인다

조직이 capability 단위로 움직이면, Conway effect를 완화할 수 있다.

---

## 실전 시나리오

### 시나리오 1: 어떤 기능부터 먼저 할지 모른다

기능이 아니라 capability 병목을 먼저 찾는다.

### 시나리오 2: 전환 작업이 지연된다

새 기능보다 migration capability를 먼저 올려야 할 수 있다.

### 시나리오 3: 플랫폼 투자 우선순위를 정해야 한다

기능보다 observability, contract, rollout capability를 먼저 개선한다.

---

## 코드로 보기

```yaml
roadmap:
  q1:
    - improve contract stability
    - add rollback readiness
  q2:
    - migrate checkout capability
```

로드맵은 기능 달력보다 capability 투자표에 가깝다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| feature roadmap | 이해하기 쉽다 | 단기 기능 중심으로 쏠린다 | 초기 제품 |
| capability roadmap | 구조적 병목을 본다 | 설계가 필요하다 | 여러 팀과 서비스가 있을 때 |
| hybrid roadmap | 현실적이다 | 복잡도가 늘어난다 | 성장하는 조직 |

capability-based roadmap planning은 무엇을 만들지보다 **어떤 능력을 먼저 성숙시킬지**를 정하는 방식이다.

---

## 꼬리질문

- capability 병목은 어디에 있는가?
- roadmap은 value와 risk를 같이 반영하는가?
- 플랫폼 투자와 제품 기능의 균형은 무엇인가?
- capability maturity 변화가 일정에 반영되는가?

## 한 줄 정리

Capability-based roadmap planning은 기능 목록이 아니라 business capability의 성숙도와 병목을 기준으로 투자와 순서를 정하는 로드맵 전략이다.
