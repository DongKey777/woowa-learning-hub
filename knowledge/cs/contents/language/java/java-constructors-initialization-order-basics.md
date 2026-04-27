# Java 생성자와 초기화 순서 입문

> 한 줄 요약: Java 입문자가 `this()`/`super()` constructor chaining, field 초기화 순서, `static` vs instance 초기화 블록을 한 흐름으로 연결해서 이해하도록 돕는 beginner primer다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java constructors initialization order basics basics, java constructors initialization order basics beginner, java constructors initialization order basics intro, java basics, beginner java, 처음 배우는데 java constructors initialization order basics, java constructors initialization order basics 입문, java constructors initialization order basics 기초, what is java constructors initialization order basics, how to java constructors initialization order basics
> 관련 문서:
> - [Language README](../README.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
> - [Class Initialization Ordering](./class-initialization-ordering.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

> retrieval-anchor-keywords: java constructor chaining basics, java initialization order basics, java this super basics, java this constructor call, java super constructor call, java field initialization order, java static initialization block, java instance initialization block, java initializer block basics, java parent child constructor order, java subclass initialization order, java constructor first line rule, java default value before constructor, java beginner constructor primer

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡아야 하는 다섯 규칙](#먼저-잡아야-하는-다섯-규칙)
- [`this()`와 `super()`는 무엇이 다른가](#this와-super는-무엇이-다른가)
- [필드와 초기화 블록은 언제 실행되나](#필드와-초기화-블록은-언제-실행되나)
- [부모 클래스까지 포함한 전체 순서](#부모-클래스까지-포함한-전체-순서)
- [초보자가 자주 틀리는 포인트](#초보자가-자주-틀리는-포인트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 초보자는 생성자를 배울 때 보통 "객체를 만들 때 쓰는 함수 같은 것" 정도로만 이해하고 넘어간다.
하지만 실제 코드를 읽기 시작하면 바로 다음 질문이 붙는다.

- 생성자 안에서 왜 `this(...)`를 먼저 부를까?
- 왜 어떤 생성자는 `super(...)`가 꼭 필요할까?
- 필드에 값을 주는 코드와 생성자 본문 중 무엇이 먼저 실행될까?
- `static {}` 과 `{}` 는 둘 다 블록처럼 보이는데 언제 실행될까?

이 문서는 위 질문을 하나의 실행 순서로 묶어서 정리한다.
핵심은 **"객체가 태어나기 전후에 무슨 일이 어떤 순서로 일어나는가"** 를 손으로 추적할 수 있게 만드는 데 있다.

## 먼저 잡아야 하는 다섯 규칙

| 규칙 | 초보자용 설명 |
|---|---|
| `this(...)` 는 같은 클래스의 다른 생성자를 부른다 | 생성자끼리 중복 코드를 줄일 때 쓴다 |
| `super(...)` 는 부모 클래스 생성자를 부른다 | 부모가 가져야 할 시작 상태를 먼저 만든다 |
| 생성자의 첫 줄에는 `this(...)` 또는 `super(...)`만 올 수 있다 | 둘을 같이 쓸 수 없고, 다른 문장보다 먼저 와야 한다 |
| 필드 초기화와 초기화 블록은 선언 순서대로 실행된다 | 위에서 아래로 읽는 습관이 중요하다 |
| `static` 초기화는 클래스당 한 번, instance 초기화는 객체마다 한 번 실행된다 | 클래스 소속과 객체 소속을 구분해야 한다 |

추가로 하나 더 기억하면 좋다.

- 생성자에서 `this(...)`도 `super(...)`도 직접 쓰지 않으면 컴파일러가 보통 `super()`를 넣는다.
- 그래서 부모 클래스에 기본 생성자(no-arg constructor)가 없으면, 자식 생성자에서 어떤 부모 생성자를 부를지 직접 적어야 한다.

## `this()`와 `super()`는 무엇이 다른가

### `this(...)`: 같은 클래스 생성자끼리 연결한다

생성자 여러 개가 비슷한 검증과 대입을 반복한다면, 가장 상세한 생성자 하나로 모으고 나머지는 `this(...)`로 연결하는 편이 읽기 쉽다.

```java
public class Order {
    private final String productName;
    private final int quantity;
    private final boolean gift;

    public Order(String productName) {
        this(productName, 1);
    }

    public Order(String productName, int quantity) {
        this(productName, quantity, false);
    }

    public Order(String productName, int quantity, boolean gift) {
        if (quantity <= 0) {
            throw new IllegalArgumentException("quantity must be positive");
        }
        this.productName = productName;
        this.quantity = quantity;
        this.gift = gift;
    }
}
```

이 예시에서 핵심은 다음이다.

- `Order(String productName)`은 기본 수량 `1`을 정한다.
- `Order(String productName, int quantity)`는 `gift=false`를 정한다.
- 실제 검증과 필드 대입은 가장 아래 생성자 한 곳에서만 처리한다.

즉 `this(...)`는 **같은 클래스 안에서 기본값을 채우며 생성자를 이어 붙이는 도구**다.

### `super(...)`: 부모 생성자를 먼저 호출한다

상속이 있으면 자식 객체 안에는 부모 부분도 함께 들어 있다.
그래서 자식 생성자는 자기 필드만 채우는 것이 아니라, 부모가 가진 상태도 먼저 초기화해야 한다.

```java
public class Animal {
    protected final String name;

    public Animal(String name) {
        this.name = name;
    }
}

public class Dog extends Animal {
    private final int age;

    public Dog(String name, int age) {
        super(name);
        this.age = age;
    }
}
```

`Dog`는 `name` 필드를 직접 선언하지 않았지만 부모 `Animal`이 그 상태를 가진다.
그래서 `Dog` 생성자는 `super(name)`으로 부모 쪽 시작 상태를 먼저 만든다.

## `this()`와 `super()`는 무엇이 다른가 (계속 2)

### `this`와 `super`는 "생성자 호출"과 "멤버 접근" 두 역할이 있다

| 형태 | 뜻 |
|---|---|
| `this(...)` | 같은 클래스의 다른 생성자 호출 |
| `super(...)` | 부모 클래스 생성자 호출 |
| `this.name` | 현재 객체의 필드/메서드 접근 |
| `super.name`, `super.method()` | 부모 쪽 멤버 접근 |

문맥이 다르므로 헷갈리지 말아야 한다.
괄호가 붙으면 생성자 호출, 점(`.`)이 붙으면 멤버 접근이다.

## 필드와 초기화 블록은 언제 실행되나

Java는 생성자 본문만 바로 실행하지 않는다.
필드 initializer와 초기화 블록이 먼저 끼어든다.

### 한 클래스 안에서는 "선언 순서"가 핵심이다

```java
public class InitOrderSample {
    static int staticValue = trace("1. static field");

    static {
        trace("2. static block");
    }

    int first = trace("3. instance field first");

    {
        trace("4. instance block");
    }

    int second = trace("5. instance field second");

    public InitOrderSample() {
        trace("6. constructor body");
    }

    private static int trace(String message) {
        System.out.println(message);
        return 0;
    }
}
```

`new InitOrderSample()`를 처음 실행하면 출력 순서는 다음과 같다.

```text
1. static field
2. static block
3. instance field first
4. instance block
5. instance field second
6. constructor body
```

여기서 봐야 할 점은 세 가지다.

1. `static` field와 `static` block은 클래스가 처음 초기화될 때 한 번만 실행된다.
2. instance field와 instance block은 객체를 만들 때마다 다시 실행된다.
3. 같은 종류끼리 묶이지 않고, **파일에 적힌 순서 그대로** 실행된다.

즉 Java는 "필드 다 끝내고 블록 다 실행"이 아니라, **위에서 아래로 읽으며 initializer를 실행**한다.

### 객체는 default value부터 시작한다

필드는 생성자 실행 전 잠깐 기본값으로 채워진다.

| 필드 타입 | 기본값 |
|---|---|
| 숫자형 | `0` |
| `boolean` | `false` |
| 참조형 | `null` |

그 뒤에 field initializer, instance block, 생성자 본문 순서로 값이 덮어써진다.
그래서 "생성자에서 대입했으니 그 전에는 아무 값도 없다"라고 생각하면 순서 추적이 자주 꼬인다.

### instance 초기화 블록은 언제 쓰나

instance block은 생성자마다 공통으로 들어가는 전처리를 묶을 때 쓸 수 있다.

## 필드와 초기화 블록은 언제 실행되나 (계속 2)

```java
public class Coupon {
    private final String code;
    private long createdAt = System.currentTimeMillis();

    {
        System.out.println("coupon object is being created");
    }

    public Coupon(String code) {
        this.code = code;
    }
}
```

다만 초보자 기준에서는 **"이런 문법이 있다"를 아는 것**이 더 중요하고, 실제 설계에서는 생성자나 private helper가 더 읽기 쉬운 경우가 많다.
즉 instance block은 자주 쓰는 기본 도구라기보다, 기존 코드를 읽을 때 알아봐야 하는 문법에 가깝다.

## 부모 클래스까지 포함한 전체 순서

상속과 constructor chaining이 같이 나오면 순서를 이렇게 읽으면 된다.

1. 아직 클래스가 초기화되지 않았다면 부모 `static` 초기화부터 한 번 실행된다.
2. 그다음 자식 `static` 초기화가 한 번 실행된다.
3. 객체를 만들면 먼저 부모 쪽 instance field / instance block이 선언 순서대로 실행된다.
4. 부모 생성자 본문이 실행된다.
5. 그다음 자식 쪽 instance field / instance block이 선언 순서대로 실행된다.
6. 마지막으로 자식 생성자 본문이 실행된다.

아래 예시를 보자.

```java
public class Parent {
    static String parentStatic = trace("1. parent static field");

    static {
        trace("2. parent static block");
    }

    String parentField = trace("3. parent instance field");

    {
        trace("4. parent instance block");
    }

    public Parent(String name) {
        trace("5. parent constructor body: " + name);
    }

    protected static String trace(String message) {
        System.out.println(message);
        return message;
    }
}

public class Child extends Parent {
    static String childStatic = trace("6. child static field");

    static {
        trace("7. child static block");
    }

    String childField = trace("8. child instance field");

    {
        trace("9. child instance block");
    }

    public Child() {
        this("guest");
        trace("11. child no-arg constructor body");
    }

    public Child(String name) {
        super(name);
        trace("10. child one-arg constructor body");
    }
}
```

처음 `new Child()`를 실행하면 출력은 대략 이렇게 읽힌다.

## 부모 클래스까지 포함한 전체 순서 (계속 2)

```text
1. parent static field
2. parent static block
6. child static field
7. child static block
3. parent instance field
4. parent instance block
5. parent constructor body: guest
8. child instance field
9. child instance block
10. child one-arg constructor body
11. child no-arg constructor body
```

이 예시에서 특히 중요한 포인트는 두 가지다.

- `this("guest")`를 썼다고 해서 child instance field와 instance block이 두 번 실행되지는 않는다.
- 두 번째 `new Child()`부터는 `static` 부분은 다시 출력되지 않고 instance 부분만 반복된다.

## 초보자가 자주 틀리는 포인트

### `this()`와 `super()`를 둘 다 한 생성자에 쓸 수 있다고 생각한다

불가능하다.
생성자의 첫 줄에는 둘 중 하나만 올 수 있다.

### field initializer보다 생성자 본문이 먼저 실행된다고 생각한다

아니다.
field initializer와 초기화 블록이 먼저 실행되고, 그 다음 생성자 본문이 실행된다.

### 부모 생성자는 자식 생성자 본문 뒤에 실행된다고 생각한다

반대다.
부모 쪽 초기화와 부모 생성자가 먼저 끝나야 자식 쪽 생성자 본문으로 내려온다.

### `static {}` 와 `{}` 를 같은 것으로 본다

둘은 전혀 다르다.

- `static {}` 는 클래스당 한 번
- `{}` 는 객체마다 한 번

### instance 초기화 블록을 "생성자보다 더 좋은 기본 방식"으로 받아들인다

대부분의 입문 코드에서는 생성자만으로도 충분하다.
instance block은 존재와 실행 시점을 이해하는 것이 우선이고, 남용하는 것은 별개의 문제다.

## 어떤 문서를 다음에 읽으면 좋은가

- 생성자 overloading과 상태 변경 메서드를 더 짧은 예제로 다시 묶어 보고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- `static`, instance 멤버, `final`이 객체 모델에 어떤 차이를 만드는지 이어서 보고 싶다면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 클래스 초기화(`clinit`), 순환 초기화, holder pattern까지 더 깊게 보고 싶다면 [Class Initialization Ordering](./class-initialization-ordering.md)
- 생성자에서 불변 조건을 어떻게 지켜야 하는지 보고 싶다면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

## 한 줄 정리

Java 초기화 순서는 "`static`은 클래스당 한 번, instance initializer는 객체마다 선언 순서대로, 생성자 본문은 그 다음"으로 읽고, 생성자 연결은 같은 클래스면 `this()`, 부모 상태면 `super()`로 구분하면 된다.
