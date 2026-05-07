---
schema_version: 3
title: Blackjack Turn State Transition Drill
concept_id: design-pattern/blackjack-turn-state-transition-drill
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
- state-transition
- hit-stand
- boolean-flag-smell
aliases:
- blackjack turn state drill
- 블랙잭 hit stand 상태 전이 드릴
- PlayerTurn DealerTurn RoundFinished exercise
- isFinished dealerTurn boolean smell drill
- blackjack state pattern practice
symptoms:
- hit, stand, dealer turn, finished 조건이 boolean 여러 개로 얽혀 있다
- 지금 가능한 행동이 무엇인지 service if 문을 끝까지 읽어야 보인다
- 상태 패턴을 쓰라는 리뷰를 받았지만 enum과 상태 객체 차이가 흐리다
intents:
- drill
- design
- troubleshooting
prerequisites:
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/strategy-vs-state-vs-policy-object
next_docs:
- design-pattern/state-pattern-workflow-payment
- design-pattern/state-machine-library-vs-state-pattern
- software-engineering/blackjack-testability-cause-router
linked_paths:
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
- contents/design-pattern/state-pattern-workflow-payment.md
- contents/design-pattern/state-machine-library-vs-state-pattern.md
- contents/software-engineering/blackjack-testability-cause-router.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
confusable_with:
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/strategy-vs-state-vs-policy-object
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
forbidden_neighbors:
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
expected_queries:
- blackjack hit stand 상태 전이를 문제로 연습하고 싶어
- isFinished dealerTurn boolean이 많아졌을 때 어떻게 상태로 나눠?
- 블랙잭에서 지금 가능한 행동을 상태 패턴으로 판단하는 드릴을 줘
- enum만 두고 switch하는 구조와 상태 객체 차이를 예제로 설명해줘
contextual_chunk_prefix: |
  이 문서는 blackjack turn state transition drill이다. hit, stand,
  dealer turn, round finished, isFinished boolean, dealerTurn flag, enum
  switch smell 같은 미션 리뷰 문장을 상태 전이 판별 문제로 매핑한다.
---
# Blackjack Turn State Transition Drill

> 한 줄 요약: 턴 상태는 "지금 가능한 행동"을 결정하고, 점수 규칙은 "현재 손패의 값"을 결정한다.

**난이도: Beginner**

## 문제 1

상황:

```text
GameService.hit()가 if (finished || dealerTurn || playerBust) 세 조건을 매번 검사한다.
```

답:

상태가 boolean 조합에 숨어 있다. `PlayerTurn`, `DealerTurn`, `RoundFinished` 같은 상태가 허용 행동을 직접 말하게 만들 후보다.

## 문제 2

상황:

```text
enum RoundStatus는 있지만 모든 분기는 service switch(status) 안에 있다.
```

답:

상태 이름만 생겼고 행동은 아직 service에 남았다. 상태 객체가 `hit`, `stand`, `next` 같은 허용 동작을 나눠 가져야 상태 패턴의 이점이 생긴다.

## 문제 3

상황:

```text
dealer는 16 이하에서 자동으로 한 장 더 뽑는다.
```

답:

이 규칙은 상태와 정책을 함께 본다. "딜러 차례인가"는 상태 질문이고, "몇 점 이하에서 뽑는가"는 dealer draw policy 질문이다.

## 빠른 체크

| 신호 | 더 가까운 개념 |
|---|---|
| 지금 `hit` 가능한가 | state |
| dealer가 몇 점까지 뽑는가 | policy / strategy |
| 이미 종료됐는데 요청이 들어왔나 | state guard |
| Ace 점수는 몇 점인가 | domain invariant |
