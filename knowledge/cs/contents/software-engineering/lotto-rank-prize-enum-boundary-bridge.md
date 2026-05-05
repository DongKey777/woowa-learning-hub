---
schema_version: 3
title: 'lotto 당첨 등수/상금 규칙 ↔ Rank enum 경계 브릿지'
concept_id: software-engineering/lotto-rank-prize-enum-boundary-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- rank-enum-boundary
- prize-policy-location
- result-calculation-leak
aliases:
- lotto 등수 enum 책임
- 로또 Rank 상금 규칙
- lotto 당첨 등수 객체
- 로또 상금 테이블 위치
- lotto rank policy boundary
symptoms:
- 등수별 상금과 일치 개수 조건이 service if문에 길게 늘어져 있어요
- Rank enum이 있는데도 보너스 번호 여부와 상금 계산을 다른 클래스가 다시 판단해요
- 결과 출력 직전에 등수 규칙을 또 해석하느라 책임이 흩어져 보여요
intents:
- mission_bridge
- design
prerequisites:
- software-engineering/domain-invariants-as-contracts
- software-engineering/lotto-winning-numbers-value-object-boundary-bridge
next_docs:
- software-engineering/lotto-winning-statistics-result-object-bridge
- design-pattern/lotto-strategy-rank-decision-bridge
- software-engineering/lotto-winning-numbers-value-object-boundary-bridge
linked_paths:
- contents/software-engineering/domain-invariants-as-contracts.md
- contents/software-engineering/lotto-winning-numbers-value-object-boundary-bridge.md
- contents/software-engineering/lotto-winning-statistics-result-object-bridge.md
- contents/design-pattern/lotto-strategy-rank-decision-bridge.md
confusable_with:
- design-pattern/lotto-strategy-rank-decision-bridge
- software-engineering/lotto-winning-statistics-result-object-bridge
- software-engineering/lotto-winning-numbers-value-object-boundary-bridge
forbidden_neighbors: []
expected_queries:
- 로또 미션에서 등수별 상금이랑 일치 개수 규칙을 Rank enum 안에 넣으라는 말은 무슨 뜻이야?
- 당첨 결과 계산할 때 if문으로 1등 2등 3등을 나누지 말고 enum으로 묶으라는 리뷰를 받았어. 왜 그래?
- 보너스 번호 포함 여부와 상금 금액을 서비스가 아니라 Rank가 알아야 한다는 이유가 뭐야?
- 로또 결과 출력 전에 등수 규칙을 여러 클래스가 다시 해석하는 구조가 왜 어색해?
- Rank enum은 그냥 이름만 들고 있고 상금 계산은 밖에서 해도 되나?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션에서 당첨 번호 비교 뒤 등수 이름, 일치 개수 기준,
  보너스 번호 여부, 상금 금액을 어디에 모아야 하는지 설명하는 mission_bridge다.
  등수 if문이 service에 김, Rank enum이 이름만 들고 있음, 상금 규칙 위치가
  흔들림, 결과 출력 전에 등수 조건을 다시 해석함, 보너스 포함 여부를 여러
  클래스가 반복 계산함 같은 학습자 표현을 enum 경계와 결과 규칙 응집 관점으로
  연결한다.
---

# lotto 당첨 등수/상금 규칙 ↔ Rank enum 경계 브릿지

## 한 줄 요약

> lotto의 `Rank`는 단순한 표시 이름보다 "몇 개 맞으면 이 등수인지"와 "상금이 얼마인지"를 함께 들고 있는 규칙 경계에 가깝다. 그래서 서비스가 긴 `if`로 등수를 다시 해석하기보다, 비교 결과를 `Rank`로 닫고 나머지는 그 의미를 읽는 편이 덜 흔들린다.

## 미션 시나리오

lotto 미션 후반에 자주 나오는 구조는 이렇다. 서비스가 티켓 한 장과 `WinningNumbers`를 비교한 뒤, `matchCount == 6`, `matchCount == 5 && bonus`, `matchCount == 5` 같은 분기를 길게 나열해 등수를 정한다. 그다음 또 다른 곳에서 상금 금액을 `switch`로 다시 붙이고, 출력 단계는 같은 등수 순서를 다시 배열한다.

처음에는 빠르지만 곧 같은 규칙이 세 군데로 흩어진다. "2등은 5개 일치 + 보너스"라는 사실을 서비스도 알고 결과 집계도 알고 출력도 암묵적으로 기대하게 된다. 리뷰에서 "`Rank`가 이름표만 들고 있네요", "등수 규칙을 서비스가 너무 많이 안다"는 말이 나오는 이유가 여기다.

## CS concept 매핑

이 장면은 패턴 선택보다 "규칙을 어느 타입 경계에 응집시킬 것인가"의 문제에 가깝다. `WinningNumbers`가 비교 기준의 불변식을 묶는 값 객체라면, `Rank`는 비교 결과의 분류 규칙을 묶는 enum 계약이 될 수 있다.

짧게 보면 흐름은 `Rank rank = Rank.from(matchCount, bonusMatched);`처럼 끝나는 편이 자연스럽다. 그러면 서비스는 티켓들을 비교해 `Rank`를 얻고, `WinningStatistics`는 그 `Rank`를 세면 된다. 상금도 `rank.getPrize()`처럼 읽으면 되므로 결과 객체나 출력 계층이 "2등이면 3천만 원"을 다시 외울 필요가 없다.

핵심은 enum을 무조건 똑똑하게 만들자는 뜻이 아니다. 핵심은 닫힌 규칙 집합이라면 그 집합을 대표하는 타입이 최소한의 의미를 같이 들고 있게 하자는 것이다. lotto 등수는 외부 입력마다 새로 늘어나는 규칙이 아니라 미션 안에서 닫혀 있으므로, 서비스의 분기문보다 `Rank` 경계에 규칙을 붙이는 쪽이 읽기 쉽다.

## 미션 PR 코멘트 패턴

- "`matchCount == 5 && bonus` 같은 분기가 서비스와 출력 코드에 같이 있으면 등수 규칙이 중복됩니다."
- "`Rank`가 문자열 라벨만 들고 있으면 상금표와 판정표가 밖으로 새어 나갑니다."
- "서비스는 등수를 계산한 결과를 얻는 자리이지, 등수 표 전체를 매번 다시 해석하는 자리가 아닙니다."
- "등수 규칙이 닫힌 집합이면 enum에 응집시키고, 결과 집계는 그 enum을 세는 쪽으로 단순화해 보세요."

## 다음 학습

- 등수 규칙을 enum으로 둘지 전략으로 펼칠지 더 비교하려면 `design-pattern/lotto-strategy-rank-decision-bridge`
- 등수별 개수와 수익률을 결과 객체로 닫는 다음 단계는 `software-engineering/lotto-winning-statistics-result-object-bridge`
- 비교 기준 자체를 값 객체로 잠그는 이유를 다시 보려면 `software-engineering/lotto-winning-numbers-value-object-boundary-bridge`
