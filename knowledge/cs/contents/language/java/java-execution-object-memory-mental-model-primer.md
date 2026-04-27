# Java 실행 모델과 객체 메모리 mental model 입문

> 한 줄 요약: Java 초보자가 `.java -> .class -> JVM`, class/object/instance, `static`/instance, stack/heap intuition을 한 장의 흐름으로 연결해 이해하도록 돕는 primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- [Stack vs Heap Escape Intuition](./stack-vs-heap-escape-intuition.md)
- [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
- [가상 메모리 기초](../../operating-system/virtual-memory-basics.md)

retrieval-anchor-keywords: java execution model basics, java source to bytecode, java jvm execution beginner, java class object instance difference, java static vs instance basics, java stack heap intuition, java reference variable basics, java object memory mental model, 자바 실행 모델 입문, 클래스 객체 인스턴스 차이, static instance 차이, stack heap 기초

## 핵심 개념

Java를 처음 읽을 때 가장 많이 꼬이는 이유는 문법, 객체, 메모리 이야기가 서로 다른 챕터에 흩어져 있기 때문이다.

초보자 기준으로는 아래 다섯 줄을 먼저 한 세트로 잡으면 된다.

- `.java`는 사람이 읽는 소스 코드다.
- `javac`는 소스를 `.class` 바이트코드로 바꾼다.
- JVM은 그 바이트코드를 읽고 실행한다.
- `class`는 설계도고, `new`를 호출할 때마다 `object`가 만들어진다.
- 메서드 안 지역 변수는 호출 단위로 따로 생기고, 그 변수가 가리키는 객체는 보통 별도 공간에 존재한다고 이해하면 출발점으로 충분하다.

즉 Java 입문은 문법 암기보다 **"무엇이 정의이고, 무엇이 실행 중 실체이며, 무엇이 공유되고, 무엇이 호출마다 새로 생기는가"** 를 구분하는 일에 가깝다.

## 한눈에 보기

```text
OrderApp.java
  -> javac
OrderApp.class
  -> JVM starts
Order class loaded
  -> main(...) stack frame created
  -> new Order("ramen", 2)
  -> Order object created
  -> order.addQuantity(1)
```

| 구분 | 지금 잡을 mental model | 초보자 체크 포인트 |
|---|---|---|
| source code | 사람이 작성하는 `.java` | 타입, 문법, 메서드 이름이 여기서 결정된다 |
| bytecode | `javac`가 만든 `.class` | JVM이 읽을 중간 형식이다 |
| JVM execution | 바이트코드를 실제로 실행하는 단계 | `main`이 시작되고 메서드 호출이 쌓인다 |
| class | 필드와 메서드를 정의한 설계도 | `Order` 자체는 객체 하나가 아니다 |
| object / instance | `new Order(...)`로 만들어진 실제 대상 | 같은 class로 여러 개 만들 수 있다 |
| instance member | 객체마다 따로 가진 상태/동작 | `first.quantity`, `second.quantity`는 다를 수 있다 |
| `static` member | class 하나당 공유하는 상태/동작 | 모든 `Order`가 함께 본다 |
| stack / heap intuition | 지역 변수는 호출 단위, 객체는 참조 대상 | 변수와 객체를 같은 것으로 보면 자주 틀린다 |

## 상세 분해

### 1. source -> bytecode -> JVM

```java
class Order {
    private final String menuName;

    Order(String menuName) {
        this.menuName = menuName;
    }
}
```

이 코드를 저장한 뒤 `javac`로 컴파일하면 JVM이 읽을 수 있는 `.class`가 생긴다.
중요한 포인트는 "소스가 바로 CPU 기계어로 가는 것"이 아니라, **Java는 바이트코드를 거쳐 JVM 위에서 실행된다**는 점이다.

초보자 단계에서는 다음 정도만 분리하면 충분하다.

- compile time: 문법/타입/이름을 검사한다
- runtime: JVM이 클래스를 로드하고 메서드를 실제로 실행한다

### 2. class vs object vs instance

```java
class Order {
    private final String menuName;
    private int quantity;

    Order(String menuName, int quantity) {
        this.menuName = menuName;
        this.quantity = quantity;
    }
}
```

`Order`는 "이런 주문 데이터를 가진 대상을 만들 수 있다"는 정의다.
아래 코드가 실행될 때 실제 주문 둘이 만들어진다.

```java
Order first = new Order("ramen", 2);
Order second = new Order("dumpling", 1);
```

| 용어 | 입문자용 뜻 |
|---|---|
| `class` | 어떤 필드와 메서드를 가질지 적어 둔 설계도 |
| `object` | 실행 중 실제로 만들어진 대상 |
| `instance` | 어떤 class의 object라는 관계를 강조한 말 |
| reference variable | object 자체가 아니라 그 object를 가리키는 변수 |

실무에서는 object와 instance를 거의 비슷하게 쓰지만, 입문 단계에서는 **"class는 정의, object는 결과"** 로만 구분해도 충분하다.

### 3. `static` vs instance

```java
class Order {
    private static int createdCount = 0;

    private final String menuName;
    private int quantity;

    Order(String menuName, int quantity) {
        this.menuName = menuName;
        this.quantity = quantity;
        createdCount++;
    }

    void addQuantity(int amount) {
        quantity += amount;
    }

    static int getCreatedCount() {
        return createdCount;
    }
}
```

`quantity`는 주문 객체마다 다르다. 반면 `createdCount`는 모든 주문이 함께 보는 값이다.

| 질문 | instance | `static` |
|---|---|---|
| 누구 소유인가 | 객체 하나 | class 전체 |
| 호출 모양 | `first.addQuantity(1)` | `Order.getCreatedCount()` |
| 개수 | 객체마다 따로 | class당 한 번 공유 |
| `this` 필요 여부 | 필요하다 | 없다 |

입문 단계에서는 "`static`은 편한 전역 변수"가 아니라 **class 수준 공유 상태/동작**으로 읽는 습관이 중요하다.

### 4. stack / heap intuition

아래 코드를 실행한다고 생각해 보자.

```java
Order first = new Order("ramen", 2);
Order second = first;
second.addQuantity(1);
```

초보자에게 유용한 첫 그림은 이렇다.

```text
main stack frame
- first  -> Order object A
- second -> Order object A

shared class-level state
- Order.createdCount = 1

object area (heap intuition)
- Order object A { menuName="ramen", quantity=3 }
```

핵심은 두 가지다.

- `second = first`는 주문 객체를 하나 더 만든 것이 아니라, 같은 객체를 같이 가리키게 만든다.
- 지역 변수 `first`, `second`와 실제 주문 객체를 구분해야 side effect를 설명할 수 있다.

정확한 JVM 구현은 더 복잡하지만, beginner 단계에서는 **"메서드 호출마다 지역 변수 공간이 생기고, 객체는 그 변수가 가리키는 대상이다"** 라는 감각이면 충분하다.

## 흔한 오해와 함정

### "`new`를 하면 변수 안에 객체 전체가 들어간다"

아니다. 변수는 보통 객체를 가리키는 참조를 들고 있다고 이해해야 한다. 그래서 `second = first` 뒤에 한쪽으로 상태를 바꾸면 다른 쪽에서도 같은 변경이 보인다.

### "`static`이면 어디서나 막 써도 된다"

편하다고 해서 인스턴스 상태를 `static`으로 올리면 객체 경계가 무너진다. 백엔드 코드에서는 요청마다 다른 값, 주문마다 다른 값은 보통 instance field가 맞다.

### "object와 instance는 완전히 다른 시험용 용어다"

입문 단계에서는 거의 같은 뜻으로 봐도 된다. 다만 "어떤 class의 instance"라고 말할 때 class와의 관계가 더 분명해진다.

### "stack / heap 그림이 JVM의 정확한 내부 구조다"

아니다. 그 그림은 초보자용 생각 도구다. JIT 최적화나 실제 HotSpot 구현까지 들어가면 더 복잡하다. 이 단계에서는 local variable과 object를 구분하는 데 집중하는 편이 낫다.

## 실무에서 쓰는 모습

우아한테크코스 백엔드 미션에서 `Order`, `Cart`, `Menu` 같은 도메인 객체를 읽을 때도 같은 프레임으로 보면 된다.

1. compile time에는 타입과 메서드 이름이 맞는지 잡힌다.
2. runtime에는 요청 흐름 안에서 실제 객체가 만들어지고 메서드가 호출된다.
3. 객체마다 달라야 하는 상태는 instance field에 둔다.
4. 모든 객체가 함께 써야 하는 값만 `static final` 상수나 class-level helper로 둔다.

예를 들어 `Order.createdCount` 같은 진짜 공유 상태는 조심해서 쓰고, `order.quantity`처럼 도메인 상태는 객체 안에 두는 편이 자연스럽다. 디버깅할 때도 "변수가 바뀌었는가?"보다 "같은 객체를 여러 변수가 공유하고 있는가?"를 먼저 보면 side effect를 더 빨리 찾는다.

## 더 깊이 가려면

- source/bytecode/JVM 큰 그림을 먼저 더 단단히 잡고 싶다면 [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- class/object/instance를 OOP 문맥까지 넓히고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- `static`, `private`, `final`을 멤버 모델 관점에서 더 정확히 보고 싶다면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- stack/heap 직관의 한계와 HotSpot 최적화까지 이어서 보고 싶다면 [Stack vs Heap Escape Intuition](./stack-vs-heap-escape-intuition.md)
- OS 관점의 메모리 큰 그림을 같이 보고 싶다면 [가상 메모리 기초](../../operating-system/virtual-memory-basics.md)

## 면접/시니어 질문 미리보기

**Q. Java는 왜 `.java`를 바로 실행하지 않고 `.class`를 거치나요?**
바이트코드라는 중간 형식을 두면 JVM이 여러 OS 환경에서 같은 코드를 실행하고 최적화하기 쉬워진다.

**Q. class와 object의 차이는 무엇인가요?**
class는 필드와 메서드의 정의이고, object는 그 정의를 바탕으로 실행 중에 만들어진 실제 대상이다.

**Q. 왜 서버 코드에서 `static` 가변 상태를 조심하라고 하나요?**
요청마다 분리돼야 할 데이터를 class 전체가 공유해 버리면 테스트와 동시성 버그가 커지기 쉽기 때문이다.

## 한 줄 정리

Java를 읽을 때는 source -> bytecode -> JVM 실행, class -> object 생성, instance -> `static` 소유 차이, 지역 변수 -> 객체 참조 관계를 먼저 분리하면 이후 문법이 훨씬 덜 헷갈린다.
