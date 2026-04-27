# Java enum 기초

> 한 줄 요약: enum은 미리 정의한 상수 집합을 타입으로 만들어서, 정수 상수 대신 이름 있는 값으로 컴파일 시점에 안전하게 사용하는 기능이다.

**난이도: 🟢 Beginner**

관련 문서:

- [enum-persistence-json-unknown-value-evolution](./enum-persistence-json-unknown-value-evolution.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [language 카테고리 인덱스](../README.md)
- [Java 예외 처리 기초](./java-exception-handling-basics.md)

retrieval-anchor-keywords: java enum basics, enum 입문, 열거형 기초, enum 왜 쓰나요, enum vs 상수 정수, java enum switch, enum values ordinal, enum 상수 집합, beginner enum java, 열거형 사용법, java enum name ordinal, java 상태값 enum, enum 처음 배우는데, enum 큰 그림, enum 언제 쓰는지, 상태값 int 대신 enum, ordinal 쓰면 안되는 이유, enum name 저장 이유, switch enum 기초

## 핵심 개념

`enum`은 고정된 상수 집합을 하나의 타입으로 선언하는 방법이다. 예를 들어 요일, 주문 상태, 방향 같이 미리 정해진 값들만 쓸 수 있는 경우에 쓴다.

정수 상수(`static final int MONDAY = 0`)로 대체할 수 있지만, 정수는 컴파일러가 의미를 모른다. `setDay(0)` 대신 `setDay(Day.MONDAY)`로 쓰면 잘못된 값 전달을 컴파일 시점에 막을 수 있다.

입문자가 헷갈리는 지점은 enum도 클래스처럼 메서드와 필드를 가질 수 있다는 것이다. 단순 상수 이상이다.

## 한눈에 보기

```
// 정수 상수 방식 (오류 가능성 있음)
static final int STATUS_WAIT   = 0;
static final int STATUS_ACTIVE = 1;
void process(int status) { ... }  // process(999) 컴파일 통과

// enum 방식 (타입 안전)
enum OrderStatus { WAIT, ACTIVE, DONE }
void process(OrderStatus status) { ... }  // process(OrderStatus.WAIT)만 가능
```

## 상세 분해

### 기본 선언과 사용

```java
public enum Direction { NORTH, SOUTH, EAST, WEST }

Direction d = Direction.NORTH;
System.out.println(d.name());    // "NORTH"
System.out.println(d.ordinal()); // 0 (선언 순서 인덱스)
```

`name()`은 선언한 이름 문자열, `ordinal()`은 0부터 시작하는 순서 인덱스를 반환한다.

### switch에서 활용

```java
OrderStatus status = OrderStatus.WAIT;
switch (status) {
    case WAIT   -> System.out.println("대기 중");
    case ACTIVE -> System.out.println("처리 중");
    case DONE   -> System.out.println("완료");
}
```

switch 표현식과 잘 어울리며, 빠진 케이스를 IDE나 컴파일러가 경고해 준다.

### 필드와 메서드를 가진 enum

```java
public enum Planet {
    EARTH(5.97e24, 6.37e6),
    MARS (6.42e23, 3.39e6);

    private final double mass;
    private final double radius;

    Planet(double mass, double radius) {
        this.mass   = mass;
        this.radius = radius;
    }

    public double surfaceGravity() {
        return 6.674e-11 * mass / (radius * radius);
    }
}
```

enum 상수에 값을 붙이고 메서드를 정의할 수 있다. 상태별 로직을 enum 안에 캡슐화하는 패턴이다.

## 흔한 오해와 함정

**오해 1: `ordinal()` 값을 DB에 저장하면 된다**
enum 순서가 바뀌거나 중간에 상수가 삽입되면 ordinal이 밀린다. DB에는 `name()`(문자열)을 저장하는 것이 안전하다.

**오해 2: `==`와 `equals()`가 다르게 동작한다**
enum 상수는 싱글턴이므로 `==`와 `equals()` 모두 같은 결과를 낸다. 관용적으로는 `==`를 쓴다.

**오해 3: `Enum.values()`는 항상 선언 순서대로다**
맞다. 하지만 ordinal에 의존한 로직을 짜면 상수 추가 시 버그가 생긴다. 순서 의존을 피하고 필드로 순서를 관리하는 것이 낫다.

## 실무에서 쓰는 모습

주문 도메인에서 상태 전이를 enum으로 표현한다.

1. `OrderStatus { PENDING, PAID, SHIPPED, DELIVERED, CANCELLED }` 선언
2. 서비스에서 `order.getStatus() == OrderStatus.PENDING` 조건 체크
3. JPA에서 `@Enumerated(EnumType.STRING)`으로 문자열로 DB 저장
4. 잘못된 상태 값이 API로 들어오면 `IllegalArgumentException`으로 처리

## 더 깊이 가려면

- JSON 직렬화·DB 저장 시 unknown 값 처리: [enum-persistence-json-unknown-value-evolution](./enum-persistence-json-unknown-value-evolution.md)

## 면접/시니어 질문 미리보기

**Q. enum이 일반 클래스와 다른 점은?**
모든 생성자가 `private`이고, 인스턴스는 선언된 상수들뿐이다. 외부에서 `new`로 만들 수 없다. 또한 암묵적으로 `java.lang.Enum`을 상속한다.

**Q. enum을 Map의 키로 쓸 때 `HashMap` 대신 `EnumMap`을 쓰는 이유는?**
`EnumMap`은 ordinal 기반 배열로 구현되어 `HashMap`보다 빠르고 메모리 효율이 높다. 키가 enum으로 고정된 경우 항상 `EnumMap`이 유리하다.

**Q. enum에서 abstract 메서드를 선언할 수 있는가?**
가능하다. 상수별 구현을 강제하는 패턴으로, 각 상수가 abstract 메서드를 오버라이드한다.

## 한 줄 정리

enum은 컴파일 시점에 안전한 상수 집합 타입이고, 정수 상수 대신 쓰면 잘못된 값 전달을 원천 차단할 수 있다.
