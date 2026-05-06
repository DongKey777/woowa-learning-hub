---
schema_version: 3
title: RFC vs ADR Decision Flow
concept_id: software-engineering/rfc-vs-adr-decision-flow
canonical: false
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- rfc-vs-adr
- decision-record-scope
- architecture-governance
aliases:
- RFC vs ADR
- decision flow
- proposal process
- design record
- governance flow
- decision revalidation
- superseded ADR
symptoms:
- 제안 문서와 결정 문서를 따로 써야 한다는 말이 왜 필요한지 모르겠어요
- RFC를 쓰다가 그대로 ADR처럼 굳혀 버려서 토론과 기록이 섞여 버려요
- 큰 아키텍처 변경에서 언제 RFC로 열고 언제 ADR로 닫아야 하는지 헷갈려요
intents:
- comparison
- design
prerequisites:
- software-engineering/adr-decision-records-at-scale
- software-engineering/architectural-governance-operating-model
- software-engineering/decision-revalidation-supersession-lifecycle
next_docs:
- software-engineering/policy-as-code-architecture-linting
- software-engineering/change-ownership-handoff-boundaries
- software-engineering/incident-review-learning-loop-architecture
linked_paths:
- contents/software-engineering/adr-decision-records-at-scale.md
- contents/software-engineering/architectural-governance-operating-model.md
- contents/software-engineering/policy-as-code-architecture-linting.md
- contents/software-engineering/change-ownership-handoff-boundaries.md
- contents/software-engineering/incident-review-learning-loop-architecture.md
- contents/software-engineering/decision-revalidation-supersession-lifecycle.md
confusable_with:
- software-engineering/adr-decision-records-at-scale
- software-engineering/decision-revalidation-supersession-lifecycle
- software-engineering/architectural-governance-operating-model
forbidden_neighbors:
expected_queries:
- 팀 설계 변경안을 먼저 토론할지 바로 결정 기록으로 남길지 고르는 기준이 뭐야?
- RFC 문서와 ADR 문서를 둘 다 쓰는 흐름을 한 번에 이해하고 싶어
- 아키텍처 변경이 여러 팀에 걸칠 때 언제 proposal 단계가 필요해?
- 이미 채택한 결정이 바뀌었을 때 기존 ADR을 어떻게 이어서 관리해야 해?
- 합의 과정과 최종 결정을 같은 문서에 섞지 말라는 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 RFC와 ADR을 같은 종류의 설계 문서로 오해하는 학습자를 위한
  chooser다. 아직 대안을 열어 두고 토론해야 하는지, 이미 결정된 내용을 짧게
  고정하고 추적해야 하는지, 재검토와 supersede 흐름까지 포함해 어떤 문서
  단계가 맞는지 판단하게 해 주는 비교 문서라는 맥락을 모든 청크 앞에 붙인다.
---
# RFC vs ADR Decision Flow

> 한 줄 요약: RFC는 선택지를 넓게 열어 토론과 합의를 만들고, ADR은 그 결과를 짧게 고정해 실행과 추적을 가능하게 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)

> retrieval-anchor-keywords:
> - RFC
> - ADR
> - decision flow
> - proposal process
> - consensus building
> - design record
> - decision gate
> - governance flow
> - decision revalidation
> - superseded ADR

## 핵심 개념

RFC와 ADR은 비슷해 보이지만 역할이 다르다.

- RFC: 아직 확정되지 않은 제안을 넓게 검토하는 문서
- ADR: 선택된 결정을 간결하게 고정하는 문서

둘을 섞으면 토론도 흐려지고 기록도 흐려진다.

---

## 깊이 들어가기

### 1. RFC는 문제를 넓게 여는 데 적합하다

RFC는 보통 다음에 좋다.

- 여러 대안이 있을 때
- 영향 범위가 넓을 때
- 팀 간 조율이 필요할 때
- 아직 답이 확정되지 않았을 때

즉 RFC는 **의견 수렴의 장**이다.

### 2. ADR은 결정 이후를 위해 존재한다

ADR은 토론을 끝내는 문서가 아니라, 끝난 결정을 다음 사람에게 전달하는 문서다.

좋은 ADR은:

- 선택된 안
- 버린 안
- 이유
- 후속 작업

만 남기면 충분하다.

### 3. 흐름은 RFC -> review -> decision -> ADR -> revalidation이다

좋은 decision flow는 다음과 같다.

1. RFC로 문제와 대안을 넓게 정의
2. 리뷰와 코멘트로 조정
3. 승인 또는 선택
4. ADR로 짧게 고정
5. 관련 코드/정책/문서에 반영
6. trigger가 오면 decision을 revalidation

이 흐름이 없으면 토론이 끝나지 않거나, 결정이 문서화되지 않는다.

### 4. 규모가 커질수록 분리 기준이 중요하다

RFC를 너무 사소한 것까지 쓰면 문서 피로가 커진다.
ADR을 너무 큰 주제에만 쓰면 합의 과정이 추적되지 않는다.

기준 예:

- 다수 팀 영향이면 RFC
- 구조를 바꾸는 결정이면 ADR
- 실행 순서가 긴 변경이면 둘 다 필요

### 5. decision flow는 review gate와 연결되어야 한다

문서가 쌓여도 실행되지 않으면 의미가 없다.

그래서 다음과 연결한다.

- architecture review
- PR gate
- release gate
- policy as code

---

## 실전 시나리오

### 시나리오 1: BFF 분리 여부를 논의한다

초기에는 RFC로 클라이언트 요구와 대안을 모은 뒤, 선택이 끝나면 ADR로 고정한다.

### 시나리오 2: 서비스 deprecation을 시작한다

대안과 영향 분석은 RFC, 최종 종료 결정은 ADR로 남긴다.

### 시나리오 3: 운영 정책이 바뀐다

릴리스 정책은 RFC에서 의견을 모으고, 실제 gate 규칙은 ADR과 policy as code로 고정한다.

---

## 코드로 보기

```markdown
RFC: propose, discuss, compare alternatives
ADR: decide, record consequences, link implementation
```

둘은 경쟁 관계가 아니라, 같은 의사결정의 서로 다른 단계다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| RFC만 사용 | 토론이 풍부하다 | 결정이 흐려질 수 있다 | 탐색 단계 |
| ADR만 사용 | 빠르고 명확하다 | 대안 검토가 약하다 | 작은 결정 |
| RFC + ADR | 탐색과 고정이 분리된다 | 문서 체계가 필요하다 | 큰 아키텍처 결정 |

decision flow의 핵심은 **논의와 결정을 다른 문서 단계로 분리하는 것**이다.

---

## 꼬리질문

- 이 사안은 토론이 필요한가, 기록만 필요한가?
- RFC와 ADR의 책임자는 같은가?
- 결정 후 어떤 시스템에 반영할 것인가?
- 문서가 코드와 정책에 연결되는가?

## 한 줄 정리

RFC vs ADR decision flow는 넓은 탐색을 RFC로, 최종 결정을 ADR로 분리해 팀의 합의와 실행을 동시에 지원하는 구조다.
