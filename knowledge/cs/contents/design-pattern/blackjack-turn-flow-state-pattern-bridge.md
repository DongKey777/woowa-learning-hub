---
schema_version: 3
title: 'blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지'
concept_id: design-pattern/blackjack-turn-flow-state-pattern-bridge
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
- state-transition-modeling
- boolean-flag-smell
- dealer-turn-boundary
aliases:
- blackjack 상태 패턴
- 블랙잭 턴 분기
- hit stand 분기 설계
- 블랙잭 isFinished boolean
- dealer draw 규칙 모델링
symptoms:
- 블랙잭에서 hit/stand 분기가 서비스에 몰려요
- 플레이어 차례와 딜러 차례가 boolean 여러 개로 얽혀요
- bust나 blackjack 처리 때문에 if 문이 계속 늘어나요
intents:
- mission_bridge
- design
prerequisites:
- design-pattern/object-oriented-design-pattern-basics
- design-pattern/strategy-pattern
next_docs:
- design-pattern/strategy-vs-state-vs-policy-object
- design-pattern/state-pattern-workflow-payment
- design-pattern/state-machine-library-vs-state-pattern
linked_paths:
- contents/design-pattern/state-pattern-workflow-payment.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
- contents/design-pattern/strategy-pattern.md
- contents/design-pattern/state-machine-library-vs-state-pattern.md
confusable_with:
- design-pattern/strategy-pattern
- design-pattern/strategy-vs-state-vs-policy-object
forbidden_neighbors:
- contents/design-pattern/strategy-pattern.md
expected_queries:
- 블랙잭 미션에서 hit/stand 분기를 계속 if 문으로 두면 왜 힘들어?
- 플레이어 턴과 딜러 턴을 상태 패턴으로 나누라는 말이 무슨 뜻이야?
- bust, blackjack, stand를 enum만 두는 것과 상태 객체로 나누는 건 뭐가 달라?
- 블랙잭 미션에서 dealer가 16 이하일 때 한 장 더 뽑는 규칙은 전략이야 상태야?
- 블랙잭 리뷰에서 boolean 여러 개 대신 턴 상태를 모델링하라는데 어떻게 이해해?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 hit, stand, bust, dealer turn 분기가
  서비스 if 문으로 커질 때 턴 흐름을 상태 패턴으로 잇는 mission_bridge다.
  플레이어 차례와 딜러 차례 분리, boolean flag 얽힘, isFinished 남발,
  종료 조건 증가, dealer 16 규칙, 지금 가능한 행동이 뭐냐 같은 자연어
  paraphrase가 본 문서의 상태 전이 설명에 매핑된다.
---

# blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지

## 한 줄 요약

> blackjack 미션의 핵심은 "카드를 한 장 더 뽑을 수 있는가"가 현재 단계에 따라 달라진다는 점이다. 이 질문이 커질수록 `isFinished`, `isBust`, `dealerTurn` 같은 boolean 묶음보다 상태 전이로 모델링하는 편이 읽기 쉽다.

## 미션 시나리오

blackjack 미션을 진행하면 처음에는 `Player`와 `Dealer`가 카드를 들고 있고, 요청마다 `hit` 또는 `stand`를 처리하면 끝나 보인다. 그런데 라운드가 조금만 커져도 분기가 빠르게 늘어난다. 플레이어가 `blackjack`인지, 이미 `bust`인지, 딜러 차례로 넘어갔는지, 게임이 완전히 종료됐는지를 계속 함께 물어야 하기 때문이다.

리뷰에서 자주 나오는 지점도 여기다. "왜 서비스가 플레이어/딜러 진행 규칙을 다 알고 있나요?", "`if` 문을 따라가야만 지금 가능한 동작이 보이네요", "`dealerTurn`과 `finished`가 동시에 true일 수 있는 이유가 뭔가요?" 같은 코멘트는 단순 스타일 지적이 아니라 전이 규칙이 흩어졌다는 신호다.

특히 딜러는 `16 이하이면 한 장 더`, 플레이어는 `stand`를 선언하면 더 못 뽑기, `bust`면 즉시 종료처럼 허용 동작이 다르다. 이 차이를 "누가 어떤 메서드를 호출할 수 있는가"로 끌어올리면 blackjack의 미션 흐름이 CS의 상태 패턴 질문으로 연결된다.

## CS concept 매핑

blackjack 미션의 흐름을 상태 패턴으로 읽으면, 객체가 들고 있는 것은 단순 점수만이 아니라 "지금 어떤 단계인가"다. 예를 들어 `PlayerTurn`, `DealerTurn`, `RoundFinished` 같은 상태를 두면 현재 상태가 허용 동작을 결정한다. `PlayerTurn`에서는 `hit`와 `stand`가 가능하지만, `RoundFinished`에서는 둘 다 막혀야 한다.

여기서 중요한 건 상태 패턴이 "점수 계산 로직을 전부 클래스 수로 늘리라"는 뜻이 아니라는 점이다. `dealer는 16 이하에서 한 장 더 뽑는다` 같은 판정 규칙은 전략이나 정책 객체로 남겨 둘 수 있다. 반대로 `지금 플레이어가 더 뽑아도 되는가`, `딜러 차례로 넘어갔는가`, `이미 종료됐는가`는 현재 단계가 바뀌며 허용 행동이 달라지므로 상태 패턴 쪽에 더 가깝다.

짧게 매핑하면 이렇다. 미션의 `hit/stand` 요청은 상태 객체에 위임되는 행동이고, `blackjack`이나 `bust`는 다음 상태로의 전이 결과다. 리뷰에서 "boolean 여러 개 대신 모델을 세워 보라"는 말은 결국 전이 규칙을 서비스의 분기문에서 도메인 상태로 끌어올리라는 뜻이다.

## 미션 PR 코멘트 패턴

- "`isBust`, `isFinished`, `dealerTurn` 세 값 조합을 외우지 않으면 코드를 못 읽겠어요"라는 피드백은 상태가 값 조합에 숨어 있다는 뜻이다.
- "플레이어 차례와 딜러 차례가 같은 메서드에 섞여 있네요"라는 코멘트는 허용 동작을 상태별로 분리하라는 신호다.
- "`dealer는 왜 여기서 또 카드를 뽑나요?`라는 질문이 반복되면" 딜러 진행 규칙과 종료 전이가 흩어져 있을 가능성이 크다.
- "`enum`만 두고 서비스에서 switch 하는 구조가 계속 커진다"면 상태 이름만 만든 것이고, 전이 책임은 아직 서비스에 남아 있다.

## 다음 학습

- 상태와 전략의 경계를 더 또렷하게 보려면 [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)를 이어서 읽는다.
- 상태 전이 자체를 일반화한 설명은 [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)에서 확인한다.
- "딜러 규칙은 상태가 아니라 선택 규칙 아닌가?"가 헷갈리면 [전략 패턴](./strategy-pattern.md)과 나란히 비교해 보면 된다.
