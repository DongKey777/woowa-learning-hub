---
schema_version: 3
title: 'blackjack 웹 전환 후 게임 상태 혼선 원인 라우터'
concept_id: spring/blackjack-web-state-mixing-cause-router
canonical: false
category: spring
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/blackjack
- missions/baseball
review_feedback_tags:
- singleton-state-leak
- request-vs-session-scope
- game-state-storage
aliases:
- blackjack 웹 상태 혼선
- 블랙잭 게임 상태 섞임
- 블랙잭 singleton 서비스 상태
- blackjack controller 필드 game
- 블랙잭 웹 상태 저장 위치
symptoms:
- blackjack을 웹으로 옮겼더니 다른 요청의 카드 상태가 같이 보여요
- 새 게임을 시작했는데 이전 라운드 점수나 덱이 남아 있어요
- controller나 service 필드에 Game을 넣었더니 탭을 두 개 열면 진행이 헷갈려요
- 요청마다 게임 상태가 사라지거나 반대로 사용자끼리 섞여요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- spring/bean-lifecycle-basics
- spring/spring-mvc-request-lifecycle-basics
next_docs:
- spring/baseball-game-state-singleton-bean-scope-bridge
- spring/bean-lifecycle-basics
- spring/request-scope-proxy-pitfalls
- spring/spring-mvc-request-lifecycle-basics
linked_paths:
- contents/spring/baseball-game-state-singleton-bean-scope-bridge.md
- contents/spring/spring-bean-lifecycle-basics.md
- contents/spring/spring-bean-lifecycle-scope-traps.md
- contents/spring/spring-request-scope-proxy-pitfalls.md
- contents/spring/spring-mvc-request-lifecycle-basics.md
confusable_with:
- spring/baseball-game-state-singleton-bean-scope-bridge
- spring/request-scope-proxy-pitfalls
- spring/bean-lifecycle-basics
forbidden_neighbors: []
expected_queries:
- 블랙잭 콘솔 코드를 스프링으로 옮겼더니 게임 진행 상태가 왜 사용자끼리 섞여?
- 현재 게임을 service 멤버 변수로 들고 있으면 뭐가 문제야?
- 블랙잭 웹 버전에서 요청이 바뀔 때마다 덱이 초기화되거나 남아 있는 이유를 어디서 봐야 해?
- controller 필드에 Game을 넣었는데 탭 두 개에서 테스트하면 꼬이는 이유가 뭐야?
- request scope, session, DB 중 어디에 블랙잭 게임 상태를 둬야 할지 헷갈릴 때 먼저 뭘 구분해?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 웹 요청 모델로 옮길 때 게임 상태가
  요청마다 사라지거나 사용자끼리 섞이는 증상을 singleton Bean 상태 공유,
  request/session scope 오해, 외부 상태 저장소 부재로 나누는 symptom_router다.
  controller field에 Game 저장, service 멤버 변수 상태, 탭 두 개에서 게임 꼬임,
  request마다 덱 초기화, 웹 상태 저장 위치 같은 학습자 표현을 원인별로
  연결한다.
---
# blackjack 웹 전환 후 게임 상태 혼선 원인 라우터

## 한 줄 요약

> blackjack을 콘솔에서 웹으로 옮긴 뒤 상태가 꼬이는 장면은 대개 "Spring이 이상하다"보다 게임 상태의 수명을 요청, 사용자, Bean 범위 중 어디에 두는지 아직 못 자른 상태다.

## 가능한 원인

1. **singleton Bean 필드에 현재 게임을 보관하고 있다.** `@Service`나 `@RestController`는 기본적으로 singleton이라 `currentGame`, `deck`, `dealer` 같은 가변 필드를 두면 요청과 사용자가 같은 객체를 함께 만진다. 이 갈래는 [baseball 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지](./baseball-game-state-singleton-bean-scope-bridge.md)로 이어서 "웹에서는 왜 Game 하나를 오래 쥐면 안 되는가"를 먼저 본다.
2. **request scope와 session 성격을 섞어 생각하고 있다.** 한 번의 HTTP 요청 안에서만 필요한 값을 request처럼 두면 다음 요청에서 사라지는 게 맞고, 반대로 여러 요청에 걸친 게임 진행 상태를 request에 기대하면 새로고침 때마다 초기화된다. 이 경우는 [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)로 가서 request 수명과 proxy 경계를 먼저 정리한다.
3. **사용자별 상태 저장소가 아직 없다.** 콘솔에서는 프로세스 안의 `Game` 객체 하나가 진실 원천이었지만, 웹에서는 `gameId`나 세션 키 같은 식별자 없이 상태를 이어 붙일 수 없다. 저장 위치를 명시하지 않은 채 Bean 메모리에 기대면 "사라지거나 섞이는" 두 증상이 번갈아 나타난다.
4. **요청 생명주기와 도메인 생명주기를 같은 것으로 보고 있다.** `POST /games`와 `POST /games/{id}/hits`는 서로 다른 요청이므로, 첫 요청에서 만든 객체 참조를 두 번째 요청에서 당연히 들고 있을 거라고 기대하면 모델이 틀어진다. 이 갈래는 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)로 가서 요청 단위 모델을 다시 잡는 편이 빠르다.

## 빠른 자기 진단

1. `controller`나 `service` 필드에 `Game`, `Deck`, `Dealer` 같은 가변 객체가 있으면 singleton 상태 공유를 먼저 의심한다.
2. 새로고침이나 두 번째 API 호출에서 상태가 사라지면 request 수명으로 둔 값을 여러 요청에 걸쳐 기대하고 있지 않은지 본다.
3. 브라우저 탭 두 개나 다른 사용자 테스트에서 상태가 서로 섞이면 사용자별 저장 키 없이 전역 객체를 공유하고 있을 가능성이 크다.
4. `gameId`나 세션 식별자 없이 "방금 만든 게임"을 계속 찾으려 한다면 저장소 설계보다 객체 참조를 오래 붙드는 구조일 수 있다.

## 다음 학습

- singleton Bean 필드가 왜 요청 간 오염을 만드는지 미션 맥락으로 다시 보려면 [baseball 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지](./baseball-game-state-singleton-bean-scope-bridge.md)를 본다.
- Bean 수명과 scope 큰 그림을 먼저 다시 잡으려면 [Spring Bean 생명주기 기초](./spring-bean-lifecycle-basics.md)로 간다.
- request scope를 써도 되는 장면과 proxy 함정을 분리하려면 [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)를 잇는다.
- 요청이 끊길 때 객체 수명도 함께 끊긴다는 점을 다시 확인하려면 [Spring MVC 요청 생명주기 기초](./spring-mvc-request-lifecycle-basics.md)를 읽는다.
