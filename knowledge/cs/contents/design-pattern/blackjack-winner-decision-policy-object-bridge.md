---
schema_version: 3
title: 'blackjack 승패 판정 ↔ Policy Object 브릿지'
concept_id: design-pattern/blackjack-winner-decision-policy-object-bridge
canonical: false
category: design-pattern
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
review_feedback_tags:
- winner-decision-boundary
- dealer-draw-policy
- if-else-rule-sprawl
aliases:
- blackjack 승패 판정 객체
- 블랙잭 승자 결정 정책
- blackjack 딜러 16 규칙 분리
- 블랙잭 결과 판정 if 문
- Dealer draw rule policy
symptoms:
- 승패 비교 if 문이 RoundService에 계속 늘어나요
- 딜러는 16 이하 hit 규칙과 승패 판정이 한 메서드에 섞여요
- blackjack push 규칙을 어디서 판단해야 할지 모르겠어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- design-pattern/policy-object-pattern
- design-pattern/strategy-vs-state-vs-policy-object
next_docs:
- design-pattern/policy-object-pattern
- design-pattern/strategy-vs-state-vs-policy-object
- design-pattern/blackjack-turn-flow-state-pattern-bridge
linked_paths:
- contents/design-pattern/policy-object-pattern.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
confusable_with:
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
forbidden_neighbors:
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
expected_queries:
- 블랙잭 미션에서 승패 판정을 service if 문으로 두지 말라는 리뷰는 무슨 뜻이야?
- dealer는 16 이하면 한 장 더 뽑는 규칙을 객체로 빼라는 말이 왜 나와?
- blackjack에서 push 승부 규칙은 상태 패턴이 아니라 뭐로 보는 게 좋아?
- 플레이어 점수 비교와 딜러 draw 조건을 한곳에서 설명하려면 어떤 모델이 맞아?
- 블랙잭 결과 판정 로직이 커질 때 policy object를 떠올리는 기준이 뭐야?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 dealer의 추가 draw 규칙과 최종 승패 판정이
  service if 문에 함께 뭉칠 때, 이를 Policy Object로 분리해 읽는 mission_bridge다.
  딜러 16 규칙, push 판정, 승자 결정, 결과 비교 로직, rule object 같은 학습자
  표현을 상태 전이와 값 계산이 아닌 판정 규칙 경계로 연결한다.
---

# blackjack 승패 판정 ↔ Policy Object 브릿지

## 한 줄 요약

> blackjack 미션에서 `hit/stand` 흐름은 상태 전이 문제지만, "딜러가 한 장 더 뽑아야 하는가"와 "최종 승자가 누구인가"는 규칙 판정 문제다. 이 규칙이 `RoundService`의 긴 `if` 문으로 커지면 Policy Object로 끌어올리는 편이 읽기 쉽다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "승패 비교 if문이 `RoundService`에 계속 늘어나요" | bust, blackjack, push, dealer score 비교가 한 서비스 메서드에 이어지는 코드 | 현재 손패를 해석하는 판정 규칙을 Policy Object로 드러낸다 |
| "딜러 16 이하 hit 규칙과 최종 승패가 한 메서드에 섞여요" | dealer draw 조건과 winner decision이 같은 절차 흐름에 묻힌 구조 | 진행 단계 전이, 점수 계산, 결과 판정을 다른 책임으로 나눈다 |
| "push 규칙은 상태 패턴으로 빼야 하나요?" | 동점/무승부 판정을 턴 상태와 같은 축으로 모델링하려는 상황 | 상태 전이가 아니라 결과 해석 규칙이면 policy 쪽 질문으로 본다 |

## 미션 시나리오

blackjack을 구현하다 보면 라운드 끝부분이 특히 빠르게 복잡해진다. 플레이어들이 모두 멈춘 뒤 딜러는 `16 이하이면 hit`를 반복해야 하고, 마지막에는 `bust`, `blackjack`, 동점, 일반 승패를 한 번에 비교해야 한다.

초기 구현은 흔히 `if (dealer.score() <= 16) ...` 다음에 `if (player.isBust()) ... else if ...`를 길게 잇는 형태가 된다. 그러면 점수 계산 책임, 턴 흐름 책임, 승패 규칙 책임이 같은 메서드에 섞인다. 리뷰에서 "결과 판정 규칙을 객체로 빼 보세요", "딜러 규칙이 서비스 절차에 묻혀 있어요" 같은 코멘트가 나오는 이유가 여기다.

## CS concept 매핑

이 장면은 strategy보다 Policy Object에 더 가깝다. 지금 필요한 것은 여러 실행 방법 중 하나를 고르는 일이 아니라, 현재 손패 상태를 보고 "계속 뽑는가", "누가 이겼는가", "무승부인가"를 판정하는 규칙 묶음이기 때문이다.

예를 들어 `DealerDrawPolicy.shouldHit(dealerScore)`와 `WinnerPolicy.decide(playerHand, dealerHand)`처럼 두면 규칙의 이름이 먼저 드러난다. 짧은 코드로는 `return dealer.score() <= 16;` 정도면 충분하다. 핵심은 규칙을 서비스 절차 안에 숨기지 않고, 테스트 가능한 판정 객체로 세우는 데 있다.

이 문서는 상태 패턴 문서와도 역할이 다르다. `PlayerTurn -> DealerTurn -> RoundFinished`처럼 단계가 바뀌는 문제는 상태 전이이고, Ace를 1 또는 11로 읽는 문제는 값 계산이다. 반면 "현재 결과를 어떤 기준으로 해석할까"는 판정 규칙이므로 Policy Object 쪽 질문이다.

## 미션 PR 코멘트 패턴

- "`dealer는 왜 16에서 멈추고 15에서만 더 뽑는지`가 서비스 흐름을 따라가야 보이면 규칙이 숨어 있다는 뜻입니다."
- "`push`, `blackjack`, `bust` 비교가 긴 if-else로 이어지면 결과 규칙을 객체 이름으로 드러내 보세요."라는 코멘트는 Policy Object 분리를 뜻한다.
- "`점수 계산은 Hand가, 승패 해석은 다른 객체가 맡는 편이 역할이 선명합니다.`"라는 피드백은 값 계산과 규칙 판정을 가르라는 말이다.
- "`상태 패턴을 이미 썼더라도 승패 규칙까지 상태 객체에 몰아넣을 필요는 없습니다.`"라는 코멘트는 전이와 판정을 분리하라는 뜻이다.

## 다음 학습

- Policy Object 자체를 더 일반화해서 보려면 [Policy Object Pattern](./policy-object-pattern.md)을 읽는다.
- state, strategy, policy object 경계를 한 번에 비교하려면 [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)로 간다.
- blackjack에서 `hit/stand` 단계 전이가 더 헷갈리면 [blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지](./blackjack-turn-flow-state-pattern-bridge.md)를 이어서 본다.
- Ace 점수 계산과 bust 판정 책임을 분리해서 보려면 [blackjack Ace 점수 계산 ↔ 도메인 불변식 브릿지](../software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md)를 본다.
