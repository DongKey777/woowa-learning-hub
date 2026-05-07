---
schema_version: 3
title: Ownership Metadata Quality
concept_id: software-engineering/ownership-metadata-quality
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- ownership
- metadata
- service-catalog
- operability
aliases:
- Ownership Metadata Quality
- ownership metadata
- stale ownership metadata
- service catalog metadata quality
- source of truth ownership
- 운영 소유권 메타데이터 품질
symptoms:
- service catalog에 owner, backup owner, on-call, ADR, approver, updated_at이 없거나 서로 다른 문서에서 달라 incident와 migration 대응이 늦어져
- 오래된 팀명, dead link, 바뀐 on-call channel, 끊어진 ADR 링크가 남아 source of truth가 신뢰되지 않아
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/on-call-ownership-boundaries
next_docs:
- software-engineering/service-portfolio-lifecycle-governance
- software-engineering/production-readiness-review
- software-engineering/contract-registry-governance
linked_paths:
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/on-call-ownership-boundaries.md
- contents/software-engineering/change-ownership-handoff-boundaries.md
- contents/software-engineering/contract-registry-governance.md
- contents/software-engineering/api-lifecycle-stage-model.md
- contents/software-engineering/service-portfolio-lifecycle-governance.md
- contents/software-engineering/production-readiness-review.md
confusable_with:
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/on-call-ownership-boundaries
- software-engineering/change-ownership-handoff
forbidden_neighbors: []
expected_queries:
- ownership metadata quality를 freshness, completeness, consistency 기준으로 어떻게 점검해?
- service catalog에서 owner, backup owner, on-call, ADR, approver, updated_at 필드가 왜 운영 대응에 필요해?
- stale owner나 dead link, cross-system mismatch를 자동 점검하려면 어떤 guardrail을 둬야 해?
- ownership metadata quality가 낮은 것은 입력 오류가 아니라 책임 구조 문제일 수 있다는 뜻을 설명해줘
- PRR, migration checklist, deprecation communication에서 같은 ownership metadata source of truth를 써야 하는 이유는?
contextual_chunk_prefix: |
  이 문서는 service ownership metadata의 freshness, completeness, consistency를 유지해 incident, PRR, migration, deprecation 대응 가능성을 보장하는 advanced playbook이다.
---
# Ownership Metadata Quality

> 한 줄 요약: ownership metadata quality는 서비스 이름이 아니라, 누가 소유하고 어떻게 운영하는지를 정확히 찾을 수 있는 메타데이터의 신뢰도를 말한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Contract Registry Governance](./contract-registry-governance.md)
> - [API Lifecycle Stage Model](./api-lifecycle-stage-model.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)

> retrieval-anchor-keywords:
> - ownership metadata
> - metadata quality
> - service catalog
> - stale ownership
> - source of truth
> - discoverability
> - stewardship
> - operational directory
> - lifecycle metadata

## 핵심 개념

소유권 메타데이터가 부정확하면 서비스 카탈로그는 쓸모가 없다.

좋은 metadata는 다음 질문에 즉시 답할 수 있어야 한다.

- 누가 owner인가
- backup owner는 누구인가
- on-call은 어디로 가는가
- 관련 ADR은 무엇인가
- 변경 승인자는 누구인가

즉 metadata quality는 단순한 문서 품질이 아니라 **운영 대응 가능성**의 문제다.

---

## 깊이 들어가기

### 1. metadata quality는 최신성, 완전성, 일관성으로 본다

세 가지를 같이 봐야 한다.

- 최신성: 지금도 맞는가
- 완전성: 필요한 필드가 있는가
- 일관성: 서로 다른 문서에서 같은 값인가

### 2. 누락보다 더 위험한 것은 잘못된 정보다

owner가 틀리면 장애 대응이 다른 팀으로 흘러간다.

예:

- 오래전 팀 이름이 남아 있음
- on-call channel이 바뀌었는데 업데이트 안 됨
- ADR 링크가 끊어짐

### 3. metadata는 자동 점검 대상이 되어야 한다

좋은 점검:

- dead links
- stale owner detection
- missing fields
- cross-system mismatch
- last updated age

### 4. quality는 ownership과 연결된다

메타데이터 품질이 낮은 이유는 종종 소유권이 불분명해서다.

즉 metadata quality 문제는 단지 입력 오류가 아니라 **책임 구조의 문제**일 수 있다.

### 5. metadata는 카탈로그와 PRR에 모두 필요하다

서비스 카탈로그뿐 아니라:

- production readiness review
- migration checklist
- deprecation communication

에서도 동일한 정보가 써야 한다.

---

## 실전 시나리오

### 시나리오 1: 장애가 났는데 owner를 찾을 수 없다

메타데이터 품질이 낮으면 대응이 늦어진다.

### 시나리오 2: 여러 문서에서 owner가 다르다

source of truth를 정하고, 나머지는 동기화해야 한다.

### 시나리오 3: 오래된 팀명이 남아 있다

metadata age를 기준으로 정기 점검해야 한다.

---

## 코드로 보기

```yaml
service_metadata:
  owner: commerce-platform
  backup_owner: commerce-oncall
  adr: adr-014
  updated_at: 2026-04-09
```

quality는 필드가 있는지보다, 실제로 신뢰할 수 있는지가 중요하다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 수동 관리 | 쉽다 | 금방 낡는다 | 작은 조직 |
| 자동 점검 | 신뢰성이 높다 | 규칙 설계가 필요하다 | 서비스가 많을 때 |
| catalog + workflow sync | 가장 정확하다 | 운영이 복잡하다 | 성숙한 조직 |

ownership metadata quality는 검색 편의가 아니라 **운영 신뢰도**다.

---

## 꼬리질문

- 어떤 필드를 반드시 채워야 하는가?
- stale metadata는 어떻게 감지할 것인가?
- source of truth는 어디인가?
- metadata 품질을 누가 책임지는가?

## 한 줄 정리

Ownership metadata quality는 서비스 소유권과 운영 연결 정보의 최신성, 완전성, 일관성을 유지해 실제 대응 가능성을 보장하는 품질 기준이다.
