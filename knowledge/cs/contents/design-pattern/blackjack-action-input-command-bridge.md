---
schema_version: 3
title: 'blackjack 행동 선택 입력 ↔ Command 패턴 브릿지'
concept_id: design-pattern/blackjack-action-input-command-bridge
canonical: false
category: design-pattern
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/blackjack
review_feedback_tags:
- input-command-object
- action-dispatch-branching
- controller-switch-sprawl
aliases:
- blackjack 커맨드 패턴
- 블랙잭 hit stand command
- 블랙잭 행동 입력 객체
- blackjack action command
- 블랙잭 switch 분기 제거
symptoms:
- hit stand 입력 분기가 controller switch 문에 계속 늘어나요
- H S 같은 입력 문자열을 service까지 그대로 넘기고 있어요
- 행동이 늘 때마다 if 문과 테스트가 같이 터져요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- design-pattern/command-pattern-basics
- design-pattern/command-vs-strategy-quick-bridge
next_docs:
- design-pattern/command-pattern-basics
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/blackjack-winner-decision-policy-object-bridge
linked_paths:
- contents/design-pattern/command-pattern-basics.md
- contents/design-pattern/command-vs-strategy-quick-bridge.md
- contents/design-pattern/blackjack-turn-flow-state-pattern-bridge.md
- contents/design-pattern/blackjack-winner-decision-policy-object-bridge.md
- contents/design-pattern/observer-vs-command-beginner-bridge.md
confusable_with:
- design-pattern/blackjack-turn-flow-state-pattern-bridge
- design-pattern/command-pattern-basics
- design-pattern/command-vs-strategy-quick-bridge
forbidden_neighbors:
- contents/design-pattern/command-pattern-basics.md
- contents/design-pattern/command-vs-strategy-quick-bridge.md
expected_queries:
- 블랙잭 미션에서 hit stand 입력을 switch 문으로만 처리하면 왜 점점 힘들어져?
- H S 같은 명령 문자열을 객체로 감싸라는 리뷰는 무슨 뜻이야?
- 블랙잭에서 플레이어 행동을 command로 보라는 말은 상태 패턴이랑 뭐가 달라?
- 콘솔 입력 한 줄이 서비스 메서드 분기로 바로 가는 구조를 어떻게 읽어야 해?
- 블랙잭 액션이 늘 때 controller if 문이 커지면 어떤 패턴을 떠올리면 돼?
contextual_chunk_prefix: |
  이 문서는 Woowa blackjack 미션에서 플레이어의 hit, stand 같은 행동 입력이
  controller나 game loop의 switch 문으로 불어나기 시작할 때 이를 Command
  패턴으로 읽는 mission_bridge다. H/S 입력 문자열, action dispatch,
  실행 요청 객체, controller 분기 비대화, 행동 추가 시 테스트 폭증 같은
  학습자 표현을 상태 전이나 승패 규칙이 아닌 실행 요청 모델링 관점으로 연결한다.
---

# blackjack 행동 선택 입력 ↔ Command 패턴 브릿지

## 한 줄 요약

> blackjack에서 `hit`, `stand` 같은 선택이 문자열 분기만으로 흘러다니기 시작하면, "지금 무엇을 실행하라는 요청인가"를 객체로 세우는 Command 패턴으로 읽는 편이 구조가 빨리 정리된다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "`H`, `S` 입력 문자열을 service까지 그대로 넘겨요" | 입력 token이 실행 의미로 바뀌지 못하고 여러 계층을 지나가는 코드 | 문자열 해석과 실행 요청 모델을 분리한다 |
| "hit/stand switch가 controller에 계속 커져요" | action 추가마다 controller 분기와 테스트가 함께 늘어나는 구조 | 선택과 실행 책임을 Command 객체로 나눌 수 있는지 본다 |
| "Command와 State가 둘 다 행동을 다루는 것 같아요" | 선택된 행동 실행과 현재 가능한 행동 판단을 같은 패턴으로 묶는 설계 | Command는 무엇을 실행할지, State는 지금 가능한지로 분리한다 |

## 미션 시나리오

blackjack 미션 초반에는 플레이어에게 `H` 또는 `S`를 입력받아 `if` 나 `switch`
한 번으로 처리해도 크게 불편하지 않다. 하지만 라운드가 커지면 입력 검증,
행동 실행, 메시지 출력, 다음 턴 이동이 한 메서드에 같이 붙기 시작한다.

이때 자주 보이는 구조가 "문자열을 읽고 `hit`면 카드 추가, `stand`면 종료,
그 외면 예외"를 컨트롤러나 game loop가 직접 다 아는 형태다. 여기에 dealer
자동 진행, 재입력, 테스트 더블이 얹히면 입력 하나 추가할 때마다 분기와
테스트 케이스가 함께 늘어난다.

리뷰에서 "`H`, `S`를 그대로 넘기지 말고 행동을 모델링해 보세요",
"실행 요청이 문자열 비교에 묻혀 있네요" 같은 코멘트가 나오는 이유가 여기다.
문제의 핵심은 점수 계산도, 턴 상태도 아니라 "어떤 행동을 실행하라는 요청인가"를
지금 구조가 이름으로 드러내지 못한다는 데 있다.

## CS concept 매핑

Command 패턴으로 읽으면 `hit`와 `stand`는 단순 문자가 아니라 실행 요청이다.
예를 들어 입력을 해석한 뒤 `commands.get(input).execute()`처럼 연결하면,
컨트롤러는 "어떤 커맨드를 고를까"까지만 알고 실제 카드 추가나 턴 종료는 각
행동 객체가 맡는다.

여기서 상태 패턴과의 경계가 중요하다. Command는 "무슨 행동을 실행할까"를
모델링하고, State는 "지금 그 행동이 가능한가"를 모델링한다. 그래서 `HitCommand`
가 존재하더라도, bust 이후에 그 커맨드를 막을지 허용할지는 상태 쪽 질문이다.
반대로 승패 판정은 요청 실행이 아니라 규칙 해석이므로 Policy Object 쪽에 더 가깝다.

짧게 정리하면 blackjack에서 입력 문자열을 행동 객체로 끌어올리는 순간,
controller 분기와 도메인 실행이 분리된다. 리뷰에서 "문자열 switch를 줄여 보라"는
말은 패턴 이름을 외우라는 뜻보다, 실행 요청을 명시적인 객체로 세워 테스트와
확장 지점을 분리하라는 뜻에 가깝다.

## 미션 PR 코멘트 패턴

- "`H`, `S` 같은 입력값을 service까지 그대로 전달하면 실행 의미가 타입으로 안 보입니다."라는 코멘트는 요청 모델링이 약하다는 뜻이다.
- "행동이 하나 늘 때마다 controller의 `switch`가 커진다면, 선택과 실행 책임을 갈라 보세요."라는 피드백은 Command 분리를 가리킨다.
- "`hit` 실행과 `stand` 실행 테스트가 입력 파싱 테스트와 섞여 있네요."라는 코멘트는 행동 객체와 입력 해석을 끊으라는 뜻이다.
- "지금 가능한 행동은 상태가 판단하고, 선택된 행동 실행은 별도 객체가 맡을 수 있습니다."라는 리뷰는 State와 Command를 함께 쓰라는 신호다.

## 다음 학습

- Command 자체의 큰 그림을 다시 잡으려면 [커맨드 패턴 기초](./command-pattern-basics.md)를 본다.
- `hit`와 `stand`가 지금 가능한 행동인지까지 함께 헷갈리면 [blackjack 카드 뽑기/정지 흐름 ↔ 상태 패턴 브릿지](./blackjack-turn-flow-state-pattern-bridge.md)로 이어서 본다.
- 결과 판정 규칙까지 같은 메서드에 섞였다면 [blackjack 승패 판정 ↔ Policy Object 브릿지](./blackjack-winner-decision-policy-object-bridge.md)를 같이 본다.
- 커맨드와 전략이 둘 다 `execute()`처럼 보여 혼동되면 [Command vs Strategy](./command-vs-strategy-quick-bridge.md)로 경계를 먼저 자른다.
