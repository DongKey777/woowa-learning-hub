---
schema_version: 3
title: Blackjack Testability Boundary Drill
concept_id: software-engineering/blackjack-testability-boundary-drill
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
- testability-boundary
- first-failing-test
- responsibility-split
aliases:
- blackjack testability drill
- 블랙잭 테스트 경계 드릴
- blackjack first failing test practice
- score turn result test split
- blackjack test setup bloat drill
symptoms:
- blackjack 테스트 하나를 추가하면 점수, 입력, 턴, 결과 준비 코드가 모두 따라온다
- first failing test를 점수 규칙, 턴 흐름, 승패 판정 중 어디에 둘지 헷갈린다
- 리뷰에서 테스트하기 어려운 구조라고 했지만 어떤 책임부터 분리할지 모르겠다
intents:
- drill
- troubleshooting
- design
prerequisites:
- software-engineering/blackjack-testability-cause-router
- software-engineering/test-strategy-basics
next_docs:
- software-engineering/blackjack-ace-score-invariant-drill
- design-pattern/blackjack-turn-state-transition-drill
- design-pattern/blackjack-winner-policy-object-drill
linked_paths:
- contents/software-engineering/blackjack-testability-cause-router.md
- contents/software-engineering/test-strategy-basics.md
- contents/software-engineering/blackjack-ace-score-invariant-drill.md
- contents/design-pattern/blackjack-turn-state-transition-drill.md
- contents/design-pattern/blackjack-winner-policy-object-drill.md
- contents/design-pattern/blackjack-action-command-input-drill.md
confusable_with:
- software-engineering/blackjack-testability-cause-router
- software-engineering/mission-test-slice-selection-drill
- software-engineering/controller-service-domain-responsibility-split-drill
forbidden_neighbors:
- contents/software-engineering/mission-test-slice-selection-drill.md
expected_queries:
- blackjack 테스트가 너무 많은 준비를 요구할 때 어디부터 쪼개?
- 점수 규칙 턴 흐름 승패 판정 테스트를 어떻게 나눠?
- 블랙잭 first failing test 선택을 문제로 연습하고 싶어
- 테스트하기 어려운 blackjack 구조를 책임 경계별로 드릴해줘
contextual_chunk_prefix: |
  이 문서는 blackjack testability boundary drill이다. score rule,
  turn flow, input command, winner policy, first failing test, setup bloat,
  tests break together 같은 미션 리뷰 문장을 테스트 경계 판별 문제로
  매핑한다.
---
# Blackjack Testability Boundary Drill

> 한 줄 요약: 테스트 준비가 과하면 테스트 기술보다 책임 경계가 섞였는지 먼저 본다.

**난이도: Beginner**

## 문제 1

상황:

```text
A, A, 9 점수 테스트를 쓰려는데 GameService와 InputView까지 만들어야 한다.
```

답:

점수 규칙이 독립 테스트 가능한 경계로 닫히지 않았다. `Hand`나 `Score` 단위 테스트로 먼저 분리할 후보다.

## 문제 2

상황:

```text
hit이 가능한지 테스트하려면 dealerTurn, finished, bust boolean을 모두 맞춰야 한다.
```

답:

턴 상태가 값 조합에 숨어 있다. state transition test로 "현재 상태가 허용하는 행동"을 직접 검증하는 편이 낫다.

## 문제 3

상황:

```text
승패 판정 하나를 검증하려고 전체 라운드를 끝까지 진행해야 한다.
```

답:

winner policy가 절차에 묻혀 있다. 최종 손패 두 개만 주고 결과를 판단하는 단위 테스트가 가능해야 한다.

## 빠른 체크

| 테스트 이름 | 먼저 볼 경계 |
|---|---|
| Ace score handles multiple aces | score invariant |
| Cannot hit after stand | turn state |
| Dealer bust means player wins | winner policy |
| H input calls hit action | command input boundary |
