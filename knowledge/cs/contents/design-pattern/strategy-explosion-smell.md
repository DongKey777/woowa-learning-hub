# 전략 폭발 냄새: 전략 패턴이 많아질수록 의심해야 하는 것

> 한 줄 요약: 전략 패턴이 너무 많이 늘어날 때는 "유연해졌다"가 아니라 "변화 축을 잘못 쪼갰다"는 신호일 수 있다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [전략 패턴](./strategy-pattern.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

전략 폭발(Strategy Explosion)은 **전략 클래스를 늘려서 문제를 해결하려다 오히려 클래스 수와 조합 수가 폭증하는 현상**이다.  
전략 패턴 자체는 좋은 도구지만, 변화 축이 여러 개일 때는 클래스 하나가 1:1로 대응되지 않는다.

backend에서 자주 보이는 냄새는 이런 형태다.

- `PaymentStrategy`, `PaymentStrategyV2`, `PaymentStrategyForMobile`
- `DiscountStrategy`, `DiscountStrategyForVip`, `DiscountStrategyForCoupon`
- 팩토리가 전략을 너무 많이 조립한다
- 조건문을 클래스 폭발로 옮겨 놓았다

### Retrieval Anchors

- `strategy explosion`
- `enum to class smell`
- `combinatorial behavior`
- `policy matrix`
- `too many strategy classes`

---

## 깊이 들어가기

### 1. 전략이 늘어나는 이유는 보통 축이 여러 개이기 때문이다

문제가 한 축으로만 바뀌면 전략 패턴이 잘 맞는다.
하지만 현실의 backend는 대개 두세 개 축이 동시에 바뀐다.

- 결제 수단
- 채널
- 사용자 등급
- 지역
- 프로모션 여부

이때 축을 분리하지 않고 전략 하나씩 늘리면 조합이 폭발한다.

### 2. 전략 폭발의 신호

- 전략 클래스가 enum 값보다 많다
- 전략 이름에 조건이 붙는다
- 팩토리에서 `if` 문이 다시 커진다
- 테스트가 전략 개수만큼 늘어난다
- 새 요구사항이 오면 전략 생성부터 고민한다

이 상태는 "객체지향화"가 아니라 **분기 이동**일 가능성이 크다.

### 3. 대안은 전략이 아니라 분해다

전략 폭발의 해법은 전략을 더 만드는 것이 아니라, 변화 축을 다시 나누는 것이다.

- 공통 규칙은 Specification으로 뽑는다
- 상태 전이는 State로 바꾼다
- 공통 파이프라인은 Template Method나 Chain으로 둔다
- 독립 축은 작은 value object로 분리한다

---

## 실전 시나리오

### 시나리오 1: 할인 정책

처음에는 `VipDiscountStrategy`, `NewbieDiscountStrategy` 정도로 끝난다.  
그런데 어느 순간 `VipMobileWeekendDiscountStrategy`가 생기면 이미 구조가 위험하다.

### 시나리오 2: 알림 발송

이메일, SMS, 푸시를 전략으로 만들 수 있지만, 채널과 템플릿과 재시도 정책까지 분기되면 전략만으로는 과하다.

### 시나리오 3: 결제 라우팅

PG, 간편결제, 포인트, 지역 규정이 섞이면 전략 조합이 아니라 정책 모델이 필요하다.

---

## 코드로 보기

### Before: 전략 클래스가 축마다 늘어난다

```java
public interface DiscountStrategy {
    int discount(int amount);
}

public class VipMobileWeekendDiscountStrategy implements DiscountStrategy {
    @Override
    public int discount(int amount) {
        return (int) (amount * 0.7);
    }
}
```

전략 이름만 봐도 "무엇이 바뀌는지"가 아닌 "모든 경우의 수"가 드러난다.

### After: 축을 분리한다

```java
public record DiscountContext(MemberGrade grade, Channel channel, boolean weekend) {}

public interface DiscountRule {
    boolean matches(DiscountContext context);
    int discount(int amount, DiscountContext context);
}

public class VipRule implements DiscountRule {
    @Override
    public boolean matches(DiscountContext context) {
        return context.grade() == MemberGrade.VIP;
    }

    @Override
    public int discount(int amount, DiscountContext context) {
        return (int) (amount * 0.8);
    }
}
```

### 조합 접근

```java
public class DiscountPolicy {
    private final List<DiscountRule> rules;

    public int calculate(int amount, DiscountContext context) {
        return rules.stream()
            .filter(rule -> rule.matches(context))
            .findFirst()
            .map(rule -> rule.discount(amount, context))
            .orElse(amount);
    }
}
```

이 구조는 "전략 수를 줄였다"가 아니라 **변화 축을 정책과 규칙으로 다시 모델링했다**는 점이 중요하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 전략 클래스 다수 | 교체는 쉽다 | 클래스가 급증한다 | 진짜로 독립적인 알고리즘일 때 |
| 전략 + 팩토리 | 생성은 통제된다 | 팩토리가 비대해질 수 있다 | 전략 수가 적당할 때 |
| 규칙/명세 조합 | 축을 다시 나눌 수 있다 | 설계가 조금 더 추상적이다 | 조건이 합성될 때 |
| State/Chain/Template 전환 | 구조가 더 명확해진다 | 개념 전환이 필요하다 | 전략이 아니라 흐름 문제일 때 |

판단 기준은 다음과 같다.

- 전략이 "선택지"라면 유지한다
- 전략이 "경우의 수"가 되면 의심한다
- 이름에 조건이 붙기 시작하면 축 분해를 다시 한다

---

## 꼬리질문

> Q: 전략 클래스가 많아지면 왜 문제가 되나요?
> 의도: 클래스 수 자체보다 변화 축의 설계가 중요하다는 점을 아는지 확인한다.
> 핵심: 조합 수가 늘어 유지보수와 테스트 비용이 커진다.

> Q: 전략 폭발과 if-else 스파게티는 같은 문제인가요?
> 의도: 구조만 바뀌고 본질은 안 바뀌는 경우를 구분하는지 확인한다.
> 핵심: 형태만 다를 뿐, 둘 다 변화 축을 잘못 잡았을 가능성이 높다.

> Q: 전략을 언제 포기해야 하나요?
> 의도: 패턴 과사용을 경계하는지 확인한다.
> 핵심: 조건 조합이 중심이면 Specification이나 다른 분해가 더 낫다.

## 한 줄 정리

전략 폭발은 전략 패턴이 실패했다는 뜻이 아니라, 문제의 변화 축이 여러 개인데도 전략 하나로 억지로 풀고 있다는 경고다.

