---
schema_version: 3
title: blackjack 테스트가 자꾸 흔들려요 원인 라우터
concept_id: software-engineering/blackjack-testability-cause-router
canonical: false
category: software-engineering
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/blackjack
review_feedback_tags:
- testability-boundary
- rule-scatter
- state-transition-hidden
aliases:
- blackjack 테스트 흔들림
- 블랙잭 테스트가 자꾸 깨져요
- blackjack 테스트 어디서부터 쪼개
- 블랙잭 테스트 어려움 원인
- blackjack testability
symptoms:
- blackjack 테스트를 하나 추가하면 다른 테스트가 같이 깨져요
- 점수 계산 테스트를 하려는데 입력 처리나 턴 흐름까지 같이 끌려와요
- 리뷰에서 테스트하기 어려운 구조라고 했는데 정확히 뭐가 엉킨 건지 모르겠어요
- hit stand 시나리오를 검증하려면 너무 많은 객체를 같이 세팅해야 해요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- software-engineering/blackjack-big-if-responsibility-cause-router
next_docs:
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/blackjack-action-input-command-bridge
- design-pattern/blackjack-winner-decision-policy-object-bridge
linked_paths:
- contents/software-engineering/blackjack-big-if-responsibility-cause-router.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/blackjack-action-input-command-bridge.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
confusable_with:
- software-engineering/blackjack-big-if-responsibility-cause-router
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
forbidden_neighbors:
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/blackjack-action-input-command-bridge.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
expected_queries:
- 블랙잭 미션 테스트를 하나 추가할 때마다 다른 테스트가 깨지면 무엇이 섞인 거야?
- blackjack에서 점수 계산만 검증하고 싶은데 입력 처리와 턴 흐름까지 같이 따라오는 이유가 뭐야?
- 블랙잭 코드가 테스트하기 어렵다는 리뷰는 보통 어떤 책임 경계가 없다는 뜻이야?
- hit stand 시나리오 테스트를 쓰려면 준비 코드가 너무 많은데 어디부터 분리해야 해?
- 블랙잭에서 규칙 테스트와 흐름 테스트가 서로 발목 잡을 때 먼저 어떤 문서로 가야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 테스트를 하나 추가할 때마다 다른 테스트가
  함께 흔들리고, 점수 계산만 보려 해도 입력 처리와 턴 흐름과 승패 판정이 같이
  따라오는 증상을 가르는 symptom_router다. 블랙잭 테스트 준비 코드가 너무 많음,
  hit stand 시나리오 검증이 어려움, 규칙 테스트와 흐름 테스트가 서로 엉킴,
  테스트하기 어려운 구조라는 리뷰 같은 학습자 표현을 값 규칙 분산, 상태 전이
  은닉, 입력 해석 결합, 결과 판정 결합 갈래로 라우팅한다.
---

# blackjack 테스트가 자꾸 흔들려요 원인 라우터

## 한 줄 요약

> blackjack 테스트가 자꾸 같이 깨지는 이유는 대개 테스트 기술이 부족해서가 아니라, 점수 규칙, 턴 전이, 입력 해석, 승패 판정이 서로 독립적으로 검증될 경계가 아직 없기 때문이다.

## 가능한 원인

1. **점수 규칙이 여러 곳에 흩어져 있다.** Ace 계산과 `bust` 판정이 `Hand`, `Service`, `OutputView`에 나뉘어 있으면 점수 테스트 하나가 출력 포맷이나 흐름 세팅까지 끌고 온다. 이 갈래는 [blackjack Ace 점수 계산 ↔ 도메인 불변식 브릿지](./blackjack-ace-scoring-domain-invariant-bridge.md)로 가서 값 규칙을 한 객체의 진실로 닫는다.
2. **턴 진행이 boolean 조합에 숨어 있다.** `dealerTurn`, `finished`, `playerTurn` 같은 값을 매번 조합해 판단하면, `hit` 한 번 테스트하려고도 전체 라운드 상태를 전부 세팅해야 한다. 이 경우는 [blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지](../design-pattern/blackjack-turn-flow-state-pattern-bridge.md)로 이어서 허용 행동을 상태 이름으로 드러낸다.
3. **입력 해석과 도메인 실행이 붙어 있다.** `"H"`나 `"stand"` 문자열 분기가 카드 추가와 즉시 연결되면, 규칙 테스트가 입력 파싱 테스트와 분리되지 않는다. 이 갈래는 [blackjack 행동 선택 입력 ↔ Command 패턴 브릿지](../design-pattern/blackjack-action-input-command-bridge.md)로 가서 요청 해석과 실행 책임을 자른다.
4. **최종 승패 판정이 라운드 절차 안에 묻혀 있다.** `push`, `dealer bust`, `blackjack` 비교가 서비스 마지막 `if-else`에 붙어 있으면 결과 규칙 테스트를 하려면 전체 진행 시나리오를 재현해야 한다. 이때는 [blackjack 승패 판정 ↔ Policy Object 브릿지](../design-pattern/blackjack-winner-decision-policy-object-bridge.md)로 가서 판정 규칙을 별도로 세운다.

## 빠른 자기 진단

1. 점수 계산 테스트를 쓰려는데 `Controller`나 입력 문자열까지 같이 등장하면 값 규칙이 새고 있는지 먼저 본다.
2. `hit` 가능 여부 테스트마다 `dealerTurn=false`, `finished=false` 같은 세팅이 길어지면 상태 전이 경계가 흐린 쪽이 우선이다.
3. 테스트 이름이 "입력을 주면 점수도 변하고 턴도 넘어가고 승패도 나온다"처럼 한 번에 너무 많은 결과를 검증하면 입력 해석과 실행 책임이 붙어 있을 가능성이 크다.
4. 승패 비교 하나 검증하려고 전체 라운드를 끝까지 재현해야 하면 결과 판정 규칙이 절차 안에 숨어 있는지 의심한다.

## 다음 학습

- 전체 분기 비대화부터 먼저 갈라 보고 싶다면 [blackjack 긴 if 문 비대화 원인 라우터](./blackjack-big-if-responsibility-cause-router.md)를 본다.
- 점수 계산 테스트를 독립시키고 싶다면 [blackjack Ace 점수 계산 ↔ 도메인 불변식 브릿지](./blackjack-ace-scoring-domain-invariant-bridge.md)로 간다.
- `hit/stand/dealer turn` 테스트 준비가 과한 이유를 보려면 [blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지](../design-pattern/blackjack-turn-flow-state-pattern-bridge.md)를 잇는다.
- 입력 파싱이 도메인 규칙 테스트를 끌고 온다면 [blackjack 행동 선택 입력 ↔ Command 패턴 브릿지](../design-pattern/blackjack-action-input-command-bridge.md)를 본다.
- 라운드 종료 뒤 승패 비교만 따로 검증하고 싶다면 [blackjack 승패 판정 ↔ Policy Object 브릿지](../design-pattern/blackjack-winner-decision-policy-object-bridge.md)를 이어서 읽는다.
