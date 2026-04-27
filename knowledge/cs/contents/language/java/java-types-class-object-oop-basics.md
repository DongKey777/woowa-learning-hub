# Java 타입, 클래스, 객체, OOP 입문

> 한 줄 요약: Java 입문자가 문법 암기에서 멈추지 않도록 기본형과 참조형, 클래스와 객체, 인터페이스와 추상 클래스, OOP 핵심 원리를 한 흐름으로 묶어 설명하는 primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- [Java parameter 전달, pass-by-value, side effect 입문](./java-parameter-passing-pass-by-value-side-effects-primer.md)
- [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) - 객체지향 큰 그림 다음에 "상속 언제 쓰는지"를 `extends`와 dynamic dispatch로 좁혀 보는 다음 primer
- [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md)
- [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- [객체지향 핵심 원리](./object-oriented-core-principles.md) - 클래스/객체 감각을 OOP 큰 그림으로 먼저 묶고, 그다음 "상속 언제 쓰는지"로 넘어가게 만드는 첫 handoff primer
- [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) - OOP 큰 그림과 상속 primer를 지난 뒤 "공통 흐름을 부모가 쥘지, 계약을 인터페이스로 열지"를 beginner 기준으로 나누는 다음 handoff primer
- [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)
- [디자인 패턴 카테고리 인덱스](../../design-pattern/README.md) - 처음 배우는데 디자인 패턴을 어디부터 읽을지 막히면 조합 -> 패턴 기초 route map으로 이어 주는 beginner entrypoint
- [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md)
- [템플릿 메소드 vs 전략](../../design-pattern/template-method-vs-strategy.md)
- [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
- [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)

retrieval-anchor-keywords: java oop primer, java class object instance basics, java primitive vs reference type, java oop beginner route, 객체지향 기초, 클래스 객체 인스턴스 차이, 처음 배우는데 클래스 객체 차이, 처음 배우는데 oop, 처음 배우는데 상속 언제 쓰는지, oop to design pattern beginner route, design pattern beginner route, 처음 배우는데 디자인 패턴 어디부터

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [처음 읽는 순서](#처음-읽는-순서)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [클래스/객체/인스턴스 3단계 브리지](#클래스객체인스턴스-3단계-브리지)
- [기본형과 참조형](#기본형과-참조형)
- [클래스, 객체, 인스턴스](#클래스-객체-인스턴스)
- [인터페이스와 추상 클래스](#인터페이스와-추상-클래스)
- [핵심 OOP 원리](#핵심-oop-원리)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [초보자가 자주 헷갈리는 포인트](#초보자가-자주-헷갈리는-포인트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문 구간에서 가장 흔한 막힘은 문법 자체보다도 "이 문법이 객체 모델과 어떻게 연결되는가"를 놓치는 데서 나온다.

예를 들면 이런 질문들이다.

- `int`와 `String`은 둘 다 변수에 담기는데 왜 성격이 다를까?
- 클래스와 객체는 정확히 무엇이 다를까?
- 인터페이스와 추상 클래스는 둘 다 추상적인데 언제 무엇을 써야 할까?
- 캡슐화, 상속, 다형성, 추상화는 코드에서 어떻게 보일까?

이 문서는 위 질문을 한 번에 연결해 주는 `primer` 역할을 한다. 세부 문법이나 심화 설계는 관련 문서로 확장하고, 여기서는 초보자가 먼저 잡아야 할 최소한의 개념 지도를 정리한다.

## 처음 읽는 순서

처음 배우는데 OOP 큰 그림이 한 번에 안 잡히면, 문서를 따로따로 외우기보다 **"타입과 객체 이해 -> OOP 큰 그림 연결 -> 상속 이해 -> 추상 클래스/인터페이스 구분 -> 조합 우선 판단"** 순서로 보면 된다.

| 지금 막히는 질문 | 먼저 읽을 문서 | 이 문서가 하는 일 |
|---|---|---|
| "클래스, 객체, 타입이 대체 뭐지?" | 이 문서 | 기본형/참조형, 클래스/객체, OOP 핵심 용어를 한 번에 묶는다 |
| "클래스/객체는 알겠는데 OOP 큰 그림은 왜 필요한가?" | [객체지향 핵심 원리](./object-oriented-core-principles.md) | 클래스/객체 감각을 캡슐화, 추상화, 상속, 다형성으로 연결한다 |
| "`extends`가 코드 복사랑 뭐가 다르지?" | [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) | is-a 관계, overriding, dynamic dispatch를 먼저 분리한다 |
| "`@Override`와 overloading 이름이 왜 헷갈리지?" | [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md) | compile-time 선택과 runtime 선택을 분리한다 |
| "추상 클래스와 인터페이스는 언제 나누지?" | [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) | 부모가 공통 흐름을 쥐는지, 계약을 열어 두는지로 자른다 |
| "재사용하려면 일단 상속해야 하나?" | [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) | 코드 재사용과 설계 결합을 분리하고, 조합을 기본값으로 잡는다 |

첫 읽기 경로를 한 줄로 줄이면 이렇다.
**이 문서 -> [객체지향 핵심 원리](./object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) -> [Java 오버로딩 vs 오버라이딩 입문](./java-overloading-vs-overriding-beginner-primer.md) -> [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) -> [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)**
템플릿 메소드는 그 다음에 "상속을 좁게 허용하는 예외"로 보면 덜 헷갈린다.

처음 배우는데 "디자인 패턴은 어디부터 보지?"가 바로 나오면 [디자인 패턴 카테고리 인덱스](../../design-pattern/README.md)를 같이 본다. 이 문서에서 잡은 큰 그림을 그대로 이어서 **객체지향 핵심 원리 -> 상속보다 조합 -> 패턴 기초** route로 연결해 주는 beginner route map이다.

## 먼저 잡을 mental model

처음 배우는데 클래스, 객체, 인스턴스가 한꺼번에 나오면 아래 네 칸만 먼저 기억해도 큰 그림이 잡힌다.

| 말 | 처음엔 이렇게 기억 | 코드에서 보이는 모습 |
|---|---|---|
| 클래스 | 객체를 만들기 위한 틀 | `class Student { ... }` |
| 객체 | 실행 중 실제로 만들어진 대상 | `new Student("jane", 20)` |
| 인스턴스 | "어느 클래스에서 만들어졌는가"를 강조한 객체 | "`student`는 `Student`의 인스턴스" |
| 참조 변수 | 객체를 가리키는 손잡이 | `Student student` |

처음엔 이 세 문장으로 충분하다.

- `Student`는 클래스 이름이다.
- `Student student;`는 참조 변수 선언일 뿐, 아직 객체를 만들지 않았다.
- `student = new Student("jane", 20);`가 실행되어야 비로소 객체가 생기고, 그 객체를 `student`가 가리킨다.

## 클래스/객체/인스턴스 3단계 브리지

처음 배우는데 `Student student = new Student("jane", 20);` 한 줄이 복잡하면, 선언과 생성을 분리해서 보면 훨씬 덜 헷갈린다.

| 단계 | 코드 | 실제로 일어나는 일 | 처음 배우는데 체크할 포인트 |
|---|---|---|---|
| 1 | `class Student { ... }` | `Student`라는 타입(설계도)을 정의 | 이 단계에서는 객체가 아직 없다 |
| 2 | `Student student;` | `Student` 객체를 가리킬 참조 변수만 준비 | 변수 선언만으로는 객체가 안 생긴다 |
| 3 | `student = new Student("jane", 20);` | 새 객체를 만들고 변수에 연결 | 이때가 인스턴스화(객체 생성) 순간이다 |

```java
class Student { ... }      // 1) 타입 정의
Student student;           // 2) 참조 변수 선언 (객체 없음)
student = new Student(...);// 3) 객체 생성 + 참조 연결
```

처음엔 아래 두 줄만 기억하면 된다.

- `=` 왼쪽은 "어떤 타입을 가리킬지"를 말하고, 오른쪽 `new`는 "실제 객체를 만드는 동작"이다.
- "객체(object)"와 "인스턴스(instance)"는 입문 단계에서는 거의 같은 말로 써도 된다. 다만 "Student의 인스턴스"처럼 출처를 강조할 때 인스턴스를 쓴다.

## 기본형과 참조형

Java 변수는 크게 **기본형(primitive type)** 과 **참조형(reference type)** 으로 나뉜다.

| 구분 | 무엇을 담는가 | 대표 예시 | `null` 가능 여부 | 특징 |
|---|---|---|---|---|
| 기본형 | 값 자체 | `byte`, `short`, `int`, `long`, `float`, `double`, `char`, `boolean` | 불가 | 작고 단순한 값 표현에 적합 |
| 참조형 | 객체를 가리키는 참조 | `String`, 배열, 클래스, 인터페이스 타입, `Integer` 같은 wrapper | 가능 | 객체의 상태와 동작을 함께 다룰 수 있음 |

### 기본형은 "값 자체"를 다룬다

```java
int age = 20;
boolean enrolled = true;
```

기본형 변수는 숫자, 문자, 논리값 같은 단순 데이터를 직접 표현한다. 초보자 관점에서는 "변수에 실제 값이 들어 있다"고 이해하면 충분하다.

### 참조형은 "객체를 가리킨다"

```java
String name = "jane";
int[] scores = {90, 80, 70};
Student student = new Student("jane", 20);
```

`String`, 배열, 클래스 타입 변수는 객체 자체를 복사하는 것이 아니라 **그 객체를 참조하는 값**을 가진다. 그래서 같은 객체를 여러 변수가 함께 가리킬 수 있다.

```java
Student first = new Student("jane", 20);
Student second = first;

second.increaseAge();
System.out.println(first.getAge()); // 21
```

`second = first`는 새로운 학생 객체를 만든 것이 아니라 같은 객체를 함께 바라보게 만든 것이다.

### 초보자가 기억할 최소 규칙

- 기본형은 단순 값 표현에 쓴다.
- 참조형은 여러 값을 묶은 "대상"을 표현할 때 쓴다.
- `String`은 참조형이다.
- `Integer`, `Long`, `Boolean`은 기본형이 아니라 wrapper 참조형이다.
- 참조형 변수는 `null`이 될 수 있지만, 기본형 변수는 `null`이 될 수 없다.

## 클래스, 객체, 인스턴스

### 클래스는 설계도다

클래스는 "어떤 데이터를 가지고, 어떤 동작을 할 수 있는가"를 정의하는 사용자 정의 타입이다.

```java
public class Student {
    private final String name;
    private int age;

    public Student(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public void increaseAge() {
        age++;
    }

    public int getAge() {
        return age;
    }
}
```

이 클래스는 다음을 함께 정의한다.

- 필드(field): 객체가 기억해야 하는 상태
- 생성자(constructor): 객체를 생성할 때 필요한 초기화 규칙
- 메서드(method): 객체가 수행할 수 있는 동작

### 객체와 인스턴스는 실행 중인 실체다

```java
Student student = new Student("jane", 20);
```

위 코드가 실행되면 `Student`라는 클래스로부터 실제 대상이 하나 만들어진다. 이를 흔히 **객체(object)** 또는 **인스턴스(instance)** 라고 부른다.

- 클래스: "이런 학생이라는 타입을 만들 수 있다"는 정의
- 객체/인스턴스: 실제로 메모리에 만들어진 학생 하나

실무와 면접에서는 두 용어를 거의 비슷하게 쓰지만, 초보자에게는 "클래스는 설계도, 객체는 만들어진 결과"로 구분해 두면 충분하다.

### 코드에서 헷갈리기 쉬운 세 조각

| 코드 조각 | 무엇인가 | 처음 배우는데 자주 하는 착각 |
|---|---|---|
| `Student` | 클래스 이름 | 객체 이름이라고 생각 |
| `student` | 참조 변수 이름 | 객체 자체가 변수 안에 통째로 들어 있다고 생각 |
| `new Student("jane", 20)` | 새 객체를 만드는 표현식 | 선언만 해도 객체가 생긴다고 생각 |

즉 `Student student = new Student("jane", 20);`는 "클래스 `Student`로 객체 하나를 만들고, 참조 변수 `student`가 그 객체를 가리키게 한다"는 뜻이다.

### 생성자는 객체의 시작 상태를 정한다

생성자는 객체가 만들어질 때 호출된다.

```java
Student student = new Student("jane", 20);
```

이 문장에서 생성자는 `"jane"`과 `20`을 받아 `Student`의 시작 상태를 정한다.
즉 "생성자"는 단순 문법이 아니라 **객체가 잘못된 상태로 태어나지 않게 하는 첫 번째 규칙**이다.

## 인터페이스와 추상 클래스

초보자는 둘 다 "완전하지 않은 타입"처럼 보여 헷갈리기 쉽다. 하지만 역할이 다르다.

### 인터페이스는 "무엇을 할 수 있는가"를 표현한다

```java
public interface DiscountPolicy {
    int discount(int price);
}
```

인터페이스는 구현보다 **계약(contract)** 에 가깝다.

- "이 타입은 어떤 기능을 제공해야 한다"
- "이 메서드 이름과 시그니처를 따라야 한다"
- "구현체는 여러 개일 수 있다"

그래서 인터페이스는 **역할**, **기능 약속**, **다형성의 진입점**을 표현할 때 자주 쓴다.

### 추상 클래스는 "공통 상태와 공통 구현"을 묶는다

```java
public abstract class Member {
    private final String name;

    protected Member(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public abstract int gradeDiscount(int price);
}
```

추상 클래스는 다음이 필요할 때 잘 맞는다.

- 하위 클래스들이 공유해야 하는 필드가 있다
- 공통 메서드 구현을 미리 제공하고 싶다
- 기본 골격은 같고 일부 동작만 자식이 바꾸게 하고 싶다

### 초보자용 선택 기준

| 질문 | 인터페이스가 더 자연스러운 경우 | 추상 클래스가 더 자연스러운 경우 |
|---|---|---|
| 핵심 목적이 무엇인가 | 역할과 계약을 정의 | 공통 상태와 공통 구현을 재사용 |
| 여러 타입이 동시에 구현해야 하나 | 그렇다 | 아니다. Java는 클래스 단일 상속만 가능 |
| 공통 필드가 필요한가 | 보통 아니다 | 그렇다 |
| "무엇을 할 수 있는가"가 중요한가 | 그렇다 | 덜 그렇다 |

한 문장으로 줄이면 다음과 같다.

- 인터페이스: `can-do`
- 추상 클래스: 공통 상태를 가진 `base type`

## 핵심 OOP 원리

초보자는 OOP 원리를 정의로 외우기보다, 코드에서 어떤 선택을 뜻하는지 이해하는 편이 낫다.

### 1. 캡슐화

객체의 내부 상태를 함부로 밖에서 바꾸지 못하게 하고, 필요한 동작만 공개하는 것이다.

```java
public class BankAccount {
    private int balance;

    public void deposit(int amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
        balance += amount;
    }

    public int getBalance() {
        return balance;
    }
}
```

`balance`를 `private`으로 숨기고 `deposit()`을 통해서만 변경하게 하면, 객체가 스스로 자기 규칙을 지킬 수 있다.

### 2. 추상화

복잡한 현실에서 필요한 관점만 뽑아 타입으로 표현하는 것이다.

- `Student`는 이름, 나이, 학번이 중요할 수 있다.
- 하지만 "좋아하는 음식"이 지금 문제에 필요 없다면 클래스에 넣지 않아도 된다.

즉 추상화는 "모든 것을 담는 것"이 아니라 **지금 문제를 푸는 데 필요한 속성과 동작만 고르는 것**이다.

### 3. 상속

기존 클래스의 특성을 이어받아 확장하는 것이다.

```java
public class VipMember extends Member {
    public VipMember(String name) {
        super(name);
    }

    @Override
    public int gradeDiscount(int price) {
        return price / 10;
    }
}
```

단, 상속은 문법이 가능하다고 바로 쓰는 것이 아니다.
`VipMember is a Member`처럼 **논리적인 is-a 관계**가 자연스러울 때 사용해야 한다.

### 4. 다형성

같은 인터페이스나 상위 타입으로 여러 구현체를 다르게 다룰 수 있는 능력이다.

```java
DiscountPolicy policy = new FixedDiscountPolicy();
int discounted = policy.discount(10000);
```

여기서 중요한 점은 호출하는 쪽이 `FixedDiscountPolicy`의 내부 구현을 몰라도 된다는 것이다.
즉 다형성은 "구현 교체를 쉽게 만드는 구조"다.

## 코드로 한 번에 보기

아래 예시는 기본형/참조형, 클래스/객체, 인터페이스, 추상 클래스, 다형성을 한 흐름으로 묶는다.

```java
public interface DiscountPolicy {
    int discount(int price);
}

public class FixedDiscountPolicy implements DiscountPolicy {
    private final int amount; // primitive field

    public FixedDiscountPolicy(int amount) {
        this.amount = amount;
    }

    @Override
    public int discount(int price) {
        return amount;
    }
}

public abstract class Member {
    private final String name; // reference field

    protected Member(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public abstract int discountPrice(int price, DiscountPolicy policy);
}

public class VipMember extends Member {
    public VipMember(String name) {
        super(name);
    }

    @Override
    public int discountPrice(int price, DiscountPolicy policy) {
        return price - policy.discount(price);
    }
}
```

이 코드를 초보자 관점에서 읽으면 다음이 보이면 된다.

- `amount`는 기본형 `int`다.
- `name`과 `policy`는 참조형이다.
- `DiscountPolicy`는 역할을 나타내는 인터페이스다.
- `Member`는 공통 상태를 가진 추상 클래스다.
- `VipMember`는 `Member`를 상속한다.
- `policy`를 인터페이스 타입으로 받기 때문에 구현체를 바꿔도 호출 코드는 크게 바뀌지 않는다.

## 초보자가 자주 헷갈리는 포인트

### `String`은 기본형이 아니다

문자열은 많이 써서 특별해 보이지만 `String`은 객체다. 따라서 참조형이다.

### `==`와 `.equals()`는 같은 비교가 아니다

기본형은 보통 `==`로 값 비교를 하지만, 참조형은 같은 객체를 가리키는지와 내용이 같은지를 구분해야 한다.
예를 들어 `String` 내용 비교는 보통 `.equals()`를 사용한다.

### `new`를 쓸 때마다 항상 다른 객체가 만들어진다

`new Student(...)`를 호출하면 새 객체가 생성된다.
반면 `Student b = a;`는 새 객체 생성이 아니라 참조 복사다.

### 인터페이스는 "가벼운 클래스"가 아니다

인터페이스는 구현체의 공통 부모가 아니라 **공통 계약**이라는 관점으로 이해해야 한다.

### 추상 클래스는 객체를 직접 만들 수 없다

`abstract`가 붙은 클래스는 공통 뼈대만 정의하는 타입이므로 직접 `new` 할 수 없다.

### 상속보다 조합이 더 나을 때도 많다

상속은 강한 결합을 만들 수 있다.
공통 기능 공유보다 역할 조합이 더 중요하면 인터페이스와 필드 조합이 더 자연스러울 수 있다.

### 처음 배우는데 "상속을 언제 쓰는지" 헷갈리면

큰 그림은 먼저 이렇게 자르면 된다.

- 부모 클래스가 **공통 순서를 끝까지 고정**해야 한다면 템플릿 메소드 쪽 질문이다.
- 동작이나 정책을 **객체로 갈아끼워야** 한다면 상속보다 조합 쪽 질문이다.
- 이유가 "코드 재사용이 쉬워 보여서"라면 상속을 바로 고르지 말고 조합을 먼저 의심한다.

이 감각을 이어서 보고 싶다면 [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)로 먼저 큰 그림을 잡고, 상속이 허용되는 좁은 예외를 [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md), 조합과 상속의 비교를 [템플릿 메소드 vs 전략](../../design-pattern/template-method-vs-strategy.md)에서 이어 보면 된다.

## 어떤 문서를 다음에 읽으면 좋은가

- 변수, 제어문, 배열, 형변환까지 문법을 먼저 다지고 싶다면 [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- 메서드, 생성자, parameter, return type, overloading을 한 클래스 흐름으로 묶어 보고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- 클래스/객체/인스턴스 차이를 캡슐화, 추상화, 상속, 다형성 큰 그림으로 이어서 보고 싶다면 [객체지향 핵심 원리](./object-oriented-core-principles.md)
- `extends`, overriding, `@Override`, dynamic dispatch를 작은 예제로 이어 보고 싶다면 [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)
- 처음 배우는데 "상속을 언제 쓰는지", "추상 클래스와 인터페이스를 어디서 나누는지", "상속 vs 조합을 어떻게 보나"가 궁금하다면 [객체지향 핵심 원리](./object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) -> [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) -> [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) 순서가 가장 안전하다
- 접근 제한자, `static`, `final`을 클래스 모델과 함께 잡고 싶다면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 처음 배우는데 디자인 패턴을 어디부터 볼지 막히면 [디자인 패턴 카테고리 인덱스](../../design-pattern/README.md)에서 **상속보다 조합 -> 패턴 기초** route map부터 타면 된다

## 한 줄 정리

Java 입문에서는 "문법을 외운다"보다 "타입이 값인지 객체인지, 클래스가 설계도인지 실행 중 객체인지, 인터페이스와 추상 클래스가 어떤 설계 역할을 갖는지"를 연결해 이해하는 것이 더 중요하다.
