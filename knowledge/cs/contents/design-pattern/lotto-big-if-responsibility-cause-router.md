---
schema_version: 3
title: lotto 긴 if/switch 분기 비대화 원인 라우터
concept_id: design-pattern/lotto-big-if-responsibility-cause-router
canonical: false
category: design-pattern
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/lotto
review_feedback_tags:
- mixed-responsibility-big-if
- static-factory-vs-strategy
- rank-decision-boundary
- result-object-leak
aliases:
- lotto 긴 if 문 원인
- 로또 switch 분기 비대화
- lotto 패턴 경계 라우터
- 로또 수동 자동 등수 분기
- lotto big if router
symptoms:
- lotto 미션 코드에서 if 문이나 switch가 계속 길어져요
- 수동 입력, 자동 생성, 등수 판정, 통계 출력 분기가 한 메서드에 다 붙어 있어요
- 리뷰에서 정적 팩토리, 전략, 결과 객체 얘기가 같이 나와서 무엇부터 봐야 할지 모르겠어요
- controller나 service 한 곳이 로또 생성부터 결과 출력 직전 계산까지 다 들고 있어요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- software-engineering/lotto-input-parsing-vs-domain-invariant-vs-purchase-flow-decision-guide
next_docs:
- design-pattern/lotto-static-factory-bridge
- design-pattern/lotto-manual-auto-number-generator-strategy-bridge
- design-pattern/lotto-strategy-rank-decision-bridge
- software-engineering/lotto-winning-statistics-result-object-bridge
linked_paths:
- contents/software-engineering/lotto-input-parsing-vs-domain-invariant-vs-purchase-flow-decision-guide.md
- contents/design-pattern/lotto-static-factory-bridge.md
- contents/design-pattern/lotto-manual-auto-number-generator-strategy-bridge.md
- contents/design-pattern/lotto-strategy-rank-decision-bridge.md
- contents/software-engineering/lotto-winning-statistics-result-object-bridge.md
confusable_with:
- design-pattern/lotto-static-factory-bridge
- design-pattern/lotto-manual-auto-number-generator-strategy-bridge
- design-pattern/lotto-strategy-rank-decision-bridge
- software-engineering/lotto-winning-statistics-result-object-bridge
forbidden_neighbors:
- contents/design-pattern/lotto-static-factory-bridge.md
- contents/design-pattern/lotto-manual-auto-number-generator-strategy-bridge.md
- contents/design-pattern/lotto-strategy-rank-decision-bridge.md
- contents/software-engineering/lotto-winning-statistics-result-object-bridge.md
expected_queries:
- 로또 미션에서 긴 if 문이 생겼을 때 이게 생성 경로 문제인지 등수 판정 문제인지 어떻게 구분해?
- 수동 구매와 자동 구매, 결과 통계까지 한 메서드에 몰렸는데 어떤 문서부터 보면 돼?
- lotto 리뷰에서 정적 팩토리로 빼라, 전략으로 바꿔라, 결과 객체를 만들라가 같이 나오면 무엇부터 판단해야 해?
- controller나 service의 switch가 계속 커질 때 로또 미션에서는 어떤 책임 축으로 쪼개야 해?
- 로또 코드 비대화가 단순 리팩터링 문제가 아니라 패턴 경계 혼합인지 빠르게 진단하는 방법이 있어?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션에서 긴 if/switch 하나에 생성 경로 이름짓기,
  수동/자동 번호 생성 선택, 당첨 등수 판정, 통계 결과 조립이 함께 섞여 보일 때
  원인을 갈라 주는 symptom_router다. lotto 긴 if 문, 수동 자동 분기와 등수
  계산이 한 메서드에 붙음, 정적 팩토리와 전략과 결과 객체 리뷰가 한꺼번에 나옴,
  controller나 service가 모든 분기를 들고 있음 같은 학습자 표현을 다음 문서로
  라우팅한다.
---

# lotto 긴 if/switch 분기 비대화 원인 라우터

## 한 줄 요약

> lotto의 긴 `if`나 `switch`는 보통 "조건이 많아서"보다 생성 경로 이름짓기, 번호 생성 방식 선택, 등수 판정 규칙, 결과 표현이 서로 다른 질문인데도 한 메서드가 전부 떠안고 있기 때문에 커진다.

## 가능한 원인

1. **생성 경로 이름이 없어 수동 입력과 자동 생성이 생성자 분기로 붙었다.** `new Lotto(numbers)`와 `Lotto.auto()` 성격이 다른데 `numbers == null` 같은 분기로 한 곳에서 처리하면 생성 의도가 숨고 분기가 자란다. 이 갈래는 [lotto 미션 Lotto.from / Lotto.auto 정적 팩토리 메소드의 의도](./lotto-static-factory-bridge.md)로 이어서 생성 경로 이름을 먼저 세운다.
2. **번호를 어떻게 만들지와 한 장 규칙이 같은 곳에 있다.** `Random` 호출, 수동 번호 전달, 테스트용 고정 번호 주입이 `Lotto` 내부나 서비스 `if` 문에 같이 있으면 알고리즘 선택 문제가 한 장 불변식과 섞인다. 이 경우는 [lotto 수동 입력/자동 생성 ↔ NumberGenerator 전략 브릿지](./lotto-manual-auto-number-generator-strategy-bridge.md)로 보내서 생성 방식을 별도 seam으로 읽는다.
3. **등수 판정 규칙을 상태 전이처럼 취급해 분기가 커졌다.** "`일치 개수 + 보너스 번호`면 몇 등인가" 같은 질문은 구매 흐름이 아니라 판정 규칙 문제다. 이때는 [lotto 당첨 등수 결정 로직에서 Strategy 패턴이 어울리는 이유](./lotto-strategy-rank-decision-bridge.md)로 가서 enum 매핑, 정적 판정 메서드, 전략 오남용 경계를 먼저 본다.
4. **계산이 끝난 결과를 타입으로 닫지 않아 출력 직전 분기가 계속 남는다.** 등수별 개수와 수익률을 `Map`과 `double`로 흘리면 출력 계층이 "`이 등수는 몇 번째 줄에 보여줄까`", "`수익률은 여기서 다시 계산할까`" 같은 분기를 다시 품는다. 이때는 [lotto 당첨 통계/수익률 계산 ↔ 결과 객체 경계 브릿지](../software-engineering/lotto-winning-statistics-result-object-bridge.md)로 이어서 결과 의미를 먼저 잠근다.

## 빠른 자기 진단

1. `null`, `manual`, `auto` 같은 값으로 생성 경로를 나누고 있으면 정적 팩토리 갈래가 먼저다.
2. `Random`, `shuffle`, 테스트용 고정 번호 주입 조건이 보이면 전략 seam 문제를 의심한다.
3. 분기 대부분이 "`몇 개 맞았는가`", "`보너스가 맞았는가`"를 해석하는 데 쓰이면 등수 판정 규칙 갈래가 더 가깝다.
4. 출력 직전에 등수별 개수 정렬, 수익률 계산, 문장 조립 분기가 남아 있으면 결과 객체 경계부터 본다.
5. 위 네 축이 둘 이상 동시에 보이면 먼저 [lotto 입력 파싱 vs 도메인 불변식 vs 구매 흐름 결정 가이드](../software-engineering/lotto-input-parsing-vs-domain-invariant-vs-purchase-flow-decision-guide.md)로 전체 책임을 정리하고, 그다음 가장 긴 분기 하나만 고른다.

## 다음 학습

- 생성자 분기를 이름 있는 진입점으로 바꾸는 기준은 [lotto 미션 Lotto.from / Lotto.auto 정적 팩토리 메소드의 의도](./lotto-static-factory-bridge.md)에서 본다.
- 수동/자동 생성 알고리즘을 별도 객체로 빼는 감각은 [lotto 수동 입력/자동 생성 ↔ NumberGenerator 전략 브릿지](./lotto-manual-auto-number-generator-strategy-bridge.md)로 잇는다.
- 등수 판정이 전략인지 단순 매핑인지 가르는 기준은 [lotto 당첨 등수 결정 로직에서 Strategy 패턴이 어울리는 이유](./lotto-strategy-rank-decision-bridge.md)를 본다.
- 통계와 수익률을 계산 완료된 결과 타입으로 닫으려면 [lotto 당첨 통계/수익률 계산 ↔ 결과 객체 경계 브릿지](../software-engineering/lotto-winning-statistics-result-object-bridge.md)를 이어서 읽는다.
