# 추상 클래스 vs 인터페이스 입문

> 한 줄 요약: 처음 배우는 사람이 "추상 클래스와 인터페이스를 언제 쓰는지" 큰 그림부터 잡도록, 추상 클래스는 "같은 부모를 공유하는 is-a 관계"에서 구현을 물려줄 때 쓰고 인터페이스는 "능력/계약을 여러 타입에 붙일 때" 쓴다는 기준을 기초 질문형으로 정리한 primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md) - 클래스/객체에서 OOP 큰 그림으로 들어가는 첫 출발점이 다시 필요할 때 먼저 보는 primer
- [sealed-interfaces-exhaustive-switch-design](./sealed-interfaces-exhaustive-switch-design.md)
- [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) - "상속 언제 쓰는지"를 먼저 잡고, 그다음 추상 클래스/인터페이스로 넘어오는 바로 전 단계 primer
- [객체지향 핵심 원리](./object-oriented-core-principles.md) - 객체지향 큰 그림에서 상속과 추상화를 먼저 연결한 뒤 이 문서로 내려오고 싶을 때 보는 primer
- [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) - 첫 읽기 bridge는 이 문서 다음에 조합으로 먼저 넘어가도록 고정하는 beginner primer
- [추상 클래스 vs 인터페이스 Follow-up Quick Check](./abstract-class-vs-interface-follow-up-drill.md) - 큰 그림을 잡은 뒤 `공통 상태 vs 계약` 판단을 5개 짧은 예제로 바로 확인하는 follow-up drill
- [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md) - 조합을 기본값으로 잡은 뒤에도 부모가 흐름을 쥐는 좁은 경우를 이어서 보는 follow-up primer
- [템플릿 메소드 vs 전략](../../design-pattern/template-method-vs-strategy.md) - 템플릿 메소드 다음에 상속 skeleton과 전략 주입을 같은 축으로 비교하는 follow-up primer
- [Marker Interface vs Capability Method 브리지](./marker-interface-vs-capability-method-bridge.md)
- [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- [language 카테고리 인덱스 - Java primer](../README.md#java-primer)
- [software-engineering repository-dao-entity](../../software-engineering/repository-dao-entity.md)

retrieval-anchor-keywords: abstract class vs interface beginner, abstract class vs default method card, interface default method vs abstract class state, 추상 클래스 인터페이스 차이 입문, 처음 배우는데 추상 클래스 인터페이스 언제 쓰는지, 추상 클래스 인터페이스 10초 비교표, 공통 상태가 필요하면 추상 클래스, 기본 동작만 있으면 인터페이스, default method에 필드 못 넣나요, 인터페이스에 상태를 넣고 싶어요, extends vs implements beginner, 같은 default method 두 개 충돌, java abstract class vs interface basics basics, java abstract class vs interface basics beginner, java abstract class vs interface basics intro

## 핵심 개념

추상 클래스(abstract class)와 인터페이스(interface)는 둘 다 "직접 인스턴스를 만들 수 없고, 하위 타입에서 구현을 채워야 한다"는 점이 같다. 하지만 목적이 다르다.

입문자가 자주 헷갈리는 건 "둘 다 미완성인데 뭐가 다른가"다. 핵심 질문은 **관계의 종류**다.

- 공통 구현을 물려주는 부모가 필요하다 → 추상 클래스
- 여러 타입에 특정 능력(계약)을 붙이고 싶다 → 인터페이스

## 10초 decision card

처음 배우는데 헷갈리면 이 표부터 본다. 판단 기준은 딱 두 개다. `공통 상태가 필요한가`, `기본 동작만 있으면 충분한가`.

| 지금 상황 | 먼저 고를 쪽 | 10초 이유 |
|---|---|---|
| 필드로 들고 갈 공통 상태가 있다 | 추상 클래스 | 인터페이스 `default method`는 인스턴스 필드를 가질 수 없다 |
| 하위 타입마다 같은 뼈대 메서드와 생성 규칙이 필요하다 | 추상 클래스 | 부모가 상태와 공통 구현을 같이 쥘 수 있다 |
| "이 기능을 할 수 있다"는 계약만 있으면 된다 | 인터페이스 | 여러 타입에 붙이기 쉽고 다중 구현이 가능하다 |
| 간단한 기본 동작 하나를 공짜로 주고 싶다 | 인터페이스 `default method` | 상태 없이도 작은 공통 행동을 제공할 수 있다 |

### 한 줄 컷

- `공통 상태 + 공통 구현`이 같이 필요하다면 추상 클래스를 먼저 의심한다.
- `상태 없이 계약 + 작은 기본 동작`이면 인터페이스 `default method`로 시작한다.
- `default method`가 커지거나 필드가 있었으면 좋겠다는 생각이 들면 추상 클래스나 조합으로 다시 본다.

## 큰 그림: 상속, 조합, 템플릿 메소드와 연결하기

처음 배우는데 추상 클래스와 인터페이스를 표로만 외우면 "언제 쓰는지"가 잘 안 남는다. 이 문서도 `처음 배우는데`, `큰 그림`, `기초`, `언제 쓰는지` 질문형을 그대로 유지한 채 이렇게 잡는다.

- 추상 클래스는 **부모 클래스가 공통 상태나 흐름을 쥐고**, 자식이 빈칸만 채우는 쪽이다.
- 인터페이스는 **이 타입이 할 수 있는 일의 약속을 세우고**, 구현체는 조합/DI로 갈아끼우는 쪽이다.
- 인터페이스 안에서도 "타입 표지(marker)"와 "`supportsX()` 같은 capability 질문"은 같은 층위가 아니므로, interface 설계 첫 진입점이 필요하면 [Marker Interface vs Capability Method 브리지](./marker-interface-vs-capability-method-bridge.md)를 먼저 붙여 본다.
- 단지 중복 코드를 줄이고 싶다는 이유라면 상속보다 조합을 먼저 의심한다.

| 처음 묻는 질문 | 먼저 떠올릴 선택 | 이유 | 다음에 읽을 문서 |
|---|---|---|---|
| "부모가 순서를 고정하고 단계만 바꾸고 싶다" | 추상 클래스 + 템플릿 메소드 | 부모가 전체 흐름을 `final`로 잡고 자식이 일부 단계만 구현한다 | [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md) |
| "결제 정책, 저장소 구현처럼 바꿔 끼우고 싶다" | 인터페이스 + 조합 | 서비스는 계약만 알고 실제 구현은 주입받는다 | [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) |
| "흐름을 부모가 쥐어야 하나, 호출자가 고르게 해야 하나" | 템플릿 메소드 vs 전략 비교 | 상속 skeleton인지 전략 객체 주입인지 먼저 나눈다 | [템플릿 메소드 vs 전략](../../design-pattern/template-method-vs-strategy.md) |

### 템플릿 메소드로 넘길 때 20초 핸드오프

추상 클래스 질문에서 템플릿 메소드 기초로 넘어갈 때는 문장을 그대로 맞춰 읽으면 덜 헷갈린다.

- 템플릿 메소드: **부모가 흐름을 쥔다**
- 전략/조합: **호출자가 전략을 고른다**
- 템플릿 메소드 내부 슬롯은 **필수 슬롯(`abstract step`) vs 선택 슬롯(`hook`)**으로 본다

즉 "추상 클래스냐 인터페이스냐"를 묻다가도, 실제로는 "부모가 전체 순서를 고정해야 하는가" 질문이면 [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md)로 바로 이어서 보는 게 맞다.

### 템플릿 메소드 쪽 예시

## 큰 그림: 상속, 조합, 템플릿 메소드와 연결하기 (계속 2)

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

## 처음 읽는 순서

처음 읽기 경로를 짧게 잡으면 **[객체지향 핵심 원리](./object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) -> 이 문서 -> [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)** 순서다. 이 문서는 그 가운데서 "상속을 배운 뒤, 추상 클래스와 인터페이스를 어떻게 자르고 조합으로 넘어갈지"를 연결하는 다리 역할이다.

초급 질의가 `처음 배우는데 추상 클래스 인터페이스 차이`로 바로 들어와도, retrieval은 위 순서를 되살려 같은 chain으로 붙는 편이 안전하다. 즉 이 문서는 단독 종착지가 아니라 `상속 언제 쓰는지` 질문과 `상속 vs 조합 언제 쓰는지` 질문이 같은 beginner primer route로 다시 모이는 중간 허브다.

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
처음 배우는데 `default method`가 보이면 "핵심 계약"인지, "기존 구현체를 덜 깨뜨리기 위한 evolution용 기본값"인지부터 나누어 보는 편이 좋다. 이 큰 그림은 [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)에서 따로 정리했다.

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

- related primer 기준 기본 next-read 순서는 **[객체지향 핵심 원리](./object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) -> 이 문서 -> [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)** 다. 검색으로 어느 문서부터 들어와도 이 순서로 다시 정렬하면 beginner route가 맞춰진다.
- 손으로 바로 구분 연습을 해보고 싶다면 [추상 클래스 vs 인터페이스 Follow-up Quick Check](./abstract-class-vs-interface-follow-up-drill.md)
- 첫 읽기 경로를 다시 확인하고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md) -> [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md) -> [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)
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
