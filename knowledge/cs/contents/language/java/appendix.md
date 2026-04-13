# 부록 - 생각해보기

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: 추상 클래스와 인터페이스는 문법이 비슷해 보여도 상속 경로, 상태 보유, 확장성, 경계 제어에서 완전히 다른 설계 도구다.

**난이도: 🟠 Intermediate**

> 관련 문서:
> - [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)
> - [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md)
> - [Java Module System Runtime Boundaries](./java-module-system-runtime-boundaries.md)
> - [ClassLoader Delegation Edge Cases](./classloader-delegation-edge-cases.md)

> retrieval-anchor-keywords: abstract class, interface, default method, multiple inheritance, template method, stateful base class, contract, sealed interface, evolution, capability, inheritance boundary

<details>
<summary>Table of Contents</summary>

- [왜 다시 생각해봐야 하나](#왜-다시-생각해봐야-하나)
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

Java의 추상 클래스와 인터페이스는 오랫동안 기본 문법처럼 보였지만, 현대 Java에서는 record, sealed interface, default method, module boundary까지 같이 봐야 설계 판단이 더 정확해진다.

즉 이 주제는 단순 암기가 아니라 **어떤 경계를 타입이 책임질 것인가**를 묻는 문제다.

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
