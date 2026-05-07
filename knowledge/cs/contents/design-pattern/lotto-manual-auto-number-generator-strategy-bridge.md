---
schema_version: 3
title: 'lotto 수동 입력/자동 생성 ↔ NumberGenerator 전략 브릿지'
concept_id: design-pattern/lotto-manual-auto-number-generator-strategy-bridge
canonical: false
category: design-pattern
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/lotto
review_feedback_tags:
- random-generator-seam
- manual-vs-auto-generation
- test-double-generator
aliases:
- lotto 번호 생성 전략
- 로또 자동 생성기 주입
- 수동 입력 자동 생성 분리
- LottoNumberGenerator
- lotto Random 분리
symptoms:
- 수동 번호와 자동 번호를 같은 생성자에 다 넣으니 분기가 커져요
- Random 호출이 Lotto 안에 숨어 있어서 테스트가 어려워요
- 자동 생성 로직을 바꾸고 싶은데 어디를 갈아끼워야 할지 모르겠어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- design-pattern/strategy-pattern-basics
- design-pattern/lotto-static-factory-bridge
next_docs:
- design-pattern/strategy-pattern-basics
- design-pattern/strategy-vs-function-chooser
- design-pattern/lotto-static-factory-bridge
linked_paths:
- contents/design-pattern/strategy-pattern-basics.md
- contents/design-pattern/strategy-vs-function-chooser.md
- contents/design-pattern/lotto-static-factory-bridge.md
- contents/software-engineering/lotto-purchase-flow-service-layer-bridge.md
confusable_with:
- design-pattern/lotto-static-factory-bridge
- design-pattern/strategy-vs-function-chooser
forbidden_neighbors:
- contents/design-pattern/lotto-static-factory-bridge.md
expected_queries:
- 로또 미션에서 자동 번호 생성기를 왜 따로 빼라고 해?
- Lotto.auto 안에서 Random을 바로 쓰면 뭐가 문제야?
- 수동 입력 로또와 자동 생성 로또를 같은 경로로 만들지 말라는 리뷰는 무슨 뜻이야?
- 테스트에서 고정 번호를 넣고 싶은데 로또 생성 구조를 어떻게 나눠야 해?
- 번호 생성 규칙을 바꿀 수 있게 만들라는 말이 전략 패턴이랑 어떻게 이어져?
contextual_chunk_prefix: |
  이 문서는 Woowa lotto 미션에서 수동 입력과 자동 번호 생성을 같은 생성 경로에
  섞지 않고, Random 의존성을 NumberGenerator 같은 전략 객체로 분리하는 이유를
  설명하는 mission_bridge다. 자동 번호 생성기, 고정 번호 테스트 더블, 수동/자동
  분리, Lotto.auto 내부 Random, 생성 책임 경계 같은 학습자 표현을 전략 객체와
  생성 경로 분리 설명으로 연결한다.
---

# lotto 수동 입력/자동 생성 ↔ NumberGenerator 전략 브릿지

## 한 줄 요약

> lotto에서 중요한 분리는 "로또 한 장이 유효한가"와 "번호를 어떻게 만들어 오는가"다. 전자는 `Lotto.from(numbers)`가, 후자는 `NumberGenerator` 같은 전략 객체가 맡아야 수동 입력과 자동 생성이 덜 엉킨다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "`Lotto.auto()` 안에서 `Random`을 바로 써도 되나요?" | 자동 번호 생성 방식이 `Lotto` 값 객체 내부에 숨어 테스트가 흔들리는 코드 | 번호 유효성 검증과 번호 생성 전략을 분리한다 |
| "수동 번호와 자동 번호를 같은 생성자 분기로 처리해요" | `null`, flag, mode 값으로 수동/자동 경로를 한 생성자에 몰아넣은 구조 | 생성 경로 이름과 생성 규칙 교체 지점을 따로 본다 |
| "테스트에서 고정 번호를 넣으려면 어디를 열어야 하죠?" | 랜덤 생성기가 내부에 고정되어 시나리오 재현이 어려운 lotto 구매 테스트 | `NumberGenerator` 전략 객체를 주입 가능한 seam으로 만든다 |

## 미션 시나리오

lotto 미션을 하다 보면 당첨 번호나 수동 구매 번호는 사용자가 직접 넣고, 자동 구매는 `Random`으로 6개를 뽑아야 한다. 처음 구현에서는 `Lotto.auto()` 안에서 바로 `Random`을 돌리거나, 생성자에서 `numbers == null` 같은 분기로 수동/자동 경로를 함께 처리하기 쉽다.

이 구조는 금방 흔들린다. 번호 검증 객체가 생성 알고리즘까지 알게 되고, 테스트에서는 "항상 1,2,3,4,5,6을 만드는 경우"를 고정하기 어려워진다. PR에서 "`Random`을 숨기지 말고 바깥으로 빼세요", "수동 입력 경로와 자동 생성 경로를 같은 생성자 분기로 묶지 마세요"라는 코멘트가 붙는 자리가 여기다.

## CS concept 매핑

여기서 닿는 개념은 전략 패턴의 아주 작은 형태다. `Lotto`는 이미 만들어진 번호가 유효한지만 검사하고, 번호를 어떤 규칙으로 뽑을지는 협력 객체에 위임한다.

```java
public interface NumberGenerator {
    List<Integer> generate();
}
```

실행에서는 `RandomNumberGenerator`, 테스트에서는 `FixedNumberGenerator`를 넣을 수 있다. 그러면 `Lotto.from(generator.generate())`는 "번호 생성 전략이 만든 결과를 검증해 값 객체로 만든다"는 흐름으로 읽힌다. 정적 팩토리는 생성 경로의 이름을 드러내고, 전략 객체는 자동 생성 규칙의 교체 지점을 만든다. 둘은 경쟁 관계가 아니라 책임이 다른 두 층이다.

## 미션 PR 코멘트 패턴

- "`Lotto`가 번호 검증과 랜덤 생성까지 같이 들고 있어서 바뀌는 축이 두 개입니다."
- "`Random`이 메서드 안에 숨어 있으면 테스트에서 고정 번호를 넣을 seam이 없습니다."
- "`auto`와 `manual`을 같은 생성자 분기로 처리하면 생성 의도는 보이지만 생성 규칙 교체는 막힙니다."
- "지금 필요한 건 큰 패턴 도입보다 번호 생성 책임을 밖으로 빼는 작은 전략 분리입니다."

## 다음 학습

- 생성 경로 이름을 어떻게 드러낼지 더 보려면 `design-pattern/lotto-static-factory-bridge`
- 전략 타입이 꼭 필요한지, 함수 하나로 충분한지 비교하려면 `design-pattern/strategy-vs-function-chooser`
- 여러 장 구매 흐름에서 생성기 호출이 왜 Service 책임인지 이어 보려면 `software-engineering/lotto-purchase-flow-service-layer-bridge`
