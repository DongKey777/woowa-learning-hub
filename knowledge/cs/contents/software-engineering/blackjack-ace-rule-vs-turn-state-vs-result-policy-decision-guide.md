---
schema_version: 3
title: 'blackjack 점수 규칙 vs 턴 상태 vs 결과 판정 결정 가이드'
concept_id: software-engineering/blackjack-ace-rule-vs-turn-state-vs-result-policy-decision-guide
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids:
- missions/blackjack
review_feedback_tags:
- ace-rule-vs-turn-flow
- state-vs-policy-boundary
- dealer-rule-placement
aliases:
- blackjack 규칙 분리 기준
- 블랙잭 점수 계산과 턴 흐름 구분
- 블랙잭 상태 패턴 policy object 경계
- 블랙잭 ace 규칙 위치
- 블랙잭 dealer 규칙 분리
symptoms:
- Ace 계산, hit/stand 흐름, 승패 비교가 한 클래스에 다 붙어 있어 어디부터 쪼개야 할지 모르겠어요
- blackjack 리뷰에서 상태 패턴과 정책 객체 이야기가 같이 나와서 같은 말처럼 들려요
- dealer가 한 장 더 뽑는 규칙과 bust 계산을 같은 책임으로 묶어도 되나 헷갈려요
intents:
- comparison
- design
- mission_bridge
prerequisites:
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/blackjack-winner-decision-policy-object-bridge
next_docs:
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/blackjack-winner-decision-policy-object-bridge
linked_paths:
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
- contents/design-pattern/blackjack-action-input-command-bridge.md
confusable_with:
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/blackjack-winner-decision-policy-object-bridge
forbidden_neighbors:
- contents/spring/blackjack-web-state-mixing-cause-router.md
expected_queries:
- 블랙잭에서 Ace 합계 계산과 hit stand 단계 처리를 왜 같은 패턴으로 보면 안 돼?
- dealer가 16 이하면 한 장 더 뽑는 규칙은 상태 패턴이야 정책 객체야?
- blackjack 미션에서 bust 계산, 턴 종료, 최종 승패 비교를 나누는 기준이 뭐야?
- 블랙잭 리뷰에서 점수 규칙은 값 객체로, 흐름은 상태로 보라는 말이 정확히 어떻게 다른 거야?
- 블랙잭 코드가 긴 if 문 하나인데 어떤 부분은 불변식이고 어떤 부분은 결과 판정인지 빨리 가르는 법이 있어?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 Ace 합계 보장, hit/stand 단계,
  dealer 추가 draw, 최종 승패 비교가 한 코드에 섞였을 때 무엇을 값 규칙, 턴
  전이, 결과 해석으로 나눌지 결정하는 chooser다. Ace를 어디서 계산하지,
  dealer는 언제 더 뽑지, bust 판정과 라운드 종료를 같은 책임으로 봐도 되나,
  긴 조건문을 어떤 경계로 자르지 같은 자연어 paraphrase가 본 문서의 판단
  기준에 매핑된다.
---

# blackjack 점수 규칙 vs 턴 상태 vs 결과 판정 결정 가이드

## 한 줄 요약

> 손패 합계와 bust/blackjack 보장은 도메인 규칙, 지금 hit/stand가 가능한지는 상태 전이, 라운드 종료 뒤 누가 이겼는지는 결과 판정으로 자르면 blackjack 미션의 긴 분기가 세 덩어리로 정리된다.

## 결정 매트릭스

| 지금 코드가 답하는 질문 | 먼저 볼 개념 | 왜 그쪽이 맞는가 |
|---|---|---|
| 이 손패의 합계는 얼마고 Ace는 1인가 11인가? | 도메인 불변식 | 같은 카드 조합이면 플레이어와 딜러 모두 같은 결과가 나와야 하는 값 규칙이다. |
| 지금 이 참가자가 hit 또는 stand를 할 수 있는가? | 상태 패턴 | 허용 행동이 현재 턴 단계에 따라 달라지고, 행동 뒤 다음 단계로 전이된다. |
| 딜러는 16 이하에서 더 뽑아야 하는가? | Policy Object | 특정 상황에서 어떤 결정을 내릴지 판정하는 규칙이며, 상태 전체를 바꾸는 문제와는 다르다. |
| 라운드가 끝난 뒤 승자 문구를 어떻게 정할까? | Policy Object | `bust`, `push`, `blackjack` 비교는 결과 규칙 해석이다. |
| boolean 몇 개를 조합해 `isFinished`, `dealerTurn`을 계산하고 있나? | 상태 패턴 | 현재 단계가 핵심 정보라는 신호다. |

## 흔한 오선택

Ace 계산을 상태 패턴으로 빼는 경우:
Ace를 1로 내릴지 11로 둘지는 "현재 단계"보다 손패 조합이 만든 값 규칙이다. `Hand`나 점수 계산 객체가 끝까지 보장해야 하고, 플레이어 턴인지 딜러 턴인지와는 분리하는 편이 맞다.

dealer의 추가 draw 규칙을 상태 패턴 하나로 다 삼키는 경우:
딜러 차례라는 상태와, 그 상태에서 "16 이하면 한 장 더"라는 판정 규칙은 다른 층위다. 상태가 행동 가능 구간을 열고, 정책 객체가 그 안의 의사결정을 맡는 식으로 나누면 읽기 쉬워진다.

최종 승패 비교까지 도메인 불변식으로 부르는 경우:
불변식은 손패가 항상 스스로 지켜야 하는 규칙에 가깝다. 반면 `push`, `dealer bust`, `player blackjack` 우선순위는 라운드 종료 뒤 결과를 해석하는 규칙이라 Policy Object 쪽 이름이 더 잘 맞는다.

## 다음 학습

- Ace 계산과 bust 보장을 값 규칙 관점으로 다시 보려면 [blackjack Ace 점수 계산 ↔ 도메인 불변식 브릿지](./blackjack-ace-scoring-domain-invariant-bridge.md)
- hit/stand, bust, dealer turn 전이를 단계 모델로 보려면 [blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지](../design-pattern/blackjack-turn-flow-state-pattern-bridge.md)
- dealer draw와 최종 승패 비교를 결과 규칙으로 분리하려면 [blackjack 승패 판정 ↔ Policy Object 브릿지](../design-pattern/blackjack-winner-decision-policy-object-bridge.md)
- 입력 문자열 분기와 실행 요청 모델링까지 함께 헷갈리면 [blackjack 행동 선택 입력 ↔ Command 패턴 브릿지](../design-pattern/blackjack-action-input-command-bridge.md)
