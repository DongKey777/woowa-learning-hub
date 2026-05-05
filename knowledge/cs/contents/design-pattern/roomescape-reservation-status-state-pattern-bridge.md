---
schema_version: 3
title: 'roomescape 예약 상태 전이 ↔ 상태 패턴 브릿지'
concept_id: design-pattern/roomescape-reservation-status-state-pattern-bridge
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- reservation-status-switch-sprawl
- invalid-transition-guard
- cancel-reschedule-state-modeling
aliases:
- roomescape 예약 상태 패턴
- roomescape 예약 상태 전이
- 룸이스케이프 예약 status switch
- roomescape cancel confirm state
- 예약 상태 enum 분기 roomescape
symptoms:
- roomescape에서 CONFIRMED CANCELED 같은 상태가 늘수록 service if 문이 길어져요
- 예약 취소 뒤에 다시 변경이 되거나 이미 지난 예약을 또 취소해도 되는 것처럼 보여요
- 상태 enum은 있는데 어떤 전이가 허용되는지 controller와 service가 같이 알고 있어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- design-pattern/state-pattern-workflow-payment
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
next_docs:
- design-pattern/state-pattern-workflow-payment
- design-pattern/strategy-vs-state-vs-policy-object
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
- design-pattern/aggregate-invariant-guard-pattern
linked_paths:
- contents/design-pattern/state-pattern-workflow-payment.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
- contents/design-pattern/aggregate-invariant-guard-pattern.md
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/database/roomescape-reservation-cancel-reschedule-active-predicate-bridge.md
- contents/database/roomescape-reservation-concurrency-bridge.md
confusable_with:
- design-pattern/roomescape-strategy-vs-factory-bridge
- design-pattern/strategy-vs-state-vs-policy-object
- database/roomescape-reservation-cancel-reschedule-active-predicate-bridge
forbidden_neighbors:
- contents/design-pattern/state-pattern-workflow-payment.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
expected_queries:
- roomescape 미션에서 예약 상태가 늘수록 service switch 문이 커지는데 이걸 상태 패턴으로 보라는 말이 무슨 뜻이야?
- CONFIRMED 예약이 취소된 뒤 다시 변경되면 안 된다는 규칙을 enum 말고 어디에 두라는 거야?
- roomescape에서 예약 변경과 취소 허용 여부를 현재 상태가 설명하게 만들라는 리뷰를 이해하고 싶어
- 예약 상태 전이 책임을 Reservation으로 올리라는 피드백은 controller와 service를 어떻게 바꾸라는 뜻이야?
- roomescape에서 상태 패턴과 예약 검증 전략을 왜 다른 질문으로 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 예약 생성 이후 취소, 변경, 만료 같은 상태가
  붙으면서 ReservationService의 switch 문과 status enum 분기가 커지는 장면을
  상태 패턴으로 읽게 돕는 mission_bridge다. confirmed/canceled 같은 예약 상태,
  허용 전이, 이미 끝난 예약 재변경 방지, controller와 service가 전이 규칙을 같이
  아는 구조, 상태 패턴과 전략 패턴 혼동이 이 문서의 핵심 검색 표면이다.
---

# roomescape 예약 상태 전이 ↔ 상태 패턴 브릿지

## 한 줄 요약

> roomescape에서 어려워지는 지점은 예약 row를 하나 더 저장하는 것이 아니라, "지금 이 예약이 취소될 수 있는가, 변경될 수 있는가, 이미 끝난 상태인가"가 단계마다 달라진다는 점이다. 이 분기가 커질수록 `status` enum과 service `switch` 문보다 상태 전이로 읽는 편이 낫다.

## 미션 시나리오

roomescape 미션이 예약 생성에서 끝나지 않고 취소, 변경, 지난 예약 처리까지 붙기 시작하면 학습자는 `ReservationStatus` enum 하나를 두고 service 메서드에서 `if (status == CONFIRMED)`처럼 분기하기 시작한다. 처음에는 간단해 보이지만, "이미 취소된 예약은 다시 바꿀 수 있나", "지난 예약은 취소 대신 종료로 봐야 하나", "변경 중 old slot과 new slot 사이에 어떤 상태를 거치나" 같은 질문이 붙는 순간 분기가 빠르게 길어진다.

리뷰에서 "`ReservationService`가 현재 상태와 허용 전이를 전부 알고 있네요", "`enum`은 있는데 전이 규칙은 객체가 모르네요"라는 코멘트가 나오는 이유가 여기 있다. 문제의 핵심은 상태 이름 부족이 아니라, 현재 단계에 따라 허용 행동이 달라지는 규칙이 controller와 service의 조건문으로 흩어진 데 있다.

## CS concept 매핑

상태 패턴으로 읽으면 reservation은 단순히 `status` 값을 들고 있는 데이터가 아니라, 현재 단계가 가능한 행동을 설명하는 객체가 된다. 예를 들어 `ConfirmedReservation`, `CanceledReservation`, `FinishedReservation`처럼 보면 `cancel`, `reschedule`, `markFinished`가 모든 상태에서 같은 의미를 가지지 않는다는 점이 드러난다.

roomescape에서 이 관점이 특히 중요한 이유는 취소와 변경이 단순 검증 문장이 아니라 상태 전이이기 때문이다. `CANCELED` 예약을 다시 변경하면 안 되고, 이미 지난 예약을 다시 확정하면 안 되며, 변경 중에는 old slot 해제와 new slot 점유가 같은 전이 맥락으로 읽혀야 한다. 전략 패턴이 "어떤 검증 알고리즘을 적용할까"를 묻는다면, 상태 패턴은 "지금 이 예약이 무엇을 할 수 있나"를 묻는다.

## 미션 PR 코멘트 패턴

- "`switch (reservationStatus)`가 서비스 여러 메서드에 반복되네요"라는 코멘트는 상태 이름만 있고 전이 책임은 아직 객체 밖에 있다는 뜻이다.
- "`이미 취소된 예약도 같은 reschedule 메서드를 타네요`"라는 피드백은 현재 상태가 허용 행동을 막지 못하고 있다는 신호다.
- "`취소 가능 여부 판단`과 `취소 실행`이 다른 계층에 흩어져 있어요"라는 코멘트는 전이 규칙과 유스케이스 조립을 다시 나누라는 뜻이다.
- "`전략으로 검증기를 나눴는데도 상태 혼란이 남아요`"라는 리뷰는 검증 규칙 선택과 상태 전이를 다른 축으로 보라는 의미다.

## 다음 학습

- 상태 전이를 일반화한 설명은 `상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기`에서 이어서 본다.
- 상태, 전략, 정책 객체 경계를 다시 자르려면 `Strategy vs State vs Policy Object`를 본다.
- roomescape에서 취소와 변경이 DB blocker 기준과 어떻게 연결되는지 보려면 `roomescape 예약 변경/취소 ↔ active predicate와 상태 전이 브릿지`를 함께 읽는다.
- 상태 전이 규칙을 aggregate 안에 가두는 쪽으로 더 보고 싶으면 `Aggregate Invariant Guard Pattern`을 잇는다.
