---
schema_version: 3
title: roomescape 예약 분기 if-else가 계속 늘어요 원인 라우터
concept_id: design-pattern/roomescape-reservation-branching-if-else-cause-router
canonical: false
category: design-pattern
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
review_feedback_tags:
- reservation-branch-axis-mix
- strategy-vs-state-vs-policy
- locator-drift-in-service
aliases:
- roomescape 예약 분기 if else 원인 라우터
- roomescape ReservationService switch 너무 많음
- 룸이스케이프 예약 로직 분기 어디서 쪼개지
- roomescape 패턴 선택 증상 라우터
- 예약 서비스 분기 축 섞임
symptoms:
- roomescape 예약 생성과 변경 로직에 if 문이 계속 늘어나는데 어떤 패턴으로 나눠야 할지 모르겠어요
- 리뷰에서 분기 축이 섞였다고 하는데 strategy로 갈지 state로 갈지 감이 안 와요
- ReservationService가 상태 확인, 규칙 판정, 구현 선택을 한 메서드에서 다 하고 있어요
- 예약 검증기를 늘렸는데도 서비스 switch 문이 줄지 않고 오히려 더 헷갈려졌어요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
- comparison
prerequisites:
- design-pattern/strategy-state-policy-object-decision-guide
- software-engineering/roomescape-reservation-flow-service-layer-bridge
next_docs:
- design-pattern/roomescape-reservation-status-state-pattern-bridge
- design-pattern/roomescape-strategy-vs-factory-bridge
- design-pattern/service-locator-antipattern
- design-pattern/strategy-state-policy-object-decision-guide
linked_paths:
- contents/design-pattern/roomescape-reservation-status-state-pattern-bridge.md
- contents/design-pattern/roomescape-strategy-vs-factory-bridge.md
- contents/design-pattern/service-locator-antipattern.md
- contents/design-pattern/strategy-state-policy-object-decision-guide.md
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
confusable_with:
- design-pattern/roomescape-reservation-status-state-pattern-bridge
- design-pattern/roomescape-strategy-vs-factory-bridge
- design-pattern/service-locator-antipattern
- design-pattern/strategy-state-policy-object-decision-guide
forbidden_neighbors:
- contents/design-pattern/roomescape-reservation-status-state-pattern-bridge.md
- contents/design-pattern/roomescape-strategy-vs-factory-bridge.md
- contents/design-pattern/service-locator-antipattern.md
expected_queries:
- roomescape 예약 서비스에서 상태 분기랑 검증 분기가 한꺼번에 커질 때 무엇부터 갈라 봐야 해?
- ReservationService switch 문이 커졌다는 리뷰를 받으면 패턴 선택을 어떤 질문 순서로 해야 해?
- 예약 변경 가능 여부와 검증기 선택과 빈 조회가 한 메서드에 섞여 있으면 각각 어디로 보내야 해?
- 룸이스케이프 미션에서 strategy인지 state인지 service locator 냄새인지 증상으로 구분하는 법이 있어?
- roomescape에서 검증 클래스를 늘렸는데도 if else가 줄지 않으면 무엇을 잘못 자른 걸까?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 ReservationService와 예약 도메인 주변의
  if-else, switch, validator 선택 코드가 계속 커질 때 원인을 가르는
  symptom_router다. 예약 상태 전이 분기, 검증 규칙 선택, 구현체 조회 helper,
  strategy인지 state인지 모르겠음, service가 getBean이나 map lookup까지 직접 함
  같은 학습자 표현을 state pattern, strategy/factory 경계, service locator
  antipattern, 패턴 비교 가이드 갈래로 라우팅한다.
---

# roomescape 예약 분기 if-else가 계속 늘어요 원인 라우터

## 한 줄 요약

> roomescape의 긴 분기는 "if 문이 많다"가 아니라 상태 전이, 규칙 판정, 구현 선택이 한 메서드에 눌어붙었다는 신호라서 먼저 어떤 질문이 섞였는지 갈라야 한다.

## 가능한 원인

1. **예약의 현재 상태에 따라 가능한 행동이 달라진다.** `CONFIRMED`일 때만 취소 가능하고 이미 지난 예약은 변경 불가처럼 "지금 이 예약이 무엇을 할 수 있나"가 핵심이면 상태 축이다. 이 갈래는 [roomescape 예약 상태 전이 ↔ 상태 패턴 브릿지](./roomescape-reservation-status-state-pattern-bridge.md)로 간다.
2. **검증 규칙 선택과 객체 생성 질문을 같은 패턴으로 풀려 한다.** 과거 시간 금지, 중복 예약 방지처럼 행동을 고르는 문제는 Strategy 쪽이고, 슬롯 객체를 어떤 타입으로 만들지 같은 생성 문제는 Factory 쪽이다. 이 경우는 [roomescape에서 예약 검증/시간 슬롯 결정에 Strategy vs Factory 어떤 게 맞나](./roomescape-strategy-vs-factory-bridge.md)를 먼저 본다.
3. **서비스가 구현체 조회까지 직접 한다.** `Map` 조회 helper나 `getBean` 호출로 validator, handler, policy를 서비스 본문에서 찾아 쓰고 있다면 분기 이전에 의존성 경계가 새고 있는 것이다. 이때는 [Service Locator Antipattern](./service-locator-antipattern.md)으로 가서 왜 lookup이 설계를 더 흐리게 만드는지 본다.
4. **패턴 이름은 붙였는데 질문 분리가 안 됐다.** Strategy, State, Policy Object를 모두 도입했는데도 "무엇을 고르는 코드인지"가 흐리면 축을 잘못 자른 것이다. 이 갈래는 [Strategy vs State vs Policy Object 결정 가이드](./strategy-state-policy-object-decision-guide.md)에서 다시 분기 기준을 잡는다.

## 빠른 자기 진단

1. 분기 조건이 `reservationStatus` 값이고 허용 행동이 달라진다면 state 갈래를 먼저 본다.
2. 분기 조건이 "어떤 검증기/정책을 실행할까"라면 strategy 또는 policy 축인지 확인한다. 생성 질문이면 factory 쪽이다.
3. 서비스 메서드 안에 `getBean`, 전역 registry, 문자열 bean name 조회가 보이면 locator drift를 먼저 의심한다.
4. 한 메서드에서 상태 검사와 validator 실행과 객체 생성이 모두 보이면 패턴 도입보다 질문 분리부터 다시 해야 한다.

## 다음 학습

- 상태 전이가 핵심이면 [roomescape 예약 상태 전이 ↔ 상태 패턴 브릿지](./roomescape-reservation-status-state-pattern-bridge.md)를 본다.
- 검증 규칙 선택과 생성 분기를 나누려면 [roomescape에서 예약 검증/시간 슬롯 결정에 Strategy vs Factory 어떤 게 맞나](./roomescape-strategy-vs-factory-bridge.md)를 잇는다.
- lookup helper가 설계를 흐리는지 보려면 [Service Locator Antipattern](./service-locator-antipattern.md)을 읽는다.
- 패턴 이름 자체가 헷갈리면 [Strategy vs State vs Policy Object 결정 가이드](./strategy-state-policy-object-decision-guide.md)로 돌아가 축을 다시 세운다.
