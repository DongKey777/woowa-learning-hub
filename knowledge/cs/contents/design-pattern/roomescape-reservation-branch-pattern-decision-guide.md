---
schema_version: 3
title: roomescape 예약 분기 패턴 결정 가이드
concept_id: design-pattern/roomescape-reservation-branch-pattern-decision-guide
canonical: false
category: design-pattern
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/roomescape
review_feedback_tags:
- reservation-pattern-choice
- strategy-vs-factory-vs-policy-vs-state
- branch-axis-mix
aliases:
- roomescape 예약 분기 패턴 선택
- roomescape strategy factory policy state chooser
- 룸이스케이프 패턴 경계 분기표
- 예약 검증 생성 상태 전이 패턴 구분
- roomescape 패턴 이름 헷갈림
symptoms:
- roomescape에서 예약 코드를 나누려는데 strategy, factory, policy object, state 중 이름을 뭘 붙여야 할지 모르겠어요
- 리뷰에서 분기 축이 섞였다고 하는데 예약 검증, 슬롯 생성, 상태 변경을 같은 패턴으로 설명하고 있어요
- ReservationService if 문을 쪼개고 싶은데 무엇이 규칙이고 무엇이 생성이고 무엇이 상태인지 헷갈려요
intents:
- comparison
- design
- mission_bridge
prerequisites:
- design-pattern/strategy-state-policy-object-decision-guide
- software-engineering/roomescape-reservation-responsibility-placement-decision-guide
next_docs:
- design-pattern/roomescape-strategy-vs-factory-bridge
- design-pattern/roomescape-reservation-booking-policy-object-bridge
- design-pattern/roomescape-reservation-status-state-pattern-bridge
- software-engineering/roomescape-reservation-responsibility-placement-decision-guide
linked_paths:
- contents/design-pattern/roomescape-strategy-vs-factory-bridge.md
- contents/design-pattern/roomescape-reservation-booking-policy-object-bridge.md
- contents/design-pattern/roomescape-reservation-status-state-pattern-bridge.md
- contents/design-pattern/strategy-state-policy-object-decision-guide.md
- contents/software-engineering/roomescape-reservation-responsibility-placement-decision-guide.md
confusable_with:
- design-pattern/roomescape-strategy-vs-factory-bridge
- design-pattern/roomescape-reservation-booking-policy-object-bridge
- design-pattern/roomescape-reservation-status-state-pattern-bridge
- software-engineering/roomescape-reservation-responsibility-placement-decision-guide
forbidden_neighbors:
- contents/design-pattern/roomescape-strategy-vs-factory-bridge.md
- contents/design-pattern/roomescape-reservation-booking-policy-object-bridge.md
- contents/design-pattern/roomescape-reservation-status-state-pattern-bridge.md
- contents/software-engineering/roomescape-reservation-responsibility-placement-decision-guide.md
expected_queries:
- roomescape에서 예약 검증기를 나누는 일과 시간 슬롯 객체를 만드는 일을 왜 같은 패턴으로 보면 안 돼?
- 예약 가능 여부 판정, 구현 선택, 상태 전이를 한 표에서 빠르게 구분하는 기준이 필요해
- roomescape 미션 리뷰에서 분기 축이 섞였다는 말은 strategy와 policy object와 state를 어떻게 다르게 보라는 뜻이야?
- 예약 생성 코드가 길어질 때 factory를 쓸지 policy object를 쓸지 state로 올릴지 판단 순서가 있어?
- 슬롯 생성 분기와 예약 취소 가능 여부를 같은 리팩터링으로 풀면 왜 자꾸 이름이 어색해져?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 예약 관련 분기를 어떤 패턴으로
  설명해야 하는지 고르는 chooser다. 예약 검증 규칙 추가, 시간 슬롯이나 응답
  객체 생성, 현재 상태에 따른 취소와 변경 허용, 서비스 if 문 비대화 같은
  장면을 strategy, factory, policy object, state 네 갈래로 가른다.
  분기 축이 섞였다, 패턴 이름이 안 잡힌다, 무엇이 규칙이고 무엇이 상태인지
  모르겠다는 학습자 표현이 이 문서의 결정 매트릭스에 매핑된다.
---

# roomescape 예약 분기 패턴 결정 가이드

## 한 줄 요약

> roomescape에서 같은 `if` 문처럼 보여도 "구현을 고르나", "객체를 만드나", "허용 여부를 판정하나", "현재 상태가 행동을 바꾸나"에 따라 패턴 이름이 달라진다.

## 결정 매트릭스

| roomescape에서 지금 답하는 질문 | 더 가까운 패턴 | 먼저 볼 문서 |
| --- | --- | --- |
| 어떤 검증기나 구현을 골라 같은 요청을 처리할까 | Strategy | `roomescape에서 예약 검증/시간 슬롯 결정에 Strategy vs Factory 어떤 게 맞나` |
| 어떤 종류의 시간 슬롯이나 객체를 만들까 | Factory | `roomescape에서 예약 검증/시간 슬롯 결정에 Strategy vs Factory 어떤 게 맞나` |
| 이 날짜와 시간에 지금 예약을 받아도 되는가 | Policy Object | `roomescape 예약 가능 여부 판단 ↔ Policy Object 브릿지` |
| 이미 확정되거나 취소된 예약이 지금 변경·취소될 수 있는가 | State | `roomescape 예약 상태 전이 ↔ 상태 패턴 브릿지` |
| 패턴보다 controller, service, repository 책임이 먼저 엉켜 있는가 | 책임 배치부터 분리 | `roomescape 예약 생성 책임 배치 결정 가이드` |

짧게 외우면, 구현 선택은 strategy, 생성 분기는 factory, 규칙 판정은 policy object, 현재 단계에 따라 허용 행동이 달라지면 state다.

## 흔한 오선택

검증 규칙이 많다는 이유만으로 전부 strategy라고 부르는 경우가 많다.
하지만 "가능한가, 왜 안 되는가"가 중심이면 실행 방식 교체보다 policy object 쪽 설명력이 더 크다.

반대로 `ReservationTime`이나 응답 객체를 만드는 분기를 policy object로 부르면 생성 축과 판정 축이 섞인다.
이 장면은 허용 여부보다 어떤 인스턴스를 반환할지가 핵심이라 factory 질문에 가깝다.

또 취소 가능 여부와 변경 허용을 validator 체인으로만 밀어 넣는 경우도 흔하다.
이미 확정된 예약과 취소된 예약이 같은 메서드를 타되 허용 행동이 달라진다면, 현재 상태가 행동을 설명하는 state 질문이 먼저다.

마지막으로 패턴 이름을 붙이기 전에 책임 배치가 섞여 있는 경우도 있다.
controller, service, repository 경계가 먼저 흐리면 패턴 선택보다 책임 분리가 선행되어야 한다.

## 다음 학습

- 검증기 선택과 객체 생성을 두 축으로 먼저 가르려면 [roomescape에서 예약 검증/시간 슬롯 결정에 Strategy vs Factory 어떤 게 맞나](./roomescape-strategy-vs-factory-bridge.md)를 본다.
- 예약 가능 여부 판정을 규칙 객체로 올리는 기준은 [roomescape 예약 가능 여부 판단 ↔ Policy Object 브릿지](./roomescape-reservation-booking-policy-object-bridge.md)에서 잇는다.
- 취소와 변경 허용이 현재 단계에 묶이는 순간은 [roomescape 예약 상태 전이 ↔ 상태 패턴 브릿지](./roomescape-reservation-status-state-pattern-bridge.md)로 이어서 본다.
- 아직 패턴보다 계층 책임이 더 흐리다면 [roomescape 예약 생성 책임 배치 결정 가이드](../software-engineering/roomescape-reservation-responsibility-placement-decision-guide.md)로 먼저 내려간다.
