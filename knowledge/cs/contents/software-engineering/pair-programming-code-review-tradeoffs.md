---
schema_version: 3
title: Pair Programming and Code Review Trade-offs
concept_id: software-engineering/pair-programming-code-review-tradeoffs
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- pair-vs-review-choice
- review-latency-reduction
- high-risk-change-collaboration
aliases:
- pair programming
- code review tradeoff
- pair vs code review
- mob programming
- asynchronous review
- review latency
- collaboration quality gate
- 실시간 피드백 협업
- 페어 프로그래밍 리뷰 차이
- 위험한 작업 같이 코딩
- 코드 리뷰만으로 충분한가
symptoms:
- 구현 중 바로 같이 보는 게 좋은지 PR 리뷰만으로도 충분한지 판단이 안 돼요
- 리뷰가 자꾸 밀려서 배포가 느린데 pair programming을 늘리면 나아질지 모르겠어요
- 온보딩이나 위험한 변경에서 왜 pair를 권하는지 코드 리뷰와 차이가 헷갈려요
intents:
- comparison
- design
prerequisites:
- software-engineering/code-review-basics
- software-engineering/testing-strategy-and-test-doubles
next_docs:
- software-engineering/change-ownership-handoff-boundaries
- software-engineering/production-readiness-review
- software-engineering/architectural-fitness-functions
linked_paths:
- contents/software-engineering/code-review-basics.md
- contents/software-engineering/testing-strategy-and-test-doubles.md
- contents/software-engineering/change-ownership-handoff-boundaries.md
- contents/software-engineering/production-readiness-review.md
- contents/software-engineering/architectural-fitness-functions.md
- contents/software-engineering/lead-time-change-failure-recovery-loop.md
confusable_with:
- software-engineering/code-review-basics
- software-engineering/change-ownership-handoff-boundaries
- software-engineering/testing-strategy-and-test-doubles
forbidden_neighbors:
expected_queries:
- 위험한 변경을 할 때 pair programming이 code review보다 먼저 필요한 순간은 언제야?
- 리뷰가 자꾸 밀리는 팀이면 pair와 review 비율을 어떻게 조정해야 해?
- 온보딩 중인 개발자에게 pair를 붙이는 것과 PR 리뷰를 자세히 남기는 것 중 뭐가 더 효과적이야?
- mob programming까지 가야 하는 상황과 그냥 pair면 충분한 상황을 어떻게 나눠?
- code review가 있는데도 구현 단계에서 같이 코딩해야 한다는 말은 어떤 비용을 줄이려는 거야?
contextual_chunk_prefix: |
  이 문서는 pair programming과 code review를 대체재로 오해하는 학습자를 위한
  chooser다. 구현 중 즉시 설계 보정이 필요한지, PR 대기열과 review latency가
  더 큰 문제인지, 온보딩이나 장애 대응처럼 맥락 전파 속도가 중요한지, 기록과
  확장성이 더 중요한지 같은 질문을 실시간 피드백과 비동기 검토의 차이로
  연결한다.
---
# Pair Programming and Code Review Trade-offs

> 한 줄 요약: pair programming과 code review는 둘 다 품질 장치지만, 하나는 실시간 설계 보정에 강하고 다른 하나는 비동기적 검토와 지식 축적에 강하다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: pair programming code review tradeoffs basics, pair programming code review tradeoffs beginner, pair programming code review tradeoffs intro, software engineering basics, beginner software engineering, 처음 배우는데 pair programming code review tradeoffs, pair programming code review tradeoffs 입문, pair programming code review tradeoffs 기초, what is pair programming code review tradeoffs, how to pair programming code review tradeoffs
> 관련 문서:
> - [eXtreme Programming (XP)](./eXtremeProgramming.md)
> - [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Production Readiness Review](./production-readiness-review.md)

> retrieval-anchor-keywords:
> - pair programming
> - code review
> - mob programming
> - asynchronous review
> - quality gate
> - knowledge sharing
> - collaboration trade-off
> - review latency

## 핵심 개념

둘 다 "코드를 더 좋게 만드는 협업"이지만 역할이 다르다.

- pair programming은 구현 중 즉시 피드백
- code review는 구현 후 비동기 검토

즉 pair programming은 흐름을 멈추지 않으면서 품질을 높이고, code review는 팀 전체의 판단을 축적한다.

---

## 깊이 들어가기

### 1. pair programming은 실시간 리스크가 큰 작업에 강하다

좋은 경우:

- 낯선 도메인
- 복잡한 알고리즘
- 운영 위험이 큰 변경
- 온보딩 중인 개발자

장점:

- 설계 실수를 즉시 잡는다
- 지식이 실시간으로 공유된다
- 막히는 시간이 줄어든다

### 2. code review는 확장성과 기록성에 강하다

좋은 경우:

- 여러 파일에 걸친 변경
- 조직 표준 검토
- 아키텍처 경계 확인
- 성능/보안 관점 검토

장점:

- 여러 사람의 시각을 받을 수 있다
- 비동기적으로 진행된다
- 기록이 남는다

### 3. 둘은 대체재가 아니라 조합재다

실무에서는 보통 이렇게 쓴다.

- 위험한 핵심 로직은 pair로 만들고
- 리뷰는 경계와 정책을 보는 데 쓴다

즉 pair는 탐색, review는 확산이다.

### 4. review latency는 배포 리듬에 영향을 준다

리뷰가 오래 걸리면 작은 변경도 대기열에 쌓인다.

이 경우:

- 리뷰 범위를 줄이고
- policy as code로 자동화하고
- pair programming을 부분적으로 도입한다

### 5. mob programming은 극단적이지만 특정 상황에서는 유효하다

크리티컬 장애 대응, 대형 설계 문제, 전환 초기에 유효할 수 있다.

하지만 장기 운영 방식으로 쓰면 피로도가 높다.

---

## 실전 시나리오

### 시나리오 1: 위험한 결제 변경

pair programming으로 구현 중 실수를 줄이고, code review로 경계와 contract를 확인한다.

### 시나리오 2: 신규 합류자 온보딩

pair programming이 지식 전파에 매우 효과적이다.

### 시나리오 3: 대규모 아키텍처 변경

review만으로는 맥락이 늦게 맞춰질 수 있어, 핵심 구간은 pair로 함께 진행한다.

---

## 코드로 보기

```text
pair: think together while coding
review: verify decisions after change
```

둘은 속도와 확산의 균형을 맞춘다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| pair programming | 즉시 보정이 된다 | 인력 비용이 든다 | 위험한 작업 |
| code review | 확장성이 좋다 | 피드백이 늦다 | 일반 개발 |
| hybrid | 균형이 좋다 | 운영 규칙이 필요하다 | 성숙한 팀 |

협업 방식의 핵심은 "누가 더 똑똑한가"가 아니라 **언제 어떤 피드백을 받을 것인가**다.

---

## 꼬리질문

- 어떤 작업은 pair가 더 안전한가?
- review latency는 배포를 막고 있지 않은가?
- 지식 분산이 필요한 구간은 어디인가?
- code review가 형식화되어 있지 않은가?

## 한 줄 정리

Pair programming과 code review는 실시간 설계 보정과 비동기적 검증이라는 서로 다른 장점을 가지며, 위험도와 팀 성숙도에 따라 조합해야 한다.
