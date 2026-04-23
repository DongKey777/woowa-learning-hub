# Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택

> 한 줄 요약: `@Qualifier`는 "컨테이너가 이 주입 지점에 어떤 bean을 꽂을지"를 정하는 장치이고, `Map<String, Bean>`/router 패턴은 "애플리케이션 코드가 요청마다 어떤 전략을 실행할지"를 정하는 장치다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 injection-time 후보 선택과 runtime 전략 선택을 결제/알림 예제로 분리해 주는 **beginner boundary primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](../design-pattern/bean-name-vs-domain-key-lookup.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)

retrieval-anchor-keywords: spring router vs qualifier, map string bean router, map string bean vs @qualifier, spring map bean 주입 vs qualifier, map string bean 언제 쓰는지, qualifier 언제 쓰는지, 처음 배우는데 qualifier router 차이, 큰 그림 qualifier vs router, 고정 wiring vs runtime selection, injection-time qualifier, runtime strategy selection, per request strategy selection, collection injection router, bean name vs domain key, 요청마다 구현체 선택

## 이 문서 다음에 보면 좋은 문서

- 단일 후보 기본값, 명시 선택, 전체 수집을 먼저 표로 나누고 싶다면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)로 이어진다.
- bean 이름 문자열과 역할 annotation의 경계를 보고 싶다면 [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)로 이어진다.
- `Map<String, T>`가 컨테이너에서 어떻게 주입되는지까지 같이 보려면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)를 본다.
- `Map<String, Bean>`의 key를 외부 API 값과 바로 묶어도 되는지 헷갈리면 [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](../design-pattern/bean-name-vs-domain-key-lookup.md)로 이어진다.

---

## 먼저 큰 그림

처음 배우는데 `Map<String, Bean>`과 `@Qualifier`가 둘 다 "여러 구현체 중 하나를 고른다"처럼 보여서 헷갈리면, "언제 쓰는지"를 먼저 자르면 된다.

- 애플리케이션이 뜰 때 한 번 고정할 선택이면 `@Qualifier`
- 요청 값이나 enum에 따라 매번 달라질 선택이면 router
- `Map<String, Bean>`은 후보를 모아 두는 출발점이지, 그 자체가 `@Qualifier`의 대체품은 아니다

한 줄로 줄이면 **고정 wiring은 qualifier, 호출마다 달라지는 분기는 router**다.

---

## 핵심 구분

헷갈릴 때는 아래 세 질문만 먼저 나누면 된다.

| 질문 | `@Qualifier` | `Map<String, Bean>` / router |
|---|---|---|
| 누가 고르나 | Spring 컨테이너 | 애플리케이션 코드 |
| 언제 고르나 | bean 주입 시점 | 메서드 호출마다, 요청마다 |
| 무엇을 기준으로 고르나 | wiring 의도, 역할, 고정된 선택 규칙 | 사용자 입력, enum, 파트너사, 채널 같은 runtime 값 |

즉, 둘 다 "여러 구현체 중 하나를 쓴다"는 점은 비슷하지만, **선택 주체와 선택 시점이 다르다**.

- `@Qualifier`는 "이 서비스는 처음부터 이 구현체를 써야 한다"에 가깝다.
- router는 "이번 호출에서는 이 구현체를 써야 한다"에 가깝다.

---

## 결제 예제: `@Qualifier`

결제 클라이언트가 두 개 있다고 가정한다.

```java
public interface PaymentClient {
    void pay(PaymentCommand command);
}

@Component("tossPaymentClient")
public class TossPaymentClient implements PaymentClient {
}

@Component("kakaoPaymentClient")
public class KakaoPaymentClient implements PaymentClient {
}
```

```java
@Service
public class SettlementService {
    private final PaymentClient paymentClient;

    public SettlementService(
            @Qualifier("kakaoPaymentClient") PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }

    public void settle(PaymentCommand command) {
        paymentClient.pay(command);
    }
}
```

여기서 중요한 점은 `SettlementService`가 실행될 때마다 컨테이너가 다시 고르지 않는다는 것이다.

- 애플리케이션 시작 시점에 `SettlementService`는 `kakaoPaymentClient`로 wiring된다
- 이후 요청이 100번 와도 같은 `PaymentClient`를 쓴다
- 즉, 이 문제는 "이번 서비스는 어떤 bean을 써야 하는가"라는 **구성 문제**다

## 결제 예제: router

```java
@Service
public class PaymentRouter {
    private final Map<String, PaymentClient> paymentClients;

    public PaymentRouter(Map<String, PaymentClient> paymentClients) {
        this.paymentClients = paymentClients;
    }

    public void pay(String pgCode, PaymentCommand command) {
        PaymentClient paymentClient = paymentClients.get(pgCode);
        if (paymentClient == null) {
            throw new IllegalArgumentException("Unknown pgCode: " + pgCode);
        }
        paymentClient.pay(command);
    }
}
```

여기서 컨테이너는 `PaymentRouter`에 후보를 **전부 주입**할 뿐이다.

- `paymentClients`에는 `tossPaymentClient`, `kakaoPaymentClient`가 모두 들어간다
- 실제 선택은 `pay()`가 호출될 때 `pgCode`로 결정된다
- 즉, 이 문제는 "이번 결제 요청은 어느 PG로 보낼까"라는 **runtime dispatch 문제**다

초보자 기준으로는 아래처럼 외우면 된다.

- `SettlementService(@Qualifier(...))` -> 서비스 wiring을 고정
- `PaymentRouter(Map<String, PaymentClient>)` -> 요청마다 전략을 선택

---

## 알림 예제로 한 번 더 보기

알림 채널도 같은 방식으로 갈린다.

```java
public interface NotificationSender {
    void send(NotificationMessage message);
}

@Component("emailSender")
public class EmailNotificationSender implements NotificationSender {
}

@Component("smsSender")
public class SmsNotificationSender implements NotificationSender {
}
```

### 특정 용도의 서비스가 항상 같은 채널을 쓴다면 qualifier가 맞다

```java
@Service
public class ReceiptSender {
    private final NotificationSender notificationSender;

    public ReceiptSender(
            @Qualifier("emailSender") NotificationSender notificationSender) {
        this.notificationSender = notificationSender;
    }

    public void sendReceipt(NotificationMessage message) {
        notificationSender.send(message);
    }
}
```

영수증은 항상 이메일로 보낸다는 정책이라면, 이건 runtime 선택이 아니라 고정 wiring이다.

### 사용자 선호 채널에 따라 달라지면 router가 맞다

```java
@Service
public class NotificationRouter {
    private final Map<String, NotificationSender> senders;

    public NotificationRouter(Map<String, NotificationSender> senders) {
        this.senders = senders;
    }

    public void send(String channel, NotificationMessage message) {
        NotificationSender sender = senders.get(channel);
        if (sender == null) {
            throw new IllegalArgumentException("Unknown channel: " + channel);
        }
        sender.send(message);
    }
}
```

사용자 설정이 `email`일 수도 있고 `sms`일 수도 있다면, 이건 `@Qualifier`로 못 푼다.

- `@Qualifier`는 파라미터에 박아 두는 값이다
- 사용자별 채널 선호는 요청마다 바뀔 수 있다
- 따라서 router나 strategy registry 쪽이 자연스럽다

---

## 자주 섞이는 오해

### 1. `Map<String, Bean>`도 결국 bean 하나를 고르는 것이니 qualifier와 같다고 생각한다

같지 않다.

- `@Qualifier`는 컨테이너의 후보 해석 규칙이다
- router는 이미 주입된 후보들 중에서 애플리케이션이 직접 dispatch하는 규칙이다

### 2. runtime 선택 문제인데 `@Qualifier`를 늘려서 해결하려고 한다

예를 들어 `@Qualifier("kakaoPaymentClient")`, `@Qualifier("tossPaymentClient")`를 여러 서비스에 퍼뜨리면 "고정 wiring"만 늘어난다.

사용자 입력이나 enum에 따라 바뀌는 선택은 router로 올려야 한다.

### 3. router의 key로 외부 입력을 bean 이름에 바로 묶는다

`Map<String, Bean>`의 key는 기본적으로 bean 이름이다.

이때 `"email"` 같은 외부 API 값을 바로 `"emailSender"` bean 이름에 결합해 버리면, wiring 이름이 외부 계약으로 새어 나간다.

beginner 기준으로는 아래가 더 안전하다.

- 외부 입력은 `NotificationChannel.EMAIL` 같은 enum으로 먼저 정규화한다
- router 내부에서 bean 이름 또는 별도 registry key로 매핑한다

즉, `Map<String, Bean>`를 쓰더라도 **bean 이름을 곧바로 API 계약으로 만들지는 않는 편이 낫다**.

### 4. qualifier가 반복된다고 바로 router로 가려고 한다

qualifier 반복은 대개 "같은 역할을 여러 곳에서 고정 선택한다"는 신호다.

이때는 먼저 [커스텀 `@Qualifier`](./spring-custom-qualifier-primer.md)를 검토한다.  
router는 "반복된 고정 선택"이 아니라 "호출마다 달라지는 선택"일 때 맞다.

---

## 빠른 선택 기준

| 상황 | 더 맞는 선택 | 이유 |
|---|---|---|
| 정산 서비스는 항상 카카오 PG만 써야 한다 | `@Qualifier` | wiring이 고정돼 있다 |
| 주문마다 PG사를 다르게 골라야 한다 | router | 요청 값마다 달라진다 |
| 영수증은 항상 이메일로 보낸다 | `@Qualifier` | 채널 정책이 고정이다 |
| 사용자 선호 채널에 따라 이메일/SMS를 바꾼다 | router | 실행 시점 입력이 필요하다 |
| 외부 `channel` 값을 bean 이름과 바로 연결하고 싶다 | router + domain key 정규화 | bean 이름은 컨테이너 key이고 API 계약은 따로 두는 편이 안전하다 |
| 같은 qualifier가 여러 서비스에 반복된다 | 커스텀 qualifier 검토 | runtime 선택이 아니라 의미 계약일 수 있다 |

---

## 꼬리질문

> Q: `@Qualifier`와 router의 가장 큰 차이는 무엇인가?
> 의도: 선택 주체와 시점을 구분하는지 확인
> 핵심: `@Qualifier`는 컨테이너가 주입 시점에 고르고, router는 애플리케이션이 실행 시점에 고른다.

> Q: `Map<String, PaymentClient>`를 주입받으면 Spring이 요청마다 다시 bean을 고르는가?
> 의도: collection 주입과 runtime dispatch를 구분하는지 확인
> 핵심: 아니다. Spring은 후보 전체를 한 번 주입하고, 이후 선택은 router 코드가 한다.

> Q: 결제 수단이 주문마다 달라질 수 있는데 `@Qualifier("kakaoPaymentClient")`로 해결해도 되는가?
> 의도: 고정 wiring과 per-request 선택을 구분하는지 확인
> 핵심: 아니다. 그건 runtime 전략 선택이므로 router가 더 맞다.

> Q: qualifier가 여러 서비스에 반복되면 바로 router로 가야 하는가?
> 의도: 반복된 고정 선택과 runtime 선택을 구분하는지 확인
> 핵심: 아니다. 먼저 커스텀 qualifier로 역할 계약을 올릴지 본다.

---

## 한 줄 정리

`@Qualifier`는 "이 서비스에 어떤 bean을 꽂을까"를 정하고, `Map<String, Bean>`/router는 "이번 호출에 어떤 전략을 실행할까"를 정한다.
