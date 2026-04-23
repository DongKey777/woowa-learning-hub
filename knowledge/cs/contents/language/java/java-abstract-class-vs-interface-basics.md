# 추상 클래스 vs 인터페이스 입문

> 한 줄 요약: 추상 클래스는 "같은 부모를 공유하는 is-a 관계"에서 구현을 물려줄 때 쓰고, 인터페이스는 "능력/계약을 여러 타입에 붙일 때" 쓴다.

**난이도: 🟢 Beginner**

관련 문서:

- [sealed-interfaces-exhaustive-switch-design](./sealed-interfaces-exhaustive-switch-design.md)
- [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)
- [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)
- [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md)
- [템플릿 메소드 vs 전략](../../design-pattern/template-method-vs-strategy.md)
- [language 카테고리 인덱스](../README.md)
- [software-engineering repository-dao-entity](../../software-engineering/repository-dao-entity.md)

retrieval-anchor-keywords: abstract class vs interface beginner, java interface basics, java abstract class basics, 추상클래스 인터페이스 차이 입문, when to use interface java, java implements vs extends, default method interface beginner, abstract method basics, java multiple interface, interface contract basics, 인터페이스 언제 써요, 추상클래스 언제 써요, 처음 배우는데 추상 클래스 인터페이스 차이, 추상 클래스 인터페이스 큰 그림, 추상 클래스 인터페이스 기초, abstract class vs interface when to use beginner, 상속 vs 조합 기초, 추상 클래스 vs 조합, 인터페이스와 조합, 추상 클래스 템플릿 메소드 언제 쓰는지, abstract class template method beginner, inheritance vs composition java beginner, extends vs implements vs composition, 부모 클래스 흐름 고정 vs 전략 객체 주입

## 핵심 개념

추상 클래스(abstract class)와 인터페이스(interface)는 둘 다 "직접 인스턴스를 만들 수 없고, 하위 타입에서 구현을 채워야 한다"는 점이 같다. 하지만 목적이 다르다.

입문자가 자주 헷갈리는 건 "둘 다 미완성인데 뭐가 다른가"다. 핵심 질문은 **관계의 종류**다.

- 공통 구현을 물려주는 부모가 필요하다 → 추상 클래스
- 여러 타입에 특정 능력(계약)을 붙이고 싶다 → 인터페이스

## 큰 그림: 상속, 조합, 템플릿 메소드와 연결하기

처음 배우는데 추상 클래스와 인터페이스를 표로만 외우면 "언제 쓰는지"가 잘 남지 않는다. 먼저 이렇게 잡으면 된다.

- 추상 클래스는 **부모 클래스가 공통 상태나 흐름을 쥐고**, 자식이 빈칸만 채우는 쪽이다.
- 인터페이스는 **이 타입이 할 수 있는 일의 약속을 세우고**, 구현체는 조합/DI로 갈아끼우는 쪽이다.
- 단지 중복 코드를 줄이고 싶다는 이유라면 상속보다 조합을 먼저 의심한다.

| 처음 묻는 질문 | 먼저 떠올릴 선택 | 이유 | 다음에 읽을 문서 |
|---|---|---|---|
| "부모가 순서를 고정하고 단계만 바꾸고 싶다" | 추상 클래스 + 템플릿 메소드 | 부모가 전체 흐름을 `final`로 잡고 자식이 일부 단계만 구현한다 | [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md) |
| "결제 정책, 저장소 구현처럼 바꿔 끼우고 싶다" | 인터페이스 + 조합 | 서비스는 계약만 알고 실제 구현은 주입받는다 | [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) |
| "흐름을 부모가 쥐어야 하나, 호출자가 고르게 해야 하나" | 템플릿 메소드 vs 전략 비교 | 상속 skeleton인지 전략 객체 주입인지 먼저 나눈다 | [템플릿 메소드 vs 전략](../../design-pattern/template-method-vs-strategy.md) |

### 템플릿 메소드 쪽 예시

```java
abstract class AbstractImporter {
    public final void importAll() {
        read();
        validate();
        save();
    }

    protected abstract void read();
    protected void validate() { System.out.println("공통 검증"); }
    protected abstract void save();
}
```

이 구조에서는 `importAll()`의 순서가 흔들리면 안 된다. 그래서 부모 추상 클래스가 흐름을 고정하고, 자식 클래스는 `read()`와 `save()`만 채운다.

### 조합 쪽 예시

```java
interface DiscountPolicy {
    int discount(int price);
}

class OrderService {
    private final DiscountPolicy discountPolicy;

    OrderService(DiscountPolicy discountPolicy) {
        this.discountPolicy = discountPolicy;
    }

    int pay(int price) {
        return price - discountPolicy.discount(price);
    }
}
```

이 구조에서는 할인 정책을 런타임 설정이나 테스트에서 바꿔 끼우는 것이 자연스럽다. `OrderService`가 부모 클래스를 상속받는 대신 `DiscountPolicy`라는 계약을 필드로 가진다.

## 한눈에 보기

| 항목 | 추상 클래스 | 인터페이스 |
|---|---|---|
| 키워드 | `abstract class` | `interface` |
| 상속 | `extends` (단일) | `implements` (다중 가능) |
| 인스턴스 변수 | 가질 수 있음 | 상수만 (`public static final`) |
| 생성자 | 있음 | 없음 |
| 구현 메서드 | 가질 수 있음 | `default` / `static`으로만 |
| 목적 | 공통 구현 공유 (is-a) | 계약/능력 선언 (can-do) |
| 설계 연결 | 템플릿 메소드처럼 부모가 흐름을 고정 | 조합/전략처럼 구현을 갈아끼움 |

## 상세 분해

### 추상 클래스 예시

```java
abstract class Shape {
    private String color;

    public Shape(String color) {
        this.color = color;
    }

    public String getColor() { return color; }

    public abstract double area(); // 하위 클래스가 반드시 구현
}

class Circle extends Shape {
    private double radius;

    public Circle(String color, double radius) {
        super(color);
        this.radius = radius;
    }

    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
}
```

`Shape`는 `color`라는 공통 상태와 `getColor()` 구현을 제공하면서, `area()`는 각 도형이 다르게 구현하도록 강제한다.

### 인터페이스 예시

```java
interface Printable {
    void print(); // 구현 없는 추상 메서드
}

interface Exportable {
    void export(String format);
}

class Report implements Printable, Exportable {
    @Override
    public void print() { System.out.println("출력"); }

    @Override
    public void export(String format) { System.out.println(format + " 내보내기"); }
}
```

`Report`는 `Printable`과 `Exportable`이라는 두 가지 능력을 동시에 가질 수 있다. Java는 다중 상속을 허용하지 않지만 인터페이스는 여러 개를 `implements`할 수 있다.

## 흔한 오해와 함정

**오해 1: 인터페이스에는 구현이 없다**
Java 8부터 `default` 메서드로 기본 구현을 제공할 수 있다. 단, 이것은 인터페이스의 예외적 기능이지 기본 사용 방식이 아니다.

**오해 2: 추상 클래스가 더 강력하니 항상 쓰면 된다**
Java는 단일 상속만 지원하므로 추상 클래스를 쓰면 다른 클래스를 상속할 수 없다. 인터페이스는 여러 개를 구현할 수 있어 더 유연하다.

**오해 3: 인터페이스는 상수만 선언할 수 있다**
상수는 선언할 수 있지만, 그 용도로만 인터페이스를 쓰는 것은 안티패턴이다. 인터페이스는 타입 계약 선언에 집중해야 한다.

**오해 4: 추상 클래스는 중복 제거용 도구다**
중복 제거만 목적이면 부모-자식 결합이 너무 강해질 수 있다. "같은 종류라서 부모 흐름을 공유한다"가 아니라 "필요한 기능을 가져다 쓴다"에 가깝다면 [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)를 먼저 본다.

## 실무에서 쓰는 모습

Spring 프로젝트에서 `Repository` 인터페이스를 만들고 여러 구현체(JPA 기반, JDBC 기반 등)를 갈아끼우는 구조가 대표적이다.

1. `UserRepository` 인터페이스에 `findById`, `save` 등 계약 선언
2. `JpaUserRepository`, `InMemoryUserRepository`가 각각 구현
3. 서비스 계층은 인터페이스 타입만 알고, 구현체는 Spring DI가 주입

이 덕분에 테스트 시 `InMemoryUserRepository`로 교체해도 서비스 코드는 바뀌지 않는다.

## 더 깊이 가려면

- sealed interface와 패턴 매칭의 연결은 [sealed-interfaces-exhaustive-switch-design](./sealed-interfaces-exhaustive-switch-design.md)
- Repository 패턴에서 인터페이스가 어떻게 쓰이는지는 [Repository, DAO, Entity](../../software-engineering/repository-dao-entity.md)
- "상속을 써도 되는 좁은 경우"와 조합의 차이는 [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)
- 추상 클래스가 알고리즘 흐름을 고정하는 대표 구조는 [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md)

## 면접/시니어 질문 미리보기

**Q. 추상 클래스와 인터페이스 중 어떤 것을 선택하나?**
공통 상태/구현을 물려줘야 하면 추상 클래스, 타입 계약만 필요하면 인터페이스. 대부분의 실무 설계는 인터페이스를 우선 선택한다.

**Q. 인터페이스에 `default` 메서드를 왜 넣나?**
라이브러리 설계 시 기존 구현체를 변경하지 않고 인터페이스에 새 메서드를 추가하려고 도입했다. 남용하면 설계를 복잡하게 만든다.

**Q. 추상 클래스도 `implements`로 인터페이스를 구현할 수 있나?**
가능하다. 추상 클래스는 인터페이스 메서드를 일부만 구현하고 나머지는 하위에 위임할 수도 있다.

## 한 줄 정리

추상 클래스는 공통 구현을 물려주는 부모 역할이고, 인터페이스는 여러 타입에 붙일 수 있는 계약 선언이다.
