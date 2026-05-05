---
schema_version: 3
title: lotto 책임 경계가 자꾸 섞여요 원인 라우터
concept_id: software-engineering/lotto-boundary-mixing-cause-router
canonical: false
category: software-engineering
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
  - missions/lotto
review_feedback_tags:
  - boundary-mixing
  - input-parsing-leak
  - purchase-flow-orchestration
  - result-object-boundary
aliases:
  - lotto 책임 경계
  - 로또 역할 분리
  - lotto layer boundary
  - 로또 클래스가 너무 많은 일
  - lotto controller service domain 섞임
  - 로또 책임 분리 어디서
  - lotto boundary mixing
symptoms:
  - lotto 한 클래스가 입력 파싱, 번호 생성, 결과 계산까지 다 하고 있어요
  - controller, service, domain이 서로 너무 많이 알아요
  - 리뷰에서 생성 책임과 검증 책임, 출력 책임을 나누라고 하는데 어디부터 잘라야 할지 모르겠어요
  - 수동/자동 생성, 구매 흐름, 통계 출력이 한 메서드에 붙어 있어요
intents:
  - symptom
  - troubleshooting
  - mission_bridge
prerequisites:
  - software-engineering/lotto-domain-invariant-bridge
  - software-engineering/service-layer-basics
next_docs:
  - software-engineering/lotto-inputview-domain-conversion-boundary-bridge
  - software-engineering/lotto-purchase-flow-service-layer-bridge
  - design-pattern/lotto-manual-auto-number-generator-strategy-bridge
  - software-engineering/lotto-winning-statistics-result-object-bridge
linked_paths:
  - contents/software-engineering/lotto-domain-invariant-bridge.md
  - contents/software-engineering/lotto-inputview-domain-conversion-boundary-bridge.md
  - contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
  - contents/design-pattern/lotto-manual-auto-number-generator-strategy-bridge.md
  - contents/software-engineering/lotto-winning-statistics-result-object-bridge.md
confusable_with:
  - software-engineering/lotto-inputview-domain-conversion-boundary-bridge
  - software-engineering/lotto-purchase-flow-service-layer-bridge
  - design-pattern/lotto-manual-auto-number-generator-strategy-bridge
  - software-engineering/lotto-winning-statistics-result-object-bridge
forbidden_neighbors:
  - contents/software-engineering/lotto-inputview-domain-conversion-boundary-bridge.md
  - contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
  - contents/design-pattern/lotto-manual-auto-number-generator-strategy-bridge.md
  - contents/software-engineering/lotto-winning-statistics-result-object-bridge.md
expected_queries:
  - 로또 미션 코드가 자꾸 한 군데로 몰리는데 먼저 입력 쪽을 자를지 서비스 흐름을 자를지 어떻게 판단해?
  - controller에서 Lotto를 만들고 OutputView에서 수익률까지 계산하면 어떤 책임이 섞인 거야?
  - 수동 번호 생성과 여러 장 구매 반복, 통계 출력이 한 메서드에 있을 때 어디부터 분리해야 해?
  - 로또 리뷰에서 역할이 섞였다는 말을 들었는데 생성 seam 문제인지 결과 객체 문제인지 어떻게 구분해?
  - 로또 미션에서 클래스가 서로 너무 많이 아는 느낌일 때 어떤 문서부터 보면 돼?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션에서 입력 파싱, 한 장 로또 검증, 여러 장 구매 흐름,
  자동 번호 생성 seam, 당첨 통계 결과 조립이 한 클래스나 한 메서드에 섞여 보일 때
  원인을 네 갈래로 나누는 symptom_router다. controller가 Lotto를 만들고,
  service가 Random을 직접 돌리고, OutputView가 수익률을 다시 계산하는 식의
  학습자 표현을 경계 누수 원인별 문서로 라우팅한다.
---

# lotto 책임 경계가 자꾸 섞여요 원인 라우터

## 한 줄 요약

> lotto 코드가 한곳으로 몰리는 건 보통 "객체 수가 적어서"가 아니라 입력 해석, 한 장 규칙, 여러 장 유스케이스, 결과 표현이 각각 다른 질문인데도 한 메서드가 전부 떠안기 때문이다.

## 가능한 원인

1. **입력 문자열 해석이 도메인 생성까지 침범했다.** `InputView`나 controller가 `"1,2,3,4,5,6"`을 자르는 데서 끝나지 않고 바로 `Lotto`와 `WinningNumbers`를 만들기 시작하면, 형식 변환 책임과 도메인 규칙 책임이 붙는다. 이 갈래는 [lotto InputView 문자열 파싱 ↔ DTO/도메인 변환 경계 브릿지](./lotto-inputview-domain-conversion-boundary-bridge.md)로 간다.
2. **한 장 규칙과 여러 장 구매 흐름이 같은 곳에 있다.** `money / 1000`, 반복 생성, `List<Lotto>` 조립까지 `Lotto`나 controller가 맡으면 "한 장이 유효한가"와 "구매 유스케이스를 어떻게 끝까지 조립하나"가 섞인다. 이 경우는 [lotto 여러 장 구매 흐름 ↔ Service 계층 브릿지](./lotto-purchase-flow-service-layer-bridge.md)로 보내서 orchestration 책임을 분리한다.
3. **자동 번호 생성 seam이 없어 수동/자동 경로가 분기 폭발로 번졌다.** `Lotto.auto()` 안에서 `Random`을 직접 쓰거나 `numbers == null` 같은 분기로 수동과 자동을 같이 처리하면 생성 알고리즘 교체 지점이 사라진다. 이 갈래는 [lotto 수동 입력/자동 생성 ↔ NumberGenerator 전략 브릿지](../design-pattern/lotto-manual-auto-number-generator-strategy-bridge.md)로 이어진다.
4. **계산이 끝난 결과를 타입으로 닫지 않아 출력 책임이 새고 있다.** `Map<Rank, Integer>`와 구매 금액을 흘리며 `OutputView`가 수익률을 다시 계산하면 결과 의미와 표현 포맷이 한 덩어리가 된다. 이때는 [lotto 당첨 통계/수익률 계산 ↔ 결과 객체 경계 브릿지](./lotto-winning-statistics-result-object-bridge.md)를 먼저 본다.

## 빠른 자기 진단

1. 문자열 split, 숫자 변환, 예외 메시지 조립이 많으면 입력 변환 경계부터 의심한다. 이 단계에서 이미 `new Lotto(...)`가 보이면 1번 갈래 신호다.
2. `money / 1000`, 반복문, 여러 장 컬렉션 조립이 한 메서드에 있으면 서비스 흐름 누수다. 한 장 규칙보다 유스케이스 orchestration이 먼저 섞인 상황이다.
3. `Random`, `Collections.shuffle`, `manual 여부 if`가 도메인 객체 내부에 있으면 생성 seam 문제다. 자동 생성 규칙을 바꿔 끼우거나 테스트 더블을 넣기 어렵다면 3번 갈래가 맞다.
4. 출력 직전에 수익률이나 등수별 개수를 다시 계산하면 결과 객체 경계 문제다. 출력 포맷이 아니라 계산 완료 상태를 어디서 닫을지 먼저 본다.

## 다음 학습

- 입력 해석과 도메인 생성의 경계를 먼저 자르려면 [lotto InputView 문자열 파싱 ↔ DTO/도메인 변환 경계 브릿지](./lotto-inputview-domain-conversion-boundary-bridge.md)를 본다.
- 구매 1회가 어떤 유스케이스 조립인지 다시 잡으려면 [lotto 여러 장 구매 흐름 ↔ Service 계층 브릿지](./lotto-purchase-flow-service-layer-bridge.md)를 잇는다.
- 수동/자동 생성 분기와 `Random` 의존성부터 분리하려면 [lotto 수동 입력/자동 생성 ↔ NumberGenerator 전략 브릿지](../design-pattern/lotto-manual-auto-number-generator-strategy-bridge.md)를 읽는다.
- 통계와 수익률을 의미 있는 결과 타입으로 닫으려면 [lotto 당첨 통계/수익률 계산 ↔ 결과 객체 경계 브릿지](./lotto-winning-statistics-result-object-bridge.md)를 이어서 본다.
