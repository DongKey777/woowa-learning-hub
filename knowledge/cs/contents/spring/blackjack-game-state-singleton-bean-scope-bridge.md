---
schema_version: 3
title: 'blackjack 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지'
concept_id: spring/blackjack-game-state-singleton-bean-scope-bridge
canonical: false
category: spring
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
- missions/baseball
review_feedback_tags:
- singleton-state-leak
- stateless-service-boundary
- game-state-storage
aliases:
- blackjack 게임 상태 bean 저장
- 블랙잭 singleton 상태 오염
- blackjack service 필드 game 보관
- 블랙잭 요청 간 상태 유지
- 스프링 블랙잭 state 저장 위치
symptoms:
- controller 필드에 Game을 넣었더니 새 요청에서 이전 카드 상태가 남아요
- singleton service에 현재 블랙잭 게임을 저장해도 되는지 모르겠어요
- 탭 두 개로 테스트하면 블랙잭 진행 상태가 서로 섞여요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/bean-lifecycle-basics
- spring/baseball-mvc-controller-binding-bridge
next_docs:
- spring/blackjack-web-state-mixing-cause-router
- spring/bean-lifecycle-basics
- spring/baseball-game-state-singleton-bean-scope-bridge
linked_paths:
- contents/spring/blackjack-web-state-mixing-cause-router.md
- contents/spring/spring-bean-lifecycle-basics.md
- contents/spring/spring-bean-lifecycle-scope-traps.md
- contents/spring/spring-request-scope-proxy-pitfalls.md
- contents/spring/baseball-game-state-singleton-bean-scope-bridge.md
confusable_with:
- spring/blackjack-web-state-mixing-cause-router
- spring/baseball-game-state-singleton-bean-scope-bridge
- database/baseball-guess-history-current-state-transaction-bridge
forbidden_neighbors: []
expected_queries:
- 블랙잭 미션을 스프링으로 옮길 때 Game 객체를 service 멤버 변수로 두면 왜 안 돼?
- blackjack 웹 버전에서 현재 게임을 controller 필드에 저장하면 어떤 문제가 생겨?
- 콘솔 블랙잭은 객체 하나로 됐는데 웹에서는 게임 상태를 어디에 둬야 해?
- 여러 사용자가 동시에 블랙잭을 치면 상태가 섞이는 이유를 스프링 관점에서 어떻게 설명해?
- stateless service로 바꾸라는 리뷰가 블랙잭 미션에서는 정확히 무슨 뜻이야?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 웹 요청 모델로 옮길 때 콘솔의 단일 Game
  객체를 Spring controller나 service 필드에 그대로 두면 왜 상태가 섞이는지
  설명하는 mission_bridge다. singleton Bean, 요청 간 상태 공유, 사용자별
  게임 진행 상태, stateless service, gameId 기반 조회, 외부 상태 저장소
  같은 리뷰 표현을 blackjack 게임 흐름과 연결한다.
---

# blackjack 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지

## 한 줄 요약

> 콘솔 blackjack의 `Game` 객체 하나를 Spring controller나 service 필드에 그대로 보관하면, 웹에서는 그 객체가 여러 요청과 사용자 사이에 공유될 수 있다. 그래서 게임 진행 상태는 singleton Bean 안의 가변 필드보다 명시적인 저장소와 식별자로 읽는 편이 안전하다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "service 필드에 `currentGame`을 두면 새 요청에서도 이어지지 않나요?" | singleton `@Service` 안에 현재 blackjack 게임 객체를 저장한 코드 | Bean 수명과 게임 한 판의 수명이 다르다는 점을 먼저 분리한다 |
| "탭 두 개로 블랙잭을 하면 카드 상태가 섞여요" | 여러 요청이 같은 controller/service 가변 필드를 공유하는 테스트 | 요청별 상태를 Bean 필드가 아니라 식별자와 저장소로 찾게 만든다 |
| "콘솔에서는 객체 하나로 됐는데 웹에서는 왜 저장소가 필요하죠?" | 콘솔 game loop를 HTTP 요청 여러 개로 쪼개는 전환 단계 | 끊긴 요청 사이에서 같은 게임을 다시 찾는 상태 저장 경계를 잡는다 |

## 미션 시나리오

콘솔 blackjack은 한 프로세스 안에서 한 사람이 한 판을 이어서 진행하니 `Game`
객체 하나가 자연스럽다. 하지만 웹으로 옮기면 `POST /games`,
`POST /games/{id}/hit`, `POST /games/{id}/stand`처럼 요청이 끊기고, 같은 서버가
여러 사용자의 요청을 함께 받는다.

이때 자주 나오는 실수는 controller나 service에 `currentGame` 필드를 두고 새
게임 시작과 다음 행동을 그 객체 하나로 이어 붙이는 구조다. 혼자 클릭할 때는
돌아가 보이지만, 새로고침이나 탭 두 개 테스트를 하면 "방금 시작한 게임인데
이전 카드가 남아 있다", "다른 요청의 진행 상태가 섞인다" 같은 증상이 바로
드러난다.

## CS concept 매핑

여기서 닿는 개념은 `stateless singleton`과 `state store 분리`다. Spring의
일반적인 controller/service Bean은 기본적으로 singleton이라 가변 필드를 두면
요청 단위 정보가 그 한 객체로 몰린다. 그래서 Bean은 행동을 조립하는 협력자로
두고, 사용자별 게임 진행 상태는 세션 키나 DB row처럼 Bean 밖 저장소에 두는
편이 맞다.

blackjack에 대입하면 service는 "이 `gameId`의 현재 상태를 읽고 `hit` 결과를
반영하라"를 조립하고, 실제 게임 상태는 저장소에서 조회·갱신한다. 콘솔에서는
메모리 객체 하나가 진실 원천이었지만, 웹에서는 "누구의 몇 번째 게임인가"를
식별할 경계가 먼저 필요하다. 리뷰에서 "`@Service`가 게임판을 들고 있으면 안
된다"는 말은 Spring이 싫다는 뜻이 아니라, Bean 수명과 게임 수명이 다르다는
뜻이다.

## 미션 PR 코멘트 패턴

- "`controller/service` 필드에 현재 게임을 넣으면 singleton Bean 특성 때문에 요청 간 오염이 납니다."
- "콘솔 객체 수명과 웹 요청 수명을 같은 것으로 보면 안 됩니다. `gameId`로 상태를 찾는 구조를 먼저 세우세요."
- "서비스는 상태를 오래 보관하는 곳보다 상태 변화를 조립하는 곳에 가깝습니다."
- "탭 두 개, 사용자 두 명 시나리오를 떠올리면 Bean 필드 상태가 왜 위험한지 바로 드러납니다."

## 다음 학습

- 증상별로 무엇이 섞였는지 먼저 가르려면 [blackjack 웹 전환 후 게임 상태 혼선 원인 라우터](./blackjack-web-state-mixing-cause-router.md)를 본다.
- singleton Bean이 왜 오래 살아남는지 다시 잡으려면 [Spring Bean 생명주기 기초](./spring-bean-lifecycle-basics.md)로 간다.
- 같은 문제를 baseball 미션으로 옮겨 비교해 보려면 [baseball 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지](./baseball-game-state-singleton-bean-scope-bridge.md)를 읽는다.
- request scope를 상태 저장소로 오해하기 쉬운 지점은 [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)에서 분리한다.
