---
schema_version: 3
title: 'blackjack 현재 게임 조회/저장 ↔ Repository 경계 브릿지'
concept_id: software-engineering/blackjack-current-game-load-save-repository-bridge
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
review_feedback_tags:
- game-repository-boundary
- load-modify-save-usecase
- persistence-contract-separation
aliases:
- blackjack 현재 게임 repository
- 블랙잭 game 조회 저장 경계
- blackjack load save 흐름
- 블랙잭 repository 책임
- 블랙잭 gameRepository 계약
symptoms:
- controller가 Map에서 게임을 직접 꺼내 수정하고 다시 넣고 있어요
- hit 한 번 처리할 때 어느 계층이 게임을 조회하고 저장해야 할지 헷갈려요
- 블랙잭 웹 전환 뒤 Game 객체와 저장 모델 경계가 흐려 보여요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/repository-interface-contract
- software-engineering/blackjack-turn-processing-service-layer-bridge
- spring/blackjack-game-id-session-boundary-bridge
next_docs:
- software-engineering/repository-interface-contract
- database/blackjack-action-history-current-state-transaction-bridge
- spring/blackjack-game-id-session-boundary-bridge
linked_paths:
- contents/software-engineering/repository-interface-contract-primer.md
- contents/software-engineering/blackjack-turn-processing-service-layer-bridge.md
- contents/spring/blackjack-game-id-session-boundary-bridge.md
- contents/database/blackjack-action-history-current-state-transaction-bridge.md
- contents/software-engineering/dto-vo-entity-basics.md
confusable_with:
- software-engineering/repository-interface-contract
- software-engineering/blackjack-turn-processing-service-layer-bridge
- database/blackjack-action-history-current-state-transaction-bridge
forbidden_neighbors: []
expected_queries:
- 블랙잭 웹 미션에서 현재 게임을 어디서 읽고 어디서 저장해야 하는지 감이 안 와
- blackjack에서 controller가 직접 Map 저장소를 만지지 말라는 리뷰는 무슨 뜻이야?
- hit 요청 한 번 처리할 때 game 조회 수정 저장 순서를 repository 관점에서 어떻게 봐야 해?
- 세션이나 메모리에서 게임을 찾더라도 repository 계약을 따로 두라는 이유가 뭐야?
- 블랙잭 미션에서 Game 객체와 DB row 사이 변환 책임을 어느 계층에 둬야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션을 콘솔 메모리 모델에서 웹과 저장소 모델로
  옮길 때 현재 게임을 어디서 조회하고 어디서 저장할지 설명하는 mission_bridge다.
  controller가 Map이나 session에서 Game을 직접 꺼내 수정함, hit 한 번 처리 시
  load-modify-save 순서가 흩어짐, gameId로 찾은 게임과 저장 모델 경계가 흐림,
  repository 계약 없이 service와 controller가 저장 세부를 아는 상태 같은
  학습자 표현을 blackjack 유스케이스와 Repository 경계로 연결한다.
---

# blackjack 현재 게임 조회/저장 ↔ Repository 경계 브릿지

## 한 줄 요약

> blackjack에서 `hit` 한 번은 "어느 게임을 읽어 와서 규칙을 적용하고 다시 보관하는가"까지 포함한 유스케이스다. 이 경계가 controller나 session 코드에 흩어지면 Repository가 맡아야 할 저장 계약이 흐려진다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "controller가 session Map에서 Game을 꺼내 수정하고 다시 넣고 있어요" | 저장 기술 세부와 유스케이스 흐름이 controller에 함께 있는 코드 | 현재 게임을 읽고 저장하는 계약을 Repository 경계로 감싼다 |
| "hit 한 번 처리할 때 조회와 저장은 어느 계층이 맡죠?" | `gameId` lookup, `Game.hit`, save가 여러 계층에 흩어진 흐름 | service가 load-modify-save 순서를 조립하고 repository는 저장 계약을 제공한다 |
| "메모리 Map이면 repository가 굳이 필요한가요?" | DB가 없다는 이유로 저장소 계약을 controller/service 시그니처에 노출한 구조 | 저장 기술이 Map이어도 application은 `find/save` 계약만 믿게 한다 |

## 미션 시나리오

콘솔 blackjack에서는 `Game` 객체 하나를 계속 들고 가면 되니 저장 경계가 거의
보이지 않는다. 하지만 웹으로 옮기면 `gameId`로 현재 게임을 다시 찾고,
`hit`나 `stand`를 적용한 뒤, 바뀐 상태를 다음 요청에서도 읽을 수 있게
보관해야 한다.

이때 자주 보이는 초기 구조는 controller가 `Map<Long, Game>`이나 session에서
직접 게임을 꺼내 수정하고 다시 넣는 형태다. 혼자 구현할 때는 빨라 보이지만,
곧 "`조회는 여기, 저장은 저기, 응답 조립은 또 다른 곳`"이 되면서 한 턴의
load-modify-save 순서가 여러 계층에 흩어진다.

## CS concept 매핑

이 장면에서 닿는 개념은 Repository를 "DB 접근 클래스"보다 "현재 게임을
찾고 보관하는 계약"으로 읽는 감각이다. Service는 `gameRepository.find(gameId)`
로 현재 게임을 가져와 도메인 규칙을 실행하고, 저장 기술이 메모리 Map이든 DB든
다시 `save`하는 약속만 믿는 편이 경계가 선다.

중요한 점은 Repository가 규칙을 대신 수행하지 않는다는 것이다. `hit` 가능
여부나 점수 계산은 여전히 `Game`이 맡고, Service는 한 턴의 순서를 조립한다.
Repository는 그 사이에서 "지금 진행 중인 게임 aggregate를 어떻게 다시 읽고
보관할 것인가"를 캡슐화한다.

그래서 리뷰에서 "`controller가 저장소 세부를 너무 많이 안다`", "`session에
객체를 넣더라도 repository 계약으로 감싸라`"는 말이 나온다. 핵심은 DB를
도입하라는 강요보다, 콘솔의 객체 참조 하나로 끝나던 흐름을 웹에서는 명시적인
조회/저장 계약으로 바꾸라는 뜻에 가깝다.

## 미션 PR 코멘트 패턴

- "`Controller`가 `Map` 조회와 갱신까지 직접 하면 유스케이스와 저장 계약이 같이 샙니다."라는 코멘트는 Repository 경계가 약하다는 뜻이다.
- "`gameId`로 게임을 찾는 책임과 `hit` 규칙을 적용하는 책임을 같은 메서드에 섞지 마세요."라는 리뷰는 Service와 Repository를 분리하라는 신호다.
- "`Session`에 객체를 넣더라도 application은 `현재 게임을 읽는다/저장한다`는 계약만 알면 됩니다."라는 피드백은 저장 기술 세부를 숨기라는 뜻이다.
- "`JPA Entity`나 `Map` 구조가 Service 시그니처까지 올라오면 저장 모델이 도메인 경계를 오염시킵니다."라는 코멘트는 변환 책임을 adapter 쪽으로 내리라는 말이다.

## 다음 학습

- Repository 자체를 왜 계약으로 읽는지 다시 잡으려면 [Repository Interface Contract Primer](./repository-interface-contract-primer.md)를 본다.
- 한 턴의 orchestration을 Service가 왜 쥐어야 하는지 보려면 [blackjack 한 턴 처리 흐름 ↔ Service 계층 브릿지](./blackjack-turn-processing-service-layer-bridge.md)를 잇는다.
- `gameId`를 다음 요청까지 어떻게 이어 가는지 먼저 헷갈리면 [blackjack 게임 식별자 전달 ↔ Spring 세션과 요청 상태 경계 브릿지](../spring/blackjack-game-id-session-boundary-bridge.md)로 간다.
- 조회/저장 계약 뒤에서 action history와 current state를 어떤 write 단위로 묶을지 보려면 [blackjack 행동 이력/현재 손패 상태 ↔ DB 트랜잭션 브릿지](../database/blackjack-action-history-current-state-transaction-bridge.md)를 이어서 본다.
