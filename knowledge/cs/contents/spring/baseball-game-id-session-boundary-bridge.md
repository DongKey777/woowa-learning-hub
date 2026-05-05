---
schema_version: 3
title: 'baseball 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지'
concept_id: spring/baseball-game-id-session-boundary-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/baseball
review_feedback_tags:
- game-id-propagation
- session-state-boundary
- stateless-request-model
aliases:
- baseball gameId 전달
- 야구 미션 세션 gameId
- 게임 시작 후 식별자 유지
- baseball 요청마다 어떤 게임인지
- 스프링 야구 gameId 보관
symptoms:
- 게임을 시작한 뒤 다음 추측 요청이 어느 게임인지 연결이 안 돼요
- controller 필드 currentGame 대신 gameId를 넘기라는데 왜 필요한지 모르겠어요
- 세션에 뭘 넣고 요청 바디에는 뭘 넣어야 하는지 헷갈려요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/baseball-console-game-loop-http-request-lifecycle-bridge
- spring/baseball-game-state-singleton-bean-scope-bridge
- spring/mvc-controller-basics
next_docs:
- spring/baseball-mvc-controller-binding-bridge
- spring/baseball-game-state-singleton-bean-scope-bridge
- database/baseball-guess-history-current-state-transaction-bridge
linked_paths:
- contents/spring/baseball-console-game-loop-http-request-lifecycle-bridge.md
- contents/spring/baseball-game-state-singleton-bean-scope-bridge.md
- contents/spring/baseball-mvc-controller-binding-bridge.md
- contents/spring/spring-mvc-controller-basics.md
- contents/network/http-state-session-cache.md
- contents/database/baseball-guess-history-current-state-transaction-bridge.md
confusable_with:
- spring/baseball-console-game-loop-http-request-lifecycle-bridge
- spring/baseball-game-state-singleton-bean-scope-bridge
- spring/baseball-mvc-controller-binding-bridge
forbidden_neighbors: []
expected_queries:
- 야구 미션을 웹으로 바꾸면 gameId를 왜 응답하고 다음 요청에서 다시 보내야 해?
- baseball에서 currentGame 필드 대신 식별자를 들고 다니라는 리뷰는 무슨 뜻이야?
- 세션에 게임 전체를 넣지 말고 gameId만 두라는 이유가 뭐야?
- 게임 시작 요청 이후 추측 요청이 같은 게임이라는 걸 Spring에서 어떻게 연결해?
- 웹 야구 미션에서 요청마다 어느 게임인지 식별하는 자리를 어디에 둬야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa baseball 미션을 웹으로 옮길 때 게임 시작 후 생긴 gameId를
  다음 추측 요청까지 어떻게 이어 가야 하는지 설명하는 mission_bridge다.
  controller 필드에 currentGame을 들고 있지 말라는 리뷰, 요청은 stateless인데
  같은 게임을 어떻게 식별하나, 세션에는 무엇을 두고 request body에는 무엇을
  두나, gameId와 상태 저장소를 분리하라는 학습자 표현을 Spring 요청 경계와
  세션/식별자 모델로 연결한다.
---

# baseball 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지

## 한 줄 요약

> baseball를 웹으로 옮기면 게임 한 판은 메모리 객체 하나보다 `gameId`로 식별되는 긴 수명의 상태가 된다. 그래서 다음 추측 요청은 `currentGame` 필드를 공유하기보다 "어느 게임에 대한 요청인가"를 식별자로 다시 말해 주는 편이 Spring의 요청 모델과 맞다.

## 미션 시나리오

콘솔 baseball에서는 `Game game = new Game()` 한 객체를 계속 붙잡고 `while` 루프 안에서 추측을 반복하면 된다. 하지만 웹에서는 `POST /games`로 게임을 시작하고, 그다음 `POST /games/{gameId}/guesses`로 추측을 보내며, 필요하면 `POST /games/{gameId}/restart`로 다음 라운드를 연다. 요청이 나뉘는 순간 서버는 "이 추측이 방금 만든 그 게임의 다음 턴인가"를 매번 다시 알아야 한다.

이때 학습자가 자주 만드는 실수는 controller나 service에 `currentGame` 필드를 두고, 직전에 시작한 게임을 그대로 이어 쓰는 구조다. 혼자 테스트할 때는 돌아가 보이지만 새 탭, 동시 사용자, 서버 재시작이 끼면 어느 요청이 어느 게임을 가리키는지 금방 흐려진다. PR에서 "`게임 상태 자체`와 `그 상태를 찾는 식별자`를 분리해 보세요", "`세션에 거대한 객체보다 gameId나 사용자 식별 경계를 먼저 정하세요`"라는 코멘트가 나오는 이유가 여기다.

## CS concept 매핑

여기서 닿는 개념은 `stateless request + explicit identity propagation`이다. HTTP 요청은 이전 메서드의 로컬 변수나 Bean 필드를 기억하지 않는다. 그래서 웹 애플리케이션은 요청마다 필요한 identity를 path, cookie, session, token 같은 경로로 다시 전달받고, 그 식별자를 기준으로 실제 상태 저장소를 조회한다.

baseball에 대입하면 `POST /games`가 새 `gameId`를 만들고, 이후 요청은 그 `gameId`를 path variable이나 세션 키로 실어 보낸다. 세션을 쓴다 해도 세션 안에 `Game` 객체 전체를 오래 보관하는 것보다 "현재 사용자의 진행 중 gameId" 정도를 두고 실제 턴 이력과 현재 상태는 별도 저장소에서 읽는 편이 경계를 설명하기 쉽다. 핵심은 "`상태를 들고 있나`"보다 "`다음 요청이 같은 게임임을 무엇으로 증명하나`"다.

## 미션 PR 코멘트 패턴

- "`currentGame` 필드를 공유하지 말고 요청이 어떤 게임을 가리키는지 식별자를 통해 드러내세요`"라는 리뷰는 상태 저장 위치보다 identity 전달 경계를 먼저 자르라는 뜻이다.
- "`세션을 써도 객체 전체를 넣기보다 gameId처럼 작은 참조를 두는 편이 낫습니다`"라는 코멘트는 세션을 상태 원천으로 삼지 말고 lookup 힌트로 제한하라는 신호다.
- "`게임 시작 응답에서 생성된 식별자가 다음 추측 요청 계약으로 이어져야 합니다`"라는 피드백은 API 설계와 저장 모델이 같이 맞물려야 한다는 뜻이다.
- "`웹 요청은 stateless하니 같은 게임을 다시 찾는 경로를 명시해 주세요`"라는 말은 controller가 기억력이 없는 대신 요청 계약이 더 분명해야 한다는 의미다.

## 다음 학습

- 요청 경계 자체를 먼저 잡으려면 `spring/baseball-console-game-loop-http-request-lifecycle-bridge`
- Bean 필드에 상태를 오래 두면 왜 위험한지 이어서 보려면 `spring/baseball-game-state-singleton-bean-scope-bridge`
- 추측 요청의 입력 바인딩과 `gameId` path variable 조합은 `spring/baseball-mvc-controller-binding-bridge`
- `gameId` 뒤에서 실제 현재 상태와 이력을 어떻게 commit할지는 `database/baseball-guess-history-current-state-transaction-bridge`
