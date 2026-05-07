---
schema_version: 3
title: On-Call Ownership Boundaries
concept_id: software-engineering/on-call-ownership-boundaries
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- on-call
- ownership
- escalation
- incident-response
aliases:
- On-Call Ownership Boundaries
- pager duty ownership
- support boundary escalation path
- service stewardship on-call
- ownership matrix on-call
- 온콜 소유권 경계
symptoms:
- 호출을 받는 팀이 서비스 소유자가 아니거나 service owner는 있는데 on-call과 escalation path가 없어 장애가 공중에 떠
- 하나의 on-call이 너무 많은 서비스와 서로 다른 runbook을 맡거나, 너무 잘게 쪼개져 handoff 비용이 커져
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/incident-review-learning-loop
next_docs:
- software-engineering/support-sla-escalation-contracts
- software-engineering/service-criticality-tiering
- software-engineering/runbook-playbook-automation-boundaries
linked_paths:
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/change-ownership-handoff-boundaries.md
- contents/software-engineering/incident-review-learning-loop-architecture.md
- contents/software-engineering/runbook-playbook-automation-boundaries.md
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/service-criticality-tiering-control-intensity.md
- contents/software-engineering/support-sla-escalation-contracts.md
confusable_with:
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/change-ownership-handoff
- software-engineering/support-sla-escalation-contracts
forbidden_neighbors: []
expected_queries:
- on-call ownership은 누가 밤에 일어나느냐가 아니라 서비스 책임 경계를 운영 가능하게 만드는 설계라는 뜻을 설명해줘
- 서비스 owner와 on-call이 분리되면 incident response가 왜 느려지는지 알려줘
- 24/7 대응이 필요한 서비스와 business hours 대응으로 충분한 서비스를 criticality 기준으로 어떻게 나눠?
- escalation path, runbook, owner metadata를 on-call matrix에 어떻게 연결해야 해?
- on-call fatigue를 page frequency, false positive, night page, runbook resolution rate로 어떻게 줄여?
contextual_chunk_prefix: |
  이 문서는 on-call을 개인 배정표가 아니라 service ownership, criticality, escalation path, runbook, fatigue metrics가 연결된 advanced playbook으로 다룬다.
---
# On-Call Ownership Boundaries

> 한 줄 요약: on-call ownership은 "누가 밤에 일어나느냐"가 아니라, 어떤 서비스와 책임 경계를 누가 끝까지 운영 가능한지 정하는 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Service Criticality Tiering and Control Intensity](./service-criticality-tiering-control-intensity.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)

> retrieval-anchor-keywords:
> - on-call ownership
> - pager duty
> - support boundary
> - escalation path
> - operational responsibility
> - service stewardship
> - after-hours incident
> - ownership matrix

## 핵심 개념

on-call은 단순 교대 근무가 아니다.
좋은 on-call 구조는 서비스 경계와 책임 경계를 맞춰, 장애가 났을 때 **누가 무엇을 끝까지 볼지** 명확히 한다.

문제가 생기면 자주 보이는 실패:

- 호출 받는 팀이 서비스 소유자가 아니다
- 누구에게 넘길지 불명확하다
- runbook이 오래됐다
- escalation path가 없다

즉 on-call은 조직 운영과 아키텍처를 같이 반영해야 한다.

---

## 깊이 들어가기

### 1. on-call과 ownership은 분리되면 안 된다

서비스를 소유하지 않은 팀이 on-call을 받으면, 장애 대응은 느려진다.
반대로 소유는 있는데 on-call이 없으면 책임이 공중에 뜬다.

좋은 구조는:

- 소유 팀 = 1차 대응 책임
- 플랫폼 팀 = 공통 인프라 2차 대응
- 필요 시 타 팀/벤더 escalation

### 2. on-call boundary는 서비스 경계와 비슷해야 한다

하나의 온콜이 너무 많은 서비스를 맡으면 피로도가 커진다.
반대로 너무 잘게 쪼개면 넘기는 비용이 높아진다.

그래서 on-call 경계는 다음을 기준으로 잡는다.

- 장애 패턴이 비슷한가
- 같은 runbook을 쓰는가
- 같은 대시보드를 보는가
- 같은 owner가 빠르게 판단할 수 있는가

### 3. after-hours와 business hours는 다를 수 있다

모든 서비스가 24/7 같은 대응을 받을 필요는 없다.

예:

- 결제, 인증, 주문: 강한 on-call
- 내부 배치, 리포트: 완화된 대응

즉 서비스의 business criticality에 따라 온콜 강도를 다르게 해야 한다.

### 4. escalation path는 미리 정해둬야 한다

장애가 왔을 때 누구에게 넘길지 즉석 판단하면 시간이 늦어진다.

필요한 것:

- 1차/2차/3차 담당
- 호출 순서
- 침묵 시간
- 외부 벤더 연락처

### 5. on-call은 학습과 회수 장치가 있어야 한다

온콜 피로도가 계속 쌓이면 장기적으로 운영이 무너진다.

그래서 다음을 봐야 한다.

- 페이지 빈도
- false positive 비율
- 야간 호출 비율
- runbook 해결률
- 반복 장애율

이 지표는 [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)와 연결된다.

---

## 실전 시나리오

### 시나리오 1: 플랫폼 공통 인프라 장애

플랫폼 팀 on-call이 먼저 받고, 제품 팀은 영향 범위 확인만 돕는다.

### 시나리오 2: 주문 서비스 장애

주문 서비스 소유 팀이 1차 대응을 맡고, 필요한 경우 결제/배송 팀으로 연결한다.

### 시나리오 3: 야간 페이지가 너무 많다

알림 기준을 조정하거나 automation으로 줄여야 한다.
온콜을 늘리기 전에 경보 품질부터 봐야 한다.

---

## 코드로 보기

```yaml
on_call_matrix:
  order-service: commerce-team
  payment-platform: platform-team
  escalation:
    - sre
    - vendor-support
```

온콜은 개인 배정표가 아니라 책임의 구조다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 팀별 온콜 | 책임이 명확하다 | 팀 피로가 생긴다 | 소유 경계가 뚜렷할 때 |
| 중앙 온콜 | 커버리지가 쉽다 | 맥락 손실이 있다 | 플랫폼/공통 인프라 |
| 하이브리드 | 현실적이다 | 경계가 복잡하다 | 조직이 성장할 때 |

on-call ownership은 호출을 받는 구조가 아니라 **장애를 끝까지 책임질 수 있는 구조**여야 한다.

---

## 꼬리질문

- on-call 경계가 서비스 ownership과 일치하는가?
- 24/7이 필요한 서비스와 그렇지 않은 서비스를 구분했는가?
- escalation path와 runbook이 실제로 연결되는가?
- 온콜 피로도를 어떤 지표로 보정할 것인가?

## 한 줄 정리

On-call ownership boundaries는 누가 호출을 받는지보다, 어떤 책임 경계에서 어떤 팀이 장애를 끝까지 운영할 수 있는지를 정하는 설계다.
