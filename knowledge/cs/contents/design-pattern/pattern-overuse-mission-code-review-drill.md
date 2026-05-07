---
schema_version: 3
title: '미션 코드리뷰에서 패턴 과잉 도입을 걸러내는 드릴'
concept_id: design-pattern/pattern-overuse-mission-code-review-drill
canonical: false
category: design-pattern
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 72
mission_ids:
- missions/baseball
- missions/lotto
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- pattern-overuse
- strategy-factory-command-choice
- responsibility-before-pattern
aliases:
- 패턴 과잉 도입
- mission pattern overuse drill
- strategy factory command 남용
- 리뷰에서 패턴 필요성 판단
- 디자인 패턴 먼저 쓰면 안 되는 이유
symptoms:
- 요구사항은 단순한데 Strategy, Factory, Command를 먼저 만들고 싶다
- 리뷰에서 패턴 이름은 보이지만 책임 분리가 더 나아졌는지 설명하지 못한다
- if 문 제거만 목표로 삼아 객체 수가 불필요하게 늘어난다
intents:
- drill
- design
prerequisites:
- design-pattern/object-oriented-design-pattern-basics
- design-pattern/factory-misnaming-checklist
next_docs:
- design-pattern/strategy-pattern-basics
- design-pattern/command-vs-strategy-quick-bridge
- design-pattern/bridge-strategy-vs-factory-runtime-selection
linked_paths:
- contents/design-pattern/object-oriented-design-pattern-basics.md
- contents/design-pattern/factory-misnaming-checklist.md
- contents/design-pattern/strategy-pattern-basics.md
- contents/design-pattern/command-vs-strategy-quick-bridge.md
- contents/design-pattern/bridge-strategy-vs-factory-runtime-selection.md
- contents/design-pattern/lotto-big-if-responsibility-cause-router.md
- contents/design-pattern/baseball-big-if-responsibility-cause-router.md
- contents/design-pattern/shopping-cart-checkout-pattern-decision-guide.md
confusable_with: []
forbidden_neighbors: []
confusable_with:
- design-pattern/object-oriented-design-pattern-basics
- design-pattern/factory-misnaming-checklist
- design-pattern/strategy-pattern-basics
- design-pattern/command-vs-strategy-quick-bridge
expected_queries:
- 미션 코드에서 Strategy나 Factory를 너무 일찍 쓰는지 점검하고 싶어
- if 문을 없애려고 패턴을 넣었는데 과한 설계인지 어떻게 판단해?
- 리뷰에서 패턴 이름보다 책임 분리를 설명하려면 어떤 질문을 던져야 해?
- baseball lotto roomescape 코드에서 패턴이 필요한지 드릴로 확인해줘
contextual_chunk_prefix: |
  이 문서는 우아한테크코스 미션 코드리뷰에서 Strategy, Factory, Command 같은
  디자인 패턴을 과하게 도입했는지 점검하는 design-pattern drill이다. 패턴
  이름 먼저 붙이기, if 제거 집착, 책임 분리 설명 부족, 미션 코드 과설계 같은
  질의를 코드리뷰용 판단 질문으로 연결한다.
---
# 미션 코드리뷰에서 패턴 과잉 도입을 걸러내는 드릴

> 한 줄 요약: 패턴은 "이름 붙은 해결책"이지 "먼저 붙이는 장식"이 아니다. 미션 코드에서는 패턴 이름보다 바뀌는 책임, 선택 시점, 테스트 모양이 좋아졌는지를 먼저 확인한다.

**난이도: 🟢 Beginner**

## 드릴 1. if 문이 보이면 바로 Strategy인가?

상황:

```text
로또 등수 결정에 if가 5개 있다.
```

질문:

- 분기 규칙이 자주 바뀌는가?
- 분기마다 완전히 다른 행동을 하는가?
- enum이나 table lookup으로 충분한가?
- 테스트가 더 읽기 쉬워지는가?

판단:

if가 많다는 사실만으로 Strategy가 필요한 것은 아니다. 단순 매핑은 enum, table, 정적 메서드가 더 단순할 수 있다.

## 드릴 2. 객체 생성을 감쌌다고 Factory인가?

상황:

```text
new Lotto(numbers)를 LottoFactory.create(numbers)로 감쌌다.
```

질문:

- 생성 규칙이 여러 종류인가?
- 이름이 생성 의도를 드러내는가?
- 단순 위임 wrapper만 늘어난 것은 아닌가?

판단:

생성 의도를 드러내려면 정적 팩토리로 충분할 수 있고, 객체 생성 조합이 복잡할 때 Factory가 자연스럽다.

## 드릴 3. 명령을 객체로 만들면 무조건 Command인가?

상황:

```text
게임 재시작/종료 선택을 RestartCommand, QuitCommand로 분리했다.
```

질문:

- 실행을 큐에 넣거나 undo/redo해야 하는가?
- 호출자와 실행자를 분리할 필요가 있는가?
- 단순 enum 분기보다 테스트나 확장이 나아졌는가?

판단:

단순 입력 분기라면 enum과 작은 메서드가 충분할 수 있다. Command는 실행 시점 분리나 이력 관리가 있을 때 힘이 난다.

## 리뷰 코멘트로 바꾸는 문장

```text
패턴을 썼는지보다 이 분리가 어떤 변경을 더 싸게 만들었는지 설명해보세요.
```

```text
if 제거 자체가 목표라면 객체 수만 늘 수 있습니다. 분기 기준, 변경 가능성,
테스트 모양이 나아졌는지 먼저 비교해봅시다.
```

## 한 줄 정리

미션에서 패턴 도입은 `변경 축`, `선택 시점`, `테스트 모양`을 설명할 수 있을 때만 설득력이 있다.
