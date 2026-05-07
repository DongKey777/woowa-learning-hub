---
schema_version: 3
title: 'baseball 컴퓨터 숫자 생성 ↔ 전략 객체와 Random 경계 브릿지'
concept_id: design-pattern/baseball-random-number-generator-strategy-bridge
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
- random-generator-seam
- strategy-test-double
- hidden-random-dependency
aliases:
- baseball 숫자 생성 전략
- 야구 미션 Random 분리
- 컴퓨터 숫자 생성기 주입
- baseball 테스트용 고정 숫자
- NumberGenerator 전략 객체
symptoms:
- Random이 Game 안에 박혀 있어서 테스트가 흔들려요
- 컴퓨터 숫자를 고정하고 싶은데 생성 로직을 바꿀 곳이 없어요
- controller나 service가 숫자 생성 책임까지 들고 있어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- design-pattern/strategy-pattern-basics
- software-engineering/baseball-guess-value-object-boundary-bridge
next_docs:
- design-pattern/strategy-vs-function-chooser
- software-engineering/baseball-guess-value-object-boundary-bridge
- software-engineering/test-strategy-basics
linked_paths:
- contents/design-pattern/strategy-pattern-basics.md
- contents/design-pattern/strategy-vs-function-chooser.md
- contents/software-engineering/baseball-guess-value-object-boundary-bridge.md
- contents/software-engineering/test-strategy-basics.md
confusable_with:
- design-pattern/strategy-vs-function-chooser
- software-engineering/baseball-guess-value-object-boundary-bridge
forbidden_neighbors:
- contents/software-engineering/baseball-guess-value-object-boundary-bridge.md
expected_queries:
- 야구 미션에서 컴퓨터 숫자 뽑는 로직을 Game 안에 두면 왜 테스트가 어려워져?
- baseball에서 Random 숫자를 고정하려면 어떤 구조로 바꾸면 돼?
- NumberGenerator 같은 인터페이스를 만들라는 리뷰는 무슨 뜻이야?
- 랜덤 생성 책임을 controller에서 빼라고 하는 이유가 뭐야?
- 야구 미션 비밀 숫자 생성이 전략 패턴 질문으로 이어지는 이유가 궁금해
contextual_chunk_prefix: |
  이 문서는 Woowa baseball 미션에서 컴퓨터 숫자 생성 책임을 Random 직접
  호출에서 분리해 NumberGenerator 같은 전략 객체로 연결하는 mission_bridge다.
  랜덤 의존성 숨김, 고정 숫자로 테스트하고 싶음, 생성 책임 분리, Game 안의
  Random 제거, 교체 가능한 생성 규칙, 전략 패턴 입문 같은 자연어
  paraphrase가 본 문서의 미션 맥락에 매핑된다.
---

# baseball 컴퓨터 숫자 생성 ↔ 전략 객체와 Random 경계 브릿지

## 한 줄 요약

> baseball 미션에서 컴퓨터 숫자 생성은 "그때그때 `Random`을 호출하는 편의 코드"보다 "교체 가능한 생성 규칙"으로 보는 편이 낫다. 그래야 게임 규칙과 랜덤 생성 책임이 분리되고, 테스트에서는 고정 숫자 생성기로 바로 바꿔 끼울 수 있다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "`Random`이 `Game` 안에 박혀 있어서 테스트가 흔들려요" | 비밀 숫자 생성과 게임 판정 규칙이 한 객체에 섞인 코드 | 랜덤 생성 책임을 교체 가능한 `NumberGenerator`로 분리한다 |
| "컴퓨터 숫자를 고정해서 테스트하고 싶은데 구조가 막혀 있어요" | 매 테스트마다 실제 랜덤 결과에 기대는 baseball 판정 테스트 | fixed generator test double을 꽂을 seam을 만든다 |
| "controller나 service가 숫자 생성까지 들고 있어요" | 입력 처리, 유스케이스 조립, 랜덤 생성이 한 계층에 섞인 구조 | 생성 전략은 협력 객체, service는 흐름 조립으로 나눈다 |

## 미션 시나리오

학습자가 처음 자주 쓰는 코드는 이런 모양이다.

```java
public class Game {
    public Result play(String input) {
        List<Integer> answer = pickRandomNumbers();
        ...
    }
}
```

처음엔 짧지만 곧 문제가 생긴다. 매 턴마다 랜덤 숫자를 어디서 만들지 흐려지고, 테스트는 "`123`일 때 strike 3이 나오는지"를 확인하고 싶은데 `Random` 때문에 결과가 흔들린다. PR에서 "`랜덤 의존성을 숨기지 말고 바깥으로 빼 보세요`", "`고정된 생성기를 넣어 테스트 가능하게 만드세요`"라는 코멘트가 붙는 지점이 여기다.

## CS concept 매핑

여기서 닿는 개념은 전략 패턴의 아주 작은 형태다. 핵심은 "게임이 숫자를 *어떻게* 만들지는 모르고, 숫자를 만들어 주는 역할만 안다"는 점이다.

```java
public interface NumberGenerator {
    Guess generate();
}
```

실행에서는 `RandomNumberGenerator`, 테스트에서는 `FixedNumberGenerator`를 넣으면 된다. 이때 `Game`은 "`랜덤을 쓴다`"가 아니라 "`숫자 생성 전략에 위임한다`"로 읽힌다. baseball의 질문은 거대한 패턴 도입보다, 숨은 `Random` 의존성을 드러내고 테스트 seam을 만드는 데 더 가깝다.

## 미션 PR 코멘트 패턴

- "`Game`이 규칙 판단과 숫자 생성까지 같이 들고 있어서 책임이 두 겹입니다."
- "`Random`을 직접 호출하면 테스트가 입력-출력 검증이 아니라 운에 기대게 됩니다."
- "`비밀 숫자 생성`은 교체 가능한 협력인데, 지금은 메서드 안에 숨어 있어 주입이 안 됩니다."
- "`고정 숫자 생성기` 하나만 있어도 테스트가 훨씬 짧아지는데 seam이 없습니다."
- "`전략 패턴`이라고 해서 클래스 수를 늘리자는 뜻이 아니라, 바뀌는 축인 생성 규칙을 분리하자는 뜻입니다."

## 다음 학습

- 전략 타입이 과한지, 작은 함수나 객체 하나로 충분한지 더 자르려면 `design-pattern/strategy-vs-function-chooser`
- 숫자 문자열을 `Guess` 값 객체로 묶는 이유까지 이어 보려면 `software-engineering/baseball-guess-value-object-boundary-bridge`
- 이 변경 뒤 첫 테스트를 unit으로 둘지 통합으로 둘지 정리하려면 `software-engineering/test-strategy-basics`
