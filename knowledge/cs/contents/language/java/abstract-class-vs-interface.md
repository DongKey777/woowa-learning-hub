---
schema_version: 3
title: 추상 클래스 vs 인터페이스
concept_id: language/abstract-class-vs-interface
canonical: false
category: language
difficulty: intermediate
doc_role: deep_dive
level: intermediate
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- abstract-class-vs-interface-choice
- inheritance-boundary-design
- default-method-overreach
aliases:
- abstract class interface deep dive
- abstract class interface primer first
- abstract class interface beginner route
- abstract class interface basics first
- abstract class interface when to use beginner
- 처음 배우는데 추상 클래스 인터페이스 차이
- 추상 클래스 인터페이스 큰 그림
- 추상 클래스 인터페이스 기초 먼저
- 추상 클래스 인터페이스 언제 쓰는지
- 추상 클래스 인터페이스 입문 먼저
- stateful base class
- contract evolution
- template method design boundary
- composition before template method beginner route
- abstract class vs interface basics
symptoms:
- 입문 기준은 알겠는데 실무 설계로 가면 추상 클래스와 인터페이스 경계가 다시 흐려져
- default method랑 sealed interface까지 섞이면 어느 축으로 판단해야 할지 모르겠어
- 상속 경계와 계약 경계를 같이 봐야 한다는데 무엇이 더 본질인지 헷갈려
intents:
- comparison
- design
prerequisites:
- language/java-abstract-class-vs-interface-basics
- language/interface-default-method-contract-evolution-primer
- language/object-oriented-core-principles
next_docs:
- language/interface-default-vs-static-method-primer
- language/abstract-class-vs-interface-follow-up-drill
- language/sealed-interfaces-exhaustive-switch-design
linked_paths:
- contents/language/java/java-abstract-class-vs-interface-basics.md
- contents/language/java/interface-default-method-contract-evolution-primer.md
- contents/language/java/interface-default-vs-static-method-primer.md
- contents/language/java/abstract-class-vs-interface-follow-up-drill.md
- contents/language/java/object-oriented-core-principles.md
- contents/language/java/sealed-interfaces-exhaustive-switch-design.md
- contents/language/java/records-sealed-pattern-matching.md
- contents/language/java/java-binary-compatibility-linkage-errors.md
- contents/language/java/java-module-system-runtime-boundaries.md
- contents/language/java/classloader-delegation-edge-cases.md
- contents/design-pattern/composition-over-inheritance-basics.md
- contents/design-pattern/template-method-basics.md
- contents/design-pattern/template-method-vs-strategy.md
confusable_with:
- language/java-abstract-class-vs-interface-basics
- language/interface-default-method-contract-evolution-primer
- language/sealed-interfaces-exhaustive-switch-design
forbidden_neighbors: []
expected_queries:
- 추상 클래스와 인터페이스를 기초 다음 단계에서 어떻게 다시 판단해야 하는지 설명해줘
- Java에서 상속 경계와 계약 경계를 같이 볼 때 어떤 기준으로 설계 결정을 내려야 해?
- default method와 sealed interface까지 포함해서 추상 클래스 인터페이스 차이를 깊게 보고 싶어
- 단순 비교표 말고 추상 클래스와 인터페이스의 확장성 차이를 중급 관점에서 정리한 문서가 필요해
- 템플릿 메서드, 조합, 인터페이스 계약을 한 축에서 비교해 주는 자바 문서가 있어?
contextual_chunk_prefix: |
  이 문서는 Java 학습자가 추상 클래스와 인터페이스를 문법 비교에서 끝내지
  않고 상태 공유, 부모가 쥔 실행 순서, 계약 확장, 조합으로의 피벗까지 함께
  깊이 잡는 deep_dive다. 공통 필드와 생성자를 부모에 둘지, 여러 타입에 같은
  역할만 붙일지, default method를 어디까지 허용할지, 템플릿 메서드 대신
  조합이 더 안전한지 같은 자연어 표현이 본 문서의 설계 판단 축에 매핑된다.
---
# 추상 클래스 vs 인터페이스

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: 추상 클래스와 인터페이스는 문법이 비슷해 보여도 상속 경로, 상태 보유, 확장성, 경계 제어에서 완전히 다른 설계 도구다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Language README](../README.md)
- [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) - 처음 배우는데 큰 그림과 "언제 쓰는지"부터 잡아야 하면 먼저 보는 beginner primer
- [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) - beginner handoff는 추상 클래스/인터페이스 다음에 조합을 먼저 고정할 때 보는 primer
- [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md) - 조합 기본값 뒤에도 부모가 흐름을 쥐는 경우를 좁혀 보는 follow-up primer
- [템플릿 메소드 vs 전략](../../design-pattern/template-method-vs-strategy.md) - 템플릿 메소드 다음에 상속 skeleton과 전략 주입을 같은 축으로 비교하는 follow-up primer
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [객체지향 핵심 원리](./object-oriented-core-principles.md)
- [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md) - 이 deep dive에서 `default method` 분기가 궁금해질 때 붙는 다음 primer
- [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)
- [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md)
- [Java Binary Compatibility and Runtime Linkage Errors](./java-binary-compatibility-linkage-errors.md)
- [Java Module System Runtime Boundaries](./java-module-system-runtime-boundaries.md)
- [ClassLoader Delegation Edge Cases](./classloader-delegation-edge-cases.md)

retrieval-anchor-keywords: abstract class interface deep dive, abstract class interface primer first, abstract class interface beginner route, abstract class interface basics first, abstract class interface when to use beginner, 처음 배우는데 추상 클래스 인터페이스 차이, 추상 클래스 인터페이스 큰 그림, 추상 클래스 인터페이스 기초 먼저, 추상 클래스 인터페이스 언제 쓰는지, 추상 클래스 인터페이스 입문 먼저, stateful base class, contract evolution, template method design boundary, composition before template method beginner route, abstract class vs interface basics

<details>
<summary>Table of Contents</summary>

- [왜 다시 생각해봐야 하나](#왜-다시-생각해봐야-하나)
- [처음 배우는 질문이면 여기부터](#처음-배우는-질문이면-여기부터)
- [추상 클래스](#추상-클래스)
- [인터페이스](#인터페이스)
- [차이점과 선택 기준](#차이점과-선택-기준)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 다시 생각해봐야 하나

처음 배우는 질문에서는 `추상 클래스는 공통 상태/흐름`, `인터페이스는 계약/역할`까지만 잡아도 충분하다. 이 문서는 그 다음 단계에서 "왜 같은 표를 봤는데 실전 선택은 더 어려워지는가"를 설명하는 long-form bridge다.

Java의 추상 클래스와 인터페이스는 오랫동안 기본 문법처럼 보였지만, 현대 Java에서는 record, sealed interface, default method, module boundary까지 같이 봐야 설계 판단이 더 정확해진다.

즉 이 주제는 단순 암기가 아니라 **어떤 경계를 타입이 책임질 것인가**를 묻는 문제다.

## 처음 배우는 질문이면 여기부터

처음 배우는데 `추상 클래스와 인터페이스 차이`, `언제 쓰는지`, `큰 그림`, `기초`를 찾는 상태라면 이 문서보다 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)을 먼저 보는 편이 맞다. 검색도 원래 이 primer가 먼저 잡히는 편이 맞고, 이 문서는 그 다음에 "예외와 경계"를 붙이는 역할이다.

이 문서는 입문 비교표를 다시 설명하는 문서가 아니라, 아래처럼 **입문 다음 단계의 설계 guardrail**을 정리한다.

| 지금 질문 | 먼저 볼 문서 | 이유 |
|---|---|---|
| "기초로 차이만 빨리 알고 싶다" | [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) | 공통 상태/흐름 vs 계약/조합을 먼저 잡아준다 |
| "`default method`가 인터페이스 본질인가?" | [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md) | 계약과 진화 전략을 같은 층위로 섞지 않게 해준다 |
| "sealed interface까지 같이 봐야 하나?" | [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md) | 타입 집합을 닫는 문제를 따로 분리해서 본다 |

짧게 말해, **입문 검색은 primer가 먹고 이 문서는 deep dive가 먹는 구조**가 맞다.

## 추상 클래스

추상 클래스는 상속받는 하위 클래스들이 공통 상태와 공통 구현을 공유하도록 돕는다.

### 특징

- 상태(field)를 가질 수 있다
- 생성자를 가질 수 있다
- 공통 동작을 기본 구현으로 제공할 수 있다
- 단일 상속 제약을 받는다

### 언제 잘 맞나

- 템플릿 메서드 패턴
- 공통 state와 behavior를 묶고 싶을 때
- 구현 세부를 상속 계층 안에 가두고 싶을 때

### runtime 관점

추상 클래스는 단순 코드 재사용이 아니라 호출 경로를 통제하는 수단이다.
공통 상태를 가진 base class는 JIT/GC 관점에서도 객체 layout과 initialization order에 영향을 줄 수 있다.

## 인터페이스

인터페이스는 구현 약속과 capability를 표현하는 데 적합하다.

### 특징

- 다중 구현 가능
- 상태를 거의 가지지 않는다
- default method로 일부 구현 가능
- 서로 다른 계층의 타입을 같은 계약으로 묶을 수 있다

### 언제 잘 맞나

- "무엇을 할 수 있는가"를 표현할 때
- 구현체를 갈아끼우고 싶을 때
- mocking/test double/플러그인 경계가 필요할 때

### modern Java 관점

인터페이스는 단순 추상 메서드 집합이 아니다.

- default method로 evolution을 할 수 있다
- sealed interface로 구현 집합을 닫을 수 있다
- module boundary와 함께 public contract를 명확하게 만들 수 있다

## 차이점과 선택 기준

### 사용 의도의 차이

- 추상 클래스: `is-a`와 공통 상태/구현
- 인터페이스: `can-do`와 계약/역할

### 공통 기능의 차이

공통 동작이 많고 상태를 공유해야 하면 추상 클래스가 유리하다.
계약만 필요하고 구현은 다양한 경우 인터페이스가 유리하다.

### 확장성의 차이

인터페이스는 다중 구현이 가능하므로 조합이 쉽다.
추상 클래스는 상속 계층이 깊어지면 coupling이 커진다.

### 실무 판단 기준

- 상태를 공유해야 하는가
- 구현을 강제할 것인가, 역할만 강제할 것인가
- 향후 구현체가 여러 개로 늘어날 가능성이 있는가
- API 안정성과 binary compatibility를 얼마나 중요하게 보는가

입문 단계에서는 여기서 멈춰도 충분하지만, 이 문서는 그 다음 질문인 "`default method` 추가가 기존 구현체와 바이너리 호환성에 어떤 영향을 주는가", "sealed interface로 구현 집합을 닫을 때 확장 경계를 어떻게 둘 것인가"까지 이어지는 판단을 다룬다.

## 실전 시나리오

### 시나리오 1: 상태와 동작을 같이 묶고 싶다

공통 필드와 기본 로직이 있다면 추상 클래스가 자연스럽다.

### 시나리오 2: 여러 구현체를 외부에 노출한다

인터페이스가 더 잘 맞는다.
특히 plugin, SPI, test double, mock이 필요할 때 그렇다.

### 시나리오 3: 타입 집합을 닫고 싶다

sealed interface가 더 현대적일 수 있다.
관련해서 [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md)를 같이 보면 좋다.

### 시나리오 4: 구현 변경이 잦다

인터페이스는 default method와 module boundary로 evolution 전략을 짤 수 있다.
추상 클래스는 public inheritance contract가 더 강하게 묶인다.

## 코드로 보기

### 1. 추상 클래스

```java
abstract class AbstractProcessor {
    protected final String name;

    protected AbstractProcessor(String name) {
        this.name = name;
    }

    public final void execute() {
        validate();
        doExecute();
    }

    protected abstract void doExecute();

    protected void validate() {
        // common validation
    }
}
```

### 2. 인터페이스

```java
interface Flyable {
    void fly();
}
```

### 3. default method

```java
interface Retryable {
    default int maxAttempts() {
        return 3;
    }
}
```

### 4. sealed interface와 연결

```java
public sealed interface PaymentResult permits Success, Failure {}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| 추상 클래스 | 공통 상태와 구현을 공유하기 쉽다 | 단일 상속이라 유연성이 떨어진다 |
| 인터페이스 | 다중 구현과 계약 설계에 좋다 | 공통 state 공유가 어렵다 |
| sealed interface | 구현 집합을 닫을 수 있다 | 확장 시 계약을 더 신중히 바꿔야 한다 |
| default method | evolution이 쉽다 | API가 점점 무거워질 수 있다 |

핵심은 추상 클래스와 인터페이스를 문법 선택이 아니라 inheritance boundary 설계로 보는 것이다.

## 꼬리질문

> Q: 추상 클래스는 언제 쓰나요?
> 핵심: 공통 상태와 공통 구현을 묶고 template method 같은 구조를 만들고 싶을 때다.

> Q: 인터페이스는 언제 쓰나요?
> 핵심: 구현체가 다양하고 역할/계약을 분리하고 싶을 때다.

> Q: sealed interface는 왜 유용한가요?
> 핵심: 타입 집합을 닫아 exhaustive handling을 돕기 때문이다.

> Q: default method는 왜 생겼나요?
> 핵심: 인터페이스를 깨지 않고 evolution할 수 있게 하려는 목적이 크다.

## 한 줄 정리

추상 클래스는 공통 상태와 구현의 경계, 인터페이스는 역할과 계약의 경계를 나타내며, 현대 Java에서는 sealed/default/module과 함께 설계하는 것이 더 정확하다.
