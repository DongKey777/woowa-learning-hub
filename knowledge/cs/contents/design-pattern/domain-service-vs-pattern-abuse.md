# Domain Service vs Pattern Abuse

> 한 줄 요약: Domain Service는 엔티티에 넣기 어려운 도메인 규칙을 담는 용도지만, 책임이 쌓이면 곧바로 패턴 과사용과 God Service가 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [Specification Pattern](./specification-pattern.md)
> - [Transaction Script vs Rich Domain Model](./transaction-script-vs-rich-domain-model.md)
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [안티 패턴](./anti-pattern.md)
> - [God Object / Spaghetti / Golden Hammer](./god-object-spaghetti-golden-hammer.md)

---

## 핵심 개념

Domain Service는 DDD에서 **엔티티나 값 객체에 넣기 어색한 도메인 규칙**을 담는 객체다.  
하지만 이름에 "Service"가 붙는 순간 모든 로직이 빨려 들어가면서 패턴 과사용이 발생하기 쉽다.

이 문서가 다루는 핵심은 두 가지다.

- 언제 Domain Service가 필요한가
- 언제 Domain Service가 사실상 비대해진 잡동사니인지

### Retrieval Anchors

- `domain service`
- `application service`
- `anemic domain model`
- `transaction script`
- `rich domain model`
- `god service`
- `pattern abuse`

---

## 깊이 들어가기

### 1. Domain Service가 필요한 경우

엔티티 한 개의 책임으로 표현하기 어려운 도메인 규칙이 있을 때다.

- 여러 엔티티를 함께 판단해야 한다
- 정책이 도메인 언어로 존재한다
- 값 객체나 엔티티에 넣으면 의미가 흐려진다

예를 들어 "두 계정 사이의 송금 가능 여부"는 한 계정 엔티티만으로는 설명하기 어렵다.

### 2. Service가 과해지는 신호

- `UserService`, `OrderService`, `PaymentService`가 모든 걸 처리한다
- 상태 변경, 검증, 외부 호출, 매핑이 한 클래스에 섞인다
- 같은 서비스 안에 유스케이스와 도메인 규칙이 뒤섞인다
- 메서드가 엔티티 생성, 검증, 저장, 이벤트 발행까지 다 한다

이때는 Domain Service가 아니라 **Application Service + Domain Model + Policy Object**로 나눠야 할 가능성이 크다.

### 3. 엔티티 행동을 먼저 의심해보자

서비스를 만들기 전에 먼저 묻는 게 좋다.

- 이 규칙은 엔티티의 상태와 직접 관련이 있는가
- 이 규칙은 여러 애그리게잇을 함께 다뤄야 하는가
- 이 규칙은 정책 객체나 상태 객체로 더 자연스럽지 않은가

---

## 실전 시나리오

### 시나리오 1: 송금 서비스

송금 가능 여부, 한도 검사, 수수료 계산은 계좌 하나의 메서드보다 Domain Service가 적합할 수 있다.

### 시나리오 2: 주문 할인 계산

할인 계산이 계속 커지면 Service 대신 Specification이나 Policy Object를 분리하는 편이 낫다.

### 시나리오 3: 주문 취소

취소 가능 여부는 상태 패턴, 취소 수수료는 Policy Object, 흐름 조립은 Application Service가 맡는 식이 더 안전하다.

---

## 코드로 보기

### 적절한 Domain Service

```java
@Service
public class TransferDomainService {
    public TransferDecision canTransfer(Account source, Account target, Money amount) {
        if (!source.isActive() || !target.isActive()) {
            return TransferDecision.denied("inactive account");
        }
        if (source.balance().isLessThan(amount)) {
            return TransferDecision.denied("insufficient balance");
        }
        return TransferDecision.allowed();
    }
}
```

### 과해진 Service

```java
@Service
public class OrderService {
    public void process(OrderRequest request) {
        validate(request);
        updateStatus(request);
        sendEmail(request);
        publishEvent(request);
        callExternalApi(request);
        save(request);
    }
}
```

이런 구조는 도메인 서비스가 아니라 서비스 객체에 모든 책임이 붙은 상태다.

### 나누는 방식

```java
@Service
public class PlaceOrderUseCase {
    private final DiscountPolicy discountPolicy;
    private final OrderRepository repository;

    public void place(PlaceOrderCommand command) {
        int discounted = discountPolicy.apply(command.amount());
        Order order = Order.place(command, discounted);
        repository.save(order);
    }
}
```

Domain Service는 도메인 규칙을, Application Service는 유스케이스 흐름을 담당한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 엔티티 메서드 | 응집도가 높다 | 여러 엔티티 규칙을 담기 어렵다 | 한 개체의 상태 규칙 |
| Domain Service | 도메인 규칙을 모을 수 있다 | 비대해지기 쉽다 | 여러 엔티티에 걸친 규칙 |
| Application Service | 흐름이 보인다 | 도메인 규칙이 섞이기 쉽다 | 유스케이스 조립 |

판단 기준은 다음과 같다.

- 상태와 직접 관련된 규칙은 엔티티나 상태 객체로 보낸다
- 여러 애그리게잇을 함께 다루는 규칙은 Domain Service를 본다
- 외부 호출, 저장, 이벤트는 Application Service가 조립한다

---

## 꼬리질문

> Q: Domain Service와 Application Service의 차이는 무엇인가요?
> 의도: 도메인 규칙과 유스케이스 조립을 분리하는지 확인한다.
> 핵심: 도메인 서비스는 규칙, 애플리케이션 서비스는 흐름이다.

> Q: Service 클래스가 커지면 왜 위험한가요?
> 의도: 서비스가 God Object가 되는 경로를 아는지 확인한다.
> 핵심: 책임이 섞여 변경 이유가 한곳에 모인다.

> Q: Service를 줄이기 위해 무조건 엔티티에 로직을 넣어야 하나요?
> 의도: 극단적으로 반대편으로 가는 실수를 피하는지 확인한다.
> 핵심: 아니다. 정책 객체, 상태 객체, Specification도 함께 고려해야 한다.

## 한 줄 정리

Domain Service는 여러 엔티티에 걸친 도메인 규칙을 담는 그릇이지만, 책임이 커지면 곧바로 패턴 과사용과 God Service가 된다.
