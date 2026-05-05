---
schema_version: 3
title: 'blackjack 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나'
concept_id: spring/blackjack-mvc-controller-binding-validation-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
- missions/baseball
review_feedback_tags:
- request-binding
- bean-validation
- console-to-http
aliases:
- blackjack Spring MVC binding
- 블랙잭 RequestBody 검증
- blackjack controller dto validation
- 블랙잭 hit stand 요청 바인딩
- 블랙잭 HTTP 입력 검증
symptoms:
- 콘솔 블랙잭의 hit stand 입력을 Spring controller에서 어떻게 받아야 할지 모르겠어요
- RequestBody DTO에서 막을 것과 Game이 직접 막아야 할 규칙이 섞여 보여요
- hit 요청이 400으로 끝나는 문제와 이미 종료된 게임에 hit한 문제를 같은 검증으로 보고 있어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/mvc-controller-basics
- spring/modelattribute-vs-requestbody-binding-primer
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
next_docs:
- spring/requestbody-400-before-controller-primer
- spring/spring-bindingresult-local-validation-400-primer
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
linked_paths:
- contents/spring/spring-mvc-controller-basics.md
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/spring/spring-bindingresult-local-validation-400-primer.md
- contents/spring/spring-requestbody-400-before-controller-primer.md
- contents/software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md
- contents/spring/baseball-mvc-controller-binding-bridge.md
confusable_with:
- spring/baseball-mvc-controller-binding-bridge
- spring/modelattribute-vs-requestbody-binding-primer
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
forbidden_neighbors: []
expected_queries:
- 블랙잭 미션을 스프링으로 옮기면 hit stand 요청은 컨트롤러에서 어떤 DTO로 받아야 해?
- blackjack에서 RequestBody 검증과 게임 규칙 검증을 어디서 나눠야 해?
- 블랙잭 API에서 400으로 끝나는 입력 오류와 이미 종료된 게임 액션 오류는 왜 다르게 봐야 해?
- 콘솔 블랙잭의 scanner 입력 검증을 Spring MVC에서는 어떤 계층으로 옮기면 돼?
- 블랙잭 미션 리뷰에서 controller는 형식만 보고 Game이 규칙을 지키게 하라는 말이 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 콘솔 입력 모델에서 Spring MVC 요청 모델로
  옮길 때 hit, stand, 새 게임 시작 요청을 어떤 DTO로 받고 어디까지 형식
  검증할지 설명하는 mission_bridge다. RequestBody DTO, PathVariable gameId,
  hit 요청 400, 잘못된 action 문자열, 이미 끝난 게임에 다시 hit, controller는
  형식만 보고 Game이 규칙을 지켜야 함 같은 학습자 표현을 HTTP 바인딩과
  도메인 불변식 경계로 연결한다.
---

# blackjack 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나

## 한 줄 요약

> 콘솔 blackjack의 `Scanner` 입력은 Spring MVC에서 `@RequestBody` DTO와 `@PathVariable`로 갈라지고, 컨트롤러는 입력 형식만 걸러 준다. `이미 stand 한 게임에 다시 hit 금지` 같은 규칙은 DTO가 아니라 `Game`과 서비스 흐름이 끝까지 지켜야 한다.

## 미션 시나리오

콘솔 blackjack에서는 `"hit"`나 `"stand"` 문자열을 읽고 바로 메서드를 호출해도
흐름이 이어진다. 하지만 웹으로 옮기면 `POST /games`, `POST /games/{id}/actions`
같은 요청이 되고, 이제는 "어떤 action을 보냈는가"와 "어느 게임에 보냈는가"를
HTTP 입력으로 먼저 분리해야 한다.

이때 자주 보이는 초기 구조는 controller가 요청 body 문자열을 직접 비교하면서
`if ("hit".equals(action))` 분기와 게임 종료 여부 판단까지 한 번에 처리하는
형태다. 그러면 잘못된 JSON, 빈 action, 존재하지 않는 gameId, 이미 끝난 게임에
다시 hit한 상황이 모두 비슷한 `예외 한 덩어리`로 뭉친다. 리뷰에서 "컨트롤러는
입력 형식만, 게임 규칙은 도메인이"라는 말이 나오는 이유가 여기다.

## CS concept 매핑

여기서 닿는 개념은 HTTP 바인딩 경계와 도메인 불변식 경계다. 예를 들어
`@PathVariable Long gameId`는 "어느 게임인가"를 받고, `@RequestBody ActionRequest`
는 `"hit"` 같은 입력 형식을 DTO로 읽는다. 이 층에서는 `action`이 비었는지,
JSON 구조가 맞는지 같은 문 앞 검증만 처리한다.

반대로 `이미 bust된 플레이어는 더 못 뽑는다`, `dealer 차례에는 player hit가
불가하다`, `존재하지 않는 gameId`는 현재 게임 상태를 알아야 판단된다. 이런
규칙까지 DTO 어노테이션으로 막으려 하면 request binding과 게임 규칙이 섞인다.
짧게 말해 controller는 "HTTP를 메서드 호출로 바꾸는 입구"이고, blackjack의
실제 규칙은 `Game`, `Hand`, 서비스 조합이 끝까지 지켜야 한다.

## 미션 PR 코멘트 패턴

- "`@RequestBody` DTO는 형식 검증까지만 맡기고, 이미 종료된 게임 액션 금지는 도메인에서 설명되게 하세요."
- "`gameId`가 path에 있는데 controller가 현재 게임 객체를 필드에서 꺼내 쓰면 HTTP 경계가 흐려집니다."
- "`400 잘못된 요청`과 `게임 상태상 불가능한 행동`을 같은 예외로 다루면 API 의미가 약해집니다."
- "콘솔의 문자열 파싱 코드를 controller로 옮기는 데서 멈추지 말고, 입력 해석과 규칙 적용 책임을 분리해 보세요."

## 다음 학습

- JSON body가 controller 전에 왜 `400`으로 끊기는지 먼저 가르려면 [Spring `@RequestBody`가 컨트롤러 전에 `400` 나는 이유](./spring-requestbody-400-before-controller-primer.md)를 본다.
- `@RequestBody`와 `@ModelAttribute`를 언제 가를지 아직 헷갈리면 [Spring `@ModelAttribute` vs `@RequestBody` 초급 비교 카드](./spring-modelattribute-vs-requestbody-binding-primer.md)로 간다.
- 형식 검증과 도메인 규칙 검증을 더 일반화해서 보려면 [Validation Boundary Mini Bridge](../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)를 잇는다.
- baseball 미션의 같은 이동을 비교해 보고 싶다면 [baseball 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나](./baseball-mvc-controller-binding-bridge.md)를 함께 읽는다.
