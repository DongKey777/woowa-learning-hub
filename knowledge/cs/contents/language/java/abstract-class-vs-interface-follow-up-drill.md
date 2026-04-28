# 추상 클래스 vs 인터페이스 Follow-up Quick Check

> 한 줄 요약: `계약만 필요한가`, `공통 상태와 부모 흐름이 필요한가`를 5개의 아주 짧은 Java 예제로 다시 판별하는 beginner quick-check 카드다.

**난이도: 🟢 Beginner**

관련 문서:

- [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) - 큰 그림을 먼저 잡고 온 뒤 바로 손으로 판별 연습할 때 보는 entry primer
- [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md) - beginner 기준을 잡은 뒤 경계와 예외를 더 길게 보고 싶을 때 보는 deep dive
- [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md) - `default method`를 추상 클래스 대체품처럼 읽는 오해를 따로 정리한 primer
- [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md) - "둘 다 아닌데?"가 보일 때 상속보다 먼저 조합으로 빠지는 안전한 다음 단계
- [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md) - 부모가 전체 순서를 쥐는 경우를 추상 클래스 축으로 이어서 보는 follow-up
- [language 카테고리 인덱스 - Java primer](../README.md#java-primer)

retrieval-anchor-keywords: abstract class interface quick check, abstract class interface drill, abstract class vs interface examples beginner, contract vs shared state java, java abstract class interface follow up, 추상 클래스 인터페이스 예제 문제, 처음 배우는데 추상 클래스 인터페이스 연습, 추상 클래스 인터페이스 왜 헷갈려요, 공통 상태가 필요하면 추상 클래스, 계약만 필요하면 인터페이스, default method vs abstract class quick check, what is abstract class vs interface drill

## 핵심 개념

이 드릴은 문법 암기보다 판단 연습에 가깝다. 한 문제를 볼 때 아래 두 질문만 먼저 적으면 된다.

- 이 타입들이 **같은 부모 상태**를 공유해야 하나?
- 아니면 **할 수 있는 일의 계약**만 맞추면 충분한가?

공통 필드, 생성자, 부모가 고정한 실행 순서가 보이면 추상 클래스 쪽으로 기울고, 구현체를 여러 타입에 붙이거나 갈아끼우는 계약이면 인터페이스 쪽으로 기운다.

## 15초 decision card

| 코드에서 먼저 찾을 힌트 | 먼저 고를 쪽 | 이유 |
|---|---|---|
| `protected` 필드, 생성자, 공통 초기화 | 추상 클래스 | 부모가 상태와 초기 규칙을 같이 쥔다 |
| `A도 되고 B도 되는 능력` | 인터페이스 | 서로 다른 클래스에도 같은 계약을 붙일 수 있다 |
| `final` 템플릿 메서드로 순서 고정 | 추상 클래스 | 부모 흐름을 자식이 공유한다 |
| 얇은 기본 동작 1개, 상태는 없음 | 인터페이스 `default method` | 계약 중심으로 유지하면서 편의 동작만 준다 |
| "중복 제거만 하고 싶다" | 둘 다 다시 보류 | 상속보다 조합이 더 자연스러운 경우가 많다 |

## quick check 1-3

### 1. 공통 잔액 필드가 필요한가

```java
abstract class Account {
    protected int balance;

    Account(int balance) {
        this.balance = balance;
    }

    abstract void withdraw(int amount);
}
```

정답: **추상 클래스**

왜:
- `balance`라는 공통 상태를 부모가 들고 있다
- 생성자로 공통 초기화 규칙도 같이 묶는다

### 2. 서로 다른 타입에 "알림 보낼 수 있음"만 붙이나

```java
interface Notifiable {
    void notify(String message);
}

class EmailSender implements Notifiable { ... }
class SlackSender implements Notifiable { ... }
```

정답: **인터페이스**

왜:
- 핵심은 "무엇을 할 수 있나"라는 계약이다
- 구현체가 완전히 달라도 같은 능력 이름으로 묶을 수 있다

### 3. 부모가 전체 순서를 고정하나

```java
abstract class ReportJob {
    public final void run() {
        read();
        validate();
        save();
    }

    protected abstract void read();
    protected abstract void save();
    protected void validate() { }
}
```

정답: **추상 클래스**

왜:
- `run()`이 전체 흐름을 고정한다
- 자식은 빈칸만 채우므로 템플릿 메소드 축이다

## quick check 4-5

### 4. 계약은 그대로 두고 작은 기본 동작만 주나

```java
interface Payable {
    int amount();

    default boolean isFree() {
        return amount() == 0;
    }
}
```

정답: **인터페이스**

왜:
- 핵심 계약은 `amount()`다
- `isFree()`는 상태 없이 붙는 얇은 편의 동작이다

체크 포인트:
- 여기서 "필드도 넣고 싶다"는 생각이 들면 추상 클래스나 조합으로 다시 돌아간다

### 5. 둘 다 아닌 경우도 보이나

```java
class OrderService {
    private final DiscountPolicy discountPolicy;

    OrderService(DiscountPolicy discountPolicy) {
        this.discountPolicy = discountPolicy;
    }
}

interface DiscountPolicy {
    int discount(int price);
}
```

정답: **서비스는 조합, 정책 계약은 인터페이스**

왜:
- `OrderService`가 `DiscountPolicy`를 상속하지 않는다
- 정책을 갈아끼우기 위해 계약은 인터페이스로 두고, 서비스는 그 계약을 필드로 가진다

이 예제는 "추상 클래스 vs 인터페이스" 질문이 사실은 "상속 대신 조합이 맞나?"로 바뀌는 대표 사례다.

## 흔한 오해와 함정

- `default method`가 보이면 인터페이스가 추상 클래스와 같아졌다고 오해하기 쉽다. 하지만 인스턴스 상태와 생성자 축은 여전히 다르다.
- 공통 메서드가 두 개쯤 보인다고 바로 추상 클래스를 고르면 결합이 빨리 강해진다. 상태 공유가 없으면 인터페이스 + 헬퍼/조합이 더 낫다.
- 추상 클래스는 "더 강력한 버전"이 아니라 "부모-자식 결합을 더 강하게 여는 선택"이다.
- 문제를 풀다 `둘 중 하나`만 고르려 하면 막히는 경우가 있다. 실제 설계에서는 인터페이스 계약 + 조합이 더 자주 기본값이다.

## 다음에 바로 이어서 보면 좋은 문서

- quick check 전에 큰 그림을 다시 붙이고 싶다면 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md)
- `default method` 경계를 따로 자르고 싶다면 [인터페이스 default method 기초: 계약 vs evolution](./interface-default-method-contract-evolution-primer.md)
- "왜 상속보다 조합을 먼저 보라고 하나요?"가 남으면 [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)
- 부모가 흐름을 쥐는 구조만 따로 연습하려면 [템플릿 메소드 패턴 기초](../../design-pattern/template-method-basics.md)

## 한 줄 정리

짧은 예제를 볼 때도 `공통 상태/부모 흐름`이면 추상 클래스, `능력 계약/교체 가능성`이면 인터페이스, 둘 다 애매하면 조합부터 다시 의심하는 습관이 가장 안전하다.
