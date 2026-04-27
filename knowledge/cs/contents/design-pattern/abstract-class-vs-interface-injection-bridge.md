# 추상 클래스냐 인터페이스+주입이냐: 템플릿 메소드·전략·조합 브리지

> 한 줄 요약: **흐름을 부모가 고정해야 하면 추상 클래스(템플릿 메소드)**, **규칙을 바꿔 끼워야 하면 인터페이스+주입(전략/조합)** 이다.

**난이도: 🟢 Beginner**

> 학습 순서 라벨: `basics -> framework examples -> deep dive` (`basics` 진입 전후에 읽는 companion bridge)

관련 문서:

- [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md)
- [템플릿 메소드 패턴 기초](./template-method-basics.md)
- [전략 패턴 기초](./strategy-pattern-basics.md)
- [상속보다 조합 기초](./composition-over-inheritance-basics.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)

retrieval-anchor-keywords: abstract class vs interface injection beginner, abstract class or interface with di, abstract class vs injected strategy, template method vs strategy beginner, dependency injection easy to test, dependency injection runtime swap example, strategy test double injection, runtime replacement by injection, 추상 클래스냐 인터페이스+주입이냐, 추상 클래스면 다 템플릿 메소드인가, 비 템플릿 추상 클래스 예시, 부모가 흐름을 쥔다 호출자가 전략을 고른다, abstract class vs interface injection bridge basics, abstract class vs interface injection bridge beginner, abstract class vs interface injection bridge intro

## 처음 배우는데 큰 그림

처음 배우는데 이 질문은 문법 문제가 아니라 **변경 지점** 문제다.

템플릿 메소드 route 기준으로 보면 이 문서는 `basics -> framework examples -> deep dive` 흐름에 들어가기 전후, "왜 추상 클래스가 자동으로 템플릿 메소드가 아닌지"를 먼저 자르는 companion bridge다.

- 변경 지점이 "단계의 구현"이면: 추상 클래스 + 템플릿 메소드
- 변경 지점이 "규칙 선택"이면: 인터페이스 + 주입 + 전략/조합

짧게 외우면 다음 두 줄이다.

- **부모가 흐름을 쥔다** -> 템플릿 메소드 쪽
- **호출자가 구현을 고른다** -> 전략/조합 쪽

## 30초 선택표

| 질문 | YES면 먼저 볼 것 | 이유 |
|---|---|---|
| `검증 -> 변환 -> 저장`처럼 순서를 절대 고정해야 하나? | 추상 클래스 + 템플릿 메소드 | 부모가 skeleton을 고정하고 하위 단계만 연다 |
| 런타임/설정/테스트에서 구현을 바꿔 끼워야 하나? | 인터페이스 + 주입 + 전략 | 호출자가 구현체를 선택해야 유지보수가 쉽다 |
| 중복 제거만 목적이고 부모-자식 의미가 약한가? | 조합 우선 | 상속 결합보다 작은 객체 조합이 안전하다 |

## 같은 요구를 두 방식으로 보기

### A. 추상 클래스(템플릿 메소드) 쪽

```java
abstract class ImportJob {
    public final void run() {
        read();
        validate();
        save();
    }

    protected abstract void read();
    protected void validate() {}
    protected abstract void save();
}
```

핵심은 `run()` 순서를 부모가 고정하는 것이다.

### B. 인터페이스+주입(전략/조합) 쪽

```java
interface DiscountPolicy {
    int discount(int price);
}

class OrderService {
    private final DiscountPolicy policy;

    OrderService(DiscountPolicy policy) {
        this.policy = policy;
    }

    int pay(int price) {
        return price - policy.discount(price);
    }
}
```

핵심은 `OrderService`가 부모를 상속받지 않고, 정책 객체를 주입받아 교체 가능하게 유지하는 것이다.

## 왜 주입이 쉬운가: 테스트 교체와 런타임 교체

같은 `OrderService`라도 **누가 할인 규칙을 넣어 주느냐**만 바꾸면 된다. 서비스 본문은 그대로 두고, 바깥에서 정책 객체만 갈아끼운다.

```java
interface DiscountPolicy {
    int discount(int price);
}

final class FixedDiscountPolicy implements DiscountPolicy {
    public int discount(int price) { return 1000; }
}

final class NoDiscountPolicy implements DiscountPolicy {
    public int discount(int price) { return 0; }
}

final class OrderService {
    private final DiscountPolicy policy;

    OrderService(DiscountPolicy policy) {
        this.policy = policy;
    }

    int pay(int price) {
        return price - policy.discount(price);
    }
}
```

테스트에서는 fake 구현을 넣어 결과를 바로 고정할 수 있다.

```java
DiscountPolicy fake = price -> 500;
OrderService service = new OrderService(fake);

assert service.pay(10000) == 9500;
```

런타임에서는 설정이나 상황에 따라 다른 구현을 넣을 수 있다.

```java
OrderService eventService = new OrderService(new FixedDiscountPolicy());
OrderService normalService = new OrderService(new NoDiscountPolicy());
```

이게 beginner 관점에서 중요한 이유는 간단하다.

| 바꾸는 대상 | 인터페이스+주입에서 바뀌는 것 | 안 바뀌는 것 |
|---|---|---|
| 테스트 | fake/stub 정책 객체 | `OrderService` 본문 |
| 운영 설정 | 실제 정책 구현체 | `pay()` 흐름 |

즉, **주입이 쉽다**는 말은 "서비스 코드를 뜯지 않고 바깥에서 부품만 교체하기 쉽다"는 뜻이다.

## 자주 헷갈리는 포인트

- "추상 클래스면 다 템플릿 메소드 아닌가?"
  - 아니다. 추상 클래스는 그냥 **공통 상태/도우미를 묶는 base class**일 수도 있다. 부모가 고정 순서를 쥐는 `final run()` 같은 메서드가 있어야 템플릿 메소드 쪽이다.
- "추상 클래스가 구현도 있으니 더 좋아 보인다"
  - 구현 재사용은 편하지만 단일 상속 제약과 결합이 커진다.
- "인터페이스면 무조건 메서드 선언만 있다"
  - `default` 메서드는 가능하지만, 핵심은 여전히 계약/교체 가능성이다.
- "둘 다 되는데 뭘로 시작하지?"
  - 처음엔 조합을 기본값으로 두고, 흐름 고정이 필요할 때만 템플릿 메소드로 좁힌다.

## 반례 한 개: 추상 클래스지만 템플릿 메소드는 아님

아래 `BaseNotifier`는 추상 클래스이지만, 부모가 `send() -> log() -> retry()` 같은 **고정 순서**를 잡고 있지 않다.
그냥 공통 필드와 도우미 메서드를 묶어 둔 base class다.

```java
abstract class BaseNotifier {
    protected final Clock clock;

    protected BaseNotifier(Clock clock) {
        this.clock = clock;
    }

    protected String now() {
        return clock.instant().toString();
    }

    public abstract void send(String message);
}

final class SlackNotifier extends BaseNotifier {
    SlackNotifier(Clock clock) {
        super(clock);
    }

    @Override
    public void send(String message) {
        System.out.println("[SLACK][" + now() + "] " + message);
    }
}
```

이 예시는 "추상 클래스 사용"에는 해당하지만 "템플릿 메소드 패턴"이라고 부르기엔 부족하다.

| 질문 | 이 예시의 답 | 의미 |
|---|---|---|
| 부모가 전체 순서를 고정하나? | 아니오 | 템플릿 메소드 아님 |
| 부모가 공통 상태/헬퍼를 주나? | 예 | base class 재사용 |
| 구현 교체를 더 쉽게 하려면? | `Notifier` 인터페이스 + 주입도 가능 | 조합 대안이 자연스러움 |

처음 읽을 때는 이렇게 외우면 된다.

- **추상 클래스**는 문법/도구 이름이다.
- **템플릿 메소드**는 "부모가 흐름을 고정한다"는 설계 패턴 이름이다.
- 그래서 추상 클래스를 써도 템플릿 메소드가 아닐 수 있다.

## 읽기 라우트(짧게)

1. [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md)
2. [상속보다 조합 기초](./composition-over-inheritance-basics.md)
3. [템플릿 메소드 패턴 기초](./template-method-basics.md)
4. [전략 패턴 기초](./strategy-pattern-basics.md)
5. [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)

## 한 줄 정리

`추상 클래스냐 인터페이스+주입이냐`는 "문법 비교"가 아니라 **고정 흐름(템플릿)** 과 **교체 규칙(전략/조합)** 중 어디가 문제인지 먼저 자르는 질문이다.
