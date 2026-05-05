---
schema_version: 3
title: 'blackjack 한 턴 처리 흐름 ↔ Service 계층 브릿지'
concept_id: software-engineering/blackjack-turn-processing-service-layer-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
review_feedback_tags:
- controller-logic-leak
- service-orchestration
- action-usecase-boundary
aliases:
- blackjack service layer
- 블랙잭 한 턴 service
- blackjack controller 로직 분리
- 블랙잭 hit stand 흐름 service
- 블랙잭 service 책임
symptoms:
- controller가 gameId 조회부터 hit 처리와 응답 조립까지 다 하고 있어요
- service가 너무 얇아 보여서 hit stand 흐름도 controller에 두고 싶어요
- 블랙잭 한 턴 요청의 순서를 어디까지 service가 가져가야 할지 헷갈려요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
- spring/blackjack-mvc-controller-binding-validation-bridge
- spring/blackjack-game-id-session-boundary-bridge
next_docs:
- spring/blackjack-mvc-controller-binding-validation-bridge
- spring/blackjack-game-id-session-boundary-bridge
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
linked_paths:
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/service-layer-basics.md
- contents/spring/blackjack-mvc-controller-binding-validation-bridge.md
- contents/spring/blackjack-game-id-session-boundary-bridge.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
confusable_with:
- software-engineering/service-layer-basics
- spring/blackjack-mvc-controller-binding-validation-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
forbidden_neighbors:
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/layered-architecture-basics.md
expected_queries:
- 블랙잭 미션에서 hit 한 번 처리하는 순서는 service가 어디까지 맡아야 해?
- controller에서 gameId로 게임 찾고 카드 뽑고 응답 만들기까지 다 하면 왜 경계가 흐려?
- blackjack에서 service가 얇아 보여도 한 턴 흐름만 모으면 되는 이유가 뭐야?
- 블랙잭 웹 미션에서 요청 DTO 검증 다음에 game 진행 순서를 어느 계층이 조립해야 해?
- hit stand 한 번의 유스케이스를 controller와 domain 사이 어디에 두면 좋을지 감이 안 와
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 한 번의 hit 또는 stand 요청을 처리할 때
  controller가 요청 해석, gameId 조회, 게임 진행, 응답 조립을 모두 쥐지 않고
  service가 유스케이스 순서를 묶어야 하는 이유를 설명하는 mission_bridge다.
  블랙잭 service가 얇아 보임, controller 로직 비대화, 한 턴 처리 순서, gameId로
  게임 찾기, hit/stand 실행 뒤 응답 조립 같은 학습자 표현을 service layer
  orchestration 관점으로 연결한다.
---

# blackjack 한 턴 처리 흐름 ↔ Service 계층 브릿지

## 한 줄 요약

> blackjack에서 한 번의 `hit` 또는 `stand` 요청은 입력 형식 검증, 게임 식별, 도메인 진행, 응답 조립이 이어지는 유스케이스다. Controller는 HTTP 입구를 맡고, 그 순서를 끝까지 묶는 자리는 Service에 더 가깝다.

## 미션 시나리오

blackjack를 웹으로 옮기면 `POST /games/{gameId}/actions` 한 번이 단순 메서드
호출이 아니라 끊어진 요청 하나가 된다. 이때 controller에서 action 문자열을
검증하고, `gameId`로 현재 게임을 찾고, `Game.hit()` 또는 `Game.stand()`를
호출한 뒤, 바뀐 손패와 종료 여부를 응답 DTO로 다시 조립하는 코드가 한 메서드에
붙기 쉽다.

처음에는 한 파일에서 다 보여서 빠르게 느껴진다. 하지만 곧 "`controller가 게임
진행 순서까지 다 알고 있네요`", "`service가 비어 있어도 유스케이스 조립은 거기에
두는 편이 낫습니다`" 같은 리뷰를 받는다. 이 코멘트는 Service에 규칙을 몰아넣으라는
뜻이 아니라, 웹 입구와 "한 턴을 끝내는 순서"를 분리하라는 뜻이다.

## CS concept 매핑

Service 계층은 복잡한 계산을 직접 해야 해서 필요한 게 아니라, 여러 책임을 한
유스케이스 순서로 묶기 위해 필요하다. blackjack 한 턴에서는 대체로 아래 흐름이
여기에 들어간다.

```java
Game game = gameRepository.get(gameId);
TurnResult result = blackjackService.play(game, action);
```

여기서 controller는 `action` 형식이 맞는지와 `gameId`를 어디서 받는지만 다룬다.
`Game`은 Ace 계산, bust 판정, 현재 단계에서 `hit`이 가능한지 같은 도메인 규칙을
지킨다. Service는 "어떤 게임을 읽고, 어떤 행동을 적용하고, 어떤 응답으로
내보낼지"를 조립한다. 그래서 Service가 얇아 보여도 괜찮다. 중요한 건 한 턴의
순서가 controller, domain, repository에 흩어지지 않는 것이다.

이 경계를 먼저 잡아야 다른 문서와도 충돌이 줄어든다. 입력 형식 검증은 controller
바인딩 문제고, `gameId` 전달은 요청 상태 모델 문제며, `dealer`가 언제 더 뽑는지는
상태나 정책 문제다. 반대로 "이번 요청 한 번을 어디서 완성할까"는 Service 계층
질문이다.

## 미션 PR 코멘트 패턴

- "`Controller`가 `gameId` 조회, 도메인 호출, 응답 조립을 모두 알고 있으면 웹 계층이 유스케이스 순서를 소유하게 됩니다."
- "`Service`가 얇아 보여도 괜찮습니다. 한 턴 실행 흐름이 한곳에 모여 있는지가 더 중요합니다."
- "`Game`은 규칙을 지키고, Service는 그 규칙 호출 순서를 조립해 주세요."라는 리뷰는 도메인 규칙과 애플리케이션 흐름을 나누라는 뜻이다.
- "`hit`와 `stand` 처리 후 공통 응답 조립이 controller마다 반복되면 유스케이스 경계가 약합니다."라는 코멘트는 orchestration 위치를 다시 보라는 신호다.

## 다음 학습

- HTTP 입력 형식과 도메인 규칙 검증을 어디서 나누는지 더 보려면 `spring/blackjack-mvc-controller-binding-validation-bridge`
- 요청마다 게임을 어떻게 식별해 이어 붙이는지 보려면 `spring/blackjack-game-id-session-boundary-bridge`
- Ace 계산과 bust 판정을 왜 도메인 규칙으로 닫아야 하는지 보려면 `software-engineering/blackjack-ace-scoring-domain-invariant-bridge`
- `hit` 가능 여부와 딜러 턴 전이를 왜 상태 문제로 읽는지 보려면 `design-pattern/blackjack-turn-flow-state-pattern-bridge`
