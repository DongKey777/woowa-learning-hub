---
schema_version: 3
title: 'baseball Guess 값 객체 vs 턴 처리 service vs 상태 전이 결정 가이드'
concept_id: software-engineering/baseball-guess-vo-vs-service-flow-vs-state-transition-decision-guide
canonical: false
category: software-engineering
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
review_feedback_tags:
- boundary-choice-confusion
- guess-vo-vs-service-flow
- restart-state-transition
aliases:
- baseball 리뷰 경계 선택
- 야구 미션 Guess service state 구분
- baseball 값 객체 서비스 상태 패턴 차이
- 야구 미션 어디부터 쪼개야 해
- baseball 추측 처리 책임 분리
symptoms:
- Guess를 만들라는 말과 service로 빼라는 말과 상태 패턴 얘기가 한꺼번에 나와서 같은 말처럼 들려요
- baseball 리뷰에서 지금 고쳐야 할 축이 입력 규칙인지 턴 흐름인지 재시작 단계인지 헷갈려요
- 클래스는 늘었는데 왜 분리가 좋아졌는지 설명을 못 하겠어요
intents:
- comparison
- design
- mission_bridge
prerequisites:
- software-engineering/baseball-guess-value-object-boundary-bridge
- software-engineering/baseball-turn-processing-service-layer-bridge
- design-pattern/baseball-restart-flow-state-pattern-bridge
next_docs:
- software-engineering/baseball-guess-value-object-boundary-bridge
- software-engineering/baseball-turn-processing-service-layer-bridge
- design-pattern/baseball-restart-flow-state-pattern-bridge
linked_paths:
- contents/software-engineering/baseball-guess-value-object-boundary-bridge.md
- contents/software-engineering/baseball-turn-processing-service-layer-bridge.md
- contents/design-pattern/baseball-restart-flow-state-pattern-bridge.md
- contents/design-pattern/baseball-random-number-generator-strategy-bridge.md
confusable_with:
- software-engineering/baseball-guess-value-object-boundary-bridge
- software-engineering/baseball-turn-processing-service-layer-bridge
- design-pattern/baseball-restart-flow-state-pattern-bridge
forbidden_neighbors:
- contents/spring/baseball-game-state-singleton-bean-scope-bridge.md
expected_queries:
- 야구 미션 리뷰에서 Guess 객체로 빼라는 말과 service로 옮기라는 말은 어떻게 달라?
- baseball에서 3자리 검증, 한 턴 실행, 재시작 분기를 각각 어디에 두는 게 맞아?
- 상태 패턴이 필요한 문제인지 그냥 service 메서드 분리면 되는지 빨리 구분하고 싶어
- 야구 미션에서 지금 긴 if 문이 값 규칙 문제인지 흐름 조립 문제인지 판단 기준이 뭐야?
- Guess, Service, State 중 어디를 먼저 도입해야 코드가 덜 꼬일까?
contextual_chunk_prefix: |
  이 문서는 Woowa baseball 미션 리뷰에서 Guess 값 객체, 한 턴 처리 service
  orchestration, 재시작 단계 상태 전이가 한 번에 언급될 때 무엇이 입력 규칙
  경계이고 무엇이 유스케이스 순서이며 무엇이 단계 전이인지 가르는 chooser다.
  3자리 숫자 검증, 한 턴 실행 순서, 3스트라이크 뒤 재시작 명령, 긴 if 문을
  어디부터 자를지, 지금 필요한 추상화가 무엇인지 같은 자연어 paraphrase가
  본 문서의 경계 선택 기준에 매핑된다.
---

# baseball Guess 값 객체 vs 턴 처리 service vs 상태 전이 결정 가이드

## 한 줄 요약

> `123`이 유효한 입력인가를 묻는 순간은 Guess 값 객체, 한 번의 추측 요청을 어떤 순서로 끝낼지 묻는 순간은 service, 지금 허용된 입력 단계가 바뀌는가를 묻는 순간은 상태 전이로 자르면 된다.

## 결정 매트릭스

| 지금 코드가 답해야 하는 질문 | 먼저 볼 경계 | 왜 그쪽이 맞는가 |
|---|---|---|
| `123`이 3자리·중복 없음·1~9 규칙을 만족하는가? | Guess 값 객체 | 입력이 한 번 만들어진 뒤 계속 지켜야 하는 값 규칙이다. |
| 한 번의 추측에서 `입력 해석 -> 판정 -> 응답 조립`을 누가 순서대로 묶는가? | 턴 처리 service | 유스케이스 orchestration 문제라서 화면 입구보다 service가 더 잘 맞는다. |
| 3스트라이크 뒤 지금 숫자를 받아야 하나, 재시작 명령을 받아야 하나? | 상태 전이 | 허용 행동이 단계에 따라 달라지는 흐름 문제다. |
| `if` 문이 길지만 대부분 문자열 파싱과 중복 검사인가? | Guess 값 객체 | 흐름보다 입력 의미 잠그기가 먼저라 상태 패턴까지 갈 필요가 없다. |
| controller가 `while`, 재시작 분기, 결과 메시지까지 다 들고 있나? | service + 상태 전이 | 한 턴 조립과 단계 전이가 한 메서드에 섞였다는 신호다. |

## 흔한 오선택

Guess 값 객체로 풀어야 할 문제를 service 분리만으로 끝내는 경우:
학습자가 "`split`만 service로 옮겼는데 중복 검증이 여기저기 남아요"라고 말하면 값 규칙 소유권이 아직 안 잡힌 상태다. 이때는 메서드 위치보다 `Guess.from(...)` 같은 생성 경계가 먼저다.

service가 맡을 유스케이스 순서를 상태 패턴으로 과하게 올리는 경우:
"`GameState` enum은 생겼는데 한 턴 실행 순서는 여전히 controller에 있어요"라는 패턴이 자주 나온다. 추측 한 번을 끝내는 기본 순서가 아직 안 모였으면, 상태 객체보다 service orchestration부터 정리하는 편이 덜 과하다.

재시작/종료 단계를 단순 값 검증처럼 보는 경우:
"`1` 아니면 `2`만 검사하면 끝 아닌가요?"라는 말이 나오면 입력 형식과 단계 전이가 섞인 것이다. 문제의 핵심은 숫자 한 글자 검증이 아니라, 승리 뒤에는 더 이상 추측 입력이 허용되지 않는다는 상태 변화다.

## 다음 학습

- 입력 문자열을 왜 빨리 의미 있는 타입으로 가둬야 하는지 보려면 `software-engineering/baseball-guess-value-object-boundary-bridge`
- 한 턴 실행 순서를 controller 밖으로 빼는 이유를 보려면 `software-engineering/baseball-turn-processing-service-layer-bridge`
- 재시작/종료 분기가 왜 단계 전이 문제인지 보려면 `design-pattern/baseball-restart-flow-state-pattern-bridge`
- 랜덤 생성 책임까지 함께 헷갈리면 `design-pattern/baseball-random-number-generator-strategy-bridge`
