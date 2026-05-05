---
schema_version: 3
title: blackjack gameId path vs session vs request body 결정 가이드
concept_id: spring/blackjack-game-id-path-vs-session-vs-requestbody-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/blackjack
review_feedback_tags:
- game-id-transport-choice
- path-vs-session-boundary
- request-contract-shape
aliases:
- blackjack gameId 전달 방식
- 블랙잭 gameId 위치 선택
- 블랙잭 path variable 세션 바디 구분
- blackjack 요청 계약 식별자 위치
- 블랙잭 action body와 gameId 분리
- 스프링 블랙잭 gameId path session
symptoms:
- blackjack 웹 미션에서 gameId를 URL path에 둘지 session에 숨길지 body에 같이 넣을지 기준이 헷갈려요
- 리뷰에서 gameId는 path variable로 빼고 action body는 따로 두라는데 왜 나누는지 모르겠어요
- 세션에 gameId만 둘지 매 요청마다 보내게 할지 정하지 못해서 API 모양이 흔들려요
intents:
- comparison
- design
- mission_bridge
- troubleshooting
prerequisites:
- spring/blackjack-game-id-session-boundary-bridge
- spring/modelattribute-vs-requestbody-binding-primer
- spring/spring-mvc-controller-basics
next_docs:
- spring/blackjack-game-id-session-boundary-bridge
- spring/blackjack-mvc-controller-binding-validation-bridge
- spring/blackjack-post-redirect-get-refresh-replay-bridge
- software-engineering/blackjack-current-game-load-save-repository-bridge
linked_paths:
- contents/spring/blackjack-game-id-session-boundary-bridge.md
- contents/spring/blackjack-mvc-controller-binding-validation-bridge.md
- contents/spring/blackjack-post-redirect-get-refresh-replay-bridge.md
- contents/software-engineering/blackjack-current-game-load-save-repository-bridge.md
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/network/http-state-session-cache.md
confusable_with:
- spring/blackjack-game-id-session-boundary-bridge
- spring/blackjack-mvc-controller-binding-validation-bridge
- spring/modelattribute-vs-requestbody-binding-primer
- software-engineering/blackjack-current-game-load-save-repository-bridge
forbidden_neighbors: []
expected_queries:
- 블랙잭 웹 API에서 gameId를 URL에 둘지 세션으로 숨길지 요청 body에 같이 보낼지 어떻게 판단해?
- blackjack에서 hit 요청 DTO 안에 gameId까지 넣지 말라고 하는 리뷰는 무슨 기준이야?
- 세션에 현재 게임 id를 저장하는 방식과 path variable로 드러내는 방식은 각각 언제 더 맞아?
- 블랙잭 미션에서 action 문자열과 게임 식별자를 같은 request body로 묶으면 왜 경계가 흐려져?
- POST /games/{id}/hit 형태와 POST /hit body에 gameId 넣는 형태 중 초심자에게 어떤 계약이 더 낫지?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 웹으로 옮길 때 현재 게임 식별자인
  gameId를 URL path variable로 드러낼지, session 키로 숨길지, request body에
  action과 함께 넣을지 고르는 chooser다. 블랙잭 gameId 위치 선택, path
  variable vs session, action DTO와 식별자 분리, API 계약 모양, 새로고침과
  멀티탭 디버깅까지 고려한 전달 경계 같은 자연어 질문을 판단 표로 연결한다.
---

# blackjack gameId path vs session vs request body 결정 가이드

## 한 줄 요약

> blackjack에서 `gameId`는 "어느 게임에 대한 요청인가"를 드러내는 식별자라서, 기본값은 path variable이 가장 읽기 쉽다. session은 브라우저 흐름을 단순화할 때만 제한적으로 쓰고, request body는 행동 데이터와 식별자를 섞지 않으려는 이유가 없다면 마지막 선택지로 미룬다.

## 결정 매트릭스

| 지금 더 중요한 것 | 먼저 고를 전달 위치 | 왜 그 선택이 맞나 |
| --- | --- | --- |
| 요청 로그와 API 주소만 봐도 어느 게임인지 바로 보여야 한다 | path variable | `POST /games/{gameId}/hit`처럼 identity가 URL에 드러나면 멀티탭, 테스트, PR 리뷰에서 흐름을 추적하기 쉽다 |
| 브라우저 서버 렌더링 흐름에서 "현재 사용자 한 판"만 잠깐 이어 가면 된다 | session 키 | 화면 이동마다 gameId를 폼에 다시 싣지 않아도 되지만, session에는 `Game` 전체가 아니라 작은 식별자만 두는 편이 안전하다 |
| body에는 `hit`나 `stand`처럼 행동 값만 담고 싶다 | path variable + request body 분리 | 식별자는 "어느 자원인가", body는 "무슨 행동인가"로 역할이 갈려 DTO와 도메인 규칙 경계가 선다 |
| 외부 클라이언트나 API 테스트 도구도 쉽게 호출해야 한다 | path variable | session에 기대지 않아 재현이 쉽고, 요청 하나만 복사해도 같은 게임을 다시 겨냥할 수 있다 |
| body 하나로 모든 입력을 몰아넣고 싶다 | request body는 신중히 | 초반엔 편해 보여도 action 형식 오류와 game 식별 책임이 한 DTO에 붙어 `binding`과 상태 조회 질문이 섞이기 쉽다 |

짧게 외우면 `path = 공개된 identity`, `session = 브라우저 편의용 힌트`, `body = 행동 데이터`다.

## 흔한 오선택

`ActionRequest { gameId, action }` 하나로 끝내면 단순해 보이지만, 리뷰에서 "`gameId`는 자원 식별이고 `action`은 명령"이라고 자주 끊는 이유가 있다.
같은 DTO에 넣는 순간 "`JSON 형식이 틀렸나`"와 "`존재하지 않는 게임인가`"가 같은 층처럼 보이기 쉽다.

session에 `Game` 객체 전체를 넣고 path를 비워 두는 선택도 흔하다.
이 방식은 한 사람 데모에는 빨라 보여도 새 탭, 서버 재시작, 저장소 교체 순간에 흐름이 갑자기 불투명해진다.
session을 쓰더라도 "현재 사용자의 진행 중 gameId" 같은 작은 참조만 두고 실제 상태는 repository에서 읽는 쪽이 덜 흔들린다.

반대로 session을 쓴다는 이유로 path variable을 완전히 금지할 필요도 없다.
서버 렌더링 화면에서는 session으로 현재 게임을 따라가되, API나 디버깅 경로는 path variable로 드러내는 혼합 구조가 더 읽기 쉬운 경우도 있다.
중요한 것은 "식별자 책임을 어디에 두는가"를 문서화한 채 일관되게 가는 것이다.

## 다음 학습

- gameId를 왜 객체 전체 대신 작은 참조로 다뤄야 하는지 미션 맥락으로 보려면 [blackjack 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지](./blackjack-game-id-session-boundary-bridge.md)를 본다.
- path variable과 request body를 controller에서 어떻게 나눠 받는지 보려면 [blackjack 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나](./blackjack-mvc-controller-binding-validation-bridge.md)를 잇는다.
- 새로고침과 중복 submit까지 같이 보려면 [blackjack 게임 시작/액션 제출 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지](./blackjack-post-redirect-get-refresh-replay-bridge.md)를 읽는다.
- 식별자를 받은 뒤 실제 게임을 어디서 조회하고 저장하는지가 헷갈리면 [blackjack 현재 게임 조회/저장 ↔ Repository 경계 브릿지](../software-engineering/blackjack-current-game-load-save-repository-bridge.md)로 넘어간다.
