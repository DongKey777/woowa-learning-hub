# Java 상속과 오버라이딩 기초

> 한 줄 요약: `extends`, method overriding vs overloading, `@Override`, dynamic dispatch를 작은 클래스 예제로 묶어 입문자가 "상속은 타입 관계, 오버라이딩은 재정의, 실제 메서드 선택은 런타임 객체가 결정한다"는 흐름을 잡도록 돕는 primer다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
> - [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md)
> - [Java 생성자와 초기화 순서 입문](./java-constructors-initialization-order-basics.md)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md)

> retrieval-anchor-keywords: java inheritance basics, java overriding basics, java overloading vs overriding, java extends basics, java override annotation basics, java @Override basics, java dynamic dispatch basics, runtime polymorphism basics, parent child class basics, java beginner inheritance primer, java super constructor basics, java overridden method dispatch, java overloaded method signature basics

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [`extends`로 부모와 자식을 연결하기](#extends로-부모와-자식을-연결하기)
- [오버라이딩과 오버로딩을 구분하기](#오버라이딩과-오버로딩을-구분하기)
- [`@Override`를 붙이는 이유](#override를-붙이는-이유)
- [dynamic dispatch를 손으로 추적하기](#dynamic-dispatch를-손으로-추적하기)
- [초보자가 자주 헷갈리는 포인트](#초보자가-자주-헷갈리는-포인트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자가 상속과 다형성에서 자주 막히는 지점은 문법보다도 "누가 무엇을 물려받고, 어떤 메서드가 실제로 호출되는가"를 한 흐름으로 연결하지 못하는 데 있다.

대표적으로 이런 질문이 나온다.

- `extends`는 그냥 부모 코드를 복사해 오는 것인가?
- 메서드 이름이 같으면 모두 overriding인가?
- `@Override`는 없어도 되는데 왜 붙이라고 하나?
- 변수 타입이 `Animal`인데 왜 `Dog`의 메서드가 실행되나?

이 문서는 위 질문을 작은 클래스 예제로 묶어 설명한다. 핵심은 다음 네 문장이다.

- `extends`는 부모-자식 타입 관계를 만든다.
- overriding은 부모 메서드를 자식이 같은 시그니처로 다시 정의하는 것이다.
- overloading은 이름은 같지만 parameter 목록이 다른 메서드를 여는 것이다.
- overridden instance method는 런타임의 실제 객체를 기준으로 선택된다.

## `extends`로 부모와 자식을 연결하기

가장 작은 예시부터 보자.

```java
public class Animal {
    private final String name;

    public Animal(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public void eat() {
        System.out.println(name + " eats");
    }

    public void speak() {
        System.out.println(name + " makes a sound");
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
}
```

이 코드에서 읽어야 할 핵심은 세 가지다.

- `Dog extends Animal`은 `Dog is an Animal` 관계를 만든다.
- `Dog`는 `Animal`의 public/protected 멤버를 이어받아 사용할 수 있다.
- `Dog` 생성자는 `super(name)`으로 부모 쪽 초기화를 먼저 맡긴다.

즉 `Dog`는 `Animal`의 하위 타입이므로 `eat()` 같은 공통 동작은 그대로 쓰고, `speak()` 같은 동작은 자기 방식으로 바꿀 수 있다.

다만 상속이 "모든 것을 그대로 복사"하는 것은 아니다.

- 부모 생성자는 상속되지 않는다. 그래서 자식 생성자에서 `super(...)`를 호출한다.
- 부모의 `private` 필드는 자식이 직접 접근할 수 없다. 위 예시에서 `name`은 `getName()`으로만 읽는다.
- 문법이 된다고 아무 관계나 상속으로 만들면 안 된다. `is-a`가 자연스러울 때만 써야 한다.

## 오버라이딩과 오버로딩을 구분하기

초보자가 가장 자주 섞어 말하는 두 개념이 overriding과 overloading이다.

| 구분 | overriding | overloading |
|---|---|---|
| 어디서 일어나나 | 상속 관계의 자식이 부모 메서드를 다시 정의 | 같은 클래스 안에서 이름이 같은 메서드를 여러 형태로 선언 |
| 메서드 이름 | 같다 | 같다 |
| parameter 목록 | 같아야 한다 | 달라야 한다 |
| 핵심 목적 | 부모 동작을 자식 방식으로 교체 | 같은 의도를 다른 입력 형태로 제공 |
| 선택 시점 | 런타임 dispatch와 연결됨 | 컴파일 시 argument 목록으로 결정 |

아래 코드를 보자.

```java
public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }

    @Override
    public void speak() {
        System.out.println(getName() + " barks");
    }

    public void speak(int times) {
        for (int i = 0; i < times; i++) {
            speak();
        }
    }
}
```

여기서 두 메서드는 이름이 같지만 의미가 다르다.

- `public void speak()`는 부모의 `speak()`를 다시 정의한 것이므로 overriding이다.
- `public void speak(int times)`는 parameter가 다르므로 overloading이다.

즉 "이름이 같다"만으로 overriding이라고 말하면 안 된다.  
부모 메서드와 **이름과 parameter 목록이 같아야** overriding이다.

반대로 return type만 바꿔서는 overloading이 되지 않는다.

```java
// 컴파일 에러
public int level() { return 1; }
public String level() { return "one"; }
```

Java는 메서드 선택에서 parameter 목록을 중요하게 보기 때문이다.

## `@Override`를 붙이는 이유

`@Override`는 문법 장식이 아니라 "나는 지금 부모 메서드를 재정의하려고 한다"는 의도를 컴파일러에게 확인시키는 안전장치다.

```java
public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }

    @Override
    public void speak() {
        System.out.println(getName() + " barks");
    }
}
```

이 어노테이션을 붙이면 다음 같은 실수를 빨리 잡을 수 있다.

```java
public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }

    @Override
    public void speek() { // 컴파일 에러: 부모 메서드를 override하지 않음
        System.out.println(getName() + " barks");
    }
}
```

`speek()`처럼 이름을 잘못 쓰거나 parameter를 다르게 적으면, `@Override`가 없는 경우 초보자는 "재정의한 줄 알았는데 사실은 새 메서드를 하나 더 만든 상태"가 되기 쉽다.  
그래서 실무에서는 overriding하는 메서드에 `@Override`를 거의 습관처럼 붙인다.

## dynamic dispatch를 손으로 추적하기

다형성은 대개 "상위 타입 변수로 여러 하위 타입을 다룰 수 있다"로 설명되지만, 초보자에게 더 중요한 것은 **실제 호출 메서드가 런타임 객체 기준으로 결정된다**는 점이다.

아래 코드를 보자.

```java
public class Cat extends Animal {
    public Cat(String name) {
        super(name);
    }

    @Override
    public void speak() {
        System.out.println(getName() + " meows");
    }
}
```

```java
Animal first = new Dog("Coco");
Animal second = new Cat("Nabi");

first.eat();
first.speak();
second.speak();
```

실행 흐름은 이렇게 읽으면 된다.

1. `first`의 변수 타입은 `Animal`이지만 실제 객체는 `Dog`다.
2. `first.eat()`는 `Dog`가 `eat()`를 override하지 않았으므로 부모 `Animal.eat()`가 실행된다.
3. `first.speak()`는 `Dog`가 `speak()`를 override했으므로 `Dog.speak()`가 실행된다.
4. `second.speak()`는 실제 객체가 `Cat`이므로 `Cat.speak()`가 실행된다.

출력은 대략 이렇게 된다.

```text
Coco eats
Coco barks
Nabi meows
```

여기서 중요한 구분은 다음이다.

- "무슨 메서드를 호출할 수 있는가"는 변수의 타입이 결정한다.
- "그 메서드 구현 중 무엇이 실제 실행되는가"는 런타임 객체가 결정한다.

이것이 beginner 문맥에서 말하는 dynamic dispatch의 핵심이다.

조금 더 짧게 줄이면 이렇게 기억하면 된다.

- 참조 타입이 `Animal`이어도
- 실제 객체가 `Dog`면
- overridden instance method는 `Dog` 쪽 구현이 실행된다

## 초보자가 자주 헷갈리는 포인트

### `extends`는 코드 복사가 아니다

상속은 부모-자식 타입 관계를 만드는 것이다.  
부모 설계를 자식이 그대로 안고 가므로, 공통 기능 재사용이 편한 대신 결합도도 커진다.

### 이름이 같다고 모두 overriding은 아니다

parameter 목록이 다르면 overloading이다.  
`speak()`와 `speak(int times)`는 이름이 같아도 다른 개념이다.

### `@Override`는 선택이 아니라 안전장치에 가깝다

없어도 컴파일되는 경우가 많지만, 오타나 시그니처 착각을 빨리 잡는 데 큰 도움이 된다.

### 부모 타입 변수로 자식 메서드가 호출될 수 있다

`Animal pet = new Dog("Coco");`에서 `pet.speak()`가 `Dog.speak()`를 호출하는 이유는 dynamic dispatch 때문이다.

### field와 static method는 instance method overriding처럼 동작하지 않는다

입문 단계에서는 "런타임에 갈아끼워지는 것은 overridden instance method"라고 먼저 기억하면 된다.  
field 접근과 static method는 같은 방식으로 dispatch되지 않는다.

### `private` 메서드는 override 대상이 아니다

자식이 직접 볼 수 없는 멤버는 같은 의미의 overriding 대상이 되지 않는다.  
그래서 overriding은 보통 상속받아 접근 가능한 instance method를 중심으로 이해하면 된다.

## 어떤 문서를 다음에 읽으면 좋은가

- 클래스, 객체, 인터페이스, 추상 클래스까지 OOP 지도를 먼저 잡고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- parameter, return type, method overloading을 더 기초부터 다시 묶어 보고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- method overloading과 method overriding의 차이만 짧게 다시 고정하고 싶다면 [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md)
- `super(...)`, constructor chaining, 초기화 순서를 같이 이해하고 싶다면 [Java 생성자와 초기화 순서 입문](./java-constructors-initialization-order-basics.md)
- `protected`, `final`, `static` 같은 멤버 규칙과 함께 상속 경계를 보고 싶다면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 상속, 다형성, 추상화를 조금 더 넓은 OOP 문맥에서 다시 읽고 싶다면 [객체지향 핵심 원리](./object-oriented-core-principles.md)
- 추상 클래스와 인터페이스를 언제 나눠 써야 하는지 더 정확히 보고 싶다면 [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md)

## 한 줄 정리

`extends`는 부모-자식 타입 관계를 만들고, overriding은 그 관계 안에서 같은 시그니처의 instance method를 다시 정의하며, 실제 호출 구현은 런타임 객체가 결정된다.
