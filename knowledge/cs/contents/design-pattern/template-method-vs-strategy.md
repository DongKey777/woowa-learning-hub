# 템플릿 메소드 vs 전략

> 한 줄 요약: 템플릿 메소드는 흐름을 상속으로 고정하고, 전략 패턴은 알고리즘 전체를 조합으로 교체한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [템플릿 메소드 패턴](./template-method.md)
> - [전략 패턴](./strategy-pattern.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

---

## 핵심 개념

둘 다 "바뀌는 부분과 안 바뀌는 부분을 분리"한다.  
차이는 바뀌는 부분을 어디에 두느냐다.

- 템플릿 메소드: 상위 클래스가 알고리즘 뼈대를 잡고 일부 단계를 하위 클래스가 바꾼다
- 전략 패턴: 알고리즘 자체를 객체로 분리해 실행 시점에 교체한다

이 차이를 놓치면 상속을 과도하게 쓰거나, 반대로 너무 많은 전략 클래스를 만든다.

---

## 깊이 들어가기

### 1. 템플릿 메소드가 잘 맞는 문제

흐름은 거의 고정인데 단계 일부만 다를 때다.

- 파일 파싱
- 배치 처리
- 인증 처리 순서
- 컴파일/빌드 파이프라인

공통 흐름이 상위에 있으면 실수로 순서를 바꾸기 어렵다.

### 2. 전략이 잘 맞는 문제

정책 자체가 자주 바뀌고, 교체 시점이 런타임일 때다.

- 할인 정책
- 배송비 계산
- 정렬 기준
- 결제 수단

전략은 "무엇을 할지"를 객체로 바꿔치기할 수 있다.

### 3. 상속과 조합의 경계

템플릿 메소드는 상속이라 구조가 단단해진다.  
전략은 조합이라 유연하지만 객체 수가 늘어난다.

| 구분 | 템플릿 메소드 | 전략 |
|---|---|---|
| 변경 방식 | 단계 일부 수정 | 알고리즘 전체 교체 |
| 결합 방식 | 상속 | 조합 |
| 런타임 교체 | 약함 | 강함 |
| 흐름 보장 | 강함 | 약함 |

---

## 실전 시나리오

### 시나리오 1: 배치 작업

배치는 보통 순서가 중요하다.

1. 소스 읽기
2. 정제
3. 저장
4. 후처리

이때 단계 순서가 고정되면 템플릿 메소드가 더 자연스럽다.

### 시나리오 2: 할인/결제 정책

정책이 자주 바뀌면 전략이 더 낫다.  
새 정책이 추가될 때 상위 클래스의 `if`를 계속 늘리는 것보다, 새 전략만 추가하는 편이 낫다.

### 시나리오 3: Spring/JDK 예시

`Comparator`는 전략의 대표 예다.  
반면 Spring의 일부 설정 흐름은 템플릿 메소드 느낌이 강하다. 공통 흐름을 프레임워크가 잡고, 세부 동작은 콜백이나 빈으로 바뀐다.

---

## 코드로 보기

### 1. 템플릿 메소드

```java
public abstract class ReportGenerator {
    public final void generate() {
        load();
        transform();
        save();
    }

    protected abstract void load();
    protected abstract void transform();
    protected abstract void save();
}
```

### 2. 전략

```java
public interface PricingStrategy {
    int calculate(int basePrice);
}

public class VipPricingStrategy implements PricingStrategy {
    public int calculate(int basePrice) {
        return (int) (basePrice * 0.8);
    }
}

public class PriceService {
    private final PricingStrategy strategy;

    public PriceService(PricingStrategy strategy) {
        this.strategy = strategy;
    }

    public int price(int basePrice) {
        return strategy.calculate(basePrice);
    }
}
```

### 3. 함수형 대안

```java
IntUnaryOperator strategy = price -> (int) (price * 0.8);
```

단순하면 함수가 가장 가볍다.  
상태가 붙거나 단계가 늘어날 때 전략 클래스로 올리면 된다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 템플릿 메소드 | 흐름을 강하게 보장한다 | 상속 계층이 굳는다 | 순서가 중요한 파이프라인 |
| 전략 | 정책 교체가 쉽다 | 객체 수가 늘어난다 | 자주 바뀌는 정책 |
| 함수형 | 가장 단순하다 | 복잡한 상태를 담기 어렵다 | 작은 계산 로직 |

핵심은 "누가 흐름을 통제해야 하는가"다.  
흐름이 중요하면 템플릿, 교체가 중요하면 전략이다.

---

## 꼬리질문

> Q: 전략 패턴인데도 템플릿 메소드가 더 나은 경우는 언제인가요?
> 의도: 런타임 교체보다 흐름 고정이 중요한 상황을 아는지 확인
> 핵심: 공통 순서가 더 중요하면 상속이 낫다

> Q: if-else가 있으면 무조건 전략으로 바꿔야 하나요?
> 의도: 패턴 과사용을 경계하는지 확인
> 핵심: 변화가 적고 단순하면 함수나 작은 분기가 더 낫다

## 한 줄 정리

템플릿 메소드는 알고리즘의 순서를 고정하고 일부만 바꾸는 패턴이고, 전략은 알고리즘 전체를 객체로 분리해 교체하는 패턴이다.
