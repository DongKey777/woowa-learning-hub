---
schema_version: 3
title: Blackjack Winner Policy Object Drill
concept_id: design-pattern/blackjack-winner-policy-object-drill
canonical: false
category: design-pattern
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/blackjack
review_feedback_tags:
- blackjack
- winner-policy
- result-rule
- policy-object
aliases:
- blackjack winner policy drill
- 블랙잭 승패 판정 policy 드릴
- dealer bust player bust push policy
- blackjack result decision exercise
- winner decision object practice
symptoms:
- dealer bust, player bust, push, blackjack 우선순위가 service if 문에 길게 붙어 있다
- 승패 판정 테스트를 하려면 전체 round 진행을 끝까지 재현해야 한다
- Policy Object와 Strategy 이름을 어디에 붙일지 헷갈린다
intents:
- drill
- design
- troubleshooting
prerequisites:
- design-pattern/blackjack-winner-decision-policy-object-bridge
- design-pattern/policy-object-pattern
next_docs:
- design-pattern/policy-object-vs-strategy-map-beginner-bridge
- software-engineering/blackjack-testability-cause-router
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
linked_paths:
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
- contents/design-pattern/policy-object-pattern.md
- contents/design-pattern/policy-object-vs-strategy-map-beginner-bridge.md
- contents/software-engineering/blackjack-testability-cause-router.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
confusable_with:
- design-pattern/blackjack-winner-decision-policy-object-bridge
- design-pattern/policy-object-vs-strategy-map-beginner-bridge
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
forbidden_neighbors:
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
expected_queries:
- blackjack 승패 판정을 policy object로 나누는 문제를 풀고 싶어
- dealer bust player bust push 우선순위를 어디에 둬야 해?
- 승패 판정 테스트가 전체 라운드에 묶이는 문제를 어떻게 분리해?
- 블랙잭 result decision을 service if에서 빼는 드릴을 줘
contextual_chunk_prefix: |
  이 문서는 blackjack winner policy object drill이다. dealer bust,
  player bust, push, blackjack natural, winner decision priority, service
  if chain, result test setup bloat 같은 미션 리뷰 문장을 policy object
  판별 문제로 매핑한다.
---
# Blackjack Winner Policy Object Drill

> 한 줄 요약: 승패 판정은 라운드 절차가 끝난 뒤 결과를 해석하는 규칙이므로, 전체 게임 흐름과 분리해 테스트할 수 있어야 한다.

**난이도: Beginner**

## 문제 1

상황:

```text
GameService.finishRound()에 player bust, dealer bust, push, blackjack 분기가 모두 붙어 있다.
```

답:

승패 policy 추출 후보가 맞다. 라운드 진행과 결과 판정 우선순위가 같은 메서드에 붙으면 테스트 준비가 커진다.

## 문제 2

상황:

```text
WinnerPolicy.decide(playerHand, dealerHand)가 Result를 반환한다.
```

답:

좋은 경계다. 손패만 주고 승패 결과를 검증할 수 있으므로 전체 hit/stand 흐름을 재현하지 않아도 된다.

## 문제 3

상황:

```text
dealer가 16 이하에서 카드를 더 뽑을지 결정하는 객체를 WinnerPolicy라고 이름 붙였다.
```

답:

이름이 어긋난다. 딜러 draw 여부는 진행 정책이고, winner policy는 최종 손패를 비교해 결과를 정하는 규칙이다.

## 빠른 체크

| 질문 | 더 가까운 위치 |
|---|---|
| 누가 이겼는가 | winner policy |
| 아직 딜러가 더 뽑아야 하는가 | dealer draw policy |
| 라운드가 끝났는가 | turn state |
| Ace 점수는 몇인가 | score invariant |
