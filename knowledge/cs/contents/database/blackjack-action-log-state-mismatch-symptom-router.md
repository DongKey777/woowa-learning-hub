---
schema_version: 3
title: blackjack 행동 로그는 있는데 상태가 안 맞아요 원인 라우터
concept_id: database/blackjack-action-log-state-mismatch-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/blackjack
review_feedback_tags:
- history-state-mismatch-triage
- action-dedup-vs-transaction-split
- bean-state-leak-vs-db-state
aliases:
- blackjack 행동 로그는 있는데 상태가 안 맞음
- 블랙잭 hit 로그는 남았는데 점수가 다름
- blackjack 현재 손패와 action history 불일치
- 블랙잭 상태 꼬임 원인 라우터
- blackjack hit stand 결과 불일치 어디부터 봐야 해
symptoms:
- hit은 한 번만 눌렀는데 행동 로그에는 남아 있고 현재 점수는 이전 값으로 보여요
- stand가 처리됐다고 보이는데 다음 요청에서 아직 내 차례처럼 동작해요
- 블랙잭 웹 버전에서 새로고침하거나 두 탭으로 테스트하면 로그와 현재 상태가 서로 안 맞아요
- 카드가 두 장 들어간 것처럼 보일 때도 있고, 로그는 한 줄인데 상태만 두 번 진행된 것처럼 보일 때도 있어요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- database/transaction-basics
- database/blackjack-action-history-current-state-transaction-bridge
- spring/blackjack-game-state-singleton-bean-scope-bridge
next_docs:
- database/blackjack-action-history-current-state-transaction-bridge
- database/blackjack-hit-stand-duplicate-submit-idempotency-bridge
- spring/blackjack-game-state-singleton-bean-scope-bridge
- database/transaction-basics
linked_paths:
- contents/database/blackjack-action-history-current-state-transaction-bridge.md
- contents/database/blackjack-hit-stand-duplicate-submit-idempotency-bridge.md
- contents/database/transaction-basics.md
- contents/spring/blackjack-game-state-singleton-bean-scope-bridge.md
- contents/spring/blackjack-game-id-session-boundary-bridge.md
confusable_with:
- database/blackjack-action-history-current-state-transaction-bridge
- database/blackjack-hit-stand-duplicate-submit-idempotency-bridge
- spring/blackjack-game-state-singleton-bean-scope-bridge
forbidden_neighbors: []
expected_queries:
- 블랙잭에서 행동 로그는 저장됐는데 현재 점수나 차례가 안 맞을 때 원인을 어떻게 먼저 갈라 봐?
- blackjack hit 처리 후 로그와 현재 손패 상태가 다르면 중복 제출 문제인지 트랜잭션 문제인지 어떻게 구분해?
- stand가 끝났다고 보였는데 다음 요청에서 아직 진행 중처럼 보이면 DB 쪽에서 어디부터 확인해야 해?
- 두 탭으로 블랙잭을 테스트할 때 상태가 섞이거나 로그와 현재 상태가 어긋나는 상황을 어떤 질문 순서로 진단해?
- 블랙잭 웹 미션에서 action history는 맞는데 snapshot state가 틀린 장면을 어떤 개념으로 설명해야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 웹과 DB로 확장할 때 행동 로그는 남았는데
  현재 손패 점수, 차례, 종료 여부가 맞지 않거나, 같은 액션이 두 번 처리된 듯
  보이는 상황을 원인별로 가르는 symptom_router다. hit 로그는 있는데 점수가
  이전 값임, stand 뒤에도 진행 중처럼 보임, 두 탭 테스트에서 상태가 섞임,
  action history와 snapshot state가 어긋남 같은 학습자 표현을 트랜잭션 분리,
  중복 제출 dedup 누락, singleton 상태 보관 문제로 라우팅한다.
---

# blackjack 행동 로그는 있는데 상태가 안 맞아요 원인 라우터

## 한 줄 요약

> blackjack에서 "로그는 남았는데 상태가 안 맞다"는 증상은 하나가 아니다. 먼저 한 액션의 로그 append와 현재 상태 update가 같은 commit으로 묶였는지, 같은 요청이 두 번 인정된 건 아닌지, 아예 상태를 Bean 필드에 들고 있어 요청끼리 섞인 건 아닌지 갈라야 한다.

## 가능한 원인

1. **행동 로그 insert와 현재 상태 update가 서로 다른 write로 찢어졌다.** `game_actions`에는 `HIT`가 남았는데 `round_state` 점수나 `finished` 갱신이 다른 commit으로 빠지면, 로그와 현재 상태가 어긋난다. 이 갈래는 [blackjack 행동 이력/현재 손패 상태 ↔ DB 트랜잭션 브릿지](./blackjack-action-history-current-state-transaction-bridge.md)로 이어진다.
2. **같은 hit/stand 요청이 재전송돼 dedup 없이 두 번 인정됐다.** 로그가 두 줄 생기거나, 상태만 한 번 더 진행된 것처럼 보이면 더블클릭, timeout 뒤 재전송, action token 부재를 먼저 본다. 이 경우는 [blackjack hit/stand 중복 제출 ↔ 멱등성 키와 UNIQUE 브릿지](./blackjack-hit-stand-duplicate-submit-idempotency-bridge.md)로 간다.
3. **현재 게임 상태를 singleton Bean 필드 같은 요청 외부 메모리에 들고 있다.** 두 탭이나 두 사용자가 섞일 때만 증상이 튀면, DB write보다 먼저 상태 보관 위치가 틀렸을 가능성이 크다. 이 갈래는 [blackjack 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지](../spring/blackjack-game-state-singleton-bean-scope-bridge.md)를 본다.
4. **게임 식별자와 현재 라운드 선택이 불안정하다.** 로그는 맞게 쌓였는데 다른 `game_id`의 snapshot을 읽거나, 세션에서 현재 게임을 잘못 꺼내면 "방금 action과 지금 보이는 상태"가 다른 게임을 가리킬 수 있다. 이 경우는 [blackjack 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지](../spring/blackjack-game-id-session-boundary-bridge.md)까지 같이 본다.

## 빠른 자기 진단

1. `hit` 한 번 처리할 때 action history insert와 round state update가 같은 트랜잭션인지 먼저 확인한다. 아니면 로그/상태 불일치가 가장 자연스럽다.
2. 같은 액션에 request id, action token, unique key가 있는지 본다. 없으면 재전송이 로그 두 줄 또는 상태 두 번 진행으로 보일 수 있다.
3. 증상이 두 탭, 새로고침, 다른 사용자 동시 테스트에서만 심해지는지 확인한다. 그렇다면 DB 락보다 singleton 상태 공유 가능성이 더 높다.
4. 로그 row의 `game_id`와 화면이 읽는 현재 상태의 `game_id`가 같은지 대조한다. 식별자가 엇갈리면 저장은 정상이어도 다른 게임 상태를 보고 있을 수 있다.

## 다음 학습

- 한 액션의 로그 append와 snapshot update를 왜 같은 commit으로 묶어야 하는지 보려면 [blackjack 행동 이력/현재 손패 상태 ↔ DB 트랜잭션 브릿지](./blackjack-action-history-current-state-transaction-bridge.md)를 읽는다.
- 더블클릭과 재전송을 같은 action 한 번으로 닫는 방법이 궁금하면 [blackjack hit/stand 중복 제출 ↔ 멱등성 키와 UNIQUE 브릿지](./blackjack-hit-stand-duplicate-submit-idempotency-bridge.md)로 간다.
- 상태가 사용자/탭 사이에서 섞이는 근본 원인을 보려면 [blackjack 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지](../spring/blackjack-game-state-singleton-bean-scope-bridge.md)를 함께 본다.
- 요청마다 어떤 게임을 가리키는지부터 흔들린다면 [blackjack 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지](../spring/blackjack-game-id-session-boundary-bridge.md)를 이어서 본다.
