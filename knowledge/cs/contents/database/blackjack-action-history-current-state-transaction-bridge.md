---
schema_version: 3
title: 'blackjack 행동 이력/현재 손패 상태 ↔ DB 트랜잭션 브릿지'
concept_id: database/blackjack-action-history-current-state-transaction-bridge
canonical: false
category: database
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
review_feedback_tags:
- action-history-current-state
- hit-stand-transactional-update
- round-snapshot-truth-source
aliases:
- blackjack 행동 이력 저장
- 블랙잭 현재 상태 테이블
- blackjack hit stand DB 반영
- 블랙잭 라운드 스냅샷 저장
- blackjack action history transaction
symptoms:
- hit 한 번 처리했는데 행동 이력은 남았는데 현재 점수가 안 맞아요
- 블랙잭 웹 버전에서 이전 행동 로그와 지금 손패 상태가 따로 놀아요
- hit stand 요청마다 insert와 update가 흩어져 있어 어디를 진실 원천으로 봐야 할지 모르겠어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- database/transaction-basics
- database/baseball-guess-history-current-state-transaction-bridge
- spring/blackjack-game-state-singleton-bean-scope-bridge
next_docs:
- database/transaction-basics
- database/baseball-guess-history-current-state-transaction-bridge
- spring/blackjack-game-state-singleton-bean-scope-bridge
linked_paths:
- contents/database/transaction-basics.md
- contents/database/baseball-guess-history-current-state-transaction-bridge.md
- contents/database/transaction-isolation-basics.md
- contents/spring/blackjack-game-state-singleton-bean-scope-bridge.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
confusable_with:
- database/baseball-guess-history-current-state-transaction-bridge
- spring/blackjack-game-state-singleton-bean-scope-bridge
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
forbidden_neighbors: []
expected_queries:
- 블랙잭 미션을 웹으로 옮기면 hit 한 번을 DB에 어떤 단위로 저장해야 해?
- blackjack에서 행동 로그 insert와 현재 손패 update를 같은 트랜잭션으로 묶으라는 말은 무슨 뜻이야?
- 블랙잭 게임 진행 이력을 남기면서 지금 차례와 점수는 어디서 믿어야 해?
- hit 요청은 성공했는데 목록에는 행동이 남고 게임 상태는 이전 점수인 상황을 어떻게 설명해?
- 블랙잭에서 append 로그만 쌓고 현재 라운드 상태는 나중에 계산해도 되는지 궁금해
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 웹과 DB로 확장할 때 hit, stand 같은 행동
  이력 append와 현재 라운드 상태 snapshot을 같은 write 단위로 읽게 돕는
  mission_bridge다. 행동 로그는 남았는데 현재 손패 점수나 차례가 안 맞음,
  지금 게임 상태를 어디서 믿나, 한 번의 hit 요청에 insert와 update가 흩어짐,
  append-only history와 current state를 함께 commit해야 하나 같은 학습자
  표현을 blackjack 저장 모델과 트랜잭션 경계 설명으로 연결한다.
---

# blackjack 행동 이력/현재 손패 상태 ↔ DB 트랜잭션 브릿지

## 한 줄 요약

> blackjack에서 `hit` 한 번은 "행동 로그 한 줄 추가"만이 아니라 "현재 손패 합계, 다음 차례, 종료 여부가 어떻게 바뀌었는가"까지 함께 확정되는 write다. 그래서 action history append와 round snapshot update를 같은 트랜잭션으로 읽는 편이 현재 truth가 덜 흔들린다.

## 미션 시나리오

콘솔 blackjack은 메모리 안 `Game` 객체 하나가 행동 이력과 현재 상태를 동시에
들고 있으니 둘이 쉽게 어긋나지 않는다. 하지만 웹으로 옮기면 `POST /games/{id}/hit`
한 번마다 "플레이어가 카드를 한 장 더 뽑았다"는 이력과 "현재 점수는 몇이고,
다음 행동이 가능한가"라는 현재 상태를 따로 저장하고 싶어진다.

이때 자주 보이는 초기 구조는 `game_actions` 같은 테이블에 `HIT` 로그를 먼저
insert하고, 서비스 마지막에 `games`나 `rounds` row의 점수와 차례를 update하는
방식이다. 처음에는 자연스러워 보여도 중간 실패가 생기면 "행동은 남았는데 현재
손패는 이전 점수", "stand 로그는 있는데 아직도 플레이어 차례" 같은 설명하기
어려운 상태가 생긴다. 리뷰에서 "한 번의 행동 요청이 남기는 truth를 같은 write
단위로 묶어 보세요"라는 코멘트가 나오는 이유가 여기다.

## CS concept 매핑

여기서 닿는 개념은 `append-only history`와 `current snapshot`을 같은
트랜잭션으로 맞추는 감각이다. `game_actions`는 과거에 어떤 선택이 있었는지를
설명하고, `games` 또는 `round_state` row는 지금 API가 바로 믿을 현재 truth를
가진다. 역할은 다르지만, 같은 `hit` 요청에서 함께 움직여야 읽는 쪽이 혼란스럽지
않다.

예를 들면 `INSERT INTO game_actions (...) VALUES ('HIT', ...)` 뒤에
`UPDATE round_state SET player_score = ?, turn = ?, finished = ? WHERE game_id = ?`
가 같은 commit 안에 있어야 한다. 핵심은 테이블 개수가 아니라 "현재 상태를 어디서
믿을지"를 먼저 고정하는 것이다. history만 보고 매번 점수와 차례를 재구성할 수도
있지만, beginner~intermediate 단계에서는 현재 상태 row를 두고 행동 결과를
원자적으로 반영하는 편이 PR 대화와 운영 설명 둘 다 단순해진다.

## 미션 PR 코멘트 패턴

- "`hit` 로그는 저장됐는데 현재 점수와 종료 여부 갱신이 분리돼 있어 중간 실패를 설명하기 어렵습니다."
- "행동 이력은 audit 용도고, 지금 게임이 어떤 상태인지 바로 읽을 current snapshot도 함께 관리해야 합니다."
- "`insert history -> 나중에 update state` 구조라면 한 번의 요청이 남기는 truth가 찢어질 수 있습니다."
- "점수 계산 규칙은 도메인 객체가 맡고, DB는 그 결과를 이력과 현재 상태로 함께 commit하는 역할로 나누면 읽기 쉽습니다."

## 다음 학습

- 트랜잭션이 왜 "같이 성공하고 같이 실패하는 write 단위"인지 다시 잡으려면 [트랜잭션 기초](./transaction-basics.md)를 본다.
- 현재 상태 row와 이력 테이블을 함께 두는 감각을 더 익히려면 [baseball 추측 기록/현재 게임 상태 ↔ DB 트랜잭션 브릿지](./baseball-guess-history-current-state-transaction-bridge.md)를 비교해서 읽는다.
- 웹에서 게임 상태를 Bean 필드에 두면 왜 또 다른 문제가 생기는지 보려면 [blackjack 게임 진행 상태 보관 ↔ Spring singleton Bean 상태 경계 브릿지](../spring/blackjack-game-state-singleton-bean-scope-bridge.md)로 이어간다.
- 점수 계산 규칙 자체의 책임 경계가 헷갈리면 [blackjack Ace 점수 계산 ↔ 도메인 불변식 브릿지](../software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md)를 같이 본다.
