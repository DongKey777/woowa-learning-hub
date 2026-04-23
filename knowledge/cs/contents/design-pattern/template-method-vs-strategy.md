# 템플릿 메소드 vs 전략

> 한 줄 요약: 템플릿 메소드는 **고정된 흐름 안의 필수 단계/선택적 hook**을 상속으로 연다. 전략은 **바뀌는 규칙 전체**를 조합으로 갈아낀다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
> - [템플릿 메소드 패턴](./template-method.md)
> - [전략 패턴](./strategy-pattern.md)
> - [Template Hook Smells: 템플릿 메소드가 과해졌다는 신호](./template-hook-smells.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

retrieval-anchor-keywords: template method vs strategy, beginner chooser, runtime vs fixed flow, fixed workflow vs runtime algorithm selection, hook method vs abstract method, abstract step vs strategy, template method beginner, strategy beginner, template hook smell, composition over inheritance, when to use template method, when to use strategy, fixed workflow inheritance, runtime policy swap

---

## 이 문서는 언제 읽으면 좋은가

아래 질문이 한 번이라도 떠오르면 이 비교 문서를 먼저 보면 된다.

- "상속으로 뼈대를 잡아야 하나, 객체를 주입해야 하나?"
- "흐름은 같은데 일부만 다르다"와 "규칙 자체를 갈아낀다"가 자꾸 섞일 때
- hook method를 열어야 하는지, 그냥 전략으로 빼야 하는지 헷갈릴 때

핵심은 패턴 이름이 아니라 **무엇이 바뀌고, 누가 그 변화를 고르는가**다.

---

## 30초 선택 가이드

먼저 두 질문만 보면 대부분 정리된다.

1. **공통 순서를 실수로 바꾸면 안 되는가?**
   `검증 -> 변환 -> 저장`처럼 흐름이 고정이라면 템플릿 메소드 쪽이다.
2. **구현을 실행 시점에 바꿔 끼워야 하는가?**
   결제 수단, 할인 정책, 정렬 기준처럼 호출자나 설정이 구현을 고르면 전략 쪽이다.

짧게 외우면 다음과 같다.

- **"흐름은 고정, 단계만 다름"**이면 템플릿 메소드
- **"규칙을 갈아끼우는 문제"**면 전략
- **"기본 흐름에 선택적 덧붙임만 필요"**하면 템플릿 메소드의 hook
- **"hook가 사실상 전체 규칙을 대신"**하기 시작하면 전략이나 pipeline 쪽으로 다시 본다

---

## 한눈에 구분

| 질문 | 템플릿 메소드 | 전략 |
|---|---|---|
| 무엇이 안정적인가 | 알고리즘의 순서 | 호출 흐름은 그대로, 선택할 규칙만 바뀜 |
| 무엇이 바뀌는가 | 일부 단계 구현 | 규칙/알고리즘 전체 |
| 누가 선택하는가 | 상속 구조를 만든 설계자 | 호출자, 설정, DI, 런타임 |
| 확장 방식 | 상속 | 조합 |
| 런타임 교체 | 거의 없음 | 핵심 장점 |
| hook의 위치 | 고정된 흐름 안의 선택적 확장 지점 | 개념적으로 hook이 아니라 교체 대상 자체 |
| 잘 맞는 예시 | 파서, 배치 파이프라인, 공통 인증 뼈대 | 할인 정책, 결제 수단, 정렬 방식 |
| 위험 신호 | 하위 클래스와 hook가 계속 늘어남 | 클래스 수가 과도하게 늘고 실제 변화는 거의 없음 |

한 문장으로 다시 정리하면:

- 템플릿 메소드: **"순서를 통제하고 싶다"**
- 전략: **"방법을 바꿔 끼우고 싶다"**

---

## 추상 단계, hook, 전략은 같은 것이 아니다

이 비교에서 가장 자주 섞이는 지점이다.

| 구분 | 의미 | 기본 구현 | 누가 고르는가 | 언제 쓰는가 |
|---|---|---|---|---|
| 추상 단계 | 없으면 알고리즘이 완성되지 않는 필수 빈칸 | 없음 | 하위 클래스가 반드시 구현 | 구현체마다 핵심 단계가 다를 때 |
| hook method | 있어도 되고 없어도 되는 선택적 확장 | 안전한 기본값 있음 | 하위 클래스가 필요할 때만 override | 공통 흐름 끝에 알림, 메트릭, 부가 처리만 붙일 때 |
| 전략 | 교체 가능한 규칙/알고리즘 객체 | 없음 또는 별도 기본 전략 | 호출자/설정/DI가 선택 | 런타임에 구현을 바꿔야 할 때 |

### 템플릿 메소드 안에서의 구분

- `convert()`처럼 없으면 흐름이 완성되지 않으면 `추상 단계`
- `afterExport()`처럼 기본은 비워 두고 필요할 때만 덧붙이면 `hook`

### 전략과의 경계

전략은 "여기 한 번 override 해도 된다"가 아니다.  
**아예 어떤 규칙 객체를 쓸지 바꿔 끼우는 선택점**이다.

그래서 아래 같은 요구는 hook보다 전략 쪽이다.

- 요청마다 다른 할인 규칙을 고른다
- 테넌트 설정에 따라 다른 결제 구현을 쓴다
- 정렬 방식이 사용자 입력에 따라 바뀐다

반대로 아래 같은 요구는 전략보다 템플릿 hook이 자연스럽다.

- 공통 내보내기 흐름 끝에 메트릭만 남긴다
- 테스트용 구현에서만 후처리를 추가한다
- 특정 채널에서만 감사 로그를 한 줄 더 찍는다

hook가 `stepOrder()`처럼 **순서를 뒤집거나 건너뛰는 힘**을 가지기 시작하면 템플릿 메소드의 장점이 무너진다.  
그 시점부터는 [Template Hook Smells](./template-hook-smells.md)를 같이 봐야 한다.

---

## 같은 도메인에서 비교하기

### 1. 보고서 내보내기: 템플릿 메소드

보고서 내보내기가 항상 아래 순서를 따른다고 하자.

1. 입력 검증
2. 포맷 변환
3. 파일 저장
4. 선택적 후처리

여기서 중요한 것은 **순서 고정**이다.

- `convert()`는 포맷마다 달라지는 필수 단계
- `afterExport()`는 필요할 때만 붙이는 hook

이 문제는 "실행 방법을 매번 선택"하는 문제보다  
"내보내기 순서를 흔들리지 않게 유지"하는 문제가 더 크다.  
그래서 템플릿 메소드가 자연스럽다.

### 2. 할인 정책: 전략

할인 계산은 보통 아래처럼 바뀐다.

- 일반 회원 할인
- VIP 할인
- 프로모션 할인
- 파트너 전용 할인

여기서 중요한 것은 **어떤 규칙을 쓸지 선택하는 일**이다.  
공통 흐름의 순서를 고정하는 것보다, 규칙을 바꿔 끼우는 유연성이 더 중요하다.

그래서 이 문제는 전략이 자연스럽다.

### 3. 둘을 함께 쓰는 구조도 많다

실무에서는 둘 중 하나만 고르는 경우보다, 경계를 나눠 함께 쓰는 경우가 많다.

- 주문 처리 전체 순서 `validate -> reserve -> pay -> persist` 는 템플릿/고정 흐름
- `pay` 단계 안에서 카드/계좌이체/간편결제를 고르는 것은 전략
- 저장 후 감사 로그만 추가하는 것은 hook

즉 질문은 "둘 중 누가 더 고급인가"가 아니라  
**"어디까지가 고정 흐름이고, 어디부터가 교체 규칙인가"**다.

---

## 코드로 보기

### 1. 템플릿 메소드: 필수 단계 + 선택적 hook

```java
public abstract class ReportExporter {
    public final void export(List<Order> orders, Path path) {
        validate(orders);
        String body = convert(orders);
        writeFile(path, body);
        afterExport(path);
    }

    private void validate(List<Order> orders) {
        if (orders.isEmpty()) {
            throw new IllegalArgumentException("orders must not be empty");
        }
    }

    protected abstract String convert(List<Order> orders);

    protected void afterExport(Path path) {
        // optional hook
    }

    private void writeFile(Path path, String body) {
        // 공통 저장 로직
    }
}
```

여기서 `convert()`는 필수 단계고, `afterExport()`는 hook이다.  
둘 다 override될 수 있어 보여도 역할은 다르다.

### 2. 전략: 규칙 객체를 런타임에 바꾼다

```java
public interface DiscountStrategy {
    int discount(int price);
}

public class VipDiscountStrategy implements DiscountStrategy {
    @Override
    public int discount(int price) {
        return (int) (price * 0.8);
    }
}

public class OrderService {
    private final DiscountStrategy discountStrategy;

    public OrderService(DiscountStrategy discountStrategy) {
        this.discountStrategy = discountStrategy;
    }

    public int price(int originalPrice) {
        return discountStrategy.discount(originalPrice);
    }
}
```

여기서 핵심은 `OrderService`가 하위 클래스로 늘어나지 않는다는 점이다.  
규칙은 주입된 전략이 맡고, 호출부가 교체를 결정한다.

### 3. 같이 쓰는 예시

```java
public abstract class CheckoutFlow {
    private final PaymentStrategy paymentStrategy;

    protected CheckoutFlow(PaymentStrategy paymentStrategy) {
        this.paymentStrategy = paymentStrategy;
    }

    public final Receipt checkout(Order order) {
        validate(order);
        reserve(order);
        PaymentResult paymentResult = paymentStrategy.pay(order);
        afterPayment(order, paymentResult);
        return persist(order, paymentResult);
    }

    protected void reserve(Order order) {
        // default no-op
    }

    protected void afterPayment(Order order, PaymentResult paymentResult) {
        // optional hook
    }

    protected abstract Receipt persist(Order order, PaymentResult paymentResult);

    private void validate(Order order) {
        // 공통 검증
    }
}
```

이 코드는 경계를 잘 보여준다.

- `checkout()` 순서는 템플릿 메소드
- `paymentStrategy.pay(...)`는 전략
- `afterPayment(...)`는 hook

---

## 자주 하는 오해

### 1. "상속이 있으면 템플릿 메소드 아닌가요?"

아니다. 상속을 쓴다고 모두 템플릿 메소드가 되진 않는다.  
**상위 클래스가 알고리즘의 순서를 고정**해야 템플릿 메소드다.

### 2. "인터페이스가 있으면 전략 아닌가요?"

아니다. 인터페이스가 있어도 런타임 교체 요구가 없다면 단순 분리일 수 있다.  
전략의 핵심은 **교체 가능한 규칙을 외부에서 선택**한다는 점이다.

### 3. "hook 하나 추가할까, 전략으로 뺄까?"

다음 기준으로 보면 된다.

- 기본 흐름은 그대로고, 특정 구현에서만 부가 행동을 더한다: hook
- 실행 규칙 자체를 다른 구현으로 바꾼다: 전략
- hook가 많아져서 상위 클래스 내부 순서를 계속 설명해야 한다: 템플릿 메소드가 과해진 신호

---

## 선택 실수 줄이는 체크리스트

- "이 순서를 누가 통제해야 하지?"가 먼저면 템플릿 메소드
- "호출자가 어떤 구현을 쓸지 골라야 하지?"가 먼저면 전략
- "기본값이 안전한 선택적 확장인가?"면 hook
- "없으면 알고리즘이 완성되지 않는가?"면 추상 단계
- "하위 클래스/훅이 계속 늘어나나?"면 전략, pipeline, 조합 쪽으로 다시 보기

---

## 꼬리질문

> Q: 템플릿 메소드 안에서 전략을 같이 써도 되나요?
> 의도: 패턴을 배타적으로만 보는지 확인한다.
> 핵심: 가능하다. 고정 흐름 안의 특정 단계만 교체 규칙이면 전략을 함께 두는 편이 자연스럽다.

> Q: hook method와 전략의 차이를 한 문장으로 말하면?
> 의도: 선택적 확장과 런타임 교체를 구분하는지 확인한다.
> 핵심: hook은 고정 흐름 안의 선택적 덧붙임이고, 전략은 바뀌는 규칙 전체를 외부에서 갈아끼우는 것이다.

> Q: `beforeX`, `afterX` hook이 계속 늘어나면 무조건 잘못인가요?
> 의도: 템플릿 메소드의 한계를 감지하는지 확인한다.
> 핵심: 몇 개는 괜찮지만, hook가 순서 통제를 흐리기 시작하면 전략이나 pipeline으로 분해할 신호다.

---

## 한 줄 정리

템플릿 메소드는 **고정된 흐름 안의 필수 단계와 선택적 hook**을 상속으로 열고, 전략은 **바뀌는 규칙 자체를 런타임에 교체**한다.
