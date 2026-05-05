---
schema_version: 3
title: Factory vs Abstract Factory vs Builder
concept_id: design-pattern/factory-vs-abstract-factory-vs-builder
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- factory-family-vs-builder
- pattern-selection
- object-creation-boundary
aliases:
- factory vs abstract factory vs builder basics
- factory vs abstract factory vs builder beginner
- factory vs abstract factory vs builder intro
- design pattern basics
- beginner design pattern
- 처음 배우는데 factory vs abstract factory vs builder
- factory vs abstract factory vs builder 입문
- factory vs abstract factory vs builder 기초
- what is factory vs abstract factory vs builder
- how to factory vs abstract factory vs builder
symptoms:
- 팩토리랑 빌더 차이가 머리에 안 잡혀
- 제품군 생성이 뭔지 모르겠어
- factory라는 말이 다 같은 뜻처럼 보여
intents:
- comparison
- design
prerequisites:
- design-pattern/constructor-vs-static-factory-vs-factory-pattern
- design-pattern/builder-pattern-basics
next_docs:
- design-pattern/bridge-strategy-vs-factory-runtime-selection
- design-pattern/factory-misnaming-checklist
linked_paths:
- contents/design-pattern/factory.md
- contents/design-pattern/constructor-vs-static-factory-vs-factory-pattern.md
- contents/design-pattern/builder-pattern.md
- contents/design-pattern/factory-misnaming-checklist.md
- contents/design-pattern/bridge-strategy-vs-factory-runtime-selection.md
- contents/software-engineering/oop-design-basics.md
confusable_with:
- design-pattern/constructor-vs-static-factory-vs-factory-pattern
- design-pattern/bridge-strategy-vs-factory-runtime-selection
- design-pattern/record-vs-builder-request-model-chooser
forbidden_neighbors: []
expected_queries:
- abstract factory는 언제 나오고 builder는 언제 써?
- 관련 객체 묶음을 만드는 거랑 단계적 조립 차이를 설명해줘
- factory 계열 패턴을 한 번에 비교해서 보고 싶어
- 구현 선택이랑 객체 조립을 어떻게 구분하지
- 팩토리 하나로 충분한데 abstract factory가 필요한 순간이 뭐야
- builder와 factory를 같은 생성 패턴으로만 보면 왜 헷갈려?
contextual_chunk_prefix: |
  이 문서는 생성 패턴을 비교하는 학습자가 Factory, Abstract Factory, Builder 중 무엇을 골라야 하는지와 객체 하나의 생성, 서로 맞는 제품군 생성, 단계적 조립을 어떻게 구분하는지 결정한다. 관련 객체 묶음 만들기, 테마 계열 함께 생성, 생성 분기 숨기기, 옵션 많은 객체 조립, 구현 선택과 조립 구분 같은 자연어 paraphrase가 본 문서의 선택 기준에 매핑된다.
---
# Factory vs Abstract Factory vs Builder

> 한 줄 요약: Factory는 "무엇을 만들지"를 숨기고, Abstract Factory는 "서로 관련된 제품군"을 만들고, Builder는 "어떻게 조립할지"를 단계적으로 분리한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)


retrieval-anchor-keywords: factory vs abstract factory vs builder basics, factory vs abstract factory vs builder beginner, factory vs abstract factory vs builder intro, design pattern basics, beginner design pattern, 처음 배우는데 factory vs abstract factory vs builder, factory vs abstract factory vs builder 입문, factory vs abstract factory vs builder 기초, what is factory vs abstract factory vs builder, how to factory vs abstract factory vs builder
> 관련 문서:
> - [팩토리 (Factory)](./factory.md)
> - [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
> - [빌더 (Builder)](./builder-pattern.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)

---

## 핵심 개념

세 패턴은 모두 객체 생성을 다루지만 초점이 다르다.

- Factory: 생성 책임을 캡슐화한다
- Abstract Factory: 서로 맞물리는 객체 집합을 함께 만든다
- Builder: 복잡한 객체를 단계적으로 조립한다

이 차이를 모르고 쓰면, 생성 패턴을 전부 같은 것으로 오해하게 된다.

---

## 깊이 들어가기

### 1. Factory는 단일 객체 생성에 가깝다

Factory는 생성 로직을 숨긴다.

```java
public interface CardPayment {
    void pay(int amount);
}

public class CardPaymentFactory {
    public static CardPayment create(String type) {
        if ("kb".equals(type)) return new KbCardPayment();
        if ("hana".equals(type)) return new HanaCardPayment();
        throw new IllegalArgumentException("unknown type");
    }
}
```

생성 로직이 흩어지지 않는 게 장점이다.

### 2. Abstract Factory는 제품군을 묶는다

서로 호환되는 객체들을 한 묶음으로 만들어야 할 때 쓴다.

```java
public interface UIThemeFactory {
    Button createButton();
    Checkbox createCheckbox();
}

public class DarkThemeFactory implements UIThemeFactory {
    public Button createButton() { return new DarkButton(); }
    public Checkbox createCheckbox() { return new DarkCheckbox(); }
}
```

여기서는 버튼 하나를 만드는 문제가 아니라, 버튼과 체크박스가 **같은 테마 계열**이어야 한다는 문제가 중요하다.

### 3. Builder는 조립 과정을 드러낸다

Builder는 생성 규칙이 복잡할 때, 필수값과 선택값을 분리해 읽기 쉽게 만든다.

```java
Order order = Order.builder()
    .userId("u1")
    .itemId("i9")
    .quantity(2)
    .giftWrap(true)
    .build();
```

Factory가 "어떤 객체를 만들지"라면, Builder는 "어떻게 채울지"에 가깝다.

### 4. Abstract Factory와 Builder의 차이

| 항목 | Abstract Factory | Builder |
|------|------------------|---------|
| 초점 | 제품군 생성 | 객체 조립 |
| 결과물 | 서로 호환되는 여러 객체 | 하나의 복잡한 객체 |
| 질문 | 어떤 계열을 만들까 | 어떤 옵션을 넣을까 |

---

## 실전 시나리오

### 시나리오 1: DB 커넥션 생성

환경에 따라 MySQL, PostgreSQL, 테스트용 H2를 바꾸는 건 Factory 감각이다.

### 시나리오 2: UI 테마

버튼, 입력창, 체크박스가 모두 같은 스타일이어야 하면 Abstract Factory가 더 자연스럽다.

### 시나리오 3: 요청 DTO 또는 테스트 픽스처

필드가 많고 선택값이 많으면 Builder가 가장 읽기 쉽다.

---

## 코드로 보기

### Factory

```java
PaymentService service = PaymentFactory.create("card");
```

### Abstract Factory

```java
ThemeFactory factory = new DarkThemeFactory();
Button button = factory.createButton();
Checkbox checkbox = factory.createCheckbox();
```

### Builder

```java
Order order = Order.builder()
    .userId("u1")
    .itemId("i9")
    .quantity(2)
    .build();
```

---

## 트레이드오프

| 패턴 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Factory | 생성 책임을 숨긴다 | 제품군 관계는 표현하기 어렵다 | 생성 분기가 많을 때 |
| Abstract Factory | 호환되는 제품군을 묶는다 | 구조가 무거워진다 | 계열 일관성이 중요할 때 |
| Builder | 조립 순서와 옵션이 드러난다 | 생성 오버헤드가 있다 | 선택값이 많고 복잡할 때 |

판단 기준은 간단하다.

- 객체 하나를 어떻게 만들지 숨기면 Factory
- 여러 객체가 서로 호환돼야 하면 Abstract Factory
- 한 객체를 단계적으로 조립하면 Builder

---

## 꼬리질문

> Q: Abstract Factory와 Builder를 같이 쓸 수 있나요?
> 의도: 패턴을 서로 배타적으로만 보는지 확인한다.
> 핵심: 제품군 생성은 Abstract Factory, 개별 객체 조립은 Builder로 함께 쓸 수 있다.

> Q: Factory와 정적 팩토리 메서드는 같은가요?
> 의도: 용어와 구현을 혼동하는지 확인한다.
> 핵심: 정적 팩토리는 구현 방식이고, Factory는 역할과 패턴이다.

> Q: Builder가 항상 더 좋은가요?
> 의도: 과설계를 구분하는지 확인한다.
> 핵심: 객체가 단순하면 생성자나 정적 팩토리가 더 낫다.

---

## 한 줄 정리

Factory는 생성, Abstract Factory는 제품군 생성, Builder는 복잡한 객체 조립이다.
