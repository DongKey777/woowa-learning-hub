---
schema_version: 3
title: 'blackjack hit/stand 중복 제출 ↔ 멱등성 키와 UNIQUE 브릿지'
concept_id: database/blackjack-hit-stand-duplicate-submit-idempotency-bridge
canonical: false
category: database
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
review_feedback_tags:
- action-idempotency
- duplicate-submit
- insert-first-arbitration
aliases:
- blackjack hit 중복 요청
- blackjack stand 두 번 처리
- 블랙잭 액션 재전송 중복
- 블랙잭 더블클릭 카드 두 장
- blackjack action idempotency
symptoms:
- hit 버튼을 두 번 눌렀더니 카드가 한 장이 아니라 두 장 들어가요
- 응답이 늦어서 stand를 다시 보냈더니 같은 게임이 두 번 종료 처리돼요
- 같은 action 요청 재전송을 service if 문으로만 막았는데 상태가 또 진행돼요
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- spring/blackjack-game-id-session-boundary-bridge
- database/blackjack-action-history-current-state-transaction-bridge
- database/transaction-basics
next_docs:
- database/idempotency-key-and-deduplication
- database/duplicate-key-vs-busy-response-mapping
- database/blackjack-action-history-current-state-transaction-bridge
linked_paths:
- contents/spring/blackjack-game-id-session-boundary-bridge.md
- contents/database/blackjack-action-history-current-state-transaction-bridge.md
- contents/database/transaction-basics.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/duplicate-key-vs-busy-response-mapping.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
confusable_with:
- database/blackjack-action-history-current-state-transaction-bridge
- database/idempotency-key-and-deduplication
- database/unique-vs-locking-read-duplicate-primer
forbidden_neighbors: []
expected_queries:
- 블랙잭 웹 미션에서 hit 요청이 재전송되면 카드가 두 장 들어가지 않게 DB에서 어떻게 막아?
- blackjack에서 stand를 두 번 보내도 한 번만 처리되게 만들려면 어떤 키를 둬야 해?
- 액션 중복 제출을 exists 확인으로만 막으면 왜 블랙잭 상태가 두 번 진행돼?
- 블랙잭 미션 리뷰에서 같은 action을 한 번만 인정하라는 말은 멱등성으로 어떻게 이해해?
- hit 또는 stand 요청 재시도 뒤 이미 처리된 결과를 다시 보여주려면 어떤 저장 구조가 좋아?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 웹과 DB로 확장할 때 hit, stand 같은
  액션 요청이 더블클릭, timeout 뒤 재전송, 네트워크 재시도 때문에 두 번
  들어와 카드가 두 장 추가되거나 종료가 중복 처리되는 문제를 멱등성 키와
  UNIQUE 제약으로 설명하는 mission_bridge다. 같은 action 한 번만 인정,
  duplicate key, action sequence, 재전송 결과 replay, insert-first arbitration
  같은 리뷰 표현을 blackjack 게임 진행 상태와 연결한다.
---

# blackjack hit/stand 중복 제출 ↔ 멱등성 키와 UNIQUE 브릿지

## 한 줄 요약

> blackjack에서 `hit` 한 번은 카드 한 장 추가라는 사건 하나여야 한다. 웹 요청이 재전송될 수 있다면 "이미 처리했는가?"를 읽고 판단하기보다, 같은 action identity를 DB가 한 번만 통과시키고 나머지는 기존 결과를 다시 읽게 만드는 편이 덜 흔들린다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "hit 버튼을 두 번 누르면 카드가 두 장 들어가요" | 같은 action POST가 더블클릭이나 retry로 두 번 처리되는 blackjack API | action identity를 DB가 한 번만 통과시키게 한다 |
| "이미 진행 중인지 service if문으로 확인하면 안 되나요?" | 두 요청이 같은 현재 상태를 보고 모두 hit 가능하다고 판단하는 코드 | 도메인 상태 검사와 HTTP 재전송 dedup을 다른 축으로 본다 |
| "stand 두 번이면 그냥 두 번째는 무시하면 되나요?" | 종료 action replay를 결과 재사용 없이 예외나 중복 처리로 끝내는 구조 | duplicate key 뒤 기존 action 결과를 fresh read/replay할 수 있게 한다 |

## 미션 시나리오

콘솔 blackjack에서는 사용자가 Enter를 한 번 치면 `hit`도 한 번만 실행된다.
하지만 웹으로 옮기면 버튼 더블클릭, timeout 뒤 재시도, 모바일 네트워크 흔들림
때문에 `POST /games/{id}/actions`가 같은 의미로 두 번 들어올 수 있다. 이때
서비스가 "`게임이 아직 진행 중인가?`"만 확인하고 곧바로 카드를 한 장 추가하면,
두 요청이 둘 다 통과해 플레이어 손패가 한 번에 두 장 늘어날 수 있다.

`stand`도 비슷하다. 첫 요청이 이미 종료 처리를 끝냈는데 두 번째 요청이 거의
같은 시점에 들어오면, 결과 이력과 현재 상태를 또 한 번 갱신하려고 시도한다.
리뷰에서 "`같은 action 재전송을 business if문으로만 막지 마세요`",
"`hit` 한 번의 identity를 저장소가 먼저 인정하게 하세요`"라는 코멘트가
나오는 자리가 여기다.

## CS concept 매핑

여기서 닿는 개념은 멱등성 키와 insert-first arbitration이다. 예를 들어
`game_actions`에 `(game_id, action_token)` 또는 `(game_id, action_no)` 같은
`UNIQUE` 제약을 두면, 같은 action을 두 번 넣으려는 경쟁에서 DB가 한 요청만
승자로 정한다.

짧게 쓰면 이런 감각이다.

```sql
INSERT INTO game_actions (game_id, action_token, action_type)
VALUES (?, ?, ?);
```

이 insert가 성공한 요청만 카드 추가와 현재 상태 갱신까지 진행하고, 같은
`action_token`으로 다시 온 요청은 duplicate key를 보고 "이미 처리된 action"
으로 해석한다. 핵심은 `hit 가능 여부` 자체가 도메인 규칙인 것과, 같은 HTTP
요청 재전송을 한 번만 인정하는 dedup 계약이 다른 축이라는 점이다. 전자는
`Game` 규칙이고, 후자는 요청 identity를 저장하는 DB 경계다.

## 미션 PR 코멘트 패턴

- "`exists` 확인 후 `save`만으로는 재전송 경쟁에서 둘 다 통과할 수 있습니다."
- "`hit` 한 번의 identity를 `gameId`만으로 뭉개지 말고 action별 키를 두세요."
- "중복 요청을 long lock으로만 막기보다, `UNIQUE` 제약이 먼저 승자를 정하고 나머지는 기존 결과를 읽게 만드는 편이 단순합니다."
- "`이미 종료된 게임이라서 막았다`와 `같은 요청을 두 번 받았다`는 다른 문제입니다. 도메인 상태 검사와 dedup 경계를 분리하세요."

## 다음 학습

- 멱등성 키 저장소와 replay 응답 패턴을 더 일반화해서 보려면 [Idempotency Key and Deduplication](./idempotency-key-and-deduplication.md)를 읽는다.
- duplicate key를 API 의미로 어떻게 번역할지 보려면 [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)으로 간다.
- action 이력 append와 현재 손패 snapshot을 같은 commit으로 묶는 문제는 [blackjack 행동 이력/현재 손패 상태 ↔ DB 트랜잭션 브릿지](./blackjack-action-history-current-state-transaction-bridge.md)로 이어진다.
- 요청마다 어느 게임인지 식별하는 경계를 먼저 복습하려면 [blackjack 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지](../spring/blackjack-game-id-session-boundary-bridge.md)를 함께 본다.
