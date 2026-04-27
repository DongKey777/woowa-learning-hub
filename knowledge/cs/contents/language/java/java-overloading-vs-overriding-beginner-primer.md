# Java 오버로딩 vs 오버라이딩 입문

> 한 줄 요약: `overloading`은 같은 이름에 다른 parameter 목록을 여는 것이고, `overriding`은 상속 관계에서 같은 시그니처의 instance method 구현을 바꾸는 것이다. 입문자는 "컴파일 시그니처 선택 -> 런타임 구현 선택" 두 단계로 읽으면 헷갈림이 크게 줄어든다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java overloading vs overriding beginner primer basics, java overloading vs overriding beginner primer beginner, java overloading vs overriding beginner primer intro, java basics, beginner java, 처음 배우는데 java overloading vs overriding beginner primer, java overloading vs overriding beginner primer 입문, java overloading vs overriding beginner primer 기초, what is java overloading vs overriding beginner primer, how to java overloading vs overriding beginner primer
> 관련 문서:
> - [Language README](../README.md)
> - [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
> - [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)

> retrieval-anchor-keywords: java overloading vs overriding, java overload override difference, java method overloading basics, java method overriding basics, java compile time vs runtime method selection, java parent reference child object method call, java polymorphism beginner example, java inheritance practice example, java same method name different parameter, java same signature override, java @Override basics, java dynamic dispatch beginner, java overload argument list, java override runtime dispatch, 자바 오버로딩 오버라이딩 차이, 처음 배우는데 오버로딩 오버라이딩, 메서드 이름 같은데 왜 다르게 동작하나요, 자바 @Override 왜 쓰나요, 부모 타입 자식 객체 메서드 호출, 컴파일 타임 런타임 메서드 선택 차이, 오버로딩 언제 쓰는지 기초, 오버라이딩 언제 쓰는지 기초

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 한 줄로 구분하기](#먼저-한-줄로-구분하기)
- [한 가족 예제로 같이 보기](#한-가족-예제로-같이-보기)
- [메서드 선택을 2단계로 읽기](#메서드-선택을-2단계로-읽기)
- [손으로 풀어보는 연습](#손으로-풀어보는-연습)
- [초보자가 자주 틀리는 포인트](#초보자가-자주-틀리는-포인트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문에서 `overloading`과 `overriding`이 자주 섞이는 이유는 둘 다 "메서드 이름이 같다"는 겉모습을 공유하기 때문이다.

대표적으로 이런 오해가 나온다.

- 이름만 같으면 모두 overriding인가?
- 부모 타입 변수로 자식 객체를 담았을 때 왜 어떤 호출은 되고 어떤 호출은 컴파일 에러가 나는가?
- `@Override`를 붙인 메서드와 그냥 이름이 같은 메서드는 무엇이 다른가?

이 문서는 이 혼란을 줄이기 위해 같은 `Animal` 계층 안에서 두 개념을 나란히 보여 준다. 핵심은 "`이름이 같은가`"가 아니라 "`parameter 목록이 같은가`", "`상속 관계인가`", "`컴파일 시그니처 선택과 런타임 구현 선택 중 어느 단계 이야기인가`"를 구분하는 것이다.

## 먼저 한 줄로 구분하기

| 구분 | overloading | overriding |
|---|---|---|
| 핵심 질문 | "같은 의도를 다른 입력 형태로 열 수 있나?" | "부모 동작을 자식 방식으로 바꿀 수 있나?" |
| 조건 | 같은 이름, 다른 parameter 목록 | 상속 관계, 같은 이름, 같은 parameter 목록 |
| 주된 위치 | 같은 클래스 안 또는 상속 계층 안 | 부모-자식 클래스 사이 |
| 선택 기준 | 컴파일 시점의 변수 타입 + argument 목록 | 런타임의 실제 객체 |
| 실전 신호 | `deposit(int)`, `deposit(int, int)` | `Animal.speak()` -> `Dog.speak()` |

입문 단계에서는 다음 두 문장을 먼저 외워 두면 좋다.

- overloading은 **메서드 모양을 늘리는 일**이다.
- overriding은 **선택된 메서드의 구현을 자식이 바꾸는 일**이다.

즉 둘은 경쟁 개념이 아니라 서로 다른 층위의 규칙이다.

## 한 가족 예제로 같이 보기

```java
public class Animal {
    private final String name;

    public Animal(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public void speak() {
        System.out.println(name + " makes a sound");
    }

    public void speak(String mood) {
        System.out.println(name + " makes a " + mood + " sound");
    }
}

public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }

    @Override
    public void speak() {
        System.out.println(getName() + " barks");
    }

    @Override
    public void speak(String mood) {
        System.out.println(getName() + " barks in a " + mood + " mood");
    }

    public void speak(int times) {
        for (int i = 0; i < times; i++) {
            speak();
        }
    }
}
```

이 코드에서 읽어야 할 포인트는 세 가지다.

- `Animal.speak()`와 `Animal.speak(String)`는 이름은 같고 parameter 목록이 다르므로 overloading이다.
- `Dog.speak()`와 `Dog.speak(String)`는 부모의 같은 시그니처 메서드를 다시 정의하므로 overriding이다.
- `Dog.speak(int)`는 부모에 같은 시그니처가 없으므로 overriding이 아니라 새로운 overload다.

즉 `Dog` 안에는 overriding과 overloading이 동시에 들어 있다.
그래서 초보자는 "`Dog` 클래스 안에 있으니 다 overriding"처럼 읽지 말고, **각 메서드가 부모와 시그니처가 같은지**부터 봐야 한다.

## 메서드 선택을 2단계로 읽기

혼란이 가장 많이 줄어드는 지점은 메서드 호출을 아래 두 단계로 나눠 읽는 습관이다.

1. 컴파일 시점에 변수 타입과 argument 목록으로 **어떤 시그니처를 부를지** 고른다.
2. 그 시그니처가 overridden instance method라면 런타임에 **실제 객체의 구현**이 실행된다.

아래 호출을 보자.

```java
Animal animal = new Dog("Coco");
Dog dog = new Dog("Coco");

animal.speak();
animal.speak("happy");
// animal.speak(3); // 컴파일 에러
dog.speak(3);
```

각 줄은 이렇게 읽는다.

- `animal.speak()`
  - 1단계: 변수 타입이 `Animal`이므로 `speak()` 시그니처를 찾는다
  - 2단계: 실제 객체가 `Dog`이므로 `Dog.speak()`가 실행된다
- `animal.speak("happy")`
  - 1단계: `Animal` 타입에서 `speak(String)`을 찾는다
  - 2단계: 실제 객체가 `Dog`이므로 `Dog.speak(String)`이 실행된다
- `animal.speak(3)`
  - 1단계에서 실패한다. 변수 타입 `Animal`에는 `speak(int)`가 없기 때문이다
  - 런타임 dispatch까지 가지도 못한다
- `dog.speak(3)`
  - 1단계에서 `Dog.speak(int)`를 찾는다
  - 이것은 overload 선택이지 override dispatch의 핵심 예시가 아니다

즉 overloading은 **호출 가능한 시그니처를 고르는 문제**이고, overriding은 **이미 고른 시그니처의 구현을 누가 맡는가**의 문제다.

## 손으로 풀어보는 연습

### 연습 1. 어떤 구현이 실행될까

```java
Animal first = new Dog("Coco");
Animal second = new Animal("Momo");

first.speak();
first.speak("sleepy");
second.speak();
```

정답은 다음과 같다.

- `first.speak()` -> `Dog.speak()`
- `first.speak("sleepy")` -> `Dog.speak(String)`
- `second.speak()` -> `Animal.speak()`

이유는 둘 다 시그니처 선택은 `Animal` 기준으로 되지만, `first`는 실제 객체가 `Dog`이기 때문이다.

### 연습 2. 무엇이 컴파일되고 무엇이 막힐까

```java
Animal animal = new Dog("Coco");
Dog dog = new Dog("Coco");

animal.speak();
animal.speak("happy");
animal.speak(2);
dog.speak(2);
```

정답은 다음과 같다.

- `animal.speak()` 컴파일됨
- `animal.speak("happy")` 컴파일됨
- `animal.speak(2)` 컴파일 에러
- `dog.speak(2)` 컴파일됨

핵심은 "`실제 객체가 Dog니까 `animal.speak(2)`도 되겠지"라고 읽으면 안 된다는 점이다.
overloading 후보를 찾을 때는 먼저 **변수 타입 `Animal`** 을 본다.

### 연습 3. `@Override`가 왜 필요한가

```java
public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }

    @Override
    public void speek() {
        System.out.println(getName() + " barks");
    }
}
```

이 코드는 컴파일 에러다. `speek()`는 부모 메서드를 override하지 않기 때문이다.

`@Override`가 없었다면 초보자는 "재정의했다"고 착각한 채, 사실은 전혀 다른 새 메서드를 하나 만든 상태로 지나갈 수 있다.

## 초보자가 자주 틀리는 포인트

### 이름이 같다고 모두 overriding은 아니다

같은 이름이어도 parameter 목록이 다르면 overloading이다.
상속 관계 안에 있다고 해서 자동으로 overriding이 되지 않는다.

### return type만 바꿔서는 overloading이 되지 않는다

Java는 메서드 호출을 구분할 때 parameter 목록을 본다.
return type만 다르게 두는 것은 허용되지 않는다.

### 변수 타입과 실제 객체 타입의 역할을 섞으면 안 된다

- 변수 타입: "어떤 시그니처를 부를 수 있는가"를 정한다
- 실제 객체 타입: override된 메서드라면 "어느 구현이 실행되는가"를 정한다

이 둘을 섞으면 `animal.speak(2)` 같은 예제에서 거의 항상 헷갈린다.

### overriding 메서드에는 `@Override`를 붙이는 편이 안전하다

오타나 시그니처 불일치를 바로 컴파일 에러로 바꿔 주기 때문이다.

## 어떤 문서를 다음에 읽으면 좋은가

- parameter, return type, method overloading을 더 기초부터 보고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- `extends`, `super(...)`, dynamic dispatch를 상속 관점에서 더 길게 읽고 싶다면 [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)
- 클래스, 객체, 추상화, 다형성까지 OOP 지도를 넓히고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- overloading/overriding 뒤에 "상속 vs 조합, 추상 클래스 vs 인터페이스를 언제 쓰는지"까지 이어 보고 싶다면 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)
- 상속과 다형성을 더 넓은 설계 원리로 연결하고 싶다면 [객체지향 핵심 원리](./object-oriented-core-principles.md)

## 한 줄 정리

overloading은 같은 이름의 **여러 시그니처를 여는 규칙**이고, overriding은 상속 관계에서 **같은 시그니처의 구현을 바꾸는 규칙**이다. 호출은 먼저 컴파일 시그니처 선택을 거친 뒤, 필요하면 런타임 객체가 최종 구현을 결정한다.
