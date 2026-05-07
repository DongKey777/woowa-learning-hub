---
schema_version: 3
title: Blackjack Ace Score Invariant Drill
concept_id: software-engineering/blackjack-ace-score-invariant-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/blackjack
review_feedback_tags:
- blackjack
- ace-score-invariant
- domain-invariant
- review-drill
aliases:
- blackjack ace score drill
- 블랙잭 에이스 점수 드릴
- Ace 1 or 11 invariant drill
- blackjack Hand score practice
- bust rule invariant exercise
symptoms:
- Ace를 1로 볼지 11로 볼지 분기가 여러 클래스에 흩어져 있다
- bust 판정과 score 계산이 서로 다른 경로를 타서 테스트가 흔들린다
- 리뷰에서 점수 규칙을 값으로 닫으라는 말을 받았지만 예제로 연습하고 싶다
intents:
- drill
- troubleshooting
- design
prerequisites:
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
next_docs:
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- software-engineering/dto-vo-entity-basics
- software-engineering/domain-invariants-as-contracts
linked_paths:
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md
- contents/software-engineering/dto-vo-entity-basics.md
- contents/software-engineering/domain-invariants-as-contracts.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/software-engineering/blackjack-testability-cause-router.md
confusable_with:
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
forbidden_neighbors:
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
expected_queries:
- blackjack Ace 점수 계산을 도메인 불변식 문제로 연습하고 싶어
- A가 여러 장일 때 score와 bust 판정을 어디에 둬야 하는지 드릴로 풀어줘
- 블랙잭 점수 규칙이 서비스와 출력에 흩어진 코드를 어떻게 판단해?
- Hand나 Score 값 객체로 Ace 규칙을 닫는 연습 문제를 줘
contextual_chunk_prefix: |
  이 문서는 blackjack Ace score invariant drill이다. Ace 1 or 11, Hand
  score, bust rule, blackjack 여부, score calculation scattered in service
  and view 같은 리뷰 문장을 도메인 불변식 판별 문제로 매핑한다.
---
# Blackjack Ace Score Invariant Drill

> 한 줄 요약: Ace 점수는 출력 편의가 아니라 손패가 항상 같은 진실을 말하게 하는 도메인 규칙이다.

**난이도: Beginner**

## 문제 1

상황:

```text
OutputView가 A, 7을 출력할 때만 Ace를 11로 계산하고, Service는 A를 항상 1로 계산한다.
```

답:

규칙이 샌다. 같은 손패가 화면과 service에서 다른 점수를 말하므로 `Hand`나 `Score`가 단일 계산 규칙을 가져야 한다.

## 문제 2

상황:

```text
Hand가 cards만 들고 있고, bust 여부는 GameService가 매번 sum(cards)로 다시 계산한다.
```

답:

처음엔 가능하지만 불변식이 약하다. `isBust()`가 손패 점수 규칙에서 바로 나오도록 두면 service는 흐름만 조합하고 점수 진실은 Hand 쪽에 남는다.

## 문제 3

상황:

```text
A, A, 9를 21로 처리하는 테스트가 없다.
```

답:

Ace 규칙의 핵심 반례가 비어 있다. 여러 Ace 중 일부를 1로 낮춰야 하는 케이스를 점수 객체 단위 테스트로 먼저 잠그는 편이 안전하다.

## 빠른 체크

| 질문 | 판단 |
|---|---|
| 같은 손패가 어디서나 같은 score를 말하는가 | invariant OK |
| bust가 저장된 boolean과 score 계산이 따로 움직이는가 | leakage 후보 |
| Ace 여러 장 테스트가 있는가 | boundary coverage |
| 출력 포맷 때문에 score 계산이 바뀌는가 | view leakage |
