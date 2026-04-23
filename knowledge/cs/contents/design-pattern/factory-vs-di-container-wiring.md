# Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성

> 한 줄 요약: 애플리케이션 시작 시 고정되는 객체 그래프는 DI 컨테이너가 맡고, 요청마다 달라지는 선택과 짧은 생명주기 생성은 여전히 hand-written factory나 builder가 맡는다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [팩토리 (Factory)](./factory.md)
> - [팩토리 패턴 기초](./factory-basics.md)
> - [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
> - [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)
> - [Registry Pattern](./registry-pattern.md)
> - [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
> - [Singleton vs DI Container Scope](./singleton-vs-di-container-scope.md)
> - [Service Locator Antipattern](./service-locator-antipattern.md)

retrieval-anchor-keywords: factory vs di container, spring bean factory method, handwritten factory vs @Bean, framework wiring factory example, dependency injection wiring vs runtime factory, conditional bean vs manual factory, payment handler map injection, applicationcontext getbean service locator, beginner spring factory, di container wiring beginner, request dto bean, command object not bean, builder vs di container

---

## 핵심 개념

먼저 아주 단순하게 나누면 된다.

- **Factory가 답하는 질문**: "지금 어떤 객체를 만들까?"
- **DI 컨테이너가 답하는 질문**: "애플리케이션이 뜰 때 어떤 객체들을 연결해 둘까?"

그래서 판단 기준도 두 갈래다.

- 배포 환경, 설정, 프레임워크 생명주기에 따라 **한 번 연결해 두면 되는 객체**면 DI 컨테이너가 더 자연스럽다.
- 요청 데이터, 사용자 입력, 현재 결제수단처럼 **호출 시점마다 달라지는 선택**이면 hand-written factory나 registry가 남는다.

한 문장 규칙:
**"시작할 때 고정되면 컨테이너, 호출할 때 바뀌면 factory"**로 먼저 생각하면 대부분 맞다.

---

## 먼저 30초 판단표

| 상황 | 기본 선택 | 이유 |
|---|---|---|
| `Service`, `Client`, `Repository` 같은 앱 wiring | DI 컨테이너 | 생성보다 의존성 그래프 연결이 핵심이다 |
| 같은 타입의 이름 있는 생성 | 정적 팩토리 메서드 | 별도 factory 클래스를 늘리지 않아도 된다 |
| 옵션 많은 한 객체 조립 | Builder | 구현 선택보다 조립 가독성이 중요하다 |
| 런타임 입력으로 구현 선택 | Factory / Registry + DI | 컨테이너는 객체를 준비하고, 선택은 코드가 한다 |
| 요청마다 새로 만드는 값 객체/커맨드 | 생성자 / 정적 팩토리 / Builder | 컨테이너가 사용자 입력을 대신 넣어주지 않는다 |

---

## 예시 1: 손으로 서비스 wiring 하던 factory는 컨테이너로 옮긴다

처음엔 아래처럼 `*Factory`를 만들기 쉽다.

```java
public class BillingServiceFactory {
    public BillingService create(BillingProperties props) {
        HttpClient httpClient = HttpClient.newHttpClient();
        TaxClient taxClient = new TaxClient(httpClient, props.taxBaseUrl());
        ReceiptPublisher receiptPublisher = new KafkaReceiptPublisher(props.topic());
        return new BillingService(taxClient, receiptPublisher);
    }
}
```

이 코드는 "어떤 구현을 런타임에 고를까"보다 **앱 시작 시 의존성을 한 번 묶는 작업**에 가깝다.
이럴 때는 DI 컨테이너가 더 잘 맞는다.

```java
@Configuration
public class BillingConfig {
    @Bean
    public HttpClient httpClient() {
        return HttpClient.newHttpClient();
    }

    @Bean
    public TaxClient taxClient(HttpClient httpClient, BillingProperties props) {
        return new TaxClient(httpClient, props.taxBaseUrl());
    }

    @Bean
    public ReceiptPublisher receiptPublisher(BillingProperties props) {
        return new KafkaReceiptPublisher(props.topic());
    }
}

@Service
public class BillingService {
    private final TaxClient taxClient;
    private final ReceiptPublisher receiptPublisher;

    public BillingService(TaxClient taxClient, ReceiptPublisher receiptPublisher) {
        this.taxClient = taxClient;
        this.receiptPublisher = receiptPublisher;
    }
}
```

왜 더 나은가.

- `BillingServiceFactory`라는 중간 계층이 사라진다
- 의존성이 생성자 시그니처에 드러난다
- 테스트에서 필요한 의존성만 바꿔 주입하기 쉽다
- 프레임워크가 생명주기와 wiring을 관리한다

여기서 `@Bean` 메서드는 여전히 "factory method"다.
차이는 **앱 전역 wiring의 소유권을 프레임워크에 넘겼다**는 점이다.

---

## 예시 2: 배포 환경별 구현 선택도 컨테이너가 더 자연스러울 때가 많다

스토리지 구현이 `local` 또는 `s3` 중 하나로 **배포 시점에 고정**된다면, hand-written factory보다 조건부 bean wiring이 읽기 쉽다.

```java
@Configuration
public class StorageConfig {
    @Bean
    @ConditionalOnProperty(name = "storage.provider", havingValue = "s3")
    public StorageClient s3StorageClient(StorageProperties props) {
        return new S3StorageClient(props.bucket(), props.region());
    }

    @Bean
    @ConditionalOnProperty(
        name = "storage.provider",
        havingValue = "local",
        matchIfMissing = true
    )
    public StorageClient localStorageClient(StorageProperties props) {
        return new LocalStorageClient(props.rootPath());
    }
}
```

서비스는 그냥 `StorageClient`를 주입받는다.

```java
@Service
public class FileUploadService {
    private final StorageClient storageClient;

    public FileUploadService(StorageClient storageClient) {
        this.storageClient = storageClient;
    }
}
```

이 경우 `StorageClientFactory.create()`를 따로 둘 이유가 약하다.
선택 기준이 요청마다 바뀌지 않고 설정으로 고정되기 때문이다.

---

## 예시 3: 런타임 선택은 컨테이너가 대신하지 않는다

반대로 결제 방식처럼 **요청마다 달라지는 선택**은 여전히 코드에 남아야 한다.

```java
public interface PaymentHandler {
    PaymentMethod supports();
    void pay(Order order);
}

@Component
public class CardPaymentHandler implements PaymentHandler {
    @Override
    public PaymentMethod supports() {
        return PaymentMethod.CARD;
    }

    @Override
    public void pay(Order order) {
        // ...
    }
}

@Component
public class PointPaymentHandler implements PaymentHandler {
    @Override
    public PaymentMethod supports() {
        return PaymentMethod.POINT;
    }

    @Override
    public void pay(Order order) {
        // ...
    }
}
```

컨테이너는 핸들러 인스턴스를 준비해 줄 수 있다.
하지만 "이번 주문은 어떤 핸들러를 써야 하는가"는 여전히 애플리케이션 코드가 정해야 한다.

```java
@Component
public class PaymentHandlerFactory {
    private final Map<PaymentMethod, PaymentHandler> handlers;

    public PaymentHandlerFactory(List<PaymentHandler> handlers) {
        this.handlers = handlers.stream()
            .collect(Collectors.toUnmodifiableMap(
                PaymentHandler::supports,
                handler -> handler
            ));
    }

    public PaymentHandler get(PaymentMethod method) {
        PaymentHandler handler = handlers.get(method);
        if (handler == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return handler;
    }
}
```

```java
@Service
public class CheckoutService {
    private final PaymentHandlerFactory paymentHandlerFactory;

    public CheckoutService(PaymentHandlerFactory paymentHandlerFactory) {
        this.paymentHandlerFactory = paymentHandlerFactory;
    }

    public void checkout(Order order) {
        paymentHandlerFactory.get(order.getPaymentMethod()).pay(order);
    }
}
```

핵심은 다음이다.

- 컨테이너가 `CardPaymentHandler`, `PointPaymentHandler`를 만들어 준다
- `PaymentHandlerFactory`가 런타임 입력으로 적절한 구현을 고른다

즉 **DI와 factory는 경쟁 관계가 아니라 역할 분담 관계**일 수 있다.
다만 이 구조가 단순 lookup만 한다면 [Registry Pattern](./registry-pattern.md)에 더 가깝게 부를 수도 있다.
핸들러 컬렉션 주입에서 이 경계를 바로 자르고 싶다면 [주입된 Handler Map에서 Registry vs Factory](./registry-vs-factory-injected-handler-maps.md)를 이어서 보면 된다.

---

## 예시 4: 요청 데이터로 만드는 객체는 컨테이너로 넘기지 않는다

아래처럼 메서드 인자로부터 바로 만들어지는 객체는 DI 컨테이너보다 일반 생성 방식이 더 자연스럽다.

```java
CreateCouponCommand command = new CreateCouponCommand(code, expiresAt, limit);

Money refundAmount = Money.of("KRW", amount);

UploadRequest request = UploadRequest.builder()
    .filename(filename)
    .contentType(contentType)
    .size(size)
    .build();
```

이런 객체는

- 생명주기가 짧고
- 호출마다 값이 달라지고
- 사용자 입력이나 메서드 인자에 강하게 묶인다

그래서 컨테이너가 관리할 대상이 아니라 **호출부가 직접 만드는 데이터**에 가깝다.
요청 DTO, command, value object 경계를 이 예시만 따로 다시 잡고 싶다면 [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)를 이어서 보면 된다.

---

## 헷갈리기 쉬운 포인트

- `@Bean` 메서드는 팩토리 메서드다. 다만 "앱 wiring"을 손으로 쓰지 않고 프레임워크가 관리하게 만든다는 점이 다르다.
- `ApplicationContext.getBean()`을 서비스 안에서 직접 호출하면 DI를 쓰는 것이 아니라 [Service Locator Antipattern](./service-locator-antipattern.md) 쪽으로 미끄러질 수 있다.
- handler map을 주입받았다고 해서 컨테이너가 런타임 정책까지 대신 결정해 주는 것은 아니다.
- `new`가 남아 있다고 해서 무조건 냄새는 아니다. 단순 값 객체와 요청 DTO는 직접 생성이 더 읽기 쉽다.

---

## 언제 무엇을 택하나

| 질문 | 우선 검토할 선택 |
|---|---|
| 앱 시작 시 의존성 그래프를 묶는 일인가 | DI 컨테이너 |
| 같은 타입에 이름 있는 생성만 필요한가 | 정적 팩토리 메서드 |
| 한 객체를 읽기 좋게 조립하는가 | Builder |
| 런타임 입력으로 구현을 고르는가 | Factory / Registry |
| 전역 조회로 숨은 의존성을 만들고 있는가 | Service Locator 여부 점검 |

---

## 한 줄 정리

DI 컨테이너는 **애플리케이션 wiring**을 대신하고, factory는 **호출 시점의 선택과 생성 규칙**을 담당한다.
둘 중 하나만 고르는 문제가 아니라, 어느 책임을 어디에 둘지 나누는 문제로 보면 된다.
