---
schema_version: 3
title: 'blackjack 게임 시작/액션 제출 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지'
concept_id: spring/blackjack-post-redirect-get-refresh-replay-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
review_feedback_tags:
- redirect-after-post
- refresh-resubmit-boundary
- prg-vs-idempotency
aliases:
- blackjack PRG
- 블랙잭 새로고침 중복 제출
- blackjack redirect after post
- 블랙잭 POST 뒤 redirect
- 블랙잭 hit stand 새로고침
symptoms:
- hit 하고 새로고침했더니 브라우저가 같은 요청을 다시 보내려 해요
- 게임 시작 POST 응답에서 바로 화면을 렌더했더니 F5가 불안해요
- 리뷰에서 redirect after post를 하라는데 블랙잭에 왜 필요한지 모르겠어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/blackjack-game-id-session-boundary-bridge
- spring/blackjack-mvc-controller-binding-validation-bridge
- network/post-redirect-get-prg-beginner-primer
next_docs:
- network/post-redirect-get-prg-beginner-primer
- database/blackjack-hit-stand-duplicate-submit-idempotency-bridge
- spring/blackjack-game-id-session-boundary-bridge
linked_paths:
- contents/network/post-redirect-get-prg-beginner-primer.md
- contents/database/blackjack-hit-stand-duplicate-submit-idempotency-bridge.md
- contents/spring/blackjack-game-id-session-boundary-bridge.md
- contents/spring/blackjack-mvc-controller-binding-validation-bridge.md
- contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md
confusable_with:
- database/blackjack-hit-stand-duplicate-submit-idempotency-bridge
- spring/blackjack-game-id-session-boundary-bridge
- spring/blackjack-mvc-controller-binding-validation-bridge
forbidden_neighbors: []
expected_queries:
- 블랙잭 웹 미션에서 POST 응답으로 바로 뷰를 그리면 새로고침 때 왜 같은 action이 다시 나가?
- blackjack에서 game start나 hit 뒤 redirect 하라는 리뷰는 PRG 관점에서 무슨 뜻이야?
- hit stand 처리 후 결과 페이지를 GET으로 다시 열어야 하는 이유가 뭐야?
- 블랙잭 미션에서 새로고침 중복 제출 문제를 Spring controller 설계로 먼저 줄이려면 어떻게 봐야 해?
- redirect after post와 DB 멱등성은 블랙잭에서 각각 어떤 역할이야?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 Spring MVC로 옮길 때 게임 시작, hit,
  stand 같은 상태 변경 POST 뒤 결과 화면을 바로 렌더하지 않고 redirect 후 GET
  으로 다시 여는 PRG(Post/Redirect/Get) 경계를 설명하는 mission_bridge다.
  새로고침 시 POST 재전송, redirect after post, 결과 페이지 GET, action
  replay 감소, PRG와 DB 멱등성 차이 같은 학습자 표현을 blackjack 요청 흐름과
  브라우저-서버 계약으로 연결한다.
---

# blackjack 게임 시작/액션 제출 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지

## 한 줄 요약

> blackjack에서 `POST /games`나 `POST /games/{id}/actions`가 상태를 바꿨다면, 결과 화면은 그 POST 응답에서 바로 끝내기보다 redirect 뒤 `GET`으로 다시 열어야 새로고침이 같은 상태 변경을 반복할 가능성을 줄일 수 있다.

## 미션 시나리오

blackjack를 웹으로 옮기면 `게임 시작`, `hit`, `stand`가 더 이상 메서드 호출 한
번으로 끝나지 않고 브라우저가 보내는 POST 요청이 된다. 이때 처음 짜기 쉬운 코드는
controller가 POST를 처리한 직후 곧바로 결과 view를 렌더하는 구조다. 화면은 바로
보이지만, 학습자가 F5를 누르거나 브라우저가 "양식 재전송"을 물을 때 같은 POST가
다시 나갈 수 있다.

PR에서 "`상태를 바꾼 뒤에는 redirect로 끊어 주세요`", "`결과 화면은 GET 주소를
갖게 하세요`"라는 코멘트가 붙는 자리가 여기다. blackjack에서는 한 번의 `hit`가
카드 한 장 추가와 연결되기 때문에, 새로고침이 같은 액션 재실행처럼 보이면 API
계약이 불안해진다.

## CS concept 매핑

여기서 닿는 개념은 PRG(Post/Redirect/Get)다. 상태 변경은 POST가 맡고, 사용자가
다시 보게 될 결과 화면은 redirect 이후 GET이 맡는다. 예를 들면 `POST /games`
뒤에 `303 See Other`로 `/games/{id}`를 알려 주고, 브라우저는 그 주소를 GET으로
다시 연다. `hit`나 `stand`도 비슷하게 처리하면 결과 페이지의 새로고침 대상이
"같은 POST 재전송"이 아니라 "현재 게임 화면 GET"이 된다.

다만 PRG가 중복 실행을 완전히 없애 주는 것은 아니다. 네트워크 재시도나 더블클릭은
redirect 전에 이미 두 POST가 들어올 수 있다. 그래서 PRG는 브라우저 새로고침
경계를 정리하는 장치이고, 같은 action을 한 번만 인정하는 보장은 DB 멱등성 키나
UNIQUE 제약 같은 저장소 계약이 맡는다. 리뷰에서 "`redirect after post`도 하고
`idempotency`도 생각하세요"라는 말은 둘 중 하나를 고르라는 뜻이 아니다.

## 미션 PR 코멘트 패턴

- "`POST` 응답에서 바로 view를 렌더하면 결과 페이지가 새로고침 가능한 주소를 못 갖습니다."
- "`게임 시작`이나 `hit`는 상태 변경이니, 완료 후에는 `GET /games/{id}` 같은 조회 주소로 넘겨 주세요."
- "PRG는 브라우저 새로고침 위험을 줄이는 장치이고, action 중복 자체를 막는 최종 보장은 아닙니다."
- "`redirect`를 넣었다고 중복 submit 방어가 끝난 건 아닙니다. 저장소 dedup 경계는 별도로 필요합니다."

## 다음 학습

- PRG 자체를 HTTP 흐름으로 다시 정리하려면 [Post/Redirect/Get(PRG) 패턴 입문](../network/post-redirect-get-prg-beginner-primer.md)을 읽는다.
- 같은 action 재전송을 저장소에서 한 번만 인정하는 쪽은 [blackjack hit/stand 중복 제출 ↔ 멱등성 키와 UNIQUE 브릿지](../database/blackjack-hit-stand-duplicate-submit-idempotency-bridge.md)로 이어진다.
- 요청마다 어떤 게임인지 식별자를 어떻게 잇는지 보려면 [blackjack 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지](./blackjack-game-id-session-boundary-bridge.md)를 함께 본다.
- `@RequestBody`, `gameId`, 형식 검증을 controller에서 어디까지 다룰지 보려면 [blackjack 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나](./blackjack-mvc-controller-binding-validation-bridge.md)를 잇는다.
