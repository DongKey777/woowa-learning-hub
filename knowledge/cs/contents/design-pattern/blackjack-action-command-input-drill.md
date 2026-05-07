---
schema_version: 3
title: Blackjack Action Command Input Drill
concept_id: design-pattern/blackjack-action-command-input-drill
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
- command-pattern
- input-boundary
- action-routing
aliases:
- blackjack command input drill
- 블랙잭 hit stand command 드릴
- blackjack action input parsing drill
- input view command boundary exercise
- H S 입력 커맨드 패턴 연습
symptoms:
- H, S 같은 입력 문자열 해석과 도메인 실행이 같은 if 문에 붙어 있다
- 입력 값이 늘 때마다 service 분기가 같이 커진다
- Command 패턴을 쓰라는 리뷰를 받았지만 단순 입력 분리와 헷갈린다
intents:
- drill
- design
- troubleshooting
prerequisites:
- design-pattern/blackjack-action-input-command-bridge
- design-pattern/command-pattern-basics
next_docs:
- design-pattern/command-vs-strategy-quick-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- software-engineering/blackjack-testability-cause-router
linked_paths:
- contents/design-pattern/blackjack-action-input-command-bridge.md
- contents/design-pattern/command-pattern-basics.md
- contents/design-pattern/command-vs-strategy-quick-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/software-engineering/blackjack-testability-cause-router.md
- contents/software-engineering/controller-service-domain-responsibility-split-drill.md
confusable_with:
- design-pattern/blackjack-action-input-command-bridge
- design-pattern/command-vs-strategy-quick-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
forbidden_neighbors:
- contents/design-pattern/strategy-pattern.md
expected_queries:
- blackjack H S 입력을 command로 나누는 문제를 풀고 싶어
- 입력 파싱과 hit stand 실행을 어디서 끊어야 하는지 드릴로 설명해줘
- Command 패턴과 단순 if 분리 차이를 blackjack 예제로 연습해줘
- 블랙잭 action routing 테스트를 Spring 없이 어떻게 볼지 알려줘
contextual_chunk_prefix: |
  이 문서는 blackjack action command input drill이다. H/S input parsing,
  hit stand command, input view boundary, service if growth, command vs
  strategy confusion 같은 미션 리뷰 문장을 command input 판별 문제로
  매핑한다.
---
# Blackjack Action Command Input Drill

> 한 줄 요약: 입력 문자열을 해석하는 일과 게임 행동을 실행하는 일은 같은 `if` 안에 붙어 있을 필요가 없다.

**난이도: Beginner**

## 문제 1

상황:

```text
GameService.play(String input)가 "H"이면 hit, "S"이면 stand를 직접 분기한다.
```

답:

입력 해석과 도메인 실행이 붙어 있다. `InputView`나 adapter가 문자열을 action으로 바꾸고, service는 action command나 유스케이스 메서드를 받는 구조가 더 테스트하기 쉽다.

## 문제 2

상황:

```text
HitCommand.execute(game), StandCommand.execute(game)가 있고 입력 parser는 command를 고른다.
```

답:

Command 후보가 맞다. 입력 선택이 실행 객체로 바뀌면 새 행동 추가와 테스트 경계가 명확해진다.

## 문제 3

상황:

```text
DealerDrawStrategy가 16 이하에서 draw할지 결정한다.
```

답:

이건 Command보다 Strategy/Policy에 가깝다. 외부 입력 행동을 캡슐화하는지, 선택 규칙을 바꾸는지로 구분한다.

## 빠른 체크

| 질문 | 더 가까운 선택 |
|---|---|
| 사용자가 선택한 행동을 실행 객체로 만든다 | Command |
| 딜러가 어떤 기준으로 뽑을지 바꾼다 | Strategy / Policy |
| 지금 행동이 가능한지 막는다 | State |
| 문자열을 domain action으로 번역한다 | input adapter |
