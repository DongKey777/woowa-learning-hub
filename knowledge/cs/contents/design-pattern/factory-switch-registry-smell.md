# Factory Switch Registry Smell

> 한 줄 요약: Factory의 switch가 계속 늘어나면 그건 더 이상 단순한 생성기가 아니라 Registry나 전략 선택기로 재설계해야 한다는 신호다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [팩토리 (Factory)](./factory.md)
> - [Registry Pattern](./registry-pattern.md)
> - [Strategy Pattern](./strategy-pattern.md)
> - [Service Locator Antipattern](./service-locator-antipattern.md)

---

## 핵심 개념

팩토리의 `switch`나 `if-else`는 작은 규모에서는 괜찮다.  
문제는 선택지와 조건이 계속 늘어날 때다.

그 순간 팩토리는 다음 중 하나로 바뀌어야 한다.

- Registry: 키로 객체를 찾는다
- Strategy: 행동을 선택한다
- DI configuration: 생성 조합을 설정한다

### Retrieval Anchors

- `factory switch smell`
- `registry refactor`
- `strategy selection`
- `creation selection explosion`
- `factory branching`

---

## 깊이 들어가기

### 1. switch가 길어지는 이유

factory가 하는 일이 하나에서 둘 이상으로 늘어난다.

- 구현 선택
- 생성 파라미터 조립
- 외부 설정 반영
- 예외 처리

이때 switch는 이미 선택기다.

### 2. smell의 신호

- case가 계속 늘어난다
- 문자열 키가 여기저기 반복된다
- factory 안에 비즈니스 규칙이 들어간다
- 새 구현을 추가할 때 factory만 수정하면 끝나지 않는다

### 3. 대안은 구조를 나누는 것이다

- 선택은 Registry
- 행동은 Strategy
- 생성은 Factory

이 셋을 분리하면 책임이 선명해진다.

---

## 실전 시나리오

### 시나리오 1: 결제 provider 선택

지역, 채널, 기능 플래그가 많아지면 switch factory는 급격히 비대해진다.

### 시나리오 2: storage client 생성

S3, GCS, local, mock이 섞이면 registry나 DI로 바꾸는 편이 낫다.

### 시나리오 3: 테스트 더블

테스트용 구현을 추가하기 시작하면 factory는 보통 과하게 커진다.

---

## 코드로 보기

### Bad

```java
public class PaymentFactory {
    public PaymentPort create(String type) {
        return switch (type) {
            case "CARD" -> new CardPaymentPort();
            case "POINT" -> new PointPaymentPort();
            case "BANK" -> new BankPaymentPort();
            default -> throw new IllegalArgumentException("unknown type");
        };
    }
}
```

### Better: Registry

```java
public class PaymentFactory {
    private final Map<String, Supplier<PaymentPort>> registry;

    public PaymentPort create(String type) {
        Supplier<PaymentPort> supplier = registry.get(type);
        if (supplier == null) {
            throw new IllegalArgumentException("unknown type");
        }
        return supplier.get();
    }
}
```

### Even better: selection and behavior split

```java
public interface PaymentStrategy {
    PaymentResult pay(PaymentRequest request);
}
```

The smell is not the switch itself, but the fact that the switch has become the design.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| small switch factory | 가장 단순하다 | 커지면 유지보수 지옥 | 구현이 2~3개일 때 |
| Registry-backed factory | 선택이 데이터화된다 | 등록 관리가 필요하다 | 구현이 많을 때 |
| Strategy selection | 행동과 생성이 분리된다 | 구조가 더 필요하다 | 알고리즘이 바뀔 때 |

판단 기준은 다음과 같다.

- case가 5개를 넘으면 재검토한다
- factory가 규칙을 판단하기 시작하면 smell이다
- 생성과 선택의 책임을 분리한다

---

## 꼬리질문

> Q: factory switch가 왜 smell인가요?
> 의도: 선택 로직 폭발을 아는지 확인한다.
> 핵심: 생성 규칙이 factory 하나에 몰리기 때문이다.

> Q: Registry로 바꾸면 무조건 좋아지나요?
> 의도: registry도 설계가 필요하다는 걸 아는지 확인한다.
> 핵심: 아닐 수 있고, 숨은 service locator가 되면 안 된다.

> Q: Strategy와 Factory를 같이 써도 되나요?
> 의도: 생성과 행동 분리를 이해하는지 확인한다.
> 핵심: 보통 같이 쓰면 더 선명해진다.

## 한 줄 정리

Factory의 switch가 커지기 시작하면, 선택과 생성 책임을 Registry나 Strategy로 다시 나눠야 한다.

