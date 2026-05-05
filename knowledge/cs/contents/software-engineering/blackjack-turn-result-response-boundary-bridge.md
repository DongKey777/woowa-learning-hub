---
schema_version: 3
title: 'blackjack 한 턴 결과 ↔ 결과 객체와 Response DTO 경계 브릿지'
concept_id: software-engineering/blackjack-turn-result-response-boundary-bridge
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
- turn-result-boundary
- domain-to-string-leak
- response-dto-mapping
aliases:
- blackjack 결과 객체
- 블랙잭 응답 DTO 경계
- blackjack turn result response
- 블랙잭 한 턴 결과 모델
- blackjack 도메인 문자열 반환
symptoms:
- Game.hit가 바로 카드 문자열이나 승패 문구를 만들어 반환하고 있어요
- controller가 현재 점수와 bust 여부를 다시 조립해 응답 JSON을 만들고 있어요
- stand 결과와 dealer turn 결과 문구 규칙이 여기저기 흩어져 보여요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/blackjack-turn-processing-service-layer-bridge
- software-engineering/dto-vo-entity-basics
- design-pattern/blackjack-winner-decision-policy-object-bridge
next_docs:
- software-engineering/blackjack-turn-processing-service-layer-bridge
- software-engineering/dto-vo-entity-basics
- spring/blackjack-mvc-controller-binding-validation-bridge
linked_paths:
- contents/software-engineering/blackjack-turn-processing-service-layer-bridge.md
- contents/software-engineering/dto-vo-entity-basics.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
- contents/spring/blackjack-mvc-controller-binding-validation-bridge.md
confusable_with:
- software-engineering/blackjack-turn-processing-service-layer-bridge
- software-engineering/dto-vo-entity-basics
- design-pattern/blackjack-winner-decision-policy-object-bridge
forbidden_neighbors:
- contents/software-engineering/blackjack-turn-processing-service-layer-bridge.md
- contents/software-engineering/dto-vo-entity-basics.md
expected_queries:
- 블랙잭 미션에서 Game이 바로 카드 목록 문자열이나 결과 문구를 반환하면 왜 아쉬워?
- hit stand 한 턴 결과를 Response DTO로 한 번 더 감싸라는 리뷰는 무슨 뜻이야?
- blackjack에서 bust 여부와 다음 행동 가능 여부를 어디까지 도메인 결과로 보고 어디서 JSON으로 바꿔야 해?
- 블랙잭 미션에서 controller가 점수와 승패 문구를 다시 조립하면 왜 경계가 흐려져?
- 한 턴 결과 의미와 응답 포맷을 어디서 끊어야 하는지 감이 안 와
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 hit 또는 stand 한 번의 결과를 도메인
  문자열로 바로 반환하거나 controller가 점수, bust, winner, nextAction 같은
  값을 다시 조립하는 혼선을 결과 객체와 Response DTO 경계로 정리하는
  mission_bridge다. 블랙잭 한 턴 결과 모델, 도메인 문자열 반환, 응답 JSON
  조립, 결과 의미와 표현 포맷 분리 같은 학습자 표현을 blackjack 유스케이스의
  결과 계약과 응답 변환 감각으로 연결한다.
---

# blackjack 한 턴 결과 ↔ 결과 객체와 Response DTO 경계 브릿지

## 한 줄 요약

> blackjack 한 턴의 본질은 "카드가 어떻게 바뀌었고, 지금 bust인지, 다음 행동이 가능한지, 라운드가 끝났는가"라는 결과 의미다. 그래서 도메인이 바로 화면 문구나 JSON 모양을 만들기보다, 먼저 결과 객체로 의미를 닫고 바깥에서 Response DTO로 바꾸는 편이 경계가 덜 섞인다.

## 미션 시나리오

blackjack 미션을 진행하다 보면 `Game.hit()`나 `Game.stand()`가 곧바로
`"딜러: 16, 플레이어 bust"` 같은 문자열을 반환하거나, 반대로 controller가
`game.score()`, `game.isBust()`, `game.canHit()`를 여기저기 호출해 응답 JSON을
직접 조립하는 코드가 자주 나온다. 처음에는 둘 다 빠르게 보인다.

하지만 웹 응답 형식, 테스트, 결과 화면이 붙기 시작하면 문제가 드러난다.
도메인이 문자열을 직접 만들면 한국어 문구와 응답 포맷을 알아버리고, 바깥 계층이
숫자와 상태를 다시 조립하면 "`bust면 다음 행동 불가`", "`dealer turn이면
playerAction은 null`" 같은 규칙 일부가 controller로 새어 나온다. 리뷰에서
"한 턴 결과를 먼저 타입으로 세워 보세요", "응답 모양과 게임 결과 의미를
분리하세요"라는 코멘트가 붙는 장면이 여기다.

## CS concept 매핑

여기서 닿는 개념은 `result object + response mapping`이다. 도메인 규칙이
끝난 뒤 남는 것은 화면 문구가 아니라 한 턴의 의미다. 예를 들면 `TurnResult`가
플레이어 손패, 딜러 손패 공개 여부, 현재 상태, 다음 행동 가능 여부, 최종 승패를
들고 있고, controller는 그 결과를 `ActionResponse` 같은 DTO로 변환한다.

```java
TurnResult result = blackjackService.play(gameId, action);
return ActionResponse.from(result);
```

이렇게 자르면 도메인은 "이번 요청 뒤 게임이 어떤 의미 상태가 되었는가"만
설명하고, 바깥 계층은 "이걸 JSON이나 화면 문장으로 어떻게 보여 줄까"를 맡는다.
핵심은 DTO를 하나 더 만드는 형식주의가 아니라, 결과 의미와 표현 포맷이 바뀌는
이유를 분리하는 데 있다. `bust` 여부, 딜러 차례, 종료 여부는 도메인 결과이고,
`"playerCards"`, `"dealerCards"`, `"message"` 같은 필드명은 외부 응답 계약이다.

## 미션 PR 코멘트 패턴

- "`Game`이 바로 문구를 반환하면 도메인이 출력 포맷을 알아버립니다."라는 코멘트는 결과 의미와 표현을 분리하라는 뜻이다.
- "`controller`가 `isBust`, `winner`, `canHit`를 조합해 응답을 만들고 있네요."라는 리뷰는 바깥 계층이 도메인 규칙 일부를 다시 해석하고 있다는 신호다.
- "`TurnResult` 같은 결과 타입이 있으면 `hit`와 `stand`의 공통 응답 계약을 더 안정적으로 맞출 수 있습니다."라는 피드백은 한 턴 결과를 먼저 닫으라는 뜻이다.
- "`JSON 필드나 화면 문구가 바뀌어도 게임 규칙 코드는 흔들리지 않게 해 보세요.`"라는 코멘트는 Response DTO 경계를 따로 두라는 뜻이다.

## 다음 학습

- 한 턴 실행 순서를 service가 왜 조립하는지 같이 보려면 [blackjack 한 턴 처리 흐름 ↔ Service 계층 브릿지](./blackjack-turn-processing-service-layer-bridge.md)를 본다.
- 결과 객체, DTO, 값 객체 이름이 한꺼번에 헷갈리면 [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)로 내려간다.
- 최종 승패 해석 규칙 자체를 어디까지 따로 세울지 보려면 [blackjack 승패 판정 ↔ Policy Object 브릿지](../design-pattern/blackjack-winner-decision-policy-object-bridge.md)를 이어서 읽는다.
- 웹으로 옮길 때 이 결과를 어떤 요청/응답 DTO로 노출할지 보려면 [blackjack 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나](../spring/blackjack-mvc-controller-binding-validation-bridge.md)를 함께 본다.
