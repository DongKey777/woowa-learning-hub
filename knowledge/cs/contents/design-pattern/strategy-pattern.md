# 전략 패턴

> 한 줄 요약: 같은 일을 하는 여러 구현 중 무엇을 쓸지 **호출자/설정이 런타임에 고르고**, `Context`는 그 구현을 전략 객체로 위임하는 패턴이다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
> - [Strategy vs Function: lambda로 충분한가, 전략 타입이 필요한가](./strategy-vs-function-chooser.md)
> - [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [전략 폭발 냄새](./strategy-explosion-smell.md)
> - [팩토리 (Factory)](./factory.md)

retrieval-anchor-keywords: strategy pattern, runtime algorithm selection, runtime implementation selection, caller chooses strategy, caller owned strategy selection, context delegates to strategy, replace if else with strategy, when to use strategy, when not to use strategy, strategy overuse, strategy explosion smell, strategy vs template method, beginner strategy pattern, strategy vs state, strategy vs policy object, payment method strategy, lambda vs strategy, function vs strategy, strategy vs small function, function map vs strategy

---

## 핵심 개념

전략 패턴(Strategy Pattern)은 **같은 목적을 수행하지만 구현이 다른 알고리즘을 교체 가능한 객체로 분리**하는 패턴이다.
핵심은 "어떻게 할지"를 객체로 빼는 것만이 아니라, **어떤 구현을 쓸지 고르는 책임을 `Context` 밖으로 밀어내는 것**이다.

보통 이 선택은 호출자, 설정, DI가 맡는다.
`Context`는 "작업을 수행한다"는 흐름만 알고, "어떤 전략이 맞는가"는 직접 판단하지 않는다.

이 패턴이 필요한 이유는 단순하다.

- 요청/설정/테넌트에 따라 런타임에 다른 구현을 골라야 한다
- 새로운 정책이 추가될 때 기존 큰 분기문을 계속 수정하고 싶지 않다
- 구현마다 이름, 협력 객체, 테스트 경계를 독립적으로 두고 싶다

즉 전략 패턴은 **if-else sprawl을 객체 분리로 치유하면서, 선택 책임을 호출자 쪽으로 돌리는 방법**이다.

### 전략 패턴이 잘 맞는 경우

- 할인 정책, 결제 수단, 정렬 기준처럼 **같은 역할을 하는 선택지**가 여러 개일 때
- 호출자/설정/DI가 **실행 시점에 어떤 구현을 쓸지 고르는 문제**일 때
- 구현마다 협력 객체나 보조 로직이 붙고, 구현체별 테스트 경계가 필요할 때

### 전략 패턴이 덜 맞는 경우

- 분기가 1~2개뿐이고 앞으로도 잘 안 바뀔 때
- 계산식이 1~3줄 정도로 짧고 stateless라서 작은 함수나 `lambda`가 더 직접적일 때
- `VipWeekendMobileStrategy`처럼 조건 조합마다 전략 클래스가 늘어나는 과사용 신호가 보일 때
- 알고리즘 자체가 거의 고정되어 있고, 상속으로 공통 골격을 잡는 편이 더 자연스러울 때

관련 경계를 같이 보면 더 빨리 정리된다.

- 짧은 함수와의 경계는 [Strategy vs Function](./strategy-vs-function-chooser.md)
- 고정 흐름과의 경계는 [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- 전략 이름이 경우의 수를 설명하기 시작하면 [전략 폭발 냄새](./strategy-explosion-smell.md)

---

## 깊이 들어가기

### 1. if-else가 커질 때 생기는 문제

전략 패턴을 쓰기 전 코드는 보통 이런 모양이다.

```java
public class DiscountService {
    public int calculate(String grade, int price) {
        if ("VIP".equals(grade)) {
            return (int) (price * 0.8);
        }
        if ("GOLD".equals(grade)) {
            return (int) (price * 0.9);
        }
        if ("SILVER".equals(grade)) {
            return (int) (price * 0.95);
        }
        return price;
    }
}
```

문제는 정책이 추가될 때마다 이 메서드가 계속 비대해진다는 점이다.  
이 구조는 "지금 당장 돌아가는 코드"는 만들지만, "정책이 자주 바뀌는 코드"에는 취약하다.

### 2. 전략 패턴의 구조

- `Strategy`: 교체 가능한 알고리즘의 공통 인터페이스
- `ConcreteStrategy`: 실제 알고리즘 구현
- `Context`: 전달받은 전략을 사용해 작업을 수행하는 객체

중요한 점은 `Context`가 구체 클래스가 아니라 **인터페이스**에 의존하고,
어떤 전략을 쓸지 직접 판단하지 않는다는 것이다. 선택은 호출자/설정/DI가 맡고 `Context`는 실행 흐름만 유지한다.

### 3. Template Method와의 차이

둘 다 "알고리즘을 캡슐화"하지만, 선택 방식이 다르다.

| 항목 | Strategy | Template Method |
|------|----------|-----------------|
| 재사용 방식 | 조합 | 상속 |
| 선택 시점 | 런타임 | 주로 설계/상속 구조 |
| 변화 지점 | 알고리즘 전체를 교체 | 알고리즘 일부 단계만 교체 |
| 결합도 | 낮다 | 상속 계층에 묶인다 |

간단히 말하면:

- 전략 패턴은 "무엇을 쓸지 바꾼다"
- 템플릿 메소드는 "뼈대는 고정하고 일부만 바꾼다"

### 4. 함수 하나로 충분한 경우도 있다

전략 패턴은 무조건 좋은 게 아니다.  
함수가 한두 개뿐이면 `Function<T, R>` 같은 함수형 조합이 더 단순할 수 있다.

`lambda`/작은 함수와 Strategy 타입 사이 경계를 짧게 잡고 싶다면
[Strategy vs Function: lambda로 충분한가, 전략 타입이 필요한가](./strategy-vs-function-chooser.md)를 같이 보면 된다.

전략 패턴을 쓰면 생기는 비용:

- 클래스 수가 늘어난다
- 객체 생성을 관리해야 한다
- 초보자에게 구조가 무거워 보일 수 있다

전략 이름이 조건 조합을 그대로 담기 시작하면 [전략 폭발 냄새](./strategy-explosion-smell.md)를 의심해야 한다.

즉 "if-else를 없애는 것"이 목적이 아니라, **변화 지점을 분리하는 것**이 목적이다.

---

## 실전 시나리오

### 시나리오 1: 결제 수단이 늘어난다

처음에는 카드와 계좌이체만 있다가, 나중에는 간편결제와 포인트 결제가 추가된다.  
`if-else`로 처리하면 결제 로직과 분기 조건이 한 파일에 계속 쌓인다.

전략 패턴으로 분리하면:

- 결제 흐름은 유지
- 결제 수단만 추가
- 테스트는 결제 수단별로 독립적으로 작성 가능

### 시나리오 2: 정렬 기준이 바뀐다

JDK의 `Comparator`는 전략 패턴의 대표적인 예다.

```java
List<String> names = List.of("bob", "alice", "charlie");
names.stream()
    .sorted(Comparator.comparingInt(String::length))
    .forEach(System.out::println);
```

정렬 대상은 같지만 기준은 바뀔 수 있다.  
정렬 기준을 객체로 넘기면 코드가 훨씬 유연해진다.

### 시나리오 3: Spring MVC에서 뷰를 바꾼다

Spring은 내부적으로 전략 인터페이스를 많이 쓴다.  
예를 들어 `ViewResolver`는 같은 논리 뷰 이름을 JSP, Thymeleaf, JSON 응답 등으로 해석하는 전략 역할을 한다.

프레임워크 입장에서는 "어떤 뷰를 쓸지"를 고정할 필요가 없고,  
애플리케이션은 설정만 바꾸면 다른 전략을 선택할 수 있다.

---

## 코드로 보기

### 1. 전략 패턴 없이

```java
public class ShippingService {
    public int calculateFee(String type, int distance) {
        if ("STANDARD".equals(type)) {
            return 3000;
        } else if ("EXPRESS".equals(type)) {
            return 5000 + distance * 100;
        } else if ("SAME_DAY".equals(type)) {
            return 8000 + distance * 150;
        }
        throw new IllegalArgumentException("unknown shipping type");
    }
}
```

문제는 정책이 늘어날수록 분기문도 같이 늘어난다는 점이다.

### 2. 전략 패턴 적용 후

```java
public interface ShippingStrategy {
    int calculateFee(int distance);
}

public class StandardShippingStrategy implements ShippingStrategy {
    @Override
    public int calculateFee(int distance) {
        return 3000;
    }
}

public class ExpressShippingStrategy implements ShippingStrategy {
    @Override
    public int calculateFee(int distance) {
        return 5000 + distance * 100;
    }
}

public class ShippingService {
    private final Map<String, ShippingStrategy> strategies;

    public ShippingService(Map<String, ShippingStrategy> strategies) {
        this.strategies = strategies;
    }

    public int calculateFee(String type, int distance) {
        ShippingStrategy strategy = strategies.get(type);
        if (strategy == null) {
            throw new IllegalArgumentException("unknown shipping type");
        }
        return strategy.calculateFee(distance);
    }
}
```

이 구조의 장점은 분기 로직과 계산 로직이 분리된다는 것이다.  
새로운 배송 타입이 추가되면 새로운 클래스만 추가하면 된다.

### 3. 함수형 대안

전략이 아주 단순하면 함수형으로도 충분하다.

```java
Map<String, IntUnaryOperator> strategies = Map.of(
    "STANDARD", distance -> 3000,
    "EXPRESS", distance -> 5000 + distance * 100
);
```

단순한 정책이면 이 방식이 더 가볍다.  
복잡한 상태나 여러 협력 객체가 필요해지는 순간 전략 클래스로 분리하는 편이 낫다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| `if-else` | 가장 단순하다 | 정책이 늘수록 유지보수성이 급격히 나빠진다 | 조건이 거의 안 바뀔 때 |
| 함수형 전략 | 가볍고 짧다 | 상태와 협력이 많아지면 한계가 있다 | 계산 로직이 단순할 때 |
| 전략 패턴 | 교체와 테스트가 쉽다 | 클래스 수와 구조가 늘어난다 | 정책이 자주 바뀔 때 |
| 템플릿 메소드 | 뼈대를 재사용하기 좋다 | 상속에 묶인다 | 알고리즘 단계가 안정적일 때 |

판단 기준은 명확하다.

- 바뀌는 것이 "계산식"이면 함수도 충분할 수 있다
- 바뀌는 것이 "정책 묶음"이면 전략 패턴이 더 적합하다
- 바뀌는 것이 "공통 흐름 + 일부 단계"면 템플릿 메소드가 더 자연스럽다

---

## 꼬리질문

> Q: 전략 패턴과 템플릿 메소드 중 무엇을 먼저 떠올려야 하나요?
> 의도: 상속과 조합의 선택 기준을 아는지 확인한다.
> 핵심: 알고리즘 뼈대가 고정인지, 바뀌는 부분을 객체로 교체해야 하는지부터 본다.

> Q: 전략 패턴을 쓰면 무조건 if-else가 없어지나요?
> 의도: 패턴을 만능으로 보는지 확인한다.
> 핵심: 분기는 사라지지 않고, 위치만 전략 선택 단계로 이동한다.

> Q: JDK에서 전략 패턴을 보여주는 대표 예시는 무엇인가요?
> 의도: 개념을 실전 API와 연결할 수 있는지 확인한다.
> 핵심: `Comparator`, `Charset`, `ThreadFactory` 같은 인터페이스가 대표적이다.

> Q: Spring에서 전략 패턴을 왜 자주 쓰나요?
> 의도: 프레임워크 내부 구조를 이해하는지 확인한다.
> 핵심: 뷰 해석, 예외 처리, 메시지 변환처럼 실행 시점에 구현을 바꿔야 하는 지점이 많기 때문이다.

---

## 한 줄 정리

전략 패턴은 if-else를 없애는 기술이 아니라, 바뀌는 알고리즘을 교체 가능한 객체로 분리해서 유지보수와 테스트를 쉽게 만드는 구조다.
