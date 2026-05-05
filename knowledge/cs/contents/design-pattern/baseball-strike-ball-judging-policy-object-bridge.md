---
schema_version: 3
title: 'baseball 스트라이크/볼 판정 ↔ Policy Object 브릿지'
concept_id: design-pattern/baseball-strike-ball-judging-policy-object-bridge
canonical: false
category: design-pattern
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/baseball
review_feedback_tags:
- strike-ball-rule-boundary
- umpire-policy-object
- judging-if-else-sprawl
aliases:
- baseball 스트라이크 볼 판정 객체
- 야구 미션 심판 객체 분리
- baseball umpire policy
- strike ball 계산 책임 분리
- baseball 판정 규칙 객체
symptoms:
- strike와 ball 계산 if 문이 Game 안에서 계속 길어져요
- 심판이나 referee 같은 객체를 만들라는 리뷰가 왜 나왔는지 모르겠어요
- 숫자 비교 규칙을 값 객체로 둘지 별도 판정 객체로 둘지 헷갈려요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- design-pattern/policy-object-pattern
- software-engineering/baseball-guess-value-object-boundary-bridge
- design-pattern/strategy-vs-state-vs-policy-object
next_docs:
- design-pattern/policy-object-pattern
- design-pattern/strategy-vs-state-vs-policy-object
- design-pattern/baseball-restart-flow-state-pattern-bridge
linked_paths:
- contents/design-pattern/policy-object-pattern.md
- contents/design-pattern/strategy-vs-state-vs-policy-object.md
- contents/design-pattern/baseball-restart-flow-state-pattern-bridge.md
- contents/software-engineering/baseball-guess-value-object-boundary-bridge.md
- contents/software-engineering/baseball-guess-vo-vs-service-flow-vs-state-transition-decision-guide.md
confusable_with:
- software-engineering/baseball-guess-value-object-boundary-bridge
- design-pattern/baseball-restart-flow-state-pattern-bridge
- design-pattern/policy-object-pattern
forbidden_neighbors:
- contents/design-pattern/baseball-restart-flow-state-pattern-bridge.md
expected_queries:
- 야구 미션에서 strike ball 계산을 Game 메서드에 다 두지 말라는 리뷰는 무슨 뜻이야?
- baseball에서 심판 객체나 Umpire 클래스를 만들면 뭐가 좋아져?
- 숫자 비교 규칙이 길어질 때 값 객체 말고 policy object를 떠올리는 기준이 뭐야?
- guess 두 개를 비교해서 스트라이크와 볼을 만드는 책임은 어디에 두는 게 읽기 쉬워?
- 야구 미션 판정 로직이 커질 때 상태 패턴 말고 다른 경계가 필요하다는 말이 궁금해
contextual_chunk_prefix: |
  이 문서는 Woowa baseball 미션에서 사용자 추측과 정답 숫자를 비교해
  스트라이크와 볼을 만드는 규칙이 Game 안의 긴 if 문으로 커질 때,
  이를 Umpire나 JudgingPolicy 같은 Policy Object로 분리해 읽는
  mission_bridge다. 심판 객체, strike ball 계산 책임, 비교 규칙 분리,
  값 객체와 판정 객체의 경계, 상태 전이가 아니라 규칙 판정이라는 리뷰 표현을
  baseball 미션의 숫자 비교 시나리오와 연결한다.
---

# baseball 스트라이크/볼 판정 ↔ Policy Object 브릿지

## 한 줄 요약

> baseball에서 `123`이 유효한 추측인지 확인하는 일과, 정답 `427`과 비교해 `1스트라이크 1볼`을 만드는 일은 다른 책임이다. 전자는 값 규칙이고 후자는 판정 규칙이라서, 비교 if 문이 커지면 `Umpire` 같은 Policy Object로 분리하는 편이 읽기 쉽다.

## 미션 시나리오

baseball 미션을 진행하면 초반에는 `Game` 안에서 정답 숫자와 추측 숫자를 바로 이중 반복문으로 비교하는 코드가 자주 나온다. 처음에는 짧지만, 곧 "`같은 위치면 strike`, "`다른 위치지만 포함되면 ball`, "`아무것도 없으면 nothing`"을 한 메서드가 모두 품게 된다. 여기에 결과 메시지 조립이나 승리 판정까지 붙으면 `play()`가 빠르게 비대해진다.

이때 리뷰에서 "`판정 규칙을 객체로 분리해 보세요`", "`심판 역할을 Game이 전부 들고 있네요`" 같은 코멘트가 나온다. 학습자는 자주 "`Guess`도 객체인데 또 클래스를 만들어야 하나?"라고 묻는다. 이 질문의 핵심은 클래스 수가 아니라, "입력 자체의 규칙"과 "두 값을 비교해 결과를 해석하는 규칙"을 같은 곳에 둘지 분리할지에 있다.

## CS concept 매핑

여기서 닿는 개념은 `Policy Object`다. `Guess`가 "중복 없는 세 자리 숫자"라는 값을 안전하게 만드는 객체라면, `Umpire`나 `JudgingPolicy`는 "두 `Guess`를 비교해 어떤 결과를 내릴까"를 결정하는 규칙 객체다. 즉 값 객체는 자기 내부 불변식을 지키고, 정책 객체는 여러 값을 입력으로 받아 판정 결과를 만든다.

baseball에 대입하면 `Game`은 턴을 진행시키고, `Umpire`는 `answer`와 `guess`를 받아 `Judgement`를 만든다. 이렇게 자르면 `Game`은 흐름을 읽기 쉬워지고, 판정 규칙은 "`중복 계산이 없는가`", "`ball과 strike가 동시에 세어지지 않는가`" 같은 기준으로 따로 테스트하기 좋아진다. 중요한 건 전략 선택이나 상태 전이보다, 현재 숫자 비교 규칙을 이름 있는 판정 객체로 드러내는 일이다.

## 미션 PR 코멘트 패턴

- "`Game`이 입력 검증, 판정, 결과 메시지까지 다 들고 있어서 역할이 겹칩니다. 심판 역할을 분리해 보세요."
- "`스트라이크/볼 계산 규칙`은 도메인 판정이라 서비스 절차보다 규칙 객체 이름으로 드러나는 편이 읽기 쉽습니다."
- "`Guess`는 값 자체를 지키는 타입이고, 두 `Guess`의 비교 결과는 다른 책임입니다."
- "`상태 패턴`이 필요한 문제는 단계 전이이고, 지금 긴 코드는 판정 규칙 쪽에 더 가깝습니다."

## 다음 학습

- Policy Object 자체를 더 일반화해서 보려면 `design-pattern/policy-object-pattern`
- 값 객체와 판정 객체 경계가 함께 헷갈리면 `software-engineering/baseball-guess-value-object-boundary-bridge`
- state, strategy, policy object를 한 번에 비교하려면 `design-pattern/strategy-vs-state-vs-policy-object`
- 재시작/종료 단계처럼 진짜 상태 전이 문제가 어디서 시작되는지 보려면 `design-pattern/baseball-restart-flow-state-pattern-bridge`
