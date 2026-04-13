# SOLID Failure Patterns

> 한 줄 요약: SOLID는 암기용 구호가 아니라, 설계가 깨지는 패턴을 빨리 알아차리기 위한 실패 진단 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [API 설계와 예외 처리](./api-design-error-handling.md)
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)

---

## 핵심 개념

SOLID는 “좋은 코드의 체크리스트”처럼 보이지만, 실전에서는 **깨지는 패턴을 미리 알아차리는 신호**에 가깝다.

- SRP가 깨지면 변경 이유가 하나가 아니다.
- OCP가 깨지면 수정할 때마다 기존 코드를 갈아엎는다.
- LSP가 깨지면 상속이 오히려 예외를 만든다.
- ISP가 깨지면 인터페이스가 무거워지고 구현체가 빈 껍데기가 된다.
- DIP가 깨지면 구체 클래스가 도메인을 끌고 다닌다.

중요한 점은 반대도 마찬가지라는 것이다.

- 원칙을 전혀 안 지키면 구조가 무너진다.
- 원칙을 과하게 지키면 추상화만 늘고 오히려 유지보수성이 떨어진다.

즉, SOLID는 정답이 아니라 **변경 비용을 줄이기 위한 경계 설정 도구**다.

---

## 깊이 들어가기

### 1. SRP: 하나의 이유만 바뀌어야 한다

SRP를 어기면 한 클래스가 여러 변경 이유를 갖는다.

```java
public class OrderService {
    public void placeOrder() { /* 주문 생성 */ }
    public void sendEmail() { /* 메일 발송 */ }
    public void calculateDiscount() { /* 할인 계산 */ }
    public void logAudit() { /* 감사 로그 */ }
}
```

이 구조는 처음엔 단순하지만, 나중에는 주문 정책, 메일 정책, 할인 정책, 로그 정책이 한 파일에 얽힌다.  
한 기능을 바꾸려다 테스트가 깨지고, 영향 범위를 읽는 데 시간이 든다.

반대로 SRP를 과하게 밀면 문제가 반대 방향으로 생긴다.

- `OrderValidationService`
- `OrderDiscountPolicy`
- `OrderAuditWriter`
- `OrderEmailNotifier`

이렇게 쪼개다가 실제로는 조율 코드만 늘어난다.  
SRP의 목표는 클래스 수를 늘리는 게 아니라, **변경 이유를 분리하는 것**이다.

### 2. OCP: 수정 대신 확장을 유도한다

OCP가 깨지는 전형은 `if-else`와 `switch`다.

```java
public int calculateFee(String type, int amount) {
    if (type.equals("CARD")) return amount * 3 / 100;
    if (type.equals("BANK")) return amount * 2 / 100;
    if (type.equals("COUPON")) return 0;
    throw new IllegalArgumentException("unknown type");
}
```

새 타입이 추가되면 기존 함수를 계속 수정해야 한다.  
이건 기능 추가가 아니라 기존 코드 변경의 누적이다.

하지만 OCP도 과하면 문제다.

- 타입이 3개뿐인데 인터페이스와 팩토리를 먼저 만든다
- 확장 포인트가 실제로 없는 시스템에 전략 패턴을 심는다
- 매번 새 구현체를 등록하느라 간접 계층만 늘어난다

OCP는 “무조건 추상화”가 아니라, **변경이 반복되는 지점을 먼저 추상화**하는 것이다.

### 3. LSP: 자식은 부모를 대체할 수 있어야 한다

LSP를 어기면 상속이 안전하지 않다.

```java
class Bird {
    public void fly() { }
}

class Penguin extends Bird {
    @Override
    public void fly() {
        throw new UnsupportedOperationException("penguin cannot fly");
    }
}
```

이 순간 `Bird`를 기대한 코드는 `Penguin`에서 깨진다.  
즉 상속 관계가 “is-a”가 아니라 “looks-like-a”가 되어버린다.

실무에서 LSP는 도메인 불변식과도 연결된다.

- 부모 타입의 전제 조건이 자식에서 더 강해지면 안 된다
- 자식이 부모의 리턴 의미를 바꾸면 안 된다
- 부모가 허용하는 작업을 자식이 막아버리면 안 된다

과한 상속도 문제다.

- 공통 코드만 보려고 억지로 상속을 묶는다
- 사실은 합성으로 해결해야 할 일을 계층으로 만든다

LSP가 잘 안 맞는 계층은 대개 상속보다 **조합**이 맞다.

### 4. ISP: 인터페이스는 작을수록 좋다

ISP를 어기면 구현체가 자신이 쓰지 않는 메서드까지 떠안는다.

```java
public interface ReportManager {
    void generate();
    void exportPdf();
    void email();
    void archive();
}
```

어떤 구현은 이메일만 보내고, 어떤 구현은 PDF만 만든다면 이 인터페이스는 fat interface다.  
호출자는 필요 없는 메서드까지 의존하게 되고, 구현체는 빈 메서드를 채우거나 예외를 던진다.

하지만 ISP도 쪼개기만 하면 끝이 아니다.

- 인터페이스가 지나치게 잘게 쪼개지면 호출자가 여러 인터페이스를 동시에 알아야 한다
- 구현체가 많지 않은데 인터페이스가 남발되면 읽기만 복잡해진다

ISP의 목적은 “작게 쪼개기”가 아니라, **호출자 관점에서 필요한 계약만 노출하기**다.

### 5. DIP: 도메인은 구체 구현을 몰라야 한다

DIP가 깨지면 상위 정책이 하위 기술에 끌려간다.

```java
public class PaymentService {
    private final TossClient tossClient = new TossClient();

    public void pay() {
        tossClient.requestPayment();
    }
}
```

이 구조는 간단하지만, 결제수단이 바뀌면 서비스 자체가 흔들린다.  
도메인은 `PaymentGateway` 같은 추상에 의존하고, 구체 구현은 바깥에서 주입해야 한다.

DIP도 과하면 복잡해진다.

- 추상 클래스/인터페이스가 실체보다 먼저 늘어난다
- 구현 하나뿐인데도 모든 걸 인터페이스로 만든다
- 테스트를 위해 존재하는 추상화가 운영 코드를 지배한다

DIP는 “무조건 인터페이스”가 아니라, **변화하는 부분과 안정적인 부분을 분리하는 것**이다.

---

## 실전 시나리오

### 시나리오 1: 주문 서비스가 God Service가 된다

초기에는 `OrderService` 하나로 충분하다.

- 주문 생성
- 쿠폰 계산
- 재고 검증
- 이메일 발송
- 감사 로그

그런데 시간이 지나면 이 서비스가 모든 정책 변경의 착륙 지점이 된다.

증상:

- 테스트가 느려진다
- 하나 수정하면 다른 기능이 깨진다
- 팀원이 같은 파일을 동시에 수정한다

이건 SRP와 DIP가 같이 무너진 상태다.

### 시나리오 2: 상속 구조가 도메인을 왜곡한다

`Bird`, `FlyingBird`, `Penguin` 같은 구조는 예쁘지만, 실제 도메인이 그 형태를 보장하지 않으면 LSP가 무너진다.

이때 상속을 유지하려고 `UnsupportedOperationException`을 넣는 순간, 설계는 이미 실패했다.  
해결책은 대개 상속 제거, 조합 도입, 정책 객체 분리다.

### 시나리오 3: 인터페이스가 많아질수록 테스트가 쉬워질까?

항상 그렇지 않다.

- 좋은 인터페이스는 테스트를 쉽게 만든다
- 의미 없는 인터페이스는 mocking boilerplate만 만든다

즉, ISP는 테스트 편의를 위한 장난감이 아니라, **계약을 더 정확하게 만드는 작업**이다.

### 시나리오 4: DIP를 지키다 오히려 복잡해진다

아직 대안이 하나뿐인 데도 `Gateway`, `Provider`, `Port`, `Adapter`를 다 만든다.  
이때 팀은 기능보다 구조를 유지하는 데 시간을 쓴다.

이런 경우는 DIP의 과적용이다.

---

## 코드로 보기

### 나쁜 예: SRP/OCP/DIP가 한 번에 깨진 구조

```java
public class OrderService {
    public void process(String type, int amount) {
        if ("CARD".equals(type)) {
            // 카드 결제
        } else if ("BANK".equals(type)) {
            // 계좌이체
        } else if ("COUPON".equals(type)) {
            // 쿠폰
        }

        // 이메일, 로그, 저장, 통계까지 한 메서드에 섞임
    }
}
```

이 구조는 변경 이유가 많고, 확장도 어렵고, 테스트도 비싸다.

### 개선 예: 변경 지점을 분리

```java
public interface PaymentPolicy {
    int calculateFee(int amount);
}

public class CardPaymentPolicy implements PaymentPolicy {
    public int calculateFee(int amount) {
        return amount * 3 / 100;
    }
}

public class OrderService {
    private final PaymentPolicy paymentPolicy;
    private final OrderNotifier notifier;

    public OrderService(PaymentPolicy paymentPolicy, OrderNotifier notifier) {
        this.paymentPolicy = paymentPolicy;
        this.notifier = notifier;
    }

    public void process(int amount) {
        int fee = paymentPolicy.calculateFee(amount);
        notifier.notifyPaid(amount, fee);
    }
}
```

이 구조의 장점은 분명하다.

- 결제 정책 변경은 정책 클래스만 바꾸면 된다
- 알림은 별도 책임으로 분리된다
- `OrderService`는 유스케이스 조율에 집중한다

하지만 여기서도 구현이 하나뿐인 시점에는 너무 일찍 인터페이스를 늘리지 않는 편이 낫다.

---

## 트레이드오프

| 원칙 | 지키면 좋은 점 | 과하면 생기는 문제 | 실전 판단 기준 |
|------|----------------|------------------|----------------|
| SRP | 변경 범위가 줄어든다 | 클래스와 파일이 과도하게 쪼개진다 | 변경 이유가 실제로 다른가 |
| OCP | 새 기능 추가가 안전하다 | 추상화 계층이 과해진다 | 반복되는 변경인가 |
| LSP | 상속이 예측 가능해진다 | 상속이 억지로 유지된다 | 자식이 부모를 진짜 대체 가능한가 |
| ISP | 호출자가 필요한 계약만 본다 | 인터페이스가 너무 잘게 쪼개진다 | 호출자 관점에서 정말 필요한가 |
| DIP | 기술 교체와 테스트가 쉬워진다 | 인터페이스가 목적 없이 난립한다 | 구현 변경 가능성이 충분한가 |

실무 판단은 보통 이 질문으로 정리된다.

1. 지금 이 변화는 자주 일어나는가
2. 그 변화는 도메인 규칙인가, 인프라 기술인가
3. 추상화 비용이 현재 규모에서 감당 가능한가
4. 이 원칙이 변경 비용을 낮추는가, 아니면 구조 비용만 늘리는가

---

## 꼬리질문

> Q: SRP를 지킨다고 클래스를 계속 쪼개면 왜 안 좋은가?  
> 의도: 원칙을 구조의 개수로 오해하는지 확인
> 핵심: 변경 이유를 분리해야지 파일 수를 늘리는 게 목표가 아니다

> Q: OCP는 왜 실제로 지키기 어려운가?  
> 의도: 확장 포인트를 사전에 예측하는 능력 확인
> 핵심: 자주 바뀌는 지점을 정확히 찾는 것이 어렵고, 과한 추상화는 오히려 비용이다

> Q: LSP가 깨졌을 때 가장 먼저 보이는 증상은 무엇인가?  
> 의도: 상속 설계가 안정적인지 확인
> 핵심: 자식 타입에서 예외가 늘어나거나 부모 계약을 만족하지 못한다

> Q: ISP와 DTO 분리는 어떤 관계가 있는가?  
> 의도: 인터페이스 계약과 데이터 노출의 경계를 이해하는지 확인
> 핵심: 호출자에게 필요한 것만 노출하는 사고는 DTO와 API 설계에도 이어진다

> Q: DIP를 지키려다 과해진 구조는 어떻게 줄일 것인가?  
> 의도: 실전에서 추상화를 정리할 수 있는지 확인
> 핵심: 구현체가 하나뿐인 추상은 없애고, 실제 변화 지점만 남긴다

---

## 한 줄 정리

SOLID는 “무조건 지켜야 하는 규칙”이 아니라, **설계가 실패하는 지점을 미리 발견하고, 필요한 만큼만 추상화하기 위한 판단 도구**다.
