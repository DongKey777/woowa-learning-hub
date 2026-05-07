---
schema_version: 3
title: baseball 긴 if 문 비대화 원인 라우터
concept_id: design-pattern/baseball-big-if-responsibility-cause-router
canonical: false
category: design-pattern
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/baseball
review_feedback_tags:
- mixed-responsibility-big-if
- guess-service-state-policy-routing
- baseball-pattern-boundary-confusion
aliases:
- baseball 긴 if 문 원인
- 야구 미션 책임 분리 라우터
- baseball 분기 로직 어디서 쪼개
- 야구 미션 패턴 경계 혼란
- baseball 설계 리뷰 원인 찾기
symptoms:
- baseball 미션 코드에서 if 문이 계속 길어져요
- Guess 검증, 턴 처리, 재시작 분기, 판정 로직이 한 메서드에 다 붙어 있어요
- 리뷰에서 값 객체, service, 상태 패턴, policy object 얘기가 같이 나와서 어디부터 봐야 할지 모르겠어요
- controller 하나가 입력 파싱부터 게임 종료까지 다 들고 있어서 고칠 순서를 못 잡겠어요
intents:
- symptom
- troubleshooting
- mission_bridge
- design
prerequisites:
- software-engineering/baseball-guess-vo-vs-service-flow-vs-state-transition-decision-guide
next_docs:
- software-engineering/baseball-guess-value-object-boundary-bridge
- software-engineering/baseball-turn-processing-service-layer-bridge
- design-pattern/baseball-restart-flow-state-pattern-bridge
- design-pattern/baseball-strike-ball-judging-policy-object-bridge
linked_paths:
- contents/software-engineering/baseball-guess-vo-vs-service-flow-vs-state-transition-decision-guide.md
- contents/software-engineering/baseball-guess-value-object-boundary-bridge.md
- contents/software-engineering/baseball-turn-processing-service-layer-bridge.md
- contents/design-pattern/baseball-restart-flow-state-pattern-bridge.md
- contents/design-pattern/baseball-strike-ball-judging-policy-object-bridge.md
confusable_with:
- software-engineering/baseball-guess-vo-vs-service-flow-vs-state-transition-decision-guide
- software-engineering/baseball-turn-processing-service-layer-bridge
- design-pattern/baseball-restart-flow-state-pattern-bridge
- design-pattern/baseball-strike-ball-judging-policy-object-bridge
forbidden_neighbors: []
expected_queries:
- 야구 미션에서 긴 if 문이 생겼을 때 이게 입력 규칙 문제인지 턴 흐름 문제인지 어떻게 구분해?
- baseball 리뷰에서 값 객체로 빼라, service로 옮겨라, 상태 패턴 보라가 한꺼번에 나오면 무엇부터 판단해야 해?
- controller가 문자열 파싱, 게임 판정, 재시작 분기를 다 들고 있으면 어떤 축으로 쪼개야 해?
- 야구 미션에서 strike ball 계산이 커질 때 상태 패턴이 아니라 다른 문서를 봐야 하는 기준이 뭐야?
- baseball 코드 비대화가 단순 리팩터링 문제가 아니라 책임 섞임인지 빠르게 진단하는 방법이 있어?
contextual_chunk_prefix: |
  이 문서는 Woowa baseball 미션에서 긴 if 문 하나에 입력 검증, 한 턴 실행
  순서, 재시작 단계 전이, strike ball 판정 규칙이 섞여 보일 때 원인을 갈라
  주는 symptom_router다. baseball 긴 if 문, 값 객체와 service와 상태 패턴과
  policy object가 한꺼번에 리뷰에 등장함, controller가 모든 분기를 들고 있음,
  무엇부터 쪼개야 할지 모르겠음 같은 학습자 표현을 책임 축별 다음 문서로
  라우팅한다.
---

# baseball 긴 if 문 비대화 원인 라우터

## 한 줄 요약

> baseball의 긴 `if` 문은 보통 "조건이 많아서"보다 입력 규칙, 턴 orchestration, 단계 전이, 판정 규칙이 한 메서드에 눌어붙었기 때문에 커진다.

## 가능한 원인

1. **입력 규칙과 도메인 값 생성이 안 잠겼다.** `123` 문자열을 읽은 뒤 중복 검사, 자리수 검사, 숫자 범위 검사를 여러 메서드에서 다시 하면 `if` 문이 입력 방어 코드로 부푼다. 이 갈래는 [baseball 3자리 추측 입력을 String으로 흘리지 않고 Guess 값 객체로 가두는 이유](../software-engineering/baseball-guess-value-object-boundary-bridge.md)로 이어서 "어디서부터 이 값을 신뢰할까"를 먼저 본다.
2. **한 턴 실행 순서를 controller가 직접 조립한다.** 입력 파싱 뒤 `Guess` 생성, 게임 판정 호출, 응답 메시지 조합까지 한 메서드에 있으면 분기 하나가 늘 때마다 유스케이스 흐름도 같이 옆으로 번진다. 이 경우는 [baseball 한 턴 처리 흐름 ↔ Service 계층 브릿지](../software-engineering/baseball-turn-processing-service-layer-bridge.md)로 가서 한 번의 추측 처리 순서를 별도 service로 읽는다.
3. **재시작과 종료가 값 검증이 아니라 단계 전이 문제인데도 같은 `if` 사슬에 있다.** `3스트라이크` 뒤에는 더 이상 숫자 추측을 받지 말아야 하는데, 여전히 같은 메서드가 "`숫자 입력인가 1/2 명령인가`"를 모두 판단하면 단계별 허용 행동이 흐려진다. 이 신호는 [baseball 재시작 입력/게임 종료 흐름 ↔ 상태 패턴 브릿지](./baseball-restart-flow-state-pattern-bridge.md)로 보낸다.
4. **strike/ball 계산 규칙이 흐름 분기와 섞였다.** 정답과 추측 비교 규칙이 길어질 때 상태 패턴까지 가기보다 "`어떤 규칙으로 결과를 만들까`"가 핵심일 수 있다. 이때는 [baseball 스트라이크/볼 판정 ↔ Policy Object 브릿지](./baseball-strike-ball-judging-policy-object-bridge.md)로 이어서 판정 규칙 축을 먼저 분리한다.

## 빠른 자기 진단

1. 같은 자리수 검사나 중복 검사가 여러 메서드에 반복되면 Guess 값 객체 갈래가 먼저다.
2. `playRound`, `processGuess`, `response` 조립이 controller 안에 같이 있으면 service orchestration 갈래를 본다.
3. `won`, `restart`, `finished` 같은 boolean 조합으로 "지금 무엇을 입력받는가"를 계속 따지면 상태 전이 문제다.
4. 입력 단계는 단순한데 strike/ball 계산 `if` 만 유독 길다면 policy object 갈래가 더 가깝다.
5. 위 네 축이 둘 이상 동시에 보이면 먼저 [baseball Guess 값 객체 vs 턴 처리 service vs 상태 전이 결정 가이드](../software-engineering/baseball-guess-vo-vs-service-flow-vs-state-transition-decision-guide.md)로 전체 축을 정리한 뒤, 가장 아픈 갈래 하나만 고른다.

## 다음 학습

- 입력 문자열을 도메인 값으로 빨리 잠그는 이유는 [baseball 3자리 추측 입력을 String으로 흘리지 않고 Guess 값 객체로 가두는 이유](../software-engineering/baseball-guess-value-object-boundary-bridge.md)에서 본다.
- 한 번의 추측 요청 순서를 controller 밖으로 옮기는 기준은 [baseball 한 턴 처리 흐름 ↔ Service 계층 브릿지](../software-engineering/baseball-turn-processing-service-layer-bridge.md)로 잇는다.
- 재시작/종료 단계가 왜 별도 상태 문제인지 보려면 [baseball 재시작 입력/게임 종료 흐름 ↔ 상태 패턴 브릿지](./baseball-restart-flow-state-pattern-bridge.md)를 본다.
- 판정 규칙이 길어질 때 어떤 객체로 분리할지 보려면 [baseball 스트라이크/볼 판정 ↔ Policy Object 브릿지](./baseball-strike-ball-judging-policy-object-bridge.md)를 이어서 읽는다.
