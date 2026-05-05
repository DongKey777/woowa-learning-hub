---
schema_version: 3
title: blackjack 긴 if 문 비대화 원인 라우터
concept_id: software-engineering/blackjack-big-if-responsibility-cause-router
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
- mixed-responsibility-big-if
- command-state-policy-boundary
- score-rule-leak
aliases:
- blackjack 긴 if 문 원인
- 블랙잭 책임 분리 안 됨
- 블랙잭 서비스 분기 폭발
- blackjack 분기 로직 어디서 쪼개
- 블랙잭 패턴 코멘트 경계
symptoms:
- blackjack 서비스 if 문이 계속 길어져요
- hit stand 처리, 점수 계산, 승패 판정이 한 메서드에 다 붙어 있어요
- 리뷰에서 상태 패턴, 커맨드, 정책 객체 얘기가 같이 나와서 어디부터 고쳐야 할지 모르겠어요
- dealer 규칙과 bust 계산을 분리하라는 말이 추상적으로 들려요
intents:
- symptom
- troubleshooting
- mission_bridge
prerequisites:
- software-engineering/blackjack-ace-rule-vs-turn-state-vs-result-policy-decision-guide
next_docs:
- design-pattern/blackjack-action-input-command-bridge
- software-engineering/blackjack-ace-scoring-domain-invariant-bridge
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/blackjack-winner-decision-policy-object-bridge
linked_paths:
- contents/software-engineering/blackjack-ace-rule-vs-turn-state-vs-result-policy-decision-guide.md
- contents/design-pattern/blackjack-action-input-command-bridge.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
confusable_with:
- software-engineering/blackjack-ace-rule-vs-turn-state-vs-result-policy-decision-guide
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/blackjack-winner-decision-policy-object-bridge
forbidden_neighbors:
- contents/design-pattern/blackjack-action-input-command-bridge.md
- contents/software-engineering/blackjack-ace-scoring-domain-invariant-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
expected_queries:
- 블랙잭 미션 코드가 긴 if 문 하나인데 어떤 줄은 커맨드고 어떤 줄은 상태인지 어떻게 가려?
- 플레이어 입력 처리와 딜러 승패 비교가 한 메서드에 있을 때 먼저 어디부터 쪼개야 해?
- blackjack 리뷰에서 점수 규칙, 턴 흐름, 결과 판정을 분리하라는 말이 정확히 무슨 뜻이야?
- 딜러 16 규칙하고 bust 계산이 같이 있으면 어떤 책임 누수가 섞인 거야?
- 블랙잭에서 패턴 이름은 많이 들었는데 지금 코드 증상으로는 어느 문서부터 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 hit/stand 입력 처리, Ace 점수 계산,
  턴 상태 전이, dealer 추가 draw 규칙, 최종 승패 비교가 한 메서드의 긴 if
  문에 뭉쳐 보일 때 원인을 네 갈래로 나누는 symptom_router다. 블랙잭 서비스
  분기 폭발, 책임 분리 안 됨, 상태 패턴과 커맨드와 정책 객체가 한꺼번에
  리뷰에 등장함, dealer 규칙과 bust 계산 경계가 흐림 같은 학습자 표현을
  입력 해석 / 도메인 규칙 / 상태 전이 / 결과 판정 문서로 라우팅한다.
---

# blackjack 긴 if 문 비대화 원인 라우터

## 한 줄 요약

> blackjack의 긴 `if` 문은 대개 "조건이 많아서"가 아니라 입력 해석, 점수 규칙, 턴 전이, 승패 판정이 한 자리에 섞였기 때문에 커진다.

## 가능한 원인

1. **입력 해석과 행동 실행이 섞였다.** `H`, `S` 같은 문자열을 읽은 메서드가 바로 카드 추가나 턴 종료까지 수행하면, 분기 하나가 늘 때마다 입력 파싱과 도메인 실행이 함께 엉킨다. 이 갈래는 [blackjack 행동 선택 입력 ↔ Command 패턴 브릿지](../design-pattern/blackjack-action-input-command-bridge.md)로 가서 "무슨 요청을 실행할까"를 먼저 분리한다.
2. **손패 점수 규칙이 여러 층으로 새고 있다.** Ace를 1 또는 11로 해석하는 규칙, `bust` 여부, `blackjack` 여부가 `Controller`, `Service`, `OutputView`에 나뉘어 있으면 긴 분기 안에 값 계산이 계속 끼어든다. 이 경우는 [blackjack Ace 점수 계산 ↔ 도메인 불변식 브릿지](./blackjack-ace-scoring-domain-invariant-bridge.md)로 가서 점수 규칙을 한 객체의 진실로 닫는다.
3. **지금 가능한 행동을 상태가 아니라 boolean 조합으로 읽고 있다.** `dealerTurn`, `finished`, `bust` 같은 값 조합을 매번 확인하며 `hit/stand` 허용 여부를 정하면, 메서드가 사실상 상태 전이표를 직접 들고 있는 셈이다. 이 분기는 [blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지](../design-pattern/blackjack-turn-flow-state-pattern-bridge.md)로 보내서 "지금 어느 단계인가"를 먼저 세운다.
4. **딜러 추가 draw 규칙과 최종 승패 해석이 절차 안에 묻혀 있다.** `dealer.score() <= 16`, `push`, `player blackjack` 같은 판정이 같은 `if-else` 사슬에 달리면, 흐름 제어와 결과 규칙이 구분되지 않는다. 이 갈래는 [blackjack 승패 판정 ↔ Policy Object 브릿지](../design-pattern/blackjack-winner-decision-policy-object-bridge.md)로 이어서 판정 규칙을 별도 객체로 읽는다.

## 빠른 자기 진단

1. 메서드 첫 부분에 입력 문자열 비교가 많으면 먼저 Command 갈래를 의심한다. "`H`면 카드 뽑기, `S`면 종료"가 그대로 보이면 입력 해석과 실행이 한 덩어리다.
2. 같은 메서드 안에서 점수 합계, Ace 보정, `bust` 계산이 반복되면 도메인 규칙 누수다. 점수 계산을 다른 곳에서도 다시 한다면 상태보다 불변식 문서를 먼저 보는 편이 맞다.
3. `dealerTurn && !finished` 같은 조건 조합이 계속 보이면 상태 전이 문제다. "지금 이 객체가 어떤 행동을 허용하나"를 상태 이름으로 바꾸는 쪽이 우선이다.
4. 라운드 마지막에만 커다란 `if-else`가 남고 `push`, `dealer hit`, `winner` 비교가 몰려 있다면 Policy Object 갈래다. 흐름이 아니라 판정 규칙을 따로 세워야 읽힌다.

## 다음 학습

- 입력 문자열과 행동 실행의 경계를 먼저 자르려면 [blackjack 행동 선택 입력 ↔ Command 패턴 브릿지](../design-pattern/blackjack-action-input-command-bridge.md)를 본다.
- Ace 계산과 `bust` 판단이 여러 객체에 흩어졌다면 [blackjack Ace 점수 계산 ↔ 도메인 불변식 브릿지](./blackjack-ace-scoring-domain-invariant-bridge.md)로 간다.
- `hit/stand/dealer turn` 단계 자체가 헷갈리면 [blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지](../design-pattern/blackjack-turn-flow-state-pattern-bridge.md)를 잇는다.
- 딜러 16 규칙과 최종 승패 비교를 결과 판정으로 나눠 보고 싶다면 [blackjack 승패 판정 ↔ Policy Object 브릿지](../design-pattern/blackjack-winner-decision-policy-object-bridge.md)를 이어서 읽는다.
