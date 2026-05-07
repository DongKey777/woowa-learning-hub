---
schema_version: 3
title: ADRs and Decision Records at Scale
concept_id: software-engineering/adr-decision-records
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- adr
- architecture-governance
- decision-history
aliases:
- ADRs and Decision Records at Scale
- architecture decision record
- ADR decision log
- decision hygiene
- design rationale
- architectural decision 기록
symptoms:
- 중요한 설계 선택이 구두 합의와 PR 댓글에 흩어져 신규 합류자가 왜 그런 구조가 됐는지 추적하지 못해
- 이미 버린 대안을 반복 논의하거나 폐기된 ADR을 현재 정책처럼 읽어 decision lifecycle이 흐려져
- ADR을 회의록처럼 길게 쓰거나 사소한 구현 취향까지 기록해 정작 변경 비용이 큰 결정이 묻혀
intents:
- design
- deep_dive
- troubleshooting
prerequisites:
- software-engineering/rfc-vs-adr-decision-flow
- software-engineering/architectural-governance
next_docs:
- software-engineering/decision-revalidation-lifecycle
- software-engineering/architecture-council-cadence
- software-engineering/architecture-exception-process
linked_paths:
- contents/software-engineering/rfc-vs-adr-decision-flow.md
- contents/software-engineering/architectural-governance-operating-model.md
- contents/software-engineering/decision-revalidation-supersession-lifecycle.md
- contents/software-engineering/architecture-council-domain-stewardship-cadence.md
- contents/software-engineering/architecture-exception-process.md
- contents/software-engineering/clean-architecture-layered-modular-monolith.md
- contents/software-engineering/ddd-hexagonal-consistency.md
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
confusable_with:
- software-engineering/rfc-vs-adr-decision-flow
- software-engineering/decision-revalidation-lifecycle
- software-engineering/architectural-governance
forbidden_neighbors: []
expected_queries:
- ADR은 회의록이 아니라 왜 당시 그 결정을 했는지 남기는 기록이라는 뜻을 설명해줘
- 어떤 설계 결정은 ADR로 남기고 어떤 것은 코드 리뷰나 주석으로 충분한지 기준이 뭐야?
- ADR이 많아질 때 accepted deprecated superseded 상태와 owner를 어떻게 관리해야 해?
- 이미 폐기된 아키텍처 결정을 삭제하지 않고 superseded 링크로 남기는 이유는 뭐야?
- 팀이 커질수록 decision record가 architecture governance와 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 ADR과 architecture decision record를 design rationale, alternatives, trade-off history, supersession lifecycle, governance 운영 관점에서 다루는 advanced playbook이다.
---
# ADRs and Decision Records at Scale

> 한 줄 요약: ADR은 "왜 이렇게 했는가"를 남기는 문서가 아니라, 팀이 커져도 설계 결정의 맥락과 대안을 잃지 않게 하는 운영 장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)

> retrieval-anchor-keywords:
> - ADR
> - architecture decision record
> - decision log
> - decision hygiene
> - architectural governance
> - design rationale
> - trade-off history
> - decision lifecycle

## 핵심 개념

ADR(Architecture Decision Record)은 단순 회의록이 아니다.
좋은 ADR은 특정 결정을 "누가 했는가"보다, **무엇을 비교했고 왜 그 선택이 당시 최선이었는가**를 남긴다.

팀이 작을 때는 구두 합의로도 버틸 수 있지만, 팀이 커지고 시스템이 오래가면 다음 문제가 생긴다.

- 같은 결정을 반복해서 다시 논의한다
- 이미 버린 대안을 또 꺼낸다
- 현재 구조가 왜 나왔는지 모른다
- 신규 합류자가 의사결정 맥락을 잃는다

ADR은 이런 상황에서 설계의 기억 장치 역할을 한다.

---

## 깊이 들어가기

### 1. ADR은 "사실 기록"이 아니라 "의도 기록"이다

ADR에는 보통 다음이 필요하다.

- 문제 정의
- 고려한 대안
- 선택한 옵션
- 선택 이유
- 후속 영향

핵심은 당시 팀이 어떤 제약 아래 어떤 판단을 했는지 남기는 것이다.

### 2. 좋은 ADR은 짧고, 연결 가능해야 한다

너무 길면 읽히지 않는다.
너무 짧으면 맥락이 없다.

좋은 ADR은 보통 다음 특성을 가진다.

- 한 문서에 하나의 결정만 다룬다
- 다른 ADR이나 설계 문서로 이어진다
- 나중에 폐기/수정 여부를 남긴다

즉 ADR은 정답집이 아니라 **결정의 그래프**여야 한다.

### 3. 결정이 늘어날수록 메타 관리가 필요하다

ADR이 많아지면 문서 자체보다 관리가 중요해진다.

필요한 것:

- 일관된 파일명 규칙
- 상태 표기
- 소유자
- 대체 ADR 링크
- 폐기일 또는 재검토일

이 관리가 없으면 ADR이 쌓여도 결국 검색되지 않는 박제가 된다.

### 4. ADR은 아키텍처 리뷰를 대체하지 않는다

ADR은 토론을 줄여 주지만, 검토를 없애지는 못한다.

적절한 사용:

- 중요한 경계 변경
- 스키마/계약 정책 변경
- 전환 전략 선택
- 운영 안전장치 도입

부적절한 사용:

- 사소한 스타일 선호
- 구현 세부를 과하게 기록
- 코드 리뷰로 충분한 사항

즉 ADR은 **변경 비용이 큰 선택**에 붙여야 가치가 있다.

### 5. ADR의 수명은 설계의 수명보다 길 수 있다

오래된 ADR은 그대로 두면 오해를 낳지만, 지우면 의사결정 흔적이 사라진다.

그래서 보통은 삭제보다 다음을 선호한다.

- superseded by 링크
- deprecated 상태
- 재검토 메모

기록을 보존하되, 현재 선택이 무엇인지 분명히 해야 한다.
이 문맥은 [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)과 직접 연결된다.

---

## 실전 시나리오

### 시나리오 1: 왜 trunk-based를 택했는가

팀이 trunk-based를 선택했다면, 그 이유는 "요즘 다 그렇게 하니까"가 아니라 CI 속도, feature flag 성숙도, 배포 리듬 때문이어야 한다.
ADR은 이런 선택의 기준을 남겨 다음 팀이 다시 판단할 수 있게 한다.

### 시나리오 2: BFF를 분리한 이유

모든 화면을 공용 API로 묶지 않고 BFF를 분리했다면, 클라이언트별 payload shape와 운영 책임이 달랐다는 사실을 기록해야 한다.
이 문맥은 [BFF Boundaries and Client-Specific Aggregation](./bff-boundaries-client-specific-aggregation.md)과 연결된다.

### 시나리오 3: 스트랭글러를 택하지 않은 이유

어떤 전환은 Strangler 대신 branch by abstraction이나 단순 리팩터링이 맞을 수 있다.
ADR은 "왜 이번엔 안 썼는가"까지 남길 때 더 유용하다.

---

## 코드로 보기

```markdown
# ADR-014: Separate BFF per client type

## Status
Accepted

## Context
Mobile and admin clients need different payload shapes and latency budgets.

## Decision
Create a dedicated BFF for mobile and admin clients.

## Consequences
- Faster screen-level aggregation
- More operational boundaries
- Shared policies move to common libraries
```

짧아도 핵심은 남는다.
문서의 목적은 길게 쓰는 것이 아니라, 미래의 재논의를 빠르게 만드는 것이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| ADR 없음 | 빨리 움직인다 | 맥락이 사라진다 | 아주 작은 팀의 단기 작업 |
| ADR 최소화 | 읽히기 쉽다 | 세부 맥락이 부족할 수 있다 | 일반적인 팀 운영 |
| ADR 체계화 | 결정 추적이 쉽다 | 유지보수 비용이 든다 | 시스템과 팀이 커질 때 |

ADR은 문서 작업을 늘리는 도구가 아니라, **미래 재논의 비용을 줄이는 투자**다.

---

## 꼬리질문

- 어떤 결정은 ADR로 남기고 어떤 결정은 코드 주석으로 충분한가?
- ADR이 많아질 때 검색과 소유권은 어떻게 관리할 것인가?
- 폐기된 ADR은 삭제해야 하는가, superseded로 남겨야 하는가?
- 기술 결정을 제품/조직 결정과 어떻게 분리할 것인가?

## 한 줄 정리

ADR은 설계 선택의 흔적을 남겨 팀이 커져도 같은 결정을 다시 처음부터 하지 않게 만드는 구조적 기억 장치다.
