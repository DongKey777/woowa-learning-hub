---
schema_version: 3
title: 'baseball 현재 게임 조회/저장 ↔ Repository 경계 브릿지'
concept_id: software-engineering/baseball-current-game-load-save-repository-bridge
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/baseball
review_feedback_tags:
- game-repository-boundary
- load-modify-save-usecase
- persistence-contract-separation
aliases:
- baseball 현재 게임 repository
- 야구 미션 game 조회 저장 경계
- baseball load save 흐름
- 야구 미션 gameRepository 계약
- gameId로 게임 다시 읽기
symptoms:
- controller가 Map이나 세션에서 게임을 직접 꺼내 수정하고 다시 넣고 있어요
- 추측 한 번 처리할 때 어느 계층이 게임을 조회하고 저장해야 할지 헷갈려요
- gameId는 있는데 현재 게임을 다시 읽는 계약이 코드에 안 보여요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/repository-interface-contract
- software-engineering/baseball-turn-processing-service-layer-bridge
- spring/baseball-game-id-session-boundary-bridge
next_docs:
- software-engineering/repository-interface-contract
- database/baseball-guess-history-current-state-transaction-bridge
- spring/baseball-game-id-session-boundary-bridge
linked_paths:
- contents/software-engineering/repository-interface-contract-primer.md
- contents/software-engineering/baseball-turn-processing-service-layer-bridge.md
- contents/spring/baseball-game-id-session-boundary-bridge.md
- contents/database/baseball-guess-history-current-state-transaction-bridge.md
- contents/database/baseball-current-game-state-lost-update-version-cas-bridge.md
confusable_with:
- software-engineering/repository-interface-contract
- software-engineering/baseball-turn-processing-service-layer-bridge
- database/baseball-guess-history-current-state-transaction-bridge
forbidden_neighbors: []
expected_queries:
- 야구 미션 웹 버전에서 현재 게임을 어디서 읽고 어디서 저장해야 하는지 감이 안 와
- baseball에서 controller가 Map 저장소를 직접 만지지 말라는 리뷰는 무슨 뜻이야?
- guess 요청 한 번 처리할 때 game 조회 수정 저장 순서를 repository 관점에서 어떻게 봐야 해?
- session에 게임을 넣어도 repository 계약을 따로 두라는 이유가 뭐야?
- gameId로 찾은 현재 게임과 DB row 변환 책임을 어느 계층에 둬야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa baseball 미션을 콘솔 메모리 모델에서 웹과 저장소 모델로
  옮길 때 현재 게임을 어디서 조회하고 어디서 저장할지 설명하는 mission_bridge다.
  controller가 Map이나 session에서 Game을 직접 꺼내 수정함, guess 한 번 처리 시
  load-modify-save 순서가 흩어짐, gameId로 찾은 현재 게임과 저장 모델 경계가
  흐림, repository 계약 없이 service와 controller가 저장 세부를 아는 상태 같은
  학습자 표현을 baseball 유스케이스와 Repository 경계로 연결한다.
---

# baseball 현재 게임 조회/저장 ↔ Repository 경계 브릿지

## 한 줄 요약

> baseball에서 추측 한 번은 "`어느 게임을 다시 읽어 와서 규칙을 적용하고 다음 요청을 위해 보관하는가`"까지 포함한 유스케이스다. 이 경계가 controller나 session 코드에 흩어지면 Repository가 맡아야 할 저장 계약이 흐려진다.

## 미션 시나리오

콘솔 baseball에서는 `Game` 객체 하나를 계속 들고 가면 되니 조회와 저장이 거의
보이지 않는다. 하지만 웹으로 옮기면 `gameId`로 현재 게임을 다시 찾고, 추측을
적용한 뒤, 바뀐 상태를 다음 요청에서도 읽을 수 있게 보관해야 한다.

이때 자주 나오는 초기 구조는 controller가 `Map<Long, Game>`이나 session에서
직접 게임을 꺼내 `guess()`를 호출하고 다시 넣는 방식이다. 혼자 구현할 때는
빨라 보이지만 곧 "`조회는 여기, 저장은 저기, 응답 조립은 또 다른 곳`"이 되며
한 턴의 load-modify-save 순서가 여러 계층에 흩어진다.

## CS concept 매핑

이 장면에서 닿는 개념은 Repository를 "`DB 접근 클래스`"보다 "`현재 게임을
찾고 다시 보관하는 계약`"으로 읽는 감각이다. Service는
`gameRepository.find(gameId)`로 현재 게임을 가져와 도메인 규칙을 실행하고,
저장 기술이 메모리 Map이든 DB든 다시 `save`하는 약속만 믿는 편이 경계가 선다.

중요한 점은 Repository가 규칙을 대신 수행하지 않는다는 것이다. strike/ball
판정이나 종료 여부는 여전히 `Game`이 맡고, Service는 추측 1회의 순서를
조립한다. Repository는 그 사이에서 "`지금 진행 중인 game aggregate를 어떻게
다시 읽고 보관할 것인가`"를 캡슐화한다.

## 미션 PR 코멘트 패턴

- "`Controller`가 `Map` 조회와 갱신까지 직접 하면 유스케이스와 저장 계약이 같이 샙니다.`"라는 코멘트는 Repository 경계가 약하다는 뜻이다.
- "`gameId`로 게임을 찾는 책임과 추측 규칙을 적용하는 책임을 같은 메서드에 섞지 마세요.`"라는 리뷰는 Service와 Repository를 분리하라는 신호다.
- "`Session`에 객체를 넣더라도 application은 `현재 게임을 읽는다/저장한다`는 계약만 알면 됩니다.`"라는 피드백은 저장 기술 세부를 숨기라는 뜻이다.
- "`JPA Entity`나 `Map` 구조가 Service 시그니처까지 올라오면 저장 모델이 도메인 경계를 오염시킵니다.`"라는 코멘트는 변환 책임을 adapter 쪽으로 내리라는 말이다.

## 다음 학습

- Repository 자체를 왜 계약으로 읽는지 다시 잡으려면 `software-engineering/repository-interface-contract`
- 한 턴의 orchestration을 Service가 왜 쥐어야 하는지 보려면 `software-engineering/baseball-turn-processing-service-layer-bridge`
- `gameId`를 다음 요청까지 어떻게 이어 가는지 먼저 헷갈리면 `spring/baseball-game-id-session-boundary-bridge`
- 조회/저장 계약 뒤에서 이력 append와 현재 상태 snapshot을 어떤 write 단위로 묶을지 보려면 `database/baseball-guess-history-current-state-transaction-bridge`
