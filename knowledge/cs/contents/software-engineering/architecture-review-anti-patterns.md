# Architecture Review Anti-Patterns

> 한 줄 요약: architecture review는 감으로 막는 회의가 아니라, 반복되는 설계 실패를 드러내는 검사 과정인데, 반대로 운영되면 결정 지연과 형식주의만 남는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [RFC vs ADR Decision Flow](./rfc-vs-adr-decision-flow.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Policy as Code and Architecture Linting](./policy-as-code-architecture-linting.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Non-Functional Requirements as Budgets](./non-functional-requirements-budgeting.md)
> - [Prototype, Spike, and Productionization Boundaries](./prototype-spike-productionization-boundaries.md)
> - [Architectural Governance Operating Model](./architectural-governance-operating-model.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)

> retrieval-anchor-keywords:
> - architecture review
> - review anti-pattern
> - decision bottleneck
> - cargo cult architecture
> - approval theater
> - design review
> - governance fatigue
> - review checklist

## 핵심 개념

아키텍처 리뷰는 필요하다.
하지만 잘못 운영하면 다음이 생긴다.

- 결정을 막기만 하는 병목
- 근거 없는 취향 싸움
- 체크박스용 형식 리뷰
- 이미 정한 결론을 다시 승인받는 의식

즉 review는 설계를 돕는 장치여야지, **발목을 잡는 의례**가 되어서는 안 된다.

---

## 깊이 들어가기

### 1. approval theater

이미 결정된 내용을 형식적으로 승인받는 리뷰는 가치가 낮다.

증상:

- 리뷰 전에 결론이 정해짐
- 질문은 많지만 대안은 안 봄
- 기록은 남지만 행동은 안 바뀜

### 2. cargo cult architecture

문맥 없이 유행하는 구조를 그대로 들여오는 것이다.

예:

- MSA를 이유 없이 쪼갬
- event-driven을 모든 문제에 적용
- BFF를 화면마다 남발

리뷰는 이런 유행 복제를 막아야 한다.

### 3. decision bottleneck

모든 결정을 소수 리뷰어가 승인하면 팀이 느려진다.

리뷰는 다음에 집중해야 한다.

- 영향이 큰 경계
- 되돌리기 어려운 변경
- 보안/데이터/운영 리스크

### 4. review checklist는 맥락형이어야 한다

체크리스트가 있으면 좋지만, 단순 형식이면 효과가 없다.

좋은 질문 예:

- 대안은 무엇이었는가?
- 계약/운영 영향은 있는가?
- rollback 경로가 있는가?
- ownership이 명확한가?
- budget이나 graduation criteria가 있는가?

### 5. review는 피드백 루프여야 한다

리뷰가 끝나면 정책, ADR, fitness function으로 반영되어야 한다.

그렇지 않으면 같은 실수를 반복한다.

---

## 실전 시나리오

### 시나리오 1: 리뷰가 병목이 된다

소규모 변경까지 모두 architecture review를 거치면 throughput이 떨어진다.
이럴 땐 policy as code와 fitness function으로 자동화할 수 있는 부분을 줄여야 한다.

### 시나리오 2: 특정 팀만 계속 지적받는다

리뷰 기준이 불명확하거나, 문서와 코드가 분리된 경우다.
ADR과 lint 규칙으로 기준을 고정해야 한다.

### 시나리오 3: 리뷰는 통과했는데 장애가 난다

리뷰 질문이 구조만 보고 실행/운영 리스크를 놓친 것이다.
운영 문맥을 반드시 포함해야 한다.

---

## 코드로 보기

```markdown
Review questions:
- What problem does this solve?
- What alternatives were rejected?
- What can fail in production?
- What policy or test will prevent drift?
```

architecture review는 승인 문서가 아니라 검증 질문 세트여야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 강한 review gate | 사고를 줄인다 | 느려진다 | 큰 변경 |
| 가벼운 review | 빠르다 | 기준이 흔들린다 | 작은 변경 |
| review + policy as code | 균형이 좋다 | 체계가 필요하다 | 성숙한 팀 |

좋은 architecture review는 판단을 늦추는 것이 아니라, **되돌릴 수 없는 실수를 줄이는 것**이다.

---

## 꼬리질문

- 어떤 변경은 리뷰보다 자동 policy가 더 적절한가?
- review가 취향 싸움으로 흐르지 않도록 어떻게 막을 것인가?
- approval theater를 어떻게 식별할 것인가?
- 리뷰 결과는 어디에 기록하고 어떻게 회수할 것인가?

## 한 줄 정리

Architecture review anti-patterns는 리뷰가 병목과 형식주의로 변질되는 패턴을 막고, 실제 구조적 리스크만 다루게 하는 운영 원칙이다.
