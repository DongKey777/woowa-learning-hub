# Facade vs Adapter vs Proxy

> 한 줄 요약: 세 패턴 모두 "중간에 끼는 객체"처럼 보이지만, Facade는 복잡성을 숨기고, Adapter는 인터페이스를 맞추고, Proxy는 호출을 제어한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [데코레이터 vs 프록시](./decorator-vs-proxy.md)
> - [전략 (Strategy)](./strategy-pattern.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

세 패턴은 모두 "중간 계층"을 만든다. 하지만 의도가 다르다.

- Facade: 복잡한 하위 시스템을 단순한 진입점 하나로 묶는다
- Adapter: 서로 맞지 않는 인터페이스를 연결한다
- Proxy: 실제 객체 대신 호출을 받아 제어한다

이 차이를 모르고 쓰면, 단순한 래퍼를 모든 문제의 답처럼 오해하게 된다.

### 한 줄 구분

- Facade: "쓰기 편하게 묶자"
- Adapter: "호환되게 바꾸자"
- Proxy: "호출을 대신 받자"

---

## 깊이 들어가기

### 1. Facade는 복잡성을 숨긴다

Facade는 하위 시스템이 너무 복잡할 때, 사용자가 알아야 할 순서를 하나의 진입점으로 정리한다.

```java
public class OrderFacade {
    private final InventoryService inventoryService;
    private final PaymentService paymentService;
    private final ShippingService shippingService;

    public void placeOrder(OrderRequest request) {
        inventoryService.reserve(request.itemId());
        paymentService.pay(request.paymentInfo());
        shippingService.createShipment(request.address());
    }
}
```

호출자는 내부 순서를 몰라도 된다.  
중요한 건 기능을 바꾸는 것이 아니라, **사용성을 바꾸는 것**이다.

### 2. Adapter는 인터페이스를 맞춘다

이미 있는 클래스가 필요한 인터페이스와 다를 때 사용한다.

```java
public interface PaymentGateway {
    void pay(int amount);
}

public class LegacyCardClient {
    public void sendPayment(String cents) {
        System.out.println("pay " + cents);
    }
}

public class LegacyCardAdapter implements PaymentGateway {
    private final LegacyCardClient client;

    public LegacyCardAdapter(LegacyCardClient client) {
        this.client = client;
    }

    @Override
    public void pay(int amount) {
        client.sendPayment(String.valueOf(amount * 100));
    }
}
```

Adapter는 "새 기능 추가"보다 "기존 자산 재활용"에 가깝다.

### 3. Proxy는 호출을 제어한다

Proxy는 접근 제어, 캐싱, 지연 로딩, 로깅 같은 부가 기능을 얹는다.

```java
public class CachedReportProxy implements ReportService {
    private final ReportService target;
    private Report cached;

    public Report getReport() {
        if (cached != null) {
            return cached;
        }
        cached = target.getReport();
        return cached;
    }
}
```

Spring AOP나 `@Transactional`은 이 감각과 가깝다.  
반면 Facade는 호출 제어가 아니라 흐름 정리에 더 가깝다.

---

## 실전 시나리오

### 시나리오 1: 레거시 SDK를 붙인다

외부 결제 SDK가 내부 인터페이스와 다르면 Adapter가 자연스럽다.

### 시나리오 2: 복잡한 주문 흐름을 단순화한다

여러 서비스 호출 순서를 외부에 노출하지 않고 싶으면 Facade가 맞다.

### 시나리오 3: 인증, 트랜잭션, 캐시를 끼운다

실제 호출 전후에 공통 기능을 넣고 싶으면 Proxy가 더 적합하다.

---

## 코드로 보기

### Before: 호출부가 복잡하다

```java
inventoryService.reserve(itemId);
couponService.validate(couponId);
paymentService.pay(amount);
shippingService.ship(address);
```

### After: Facade

```java
orderFacade.placeOrder(request);
```

### Adapter

```java
PaymentGateway gateway = new LegacyCardAdapter(new LegacyCardClient());
gateway.pay(10000);
```

### Proxy

```java
ReportService service = new CachedReportProxy(new RealReportService());
service.getReport();
```

---

## 트레이드오프

| 패턴 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Facade | 복잡한 흐름을 단순화한다 | 내부 단계가 숨겨진다 | 서브시스템이 많을 때 |
| Adapter | 기존 코드를 재활용한다 | 변환 코드가 추가된다 | 인터페이스 불일치가 있을 때 |
| Proxy | 호출 제어와 부가기능을 넣기 쉽다 | 흐름이 숨겨진다 | 트랜잭션, 캐시, 접근 제어 |

판단 기준은 명확하다.

- 사용자가 헷갈리는 순서 자체를 줄이고 싶으면 Facade
- 외부 API와 내부 API를 맞추고 싶으면 Adapter
- 호출 자체를 감싸고 싶으면 Proxy

---

## 꼬리질문

> Q: Facade와 Adapter를 헷갈리면 어떤 실수가 생기나요?
> 의도: "단순화"와 "호환"의 차이를 구분하는지 확인한다.
> 핵심: Facade는 사용성을, Adapter는 인터페이스를 맞춘다.

> Q: Spring AOP는 왜 Proxy인가요?
> 의도: 호출 제어와 기능 조합을 구분하는지 확인한다.
> 핵심: 메서드 호출을 가로채 부가기능을 넣기 때문이다.

> Q: Facade를 너무 많이 쓰면 무엇이 문제인가요?
> 의도: 추상화가 항상 좋은 게 아니라는 점을 아는지 확인한다.
> 핵심: 내부 흐름이 숨겨져서 디버깅이 어려워진다.

---

## 한 줄 정리

Facade는 복잡성을 숨기고, Adapter는 인터페이스를 맞추고, Proxy는 호출을 제어한다.
