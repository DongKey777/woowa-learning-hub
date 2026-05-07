---
schema_version: 3
title: 'lotto 구매 POST 뒤 결과 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지'
concept_id: spring/lotto-purchase-post-redirect-get-refresh-replay-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- redirect-after-post
- refresh-resubmit-boundary
- prg-vs-idempotency
aliases:
- lotto PRG
- 로또 구매 새로고침 중복 제출
- lotto redirect after post
- 로또 구매 POST 뒤 redirect
- 로또 결과 화면 GET 전환
symptoms:
- 로또 구매를 POST로 처리한 뒤 결과를 바로 렌더했더니 새로고침이 불안해요
- 구매 완료 화면에서 F5를 누르면 브라우저가 같은 요청을 다시 보내려 해요
- 리뷰에서 redirect after post를 하라는데 lotto에 왜 필요한지 모르겠어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/lotto-purchase-ticket-transaction-boundary-bridge
- software-engineering/lotto-purchase-flow-service-layer-bridge
- database/lotto-purchase-duplicate-submit-idempotency-bridge
next_docs:
- database/lotto-purchase-duplicate-submit-idempotency-bridge
- spring/lotto-purchase-ticket-transaction-boundary-bridge
- software-engineering/lotto-purchase-history-repository-boundary-bridge
linked_paths:
- contents/database/lotto-purchase-duplicate-submit-idempotency-bridge.md
- contents/spring/lotto-purchase-ticket-transaction-boundary-bridge.md
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
- contents/software-engineering/lotto-purchase-history-repository-boundary-bridge.md
- contents/network/post-redirect-get-prg-beginner-primer.md
confusable_with:
- database/lotto-purchase-duplicate-submit-idempotency-bridge
- spring/lotto-purchase-ticket-transaction-boundary-bridge
- software-engineering/lotto-purchase-flow-service-layer-bridge
forbidden_neighbors: []
expected_queries:
- 로또 구매 요청을 처리한 뒤 결과 화면을 바로 렌더하지 말고 redirect 하라는 건 무슨 뜻이야?
- lotto를 웹으로 옮겼더니 구매 완료 페이지에서 새로고침할 때 같은 POST가 다시 나갈 수 있다는데 왜 그래?
- purchase 완료 후 GET 주소로 다시 보내라는 리뷰를 Spring controller 기준으로 설명해 줄 수 있어?
- 로또 미션에서 redirect after post와 중복 구매 방지는 각각 어떤 문제를 막아?
- 구매 성공 응답에서 바로 모델을 채워 뷰를 그리면 뭐가 어색해지는지 lotto 예시로 알고 싶어
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션을 Spring MVC로 옮길 때 구매 상태를 바꾸는 POST 뒤에
  결과 화면을 바로 렌더하지 않고 redirect 후 GET으로 다시 여는
  PRG(Post/Redirect/Get) 경계를 설명하는 mission_bridge다. 로또 구매
  새로고침 중복 제출, redirect after post, 결과 페이지 GET 주소, 브라우저 F5,
  PRG와 DB 멱등성의 역할 차이 같은 학습자 표현을 lotto 구매 흐름과
  브라우저-서버 계약으로 연결한다.
---

# lotto 구매 POST 뒤 결과 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지

## 한 줄 요약

> lotto 구매처럼 상태를 바꾸는 POST는 처리 직후 결과를 바로 렌더하기보다, redirect 뒤 GET 주소에서 다시 보여 주는 편이 브라우저 새로고침 때 같은 구매 요청이 다시 재생되는 혼란을 줄인다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "구매 완료 화면에서 F5를 누르면 같은 POST가 다시 나갈까 봐 불안해요" | `POST /purchases` 응답에서 바로 결과 view를 렌더하는 lotto 화면 | 상태 변경 POST와 다시 열 수 있는 결과 GET을 redirect로 끊는다 |
| "구매 결과를 보여 주려면 POST에서 모델을 채워도 되는 거 아닌가요?" | 완료 화면 주소가 없고 브라우저 새로고침 대상이 POST로 남는 구조 | 결과 화면은 `/purchases/{id}` 같은 조회 GET 주소를 갖게 한다 |
| "PRG를 넣으면 중복 구매가 완전히 막히나요?" | 더블클릭이나 timeout retry가 redirect 전에 이미 들어올 수 있는 상황 | PRG는 새로고침 경계이고 DB 멱등성은 별도 방어라는 점을 나눈다 |

## 미션 시나리오

lotto를 웹 애플리케이션으로 옮기면 `구매 금액 입력 -> 티켓 생성 -> purchase 저장 ->
결과 화면 표시`가 한 번의 HTTP 흐름이 된다. 처음 구현에서는 `POST /purchases`를
처리한 controller가 곧바로 모델을 채워 "구매 완료" 화면을 렌더하기 쉽다. 눈앞의
화면은 잘 나오지만, 학습자가 F5를 누르거나 브라우저가 "양식 재전송"을 묻는 순간
"같은 구매 POST를 다시 보내도 되나?"라는 불안정한 상태가 드러난다.

리뷰에서 "`POST` 후에는 redirect로 끊어 주세요", "`완료 화면은 다시 열 수 있는
GET 주소를 가지게 하세요`"라는 코멘트가 붙는 자리가 여기다. lotto에서는 한 번의
구매가 여러 티켓 생성과 저장으로 이어지므로, 결과 화면 새로고침이 구매 재실행처럼
보이면 사용자 경험도 어색하고 서버 책임도 흐려진다.

## CS concept 매핑

여기서 닿는 개념은 PRG(Post/Redirect/Get)다. 상태 변경은 POST가 맡고, 사용자가
다시 보게 될 결과 화면은 redirect 이후 GET이 맡는다. 예를 들어
`POST /purchases`가 성공하면 `303 See Other`로 `/purchases/{id}`를 알려 주고,
브라우저는 그 주소를 GET으로 다시 연다. 그러면 결과 페이지의 새로고침 대상은
"같은 구매 POST 재전송"이 아니라 "이미 만들어진 구매 조회 GET"이 된다.

다만 PRG가 중복 구매를 완전히 막아 주는 것은 아니다. 더블클릭이나 timeout 뒤
재시도는 redirect 전에 이미 두 POST가 들어올 수 있다. 그래서 PRG는 브라우저
새로고침 경계를 정리하는 장치이고, 같은 구매 요청을 한 번만 인정하는 최종 보장은
멱등성 키나 `UNIQUE` 제약 같은 저장소 계약이 맡는다. 반대로 트랜잭션 경계는
`purchase`와 `ticket`이 함께 commit/rollback되는 원자성을 책임진다. 즉 lotto
구매 흐름에서는 PRG, 트랜잭션, 멱등성이 각자 다른 층위의 문제를 나눠 맡는다.

## 미션 PR 코멘트 패턴

- "`POST` 응답에서 바로 view를 렌더하면 결과 화면이 재조회 가능한 주소를 갖지 못합니다."
- "구매 성공 후에는 `/purchases/{id}` 같은 조회 GET으로 넘겨서 새로고침 대상을 바꾸세요."
- "redirect를 넣어도 중복 submit 방어가 끝난 것은 아닙니다. PRG와 idempotency를 분리해서 설명해 보세요."
- "controller는 HTTP 흐름 전환을 맡고, purchase와 ticket의 원자성은 service 트랜잭션이 맡아야 합니다."

## 다음 학습

- PRG 자체를 HTTP 왕복 기준으로 다시 정리하려면 `network/post-redirect-get-prg-beginner-primer`
- 같은 구매 요청을 DB에서 한 번만 인정하는 쪽은 `database/lotto-purchase-duplicate-submit-idempotency-bridge`
- 구매 1회와 여러 ticket 저장을 같은 원자 단위로 묶는 쪽은 `spring/lotto-purchase-ticket-transaction-boundary-bridge`
- 완료 화면 GET이 어떤 도메인 단위를 조회해야 하는지 보려면 `software-engineering/lotto-purchase-history-repository-boundary-bridge`
