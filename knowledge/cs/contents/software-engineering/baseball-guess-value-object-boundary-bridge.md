---
schema_version: 3
title: 'baseball 3자리 추측 입력을 String으로 흘리지 않고 Guess 값 객체로 가두는 이유'
concept_id: software-engineering/baseball-guess-value-object-boundary-bridge
canonical: false
category: software-engineering
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/baseball
review_feedback_tags:
- primitive-obsession
- value-object-boundary
- string-parsing-leak
aliases:
- baseball Guess 값 객체
- 야구 미션 String 파싱 위치
- 3자리 숫자 Guess 객체
- 숫자 추측 value object
- baseball 원시값 집착
symptoms:
- 문자열을 service까지 그대로 넘기고 있어요
- 숫자 3개 검증이 controller와 domain에 둘 다 있어요
- split한 List<Integer>가 여기저기 돌아다녀요
intents:
- mission_bridge
- design
prerequisites:
- software-engineering/dto-vo-entity-basics
- software-engineering/domain-invariants-as-contracts
next_docs:
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
- software-engineering/domain-invariants-as-contracts
- software-engineering/dto-vo-entity-basics
linked_paths:
- contents/software-engineering/dto-vo-entity-basics.md
- contents/software-engineering/domain-invariants-as-contracts.md
- contents/software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md
confusable_with:
- software-engineering/dto-vo-entity-basics
- software-engineering/domain-invariants-as-contracts
forbidden_neighbors:
- contents/software-engineering/dto-vo-entity-basics.md
- contents/software-engineering/domain-invariants-as-contracts.md
expected_queries:
- 야구 미션에서 123 같은 입력을 String으로 계속 들고 가도 돼?
- Guess 같은 값 객체를 따로 만들라는 리뷰는 무슨 뜻이야?
- 3자리 중복 없는 숫자 규칙을 어디에 묶어야 해?
- split한 숫자 리스트를 service로 넘기지 말라는 이유가 뭐야?
- baseball에서 Guess 없이 List<Integer>만 넘기면 뭐가 깨져?
contextual_chunk_prefix: |
  이 문서는 Woowa baseball 미션에서 3자리 숫자 추측 입력을 String이나
  split 결과로 흘리지 않고 Guess 값 객체 경계로 잇는 mission_bridge다.
  문자열 그대로 넘김, 중복 없는 세 자리 검증이 여러 곳에 흩어짐,
  List<Integer>가 service까지 감, 이미 검증된 값인지 계속 불안함, Guess로
  의미를 잠그기 같은 학습자 표현을 값 객체와 도메인 불변식 감각으로 연결한다.
---

# baseball 3자리 추측 입력을 String으로 흘리지 않고 Guess 값 객체로 가두는 이유

## 한 줄 요약

> baseball 미션의 `123` 입력은 그냥 문자열이 아니라 "3자리, 중복 없음, 1-9" 규칙을 가진 도메인 값이다. 그래서 controller에서 한 번 읽은 뒤에는 `String`이나 `List<Integer>`보다 `Guess` 값 객체로 넘기는 편이 규칙 누수를 막기 쉽다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "문자열 `123`을 service까지 그대로 넘겨도 되나요?" | controller/service/domain이 모두 raw string이나 split list를 다루는 코드 | 입력 표현과 도메인 추측 값을 `Guess` 타입 경계로 나눈다 |
| "3자리·중복 없음 검증이 여러 계층에 있어요" | InputView, controller, game이 같은 숫자 규칙을 반복 확인하는 구조 | `Guess.from` 생성 시점에 도메인 불변식을 닫는다 |
| "split한 `List<Integer>`가 이미 검증됐는지 계속 불안해요" | 숫자 리스트가 의미 타입 없이 여러 메서드를 통과하는 구현 | 어디서부터 신뢰 가능한 값인지 타입으로 드러낸다 |

## 미션 시나리오

학습자가 자주 시작하는 코드는 이런 모양이다.

```java
String input = scanner.nextLine();
List<Integer> numbers = parse(input);
game.play(numbers);
```

처음에는 간단하지만 곧 문제가 생긴다. `parse`, `length == 3`, `중복 없음`, `1-9 범위` 검사가 `InputView`, `Controller`, `Service`에 나뉘어 중복된다. 재시작이나 힌트 기능을 붙일수록 "`이 숫자 리스트는 이미 검증된 거야?`"가 계속 따라온다. PR에서 "`원시값을 너무 멀리 보내지 말고 의미 있는 타입으로 묶어 보세요`"라는 코멘트가 나오는 지점이 여기다.

## CS concept 매핑

여기서 닿는 개념은 `값 객체 + 도메인 불변식`이다. `Guess`는 데이터 세 칸을 담는 컨테이너가 아니라, 생성 시점에 규칙을 잠그는 작은 계약이다.

```java
Guess guess = Guess.from(input);
game.play(guess);
```

이렇게 바꾸면 `Guess.from(...)`이 형식 파싱과 최소 검증을 모으고, `Game.play(guess)`는 이미 의미가 확정된 값을 받는다. 핵심은 "`문자열을 언제 숫자로 바꾸나`"보다 "`어디서부터 이 값을 신뢰해도 되나`"다. baseball의 `123`은 DTO도 Entity도 아니고, 한 번 만들어지면 규칙이 유지되어야 하는 값 객체에 가깝다.

## 미션 PR 코멘트 패턴

- "`split한 결과를 계속 넘기지 말고 타입으로 의도를 드러내세요`"
- "`검증이 여러 계층에 흩어져 있습니다. Guess가 자기 규칙을 들고 있게 해 보세요`"
- "`Service가 문자열 포맷까지 아는 건 경계가 흐린 신호예요`"

반대로 오해도 많다. `Guess`를 만들라는 말이 "`클래스를 늘리자`"는 뜻은 아니다. 리뷰 의도는 클래스 수보다 규칙의 소유권이다. 같은 규칙을 세 군데에서 반복하는 비용이 `Guess` 한 타입보다 커지기 시작하면 값 객체로 올릴 타이밍이다.

## 다음 학습

- 입력 검증과 도메인 규칙을 더 짧게 가르고 싶으면 `software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge`
- 값 객체, DTO, Entity 이름이 한꺼번에 헷갈리면 `software-engineering/dto-vo-entity-basics`
- "도메인이 자기 규칙을 계약처럼 지킨다"는 감각을 넓히려면 `software-engineering/domain-invariants-as-contracts`
