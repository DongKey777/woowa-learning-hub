# Composition over Inheritance Practical

> 한 줄 요약: 상속은 공통점을 재사용하는 도구가 아니라, 변화 가능성과 결합도를 함께 떠안는 선택이다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [전략 (Strategy)](./strategy-pattern.md)
> - [템플릿 메소드](./template-method.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [전략 폭발 냄새](./strategy-explosion-smell.md)
> - [Template Hook Smells](./template-hook-smells.md)
> - [안티 패턴](./anti-pattern.md)

retrieval-anchor-keywords: composition over inheritance, favor composition over inheritance, 상속보다 조합, fragile base class, inheritance rigidity, lsp violation, behavior injection, strategy via composition, template method tradeoff, penguin bird inheritance smell, composition over inheritance practical basics, composition over inheritance practical beginner, composition over inheritance practical intro, design pattern basics, beginner design pattern

---

## 핵심 개념

상속보다 조합을 우선하라는 말은 유명하지만, 그냥 구호로 쓰면 위험하다.

- 상속은 "is-a" 관계를 코드로 묶는다
- 조합은 "has-a" 관계를 느슨하게 묶는다

문제는 상속이 재사용을 쉽게 보이게 하지만, 실제로는 **부모 변경이 자식 전체에 번진다**는 점이다.

---

## 깊이 들어가기

### 1. 상속의 함정

```java
public class Bird {
    public void fly() {
        System.out.println("fly");
    }
}

public class Penguin extends Bird {
    @Override
    public void fly() {
        throw new UnsupportedOperationException();
    }
}
```

이 구조는 읽는 사람을 속인다.
`Penguin`은 `Bird`를 상속하지만 날 수 없다. 즉 LSP를 깨기 쉽다.

### 2. 조합은 역할을 분리한다

```java
public interface MoveStrategy {
    void move();
}

public class FlyMoveStrategy implements MoveStrategy {
    public void move() { System.out.println("fly"); }
}

public class SwimMoveStrategy implements MoveStrategy {
    public void move() { System.out.println("swim"); }
}

public class Animal {
    private final MoveStrategy moveStrategy;

    public Animal(MoveStrategy moveStrategy) {
        this.moveStrategy = moveStrategy;
    }

    public void move() {
        moveStrategy.move();
    }
}
```

이렇게 하면 종류가 바뀌어도 동작만 교체하면 된다.

### 3. 상속이 필요한 순간도 있다

상속이 항상 나쁜 건 아니다.
`template method`처럼 공통 골격이 안정적이고, 일부 단계만 바뀌는 경우에는 상속이 더 자연스럽다.

핵심은 "재사용"이 아니라 **변경 축**이다.

---

## 실전 시나리오

### 시나리오 1: 결제 정책

결제 수단, 할인 정책, 적립 정책은 상속보다 전략/조합이 맞다.
정책이 독립적으로 바뀌기 때문이다.

### 시나리오 2: HTTP 요청 래핑

압축, 로깅, 재시도는 데코레이터처럼 조합하는 편이 낫다.
부모 클래스를 점점 복잡하게 만드는 것보다 안전하다.

### 시나리오 3: 도메인 공통 골격

검증 -> 저장 -> 후처리처럼 순서가 안정적인 흐름은 템플릿 메소드나 공통 추상 클래스가 더 낫다.

---

## 코드로 보기

### Before: 상속으로 억지 재사용

```java
public class FileLogger {
    public void log(String message) {
        System.out.println(message);
    }
}

public class AuditLogger extends FileLogger {
    @Override
    public void log(String message) {
        super.log("[audit] " + message);
    }
}
```

### After: 조합

```java
public class Logger {
    private final PrefixStrategy prefixStrategy;

    public Logger(PrefixStrategy prefixStrategy) {
        this.prefixStrategy = prefixStrategy;
    }

    public void log(String message) {
        System.out.println(prefixStrategy.apply(message));
    }
}
```

### JDK 예시

`Comparator`는 상속보다 조합이 왜 실용적인지 보여주는 좋은 예다.

```java
list.sort(Comparator.comparingInt(String::length));
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|-------------|
| 상속 | 공통 코드를 쉽게 재사용한다 | 부모 변경이 자식에 전파된다 | 공통 골격이 안정적일 때 |
| 조합 | 교체와 테스트가 쉽다 | 객체 wiring이 늘어난다 | 변화 축이 독립적일 때 |
| 상속 + 조합 | 일부 공통 흐름과 일부 교체를 함께 처리한다 | 설계가 복잡해질 수 있다 | 둘 다 필요한 경우 |

판단 기준은 간단하다.

- "무엇이 바뀌는가"가 다르면 조합
- "흐름"이 같고 "일부 단계"만 다르면 상속
- "행동"이 독립적으로 교체되면 전략

---

## 꼬리질문

> Q: 상속과 조합 중 언제 상속을 택하나요?
> 의도: 무조건 조합만 외우는지 확인한다.
> 핵심: 공통 골격이 안정적이고 변경 축이 적을 때다.

> Q: 상속이 LSP를 깨는 대표 사례는 무엇인가요?
> 의도: 이론과 실제 버그를 연결하는지 확인한다.
> 핵심: 부모 타입으로 넣었을 때 자식이 예상을 깨는 경우다.

> Q: 전략 패턴은 조합의 어떤 예인가요?
> 의도: 패턴을 설계 원칙과 연결하는지 확인한다.
> 핵심: 바뀌는 행동을 객체로 분리한 조합 패턴이다.

---

## 한 줄 정리

상속은 공통 골격이 안정적일 때, 조합은 변화 축이 독립적일 때 더 안전하다.
